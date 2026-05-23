# Perplexity-baseline scoring

*pipeline* · `pipeline/perplexity-baseline-scoring` · v0.1.0 · stable

Score candidate answers by their perplexity under a reference LLM.
Lower perplexity = better fit. Used as a baseline for
prompt-recovery, AI-text-detection, and any task where "fluency
under a fixed prior" is a useful signal.

Verified by Open Harness Hub mining of itahiro's "Perplexity
Baseline [Phi-2, Gemma-7b-it]" (1005 votes) on llm-prompt-recovery.

| axis | value |
|---|---|
| industry | ai |
| capability | evaluation, classification |
| modality | text |
| lifecycle | stable |
| trust_boundary | local |
| license | MIT |



## Task

Given a list of candidate texts and a reference LLM, compute
per-candidate perplexity. Lower is "better fit under the reference
prior." Useful for AI-text detection, prompt recovery, scoring.

**pipeline_kind:** `evaluation`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `score_each` | harness | `harness/text-safety-review` | — |
| 2 | `rank` | processor | `processor/multi-vector-fusion` | — |

