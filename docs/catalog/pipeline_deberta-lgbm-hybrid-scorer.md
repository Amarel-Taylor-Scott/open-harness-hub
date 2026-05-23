# DeBERTa-v3 + LightGBM hybrid scorer (with spell autocorrect)

*pipeline* · `pipeline/deberta-lgbm-hybrid-scorer` · v0.1.0 · stable

Hybrid two-stage pipeline: (1) DeBERTa-v3 to embed text, (2)
LightGBM head trained on (DeBERTa embedding + hand-crafted text
features + autocorrected text). Spell autocorrect (SymSpellPy)
pre-stage. The dominant CommonLit essay-scoring shape — combines
the semantic power of a transformer with the gradient-boosted-tree
stability for the final regression head.

Verified by Open Harness Hub mining: cody11null Tuned DeBERTaV3+LGBM
+autocorrect (803 votes, CommonLit Evaluate Student Summaries),
tsunotsuno [updated] DeBERTaV3+LGBM with spell autocorrect (519
votes, same competition). 2-of-top-2 essay-grading kernels use
this hybrid shape.

| axis | value |
|---|---|
| industry | ai, education |
| capability | evaluation, extraction, classification |
| modality | text |
| lifecycle | stable |
| trust_boundary | local |
| license | MIT |



## Task

Score an essay/text on a target dimension via DeBERTa-v3 embeddings + hand-crafted features → LightGBM head.

**pipeline_kind:** `evaluation`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `guard` | rule_pack | `rule-pack/grep-prompt-injection-heuristics` | — |
| 2 | `spell_correct` | processor | `processor/structured-to-prose` | — |
| 3 | `embed_deberta` | processor | `processor/embedder-minilm` | — |
| 4 | `score_lgbm` | processor | `processor/multi-vector-fusion` | — |
| 5 | `audit` | processor | `processor/audit-trace-emitter` | — |

