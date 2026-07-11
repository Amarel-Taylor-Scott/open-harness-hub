# The Open Primitive Format, expanded: unlimited flexibility with a bounded safety kernel

> Owner (2026-07-10): "more flexibility — not just edges with blocking keys, custom dimensions/numbers/
> categoricals/embeddings, multiple descriptions, fully unlimited infinity flexibility and improvability, but
> also prepackaged docker images, cloud functions, instance/technology-specific tools, common use cases,
> ratings, throughput, industries, and literally every other characteristic and datapoint in the world … think
> information theory, search theory, edges, onion layers, descriptions, technologies, layers, stacks, mixes,
> combinations … custom-tuned, self-tuning, new columns, new blocking keys, fuzzy edits, distance measures,
> heuristics based on the data at hand, because not all solutions work for every shape of data."

The design principle that makes "unlimited flexibility" real without chaos: **bound the small kernel where
safety requires it; leave everything else an open, extensible, self-tuning registry.** A primitive is not a
fixed-schema row — it is an *open subject* over five planes, four of them unbounded and one deliberately
bounded. Every module named below is shipped this session, self-test-gated + in `run_proofs`.

---

## The five planes

| Plane | Bounded? | Module | What it carries |
|---|---|---|---|
| **Identity** | small kernel | `capability_implementation_zoo` | capability family ⟂ immutable implementation zoo (never one row) |
| **Edges** (safety) | **bounded** | `compatibility_lattice` + `edge_contract_and_adapters` | directional weighted typed ports; **contracts authorize, names retrieve** |
| **Attributes** | **unbounded** | `open_attribute_model` | uncapped typed attributes on any subject kind |
| **Retrieval** | **unbounded** | `adaptive_retrieval_strategy` + the embedder/fusion/router zoos | multiple tunable embeddings, distance measures, blocking keys, self-tuned per data shape |
| **Evidence** | claim-scoped | `primitive_attestation` (+ the DAG, next) | digest-bound, claim/environment/time-scoped |

The one **bounded** plane is edges/compatibility — because a false edge runs wrong code. Everything else is
**open by design**: you cannot have too many attributes, descriptions, embeddings, or retrieval strategies; you
can only have an unsafe join. This is the whole trick — *unlimited where flexibility helps, bounded where safety
requires.*

---

## 1. Unlimited attributes — "every datapoint in the world" (`open_attribute_model`)

A subject is a `kind` (code_function · **docker_image** · **cloud_function** · service · **tool** · dataset ·
model · workflow · sql_udf · wasm_component · … extensible) plus an **uncapped bag of typed attributes**. Each
attribute declares a **value type** (number · integer · quantity+unit · **rating** · categorical · ordinal ·
**tag_set** · text · boolean · **embedding** · **reference** · temporal · distribution · url — 15 shipped, one
row to add more) so it stays queryable and rankable. Proven: one subject simultaneously carries latency
numbers, a 0–5 rating, **throughput** as a quantity, **industries** and use-cases as tag-sets, **multiple
descriptions**, **multiple embeddings**, and **references to a prepackaged Docker image, a cloud function, and a
tool** — 500 custom attributes attach with none dropped. An unknown type is accepted + flagged *opaque*
(open-world: never dropped or coerced); register it (one row) and it becomes queryable. So "custom dimensions,
custom numbers, custom categoricals, ratings, throughput, industries, prepackaged images/functions/tools" are
all *already representable*, and "every other datapoint in the world" is one registry row away.

**Technologies · stacks · mixes · combinations** live here + in the composition layer: a *technology* is a
`tag_set`/`categorical` attribute or a first-class `tool`/`service` subject; a *stack* is a **combination** =
a network of subjects (the `primitive_networks_and_grid_search` step-lattice); a *mix* is the **grid search**
over those combinations, scored non-destructively.

---

## 2. Onion layers — descriptions at every granularity

The repo's `primitive_onion` already models a subject as *layered views*: signature (≈50 tokens) → body →
semantic → usage. In the open model these are simply **multiple `text` + `embedding` attributes** at different
layers (`doc.description_plain`, `doc.description_technical`, `doc.description_semantic`, `embed.signature`,
`embed.body`), and **retrieval picks the layer** that matches the query grain. Unlimited descriptions, unlimited
embedding layers — each a row, each independently searchable. The onion is not a fixed 3-layer object; it is an
open stack of description/embedding attributes.

---

## 3. Information theory — which feature is worth indexing?

