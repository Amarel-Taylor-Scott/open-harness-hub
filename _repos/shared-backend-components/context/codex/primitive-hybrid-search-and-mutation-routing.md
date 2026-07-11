# Primitive hybrid search and mutation routing

This is the retrieval method for Teleon primitive discovery. It is candidate evidence only:
`serves_truth=false` until a separate promotion gate verifies contracts, proofs, logs, provenance, and
owner/human approval where needed.

## Goal

Find primitives efficiently without forcing an LLM to read all primitive code. Search must answer two
questions:

1. Does this primitive already match the requested capability and I/O contracts?
2. If not, can it match through a deterministic adapter/mutation, or only through a generated
   non-deterministic candidate edit?

## Index lanes

`_repos/teleon/backend/src/teleon/registry/primitive_match.py` precomputes a `blocking_profile` for each primitive row and
the registry builder persists `primitive_blocking_index.json`.

The blocking index is an inverted index over:

- exact keys: id and name
- keyword keys: enriched lexical terms with generic schema words removed
- label keys: tags, labels, capability facets, use cases
- input signatures: input shape and fields
- output signatures: output shape and fields
- graph signatures: neighboring primitive/edge ids
- mutation hints: scalar batching, output wrapping, retry/cache/rate-limit, model downshift,
  browser-to-deterministic extraction, local/API swap
- coarse semantic buckets: deterministic buckets from the lexical embedding, used only to select a
  bounded rerank set

Cheap blocking runs first. Compatibility and mutation classification run only on the bounded candidate
set.

## Compact views are hybrid artifacts

The compact LLM-facing primitive view is not the primitive and not the source of truth. It is a generated
view over the canonical registry record. It can be produced in two lanes:

- **deterministic compact view**: mechanically rendered from id/name, purpose, input/output contract,
  side effects, graph neighbors, mutation affordances, proof status, and trust tier;
- **nondeterministic enriched view**: LLM-assisted summaries, labels, examples, query expansions, or
  planning hints.

Both are useful for search. Neither serves truth by itself. Nondeterministic enrichment must remain
candidate evidence until deterministic checks confirm it still matches the source, contracts, graph
edges, proof status, and promotion record.

## Fit classes

- `exact_match`: I/O contracts line up directly; usable as a candidate graph edge.
- `deterministic_edit_match`: graph can insert deterministic adapter nodes such as
  `normalize_to_sequence_then_map`, output wrapping, explicit field rename, retry/cache/rate-limit policy,
  cost downshift, deterministic extractor candidate, or local/API swap.
- `nondeterministic_edit_match`: topic evidence is strong, but no deterministic adapter proves the bridge;
  route to `generated_adapter_candidate` / `generated_primitive_candidate` / `pipeline_ir_patch_candidate`
  with promotion blocked.
- `incompatible`: do not assemble into the graph.

## Promotion boundary

Search never promotes. Deterministic and non-deterministic edit matches require a variation record,
proof command, execution receipts/log schema, provenance/license metadata, and promotion review before
becoming trusted registry rows.

## Generated artifacts

`scripts/primitive_registry_builder.py` emits:

- `primitive_candidate_records.jsonl`
- `primitive_search_index.jsonl`
- `primitive_blocking_index.json`
- `primitive_vector_export.jsonl`
- `manifest.json`
- `summary.md`

The proof gate covers this through `scripts/check_primitive_hybrid_search.py`,
`scripts/check_primitive_registry_builder.py`, and
`scripts/check_primitive_registry_promotion_gate.py`.
