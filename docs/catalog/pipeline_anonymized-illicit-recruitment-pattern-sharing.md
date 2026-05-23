# Anonymized cross-org pattern sharing for illicit recruitment corridors

*pipeline* · `pipeline/anonymized-illicit-recruitment-pattern-sharing` · v0.1.0 · experimental

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

| axis | value |
|---|---|
| industry | esg, supply_chain, compliance |
| capability | retrieval, verification, anonymization |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | hub |
| license | MIT |



## Task

Given an org's per-supplier finding set, emit hub-suitable
k-anonymized pattern indicators; query the hub for matching
indicators from peer orgs; surface aggregate signals back to the
org's compliance team.

**pipeline_kind:** `anonymization_and_sharing`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `redact_to_indicator` | processor | `processor/redact-pii-text` | — |
| 2 | `hash_broker_id` | processor | `processor/audit-trace-emitter` | — |
| 3 | `k_anonymity_gate` | processor | `processor/cost-ceiling-gate` | — |
| 4 | `query_hub` | tool | `tool/web-search` | — |
| 5 | `audit` | processor | `processor/audit-trace-emitter` | — |

