#!/usr/bin/env python3
"""check_parser_portfolio — proof for the swappable parser portfolio (the parser-portfolio gap, 2026-06-18):

  1. ``schemas/ParsedDocument.schema.json`` is the canonical, engine-neutral parsed-document artifact — a
     valid JSON Schema; the adjudicator's output conforms; a parse that claims serves_truth=true or omits pages
     is REJECTED.
  2. ``parse_quality`` scores a parse deterministically (a clean parse beats a degraded one).
  3. ``parse_adjudicator`` runs N engines, selects the best, and PRESERVES every engine in engine_runs (lossless).
  4. The candidate engines (MinerU/Tika/MarkItDown/GROBID/OmniParse) sit behind the ParserProvider seam, each an
     HONEST seam (a labeled NotImplementedError surfacing install + license when absent — never a faked parse),
     with license + exec-needs in parser_status so adoption is a governed decision (discovery != trust).

CLI: python3 scripts/check_parser_portfolio.py --self-test
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _R not in sys.path:
        sys.path.insert(0, _R)

from jsonschema import Draft202012Validator

from scripts.ingest.parse_adjudicator import adjudicate
from scripts.ingest.parse_quality import score_parse
from scripts.ingest.parser_provider import _CANDIDATE_ENGINES, KNOWN_PARSERS, get_parser, parser_status
from scripts.ingest.document_decompose import ParserProvider

_REPO = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_SCHEMA_PATH = _REPO / "schemas" / "ParsedDocument.schema.json"

_CLEAN = {"document": {"title": "Policy"}, "pages": [{"page_no": 1, "blocks": [
    {"kind": "heading", "ordinal": 0, "text": "Retention", "confidence": 0.95},
    {"kind": "paragraph", "ordinal": 1, "text": "365 days.", "confidence": 0.93}]}]}
_DEGRADED = {"pages": [{"page_no": 1, "blocks": [
    {"kind": "paragraph", "ordinal": 1, "text": "", "confidence": 0.4},
    {"kind": "heading", "ordinal": 0, "text": "x", "confidence": 0.4}]}, {"page_no": 2, "blocks": []}]}


def _self_test() -> int:
    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    # 1. the canonical schema is valid + the adjudicator output conforms + bad instances are rejected.
    schema = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    ck("ParsedDocument is a valid JSON Schema", True)
    validator = Draft202012Validator(schema)

    out = adjudicate([{"engine": "docling", "parsed": _CLEAN}, {"engine": "mineru", "parsed": _DEGRADED}])
    ck("the adjudicator output conforms to ParsedDocument",
       validator.is_valid(out), str([e.message for e in validator.iter_errors(out)][:2]))
    ck("a parse claiming serves_truth=true is REJECTED by the schema", not validator.is_valid({**out, "serves_truth": True}))
    ck("a parse missing pages is REJECTED by the schema", not validator.is_valid({k: v for k, v in out.items() if k != "pages"}))

    # 2. quality worker ranks parses deterministically.
    ck("parse_quality scores a clean parse strictly above a degraded one",
       score_parse(_CLEAN)["overall"] > score_parse(_DEGRADED)["overall"])
    ck("parse_quality is deterministic", score_parse(_CLEAN) == score_parse(_CLEAN))

    # 3. adjudicator selects the best + is lossless.
    selected = [r for r in out["engine_runs"] if r["selected"]]
    ck("adjudicator selects EXACTLY ONE engine (the higher-quality docling)",
       len(selected) == 1 and selected[0]["engine"] == "docling")
    ck("adjudicator is LOSSLESS: every engine is preserved in engine_runs",
       {r["engine"] for r in out["engine_runs"]} == {"docling", "mineru"})
    ck("the parse never serves truth", out["serves_truth"] is False)

    # 4. the candidate engine catalog: behind the seam, honest, license-gated.
    ck("KNOWN_PARSERS carries the offline + verified + candidate engines",
       {"canned", "docling"} <= set(KNOWN_PARSERS) and all(c in KNOWN_PARSERS for c in _CANDIDATE_ENGINES))
    ck("there are >=5 candidate engines cataloged (MinerU/Tika/MarkItDown/GROBID/OmniParse)", len(_CANDIDATE_ENGINES) >= 5)
    for cand in _CANDIDATE_ENGINES:
        st = parser_status()[cand]
        ck(f"candidate {cand} surfaces license + exec-needs + availability (governed adoption)",
           bool(st.get("license")) and bool(st.get("exec_needs")) and "available" in st)
        parser = get_parser(cand)
        ck(f"candidate {cand} satisfies the ParserProvider seam", isinstance(parser, ParserProvider))
        if importlib.util.find_spec(_CANDIDATE_ENGINES[cand]["package"]) is None:
            honest = False
            try:
                parser.parse("x.pdf")
            except NotImplementedError as exc:
                honest = "license" in str(exc).lower() and _CANDIDATE_ENGINES[cand]["install"] in str(exc)
            ck(f"candidate {cand} is an HONEST seam when absent (labeled, license-surfaced, never faked)", honest)
    # OmniParse specifically must carry its license gate (GPL + non-commercial weight threshold).
    ck("OmniParse carries its license gate (GPL / non-commercial weight threshold)",
       "GPL" in _CANDIDATE_ENGINES["omniparse"]["license"])

    print("\n" + ("PASS — check_parser_portfolio: ParsedDocument is the canonical engine-neutral artifact "
                  "(valid schema; serves_truth=true / missing-pages rejected); parse_quality ranks parses "
                  "deterministically; the adjudicator selects the best engine and PRESERVES the losers (lossless); "
                  "and 5 candidate engines sit behind the ParserProvider seam as honest, license-gated seams."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(_self_test() if "--self-test" in sys.argv else 0)
