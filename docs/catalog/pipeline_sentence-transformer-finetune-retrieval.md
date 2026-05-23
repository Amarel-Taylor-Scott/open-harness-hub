# Sentence-transformer fine-tune for retrieval / ranking

*pipeline* · `pipeline/sentence-transformer-finetune-retrieval` · v0.1.0 · stable

Fine-tune a sentence-transformer (Sentence-BERT family) on
(query, positive, negative) triplets using MultipleNegativesRankingLoss
or CosineSimilarityLoss. Embeds documents into a dense space,
retrieves by cosine similarity. The dominant Kaggle shape for
retrieval-style competitions on educational content + curriculum
matching + semantic search.

Verified by Open Harness Hub mining: yuiwai LECR-stsb-roberta-base
(420 votes, Learning Equality Curriculum Recommendations), yuiwai
all-MiniLM-L6-v2-tuning (401 votes, LECR), karakasatarik 0.459
single-model-inference w/ postprocessing (375 votes, LECR),
leonidkulyk BLIP+CLIP interrogator (732 votes, SD image-to-prompts
— uses sentence-transformer fine-tune). 7+ kernels in our 43-kernel
corpus use sentence-transformers.

| axis | value |
|---|---|
| industry | ai, education, scientific_research |
| capability | retrieval, embedding, reranking |
| modality | text |
| lifecycle | stable |
| trust_boundary | local |
| license | MIT |



## Task

Fine-tune a sentence-transformer on (query, positive, negative) triplets; serve dense retrieval at inference.

**pipeline_kind:** `training_and_serving`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `guard` | rule_pack | `rule-pack/grep-prompt-injection-heuristics` | — |
| 2 | `train` | processor | `processor/iterative-revise-loop` | — |
| 3 | `retrieve_and_rerank` | processor | `processor/cross-encoder-reranker` | — |
| 4 | `audit` | processor | `processor/audit-trace-emitter` | — |

