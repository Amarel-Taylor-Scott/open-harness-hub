# Specialized Model Signal Surfaces

Task-specific models are high-value source signals for Open Harness Hub because a publisher has already spent time collecting data, defining labels, choosing metrics, and validating a narrow capability. The model weights are useful, but the surrounding context is often more reusable: task definitions, label schemas, datasets, preprocessing assumptions, examples, metrics, failure modes, intended-use boundaries, and deployment notes.

This means a fine-tuned model repo can be mined into knowledge objects and pipeline primitives even when the hub does not host or call the model. A general LLM, retrieval stack, evaluator, or cheap classifier can reuse the captured context to build an approximate workflow, route uncertain cases to a specialist model, or decide that specialist training is justified.

## Why this matters

Hugging Face model cards explicitly support metadata and text sections for intended use, limitations, training parameters, datasets, evaluation results, base models, licenses, and pipeline tags. Hugging Face task metadata also describes the input/output shape of a model API. Those fields map directly into hub primitives:

- Task definition object: what the model is trying to do.
- Label schema object: expected classes, spans, answer types, or generated components.
- Input/output contract: modality, required fields, accepted file types, and response format.
- Dataset context pack: public dataset names, citations, collection notes, and known limits.
- Evaluation harness seed: benchmark names, metrics, thresholds, and reproducibility fields.
- Failure-mode object: limitations, out-of-scope uses, bias notes, and required human review.
- Model replacement guide: base model, fine-tune relation, adapter/quantization lineage, and runtime requirements.
- Cost-saving route: when retrieval, prompting, small classifiers, or specialist models should run.

## Source surfaces to scan

Start with model repositories and organization pages where specialization is visible through task tags, domain tags, datasets, and model trees:

- Hugging Face model cards, especially cards with `pipeline_tag`, `datasets`, `base_model`, `model-index`, eval metrics, and paper links.
- Hugging Face organization pages that publish many narrow models, such as OpenMed clinical token-classification and medical PII models.
- Domain model cards such as MedGemma for healthcare text/image baselines, FinBERT for financial sentiment, LEGAL-BERT for legal language, CodeBERT for code/search/documentation tasks, and LayoutLM-family models for document understanding.
- Leaderboards and benchmark spaces that reveal recurring task families and benchmark names.
- Dataset cards connected to the model card metadata.
- Paper pages and official repositories linked from the model card.

## Normalization contract

Each candidate model signal should emit:

| Field | Purpose |
| --- | --- |
| `source_model_id` | Stable upstream model identifier, usually `org/name`. |
| `publisher` | Organization or author namespace. |
| `task_shape` | Coarse task type and input/output contract. |
| `domain_signal` | Industry, subdomain, language, jurisdiction, or modality clues. |
| `training_context` | Datasets, corpus descriptions, labeling method, pretraining/fine-tune relation. |
| `eval_context` | Metrics, benchmark names, eval datasets, run date if available. |
| `labels_or_outputs` | Classes, entity types, answer format, generated component format. |
| `limitations` | Out-of-scope uses, validation warnings, bias notes, safety notes. |
| `reusable_primitives` | Hub primitive types that can be generated from the model context. |
| `replacement_routes` | Prompt/RAG/small-model/specialist-model deployment options. |
| `review_priority` | Higher when the model handles safety, health, legal, finance, privacy, or high-impact decisions. |

## Priority heuristic

Specialized model signals should be prioritized when they satisfy several of these conditions:

- The model exists because an out-of-box LLM underperforms on the task.
- The model card exposes label schemas, datasets, or eval metrics.
- The task appears repeatedly across organizations, spaces, papers, datasets, or benchmarks.
- The model handles regulated or high-consequence domains where context and validation matter.
- The model is cheap to replace with prompt/RAG/evaluator scaffolding for many users.
- The model can become a routing primitive: cheap first pass, specialist second pass, human review on uncertainty.

This does not imply copying proprietary data or model weights. The hub stores public metadata, citations, context summaries, reusable task contracts, and synthetic examples unless a publisher explicitly provides broader rights.

