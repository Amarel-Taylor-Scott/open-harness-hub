---
license: CC-BY-4.0
tags:
- capability-lift
- compliance
- esoteric
- exact_id
- experimental
- government
- ingestion-target
- knowledge-pack
- manufacturing
- open-harness-hub
- retrieval
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Cpu Instruction Set Opcode Reference
---

# Cpu Instruction Set Opcode Reference

<!-- Generated from OpenHubForAI manifest `knowledge-pack/cpu-instruction-set-opcode-reference` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: hallucinate opcode encodings, operands, ISA extension membership, latencies Grounded in RISC-V ISA spec (CC-BY) + Arm/Intel public refs via exact_id retrieval. Lift: bit-level encodings + extension membership exact and verifiable

**Industries**: manufacturing, compliance, government
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
| `data/esoteric-packs/cpu-instruction-set-opcode-reference.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: RISC-V ISA spec (CC-BY) + Arm/Intel public refs
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/cpu-instruction-set-opcode-reference.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{cpu-instruction-set-opcode-reference_open_harness_hub,
  title  = {Cpu Instruction Set Opcode Reference},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/cpu-instruction-set-opcode-reference},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/cpu-instruction-set-opcode-reference`.
