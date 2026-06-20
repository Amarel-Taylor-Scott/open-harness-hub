---
license: CC-BY-4.0
tags:
- canons
- chevron
- cross_industry
- drafting
- experimental
- government
- government.regulatory
- law
- legal
- legal.compliance
- loper-bright
- open-harness-hub
- reasoning
- retrieval
- statutory-interpretation
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Legal interpretation canons + statutory-drafting reference
---

# Legal interpretation canons + statutory-drafting reference

<!-- Generated from Open Harness Hub manifest `knowledge-pack/legal-interpretation-canons` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Reference pack of (composite, educational) extracts covering:

**Substantive canons of statutory construction:**
 - Textual canons: ordinary meaning, technical meaning, ejusdem
   generis, expressio unius est exclusio alterius, noscitur a
   sociis, rule against surplusage, consistent-usage canon,
   last-antecedent rule, series-qualifier canon, "and/or" usage.
 - Contextual canons: in pari materia, whole-text canon,
   harmonious-reading canon, presumption against ineffectiveness.
 - Substantive canons: constitutional avoidance, rule of lenity
   (criminal statutes), Indian-law canon (favor tribes), remedial-
   statute canon (read broadly), derogation-of-common-law canon
   (read narrowly), federalism canon, anti-extraterritoriality
   presumption, major-questions doctrine (post-WV v EPA 2022).
 - Reference canons: legislative-history use (post-Bostock and
   post-Pepper-v-Hart for US/UK), absurdity doctrine, scrivener's
   error doctrine.

**Administrative-law interpretive shifts:**
 - Chevron (1984) — overruled by Loper Bright Enterprises v
   Raimondo (2024). Federal agency interpretations no longer get
   judicial deference.
 - Auer / Kisor — agency self-interpretation of regulations still
   gets limited deference (Kisor v Wilkie 2019 narrowed it).
 - Skidmore (1944) — non-binding "power to persuade" deference,
   still applies post-Loper-Bright.
 - Major-questions doctrine (West Virginia v EPA, Biden v Nebraska)
   — agency claims of "extraordinary" power need explicit
   Congressional authorization.

**Drafting-failure taxonomy:**
 - Undefined operative terms.
 - Definitional circularity.
 - Cross-reference breakage.
 - Effective-date / retroactivity gaps.
 - Severability omissions.
 - Modal verb (shall/may/must/will) inconsistency.
 - Scope/operative-section mismatch.
 - Open enumerations without principled catch-all.

**Jurisdiction-specific notes:**
 - US federal: Scalia & Garner *Reading Law* (2012) catalog.
 - US state: Sutherland Statutes & Statutory Construction
   (7th ed.).
 - UK: Pepper v Hart (1992) admits Hansard for ambiguous statutes.
 - EU: ECJ teleological + literal + contextual + historical
   reading (Case 283/81 CILFIT).
 - Civil law (Louisiana, Quebec, France, Germany): code-first
   interpretation, distinct canon set.

Composite educational extracts; NOT legal advice and NOT a
substitute for jurisdiction-specific research.

**Industries**: legal, legal.compliance, government, government.regulatory, cross_industry
**Capabilities**: retrieval, verification, reasoning
**Modalities**: text
**Freshness**: dated
**Trust boundary**: local

## Content types (leaf vocabulary)

- `rag_doc`
- `citation_edge`

## Files

| path | format | schema |
|---|---|---|
| `data/law-pack/canons-of-construction.jsonl` | jsonl | — |
| `data/law-pack/admin-law-deference-shifts.jsonl` | jsonl | — |
| `data/law-pack/drafting-failure-taxonomy.jsonl` | jsonl | — |
| `data/law-pack/jurisdiction-canons.jsonl` | jsonl | — |

## Provenance

- **sources**: Scalia & Garner, Reading Law (2012) — canon list & framing, Sutherland Statutes & Statutory Construction (7th ed.), Loper Bright Enterprises v Raimondo, 603 US ___ (2024), West Virginia v EPA, 597 US 697 (2022), Pepper v Hart [1993] AC 593 (UK), Case 283/81 CILFIT (ECJ), Mertens, Statutory Drafting (Council on Drafting reference)
- **collected_through**: 2026-05-15

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/legal-interpretation-canons.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{legal-interpretation-canons_open_harness_hub,
  title  = {Legal interpretation canons + statutory-drafting reference},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/legal-interpretation-canons},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/legal-interpretation-canons`.
