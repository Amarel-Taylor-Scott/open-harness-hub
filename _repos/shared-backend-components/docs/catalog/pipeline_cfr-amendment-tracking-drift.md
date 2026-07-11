# US CFR amendment tracking and citation-drift detection

*pipeline* · `pipeline/cfr-amendment-tracking-drift` · v0.1.0 · experimental

Watches a set of tracked Code of Federal Regulations sections, detects when a
Federal Register final rule amends them, snapshots the authoritative text,
computes a content-hash diff against the last known version, and emits
change-data-capture events plus review tickets for every downstream component
that cites the changed section.

Negative-space task: a bare LLM has a frozen, undated view of the CFR — it
cannot tell you that a section was amended last week, what the new effective
date is, or which of your knowledge corpora now cite stale text. It confidently
recites a superseded paragraph. This pipeline grounds every fact in the Federal
Register API (authoritative effective date + html_url), preserves an immutable
capture via the web archive, diffs by content hash so formatting-only edits do
not raise false amendments, and routes real amendments to CDC + review — the
source-document-to-persistent-knowledge-layer pattern applied to volatile law.

| axis | value |
|---|---|
| industry | government.regulatory, legal.compliance, cross_industry |
| capability | retrieval, verification, governance, tool_use |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | mixed |
| freshness | volatile |
| license | MIT |



## Task

Detect Federal Register amendments to tracked CFR sections, snapshot and content-hash the authoritative text, and emit CDC events plus review tickets for every downstream component that cites a changed section.

**pipeline_kind:** `research_web.verified_fact_update`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `fetch_federal_register` | tool | `tool/federal-register-api` | - |
| 2 | `normalize_effective_dates` | processor | `processor/date-parse-multiformat` | - |
| 3 | `snapshot_authoritative_text` | tool | `tool/web-archive-snapshot-request` | - |
| 4 | `diff_against_known` | loop | `pattern/source-document-to-persistent-knowledge-layer` | $.steps.fetch_federal_register.output.count > 0 |
| 5 | `verify_official_source` | processor | `processor/official-sources-checker` | - |
| 6 | `propagate_cdc` | tool | `tool/component-cdc-planner` | - |
| 7 | `route_review` | processor | `processor/escalate-human-review` | - |
| 8 | `audit` | processor | `processor/audit-trace-emitter` | - |

