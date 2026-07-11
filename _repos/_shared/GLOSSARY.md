# Shared Glossary

The shared vocabulary so separately-managed components stay consistent. Each
term below gives the **canonical spelling** and one crisp definition, then links
to the detailed source doc — the source wins on any conflict. Nothing here is
invented: every entry cites where it comes from.

Governing vocabulary rules (spellings, what NOT to say) live in the root
`CLAUDE.md` ("Use 'components' and 'subcomponents' … Product vocabulary:
Knowledge Corpus, If Statement, Action"). The primitive/stage model is
`docs/concepts/component-taxonomy-and-stages.md`. The naming law is
`docs/codex/ai-first-naming-and-graph-spec.md`.

**Path convention:** short-form citations resolve to the canonical multi-repo layout — `docs/`, `scripts/`,
`architecture/` live under `_repos/shared-backend-components/`; `src/teleon/…` under `_repos/teleon/backend/`;
`src/baltor/…` under `_repos/baltor/backend/`.

---

## The seven primitives

Everything in a pipeline reduces to **seven primitives**, all extending one
generic shell (`scripts/primitives/base.py::Primitive`, contract `run(po) -> po`).
Every catalog component `type` is a subtype of exactly one primitive. Canonical
spellings and one-line roles (source:
`docs/concepts/component-taxonomy-and-stages.md`, "The seven primitives"):

1. **Input** — the raw payload to work on (text · document · HTML · PDF · image · combination), declared by a pipeline's `inputs`.
2. **Knowledge Corpus** — a store of facts, queried by a trigger. (Product term; see below. NOT "knowledge pack".)
3. **If Statement** — the condition (the IF), kept separate from the THEN. (NOT "rule pack" / "logic pack" in prose.)
4. **Action** — anything that *does* something (the THEN): add-persona, execute/call, transform, model-call, model-transport, evaluate, benchmark.
5. **Loop** — control flow / iteration over sub-steps (for-each · while · branch · parallel · map-reduce; a pipeline orchestrates).
6. **Stop / End** — halt early on a guard or terminal condition.
7. **Output** — finalize the result plus its trace, declared by a pipeline's `outputs`.

There is **no eighth primitive.** An unmet need is captured as a
**capability-request** (a *typed empty slot* carrying the `target_type` it will
become), an operational object like a review-ticket — never tenant-visible as a
component (source: same doc, "Not an eighth primitive").

### Knowledge Corpus

Canonical product term for the fact store. The schema `type` key stays
`knowledge-pack` for back-compat storage only and is **never shown to users**; in
prose and user-facing docs write **Knowledge Corpus**. A corpus is typed by *how
it is queried* — its `retrieval` triggers (`keyword`, `regex`, `rag_vector`,
`exact_id`, `classifier`, `graph`; a corpus may support several). It is **static**
(a versioned fixed fact set) or **dynamic** (fetched/extended by an Action, so it
carries freshness + revocation/CDC). Knowledge adds *facts*; it never holds logic.
Source: `docs/concepts/component-taxonomy-and-stages.md`, "Knowledge Corpus (the
fact store)".

### If Statement

Canonical product term for the condition primitive (schema `type`s `rule-pack` /
`logic-pack`). A rule is fundamentally **IF condition THEN action**; the If
Statement is the IF half, kept decoupled from the Action (THEN) so one condition
can drive many actions and one action can be triggered by many conditions.
Condition families: `text contains Y` (keyword), `text matches /…/` (regex),
`text similar to X` (vector similarity ≥ threshold), `classifier(text) = Z`, or a
structured/graph check. Source: same doc, "Conditions (IF) and Actions (THEN) —
decoupled". A rule pack never holds facts; a Knowledge Corpus never holds logic.

### Action

Canonical product term for the THEN primitive — anything that *does* something. A
persona, tool, processor, harness, adapter, rubric, or benchmark is an Action.
Product labels: Action: Add Persona (`persona`), Action: Execute/Call (`tool`),
Action: Transform (`processor`), Action: Model Call (`harness`), Action: Model
Transport (`adapter`), Action: Evaluate (`rubric`), Action: Benchmark
(`benchmark`). Source: same doc, "Component types at a glance" and "Conditions
(IF) and Actions (THEN)".

---

## Component vs subcomponent

