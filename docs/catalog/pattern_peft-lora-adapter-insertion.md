# PEFT LoRA adapter insertion

*pattern* · `pattern/peft-lora-adapter-insertion` · v0.1.0 · stable

Train tiny low-rank decomposition matrices A∈R^(d×r), B∈R^(r×d) inserted alongside frozen base weights W. Forward pass becomes W·x + B·A·x. Only A + B are trained; base stays frozen. Adapter weights are ~1% of base; multiple task adapters can be hot-swapped against one base model in memory.

| axis | value |
|---|---|
| industry | cross_industry |
| capability | generation |
| modality | text |
| lifecycle | stable |
| trust_boundary | local |
| license | MIT |



