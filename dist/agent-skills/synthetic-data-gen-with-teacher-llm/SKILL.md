---
name: synthetic-data-gen-with-teacher-llm
description: Generate N synthetic (input, output) pairs for fine-tuning a student
  model. Filter for diversity, difficulty, and safety. Output Unsloth- ready JSONL.
when_to_use: 'Pipeline kind: synthetic_data_gen.'
---

# Synthetic-data generation with teacher LLM

Use a teacher LLM to generate (input, output) training pairs for a
downstream student fine-tune. Includes filtering for diversity +
difficulty + safety. The pattern that won the prompt-recovery class
of competitions.

Verified by Open Harness Hub mining of wlifferth's "Starter Notebook:
Generating More Data With Gemma" (1820 votes) on llm-prompt-recovery.

## Task

Generate N synthetic (input, output) pairs for fine-tuning a student
model. Filter for diversity, difficulty, and safety. Output Unsloth-
ready JSONL.

## Steps

1. **spawn_seeds** — `harness` → `harness/text-safety-review`
2. **expand_pairs** — `processor` → `processor/persona-set-generator`
3. **filter_diversity** — `processor` → `processor/multi-vector-fusion`
4. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/research-analyst
- **model_adapter**: adapter/ollama-default
- **rule_packs**: `rule-pack/grep-prompt-injection-heuristics`

## Provenance

- Hub artifact: `pipeline/synthetic-data-gen-with-teacher-llm` v0.1.0
- License: `MIT`
- Industry: ai
- Full source manifest: see `references/manifest.yaml`
