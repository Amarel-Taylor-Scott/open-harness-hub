#!/usr/bin/env python3
"""src.baltor.determinism.demo — build a DETERMINISTIC projection of the whole Determinism Factory motion.

This module re-uses the REAL engine (Lanes B+C) and mirrors the EXACT motion proven end-to-end by
``_repos/shared-backend-components/scripts/check_determinism_full_stack.py`` (that proof is the template for this build). It runs ONE CFPB
Reg-E-vs-FAQ deadline-mismatch slice through every stage and returns every artifact via its own ``to_dict()``,
grouped by the nine endpoint keys the projection API serves, plus an ``overview`` (stage counts + the REFERENCE
assertion that the winner is Reg E "10 business days" and the FAQ "30 days" is held out).

The motion (one fixture, one rule, every stage — identical to the full-stack proof):

  propose   LLM proposals                 → recorded as ``llm`` traces (verified=False, never truth)
  consensus multi-model run               → ``record_consensus`` → ConsensusRun (EVIDENCE; can_serve_fact=False)
  traces    the EXISTING authority         → VERIFIED ``workflow`` traces (source-grounded + receipt)
  patterns  mine repeated VERIFIED traces  → ``mine_patterns`` → PatternCandidate (verified-only)
  rules     PatternCandidate               → ``from_pattern`` → RuleCandidate (proposed, lossless link-back)
  replay    candidate vs historical traces → ``replay`` → RuleReplayReport (precision 1.0, 0 unsafe)
  shadow    candidate beside the live path → ``run_shadow`` → ShadowRunReport (live stayed authoritative)
  promotions gate (truth-serving bar)      → ``evaluate`` → RulePromotionReceipt (+ a BLOCKED counter-case)
  fallback  promoted rule serves first     → ``activate`` + ``route`` → RoutingEvent (rule-served + OOD fallback)

This is a PURE BUILDER: it imports + calls the engine (it does NOT re-implement any stage), takes an injected
``now``, uses ``hashlib`` content-addressed ids, no RNG, the engine is in-memory (no I/O, no socket, no
network), and it never mutates durable truth. The handler (``_repos/shared-backend-components/scripts/api_determinism_handler.py``) projects
this dict read-only; the page (``_repos/baltor/frontend/determinism.html``) renders it.
"""
from __future__ import annotations

from src.baltor.determinism.consensus import ModelOutput, record_consensus
from src.baltor.determinism.fallback_router import (
    REASON_OOD,
    REASON_RULE_FIRED,
    SERVED_BY_RULE,
    activate,
    route,
)
from src.baltor.determinism.pattern_miner import mine_patterns
from src.baltor.determinism.replay_engine import replay
from src.baltor.determinism.rule_candidate_generator import (
    LABEL_AUTHORITY,
    FallbackPolicy,
    from_pattern,
)
from src.baltor.determinism.rule_promotion_gate import evaluate
from src.baltor.determinism.shadow_runner import run_shadow
from src.baltor.determinism.trace_store import (
    GLOBAL_PUBLIC,
    KIND_LLM,
    KIND_WORKFLOW,
    TENANT_PRIVATE,
    TraceStore,
)

#: default injected wall-clock for the demo (deterministic; the handler may pass its own).
DEFAULT_NOW = "2026-06-05T00:00:00Z"

_TENANT = "global"          # the shared global namespace for global_public traces in this fixture
_PRIVATE_TENANT = "acme"    # a tenant whose private decisions must NEVER mint a global rule

# The CFPB reference invariant — the only answer that may ever be served, and the one that stays held out.
GOLDEN_ANSWER = "10 business days"   # Reg E (source-of-law) — winner
HELD_OUT_ANSWER = "30 days"          # FAQ summary — held out, NEVER served as truth

_DECISION_KEY = "reconcile:deadline_mismatch"
_WORKFLOW = "cfpb_reg_e_deadline"

