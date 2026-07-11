# Anti-pattern: Un-cited extraction

*pattern* · `pattern/anti-un-cited-extraction` · v0.1.0 · stable

Pipeline extracts fields from a document but the output does not include a (page, span) pointer back to the source. Downstream consumers cannot verify; mistakes propagate silently; the LLM's authoring style smooths over fabrications.

| axis | value |
|---|---|
| industry | cross_industry, compliance, legal, healthcare |
| capability | extraction |
| modality | text |
| lifecycle | stable |
| trust_boundary | local |
| license | MIT |



