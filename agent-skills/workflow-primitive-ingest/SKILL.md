---
name: workflow-primitive-ingest
description: Convert external AI workflow graphs into searchable candidate primitives
  with safety, cost, provenance, and evaluation metadata.
when_to_use: 'Pipeline kind: research_web.workflow_primitive_ingest.'
---

# Workflow primitive ingest

Import AI workflow graphs from systems such as ComfyUI, n8n, Flowise, Dify, and Langflow, then normalize, safety-scan, score, and index reusable primitives.

## Task

Convert external AI workflow graphs into searchable candidate primitives with safety, cost, provenance, and evaluation metadata.

## Steps

1. **normalize_workflow** — `tool` → `tool/workflow-import-normalizer`
2. **scan_nodes** — `tool` → `tool/workflow-node-safety-scanner`
3. **score_primitives** — `tool` → `tool/capability-gap-signal-scorer`
4. **plan_index** — `tool` → `tool/primitive-index-orchestrator`
5. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/workflow-builder-inspiration`, `knowledge-pack/saas-operating-platform-patterns`
- **rule_packs**: `rule-pack/grep-prompt-injection-heuristics`

## Success criteria

- deterministic `$.outputs.candidate_primitives` is_truthy `True`

## Provenance

- Hub component: `pipeline/workflow-primitive-ingest` v0.1.0
- License: `MIT`
- Industry: ai, software.devops, media, cross_industry
- Full source manifest: see `references/manifest.yaml`
