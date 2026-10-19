---
license: CC-BY-4.0
tags:
- capability-lift
- compliance
- esoteric
- experimental
- finance
- ingestion-target
- knowledge-pack
- open-harness-hub
- rag_vector
- retrieval
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Mifid2 Mar Best Execution And Market Abuse
---

# Mifid2 Mar Best Execution And Market Abuse

<!-- Generated from Open Harness Hub manifest `knowledge-pack/mifid2-mar-best-execution-and-market-abuse` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: blur MiFID II RTS 27/28/22 and MAR insider-list/STOR/PDMR thresholds; cite repealed RTS Grounded in ESMA MiFID II/MiFIR RTS + MAR Reg 596/2014 (EUR-Lex) via rag_vector retrieval. Lift: dense frequently-amended field-level obligations conflated across regimes

**Industries**: finance, compliance
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
| `data/esoteric-packs/mifid2-mar-best-execution-and-market-abuse.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: ESMA MiFID II/MiFIR RTS + MAR Reg 596/2014 (EUR-Lex)
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/mifid2-mar-best-execution-and-market-abuse.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{mifid2-mar-best-execution-and-market-abuse_open_harness_hub,
  title  = {Mifid2 Mar Best Execution And Market Abuse},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/mifid2-mar-best-execution-and-market-abuse},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/mifid2-mar-best-execution-and-market-abuse`.
