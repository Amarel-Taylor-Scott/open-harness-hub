---
name: occupation-to-procedure-primitive-index
description: Mine occupation and job-description sources for tasks, questions, facts,
  tools, evidence requirements, policies, outputs, evals, and candidate AI pipeline
  primitives.
when_to_use: 'Pipeline kind: research_web.occupation_work_atom_index_build.'
---

# Occupation to procedure primitive index

Convert occupation taxonomies, job descriptions, and role classifications into work atoms, procedure knowledge objects, candidate primitives, and searchable pipeline-building context.

## Task

Mine occupation and job-description sources for tasks, questions, facts, tools, evidence requirements, policies, outputs, evals, and candidate AI pipeline primitives.

## Steps

1. **load_occupation_surfaces** — `knowledge_pack` → `knowledge-pack/occupation-source-surface-map`
2. **lookup_occupation_profiles** — `tool` → `tool/occupation-taxonomy-source-lookup`
3. **extract_work_atoms** — `tool` → `tool/job-description-work-atom-extractor`
4. **normalize_as_procedure_objects** — `tool` → `tool/procedure-object-normalizer`
5. **dedupe_existing_primitives** — `tool` → `tool/embedding-index-search`
6. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/occupation-source-surface-map`, `knowledge-pack/procedure-knowledge-object-patterns`
- **rule_packs**: `rule-pack/grep-prompt-injection-heuristics`

## Success criteria

- deterministic `$.outputs.work_atoms` is_truthy `True`
- deterministic `$.outputs.procedure_objects` is_truthy `True`

## Provenance

- Hub component: `pipeline/occupation-to-procedure-primitive-index` v0.1.0
- License: `MIT`
- Industry: ai, hr, education, cross_industry
- Full source manifest: see `references/manifest.yaml`
