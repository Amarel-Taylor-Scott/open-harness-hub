# Synthetic climate disclosure samples (2 cases)

*dataset* · `dataset/climate-disclosure-samples` · v0.1.0 · experimental

Two synthetic corporate climate disclosures for testing
`pipeline/climate-disclosure-review`:
 - sample-disclosure-good.json — Acme Corp, manufacturing, board
   oversight quarterly + 1.5C-aligned transition plan + SBTi
   validated + Scope 3 all 15 categories + ISAE 3410 assurance.
   Expected ~1 finding (offsetting language without disclosure).
 - sample-disclosure-flagged.json — Generic Industries, extractive,
   no board oversight + no transition plan + no Scope 3 + no SBTi
   + no scenario analysis + offset-only pathway. Expected ~9
   findings (2 critical / 5 high / 2 medium).

| axis | value |
|---|---|
| industry | climate, esg, finance |
| capability | evaluation |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



