# Schema extensibility — attribute over column (avoid fragile schemas)

**Rule:** a new *facet* of a component is an **attribute row**, not a new **column** on the envelope.
Schemas that grow a column per facet become fragile — every new facet is a migration, a backfill, and
a join that breaks old rows. Attribute-level (entity-attribute-value) storage adds facets with **zero
schema change**. This is a QOL + extensibility mandate, and it is already half-built — lean into it.

## The decision rule

When you want to attach a new piece of information to a component, pick in this order:

1. **Is it one of the handful of universal, load-bearing fields every component must have?**
   (`id`, `type`, `version`, `lifecycle`, `license`…) → it belongs in the **envelope** (`_common.schema.json`).
   These are deliberately few and closed. Adding here is rare and reviewed.

2. **Is it a typed, queryable measurement or facet that only *some* components have, and that we'll
   keep adding more of?** (token cost, hit rate, languages, latency class, a new ranking signal, a new
   risk score…) → it is a **`dimension-record`** (attribute row), never a new envelope column.
   `dimension-record.schema.json` is already EAV: `{dimension_id, name, subject_id, value, value_type,
   confidence, assignment_method, provenance}`. Adding a 40th dimension is **zero schema change**.

3. **Is it a label / tag / classification?** → a **`label-record`** (attribute row), same logic.

4. **Is it a kind/category that will keep growing?** (process kinds, capabilities, industries,
   modalities) → an **open vocabulary** (`type: string` + `examples` + a `vocabularies/*.yaml` list),
   **not** a closed `enum`. `process_kind` already does this right. Validate membership in CI against
   the vocabulary file, not in the schema enum — so adding a kind is a vocab-file edit, not a schema bump.

Only #1 touches the rigid schema. #2–#4 are migration-free by construction.

## Closed enum vs open vocabulary

Closed `enum` is correct **only** for a small, load-bearing, rarely-changing set that storage/routing
depends on:
- `componentType` (the 14 storage `type` keys) — closed for good reason: it's the partition key. ✅
- `lifecycle` (4 states), `trust_boundary`, `freshness`, `value_type` — small, stable state machines. ✅

Everything that is a *taxonomy that will grow* must be an **open vocabulary**:
- `process_kind`, `capability`, `industry`, `modality` — open. ✅ (keep them open; never freeze.)

**Smell test:** if you'd be tempted to ship a PR that *adds one value to an enum*, that enum should
have been an open vocabulary. A taxonomy that changes is data, not schema.

## additionalProperties policy

- **Envelope-level extension bags** (`data_protection`, `provenance`, `metadata`, `links`) →
  `additionalProperties: true`. New governed metadata must not require a schema bump. ✅
- **Fixed-shape value objects** (`author`, an input/output port) → `additionalProperties: false` is
  fine; their shape is stable and a typo there should fail loudly.
- **Default for new objects that represent an evolving concept:** prefer `true` (or omit), and pin the
  shape later once it stops moving. Fragility comes from freezing too early.

## QOL / extensibility checklist (apply to every schema or row-family change)

- **No magic values.** A constant lives once and is imported; counts are computed, never typed (see
  [[no-magic-values.md]]). Brand strings, dimensions, thresholds, type lists → one definition.
- **Attribute, not column,** for anything you'll add more of (the rule above).
- **Open vocabulary, not enum,** for any growing taxonomy; validate against `vocabularies/` in CI.
- **Content-hash stability.** A *formatting* change must not produce a new hash/version; a *content*
  change must. Hash the normalized body, not the wrapper (see CLAUDE.md ID/hash discipline).
- **Forward-compatible reads.** Consumers ignore unknown attributes rather than erroring — old code
  reads new rows. (Same principle as `OHH.product()` reading a config it didn't ship with.)
- **One source of truth across products.** Both Open Harness Hub and Context Layer read the *same*
  schemas, vocabularies, and dimension definitions — the two-product split
  ([[two-services-shared-infrastructure.md]]) shares the backend precisely so a facet added for one is
  instantly available to the other. A facet must never be a per-service column. See
  [[two-services-shared-infrastructure.md]] and [[context-enrichment-service.md]].

## Why this matters for the two-product split

Two products on one backend only stays cheap if adding a facet for Context Layer (say, a
`token_savings_ratio` dimension on a cache component) is an **attribute row both products read** — not
a column one product's loader knows about and the other's doesn't. Attribute-level storage *is* the
mechanism that keeps the shared backend genuinely shared. Column-level facets would silently fork it.
