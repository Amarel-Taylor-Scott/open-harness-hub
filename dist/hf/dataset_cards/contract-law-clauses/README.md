---
license: CC-BY-4.0
tags:
- beta
- clause-library
- contract
- legal
- legal.compliance
- legal.contract
- open-harness-hub
- playbook
- redline
- retrieval
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Commercial contract clause library (composite educational)
---

# Commercial contract clause library (composite educational)

<!-- Generated from Open Harness Hub manifest `knowledge-pack/contract-law-clauses` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite, educational reference of common commercial contract
clauses with: standard market language, common red-flag variants,
why each red flag matters, and a suggested redline. Covers the
10 highest-leverage clause families:

 1. Indemnification + limitation of liability (caps, carve-outs,
    mutual vs unilateral)
 2. IP assignment + pre-existing IP carve-outs + license-back
 3. Confidentiality + residual-knowledge clause
 4. Termination (for-cause, for-convenience, change-of-control)
 5. Data-processing addendum + sub-processor consent + audit
    rights
 6. Anti-bribery + sanctions + export-control compliance
 7. Warranties + disclaimers
 8. Payment terms + late-payment interest
 9. Governing law + jurisdiction + arbitration (seat, rules,
    carve-outs)
10. Force majeure (post-COVID standard scope)

Composite educational extracts; clause review requires the lead
company's playbook + jurisdiction-specific counsel.

**Industries**: legal, legal.contract, legal.compliance
**Capabilities**: retrieval, verification
**Modalities**: text
**Freshness**: dated
**Trust boundary**: local

## Content types (leaf vocabulary)

- `rag_doc`
- `citation_edge`

## Files

| path | format | schema |
|---|---|---|
| `data/contract-pack/clauses.jsonl` | jsonl | — |

## Provenance

- **sources**: Composite of common commercial-contract patterns (NDA / MSA / SOW / DPA), GDPR Art. 28 sub-processor requirements, UK Bribery Act 2010 §7, US FCPA
- **collected_through**: 2026-04-30
- **note**: Composite educational extracts; not legal advice.

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/contract-law-clauses.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{contract-law-clauses_open_harness_hub,
  title  = {Commercial contract clause library (composite educational)},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/contract-law-clauses},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub artifact: `knowledge-pack/contract-law-clauses`.
