# LoRA + QLoRA pairwise-preference fine-tune (Gemma-2-9b 4-bit)

*pattern* · `pipeline/lora-qlora-pairwise-pref-finetune` · v0.1.0 · beta

Production-verified fine-tune shape for the LMSYS / WSDM Chatbot
Arena class of pairwise-preference competitions. Load Gemma-2-9b
with 4-bit BitsAndBytes quantization, attach a PEFT LoRA adapter,
fine-tune SFTTrainer on (prompt, response_A, response_B) → A/B/tie
triples. Inference: same loaded model + classifier head over the
three classes.

Verified by the Open Harness Hub Meta Kaggle deep miner: 3 of 9
pulled WSDM-Cup top-voted kernels match this exact stack
(transformers + peft + bitsandbytes + trl).

| axis | value |
|---|---|
| industry | ai, cross_industry |
| capability | classification, evaluation |
| modality | text |
| lifecycle | beta |
| trust_boundary | local |
| license | MIT |



