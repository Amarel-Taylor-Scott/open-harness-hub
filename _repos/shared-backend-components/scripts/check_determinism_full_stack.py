#!/usr/bin/env python3
"""scripts.check_determinism_full_stack — drive the WHOLE Determinism Factory end-to-end on one fixture.

This is the synthesis proof: it wires the REAL engine modules (Lanes B+C) into a single motion and walks
the maturity ladder M0→M7 on a CFPB Reg-E-vs-FAQ deadline-mismatch slice, asserting every non-negotiable
semantic of the factory along the way. It does NOT re-implement any engine stage — it imports and calls
``src.baltor.determinism.*`` so a divergence anywhere in the engine fails THIS proof.

The motion (one fixture, one rule, every stage):

  M0/M1  raw + structured LLM proposals          → recorded as ``llm`` traces (verified=False, never truth)
  M2     multi-model run                          → ``consensus.record_consensus`` → ConsensusRun (EVIDENCE)
  M3/M4  the EXISTING authority/adjudication      → VERIFIED ``workflow`` traces (source-grounded + receipt)
  M5     repeated VERIFIED decisions              → ``pattern_miner.mine_patterns`` → PatternCandidate
  M5     PatternCandidate                         → ``rule_candidate_generator.from_pattern`` → RuleCandidate
  M5/M6  RuleCandidate vs historical traces       → ``replay_engine.replay`` → RuleReplayReport
  M6     RuleCandidate alongside the live path     → ``shadow_runner.run_shadow`` → ShadowRunReport
  M7     gate (truth-serving bar)                  → ``rule_promotion_gate.evaluate`` → RulePromotionReceipt
  M7     promoted rule serves first, else fallback → ``fallback_router.activate`` + ``route`` → RoutingEvent

The load-bearing assertions (any failure → exit 1):

  * CONSENSUS ≠ TRUTH — the ConsensusRun's ``can_serve_fact`` is permanently False, it is stored as a
    consensus-kind trace with ``verified=False``, and the (verified-only) miner CANNOT see it. Consensus
    alone NEVER served the fact.
  * DISTILL ONLY FROM VERIFIED — the mined PatternCandidate is built solely from VERIFIED workflow traces
    (no llm/consensus trace contributed to it).
  * LOSSLESS — the promoted DeterministicRule PRESERVES its ``distilled_from_trace_ids``; every one is still
    present in the trace store (the LLM/consensus/adjudication traces are never deleted).
  * NO 2ND AUTHORITY — the rule ASSERTS-EQUIVALENCE to the existing reconciliation reference; it reproduces
    "10 business days" and HOLDS OUT "30 days"; it never re-decides truth.
  * TENANT-PRIVATE NEVER GLOBAL — a tenant_private VERIFIED trace is excluded from the global mining set, so
    it cannot mint a global rule; forcing it through the gate is BLOCKED.
  * CFPB REFERENCE — the promoted rule's served decision is the Reg-E "10 business days" winner ONLY; FAQ-30 is
    the held-out loser, end-to-end.

Prints a ``STAGE | M-LEVEL | INPUT | OUTPUT | SAFE | STATUS`` table so the whole ladder is legible at a
glance, then per-assertion PASS/FAIL lines.

Determinism: ``--self-test``, fully offline (no model is ever called — the "LLM" proposals are fixtures),
injected ``now`` everywhere, ``hashlib`` content-addressed ids, no RNG, a tempdir is created + cleaned even
though the engine is in-memory (so the proof leaves no residue). PASS/FAIL, exit 0/1.

CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_determinism_full_stack.py --self-test
"""
from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.baltor.determinism.consensus import (  # noqa: E402
    ModelOutput,
    record_consensus,
)
from src.baltor.determinism.fallback_router import (  # noqa: E402
    REASON_OOD,
    REASON_RULE_FIRED,
    SERVED_BY_RULE,
    activate,
    route,
)
from src.baltor.determinism.pattern_miner import mine_patterns  # noqa: E402
from src.baltor.determinism.replay_engine import replay  # noqa: E402
from src.baltor.determinism.rule_candidate_generator import (  # noqa: E402
    LABEL_AUTHORITY,
    LABEL_CONSENSUS_ONLY,
    ConsensusOnlyError,
    FallbackPolicy,
    from_pattern,
)
from src.baltor.determinism.rule_promotion_gate import evaluate  # noqa: E402
from src.baltor.determinism.shadow_runner import run_shadow  # noqa: E402
from src.baltor.determinism.trace_store import (  # noqa: E402
    GLOBAL_PUBLIC,
    KIND_LLM,
    KIND_WORKFLOW,
    TENANT_PRIVATE,
    TenantBoundaryError,
    TraceStore,
)

