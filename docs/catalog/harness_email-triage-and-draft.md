# Email Triage + Draft harness (preference-aware, tone-matched)

*harness* · `harness/email-triage-and-draft` · v0.1.0 · experimental

Email-handling harness: loads user preferences + recipient tone
history, triages each thread (do-now/delegate/defer/drop),
drafts reply candidates matching the recipient's tone, and
gates output through the personal-info-leakage rule pack
before showing drafts to the user.

Default tool autonomy: review-required for sends; autonomous
for calendar holds. Never autonomous on first-time recipients.

| axis | value |
|---|---|
| industry | personal_productivity, cross_industry |
| capability | dialogue, summarization, routing, memory |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |

**Consumes:** `persona_block`, `tool_definition`, `rag_doc`

**Emits:** `reasoning_step`, `context_snippet`

**Contributes to:** `pipeline/email-triage-pipeline`

## Model targets

| id | transport | trust | required | default |
|---|---|---|---|---|
| `local_ollama` | `ollama` | local | False | True |
| `anthropic_claude` | `anthropic` | external | False | False |

## Logic paths

### inbox → preferences loaded → recipient tone loaded → triage → draft → leakage check  
*model_call: `required`*

1. load user preferences (processor/preference-loader)
1. for each thread:
1.   load recipient tone history (processor/recipient-tone-history)
1.   classify (do-now/delegate/defer/drop)
1.   if reply needed: draft (tone-matched)
1.   run rule-pack/grep-personal-info-leakage on draft
1.   if violation: redact OR halt for user input
1.   enforce CC rules (pref-cc-rules)
1.   enforce after-hours-send rule (pref-no-work-after)
1. emit per-thread {classification, draft, leakage_check_result, eta_to_send}

**consumes:** `persona_block`, `tool_definition`, `rag_doc`

**emits:** `reasoning_step`, `context_snippet`

**verification:** draft tone matches the recipient's prior thread style, no personal-info-leakage critical hits in any draft, after-7pm sends auto-queue to next morning, CC rules honored



## Privacy boundaries

- **raw_input**: stays local to the assistant process
- **derived_output**: user reviews drafts before any send
- **external_calls**: only if model_target.trust_boundary == external AND user opted in (e.g. ANTHROPIC_API_KEY set)

