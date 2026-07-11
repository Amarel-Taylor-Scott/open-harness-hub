# Globally-Unique Variable Name System — portable standard

A canonical, reusable naming law for any **AI Done Right** project. Every defined thing —
code object or generated data record — gets a **globally-unique, location-derived,
meaning-bearing name**, so that the name alone resolves it with zero ambiguity.

This file is **portable**: the rules are generic to any project. The concrete engines,
schemes, and gates named below are the **reference implementation** in the
`ai_harness_and_knowledge_facts_and_logic_website_sharing` repository — cited by path so a
new project can copy the mechanism, not just the intent.

Grounded in (read before acting on any rule):
- `docs/codex/ai-first-naming-and-graph-spec.md` — the owner law (2026-06-27; DATA plane
  hardened 2026-07-01), §§1–6.
- `scripts/pyprefix.py` — the CODE-plane engine (`qualified_name`, `PREFIX`, `is_dunder`).
- `src/teleon/experiments/ids.py` — the DATA-plane single minting authority (`canonical_id`,
  `canonical_bytes`).
- `_repos/_shared/STANDARDS.md` §§2–3 — the same two planes stated as component laws.
- `CLAUDE.md` §"Deterministic Global Object Naming (AI-first)" and §"ID And Hash Discipline".

---

## 1. The principle

**Code here is read by AI first; future review is LLM review.** So the code is optimized for
**deterministic structure a model can resolve with zero ambiguity**, not for human brevity.
The mechanism is one law applied to everything you name:

- **Every defined thing gets a globally-unique name.** No name is ever reused. The same
  simple name in two scopes becomes two different global names
  (`docs/codex/ai-first-naming-and-graph-spec.md` §1).
- **Uniqueness lives IN the name.** The name carries its full location and meaning, so
  identity is not stored in an external table, an opaque key, or Python's import resolution.
- **Location-derived + meaning-bearing.** The name encodes *what kind* of thing it is, *where*
  it is defined, and *what* it does — the file path itself is in the name, so two same-named
  files never collide and nothing depends on `sys.path`
  (`ai-first-naming-and-graph-spec.md` §1, "No reliance on Python modules / import resolution").
- **Long names are GOOD.** Length is attention and context for the model — a name is context
  the model uses, not noise to minimize (`ai-first-naming-and-graph-spec.md` lines 5–6).

### Why — grep-as-graph and the reinvention guard

Because names are globally unique and self-describing, **grep resolves like a graph**: the
code graph, primitive edges, and cross-codebase search resolve by NAME with zero ambiguity.
Every collision removed increases graph recall — the reference code graph
(`scripts/codegraph.py`) still drops thousands of *ambiguous* call edges today
(`codegraph.py` tracks `ambiguous_calls_dropped`), and each unique name is one fewer dropped
edge. The name IS the node id, so the deterministic graph needs **no resolver**
(`ai-first-naming-and-graph-spec.md` §3).

