# Memory vs Verified Fact (the promotion boundary)

The single most important line in C-MEM-1: **a memory is not a fact.** A recalled item is a *candidate*; it
becomes servable truth **only** by passing Baltor's existing downstream gates. This doc states the boundary
and the one-way promotion path.

## Purpose

Prevent the failure mode that defines the memory-layer space: treating "the model/provider remembered it" as
"it is true and may be served." Baltor's answer is a typed claim ladder and a gated promotion path.

```
remembered   != verified      (a write is a candidate, not a checked claim)
retrieved    != served        (a search result is a candidate, not an answer)
profiled     != canonical     (a profile.static entry is candidate long-term memory, not a promoted fact)
candidate    != promoted      (only the downstream gates may promote)
```

## Owner

- The boundary type: `MemoryArtifact.v1` (`claim_status ∈ {candidate, promoted, held_out}`; a *provider*
  output may only ever be `candidate`).
- The gates that own promotion (NOT the memory layer): **VerificationGate -> Reconciliation ->
  ConsumptionGate** (the governed Consumption API).
- The read-only projection that surfaces both lanes without crossing them: `scripts/api_memory_handler.py`
  (`profile.static`/`dynamic` = candidate from a provider; `profile.promoted` = canonical from the
  Consumption API, never a provider).

## The promotion path (one-way)

```
provider.write/search/profile
        |                      claim_status = candidate
        v                      (external_source_handle + lineage + content preserved; lossless)
   MemoryArtifact (candidate)
        |
        |  ----------------------------------------------------------------------------- promotion
        |  VerificationGate     check the claim against governed sources (a recall is not evidence)
        |  Reconciliation       resolve conflicts by AUTHORITY + receipt (not recency); loser -> held_out
        |  ConsumptionGate      decide what is actually SERVED; record a portable receipt
        v
   CanonicalFact (served, with response_id + receipt lineage)   <-- the ONLY non-candidate lane
```

Nothing in the memory layer may set `served`/`canonical`/`verified`/`promoted` on its own — those are the
gates' job. The full-stack proof asserts every provider output is `candidate` and the artifact builder hard-
codes `served=False`/`canonical=False`.

## Contracts

- A `MemoryArtifact` is `candidate` until a gate promotes it; a `MemorySearchResult` entry may only be
  `candidate|held_out` (recall can NEVER mint a `promoted` fact).
- **Lossless distillation** (`docs/codex/lossless-distillation.md`): promotion never deletes the raw or the
  losers. The reconciliation loser is `held_out` (preserved + rollbackable), not forgotten; `MemoryTrace`
  records `held_out_artifact_ids`, `rejected_artifact_ids`, and a `rollback_target`.
- **No cross-tenant leakage**: a candidate carries `tenant_id` + project/container scope; promotion stays
  in-scope. The public `/memory` page shows no private memory.

## Inputs / Outputs

- In: candidate `MemoryArtifact`s from the memory layer.
- Out: at most a `CanonicalFact` per claim that passes all three gates, with a portable receipt; plus a
  preserved `held_out`/`rejected` set. A claim that fails a gate is **held out**, never served and never
  deleted.

## Proofs

- `scripts/check_memory_results_become_artifacts.py` — every provider output is a candidate, never served.
- `scripts/check_memory_provider_contract.py` — `claim_status` enum; a `served` claim is rejected; a recall
  result can only be `candidate|held_out`.
- `scripts/check_supermemory_no_truth_bypass.py` — no path lets a recall serve as canonical truth.
- `scripts/check_memory_page_projection_only.py` — the `/memory` page is a projection; `promoted` comes only
  from the Consumption API.
- `scripts/check_memory_provider_full_stack.py` — the full motion; nothing is served/canonical.

## Commands

```bash
python3 scripts/check_memory_results_become_artifacts.py --self-test
python3 scripts/check_supermemory_no_truth_bypass.py --self-test
python3 scripts/check_memory_provider_full_stack.py --self-test
```

## Limitations

- The promotion path is enforced by contract + proofs at this layer; the gates themselves
  (VerificationGate/Reconciliation/ConsumptionGate) are owned elsewhere and only *consume* candidates — the
  memory layer never calls itself promoted.
- `profile.promoted` in the projection degrades to `[]` when the Consumption layer has served nothing this
  process (it never fabricates a fact).

## Next

- When the Supermemory "Derives" vocabulary is considered, map `Derives` -> `held_out`/`candidate` (an
  inference without a source handle is never served).
- Extend `GovernedContextBench` with a **stale-fact-served rate** and **held-out-leak rate** so the boundary
  is measured, not just asserted.
