# Audio classification via mel-spectrogram + CNN (KerasCV / EfficientNet)

*pipeline* · `pipeline/audio-mel-spec-cnn-classifier` · v0.1.0 · stable

Convert audio to mel-spectrograms (librosa or torchaudio), treat as
images, train a CNN backbone (EfficientNet / ResNet via KerasCV or
timm). Standard Kaggle approach for bird-call ID, urban sound
classification, infant cry detection, equipment fault detection.
Audio-specific augmentation: SpecAugment (frequency + time masking),
pitch shift, time stretch.

Verified by Open Harness Hub mining: awsaf49 BirdCLEF24 KerasCV
starter (659 votes train + 364 votes infer, BirdCLEF 2024) — uses
mel spectrogram + KerasCV CNN.

| axis | value |
|---|---|
| industry | ai, scientific_research, scientific_research.bio |
| capability | classification |
| modality | audio |
| lifecycle | stable |
| trust_boundary | local |
| license | MIT |



## Task

Convert audio to mel-spectrograms, train CNN backbone, classify.

**pipeline_kind:** `training_and_serving`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `guard` | rule_pack | `rule-pack/grep-prompt-injection-heuristics` | — |
| 2 | `spectrogram_train` | processor | `processor/iterative-revise-loop` | — |
| 3 | `ensemble_folds` | processor | `processor/multi-vector-fusion` | — |
| 4 | `audit` | processor | `processor/audit-trace-emitter` | — |

