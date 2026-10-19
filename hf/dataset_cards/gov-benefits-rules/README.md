---
license: CC-BY-4.0
tags:
- benefits
- beta
- compliance
- government
- government.benefits
- medicaid
- open-harness-hub
- retrieval
- snap
- ssi
- tanf
- ui
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Government benefits program rules (SNAP / Medicaid / UI / SSI)
---

# Government benefits program rules (SNAP / Medicaid / UI / SSI)

<!-- Generated from Open Harness Hub manifest `knowledge-pack/gov-benefits-rules` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite educational reference of the major US federal benefits
programs' eligibility rules: SNAP (7 CFR 273), Medicaid (42 CFR +
state plan), Unemployment Insurance (state UI manuals), SSI/SSDI
(20 CFR / POMS), TANF (45 CFR 260-265).

**Industries**: government, government.benefits, compliance
**Capabilities**: retrieval, verification
**Modalities**: text
**Freshness**: dated
**Trust boundary**: local

## Content types (leaf vocabulary)

- `rag_doc`

## Files

| path | format | schema |
|---|---|---|
| `data/gov-benefits-pack/program-rules.jsonl` | jsonl | — |

## Provenance

- **sources**: USDA FNS SNAP Policy Handbook (composite), CMS Medicaid State Plan templates (composite), SSA POMS / 20 CFR (composite), DOL UI Program Letters (composite)
- **collected_through**: 2026-04-30
- **note**: Composite educational extracts; state programs vary.

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/gov-benefits-rules.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{gov-benefits-rules_open_harness_hub,
  title  = {Government benefits program rules (SNAP / Medicaid / UI / SSI)},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/gov-benefits-rules},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/gov-benefits-rules`.
