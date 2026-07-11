# Wikipedia category-tree walker

*processor* · `processor/wikipedia-category-walker` · v0.1.0 · experimental

Walks a Wikipedia category tree starting from a root category and
yields one structured "knowledge node" per sub-category and
per-article. Each node carries:

 - title
 - canonical URL
 - revision_id (frozen at walk time for reproducibility)
 - parent_category_path (breadcrumb from walk root)
 - intro_text (first 1500 chars of article body)
 - infobox (structured fields when present)
 - cited_sources (footnote list, up to 50)
 - sub_categories (when the node IS a category)

Designed to feed `harness/draft-manifest-author` so each emitted
node becomes a candidate draft manifest.

Respects:
 - max_depth (default 3) to bound walk size
 - max_nodes (default 200) to bound API + LLM cost
 - rate_limit_per_sec (default 1.0) per Wikipedia API etiquette
 - revision_freeze_ts so the walk is deterministically replayable

Implementation uses MediaWiki Action API (categorymembers + parse)
with on-disk caching keyed on (title, revision_id).

| axis | value |
|---|---|
| industry | media, media.editorial, media.factcheck, software, cross_industry |
| capability | retrieval, extraction |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | external |
| license | MIT |



