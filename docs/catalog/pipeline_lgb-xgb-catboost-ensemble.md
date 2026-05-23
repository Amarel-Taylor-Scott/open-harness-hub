# LightGBM + XGBoost + CatBoost ensemble (tabular ML)

*pipeline* · `pipeline/lgb-xgb-catboost-ensemble` · v0.1.0 · stable

The dominant Kaggle tabular-ML shape: train LightGBM + XGBoost +
CatBoost separately on the same features, blend predictions
(weighted-mean / rank-mean / stacking). K-fold CV (typically 5-10
StratifiedKFold) for both training + ensemble weight selection.

Verified by Open Harness Hub mining: yuanzhezhou baseline LGB+XGB+
CatBoost (1417 votes, Optiver 2023), suvroo Optuna|XGBoost|klib
(205 votes, PS4E7), jetakow Home Credit 2024 (5098 votes — highest
vote count in any kernel we've mined!), greysky Home Credit baseline
(1397 votes), rohanrao AutoML Grand Prix 1st place (222 votes,
CatBoost + ensemble). 5+ verified kernels.

| axis | value |
|---|---|
| industry | ai, finance, finance.lending, finance.fraud |
| capability | classification, evaluation |
| modality | structured |
| lifecycle | stable |
| trust_boundary | local |
| license | MIT |



## Task

Train LGB+XGB+CatBoost; ensemble via weighted mean; serve.

**pipeline_kind:** `training_and_serving`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `guard` | rule_pack | `rule-pack/grep-prompt-injection-heuristics` | — |
| 2 | `train_lgb` | processor | `processor/iterative-revise-loop` | — |
| 3 | `train_xgb` | processor | `processor/iterative-revise-loop` | — |
| 4 | `train_catboost` | processor | `processor/iterative-revise-loop` | — |
| 5 | `ensemble` | processor | `processor/multi-vector-fusion` | — |
| 6 | `audit` | processor | `processor/audit-trace-emitter` | — |

