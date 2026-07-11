#!/usr/bin/env python3
"""check_cascade_measurement — proof that the document cascade's 'cheapest-that-meets' is a MEASURED decision, not an
assumed one. Each extract method is scored against offline ground-truth fixtures (synthetic, no PII); per field the
cascade selects the cheapest method whose MEASURED accuracy clears the confidence floor. Raising the floor escalates
a field to a more expensive method (a live A/B that moves the cost); a field no available method can fill to the
floor is reported MISSING, never fabricated. The accuracy is COMPUTED from fixtures (recomputed independently here),
never a hardcoded table. serves_truth=false.

CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_cascade_measurement.py --self-test
"""
from __future__ import annotations

import os
import sys

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _R not in sys.path:
        sys.path.insert(0, _R)

from src.teleon.extraction.document_extraction_cascade import (
    EMPLOYMENT_AGENCY_SCHEMA, MEASUREMENT_FIXTURES, STRUCTURED, UNSTRUCTURED, _EXTRACTORS, _recover, _score,
    demonstrate_measured, extract_measured, measured_field_accuracy,
)


def _self_test() -> int:
    fails: list[str] = []

    def ck(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    doc = {"has_text_layer": True, "scanned": False}
    keys = ("LLM_API_KEY",)

    # 1) the accuracy is COMPUTED from fixtures — recompute it independently and require equality (no hidden table)
    field = "fee_terms"
    manual = [fx for fx in MEASUREMENT_FIXTURES if fx.field == field]
    recomputed = round(sum(_score(_recover("cheap_llm", fx, i), fx.truth, fx.field_class)
                           for i, fx in enumerate(manual)) / len(manual), 4)
    ck("measured accuracy is computed from fixtures (independent recompute matches the module)",
       recomputed == measured_field_accuracy("cheap_llm", field), f"{recomputed} vs {measured_field_accuracy('cheap_llm', field)}")
    ck("there are multiple fixtures per field (a real mean, not a single sample)", len(manual) >= 3)

    # 2) a measured partial score exists (cheap LLM on unstructured) and frontier is exact — the gap the floor exploits
    cheap_u = measured_field_accuracy("cheap_llm", field)
    front_u = measured_field_accuracy("frontier_llm", field)
    reg_u = measured_field_accuracy("regex_keyword", field)
    ck("cheap LLM scores PARTIAL on an unstructured field (measured, between 0 and 1)", 0.0 < cheap_u < 1.0, str(cheap_u))
    ck("frontier LLM scores exact on the same field", front_u == 1.0, str(front_u))
    ck("a regex cannot recover an unstructured field (measured 0.0)", reg_u == 0.0, str(reg_u))

    # 3) structured field → cheapest extractor (regex) meets an 0.8 floor; it IS the cheapest that meets
    res = extract_measured(EMPLOYMENT_AGENCY_SCHEMA, doc, available_keys=keys, confidence_floor=0.8)
    ck("structured fields are filled by the cheapest method (regex_keyword)",
       res["filled"]["agency_license_no"] == "regex_keyword" and res["field_scores"]["agency_license_no"] >= 0.8)

    # 4) cheapest-that-meets INVARIANT: every chosen method is the cheapest extractor whose measured score >= floor
    floor = 0.8
    inv_ok = True
    for f, chosen_method in res["filled"].items():
        order = [m.name for m in _EXTRACTORS]
        for m in _EXTRACTORS:
            if m.name == chosen_method:
                break
            acc = measured_field_accuracy(m.name, f)            # a strictly-cheaper extractor...
            if acc is not None and acc >= floor:                # ...must NOT also clear the floor
                inv_ok = False
        # and the chosen one clears it
        if res["field_scores"][f] < floor:
            inv_ok = False
    ck("cheapest-that-meets invariant holds for every filled field", inv_ok)

    # 5) the FLOOR is a live A/B — derive floors around the measured cheap score: just-below keeps cheap, just-above escalates
    floor_lo = round(cheap_u - 0.1, 4)
    floor_hi = round(cheap_u + 0.1, 4)
    lo = extract_measured(EMPLOYMENT_AGENCY_SCHEMA, doc, available_keys=keys, confidence_floor=floor_lo)
    hi = extract_measured(EMPLOYMENT_AGENCY_SCHEMA, doc, available_keys=keys, confidence_floor=floor_hi)
    ck("below the measured score the unstructured field uses the cheap LLM",
       lo["filled"][field] == "cheap_llm", lo["filled"].get(field, "?"))
    ck("above the measured score the SAME field escalates to the frontier LLM",
       hi["filled"][field] == "frontier_llm", hi["filled"].get(field, "?"))
    ck("escalation raises the total cost (paying more only to clear the higher bar)", hi["total_cost"] > lo["total_cost"],
       f"{hi['total_cost']} !> {lo['total_cost']}")
    ck("both still meet the requirement (frontier fills what cheap could not)",
       lo["met_requirement"] and hi["met_requirement"])

    # 6) honesty: with NO LLM key, unstructured fields cannot meet the floor → reported MISSING, never fabricated
    nokey = extract_measured(EMPLOYMENT_AGENCY_SCHEMA, doc, available_keys=(), confidence_floor=0.8)
    ck("without an LLM key the unstructured fields are MISSING (honest, not fabricated)",
       set(nokey["missing"]) == {"recruiter_obligations", "fee_terms"} and not nokey["met_requirement"], str(nokey["missing"]))
    ck("structured/semi fields are still filled deterministically without any key",
       nokey["filled"].get("agency_license_no") == "regex_keyword" and nokey["filled"].get("address") == "deterministic_nlp")

    # 7) the demo shows the A/B end to end (lenient vs strict floor moves the chosen tier and the cost)
    demo = demonstrate_measured()
    moved = [f for f, (a, b) in demo["escalation"].items() if a != b]
    ck("demonstrate_measured shows >=1 field escalating between the lenient and strict floor", len(moved) >= 1, str(moved))
    ck("the strict floor costs more than the lenient floor", demo["cost_delta"] > 0, str(demo["cost_delta"]))

    # 8) determinism + never serves truth
    ck("deterministic (same inputs → same output)",
       extract_measured(EMPLOYMENT_AGENCY_SCHEMA, doc, available_keys=keys, confidence_floor=0.8) == res)
    ck("never serves truth", res["serves_truth"] is False and nokey["serves_truth"] is False)

    print("\n" + (f"PASS - check_cascade_measurement: 'cheapest-that-meets' is MEASURED — every method scored against "
                  f"{len(MEASUREMENT_FIXTURES)} offline fixtures; per field the cascade takes the cheapest method whose "
                  f"measured accuracy clears the floor; the floor is a live A/B (cheap_llm below it, frontier above it, "
                  f"cost rises with the bar); missing fields are honest, never fabricated. serves_truth=false."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def _main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--self-test" in argv:
        return _self_test()
    print("usage: check_cascade_measurement.py --self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
