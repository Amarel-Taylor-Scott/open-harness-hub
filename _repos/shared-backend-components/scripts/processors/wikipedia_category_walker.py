#!/usr/bin/env python3
"""Backs `processor/wikipedia-category-walker`.

Walks a Wikipedia category tree via the MediaWiki Action API and yields one
structured "knowledge node" per article and per sub-category. Each node is
frozen at a specific revision_id for reproducible re-runs and cached on disk.

Public entrypoint:
    run(root_category, max_depth, max_nodes, language_edition,
        revision_freeze_ts, rate_limit_per_sec, use_cache, fetch_wikitext)
    -> {"nodes": [...], "walk_stats": {...}}

CLI:
    python -m scripts.processors.wikipedia_category_walker \\
        --root-category "Money laundering" --max-depth 2 --max-nodes 50

Offline self-test (no network):
    python -m scripts.processors.wikipedia_category_walker --self-test

Live smoke test (one small stable category, hits Wikipedia):
    python -m scripts.processors.wikipedia_category_walker --smoke-test

Dependencies: standard library only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# ─── Configuration ──────────────────────────────────────────────────────────

# Per https://meta.wikimedia.org/wiki/User-Agent_policy — must identify the
# tool and provide a contact channel. Update the contact URL if forking.
USER_AGENT = (
    "OpenHubForAIWalker/0.1 "
    "(+https://github.com/Amarel-Taylor-Scott/openhubforai; issues via repo)"
)

DEFAULT_RATE_LIMIT_PER_SEC = 1.0
CACHE_DIR = Path.home() / ".cache" / "oh-hub" / "wikipedia"

# Hard ceiling — bounds runaway walks even when max_nodes is set absurdly high.
ABSOLUTE_NODE_CEILING = 5000

# Intro text length (matches the manifest's documented 1500-char cap).
DEFAULT_EXTRACT_CHARS = 1500

# Cap on cited sources per article (matches the manifest).
DEFAULT_CITATION_CAP = 50


# ─── Output node type ───────────────────────────────────────────────────────


@dataclass
class Node:
    title: str
    canonical_url: str
    revision_id: int | None
    parent_category_path: list[str]
    is_category: bool
    intro_text: str = ""
    infobox: dict[str, str] = field(default_factory=dict)
    cited_sources: list[dict[str, str]] = field(default_factory=list)
    sub_categories: list[str] = field(default_factory=list)
    member_count: int = 0
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "canonical_url": self.canonical_url,
            "revision_id": self.revision_id,
            "parent_category_path": list(self.parent_category_path),
            "is_category": self.is_category,
            "intro_text": self.intro_text,
            "infobox": dict(self.infobox),
            "cited_sources": list(self.cited_sources),
            "sub_categories": list(self.sub_categories),
            "member_count": self.member_count,
            "warnings": list(self.warnings),
        }


# ─── HTTP + cache ───────────────────────────────────────────────────────────


class RateLimiter:
    """Simple monotonic-clock spacing between calls."""

    def __init__(self, requests_per_second: float):
        self.interval = 1.0 / max(requests_per_second, 0.01)
        self._last_call = 0.0

    def wait(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_call
        if elapsed < self.interval:
            time.sleep(self.interval - elapsed)
        self._last_call = time.monotonic()


def _cache_path(url: str) -> Path:
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:32]
    return CACHE_DIR / f"{digest}.json"


def _fetch_json(url: str, rate_limiter: RateLimiter, use_cache: bool) -> dict:
    """Fetch a MediaWiki API URL; cache hit returns immediately, miss respects rate limit + retries."""
    cache = _cache_path(url)
    if use_cache and cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))

    last_err: Exception | None = None
    for attempt in range(4):
        rate_limiter.wait()
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as e:
            last_err = e
            # Exponential backoff: 1s, 2s, 4s, 8s. Wikimedia 503s usually clear fast.
            time.sleep(min(30, 2 ** attempt))
            continue

        if use_cache:
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            cache.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        return data

    raise RuntimeError(f"failed to fetch {url}: {last_err}")


# ─── MediaWiki API helpers ──────────────────────────────────────────────────


def _api_url(lang: str, params: dict[str, str]) -> str:
    return f"https://{lang}.wikipedia.org/w/api.php?" + urllib.parse.urlencode(params)


def _canonical_url(lang: str, title: str) -> str:
    quoted = urllib.parse.quote(title.replace(" ", "_"), safe=":/_(),.")
    return f"https://{lang}.wikipedia.org/wiki/{quoted}"


def _strip_category_prefix(title: str) -> str:
    return title.split(":", 1)[1] if ":" in title and title.lower().startswith("category:") else title


def _list_category_members(
    lang: str,
    category_title: str,
    rate_limiter: RateLimiter,
    use_cache: bool,
) -> list[dict[str, Any]]:
    """All pages + sub-categories under a category, paginated via cmcontinue."""
    members: list[dict[str, Any]] = []
    cmcontinue: str | None = None
    while True:
        params: dict[str, str] = {
            "action": "query",
            "format": "json",
            "list": "categorymembers",
            "cmtitle": category_title,
            "cmlimit": "500",
            "cmtype": "page|subcat",
            "cmprop": "ids|title|type",
        }
        if cmcontinue:
            params["cmcontinue"] = cmcontinue
        data = _fetch_json(_api_url(lang, params), rate_limiter, use_cache)
        members.extend(data.get("query", {}).get("categorymembers", []) or [])
        cont = (data.get("continue") or {}).get("cmcontinue")
        if not cont:
            break
        cmcontinue = cont
    return members


def _resolve_revision(
    lang: str,
    title: str,
    rate_limiter: RateLimiter,
    use_cache: bool,
    revision_freeze_ts: str | None,
) -> int | None:
    """Pick the revision at or before revision_freeze_ts; latest if no ts given."""
    params: dict[str, str] = {
        "action": "query",
        "format": "json",
        "prop": "revisions",
        "titles": title,
        "rvprop": "ids|timestamp",
        "rvlimit": "1",
        "redirects": "1",
    }
    if revision_freeze_ts:
        params["rvstart"] = revision_freeze_ts
        params["rvdir"] = "older"
    data = _fetch_json(_api_url(lang, params), rate_limiter, use_cache)
    for _, page in (data.get("query", {}).get("pages") or {}).items():
        if page.get("missing") is not None:
            return None
        revs = page.get("revisions") or []
        if revs:
            return int(revs[0]["revid"])
    return None


def _fetch_extract(
    lang: str,
    title: str,
    rate_limiter: RateLimiter,
    use_cache: bool,
    exchars: int = DEFAULT_EXTRACT_CHARS,
) -> str:
    """Plain-text intro via the TextExtracts extension (default-enabled on Wikipedia)."""
    params = {
        "action": "query",
        "format": "json",
        "prop": "extracts",
        "titles": title,
        "exintro": "1",
        "explaintext": "1",
        "exchars": str(exchars),
        "redirects": "1",
    }
    data = _fetch_json(_api_url(lang, params), rate_limiter, use_cache)
    for _, page in (data.get("query", {}).get("pages") or {}).items():
        if page.get("missing") is not None:
            return ""
        return (page.get("extract") or "")[:exchars]
    return ""


def _fetch_wikitext(
    lang: str,
    title: str,
    revision_id: int | None,
    rate_limiter: RateLimiter,
    use_cache: bool,
) -> str:
    """Raw wikitext for an article, frozen to revision_id if supplied."""
    params: dict[str, str] = {
        "action": "parse",
        "format": "json",
        "prop": "wikitext",
        "redirects": "1",
    }
    if revision_id is not None:
        params["oldid"] = str(revision_id)
    else:
        params["page"] = title
    try:
        data = _fetch_json(_api_url(lang, params), rate_limiter, use_cache)
    except RuntimeError:
        return ""
    return ((data.get("parse") or {}).get("wikitext") or {}).get("*", "") or ""


# ─── Wikitext parsing (regex, best-effort) ──────────────────────────────────
#
# These extractors are deliberately stdlib-only. They handle the common shapes
# accurately enough for catalog drafting; pathological infoboxes with deeply
# nested templates will under-extract. Swap in `mwparserfromhell` if perfect
# fidelity becomes required.

# Locate the first {{Infobox <kind>\n| key = value\n| ... }} block.
_INFOBOX_HEAD_RE = re.compile(r"\{\{\s*Infobox[ _]([^\n|}]+)", re.IGNORECASE)
_INFOBOX_FIELD_RE = re.compile(r"^\s*\|\s*([^=\n]+?)\s*=\s*(.*?)\s*$", re.MULTILINE)


def _find_balanced_template(text: str, start: int) -> int | None:
    """Return the index AFTER the closing '}}' of the template starting at `start` ('{{')."""
    if text[start : start + 2] != "{{":
        return None
    depth = 0
    i = start
    n = len(text)
    while i < n - 1:
        pair = text[i : i + 2]
        if pair == "{{":
            depth += 1
            i += 2
        elif pair == "}}":
            depth -= 1
            i += 2
            if depth == 0:
                return i
        else:
            i += 1
    return None


def _extract_infobox(wikitext: str) -> dict[str, str]:
    """Best-effort first-infobox key/value extraction.

    Limitations:
      - Picks the FIRST infobox only.
      - Values may retain wiki markup (links, sub-templates).
      - Values are truncated to 500 chars defensively.
    """
    match = _INFOBOX_HEAD_RE.search(wikitext)
    if not match:
        return {}
    start = match.start()
    end = _find_balanced_template(wikitext, start)
    if end is None:
        return {}
    body = wikitext[start:end]
    fields: dict[str, str] = {}
    for field_match in _INFOBOX_FIELD_RE.finditer(body):
        key = field_match.group(1).strip().lower().replace(" ", "_")
        value = field_match.group(2).strip()
        if value and key not in fields:
            fields[key] = value[:500]
    return fields


# <ref>...</ref> with optional attributes; <ref name="..." /> self-closing
_REF_BLOCK_RE = re.compile(r"<ref(?:\s[^>]*)?>(.*?)</ref>", re.DOTALL | re.IGNORECASE)
# {{cite kind | key1=val1 | key2=val2}}
_CITE_TEMPLATE_RE = re.compile(r"\{\{(cite[^|}]*)\|(.*?)\}\}", re.DOTALL | re.IGNORECASE)
# bare URL
_BARE_URL_RE = re.compile(r"https?://[^\s\]|}<]+")


def _extract_citations(wikitext: str, cap: int = DEFAULT_CITATION_CAP) -> list[dict[str, str]]:
    """Pull up to `cap` citations from <ref> blocks. De-duplicates by content signature."""
    refs: list[dict[str, str]] = []
    seen: set[str] = set()
    for block_match in _REF_BLOCK_RE.finditer(wikitext):
        raw = block_match.group(1).strip()
        if not raw:
            continue
        entry: dict[str, str]
        cite = _CITE_TEMPLATE_RE.search(raw)
        if cite:
            kind = cite.group(1).strip().lower()
            args: dict[str, str] = {"kind": kind}
            for pair in cite.group(2).split("|"):
                if "=" in pair:
                    k, v = pair.split("=", 1)
                    k = k.strip().lower()
                    v = v.strip()[:300]
                    if k and v and k not in args:
                        args[k] = v
            entry = args
        else:
            url_match = _BARE_URL_RE.search(raw)
            entry = {"kind": "bare", "text": raw[:300]}
            if url_match:
                entry["url"] = url_match.group(0)[:300]
        sig = json.dumps(entry, sort_keys=True)[:300]
        if sig in seen:
            continue
        seen.add(sig)
        refs.append(entry)
        if len(refs) >= cap:
            break
    return refs


# Disambiguation pages add noise to a catalog walk; flag and skip extraction depth.
_DISAMBIG_RE = re.compile(r"\{\{\s*(disambiguation|disambig|hndis|geodis|surname)", re.IGNORECASE)


def _is_disambiguation(wikitext: str) -> bool:
    return bool(_DISAMBIG_RE.search(wikitext))


# ─── The walk ───────────────────────────────────────────────────────────────


def run(
    root_category: str,
    max_depth: int = 3,
    max_nodes: int = 200,
    language_edition: str = "en",
    revision_freeze_ts: str | None = None,
    rate_limit_per_sec: float = DEFAULT_RATE_LIMIT_PER_SEC,
    use_cache: bool = True,
    fetch_wikitext: bool = True,
) -> dict[str, Any]:
    """Walk a Wikipedia category tree and emit one knowledge node per member.

    Matches the manifest at `_repos/shared-backend-components/catalog/processors/wikipedia-category-walker.yaml`.

    Returns:
        {"nodes": [Node.to_dict(), ...], "walk_stats": {...}}
    """
    if max_nodes > ABSOLUTE_NODE_CEILING:
        raise ValueError(
            f"max_nodes={max_nodes} exceeds ABSOLUTE_NODE_CEILING={ABSOLUTE_NODE_CEILING}; "
            f"split the walk or raise the ceiling deliberately."
        )

    rate_limiter = RateLimiter(rate_limit_per_sec)
    start = time.monotonic()

    root_title = root_category if root_category.lower().startswith("category:") else f"Category:{root_category}"

    # BFS queue of (category_title, depth, parent_path)
    queue: deque[tuple[str, int, list[str]]] = deque([(root_title, 0, [])])
    visited_categories: set[str] = set()
    visited_articles: set[str] = set()
    nodes: list[Node] = []
    walk_warnings: list[str] = []
    articles_emitted = 0
    categories_walked = 0
    max_depth_reached = 0
    stopped_reason = "completed"

    while queue:
        category_title, depth, parent_path = queue.popleft()

        if category_title in visited_categories:
            continue
        if depth > max_depth:
            stopped_reason = "max_depth_exhausted"
            continue
        if len(nodes) >= max_nodes:
            stopped_reason = "max_nodes"
            break

        visited_categories.add(category_title)
        categories_walked += 1
        max_depth_reached = max(max_depth_reached, depth)

        try:
            members = _list_category_members(language_edition, category_title, rate_limiter, use_cache)
        except RuntimeError as e:
            walk_warnings.append(f"category fetch failed: {category_title}: {e}")
            continue

        category_display = _strip_category_prefix(category_title)
        sub_cat_titles = [m["title"] for m in members if m.get("type") == "subcat"]
        nodes.append(
            Node(
                title=category_display,
                canonical_url=_canonical_url(language_edition, category_title),
                revision_id=None,  # categories aren't pinned by revision in this walk
                parent_category_path=list(parent_path),
                is_category=True,
                sub_categories=[_strip_category_prefix(t) for t in sub_cat_titles],
                member_count=len(members),
            )
        )

        next_parent_path = parent_path + [category_display]

        for m in members:
            if len(nodes) >= max_nodes:
                stopped_reason = "max_nodes"
                break
            mtype = m.get("type")
            mtitle = m.get("title")
            if not mtitle:
                continue

            if mtype == "subcat":
                if depth + 1 <= max_depth:
                    queue.append((mtitle, depth + 1, next_parent_path))
                continue

            if mtype == "page":
                if mtitle in visited_articles:
                    continue
                visited_articles.add(mtitle)
                try:
                    article = _fetch_article(
                        lang=language_edition,
                        title=mtitle,
                        parent_path=next_parent_path,
                        rate_limiter=rate_limiter,
                        use_cache=use_cache,
                        revision_freeze_ts=revision_freeze_ts,
                        fetch_wikitext_=fetch_wikitext,
                    )
                except RuntimeError as e:
                    walk_warnings.append(f"article fetch failed: {mtitle}: {e}")
                    continue
                if article is not None:
                    nodes.append(article)
                    articles_emitted += 1

    walk_stats = {
        "nodes_emitted": len(nodes),
        "articles_emitted": articles_emitted,
        "categories_walked": categories_walked,
        "max_depth_reached": max_depth_reached,
        "duration_s": round(time.monotonic() - start, 2),
        "language_edition": language_edition,
        "revision_freeze_ts": revision_freeze_ts,
        "stopped_reason": stopped_reason,
        "warnings": walk_warnings,
    }
    return {
        "nodes": [n.to_dict() for n in nodes],
        "walk_stats": walk_stats,
    }


def _fetch_article(
    *,
    lang: str,
    title: str,
    parent_path: list[str],
    rate_limiter: RateLimiter,
    use_cache: bool,
    revision_freeze_ts: str | None,
    fetch_wikitext_: bool,
) -> Node | None:
    rev_id = _resolve_revision(lang, title, rate_limiter, use_cache, revision_freeze_ts)
    if rev_id is None:
        return None
    intro = _fetch_extract(lang, title, rate_limiter, use_cache)
    node = Node(
        title=title,
        canonical_url=_canonical_url(lang, title),
        revision_id=rev_id,
        parent_category_path=list(parent_path),
        is_category=False,
        intro_text=intro,
    )
    if fetch_wikitext_:
        wt = _fetch_wikitext(lang, title, rev_id, rate_limiter, use_cache)
        if wt:
            if _is_disambiguation(wt):
                node.warnings.append("disambiguation_page")
            else:
                node.infobox = _extract_infobox(wt)
                node.cited_sources = _extract_citations(wt, cap=DEFAULT_CITATION_CAP)
    return node


# ─── Self-test (offline, no network) ────────────────────────────────────────


def _self_test() -> int:
    """Verify regex helpers + balanced-template scanner against canned wikitext."""
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        marker = "ok" if ok else "FAIL"
        print(f"  [{marker}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    sample_wikitext = """\
{{Infobox company
| name        = Acme Widgets
| founded     = 1947
| headquarters = [[Springfield, USA]]
| industry    = Manufacturing
| products    = {{collapsible list | widgets | gadgets | sprockets}}
}}

