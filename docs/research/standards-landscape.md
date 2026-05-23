# Standards landscape & alignment plan

> Draft research synthesis. Maps the Open Harness Hub taxonomy against
> existing standards (schema.org, W3C, AI-specific, eval, provenance,
> privacy) and recommends where to adopt, where to adapt, and where to
> invent.

**Status:** populated from four parallel research streams. Sections
below are filled in as each stream lands.

---

## 1. Why bother aligning with existing standards

A new catalog that invents every concept from scratch loses three
things:

1. **Discoverability.** Search engines, crawlers, and dataset catalogs
   look for `schema.org`/`Croissant`/`Model Card` markup. A YAML
   manifest with no `@context` is invisible to them.
2. **Interop.** Existing eval frameworks (lm-eval-harness, promptfoo,
   garak) and tool standards (OpenAI / Anthropic / MCP) have install
   bases. A hub artifact that emits to those formats slots into
   existing workflows.
3. **Trust.** Compliance and audit tools (MLflow, OpenLineage, C2PA,
   AIBOM) already exist. Aligning with them means a regulator,
   compliance officer, or downstream consumer can ingest hub manifests
   without writing a parser.

The hub does NOT need to BE these standards - it should **emit** them
where they fit and **consume** them where authoritative sources publish
them. The hub's own taxonomy stays purpose-built for composition; the
emitted standards are the lingua franca for the outside world.

---

## 2. Recommendation summary (filled in after research)

| Standard | Decision | Where it lands in the hub |
|---|---|---|
| _will be filled in by synthesis_ | | |

---

## 3. Schema.org / W3C / JSON-LD

_research stream 1 - to be populated_

---

## 4. AI-specific standards

_research stream 2 - to be populated_

---

## 5. Tool & eval standards

_research stream 3 - to be populated_

---

## 6. Provenance, lineage, privacy & license standards

_research stream 4 - to be populated_

---

## 7. The hub's emit-don't-be philosophy

Three patterns the hub will follow:

1. **Emit, don't replace.** A hub `dataset/` manifest stays in our
   YAML shape, but `scripts/emit/croissant.py` produces a Croissant
   JSON-LD record for the same dataset. Same for Model Cards (from
   `harness/`), MLflow run rows (from a `benchmark/` run), and MCP
   server config (from `tool/` + `processor/`).
2. **Map, don't merge.** The hub's `lifecycle_position` is novel; we
   keep it. But `license` already uses SPDX, `industry.healthcare.*`
   maps to schema.org's MedicalSpecialty where one exists, and so on.
3. **Cite, don't restate.** Where an authoritative external standard
   defines a vocabulary (HIPAA Safe Harbor identifiers, ILO indicators,
   FATF typologies, MITRE ATT&CK techniques, ICD-10 codes), the hub
   references the canonical source by URI rather than re-publishing it.

---

## 8. Concrete adoption plan (filled in after research)

Sorted by effort × impact.

_will be filled in by synthesis_

---

## 9. Future-proofing

A few principles the hub already follows that pay off when standards
shift:

1. **Open vocabularies** for `industry`, `capability`, `process_kind`,
   `pipeline_kind`, `leaf-types`. New values land via PR with no schema
   migration.
2. **`body` JSONB / opaque manifest** in the database mapping - even
   relational stores can absorb new fields without DDL changes.
3. **`attribution` envelope** present on every artifact lets the hub
   ingest from external sources (Kaggle, HF, arXiv) without losing
   provenance.
4. **Versioned manifests** (semver) with `superseded_by` /
   `deprecated_on` give a clean upgrade path when a standard changes.

---

*Document populated by `scripts/research_synthesize.py` when the four
research streams complete.*
