# QLoRA 4-bit fine-tune

*pattern* · `pattern/qlora-4bit-finetune` · v0.1.0 · stable

Load base model in 4-bit NF4 quantization + freeze + insert LoRA adapters that train in BF16/FP16. Enables fine-tuning a 70B model on a single 48GB GPU (or 24GB with aggressive offload). De-quantize on-the-fly during forward pass; gradients flow only into LoRA adapters.

| axis | value |
|---|---|
| industry | cross_industry |
| capability | generation |
| modality | text |
| lifecycle | stable |
| trust_boundary | local |
| license | MIT |



