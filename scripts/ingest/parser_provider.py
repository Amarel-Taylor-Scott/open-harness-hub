#!/usr/bin/env python3
"""scripts.ingest.parser_provider — the swappable Parser Manager (real adapter behind a seam).

`document_decompose` owns the contract (raw → recursive object tree) and ships the offline
`CannedParser`. This module adds the **real, swappable byte-parse adapter** so the heavy parsing
is pluggable infra, not baked in: a `DoclingParser` that converts a file with Docling (the
verified primary parser — `research/backend-tool-verification.md`) into the exact
`{"pages": [{"page_no", "blocks": [...]}]}` shape `decompose()` consumes.

Real-or-labeled-SEAM: Docling is a heavy optional dependency, so `DoclingParser.parse` lazily
imports it and, when absent (as in this stdlib-only env), raises a clear seam error naming the
install — it never fakes a parse. `parser_status()` reports what's available; `get_parser()` is
the factory the decomposition pipeline calls. Domain code depends on the `ParserProvider`
capability, never on Docling directly — swap in LiteParse/Unstructured behind the same interface.

Offline + deterministic self-test (proves the protocol + the factory + the honest seam).
Stdlib only (Docling is imported lazily, only on the live path).

CLI:
    python3 scripts/ingest/parser_provider.py --self-test
    python3 scripts/ingest/parser_provider.py --status
"""
from __future__ import annotations

import argparse
import importlib.util
from typing import Any

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    import os
    import sys

    _REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if _REPO_ROOT not in sys.path:
        sys.path.insert(0, _REPO_ROOT)

from scripts.ingest.document_decompose import CannedParser, ParserProvider

#: Registry of known parser adapters → the Baltor-verified backend (research/backend-tool-verification.md).
#: primary Docling; LiteParse/Unstructured are fallbacks (not yet wired — declared, not faked).
KNOWN_PARSERS = ("canned", "docling")
_DOCLING_INSTALL = "pip install docling"


def _docling_available() -> bool:
    return importlib.util.find_spec("docling") is not None


class DoclingParser:
    """Real `ParserProvider` backed by Docling. Lazily imports docling; if absent, raises a
    labeled seam (never fakes). ``parse(raw)`` takes a file path and returns the decompose shape."""

    name = "docling"

    def parse(self, raw: Any) -> dict:
        if not _docling_available():
            raise NotImplementedError(
                f"DoclingParser is a live SEAM: the 'docling' package is not installed "
                f"({_DOCLING_INSTALL}). The contract + offline path are proven via CannedParser; "
                f"this adapter runs in a dependency-permitted environment."
            )
        # ── Live path (only when docling is installed) — the byte-parse seam, mapped to the
        #    decompose shape. Best-effort mapping of a DoclingDocument's page items → blocks. ──
        from docling.document_converter import DocumentConverter  # pragma: no cover - optional dep

        doc = DocumentConverter().convert(str(raw)).document  # pragma: no cover
        pages: dict[int, list[dict]] = {}                      # pragma: no cover
        for ordinal, item in enumerate(getattr(doc, "texts", []) or []):  # pragma: no cover
            prov = (getattr(item, "prov", None) or [None])[0]
            page_no = int(getattr(prov, "page_no", 1) or 1)
            label = str(getattr(item, "label", "") or "").lower()
            kind = {"section_header": "heading", "title": "heading", "table": "table"}.get(label, "paragraph")
            pages.setdefault(page_no, []).append(
                {"kind": kind, "ordinal": ordinal, "text": getattr(item, "text", "") or "", "confidence": 1.0}
            )
        return {"pages": [{"page_no": p, "blocks": pages[p]} for p in sorted(pages)]}  # pragma: no cover


def get_parser(name: str, *, fixture: dict | None = None) -> ParserProvider:
    """Factory: return a parser adapter by name. ``canned`` needs a ``fixture`` (the offline path)."""
    if name == "canned":
        if fixture is None:
            raise ValueError("the 'canned' parser requires a fixture={'pages': [...]} mapping")
        return CannedParser(fixture)
    if name == "docling":
        return DoclingParser()
    raise KeyError(f"unknown parser {name!r}; known: {KNOWN_PARSERS}")


def parser_status() -> dict[str, Any]:
    """Which parsers are usable here (the offline 'canned' always; 'docling' only if installed)."""
    return {"canned": {"available": True, "kind": "offline-fixture"},
            "docling": {"available": _docling_available(), "kind": "live-byte-parse",
                        "install": None if _docling_available() else _DOCLING_INSTALL}}


def _self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    # CannedParser satisfies the runtime-checkable ParserProvider protocol.
    canned = get_parser("canned", fixture={"pages": [{"page_no": 1, "blocks": []}]})
    check("CannedParser satisfies ParserProvider", isinstance(canned, ParserProvider))
    check("canned parse returns the decompose shape", canned.parse(None) == {"pages": [{"page_no": 1, "blocks": []}]})
    raised = False
    try:
        get_parser("canned")  # no fixture
    except ValueError:
        raised = True
    check("canned without fixture raises", raised)

    # DoclingParser also satisfies the protocol, and is an honest SEAM when docling is absent.
    docling = get_parser("docling")
    check("DoclingParser satisfies ParserProvider", isinstance(docling, ParserProvider))
    if _docling_available():
        check("docling reported available", parser_status()["docling"]["available"] is True)
    else:
        seam = False
        try:
            docling.parse("some.pdf")
        except NotImplementedError as e:
            seam = "docling" in str(e) and _DOCLING_INSTALL in str(e)
        check("docling absent → labeled seam raised (not faked)", seam)
        check("status reports docling unavailable + install hint",
              parser_status()["docling"] == {"available": False, "kind": "live-byte-parse", "install": _DOCLING_INSTALL})

    # unknown parser fails closed.
    raised = False
    try:
        get_parser("nope")
    except KeyError:
        raised = True
    check("unknown parser raises", raised)

    print(f"\n{'all parser_provider self-tests passed.' if not failures else f'{len(failures)} FAILURES: {failures}'}")
    return 0 if not failures else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Swappable Parser Manager (Docling adapter behind the ParserProvider seam).")
    p.add_argument("--self-test", action="store_true", help="offline, deterministic")
    p.add_argument("--status", action="store_true", help="report which parsers are available here")
    args = p.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.status:
        import json
        print(json.dumps(parser_status(), indent=2))
        return 0
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
