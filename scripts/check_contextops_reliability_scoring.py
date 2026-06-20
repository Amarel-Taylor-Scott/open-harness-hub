#!/usr/bin/env python3
"""scripts.check_contextops_reliability_scoring — proof (CONTEXTOPS RELIABILITY MODE): the source-reliability
scorer produces a deterministic SourceReliabilityScore that reconciliation can read, and the load-bearing
precedence holds: a source-of-law / regulation OUTRANKS an agency FAQ — a FAQ can never win on factors.

What it proves:
  * the Reg-E source-of-law / regulation source outranks a CFPB-FAQ source (authority dominates the composite);
  * a FAQ can NEVER outrank a regulation even when the FAQ's other factors are maxed (authority is decisive);
  * scores are deterministic — same candidate + same factors → same score_id + same overall, every run;
  * the factors block is closed: a missing factor or an unknown factor or an out-of-range value is REJECTED;
  * served_as_truth is pinned False (a reliability score ranks; it is never itself a served fact);
  * tenant_scope_ok is computed — a tenant_private source can't back a global fact;
  * the score serializes to the SourceReliabilityScore.v1 shape (closed factors block, all eight signals).

Deterministic, stdlib-only, offline (time injected). CLI: PYTHONPATH=. python3 scripts/check_contextops_reliability_scoring.py --self-test
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.baltor.contextops.reliability import (  # noqa: E402
    AUTHORITY_RANK,
    FACTOR_NAMES,
    ReliabilityError,
    SourceReliabilityScore,
    default_authority_rank,
    outranks,
    score_source,
)

_NOW = 1_700_000_000  # injected epoch seconds

#: a strong, official factor profile (Reg E source-of-law) and a maxed-out-but-FAQ profile (red-team).
_REG_FACTORS = {"officialness": 1.0, "freshness": 0.95, "stability": 0.98, "machine_readability": 0.8,
                "contradiction_rate": 0.0, "availability": 0.99, "parse_stability": 0.9, "historical_accuracy": 1.0}
_FAQ_MAXED = {"officialness": 1.0, "freshness": 1.0, "stability": 1.0, "machine_readability": 1.0,
              "contradiction_rate": 0.0, "availability": 1.0, "parse_stability": 1.0, "historical_accuracy": 1.0}
_FAQ_NORMAL = {"officialness": 0.5, "freshness": 0.7, "stability": 0.8, "machine_readability": 0.6,
               "contradiction_rate": 0.4, "availability": 0.98, "parse_stability": 0.7, "historical_accuracy": 0.6}


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    # ── 1) default authority ranks encode the precedence (source-of-law > regulation > FAQ). ──
    check("default authority: regulation outranks agency_faq",
          default_authority_rank("regulation") > default_authority_rank("agency_faq"))
    check("default authority: source_of_law is the top rank",
          default_authority_rank("source_of_law") == max(AUTHORITY_RANK.values()))
    check("an unknown source_type defaults to the lowest authority (0)", default_authority_rank("mystery") == 0)

    # ── 2) the CFPB reference: the Reg-E regulation source outranks the CFPB FAQ source. ──
    reg = score_source(candidate_id="scand-ecfr-1005-11", source_type="regulation", factors=_REG_FACTORS,
                       scored_at=_NOW)
    faq = score_source(candidate_id="scand-cfpb-faq", source_type="agency_faq", factors=_FAQ_NORMAL, scored_at=_NOW)
    check("Reg-E regulation authority_rank (90) > CFPB FAQ authority_rank (30)",
          reg.authority_rank == 90 and faq.authority_rank == 30)
    check("Reg-E regulation OUTRANKS the CFPB FAQ (reconciliation precedence)", outranks(reg, faq) is True)
    check("the FAQ does NOT outrank the regulation", outranks(faq, reg) is False)
    check("Reg-E composite (overall) is higher than the FAQ composite", reg.overall > faq.overall,
          f"{reg.overall} vs {faq.overall}")

    # ── 3) RED-TEAM: a FAQ with MAXED factors STILL cannot outrank a regulation (authority is decisive). ──
    faq_maxed = score_source(candidate_id="scand-cfpb-faq-maxed", source_type="agency_faq", factors=_FAQ_MAXED,
                             scored_at=_NOW)
    check("RED-TEAM: a FAQ with every factor maxed still has lower authority than a regulation",
          faq_maxed.authority_rank < reg.authority_rank)
    check("RED-TEAM: a maxed-factor FAQ STILL does not outrank the regulation (authority dominates)",
          outranks(faq_maxed, reg) is False and outranks(reg, faq_maxed) is True)

    # ── 4) deterministic: same candidate + same factors → same score_id + same overall, every run. ──
    reg2 = score_source(candidate_id="scand-ecfr-1005-11", source_type="regulation", factors=dict(_REG_FACTORS),
                        scored_at=_NOW + 12345)
    check("score_id is content-addressed + deterministic (same inputs → same id; time excluded)",
          reg.score_id == reg2.score_id and reg.score_id.startswith("srs-"))
    check("overall is deterministic (same inputs → same composite)", reg.overall == reg2.overall)
    # a different candidate/factor set → a different score_id.
    check("a different factor set → a different score_id",
          score_source(candidate_id="scand-ecfr-1005-11", source_type="regulation",
                       factors=_FAQ_NORMAL, scored_at=_NOW).score_id != reg.score_id)

    # ── 5) the factors block is closed — missing / unknown / out-of-range factors are REJECTED. ──
    missing = dict(_REG_FACTORS); missing.pop("historical_accuracy")
    rejected = False
    try:
        SourceReliabilityScore(candidate_id="c", tenant_id="acme", source_scope="global_public",
                               authority_rank=90, factors=missing, scored_at=_NOW)
    except ReliabilityError:
        rejected = True
    check("a score missing a required factor is REJECTED", rejected)

    unknown = dict(_REG_FACTORS); unknown["made_up_factor"] = 1.0
    rejected = False
    try:
        SourceReliabilityScore(candidate_id="c", tenant_id="acme", source_scope="global_public",
                               authority_rank=90, factors=unknown, scored_at=_NOW)
    except ReliabilityError:
        rejected = True
    check("a score with an UNKNOWN factor is REJECTED (the factor set can't silently drift)", rejected)

    oob = dict(_REG_FACTORS); oob["freshness"] = 1.5
    rejected = False
    try:
        SourceReliabilityScore(candidate_id="c", tenant_id="acme", source_scope="global_public",
                               authority_rank=90, factors=oob, scored_at=_NOW)
    except ReliabilityError:
        rejected = True
    check("a factor outside 0..1 is REJECTED", rejected)

    # ── 6) RED-TEAM: served_as_truth=True is REJECTED (a score ranks; it is never a served fact). ──
    rejected = False
    try:
        SourceReliabilityScore(candidate_id="c", tenant_id="acme", source_scope="global_public",
                               authority_rank=90, factors=_REG_FACTORS, scored_at=_NOW, served_as_truth=True)
    except ReliabilityError:
        rejected = True
    check("RED-TEAM: served_as_truth=True is REJECTED (a reliability score is never served truth)", rejected)
    check("a normal score pins served_as_truth False", reg.served_as_truth is False)

    # ── 7) tenant_scope_ok: a tenant_private source can't back a global fact. ──
    priv_global = score_source(candidate_id="tdoc", source_type="tenant_document", factors=_REG_FACTORS,
                               source_scope="tenant_private", fact_scope="global_public", scored_at=_NOW)
    priv_priv = score_source(candidate_id="tdoc", source_type="tenant_document", factors=_REG_FACTORS,
                             source_scope="tenant_private", fact_scope="tenant_private", scored_at=_NOW)
    check("a tenant_private source backing a GLOBAL fact → tenant_scope_ok False", priv_global.tenant_scope_ok is False)
    check("a tenant_private source backing a tenant_private fact → tenant_scope_ok True", priv_priv.tenant_scope_ok is True)

    # ── 8) the score serializes to the SourceReliabilityScore.v1 shape (all eight factors, composite, pinned flag). ──
    d = reg.to_dict()
    check("serialized score declares schema_version SourceReliabilityScore.v1",
          d.get("schema_version") == "SourceReliabilityScore.v1")
    check("serialized factors carry exactly the eight signals", set(d.get("factors", {})) == set(FACTOR_NAMES))
    check("serialized score carries composite_score + served_as_truth=false",
          "composite_score" in d and d.get("served_as_truth") is False)

    ok = not fails
    print(
        f"\n{'PASS — check_contextops_reliability_scoring: the scorer produces a deterministic SourceReliabilityScore reconciliation can read; a Reg-E regulation OUTRANKS a CFPB FAQ and a FAQ with maxed factors STILL cannot outrank a regulation (authority is decisive); scores are content-addressed + deterministic; the factors block is closed (missing/unknown/out-of-range REJECTED); served_as_truth is pinned False; a tenant_private source can not back a global fact (tenant_scope_ok); the score serializes to the .v1 shape with all eight factors.' if ok else f'{len(fails)} FAILURES: {fails}'}"
    )
    return 0 if ok else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: ContextOps source-reliability scoring (deterministic, FAQ < law).")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
