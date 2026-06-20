# English-pivot translation (generate English first, translate to low-resource language)

*processor* · `processor/english-pivot-translation` · v0.1.0 · experimental

Two-step translation processor that routes through English as a pivot
language to reach low-resource target languages. Instead of translating
directly from a source language (e.g. Filipino official bulletin) to a
target low-resource language (e.g. Waray, Ilocano, Kapampangan), the
processor:

  Step 1 — English generation: prompts the model to produce a complete,
           faithful English output from the source content.
  Step 2 — Low-resource translation: prompts the model to translate the
           English output into the target language, optionally with
           phonetic simplification hints for TTS.

The English-pivot pattern exploits the asymmetry in model training data:
source→English and English→target both have stronger training signal than
source→target directly, because most parallel corpora pass through English.
This yields measurably better fluency for the target language, especially
for technical/numeric content.

CAPABILITY LIFT (structural): direct low-resource-to-low-resource
translation is systematically worse because almost no parallel corpora
exist for these pairs. The gap is a data-distribution artifact: it will
not close for very-low-resource language pairs regardless of model size
unless parallel corpora exist. English-pivot is a structural mitigation.
lift_reason: sparse_data (low-resource language pair); mechanism:
orchestration_complexity (two-stage chained prompt that a single-pass
model call cannot replicate reliably).

| axis | value |
|---|---|
| industry | public_safety, government.regulatory, education, cross_industry |
| capability | translation, format_conversion, agent_loop |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| license | Apache-2.0 |



