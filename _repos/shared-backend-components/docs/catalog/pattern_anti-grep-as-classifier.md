# Anti-pattern: GREP regex as a classifier

*pattern* · `pattern/anti-grep-as-classifier` · v0.1.0 · stable

Stretching pattern-match rules to classify intent / sentiment / risk / topic when the signal is semantic, not lexical. Regex catches the surface form ('passport held') but misses synonyms ('document retained', 'ID locked away'). Becomes a Frankenstein of 200 alternations with corner cases that break each other.

| axis | value |
|---|---|
| industry | cross_industry |
| capability | classification, safety_gating |
| modality | text |
| lifecycle | stable |
| trust_boundary | local |
| license | MIT |



