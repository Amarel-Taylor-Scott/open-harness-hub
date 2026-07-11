# Source Artifact Graph — section card

Section: `source_artifact_graph` (category: decomposition) · critical-path. This is a per-section card to the
documentation standard; the artifact-graph demo doc (`_repos/baltor/context/architecture/cfpb-artifact-graph-demo.md`) gives
the wider walkthrough.

## Purpose

A source document is not an opaque blob: it is a recursive tree of addressable, content-hashed artifacts. The
source artifact graph turns a `source_record` into that tree — a root, one `source_field` per structured
field, and (for free-text fields) a `source_block` with one `sentence` child per sentence — so every later
stage (decomposition, vectorization, conflicts, lineage) can address and track any fragment by a STABLE id
across versions, and a content-hash diff says exactly what changed when a source is re-fetched.

## Owner module

`_repos/shared-backend-components/scripts/pipeline_runtime/source_graph.py` — `SourceArtifact`, `build_cfpb_source_graph(...)`,
`diff_source_graph(...)`, `content_hash(...)`, `descendants(...)`.

## Contracts

Input: `source_record`. Output: `SourceArtifact` (a tree of content-hashed nodes). Each artifact carries a
stable identity plus a content hash, so identity is preserved across versions while the hash signals change.

## Proof scripts

`_repos/shared-backend-components/scripts/check_cfpb_source_graph_diff.py` (registered in the flywheel) — builds the CFPB source graph and
asserts the content-hash diff is deterministic and scoped to the changed nodes.

## Commands

```bash
PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_cfpb_source_graph_diff.py --self-test
```

## Limitations

The shipped builder is CFPB-shaped (`build_cfpb_source_graph`); other source families reuse the same
`SourceArtifact` tree + diff but need their own field/sentence builders. Sentence splitting is deterministic
and rule-based, not linguistic.

## Opportunities

Generalize the field/sentence builders beyond CFPB; feed graph node ids into served-fact lineage
(`OPP-vector-graph-lineage`, `_repos/shared-backend-components/architecture/opportunities.json`).
