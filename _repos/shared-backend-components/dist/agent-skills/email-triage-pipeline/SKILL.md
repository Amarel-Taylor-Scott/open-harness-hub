---
name: email-triage-pipeline
description: Triage inbox + draft replies + leakage-check each draft.
when_to_use: 'Pipeline kind: agent_loop.'
---

# Email triage pipeline (preference-loaded, tone-matched, leakage-checked)

Concrete pipeline wrapping `harness/email-triage-and-draft`.
Loads user prefs + recipient tone → triages each thread → drafts
replies → leakage-checks each draft → returns thread decisions.

## Task

Triage inbox + draft replies + leakage-check each draft.

## Steps

1. **load_prefs** — `processor` → `processor/preference-loader`
2. **load_tone_history** — `processor` → `processor/recipient-tone-history`
3. **triage_and_draft** — `harness` → `harness/email-triage-and-draft`
4. **leakage_check** — `rule_pack` → `rule-pack/grep-personal-info-leakage`
5. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/inbox-zero-coach
- **model_adapter**: adapter/ollama-default
- **rule_packs**: `rule-pack/grep-personal-info-leakage`
- **knowledge_packs**: `knowledge-pack/user-preference-schema`

## Success criteria

- deterministic `$.steps.leakage_check.output.hit_count` == `0`
- deterministic `$.steps.load_prefs.output.preferences` is_truthy `None`

## Provenance

- Hub component: `pipeline/email-triage-pipeline` v0.1.0
- License: `MIT`
- Industry: personal_productivity, cross_industry
- Full source manifest: see `references/manifest.yaml`
