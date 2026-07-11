---
name: personal-chat-pipeline
description: Multi-turn personal chat with preference + memory awareness.
when_to_use: 'Pipeline kind: agent_loop.'
---

# Personal chat pipeline (preference + memory + tool-aware)

Wraps `harness/chat-with-memory` in a concrete pipeline that
loads user preferences, resolves any tool calls, and persists
the turn to the memory backend.

## Task

Multi-turn personal chat with preference + memory awareness.

## Steps

1. **load_prefs** — `processor` → `processor/preference-loader`
2. **chat** — `harness` → `harness/chat-with-memory`
3. **leakage_check** — `rule_pack` → `rule-pack/grep-personal-info-leakage`
4. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/personal-assistant
- **model_adapter**: adapter/anthropic-claude-sonnet
- **rule_packs**: `rule-pack/grep-personal-info-leakage`
- **knowledge_packs**: `knowledge-pack/user-preference-schema`

## Provenance

- Hub component: `pipeline/personal-chat-pipeline` v0.1.0
- License: `MIT`
- Industry: personal_productivity, cross_industry
- Full source manifest: see `references/manifest.yaml`
