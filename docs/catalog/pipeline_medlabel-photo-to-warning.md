# MedLabel — photo-to-warning medicine safety pipeline

*pipeline* · `pipeline/medlabel-photo-to-warning` · v0.1.0 · experimental

Photograph of a medicine label → Gemma 4 vision extract (active
ingredients + dosage + strength + warnings) → drug-interaction
check against the user's current medication list → multilingual
user-language warning if a critical interaction or contraindication
is detected. Offline-first to work in low-connectivity settings.

Verified reference port of MedLabel by [unconfirmed author], shown
at the Gemma 4 Good Hackathon 2026 (companion to Bill_info AI in
the same hackathon's Impact Track — Digital Equity & Inclusivity /
Safety & Trust). Sourced from the project's public YouTube demo;
catalog port maintains the architectural shape but needs author
attribution + repo URL confirmation before claiming author co-
credit.

Implements the same 3 design patterns Bill_info AI publishes:
 - pattern/two-stage-extract-then-judge (extract fields → judge
   interaction risk)
 - pattern/critical-tier-output-override (severe interaction →
   "STOP, do not take, contact doctor" overrides anything else)
 - pattern/refuse-on-redacted (illegible label fields → null +
   "unreadable" warning rather than guessing dosage)

| axis | value |
|---|---|
| industry | healthcare, healthcare.pharmacy, humanitarian, bureaucracy_translation |
| capability | extraction, verification, translation, classification |
| modality | image, text |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



## Task

Given a photograph of a medicine label + user's current med list, detect dangerous drug interactions and emit a multilingual user-language warning.

**pipeline_kind:** `review`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `guard_input` | rule_pack | `rule-pack/grep-prompt-injection-heuristics` | — |
| 2 | `extract_label_fields` | harness | `harness/text-safety-review` | — |
| 3 | `rag_drug_interactions` | rule_pack | `rule-pack/hybrid-retrieval-policy` | — |
| 4 | `judge_interaction_risk` | harness | `harness/text-safety-review` | — |
| 5 | `assemble_warning` | harness | `harness/text-safety-review` | — |
| 6 | `audit` | processor | `processor/audit-trace-emitter` | — |

