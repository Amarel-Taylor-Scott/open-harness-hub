# ContextOps — The M0→M7 Cost-Reduction Ladder

> The economic moat, made visible: **unbounded LLM cost → a bounded research ONCE → deterministic
> verification FOREVER.**

## Purpose

Observe a deterministic sequence of verification events for a fact and compute the cost-reduction story the
dashboard tells. The module does not verify anything itself — it PRICES the motion. It turns "we replaced
asking-the-model-every-time with a deterministic path" into reproducible numbers.

## Owner

Baltor ContextOps. Single source of the ladder and its costs: `src/baltor/contextops/cost_tracking.py`.

## The ladder (the rungs)

| Rung | Event kind | Cost | Meaning |
|---|---|---|---|
| M0 | (baseline) | `LLM_BASELINE_TOKENS` | ask the LLM EVERY time — the cost we replace |
| M1 | `agent_research` | `AGENT_RESEARCH_TOKENS` | the expensive bounded discovery — happens ONCE per fact |
| M3 | `deterministic_verify` | `DETERMINISTIC_VERIFY_TOKENS` | the cheap deterministic extractor re-verify (no LLM) |
| M5 | `scheduled_hashcheck` | `HASHCHECK_TOKENS` | a scheduled watch confirms the source hasn't moved — near-zero |
| M5/M6 | `cached_fact_hit` | `CACHED_HIT_TOKENS` | served from the canonical fact + receipt — near-zero |
| — | `source_fetch` | `SOURCE_FETCH_TOKENS` | source payload fetch/refresh — cheap I/O, not an LLM call |

Every event that is NOT an `agent_research` is an LLM call the M0 world would have spent and we did not — so
`llm_calls_avoided` rises with every deterministic verify / cached hit / scheduled check.

## Inputs

- A sequence of `CostEvent(kind, fact_key, at=<injected ISO>)`. The per-event token cost is DERIVED from the
  kind (`EVENT_TOKEN_COST`) — a caller never hand-types a cost, so two events of the same kind never drift.
- `cfpb_reference_lifecycle(fact_key, now=...)` returns the canonical lifecycle (research once → deterministic
  verify → cached hit → scheduled check).

## Outputs

`CostLadderMetrics` — the moat numbers: `llm_calls_avoided`, `agent_research_runs`,
`deterministic_verifications`, `cached_fact_hits`, `source_fetches`, `scheduled_watch_runs`,
`token_cost_before` (M0 baseline = one LLM call per verification), `token_cost_after` (actual ladder spend),
`cost_per_verified_fact`, `cost_reduction_estimate` (fraction saved, 0..1). `serves_truth` is pinned False — a
cost metric is an observation, never a served fact. The ladder id is content-addressed.

## Proofs

`scripts/check_contextops_cost_reduction.py` proves: the first verification is expensive, the second is cheap
+ deterministic, a scheduled check is near-zero; `llm_calls_avoided` and `cost_reduction_estimate` both RISE as
cheap events accrue; `cost_per_verified_fact` FALLS toward the deterministic floor as the one-time research
amortizes; metrics never serve truth; the ladder id is content-addressed; an unknown event kind is an explicit
`CostTrackingError`.

## Commands

```bash
PYTHONPATH=. python3 scripts/check_contextops_cost_reduction.py --self-test
```

## Limitations

- Token costs are injected named constants — a deterministic, reproducible PROXY for cost, not a live pricing
  feed. The shape (research expensive / deterministic cheap / scheduled near-zero) is what is load-bearing.
- The baseline assumes one LLM call per verification in the M0 world; it does not model multi-turn agent loops.

## Next

- Surface the ladder on the dashboard (the moat, visible) and accumulate it across many facts.
- Feed real per-rung token counts from the runtime once worker execution lands (OPP-contextops-runtime).
