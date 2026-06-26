---
name: call-qa-grading-from-audio
description: 'Given a recorded customer call (audio) and the applicable QA rubric,
  produce a per-dimension QA score where every dimension''s rating is justified by
  a verbatim quoted transcript span with its timestamp, and a pass/fail gate on whether
  the agent spoke the required disclosure(s). Output: dimension scores + cited spans
  + disclosure verdict (disclosed | missing_required_disclosure) + overall grade.'
when_to_use: 'Pipeline kind: evaluate.'
---

# Call-QA grading from audio with cited transcript spans + required-disclosure gate

Negative-space task: grading a recorded support/collections/sales call
against a QA rubric. A bare LLM handed a raw audio file (or even a
transcript) produces a plausible score with no audit trail, drifts on
whether a MANDATORY disclosure was actually spoken, and cites nothing —
so the score cannot be defended in a dispute or a regulator review. This
pipeline transcribes deterministically with Whisper (segments +
timestamps), redacts PII before the model, retrieves the controlling QA
criteria, grades each rubric dimension with the model REQUIRED to quote the
verbatim transcript span that justifies it, and runs a deterministic gate
that fails the call when a required-disclosure phrase is absent from the
transcript — regardless of what the model scored.

Capability lift is structural: the durable lift is grounding (every score
tied to a quoted span) + a deterministic disclosure check (a phrase is
present in the transcript or it is not — one correct answer). Both survive
model upgrades; the transcription, redaction, retrieval, and disclosure
check are freezable and cost no model tokens beyond the single grading call.

Bundle: Standard hybrid RAG over the QA-criteria corpus (taxonomy Bundle A)
fronted by an audio→text Input-Formatting step and closed by grounded,
cited grading with deterministic verification.

## Task

Given a recorded customer call (audio) and the applicable QA rubric, produce
a per-dimension QA score where every dimension's rating is justified by a
verbatim quoted transcript span with its timestamp, and a pass/fail gate on
whether the agent spoke the required disclosure(s). Output: dimension scores
+ cited spans + disclosure verdict (disclosed | missing_required_disclosure)
+ overall grade.

## Steps

1. **transcribe** — `processor` → `processor/audio-to-text-whisper`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **grep_flags** — `rule_pack` → `rule-pack/grep-customer-escalation-quality-flags`
4. **retrieve_criteria** — `rule_pack` → `rule-pack/rag-customer-escalation-quality-retrieval-policy`
5. **disclosure_check** — `processor` → `processor/verify-regex-criterion`
6. **grade_harness** — `harness` → `harness/customer-escalation-quality-review`
7. **check_citations** — `processor` → `processor/citation-span-checker`
8. **grade** — `processor` → `processor/llm-judge`
9. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/customer-escalation-reviewer
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/customer-escalation-quality-frameworks`
- **rule_packs**: `rule-pack/grep-customer-escalation-quality-flags`, `rule-pack/rag-customer-escalation-quality-retrieval-policy`

## Success criteria

- rubric `rubric/customer-escalation-quality-quality-v1` threshold 0.65
- deterministic `$.steps.check_citations.output.result.pass` == `True`
- composite `OR` over 2 child criteria

## Provenance

- Hub component: `pipeline/call-qa-grading-from-audio` v0.1.0
- License: `MIT`
- Industry: retail.support, customer_success.escalation, finance.fraud
- Full source manifest: see `references/manifest.yaml`
