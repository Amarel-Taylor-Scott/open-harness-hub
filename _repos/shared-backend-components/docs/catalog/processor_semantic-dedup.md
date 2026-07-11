# Semantic dedup against live catalog (SimHash + Jaccard)

*processor* · `processor/semantic-dedup` · v0.1.0 · experimental

Cheap, no-LLM dedup pass that catches near-duplicates of existing
live-catalog components before sending a draft to the LLM judge.

Two complementary signals:
 - SimHash on (name + description) shingles — 64-bit fingerprint; Hamming
   distance ≤ 3 = "likely duplicate."
 - Jaccard on (industry ∪ capability ∪ modality ∪ tags ∪ slug tokens) —
   structural fit; ≥ 0.60 = "likely duplicate."

BOTH must agree for `is_duplicate: true`. If only one fires, returns
`is_near_match: true` for curator review.

Critical at 2000x scale: without it, the same Wikipedia articles
(re-walked at different depths, in different languages, from different
categories) collapse into thousands of redundant drafts.

| axis | value |
|---|---|
| industry | software, ai, cross_industry |
| capability | classification, verification |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



