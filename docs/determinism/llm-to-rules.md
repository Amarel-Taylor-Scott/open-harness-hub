# From LLM decisions to deterministic rules

## Purpose

Describe the full distillation pipeline — how a repeated VERIFIED decision becomes a promoted,
deterministic-first rule — and make explicit the two structural invariants that keep it safe: **distill only
from verified outcomes** and **no second authority**.

## Owner

Engine: `src/baltor/determinism/` (`pattern_miner` → `rule_candidate_generator` → `replay_engine` →
`shadow_runner` → `rule_promotion_gate` → `fallback_router`). The verified-outcome front-end is
`trace_store.py`.

## The pipeline, stage by stage

```
verified workflow/adjudication traces
        │  (mining_set: verified-only, tenant-boundary enforced)
        ▼
pattern_miner.mine_patterns ──► PatternCandidate            # repeated (decision_key, decision_value), support ≥ N
        │
        ▼
rule_candidate_generator.from_pattern ──► RuleCandidate      # PROPOSED, never active; declarative decision_logic
        │                                                    # carries examples + counterexamples + MANDATORY fallback
        │                                                    # + lossless distilled_from_trace_ids + asserts_equivalence_to
        ▼
replay_engine.replay ──► RuleReplayReport                    # rule vs historical VERIFIED final_decision:
        │                                                    # precision/recall/FP/FN/abstention/unsafe/tenant-leak
        ▼
shadow_runner.run_shadow ──► ShadowRunReport                 # rule alongside the LIVE authority; recorded, never served
        │                                                    # unsafe mismatch > 0 BLOCKS promotion
        ▼
rule_promotion_gate.evaluate ──► RulePromotionReceipt        # hard AND of every safety check; risk-scaled bar
        │                                                    # PRESERVES distilled_from_trace_ids (lossless)
        ▼
fallback_router.activate + route ──► DeterministicRule + RoutingEvent   # deterministic-first; fallback never fabricates
```

### Invariant 1 — distill only from VERIFIED outcomes

A `RuleCandidate` may only descend from VERIFIED traces: `workflow`/`adjudication` traces that are
source-grounded (≥1 source handle) and receipt-backed (≥1 receipt id). This is enforced at three points so it
cannot be bypassed:

- `TraceStore.append` refuses to mark an `llm`/`consensus` trace `verified`, and refuses `verified=True`
  without a source handle AND a receipt.
- `pattern_miner.mine_patterns` reads ONLY `mining_set(require_verified=True)` — raw proposals + consensus
  runs are invisible to it.
- `rule_candidate_generator.from_pattern` raises `ConsensusOnlyError` (label from consensus alone) and
  `NoVerifiedTraceError` (no traces to link back to).

### Invariant 2 — no second authority (assert-equivalence)

A reconciliation/conflict rule does NOT re-decide truth. It carries `asserts_equivalence_to` naming the
EXISTING Baltor reference it reproduces (e.g. `scripts/artifact_graph/reconciliation.py`). The replay engine
re-applies only the rule's **declarative** `decision_logic` (`{"if": {...}, "then": <selector|literal>}`) and
SCORES it against outcomes the existing authority already produced — it never runs reconciliation or the
optimizer. The factory is a META ledger; if the rule and the authority ever diverge, the proof fails.

### The promotion gate (risk-scaled)

`rule_promotion_gate.evaluate` is a deterministic AND of: schema-valid candidate · replay report present for
THIS candidate · fallback present · source handles preserved (truth-serving) · precision ≥ the risk bar ·
**zero unsafe false positives** (truth-serving) · no tenant leak · global rule not minted from tenant_private
traces · shadow had no unsafe mismatch · `distilled_from_trace_ids` present · **human-review sign-off for the
first truth-serving promotion**. Any failed check BLOCKS promotion and is recorded in the receipt; a blocked
candidate stays `proposed`.

### Serving (deterministic-first, fallback never fabricates)

After activation, `fallback_router.route` runs the rule FIRST. It falls back when the rule is inactive, the
input is out-of-distribution (a required field missing), confidence is below `min_confidence`, or the rule
abstains. Every fallback is recorded as a `RoutingEvent` with `is_authoritative=False` and
`fabricated=False` — a fallback may abstain or escalate (gateway/human/hold-out), it may NEVER invent a fact.

## Contracts

`PatternCandidate.v1` · `RuleCandidate.v1` · `RuleReplayReport.v1` · `ShadowRunReport.v1` ·
`RulePromotionReceipt.v1` · `DeterministicRule.v1` · `FallbackPolicy.v1`.

## Inputs / Outputs

- **Inputs**: VERIFIED traces in the `TraceStore` (workflow/adjudication, source-grounded + receipt-backed).
- **Outputs**: a promoted `DeterministicRule` that serves deterministically-first with a recorded fallback,
  plus the full evidence chain (pattern → candidate → replay → shadow → receipt) — all lossless-linked back
  to the verified traces.

## Proofs

- `scripts/check_determinism_full_stack.py` — drives every stage above end-to-end and asserts both invariants.
- `scripts/check_determinism_pattern_miner.py` · `check_rule_candidate_generation.py` ·
  `check_rule_replay_engine.py` · `check_rule_shadow_mode.py` · `check_rule_promotion_gate.py` ·
  `check_deterministic_rule_fallback.py`.

## Commands

```bash
PYTHONPATH=. python3 scripts/check_determinism_full_stack.py --self-test
PYTHONPATH=. python3 scripts/check_rule_promotion_gate.py --self-test
PYTHONPATH=. python3 scripts/check_deterministic_rule_fallback.py --self-test
```

## Limitations

- The replay/shadow corpora here are fixtures. Replaying against a large historical trace store (and
  measuring drift over time) is future work behind a durable backing store.
- `decision_logic` is a small declarative form (field-equality + `higher_authority_wins` /
  `newer_version_wins` selectors). Richer rule bodies (decision tables, regex packs) are supported by the
  taxonomy but exercised minimally in this pass.

## Next

Wire the trace-store front-end to live workflow telemetry, then run the miner on real repeated decisions to
surface the next promotable slices (source classification, optimization rejection, worker routing).