'''Acme Widgets''' is a fictitious manufacturer of widgets.<ref>{{cite news |url=https://example.com/acme |title=Acme background |publisher=Example News |date=2024-01-15}}</ref>

It has appeared in many cartoons.<ref name="cartoon-history" />
Sources include:<ref>{{cite book |author=Smith, J. |title=Cartoon Antagonists |year=2010 |publisher=Acme Press}}</ref>
<ref>Direct quote with bare URL https://example.org/page-about-acme without a cite template</ref>
"""

    print("[self-test] infobox extraction")
    info = _extract_infobox(sample_wikitext)
    check("name field present", info.get("name") == "Acme Widgets", f"got {info.get('name')!r}")
    check("founded field present", info.get("founded") == "1947", f"got {info.get('founded')!r}")
    check("industry field present", info.get("industry") == "Manufacturing")
    check("nested-template value captured", "collapsible list" in info.get("products", ""))

    print("[self-test] citation extraction")
    cites = _extract_citations(sample_wikitext)
    check("at least 2 distinct refs", len(cites) >= 2, f"got {len(cites)}")
    kinds = {c.get("kind") for c in cites}
    check("cite news kind detected", any(k.startswith("cite news") for k in kinds), f"kinds={kinds}")
    check("cite book kind detected", any(k.startswith("cite book") for k in kinds), f"kinds={kinds}")
    check("bare URL captured", any("example.org" in c.get("url", "") for c in cites if c.get("kind") == "bare"))

    print("[self-test] balanced template scanner")
    nested = "{{outer | {{inner1}} | {{inner2 | nested}} }}"
    end = _find_balanced_template(nested, 0)
    check("balanced scanner reaches end", end == len(nested), f"end={end} len={len(nested)}")

    print("[self-test] disambiguation detection")
    disamb_wt = "Foo (foo) may refer to:\n{{Disambiguation}}\n"
    check("disambiguation flagged", _is_disambiguation(disamb_wt))
    check("plain article not flagged", not _is_disambiguation("Plain article body."))

    print("[self-test] canonical URL builder")
    check(
        "canonical_url has underscores not spaces",
        _canonical_url("en", "Money laundering") == "https://en.wikipedia.org/wiki/Money_laundering",
    )
    check(
        "canonical_url for categories",
        _canonical_url("en", "Category:Money laundering")
        == "https://en.wikipedia.org/wiki/Category:Money_laundering",
    )

    print(f"\n{'all self-tests passed.' if not failures else f'{len(failures)} self-test failures: {failures}'}")
    return 0 if not failures else 1


def _smoke_test() -> int:
    """Tiny live walk against a small stable category. Hits Wikipedia — needs network."""
    print("[smoke-test] walking Category:Wikipedia_administration (depth=0, max_nodes=10, skip wikitext)")
    result = run(
        root_category="Wikipedia administration",
        max_depth=0,
        max_nodes=10,
        language_edition="en",
        fetch_wikitext=False,  # speed: skip per-article wikitext fetch
    )
    stats = result["walk_stats"]
    print(json.dumps(stats, indent=2))
    print(f"first {min(3, len(result['nodes']))} node titles:")
    for n in result["nodes"][:3]:
        kind = "CAT" if n["is_category"] else "ART"
        print(f"  [{kind}] {n['title']} — {n['canonical_url']}")
    return 0 if stats["nodes_emitted"] > 0 else 1


# ─── CLI ────────────────────────────────────────────────────────────────────


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Walk a Wikipedia category tree into structured nodes.")
    p.add_argument("--root-category", help='e.g. "Money laundering"')
    p.add_argument("--max-depth", type=int, default=3)
    p.add_argument("--max-nodes", type=int, default=200)
    p.add_argument("--language-edition", default="en")
    p.add_argument(
        "--revision-freeze-ts",
        default=None,
        help="ISO 8601 timestamp; revisions at or before this are pinned",
    )
    p.add_argument("--rate-limit-per-sec", type=float, default=DEFAULT_RATE_LIMIT_PER_SEC)
    p.add_argument("--no-cache", action="store_true", help="Disable on-disk cache")
    p.add_argument(
        "--skip-wikitext",
        action="store_true",
        help="Faster walk; skips infobox + citation extraction",
    )
    p.add_argument("--output", default="-", help="Output file path (- for stdout)")
    p.add_argument("--self-test", action="store_true", help="Run offline regex self-tests")
    p.add_argument(
        "--smoke-test",
        action="store_true",
        help="Run a tiny live walk (needs network) to verify API access",
    )
    args = p.parse_args(argv)

    if args.self_test:
        return _self_test()
    if args.smoke_test:
        return _smoke_test()
    if not args.root_category:
        p.error("--root-category is required (or use --self-test / --smoke-test)")

    result = run(
        root_category=args.root_category,
        max_depth=args.max_depth,
        max_nodes=args.max_nodes,
        language_edition=args.language_edition,
        revision_freeze_ts=args.revision_freeze_ts,
        rate_limit_per_sec=args.rate_limit_per_sec,
        use_cache=not args.no_cache,
        fetch_wikitext=not args.skip_wikitext,
    )

    out_json = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output == "-":
        sys.stdout.write(out_json)
        sys.stdout.write("\n")
    else:
        Path(args.output).write_text(out_json, encoding="utf-8")
        sys.stderr.write(
            f"wrote {len(result['nodes'])} nodes "
            f"({result['walk_stats']['articles_emitted']} articles, "
            f"{result['walk_stats']['categories_walked']} categories) to {args.output}\n"
        )
    return 0


if __name__ == "__main__":
    sys.exit(_main())
