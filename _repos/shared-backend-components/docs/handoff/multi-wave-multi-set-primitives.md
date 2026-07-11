# Multi-Wave and Multi-Set Primitives — Formal Definition

> **Status.** Concept formalization (owner concepts, 2026-07-03). Every row this doc describes is
> `candidate=true` / `serves_truth=false` until a promotion gate says otherwise — formalizing a shape never
> promotes truth. **Number discipline:** every count in this doc is cited by the *manifest / receipt / report
> path that computes it*; no count is typed into this prose (the README-drift bug is the thing we are avoiding).
>
> **Precedence.** `docs/BIBLE.md` wins on vision/laws · `docs/OPERATIONS-BIBLE.md` wins on current state +
> operations · `docs/handoff/primitive-generation-verification-and-upload-manual.md` (the *generation manual*)
> wins on the exact generation→verify→bridge commands. This file adds two orthogonal composition concepts on top
> of that pipeline; where it disagrees with the OPERATIONS-BIBLE on state, the OPERATIONS-BIBLE wins.

These are two *independent* axes of the same primitive substrate:

- **MULTI-WAVE** is a **vertical** relation — the *same capability* seen at different **decomposition depths**,
  produced across successive generation waves and linked into a lineage tree.
- **MULTI-SET** is a **horizontal** relation — *one* authored primitive **reused across many families/sets**,
  linked by a membership index so the same helper is never regenerated per family.

A single primitive can be both: authored once (multi-set), and itself the parent of a wave-2 expansion
(multi-wave). The two relations never collapse into one field — depth is `wave` + `parent_primitive_id`;
breadth is the membership index.

---

## 1. MULTI-WAVE primitive (depth across generation waves)

### 1.1 Definition

A **multi-wave primitive** is a capability that exists at multiple **decomposition LEVELS**, each level minted by a
later generation wave over the prior wave's output:

| wave | what it emits | edge visibility | example role |
| --- | --- | --- | --- |
| **Wave 1 — breadth** | the family **GROUP card** (`kind: primitive_group`) | ONE visible edge (`input_edge → output_edge` for the whole family) | "adverse-media KYC screening" as one composable box |
| **Wave 2 — depth** | the group's **MEMBER primitives** (`kind: primitive`) | each member has its own edge; the union of member edges refines the group edge | "name normalization", "sanctions-list match", "media sentiment stance" |
| **Wave 3 — sub-depth** | the **sub-primitives / mutators / receipts** the members *imply* | edges internal to a member; mutators and proof receipts a member requires | "unicode fold mutator", "match-threshold receipt", "held-out negative case" |

The unit of "a primitive" at each wave is exactly the verifier row schema in the generation manual §1
(`kind ∈ {primitive, primitive_group}` only — family strings live in `primitive_kind`, never in `kind`). A
multi-wave primitive is therefore not a new schema; it is **the same row schema instantiated at three depths and
threaded by lineage fields**.

### 1.2 Lineage fields (how a wave references the prior)

Every non-root wave row carries a lineage triple, added as METADATA (never in the id/slug — version and lineage
live in fields, per the No-Magic-Values / deterministic-naming law):

```jsonc
{
  "primitive_id": "<canonical-id — sha suffix, NO wave/version in the string>",
  "kind": "primitive",                    // or "primitive_group" for a wave-1 root
  "wave": 2,                              // 1 = group card, 2 = member, 3 = sub/mutator/receipt
  "parent_primitive_id": "<wave-1 group card's primitive_id>",
  "root_group_id": "<the wave-1 group card at the top of this tree>",
  "decomposition_reason": "member_of_family | implied_mutator | implied_receipt | sub_edge",
  "candidate": true,
  "serves_truth": false
}
```

- **Reference direction is child → parent only.** A wave-N row points UP at its `parent_primitive_id`
  (wave N−1) and at the tree root `root_group_id` (always the wave-1 group card). The parent is never rewritten
  to enumerate its children — children are discovered by *querying the index for `parent_primitive_id == X`*, so a
  wave can be extended without touching already-verified parent rows (ADD-ONLY holds at the data layer too).
- **The tree is the lineage.** `(root_group_id, parent_primitive_id, wave)` reconstructs the full
  decomposition tree by pointer-walk; no wave stores a materialized child list that could drift.

### 1.3 Depth is BOUNDED

