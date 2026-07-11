# Autonomous Agent Prediction (Beta) — our entry

An ADK Agent Config for Kaggle's [Autonomous Agent Prediction](https://kaggle.com/competitions/autonomous-agent-prediction-beta)
competition: an autonomous agent that trains a binary classifier and submits, under a **60-min / 30-submission
/ $2.00** per-session budget, scored by **AUC ROC**.

## The thesis (why this design)

The budget is the whole game. Deriving an ML pipeline with LLM tokens every run is slow, brittle, and burns
the $2. Instead the agent **reuses a tested pipeline primitive** — the `tabular-automl` skill runs in the
sandbox (debited against *time*, not tokens) and produces a strong, blended submission for near-zero token
cost. The model spends its budget only on orchestration, reading public scores, and selecting the best two
submissions. This is token-reduction-by-reuse applied to win — the same principle as the primitive registry.

## Structure

```
submission.zip
├── agent.yaml                       # ADK Agent Config (model gemini-3.1-flash-lite, tools, skill)
├── prompts/system.md                # budget-aware orchestration: baseline -> submit -> score -> iterate -> select
└── skills/tabular-automl/
    ├── SKILL.md                     # skill manifest
    ├── scripts/automl.py            # the multi-path self-tuning AutoML pipeline (sklearn/pandas/numpy)
    └── resources/playbook.md        # tabular binary-classification domain knowledge
```

## The AutoML skill (multi-path, self-tuning) — verified

`automl.py` auto-discovers train/test/sample_submission, detects the id + target columns, engineers features
(median-impute numerics; one-hot low-card / frequency-encode high-card categoricals; leakage-free), then
**races five model families** (HistGradientBoosting · GradientBoosting · RandomForest · ExtraTrees ·
LogisticRegression) by stratified-k-fold **out-of-fold AUC** and **rank-blends the top three** into
`submission.csv`. A failing model is dropped; if all fail it emits the class prior — it always produces a
valid submission.

**Local smoke tests (synthetic data from a comparable family):**
- numeric + categorical + 10% NaN, integer target → **held-out AUC 0.986** (CV AUC ~0.985 across all 5 models)
- string "yes/no" labels + high-cardinality categorical + custom `PassengerId` → **held-out AUC 0.974**

## Build the submission

```bash
cd dist/competitions/autonomous-agent-prediction
bash build_submission.sh      # -> submission.zip (agent.yaml at the archive root)
```

## Caveats / to validate against the competition's demo notebook

- The exact ADK Agent Config schema (tool/skill declaration syntax) should be checked against the competition's
  provided demo notebook + sample submission; adjust `agent.yaml` field names if they differ.
- Model IDs come from the competition's `models.yaml`; `gemini-3.1-flash-lite` is the cheapest listed — swap
  if the harness names differ.
- The 16 provided training datasets should be used to validate `automl.py` end-to-end before the real
  submission (drop them into this dir and run the skill on each).
