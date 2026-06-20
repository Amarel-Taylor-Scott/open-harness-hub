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

#: Candidate parser engines behind the SAME ParserProvider seam (declared, never faked). Each lazily imports its
#: package on the live path and raises a LABELED seam when absent, with license + exec-needs surfaced so adoption
#: is a governed decision (discovery != trust). From the parser-portfolio gap + the 2026-06-18 DeepRepo intake.
_CANDIDATE_ENGINES = {
    "mineru":     {"package": "magic_pdf",     "install": "pip install magic-pdf", "license": "AGPL-3.0 + model conditions", "exec_needs": "cpu/gpu; formula+table+OCR", "strength": "scientific / formula-heavy PDFs -> Markdown+JSON"},
    "tika":       {"package": "tika",          "install": "pip install tika (+ Java/Tika server)", "license": "Apache-2.0", "exec_needs": "JVM / Tika server", "strength": "broad MIME detection + text (1000+ types); low-fidelity fallback"},
    "markitdown": {"package": "markitdown",    "install": "pip install markitdown", "license": "MIT", "exec_needs": "cpu", "strength": "lightweight any->Markdown for LLM pipelines"},
    "grobid":     {"package": "grobid_client", "install": "pip install grobid-client-python (+ GROBID server)", "license": "Apache-2.0", "exec_needs": "GROBID server", "strength": "scientific papers -> structured TEI/XML (citations/sections)"},
    "omniparse":  {"package": "omniparse",     "install": "github.com/adithya-s-k/omniparse (Docker)", "license": "GPL-3.0 (weights cc-by-nc-sa; non-commercial above a revenue threshold)", "exec_needs": "docker/gpu; documents+media+web", "strength": "multimodal: PDF/DOCX/PPTX/image/audio/video/web -> Markdown"},
}
#: Registry of known parser adapters: the offline CannedParser, the verified primary Docling, and the candidate
#: engines above — each a swappable ParserProvider, none faked.
KNOWN_PARSERS = ("canned", "docling", *_CANDIDATE_ENGINES)
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


class CandidateParser:
    """A CANDIDATE ParserProvider behind the same seam as Docling: lazily imports its package on the live path;
    when absent (as in this stdlib-only env) it raises a LABELED seam naming the install + license + exec-needs
    — it NEVER fakes a parse. Adopting it is a governed decision (discovery != trust)."""

    def __init__(self, name: str) -> None:
        if name not in _CANDIDATE_ENGINES:
            raise KeyError(f"unknown candidate engine {name!r}; known: {tuple(_CANDIDATE_ENGINES)}")
        self.name = name
        self._meta = _CANDIDATE_ENGINES[name]

    def _available(self) -> bool:
        return importlib.util.find_spec(self._meta["package"]) is not None

    def parse(self, raw: Any) -> dict:
        if not self._available():
            raise NotImplementedError(
                f"{self.name} is a CANDIDATE parser SEAM: package '{self._meta['package']}' is not installed "
                f"({self._meta['install']}). License: {self._meta['license']}; exec: {self._meta['exec_needs']}. "
                f"The contract is proven via CannedParser; adopting this adapter is a governed decision "
                f"(discovery != trust) — it never fakes a parse.")
        raise NotImplementedError(  # pragma: no cover - per-engine live mapping is future work
            f"{self.name} live byte-parse -> ParsedDocument mapping is not yet wired (candidate adapter).")


def get_parser(name: str, *, fixture: dict | None = None) -> ParserProvider:
    """Factory: return a parser adapter by name. ``canned`` needs a ``fixture`` (the offline path); the candidate
    engines (mineru/tika/markitdown/grobid/omniparse) return a labeled seam until their package is installed."""
    if name == "canned":
        if fixture is None:
            raise ValueError("the 'canned' parser requires a fixture={'pages': [...]} mapping")
        return CannedParser(fixture)
    if name == "docling":
        return DoclingParser()
    if name in _CANDIDATE_ENGINES:
        return CandidateParser(name)
    raise KeyError(f"unknown parser {name!r}; known: {KNOWN_PARSERS}")


def parser_status() -> dict[str, Any]:
    """Which parsers are usable here + the candidate engines' license/exec-needs (governed adoption metadata)."""
    status: dict[str, Any] = {"canned": {"available": True, "kind": "offline-fixture"},
                              "docling": {"available": _docling_available(), "kind": "live-byte-parse",
                                          "install": None if _docling_available() else _DOCLING_INSTALL}}
    for cand_name, meta in _CANDIDATE_ENGINES.items():
        avail = importlib.util.find_spec(meta["package"]) is not None
        status[cand_name] = {"available": avail, "kind": "candidate-byte-parse", "license": meta["license"],
                             "exec_needs": meta["exec_needs"], "strength": meta["strength"],
                             "install": None if avail else meta["install"]}
    return status


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

    # the candidate engines are honest seams too: absent package → labeled seam surfacing install + license.
    for cand in _CANDIDATE_ENGINES:
        cp = get_parser(cand)
        check(f"CandidateParser({cand}) satisfies ParserProvider", isinstance(cp, ParserProvider))
        if importlib.util.find_spec(_CANDIDATE_ENGINES[cand]["package"]) is None:
            seam = False
            try:
                cp.parse("some.pdf")
            except NotImplementedError as e:
                seam = (cand in str(e) and _CANDIDATE_ENGINES[cand]["install"] in str(e)
                        and "license" in str(e).lower())
            check(f"{cand} absent → labeled candidate seam (install + license surfaced, not faked)", seam)
    check("parser_status surfaces every candidate engine with license + exec-needs + availability",
          all(all(k in parser_status()[c] for k in ("license", "exec_needs", "available")) for c in _CANDIDATE_ENGINES))
    check("KNOWN_PARSERS includes all candidate engines", all(c in KNOWN_PARSERS for c in _CANDIDATE_ENGINES))

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