Unbounded decomposition is the failure mode (a mutator of a mutator of a receipt is noise, not capability). Depth
is bounded three ways, all deterministic:

1. **Hard cap `wave ≤ 3`.** Wave 3 (sub-primitives / mutators / receipts) is the leaf tier. Anything a wave-3 row
   would imply is expressed as a *mutator field on the wave-3 row*, not a wave-4 row.
2. **Saturation gate (the real stop signal).** A wave only spawns the next wave while it is still producing NEW
   edges. Rising duplicate rate in a lane is the saturation signal (OPERATIONS-BIBLE §5; monitored by
   `scripts/track_primitive_saturation_and_savings.py`). When a wave's dup rate crosses the lane threshold, the
   decomposition **sprouts elsewhere or moves on** — it does not descend further into a saturated family.
3. **Lift bar per wave.** A child wave is only admitted if it *lifts* over collapsing the child back into the
   parent (two-axis admission: `pipeline_score − bare_model_score > 0` AND structural durability;
   `scripts/eval/reason_codes.py` is the single source of the reason→durability taxonomy). A wave-3 mutator that
   the model would infer for free from the wave-2 member does not clear the bar and is written to negative memory,
   not the registry.

### 1.4 Each wave VERIFIES and BRIDGES independently (partial waves are usable)

This is the load-bearing property: **a wave is shippable the moment it verifies, without waiting for deeper
waves.** Each wave runs the full generation-manual pipeline on its own output:

```text
wave-N shards
  -> C. one-shot VERIFY   scripts/run_primitive_verification_loop.py --source-root <wave-N dir> --out-dir <label> --max-ticks 1
  -> D. registry BRIDGE   scripts/load_verified_candidates_into_registry.py --write
  -> E. report            scripts/report_multilane_primitive_generation.py --date-prefix <day> --write
```

Consequences:

- **Wave 1 alone is a product.** The verified GROUP cards are searchable (one coarse edge per family) even if
  wave 2 never runs. Callers compose at family granularity today.
- **Wave 2 refines in place.** When members verify and bridge, search resolves to the finer member edges; the
  group card stays valid as the coarse entry point (`parent_primitive_id` links the two — no rewrite).
- **A dead/partial wave never blocks the tree.** Fable wave agents die on session limits (OPERATIONS-BIBLE §5,
  §11); the completed shards of a wave are already verified + bridged, and the wave resumes from cache
  (`Workflow resumeFromRunId`). Missing children are simply "not yet expanded", detectable as
  `root_group_id` trees with no `wave: 2` rows.
- **The bridge is what makes each wave usable.** A verified row sitting in
  `data/dev-intel/primitive_factory/verified_candidates/<label>/` is invisible to the product until the bridge
  loads it (generation manual §4). "Verified" ≠ "usable"; the per-wave bridge closes that gap.

### 1.5 Where a wave's counts live (cite, never type)

- Per-wave verified count → the `total_verified` field of that day's row in
  `data/dev-intel/primitive_factory/multilane_generation_receipts.jsonl`, rendered in
  `data/dev-intel/primitive_factory/multilane_generation_report_<date>.md`.
- Per-label wave output → `data/dev-intel/primitive_factory/verified_candidates/<label>/manifest.json`.
- Fable wave labels + their verified counts (uc01…uc0N) → OPERATIONS-BIBLE §5 ("Fable ultracode waves"), which
  itself cites the receipts above.

---

## 2. MULTI-SET primitive (breadth: author once, belong to many families)

### 2.1 Definition

A **multi-set primitive** is a primitive **authored ONCE** that **belongs to MANY sets/families**. The canonical
example is a cross-cutting helper — "unicode fold", "normalize date to ISO-8601", "sha256 content hash",
"deduplicate near-identical strings" — that a KYC family, a provider-directory family, and a cost-anomaly family
all need. The wrong outcome (the reinvention bug) is three families each generating their own copy. The
multi-set relation forbids that: the helper is one row, **referenced** by every family that needs it.

### 2.2 The author-once / reference-many rule

- The primitive is authored **once** as a normal verifier row (generation manual §1). Its `primitive_id` is
  minted deterministically (`{prefix}-{sha256[:16]}` over canonical bytes; `src.teleon.experiments.ids`) so the
  *same* helper authored from the *same* canonical bytes yields the *same* id — re-authoring is idempotent, not a
  duplicate.
