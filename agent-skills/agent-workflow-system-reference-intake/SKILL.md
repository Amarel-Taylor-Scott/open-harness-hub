---
name: agent-workflow-system-reference-intake
description: Study agent/workflow ecosystems through safe reference intake, extract
  reusable workflow and skill primitives, and route them through governance, labels,
  dedupe, and index emission.
when_to_use: 'Pipeline kind: research_web.agent_workflow_reference_intake.'
---

# Agent workflow system reference intake

Safely plan reference intake for agent frameworks, skill marketplaces, and workflow systems, then extract normalized skill/workflow primitives without republishing upstream source files.

## Task

Study agent/workflow ecosystems through safe reference intake, extract reusable workflow and skill primitives, and route them through governance, labels, dedupe, and index emission.

## Steps

1. **load_agent_systems** — `knowledge_pack` → `knowledge-pack/agent-workflow-system-source-map`
2. **plan_reference_intake** — `tool` → `tool/reference-repo-intake-planner`
3. **extract_skill_workflows** — `tool` → `tool/skill-workflow-manifest-extractor`
4. **label_and_dimension** — `pipeline` → `pipeline/hybrid-label-vector-index`
5. **governance_entity_dedupe_index** — `pipeline` → `pipeline/source-governance-entity-dedupe-index`
6. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/agent-workflow-system-source-map`, `knowledge-pack/hybrid-label-dimension-taxonomy`
- **rule_packs**: `rule-pack/grep-prompt-injection-heuristics`

## Success criteria

- deterministic `$.outputs.intake_plans` is_truthy `True`
- deterministic `$.outputs.review_tickets` is_truthy `True`

## Provenance

- Hub component: `pipeline/agent-workflow-system-reference-intake` v0.1.0
- License: `MIT`
- Industry: ai, software.devops, cross_industry
- Full source manifest: see `references/manifest.yaml`
