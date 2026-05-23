# Harness Hub Spec - foundational open-source standard for declarative LLM-pipeline registries

> _"We have hubs for models (Hugging Face) and vector DBs, but we lack
> a unified Harness Hub - a centralized registry for deterministic,
> step-by-step operational workflows (Persona injection, RegEx/Grep
> pre-filtering, hybrid RAG, and post-generation evaluation). If we
> look at how DevOps evolved, this is exactly akin to the rise of
> Docker Hub for container environments."_
> - Hassan Gasim, May 2026

This document distills the [Open Harness Hub](https://github.com/Amarel-Taylor-Scott/open-harness-hub)
implementation into a portable, vendor-neutral specification for any
team that wants to publish or consume **harnesses** - host-agnostic,
industry-agnostic descriptions of repeatable LLM-pipeline workflows.

The full implementation lives in this repo at v0.4.0+ (200 artifacts,
4 working verticals, 13 standards-format emitters). This SPEC is the
portable layer.

## 1. The shape

A harness publication is one **YAML manifest** that validates against
a published JSON Schema. The shape is the same for every artifact
type. There are **14 artifact types**:

| Type | What it is |
|---|---|
| **harness** | A named, repeatable workflow around a model or trust boundary. Declares applied layers, packs consumed/emitted, model targets, I/O verification, privacy boundaries. |
| **pipeline** | A DAG of harness + rule-pack + tool + processor + sub-pipeline steps that completes a specific task. |
| **persona** | A character / role frame the model adopts at the start of a workflow, with hard rules + refusal style. |
| **rule-pack** | A bundle of one rule family - GREP regex, glob, classifier, heuristic, retrieval policy. |
| **knowledge-pack** | A typed bundle of facts - RAG corpus, fact tables, citation graphs. |
| **logic-pack** | A typed bundle of behavior - prompt templates, response policies, tool registries. |
| **tool** | A function-call definition with example payloads and a backing implementation contract. |
| **adapter** | A provider-neutral transport (Ollama / vLLM / Anthropic / OpenAI / Gemini / HF endpoint / callable / local). |
| **processor** | A small deterministic transform - redaction, format conversion, scoring, audit emission. |
| **rubric** | An evaluation contract - dimensions, weights, evidence required per grade. |
| **dataset** | A typed collection of inputs/outputs/labels with provenance. |
| **schema** | A typed I/O contract (JSON Schema 2020-12). |
| **benchmark** | A pipeline + dataset + rubric + judge + model arms → comparable score. |
| **pattern** | A named, citable design pattern (Self-RAG / ReAct / ToT / k-anonymity-aggregation / etc.) - like a Wikipedia entry for the technique. |

## 2. The envelope

Every manifest carries the same envelope fields (from `_common.schema.json`):

```yaml
id:          "<type>/<kebab-slug>"        # globally unique
type:        "<one of the 14 above>"
version:     "0.1.0"                       # semver
name:        "Human-readable name"
description: "Multi-line markdown OK."
license:     "MIT"                         # SPDX identifier
lifecycle:   "experimental"                # experimental|beta|stable|deprecated
industry:    [legal, healthcare]           # see vocabularies/industries.yaml
capability:  [reasoning, retrieval]        # see vocabularies/capabilities.yaml
modality:    [text]                        # text|image|audio|video|structured
trust_boundary: "local"                    # local|hub|external|mixed
freshness:   "stable"                      # stable|volatile|dated
lifecycle_position: "pre_api.grep"         # pre_api|api|post_api|cross_cutting
tags:        [...]
created:     "2026-05-20"
updated:     "2026-05-20"

# Optional: cross-standards alignment
eu_ai_act_risk:        "limited"           # prohibited|high_risk|limited|minimal|gpai
nist_ai_rmf_controls:  ["GOVERN-1.1"]
iso_42001_controls:    ["A.6.2.4"]
data_protection:                            # DPV + HIPAA Safe Harbor
  data_categories:                ["dpv:Identifying"]
  hipaa_safe_harbor_categories:   ["hsh:01"]
attribution:                                # when mined from external source
  source_url:  "..."
  source_kind: "kaggle|github|huggingface|arxiv|other"
  author:      "..."
  license:     "..."
```

## 3. Composition primitives

A real pipeline is a DAG over these steps:

```yaml
steps:
  - id: "persona_inject"
    kind: "persona"            # OR rule_pack | tool | adapter | harness | processor | pipeline
    ref:  "persona/esg-auditor"
    inputs:
      seed: "$.inputs.user_message"
  - id: "grep_red_flags"
    kind: "rule_pack"
    ref:  "rule-pack/grep-esg-forced-labor-red-flags"
    inputs:
      text: "$.steps.persona_inject.output.composed"
  - id: "rag_against_csddd"
    kind: "knowledge_pack"
    ref:  "knowledge-pack/csddd-and-forced-labor-indicators"
    inputs:
      query: "$.steps.grep_red_flags.output.hits"
  - id: "judge"
    kind: "processor"
    ref:  "processor/llm-judge"
    inputs:
      candidate: "$.steps.rag_against_csddd.output.compose"
      rubric_ref: "rubric/esg-supplier-compliance-v1"
```

Step kinds (open vocabulary, current set):
`harness · rule_pack · tool · adapter · branch · loop · knowledge_pack · processor · embedder · chunker · format_convert · format_coerce · cache · memory · judge · escalate · dispatch · parallel · report · deliver · pipeline`

The `pipeline` step kind invokes a sub-pipeline - this is how the
kitchen-sink `pipeline/full-vendor-due-diligence` chains ESG +
AppSec + Legal grading into one workflow.

## 4. The six-step canonical chain

After mining hundreds of production AI pipelines (Kaggle / GitHub /
production repos), the most-recurring shape is:

```
[structured input]
     │
     ▼  processor/structured-to-prose
[normalized prose]
     │
     ▼  processor/redact-pii-text   +   rule-pack/{phi|pii}-*-en
[PII/PHI-safe text]
     │
     ▼  rule-pack/grep-{vertical}-red-flags
[deterministic red-flag hits]
     │
     ▼  rule-pack/hybrid-retrieval-policy → knowledge-pack/{vertical}
[citations from the regulatory / playbook / domain corpus]
     │
     ▼  processor/llm-judge + rubric/{vertical}-quality-v*
[scored output with rationale]
     │
     ▼  processor/audit-trace-emitter
[trace recorded for compliance / board oversight]
```

This shape is **invariant across industries**. The Open Harness Hub
reference implementation runs the IDENTICAL chain across:

- **ESG / Supply-Chain DD** (CSDDD + 12 jurisdictions + 13 languages)
- **Healthcare radiology** (ACR Appropriateness Criteria + Fleischner + RADS)
- **Legal contract review** (10 clause families + playbook redlines)
- **AppSec code review** (29 CWE-cited GREP rules + OWASP RAG)

with only the persona, GREP rule pack, knowledge pack, and rubric
changing. Adding a fifth vertical is a 6-artifact PR.

## 5. Success criteria (the bar for "this pipeline passed")

Success criteria are first-class composable items, not just a single
rubric-and-threshold pair. Seven kinds combine via AND / OR / NOT:

```yaml
success_criteria:
  - kind: rubric                                  # legacy/default
    rubric: rubric/X
    threshold: 0.7
  - kind: regex                                   # text must (not) match
    target: "$.steps.X.output.text"
    pattern: "[REDACTED:.*?]"
    must_match: true
  - kind: semantic                                # embedding similarity
    target: "$.steps.X.output.text"
    must_cover: ["topic A", "topic B"]
    similarity_threshold: 0.65
    embedder: adapter/bge-embeddings-local
  - kind: llm_judge                               # adapter-backed judge
    target: "$.steps.X.output.text"
    judge_adapter: adapter/anthropic-claude-sonnet
    rubric: rubric/X
    threshold: 0.7
  - kind: deterministic                           # numeric / boolean check
    target: "$.steps.X.output.score"
    op: ">="                                       # > >= < <= == != in not_in is_truthy is_falsy
    value: 0.7
  - kind: tool_validate                           # external tool decides
    tool: tool/json-schema-validator
    target: "$.output"
    params: { schema_path: "schemas/X.schema.json" }
  - kind: composite                               # AND/OR/NOT of children
    op: "AND"
    children: [ ... ]
```

Each criterion declares a severity; the runner emits per-criterion
pass/fail with the actual target value + operator so reviewers can
trace exactly why a pipeline failed.

## 6. Standards alignment (emitters out of the box)

A single YAML manifest emits to **13 published standards formats**
via `scripts/emit/`:

| Emitter | Format |
|---|---|
| `croissant` | ML-Commons Croissant 1.0 (HF datasets-compatible) |
| `mcp_server` | Anthropic MCP server marketplace.json + INDEX.md |
| `agent_skill` | Anthropic Agent Skill bundles |
| `hf_model_card` | HuggingFace model cards |
| `hf_dataset_card` | HuggingFace dataset cards |
| `hf_space` | HuggingFace Space README |
| `lm_eval_harness` | EleutherAI lm-evaluation-harness task YAML |
| `promptfoo` | promptfoo config + asserts |
| `cyclonedx_ml` | CycloneDX-ML AIBOM |
| `openlineage` | OpenLineage event templates |
| `c2pa` | C2PA manifest templates |
| `eu_ai_act_annex_iv` | EU AI Act Annex IV technical documentation |
| `spdx_3` | SPDX 3.0 software bill of materials |

This is the answer to "how do we publish?" - write **one** manifest;
get **thirteen** standards-format publications for free.

## 7. Vocabularies

Controlled lists live in `vocabularies/`:

- `industries.yaml` - 30+ industries with sub-industries (healthcare.radiology, finance.aml, esg.csddd, legal.contract, security.appsec, ...)
- `capabilities.yaml` - what the artifact DOES (retrieval, classification, generation, anonymization, code-execution, ...)
- `modalities.yaml` - text / image / audio / video / structured
- `lifecycle-position.yaml` - pre_api.* / api.* / post_api.* / cross_cutting
- `applied-layers.yaml` - persona / grep / rag / tools / official_sources / online / classifier / heuristic / privacy
- `leaf-types.yaml` - typed knowledge/logic/trace leaves consumed and emitted

New entries land via PR. Sub-industries are dot-separated. Open vocabulary
where it makes sense (capabilities, process_kind, tags); closed enum
where alignment matters (modalities, lifecycle stages, trust boundaries).

## 8. The "Hassan litmus test"

Hassan's example: _"a CSDDD compliance harness could pull a standardized
'Regex Compliance Filter' and a 'Hierarchical RAG Anchor' from this
central repository."_

Translated to the spec:

```yaml
# A CSDDD compliance pipeline pulls a 'regex compliance filter':
- ref: "rule-pack/grep-esg-forced-labor-red-flags"

# ...and a 'hierarchical RAG anchor':
- ref: "knowledge-pack/csddd-and-forced-labor-indicators"

# Both are individually addressable; both validate against published
# schemas; both can be referenced from any pipeline anywhere.
```

This is `pipeline/supplier-policy-grading` today, running live, valid
against `schemas/pipeline.schema.json`, with 22+ citation entries in
the knowledge pack and 39 indicator rules across the 3 ESG GREP packs.

## 9. Collaboration and forks

The spec is intentionally portable. To stand up a separate registry:

1. Fork the schemas (`schemas/`) and vocabularies (`vocabularies/`).
2. Write or import manifests into `catalog/<type>/...yaml`.
3. Validate with `python scripts/validate.py`.
4. Emit to standards formats with `python -m scripts.emit.all`.

No central server, no API key, no platform lock-in. The catalog is
plain YAML in git. The CLI (`oh-hub list / describe / search /
depends / run / emit`) works against any clone of any fork.

## 10. What this spec is NOT

- A model registry. Use Hugging Face for weights.
- A vector DB. Use Pinecone / pgvector / Weaviate / Chroma for indexing.
- A tracing / observability platform. Use Langfuse / OpenLLMetry /
  OpenTelemetry for runtime metrics.
- A workflow engine. Use Temporal / Airflow / Prefect for orchestration.

This spec is the **artifact layer between them**. The thing in the
middle that says "this is how I compose them into a repeatable,
inspectable workflow that I can publish, version, and grade."

## 11. Open invitations

- **Co-authors**: open a discussion or PR. The spec lives in this
  repo; the implementation does too.
- **Forks for verticals**: a domain-specific hub (pharma compliance,
  defense acquisitions, climate finance) is a healthy fork - same
  schemas, different catalog content.
- **Bridge to upstream registries**: emitters to LangChain Hub /
  Semantic Kernel / Hayhooks / others are welcome. The 13 current
  emitters were a 1-day each effort.

## License

MIT - same as the reference implementation. Compatible with
permissive forks, vendor publication, and registry hosting.
