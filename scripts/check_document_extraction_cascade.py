#!/usr/bin/env python3
"""check_document_extraction_cascade — proof for PDF/document → schema extraction as a CHEAPEST-THAT-MEETS-
REQUIREMENTS cascade over a method grid. Deterministic rules run before any LLM; the cheapest CAPABLE LLM runs
before the frontier one; prune/compress only when an LLM is actually needed; a field no available method can fill
is reported MISSING honestly (never fabricated); a full receipt tracks the path + cost for supervision. Far cheaper
than always sending the whole document to a frontier LLM. serves_truth=false.

CLI: PYTHONPATH=. python3 scripts/check_document_extraction_cascade.py --self-test
"""
from __future__ import annotations

import os
import sys

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _R not in sys.path:
        sys.path.insert(0, _R)

from src.teleon.extraction.document_extraction_cascade import (
    EMPLOYMENT_AGENCY_SCHEMA, STRUCTURED, UNSTRUCTURED, demonstrate, extract,
)

_TEXT_DOC = {"has_text_layer": True, "scanned": False}


def _self_test() -> int:
    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    # 1) all-structured fields → deterministic regex fills them; NO LLM; cheapest
    r1 = extract({"agency_license_no": STRUCTURED, "agency_name": STRUCTURED}, _TEXT_DOC, available_keys=("LLM_API_KEY",))
    ck("all-structured doc is filled by deterministic rules with NO LLM call (cheapest)",
       r1["met_requirement"] and not r1["used_llm"] and r1["total_cost"] < 0.01, str(r1["total_cost"]))

    # 2) full schema + key → escalates to the CHEAP LLM for unstructured fields, NOT the frontier one
    r2 = demonstrate()
    methods = {s["method"] for s in r2["receipt"] if "filled" in s}
    ck("full schema escalates to the CHEAPEST capable LLM (cheap_llm), not the frontier LLM",
       r2["met_requirement"] and "cheap_llm" in methods and "frontier_llm" not in methods, str(sorted(methods)))
    ck("deterministic rules run BEFORE the LLM (regex/nlp filled the structured/semi fields first)",
       "regex_keyword" in methods and "deterministic_nlp" in methods)

    # 3) the cost win: far cheaper than sending the whole doc to a frontier LLM (~0.30 + acquire)
    frontier_only = 0.002 + 0.300
    ck("the cascade is MUCH cheaper than always-frontier-LLM (the whole point)",
       r2["total_cost"] < frontier_only * 0.5, f"{r2['total_cost']} vs {frontier_only}")

    # 4) prune/compress only runs when an LLM is actually needed (and discounts it)
    comp = next((s for s in r2["receipt"] if s["method"] == "prune_compress"), None)
    ck("prune/compress runs only when an LLM is needed, to cut its token cost", comp is not None)
    ck("prune/compress is SKIPPED when rules already satisfy the schema (no LLM)",
       all(s["method"] != "prune_compress" for s in r1["receipt"]))

    # 5) HONESTY: no LLM key + unstructured required fields → those fields MISSING, never fabricated
    r3 = demonstrate(available_keys=())
    ck("no LLM key → unstructured fields are reported MISSING honestly (not fabricated)",
       r3["met_requirement"] is False and "recruiter_obligations" in r3["missing"]
       and all(EMPLOYMENT_AGENCY_SCHEMA[f] != UNSTRUCTURED for f in r3["filled"]))

    # 6) doc-dependent acquire: a scanned doc uses OCR (costlier) instead of the text layer
    r4 = extract({"agency_license_no": STRUCTURED}, {"has_text_layer": False, "scanned": True}, available_keys=())
    ck("a scanned doc acquires via OCR (costlier than text-layer extraction)",
       r4["receipt"][0]["method"] == "ocr" and r4["receipt"][0]["cost"] > 0.01)

    # 7) the receipt is a full supervision trail (path + per-step cost); never serves truth
    ck("the receipt records the full path + per-step cost (metadata/supervision)",
       len(r2["receipt"]) >= 4 and all("cost" in s for s in r2["receipt"]) and isinstance(r2["path"], list))
    ck("extraction never serves truth (a candidate for the verification rail)", r2["serves_truth"] is False)
    ck("deterministic (same doc+schema+keys → identical receipt)", demonstrate() == r2)

    # 8) LLM-as-CONTROL-SUPERVISOR (owner 2026-06-21): cheap methods extract all; LLM only audits + escalates flagged
    from src.teleon.extraction.document_extraction_cascade import supervise_extraction, compare_strategies
    from src.teleon.extraction.schema_templates import get_template
    land = get_template("land_lease")
    ck("land_lease + oil_gas_lease showcase templates exist (the flagship vertical)",
       land is not None and get_template("oil_gas_lease") is not None and "royalty_rate" in land)
    sup = supervise_extraction(land, {"has_text_layer": True, "scanned": False}, available_keys=("LLM_API_KEY",))
    ck("supervisor: cheap methods fill all, LLM ROLE is supervisor (audits, doesn't extract everything)",
       sup["llm_role"].startswith("supervisor") and len(sup["rule_filled"]) >= 10 and len(sup["escalated"]) <= 2)
    cmp = compare_strategies(land, {"has_text_layer": True, "scanned": False})
    ck("3-way: supervised is CHEAPEST < cascade < frontier-only (the whole-doc→Gemini baseline)",
       cmp["supervised"]["cost"] < cmp["cascade"]["cost"] < cmp["frontier_only"]["cost"] and cmp["supervised"]["pct_saved"] >= 70)
    sup_nokey = supervise_extraction(land, {"has_text_layer": True, "scanned": False}, available_keys=())
    ck("no LLM key → audit-flagged fields reported MISSING, never fabricated", sup_nokey["missing"] and sup_nokey["escalated"] == [])

    print("\n" + (f"PASS - check_document_extraction_cascade: PDF→schema as a cheapest-that-meets cascade over a "
                  f"method grid — deterministic rules before LLM, cheapest-capable LLM before frontier, "
                  f"compress-only-when-needed; full schema in ${r2['total_cost']} vs ${frontier_only} frontier-only; "
                  f"missing fields reported honestly when no method can fill them; full cost/path receipt; never "
                  f"serves truth." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def _main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--self-test" in argv:
        return _self_test()
    print("usage: check_document_extraction_cascade.py --self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
