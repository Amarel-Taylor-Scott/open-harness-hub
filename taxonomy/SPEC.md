# Open Harness Hub — Taxonomy Specification

> Version: 0.1.0
> Status: Draft for public review
> Audience: Authors of harness/pipeline/benchmark catalogs

This document defines the controlled vocabulary, artifact types, and
manifest fields used by the Open Harness Hub. Every entry in `catalog/`
must conform to one of the artifact schemas in `schemas/`.

The taxonomy is industry-agnostic. Industry-specific terms (e.g.
*corridor profile*, *medical-coding rule*, *financial-crime indicator*) are
modeled as **leaf instances** of generic types, not as new top-level
categories.

---

## 1. Layers and primitives

The hub describes AI systems at four layers. Lower layers are the
building blocks of higher layers.

```
Layer 4 — Benchmarks & Evaluations
              ▲
Layer 3 — Pipelines (compositions of harnesses + rules + tools)
              ▲
Layer 2 — Harnesses (named workflows around a model or trust boundary)
              ▲
Layer 1 — Knowledge packs · Logic packs · Rule packs · Tools · Personas · Adapters · Schemas
```

Cross-cutting: **Datasets** can live at any layer; **Rubrics** are logic
packs but get their own top-level catalog because they are central to
evaluation; **Adapters** are how a harness talks to a model.

### 1.1 Knowledge pack

A typed bundle of *facts*. Read by harnesses; never holds logic.

Examples: a RAG corpus of statutes; a directory of NGO hotlines; a table
of fee caps by jurisdiction; a citation graph; a glossary; a contact pack.

Files: a `manifest.yaml` plus one or more typed data files
(`*.jsonl`, `*.yaml`, `*.csv`, `*.md`).

### 1.2 Logic pack

A typed bundle of *behavior*. Read by harnesses; never holds facts.

Examples: a persona system prompt; a tool registry; a response schema;
a refusal-style policy; a rubric definition; a prompt template family.

### 1.3 Rule pack

A modular bundle of one **rule family**. A rule pack is a kind of logic
pack with a known schema.

| Family | Identifier | Shape |
|---|---|---|
| GREP | `grep` | List of `(id, pattern, severity, category, fires_what)` regex rules. |
| Glob | `glob` | List of `(id, pattern, applies_to)` filepath/text patterns. |
| Classifier | `classifier` | List of `(id, label, examples, threshold)` rules used by lightweight classifiers. |
| Heuristic | `heuristic` | List of `(id, condition, action)` deterministic decisions. |
| RAG | `rag` | A corpus + index spec + retrieval policy (`bm25`, `dense`, `rrf`). |
| Citation | `citation` | A graph of citation edges between RAG documents. |
| Online search | `online_search` | Allowlist/blocklist/per-source policy + sanitization + freshness window for outbound web search. |
| PII / privacy | `privacy` | Detection patterns + redaction recipes. |
| Schema | `schema` | JSON Schemas / Pydantic equivalents enforced at I/O boundaries. |
| Routing | `routing` | Conditional dispatch — which harness should handle which input. |

A rule pack is identified by `(family, slug, version)`. New families can be
proposed; the hub keeps the family list small and documented.

### 1.4 Tool

A **function-call** definition usable by any model that supports tool use.

A tool manifest declares:

- `name`, `description`, `parameters` (JSON Schema)
- `returns` (JSON Schema)
- `side_effects` (none | read | write | external_call)
- `trust_boundary` (local | hub | external)
- `examples` (golden input/output pairs)
- `implementations` (zero or more references — Python callable path, HTTP
  endpoint spec, shell command, MCP server, OpenAPI op, etc.)

A tool can exist without an implementation; it then describes a contract
others can implement.

### 1.5 Persona

A character or role frame the model adopts at the start of a workflow.
Personas are logic packs with a constrained schema:

- `system_prompt` (markdown)
- `role`, `domain`, `tone`, `refusal_style`
- `extends` (optional — inherit from a base persona)

### 1.6 Model adapter

A **provider-neutral transport** for talking to a model. Adapter manifests
declare:

- `transport`: `none` · `callable` · `transformers` · `unsloth` ·
  `llama_cpp` · `ollama` · `openai_compatible` · `anthropic` ·
  `google_gemini` · `hf_inference_endpoint` · `frontier_api` ·
  `gemma_runtime` · `local_only`
- `capabilities`: `text_generation` · `chat` · `tool_use` ·
  `vision_in` · `audio_in` · `audio_out` · `structured_json` ·
  `embedding`
- `auth`: `none` · `api_key` · `oauth` · `local_only` · `byok`
- `cost_model`: `free` · `freemium` · `paid` · `self_hosted`
- `trust_boundary`: `local` · `hub` · `external`

Adapters are the bridge to actual provider catalogs. The hub does not
itself maintain provider lists — it points to external directories
(see `examples/llm-endpoint-directory/`).

### 1.7 Harness

A **named, repeatable workflow** around a model or a trust boundary.
Harnesses are the heart of the hub. Each harness manifest declares the
full `HarnessSpec` (see §3.1).

A harness wraps one or more model calls (or zero — pure deterministic
gates count). It composes rule packs into **applied layers**, declares
which **knowledge object types** it consumes and emits, and states its
**privacy boundaries**.

### 1.8 Pipeline

A **directed acyclic graph** (DAG) of harness invocations, rule pack
calls, and tool calls that completes one specific task.

A pipeline manifest declares:

