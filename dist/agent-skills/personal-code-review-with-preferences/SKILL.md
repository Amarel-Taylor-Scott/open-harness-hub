---
name: personal-code-review-with-preferences
description: Review a code diff applying the reviewer's personal preferences.
when_to_use: 'Pipeline kind: review.'
---

# Personal code review with preference layer

Review a code diff through the user's personal-preference layer. Loads the user's preferences pack, runs the personal-coding-reviewer persona, gates output against the personal-style rule pack, refuses to ship review comments that contain disallowed idioms.

## Task

Review a code diff applying the reviewer's personal preferences.

## Steps

1. **load_preferences** — `rule_pack` → `rule-pack/hybrid-retrieval-policy`
2. **structured_to_prose** — `processor` → `processor/structured-to-prose`
3. **review_with_persona** — `processor` → `processor/llm-judge`
4. **style_gate** — `rule_pack` → `rule-pack/grep-personal-style-flags`
5. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/personal-coding-reviewer
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/personal-preferences-template`
- **rule_packs**: `rule-pack/grep-personal-style-flags`

## Success criteria

- deterministic `$.steps.style_gate.output.fired` == `[]`

## Provenance

- Hub component: `pipeline/personal-code-review-with-preferences` v0.1.0
- License: `MIT`
- Industry: cross_industry
- Full source manifest: see `references/manifest.yaml`
