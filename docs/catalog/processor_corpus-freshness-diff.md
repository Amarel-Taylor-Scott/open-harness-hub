# Corpus freshness diff (watch an authoritative source for change; flag stale internal context)

*processor* · `processor/corpus-freshness-diff` · v0.1.0 · experimental

CONTEXT-ASSURANCE component. Watches a registered authoritative source for
change and flags internal corpus context that has gone STALE relative to it.
This is the freshness axis of context assurance: a corpus can be perfectly
faithful to what was indexed and still be wrong because the world moved.

Given a source_record describing the authoritative origin (publisher,
source_url, effective_date, content_hash — see schemas/source-record.schema.json)
and the internal corpus snapshot derived from it, this processor:
  1. Re-fetches or re-reads the authoritative source and computes its current
     content_hash and effective_date.
  2. Compares against the content_hash / effective_date captured when the
     internal context was last derived.
  3. Emits a freshness verdict per derived object: current | stale | unknown,
     with the observed source change (hash delta, date delta) as the warrant.
  4. Raises a staleness flag (and optional review_ticket) when the
     authoritative source has changed but the internal context has not been
     re-derived inside its declared freshness window.

WORKED DEMO (the stale wire-transfer-limit failure): a bank's internal RAG
corpus encodes a daily wire-transfer limit. The authoritative limit is
published by the institution and changes; the internal index is rebuilt
monthly-or-less, so an agent answers with the old limit. This processor
watches the authoritative source, detects the content_hash / effective_date
change, and flags the internal context as STALE before the agent serves it.

GOVERNANCE (honest framing): this is a governed DEFINITION of a freshness
check, not a measured-lift claim. It describes WHAT is watched (a registered
authoritative source_record), WHEN context is considered stale (source changed
outside the declared freshness window), and the deterministic warrant for each
verdict (observed hash / effective_date deltas). It does not assert a populated
lift number. The differentiator versus faithfulness-only RAG evaluation is
that faithfulness asks "did the answer match the corpus"; freshness-diff asks
"is the corpus still TRUE and current relative to its authoritative origin".

| axis | value |
|---|---|
| industry | cross_industry, finance, government.regulatory, ai |
| capability | verification, governance |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | external |
| freshness | volatile |
| license | Apache-2.0 |