- `task` (a one-sentence goal — "classify a job offer's risk level",
  "draft a complaint packet from chat transcripts", "summarize a
  technical paper for a non-expert reader", "generate a cinematic
  product photo with brand-safe guard rules")
- `pipeline_kind` — see §11 for the open vocabulary
  (`research_entity`, `verify_data`, `format_response`,
  `classify`, `extract`, `summarize`, `translate`,
  `generate_text`, `generate_image`, `generate_audio`,
  `generate_video`, `route`, `evaluate`, `redact`, `agent_loop`, …)
- `inputs`, `outputs` (typed)
- `steps`: ordered list of `{kind, ref, when, on_error}` where `kind` is
  `harness | rule_pack | tool | adapter | branch | loop`
- `defaults`: persona, model adapter, knowledge packs, rule packs
- `success_criteria`: rubric refs + numeric thresholds

A pipeline is comparable across runs — different model adapters or rule
packs yield different scores under the same rubric.

### 1.9 Benchmark

A **pipeline run against a labeled test set with a rubric**, producing
a comparable score. A benchmark manifest declares:

- `pipeline` (ref)
- `dataset` (ref) — test set
- `rubric` (ref)
- `judge`: `deterministic` | `local_model` | `frontier_judge` | `human`
- `model_arms`: list of `{adapter_ref, label}` to compare side-by-side
- `headline_metric`: a single number readers should look at
- `reproducibility`: `(commit_sha, dataset_version, run_date)`

### 1.10 Rubric

An **evaluation contract**. Each rubric manifest declares:

- `dimensions`: list of `{id, label, weight, scale, evidence_required}`
- `scoring_method`: `weighted_sum` | `min` | `gating` | `custom`
- `examples`: golden examples for each grade band

### 1.11 Dataset

A typed collection of inputs, outputs, and labels. Datasets carry
**provenance** chains (source, scrape date, license, anonymization
status). They can be used as test sets, training sets, or knowledge
sources.

### 1.12 Schema

A typed I/O contract referenced by multiple artifacts. Schemas live in
`catalog/schemas/` and are referenced by `$ref` from manifests.

---

## 2. Controlled vocabularies (cross-cutting axes)

Every artifact is tagged with values from these vocabularies. Each is
defined in `vocabularies/<name>.yaml`.

### 2.1 Industry

Open vocabulary. Suggested top-level industries (one or many per
artifact):

`healthcare` · `finance` · `legal` · `education` · `government` ·
`retail` · `manufacturing` · `media` · `security` · `climate` ·
`agriculture` · `energy` · `transportation` · `real_estate` ·
`hospitality` · `nonprofit` · `defense` · `humanitarian` ·
`scientific_research` · `software` · `creative` · `personal_productivity`

A sub-vocabulary can be added per industry (e.g. `healthcare.radiology`,
`finance.aml`, `legal.immigration`).

### 2.2 Capability

What the artifact does, in user-facing terms:

`classification` · `extraction` · `retrieval` · `summarization` ·
`generation` · `translation` · `reasoning` · `planning` · `evaluation` ·
`anonymization` · `routing` · `verification` · `tool_use` · `dialogue` ·
`memory` · `safety_gating`

### 2.3 Modality

`text` · `image` · `audio` · `video` · `code` · `structured` · `tabular`

### 2.4 Trust boundary

`local` — the artifact stays on the user's machine.
`hub` — content is synced to the public hub (no raw PII).
`external` — the artifact calls a third party.

### 2.5 Lifecycle

`experimental` · `beta` · `stable` · `deprecated`

### 2.6 Freshness

`stable` — facts rarely change.
`volatile` — facts change often; bind via tool calls, not training.
`dated` — facts true as of a specific date; recheck after that date.

### 2.7 License

SPDX identifiers. Suggested defaults: `MIT`, `Apache-2.0`, `CC-BY-4.0`,
`CC-BY-SA-4.0`, `CC0-1.0`, `Proprietary`.

---

## 3. Manifest fields

Every manifest starts with the common envelope, then adds artifact-type
fields.

### 3.0 Common envelope (all artifact types)

```yaml
id: "{type}/{slug}"          # e.g. "harness/text-safety-review"
type: harness                # one of the layer-1 primitive names plus pipeline/benchmark
version: "0.1.0"             # semver
name: "Text Safety Review"
description: |
  One-paragraph plain-language description.
authors:
  - name: "Jane Doe"
    url: "https://github.com/jane"
license: "MIT"
industry:    ["humanitarian", "government"]
capability:  ["safety_gating", "classification"]
modality:    ["text"]
lifecycle:   "beta"
trust_boundary: "local"
freshness:   "stable"
links:
  source: "https://github.com/..."
  homepage: "https://..."
  paper: ""
tags: ["pii", "moderation"]
created: "2026-05-19"
updated: "2026-05-19"
```

### 3.1 Harness manifest

In addition to the envelope:

```yaml
kind: "model_harness"            # model_harness | safety_gate | utility_surface
tier: "primary"                  # primary | secondary
applied_layers:
  - persona
  - grep
  - rag
  - tools
  - online                       # optional grounding layer
consumes:                        # knowledge-object types this harness reads
  - grep_rule
  - rag_doc
  - tool_definition
emits:                           # knowledge-object types this harness can produce
  - reasoning_step
  - extracted_fact
logic_paths:                     # named execution paths
  - id: "respond_with_citations"
    label: "Prompt → grounded response"
    entrypoints: ["/api/respond"]
    steps:
      - "normalize message"
      - "compose persona + grep + rag + tools"
      - "call model"
      - "stream response + trace"
    consumes: [grep_rule, rag_doc, tool_definition]
    emits: [reasoning_step]
    model_call: "required"       # none | optional | hybrid | required | external_optional
    verification: ["layer_trace", "rubric_score"]
knowledge_packs:                 # which knowledge packs the harness needs
  - id: "core_rag"
    label: "Core RAG corpus"
    types: [rag_doc, citation_edge]
    required: true
    trust_boundary: "local"
    freshness: "stable"
logic_packs:                     # which logic packs the harness needs
  - id: "response_policy"
    label: "Refusal policy + tone"
    types: [response_policy, persona_block]
    required: true
model_io:
  input: "{messages: ChatMessage[], context: KnowledgeObject[]}"
  output: "{text: string, citations: Citation[], trace: TraceFrame[]}"
model_targets:                   # provider-neutral transports
  - id: "local_default"
    transport: "ollama"
    role: "Primary local generation"
    required: false
    default: true
    trust_boundary: "local"
  - id: "frontier_judge"
    transport: "anthropic"
    role: "Optional judge for high-stakes outputs"
    required: false
    trust_boundary: "external"
input_verification:
  - "redact PII before model call"
  - "reject input > 32KB"
output_verification:
  - "every claim has a citation"
  - "no PII leaks from RAG into response"
privacy_boundaries:
  raw_input: "stays local"
  derived_output: "may go to hub if anonymized"
  external_calls: "only on explicit user opt-in"
contributes_to:                  # optional — pipelines/benchmarks that use this harness
  - "pipeline/text-safety-review-pipeline"
```

### 3.2 Pipeline manifest

```yaml
task: |
  Classify a job-offer message as low/medium/high recruitment-risk and
  produce a worker-facing explanation with cited statutes.
inputs:
  - name: "message"
    schema: "schemas/chat_message.json"
outputs:
  - name: "risk_label"
    type: "enum[low,medium,high]"
  - name: "explanation"
    type: "markdown"
  - name: "citations"
    type: "Citation[]"
defaults:
  persona: "persona/labor-rights-explainer"
  model_adapter: "adapter/ollama-llama3-8b"
  knowledge_packs: ["knowledge-pack/ilo-indicators"]
  rule_packs: ["rule-pack/grep-recruitment-fraud", "rule-pack/rag-statutes-pH"]
steps:
  - id: "redact"
    kind: "rule_pack"
    ref: "rule-pack/privacy-pii-text-en"
  - id: "classify"
    kind: "harness"
    ref: "harness/risk-classifier"
    inputs: { message: "$.steps.redact.output" }
  - id: "ground"
    kind: "harness"
    ref: "harness/text-safety-review"
    inputs:
      message: "$.steps.redact.output"
      risk_label: "$.steps.classify.output.label"
    when: "$.steps.classify.output.label != 'low'"
  - id: "summarize"
    kind: "harness"
    ref: "harness/plain-language-summarizer"
    inputs: { text: "$.steps.ground.output.text" }
success_criteria:
  - rubric: "rubric/recruitment-risk-v1"
    threshold: 0.80
on_error:
  default: "return classification only, no explanation"
```

### 3.3 Benchmark manifest

```yaml
pipeline: "pipeline/text-safety-review"
dataset: "dataset/recruitment-risk-eval-v1"
rubric: "rubric/recruitment-risk-v1"
judge: "frontier_judge"           # deterministic | local_model | frontier_judge | human
model_arms:
  - { label: "stock-llama3-8b",            adapter_ref: "adapter/ollama-llama3-8b"     }
  - { label: "stock-llama3-8b + harness",  adapter_ref: "adapter/ollama-llama3-8b", harness_override: "harness/text-safety-review" }
  - { label: "ft-llama3-8b",               adapter_ref: "adapter/local-ft-llama3-8b"  }
  - { label: "ft-llama3-8b + harness",     adapter_ref: "adapter/local-ft-llama3-8b", harness_override: "harness/text-safety-review" }
headline_metric: "weighted_rubric_score"
reproducibility:
  commit_sha: ""
  dataset_version: "v1.0.0"
  run_date: "2026-05-19"
report:
  output: "benchmarks/{slug}/report.md"
```

### 3.4 Rule pack manifest

```yaml
family: "grep"                    # grep | glob | classifier | heuristic | rag | citation | privacy | schema | routing
language: "en"
rules:
  - id: "fee-paid-by-worker"
    pattern: "(?i)(deduct|pay|charge).{0,20}(fee|placement|deposit)"
    severity: "high"
    category: "recruitment_fraud"
    notes: |
      Fires when a job offer describes worker-borne fees.
  - id: "passport-retention"
    pattern: "(?i)hold(s|ing)? (your )?passport"
    severity: "high"
    category: "document_abuse"
```

### 3.5 Knowledge pack manifest

```yaml
content_types:
  - rag_doc
  - citation_edge
  - corridor_profile               # leaf type; OPEN — see §4
files:
  - path: "documents.jsonl"
    schema: "schemas/rag_doc.json"
  - path: "citations.json"
    schema: "schemas/citation_edge.json"
indexing:
  bm25: true
  dense:
    enabled: false
provenance:
  sources: ["ILO", "POEA", "BAILII"]
  collected_through: "2026-04-30"
freshness: "stable"
```

### 3.6 Tool manifest

```yaml
parameters:                       # JSON Schema for the tool call
  type: object
  properties:
    text:        { type: string }
    target_lang: { type: string }
  required: [text, target_lang]
returns:
  type: object
  properties:
    translation: { type: string }
side_effects: "external_call"
implementations:
  - kind: "openapi"
    url: "https://api.example.com/translate"
  - kind: "callable"
    path: "tools.translate.run"
examples:
  - input:  { text: "Hello", target_lang: "es" }
    output: { translation: "Hola" }
```

### 3.7 Persona manifest

```yaml
system_prompt: |
  You are a labor-rights educator. ...
role: "explainer"
domain: ["humanitarian", "labor_rights"]
tone: "plain, calm, citation-first"
refusal_style: "harm-reduction"
extends: "persona/base-explainer"
```

### 3.8 Model adapter manifest

```yaml
transport: "ollama"
capabilities: ["text_generation", "chat", "tool_use"]
auth: "none"
cost_model: "self_hosted"
endpoint: "http://localhost:11434"
default_model: "llama3.1:8b"
trust_boundary: "local"
```

### 3.9 Rubric manifest

```yaml
dimensions:
  - id: "groundedness"
    label: "Every claim cited"
    weight: 0.35
    scale: "0..1"
    evidence_required: "citation list non-empty for every factual sentence"
  - id: "harm_reduction"
    label: "Harm-reduction framing"
    weight: 0.25
    scale: "0..1"
    evidence_required: "no paternalistic refusals; offers next-step options"
  - id: "accuracy"
    label: "Statute correctness"
    weight: 0.40
    scale: "0..1"
    evidence_required: "every cited statute exists at the cited section"
scoring_method: "weighted_sum"
examples:
  - grade: 1.0
    response: "..."
    notes: "Best — every claim cited, harm-reduction, accurate."
  - grade: 0.5
    response: "..."
    notes: "Adequate — some citations missing."
  - grade: 0.0
    response: "..."
    notes: "Worst — paternalistic refusal, no citations."
```

### 3.10 Dataset manifest

```yaml
splits:
  train: { path: "data/train.jsonl", count: 12000 }
  val:   { path: "data/val.jsonl",   count:  1500 }
  test:  { path: "data/test.jsonl",  count:  1500 }
record_schema: "schemas/eval_record.json"
provenance:
  origin: "scraped + curated"
  collected_by: "Open Harness Hub contributors"
  collected_through: "2026-04-30"
  license: "CC-BY-4.0"
  anonymization: "PII-redacted; sha256 audit log retained"
```

---

## 4. Knowledge-object leaf types (open vocabulary)

Harnesses declare which knowledge-object **leaf types** they consume and
emit. Leaf types are the typed slices of a knowledge pack. The hub keeps
a registry of leaf types in `vocabularies/leaf-types.yaml`; new types
are added by PR.

Suggested baseline leaf types (industry-agnostic):

`grep_rule` · `glob_rule` · `classifier_rule` · `heuristic_rule` ·
`rag_doc` · `citation_edge` · `persona_block` · `context_snippet` ·
`reasoning_step` · `rubric_dimension` · `tool_definition` ·
`tool_example` · `prompt_template` · `fact_template` ·
`extracted_fact` · `entity_signal` · `envelope_schema` ·
`submission_schema` · `upload_schema` · `audit_template` ·
`response_policy`

Industry-specific examples (modeled as instances of `entity_signal` /
`fact_template` / `corridor_profile`, **not** as new top-level types):

| Industry | Leaf instance | Generic parent |
|---|---|---|
| humanitarian | `corridor_profile` | `entity_signal` |
| humanitarian | `ngo_directory` | `contact_directory` |
| healthcare | `differential_diagnosis_pattern` | `classifier_rule` |
| healthcare | `medication_interaction_edge` | `citation_edge` |
| finance | `aml_typology` | `classifier_rule` |
| finance | `sanction_list_entry` | `entity_signal` |
| legal | `statute_section` | `rag_doc` |
| legal | `case_citation_edge` | `citation_edge` |
| security | `cve_signature` | `grep_rule` |
| security | `indicator_of_compromise` | `entity_signal` |

The hub stays generic. Industry packs extend the leaf-type vocabulary
through their own manifests.

---

## 5. Composability rules

1. **A pipeline never wires raw rule packs to a model.** A rule pack
   reaches a model through a harness; this keeps the trust boundary
   explicit and auditable.
2. **Volatile facts go in tools or knowledge packs, not personas.**
   Hotline numbers, fee caps, current advisories must be fetched at
   run time. Personas describe *style*, not *facts*.
3. **Every harness declares `model_targets`, even when the value is
   `none`.** Pure deterministic gates make this explicit so auditors
   can grep for them.
4. **Privacy boundaries travel with the artifact, not the deployment.**
   A `local`-boundary harness used inside an `external`-boundary
   pipeline must still keep its raw input local.
5. **Reproducibility is a first-class field.** Every benchmark manifest
   declares `(commit_sha, dataset_version, run_date)`; without it the
   run is research-only, not a citable benchmark.

---

## 6. Lifecycle

| Stage | Meaning |
|---|---|
| `experimental` | One author, no review, no production use. |
| `beta` | At least one external review; documented gaps. |
| `stable` | Used in production; semver-stable manifest. |
| `deprecated` | Superseded by another artifact; kept for citation. |

A `deprecated` artifact must declare `superseded_by` and `deprecated_on`.

---

## 7. Naming and IDs

- Artifact IDs are `{type}/{slug}` where `slug` is lowercase-with-dashes.
- `slug` must be ≤ 64 characters.
- `id` is immutable once published; renames create a new ID with the
  old one marked `deprecated`.
- File names match the slug: `catalog/harnesses/text-safety-review.yaml`.

---

## 8. Versioning

- Artifacts use semver.
- Patch version changes for typos, doc clarifications, additional examples.
- Minor version changes for new optional fields, new manifest entries.
- Major version changes for breaking schema changes — and only after
  a 30-day deprecation window with `superseded_by` set on the old major.

---

## 9. Validation

Every manifest must pass `python scripts/validate.py`. Validation checks:

1. Manifest validates against `schemas/{type}.schema.json`.
2. All `ref` fields point to existing artifacts in the catalog.
3. Knowledge / logic / rule pack leaf types are in the leaf-type vocabulary.
4. Industry / capability / modality tags are in their vocabularies.
5. License is a valid SPDX identifier or `Proprietary`.
6. Privacy-boundary fields are present on every artifact that crosses
   a network boundary.

A pipeline manifest additionally checks the DAG — no cycles, no missing
step refs, no dangling outputs.

---

## 10. Multimodal pipelines

Image, audio, and video pipelines compose the **same** primitives as
text pipelines. The hub does not split modalities into separate trees.

A common image-generation pipeline looks like:

```
[persona]   "Brand-safe product photographer"
[rule_pack] "grep-prohibited-terms" — rejects real-celebrity names, hate slurs, trademark prompts
[rule_pack] "rag-style-references"   — retrieves cinematic-lighting style descriptors
[rule_pack] "rag-camera-physics"     — retrieves lens / focal-length physical priors
[harness]   "prompt-shaper"          — composes the raw user idea + retrieved style + rules into a final prompt
[tool]      "txt2img.sdxl"           — function-call to the image model
[harness]   "result-safety-review"   — runs NSFW / IP / brand-mark detectors on the output image
[rule_pack] "grep-output-watermark"  — verifies brand-safe watermark presence
```

Every step uses the same manifest types as a text pipeline. The only
new vocabulary is the output `modality: ["image"]` and the
`pipeline_kind: "generate_image"`.

Audio (TTS / music / SFX) and video (txt2video / video editing)
pipelines follow the identical pattern with the appropriate
`modality`, `pipeline_kind`, and tool refs.

### Image-gen pipeline checklist (recommended fields)

When a pipeline emits image / audio / video, the manifest should also
declare:

- `output_safety_packs`: rule packs that screen the generated artifact
  (NSFW, IP, watermark presence, prompt-injection-via-image, etc.).
- `style_packs`: knowledge packs of style references the prompt-shaper
  pulls from.
- `physics_packs`: knowledge packs encoding physical priors
  (lens / aperture / lighting / acoustic / motion physics).
- `attribution`: a free-text field describing who / what the style
  references are drawn from, plus the dataset license they came from.

---

## 11. Suggested pipeline catalog categories

The catalog ships with subdirectories under `catalog/pipelines/` that
mirror the most-requested **pipeline kinds**. Each is a normal pipeline
manifest; the subdirectory is purely an organizational hint for browsing.

| Subdir | Pipeline kind | Example task |
|---|---|---|
| `research-entity/` | `research_entity` | "Build a sourced one-page profile of a company / person / place." |
| `verify-data/` | `verify_data` | "Given a claim and a corpus, return supports / contradicts / no-evidence with citations." |
| `format-response/` | `format_response` | "Convert raw model output into a strict JSON envelope; auto-repair." |
| `classify/` | `classify` | "Tag a record into a controlled label set with confidence." |
| `extract/` | `extract` | "Pull typed fields from unstructured text / PDF / image." |
| `summarize/` | `summarize` | "Produce a 200-word executive summary with citations." |
| `translate/` | `translate` | "Translate with terminology guard rules + glossary RAG." |
| `redact/` | `redact` | "PII / secrets / proprietary-mark redaction with audit log." |
| `route/` | `route` | "Dispatch incoming input to the right downstream pipeline." |
| `agent-loop/` | `agent_loop` | "Plan + tool-call + verify + reflect in a loop until done." |
| `evaluate/` | `evaluate` | "Run a rubric over an artifact and return a graded score." |
| `system-prompt-library/` | `system_prompt` | "Reusable system-prompt + persona starter for common roles." |
| `rag-library/` | `rag_pack` | "Curated RAG packs (statutes, glossaries, style refs, physics)." |
| `grep-library/` | `grep_pack` | "Curated GREP rule packs (PII, NSFW, brand-safety, fraud)." |
| `tool-library/` | `tool_pack` | "Function-call schemas, MCP servers, OpenAPI ops." |
| `generate-text/` | `generate_text` | "Free-form text generation with a defined harness." |
| `generate-image/` | `generate_image` | "Image gen with prompt-shaping, style RAG, guard rules, output safety." |
| `generate-audio/` | `generate_audio` | "Speech / music / SFX gen with the same primitive stack." |
| `generate-video/` | `generate_video` | "Video gen / editing pipelines with motion-physics RAG." |
| `multimodal/` | `multimodal_*` | "Pipelines that cross modalities (e.g., image + text + audio)." |

These categories are **suggestions, not constraints**. Any pipeline can
live in any subdir; the canonical key is the `pipeline_kind` field in
the manifest.

---

## 12. Ingest paths

The catalog grows from two ingest paths:

1. **Direct contributions.** A contributor opens a PR adding one or
   more manifests under `catalog/`. CI runs schema validation, ref
   resolution, and lint.
2. **Reference ports.** Curators hand-port patterns from established,
   permissively-licensed reference repos (such as
   `_reference/gemma4_comp` and `_reference/llm-safety-framework`) by
   extracting the harness / knowledge-pack / pipeline shape and
   writing a manifest with full upstream attribution
   (`attribution.source_url`, `attribution.author`,
   `attribution.license`). License compatibility is verified before
   the port; sources without a redistribution-compatible license are
   referenced as inspiration only, not ported.

---

## 13. Database representations

Every artifact described by this taxonomy can be **persisted** in four
representative database shapes. Each shape is a published standard with
example DDL / collection spec in `db/`. Implementers pick one — the
manifest stays the same.

### 13.1 Relational (PostgreSQL / SQLite)

A relational mapping with one row per artifact and a small number of
join tables for the array fields. Canonical DDL:

```sql
CREATE TABLE artifact (
  id              TEXT PRIMARY KEY,            -- "harness/text-safety-review"
  type            TEXT NOT NULL,
  version         TEXT NOT NULL,
  name            TEXT NOT NULL,
  description     TEXT NOT NULL,
  license         TEXT NOT NULL,
  lifecycle       TEXT NOT NULL,
  trust_boundary  TEXT,
  freshness       TEXT,
  created         DATE,
  updated         DATE,
  body            JSONB NOT NULL               -- full manifest
);

CREATE TABLE artifact_industry   (artifact_id TEXT REFERENCES artifact(id), industry  TEXT, PRIMARY KEY(artifact_id, industry));
CREATE TABLE artifact_capability (artifact_id TEXT REFERENCES artifact(id), capability TEXT, PRIMARY KEY(artifact_id, capability));
CREATE TABLE artifact_modality   (artifact_id TEXT REFERENCES artifact(id), modality  TEXT, PRIMARY KEY(artifact_id, modality));
CREATE TABLE artifact_tag        (artifact_id TEXT REFERENCES artifact(id), tag       TEXT, PRIMARY KEY(artifact_id, tag));

CREATE TABLE artifact_ref (
  src_id TEXT REFERENCES artifact(id),
  dst_id TEXT REFERENCES artifact(id),
  role   TEXT NOT NULL,                         -- "consumes" | "emits" | "step_ref" | "contributes_to" | "model_target" | "rubric" | "dataset" | ...
  PRIMARY KEY(src_id, dst_id, role)
);
```

This single shape covers all artifact types because the type-specific
fields live in `body` (JSONB). Indexes on `(type, industry, capability)`
make catalog browse queries fast.

### 13.2 Document store (MongoDB / Couchbase / Firestore)

One collection per artifact `type`, one document per artifact, with
the full manifest as the document body. The `attribution`, `links`,
and array fields are nested freely. The `id` field is the document
key. A `refs` array materializes the inbound/outbound edges for
graph-style queries.

### 13.3 Key-value (Redis / DynamoDB)

Used for runtime caches, not as authoritative storage. Suggested keys:

```
artifact:<id>                                 -> manifest JSON
artifact:by_type:<type>                       -> set of ids
artifact:by_industry:<industry>               -> set of ids
artifact:by_capability:<capability>           -> set of ids
artifact:by_tag:<tag>                         -> set of ids
run:<run_id>                                  -> JSON of a pipeline run
run:by_pipeline:<pipeline_id>                 -> sorted set of run ids by ts
```

### 13.4 Vector database (Pinecone / Weaviate / Qdrant / pgvector)

Used for RAG packs and for semantic search across the catalog itself.
Each artifact gets at least one embedding of its `name + description`
for catalog search. Knowledge-pack chunks each get an embedding for
retrieval. Suggested per-vector metadata:

```
{
  "artifact_id":   "knowledge-pack/style-references-cinematic",
  "leaf_type":     "style_reference",
  "chunk_id":      "moody-noir",
  "industry":      ["creative"],
  "modality":      ["text"],
  "trust_boundary": "local",
  "lifecycle":     "experimental"
}
```

### 13.5 Row format for individual rules and knowledge leaves

Beyond the artifact-level table, the **leaves** inside rule packs and
knowledge packs follow a small fixed row shape so they are queryable
across packs:

```sql
CREATE TABLE rule (
  rule_id      TEXT PRIMARY KEY,
  pack_id      TEXT NOT NULL REFERENCES artifact(id),
  family       TEXT NOT NULL,                  -- grep | glob | classifier | heuristic | privacy | online_search | ...
  severity     TEXT,
  category     TEXT,
  pattern      TEXT,                            -- regex / glob / condition / dsl
  body         JSONB NOT NULL,                  -- full rule
  enabled      BOOLEAN DEFAULT TRUE
);

CREATE TABLE knowledge_leaf (
  leaf_id      TEXT PRIMARY KEY,
  pack_id      TEXT NOT NULL REFERENCES artifact(id),
  leaf_type    TEXT NOT NULL,
  industry     TEXT,
  language     TEXT,
  body         JSONB NOT NULL
);
```

This row format is what a SOC analyst, a fact-checker, or a fine-tuning
data engineer would actually query against — "give me every `grep_rule`
of severity `critical` in the `privacy.*` category", "give me every
`rag_doc` in the `humanitarian.trafficking` industry."

The mapping from manifest → relational rows is implemented by
`scripts/db/load_postgres.py` (and equivalents per backend). The
canonical DDL lives in `db/postgres/schema.sql`.

---

## 14. Interactive playground

Pipelines must be **viewable** and **runnable** with sample data so
visitors can build intuition before installing anything. The catalog
supports three levels of interactivity:

1. **Static catalog page (always available).** The MkDocs site renders
   each manifest as a browsable page with: description, primitives it
   consumes, primitives it emits, a step-by-step diagram, and an
   embedded sample-run output. No execution; safe on GitHub Pages.
2. **Pre-rendered sample run (always available).** Each pipeline ships
   with one or more `samples/<scenario>.json` files: a frozen input,
   the deterministic outputs of each step, and the final output. These
   are committed to git and rendered inline on the static page.
3. **Live playground (where the host allows execution).** A Gradio app
   under `hf-space/` loads a pipeline manifest, accepts user input,
   runs the pipeline against a configured model adapter, and shows the
   layer-by-layer trace. The same app works locally
   (`python hf-space/app.py`) and deploys to Hugging Face Spaces or
   any Docker host.

### Sample-run format

```json
{
  "pipeline":   "pipeline/research-entity",
  "scenario":   "company-acme",
  "inputs":    { "entity_name": "Acme Corp", "entity_kind": "company", "country": "US" },
  "steps": [
    {
      "step_id": "redact_query",
      "harness": "harness/redact-pii-text",
      "input":   { "text": "Acme Corp" },
      "output":  { "redacted_text": "Acme Corp", "audit": [] },
      "ms":      4
    }
  ],
  "output":    { "profile_markdown": "...", "citations": [], "trace": [] },
  "model":     "ollama/llama3.1:8b",
  "frozen_at": "2026-05-19T12:00:00Z",
  "license":   "MIT"
}
```

A pipeline with no sample-run committed cannot be marked `stable`. The
validator enforces this rule in §9.

---

## 15. Lifecycle position (pre-API / API / post-API)

Every artifact also declares **where in the request lifecycle it sits**.
This is independent of `lifecycle` (which is maturity:
experimental → stable → deprecated). The two answer different questions.

```
pre_api ── pre_api.input_gating       PII redact, guard rules, prohibited terms
        ├─ pre_api.context_assembly   personas, RAG, prompt templates, knowledge packs
        ├─ pre_api.classification     red-flag screens, typology pre-scoring, routing
        └─ pre_api.query_sanitization outbound search query rewrite, allowlists

api     ── api.model_call             harness + adapter wrapping the model call
        └─ api.tool_call              function-call tools invoked by the model

post_api─ post_api.output_safety      NSFW / IP / watermark / citation-coverage screens
        ├─ post_api.format_coercion   JSON repair, schema validation
        ├─ post_api.evaluation        rubrics, judges, scoring
        └─ post_api.audit             trace formatting, audit-log emission

cross_cutting
        ├─ cross_cutting.composition  pipelines
        ├─ cross_cutting.evaluation   benchmarks
        └─ cross_cutting.data         datasets, schemas
```

The field is **optional on the manifest** — `scripts/build_catalog_index.py`
derives it from type + family + name when omitted, using the rules in
the script's `derive_position()` function. Manifests should declare it
explicitly when the derived value would be ambiguous (for example,
a rule pack that screens both input and output, or a harness that runs
purely as a deterministic gate).

This label powers the static catalog browser
(`docs/catalog/browser.html`) and the vector index
(`db/vector/oh_catalog.jsonl`) so artifacts can be filtered by where
they fit in a pipeline.

---

## 16. Comprehensive pre/post-API process taxonomy

The pipeline lifecycle has many more steps than just "redact, retrieve,
call, evaluate." The hub recognises a comprehensive set of **process**
categories — repeatable, callable transformations with declared I/O —
that may appear at any pipeline stage. Each is an OPEN vocabulary value
for `processor.process_kind` and an allowed value for
`pipeline.steps[].kind`. The full list is at
`docs/concepts/pre-post-api.md`. Highlights:

- **pre_api**: format_convert (PDF/audio/image/HTML/docx → text),
  normalize, validate, redact (PII/PHI/financial/secrets), gate
  (prompt-injection/quota/cost-ceiling), classify (intent/risk/language
  /domain/red_flag), route (dispatch/fallback-chain), assemble
  (persona/prompt-template/few-shot/context-pack/tool-registry/structured
  -output-spec), retrieve (bm25/dense/hybrid/multi-query/citation-graph
  /knowledge-graph), rerank, memory.read, query (rewrite/sanitize
  /allowlist/timebox), policy (identity/permission/consent/licensing).
- **api**: call.chat / stream / tool_use / batch / embedding / vision
  / audio_in / audio_out / image_out / video_out / judge.
- **post_api**: parse (tool_calls/json/citations/usage/uncertainty),
  coerce (json_repair/schema_validate/constrained_grammar/length
  /language/format), safety (toxicity/nsfw_text/nsfw_image
  /celebrity_likeness/deepfake/copyrighted/pii_rescan/prompt_echo
  /watermark_verify/watermark_attach), verify (citation_coverage
  /factual_consistency/logical_consistency/constraint_satisfaction
  /tool_call_safety/numerical_check/source_link), eval
  (rubric_deterministic/rubric_llm_judge/pairwise/calibration
  /human_in_loop), augment (translate/simplify/tts/image_caption),
  memory (write_conversational/write_episodic/write_kb), cache
  (write_response/write_embedding), index.update_vector, escalate
  (human/different_model/different_pipeline), retry.with_critique,
  audit (trace/provenance/cost/compliance), report (markdown/pdf/html),
  deliver (streaming/email/webhook/queue/file).
- **cross_cutting**: chunk (fixed/semantic/recursive), embed
  (text/image/multimodal), parallel (fan_out/fan_in),
  loop.until_convergence, delay.backoff.

The list is OPEN. New `process_kind` values are added by PR with no
schema migration.

### 16.5 Deeper pre/post-API process kinds (extended)

The §16.1–16.4 enumeration captures the broad buckets. Real production
pipelines also use these named patterns. All are valid
`process_kind` values; the categories are open.

**Pre-API (advanced):**

| Family | process_kind | Reference |
|---|---|---|
| Context compression | `compress.llmlingua` · `compress.gist` · `compress.multi_turn_summary` | LLMLingua, Gist Tokens, conversation summary |
| System-context injection | `inject.datetime` · `inject.locale` · `inject.user_profile` · `inject.constitutional` · `inject.seed` · `inject.output_schema` | Replace `today`/locale/seed; render JSON Schema into prompt |
| Query optimization (advanced) | `query.hyde` · `query.step_back` · `query.multi_query` · `query.decompose` | HyDE, Step-Back, MultiQueryRetriever, Sub-Query Decomposition |
| Linguistic normalization | `resolve.coreference` · `expand.abbreviation` · `language.detect_translate` · `correct.spelling_grammar` | spaCy / domain glossaries |
| Tool / model selection | `select.tools_top_k` · `select.few_shot_by_difficulty` · `select.expert_route` | Gorilla, RouteLLM |
| Budget management | `count.tokens` · `cache.key_gen` | tiktoken; prompt-cache key reuse |
| Modality preprocessing | `image.preprocess` · `audio.preprocess` · `code.lint_format` | Crop / VAD / fmt |
| Safety preprocessing (advanced) | `gate.prompt_injection_paraphrase` · `watermark.canary_inject` | Spotlighting; canary tokens for leak detection |

**Post-API (advanced):**

| Family | process_kind | Reference |
|---|---|---|
| Sampling strategies | `sample.n_best` · `sample.self_consistency` · `sample.tree_of_thoughts` · `sample.beam_search` | Best-of-N, Self-Consistency, Tree-of-Thoughts |
| Critique & revision | `critique.self` · `critique.constitutional` · `critique.adversarial_judge` | Self-Refine, Constitutional AI, debate |
| Verification (advanced) | `verify.hallucination_score` · `verify.fact_check_external` · `verify.numerical_recompute` · `verify.code_execute` | SelfCheckGPT, Ragas, code interpreter |
| Format repair (broader) | `coerce.xml_repair` · `coerce.yaml_repair` · `coerce.csv_repair` · `coerce.markdown_to_pdf` · `coerce.markdown_to_slack` | WeasyPrint, pandoc, Slack Block Kit |
| Style adjustment | `style.tone_adjust` · `style.simplify_flesch` · `style.persona_lock` | Brand-voice + reading-level targeting |
| Augmentation (advanced) | `augment.citation_backfill` · `augment.confidence_intervals` · `augment.glossary` | Perplexity-style citations, calibrated CIs |
| Provenance & signing | `sign.cryptographic` · `watermark.text` · `watermark.image` · `provenance.run_hash` | Sigstore, statistical watermarking, C2PA |
| Routing & abstention | `abstain.confidence_threshold` · `route.fallback_model` | Calibrated refusal; cascades |
| Ensembling | `ensemble.blend` · `ensemble.dedupe` | Weighted blending, dedup across samples |
| Telemetry | `meter.cost` · `meter.latency` · `meter.tokens` · `meter.experiment_tag` | Cost / SRE / A/B |
| Active learning | `flag.active_learning` · `personalize.update_profile` · `feedback.collect_thumbs` · `writeback.training_jsonl` | RLHF data collection; per-harness JSONL |

These are the most common 30+ named patterns; the list will grow as
new techniques land. See `docs/concepts/pre-post-api.md` for the
full walkthrough.

---

## 17. Processor artifact type

A **processor** is a typed, repeatable transformation with declared
I/O, side effects, and trust boundary. It is the generic slot for any
step in §16 that isn't already a `harness`, `tool`, or `rule-pack`.

Use a processor when the step is **not** a model call (use `harness`)
**and** is **not** a function-call definition a model invokes (use
`tool`) **and** is **not** a pure rule pack.

Examples: PDF-to-text converter, JSON repair, citation verifier,
fixed-token chunker, watermark attacher, cost-ceiling gate,
LLM-as-judge wrapper, memory store. The hub ships 14 sample processors
under `catalog/processors/` covering the major categories.

`tool` describes a function the *model* may decide to call. A processor
is invoked *by the pipeline runtime*, never by the model. Keeping the
two distinct makes auditability easier — a regulator can grep `type:
tool` to find anything the model can call, and `type: processor` to find
anything the pipeline runtime calls deterministically.

A processor that wraps an LLM call (e.g. `processor/llm-judge`)
declares `model_targets` exactly like a harness. The distinction is
that a processor is **anonymous to the model under review** — the judge
sits *outside* that model's reasoning trace.

Required fields: `process_kind`, `inputs[]`, `outputs[]`,
`side_effects`. Optional: `deterministic`, `idempotent`, `streaming`,
`latency_budget_ms`, `on_error`, `retry`, `model_targets`,
`implementations`. Full schema at `schemas/processor.schema.json`.

---

## 18. Standards alignment

The hub's YAML manifests are the source of truth, but every manifest is
**JSON-LD-addressable** and the hub **emits to the standards that matter
externally**. The full landscape analysis lives at
[`docs/research/standards-landscape.md`](../docs/research/standards-landscape.md);
this section binds the decisions.

### 18.1 JSON-LD context

`docs/ns/context.jsonld` is the canonical context. It maps hub terms to:

- **schema.org** core (`SoftwareApplication`, `Dataset`, `HowTo`,
  `CreativeWork`)
- **DCAT-3** (`dcat:Catalog`, `dcat:Dataset`, `dcat:Distribution`)
- **SKOS** for open vocabularies (`skos:ConceptScheme`)
- **PROV-O** for `attribution`/`provenance`
- **DPV** for privacy categories
- **SPDX** for license identifiers
- **ODRL** for non-trivial license / usage policies

A custom `ohh:` namespace covers concepts without prior art: `Harness`,
`Pipeline`, `Processor`, `lifecyclePosition`, `appliedLayer`,
`processKind`, etc.

### 18.2 Emit, don't replace

Renderers under `scripts/emit/` (planned) produce standards-conformant
outputs from the YAML manifests. Source of truth stays in `catalog/`.

| Target | Renderer | Source artifact |
|---|---|---|
| Croissant 1.0 (JSON-LD ML datasets) | `croissant.py` | `dataset`, `knowledge-pack` |
| MCP server stubs | `mcp_server.py` | `tool`, `processor` |
| MCP `tools/list` JSON-RPC | `mcp_tools_list.py` | hub-wide |
| Hugging Face Model Card | `hf_model_card.py` | `harness` |
| Hugging Face Dataset Card | `hf_dataset_card.py` | `dataset`, `knowledge-pack` |
| Hugging Face Space frontmatter | `hf_space.py` | `harness` (deploy) |
| lm-evaluation-harness YAML | `lm_eval_harness.py` | `benchmark` |
| promptfoo config | `promptfoo.py` | `benchmark` |
| CycloneDX-ML 1.6 AIBOM | `cyclonedx_ml.py` | release bundle |
| OpenLineage v2.0 events | `openlineage.py` | pipeline / benchmark run |
| C2PA v2.1 manifest | `c2pa.py` | image / audio / video output |
| EU AI Act Annex IV dossier | `eu_ai_act_annex_iv.py` | `eu_ai_act_risk: high_risk` |
| SPDX 3.0 (AI + Dataset profiles) | `spdx_3.py` | release bundle |
| OpenAI / Anthropic / Gemini tools | derived from MCP | `tool` |

Tool emitters are trivial renames over the canonical JSON Schema
`parameters` / `returns` fields; Gemini requires a JSON Schema →
OpenAPI 3.0-subset down-convert.

### 18.3 New envelope fields (additive)

```yaml
'@context': "/ns/context.jsonld"
'@id':      "https://open-harness-hub.dev/{type}/{slug}/{version}"
'@type':    ["SoftwareApplication", "ohh:Harness"]

eu_ai_act_risk: "minimal"
nist_ai_rmf_controls: ["GOVERN-1.1", "MAP-3.2"]
iso_42001_controls:   ["A.6.2.4"]

data_protection:                        # DPV-aligned
  data_categories: ["dpv:MedicalHealth"]
  hipaa_safe_harbor_categories: ["hsh:12", "hsh:14"]
  purposes:        ["dpv:ResearchAndDevelopment"]
  legal_basis:     ["dpv:LegitimateInterest"]
```

All fields are optional. Existing manifests stay valid.

### 18.4 Cite, don't restate

Authoritative external vocabularies are referenced by IRI rather than
re-published:

| Vocabulary | Canonical IRI pattern |
|---|---|
| ICD-10 | `http://id.who.int/icd/release/10/{code}` |
| SPDX licenses | `https://spdx.org/licenses/{id}.html` |
| ILO forced-labour indicators | `https://www.ilo.org/publications/...` |
| FATF typologies | FATF report URLs |
| MITRE ATT&CK | `https://attack.mitre.org/techniques/{id}/` |
| OFAC SDN | `https://sanctionssearch.ofac.treas.gov/Details.aspx?id={id}` |
| HIPAA Safe Harbor categories | `vocabularies/hipaa-safe-harbor.yaml` (`hsh:01`..`hsh:18`) |

### 18.5 Adoption phases

Phase 1 (in this commit):
- `/ns/context.jsonld` published.
- Envelope schema additions: `eu_ai_act_risk`,
  `nist_ai_rmf_controls`, `iso_42001_controls`, `data_protection`.
- HIPAA Safe Harbor controlled vocabulary at
  `vocabularies/hipaa-safe-harbor.yaml`.

Phase 2 (next): `scripts/emit/{croissant,mcp_server,hf_model_card}.py`.

Phase 3 (longer): `scripts/emit/{lm_eval_harness,promptfoo,cyclonedx_ml,openlineage,c2pa,eu_ai_act_annex_iv}.py`; hub-as-MCP server; DCAT + SKOS adoption.

### 18.6 What the hub deliberately does NOT adopt

- **Linked Data Platform** — too niche.
- **MLMD** — TFX-specific; superseded by MLflow + OpenLineage.
- **OpenAI Evals** — declining vs. lm-eval-harness.
- **HELM** as a direct emit target — mirror vocabulary instead.
- **Kaggle metadata** — platform-specific; renderer only when publishing.

