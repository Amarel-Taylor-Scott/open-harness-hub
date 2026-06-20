#!/usr/bin/env python3
"""scripts.parser_router — pick a parser by document signal (the Parser Manager's routing brain).

Decides WHICH verified parser to run for a document, given cheap signals (scanned? table density?
local-only? complex layout?). The chosen parser is then instantiated behind the `ParserProvider`
port (scripts/parser_provider.py) and benchmarked via OmniDocBench (docs/evals/parser-benchmark.md);
routing recommendations are refined from ToolEvidenceCards. This module only DECIDES — it never
parses (the byte-parse is the ParserProvider seam) — so it is deterministic + offline.

Verified parser set (research/backend-tool-verification.md): Docling (primary, local, broad),
Unstructured (fallback), LiteParse (fast local + bbox), Marker (table/equation-strong),
MinerU (scanned/scientific-strong), plus an OCR pipeline for image-only PDFs.

CLI:
    python3 scripts/parser_router.py --self-test
    python3 scripts/parser_router.py --scanned --table-density high
"""
from __future__ import annotations

import argparse

#: Verified parser ids the router may choose (no flagged/unverified tools).
KNOWN_PARSERS = ("docling", "unstructured", "liteparse", "marker", "mineru", "ocr-pipeline")


def route(*, scanned: bool = False, table_density: str = "low", local_only: bool = False,
          layout_complex: bool = False) -> dict:
    """Return {parser, reason, fallbacks} for a document signal. Deterministic; priority order:
    scanned → table-heavy → local-only → complex-layout → default."""
    if scanned:
        return {"parser": "mineru", "reason": "scanned/image PDF → OCR-capable parser",
                "fallbacks": ["ocr-pipeline", "docling"]}
    if table_density == "high":
        return {"parser": "marker", "reason": "table/equation-heavy → structure-strong parser",
                "fallbacks": ["mineru", "docling"]}
    if local_only:
        return {"parser": "docling", "reason": "local-only/no-cloud → local OSS parser",
                "fallbacks": ["liteparse", "unstructured"]}
    if layout_complex:
        return {"parser": "docling", "reason": "complex layout → AI layout/table models",
                "fallbacks": ["mineru", "unstructured"]}
    return {"parser": "docling", "reason": "default → broad-coverage local OSS parser",
            "fallbacks": ["unstructured"]}


def _self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    cases = [
        ("scanned → OCR-capable", route(scanned=True), "mineru"),
        ("table-heavy → marker", route(table_density="high"), "marker"),
        ("local-only → docling", route(local_only=True), "docling"),
        ("complex layout → docling", route(layout_complex=True), "docling"),
        ("default → docling", route(), "docling"),
    ]
    for name, res, expected in cases:
        check(name, res["parser"] == expected, str(res))
        check(f"  {name}: chosen parser is verified", res["parser"] in KNOWN_PARSERS)
        check(f"  {name}: all fallbacks verified", all(f in KNOWN_PARSERS for f in res["fallbacks"]))

    # priority: scanned beats table-heavy
    check("scanned outranks table-heavy", route(scanned=True, table_density="high")["parser"] == "mineru")
    # determinism
    check("route is deterministic", route(table_density="high") == route(table_density="high"))
    # no flagged/unverified parser can ever be returned (Dolphin etc. are benchmark-only, not routed yet)
    check("no flagged tool routed", all(route(**kw)["parser"] in KNOWN_PARSERS for kw in
          [{}, {"scanned": True}, {"table_density": "high"}, {"local_only": True}, {"layout_complex": True}]))

    print(f"\n{'all parser_router self-tests passed.' if not failures else f'{len(failures)} FAILURES: {failures}'}")
    return 0 if not failures else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Pick a parser by document signal (Parser Manager routing).")
    p.add_argument("--self-test", action="store_true")
    p.add_argument("--scanned", action="store_true")
    p.add_argument("--table-density", default="low", choices=["low", "medium", "high"])
    p.add_argument("--local-only", action="store_true")
    p.add_argument("--layout-complex", action="store_true")
    args = p.parse_args(argv)
    if args.self_test:
        return _self_test()
    import json
    print(json.dumps(route(scanned=args.scanned, table_density=args.table_density,
                           local_only=args.local_only, layout_complex=args.layout_complex), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
