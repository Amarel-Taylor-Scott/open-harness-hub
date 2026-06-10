# User preference schema (canonical shape for personal assistants)

*knowledge-pack* · `knowledge-pack/user-preference-schema` · v0.1.0 · experimental

Canonical schema for storing user preferences that personal-
assistant harnesses load before taking action. Covers:
 - Communication tone preferences (formal / casual / terse / warm)
 - Scheduling rules (no-meeting hours, focus blocks, time-zone)
 - Privacy rules (what is shareable with whom)
 - Delegation rules (who can act on user's behalf for what)
 - Tool autonomy (autonomous / review-required / never)
 - Recurring tasks + commitments

The schema is portable — same shape works across email / chat /
calendar / personal-RAG harnesses.

| axis | value |
|---|---|
| industry | personal_productivity, cross_industry |
| capability | retrieval |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | volatile |
| license | MIT |



