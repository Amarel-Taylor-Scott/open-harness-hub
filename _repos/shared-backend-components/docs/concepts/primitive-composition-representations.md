# How chains, groups, networks, and primitives-of-primitives are shown

> Owner question (2026-07-10): *"tell us in an MD file how chains of primitives, groups of primitives, or
> networks of primitives or primitives of primitives can be shown."*

Every composition concept in this repo is a **projection of one underlying graph**: primitives are nodes,
their **typed edges** (`input_edge → output_edge`) are the wiring, and each concept below is a different way of
reading that graph. Nothing here is a new data model bolted on — a chain, a group, a network, and a composite
are all *views* over the same primitive cards, each persisted as its own **candidate** record family
(`candidate=true, serves_truth=false`) with a `canonical_id`. This doc shows each representation, the record
that carries it, and how to see it (agent API · JSONL · ASCII · the interactive lattice).

The worked corpus throughout is the **corporate-records scraping pack**
(`scripts/corporate_records_scraping_primitive_pack.py`, 57 governed primitives) plus its deterministic
remixes. Modules: `primitive_groups_frameworks_and_remixers.py`, `primitive_networks_and_grid_search.py`,
`primitive_deployment_profiler.py`. Agent-API surface: `capability_agent_tool.py` (read-only, also on the
public trial key).

---

## 0 · The atom — a primitive and its edges

A primitive is a small verified unit of capability that **declares what it takes and what it returns**. The
edge names are the type system of reuse: you compose by reading names, not bodies.

```
┌─────────────────────────────────────────────┐
│ Officer dedupe clusterer            [cross_source]
│ OfficerRowBatch ──▶ OfficerDedupeClusterBatch │   ← input_edge → output_edge
│ blocking_keys: dedupe · cluster · officers    │
│ candidate · serves_truth=false                │   ← governance badge (always shown)
└─────────────────────────────────────────────┘
```

Everything below is built by matching `output_edge` of one card to `input_edge` of the next. That single rule
generates all four representations.

---

## 1 · CHAINS — an ordered route through exact edges

A **chain** is a linear composition: a sequence of primitives where each one's output edge exactly equals the
next one's input edge. It is compiled deterministically (a lookup, not a generation) by the **integrator**,
which reuses the one runtime composer (`primitive_runtime.compose_route`).

**Shown as** an `integrated_primitive_candidate` record (or an honest `integration_refusal_receipt` when no
exact route exists), and via the agent action `composition.integrate {start, goal}`.

```
ProxyStatementDocument
        │  DEF 14A officer & director extractor        (edge-aligned: OfficerDirectorRowBatch → OfficerRowBatch)
        ▼
   OfficerRowBatch
        │  Officer dedupe clusterer
        ▼
OfficerDedupeClusterBatch          ✓ route found · 2 exact steps · deterministic
```

The honesty rule is load-bearing: **independently-minted primitives rarely share exact edge names**, so a raw
composite request usually *refuses*. Chains become possible after **edge alignment** (§6) maps near-miss names
onto a shared canonical edge. That refusal-then-unlock is the whole reuse thesis in one motion.

---

## 2 · GROUPS — typed collections over the corpus

A **group** is a computed set of primitives sharing a property: the same family, the same pack, the same
consumed edge, or the same produced edge. Groups answer "what do I have that produces `X`?" — the question a
composer asks. They are **computed, never hand-listed** (add a card and it joins its groups automatically).

**Shown as** `primitive_group` records (one per key) carrying member ids + the group's edge signature, and via
`composition.groups {builder}`. Four builders ship: `by_family`, `by_pack`, `by_consumed_edge`,
`by_produced_edge`. `by_family` partitions the pack losslessly.

```
group: by_produced_edge = "OfficerRowBatch"          (3 members — a slot's worth of competing extractors)
  ├─ DEF 14A officer and director extractor           (edge-aligned)
  ├─ Companies House officers list adapter            (edge-aligned)
  ├─ 990 officer and compensation extractor           (edge-aligned)
  consumes: {ProxyStatementDocument, UkCompany…, Irs990…}   produces: {OfficerRowBatch}
```

A "produced-edge" group is exactly the pool that fills a **network slot** (§3) — groups and networks are two
readings of the same fan-in.