Use **components** and **subcomponents** in new prose and user-facing docs; avoid
new uses of "artifact" or "manifest" unless quoting an existing schema, filename,
or legacy phrase (source: root `CLAUDE.md`, "Use 'components' and
'subcomponents'…"). A **component** is a reusable, database-backed capability with
a clear contract; a **subcomponent** is a smaller reusable piece an Action is
built from (e.g. "retrieve by keyword then rerank" composes small subcomponents
rather than one monolithic rule — source:
`docs/concepts/component-taxonomy-and-stages.md`, "Conditions (IF) and Actions
(THEN)"). The product is a **component network**, not a pile of static
definitions (root `CLAUDE.md`, North Star).

Note on **primitive**: "primitive" is canonical ONLY for the seven-primitive
model above. In the primitive-foundry / capability-database work a **primitive**
is also used as "a reusable capability with a clear blackbox contract" — see
`docs/codex/primitive-database-agent-brief.md` and
`docs/strategy/primitive-purpose-shape-and-self-aware-loop.md`.

---

## Edges — `input_edge` / `output_edge`

A primitive's typed connection points: `input_edge` (what it consumes) and
`output_edge` (what it emits), each with a compact typed value plus a
`*_description`. Agents **compose by reading names + edges, not bodies** — a route
is an ordered list of primitives with adapters (mutators) between them. The
`dedupe_key` is the normalized `input_edge -> output_edge` pair (the identity used
for population dedupe). Sources: `docs/strategy/primitive-purpose-shape-and-self-aware-loop.md`
("Edges — `input_edge` / `output_edge` …") and
`docs/codex/primitive-database-agent-brief.md` (the record shape:
`"input_edge"`, `"output_edge"`).

## blackbox

The one-sentence contract of a primitive: *does-what, in→out, key side effect* —
what it does **without implementation detail** (`{"does": "…"}`). It is the L1/L2
disclosure a composing agent reads before ever opening the source. Sources:
`docs/strategy/primitive-purpose-shape-and-self-aware-loop.md` ("**`blackbox`** —
one sentence: does-what, in→out, key side effect") and
`docs/codex/primitive-database-agent-brief.md` ("A primitive is a reusable
capability with a clear blackbox contract").

---

## PurposeTask (formal synonym: CapabilityTask)

The **object** in the Teleon runtime — the purpose-driven unit of work that the
runtime resolves, selects components for, and proves on real examples. Canonical
naming (source: `docs/BIBLE.md` line 50 and root `CLAUDE.md`, "Naming"): product =
**Teleon**; object = **PurposeTask**; the formal/spec synonym is
**CapabilityTask** (used by the open CapabilityTask spec / CTS). PurposeTask is
**Teleon**, not a Baltor subsystem (dependency law: Baltor → Teleon →
OpenHubForAI, never the reverse — `docs/BIBLE.md`). Superseded names ("Purpose
Runtime" / "Anneal" / "Cairn" / "OCTS") must not be reused. Brand doc:
`docs/strategy/teleon-naming-and-domain.md`.

---

## serves_truth vs candidate

Two flags that separate asserted truth from unverified work:

- **`candidate: true` / `serves_truth: false`** — the default on every generated
  row, compute output, and mined component. It is candidate advice, not asserted
  truth; it stays this way until a promotion gate passes. AIDevObserver findings,
  generated primitives, and pipeline compute outputs all sit here (sources:
  `docs/concepts/compiling-capabilities-into-bounded-dags.md`, "compute outputs
  carry `serves_truth=false` — they're **candidates**"; root `CLAUDE.md`,
  AIDevObserver steering rule; `docs/strategy/primitive-purpose-shape-and-self-aware-loop.md`).
- **`serves_truth: true`** — reserved for a **governed Baltor truth output** that
  has passed verification. Everything that is not a governed Baltor truth output
  is `serves_truth=false` (source: `docs/BIBLE.md` line 155, "**serves_truth=false**
  on everything that isn't a governed Baltor truth output"). Baltor governs truth;
  agents propose, Baltor disposes.

## verified / proven — the L1→L7 disclosure ladder

Primitives disclose progressively; deeper tiers are **more proof**, opened only
when the task needs them (the shallowness IS the saving). The nested-disclosure
ladder (source: `docs/strategy/primitive-purpose-shape-and-self-aware-loop.md`,
"Nested disclosure"):

`L1 edge card → L2 contract → L3 behavior → L4 route → L5 proof → L6 source slice → L7 full source`

A row's `verification_level` records how far its proof reached (e.g. the real
value `L4_source_ast_snippet_compiled` in
`docs/handoff/claude-code-web-primitive-foundry-handoff.md`); a row is only
**proven/verified** once executed proof at the top of the ladder passes — the
caller's shorthand for that top tier is `L7_executed_proof` (full source,
executed). Until then the row remains `candidate=true / serves_truth=false`; a
report or benchmark is **evidence, never promotion** (same source). NOTE: an
architecture red-team flags that a true L1→L7 **escalation engine does not yet
exist** — the tiers are today's disclosure/scorecard scheme, not a live
peel-back runtime (`docs/codex/architecture-red-team-2026-07-03.md`).

---

## Naming planes (two planes, one law)

Every defined thing gets a globally-unique, location-derived, meaning-bearing
name; no name is ever reused; version lives in metadata, never in a name or ID.
Full law: `docs/codex/ai-first-naming-and-graph-spec.md`; summary in root
`CLAUDE.md`, "Deterministic Global Object Naming".

- **pyprefix — the CODE-object plane.** Python definitions follow
  `py_<kind>__<file>__<scope>__<name>` (`<kind>` ∈ class · function · method ·
  const · instance · var · arg · local; dunders exempt). The name carries the
  literal file path (slashes → `_`, `.py` dropped) so two same-named files never
  collide and nothing depends on `sys.path`. Engine: `scripts/pyprefix.py`
  (`qualified_name`); gate: `scripts/check_pyprefix_conformance.py` over
  `architecture/pyprefix_migration.json`. Example:
  `py_function_src_teleon_runtime_credentials__is_present`.
- **canonical_id — the DATA-object plane.** Generated row/record/component ids are
  minted ONLY by `src.teleon.experiments.ids`:
  `canonical_id(prefix, *parts)` → `"{prefix}-{sha256(canonical_bytes(parts))[:16]}"`.
  The hash suffix (the *one* deliberate exception to "no hashes in names") is a
  collision-proof key for millions of generated rows; the `prefix` stays the
  meaning-bearing part. Version lives in `schema_version` **metadata** — no
  `.vN`, no `@N` (external `@N` ids are moved into metadata on intake). Baltor
  mints through the `src/baltor/experiments/ids.py` re-export shim. Gate:
  `scripts/check_canonical_id_single_source.py` over
  `architecture/canonical_id_migration.json` (direct `import hashlib` in `src/**`
  is the drift signal, ratcheting down from the recorded legacy sites).

Why it matters: globally-unique names make grep-as-graph exact — the code graph,
primitive edges, and cross-codebase search resolve by NAME with zero ambiguity
(source: `docs/codex/ai-first-naming-and-graph-spec.md`, §3).

---

## Terms defined + sources

| Term (canonical spelling) | Source doc |
|---|---|
| the seven primitives (Input · Knowledge Corpus · If Statement · Action · Loop · Stop / End · Output) | `docs/concepts/component-taxonomy-and-stages.md` |
| Knowledge Corpus (not "knowledge pack") | `docs/concepts/component-taxonomy-and-stages.md`; root `CLAUDE.md` |
| If Statement (not "rule pack" / "logic pack") | `docs/concepts/component-taxonomy-and-stages.md`; root `CLAUDE.md` |
| Action | `docs/concepts/component-taxonomy-and-stages.md`; root `CLAUDE.md` |
| component vs subcomponent | root `CLAUDE.md`; `docs/concepts/component-taxonomy-and-stages.md` |
| edge / `input_edge` / `output_edge` | `docs/strategy/primitive-purpose-shape-and-self-aware-loop.md`; `docs/codex/primitive-database-agent-brief.md` |
| blackbox | `docs/strategy/primitive-purpose-shape-and-self-aware-loop.md`; `docs/codex/primitive-database-agent-brief.md` |
| PurposeTask (synonym CapabilityTask) | `docs/BIBLE.md`; root `CLAUDE.md`; `docs/strategy/teleon-naming-and-domain.md` |
| serves_truth vs candidate | `docs/BIBLE.md`; `docs/concepts/compiling-capabilities-into-bounded-dags.md` |
| verified / proven (L1→L7 ladder; top tier `L7_executed_proof`) | `docs/strategy/primitive-purpose-shape-and-self-aware-loop.md`; `docs/handoff/claude-code-web-primitive-foundry-handoff.md`; `docs/codex/architecture-red-team-2026-07-03.md` |
| pyprefix naming plane (code) | `docs/codex/ai-first-naming-and-graph-spec.md`; root `CLAUDE.md` |
| canonical_id naming plane (data) | `docs/codex/ai-first-naming-and-graph-spec.md`; root `CLAUDE.md` |