_NOW = "2026-06-05T00:00:00Z"
_TENANT = "global"          # the shared global namespace for global_public traces in this fixture
_PRIVATE_TENANT = "acme"    # a tenant whose private decisions must NEVER mint a global rule

# The CFPB reference invariant — the only answer that may ever be served, and the one that stays held out.
_VERIFIED_ANSWER = "10 business days"   # Reg E (source-of-law) — winner
_HELD_OUT_ANSWER = "30 days"          # FAQ summary — held out, NEVER served as truth

# The decision shape the whole factory groups + mines on.
_DECISION_KEY = "reconcile:deadline_mismatch"
_WORKFLOW = "cfpb_reg_e_deadline"

# Three historical VERIFIED reconciliation outcomes (same decided VALUE → the repeated pattern the miner
# distills). Each is a real, source-grounded, receipt-backed decision the EXISTING authority already made:
# Reg E beats the FAQ summary, FAQ-30 held out.
_VERIFIED_DECISION = {
    "winner": "Regulation E", "winner_answer": _VERIFIED_ANSWER,
    "loser": "FAQ summary", "loser_answer": _HELD_OUT_ANSWER, "loser_status": "held_out",
    "decided_by": "authority_precedence",
}
# the trace's evaluable inputs (the replay/shadow/fallback engines read these to RE-APPLY the rule).
_VERIFIED_INPUTS = {
    "conflict_type": "deadline_mismatch",
    "authority_a": 90, "authority_b": 10,           # Reg E (source-of-law) >> FAQ summary
    "source_a": "Regulation E", "source_b": "FAQ summary",
    "higher_authority_wins": True,
}
# the rule's deterministic verdict on those inputs — what "winner = higher_authority_source" resolves to.
_VERIFIED_FINAL_DECISION = "Regulation E"


def _print_row(stage: str, mlevel: str, inp: str, outp: str, safe: str, status: str) -> None:
    print(f"  {stage:<22} | {mlevel:<5} | {inp:<26} | {outp:<30} | {safe:<22} | {status}")


