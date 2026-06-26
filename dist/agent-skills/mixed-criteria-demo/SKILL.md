---
name: mixed-criteria-demo
description: Run contract review + evaluate 5 mixed-kind success criteria.
when_to_use: 'Pipeline kind: review.'
---

# Mixed success-criteria demo (regex + semantic + deterministic + LLM + composite)

Demonstrates `pattern/composable-success-criteria`. The pipeline
runs the contract-clause-review chain, then evaluates its output
against EVERY criterion kind:

 - regex:         output text contains "indemnif" (sanity check)
 - semantic:      output covers ("uncapped indemnity", "DPA")
 - deterministic: output.fired count >= 5
 - llm_judge:     judge contract via rubric, score >= 0.5
 - composite:     (PHI-redact-fired AND no-critical) OR
                 (critical-found AND remediation-proposed)

Each criterion emits its own pass/fail record. The aggregate is
reported alongside the per-criterion breakdown.

## Task

Run contract review + evaluate 5 mixed-kind success criteria.

## Steps

1. **to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **grep_red_flags** — `rule_pack` → `rule-pack/grep-contract-red-flags`
4. **grade** — `processor` → `processor/llm-judge`

## Defaults

- **persona**: persona/contract-reviewer-cite-first
- **model_adapter**: adapter/ollama-default

## Success criteria

- regex `indemnif` against `$.steps.redact_pii.output.text`
- semantic must_cover ['uncapped indemnity damages', 'data processing addendum personal data'] against `$.steps.redact_pii.output.text`
- deterministic `$.steps.grep_red_flags.output.hit_count` >= `0`
- rubric `rubric/contract-review-quality-v1` threshold 0.5
- composite `OR` over 2 child criteria

## Provenance

- Hub component: `pipeline/mixed-criteria-demo` v0.1.0
- License: `MIT`
- Industry: cross_industry, compliance, legal
- Full source manifest: see `references/manifest.yaml`
