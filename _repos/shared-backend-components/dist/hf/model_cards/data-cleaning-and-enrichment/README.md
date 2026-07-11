---
license: MIT
tags:
- address
- anonymization
- beta
- cross_industry
- data-cleaning
- dedup
- enrichment
- extraction
- finance
- format_conversion
- government
- healthcare
- insurance
- open-harness-hub
- phone
- retail
- structured
- text
- verification
library_name: open-harness-hub
pipeline_tag: token-classification
language:
- en
region:
- cross_industry
- retail
- finance
- healthcare
- government
- insurance
---

# Data cleaning + entity enrichment harness

<!-- Generated from OpenHubForAI manifest `harness/data-cleaning-and-enrichment` v0.1.0. Do not edit by hand; edit the source manifest and re-run `python scripts/emit/hf_model_card.py`. -->

## Model description

Cross-vertical harness that normalizes a raw customer / vendor /
applicant record: addresses → USPS standardized + geocoded;
phones → E.164; names → canonical with given/family split;
countries → ISO 3166 codes; dates → ISO 8601; emails →
deliverable check; entities → linked to OpenCorporates /
Companies House. Output is a clean, enrichable record ready for
downstream pipelines (ESG / AML / claims / benefits / etc.).

Strictly local-first; external tool calls (USPS / Google Geocode /
OpenCorporates) opt-in via env-var keys.

## Intended use

Use this harness as a **wrapping workflow around a model call**. It composes:

- `grep` layer
- `tools` layer

**Industries**: cross_industry, retail, finance, healthcare, government, insurance
**Capabilities**: format_conversion, verification, extraction, anonymization
**Modalities**: text, structured
**Trust boundary**: mixed

## How the harness runs

### raw record → standardized + enriched record

1. parse address → USPS standardized + libpostal fallback
2. normalize phones → E.164 (libphonenumber)
3. canonicalize names → given_name + family_name + middle + suffix + honorific
4. resolve countries → ISO 3166 alpha-2/alpha-3/numeric
5. parse dates → ISO 8601
6. validate USPS deliverable (if US + tool/usps-address-validator configured)
7. geocode (if tool/google-geocode configured)
8. entity-link to OpenCorporates (if vendor / B2B record + tool/opencorporates-lookup configured)
9. validate SWIFT BIC (if payment / bank record)
10. compute dedup key for entity resolution

## Privacy boundaries

- **raw_input**: stays local; external tool calls send sanitized fields only
- **derived_output**: may sync to hub only after anonymization gate
- **external_calls**: USPS / Google Geocode / OpenCorporates / SWIFT BIC — only when their env keys are set AND user opted in

## Compatible model targets (provider-neutral)

| id | transport | trust |
|---|---|---|
| `no_model` | `none` | local |
| `local_ollama_fallback` | `ollama` | local |

## Evaluation

Bench against a hub `benchmark/*` manifest with `python scripts/emit/lm_eval_harness.py` (emits lm-eval-harness YAML) or `python scripts/emit/promptfoo.py` (emits promptfoo config). Both reference the same `rubric/*` and `dataset/*` manifests.

## Risks & limitations

This is a workflow harness, not a trained model. Risk profile depends on the model wired in via the configured `model_target`. See the source manifest for `input_verification` and `output_verification` checks.

## Citation

```bibtex
@misc{data-cleaning-and-enrichment_open_harness_hub,
  title  = {Data cleaning + entity enrichment harness},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/harness/data-cleaning-and-enrichment},
  version= {0.1.0},
  year   = {2026}
}
```

License: `MIT`. Hub component: `harness/data-cleaning-and-enrichment`.
