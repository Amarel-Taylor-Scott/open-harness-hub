# Email triage pipeline (preference-loaded, tone-matched, leakage-checked)

*pipeline* · `pipeline/email-triage-pipeline` · v0.1.0 · experimental

Concrete pipeline wrapping `harness/email-triage-and-draft`.
Loads user prefs + recipient tone → triages each thread → drafts
replies → leakage-checks each draft → returns thread decisions.

| axis | value |
|---|---|
| industry | personal_productivity, cross_industry |
| capability | dialogue, summarization, routing, memory |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



## Task

Triage inbox + draft replies + leakage-check each draft.

**pipeline_kind:** `agent_loop`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `load_prefs` | processor | `processor/preference-loader` | — |
| 2 | `load_tone_history` | processor | `processor/recipient-tone-history` | — |
| 3 | `triage_and_draft` | harness | `harness/email-triage-and-draft` | — |
| 4 | `leakage_check` | rule_pack | `rule-pack/grep-personal-info-leakage` | — |
| 5 | `audit` | processor | `processor/audit-trace-emitter` | — |

