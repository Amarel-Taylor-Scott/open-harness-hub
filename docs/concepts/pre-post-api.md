# Pre-API and post-API processes

The hub recognizes a comprehensive taxonomy of pre/post-API processes
so any current or future pipeline pattern has a place. The full list
lives in [SPEC §16](../reference/spec.md#16-comprehensive-prepost-api-process-taxonomy).

## What a "process" is

A **process** is a typed, repeatable transformation with declared
inputs, outputs, side effects, and trust boundary. The hub provides
four kinds of process artifacts, each with a different purpose:

| Type | Who invokes it | Example |
|---|---|---|
| `harness` | Pipeline runtime; wraps a model call | text-safety-review, clinical-decision-support |
| `tool` | The model (via function-calling) | web-search, sanctions-check, txt2img-sdxl |
| `rule-pack` | Pipeline runtime; deterministic rule eval | PII redaction, clinical red-flag classifier, FATF typology |
| `processor` | Pipeline runtime; everything else | PDF→text, JSON repair, citation coverage, LLM judge, escalation |

A `processor` is the **generic** slot for any pre/post step that is
not a model wrapper, not a function-call definition, and not a pure
rule pack. Most of the categories below land here.

## Pre-API processes

What happens **before** the model is called.

### Format conversion
PDF → text, audio → text, image → caption, HTML → markdown,
spreadsheet → records, email → thread. See
[`processor/pdf-to-text`](../catalog/processor_pdf-to-text.md),
[`processor/audio-to-text-whisper`](../catalog/processor_audio-to-text-whisper.md).

### Normalization & validation
Encoding fix, whitespace collapse, JSON Schema validation, size limit.

### Privacy & redaction
PII / PHI / financial-PII redaction, secret scanning, proprietary
mark redaction, audit-log emission. See
[`harness/redact-pii-text`](../catalog/harness_redact-pii-text.md),
[`rule-pack/phi-hipaa-en`](../catalog/rule-pack_phi-hipaa-en.md),
[`rule-pack/financial-pii-en`](../catalog/rule-pack_financial-pii-en.md).

### Safety gating (before model call)
Prompt-injection detection, prohibited-content blocking, rate-limit
gating, cost-ceiling enforcement. See
[`processor/prompt-injection-detector`](../catalog/processor_prompt-injection-detector.md),
[`processor/cost-ceiling-gate`](../catalog/processor_cost-ceiling-gate.md).

### Classification & routing
Intent, language, domain, red-flag classifiers; dispatch / fallback-chain
routers. See
[`rule-pack/clinical-red-flags`](../catalog/rule-pack_clinical-red-flags.md),
[`rule-pack/aml-typologies-fatf`](../catalog/rule-pack_aml-typologies-fatf.md),
[`processor/intent-dispatcher`](../catalog/processor_intent-dispatcher.md).

### Context assembly
Persona selection, RAG retrieval (BM25 / dense / hybrid / multi-query /
citation-graph), re-ranking, memory read, tool-registry assembly,
few-shot selection, context packing.

### Query optimization
Query rewrite, query sanitize (PII out before search), allowlist /
freshness-window enforcement.

### Identity & policy
Authn, permission check, consent verification, licensing check.

## API processes (the model call itself)

Chat completion, streaming, tool-use loop, batch API, embedding,
vision, audio-in / audio-out, image / video generation, LLM-as-judge.

## Post-API processes

What happens **after** the model returns.

### Response parsing
Tool-call extraction, reasoning-trace extraction, JSON parse,
citation extraction, token usage, uncertainty extraction.

### Format coercion / repair
JSON repair, schema validation, constrained-grammar re-prompt, length
truncation, language coercion, output-format conversion. See
[`processor/json-schema-repair`](../catalog/processor_json-schema-repair.md).

### Output safety
Toxicity, NSFW (text + image), celebrity-likeness, deepfake,
copyrighted-content detectors, PII re-scan, system-prompt-echo block,
watermark verify / attach. See
[`processor/nsfw-image-classifier`](../catalog/processor_nsfw-image-classifier.md),
[`rule-pack/grep-output-safety-image`](../catalog/rule-pack_grep-output-safety-image.md).

### Verification & grounding
Citation coverage, citation validity, factual / logical consistency,
constraint satisfaction, tool-call safety, numerical re-check, source-link
HEAD check. See
[`processor/citation-coverage`](../catalog/processor_citation-coverage.md).

### Evaluation
Deterministic rubric scoring, LLM-as-judge, pairwise comparison,
calibration scoring, human-in-loop. See
[`processor/llm-judge`](../catalog/processor_llm-judge.md) and any
`rubric/*`.

### Augmentation
Citation-metadata enrichment, translation, simplification, TTS,
image captioning.

### Memory & state
Conversational memory write, episodic memory, knowledge-base promotion,
response cache, embedding cache, vector index update. See
[`processor/memory-conversational-store`](../catalog/processor_memory-conversational-store.md).

### Routing & escalation
Escalate to human, escalate to different model, escalate to a different
pipeline, critique-and-revise retry. See
[`processor/escalate-human-review`](../catalog/processor_escalate-human-review.md).

### Audit & reporting
Trace emission, provenance attachment, cost accounting, compliance log,
markdown / PDF / HTML reports. See
[`processor/audit-trace-emitter`](../catalog/processor_audit-trace-emitter.md).

### Delivery
Streaming response, email / webhook / queue / file delivery.

## Cross-cutting

Chunking, embedding, parallel fan-out / fan-in, loop-until-convergence,
retry backoff. These can appear at any stage.

## Why the taxonomy is open

`processor.process_kind` is an **open vocabulary**. New process kinds
are added by PR (no schema change needed). The schema only validates
that the value is a string. The taxonomy in SPEC §16 is the suggested
list - extend it freely when a new use case lands.

This keeps the schema flexible for future use cases (new safety
classifiers, new format converters, new memory backends, new
agent-orchestration primitives) without requiring a schema migration.
