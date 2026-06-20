# Language lock — detect input language and enforce same-language output

*processor* · `processor/language-lock-respond-in-input-language` · v0.1.0 · stable

Pre-pass processor that detects the user's input language (using a
lightweight on-device language identifier such as fastText LangDetect or
lingua-py) and injects a language-lock instruction into the system prompt
before the LLM call. This prevents the model from mid-response switching
to English or another dominant language — a common failure mode in
multilingual low-resource settings.

The processor emits two artefacts used by the next pipeline step:
  detected_language — BCP-47 language code (e.g., "mr", "sw", "tw",
                      "tl", "hi", "yo")
  patched_system_prompt — the original system prompt with a language-lock
                          instruction prepended:
                          "IMPORTANT: The user is writing in {language}.
                          You MUST respond ONLY in {language}. Do not
                          switch to English or any other language mid-
                          response, even for technical terms. If a term
                          has no {language} equivalent, transliterate it."

CAPABILITY LIFT (structural): frontier and on-device models trained
predominantly on English data have a strong prior toward English responses,
especially when a question touches domain vocabulary that appears more
frequently in English training data (e.g., STEM terms). This bias is
architectural — it persists across model generations for under-resourced
languages. Deterministically locking the output language via a prompt
constraint is a structural fix. lift_reason: sparse_data (low-resource
language response bias); mechanism: orchestration_complexity (requires
a deterministic language-detect step outside the model's own generation).

| axis | value |
|---|---|
| industry | education, education.k12, education.tutoring, cross_industry |
| capability | extraction, format_conversion, safety_gating |
| modality | text |
| lifecycle | stable |
| trust_boundary | local |
| license | Apache-2.0 |