- Family membership is expressed **outside** the primitive, in the membership index (§2.3). A primitive does not
  list its families in its own row (that list would drift as new families adopt it); families are discovered by
  querying the index for `primitive_id == X`. This mirrors the multi-wave rule: relations point *into* an index,
  never materialized back onto the referenced row.
- **Reference, do not copy.** A family "contains" a multi-set primitive by holding a membership *edge*, not a
  second copy of the row. One authored row, N membership edges.

### 2.3 The membership index

**Location (spec):** `catalog/knowledge-packs/data/multi-set-membership-index/` — a knowledge-pack data
directory alongside the other 300 packs under `catalog/knowledge-packs/data/`. It holds one JSONL of membership
edges plus a manifest that computes the counts. (This doc defines the shape; the directory is populated by the
pipeline in §3, not by this doc.)

**Edge record shape** (`memberships.jsonl`, one edge per line):

```jsonc
{
  "record_type": "multi_set_membership_edge",
  "primitive_id": "<the author-once primitive>",
  "set_id": "<the family / set it belongs to, e.g. adverse-media-kyc>",
  "role_in_set": "core | helper | mutator | receipt",   // why this set needs it
  "authored_wave": 2,                                    // the wave the primitive was authored at (§1)
  "candidate": true,
  "serves_truth": false
}
```

**Manifest** (`memberships.manifest.json`) computes and single-sources every count so none is ever typed:

```jsonc
{
  "record_type": "multi_set_membership_index_manifest",
  "distinct_primitives": "<computed>",     // author-once rows referenced
  "distinct_sets": "<computed>",           // families covered
  "edge_count": "<computed>",              // total memberships
  "max_sets_per_primitive": "<computed>",  // the most-reused helper's fan-out
  "candidate": true,
  "serves_truth": false
}
```

Any prose that needs "how many families reuse helper X" or "how many distinct helpers are shared" reads the
manifest / queries `memberships.jsonl` — it is never restated as a literal.

### 2.4 Multi-set is the reinvention-guard at the PACK level

The reinvention-guard ("this already exists, don't rebuild it") operates at two levels:

- **Runtime level** (existing) — the matching engine / `search_all` interrupts an agent about to rebuild a
  primitive that already exists (OPERATIONS-BIBLE §7; the reinvention-guard product).
- **Pack / generation level** (this concept) — the membership index prevents the *factory itself* from
  regenerating the same helper once per family. Before a family's wave-2 expansion emits a helper member, the
  intake step checks the index: if a primitive already covers that edge, the family gets a **membership edge**
  pointing at the existing `primitive_id` instead of a freshly generated duplicate row. Fan-out (one helper, many
  sets) is recorded as `max_sets_per_primitive` in the manifest — the higher it is, the more regeneration the
  index prevented.

This is the same "search first, reuse first, generate only the missing edge" invariant (OPERATIONS-BIBLE §1),
applied to families instead of to a single caller.

---

## 3. The intake → wave → set pipeline (what produced them)

Both concepts are produced by one pipeline that extends the generation manual's `generation → usable` flow with
the wave-lineage and set-membership steps:

```text
[0] SEED PROMPT QUEUE
    scripts/build_prompt_queue_from_seeds.py --write --zip generated_primitive_packs/<pack>.zip
    -> clusters ~1M compact variation seeds by (domain, family) into ONE brief per cluster
    -> data/dev-intel/primitive_factory/prompt_queue/<date>-seed-queue.jsonl
       + <date>-seed-queue.manifest.json   (clusters / total_target_rows / cap — all COMPUTED)

[1] WAVE-1 BREADTH  (one GROUP card per cluster brief)
    generate (Fable ultracode waves | Ollama GLM/Kimi | deterministic table->row)
    -> kind: primitive_group, wave: 1, root_group_id = self
    -> VERIFY -> BRIDGE   (wave-1 is usable here, at family granularity)

[2] WAVE-2 DEPTH  (MEMBER primitives per group)
    for each verified group card, expand its members
    -> kind: primitive, wave: 2, parent_primitive_id = group card, root_group_id = group card
    -> (optional) WAVE-3: implied sub-primitives / mutators / receipts, wave: 3
    -> VERIFY -> BRIDGE   (search now resolves finer member edges)

[3] MULTI-SET INDEX  (author-once / reference-many)
    for each helper member: query the membership index; if the edge already exists,
    emit a membership EDGE (not a new row); else author once + add the edge
    -> catalog/knowledge-packs/data/multi-set-membership-index/memberships.jsonl (+ manifest)

[4] VERIFY   scripts/run_primitive_verification_loop.py --source-root <wave dir> --out-dir <label> --max-ticks 1
    (deterministic schema/source/proof gate; candidate_boundary_gate enforces candidate=true/serves_truth=false)

[5] REGISTRY BRIDGE   scripts/load_verified_candidates_into_registry.py --write
    (loads verified_candidates/<label>/ into the searchable card set — THIS is what makes a wave "usable")

[6] USABLE
    AIDevObserver + the product surfaces can now search/compose the primitives.
    Report:  scripts/report_multilane_primitive_generation.py --date-prefix <day> --write
             scripts/track_primitive_saturation_and_savings.py   (dup-rate = the saturation/stop signal)
```

