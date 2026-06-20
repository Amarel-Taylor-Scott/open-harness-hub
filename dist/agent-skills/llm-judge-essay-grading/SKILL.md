---
name: llm-judge-essay-grading
description: Given an essay + rubric, produce a grade (numeric or rubric-aligned)
  with concrete justifications. Robust to adversarial-prompt prefixes trying to inflate
  the score.
when_to_use: 'Pipeline kind: evaluation.'
---

# LLM-judge essay grading (with adversarial prompt prefix)

Run a frontier LLM as judge on candidate essays, using a few-shot
prompt with adversarial prefix patterns to discourage gaming. The
"you can't please them all" pattern: grade strictly, refuse to
inflate scores under social-engineering pressure.

Verified by Open Harness Hub mining of richolson's "Mash It Up" (561
votes), "Add It Up!" (333 votes), and jiprud's "Essays - simple
submission" (484 votes) on llms-you-cant-please-them-all.

## Task

Given an essay + rubric, produce a grade (numeric or rubric-aligned)
with concrete justifications. Robust to adversarial-prompt prefixes
trying to inflate the score.

## Steps

1. **guard** — `rule_pack` → `rule-pack/grep-prompt-injection-heuristics`
2. **judge** — `processor` → `processor/llm-judge`
3. **ensemble_across_seeds** — `processor` → `processor/self-consistency-sampler`
4. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/fact-checker
- **model_adapter**: adapter/ollama-default
- **rule_packs**: `rule-pack/grep-prompt-injection-heuristics`

## Provenance

- Hub artifact: `pipeline/llm-judge-essay-grading` v0.1.0
- License: `MIT`
- Industry: ai, education
- Full source manifest: see `references/manifest.yaml`