# Three repeated VERIFIED reconciliation outcomes (same decided VALUE → the pattern the miner distills).
_VERIFIED_DECISION = {
    "winner": "Regulation E", "winner_answer": GOLDEN_ANSWER,
    "loser": "FAQ summary", "loser_answer": HELD_OUT_ANSWER, "loser_status": "held_out",
    "decided_by": "authority_precedence",
}
# the rule's evaluable inputs (replay/shadow/fallback engines read these to RE-APPLY the rule).
_VERIFIED_INPUTS = {
    "conflict_type": "deadline_mismatch",
    "authority_a": 90, "authority_b": 10,           # Reg E (source-of-law) >> FAQ summary
    "source_a": "Regulation E", "source_b": "FAQ summary",
    "higher_authority_wins": True,
}
# the rule's deterministic verdict on those inputs — what "winner = higher_authority_source" resolves to.
_VERIFIED_FINAL_DECISION = "Regulation E"

# Two models propose correctly; one is WRONG (FAQ-30 wins). These are llm traces: verified=False.
_LLM_OUTPUTS = (
    {"model": "model-a", "winner": "Regulation E", "answer": GOLDEN_ANSWER},
    {"model": "model-b", "winner": "Regulation E", "answer": GOLDEN_ANSWER},
    {"model": "model-c", "winner": "FAQ summary", "answer": HELD_OUT_ANSWER},  # a wrong proposal
)


