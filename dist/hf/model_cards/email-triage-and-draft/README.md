---
license: MIT
tags:
- cross_industry
- dialogue
- email
- experimental
- inbox-zero
- memory
- open-harness-hub
- personal-assistant
- personal_productivity
- preference-aware
- routing
- summarization
- text
library_name: open-harness-hub
pipeline_tag: summarization
language:
- en
region:
- personal_productivity
- cross_industry
---

# Email Triage + Draft harness (preference-aware, tone-matched)

<!-- Generated from OpenHubForAI manifest `harness/email-triage-and-draft` v0.1.0. Do not edit by hand; edit the source manifest and re-run `python scripts/emit/hf_model_card.py`. -->

## Model description

Email-handling harness: loads user preferences + recipient tone
history, triages each thread (do-now/delegate/defer/drop),
drafts reply candidates matching the recipient's tone, and
gates output through the personal-info-leakage rule pack
before showing drafts to the user.

Default tool autonomy: review-required for sends; autonomous
for calendar holds. Never autonomous on first-time recipients.

## Intended use

Use this harness as a **wrapping workflow around a model call**. It composes:

- `persona` layer
- `privacy` layer
- `grep` layer
- `tools` layer

**Industries**: personal_productivity, cross_industry
**Capabilities**: dialogue, summarization, routing, memory
**Modalities**: text
**Trust boundary**: local

## How the harness runs

### inbox → preferences loaded → recipient tone loaded → triage → draft → leakage check

1. load user preferences (processor/preference-loader)
2. for each thread:
3.   load recipient tone history (processor/recipient-tone-history)
4.   classify (do-now/delegate/defer/drop)
5.   if reply needed: draft (tone-matched)
6.   run rule-pack/grep-personal-info-leakage on draft
7.   if violation: redact OR halt for user input
8.   enforce CC rules (pref-cc-rules)
9.   enforce after-hours-send rule (pref-no-work-after)
10. emit per-thread {classification, draft, leakage_check_result, eta_to_send}

## Privacy boundaries

- **raw_input**: stays local to the assistant process
- **derived_output**: user reviews drafts before any send
- **external_calls**: only if model_target.trust_boundary == external AND user opted in (e.g. ANTHROPIC_API_KEY set)

## Compatible model targets (provider-neutral)

| id | transport | trust |
|---|---|---|
| `local_ollama` | `ollama` | local |
| `anthropic_claude` | `anthropic` | external |

## Evaluation

Bench against a hub `benchmark/*` manifest with `python scripts/emit/lm_eval_harness.py` (emits lm-eval-harness YAML) or `python scripts/emit/promptfoo.py` (emits promptfoo config). Both reference the same `rubric/*` and `dataset/*` manifests.

## Risks & limitations

This is a workflow harness, not a trained model. Risk profile depends on the model wired in via the configured `model_target`. See the source manifest for `input_verification` and `output_verification` checks.

## Citation

```bibtex
@misc{email-triage-and-draft_open_harness_hub,
  title  = {Email Triage + Draft harness (preference-aware, tone-matched)},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/harness/email-triage-and-draft},
  version= {0.1.0},
  year   = {2026}
}
```

License: `MIT`. Hub component: `harness/email-triage-and-draft`.
