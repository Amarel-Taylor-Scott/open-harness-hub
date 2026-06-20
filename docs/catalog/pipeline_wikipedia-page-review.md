# Wikipedia page review (NPOV / V / RS / OR / BLP / MOS)

*pipeline* · `pipeline/wikipedia-page-review` · v0.1.0 · experimental

End-to-end pipeline that reviews a Wikipedia article against the
core content policies and the article-quality rubric. Produces
per-claim findings with policy citation, severity, and suggested
edit (tag / rewrite / remove / talk-page-escalate).

Use cases:
 - GA / FA peer review preparation
 - New page patrol (NPP) backlog assist
 - AfC (Articles for Creation) reviewer assistance
 - "Is my draft ready to publish?" pre-submission check
 - Cleanup queue triage (which {{citation needed}} articles are
   fixable, which need rewriting, which need AfD)

Article text input options:
 - paste raw wikitext
 - paste rendered text
 - (live URL fetch is via the tool/wikipedia-citation-checker
   companion; this pipeline runs against the supplied text only)

NOT a substitute for human editor review. NOT for making BLP
removal decisions — that's an editor / admin call.

| axis | value |
|---|---|
| industry | media, media.editorial, media.factcheck, education |
| capability | evaluation, extraction, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



## Task

Given the text of a Wikipedia article (English Wikipedia, v0.1.0),
produce a per-policy-pillar quality assessment with per-finding
severity, exact quote, section pointer, and suggested edit.

**pipeline_kind:** `grading`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `normalize` | processor | `processor/structured-to-prose` | - |
| 2 | `grep_quality_flags` | rule_pack | `rule-pack/grep-wikipedia-quality-flags` | - |
| 3 | `rag_wp_policies` | rule_pack | `rule-pack/hybrid-retrieval-policy` | - |
| 4 | `review` | harness | `harness/wikipedia-quality-review` | - |
| 5 | `grade` | processor | `processor/llm-judge` | - |
| 6 | `audit` | processor | `processor/audit-trace-emitter` | - |

