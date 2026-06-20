---
name: multi-agent-debate-with-judge
description: Two or more debater agents argue different positions across N rounds;
  judge scores final positions and outputs verdict + transcripts.
when_to_use: 'Pipeline kind: multi_agent.'
---

# Multi-agent debate with judge

Two or more debater personas argue different sides of a question
across N rounds. A judge persona scores the final positions. Used
for hard reasoning tasks where stress-testing improves accuracy.

Verified by Open Harness Hub clone:
`microsoft/autogen` implements the group-chat round-table pattern.

## Task

Two or more debater agents argue different positions across N rounds;
judge scores final positions and outputs verdict + transcripts.

## Steps

1. **guard** — `rule_pack` → `rule-pack/grep-prompt-injection-heuristics`
2. **spawn_debaters** — `processor` → `processor/persona-set-generator`
3. **round_1** — `harness` → `harness/text-safety-review`
4. **subsequent_rounds_loop** — `processor` → `processor/iterative-revise-loop`
5. **judge** — `processor` → `processor/llm-judge`

## Defaults

- **persona**: persona/research-analyst
- **model_adapter**: adapter/ollama-default
- **rule_packs**: `rule-pack/grep-prompt-injection-heuristics`

## Provenance

- Hub artifact: `pipeline/multi-agent-debate-with-judge` v0.1.0
- License: `MIT`
- Industry: ai
- Full source manifest: see `references/manifest.yaml`