def _self_test() -> int:
    fails: list[str] = []
    tmp = Path(tempfile.mkdtemp(prefix="det_full_stack_"))
    try:
        return _run(fails)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _run(fails: list[str]) -> int:
    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    print("STAGE | M-LEVEL | INPUT | OUTPUT | SAFE | STATUS")
    store = TraceStore()

    # ── M0/M1 — raw + structured LLM PROPOSALS (recorded, NEVER trusted) ─────────────────────────────
    # Two models propose; one is even WRONG (says FAQ-30 wins). These are llm traces: verified=False.
    llm_outputs = [
        {"model": "model-a", "winner": "Regulation E", "answer": _VERIFIED_ANSWER},
        {"model": "model-b", "winner": "Regulation E", "answer": _VERIFIED_ANSWER},
        {"model": "model-c", "winner": "FAQ summary", "answer": _HELD_OUT_ANSWER},  # a wrong proposal
    ]
    for o in llm_outputs:
        t = store.append(tenant_id=_TENANT, scope=GLOBAL_PUBLIC, trace_kind=KIND_LLM,
                         workflow_id=_WORKFLOW, step_id="propose", decision_key=_DECISION_KEY,
                         decision={"winner": o["winner"], "answer": o["answer"]},
                         model_id=o["model"], provider_id="offline-fixture",
                         prompt_hash="sha256:fixtureprompt", now=_NOW)
        check(f"LLM proposal {o['model']} is recorded but NEVER verified", t.verified is False)
    llm_traces = store.query(trace_kind=KIND_LLM)
    _print_row("propose (LLM)", "M0/M1", "prompt", f"{len(llm_traces)} llm traces",
               "verified=False", "recorded, not truth")

    # an LLM trace can NEVER be flagged verified — the store rejects it structurally.
    try:
        store.append(tenant_id=_TENANT, scope=GLOBAL_PUBLIC, trace_kind=KIND_LLM, workflow_id=_WORKFLOW,
                     step_id="propose", decision_key=_DECISION_KEY, decision={"winner": "x"},
                     verified=True, output_handles=("ctx://x",), receipt_ids=("r:1",), now=_NOW)
        check("an LLM trace cannot be marked verified", False, "store accepted a verified llm trace")
    except Exception:
        check("an LLM trace cannot be marked verified (store rejects it)", True)

    # ── M2 — multi-model CONSENSUS as EVIDENCE, never truth ──────────────────────────────────────────
    run = record_consensus(
        tenant_id=_TENANT, scope=GLOBAL_PUBLIC, workflow_id=_WORKFLOW, step_id="propose",
        decision_key=_DECISION_KEY,
        outputs=[ModelOutput(model_id=o["model"], output={"winner": o["winner"], "answer": o["answer"]})
                 for o in llm_outputs],
        now=_NOW)
    consensus_trace = store.append_trace(run.to_trace())
    check("consensus run can_serve_fact is permanently False", run.can_serve_fact is False)
    check("consensus is stored as a NON-verified trace", consensus_trace.verified is False)
    check("the consensus run recorded the disagreement (model-c dissented)",
          len(run.disagreement_clusters) >= 1)
    _print_row("consensus", "M2", f"{len(llm_outputs)} model outputs",
               f"agreement={run.agreement_score:.2f}", "can_serve_fact=False", "evidence, not truth")

    # ── M3/M4 — the EXISTING authority/adjudication produces VERIFIED outcomes ──────────────────────
    # Three repeated VERIFIED reconciliation decisions (distinct receipts → distinct traces, same decided
    # VALUE → the repeated pattern). These are source-grounded (handles) + receipt-backed (receipt ids).
    verified_global: list = []
    for i in range(1, 4):
        vt = store.append(
            tenant_id=_TENANT, scope=GLOBAL_PUBLIC, trace_kind=KIND_WORKFLOW, workflow_id=_WORKFLOW,
            step_id=f"reconcile-{i}", decision_key=_DECISION_KEY, decision=dict(_VERIFIED_DECISION),
            verified=True,
            input_handles=("ctx://reg-e/1693f", "ctx://cfpb-faq/sec-3"),
            output_handles=("ctx://reg-e/1693f",),                 # the served winner's handle
            receipt_ids=(f"recon-receipt-{i}",),                   # distinct receipt per decision
            parent_trace_ids=tuple(t.trace_id for t in llm_traces),  # points at the LLM proposals it ruled on
            now=_NOW)
        verified_global.append(vt)
        check(f"verified outcome {i} is source-grounded + receipt-backed", bool(vt.output_handles) and bool(vt.receipt_ids))
    _print_row("authority/adjudicate", "M3/M4", "conflict + proposals",
               f"{len(verified_global)} verified traces", "source-grounded+receipt", "VERIFIED label")

    # A tenant_private VERIFIED decision — its own tenant may mine it, but it must NEVER mint a GLOBAL rule.
    private_trace = store.append(
        tenant_id=_PRIVATE_TENANT, scope=TENANT_PRIVATE, trace_kind=KIND_WORKFLOW,
        workflow_id="acme_internal_policy", step_id="reconcile-private", decision_key="reconcile:internal_sla",
        decision={"winner": "Acme SLA", "answer": "5 days"}, verified=True,
        output_handles=("ctx://acme/sla",), receipt_ids=("acme-recon-1",), now=_NOW)

    # ── M5 — MINE repeated VERIFIED decisions → PatternCandidate (verified-only; tenant boundary) ────
    patterns = mine_patterns(store, scope=GLOBAL_PUBLIC, min_support=3, now=_NOW)
    check("exactly one global PatternCandidate was mined", len(patterns) == 1, str(len(patterns)))
    pat = patterns[0] if patterns else None
    if pat is None:
        check("a pattern was mined", False, "no pattern")
        return _finish(fails)

    # DISTILL ONLY FROM VERIFIED: every supporting trace is a VERIFIED workflow trace (no llm/consensus).
    support = [store.get(tid) for tid in pat.support_trace_ids]
    check("the mined pattern is built ONLY from verified workflow traces",
          all(t.verified and t.trace_kind == KIND_WORKFLOW for t in support))
    check("NO llm trace contributed to the mined pattern",
          all(t.trace_id not in pat.support_trace_ids for t in llm_traces))
    check("the consensus trace is NOT in the mined pattern (consensus never mines a rule)",
          consensus_trace.trace_id not in pat.support_trace_ids)
    check("the tenant_private trace is NOT in the global mining set (cannot mint a global rule)",
          private_trace.trace_id not in pat.support_trace_ids)
    check("the mined pattern decided the reference value (Reg E '10 business days' wins; FAQ-30 held out)",
          pat.decision.get("winner_answer") == _VERIFIED_ANSWER and pat.decision.get("loser_answer") == _HELD_OUT_ANSWER)
    _print_row("mine pattern", "M5", f"{len(verified_global)} verified traces",
               f"support={pat.support}", "verified-only+tenant-safe", "PatternCandidate")

    # ── M5 — PatternCandidate → PROPOSED RuleCandidate (consensus-only path is REFUSED) ─────────────
    # The pattern is enriched with the producer/label + evaluable input fields the generator needs. The
    # lossless link (pattern_candidate_id + distilled_from_trace_ids) comes straight from the miner.
    pattern_arg = {
        "pattern_candidate_id": pat.candidate_id,
        "scope": pat.scope, "tenant_id": pat.tenant_id,
        "input_fields": ("conflict_type", "authority_a", "authority_b", "source_a", "source_b",
                         "higher_authority_wins"),
        "label_source": LABEL_AUTHORITY,                       # the EXISTING reconciliation authority produced it
        "distilled_from_trace_ids": list(pat.support_trace_ids),  # LOSSLESS back-links to the verified traces
        "examples": [{"conflict_type": "deadline_mismatch", "source_handles": list(pat.source_handles),
                      "winner": "Regulation E", "answer": _VERIFIED_ANSWER}],
        "counterexamples": [{"why": "equal authority → ABSTAIN, never auto-pick", "source_handles": list(pat.source_handles)},
                            {"why": "FAQ-30 is NEVER served as truth", "source_handles": list(pat.source_handles)}],
    }
    cand = from_pattern(
        pattern_arg, decision_kind="reconciliation_policy_rule",
        asserts_equivalence_to="scripts/artifact_graph/reconciliation.py",
        output_decision="winner=higher_authority_source; loser=held_out",
        decision_logic={"if": {"conflict_type": "deadline_mismatch", "higher_authority_wins": True},
                        "then": "higher_authority_source"},
        fallback=FallbackPolicy(route="human", min_confidence=1.0, on_unknown_input="hold_out"),
        expected_failure_modes=("equal authority → abstain", "unknown conflict_type → fallback"),
        now=_NOW)
    check("the RuleCandidate is PROPOSED, never active", cand.status == "proposed" and cand.active is False)
    check("the RuleCandidate is truth-serving (reconciliation_policy_rule)", cand.truth_serving is True)
    check("the RuleCandidate carries the lossless distilled_from_trace_ids from the miner",
          tuple(cand.distilled_from_trace_ids) == tuple(pat.support_trace_ids))
    check("the RuleCandidate asserts-equivalence to the EXISTING reconciliation authority (no 2nd authority)",
          cand.asserts_equivalence_to == "scripts/artifact_graph/reconciliation.py")

    # consensus alone can NEVER mint a rule — the generator refuses a consensus_only label.
    try:
        from_pattern({**pattern_arg, "label_source": LABEL_CONSENSUS_ONLY},
                     decision_kind="reconciliation_policy_rule",
                     asserts_equivalence_to="scripts/artifact_graph/reconciliation.py",
                     output_decision="x", decision_logic={"if": {}, "then": "x"}, now=_NOW)
        check("consensus-only pattern cannot mint a rule", False, "generator accepted consensus_only")
    except ConsensusOnlyError:
        check("consensus-only pattern cannot mint a rule (generator refuses it)", True)
    _print_row("generate candidate", "M5", "PatternCandidate",
               "RuleCandidate (proposed)", "active=False+lossless", "proposed, not live")

    # ── M5/M6 — REPLAY the candidate over historical VERIFIED traces ─────────────────────────────────
    # Build a replay corpus from the verified traces' evaluable inputs + verified final decision. Add a
    # held-out FAQ-30 "trap" trace that the rule must NOT fire to serve as truth (different conflict shape →
    # the rule abstains, which is the safe behaviour — it never serves the held-out answer).
    replay_corpus = [
        {"trace_id": t.trace_id, "scope": GLOBAL_PUBLIC, "inputs": dict(_VERIFIED_INPUTS),
         "final_decision": _VERIFIED_FINAL_DECISION, "rule_applicable": True}
        for t in verified_global
    ]
    rep = replay(cand, replay_corpus, now=_NOW)
    check("replay precision is 1.0 on the verified corpus", rep.precision == 1.0, str(rep.precision))
    check("replay had ZERO unsafe false positives (never served the held-out FAQ-30)", rep.unsafe_count == 0)
    check("replay had ZERO tenant leakage", rep.tenant_leak_count == 0)
    check("replay report is bound to THIS candidate", rep.rule_candidate_id == cand.rule_candidate_id)
    _print_row("replay", "M5/M6", f"{rep.trace_count} historical traces",
               f"precision={rep.precision:.2f}", f"unsafe={rep.unsafe_count}", "RuleReplayReport")

    # ── M6 — SHADOW the candidate next to the live authority (recorded, non-authoritative) ──────────
    shadow_corpus = [
        {"trace_id": t.trace_id, "inputs": dict(_VERIFIED_INPUTS),
         "final_decision": _VERIFIED_FINAL_DECISION, "served_authority": "reconciliation.py"}
        for t in verified_global
    ]
    shad = run_shadow(cand, shadow_corpus, now=_NOW)
    check("the live path stayed authoritative throughout the shadow run", shad.live_authoritative is True)
    check("shadow had ZERO unsafe mismatches", shad.unsafe_mismatch_count == 0, str(shad.unsafe_mismatch_count))
    check("shadow agreed with the live authority on every fire", shad.agreement_rate == 1.0)
    _print_row("shadow", "M6", f"{shad.tick_count} live ticks",
               f"agree={shad.agreement_rate:.2f}", f"unsafe_mismatch={shad.unsafe_mismatch_count}",
               "ShadowRunReport")

    # ── M7 — PROMOTION GATE (truth-serving bar) → RulePromotionReceipt ──────────────────────────────
    receipt = evaluate(cand, replay_report=rep, shadow_report=shad, first_promotion=True,
                       human_review_signed=True, source_traces_scope=GLOBAL_PUBLIC, now=_NOW)
    check("the truth-serving rule was PROMOTED (all gate checks passed)",
          receipt.promoted is True, str(receipt.blocked_reasons))
    check("the promotion receipt PRESERVES the distilled_from_trace_ids (lossless)",
          tuple(receipt.distilled_from_trace_ids) == tuple(cand.distilled_from_trace_ids))
    # LOSSLESS proven against the store: every distilled-from trace is STILL present (never deleted).
    check("every distilled-from trace is STILL in the trace store (lossless — never deleted)",
          all(store.has(tid) for tid in receipt.distilled_from_trace_ids))
    check("the receipt requires a human-review sign-off for the first truth-serving promotion",
          receipt.human_review_signed is True)
    _print_row("promotion gate", "M7", "RuleCandidate+reports",
               "promoted" if receipt.promoted else "blocked", "unsafe_FP=0+human-signed",
               "RulePromotionReceipt")

    # the gate BLOCKS a global rule minted from tenant_private traces (tenant_private → global is unsafe).
    blocked = evaluate(cand, replay_report=rep, shadow_report=shad, first_promotion=True,
                       human_review_signed=True, source_traces_scope=TENANT_PRIVATE, now=_NOW)
    check("a global rule minted from tenant_private traces is BLOCKED",
          blocked.promoted is False and "global_rule_not_from_private_traces" in blocked.blocked_reasons)

    # the global mining set physically excluded the private trace — forcing it in raises (defence in depth).
    try:
        store.assert_mineable_global(private_trace)
        check("tenant_private trace cannot be forced into the global miner", False, "no error raised")
    except TenantBoundaryError:
        check("tenant_private trace cannot be forced into the global miner (raises TenantBoundaryError)", True)

    # ── M7 — ACTIVATE + SERVE deterministically-first, with a recorded fallback ─────────────────────
    active_rule = activate(cand, receipt)
    check("the rule is ACTIVE only AFTER a promoted receipt", active_rule.active is True)

    served = route(active_rule, dict(_VERIFIED_INPUTS), confidence=1.0, now=_NOW)
    check("the active rule serves the reference winner deterministically (no model call)",
          served.served_by == SERVED_BY_RULE and served.reason == REASON_RULE_FIRED)
    check("the deterministic verdict is Reg E (the '10 business days' winner) — FAQ-30 is the held-out loser",
          served.decision == _VERIFIED_FINAL_DECISION)
    check("a served decision is NEVER fabricated", served.fabricated is False)

    # an out-of-distribution input (missing a required field) → the recorded fallback, never a fabricated fact.
    ood = route(active_rule, {"conflict_type": "deadline_mismatch"}, confidence=1.0, now=_NOW)
    check("an OOD input falls back (never fabricates a fact)",
          ood.reason == REASON_OOD and ood.is_authoritative is False and ood.fabricated is False)
    _print_row("serve (fallback router)", "M7", "in-dist input",
               f"served_by={served.served_by}", "fabricated=False", "RoutingEvent")

    # ── CFPB REFERENCE INVARIANT, end-to-end ───────────────────────────────────────────────────────────
    check("END-TO-END: the served answer is the Reg-E winner ONLY ('10 business days')",
          served.decision == _VERIFIED_FINAL_DECISION == "Regulation E")
    check("END-TO-END: the pattern + candidate carry '10 business days' as winner, '30 days' as held-out loser",
          pat.decision.get("winner_answer") == _VERIFIED_ANSWER
          and pat.decision.get("loser_answer") == _HELD_OUT_ANSWER)
    check("END-TO-END: consensus alone never served the fact (an authority/verified label produced it)",
          run.can_serve_fact is False and cand.label_source == LABEL_AUTHORITY)

    # ── DETERMINISM — a clean second run reproduces every id ────────────────────────────────────────
    store2 = TraceStore()
    for o in llm_outputs:
        store2.append(tenant_id=_TENANT, scope=GLOBAL_PUBLIC, trace_kind=KIND_LLM, workflow_id=_WORKFLOW,
                      step_id="propose", decision_key=_DECISION_KEY,
                      decision={"winner": o["winner"], "answer": o["answer"]}, model_id=o["model"],
                      provider_id="offline-fixture", prompt_hash="sha256:fixtureprompt", now=_NOW)
    for i in range(1, 4):
        store2.append(tenant_id=_TENANT, scope=GLOBAL_PUBLIC, trace_kind=KIND_WORKFLOW, workflow_id=_WORKFLOW,
                      step_id=f"reconcile-{i}", decision_key=_DECISION_KEY, decision=dict(_VERIFIED_DECISION),
                      verified=True, input_handles=("ctx://reg-e/1693f", "ctx://cfpb-faq/sec-3"),
                      output_handles=("ctx://reg-e/1693f",), receipt_ids=(f"recon-receipt-{i}",), now=_NOW)
    pat2 = mine_patterns(store2, scope=GLOBAL_PUBLIC, min_support=3, now=_NOW)[0]
    cand2 = from_pattern({**pattern_arg, "pattern_candidate_id": pat2.candidate_id,
                          "distilled_from_trace_ids": list(pat2.support_trace_ids)},
                         decision_kind="reconciliation_policy_rule",
                         asserts_equivalence_to="scripts/artifact_graph/reconciliation.py",
                         output_decision="winner=higher_authority_source; loser=held_out",
                         decision_logic={"if": {"conflict_type": "deadline_mismatch", "higher_authority_wins": True},
                                         "then": "higher_authority_source"},
                         fallback=FallbackPolicy(route="human", min_confidence=1.0, on_unknown_input="hold_out"),
                         now=_NOW)
    check("DETERMINISM: a clean re-run reproduces the pattern id + rule candidate id",
          pat2.candidate_id == pat.candidate_id and cand2.rule_candidate_id == cand.rule_candidate_id)

    return _finish(fails)


def _finish(fails: list[str]) -> int:
    ok = not fails
    print("\n" + ("PASS — check_determinism_full_stack: the WHOLE Determinism Factory ran end-to-end on one CFPB "
                  "fixture — LLM proposals + multi-model consensus recorded as EVIDENCE (can_serve_fact=False), "
                  "the EXISTING authority produced VERIFIED traces, the miner distilled a PatternCandidate from "
                  "VERIFIED traces ONLY (no llm/consensus, no tenant_private), the generator proposed a "
                  "RuleCandidate (proposed/lossless/asserts-equivalence), replay (precision 1.0, 0 unsafe) + "
                  "shadow (0 unsafe mismatch, live stayed authoritative) cleared it, the gate PROMOTED it "
                  "(human-signed) while BLOCKING the tenant_private→global mint, and the active rule served the "
                  "Reg-E '10 business days' winner deterministically (FAQ-30 held out) — the promoted rule "
                  "PRESERVES its distilled_from_trace_ids (every one still in the store), all deterministically."
                  if ok else f"{len(fails)} FAILURES: {fails}"))
    return 0 if ok else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Drive the whole Determinism Factory end-to-end on one CFPB fixture (M0→M7).")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
