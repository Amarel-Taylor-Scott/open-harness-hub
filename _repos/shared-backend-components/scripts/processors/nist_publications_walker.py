#!/usr/bin/env python3
"""Backs `processor/nist-publications-walker`.

Walks the NIST Computer Security Resource Center (CSRC) publication catalog
and yields one knowledge node per publication. NIST SP 800-series and 1800-
series are the most-cited compliance sources in US federal AI / cyber
governance and the foundation of FedRAMP, NIST AI RMF, CMMC, FISMA control
catalogs.

Why NIST first vs. ISO / IEEE:
  - NIST publications are public-domain and have stable IDs.
  - csrc.nist.gov publishes a JSON listing of all SPs with title, summary,
    series, status, dates, and a stable PDF/HTML URL.
  - ISO and IEEE require subscription for the full text; their TITLES are
    public but the bodies aren't republishable.

This walker filters by series (SP 800, SP 1800, SP 500, FIPS, IR, AI 100)
and status (draft / final / withdrawn).

Each node carries:
  - pub_id (e.g., "NIST SP 800-53 Rev. 5")
  - series, number, revision, status, title, summary, topic_tags
  - issued_date, withdrawn_date
  - canonical_url (csrc.nist.gov landing page)
  - pdf_url

CLI:
    python -m scripts.processors.nist_publications_walker --self-test
    python -m scripts.processors.nist_publications_walker --smoke-test
    python -m scripts.processors.nist_publications_walker --series sp-800 --max 20
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from scripts.processors._walker_base import (
    DEFAULT_RATE_LIMIT_PER_SEC,
    RateLimiter,
    WalkStats,
    fetch_text,
)

# CSRC publishes per-series listing pages. The canonical search URL exposes
# a stable HTML listing we parse with regex (avoids dependency on an
# undocumented JSON endpoint that may move).
CSRC_BASE = "https://csrc.nist.gov"


SERIES_CONFIG: dict[str, dict[str, str]] = {
    "sp-800": {
        "label": "NIST Special Publication 800-series",
        "listing_url": "https://csrc.nist.gov/publications/sp800",
    },
    "sp-1800": {
        "label": "NIST Special Publication 1800-series",
        "listing_url": "https://csrc.nist.gov/publications/sp1800",
    },
    "sp-500": {
        "label": "NIST Special Publication 500-series",
        "listing_url": "https://csrc.nist.gov/publications/sp500",
    },
    "ai": {
        "label": "NIST AI publications (AI 100, AI 200, AI RMF)",
        "listing_url": "https://csrc.nist.gov/publications/ai",
    },
    "ir": {
        "label": "NIST Internal Reports (IR / NISTIR)",
        "listing_url": "https://csrc.nist.gov/publications/nistir",
    },
    "fips": {
        "label": "Federal Information Processing Standards (FIPS)",
        "listing_url": "https://csrc.nist.gov/publications/fips",
    },
}

# Each listing card contains a link to the publication page.
_PUB_LINK_RE = re.compile(
    r'<a[^>]+href="(/publications/detail/[^"]+)"[^>]*>([^<]+)</a>',
    re.IGNORECASE,
)
# Publication-detail page fields
_TITLE_RE = re.compile(r"<h3[^>]*>(.*?)</h3>", re.DOTALL | re.IGNORECASE)
_ABSTRACT_RE = re.compile(
    r'<div[^>]+id="pub-abstract-section"[^>]*>(.*?)</div>',
    re.DOTALL | re.IGNORECASE,
)
_STATUS_RE = re.compile(
    r'<strong>\s*Status\s*</strong>\s*:?\s*([A-Za-z]+)',
    re.IGNORECASE,
)
_DATE_PUBLISHED_RE = re.compile(
    r'<strong>\s*Date Published\s*</strong>\s*:?\s*([A-Za-z]+ \d{1,2},?\s*\d{4})',
    re.IGNORECASE,
)
_PDF_LINK_RE = re.compile(
    r'<a[^>]+href="([^"]+\.pdf)"',
    re.IGNORECASE,
)
_HTML_TAG_RE = re.compile(r"<[^>]+>")
_WHITESPACE_RE = re.compile(r"\s+")


def _strip_html(html: str) -> str:
    text = _HTML_TAG_RE.sub(" ", html or "")
    text = _WHITESPACE_RE.sub(" ", text).strip()
    return (
        text.replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&nbsp;", " ")
    )


@dataclass
class NISTPubNode:
    pub_id: str
    series: str
    title: str
    summary: str = ""
    status: str = ""
    issued_date: str = ""
    canonical_url: str = ""
    pdf_url: str = ""
    topic_tags: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "pub_id": self.pub_id,
            "series": self.series,
            "title": self.title,
            "summary": self.summary,
            "status": self.status,
            "issued_date": self.issued_date,
            "canonical_url": self.canonical_url,
            "pdf_url": self.pdf_url,
            "topic_tags": list(self.topic_tags),
            "warnings": list(self.warnings),
        }


def _list_publications(series_key: str, rate_limiter: RateLimiter, use_cache: bool) -> list[tuple[str, str]]:
    cfg = SERIES_CONFIG[series_key]
    html = fetch_text(cfg["listing_url"], rate_limiter, cache_kind="nist", use_cache=use_cache)
    pairs: list[tuple[str, str]] = []
    seen: set[str] = set()
    for m in _PUB_LINK_RE.finditer(html):
        path = m.group(1)
        title = _strip_html(m.group(2))
        if path in seen:
            continue
        seen.add(path)
        pairs.append((CSRC_BASE + path, title))
    return pairs


def _fetch_pub_detail(
    url: str,
    series: str,
    fallback_title: str,
    rate_limiter: RateLimiter,
    use_cache: bool,
) -> NISTPubNode:
    html = fetch_text(url, rate_limiter, cache_kind="nist", use_cache=use_cache)
    title_match = _TITLE_RE.search(html)
    title = _strip_html(title_match.group(1)) if title_match else fallback_title
    abstract_match = _ABSTRACT_RE.search(html)
    summary = _strip_html(abstract_match.group(1))[:2000] if abstract_match else ""
    status_match = _STATUS_RE.search(html)
    status = (status_match.group(1).strip().lower() if status_match else "")
    date_match = _DATE_PUBLISHED_RE.search(html)
    issued_date = date_match.group(1).strip() if date_match else ""
    pdf_match = _PDF_LINK_RE.search(html)
    pdf_url = pdf_match.group(1) if pdf_match else ""
    if pdf_url.startswith("/"):
        pdf_url = CSRC_BASE + pdf_url
    # Best-effort pub_id derivation from URL ("detail/sp/800-53/rev-5/final" → "NIST SP 800-53 Rev. 5")
    pub_id = _derive_pub_id_from_url(url, series, title)
    return NISTPubNode(
        pub_id=pub_id,
        series=series,
        title=title,
        summary=summary,
        status=status,
        issued_date=issued_date,
        canonical_url=url,
        pdf_url=pdf_url,
    )


_URL_ID_RE = re.compile(r"/publications/detail/([^/]+)/([^/]+)(?:/([^/]+))?", re.IGNORECASE)


def _derive_pub_id_from_url(url: str, series: str, fallback_title: str) -> str:
    m = _URL_ID_RE.search(url)
    if not m:
        return fallback_title
    s, num, rev = m.group(1), m.group(2), m.group(3)
    series_part = {"sp": "NIST SP", "fips": "FIPS", "ir": "NISTIR", "ai": "NIST AI"}.get(s.lower(), s.upper())
    if rev and rev.startswith("rev"):
        return f"{series_part} {num} Rev. {rev.replace('rev-', '').replace('rev', '').strip()}".strip()
    return f"{series_part} {num}".strip()


# ─── Public entrypoint ──────────────────────────────────────────────────────


def run(
    series: list[str] | None = None,
    max_nodes: int = 50,
    status_filter: list[str] | None = None,
    rate_limit_per_sec: float = DEFAULT_RATE_LIMIT_PER_SEC,
    use_cache: bool = True,
) -> dict[str, Any]:
    """Walk one or more NIST CSRC series and yield publication nodes.

    Args mirror the manifest declaration. status_filter accepts
    ['final', 'draft', 'withdrawn']; default is final-only.
    """
    if series is None:
        series = ["sp-800"]
    status_filter = [s.lower() for s in (status_filter or ["final"])]
    rate_limiter = RateLimiter(rate_limit_per_sec)
    stats = WalkStats(walker_kind="nist")
    stats.extra["series_attempted"] = list(series)
    stats.extra["status_filter"] = list(status_filter)
    start = time.monotonic()
    nodes: list[NISTPubNode] = []

    for series_key in series:
        if series_key not in SERIES_CONFIG:
            stats.warnings.append(f"unknown series: {series_key}")
            continue
        if len(nodes) >= max_nodes:
            stats.stopped_reason = "max_nodes"
            break
        try:
            pairs = _list_publications(series_key, rate_limiter, use_cache)
        except RuntimeError as e:
            stats.warnings.append(f"listing fetch failed: {series_key}: {e}")
            continue
        for url, title in pairs:
            if len(nodes) >= max_nodes:
                stats.stopped_reason = "max_nodes"
                break
            try:
                node = _fetch_pub_detail(url, series_key, title, rate_limiter, use_cache)
            except RuntimeError as e:
                stats.warnings.append(f"detail fetch failed: {url}: {e}")
                stats.nodes_skipped += 1
                continue
            if status_filter and node.status and node.status not in status_filter:
                stats.nodes_skipped += 1
                continue
            nodes.append(node)
            stats.nodes_emitted += 1

    stats.duration_s = time.monotonic() - start
    return {
        "nodes": [n.to_dict() for n in nodes],
        "walk_stats": stats.to_dict(),
    }


# ─── Self-test / smoke ──────────────────────────────────────────────────────


def _self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        marker = "ok" if ok else "FAIL"
        print(f"  [{marker}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    print("[self-test] series registry")
    for s in ("sp-800", "sp-1800", "ai", "fips"):
        check(f"series '{s}' registered", s in SERIES_CONFIG)

    print("[self-test] _derive_pub_id_from_url")
    check("SP 800-53 Rev. 5 parsed",
          _derive_pub_id_from_url("/publications/detail/sp/800-53/rev-5/final", "sp-800", "x")
          == "NIST SP 800-53 Rev. 5")
    check("FIPS 197 parsed",
          _derive_pub_id_from_url("/publications/detail/fips/197/final", "fips", "x")
          == "FIPS 197")

    print("[self-test] HTML strip")
    check("strips tags", _strip_html("<p>Hello <b>world</b></p>") == "Hello world")

    print(f"\n{'all self-tests passed.' if not failures else f'{len(failures)} failures: {failures}'}")
    return 0 if not failures else 1


def _smoke_test() -> int:
    print("[smoke-test] walking NIST sp-800, max 2 nodes (final only)")
    result = run(series=["sp-800"], max_nodes=2, rate_limit_per_sec=1.5)
    print(json.dumps(result["walk_stats"], indent=2))
    for n in result["nodes"]:
        print(f"  {n['pub_id']} — {n['title'][:80]}")
    return 0 if result["walk_stats"]["nodes_emitted"] > 0 else 1


# ─── CLI ────────────────────────────────────────────────────────────────────


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Walk NIST CSRC publications.")
    p.add_argument("--series", action="append", choices=sorted(SERIES_CONFIG.keys()))
    p.add_argument("--max-nodes", type=int, default=50)
    p.add_argument("--status", action="append", choices=["final", "draft", "withdrawn"])
    p.add_argument("--rate-limit-per-sec", type=float, default=DEFAULT_RATE_LIMIT_PER_SEC)
    p.add_argument("--no-cache", action="store_true")
    p.add_argument("--output", default="-")
    p.add_argument("--self-test", action="store_true")
    p.add_argument("--smoke-test", action="store_true")
    args = p.parse_args(argv)

    if args.self_test:
        return _self_test()
    if args.smoke_test:
        return _smoke_test()

    result = run(
        series=args.series,
        max_nodes=args.max_nodes,
        status_filter=args.status,
        rate_limit_per_sec=args.rate_limit_per_sec,
        use_cache=not args.no_cache,
    )
    out_json = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output == "-":
        sys.stdout.write(out_json + "\n")
    else:
        Path(args.output).write_text(out_json, encoding="utf-8")
        sys.stderr.write(f"wrote {len(result['nodes'])} NIST pubs to {args.output}\n")
    return 0


if __name__ == "__main__":
    sys.exit(_main())
