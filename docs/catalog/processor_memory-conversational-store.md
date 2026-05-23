# Conversational memory store

*processor* · `processor/memory-conversational-store` · v0.1.0 · experimental

Read / write conversational memory keyed by (user_id, session_id).
Stores the last N turns plus a compressed summary for older turns.
Pluggable backend: SQLite (default), Redis, Postgres, or DynamoDB.

| axis | value |
|---|---|
| industry | cross_industry |
| capability | memory |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



