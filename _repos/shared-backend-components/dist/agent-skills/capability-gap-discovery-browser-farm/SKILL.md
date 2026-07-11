---
name: capability-gap-discovery-browser-farm
description: Find and rank areas where out-of-box LLMs are weak but reusable pipelines
  and primitives can create measurable capability lift.
when_to_use: 'Pipeline kind: research_web.capability_gap_discovery.'
---

# Capability gap discovery browser farm

Coordinate browser, search, and embedding agents to discover high-value LLM capability gaps and rank candidate primitives, pipelines, evals, and deployment blueprints.

## Task

Find and rank areas where out-of-box LLMs are weak but reusable pipelines and primitives can create measurable capability lift.

## Steps

1. **load_discovery_patterns** — `knowledge_pack` → `knowledge-pack/capability-gap-discovery-patterns`
2. **semantic_prior_search** — `tool` → `tool/embedding-index-search`
3. **source_router** — `tool` → `tool/search-provider-router`
4. **dataset_browser** — `tool` → `tool/browser-research-session`
5. **paper_browser** — `tool` → `tool/browser-research-session`
6. **red_team_browser** — `tool` → `tool/browser-research-session`
7. **normalize_findings** — `tool` → `tool/search-result-normalizer`
8. **score_findings** — `tool` → `tool/capability-gap-signal-scorer`
9. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/research-analyst
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/capability-gap-discovery-patterns`, `knowledge-pack/llm-pipeline-saas-blueprints`
- **rule_packs**: `rule-pack/web-search-allowlist-default`, `rule-pack/grep-prompt-injection-heuristics`

## Success criteria

- deterministic `$.outputs.ranked_opportunities` is_truthy `True`
- deterministic `$.outputs.candidate_primitives` is_truthy `True`

## Provenance

- Hub component: `pipeline/capability-gap-discovery-browser-farm` v0.1.0
- License: `MIT`
- Industry: ai, cross_industry
- Full source manifest: see `references/manifest.yaml`
