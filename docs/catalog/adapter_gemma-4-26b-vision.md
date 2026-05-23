# Google Gemma 4 26B-A4B-IT (multimodal vision + native multilingual)

*adapter* · `adapter/gemma-4-26b-vision` · v0.1.0 · stable

Adapter for Google Gemma 4 26B Instruction-Tuned — multimodal
vision (256K context), native multilingual (Ukrainian + German +
many others without dedicated fine-tune), structured JSON output
with schema enforcement, Apache 2.0 open weights enabling
self-hosted deployment.

Used by Sviatoslav Grabovsky's Bill_info AI for refugee
bureaucracy translation. Self-hosting path is critical for NGOs
(Caritas, Diakonie, Verbraucherzentrale) that cannot send
refugee financial documents through closed APIs.

Identifier `google/gemma-4-26b-a4b-it` appears in HF Space logs
on every Bill_info AI request as verifiable proof the system
runs on the actual model (not a smaller substitute).

| axis | value |
|---|---|
| industry | ai, cross_industry, bureaucracy_translation, humanitarian |
| capability | generation, dialogue, reasoning, extraction |
| modality | text, image |
| lifecycle | stable |
| trust_boundary | local |
| license | MIT |



