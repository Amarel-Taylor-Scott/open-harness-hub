# ContextOps Verification Foundry — Overview

> Other systems RETRIEVE context; Baltor OPERATIONALIZES it. The ContextOps Verification Foundry detects
> context that is fragile / conflicting / stale / unverifiable / under-supported, uses BOUNDED agents to
> DISCOVER the right sources & methods, converts those discoveries into DETERMINISTIC source recipes +
> verifier snippets, and drives cost from unbounded LLM tokens down to mostly-deterministic verification.

## Purpose

Tie the whole verification motion into one composable, deterministic, offline-provable loop and make the
invariant structural rather than aspirational:

**Agents DISCOVER and PROPOSE; Baltor STORES, VERIFIES, RECONCILES, PROVES, SCHEDULES, and CONSUMES.**

An agent (the deterministic `research.local_stub@v1`, or a catalog-candidate open-ended provider) may search
sources, compare candidates, suggest selectors/extraction code, and explain authority. It may NOT serve final
facts, promote canonical facts, override reconciliation, bypass source storage, or skip verification.

## Owner

Baltor ContextOps (synthesis lane). The reconciliation authority it reproduces is owned by
`scripts/artifact_graph/reconciliation.py` — the foundry never builds a second reconciliation authority.

## Inputs

- A piece of context: `fact_key` + `claim_text` + its source descriptor (`source_type` / `authority_rank` /
  `source_scope` / freshness).
- A `ResearchTask` (offline, fixture-backed in the lean core: `bounds.allowed_access=["fixture"]`,
  `secrets_allowed=False`).
- Offline source fixtures (no network in the lean core).

## Outputs

Per stage (every output pins `serves_truth` / `served_as_truth` / canonical False):

- `ContextTriageResult` — which of the twelve lanes fired + the recommended `contextops.*` command.
- `SourceDiscoveryReport` + ranked `SourceCandidate` + `SourceReliabilityScore` + a proposed `SourceRecipe`.
- `VerificationRecipe` (M3) — fact_key + input recipes + extractor id + validators + authority/cross-source/
  freshness policy.
- A `FactAssertionCandidate` from a deterministic extractor — ALWAYS a candidate, ALWAYS with a source handle.
- A reliability ranking, a cross-source confirmation result, a reconciliation receipt, and the M0→M7 cost
  ladder metrics.

## The stages (the composed loop)

`TRIAGE → RESEARCH → RECIPE → EXTRACT → RELIABILITY → CROSS_SRC → RECONCILE → COST_LADDER`

| Stage | Module | Role |
|---|---|---|
| TRIAGE | `src/baltor/contextops/triage.py` | detect — route a claim into the twelve lanes |
| RESEARCH | `src/baltor/contextops/research_stub.py` | propose — discover candidate sources offline |
| RECIPE | `source_discovery.py` + `source_recipe.py` + `verification_recipe.py` | rank + distil method (M1→M3) |
| EXTRACT | `extractor_snippets.py` (sandboxed by `sandbox_gate.py`) | deterministic candidate extraction |
| RELIABILITY | `reliability.py` | rank sources (FAQ never outranks a regulation) |
| CROSS_SRC | `cross_source_confirmation.py` | evaluate the confirmation policy |
| RECONCILE | `scripts/artifact_graph/reconciliation.py` (existing) | decide the winner deterministically |
| COST_LADDER | `cost_tracking.py` | price the moat: research once, deterministic forever |

## Proofs

- `scripts/check_contextops_full_stack.py` — prints the stage table; every stage green + the invariant.
- `scripts/check_contextops_cfpb_reference.py` — the deep end-to-end thesis proof (see `cfpb-example.md`).
- `scripts/check_contextops_cost_reduction.py` — the M0→M7 cost ladder (see `cost-reduction.md`).
- `scripts/check_contextops_redteam.py` — every attack fails safely (see `redteam.md`).
- The per-module proofs: `check_contextops_{triage,source_discovery,source_recipe,verification_recipe,`
  `extractor_snippets,reliability_scoring,cross_source_confirmation,research_agent_provider,sandbox_gate,`
  `contracts}.py`.

## Commands

```bash
PYTHONPATH=. python3 scripts/check_contextops_full_stack.py --self-test
PYTHONPATH=. python3 scripts/check_contextops_cfpb_reference.py --self-test
PYTHONPATH=. python3 scripts/check_contextops_cost_reduction.py --self-test
PYTHONPATH=. python3 scripts/check_contextops_redteam.py --self-test
```

## Limitations

- LEAN CORE only: fixtures back the correctness invariant; there is NO live network fetch, NO worker execution, NO watch
  scheduler, and NO full API/UI yet. Those are DEFERRED to `OPP-contextops-runtime`.
- The candidate open-ended research agents (Hermes/OpenClaw/Claude Code/OpenHands/Open SWE) are catalog entries
  only — never imported or executed; `research.local_stub@v1` does the work.
- The cost ladder's token costs are injected named constants (a deterministic proxy), not a live pricing feed.

## Next

- Generated-worker execution + watch scheduler + the read-only `/api/contextops/*` projection (runtime OPP).
- Fold the temporal fact graph (C-GRAPH-1) under triage to feed `is_fragile` / `is_stale`.
- Wire the cost-ladder metrics onto the dashboard so the moat is visible live.
