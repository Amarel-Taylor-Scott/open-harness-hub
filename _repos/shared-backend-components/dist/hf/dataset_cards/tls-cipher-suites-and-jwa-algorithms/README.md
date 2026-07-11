---
license: CC-BY-4.0
tags:
- capability-lift
- cyber
- esoteric
- exact_id
- experimental
- knowledge-pack
- open-harness-hub
- retrieval
- security
- seeded
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Tls Cipher Suites And Jwa Algorithms
---

# Tls Cipher Suites And Jwa Algorithms

<!-- Generated from OpenHubForAI manifest `knowledge-pack/tls-cipher-suites-and-jwa-algorithms` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: garble IANA TLS hex code points, AEAD/FS/deprecated status, JOSE/JWA ids Grounded in IANA TLS + JOSE registries + NIST SP 800-52r2/800-131A (free) via exact_id retrieval. Lift: exact registry-controlled code points + version-specific deprecation

**Industries**: security, cyber
**Capabilities**: retrieval, verification
**Modalities**: structured, text
**Freshness**: volatile
**Trust boundary**: external

## Content types (leaf vocabulary)

- `fact_table`
- `reference_doc`

## Files

| path | format | schema |
|---|---|---|
| `data/esoteric-packs/tls-cipher-suites-and-jwa-algorithms.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: IANA TLS + JOSE registries + NIST SP 800-52r2/800-131A (free)
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/tls-cipher-suites-and-jwa-algorithms.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{tls-cipher-suites-and-jwa-algorithms_open_harness_hub,
  title  = {Tls Cipher Suites And Jwa Algorithms},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/tls-cipher-suites-and-jwa-algorithms},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/tls-cipher-suites-and-jwa-algorithms`.