**Why steps 1 and 2 are separate waves, not one pass:** wave 1 is breadth-first (cover every family with one
coarse edge, ship immediately), wave 2 is depth-first (refine the families that lift). Separating them means a
5-hour Fable session limit that kills wave 2 still leaves wave 1 verified, bridged, and usable — the DEPTH-BEFORE-
BREADTH binding constraint is satisfied *per family*, and breadth is never blocked on depth.

**Where the pipeline's counts live (cite, never type):**

| number | computed source |
| --- | --- |
| seed clusters / target rows / cap | `data/dev-intel/primitive_factory/prompt_queue/<date>-seed-queue.manifest.json` |
| per-day verified across lanes/waves | `data/dev-intel/primitive_factory/multilane_generation_receipts.jsonl` → `multilane_generation_report_<date>.md` |
| per-label (per-wave) output | `data/dev-intel/primitive_factory/verified_candidates/<label>/manifest.json` |
| Fable wave labels (uc01…) + counts | `docs/OPERATIONS-BIBLE.md` §5 (which cites the receipts above) |
| multi-set breadth (distinct primitives / sets / max fan-out) | `catalog/knowledge-packs/data/multi-set-membership-index/memberships.manifest.json` |
| saturation / dup-rate per lane | `data/dev-intel/primitive_saturation/<date>_saturation.md` |

---

## 4. Invariants (both concepts)

- **Candidate always.** Every wave row and every membership edge is `candidate=true` / `serves_truth=false`;
  formalizing or bridging never promotes truth.
- **Relations live in indexes, not on rows.** Children point at parents (`parent_primitive_id`); families point
  at primitives (membership edges). A referenced row is never rewritten to enumerate its referrers — this is what
  keeps waves and set-adoption ADD-ONLY and drift-free.
- **Version + lineage in metadata, never in names.** `wave`, `parent_primitive_id`, `root_group_id`, `set_id`,
  `schema_version` are all fields; ids/slugs/file names carry none of them.
- **Verify + bridge per unit.** A wave or a membership batch is usable only after its own verify → bridge; a
  partial tree and a partial index are both valid intermediate states.
- **Bounded, lift-gated growth.** Depth stops at `wave ≤ 3` and at saturation; breadth reuses via the index
  instead of regenerating. Rejects go to negative memory, not the registry.

## 5. Cross-links

- `docs/OPERATIONS-BIBLE.md` — §1 (loop + invariants), §3 (primitive atlas counts), §4 (core object shapes),
  §5 (factory ops + Fable waves + saturation), §7 (matching engine / reinvention-guard). **Wins on state.**
- `docs/handoff/primitive-generation-verification-and-upload-manual.md` — the generation manual: §0 pipeline,
  §1 verifier row schema, §3 generation lanes, §4 registry bridge. **Wins on exact commands.**
- `docs/BIBLE.md` — vision + laws (Capability-Gap Framework, No-Magic-Values, Lossless Distillation,
  deterministic global naming). **Wins on laws.**
- `scripts/build_prompt_queue_from_seeds.py` — step [0], the seed prompt queue.
- `scripts/track_primitive_saturation_and_savings.py` — the wave depth-stop signal.
- `catalog/knowledge-packs/data/multi-set-membership-index/` — the multi-set membership index (spec here;
  populated by step [3]).
