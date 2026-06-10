---
name: anonymized-illicit-recruitment-pattern-sharing
description: Given an org's per-supplier finding set, emit hub-suitable k-anonymized
  pattern indicators; query the hub for matching indicators from peer orgs; surface
  aggregate signals back to the org's compliance team.
when_to_use: 'Pipeline kind: anonymization_and_sharing.'
---

# Anonymized cross-org pattern sharing for illicit recruitment corridors

Mechanism for cross-industry knowledge sharing of systemic bad
actors (rogue labor brokers, repeat-offender contractors, illicit
recruitment corridors) WITHOUT leaking corporate-confidential
supply-chain information. The shape:

 1. Each org's audit pipeline emits a `pattern_indicator` record
    (HMACed broker ID + corridor + indicator categories + observation
    window).
 2. Indicators are bucketed; counts < `k` (default k = 5) are
    dropped (k-anonymity).
 3. Surviving buckets are signed and published to a shared hub.
 4. Member orgs query the hub: "have these indicators been seen
    against this corridor / broker?" — returns aggregate count +
    severity, never per-org provenance.

Use case: a beverage company audits a tier-3 packaging supplier in
Mae Sot and finds 3 indicators. The hub already shows 14 indicators
from 4 other orgs against the same broker in the same corridor in
the last 90 days → trigger heightened review across all members.

Inspired by reviewer feedback on the DueCare ecosystem; aligned with
FATF Recommendation 18 information-sharing principles (adapted to
ESG / forced-labor context).

## Task

Given an org's per-supplier finding set, emit hub-suitable
k-anonymized pattern indicators; query the hub for matching
indicators from peer orgs; surface aggregate signals back to the
org's compliance team.

## Steps

1. **redact_to_indicator** — `processor` → `processor/redact-pii-text`
2. **hash_broker_id** — `processor` → `processor/audit-trace-emitter`
3. **k_anonymity_gate** — `processor` → `processor/cost-ceiling-gate`
4. **query_hub** — `tool` → `tool/web-search`
5. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/esg-auditor
- **model_adapter**: adapter/ollama-default
- **rule_packs**: `rule-pack/privacy-pii-text-en`

## Success criteria

- rubric `rubric/esg-supplier-compliance-v1` threshold 0.6

## Provenance

- Hub artifact: `pipeline/anonymized-illicit-recruitment-pattern-sharing` v0.1.0
- License: `MIT`
- Industry: esg, supply_chain, compliance
- Full source manifest: see `references/manifest.yaml`
