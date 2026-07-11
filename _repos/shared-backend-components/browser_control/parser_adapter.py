#!/usr/bin/env python3
"""browser_control.parser_adapter — the pure HTML → structured-data primitive (stdlib html.parser).

Turns a page's HTML (from FetchAdapter, any BrowserAdapter, or a file) into readable text, links, tables, and
page metadata — with ZERO third-party dependencies, so it is always available. This is the extraction lane of
the zoo: fetching and parsing are separate primitives you compose.

REUSE-FIRST: the text/link/form extractors are the harness ``browser_*`` pure functions and the table
extractor is ``browser_control.adapter.extract_tables_from_html`` (the one stdlib <table> pass) — nothing is
re-implemented. The only logic added here is a small stdlib metadata parser (title / description / canonical /
lang / OpenGraph / heading counts) the harness lacks, plus an OPTIONAL "readable-article" upgrade lane that
uses trafilatura/readability IF installed and otherwise falls back to the stdlib extractor (reported via
``engine_used``). Secrets are redacted; every result is candidate-only and structured; nothing raises.

    python3 browser_control/ingestion_self_test.py --self-test   # offline, mutation-gated
"""
from __future__ import annotations

import sys
from pathlib import Path

_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install  # noqa: E402

_install()

import importlib.util  # noqa: E402
from html import unescape as _unescape  # noqa: E402
from html.parser import HTMLParser  # noqa: E402
from typing import Any, Optional  # noqa: E402

from scripts.primitive_browser_control_harness import (  # noqa: E402  single source — never re-implement
    BOUNDARY,
    browser_extract_forms,
    browser_extract_links,
    browser_extract_readable_text,
    redact_secrets,
)

from browser_control.adapter import extract_tables_from_html  # noqa: E402  single stdlib <table> extractor

#: optional parsing engines an operator MAY install for a better readable-article extraction (never required)
OPTIONAL_ENGINES: tuple[str, ...] = ("trafilatura", "readability", "bs4", "lxml", "selectolax", "parsel")
_META_TEXT_CAP = 4000


def _import_ok(module: str) -> bool:
    try:
        return importlib.util.find_spec(module) is not None
    except Exception:  # noqa: BLE001
        return False


