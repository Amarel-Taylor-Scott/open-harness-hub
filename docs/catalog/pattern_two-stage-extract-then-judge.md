# Two-stage extract-then-judge (separate calls for extraction + classification)

*pattern* · `pattern/two-stage-extract-then-judge` · v0.1.0 · beta

Use two separate LLM calls instead of one combined call: the first
extracts every relevant structured field, the second classifies /
judges given the extracted context. Costs more than a combined call
but measurably improves both extraction accuracy AND judgment
quality — focused criteria do not compete with extraction for the
model's attention.

Reverses the "one prompt does everything" anti-pattern. Particularly
valuable when the judgment task has its own taxonomy (e.g.
Verbraucherzentrale 10-indicator fraud taxonomy) that benefits from
100% of the model's reasoning budget rather than sharing it with
field-extraction parsing.

Published in Sviatoslav Grabovsky's Bill_info AI (Gemma 4 Good
Hackathon): 96% extraction success + 95.8% field accuracy + 100%
redacted-field refusal across a 28-document evaluation set.

| axis | value |
|---|---|
| industry | ai, cross_industry, bureaucracy_translation, humanitarian |
| capability | reasoning, extraction, classification, verification |
| modality | text, image |
| lifecycle | beta |
| trust_boundary | mixed |
| license | CC-BY-4.0 |



