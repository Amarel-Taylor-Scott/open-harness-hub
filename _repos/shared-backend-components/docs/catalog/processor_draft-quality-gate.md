# Deterministic pre-LLM draft quality gate

*processor* · `processor/draft-quality-gate` · v0.1.0 · experimental

Cheap, deterministic, no-LLM filter that rejects obviously bad drafts
before sending them to the LLM judge. At 2000x scale this is load-
bearing — catches the ~80% of bad drafts (placeholder text, malformed
ids, incomplete attribution, short descriptions, slug collisions, etc.)
at zero cost.

Pass criteria (ALL must hold for `accepted: true`):
 - required envelope fields present
 - id format matches "{type}/{kebab-slug}" with slug ≤ 64 chars
 - no placeholder text (TODO, FIXME, lorem ipsum, XXX, REPLACE_ME)
 - description ≥ 80 chars
 - if attribution present, complete (source_url + author + license)
 - id slug does not collide with live catalog entry
 - YAML serializes cleanly without roundtrip differences

Survivors go to `processor/llm-judge` for rubric scoring.

| axis | value |
|---|---|
| industry | software, ai, cross_industry |
| capability | verification, safety_gating |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



