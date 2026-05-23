# Verify Claim Against Corpus

*pipeline* · `pipeline/verify-claim-against-corpus` · v0.1.0 · experimental

Given a claim and a corpus, return supports / contradicts /
no-evidence with cited passages and a confidence score.

| axis | value |
|---|---|
| industry | cross_industry, media |
| capability | verification, retrieval, reasoning |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



## Task

Given a claim (string) and a corpus (knowledge-pack ref), return a
verdict in {supports, contradicts, no_evidence}, citations, and a
calibrated confidence.

**pipeline_kind:** `verify_data`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `retrieve` | knowledge_pack | `$.inputs.corpus` | — |
| 2 | `judge` | harness | `harness/text-safety-review` | — |

