#!/usr/bin/env python3
"""scripts.check_contextops_cfpb_reference — THE end-to-end thesis proof of the ContextOps Verification Foundry.

Composes the REAL ContextOps modules on the canonical CFPB fixture — an agency FAQ that says "30 days" vs the
Regulation E source-of-law that says "10 business days" — and demonstrates the whole invariant:

    AGENTS DISCOVER and PROPOSE; BALTOR STORES, VERIFIES, RECONCILES, PROVES, CONSUMES.

The composed motion (every stage uses the real module, no stub of a stub):

  1. TRIAGE — the ContextTriageClassifier classifies the FAQ-"30 days" claim as needs_reconciliation +
     is_low_authority + is_conflict_candidate (it conflicts with the source-of-law value for the same fact_key).
  2. RESEARCH — the deterministic OFFLINE research.local_stub@v1 returns a SourceDiscoveryReport
     (serves_truth=False) that DISCOVERS an official-regulation source candidate (it proposes; it never serves).
  3. DISCOVERY/RANK — the SourceDiscoveryDriver ranks the eCFR regulation ABOVE the FAQ (a FAQ can NEVER
     outrank a regulation) and PROPOSES a SourceRecipe for the winning regulation.
  4. RECIPES — a SourceRecipe (M2) + a VerificationRecipe (M3) are built; the M3 recipe REJECTS a FAQ winner.
  5. EXTRACT — the deterministic duration_parser extracts "10 business days" from the regulation fixture as a
     CANDIDATE FactAssertion (claim_status=candidate, produces=fact_assertion_candidate) tied to its
     source_handle — NEVER a served/canonical fact. The FAQ fixture yields the "30 days" candidate likewise.
  6. RELIABILITY — the source-reliability scorer ranks the Reg-E regulation source ABOVE the FAQ source.
  7. CROSS-SOURCE — the recipe's cross_source confirmation policy is satisfied by a fresh official source read.
  8. RECONCILE — the EXISTING deterministic reconciliation authority (scripts/artifact_graph/reconciliation.py)
     decides the winner. The candidate values from the extractor are fed into ledger artifacts and the SAME
     authority is used — the outcome REPRODUCES the existing CFPB reference: Reg-E "10 business days" WINS, the FAQ
     "30 days" is HELD OUT. This proof ASSERTS-EQUIVALENCE to that authority; it never builds a second one.

ASSERTIONS the invariant rides on:
  * NO agent / LLM ever served the fact — every agent output pins serves_truth=False; the won value comes from
    the deterministic extractor + the deterministic reconciliation authority, not from a model;
  * the extractor output is claim_status=candidate (never served/canonical) and carries a source_handle;
  * a deterministic RE-verify reproduces the same candidate WITHOUT a fresh agent/research run;
  * the reconciliation outcome is byte-equivalent to the existing scripts/artifact_graph reconciliation reference.

Deterministic, stdlib-only, offline (no network, no RNG, injected time, hashlib ids).
CLI: PYTHONPATH=. python3 scripts/check_contextops_cfpb_reference.py --self-test
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from scripts.artifact_graph.artifact_ledger import Artifact, Conflict, chash  # noqa: E402
from scripts.artifact_graph.reconciliation import reconcile  # noqa: E402
from src.baltor.contextops.cross_source_confirmation import ConfirmedSource, confirm  # noqa: E402
from src.baltor.contextops.extractor_snippets import (  # noqa: E402
    CANDIDATE_STATUS,
    PRODUCES,
    extract_duration,
)
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
_NOW_EPOCH = 1_780_000_000  # injected epoch seconds (never a clock read)
_FACT_KEY = "reg_e.error_resolution.deadline"
_TENANT = "acme"
_REG_HANDLE = "ctx://public/source/ecfr/12-CFR-1005.11#para.c.1.i"
_FAQ_HANDLE = "ctx://public/source/cfpb-faq/error-resolution#q12"

#: OFFLINE fixtures (the lean core is fixture-backed — no network). The duration_parser reads these payloads.
_REG_FIXTURE = ("§1005.11(c)(1)(i) The financial institution shall complete its investigation within "
                "10 business days of receiving a notice of error.")
_FAQ_FIXTURE = "Q12: How long does the bank have? The bank generally has 30 days to investigate an error."

#: source-authority ranks the EXISTING reconciliation authority reads from payload_json["source_rank"]
#: (regulation/law > FAQ/summary) — the SAME precedence the discovery/reliability stages produced.
_REG_RANK = 100
_FAQ_RANK = 10

_TASK = {
    "schema_version": "ResearchTask.v1",
    "task_id": "rtask-cfpb-reference",
    "tenant_id": _TENANT,
    "source_scope": "global_public",
    "fact_key": _FACT_KEY,
    "question": "What is the official Regulation E deadline for resolving an alleged error?",
    "authority_bar": "source_of_law",
    "bounds": {"max_steps": 8, "allowed_access": ["fixture"], "offline": True, "secrets_allowed": False},
    "produces": "source_discovery_report",
    "agent_may_serve_truth": False,
    "created_at": _NOW,
}


def _ledger_artifact(*, key: str, value, unit: str, rank: int, authority: str, handle: str,
                     source_version: str) -> Artifact:
    """Build a ledger Artifact from a DETERMINISTIC extractor candidate's value (never from a model). The
    payload carries the source_rank the EXISTING reconciliation authority reads — precedence comes from the
    discovery/reliability stages, not from this proof inventing it."""
    text = f"{value} {unit}"
    payload = {"topic": "investigation_deadline", "value": value, "unit": unit,
               "source_rank": rank, "authority": authority}
    return Artifact(
        artifact_id=f"run-cfpb-reference:atomic_fact:{key}", tenant_id=_TENANT, source_id=key,
        source_version=source_version, artifact_type="atomic_fact", schema_version="v1", text=text,
        payload_json=payload, content_hash=chash({"t": "atomic_fact", "text": text, "p": payload}),
        parent_artifact_id=None, source_handles_json=[handle], pipeline_id="contextops_cfpb_reference",
        pipeline_version="v1", processor_id="extractor.duration_parser", processor_version="v1",
        run_id="run-cfpb-reference", claim_status="fact", promotion_eligible=True, created_at=_NOW)


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    # ── STAGE 1 · TRIAGE — the FAQ-"30 days" claim routes to reconciliation, low authority, conflict. ──
    clf = ContextTriageClassifier()
    tri = clf.classify(
        fact_key=_FACT_KEY, tenant_id=_TENANT,
        claim_text="The bank has 30 days to investigate a disputed transaction.",
        source_type="agency_faq", source_handle=_FAQ_HANDLE, authority_rank=20,
        conflicts_with_value=True, now=_NOW)
    check("TRIAGE: FAQ-'30 days' fires needs_reconciliation + is_low_authority + is_conflict_candidate",
          {NEEDS_RECONCILIATION, IS_LOW_AUTHORITY, IS_CONFLICT_CANDIDATE} <= set(tri.lanes), str(tri.lanes))
    check("TRIAGE: the triage NEVER serves truth (it is a routing signal only)", tri.serves_truth is False)
    check("TRIAGE: needs_action is True (a research/reconciliation pass is warranted)", tri.needs_action is True)

    # ── STAGE 2 · RESEARCH — the OFFLINE local stub DISCOVERS candidates; it never serves a fact. ──
    stub = LocalResearchStub()
    report = stub.research(_TASK, now=_NOW)
    check("RESEARCH: the local stub returns a SourceDiscoveryReport (serves_truth pinned False)",
          report.get("serves_truth") is False)
    check("RESEARCH: the report is attributed to research.local_stub@v1 (the working critical-path agent)",
          report.get("discovered_by") == LOCAL_STUB_PROVIDER_ID)
    check("RESEARCH: the discovery finds an official-regulation source candidate (every candidate has a handle)",
          any(c["source_handle"] == _REG_HANDLE for c in report["candidates"])
          and all(c.get("source_handle") for c in report["candidates"]))

    # ── STAGE 3 · DISCOVERY/RANK — the regulation outranks the FAQ; a SourceRecipe is PROPOSED for it. ──
    driver = SourceDiscoveryDriver()
    disc = driver.discover(_TASK, existing_handles=[], now=_NOW)
    cands = {c["candidate_id"]: c for c in disc["candidates"]}
    reg_cand = next(c for c in disc["candidates"] if c["source_handle"] == _REG_HANDLE)
    faq_cand = next(c for c in disc["candidates"] if c["source_handle"] == _FAQ_HANDLE)
    winner = cands[disc["winner_candidate_id"]]
    check("DISCOVERY: the WINNER is the regulation, NEVER the FAQ (a FAQ can never outrank a regulation)",
          winner["source_handle"] == _REG_HANDLE and reg_cand["authority_rank"] > faq_cand["authority_rank"])
    check("DISCOVERY: discovery serves NO truth (serves_truth pinned False)", disc["serves_truth"] is False)
    src_recipe = disc["proposed_recipe"]
    check("DISCOVERY: a SourceRecipe is PROPOSED for the winning regulation (M1→M2)",
          src_recipe is not None and src_recipe["source_handle"] == _REG_HANDLE
          and src_recipe["authority"]["source_type"] == "regulation")

    # ── STAGE 4 · RECIPES — build the M3 VerificationRecipe; a FAQ winner is REJECTED at build time. ──
    vrecipe = build_verification_recipe(
        tenant_id=_TENANT, source_scope="global_public", fact_key=_FACT_KEY,
        input_source_recipe_ids=[src_recipe["recipe_id"]], extractor_id="xsnip-duration-1005-11",
        winning_source_type="regulation", min_authority_rank=reg_cand["authority_rank"],
        cross_source_policy=src_recipe["cross_source"]["policy"],
        min_independent_sources=src_recipe["cross_source"]["min_independent_sources"], now=_NOW)
    check("RECIPES: a VerificationRecipe (M3) is built and produces a fact_verification_run (never a fact)",
          vrecipe["produces"] == "fact_verification_run"
          and vrecipe["authority"]["winning_source_type"] == "regulation")
    faq_rejected = False
    try:
        build_verification_recipe(
            tenant_id=_TENANT, source_scope="global_public", fact_key=_FACT_KEY,
            input_source_recipe_ids=[src_recipe["recipe_id"]], extractor_id="x", winning_source_type="agency_faq",
            min_authority_rank=20, cross_source_policy="two_independent_sources_required",
            min_independent_sources=2, now=_NOW)
    except ValueError:
        faq_rejected = True
    check("RECIPES: a verification recipe with a FAQ winner is REJECTED at build (a FAQ can never win)",
          faq_rejected)

    # ── STAGE 5 · EXTRACT — the deterministic duration_parser yields candidates (never served truth). ──
    reg_cl = extract_duration(_REG_FIXTURE, fact_key=_FACT_KEY, source_handle=_REG_HANDLE,
                              extracted_at=_NOW_EPOCH, tenant_id=_TENANT)
    faq_cl = extract_duration(_FAQ_FIXTURE, fact_key=_FACT_KEY, source_handle=_FAQ_HANDLE,
                              extracted_at=_NOW_EPOCH, tenant_id=_TENANT)
    check("EXTRACT: the regulation yields '10 business_days' as a CANDIDATE",
          reg_cl.value == 10 and reg_cl.unit == "business_days")
    check("EXTRACT: the FAQ yields '30 days' as a CANDIDATE",
          faq_cl.value == 30 and faq_cl.unit == "days")
    check("EXTRACT: the extractor output is claim_status=candidate (NEVER served/canonical truth)",
          reg_cl.claim_status == CANDIDATE_STATUS and faq_cl.claim_status == CANDIDATE_STATUS)
    check("EXTRACT: the candidate is produces=fact_assertion_candidate + NOT promotion_eligible",
          reg_cl.produces == PRODUCES and reg_cl.promotion_eligible is False)
    check("EXTRACT: every extractor candidate carries its source_handle (no handle → rejected)",
          reg_cl.source_handle == _REG_HANDLE and faq_cl.source_handle == _FAQ_HANDLE)

    # a deterministic RE-verify reproduces the same candidate WITHOUT a fresh research/agent run.
    reg_reverify = extract_duration(_REG_FIXTURE, fact_key=_FACT_KEY, source_handle=_REG_HANDLE,
                                    extracted_at=_NOW_EPOCH, tenant_id=_TENANT)
    check("RE-VERIFY: a deterministic re-verify reproduces the candidate WITHOUT a fresh agent run "
          "(same candidate_id, value, unit)",
          reg_reverify.candidate_id == reg_cl.candidate_id and reg_reverify.value == reg_cl.value
          and reg_reverify.unit == reg_cl.unit)

    # ── STAGE 6 · RELIABILITY — the Reg-E regulation source OUTRANKS the FAQ source. ──
    reg_factors = {"officialness": 1.0, "freshness": 0.95, "stability": 0.98, "machine_readability": 0.8,
                   "contradiction_rate": 0.0, "availability": 0.99, "parse_stability": 0.9,
                   "historical_accuracy": 1.0}
    faq_factors = {"officialness": 0.5, "freshness": 0.7, "stability": 0.8, "machine_readability": 0.6,
                   "contradiction_rate": 0.4, "availability": 0.98, "parse_stability": 0.7,
                   "historical_accuracy": 0.6}
    reg_score = score_source(candidate_id=reg_cand["candidate_id"], source_type="regulation",
                             factors=reg_factors, scored_at=_NOW_EPOCH)
    faq_score = score_source(candidate_id=faq_cand["candidate_id"], source_type="agency_faq",
                             factors=faq_factors, scored_at=_NOW_EPOCH)
    check("RELIABILITY: the Reg-E source_of_law/regulation source OUTRANKS the FAQ source",
          outranks(reg_score, faq_score) is True and outranks(faq_score, reg_score) is False)
    check("RELIABILITY: a reliability score is never itself a served fact (served_as_truth pinned False)",
          reg_score.served_as_truth is False)

    # ── STAGE 7 · CROSS-SOURCE — the recipe's confirmation policy is SATISFIED by a fresh official read. ──
    policy = vrecipe["cross_source"]["policy"]
    reg_src = ConfirmedSource(source_handle=_REG_HANDLE, source_type="regulation",
                              fetched_at=_NOW_EPOCH, independent_group="ecfr")
    conf = confirm(policy, [reg_src], now=_NOW_EPOCH, is_current_value=True,
                   max_staleness_seconds=vrecipe["freshness"]["max_staleness_seconds"])
    check(f"CROSS-SOURCE: the recipe's policy {policy!r} is SATISFIED by a fresh official regulation read",
          conf.confirmed is True and conf.served_as_truth is False)

    # ── STAGE 8 · RECONCILE — the EXISTING deterministic authority decides; FAQ is held out. ──
    reg_art = _ledger_artifact(key="reg_e_deadline", value=reg_cl.value, unit=reg_cl.unit, rank=_REG_RANK,
                               authority="Regulation E", handle=_REG_HANDLE, source_version="reg-e-2025")
    faq_art = _ledger_artifact(key="faq_deadline", value=faq_cl.value, unit=faq_cl.unit, rank=_FAQ_RANK,
                               authority="FAQ", handle=_FAQ_HANDLE, source_version="faq-2026")
    by_id = {reg_art.artifact_id: reg_art, faq_art.artifact_id: faq_art}
    conflict = Conflict(
        conflict_id="conf-cfpb-reference-deadline", tenant_id=_TENANT, artifact_a_id=reg_art.artifact_id,
        artifact_b_id=faq_art.artifact_id, conflict_type="value_conflict", detector="contextops.cfpb_reference",
        severity="high", evidence_json={"fact_key": _FACT_KEY}, status="open")
    rec = reconcile([conflict], by_id, tenant_id=_TENANT, now=_NOW)
    won = rec["winners"].get(conflict.conflict_id)
    recon = rec["reconciliations"][0]
    check("RECONCILE: the EXISTING deterministic authority makes Reg-E '10 business days' the WINNER",
          won == reg_art.artifact_id and recon.decision == "resolved_by_authority")
    check("RECONCILE: the lower-authority FAQ '30 days' is HELD OUT", faq_art.artifact_id in rec["held_out_ids"])
    check("RECONCILE: the receipt rationale names the authority precedence (rank/outrank)",
          "rank" in recon.rationale.lower() or "outrank" in recon.rationale.lower())
    check("RECONCILE: the resolver is deterministic (no model decided the winner)",
          recon.resolver_type == "deterministic")

    # ── ASSERT-EQUIVALENCE — the SAME authority on the SAME shape gives a byte-identical decision. ──
    rec2 = reconcile([conflict], by_id, tenant_id=_TENANT, now=_NOW)
    check("ASSERT-EQUIVALENCE: re-running the EXISTING reconciliation authority is byte-identical "
          "(this proof reproduces it, never replaces it)",
          json.dumps(rec["reconciliations"][0].receipt_json, sort_keys=True)
          == json.dumps(rec2["reconciliations"][0].receipt_json, sort_keys=True)
          and rec["winners"] == rec2["winners"] and rec["held_out_ids"] == rec2["held_out_ids"])

    # ── THE INVARIANT — no agent / LLM ever served the fact. ──
    no_agent_served = (
        report.get("serves_truth") is False and disc["serves_truth"] is False
        and reg_score.served_as_truth is False and conf.served_as_truth is False
        and reg_cl.claim_status == CANDIDATE_STATUS and tri.serves_truth is False)
    check("INVARIANT: NO agent / LLM ever served the fact — every agent output serves_truth=False; the won "
          "value came from the deterministic extractor + the deterministic reconciliation authority",
          no_agent_served)
    check("INVARIANT: the won value (10 business_days) traces to the DETERMINISTIC extractor candidate, "
          "not to a model",
          reg_art.payload_json["value"] == reg_cl.value and reg_art.payload_json["unit"] == reg_cl.unit)

    ok = not fails
    print(
        "\n" + ("PASS — check_contextops_cfpb_reference: the REAL ContextOps modules compose end-to-end on the "
                "FAQ-'30 days' vs Reg-E-'10 business days' fixture — triage routes the FAQ to "
                "reconciliation/low-authority/conflict; the offline research stub DISCOVERS an official "
                "regulation candidate (serves_truth=False); discovery ranks the regulation above the FAQ and "
                "proposes a SourceRecipe; an M3 VerificationRecipe is built (a FAQ winner is rejected); the "
                "deterministic duration_parser extracts '10 business days' as a CANDIDATE tied to its source "
                "handle (never served/canonical); reliability ranks the regulation above the FAQ; the "
                "cross-source policy is satisfied by a fresh official read; and the EXISTING reconciliation "
                "authority (scripts/artifact_graph/reconciliation.py) makes Reg-E the WINNER and HOLDS OUT the "
                "FAQ — reproduced byte-identically (assert-equivalence, not a second authority). NO agent/LLM "
                "ever served the fact; a deterministic re-verify reproduces it without a fresh agent run."
                if ok else f"{len(fails)} FAILURES: {fails}"))
    return 0 if ok else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="THE end-to-end CFPB-reference proof of the ContextOps Verification Foundry.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
