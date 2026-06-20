# Applied example — CFPB Reg-E-vs-FAQ deadline reconciliation

## Purpose

Walk one concrete slice all the way up the ladder so the abstract pipeline is legible: the CFPB Regulation-E
vs. FAQ-summary **deadline-mismatch** conflict. The mined deterministic rule must **reproduce** the existing
reference — Reg E "10 business days" wins, FAQ "30 days" is held out — without becoming a competing source of
truth, and without ever needing an LLM/consensus trace for the truth.

## Owner

Engine: `src/baltor/determinism/`. The existing reference authority it asserts-equivalence to:
`scripts/artifact_graph/reconciliation.py` (+ `conflict_detector.py`). Applied proofs:
`scripts/check_cfpb_reconciliation_rule_distillation.py` (against the real runtime) and
`scripts/check_determinism_full_stack.py` (against the engine, end-to-end).

## The reference invariant

> Answer = **"10 business days"** (Regulation E — source-of-law). The FAQ summary's **"30 days"** is the
> held-out loser; it is NEVER served as truth. This holds at every rung of the ladder.

## The slice, rung by rung

| Rung | What happens here |
|---|---|
| **M0/M1** | Models propose a winner. One proposal is even WRONG (says FAQ-30 wins). Recorded as `llm` traces, `verified=False`. |
| **M2** | A multi-model `ConsensusRun` records agreement 0.67 with a recorded disagreement cluster (the dissenter). `can_serve_fact=False` — consensus is evidence; the dissent is an ambiguity flag, not a vote. |
| **M3/M4** | The EXISTING deterministic authority decides: Reg E (source-of-law, higher authority) beats the FAQ summary; FAQ-30 is held out. Recorded as VERIFIED `workflow` traces — source-grounded (`ctx://reg-e/1693f`) and receipt-backed (`recon-receipt-*`). |
| **M5** | The miner sees the same VERIFIED decision repeated (support ≥ 3) → a `PatternCandidate`. It is built ONLY from the verified traces — no `llm`, no `consensus`, no tenant_private trace. |
| **M5** | `from_pattern` proposes a `reconciliation_policy_rule`: `IF conflict_type == "deadline_mismatch" AND higher_authority_wins THEN winner = higher_authority_source, loser = held_out`. It is PROPOSED (not active), carries `asserts_equivalence_to = reconciliation.py`, and links back to the verified traces (`distilled_from_trace_ids`). |
| **M5/M6** | Replay over the historical verified traces → precision 1.0, **0 unsafe**, 0 tenant-leak. The rule reproduces the reference. |
| **M6** | Shadow alongside the live authority → 0 unsafe mismatch, the live path stayed authoritative, agreement 1.0. |
| **M7** | The promotion gate (truth-serving bar) PROMOTES — human-signed for the first promotion — and the receipt PRESERVES `distilled_from_trace_ids`. |
| **M7** | The active rule serves the Reg-E winner **deterministically** (no model call); an OOD input falls back without fabricating. |

## What this example proves about the semantics

- **Consensus never served the fact.** The dissenting model and the 0.67 agreement are recorded as evidence;
  the served answer came from the authority/verified label. `can_serve_fact` stayed `False` throughout.
- **No second authority.** The rule's verdict is checked AGAINST `reconciliation.reconcile(...)` on the same
  fixture (in `check_cfpb_reconciliation_rule_distillation`); if they ever diverge the proof fails. The rule
  reproduces the reference; it does not re-decide it.
- **Lossless.** After promotion, every `distilled_from_trace_id` is still present in the trace store — the
  LLM/consensus/adjudication traces the rule descended from are never deleted.
- **Tenant-private never global.** A tenant_private VERIFIED decision (`acme` internal SLA) is excluded from
  the global mining set, and forcing it through the gate is BLOCKED.
- **Reference held.** The served deadline answer is "10 business days" ONLY; FAQ-30 is the held-out loser, M0→M7.

## Contracts

`ConsensusRun.v1` · `WorkflowTrace.v1` · `PatternCandidate.v1` · `RuleCandidate.v1` · `RuleReplayReport.v1` ·
`ShadowRunReport.v1` · `RulePromotionReceipt.v1` · `DeterministicRule.v1`.

## Inputs / Outputs

- **Inputs**: the CFPB conflict + the existing authority's verified reconciliation outcome (Reg E beats FAQ).
- **Outputs**: a promoted `reconciliation_policy_rule` that deterministically serves "10 business days",
  with the full lossless evidence chain back to the verified traces.

## Proofs

- `scripts/check_cfpb_reconciliation_rule_distillation.py` — assert-equivalence to the REAL runtime reference.
- `scripts/check_determinism_full_stack.py` — the same slice driven through the ENGINE end-to-end (M0→M7).
- `scripts/check_determinism_redteam.py` — the "serve FAQ-30 as truth" attack FAILS SAFELY.

## Commands

```bash
PYTHONPATH=. python3 scripts/check_cfpb_reconciliation_rule_distillation.py --self-test
PYTHONPATH=. python3 scripts/check_determinism_full_stack.py --self-test
```

## Limitations

- This slice is a single, well-separated authority gap (source-of-law beats a summary). Slices with *equal*
  authority, novel conflict types, or semantic contradictions without a clear numeric/date mismatch correctly
  ABSTAIN and stay on the LLM/human path — they are not (yet) promotable.
- The full-stack proof exercises the engine on a fixture; the applied proof exercises the real runtime. Both
  assert the same reference, but neither yet runs over a large historical corpus.

## Next

Once the trace-store front-end is wired to live telemetry, replay this rule against the accumulated historical
CFPB decisions to confirm precision holds at scale, then extend the same ladder to source-classification and
optimization-rejection slices (their applied proofs already exist).
