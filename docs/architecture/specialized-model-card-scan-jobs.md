# Specialized Model Card Scan Jobs

Specialized model cards should be treated as scalable source surfaces, not as
one-off examples. A model publisher has already revealed useful information
about a narrow task: task shape, input/output contract, labels, datasets,
benchmarks, limitations, base-model lineage, runtime options, and practical
usage examples. The scan job emitter turns each model signal into a deterministic
queue plan that workers can execute without downloading model weights or copying
private training data.

## Job lifecycle

Each model signal emits the same worker chain:

1. `model_repo_discovery`
2. `model_card_snapshot`
3. `model_metadata_parse`
4. `task_context_normalize`
5. `dataset_eval_linking`
6. `entity_linking`
7. `fuzzy_dedupe`
8. `primitive_index`
9. `publish_review`

This mirrors the public-source object factory, but the source unit is a model
repository, organization, collection, space, or leaderboard entry. The output is
not a trained model. The output is a set of reusable primitive candidates:
label schemas, task definitions, input/output contracts, eval harness seeds,
limitations, model replacement routes, and cost-aware routing ideas.

## Guardrails

Every emitted job carries:

- `do_not_download_weights: true`
- `do_not_store_training_data: true`
- `do_not_republish_model_card_body_without_license: true`
- `redact_before_external_model: true`
- `privacy_boundary: public_model_metadata_only`
- excluded scopes attached to the job policy
- high-impact domain review routing

The catalog can publish source metadata, citations, normalization contracts, and
derived primitive candidates. Tenant-specific captures, private model cards,
private eval traces, and proprietary training data stay outside the public hub.

## Scaling use

At scale, this worker family can scan Hugging Face, model leaderboards, package
registries, model papers, and deployment examples for evidence that a capability
is worth encoding as a reusable pipeline primitive. High-frequency patterns can
then be promoted into canonical schemas, rubrics, benchmarks, tools, and hosted
SaaS blueprint templates.

