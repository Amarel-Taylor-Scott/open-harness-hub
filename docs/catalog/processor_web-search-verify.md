# Web search verify (a search call that queries authoritative sources for a claim and checks agreement)

*processor* · `processor/web-search-verify` · v0.1.0 · experimental

CONTEXT-ASSURANCE component. A SEARCH-CALL tool: given a claim, it queries
configured AUTHORITATIVE sources (not the open web at large) for independent
evidence about that claim, then checks whether the returned results AGREE with
it. It is one of the evidence-gathering tools whose output feeds
processor/multi-source-corroborate; on its own it gathers and tags candidate
evidence, it does not pronounce the final corroboration verdict.

EXTERNAL BY CONSTRUCTION (honest framing): this tool makes outbound calls to a
search backend / authoritative APIs. It therefore declares trust_boundary
external and side_effects external_call. It does not store secrets in the
manifest; the search backend, the allow-listed authoritative domains, and any
credentials are supplied as governed runtime configuration, not baked in here.

Procedure (over governed configuration):
  1. Build queries for the claim, restricted to a governed allow-list of
     authoritative domains / endpoints (e.g. a regulator feed, a standards
     body) so that "agreement" means agreement among sources we have declared
     trustworthy, not arbitrary web pages.
  2. Execute the search call(s) against that allow-list.
  3. For each result, capture a source_record (publisher/domain, URL,
     retrieved_at, content_hash where available — see
     schemas/source-record.schema.json) and a per-result stance toward the
     claim: supports | contradicts | unrelated.
  4. Emit the tagged evidence set plus a preliminary agreement summary
     (how many allow-listed sources supported vs contradicted). Independence
     collapse and the final corroborated/insufficient verdict are left to
     processor/multi-source-corroborate, which judges independence from
     provenance.

HONEST ABOUT LIMITS: a search call reflects what the queried sources currently
publish; it does not by itself establish ground truth, and a source can be
wrong or stale. That is exactly why its output is routed into independent
corroboration and (for the cited authority) freshness diffing
(processor/authority-fetch-diff) rather than trusted as a single answer.

GOVERNANCE (honest framing): this is a governed DEFINITION of a search-and-
check tool, not a measured-lift claim. It describes the allow-listed query
scope, the per-result stance tagging, and the evidence object it emits. It does
NOT assert a populated accuracy or recall number, and it does NOT invent
authoritative URLs — the authoritative endpoints are governed runtime config.

| axis | value |
|---|---|
| industry | cross_industry, ai, media.factcheck, government.regulatory |
| capability | verification, research, tool_use |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | external |
| freshness | volatile |
| license | Apache-2.0 |



