---
license: CC-BY-SA-4.0
tags:
- blp
- cross_industry
- education
- experimental
- media
- media.editorial
- media.factcheck
- mos
- npov
- open-harness-hub
- policy
- retrieval
- rs
- verifiability
- verification
- wikipedia
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Wikipedia content-policy reference pack (NPOV / V / RS / OR / BLP / MOS)
---

# Wikipedia content-policy reference pack (NPOV / V / RS / OR / BLP / MOS)

<!-- Generated from Open Harness Hub manifest `knowledge-pack/wikipedia-quality-guidelines` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Reference pack of distilled extracts from the core content policies
of English Wikipedia. Composite educational text — not the
authoritative policy. Always check the current policy at
en.wikipedia.org for the live version.

**Pillar policies (the "three core content policies", non-
negotiable):**
 - WP:NPOV — Neutral Point of View. Articles must present views
   fairly, proportionately, and without editorial bias. Tone
   neutral, attribution explicit, no editorial voice. Includes WP:
   YESPOV, WP:DUE (due weight), WP:STRUCTURE (avoid coatrack),
   WP:LABEL (contentious labels), WP:PEACOCK, WP:WEASEL.
 - WP:V — Verifiability. The threshold for inclusion is
   verifiability, not truth. Material likely to be challenged
   needs inline citation. Includes WP:CHALLENGE, WP:BURDEN,
   WP:CITELEAD (lead claims also need sources if challengeable).
 - WP:NOR — No Original Research. Articles must not contain
   analysis or synthesis of published material not directly
   attributable to a reliable source. Includes WP:SYNTH (combining
   sources to reach a conclusion neither states), WP:PRIMARY
   (primary sources only for descriptive claims, not
   interpretation).

**Sourcing policies:**
 - WP:RS — Reliable Sources. Source tiers:
   · Peer-reviewed academic journals (highest, varies by field)
   · Mainstream news organizations + academic books
   · National news + government statistics + textbooks
   · Trade press + niche outlets
   · Press releases + self-published (lowest, limited use)
 - WP:RSP — Perennial Sources list (community consensus on
   specific publishers).
 - WP:MEDRS — Higher bar for medical/health claims
   (peer-reviewed secondary sources required).
 - WP:RSPRIMARY — primary sources for descriptive claims only.
 - WP:SELFPUB — self-published acceptable for content about the
   publisher themselves with limits.

**Operational policies:**
 - WP:BLP — Biographies of Living Persons. Conservative editorial
   standard; contentious material removed on sight if poorly
   sourced.
 - WP:NOT — What Wikipedia Is Not. Not a dictionary, not a
   directory, not a soapbox, not a news service, not an
   advertising venue.
 - WP:NOTABILITY — Subject covered in significant detail in
   independent reliable secondary sources.
 - WP:PROMO — Promotional / advocacy content forbidden.
 - WP:COI — Conflict of Interest disclosure required.

**Style policies:**
 - WP:MOS — Manual of Style. Lead section structure, section
   headings, dates, units, units of measure (SI primary, imperial
   parenthetical for US-focused articles).
 - WP:LEAD — Lead should summarize the article in 1-4 paragraphs.
 - WP:CITESTYLE — Internal consistency (CS1 or CS2, not both).

**Review processes:**
 - GA (Good Article) criteria.
 - FA (Featured Article) criteria.
 - Peer review.
 - New page patrol (NPP) checklist.
 - AfC (Articles for Creation) reviewer guide.

Note on non-English Wikipedias: policies vary. German Wikipedia
has different notability thresholds; French Wikipedia treats
primary sources more permissively; Chinese Wikipedia has separate
source-tier guidance. This pack covers en.wikipedia.org only.

**Industries**: media, media.editorial, media.factcheck, education, cross_industry
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
| `data/wikipedia-pack/pillar-policies.jsonl` | jsonl | — |
| `data/wikipedia-pack/sourcing-policies.jsonl` | jsonl | — |
| `data/wikipedia-pack/operational-policies.jsonl` | jsonl | — |
| `data/wikipedia-pack/style-policies.jsonl` | jsonl | — |
| `data/wikipedia-pack/review-process-criteria.jsonl` | jsonl | — |

## Provenance

- **sources**: https://en.wikipedia.org/wiki/Wikipedia:Neutral_point_of_view, https://en.wikipedia.org/wiki/Wikipedia:Verifiability, https://en.wikipedia.org/wiki/Wikipedia:No_original_research, https://en.wikipedia.org/wiki/Wikipedia:Reliable_sources, https://en.wikipedia.org/wiki/Wikipedia:Biographies_of_living_persons, https://en.wikipedia.org/wiki/Wikipedia:Manual_of_Style, https://en.wikipedia.org/wiki/Wikipedia:Good_article_criteria, https://en.wikipedia.org/wiki/Wikipedia:Featured_article_criteria
- **collected_through**: 2026-05-15

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/wikipedia-quality-guidelines.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{wikipedia-quality-guidelines_open_harness_hub,
  title  = {Wikipedia content-policy reference pack (NPOV / V / RS / OR / BLP / MOS)},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/wikipedia-quality-guidelines},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-SA-4.0`. Hub component: `knowledge-pack/wikipedia-quality-guidelines`.
