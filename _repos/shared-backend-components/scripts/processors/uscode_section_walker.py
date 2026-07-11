#!/usr/bin/env python3
"""Backs `processor/uscode-section-walker`.

Walks the United States Code via the Cornell LII JSON-ish endpoints. Each
section yields one structured "knowledge node" suitable for drafting into a
knowledge-pack entry, a GREP rule-pack pattern, or a rubric input.

Source choice rationale:
  - The authoritative Office of Law Revision Counsel (OLRC) publishes the
    USC as downloadable XML "releases" at uscode.house.gov. Those are the
    canonical files but require a multi-hundred-MB download and a USLM XML
    parser.
  - Cornell LII (law.cornell.edu) republishes the USC with stable URLs at
    /uscode/text/{title}/{section} and exposes a structured-ish JSON
    sibling for many sections. We use that as the convenient public API.
  - Both sources are public domain (US federal law) so attribution is to
    the publishing URL only.

Node fields per the manifest:
  - usc_citation, title_number, chapter_number, section_number, heading,
    full_text, cross_references, canonical_url, source

CLI:
    python -m scripts.processors.uscode_section_walker --self-test
    python -m scripts.processors.uscode_section_walker --smoke-test
    python -m scripts.processors.uscode_section_walker --title 31 --max-sections 5
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

LII_BASE = "https://www.law.cornell.edu/uscode/text"
# Cornell exposes a JSON sibling on some endpoints with content-negotiation;
# the HTML-with-microdata is more reliable + scrapeable with a simple regex.

ABSOLUTE_SECTION_CEILING = 5000


@dataclass
class USCNode:
    usc_citation: str
    title_number: int
    chapter_number: str
    section_number: str
    heading: str
    canonical_url: str
    full_text: str = ""
    cross_references: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    repealed: bool = False
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "usc_citation": self.usc_citation,
            "title_number": self.title_number,
            "chapter_number": self.chapter_number,
            "section_number": self.section_number,
            "heading": self.heading,
            "canonical_url": self.canonical_url,
            "full_text": self.full_text,
            "cross_references": list(self.cross_references),
            "notes": list(self.notes),
            "repealed": self.repealed,
            "warnings": list(self.warnings),
        }


# ─── HTML parsing (regex-based; no BeautifulSoup) ───────────────────────────

_TITLE_TOC_LINK_RE = re.compile(
    r'<a[^>]+href="(/uscode/text/(\d+)/(\d+(?:\.\d+)?[a-zA-Z]?(?:-\d+)?))"[^>]*>',
    re.IGNORECASE,
)
_SECTION_HEADING_RE = re.compile(
    r'<h\d[^>]*itemprop="name"[^>]*>(.*?)</h\d>',
    re.DOTALL | re.IGNORECASE,
)
_SECTION_HEADING_FALLBACK_RE = re.compile(
    r'<h1[^>]*class="[^"]*headerNorm[^"]*"[^>]*>(.*?)</h1>',
    re.DOTALL | re.IGNORECASE,
)
_BODY_RE = re.compile(
    r'<div[^>]+id="(?:contained|text)[^"]*"[^>]*>(.*?)</div>\s*(?:<div|<aside|<footer)',
    re.DOTALL | re.IGNORECASE,
)
_XREF_RE = re.compile(
    r'(?:section|sections|chapter|chapters)\s+([0-9]+(?:\([a-z0-9]+\))*)(?:\s+of\s+(?:this title|title\s+(\d+)))?',
    re.IGNORECASE,
)
_REPEALED_RE = re.compile(r'\brepealed\.?\s*<', re.IGNORECASE)
_HTML_TAG_RE = re.compile(r"<[^>]+>")
_WHITESPACE_RE = re.compile(r"\s+")


def _strip_html(html: str) -> str:
    text = _HTML_TAG_RE.sub(" ", html)
    text = _WHITESPACE_RE.sub(" ", text).strip()
    # decode the most common entities without importing html
    return (
        text.replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&quot;", '"')
        .replace("&#39;", "'")
        .replace("&nbsp;", " ")
    )


# ─── Walks ──────────────────────────────────────────────────────────────────


def _walk_title_toc(
    title_number: int,
    rate_limiter: RateLimiter,
    use_cache: bool,
) -> list[tuple[str, str]]:
    """Return list of (section_number, canonical_url) within a USC title."""
    url = f"{LII_BASE}/{title_number}"
    try:
        html = fetch_text(url, rate_limiter, cache_kind="uscode", use_cache=use_cache)
    except RuntimeError:
        return []
    seen: set[str] = set()
    pairs: list[tuple[str, str]] = []
    for m in _TITLE_TOC_LINK_RE.finditer(html):
        rel = m.group(1)
        title_in_link = int(m.group(2))
        section = m.group(3)
        if title_in_link != title_number:
            continue
        if section in seen:
            continue
        seen.add(section)
        pairs.append((section, "https://www.law.cornell.edu" + rel))
    return pairs


def _fetch_section(
    title_number: int,
    section: str,
    url: str,
    rate_limiter: RateLimiter,
    use_cache: bool,
) -> USCNode | None:
    try:
        html = fetch_text(url, rate_limiter, cache_kind="uscode", use_cache=use_cache)
    except RuntimeError:
        return None
    if "<title>404" in html[:2000]:
        return None
    heading_match = _SECTION_HEADING_RE.search(html) or _SECTION_HEADING_FALLBACK_RE.search(html)
    heading = _strip_html(heading_match.group(1)) if heading_match else f"§ {section}"
    body_match = _BODY_RE.search(html)
    body_html = body_match.group(1) if body_match else ""
    body_text = _strip_html(body_html)[:8000] if body_html else ""
    repealed = bool(_REPEALED_RE.search(html[:5000])) or "Repealed" in heading
    xrefs: list[str] = []
    if body_text:
        for xm in _XREF_RE.finditer(body_text):
            ref_section = xm.group(1)
            ref_title = xm.group(2) or str(title_number)
            xrefs.append(f"{ref_title} U.S.C. § {ref_section}")
    # de-dup xrefs while preserving order
    seen: set[str] = set()
    xrefs_deduped: list[str] = []
    for x in xrefs:
        if x not in seen:
            seen.add(x)
            xrefs_deduped.append(x)
    return USCNode(
        usc_citation=f"{title_number} U.S.C. § {section}",
        title_number=title_number,
        chapter_number="",  # populated only when chapter walk is added
        section_number=section,
        heading=heading,
        canonical_url=url,
        full_text=body_text,
        cross_references=xrefs_deduped[:30],
        repealed=repealed,
    )


# ─── Public entrypoint ──────────────────────────────────────────────────────


def run(
    titles: list[int] | None = None,
    max_sections: int = 50,
    skip_repealed: bool = True,
    lrc_release_tag: str | None = None,
    rate_limit_per_sec: float = DEFAULT_RATE_LIMIT_PER_SEC,
    use_cache: bool = True,
) -> dict[str, Any]:
    """Walk USC titles via Cornell LII; return structured section nodes.

    Args mirror `_repos/shared-backend-components/catalog/processors/uscode-section-walker.yaml`.
    `lrc_release_tag` is recorded in stats for provenance; the LII walker
    doesn't pin to OLRC release tags (it follows Cornell's current text).
    """
    if max_sections > ABSOLUTE_SECTION_CEILING:
        raise ValueError(f"max_sections={max_sections} > ABSOLUTE_SECTION_CEILING={ABSOLUTE_SECTION_CEILING}")

    if not titles:
        # Default to a single small high-value title (Title 31 — Money & Finance) for demos.
        titles = [31]

    rate_limiter = RateLimiter(rate_limit_per_sec)
    stats = WalkStats(walker_kind="uscode")
    stats.extra["titles_attempted"] = list(titles)
    stats.extra["lrc_release_tag"] = lrc_release_tag
    stats.extra["source"] = "law.cornell.edu (Cornell LII republication)"

    start = time.monotonic()
    nodes: list[USCNode] = []

    for title_number in titles:
        if len(nodes) >= max_sections:
            stats.stopped_reason = "max_sections"
            break
        toc = _walk_title_toc(title_number, rate_limiter, use_cache)
        if not toc:
            stats.warnings.append(f"empty TOC for title {title_number}; URL may have changed")
            continue
        for section_number, section_url in toc:
            if len(nodes) >= max_sections:
                stats.stopped_reason = "max_sections"
                break
            node = _fetch_section(title_number, section_number, section_url, rate_limiter, use_cache)
            if node is None:
                stats.nodes_skipped += 1
                continue
            if skip_repealed and node.repealed:
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

    sample_html = (
        '<html><body>'
        '<h1 itemprop="name">§ 5324. Structuring transactions to evade reporting requirement prohibited</h1>'
        '<div id="contained">'
        '  <p>(a) Domestic coin and currency transactions involving financial institutions. '
        '— No person shall ...</p>'
        '  <p>(b) See section 5322 of this title and chapter 53 for definitions.</p>'
        '  <p>(c) See section 1957 of title 18 for related criminal provisions.</p>'
        '</div>'
        '<div class="related-content">unrelated sidebar</div>'
        '</body></html>'
    )

    print("[self-test] heading extraction")
    m = _SECTION_HEADING_RE.search(sample_html)
    check("heading regex matches", m is not None)
    if m:
        text = _strip_html(m.group(1))
        check("heading text correct",
              "Structuring transactions" in text, detail=repr(text))

    print("[self-test] body extraction")
    bm = _BODY_RE.search(sample_html)
    check("body regex matches", bm is not None)

    print("[self-test] cross-reference extraction")
    bm = _BODY_RE.search(sample_html)
    body_text = _strip_html(bm.group(1)) if bm else ""
    xrefs = []
    for xm in _XREF_RE.finditer(body_text):
        xrefs.append((xm.group(1), xm.group(2)))
    check("at least one xref found", len(xrefs) >= 1, detail=str(xrefs))

    print("[self-test] repealed detection")
    check("repealed flagged on 'Repealed.'", bool(_REPEALED_RE.search("<h1>§ 99. Repealed.</h1>")))
    check("not flagged on plain text", not _REPEALED_RE.search("<h1>§ 99. Regular section</h1>"))

    print(f"\n{'all self-tests passed.' if not failures else f'{len(failures)} failures: {failures}'}")
    return 0 if not failures else 1


def _smoke_test() -> int:
    print("[smoke-test] walking USC Title 31, max 3 sections")
    result = run(titles=[31], max_sections=3, rate_limit_per_sec=1.5)
    print(json.dumps(result["walk_stats"], indent=2))
    for n in result["nodes"]:
        print(f"  {n['usc_citation']} — {n['heading']!r} ({len(n['full_text'])} chars body)")
    return 0 if result["walk_stats"]["nodes_emitted"] > 0 else 1


# ─── CLI ────────────────────────────────────────────────────────────────────


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Walk USC titles via Cornell LII.")
    p.add_argument("--title", type=int, action="append", help="USC title number (repeatable)")
    p.add_argument("--max-sections", type=int, default=50)
    p.add_argument("--skip-repealed", action="store_true", default=True)
    p.add_argument("--include-repealed", dest="skip_repealed", action="store_false")
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
        titles=args.title,
        max_sections=args.max_sections,
        skip_repealed=args.skip_repealed,
        rate_limit_per_sec=args.rate_limit_per_sec,
        use_cache=not args.no_cache,
    )

    out_json = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output == "-":
        sys.stdout.write(out_json + "\n")
    else:
        Path(args.output).write_text(out_json, encoding="utf-8")
        sys.stderr.write(f"wrote {len(result['nodes'])} USC sections to {args.output}\n")
    return 0


if __name__ == "__main__":
    sys.exit(_main())
