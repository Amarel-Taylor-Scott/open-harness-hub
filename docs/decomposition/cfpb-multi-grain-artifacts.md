# CFPB Multi-Grain Artifacts

One CFPB complaint record does not decompose into a single kind of thing. It
contains structured facts, free-text allegations, machine interpretations, and
derived conclusions — and treating those as the same thing is exactly how a
context layer ends up serving an allegation as if it were a verified fact. The
Context Engine therefore emits **distinct artifact types with distinct
governance** from one record, each carrying full lineage back to its source.

Implementation: `scripts/pipeline_runtime/cfpb_artifacts.py` and the type
registry `scripts/pipeline_runtime/artifact_types.py`. Held in place by
`check_cfpb_multi_grain_artifacts.py` and `check_artifact_type_registry.py`
(both green).

## Why facts, allegations, conclusions, and signals are separate types

The four "claim-shaped" types look superficially similar — they are all short,
sentence-sized statements about the world — but they have very different
epistemic status, so they are deliberately separate types in the registry
(`CLAIM_SHAPED`) and the proof asserts their `governance_key()` values stay
distinct (no silent conflation):

- An **`atomic_fact`** comes from a structured source field (e.g. the company
  name, the product). It is source-grounded and verifiable.
- A **`narrative_allegation`** is a sentence from the consumer's free-text
  narrative. It is source-grounded — the consumer really said it — but it is an
  *unverified claim*, not an established fact. A semantically similar allegation
  is still not a fact.
- A **`conclusion`** is *derived* — the engine produced it by reasoning over
  facts and allegations. A derived statement is not a fact and must cite the
  artifacts that support it.
- An **`emotion_signal`** is a *model interpretation* of the narrative's
  sentiment. A model's reading of tone is neither source-grounded nor a fact.

Keeping them as separate types means the governance flags — `can_be_used_as_fact`,
`promotion_eligible_default`, `requires_human_review` — attach to the *type*, so
the system can never serve an allegation or a model signal under the authority
of a fact.

## Governance defaults for the four claim-shaped types

Defaults from `REGISTRY` (a run may be *more* restrictive, never looser):

| Type | source_grounded | derived | model_dependent | promotion_eligible_default | requires_human_review | can_be_used_as_fact | retention_class |
|---|---|---|---|---|---|---|---|
| `atomic_fact` | yes | no | no | **yes** | no | **yes** | standard |
| `narrative_allegation` | yes | no | no | no | **yes** | no | standard |
| `conclusion` | no | yes | no | no | **yes** | no | standard |
| `emotion_signal` | no | yes | **yes** | no | no | no | **ephemeral** |

(`atomic_fact` mirrors `source_field`, the structured leaf that is the only
other type with `can_be_used_as_fact = True`.) `emotion_signal` is the only one
that is model-dependent, and it is `ephemeral` — a transient interpretation, not
a record of fact.

## The lineage every derived artifact carries

`build_cfpb_artifacts` produces `DerivedArtifact`s through the `_derived`
helper, and every one carries full lineage:

- `source_artifact_ids` — the source-graph artifact(s) it was derived from (a
  fact points at its `source_field`; an allegation at its `sentence`);
- `pipeline_id` + `pipeline_version`;
- `processor_id` + `processor_version` (`processor_ref` = `id@version`);
- `config_hash` — the producing `ProcessorSpec.fingerprint()`;
- `run_id`, `tenant_id`, and the security envelope (`security_json`);
- `citations` — for assembled types, the supporting artifact ids (a
  `conclusion` cites its facts and allegations; a `context_pack` cites what it
  serves; a `receipt` cites its pack).

`DerivedArtifact.lineage_complete()` requires `tenant_id`, `run_id`,
`pipeline_id`, `pipeline_version`, `config_hash`, and a non-null
`source_artifact_ids`. Governance comes from the registry:
`promotion_eligible` defaults to the type's
`promotion_eligible_default` unless a run overrides it downward.

## Model-dependent artifacts must record processor metadata

The registry's `requires_processor_metadata` is `True` exactly when a type is
`model_dependent` — a model interpretation is meaningless without the
`processor_id@version` and config that produced it. `cfpb_artifacts.py` enforces
this for `emotion_signal`, which is produced by the `EMOTION`
(`emotion.lexicon@v1`) processor and asserts both `processor_ref` and
`config_hash` are present before it is emitted. The `conclusion` likewise
asserts it cites at least one supporting artifact. The `PRODUCER` map records
which processor owns each grain, which is what lets the reprocessing planner
scope a processor-version bump to just that grain and its downstream (see
`docs/architecture/source-pipeline-artifact-versioning.md`).

## Extends, does not replace, decompose_structured

This is an *extension* of the existing structured decomposition, not a
rewrite. `build_cfpb_artifacts` calls `build_cfpb_source_graph` (which itself
reuses `CFPB_LABELS`, `CFPB_NARRATIVE_FIELDS`, and `sentence_chunks` from
`scripts/ingest/decompose_structured.py`) and `decompose_cfpb_complaint`, then
wraps each decomposed component as a typed, governed, lineaged
`DerivedArtifact`. The `CLAIM_FACT` distinction that
`decompose_structured.py` already draws becomes the split between `atomic_fact`
and `narrative_allegation`, and `_sentiment` becomes the `emotion_signal`
payload. The existing decomposition stays the single source of the segmentation;
the multi-grain layer adds the type system, governance, and lineage on top.
