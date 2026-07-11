# Statute / regulation clarity & interpretation-risk review

*pipeline* · `pipeline/statute-clarity-review` · v0.1.0 · experimental

End-to-end pipeline that reviews a STATUTE, REGULATION, ORDINANCE,
or AGENCY RULE and produces a structured assessment of drafting
quality + interpretation risk:

Output:
 - per-section findings tagged with canon (ejusdem generis,
   expressio unius, etc.) OR drafting-failure category
 - severity (critical / high / medium / low)
 - suggested smallest-fix redline OR "requires policy decision"
 - rubric score (rubric/statute-clarity-v1)

Use cases:
 - Pre-enactment legislative-counsel review
 - Regulatory comment drafting (highlight ambiguity to comment on)
 - Plain-language statute summaries for the regulated population
 - "Is this drafted in a way a court can apply?" pre-litigation
   assessment

NOT legal advice; not jurisdiction-specific outside the cited
authorities; descriptive, not predictive.

| axis | value |
|---|---|
| industry | legal, legal.compliance, government, government.regulatory |
| capability | evaluation, extraction, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



## Task

Given the text of a statute, regulation, ordinance, or agency rule,
produce a structured assessment of drafting quality and
interpretation risk: per-section findings tagged with canon /
failure category / severity / suggested redline, plus a rubric
score against `rubric/statute-clarity-v1`.

**pipeline_kind:** `grading`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `normalize` | processor | `processor/structured-to-prose` | - |
| 2 | `grep_ambiguity` | rule_pack | `rule-pack/grep-statute-ambiguity-flags` | - |
| 3 | `rag_canons` | rule_pack | `rule-pack/hybrid-retrieval-policy` | - |
| 4 | `review` | harness | `harness/statute-clarity-review` | - |
| 5 | `grade` | processor | `processor/llm-judge` | - |
| 6 | `audit` | processor | `processor/audit-trace-emitter` | - |

