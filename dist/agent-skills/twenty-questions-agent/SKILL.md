---
name: twenty-questions-agent
description: 'Two agents play 20 Questions: questioner asks yes/no questions to narrow
  down a hidden concept; answerer responds based on the hidden target. Track candidate
  set and use binary-search question selection.'
when_to_use: 'Pipeline kind: agent_loop.'
---

# 20-questions agent (Akinator-style)

An agent that plays 20 Questions — asks yes/no questions to narrow
down a hidden concept. Uses a candidate set + binary-search-style
question generation. The classic agent-game pattern with a clear
win condition.

Verified by Open Harness Hub mining of ryanholbrook's "LLM 20
Questions Starter Notebook" (1420 votes) + cdeotte's "Starter Code
for Llama 8B LLM" (447 votes).

## Task

Two agents play 20 Questions: questioner asks yes/no questions to
narrow down a hidden concept; answerer responds based on the hidden
target. Track candidate set and use binary-search question selection.

## Steps

1. **guard** — `rule_pack` → `rule-pack/grep-prompt-injection-heuristics`
2. **play** — `processor` → `processor/iterative-revise-loop`
3. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/research-analyst
- **model_adapter**: adapter/ollama-default

## Provenance

- Hub artifact: `pipeline/twenty-questions-agent` v0.1.0
- License: `MIT`
- Industry: ai, education
- Full source manifest: see `references/manifest.yaml`
