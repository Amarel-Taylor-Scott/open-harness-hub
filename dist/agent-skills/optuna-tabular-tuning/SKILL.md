---
name: optuna-tabular-tuning
description: Run Optuna study to find best hyperparameters; return best params + CV
  score.
when_to_use: 'Pipeline kind: hyperparameter_tuning.'
---

# Optuna hyperparameter tuning for tabular models

Optuna-driven hyperparameter optimization for LGB / XGB / CatBoost.
TPESampler over typical search space (lr, num_leaves/max_depth,
n_estimators, subsample, colsample, reg_alpha, reg_lambda).
N_trials 50-200 with pruning. Trial objective = K-fold CV metric.

Verified by OpenHubForAI mining: suvroo PS4E7 Optuna|XGBoost
(205 votes — explicit Optuna in title), gusthema TFDF (1717 votes
with k-fold CV), greysky Home Credit baseline (1397 votes).

## Task

Run Optuna study to find best hyperparameters; return best params + CV score.

## Steps

1. **search** — `processor` → `processor/iterative-revise-loop`
2. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/research-analyst
- **model_adapter**: adapter/ollama-default

## Provenance

- Hub component: `pipeline/optuna-tabular-tuning` v0.1.0
- License: `MIT`
- Industry: ai, finance, scientific_research
- Full source manifest: see `references/manifest.yaml`
