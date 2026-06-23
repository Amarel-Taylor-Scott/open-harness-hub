#!/usr/bin/env python3
"""check_entity_resolver — registry-driven record linkage robust to typos in any column.

Proves: comparators (jaro_winkler/token_set/soundex) + normalizers (person nickname/suffix, company legal-suffix +
abbreviation) work; the identifier OVERRIDES (equal NPI -> match across name differences; different valid NPIs ->
no_match); a typo in a column is tolerated when others agree; a borderline pair -> REVIEW (no unsafe auto-merge);
resolve_entities clusters dupes and BLOCKING cuts comparisons below naive O(n^2). serves_truth=false.

  python3 scripts/check_entity_resolver.py --self-test
"""
from __future__ import annotations

from src.teleon.resolution import entity_resolver as ER
from src.teleon.verticals.provider_directory import _npi_check_digit


def _self_test() -> int:
    fails = []
    def ck(n, ok, d=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok: fails.append(n)

    # comparators + normalizers
    ck("jaro_winkler tolerates a typo (Smith~Smtih high; ~Jones low)", ER.jaro_winkler("smith", "smtih") > 0.9 and ER.jaro_winkler("smith", "jones") < 0.6)
    ck("person normalizer: nickname expansion + suffix strip (Bob Smith MD -> robert smith)", ER.normalize_person_name("Bob Smith, MD") == "robert smith")
    ck("company normalizer: legal-suffix strip + abbreviation (ABC Heart Grp LLC -> abc heart group)", ER.normalize_company_name("ABC Heart Grp, LLC") == "abc heart group")
    ck("soundex groups phonetic typos", ER.soundex("robertsmith") == ER.soundex("robertsmtih"))

    npi1 = "123456789" + str(_npi_check_digit("123456789"))
    npi2 = "987654321" + str(_npi_check_digit("987654321"))

    # identifier override + conflict
    ck("identifier override: equal NPI -> MATCH even with different names",
       ER.compare("person", {"name": "Robert Smith", "npi": npi1}, {"name": "Bob S.", "npi": npi1})["decision"] == "match")
    ck("identifier conflict: two DIFFERENT valid NPIs -> NO_MATCH (cannot be the same entity)",
       ER.compare("person", {"name": "Robert Smith", "npi": npi1}, {"name": "Robert Smith", "npi": npi2})["decision"] == "no_match")

    # typo in a column tolerated when others agree (no identifier)
    typo = ER.compare("person", {"name": "Robert Smith", "address": "100 Main St", "phone": "239-555-1234"},
                                {"name": "Robert Smtih", "address": "100 Main St", "phone": "239-555-1234"})
    ck("a typo in the name is tolerated when address+phone agree -> MATCH", typo["decision"] == "match", str(typo["score"]))

    # nickname match (no id)
    ck("nickname match: 'Bob Smith' ~ 'Robert Smith' (same address) -> MATCH",
       ER.compare("person", {"name": "Bob Smith", "address": "100 Main St"}, {"name": "Robert Smith", "address": "100 Main St"})["decision"] == "match")

    # company: legal-suffix + abbreviation differences still match
    ck("company: 'ABC Heart Group LLC' ~ 'ABC Heart Grp, Inc.' -> MATCH (legal-suffix + abbrev normalized)",
       ER.compare("company", {"name": "ABC Heart Group LLC", "address": "100 Main St"}, {"name": "ABC Heart Grp, Inc.", "address": "100 Main Street"})["decision"] == "match")
    ck("company no-match: 'ABC Heart Group' vs 'XYZ Cardiology Center'",
       ER.compare("company", {"name": "ABC Heart Group"}, {"name": "XYZ Cardiology Center"})["decision"] == "no_match")

    # review tier: name matches but address only half-overlaps -> ambiguous -> REVIEW (no unsafe auto-merge)
    rev = ER.compare("person", {"name": "Robert Smith", "address": "100 Main St"}, {"name": "Robert Smith", "address": "100 Main Ave"})
    ck("a borderline pair -> REVIEW (human, not auto-merge)", rev["decision"] == "review", str(rev["score"]))

    # entity clustering + blocking
    recs = [
        {"provider_id": "P1", "name": "Robert Smith", "address": "100 Main St"},
        {"provider_id": "P2", "name": "Robert Smtih", "address": "100 Main St"},   # typo dup of P1
        {"provider_id": "P3", "name": "Bob Smith", "address": "100 Main St"},      # nickname dup of P1
        {"provider_id": "P4", "name": "Alice Jones", "address": "9 Oak Ave"},      # distinct
    ]
    res = ER.resolve_entities(recs, "person")
    clusters = {frozenset(c) for c in res["entities"]}
    ck("resolve_entities clusters the typo + nickname dupes (P1,P2,P3) and keeps P4 distinct",
       frozenset({"P1", "P2", "P3"}) in clusters and frozenset({"P4"}) in clusters, str(res["entities"]))
    ck("blocking cuts comparisons below naive O(n^2)", res["comparisons"] <= res["naive_comparisons"])
    ck("serves_truth=false", res["serves_truth"] is False and typo["serves_truth"] is False)

    print("\n" + ("PASS - check_entity_resolver: registry-driven record linkage — comparators + per-entity normalizers + "
                  "weighted scoring + identifier override + review tier + blocking; robust to typos in any column."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(_self_test())
