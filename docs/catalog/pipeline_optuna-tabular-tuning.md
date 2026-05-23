# Optuna hyperparameter tuning for tabular models

*pipeline* · `pipeline/optuna-tabular-tuning` · v0.1.0 · stable

Optuna-driven hyperparameter optimization for LGB / XGB / CatBoost.
TPESampler over typical search space (lr, num_leaves/max_depth,
n_estimators, subsample, colsample, reg_alpha, reg_lambda).
N_trials 50-200 with pruning. Trial objective = K-fold CV metric.

Verified by Open Harness Hub mining: suvroo PS4E7 Optuna|XGBoost
(205 votes — explicit Optuna in title), gusthema TFDF (1717 votes
with k-fold CV), greysky Home Credit baseline (1397 votes).

| axis | value |
|---|---|
| industry | ai, finance, scientific_research |
| capability | evaluation, classification |
| modality | structured |
| lifecycle | stable |
| trust_boundary | local |
| license | MIT |



## Task

Run Optuna study to find best hyperparameters; return best params + CV score.

**pipeline_kind:** `hyperparameter_tuning`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `search` | processor | `processor/iterative-revise-loop` | — |
| 2 | `audit` | processor | `processor/audit-trace-emitter` | — |

