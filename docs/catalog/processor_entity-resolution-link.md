# Entity resolution: cluster records into entities

*processor* · `processor/entity-resolution-link` · v0.1.0 · beta

Given N records, cluster those that refer to the same real-world
entity (person, organization, address). Combines:
 1. Blocking on canonical fields (zip, last name initial, alpha-2
    country)
 2. Pairwise similarity using Jaro-Winkler (names), Levenshtein
    (addresses), exact match (emails / SSN / IDs)
 3. Active record linkage with a learned threshold
 4. Transitive closure into entity clusters

Outputs cluster IDs + per-cluster confidence + record-pairs above
the merge threshold.

Implements the Fellegi-Sunter (1969) probabilistic record-linkage
model with modern blocking + locality-sensitive hashing.

| axis | value |
|---|---|
| industry | cross_industry, finance, healthcare, government, compliance |
| capability | verification, extraction, classification |
| modality | text, structured |
| lifecycle | beta |
| trust_boundary | local |
| license | MIT |



