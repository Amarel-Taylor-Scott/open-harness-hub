# US Code section-tree walker

*processor* · `processor/uscode-section-walker` · v0.1.0 · experimental

Walks the United States Code by title → chapter → subchapter →
section, yielding one structured "knowledge node" per section
(and optionally per subsection). Each node carries:

 - usc_citation: e.g., "42 U.S.C. § 1983"
 - title_number, chapter_number, section_number
 - heading (section name)
 - full_text (section text including subsections)
 - effective_date
 - amendments (list of dates and Public Laws)
 - cross_references (other USC sections cited within)
 - notes (Office of Law Revision Counsel notes)
 - canonical_url (uscode.house.gov)
 - revision_id (current LRC release tag)

Pulls from the LRC's downloadable XML files (releases at
uscode.house.gov/download/) — no scraping. Each release is a
full-corpus snapshot with stable section IDs.

Designed to feed `harness/draft-manifest-author` so each section
becomes a candidate knowledge-pack entry, GREP rule-pack pattern,
or rubric input.

Bounds:
 - titles: list of USC titles to walk (default = all 54)
 - max_sections: cap on total sections emitted
 - skip_repealed: bool, default true

NOTE: Treaty-implementation titles (Title 22 affixes, Title 10
military) have heavier cross-references; expect higher per-node
processing cost.

| axis | value |
|---|---|
| industry | legal, legal.compliance, government, government.regulatory |
| capability | retrieval, extraction |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



