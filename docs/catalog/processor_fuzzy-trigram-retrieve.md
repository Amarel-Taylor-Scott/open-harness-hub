# Fuzzy / trigram retrieve

*processor* · `processor/fuzzy-trigram-retrieve` · v0.1.0 · experimental

Substring/typo/name matching via trigram (pg_trgm) + edit/phonetic distance — language-agnostic, in-DB, catches misspellings and name variants. Character-level only; not a semantic ranker.

Retrieval/prompt taxonomy step R1 (see docs/concepts/retrieval-and-prompt-taxonomy.md). One swappable method-component for the governed-model-call recipe; lift is measured at the pipeline level, not on this component.

| axis | value |
|---|---|
| industry | cross_industry, ai |
| capability | retrieval |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



