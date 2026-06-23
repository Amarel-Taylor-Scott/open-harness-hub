#!/usr/bin/env python3
"""check_provider_directory — the HealthLynked provider/practice directory freshness pipeline (governed, deterministic-first).

Proves: NPI Luhn validation; deterministic normalization (phone/address); NPI-exact + fuzzy matching; the cross-source
agreement confidence formula; multi-source agreement -> AUTO_UPDATE; conflicting sources -> HUMAN_REVIEW (safe);
honest-MISSING (a field no source reports is never fabricated); no-change detection; a telemetry-style cost-per-1000
estimate far below a naive always-LLM+review-everything baseline. serves_truth=false.

  python3 scripts/check_provider_directory.py --self-test
  python3 scripts/check_provider_directory.py --demo        # prints the HealthLynked example recommendations
"""
from __future__ import annotations

import json
import sys

from src.teleon.verticals import provider_directory as PD

# the HealthLynked example record (synthetic)
HL_001 = {"provider_id": "HL_001", "provider_name": "John Smith, MD", "npi": "1234567890", "specialty": "Cardiology",
          "practice_name": "ABC Heart Group", "address": "100 Main St, Naples, FL 34102", "phone": "239-555-1234",
          "website": "abcheart.com", "status": "active"}


def _valid_npi() -> str:
    base = "123456789"
    return base + str(PD._npi_check_digit(base))


def _self_test() -> int:
    fails = []
    def ck(n, ok, d=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok: fails.append(n)

    good = _valid_npi()
    ck("NPI Luhn validation: a valid check digit passes, a wrong one + non-10-digit fail",
       PD.validate_npi(good) and not PD.validate_npi(good[:9] + str((int(good[9]) + 1) % 10)) and not PD.validate_npi("123"))
    ck("normalize phone -> NNN-NNN-NNNN", PD.normalize_phone("(239) 555 9000") == "239-555-9000" and PD.normalize_phone("12395559000") == "239-555-9000")
    ck("normalize address (Drive->Dr, Suite->Ste, collapse ws)", PD.normalize_address("250 Health Park  Drive  Suite 3") == "250 Health Park Dr Ste 3")
    vrec = {**HL_001, "npi": good}   # a record with a VALID NPI
    ck("match: same VALID NPI -> npi_exact (certain); invalid/different NPI + similar name/addr -> fuzzy",
       PD.match_records(vrec, vrec)["method"] == "npi_exact"
       and PD.match_records(HL_001, {**HL_001, "npi": "0000000000"})["method"] in ("fuzzy", "ambiguous_needs_llm"))

    # confidence formula: 3 authoritative agreeing sources -> high conf, no conflict; 2 disagreeing -> conflict
    agree = PD.field_confidence("old", {"NPI Registry": "new", "Practice Website": "new", "State Medical Board": "new"})
    ck("confidence: multi-source agreement on a new value is high + no conflict + is a change", agree["confidence"] >= 0.9 and not agree["conflict"] and agree["change"])
    conflict = PD.field_confidence("old", {"NPI Registry": "addrX", "Practice Website": "addrY"})
    ck("confidence: sources disagree -> CONFLICT flagged", conflict["conflict"] is True)

    # AUTO_UPDATE: new address (3 sources) + new phone (2 sources) all agree
    obs_auto = {
        "NPI Registry": {"address": "250 Health Park Dr, Fort Myers, FL 33908", "phone": "239-555-9000"},
        "Practice Website": {"address": "250 Health Park Dr, Fort Myers, FL 33908", "phone": "239-555-9000"},
        "State Medical Board": {"address": "250 Health Park Dr, Fort Myers, FL 33908"},
    }
    rec = PD.resolve_record(HL_001, obs_auto)
    ck("AUTO_UPDATE: multi-source agreement on address+phone -> recommended_action=auto_update",
       rec["recommended_action"] == "auto_update" and rec["change_detected"], rec["recommended_action"])
    ck("the recommendation matches HealthLynked's format (changes w/ confidence + supporting_sources + audit trail)",
       {"field", "old_value", "new_value", "confidence_score", "supporting_sources"} <= set(rec["changes"][0]) and rec["audit_trail"])

    # HUMAN_REVIEW: NPI Registry vs Practice Website report DIFFERENT addresses
    obs_conflict = {"NPI Registry": {"address": "250 Health Park Dr, Fort Myers, FL 33908"},
                    "Practice Website": {"address": "900 Different Rd, Naples, FL 34102"}}
    rec2 = PD.resolve_record(HL_001, obs_conflict)
    ck("HUMAN_REVIEW: conflicting sources -> recommended_action=human_review (no unsafe auto-update)", rec2["recommended_action"] == "human_review", rec2["recommended_action"])

    # NO_CHANGE + honest-MISSING
    rec3 = PD.resolve_record(HL_001, {"NPI Registry": {"phone": "239-555-1234"}})   # source agrees with existing phone
    ck("NO_CHANGE when sources confirm the existing value", rec3["recommended_action"] == "no_change" and not rec3["change_detected"])
    ck("honest-MISSING: a field no source reports is never fabricated", all(c["field"] != "specialty" for c in PD.resolve_record(HL_001, obs_auto)["changes"]))

    cost = PD.cost_per_1000()
    ck("cost-per-1000 is far below a naive always-LLM + review-everything baseline", cost["total_usd_per_1000"] < cost["naive_baseline_usd_per_1000"] and cost["savings_pct_vs_naive"] > 90, str(cost["savings_pct_vs_naive"]))
    ck("serves_truth=false (proposals are candidates; verify gate + human review disposition truth)", rec["serves_truth"] is False)

    print("\n" + ("PASS - check_provider_directory: governed, deterministic-first directory freshness — NPI/normalize/match/"
                  "agreement at ~$0, LLM only on the residual, auto-update vs human-review by confidence, full audit trail."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def _demo() -> int:
    obs_auto = {"NPI Registry": {"address": "250 Health Park Dr, Fort Myers, FL 33908", "phone": "239-555-9000"},
                "Practice Website": {"address": "250 Health Park Dr, Fort Myers, FL 33908", "phone": "239-555-9000"},
                "State Medical Board": {"address": "250 Health Park Dr, Fort Myers, FL 33908"}}
    print("=== AUTO-UPDATE (multi-source agreement) ===")
    print(json.dumps(PD.resolve_record(HL_001, obs_auto), indent=2))
    print("\n=== HUMAN-REVIEW (conflicting sources) ===")
    print(json.dumps(PD.resolve_record(HL_001, {"NPI Registry": {"address": "250 Health Park Dr, Fort Myers, FL 33908"},
                                                "Practice Website": {"address": "900 Different Rd, Naples, FL 34102"}}), indent=2))
    print("\n=== COST PER 1,000 RECORDS (descent) ===")
    print(json.dumps(PD.cost_per_1000(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(_demo() if "--demo" in sys.argv else _self_test())
