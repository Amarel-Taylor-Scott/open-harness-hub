# Vectorization — section card

Section: `vectorization` (category: retrieval) · critical-path.

## Purpose

Atomic facts must be retrievable by similarity, not just by id. Vectorization embeds each `atomic_fact` into a
fixed-dimension vector and supports nearest-neighbour search — proving the full vector lifecycle (artifact →
vector → nearest-neighbour → graph linkage) with NO network and NO paid API, so the correctness invariant stays
offline and byte-for-byte deterministic.

## Owner module

`_repos/shared-backend-components/scripts/artifact_graph/vector_store.py` — `VectorProvider` (port), `DeterministicLocalVectorProvider`
(hashes a lexical bag-of-words into a fixed-dimension, L2-normalised vector), `vectorize_artifact(...)`,
`vectorize_into_ledger(...)`, `search_similar(...)`.

## Contracts

Input: `atomic_fact`. Output: `object_embedding`. The `VectorProvider` seam is swappable: a real embedding
model (sentence-transformer / hosted endpoint) replaces the deterministic local provider without touching
callers.

## Proof scripts

`_repos/shared-backend-components/scripts/check_cfpb_vectorization.py` (registered in the flywheel) — embeds CFPB atomic facts, asserts vectors
are stable across runs, and that nearest-neighbour search returns the expected related facts.

## Commands

```bash
PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_cfpb_vectorization.py --self-test
```

## Limitations

The default provider is a deterministic lexical hash, not a learned embedding — it proves the lifecycle and
the seam, not semantic quality. Qdrant / pgvector are cataloged candidate substrates
(`_repos/shared-backend-components/architecture/external_capability_catalog.json#hybrid_retrieval`), not yet wired.

## Opportunities

Wire a real embedding provider behind `VectorProvider`; embed the vector id into served-fact lineage
(`OPP-vector-graph-lineage`).