class _MetaExtractor(HTMLParser):
    """One stdlib pass → <title>, <meta name/property>, <link rel=canonical>, <html lang>, heading counts."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.description = ""
        self.canonical = ""
        self.lang = ""
        self.open_graph: dict[str, str] = {}
        self.headings: dict[str, int] = {"h1": 0, "h2": 0, "h3": 0}
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, Optional[str]]]) -> None:
        a = {k.lower(): (v or "") for k, v in attrs}
        if tag == "title":
            self._in_title = True
        elif tag == "html" and a.get("lang"):
            self.lang = a["lang"].strip()
        elif tag == "meta":
            name = (a.get("name") or "").lower()
            prop = (a.get("property") or "").lower()
            content = a.get("content", "").strip()
            if name == "description" and not self.description:
                self.description = content
            if prop.startswith("og:") and content:
                self.open_graph.setdefault(prop, content)
        elif tag == "link" and (a.get("rel") or "").lower() == "canonical" and a.get("href"):
            self.canonical = a["href"].strip()
        elif tag in self.headings:
            self.headings[tag] += 1

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title += data


def _extract_metadata(html: str) -> dict[str, Any]:
    p = _MetaExtractor()
    try:
        p.feed(html or "")
    except Exception:  # noqa: BLE001 — malformed HTML never crashes extraction
        pass
    return {"title": _unescape(p.title).strip()[:_META_TEXT_CAP],
            "description": _unescape(p.description).strip()[:_META_TEXT_CAP],
            "canonical": p.canonical, "lang": p.lang,
            "open_graph": {k: _unescape(v)[:_META_TEXT_CAP] for k, v in p.open_graph.items()},
            "headings": dict(p.headings)}


class ParserAdapter:
    """Pure HTML → structured data (stdlib). Always ``supported``; every method returns a structured, redacted,
    candidate-only result and never raises. Optional engines upgrade only the readable-article path."""

    name = "parser"

    def available_engines(self) -> dict[str, bool]:
        """stdlib is always True; the rest report install-presence for the optional readable-article upgrade."""
        return {"stdlib": True, **{e: _import_ok(e) for e in OPTIONAL_ENGINES}}

    def capabilities(self) -> dict[str, Any]:
        return {"adapter": self.name, "read_only": True, "requires_network": False,
                "methods": ["extract_text", "extract_links", "extract_forms", "extract_tables",
                            "extract_metadata", "extract_readable", "parse"],
                "engines_available": self.available_engines(), **BOUNDARY}

    def extract_text(self, html: str, *, redact: bool = True) -> dict[str, Any]:
        text = browser_extract_readable_text(html or "")
        n = 0
        if redact:
            text, n = redact_secrets(text)
        return {"supported": True, "adapter": self.name, "text": text, "chars": len(text),
                "secrets_redacted": n, **BOUNDARY}

    def extract_links(self, html: str, base_url: str = "") -> dict[str, Any]:
        links = browser_extract_links(html or "", base_url)
        return {"supported": True, "adapter": self.name, "links": links, "n_links": len(links), **BOUNDARY}

    def extract_forms(self, html: str) -> dict[str, Any]:
        forms = browser_extract_forms(html or "")
        return {"supported": True, "adapter": self.name, "forms": forms, "n_forms": len(forms), **BOUNDARY}

    def extract_tables(self, html: str) -> dict[str, Any]:
        tables = extract_tables_from_html(html or "")
        return {"supported": True, "adapter": self.name, "tables": tables, "n_tables": len(tables), **BOUNDARY}

    def extract_metadata(self, html: str) -> dict[str, Any]:
        meta = _extract_metadata(html or "")
        clean_desc, n = redact_secrets(meta["description"])
        meta["description"] = clean_desc
        return {"supported": True, "adapter": self.name, **meta, "secrets_redacted": n, **BOUNDARY}

    def extract_readable(self, html: str, *, engine: str = "auto", url: str = "") -> dict[str, Any]:
        """Readable-article text. Uses trafilatura/readability if requested-and-present, else the stdlib
        extractor. Reports ``engine_used`` so the caller knows which lane produced the text. Never raises."""
        want = engine if engine != "auto" else next(
            (e for e in ("trafilatura", "readability") if _import_ok(e)), "stdlib")
        text, engine_used = "", "stdlib"
        try:
            if want == "trafilatura" and _import_ok("trafilatura"):
                import trafilatura  # lazy
                text = trafilatura.extract(html or "", url=url or None) or ""
                engine_used = "trafilatura"
            elif want == "readability" and _import_ok("readability"):
                from readability import Document  # lazy
                summary_html = Document(html or "").summary()
                text = browser_extract_readable_text(summary_html)
                engine_used = "readability"
        except Exception:  # noqa: BLE001 — any optional-engine failure falls back to stdlib, never raises
            text, engine_used = "", "stdlib"
        if not text:
            text, engine_used = browser_extract_readable_text(html or ""), "stdlib"
        clean, n = redact_secrets(text)
        return {"supported": True, "adapter": self.name, "text": clean, "chars": len(clean),
                "engine_used": engine_used, "secrets_redacted": n, **BOUNDARY}

    def parse(self, html: str, base_url: str = "") -> dict[str, Any]:
        """One structured record: text + links + forms + tables + metadata (each already redacted)."""
        html = html or ""
        text = self.extract_text(html)
        links = self.extract_links(html, base_url)
        forms = self.extract_forms(html)
        tables = self.extract_tables(html)
        meta = self.extract_metadata(html)
        return {"supported": True, "adapter": self.name, "metadata": {k: meta[k] for k in
                ("title", "description", "canonical", "lang", "open_graph", "headings")},
                "text": text["text"], "text_chars": text["chars"], "links": links["links"],
                "n_links": links["n_links"], "forms": forms["forms"], "n_forms": forms["n_forms"],
                "tables": tables["tables"], "n_tables": tables["n_tables"],
                "secrets_redacted": text["secrets_redacted"] + meta["secrets_redacted"], **BOUNDARY}


__all__ = ["ParserAdapter", "OPTIONAL_ENGINES"]
