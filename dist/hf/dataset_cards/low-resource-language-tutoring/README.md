---
license: CC-BY-4.0
tags:
- education
- education.k12
- education.tutoring
- experimental
- gemma
- global-south
- low-resource-language
- marathi
- offline
- on-device
- open-harness-hub
- reasoning
- retrieval
- sparse-data
- structural-lift
- swahili
- translation
- tutoring
- twi
task_categories:
- text-retrieval
- translation
size_categories:
- n<1K
language:
- en
pretty_name: Low-resource-language tutoring scaffold (Marathi, Swahili, Twi — school
  subjects)
---

# Low-resource-language tutoring scaffold (Marathi, Swahili, Twi — school subjects)

<!-- Generated from OpenHubForAI manifest `knowledge-pack/low-resource-language-tutoring` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Knowledge Corpus scaffold for tutoring school subjects (mathematics,
science, basic literacy) in low-resource languages including Marathi,
Swahili, and Twi. Provides key concept glossaries, worked example
templates, and curriculum alignment notes for standard primary/secondary
curricula in Maharashtra (India), East Africa, and West Africa respectively.
Designed to run entirely on-device; no cloud dependency.

HONEST INGESTION CONTRACT:
- Coverage is partial and curriculum-approximate. This corpus MUST be
  presented to students as supplementary, not authoritative.
- Subject-matter experts for each language community should review and
  extend entries before production use.
- Entries that are uncertain are flagged with "coverage: partial".
- No proprietary curriculum content is included; all entries derive from
  public-domain syllabi and open educational resources.

CAPABILITY LIFT (structural): frontier models have sparse training data
for low-resource languages, especially in school-subject domains. Marathi
STEM vocabulary, Twi arithmetic terminology, and Swahili science glossaries
are not well represented in public LLM training corpora. This corpus
provides the vocabulary layer that a base model lacks — the gap is
structural because it cannot close by scaling the model without acquiring
the missing training data (sparse_data mechanism). The corpus is an
on-device retrieval source available when network is absent.
lift_reason: no_addressable_source (offline) + sparse_data mechanism.

**Industries**: education, education.k12, education.tutoring
**Capabilities**: retrieval, translation, reasoning
**Modalities**: text, structured
**Freshness**: stable
**Trust boundary**: local

## Content types (leaf vocabulary)

- `rag_doc`

## Files

| path | format | schema |
|---|---|---|
| `data/low-resource-language-tutoring.jsonl` | jsonl | — |

## Provenance

- **sources**: Maharashtra State Board of Secondary and Higher Secondary Education — public syllabus (open access), Kenya Institute of Curriculum Development — primary curriculum frameworks (open access), Ghana Education Service — national primary school curriculum (open access), Open educational resources in Marathi, Swahili, and Twi curated from Wikipedia, Wikibooks, and public-domain school texts
- **collected_through**: 2026-05-28
- **collected_by**: OpenHubForAI research agent (manual curation from public-domain syllabi)
- **anonymization**: none — all content is public-domain educational material; no PII

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/low-resource-language-tutoring.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{low-resource-language-tutoring_open_harness_hub,
  title  = {Low-resource-language tutoring scaffold (Marathi, Swahili, Twi — school subjects)},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/low-resource-language-tutoring},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/low-resource-language-tutoring`.
