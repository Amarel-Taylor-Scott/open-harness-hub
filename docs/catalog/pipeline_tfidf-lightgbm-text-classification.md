# TF-IDF + LightGBM text classification

*pattern* · `pipeline/tfidf-lightgbm-text-classification` · v0.1.0 · stable

The non-LLM baseline that consistently wins or co-wins Kaggle text-
classification competitions. Char- and word-ngram TF-IDF feature
extraction → LightGBM (often stacked with SGDClassifier / MultinomialNB)
→ calibrated probability.

Verified by Open Harness Hub Meta Kaggle deep mining: top kernels of
`llm-detect-ai-generated-text` all use this stack, often as the lead
baseline before any DeBERTa fine-tune is added.

| axis | value |
|---|---|
| industry | ai, cross_industry, media |
| capability | classification |
| modality | text |
| lifecycle | stable |
| trust_boundary | local |
| license | MIT |



