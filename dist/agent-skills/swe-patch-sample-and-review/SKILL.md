---
name: swe-patch-sample-and-review
description: Given a bug report + repo path, sample N candidate patches, run tests
  on each, then have a reviewer model pick the best one.
when_to_use: 'Pipeline kind: code_patch_search.'
---

# SWE-agent: sample N patches + reviewer judges

The princeton-nlp/SWE-agent pattern. Given a bug report + repo: sample
N action-rollouts (each producing a candidate patch via file-edit + run-
test loop), then a reviewer model judges the N candidates and picks
the best patch.

Verified by Open Harness Hub clone: SWE-agent's
`sweagent/agent/{agents,reviewer,history_processors,action_sampler}.py`
implements exactly this.

## Task

Given a bug report + repo path, sample N candidate patches, run tests
on each, then have a reviewer model pick the best one.

## Steps

1. **guard_bug** — `rule_pack` → `rule-pack/grep-prompt-injection-heuristics`
2. **sample_candidates** — `processor` → `processor/action-sampler-multi-rollout`
3. **reviewer_judge** — `processor` → `processor/llm-judge`
4. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/code-consultant
- **model_adapter**: adapter/ollama-default
- **rule_packs**: `rule-pack/grep-prompt-injection-heuristics`, `rule-pack/grep-cloud-secrets`

## Success criteria

- rubric `rubric/research-entity-v1` threshold 0.7

## Provenance

- Hub artifact: `pipeline/swe-patch-sample-and-review` v0.1.0
- License: `MIT`
- Industry: ai, software, software.codereview
- Full source manifest: see `references/manifest.yaml`
