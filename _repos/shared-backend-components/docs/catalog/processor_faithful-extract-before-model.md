# Faithful extract before model (deterministic text extraction — anti-hallucination pre-pass)

*processor* · `processor/faithful-extract-before-model` · v0.1.0 · stable

Pre-LLM processor that extracts all machine-readable fields from a
structured input (weather bulletin, government advisory, tabular data,
form) using deterministic parsers BEFORE passing anything to the language
model. The extracted fields are injected into the prompt as a structured
```extracted_facts block that the model is instructed to use verbatim.
The model is only invoked for tasks it is structurally better at than a
deterministic parser — e.g. chart description, prose generation from
structured facts — not for re-reading numbers or codes already available
in the text.

Implements the WeatherSpeak PH design principle: "extract first, model
only for what it cannot read" (e.g. typhoon track chart images require
VLM description; wind speed numbers in the bulletin text do not).

Extraction strategies (configurable per input_type):
  - regex_field_map:   extract named fields by regex pattern (e.g.
                       wind_speed: r"maximum winds of (\d+) km/h")
  - table_parse:       CSV/HTML table → JSON rows
  - xml_xpath:         CAP (Common Alerting Protocol) XML → alert fields
  - json_schema_cast:  coerce a partially-structured JSON to a target schema

Output: a prompt_block string suitable for direct injection into the
system or user message of the next pipeline step.

CAPABILITY LIFT (structural): language models hallucinate numeric values,
units, and place names when asked to extract them from mixed-format inputs.
The probability of hallucination increases with input length and numerical
density — precisely the characteristics of official weather bulletins and
government alerts. A deterministic extractor has zero hallucination rate
for machine-readable fields. This is a structural gap: it does not close
with model scale for sub-token arithmetic and regex-level extraction.
lift_reason: deterministic_guarantee; mechanism: sub_token.

| axis | value |
|---|---|
| industry | public_safety, government.regulatory, cross_industry |
| capability | extraction, verification, format_conversion |
| modality | text, structured |
| lifecycle | stable |
| trust_boundary | local |
| license | Apache-2.0 |



