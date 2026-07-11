#!/usr/bin/env python3
"""scripts.check_contextops_full_stack — the ContextOps Verification Foundry END-TO-END, printed as a table.

Composes EVERY stage of the foundry on the canonical CFPB fact (FAQ "30 days" vs Reg-E "10 business days")
and prints one row showing each stage GREEN plus the load-bearing invariant:

    TRIAGE | RESEARCH | RECIPE | EXTRACT | RELIABILITY | CROSS_SRC | RECONCILE | COST_LADDER | STATUS

THE INVARIANT this table proves holds: *agents PROPOSED (triage routed, the offline research stub discovered,
the codegen-shaped extractor drafted a candidate) and Baltor DISPOSED (stored, verified, reconciled, proved,
priced) — no agent/LLM ever served the fact.* The CFPB reference proof asserts the deep equivalences; this proof
is the single-glance dashboard view that every stage fires green and the invariant holds.

Deterministic, stdlib-only, offline (injected time, hashlib ids, no network, no RNG).
CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_contextops_full_stack.py --self-test
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from scripts.artifact_graph.artifact_ledger import Artifact, Conflict, chash  # noqa: E402
from scripts.artifact_graph.reconciliation import reconcile  # noqa: E402
from src.baltor.contextops.cost_tracking import cfpb_reference_lifecycle, compute_cost_ladder  # noqa: E402
from src.baltor.contextops.cross_source_confirmation import ConfirmedSource, confirm  # noqa: E402
from src.baltor.contextops.extractor_snippets import CANDIDATE_STATUS, extract_duration  # noqa: E402
from src.baltor.contextops.reliability import outranks, score_source  # noqa: E402
from src.baltor.contextops.research_stub import LOCAL_STUB_PROVIDER_ID, LocalResearchStub  # noqa: E402
from src.baltor.contextops.source_discovery import SourceDiscoveryDriver  # noqa: E402
from src.baltor.contextops.triage import (  # noqa: E402
    IS_CONFLICT_CANDIDATE,
    IS_LOW_AUTHORITY,
    NEEDS_RECONCILIATION,
    ContextTriageClassifier,
)
from src.baltor.contextops.verification_recipe import build_verification_recipe  # noqa: E402

_NOW = "2026-06-05T00:00:00Z"
_NOW_EPOCH = 1_780_000_000
_FACT_KEY = "reg_e.error_resolution.deadline"
_TENANT = "acme"
_REG_HANDLE = "ctx://public/source/ecfr/12-CFR-1005.11#para.c.1.i"
_FAQ_HANDLE = "ctx://public/source/cfpb-faq/error-resolution#q12"
_REG_FIXTURE = ("§1005.11(c)(1)(i) The financial institution shall complete its investigation within "
                "10 business days of receiving a notice of error.")
_FAQ_FIXTURE = "Q12: The bank generally has 30 days to investigate an error."

_TASK = {
    "task_id": "rtask-cfpb-fullstack", "tenant_id": _TENANT, "source_scope": "global_public",
    "fact_key": _FACT_KEY, "question": "What is the official Regulation E error-resolution deadline?",
    "bounds": {"max_steps": 8, "allowed_access": ["fixture"], "offline": True, "secrets_allowed": False},
    "created_at": _NOW,
}
_REG_FACTORS = {"officialness": 1.0, "freshness": 0.95, "stability": 0.98, "machine_readability": 0.8,
                "contradiction_rate": 0.0, "availability": 0.99, "parse_stability": 0.9,
                "historical_accuracy": 1.0}
_FAQ_FACTORS = {"officialness": 0.5, "freshness": 0.7, "stability": 0.8, "machine_readability": 0.6,
                "contradiction_rate": 0.4, "availability": 0.98, "parse_stability": 0.7,
                "historical_accuracy": 0.6}

_STAGES = ("TRIAGE", "RESEARCH", "RECIPE", "EXTRACT", "RELIABILITY", "CROSS_SRC", "RECONCILE", "COST_LADDER")


def _ledger_artifact(*, key: str, value, unit: str, rank: int, authority: str, handle: str,
                     source_version: str) -> Artifact:
    text = f"{value} {unit}"
    payload = {"topic": "investigation_deadline", "value": value, "unit": unit,
               "source_rank": rank, "authority": authority}
    return Artifact(
        artifact_id=f"run-cfpb-fullstack:atomic_fact:{key}", tenant_id=_TENANT, source_id=key,
        source_version=source_version, artifact_type="atomic_fact", schema_version="v1", text=text,
        payload_json=payload, content_hash=chash({"t": "atomic_fact", "text": text, "p": payload}),
        parent_artifact_id=None, source_handles_json=[handle], pipeline_id="contextops_cfpb_fullstack",
        pipeline_version="v1", processor_id="extractor.duration_parser", processor_version="v1",
        run_id="run-cfpb-fullstack", claim_status="fact", promotion_eligible=True, created_at=_NOW)


def _run_stack() -> dict:
    """Compose every stage and return per-stage green flags + the invariant flag (proposed vs disposed)."""
    green: dict[str, bool] = {}

    # TRIAGE — propose: route the FAQ-30 claim.
    tri = ContextTriageClassifier().classify(
        fact_key=_FACT_KEY, tenant_id=_TENANT, claim_text="The bank has 30 days to investigate a dispute.",
        source_type="agency_faq", source_handle=_FAQ_HANDLE, authority_rank=20, conflicts_with_value=True,
        now=_NOW)
    green["TRIAGE"] = ({NEEDS_RECONCILIATION, IS_LOW_AUTHORITY, IS_CONFLICT_CANDIDATE} <= set(tri.lanes)
                       and tri.serves_truth is False)

    # RESEARCH — propose: the offline stub discovers candidates, serves no truth.
    report = LocalResearchStub().research(_TASK, now=_NOW)
    green["RESEARCH"] = (report.get("serves_truth") is False
                         and report.get("discovered_by") == LOCAL_STUB_PROVIDER_ID
                         and any(c["source_handle"] == _REG_HANDLE for c in report["candidates"]))

    # RECIPE — dispose: discovery ranks regulation > FAQ, proposes a SourceRecipe; M3 recipe is built.
    disc = SourceDiscoveryDriver().discover(_TASK, existing_handles=[], now=_NOW)
    cands = {c["candidate_id"]: c for c in disc["candidates"]}
    winner = cands[disc["winner_candidate_id"]]
    reg_cand = next(c for c in disc["candidates"] if c["source_handle"] == _REG_HANDLE)
    src_recipe = disc["proposed_recipe"]
    vrecipe = build_verification_recipe(
        tenant_id=_TENANT, source_scope="global_public", fact_key=_FACT_KEY,
        input_source_recipe_ids=[src_recipe["recipe_id"]], extractor_id="xsnip-duration-1005-11",
        winning_source_type="regulation", min_authority_rank=reg_cand["authority_rank"],
        cross_source_policy=src_recipe["cross_source"]["policy"],
        min_independent_sources=src_recipe["cross_source"]["min_independent_sources"], now=_NOW)
    green["RECIPE"] = (winner["source_handle"] == _REG_HANDLE
                       and src_recipe["authority"]["source_type"] == "regulation"
                       and vrecipe["produces"] == "fact_verification_run")

    # EXTRACT — dispose: deterministic extractor yields a CANDIDATE (never served truth).
    reg_cl = extract_duration(_REG_FIXTURE, fact_key=_FACT_KEY, source_handle=_REG_HANDLE,
                              extracted_at=_NOW_EPOCH, tenant_id=_TENANT)
    faq_cl = extract_duration(_FAQ_FIXTURE, fact_key=_FACT_KEY, source_handle=_FAQ_HANDLE,
                              extracted_at=_NOW_EPOCH, tenant_id=_TENANT)
    green["EXTRACT"] = (reg_cl.value == 10 and reg_cl.unit == "business_days"
                        and reg_cl.claim_status == CANDIDATE_STATUS and reg_cl.promotion_eligible is False
                        and reg_cl.source_handle == _REG_HANDLE)

    # RELIABILITY — dispose: regulation source outranks the FAQ source.
    reg_score = score_source(candidate_id=reg_cand["candidate_id"], source_type="regulation",
                             factors=_REG_FACTORS, scored_at=_NOW_EPOCH)
    faq_score = score_source(candidate_id="scand-faq", source_type="agency_faq", factors=_FAQ_FACTORS,
                             scored_at=_NOW_EPOCH)
    green["RELIABILITY"] = outranks(reg_score, faq_score) is True and reg_score.served_as_truth is False

    # CROSS_SRC — dispose: the recipe's confirmation policy is satisfied by a fresh official read.
    reg_src = ConfirmedSource(source_handle=_REG_HANDLE, source_type="regulation", fetched_at=_NOW_EPOCH,
                              independent_group="ecfr")
    conf = confirm(vrecipe["cross_source"]["policy"], [reg_src], now=_NOW_EPOCH, is_current_value=True,
                   max_staleness_seconds=vrecipe["freshness"]["max_staleness_seconds"])
    green["CROSS_SRC"] = conf.confirmed is True and conf.served_as_truth is False

    # RECONCILE — dispose: the EXISTING deterministic authority makes Reg-E win, holds out the FAQ.
    reg_art = _ledger_artifact(key="reg_e_deadline", value=reg_cl.value, unit=reg_cl.unit, rank=100,
                               authority="Regulation E", handle=_REG_HANDLE, source_version="reg-e-2025")
    faq_art = _ledger_artifact(key="faq_deadline", value=faq_cl.value, unit=faq_cl.unit, rank=10,
                               authority="FAQ", handle=_FAQ_HANDLE, source_version="faq-2026")
    by_id = {reg_art.artifact_id: reg_art, faq_art.artifact_id: faq_art}
    conflict = Conflict(conflict_id="conf-cfpb-fullstack", tenant_id=_TENANT, artifact_a_id=reg_art.artifact_id,
                        artifact_b_id=faq_art.artifact_id, conflict_type="value_conflict",
                        detector="contextops.full_stack", severity="high",
                        evidence_json={"fact_key": _FACT_KEY}, status="open")
    rec = reconcile([conflict], by_id, tenant_id=_TENANT, now=_NOW)
    green["RECONCILE"] = (rec["winners"].get(conflict.conflict_id) == reg_art.artifact_id
                          and faq_art.artifact_id in rec["held_out_ids"])

    # COST_LADDER — price: the M0→M7 ladder shows the moat (research once, deterministic forever).
    metrics = compute_cost_ladder(cfpb_reference_lifecycle(_FACT_KEY, now=_NOW), now=_NOW)
    green["COST_LADDER"] = (metrics.agent_research_runs == 1 and metrics.llm_calls_avoided >= 1
                            and metrics.cost_reduction_estimate > 0 and metrics.serves_truth is False)

    # THE INVARIANT — agents proposed (serves_truth False everywhere), Baltor disposed (won deterministically).
    invariant = (tri.serves_truth is False and report.get("serves_truth") is False
                 and disc["serves_truth"] is False and reg_score.served_as_truth is False
                 and conf.served_as_truth is False and reg_cl.claim_status == CANDIDATE_STATUS
                 and metrics.serves_truth is False
                 and reg_art.payload_json["value"] == reg_cl.value
                 and rec["winners"].get(conflict.conflict_id) == reg_art.artifact_id)

    return {"green": green, "invariant": invariant, "metrics": metrics, "won": f"{reg_cl.value} {reg_cl.unit}"}


def _self_test() -> int:
    out = _run_stack()
    green, invariant = out["green"], out["invariant"]

    cells = [f"{s}={'GREEN' if green.get(s) else 'RED'}" for s in _STAGES]
    status = "GREEN" if (all(green.values()) and invariant) else "RED"
    print("  " + " | ".join(_STAGES) + " | STATUS")
    print("  " + " | ".join(("GREEN" if green.get(s) else "RED") for s in _STAGES) + f" | {status}")
    print()
    for c in cells:
        print(f"  [{'ok' if c.endswith('GREEN') else 'FAIL'}] {c}")
    print(f"  [{'ok' if invariant else 'FAIL'}] INVARIANT: agents PROPOSED, Baltor DISPOSED "
          f"(no agent/LLM served the fact; won value = {out['won']!r} via the deterministic path)")
    print(f"  [ok] COST_LADDER: research once → deterministic forever "
          f"(llm_calls_avoided={out['metrics'].llm_calls_avoided}, "
          f"cost_reduction_estimate={out['metrics'].cost_reduction_estimate})")

    ok = all(green.values()) and invariant
    print(
        "\n" + ("PASS — check_contextops_full_stack: the ContextOps Verification Foundry composes end-to-end on "
                "the CFPB fact — TRIAGE | RESEARCH | RECIPE | EXTRACT | RELIABILITY | CROSS_SRC | RECONCILE | "
                "COST_LADDER are ALL GREEN and the invariant holds (agents proposed, Baltor disposed; no agent/"
                "LLM ever served the fact — the won value came from the deterministic extractor + the existing "
                "deterministic reconciliation authority, and the cost ladder shows research-once / "
                "deterministic-forever)."
                if ok else f"STATUS RED: stages={[s for s in _STAGES if not green.get(s)]} invariant={invariant}"))
    return 0 if ok else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="The ContextOps Verification Foundry, end-to-end as a table.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
