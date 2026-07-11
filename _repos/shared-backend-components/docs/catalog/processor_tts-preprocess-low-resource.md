# TTS pre-processing for low-resource languages (normalize, phonetic-respell, rate hints)

*processor* · `processor/tts-preprocess-low-resource` · v0.1.0 · experimental

Text pre-processing pipeline that transforms model-generated text into a
form suitable for open-source text-to-speech engines (MMS — Meta Massively
Multilingual Speech; Coqui TTS; eSpeak-NG) for low-resource languages.
Designed for the WeatherSpeak PH pattern: disaster alert radio scripts in
Waray, Ilocano, Kapampangan, and similar Philippine regional languages.

Operations applied in sequence:
  1. Lowercase — most TTS models expect lowercase input.
  2. Punctuation normalisation — collapse multiple marks, replace em-dash
     with comma-pause, etc.
  3. Number-to-words expansion — "150 km/h" → "isang daan at limampung
     kilometro bawat oras" using language-specific numeral rules.
  4. Abbreviation expansion — common alert abbreviations (PAGASA signal
     levels, coastal names, agency codes) → full spoken form from a
     configurable expansion map.
  5. Phonetic respelling (optional) — map known difficult syllable clusters
     to phoneme-friendly spellings for the target TTS engine.
  6. Rate hint injection — wraps output in SSML speech-rate tags if the
     TTS engine supports SSML, using a per-language rate table (slower for
     elderly/emergency contexts, faster for confirmation readbacks).
  7. Segmentation — splits output at sentence boundaries for streaming TTS
     chunk delivery.

CAPABILITY LIFT (structural): low-resource TTS engines have limited G2P
(grapheme-to-phoneme) coverage and no number-expansion or abbreviation
models for regional Philippine languages. Raw model output fed directly
to MMS produces unintelligible number reads and mispronounced agency
names. This pre-processor closes that gap with deterministic rules.
lift_reason: no_addressable_source (no production G2P/numeral model for
the target languages); mechanism: sub_token (character-level normalisation
the model cannot do reliably).

| axis | value |
|---|---|
| industry | public_safety, government.regulatory, humanitarian, cross_industry |
| capability | format_conversion, extraction, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| license | Apache-2.0 |