This is load-bearing for the product, not cosmetics: the reinvention guard ("don't rebuild
what already exists") depends on **exact name resolution** — a search that cannot resolve a
name to a single definition cannot tell you the thing already exists. Ambiguous names silently
degrade the highest-ROI decision in the architecture: *"this already exists, don't rebuild it."*

---

## 2. Two planes, one law

The law applies to two kinds of named thing. They share the principle (§1) but mint names
differently, because their purposes differ: **code objects are authored** (a human/agent reads
the name), while **data ids are keys for millions of generated rows** (dedupe/index identity).

### Plane 1 — CODE objects (authored Python): the pyprefix scheme

Every defined Python thing gets a name of the form:

```
py_<kind>__<file>__<scope>__<name>
```

- `<kind>` ∈ `class` · `function` · `method` · `const` · `instance` · `var` · `arg` · `local`.
  The prefix map is the single source: `scripts/pyprefix.py` `PREFIX`
  (`py_class_`, `py_function_`, `py_method_`, `py_const_`, `py_inst_`, `py_var_`, `py_arg_`,
  `py_local_`).
- `<file>` = the literal relative path, slashes → `_`, `.py` dropped
  (`src/teleon/runtime/credentials.py` → `src_teleon_runtime_credentials`).
- `<scope>` = the enclosing class/method qualname; empty for module-level.
- `<name>` = the original descriptive name.
- **Dunders are exempt** (`__init__`, `__repr__`, `__all__` …) — they are protocol, not user
  names (`pyprefix.py` `is_dunder`, `_DUNDER`).
- **Idempotent** — a name already carrying its kind prefix is returned unchanged
  (`pyprefix.py` `qualified_name`, `target_name`).

Reference shapes the engine emits today (`ai-first-naming-and-graph-spec.md` §1):

```
py_function_src_teleon_runtime_credentials__is_present
py_method_shop__Cart__add
py_var_shop__open_cart__total
py_const_src_teleon_runtime_execution_backend_selector__GENERIC_FUNCTIONS
```

**Coverage** (every Python "defined thing"): classes, functions, methods, module constants
(ALL-CAPS), instantiations, module/class vars + type aliases + TypeVars, function parameters,
local + for/with/except bindings. Decorators/properties/classmethods add edges. Dynamic
references (`getattr`, string dispatch) are marked **unresolved** in the graph, never guessed —
honesty over false precision (`ai-first-naming-and-graph-spec.md` §2).

**New / generated code follows the scheme from the first draft** — it must not emit short,
human-optimized names and rely on a later cleanup pass. Codegen carries the AI-first name plus
purpose/input-shape/output-shape/dependencies in the docstring or contract object (reference
contract: `architecture/teleon_codegen_contracts.json`;
`ai-first-naming-and-graph-spec.md` §3c).

### Plane 2 — DATA objects (generated ids/records): one minting authority

Generated row/record/component ids obey the **same** law through exactly **one** minting
function (reference: `src/teleon/experiments/ids.py`):

```python
canonical_id(prefix, *parts) -> f"{prefix}-{sha256(canonical_bytes(parts))[:16]}"
```

- `canonical_bytes` = sorted-key, compact-separator, UTF-8 JSON
  (`json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)`), so
  **formatting never creates a false identity** and **content changes are always detectable**
  (`ids.py` `canonical_bytes`).
- The **`prefix` is the meaning-bearing, human-readable part**; the hash suffix is a stable
  content key — **never truncation-only**, and **never a re-implemented hash**. Suffix length
  is a single named constant (`ids.py` `ID_HASH_SUFFIX_LEN = 16`).
- **The deliberate exception to "no hashes in names":** DATA ids are keys for millions of
  generated rows (dedupe/index identity), so a hash suffix prevents daily-batch collapse. The
  prefix keeps the meaning; the suffix keeps the uniqueness at scale
  (`ai-first-naming-and-graph-spec.md` §6). Authored CODE objects never carry a hash.
- **Single-source law:** a project has ONE `canonical_id` definition; every other layer
  imports it (reference: Baltor mints through the `src/baltor/experiments/ids.py` re-export
  shim — one runtime, one definition).

### Version lives in metadata — never in a name or id

On **both** planes, **version is metadata, never part of a name or id**: no `.vN` suffix, no
`@N` suffix. Version lives in a `schema_version` field on the record envelope (reference:
`src/teleon/io/governed_record.mint_record`). External briefs that carry `@1`-style ids are
**adapted on intake** — the `@N` moves into metadata (`ai-first-naming-and-graph-spec.md` §6;
`CLAUDE.md` §"Deterministic Global Object Naming"). Formatting or version changes must not
create false new identities.

### Plane 3 — USER-FACING names

Names a person reads (product objects, UI labels, doc terms, edge names) follow the same
uniqueness principle with a human-readable surface:

- **Full words, no abbreviations, no jargon codenames.** Spell it out
  (`CLAUDE.md` §"Deterministic Global Object Naming", "User-facing names").
- **Records name their edges.** Composable objects declare their input/output edges
  (`input_edge` / `output_edge` contracts) so agents compose by reading **names + edges**, not
  by reading bodies (`CLAUDE.md`, same section). The name-graph extends to the product surface,
  not just the code.

---

## 3. Enforcement (no divergence, ever)

A naming law is only real if drift turns something red in the same change. The reference
implementation gates each plane:

**CODE plane (pyprefix):**
- `pyprefix check <path>` — every definition must equal its `qualified_name`; **exit 1** on any
  divergence (`scripts/pyprefix.py`, read-only lint).
- `scripts/check_pyprefix_conformance.py` — every path marked `migrated` in
  `architecture/pyprefix_migration.json` stays **100% conformant**; a renamed package can never
  drift back.
- `scripts/check_pyprefix_methodology.py` — the machine-readable methodology rules
  (`architecture/pyprefix_methodology_rules.json`) exist and scans stay scoped to owned source
  (rules include `names-are-meaningful-not-hashes`, `migrated-means-zero-violations`,
  `dynamic-refs-are-unresolved`).
- The runtime oracle for cross-file + dynamic safety during migration is
  `scripts/run_proofs.py` — never trust a single check over the full gate.

**DATA plane (single-source ratchet):**
- `scripts/check_canonical_id_single_source.py` over
  `architecture/canonical_id_migration.json`. The **drift signal is a direct `import hashlib`
  in `src/**`** — legacy sites (hand-rolled separators, missing `sort_keys`, `:12`/`:20`
  suffixes, `prefix+hash` formats) are recorded in a baseline that **ratchets DOWN**: migrating
  a file means importing from the single `ids.py` **and** removing it from the baseline **in
  the same change**; any **NEW** site fails the gate immediately
  (`ai-first-naming-and-graph-spec.md` §6).

**Portable rule:** every AI Done Right project provides (a) a code-name conformance lint that
exits non-zero, (b) a "migrated stays conformant" gate over a manifest, and (c) a single-source
ratchet for generated ids whose drift signal is a raw hash import outside the one minting
module. Migrate **leaf-first, package by package, full gate green after each** — never a single
whole-repo edit (`ai-first-naming-and-graph-spec.md` §5).

---

## 4. Do / don't

### CODE objects

- **DO** name from the first draft with kind + file + scope + original name:
  `py_function_src_teleon_runtime_credentials__is_present`.
- **DO** let the same simple name in two scopes become two distinct global names — that is the
  point (`ai-first-naming-and-graph-spec.md` §1).
- **DON'T** hand-optimize for brevity: `is_present`, `total`, `add` are ambiguous across a repo
  and drop call edges from the graph.
- **DON'T** put a hash or opaque key in an authored code name — hashes destroy the context an
  AI needs; the meaning must live in the name (`ai-first-naming-and-graph-spec.md` §2).
- **DON'T** lean on `sys.path` / import resolution for identity — the file path is in the name
  for exactly this reason.
- **DON'T** guess a dynamic reference (`getattr(obj, s)`, `globals()[s]`) — mark it
  **unresolved**, never a fabricated edge.

### DATA objects

- **DO** mint every generated id through the one `canonical_id(prefix, *parts)`; keep the
  `prefix` meaning-bearing (`component`, `grp`, `source_record`, …).
- **DO** hash over `canonical_bytes` so formatting is a non-event and content changes are
  detectable (`ids.py`).
- **DON'T** re-implement the hash (`import hashlib` in `src/**` is the tracked drift signal),
  truncate a name to make a key, or hand-roll separators / drop `sort_keys`.
- **DON'T** embed version in the id: `component-3f2a...@2`, `grp:foo@1`, `pipeline.v2` are all
  wrong — version is `schema_version` metadata; `@N` on an external brief moves into metadata on
  intake (`ai-first-naming-and-graph-spec.md` §6).

### USER-FACING names

- **DO** use full words (`KnowledgeCorpus`, `VerificationQueue`), and let records name their
  `input_edge` / `output_edge`.
- **DON'T** ship abbreviations or jargon codenames in user-facing prose or labels
  (`CLAUDE.md` §"Deterministic Global Object Naming").

---

## 5. Sources cited

| Source (reference implementation) | Used for |
|---|---|
| `docs/codex/ai-first-naming-and-graph-spec.md` §§1–6 | the owner law; both planes; migration; enforcement |
| `scripts/pyprefix.py` (`PREFIX`, `is_dunder`, `qualified_name`, `target_name`) | CODE-plane scheme, kinds, dunder exemption, idempotency |
| `src/teleon/experiments/ids.py` (`canonical_id`, `canonical_bytes`, `ID_HASH_SUFFIX_LEN`) | DATA-plane single minting authority; canonical bytes |
| `src/baltor/experiments/ids.py` | single-source shim (one runtime, one definition) |
| `scripts/codegraph.py` (`ambiguous_calls_dropped`) | grep-as-graph recall rationale |
| `scripts/check_pyprefix_conformance.py`, `scripts/check_pyprefix_methodology.py` | CODE-plane gates + methodology rules |
| `scripts/check_canonical_id_single_source.py`, `architecture/canonical_id_migration.json` | DATA-plane single-source ratchet |
| `architecture/pyprefix_migration.json`, `architecture/pyprefix_methodology_rules.json` | migration manifest + machine-readable rules |
| `architecture/teleon_codegen_contracts.json` | generated code follows the scheme from the first draft |
| `_repos/_shared/STANDARDS.md` §§2–3 | the two planes stated as component laws |
| `CLAUDE.md` §§"Deterministic Global Object Naming", "ID And Hash Discipline" | operating-layer statement; user-facing names; version-in-metadata |