def build_demo(now: str = DEFAULT_NOW) -> dict:
    """Run the whole Determinism Factory on the CFPB fixture and return a deterministic projection dict.

    Returns a dict keyed by the nine endpoint keys (``traces``, ``consensus``, ``patterns``, ``rules``,
    ``replay``, ``shadow``, ``promotions``, ``fallback``) plus ``overview``. Every artifact is its own
    ``to_dict()``. Pure + offline + deterministic for a fixed ``now``.
    """
    store = TraceStore()

    # ── propose — raw + structured LLM PROPOSALS (recorded, NEVER trusted) ───────────────────────────
    llm_traces = []
    for o in _LLM_OUTPUTS:
        t = store.append(
            tenant_id=_TENANT, scope=GLOBAL_PUBLIC, trace_kind=KIND_LLM, workflow_id=_WORKFLOW,
            step_id="propose", decision_key=_DECISION_KEY,
            decision={"winner": o["winner"], "answer": o["answer"]},
            model_id=o["model"], provider_id="offline-fixture", prompt_hash="sha256:fixtureprompt", now=now)
        llm_traces.append(t)

    # ── consensus — multi-model CONSENSUS as EVIDENCE, never truth ───────────────────────────────────
    run = record_consensus(
        tenant_id=_TENANT, scope=GLOBAL_PUBLIC, workflow_id=_WORKFLOW, step_id="propose",
        decision_key=_DECISION_KEY,
        outputs=[ModelOutput(model_id=o["model"], output={"winner": o["winner"], "answer": o["answer"]})
                 for o in _LLM_OUTPUTS],
        now=now)
    consensus_trace = store.append_trace(run.to_trace())

    # ── traces — the EXISTING authority/adjudication produces VERIFIED outcomes ──────────────────────
    verified_global = []
    for i in range(1, 4):
        vt = store.append(
            tenant_id=_TENANT, scope=GLOBAL_PUBLIC, trace_kind=KIND_WORKFLOW, workflow_id=_WORKFLOW,
            step_id=f"reconcile-{i}", decision_key=_DECISION_KEY, decision=dict(_VERIFIED_DECISION),
            verified=True,
            input_handles=("ctx://reg-e/1693f", "ctx://cfpb-faq/sec-3"),
            output_handles=("ctx://reg-e/1693f",),                 # the served winner's handle
            receipt_ids=(f"recon-receipt-{i}",),                   # distinct receipt per decision
            parent_trace_ids=tuple(t.trace_id for t in llm_traces),  # points at the LLM proposals it ruled on
            now=now)
        verified_global.append(vt)

    # A tenant_private VERIFIED decision — its own tenant may mine it, but it must NEVER mint a GLOBAL rule.
    private_trace = store.append(
        tenant_id=_PRIVATE_TENANT, scope=TENANT_PRIVATE, trace_kind=KIND_WORKFLOW,
        workflow_id="acme_internal_policy", step_id="reconcile-private",
        decision_key="reconcile:internal_sla", decision={"winner": "Acme SLA", "answer": "5 days"},
        verified=True, output_handles=("ctx://acme/sla",), receipt_ids=("acme-recon-1",), now=now)

    # ── patterns — MINE repeated VERIFIED decisions → PatternCandidate (verified-only; tenant boundary) ─
    patterns = mine_patterns(store, scope=GLOBAL_PUBLIC, min_support=3, now=now)
    pat = patterns[0] if patterns else None

    # ── rules — PatternCandidate → PROPOSED RuleCandidate (lossless link-back) ───────────────────────
    cand = None
    if pat is not None:
        pattern_arg = {
            "pattern_candidate_id": pat.candidate_id, "scope": pat.scope, "tenant_id": pat.tenant_id,
            "input_fields": ("conflict_type", "authority_a", "authority_b", "source_a", "source_b",
                             "higher_authority_wins"),
            "label_source": LABEL_AUTHORITY,                       # the EXISTING reconciliation authority
            "distilled_from_trace_ids": list(pat.support_trace_ids),  # LOSSLESS back-links to verified traces
            "examples": [{"conflict_type": "deadline_mismatch", "source_handles": list(pat.source_handles),
                          "winner": "Regulation E", "answer": GOLDEN_ANSWER}],
            "counterexamples": [
                {"why": "equal authority → ABSTAIN, never auto-pick", "source_handles": list(pat.source_handles)},
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
            now=now)

    # ── replay — REPLAY the candidate over historical VERIFIED traces ────────────────────────────────
    rep = None
    if cand is not None:
        replay_corpus = [
            {"trace_id": t.trace_id, "scope": GLOBAL_PUBLIC, "inputs": dict(_VERIFIED_INPUTS),
             "final_decision": _VERIFIED_FINAL_DECISION, "rule_applicable": True}
            for t in verified_global
        ]
        rep = replay(cand, replay_corpus, now=now)

    # ── shadow — SHADOW the candidate next to the live authority (recorded, non-authoritative) ───────
    shad = None
    if cand is not None:
        shadow_corpus = [
            {"trace_id": t.trace_id, "inputs": dict(_VERIFIED_INPUTS),
             "final_decision": _VERIFIED_FINAL_DECISION, "served_authority": "reconciliation.py"}
            for t in verified_global
        ]
        shad = run_shadow(cand, shadow_corpus, now=now)

    # ── promotions — the PROMOTION GATE (truth-serving bar) → RulePromotionReceipt (+ a BLOCKED case) ─
    receipt = None
    blocked = None
    if cand is not None and rep is not None and shad is not None:
        receipt = evaluate(cand, replay_report=rep, shadow_report=shad, first_promotion=True,
                           human_review_signed=True, source_traces_scope=GLOBAL_PUBLIC, now=now)
        # the gate BLOCKS a global rule minted from tenant_private traces (defence in depth, counter-case).
        blocked = evaluate(cand, replay_report=rep, shadow_report=shad, first_promotion=True,
                           human_review_signed=True, source_traces_scope=TENANT_PRIVATE, now=now)

    # ── fallback — ACTIVATE + SERVE deterministically-first, with a recorded fallback ────────────────
    served = None
    ood = None
    if cand is not None and receipt is not None and receipt.promoted:
        active_rule = activate(cand, receipt)
        served = route(active_rule, dict(_VERIFIED_INPUTS), confidence=1.0, now=now)
        # an OOD input (missing a required field) → the recorded fallback, never a fabricated fact.
        ood = route(active_rule, {"conflict_type": "deadline_mismatch"}, confidence=1.0, now=now)

    # ── assemble the projection, grouped by the nine endpoint keys ───────────────────────────────────
    trace_dicts = [t.to_dict() for t in store.query()]  # every trace (llm + consensus + verified + private)
    fallback_events = [e.to_dict() for e in (served, ood) if e is not None]
    safety_blocks = list(blocked.blocked_reasons) if blocked is not None else []

    reference = {
        "winner": "Regulation E",
        "winner_answer": GOLDEN_ANSWER,
        "held_out_loser": "FAQ summary",
        "held_out_answer": HELD_OUT_ANSWER,
        # the load-bearing REFERENCE assertion: the rule reproduces "10 business days", FAQ-30 held out.
        "served_decision": served.decision if served is not None else None,
        "served_by": served.served_by if served is not None else None,
        "served_is_reference": bool(served is not None and served.decision == _VERIFIED_FINAL_DECISION),
        "consensus_can_serve_fact": run.can_serve_fact,        # permanently False
        "pattern_winner_answer": pat.decision.get("winner_answer") if pat is not None else None,
        "pattern_loser_answer": pat.decision.get("loser_answer") if pat is not None else None,
        "label_source": cand.label_source if cand is not None else None,
        "lossless": bool(
            cand is not None and pat is not None
            and tuple(cand.distilled_from_trace_ids) == tuple(pat.support_trace_ids)),
    }

    overview = {
        "now": now,
        "workflow_id": _WORKFLOW,
        "decision_key": _DECISION_KEY,
        "stage_counts": {
            "llm_traces": sum(1 for t in trace_dicts if t["trace_kind"] == KIND_LLM),
            "consensus_runs": 1,
            "verified_traces": len(verified_global),
            "patterns": len(patterns),
            "rule_candidates": 1 if cand is not None else 0,
            "replay_reports": 1 if rep is not None else 0,
            "shadow_reports": 1 if shad is not None else 0,
            "promotions": 1 if (receipt is not None and receipt.promoted) else 0,
            "safety_blocks": len(safety_blocks),
            "served_events": len(fallback_events),
        },
        "stages": [
            {"stage": "propose (LLM)", "m": "M0/M1", "output": "llm traces", "safe": "verified=False"},
            {"stage": "consensus", "m": "M2", "output": "ConsensusRun", "safe": "can_serve_fact=False"},
            {"stage": "authority/adjudicate", "m": "M3/M4", "output": "verified traces",
             "safe": "source-grounded+receipt"},
            {"stage": "mine pattern", "m": "M5", "output": "PatternCandidate", "safe": "verified-only"},
            {"stage": "generate candidate", "m": "M5", "output": "RuleCandidate", "safe": "active=False+lossless"},
            {"stage": "replay", "m": "M5/M6", "output": "RuleReplayReport", "safe": "unsafe_FP=0"},
            {"stage": "shadow", "m": "M6", "output": "ShadowRunReport", "safe": "live authoritative"},
            {"stage": "promotion gate", "m": "M7", "output": "RulePromotionReceipt", "safe": "human-signed"},
            {"stage": "serve (fallback router)", "m": "M7", "output": "RoutingEvent", "safe": "fabricated=False"},
        ],
        "reference": reference,
        "note": ("the WHOLE Determinism Factory on one CFPB fixture: LLM proposals + consensus are EVIDENCE "
                 "(never truth); the EXISTING authority produced VERIFIED traces; the miner distilled a pattern "
                 "from VERIFIED traces ONLY; the rule was replayed + shadowed + gated and serves the Reg-E "
                 "'10 business days' winner deterministically (FAQ-30 held out)."),
    }

    return {
        "overview": overview,
        "traces": {"traces": trace_dicts, "total": len(trace_dicts)},
        "consensus": run.to_dict(),
        "patterns": {"patterns": [p.to_dict() for p in patterns], "total": len(patterns)},
        "rules": {"rules": [cand.to_dict()] if cand is not None else [], "total": 1 if cand is not None else 0},
        "replay": rep.to_dict() if rep is not None else {"available": False, "note": "no candidate to replay"},
        "shadow": shad.to_dict() if shad is not None else {"available": False, "note": "no candidate to shadow"},
        "promotions": {
            "promoted": receipt.to_dict() if receipt is not None else None,
            "blocked": blocked.to_dict() if blocked is not None else None,
            "safety_blocks": safety_blocks,  # the tenant_private→global block reason(s)
            "total": (1 if receipt is not None else 0) + (1 if blocked is not None else 0),
        },
        "fallback": {
            "events": fallback_events,
            "total": len(fallback_events),
            "served_by_rule": served.served_by if served is not None else None,
            "rule_fired": bool(served is not None and served.reason == REASON_RULE_FIRED),
            "ood_fell_back": bool(ood is not None and ood.reason == REASON_OOD),
            "fabricated": any(e.get("fabricated") for e in fallback_events),  # must be False
            "served_by_rule_const": SERVED_BY_RULE,
        },
    }
