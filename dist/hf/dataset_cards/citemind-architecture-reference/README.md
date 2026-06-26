---
license: CC-BY-4.0
tags:
- architecture
- beta
- citemind
- compliance
- concept-graph
- education
- local-first
- open-harness-hub
- privacy
- rag
- retrieval
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: CiteMind architecture reference (local-first PDF → research wiki + concept
  graph)
---

# CiteMind architecture reference (local-first PDF → research wiki + concept graph)

<!-- Generated from OpenHubForAI manifest `knowledge-pack/citemind-architecture-reference` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Architectural shape extracted from the CiteMind hackathon submission: Tauri 2 desktop + React 19/TypeScript + Rust backend + SQLite, OCR-aware page-chunked indexing, hybrid retrieval, Ollama/Gemma reasoning, cited answers, generated wiki pages + concept graph + study guides.

**Industries**: education, privacy, compliance
**Capabilities**: retrieval, verification
**Modalities**: text
**Freshness**: stable
**Trust boundary**: local

## Content types (leaf vocabulary)

- `rag_doc`

## Files

| path | format | schema |
|---|---|---|
| `data/citemind-pack/architecture.jsonl` | jsonl | — |

## Provenance

- **sources**: CiteMind submission writeup (Gemma 4 Good Hackathon, composite — direct upstream URL pending)
- **collected_through**: 2026-05-21
- **note**: Catalog port of CiteMind architectural shape. Awaiting upstream confirmation of repo URL + author attribution; marked beta with caveat.

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/citemind-architecture-reference.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{citemind-architecture-reference_open_harness_hub,
  title  = {CiteMind architecture reference (local-first PDF → research wiki + concept graph)},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/citemind-architecture-reference},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/citemind-architecture-reference`.