With unlimited attributes, the question becomes *which ones carry signal*. `adaptive_retrieval_strategy`
answers it with **normalized entropy**: a feature's discriminative power is its value-distribution entropy /
log(n) — 0 (all same, useless) to 1 (all distinct). Blocking keys are scored by `blocking_key_quality` =
entropy × (1 − singleton_fraction) with pair-reduction, so a **constant key** (0 entropy, no candidate
reduction) and an **all-singleton key** (no recall) both score low and a **moderate-bucket key wins** — the
information-theoretic sweet spot. So the format doesn't just *hold* infinite attributes; it *measures* which
ones are informative, per corpus.

---

## 4. Search theory — no single winner; self-tuned per data shape

"Not all solutions work for every shape of data" is executable. `adaptive_retrieval_strategy` carries a **zoo of
distance measures** (exact · levenshtein/**fuzzy** · jaccard · ngram · numeric · prefix) and a **self-tuner**
that races them on labeled pairs *drawn from the data at hand* and picks the champion by measured separation —
**numeric data selects a numeric distance, typo-prone short strings select edit distance, order-shuffled token
sets select Jaccard**, all by measurement, non-destructively (losers kept as fallbacks, re-raced when the data
shape changes). This composes with the existing retrieval zoo — `embedder_zoo` (races embedders),
`rank_fusion_zoo` (fuses rankers), `path_router_zoo` (routes per query class), `graph_autotune` (self-tunes the
retrieval graph). **Multiple tunable embeddings, multiple search systems, multiple distances, learned
fusion** — all zoos, all extensible, all chosen by measurement, none hardcoded to one winner.

---

## 5. Edges — the one bounded plane (names retrieve, contracts authorize)

Everything above is retrieval/description flexibility, which is *allowed* to be fuzzy — a wrong candidate is
inspected, not executed. The **edge plane is bounded** because it decides execution: `compatibility_lattice`
grades a join and only IDENTICAL / FAMILY_COMPATIBLE / SAFE_STRUCTURAL / VERIFIED_ADAPTER authorize;
`edge_contract_and_adapters` decides it over real structure (width subtyping, units, classified adapters); the
`compatibility_benchmark` proves the safety invariant (0 false auto-authorizes). So the format can carry
infinite fuzzy signal *and* a crisp safety verdict — the fuzzy signal feeds retrieval, the crisp verdict feeds
execution, and the two never cross.

---

## The extensibility guarantee (every axis is a registry row)

"Fully unlimited infinity flexibility and improvability" is concrete: **every** axis of the format is an
extensible registry where adding one is a single row and existing consumers are unaffected —

| Axis | Registry | Add-one-row |
|---|---|---|
| attribute value type | `open_attribute_model.ATTRIBUTE_TYPES` | `register_attribute_type` |
| subject kind (docker/cloud-fn/tool/…) | `SUBJECT_KINDS` | `register_subject_kind` |
| attribute filter | `open_attribute_model.FILTERS` | `register_filter` |
| distance measure / fuzzy edit | `adaptive_retrieval_strategy.DISTANCE_MEASURES` | `register_distance_measure` |
| blocking key | `BLOCKING_KEYS` | `register_blocking_key` |
| embedding model / search system | OPF `embeddings[]` + `search_systems[]` | a descriptor row |
| query method (Teleon/extension) | `open_primitive_format.QUERY_METHODS` | `register_query_method` |
| compatibility grade | `compatibility_lattice.GRADES` | a grade + authorization row |
| adapter operator | `edge_contract_and_adapters._OPS` | one op row |
| network / group / framework / remix | the composition zoos | one table row each |

No migration, no schema freeze on the open planes, no single hardcoded winner. The format *improves* by
measurement (self-tuned distances, entropy-ranked features, raced embedders, Pareto-ranked implementations) and
*grows* by rows.

---

## The unifying principle

> OPF is a **small owned kernel** — identity, directional edges, evidence, admission — surrounded by
> **unlimited open, self-tuning projections**: attributes, descriptions, embeddings, retrieval strategies,
> subject kinds. It is **bounded exactly where safety requires it** (an edge authorizes only through a
> contract) and **unbounded everywhere flexibility helps** (you can never carry too many attributes,
> descriptions, embeddings, or distance measures — only an unsafe join). That is how you get "every datapoint
> in the world" and "infinite improvability" without giving up the invocation-safety that registries lack.

*Grounded in this session's shipped modules (all self-test + run_proofs green); the retrieval-zoo composition
(embedder/fusion/router/autotune) is reused, not rebuilt.*
