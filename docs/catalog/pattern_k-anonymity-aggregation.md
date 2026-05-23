# K-anonymity + HMACed-key cross-organization aggregation

*pattern* · `pattern/k-anonymity-aggregation` · v0.1.0 · stable

Share *aggregated* signal across organizations without revealing
per-org provenance. Each org HMACs the key (broker ID, supplier
hash, address) with a hub-published salt so the same key produces
the same hash everywhere but cannot be reversed. Records are
bucketed by (hashed_key, category, time-window). Buckets with
`count < k` are dropped — small buckets could be re-identified
back to the contributing org. Surviving buckets are signed and
published.

Use whenever cross-org information sharing is required but
per-org confidentiality must be preserved: ESG bad-actor patterns,
AML mule networks, security threat indicators, fraud rings.

The k-anonymity threshold is the lever between strong-anonymity
(high k, slower signal) vs fast-pattern-surfacing (low k, higher
re-identification risk). Differential-privacy extensions add
calibrated noise to each bucket count for stronger guarantees.

| axis | value |
|---|---|
| industry | security, esg, compliance, finance, cross_industry |
| capability | anonymization, verification |
| modality | text, structured |
| lifecycle | stable |
| trust_boundary | hub |
| license | CC-BY-4.0 |



