# Wikidata SPARQL query walker

*processor* · `processor/wikidata-query-walker` · v0.1.0 · experimental

Walks Wikidata via SPARQL queries against query.wikidata.org. Wikidata
holds ~140M items as (subject, property, object) triples with
multilingual labels under CC0 — orders of magnitude cheaper to walk
than prose-first sources like Wikipedia.

Two invocation modes:
 - preset: one of {crimes, standards, legal-concepts, software-
   frameworks, programming-languages, diseases, international-orgs}
   (more presets are added to the registry as needed).
 - sparql: arbitrary SPARQL query (advanced; must respect
   query.wikidata.org SPARQL timeout limits).

Each node carries: qid (e.g., Q42), English label, description,
Wikidata URL, Wikipedia URL (when present), raw_claims (extensible).

This is the leverage walker for 2000x scale — a single preset query
with LIMIT 5000 returns 5000 ready-to-draft nodes in seconds.

| axis | value |
|---|---|
| industry | cross_industry, software, media |
| capability | retrieval, extraction |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | external |
| license | MIT |



