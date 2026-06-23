#!/usr/bin/env python3
"""check_licensed_directory — ONE pipeline, hundreds of professions (the generalization beyond physicians).

Proves: many professions are registered (physician/lawyer/engineer/CPA/financial-advisor/…) and INSURANCE is excluded;
the identifier validator dispatches per profession (NPI Luhn for physicians, numeric for a CRD, alphanumeric for a bar#);
the SAME resolve pipeline serves a LAWYER and an ENGINEER by swapping only the source registry (auto_update on agreement,
human_review on conflict — using THAT profession's source authority); the source descent is free-registry-first per
profession. serves_truth=false.

  python3 scripts/check_licensed_directory.py --self-test
"""
from __future__ import annotations

from src.teleon.verticals import licensed_directory as LD


def _self_test() -> int:
    fails = []
    def ck(n, ok, d=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok: fails.append(n)

    profs = LD.professions()
    ck("many professions registered (physician/lawyer/pe_engineer/cpa/financial_advisor)",
       {"physician", "lawyer", "pe_engineer", "cpa", "financial_advisor"} <= set(profs) and len(profs) >= 12, str(len(profs)))
    ck("INSURANCE is excluded (non-compete)", LD.profession("insurance_agent") is None)

    # identifier validation dispatches per profession
    from src.teleon.verticals.provider_directory import _npi_check_digit
    valid_npi = "123456789" + str(_npi_check_digit("123456789"))
    ck("validator dispatch: NPI Luhn for physician, numeric for a CRD, alphanumeric for a bar#",
       LD.validate_identifier("physician", valid_npi) and not LD.validate_identifier("physician", "123")
       and LD.validate_identifier("financial_advisor", "1234567") and not LD.validate_identifier("financial_advisor", "ABC")
       and LD.validate_identifier("lawyer", "CA-284321"))

    # the SAME pipeline serves a LAWYER (swap the registry): State Bar + ABA agree on a new firm address -> auto_update
    lawyer = {"bar_number": "CA-284321", "name": "Jane Roe", "firm_name": "Roe LLP", "address": "1 Old Plaza", "status": "active"}
    lr = LD.resolve("lawyer", lawyer, {"State Bar": {"address": "9 New Tower"}, "ABA": {"address": "9 New Tower"}})
    ck("SAME pipeline, LAWYER vertical: State Bar + ABA agree -> auto_update (using the lawyer's source authority)",
       lr["recommended_action"] == "auto_update" and lr["profession"] == "lawyer", lr["recommended_action"])
    ck("the recommendation uses the lawyer's tracked fields + identifier validity", lr["identifier_valid"] is True and lr["changes"][0]["field"] == "address")

    # the SAME pipeline serves an ENGINEER: NCEES vs State PE Board propose DIFFERENT new addresses -> human_review
    eng = {"pe_license": "PE-99001", "name": "Sam Lee", "discipline": "Civil", "address": "1 Old Rd", "status": "active"}
    er = LD.resolve("pe_engineer", eng, {"NCEES": {"address": "9 A St"}, "State PE Board": {"address": "5 B Ave"}})
    ck("SAME pipeline, ENGINEER vertical: sources conflict on a proposed change -> human_review (no unsafe update)", er["recommended_action"] == "human_review", er["recommended_action"])

    ck("source descent is free-registry-first per profession (financial_advisor: FINRA/SEC free first)",
       LD.source_descent("financial_advisor")[0]["cost_tier"] == "free")
    ck("an unknown/excluded profession is an honest error (not a guess)", "error" in LD.resolve("insurance_agent", {}, {}))
    ck("serves_truth=false", lr["serves_truth"] is False)

    print("\n" + ("PASS - check_licensed_directory: one deterministic-first governed pipeline serves hundreds of licensed "
                  "professions — swap only the sources, identifier, and fields. Insurance excluded." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(_self_test())
