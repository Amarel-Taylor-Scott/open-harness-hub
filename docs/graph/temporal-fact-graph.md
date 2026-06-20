# Temporal Fact Graph (C-GRAPH-1)

**Purpose.** A governed temporal fact graph for context reconciliation + fragile facts. It answers: what
fact was true, when it was observed/valid, when it went stale, what superseded/contradicted it, which
source authority won, which claim was held out, which reconciliation receipt decided it, and **which version
is safe to serve now**. Local-first + deterministic; Graphiti is a candidate provider, never the authority.

**Owner.** `src/baltor/graph/temporal/` (contracts · store · policy · builder · bridges) + providers in
`src/baltor/graph/providers/temporal_graph_provider.py`. Contracts: `schemas/graph/*.v1.schema.json`.

## Model
- **TemporalFactNode** — an observed assertion: subject/predicate/object + value_normalized + source_authority
  + source_handles + content_hash + first/last_observed_at + valid_from/valid_to + invalidated_at +
  **current_state** ∈ candidate · verified_current · stale · contested · superseded · held_out · tenant_override
  · needs_human · deprecated. Node id is content-addressed + deterministic (clock-independent).
- **TemporalFactEdge** — deterministic edges: OBSERVED_AS · CONTRADICTS · SUPERSEDES · HELD_OUT_BY ·
  RECONCILED_BY · VERIFIED_BY · CURRENT_VERSION_OF · TENANT_OVERRIDE_OF · IMPACTS_CONTEXT_* (20 types). Edge
  id = tenant+from+type+to+observed_at_or_policy → idempotent (rebuild never duplicates).
- **Observations** are append-only; the current projection is reconstructable from observations + policy.

## Validity semantics
observed_at (Baltor saw it) ≠ valid_from/valid_to (claim's effective window) ≠ invalidated_at (Baltor held
it out). A fact can be observed before valid, or valid historically but not current. **Superseded / held-out
≠ deleted.** Contradicted ≠ false until reconciled. Tenant override never changes the global fact. **A newer
LOWER-authority source never beats an older HIGHER-authority one** — and if the highest-authority fact goes
stale, there is NO verified_current (queued for refresh); a lower-authority claim is NEVER promoted.

## CFPB reference
`build_cfpb_temporal_graph()` → Reg E "10 business days" (source_of_law) is **verified_current**; FAQ
"30 days" (official_faq) is **held_out** (preserved + queryable). Edges: CONTRADICTS, HELD_OUT_BY,
RECONCILED_BY, VERIFIED_BY, CURRENT_VERSION_OF. The graph RECORDS the existing reconciliation authority's
decision (assert-equivalence) — it does not decide truth. Proof: `scripts/check_temporal_graph_cfpb_reference.py`.

## Bridges (record, don't replace)
- **Watchtower** (`bridges.mark_stale` / `refresh_observation`): a fragile fact → STALE (no current; FAQ
  never promoted) → verification refresh adds a NEW observation → verified_current; the old stale observation
  stays in the timeline (lossless).
- **Reconciliation** (`bridges.record_reconciliation`): writes CONTRADICTS/HELD_OUT_BY/RECONCILED_BY + receipts;
  loser held out but queryable.
- **Consumption** (`bridges.select_current_for_consumption`): serves ONLY verified_current; held_out as
  warnings; excludes stale/superseded/contested; carries observed_at + handles + receipts; tenant_private never leaks.

## Graphiti provider (candidate)
`temporal_graph.baltor_local@v1` (active authority) · `temporal_graph.graphiti@candidate` (raises
UnavailableProvider — NOT a blocker; never fabricates) · `temporal_graph.graphiti_emulator@v1` (deterministic
offline emulator, SAME contract). Graphiti may assist retrieval / propose edges; Baltor policy decides
current/safe/held-out. A missing Graphiti dependency never blocks the local graph.

## API / UI
`GET /api/graph/temporal/{facts,edges,conflicts,held-out,timeline/<key>,current/<key>,provider-status}` +
`POST /api/graph/temporal/rebuild` (projection-only; rebuild is a runtime service). Page `/temporal-graph`
(8 panels: current · held-out · contradictions · timeline · edges · held-out nodes · provider status ·
reconciliation). Proofs: `check_temporal_graph_api.py`, `check_temporal_graph_ui.py`.

## Proofs
contracts · local_store · cfpb_reference · provider_catalog · watchtower_bridge · reconciliation_bridge ·
consumption · api · ui · redteam · full_stack (`scripts/check_temporal_graph_*.py`). The full-stack proof
prints CAPABILITY | STATUS | INPUT | OUTPUT | POLICY | NOTES and asserts the reference invariant.

## Limitations / Next (OPP-temporal-graph-runtime)
Lean-but-complete core: local graph + bridges + API + UI + provider seam + proofs + docs (consolidated).
Deferred: durable `graph.temporal.*` worker commands wired to the live dispatch path, a SQLite-backed store,
a real Graphiti backend, and the per-doc split (this doc consolidates contracts/semantics/bridges/redteam).
