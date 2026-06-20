# On-device OCR pre-pass (ML Kit / TFLite, offline, deterministic text extraction)

*processor* · `processor/on-device-ocr-prepass` · v0.1.0 · experimental

Runs on-device optical character recognition (e.g. Google ML Kit Text
Recognition, TFLite OCR, or Tesseract) against an image before passing
input to the language model. The extracted text is appended to the model
prompt as a structured ```ocr_text block, giving the model a deterministic
high-accuracy text signal rather than relying on its own vision-token
decoding. Also emits bounding-box metadata for downstream spatial reasoning.

CAPABILITY LIFT (structural): small on-device vision-language models have
significantly lower text recognition accuracy than purpose-built OCR engines
(especially for handwriting, low-contrast text, non-Latin scripts). The OCR
engine is a deterministic verifier — it cannot hallucinate characters the
way a VLM can. This is a durable lift: OCR engines outperform VLM vision
tokens on sub-token-level character accuracy by design (sub_token mechanism),
and the advantage is structural because the failure is architectural (VLM
tokenisation is lossy for character-level text). lift_reason:
deterministic_guarantee; mechanism: sub_token.

| axis | value |
|---|---|
| industry | education, healthcare.public_health, ai, cross_industry |
| capability | extraction, format_conversion, verification |
| modality | image, text, structured |
| lifecycle | experimental |
| trust_boundary | local |
| license | Apache-2.0 |



