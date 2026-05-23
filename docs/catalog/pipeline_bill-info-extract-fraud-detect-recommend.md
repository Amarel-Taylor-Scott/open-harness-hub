# Bill_info AI — photo-to-action bureaucracy translator with Verbraucherzentrale-grounded fraud detection

*pipeline* · `pipeline/bill-info-extract-fraud-detect-recommend` · v0.1.0 · beta

Photograph → structured-field extraction (Gemma 4 26B vision) →
deterministic business-rule validation → Gemma 4 26B fraud-detect
call against Verbraucherzentrale 10-indicator taxonomy → action-
first user-language output with critical-tier override on fraud.

Verified port of Sviatoslav Grabovsky's Bill_info AI (Gemma 4 Good
Hackathon, Hugging Face Space at Svityk/bill-info-ai). Eval set:
28 documents (Reddit-sourced real letters, redacted documents for
refusal testing, clear synthetic cases, adversarial edge cases).
Reported metrics: 96% extraction success (27/28), 95.8% field
accuracy, 100% refusal accuracy on 7 redacted documents, 8.5s
average latency, three-level fraud classification (legitimate /
suspicious / likely_scam).

Implements 3 design patterns published from this work:
 - pattern/two-stage-extract-then-judge (focused fraud-detect call
   does not compete with extraction for model attention)
 - pattern/critical-tier-output-override (likely_scam classification
   overrides every other output component to anti-scam guidance)
 - pattern/refuse-on-redacted (null on redacted fields; user sees
   'unknown' in their language, never a hallucinated value)

| axis | value |
|---|---|
| industry | bureaucracy_translation, bureaucracy_translation.payment_letters, bureaucracy_translation.fraud_screening, humanitarian, humanitarian.refugee |
| capability | evaluation, extraction, verification, translation, classification |
| modality | image, text |
| lifecycle | beta |
| trust_boundary | local |
| license | MIT |



## Task

Given a photograph or scan of a bureaucratic document (German
payment letter — Inkasso / Mahnung / phone bill / etc.), output:
(a) one concrete next-24h action in the user's language,
(b) urgency banner color (red/yellow/green),
(c) three-level fraud classification with cited indicators,
(d) full translation + 3-5 recommended steps,
(e) ready-to-send reply draft in the document's source language.
On critical-tier fraud: override every output to anti-scam
guidance.

**pipeline_kind:** `agent_loop`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `guard_input` | rule_pack | `rule-pack/grep-prompt-injection-heuristics` | — |
| 2 | `extract_fields_gemma_vision` | harness | `harness/text-safety-review` | — |
| 3 | `validate_business_rules` | processor | `processor/verify-deterministic-criterion` | — |
| 4 | `structured_to_prose` | processor | `processor/structured-to-prose` | — |
| 5 | `grep_fake_inkasso_flags` | rule_pack | `rule-pack/grep-fake-inkasso-fraud-flags` | — |
| 6 | `fraud_detect_gemma` | harness | `harness/text-safety-review` | — |
| 7 | `rag_against_verbraucherzentrale` | rule_pack | `rule-pack/hybrid-retrieval-policy` | — |
| 8 | `assemble_user_facing` | harness | `harness/text-safety-review` | — |
| 9 | `audit` | processor | `processor/audit-trace-emitter` | — |

