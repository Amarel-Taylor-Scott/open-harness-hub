# Code templates — deterministic, zero-LLM-cost processors

A library of pre-baked Python implementations of common
transformations. Each template:

- Has a **strict JSON-Schema contract** (input + output) the pipeline
  runtime validates on every call.
- Is **deterministic and idempotent** — same input → same output,
  always. No model calls.
- Costs **zero tokens** — the LLM never sees the call.
- Has **100 %-coverage tests** at `tests/test_*.py`.
- Is **published as a `processor/*` manifest in the catalog**, so it
  shows up alongside model-wrapping processors with the same interface.

## Why this matters

Stop spending model tokens on jobs a 5-line regex can do.

| Task | Naive (LLM-based) | Code template |
|---|---|---|
| Extract emails from text | ~150 tokens prompt + 100 tokens response → $0.0005, 2 s latency, ~95 % accuracy | regex, **0 tokens, 0.2 ms**, **100 %** accuracy on RFC-5322-lite |
| Validate IBAN | ~200 tokens + 50 tokens → $0.0005, 2 s latency, ~99 % accuracy | mod-97 checksum, **0 tokens, 0.3 ms**, **100 %** accuracy |
| Cosine similarity over embeddings | LLM can't do it correctly | NumPy, **0 tokens, microseconds**, **exact** |
| SHA-256 audit hash | LLM gives a wrong hash | `hashlib`, **0 tokens, microseconds**, **exact** |

Pipelines should reach for code templates first; reserve LLM calls
for tasks that genuinely require generation, reasoning, or
classification beyond what a regex / parser can do.

## The 10 starter templates

| Slug | What it does |
|---|---|
| [`extract_email`](extract_email/) | Extract RFC-5322-lite email addresses from text |
| [`extract_url`](extract_url/) | Extract HTTP(S) URLs from text |
| [`extract_phone_e164`](extract_phone_e164/) | Extract / normalize phone numbers to E.164 |
| [`normalize_date`](normalize_date/) | Parse common date formats → ISO 8601 |
| [`validate_iban`](validate_iban/) | mod-97 IBAN checksum + country length validation |
| [`validate_luhn`](validate_luhn/) | Luhn-mod-10 checksum (credit cards, IMEI, NPI) |
| [`count_tokens_approx`](count_tokens_approx/) | Char/4 token-count approximation (no tiktoken dep) |
| [`fuzzy_jaro_winkler`](fuzzy_jaro_winkler/) | Jaro-Winkler similarity (sanctions screening) |
| [`cosine_similarity`](cosine_similarity/) | Vector cosine similarity (NumPy) |
| [`sha256_hash`](sha256_hash/) | SHA-256 hex digest (audit trail) |

Each directory contains:

```
extract_email/
├── extract_email.py        # the implementation (~30 lines)
├── input.schema.json       # JSON Schema for inputs
├── output.schema.json      # JSON Schema for outputs
├── README.md               # behaviour + edge cases + benchmarks
└── tests/
    └── test_extract_email.py
```

## Contract format

Every template's `input.schema.json` + `output.schema.json` defines
the runtime contract. The pipeline runner validates inputs before
calling and outputs after, so a misuse fails fast with a JSON-Schema
error message — never a silent miscomputation.

The corresponding `catalog/processors/.../<slug>.yaml` manifest
declares the same contract and points at the implementation:

```yaml
implementations:
  - kind: "callable"
    path: "code_templates.extract_email:run"
    language: "python"
```

## Adding a new template

```bash
# 1. Scaffold
mkdir -p code-templates/my_template/tests

# 2. Implement (extract_email/extract_email.py is the reference shape)

# 3. Write contracts
$EDITOR code-templates/my_template/input.schema.json
$EDITOR code-templates/my_template/output.schema.json

# 4. Add tests
$EDITOR code-templates/my_template/tests/test_my_template.py

# 5. Write the catalog manifest
python scripts/new.py processor my-template
$EDITOR catalog/processors/.../my-template.yaml
# (add: implementations: [{kind: callable, path: code_templates.my_template:run, language: python}])

# 6. Validate + run tests
python scripts/validate.py
python -m pytest code-templates/my_template/tests/
```

## Roadmap (next batches)

Common extractions: `extract_credit_card_pan`, `extract_isbn`,
`extract_doi`, `extract_uuid`, `extract_geo_coordinate`,
`extract_iso_country`, `extract_iso_currency`.

Common normalizations: `normalize_phone`, `normalize_currency`,
`normalize_address`, `normalize_whitespace`,
`normalize_unicode_nfkc`.

Common validations: `validate_email_with_dns_mx`,
`validate_us_ssn_format`, `validate_iso_8601_date`,
`validate_json_schema`, `validate_url_reachability`.

Common math/text utilities: `levenshtein_distance`, `bm25_score`,
`tokenize_words`, `sentence_split`, `markdown_to_plain_text`.

Common cryptographic primitives: `hmac_sha256`, `ed25519_verify`,
`x509_parse`, `c2pa_assertion_extract`.

## License

MIT for code, CC0 for the JSON Schemas. Drop these templates into any
project; no attribution required for the code (manifests retain
attribution via the catalog's `attribution` field).