---

## 3 · NETWORKS — a step lattice of competing primitives, grid-searched

A **network** expresses a *task* as an ordered chain of **edge types**, where **each step is a slot** and each
slot holds *multiple interchangeable primitives* (a produced-edge group). The **grid** is the cartesian
product of the slots — every path is valid by construction because adjacent members share exact edges. Grid
search scores every path for efficiency and returns non-destructive rankings (winners + Pareto front; losers
kept as labeled fallbacks). Different scorers can crown different winners.

**Shown as** `primitive_network` + `network_path_candidate` + `network_grid_receipt` records, via
`network.list` / `network.grid_search`, and visually as the **interactive lattice** (columns = steps, rows =
competing primitives, the winning route drawn through the selected chip per scorer).

```
edgar_control_person_network        (the deep 5-step chain — discover → plan → fetch → extract → cluster)

 step A                 step B            step C           step D          step E
 EdgarFilingRefBatch    AccessionPlan     DocumentBundle   OfficerRowBatch DedupeCluster
 ┌───────────────┐      ┌────────────┐    ┌────────────┐   ┌────────────┐  ┌────────────┐
 │ daily index   │─┐    │ fetch-plan │    │ document   │   │ bundle     │  │ officer    │
 ├───────────────┤ │    │ builder    │    │ fetcher    │   │ officer    │  │ dedupe     │
 │ weekly index  │─┼───▶│ (bridge)   │──▶ │            │──▶│ extractor  │─▶│ clusterer  │
 ├───────────────┤ │    └────────────┘    └────────────┘   │ (bridge)   │  └────────────┘
 │ monthly index │─┤       1 option          1 option      └────────────┘     1 option
 ├───────────────┤ │                                          1 option
 │ full-text srch│─┘
 └───────────────┘
   slot A = 4            slot B = 1        slot C = 1       slot D = 1      slot E = 1
   grid = 4 × 1 × 1 × 1 × 1 = 4 candidate paths, each scored; winner highlighted per scorer
```

Where a slot has **no** producer, the network does not invent a member — it emits an honest
`empty_slots` coverage-gap receipt. That gap is a signal to mint a **bridge primitive** (which is exactly how
the 5-step chain above got its depth: two real bridges, not fabricated edges).

**Grid-search scorers** (a zoo; extend = one row): `proxy_context_tokens`, `blackbox_tokens`, `declared_cost`
are runnable 0-token proxies; `execution_efficiency` is a declared harness seam. "Most efficient" is therefore
*per scorer* and *receipted*, never a silent verdict.

---

## 4 · PRIMITIVES OF PRIMITIVES — composites (recursion)

The output of the integrator (§1) is itself a primitive card: an `integrated_primitive_candidate` has its own
`input_edge`, `output_edge`, `member_ids`, and `edge_path`. So a composite **is a primitive** — it can be a
member of a group, a slot in a network, or a step in a larger chain. Composition is **closed under itself**:
primitives compose into composites, and composites compose again.

```
composite: "Integrated pipeline: ProxyStatementDocument → OfficerDedupeClusterBatch (2 exact steps)"
   input_edge:  ProxyStatementDocument
   output_edge: OfficerDedupeClusterBatch
   member_ids:  [ prmx-… (edge-aligned DEF 14A extractor), cpc-… (officer clusterer) ]
   lineage:     { integrator: exact_edge_route, members: [...], deterministic: true }
        │
        └──▶ this whole thing can now be ONE node in a bigger network's slot
```

The lattice in §3 is the general case; a chain (§1) is a lattice where every slot has one member; a composite
is a chain frozen back into a single node. That is what "primitives of primitives" means here — **the same
record shape at every level of nesting**, so a diagram can zoom in or out without changing representation.

---

## 5 · FRAMEWORKS — stage scaffolds a network fills

A **framework** is a named, ordered set of *stages* (a template for a whole motion), where each stage selects
its members by a deterministic predicate. Instantiating a framework against the corpus fills each stage from
the matching primitives, with **honest coverage gaps** — an unfilled stage is listed, never invented.

**Shown as** `primitive_framework` + `primitive_framework_instance` records, via `composition.frameworks
{framework, scope_family}`.

