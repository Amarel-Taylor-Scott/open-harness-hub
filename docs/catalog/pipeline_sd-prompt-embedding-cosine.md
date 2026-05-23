# Stable-Diffusion prompt embedding + cosine evaluation

*pipeline* · `pipeline/sd-prompt-embedding-cosine` · v0.1.0 · stable

Embed Stable-Diffusion prompts using sentence-transformers, compare
candidate prompts against gold prompts via cosine similarity. The
standard scoring approach for prompt-recovery competitions where
the metric is mean cosine similarity (Σ cos(predicted_embed,
gold_embed) / N).

Verified by Open Harness Hub mining: inversion Calculating Stable
Diffusion Prompt Embeddings (617 votes), leonidkulyk BLIP+CLIP (732
votes — uses sentence-transformer embeddings for scoring).

| axis | value |
|---|---|
| industry | ai, creative, creative.image |
| capability | evaluation, embedding |
| modality | text |
| lifecycle | stable |
| trust_boundary | local |
| license | MIT |



## Task

Embed candidate + gold prompts via sentence-transformer; return mean cosine similarity.

**pipeline_kind:** `evaluation`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `embed_candidates` | processor | `processor/embedder-minilm` | — |
| 2 | `embed_gold` | processor | `processor/embedder-minilm` | — |
| 3 | `cosine_score` | processor | `processor/multi-vector-fusion` | — |
| 4 | `audit` | processor | `processor/audit-trace-emitter` | — |

