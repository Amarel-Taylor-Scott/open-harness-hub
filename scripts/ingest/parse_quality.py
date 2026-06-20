#!/usr/bin/env python3
"""scripts.ingest.parse_quality — DETERMINISTIC parse-quality scoring for a ParsedDocument.

A parse that "ran" is not the same as a parse SAFE to feed into claim extraction. This worker scores a parsed
document (the ``{"pages":[{"page_no","blocks":[...]}]}`` shape) on text/page coverage, reading-order
monotonicity, table fidelity, and mean block confidence, and emits the ``ParsedDocument.v1`` ``quality`` block
plus human-readable warnings. It RANKS a parse; it is NEVER a served fact (no truth path). Pure + deterministic:
the same parse always yields the same scores. stdlib only.

CLI: python3 scripts/ingest/parse_quality.py --self-test
"""
from __future__ import annotations

import argparse
import os
import sys

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if _R not in sys.path:
        sys.path.insert(0, _R)

from scripts.ingest.document_decompose import KIND_TABLE, TEXT_KINDS

_ROUND = 4
#: composite weights (sum to 1.0) — coverage dominates, confidence tempers. Named so the blend is not a magic literal.
_WEIGHTS = {"text_coverage": 0.30, "page_coverage": 0.25, "reading_order_score": 0.20,
            "table_fidelity": 0.15, "avg_confidence": 0.10}
_LOW_TEXT_COVERAGE = 0.9  # below this, a warning is emitted (likely OCR/parse gaps)


def _has_content(block: dict) -> bool:
    return bool(str(block.get("text", "")).strip()) or bool(str(block.get("artifact_uri", "")).strip())


def score_parse(parsed: dict) -> dict:
    """Score a ParsedDocument's parse quality → the ``quality`` block (deterministic). RANKS, never serves truth."""
    pages = parsed.get("pages", []) or []
    all_blocks = [b for p in pages for b in (p.get("blocks") or [])]
    warnings: list[str] = []

    # page_coverage: a page with zero blocks is a parse gap.
    pages_with_blocks = sum(1 for p in pages if (p.get("blocks") or []))
    page_coverage = pages_with_blocks / len(pages) if pages else 0.0
    for p in pages:
        if not (p.get("blocks") or []):
            warnings.append(f"page {p.get('page_no')} has no blocks")

    # text_coverage: of TEXT-bearing blocks (TEXT_KINDS — paragraph/heading/cell/equation/ocr_span), the
    # fraction carrying non-empty text. Containers (table) + artifacts (figure) are not text-bearing.
    text_blocks = [b for b in all_blocks if b.get("kind") in TEXT_KINDS]
    text_with = sum(1 for b in text_blocks if str(b.get("text", "")).strip())
    text_coverage = text_with / len(text_blocks) if text_blocks else (1.0 if all_blocks else 0.0)
    if text_blocks and text_coverage < _LOW_TEXT_COVERAGE:
        warnings.append(f"low text coverage: {text_with}/{len(text_blocks)} text blocks carry text")

    # reading_order_score: per page, ordinals must be non-decreasing — scrambled order is a parser defect.
    ok_pages = 0
    for p in pages:
        blocks = p.get("blocks") or []
        ords = [int(b.get("ordinal", i)) for i, b in enumerate(blocks)]
        if ords == sorted(ords):
            ok_pages += 1
        else:
            warnings.append(f"reading order non-monotonic on page {p.get('page_no')}")
    reading_order_score = ok_pages / len(pages) if pages else 0.0

    # table_fidelity: of table blocks, the fraction with content — an empty table is lost structure.
    tables = [b for b in all_blocks if b.get("kind") == KIND_TABLE]
    empty_tables = sum(1 for b in tables if not _has_content(b))
    table_fidelity = (len(tables) - empty_tables) / len(tables) if tables else 1.0
    if empty_tables:
        warnings.append(f"{empty_tables} of {len(tables)} tables parsed empty")

    confs = [float(b.get("confidence", 0.0)) for b in all_blocks]
    avg_confidence = sum(confs) / len(confs) if confs else 0.0

    metrics = {"text_coverage": text_coverage, "page_coverage": page_coverage,
               "reading_order_score": reading_order_score, "table_fidelity": table_fidelity,
               "avg_confidence": avg_confidence}
    overall = sum(_WEIGHTS[k] * metrics[k] for k in _WEIGHTS)
    return {**{k: round(v, _ROUND) for k, v in metrics.items()},
            "overall": round(overall, _ROUND), "block_count": len(all_blocks), "warnings": warnings,
            "serves_truth": False}


def _self_test() -> int:
    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    clean = {"pages": [{"page_no": 1, "blocks": [
        {"kind": "heading", "ordinal": 0, "text": "Audit Retention", "confidence": 0.95},
        {"kind": "paragraph", "ordinal": 1, "text": "Logs are retained for 365 days.", "confidence": 0.92},
        {"kind": "table", "ordinal": 2, "artifact_uri": "s3://t/1.csv", "confidence": 0.8}]}]}
    q = score_parse(clean)
    ck("a clean parse scores high overall with no warnings", q["overall"] >= 0.9 and not q["warnings"], str(q))
    ck("clean parse is full coverage", q["text_coverage"] == 1.0 and q["page_coverage"] == 1.0 and q["table_fidelity"] == 1.0)
    ck("quality is evidence, not served truth", q["serves_truth"] is False)

    degraded = {"pages": [
        {"page_no": 1, "blocks": [
            {"kind": "paragraph", "ordinal": 1, "text": "", "confidence": 0.4},          # missing text (OCR gap)
            {"kind": "heading", "ordinal": 0, "text": "Title", "confidence": 0.5},        # ordinal out of order
            {"kind": "table", "ordinal": 2, "confidence": 0.3}]},                          # empty table
        {"page_no": 2, "blocks": []}]}                                                     # blank page
    dq = score_parse(degraded)
    ck("a degraded parse scores lower than the clean parse", dq["overall"] < q["overall"], f"{dq['overall']} vs {q['overall']}")
    ck("degraded parse flags the blank page", any("page 2 has no blocks" in w for w in dq["warnings"]), str(dq["warnings"]))
    ck("degraded parse flags non-monotonic reading order", any("non-monotonic" in w for w in dq["warnings"]))
    ck("degraded parse flags the empty table", any("parsed empty" in w for w in dq["warnings"]))
    ck("degraded parse flags low text coverage", any("low text coverage" in w for w in dq["warnings"]))

    ck("scoring is deterministic (same parse → same scores)", score_parse(clean) == score_parse(clean))

    print("\n" + ("PASS — parse_quality: a parse is scored deterministically on coverage/reading-order/table-"
                  "fidelity/confidence; gaps (blank page, scrambled order, empty table, missing text) lower the "
                  "score AND raise explicit warnings; the score ranks a parse and never serves truth."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Deterministic parse-quality scorer for a ParsedDocument.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