```
governed_scraping_framework  →  instance for family "sec_edgar"
  policy_gate      ▓▓ filled (ToS/robots preflight)
  rate_budget      ▓▓ filled
  enumerate/search ▓▓ filled (index enumerators + full-text)
  fetch            ▓▓ filled (document fetcher)
  parse/extract    ▓▓ filled (XBRL, DEF 14A, 13F, Form D)
  normalize        ░░ gap for this family (uses the cross-source normalizer)
  provenance/cdc   ▓▓ filled (receipts + watermarks)
```

A framework is the *prescriptive* view (what the motion **should** contain); a network is the *executable*
view (the paths that actually chain). A framework instance's gaps become the network's bridge-primitive TODOs.

---

## 6 · REMIXES — lineage-carrying variants

A **remix** is a deterministic transform of a card into a variant that keeps a link to its parent. The
flagship transform, `edge_vocabulary_align`, is the **chainability lever**: it maps a near-miss edge name onto
a shared canonical one, which is what lets independently-minted primitives fill the same slot (§3) and chain
(§1). Others: `jurisdiction_exemplar_swap`, `cadence_swap`.

**Shown as** `remixed_primitive_candidate` records carrying `lineage: {parent_card_id, transform_id}`, via
`composition.remix`.

```
parent:  DEF 14A officer & director extractor   (… → OfficerDirectorRowBatch)
   │  transform: edge_vocabulary_align  (OfficerDirectorRowBatch → OfficerRowBatch)
   ▼
variant: DEF 14A officer & director extractor (edge-aligned)   (… → OfficerRowBatch)
         lineage: { parent_card_id: cpc-…, transform_id: edge_vocabulary_align, deterministic: true }
```

Because every variant records its parent and transform, the **lineage/remix graph** is itself queryable — you
can always trace a slot member back to the raw primitive it aligns.

---

## 7 · The DEPLOYMENT dimension — how heavy each is to run

Any primitive, path, or network also carries a **deployment profile** (`primitive_deployment_profiler.py`):
operation class → dependencies + runtime substrate + a resource envelope, and, given a use case, a decided
medium (K8s vs cloud function vs …) + sized vCPU/memory + a cost band. A network profile **critical-paths** the
steps (you provision the heaviest step) and unions the dependencies.

**Shown as** `primitive_deployment_profile` / `network_deployment_profile` records, via `deployment.estimate`
and `deployment.profile_network`.

```
edgar_control_person_network @ 5,000,000 records/day, daily freshness
  step A gate   → 1024 MB     step D parse  → 1024 MB
  step B fetch  → 1024 MB     step E dedupe → 8192 MB   ◀ critical path (the memory bottleneck)
  step C fetch  → 1024 MB
  pipeline medium: batch_job   ·   union deps: {httpx, lxml, datasketch, tenacity, numpy, …}
```

---

## The through-line

| Concept | Record family | Agent action | One-line shape |
|---|---|---|---|
| Primitive | (pack card) | `retrieval.get` | a node with typed edges |
| Chain | `integrated_primitive_candidate` | `composition.integrate` | a line: exact edge route |
| Group | `primitive_group` | `composition.groups` | a fan-in by shared edge/family |
| Network | `primitive_network` + receipts | `network.list` / `network.grid_search` | a lattice: slots × competitors |
| Composite | `integrated_primitive_candidate` | `composition.integrate` | a chain frozen into a node (recursion) |
| Framework | `primitive_framework_instance` | `composition.frameworks` | a staged scaffold with gaps |
| Remix | `remixed_primitive_candidate` | `composition.remix` | a variant + lineage to its parent |
| Deployment | `network_deployment_profile` | `deployment.profile_network` | a resource/medium envelope |

Because all seven are projections of the same edge graph, a single visual grammar renders them: **nodes are
primitives, arrows are typed edges, a column is a slot, a highlighted line is a chosen path, and a badge is
governance state.** The interactive lattice
(`scripts/primitive_networks_and_grid_search.py` data → the published artifact) is that grammar made literal;
this doc is its legend.

*Everything described here is a governed candidate (`serves_truth=false`); promotion is earned through review
and executed proofs, never claimed.*
