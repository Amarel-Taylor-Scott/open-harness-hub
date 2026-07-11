# Attribution

The OpenHubForAI is a community catalog. Every artifact carries
its own `attribution` block; this file lists notable upstream
contributors whose work is integrated into the catalog as
verified-evidence pipelines + design patterns + reference shapes.

## Verified-evidence pipeline contributors

### Sviatoslav Grabovsky — Bill_info AI (Gemma 4 Good Hackathon)

Sviatoslav's Bill_info AI submission (Hugging Face Space:
[Svityk/bill-info-ai](https://huggingface.co/spaces/Svityk/bill-info-ai),
GitHub: [Svityk/bill-info-ai](https://github.com/Svityk/bill-info-ai))
provided the architectural inspiration for the catalog's
**refugee bureaucracy translation** vertical + **three reusable
design patterns** that now apply across the catalog:

- `pipeline/bill-info-extract-fraud-detect-recommend`
- `knowledge-pack/verbraucherzentrale-fake-inkasso-indicators`
- `rule-pack/grep-fake-inkasso-fraud-flags`
- `persona/bureaucracy-translator-cite-first`
- `rubric/bureaucracy-translation-quality-v1`
- `dataset/bill-info-test-documents`
- `adapter/gemma-4-26b-vision`
- **`pattern/two-stage-extract-then-judge`** — generalizes to ESG /
  radiology / contract review / AppSec
- **`pattern/critical-tier-output-override`** — generalizes to
  CBP-WRO halt, PHI-unredacted halt, ITAR-technical-data halt
- **`pattern/refuse-on-redacted`** — generalizes to insurance claim
  review, benefits adjudication, M&A DD, transfer pricing

Published metrics from Bill_info AI's eval (28 documents): 96%
extraction success, 95.8% field accuracy, 100% refusal accuracy on
redacted documents, 8.5s average latency, three-level fraud
classification.

License: Apache 2.0 (Gemma 4 weights) + MIT (Bill_info AI code).

### CiteMind team — Gemma 4 Good Hackathon 2026

CiteMind (local AI research wiki for PDFs — Tauri 2 + React 19 +
Rust + SQLite + Ollama/Gemma) provided the architectural shape for
the catalog's **local-first research wiki** vertical + three reusable
design patterns:

- `pipeline/citemind-pdf-to-research-wiki`
- `persona/local-first-research-tutor`
- `knowledge-pack/citemind-architecture-reference`
- `rubric/citemind-citation-fidelity-v1`
- `dataset/citemind-pdf-samples`
- `processor/pdf-extract-with-ocr-fallback`, `page-aware-chunker`,
  `local-embedder`, `hybrid-bm25-vector-retrieve`,
  `concept-graph-extractor`
- **`pattern/local-first-with-cited-answers`** — generalizes to
  legal review, defense documentation, BSL-4 SOP study, refugee
  Inkasso letter review
- **`pattern/source-document-to-persistent-knowledge-layer`** —
  generalizes to compliance audit notes, regulatory cross-references,
  ESG disclosure review
- **`pattern/concept-graph-from-text`** — generalizes to ESG
  materiality maps, supply-chain knowledge graphs, drug-interaction
  graphs, DFARS clause flow-down maps

Direct upstream repo URL + author attribution pending CiteMind team
confirmation. Marked `lifecycle: experimental` with attribution caveat
until the upstream is identified.

License: Apache 2.0 (Gemma 4 weights); upstream CiteMind repo
license TBD.

### MedLabel team — Gemma 4 Good Hackathon 2026

MedLabel ([YouTube demo](https://www.youtube.com/watch?v=JwU44PaKQc8))
provided the architectural shape for the catalog's **medicine-safety
photo-to-warning** pipeline:

- `pipeline/medlabel-photo-to-warning`
- `knowledge-pack/drug-interaction-references`

Author attribution + repo URL confirmation pending. Catalog port is
explicitly marked `lifecycle: experimental` with attribution caveat
until the MedLabel team can be reached for direct co-authorship
credit. If you are the MedLabel team or know how to reach them,
please open an issue or PR.

License: Apache 2.0 (Gemma 4 weights); upstream repo license TBD.

## Kaggle kernel contributors (verified-evidence pipelines)

The catalog includes 27 verified-evidence pipelines mined from
107 top-voted Kaggle kernels across 33 competition families. Each
pipeline manifest carries attribution to the specific kernel + author
+ vote count. Selected highest-impact contributors:

| Kernel author | Kernel | Votes | Catalog pipeline |
|---|---|---|---|
| Sviatoslav Grabovsky (Svityk) | Bill_info AI HF Space | (eval-based) | pipeline/bill-info-extract-fraud-detect-recommend |
| Daniel Herman (jetakow) | Home Credit 2024 Starter Notebook | 5098 | pipeline/lgb-xgb-catboost-ensemble |
| Mr_KnowNothing (tanulsingh077) | Jigsaw Zero To Transformers + BERT | 6394 | pipeline/bidirectional-lstm-sequence-prediction |
| Phil Culliton (philculliton) | NLP Getting Started Tutorial | 5014 | (referenced) |
| tanulsingh077 | Twitter Sentiment Extraction | 3818 | (referenced) |
| Ryan Holbrook (ryanholbrook) | Jane Street RMF Demo | 3259 | (referenced) |
| Heads or Tails (headsortails) | M5 EDA | 3215 | (referenced) |
| Gabriel Preda (gpreda) | Santander EDA & Prediction | 2963 | (referenced) |
| Sohier Dane (sohier) | Optiver 2023 Basic Submission | 2467 | (referenced) |
| Chris Deotte (cdeotte) | AMEX XGBoost Starter | 2110 | pipeline/lgb-xgb-catboost-ensemble |
| Chris Deotte (cdeotte) | SIIM Melanoma Triple Stratified KFold | 1710 | (referenced) |
| Awsaf (awsaf49) | HMS HBAC KerasCV / BirdCLEF / UWMGI | 1733/659/1473 | pipeline/efficientnet-medical-imaging + audio-mel-spec-cnn-classifier + unet-segmentation-tta |
| Chris Deotte (cdeotte) | EfficientNetB0 Starter HMS | 1564 | pipeline/efficientnet-medical-imaging |
| Eisuke Mizutani (emiz6413) | Gemma-2 9b 4-bit QLoRA LMSYS | 1351 | pipeline/lora-qlora-pairwise-pref-finetune |
| Chris Deotte (cdeotte) | TensorFlow LongFormer NER | 1350 | pipeline/longformer-bigbird-ner |
| Abhishek Thakur (abhishek) | Two LongFormers Better Than 1 | 1323 | pipeline/longformer-bigbird-ner |
| simjeg | Platypus2-70B with Wikipedia RAG | 1248 | pipeline/large-model-faiss-rag |
| Lewis Tunstall (lewtun) | Updated Code Interpretation AIMO 2 | 1173 | pipeline/deepseek-r1-code-interpreter-math |
| Henrique Mendonça (hmendonca) | Mask-RCNN COCO Transfer | 1194 | pipeline/mask-rcnn-coco-transfer |
| Henrique de Macedo (rhtsingh) | Utilizing Transformer Representations Efficiently | 1247 | pipeline/bidirectional-lstm-sequence-prediction |
| Laura Fink (allunia) | Pulmonary DICOM Preprocessing | 1249 | pipeline/dicom-medical-image-preprocessing |
| Renoir (itahiro) | DeepSeek-R1-distill-Qwen-7B AIMO 2 | 1399 | pipeline/deepseek-r1-code-interpreter-math |

Per-pipeline attribution (source URL, author, license, vote count
where applicable) lives in the `attribution:` block of each pipeline
manifest under `catalog/pipelines/`.

## Reviewer feedback

### Hassan Gasim — "Docker-Hub-for-harnesses" framing

Hassan's comment that "we have hubs for models (Hugging Face) and
vector DBs, but we lack a unified Harness Hub" directly motivated
[`docs/spec/OPENHUBFORAI_SPEC.md`](../../shared-backend-components/docs/spec/OPENHUBFORAI_SPEC.md) +
the [`comparison/peer-registries.md`](../comparison/peer-registries.md)
analysis. His CSDDD-compliance-harness example became the
ESG / CSDDD vertical's design north star.

### Anonymous Ukrainian reviewer of Bill_info AI

Sviatoslav notes a Ukrainian reviewer in Germany who tested
Bill_info AI surfaced the multi-page document requirement — that
feedback shaped the pipeline's multi-page input handling. The same
principle (real users surface real requirements early) applies
across all catalog verticals.

## Citation

If you reference this catalog in academic / commercial work, please
cite the specific artifacts you use (each has an `id` + `attribution`
block). The catalog as a whole is MIT-licensed; individual upstream
contributors' licenses are preserved.

## Adding yourself

If you contribute artifacts via PR, your name + GitHub handle goes
in the artifact's `authors:` list. If you build something the catalog
should reference, see
[`docs/contributing/integrating-hackathon-submissions.md`](../../shared-backend-components/docs/contributing/integrating-hackathon-submissions.md).

## Notes on attribution policy

- Every artifact's `authors:` list is preserved through forks
- Every artifact's `attribution` block (source URL + author + license)
  is mandatory
- Catalog ports of upstream work cite the upstream + add
  "OpenHubForAI contributors" as a secondary author for the port
- Author attribution is corrected on receipt of PR or issue from the
  original creator
- The catalog never claims primary authorship of work it ports —
  only the specific port + schema + vocabulary contributions
