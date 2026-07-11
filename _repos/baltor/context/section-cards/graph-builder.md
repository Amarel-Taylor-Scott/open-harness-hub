# Graph Builder — section card

Section: `graph_builder` (category: graph) · critical-path.

## Purpose

The artifact ledger holds nodes; the graph builder adds the EDGES that make it a graph — and it builds them
from deterministic rules, not a model, so the same ledger always yields the same edges. Edges encode
parent/child structure, source→fact/allegation derivation, entity mentions, same-complaint/company/product/
issue links, conclusion support, and (after reconciliation) pack inclusion / hold-out / receipt attestation.
This is what lets a served fact trace a full, auditable path back to its sources.

## Owner module

`_repos/shared-backend-components/scripts/artifact_graph/graph_builder.py` — `build_edges(...)`, `build_pack_edges(...)`. Every `edge_id` is a
deterministic hash of its endpoints + relation, so edges are content-addressed and stable.

## Contracts

Input: `ArtifactEnvelope`. Output: `artifact_edge`. Registered runtime owner `GraphBuilder`
(`_repos/shared-backend-components/architecture/runtime_ownership.json#GraphBuilder`).

## Proof scripts

`_repos/shared-backend-components/scripts/check_cfpb_deterministic_graph.py` (registered in the flywheel) — builds the CFPB graph twice and
asserts identical, rule-derived edges (no model in the loop, no RNG).

## Commands

```bash
PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_cfpb_deterministic_graph.py --self-test
```

## Limitations

Edges are rule-derived for the CFPB artifact families; new artifact types need their own edge rules.
HelixDB / FalkorDB are cataloged candidate graph substrates, not yet wired — edges live in the local ledger.

## Opportunities

Carry the deterministic graph path into served-fact lineage (`OPP-vector-graph-lineage`); add a real graph
substrate behind the same edge contract.
