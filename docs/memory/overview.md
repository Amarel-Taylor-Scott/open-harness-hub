# Governed Memory — Overview (C-MEM-1)

Baltor adds a memory/context layer the way it adds every external capability: **behind a port, with a
working offline fallback, as a candidate provider — never as the source of truth.** Supermemory is the
upstream that inspired the shape; the correctness invariant runs with **no credentials and no network**.

## Purpose

Give Baltor a tenant-scoped memory/recall/profile capability (remember an item, recall it later, project a
profile) while preserving every governance line: a recalled item is a **candidate `MemoryArtifact`**, not a
served or canonical fact. The architecture exists to make `remembered != verified`, `retrieved != served`,
`profiled != canonical`, and `candidate memory != promoted fact` typeable and provable, not aspirational.

## Owner

- **Port:** `src/baltor/ports/memory_provider.py` (`MemoryProviderPort`, `MemoryProfileProviderPort`,
  `MemoryMCPProviderPort`, `UnavailableProvider`).
- **Artifact builder (single source of the artifact shape):** `src/baltor/adapters/memory/__init__.py`
  (`make_memory_artifact`, `memory_content_hash`, `external_source_handle`).
- **Working providers:** `src/baltor/adapters/memory/baltor_local.py` (active local store),
  `src/baltor/adapters/memory/supermemory_emulator.py` (deterministic offline emulator).
- **Candidate contract stubs:** `src/baltor/adapters/memory/supermemory_api.py`,
  `src/baltor/adapters/memory/supermemory_mcp.py` (raise `UnavailableProvider` without creds — never import
  the SDK, never call out).
- **Projection (read-only):** `scripts/api_memory_handler.py` + the `/memory` page at
  `web/baltor/memory.html`.

## Architecture

```
                      MemoryProviderPort / MemoryProfileProviderPort / MemoryMCPProviderPort
                                              |
         +----------------------+-------------+-----------------+--------------------------+
         |                      |                               |                          |
  baltor_local@v1        supermemory_emulator@v1        supermemory_api@candidate   mcp.supermemory@candidate
  (active, offline)      (emulated, offline)            (CANDIDATE stub)            (CANDIDATE stub)
  correctness invariant            correctness invariant                    UnavailableProvider          UnavailableProvider
         |                      |                       (no creds, no SDK, no net)   (no creds, no SDK, no net)
         +----------+-----------+
                    |
        make_memory_artifact  ->  MemoryArtifact (claim_status=candidate, external_source_handle, lineage)
                    |
        api_memory_handler (read-only PROJECTION)  ->  /memory page
                    |
        (promotion ONLY downstream)  ->  VerificationGate + Reconciliation + ConsumptionGate  ->  CanonicalFact
```

The `/memory` page is a **projection** over the providers: it shows candidate artifacts, the provider status
list, traces, and the connector roadmap. It computes no truth and shows no private memory; the only
non-candidate lane it surfaces (`profile.promoted`) comes from the governed Consumption API, not a provider.

## Contracts

- Seven schemas under `schemas/memory/` (`MemoryArtifact`, `MemoryWriteRequest`, `MemorySearchRequest`,
  `MemorySearchResult`, `MemoryProfile`, `MemoryTrace`, `MemoryProviderStatus`) — each with a valid + an
  invalid example.
- `MemoryArtifact.v1` requires `external_source_handle`, `tenant_id`, `scope`/`project`, `container`,
  `claim_status`, `content`, `provider_id`, `lineage`, `created_at`. `claim_status ∈ {candidate, promoted,
  held_out}`; a provider output may only ever be `candidate`.
- Every provider output carries `tenant_id` + project/container scope + a populated `external_source_handle`
  (the upstream id) + `lineage`. Tenant isolation is structural (per-scope store), not a filter.

## Inputs

`MemoryWriteRequest` (`tenant_id`, `project`, `content`, `now`, `metadata?`, `container_tags?`),
`MemorySearchRequest` (`tenant_id`, `project`, `query`, `now`, `limit?`, `search_mode?`), and a profile scope
(`tenant_id`, `project`, `now`, `limit?`). `now` is always **injected** — no wall-clock, so output is
deterministic.

## Outputs

Governed candidate `MemoryArtifact` records (write/search/profile), a `MemorySearchResult` envelope,
a `MemoryProfile` (`static` + `dynamic`), a `MemoryProviderStatus` per provider, and a `MemoryTrace` per
operation (auditable + reversible: `rollback_target` always recorded; `held_out`/`rejected` preserved).

## Proofs

- `scripts/check_memory_provider_contract.py` — the seven schemas + governance boundary.
- `scripts/check_local_memory_provider.py`, `scripts/check_supermemory_emulator.py` — the working providers.
- `scripts/check_memory_results_become_artifacts.py` — every output is a candidate, stubs fail closed.
- `scripts/check_memory_tenant_project_scoping.py` — no cross-tenant leak.
- `scripts/check_supermemory_candidate_catalog.py` — Supermemory is cataloged **candidate** with a
  fallback/stub + contract_tests, never active.
- `scripts/check_memory_provider_full_stack.py` — the whole stack end-to-end, offline, no creds.
- `scripts/check_memory_api.py`, `scripts/check_memory_page_projection_only.py`,
  `scripts/check_no_direct_supermemory_imports.py`, `scripts/check_supermemory_no_truth_bypass.py`,
  `scripts/check_memory_trace_written.py`.

## Commands

```bash
python3 scripts/check_memory_provider_full_stack.py --self-test
python3 scripts/check_supermemory_candidate_catalog.py --self-test
python3 scripts/check_memory_provider_contract.py --self-test
```

## Limitations

- The candidate api/mcp adapters are **contract stubs**: with creds present they still raise
  `UnavailableProvider` (no live network impl is wired in this build). The emulator/local provider is the
  working impl.
- The local store and emulator are in-process — state does not persist across processes (it is a projection
  cache, not a durable truth store; canonical truth lives downstream).
- Search is deterministic term-overlap scoring, not a learned ranker.

## Next

- When a live Supermemory impl is wired behind `supermemory_api`/`supermemory_mcp`, its outputs MUST still be
  candidate `MemoryArtifact`s — the contract surface + artifact shape do not change.
- Catalog the connectors (GDrive/Gmail/Notion/OneDrive/GitHub/Web Crawler) as candidates behind the
  `SourceAdapterPort` (see `docs/memory/supermemory-candidate.md`).
- Stand up a `GovernedContextBench` assurance benchmark (source-handle coverage, held-out-leak rate,
  stale-fact-served rate) — the assurance-axis answer to MemoryBench.
