#!/usr/bin/env python3
"""scripts.check_contextops_triage — proof: the ContextTriageClassifier routes context into the 12 lanes
deterministically, the CFPB reference case classifies correctly, and a triage NEVER serves truth.

What this proves (the LEAN-CORE detection front end of the ContextOps loop):

  * each of the twelve ContextTriage lanes FIRES on a purpose-built fixture (the multi-label set), and the
    classifier's lane taxonomy is EXACTLY the contract's enum (single source — no drift);
  * the CFPB reference case — an agency FAQ "30 days" that conflicts with the Reg-E "10 business days" source of
    law — classifies as needs_reconciliation + is_low_authority + is_conflict_candidate (all three fire);
  * the load-bearing deterministic rules hold: a narrative_allegation can't become a verified fact without a
    stronger source (under_supported + needs_verification, never high_value_reusable); a model_interpretation
    requires source support; current/rate/fee/deadline claims are fragile; a FAQ ranks below a source of law;
    tenant_private context stays tenant-scoped (is_customer_private_override, never widened);
  * THE INVARIANT: every result pins serves_truth=False — a triage is a routing signal, NEVER a served fact;
  * determinism: identical inputs → byte-identical result + a content-addressed, clock-free triage_id;
  * the v1-shaped to_dict() VALIDATES against schemas/contextops/ContextTriageResult.schema.json and a
    serves_truth=true mutation is REJECTED by that schema (red-team at the contract layer).

Deterministic, stdlib-only, offline (no network, no RNG, no wall-clock).
CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_contextops_triage.py --self-test
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from scripts.runtime.schema_validator import validate as _validate  # noqa: E402
from src.baltor.contextops.triage import (  # noqa: E402
    CLAIM_ATOMIC_FACT,
    CLAIM_MODEL_INTERPRETATION,
    CLAIM_NARRATIVE_ALLEGATION,
    IS_CONFLICT_CANDIDATE,
    IS_CUSTOMER_PRIVATE_OVERRIDE,
    IS_FRAGILE,
    IS_HIGH_VALUE_REUSABLE_FACT,
    IS_LOW_AUTHORITY,
    IS_MISSING_SOURCE,
    IS_MODEL_INTERPRETATION,
    IS_STALE,
    IS_UNDER_SUPPORTED,
    NEEDS_ENRICHMENT,
    NEEDS_RECONCILIATION,
    NEEDS_VERIFICATION,
    SCOPE_TENANT_PRIVATE,
    TRIAGE_LANES,
    ContextTriageClassifier,
)

_SCHEMA = _resource("schemas") / "contextops" / "ContextTriageResult.schema.json"

# the twelve canonical lanes (single source for the proof — must equal TRIAGE_LANES AND the contract enum).
_EXPECTED_LANES = {
    "needs_reconciliation", "needs_verification", "needs_enrichment", "is_fragile", "is_stale",
    "is_low_authority", "is_under_supported", "is_conflict_candidate", "is_missing_source",
    "is_customer_private_override", "is_model_interpretation", "is_high_value_reusable_fact",
}

# a clean, source-grounded, source-of-law deadline is fragile-by-text but we strip the cue to land on a
# non-fragile reusable-fact fixture; for fragile we use a current-rate claim.
_HANDLE = "ctx://public/source/ecfr/12-CFR-1005.11#para.c.1.i"
_FAQ_HANDLE = "ctx://public/source/cfpb-faq/error-resolution#q12"
_NOW = "2026-06-05T00:00:00Z"


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    clf = ContextTriageClassifier()
    schema = __import__("json").loads(_SCHEMA.read_text())

    # ── the lane taxonomy is the single source and equals the contract enum ────────────────────────────
    check("TRIAGE_LANES is exactly the 12 canonical lanes",
          set(TRIAGE_LANES) == _EXPECTED_LANES, str(sorted(_EXPECTED_LANES ^ set(TRIAGE_LANES))))
    check("contract ContextTriageResult lane enum equals TRIAGE_LANES (no drift)",
          set(schema.get("properties", {}).get("lane", {}).get("enum", [])) == set(TRIAGE_LANES))

    # ── a fixture per lane — each fires, and every result validates + pins serves_truth=False ───────────
    # (fact_key, kwargs, the lane that MUST fire)
    fixtures: list[tuple[str, dict, str]] = [
        ("cfpb.deadline.missing_src",
         dict(claim_text="the bank must investigate within 10 business days", source_handle="",
              source_type="agency_faq"),
         IS_MISSING_SOURCE),
        ("acme.policy.override",
         dict(claim_text="our internal SLA is 5 days", source_handle="ctx://tenant/acme/policy#sla",
              source_scope=SCOPE_TENANT_PRIVATE, tenant_id="acme", source_type="tenant_policy"),
         IS_CUSTOMER_PRIVATE_OVERRIDE),
        ("complaint.42.allegation",
         dict(claim_text="the consumer alleges the charge was unauthorized", claim_type=CLAIM_NARRATIVE_ALLEGATION,
              source_handle="ctx://tenant/acme/complaint/42#narrative", source_type="complaint_form"),
         IS_UNDER_SUPPORTED),
        ("cfpb.summary.model_read",
         dict(claim_text="this appears to mean the bank is liable", claim_type=CLAIM_MODEL_INTERPRETATION,
              source_handle="ctx://model/interpretation#1", source_type="llm_summary"),
         IS_MODEL_INTERPRETATION),
        ("bank.savings.rate",
         dict(claim_text="the current APY rate is 4.5% as of today", source_handle="ctx://public/bank/rates#apy",
              source_type="vendor_doc"),
         IS_FRAGILE),
        ("cfpb.faq.deadline",
         dict(claim_text="the bank has time to investigate", source_handle=_FAQ_HANDLE,
              source_type="agency_faq", authority_rank=20),
         IS_LOW_AUTHORITY),
        ("cfpb.error_resolution.deadline.conflict",
         dict(claim_text="the bank has 30 days", source_handle=_FAQ_HANDLE, source_type="agency_faq",
              authority_rank=20, conflicts_with_value=True),
         IS_CONFLICT_CANDIDATE),
        ("cfpb.error_resolution.deadline.recon",
         dict(claim_text="the bank has 30 days", source_handle=_FAQ_HANDLE, source_type="agency_faq",
              authority_rank=20, conflicts_with_value=True),
         NEEDS_RECONCILIATION),
        ("cfpb.deadline.stale",
         dict(claim_text="the investigation deadline is fixed", source_handle=_HANDLE, source_type="regulation",
              authority_rank=90, last_verified_at=0, max_staleness_seconds=10, now_epoch=100),
         IS_STALE),
        ("cfpb.deadline.stale2",
         dict(claim_text="the investigation deadline is fixed", source_handle=_HANDLE, source_type="regulation",
              authority_rank=90, last_verified_at=0, max_staleness_seconds=10, now_epoch=100),
         NEEDS_VERIFICATION),
        ("cfpb.thin.context",
         dict(claim_text="error resolution applies", source_handle=_HANDLE, source_type="regulation",
              authority_rank=90, enrichment_hint=True),
         NEEDS_ENRICHMENT),
        ("cfpb.error_resolution.investigation_deadline",
         dict(claim_text="a financial institution shall complete its investigation in ten business segments",
              source_handle=_HANDLE, source_type="regulation", authority_rank=90, is_high_value=True,
              claim_type=CLAIM_ATOMIC_FACT),
         IS_HIGH_VALUE_REUSABLE_FACT),
    ]
    seen_lanes: set[str] = set()
    for fk, kw, expect in fixtures:
        res = clf.classify(fact_key=fk, now=_NOW, **kw)
        check(f"lane {expect!r} fires on its fixture ({fk})", res.fired(expect), f"got lanes={res.lanes}")
        seen_lanes.add(expect)
        check(f"{fk}: serves_truth pinned False (a triage is never a served fact)", res.serves_truth is False)
        errs = _validate(res.to_dict(), schema)
        check(f"{fk}: to_dict() validates against ContextTriageResult", errs == [], str(errs[:3]))
        check(f"{fk}: primary lane is one of the 12", res.lane in _EXPECTED_LANES, res.lane)

    check("every one of the 12 lanes was demonstrated by a fixture",
          seen_lanes == _EXPECTED_LANES, str(sorted(_EXPECTED_LANES - seen_lanes)))

    # ── the CFPB reference case: FAQ "30 days" conflicting with Reg-E "10 business days" source of law ─────
    cfpb = clf.classify(
        fact_key="cfpb.error_resolution.investigation_deadline",
        tenant_id="acme",
        claim_text="The bank has 30 days to investigate a disputed transaction.",
        source_handle=_FAQ_HANDLE,
        source_type="agency_faq",
        authority_rank=20,
        conflicts_with_value=True,  # it contradicts the Reg-E "10 business days" value for the same fact_key
        now=_NOW,
    )
    check("CFPB FAQ-30 fires needs_reconciliation", cfpb.fired(NEEDS_RECONCILIATION), str(cfpb.lanes))
    check("CFPB FAQ-30 fires is_low_authority", cfpb.fired(IS_LOW_AUTHORITY), str(cfpb.lanes))
    check("CFPB FAQ-30 fires is_conflict_candidate", cfpb.fired(IS_CONFLICT_CANDIDATE), str(cfpb.lanes))
    check("CFPB FAQ-30 the three required lanes all fire",
          {NEEDS_RECONCILIATION, IS_LOW_AUTHORITY, IS_CONFLICT_CANDIDATE} <= set(cfpb.lanes), str(cfpb.lanes))
    check("CFPB FAQ-30 needs_action is True", cfpb.needs_action is True)
    check("CFPB FAQ-30 validates against the v1 contract", _validate(cfpb.to_dict(), schema) == [])

    # ── load-bearing rules ─────────────────────────────────────────────────────────────────────────────
    # a narrative_allegation can NOT become a verified fact and can NEVER be high_value_reusable.
    alleg = clf.classify(fact_key="complaint.42.alleg", claim_type=CLAIM_NARRATIVE_ALLEGATION,
                         claim_text="the consumer alleges fraud", source_handle="ctx://tenant/acme/c/42#n",
                         source_type="complaint_form", is_high_value=True, now=_NOW)
    check("a narrative_allegation is under_supported + needs_verification",
          alleg.fired(IS_UNDER_SUPPORTED) and alleg.fired(NEEDS_VERIFICATION), str(alleg.lanes))
    check("a narrative_allegation can NEVER be high_value_reusable (not verified truth)",
          not alleg.fired(IS_HIGH_VALUE_REUSABLE_FACT), str(alleg.lanes))

    # a model_interpretation requires source support: unsupported → under_supported; law-backed → supported.
    mi_unsup = clf.classify(fact_key="x.mi", claim_type=CLAIM_MODEL_INTERPRETATION,
                            claim_text="this seems to mean X", source_handle="ctx://model/1",
                            source_type="llm_summary", now=_NOW)
    mi_sup = clf.classify(fact_key="x.mi2", claim_type=CLAIM_MODEL_INTERPRETATION,
                          claim_text="this means X", source_handle=_HANDLE, source_type="regulation",
                          authority_rank=90, now=_NOW)
    check("model_interpretation WITHOUT a strong source → under_supported + needs_verification",
          mi_unsup.fired(IS_MODEL_INTERPRETATION) and mi_unsup.fired(IS_UNDER_SUPPORTED)
          and mi_unsup.fired(NEEDS_VERIFICATION), str(mi_unsup.lanes))
    check("model_interpretation WITH a source-of-law handle is NOT marked under_supported",
          mi_sup.fired(IS_MODEL_INTERPRETATION) and not mi_sup.fired(IS_UNDER_SUPPORTED), str(mi_sup.lanes))

    # FAQ ranks below a source of law; a source of law is not low authority.
    faq = clf.classify(fact_key="y.faq", claim_text="guidance says", source_handle=_FAQ_HANDLE,
                       source_type="agency_faq", authority_rank=20, now=_NOW)
    law = clf.classify(fact_key="y.law", claim_text="the rule states", source_handle=_HANDLE,
                       source_type="regulation", authority_rank=90, now=_NOW)
    check("a FAQ is is_low_authority", faq.fired(IS_LOW_AUTHORITY))
    check("a source of law is NOT is_low_authority", not law.fired(IS_LOW_AUTHORITY))

    # tenant_private context stays tenant-scoped (private override fires; scope is never widened to global).
    priv = clf.classify(fact_key="acme.sla", claim_text="internal SLA", source_handle="ctx://tenant/acme/sla",
                        source_scope=SCOPE_TENANT_PRIVATE, tenant_id="acme", source_type="tenant_policy", now=_NOW)
    check("tenant_private context fires is_customer_private_override", priv.fired(IS_CUSTOMER_PRIVATE_OVERRIDE))
    check("tenant_private triage keeps its tenant_private scope (never widened to global)",
          priv.source_scope == SCOPE_TENANT_PRIVATE)

    # current/rate/fee/deadline claims are fragile (fact_key index is deterministic — no builtin hash()).
    for i, txt in enumerate(("the current rate is 5%", "the late fee is $35", "the deadline is Friday", "as of today")):
        r = clf.classify(fact_key=f"frag.{i}", claim_text=txt, source_handle=_HANDLE,
                         source_type="regulation", authority_rank=90, now=_NOW)
        check(f"value-moving claim is fragile: {txt!r}", r.fired(IS_FRAGILE))

    # ── determinism: identical inputs → byte-identical result + a clock-free, content-addressed id ──────
    a = clf.classify(fact_key="det.k", claim_text="the rate is 5%", source_handle=_HANDLE,
                     source_type="regulation", authority_rank=90, now=_NOW)
    b = clf.classify(fact_key="det.k", claim_text="the rate is 5%", source_handle=_HANDLE,
                     source_type="regulation", authority_rank=90, now=_NOW)
    check("identical inputs → identical triage_id (content-addressed, deterministic)", a.triage_id == b.triage_id)
    check("identical inputs → identical full result dict", a.to_dict() == b.to_dict())
    check("identical inputs → identical lane set", a.lanes == b.lanes)
    # the id does NOT depend on the injected time (no clock in the hashed body).
    c = clf.classify(fact_key="det.k", claim_text="the rate is 5%", source_handle=_HANDLE,
                     source_type="regulation", authority_rank=90, now="2099-01-01T00:00:00Z")
    check("triage_id is clock-free (different injected time → same id for the same identity)",
          a.triage_id == c.triage_id)

    # ── red-team at the contract layer: a serves_truth=true mutation is REJECTED by the schema ──────────
    forged = dict(cfpb.to_dict()); forged["serves_truth"] = True
    check("a serves_truth=true triage is REJECTED by the v1 schema (a triage can never be served as truth)",
          _validate(forged, schema) != [])
    forged_lane = dict(cfpb.to_dict()); forged_lane["lane"] = "looks_fine"
    check("an out-of-enum lane is REJECTED by the v1 schema", _validate(forged_lane, schema) != [])

    ok = not fails
    # NOTE: the message is precomputed — a backslash escape inside an f-string brace is
    # PEP 701 (3.12+) syntax and CI runs Python 3.11.
    pass_msg = ('PASS — check_contextops_triage: the ContextTriageClassifier routes context into the 12 lanes '
                'deterministically (taxonomy == the contract enum, every lane demonstrated by a fixture); the CFPB '
                'reference case (FAQ "30 days" vs Reg-E source of law) classifies as needs_reconciliation + '
                'is_low_authority + is_conflict_candidate; a narrative_allegation can never become a verified/reusable '
                'fact, a model_interpretation requires source support, current/rate/fee/deadline claims are fragile, '
                'a FAQ ranks below a source of law, tenant_private context stays tenant-scoped; every result pins '
                'serves_truth=False; identical inputs give a byte-identical result + a clock-free content-addressed '
                'triage_id; to_dict() validates against ContextTriageResult and a serves_truth=true / '
                'out-of-enum-lane mutation is rejected by that schema.')
    print("\n" + (pass_msg if ok else f"{len(fails)} FAILURES: {fails}"))
    return 0 if ok else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: ContextTriageClassifier routes context into the 12 lanes (deterministic, never serves truth).")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
