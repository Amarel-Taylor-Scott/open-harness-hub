# Tabular binary-classification playbook (domain knowledge)

Reference for reasoning about the data family in this competition. The default `automl.py` run already applies
the robust defaults below; consult this only if you want to justify a deviation.

## What usually moves AUC on tabular data

- **Gradient-boosted trees are the workhorse.** `HistGradientBoosting` handles NaNs natively, is fast on CPU,
  and is usually at or near the top. Tree ensembles (`RandomForest`, `ExtraTrees`) add diversity for blending.
- **Blending beats a single model.** Rank-averaging the top 2–3 diverse models' probabilities is a cheap,
  robust gain and reduces variance on the hidden split.
- **Cross-validated AUC is the honest signal.** Trust out-of-fold AUC over a single train/valid split; when
  the public score and CV disagree, prefer the model with the higher, more stable CV AUC.
- **Leakage is the classic trap.** Fit imputers/encoders on train only; never use test statistics. The skill
  does this by construction.

## Feature handling that generalizes across the dataset family

- Median-impute numerics (robust to outliers); keep NaN indicators only if a model can't handle NaN.
- One-hot encode low-cardinality categoricals; frequency-encode high-cardinality ones (avoids blowing up the
  feature count and overfitting rare levels).
- Leave monotone tree models to find interactions; don't hand-craft many polynomial features under a time
  budget.

## Budget discipline

- One strong skill run + submit gives a real score fast. Iterate only if `get_status` shows budget to spare.
- More folds (`--folds 8`) buys a steadier estimate at a small time cost; use it once you have a baseline in.
- A submitted 0.90 AUC beats an unsubmitted 0.95 — always keep a valid `submission.csv` selected.

## Failure modes to avoid

- Spending LLM tokens re-deriving preprocessing every turn (use the skill).
- Chasing the public leaderboard into overfit — the private split rewards robust, cross-validated models.
- Forgetting to `select_submission` — unselected work is not scored on the private set.
