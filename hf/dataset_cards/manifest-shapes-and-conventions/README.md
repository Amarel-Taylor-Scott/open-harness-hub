---
license: MIT
tags:
- ai
- conventions
- cross_industry
- experimental
- few-shot-grounding
- manifest-author
- meta
- open-harness-hub
- retrieval
- schemas
- software
- software.docs
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Open Harness Hub manifest shapes, schemas & conventions reference
---

# Open Harness Hub manifest shapes, schemas & conventions reference

<!-- Generated from Open Harness Hub manifest `knowledge-pack/manifest-shapes-and-conventions` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

In-catalog reference pack distilling the OHH manifest shapes for
use by `persona/manifest-author` and `harness/draft-manifest-
author` when generating draft manifests from external knowledge
trees.

Contents:
 - **Schema summaries**: one-page distillation of each of the 14
   component schemas under `schemas/*.schema.json` — required
   fields, optional fields, validation gotchas.
 - **Envelope conventions**: id format, slug rules, semver,
   license defaults, lifecycle progression, attribution.
 - **Vocabularies in-context**: industries (52+ top-level with
   sub-industries), capabilities (~25), modalities (7), leaf-
   types (40+), lifecycle (4), lifecycle-position (12+).
 - **Pattern library**: 20+ "canonical example" snippets — one
   well-formed harness, pipeline, rule-pack (each family), tool,
   rubric, etc. — to ground few-shot generation.
 - **Hard rules from AGENTS.md + SPEC.md §5**:
   · Pipeline never wires raw rule packs to a model.
   · Volatile facts go in tools/knowledge packs, not personas.
   · Every harness declares model_targets (even if `none`).
   · Privacy boundaries travel with the component.
   · Reproducibility is first-class.
   · Industry-specific concepts as leaf instances, not top-level.
 - **Curator-review etiquette**: drafts go to `catalog/_inbox/`;
   curator promotes to live `catalog/{type}/` after review.
 - **Anti-patterns to avoid**: slug-collision, attribution-
   stripping, vocabulary-explosion, missing-required-field,
   placeholder text ("TODO", "FIXME", "lorem ipsum") in shipped
   manifests.

Intended consumers:
 - `harness/draft-manifest-author` (in-context schema reference)
 - `persona/manifest-author` (system-prompt grounding)
 - Human contributors (browsable doc page)

This pack must be REGENERATED whenever schemas/ or vocabularies/
change. The CI workflow `validate.yml` should add a check that
this pack's version matches schemas/*.schema.json + vocabularies/
hashes (TODO; tracked in repo issues).

**Industries**: software, software.docs, ai, cross_industry
**Capabilities**: retrieval, verification
**Modalities**: text, structured
**Freshness**: volatile
**Trust boundary**: local

## Content types (leaf vocabulary)

- `rag_doc`
- `citation_edge`

## Files

| path | format | schema |
|---|---|---|
| `data/manifest-shapes/schema-summaries.jsonl` | jsonl | — |
| `data/manifest-shapes/envelope-conventions.jsonl` | jsonl | — |
| `data/manifest-shapes/vocabularies-distilled.jsonl` | jsonl | — |
| `data/manifest-shapes/canonical-examples.jsonl` | jsonl | — |
| `data/manifest-shapes/hard-rules-and-antipatterns.jsonl` | jsonl | — |

## Provenance

- **sources**: schemas/_common.schema.json, schemas/{harness,pipeline,rule-pack,knowledge-pack,logic-pack,tool,persona,adapter,rubric,dataset,processor,pattern,benchmark}.schema.json, vocabularies/{industries,capabilities,modalities,leaf-types,lifecycle-position}.yaml, AGENTS.md, taxonomy/SPEC.md (especially §5 hard rules, §16 processor taxonomy), catalog/* (existing 500+ validated manifests as patterns)
- **collected_through**: 2026-05-24

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/manifest-shapes-and-conventions.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{manifest-shapes-and-conventions_open_harness_hub,
  title  = {Open Harness Hub manifest shapes, schemas & conventions reference},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/manifest-shapes-and-conventions},
  version= {0.1.0},
  year   = {2026}
}
```

License: `MIT`. Hub component: `knowledge-pack/manifest-shapes-and-conventions`.
