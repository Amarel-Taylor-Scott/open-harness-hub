# The Determinism Factory — overview

## Purpose

Convert repeated LLM / multi-LLM / heuristic / human-reviewed **decisions** into **deterministic rules**
over time, on **VERIFIED** data — so that, slice by slice, a path that needed a model call becomes a cheap,
auditable, deterministic-first rule with an LLM/human/hold-out fallback for the uncertain remainder.

It is a sibling to the Pattern & Standards Factory: that one distills repeated *code/workflow shapes*; this
one distills repeated *decision shapes* ("the LLM keeps making the same classification and the existing
deterministic validator keeps agreeing").

The core principle, stated once: **LLMs propose. Baltor verifies. Repeated VERIFIED patterns become
deterministic.**

## Owner

- Spec: `_repos/baltor/context/baltor-determinism-factory.md`.
- Engine: `_repos/baltor/backend/src/baltor/determinism/` —
  `trace_store.py` · `consensus.py` · `pattern_miner.py` · `rule_candidate_generator.py` ·
  `replay_engine.py` · `shadow_runner.py` · `rule_promotion_gate.py` · `fallback_router.py`.
- This factory is a **META observe→mine→replay→shadow→promote ledger** over the EXISTING deterministic
  authorities (`_repos/shared-backend-components/scripts/artifact_graph/reconciliation.py` + `conflict_detector.py`, the optimizer, the
  consumption gate). It does **not** create a second reconciliation authority, optimizer, rule engine, or
  LLM gateway.

## The maturity ladder (M0–M8)

Every non-deterministic slice climbs the same ladder. A slice may stop climbing at any rung; it only reaches
M7/M8 when the proofs clear the risk-scaled bar.

| Rung | State | Engine module |
|---|---|---|
| **M0** | raw LLM output (risky, no schema) | `trace_store` (`llm` trace, `verified=False`) |
| **M1** | LLM output + JSON schema (structured, not trusted) | `trace_store` (`llm` trace) |
| **M2** | multiple LLMs produce candidates; agreement/disagreement recorded | `consensus.record_consensus` → `ConsensusRun` (`can_serve_fact=False`) |
| **M3** | candidates checked by deterministic validators (handles/schema/policy/conflict) | the EXISTING validator → `workflow` trace, `verified=True` |
| **M4** | human/policy adjudication → VERIFIED label (becomes training/eval data) | `adjudication` trace, `verified=True` |
| **M5** | pattern miner proposes a deterministic rule; tested against historical traces | `pattern_miner` → `rule_candidate_generator` → `replay_engine` |
| **M6** | rule runs in **shadow** (rule result vs live authority), recorded, non-authoritative | `shadow_runner` → `ShadowRunReport` |
| **M7** | rule **promoted**: deterministic-first, LLM/human/hold-out fallback only for uncertain cases | `rule_promotion_gate` → `RulePromotionReceipt`; `fallback_router` serves |
| **M8** | LLM retired for this slice: rule + proof + monitoring own the path | `DeterministicRule.status = "retired"` (rule kept, fallback owns it) |

## The four non-negotiable semantics

1. **Distill ONLY from VERIFIED outcomes** — adjudicated, source-grounded (≥1 source handle), receipt-backed.
   Never from raw/ungrounded LLM output, allegations-as-facts, reversed conflicts, stale facts, or outputs
   without handles. Enforced structurally: the trace store refuses to mark an `llm`/`consensus` trace
   `verified`, and the miner reads ONLY verified traces.
2. **Consensus ≠ truth** — multi-LLM agreement is an evidence/ambiguity signal, never a label. See
   `consensus-is-not-truth.md`. `ConsensusRun.can_serve_fact` is permanently `False`; consensus traces are
   `verified=False`, so the miner cannot distill a rule from them.
3. **No second authority** — a reconciliation/conflict rule **asserts-equivalence** to the existing Baltor
   reference; it reproduces, it never replaces. See `llm-to-rules.md` and `cfpb-example.md`.
4. **Lossless** — a promoted deterministic rule NEVER deletes the LLM/consensus/adjudication traces it was
   distilled from; the rule (and its `RulePromotionReceipt`) links back via `distilled_from_trace_ids`. The
   `_repos/baltor/backend/src/baltor/distillation` subsystem rehydrates them. Tenant-private traces cannot create global rules
   unless anonymized + approved.

## Promotion bar scales with risk

| Rule class | Bar |
|---|---|
| **truth-serving** (selects/serves a fact) | precision == 1.0, unsafe false positives == 0, source handles preserved, fallback exists, **human review for first promotion** |
| **routing** (routes work only) | looser precision bar (≥0.95), no unsafe-FP gate (a misroute is recoverable via the fallback), no human review required |

## Contracts

`WorkflowTrace` · `LLMTrace` · `ConsensusRun` · `AdjudicationRecord` · `PatternCandidate` ·
`RuleCandidate` · `RuleReplayReport` · `ShadowRunReport` · `DeterministicRule` ·
`RulePromotionReceipt` · `FallbackPolicy` (schemas under `_repos/shared-backend-components/schemas/determinism/`).

## Inputs / Outputs

- **Inputs**: decision traces — LLM proposals, multi-model runs, and the VERIFIED outcomes the existing
  authorities/adjudicators already produced (with source handles + receipts).
- **Outputs**: `PatternCandidate`s → proposed `RuleCandidate`s → `RuleReplayReport` + `ShadowRunReport` →
  `RulePromotionReceipt` → an active `DeterministicRule` served deterministically-first with a recorded
  fallback. Every served decision is a `RoutingEvent` that feeds future mining.

## Proofs

- End-to-end driver: `_repos/shared-backend-components/scripts/check_determinism_full_stack.py` — walks M0→M7 on one CFPB fixture and asserts
  every semantic above.
- Per-stage: `check_trace_store` · `check_consensus_recorder` · `check_determinism_pattern_miner` ·
  `check_rule_candidate_generation` · `check_rule_replay_engine` · `check_rule_shadow_mode` ·
  `check_rule_promotion_gate` · `check_deterministic_rule_fallback`.
- Applied distillations: `check_cfpb_reconciliation_rule_distillation` ·
  `check_source_classification_rule_distillation` · `check_optimization_rejection_rule_distillation`.
- Adversarial: `check_determinism_redteam` (every attack must FAIL SAFELY).
- Contracts: `check_determinism_contracts`.

## Commands

```bash
PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_determinism_full_stack.py --self-test
PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_determinism_redteam.py --self-test
PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_cfpb_reconciliation_rule_distillation.py --self-test
```

Each proof is `--self-test`, fully offline (no model is ever called), uses injected time + `hashlib`
content-addressed ids + no RNG, and exits 0/1.

## Limitations

- This pass builds the CORE engine + 3 applied distillations + red-team. The `/api/determinism` routes and
  the `/determinism` UI panels (spec PART 13) are DEFERRED to an opportunity — see `registrations_needed`.
- The proofs run over fixtures / in-memory stores. Wiring the trace store to live workflow telemetry and a
  durable backing store is future work.
- Promotion is gated but the *operational* monitoring loop (M8 retire + drift alarms on a live slice) is
  specified, not yet wired to a running monitor.

## Next

1. MAIN registers the proofs in `_repos/shared-backend-components/scripts/baltor_flywheel.py`, the matrix section, the contract registry
   `artifact_types`, and an opportunity for the deferred API/UI.
2. Add the `/api/determinism/{traces,patterns,rules,replay-reports,shadow-reports,promotions}` projection and
   the `/determinism` ledger UI (PART 13) under the new opportunity.
3. Wire the trace store front-end to real workflow telemetry and add an M8 retire + monitoring loop.
