# AI-first naming + deterministic graph — specification (owner law, 2026-06-27)

The code in this repo is read primarily by **AI**, not humans. So we optimize for **deterministic
structure an AI can resolve with zero ambiguity**, not for human brevity. The mechanism: every defined
thing gets a **globally-unique name that carries its full location and meaning**. Long is good — length is
attention and context for the model.

**Hard constraints (owner-stated):**
- **No hashes / opaque keys.** They destroy the context an AI needs. Uniqueness must live *in* the name and
  be *meaningful*.
- **No reliance on Python modules / import resolution.** The name carries the **file** path itself, so two
  same-named files never collide and nothing depends on `sys.path`.
- **No reliance on dynamic refs.** `getattr`/`globals()[s]`/string dispatch defeat static resolution — mark
  them **unresolved** in the graph rather than guess (honesty over false precision).
- **No reliance on markdown for structure.** Structure lives in the names + the graph, not prose docs.
  (This spec is design, not structure-knowledge.)

## 1. The name scheme (engine: `scripts/pyprefix.py` → `qualified_name`)

```
py_<kind>__<file>__<scope>__<name>
```

- `<kind>` ∈ class · function · method · const · instance · **var** · **arg** · **local**.
- `<file>` = the literal relative path, slashes → `_`, `.py` dropped (e.g. `_repos/teleon/backend/src/teleon/runtime/credentials.py`
  → `src_teleon_runtime_credentials`).
- `<scope>` = enclosing class/method qualname (empty for module-level).
- `<name>` = the original descriptive name.
- **Idempotent** (a name already carrying its kind prefix is returned unchanged); **dunders exempt**.

Examples (all real shapes the engine emits today):
```
py_function_src_teleon_runtime_credentials__is_present
py_method_shop__Cart__add
py_var_shop__open_cart__total
py_const_src_teleon_runtime_execution_backend_selector__GENERIC_FUNCTIONS
```
The same simple name in two scopes becomes two different global names — **no name is ever reused**.

**Optional extensions (owner-suggested):**
- **Purpose in the name**: append a short purpose token, e.g. `py_function_..._is_present__checks_reachability`.
- **I/O in the docstring**: every definition's docstring states inputs and outputs explicitly (a parseable
  contract), so signature + behavior are self-describing alongside the self-describing name.

## 2. Coverage — every Python "defined thing"

| construct | covered? | name kind |
|---|---|---|
| class, function, method | yes | `py_class_/py_function_/py_method_` |
| module constant (ALL-CAPS) | yes | `py_const_` |
| instantiation (`x = Cls()`) | yes | `py_inst_` |
| module/class variable / type alias / TypeVar | yes (detected; phase-1 rename for module vars) | `py_var_` |
| function parameters | yes (detected/graphed; keyword-safe rename built; risky args deferred) | `py_arg_` |
| local variables, for/with/except bindings | yes (detected/graphed; scoped rename built) | `py_local_` |
| decorators, properties, classmethod/staticmethod | edges + method kind | — |
| dunders, `__all__` | exempt | — |
| dynamic (`getattr`, string dispatch) | **unresolved** node/edge | — |

Parameters have a conservative two-step path: `arg-report` detects visible keyword calls and dynamic
`**kwargs` risks; `migrate-safe-args` only renames args with no visible keyword/dynamic risk. Remaining
args need coordinated signature + caller rewrites. Local variables have a scoped rename codemod that
handles closure reads, skips parameter reassignments unless args migrate in the same pass, and fails closed
if a planned token edit cannot be applied exactly.

## 3. The deterministic graph

Because names are globally unique and self-describing, the graph needs **no resolver**: a name *is* its
node id. Nodes = definitions; edges = `contains` (file→class→method), `calls`, `inherits`, `uses` — all
extracted by AST (`pyprefix graph`) and exact once names are typed.

**Synthetic nodes + multi-attribute edges (owner idea):** a node can be a concatenation of attributes
(file + kind + scope + name + purpose). An edge can then require **multiple attribute matches** to form
(e.g. same-file AND calls AND same-layer), which makes edges precise and queryable without an LLM. This is
the richer phase: model nodes as attribute bundles, edges as predicates over those attributes.

### 3a. Operation-level graph — every operation as a node (owner idea, 2026-06-27)

Beyond definitions + call/contains/inherits edges, the graph should represent **every operation**:
variable assignment, object assignment, comparisons, boolean/arithmetic operators, math calls, indexing,
attribute access, returns, branches, loops — each as a node carrying its **location, the source code, and
its operands**. This is exactly a **Code Property Graph (CPG)** — the model behind CodeQL, Joern, and
Semgrep — which unifies the AST (structure), the control-flow graph (order), and the data-flow graph
(value movement) into one queryable graph. Prior art to mirror, not reinvent:

- **AST layer**: every `ast` node → a graph node (`op_assign`, `op_compare`, `op_binop`, `op_call`,
  `op_subscript`, `op_return`, `op_if`, `op_for`, …) with `{file, line, col, code, kind}` and child edges.
- **Control-flow edges**: statement → next statement / branch targets (order of execution).
- **Data-flow edges**: a value defined at one node → every node that uses it (def→use), which is where the
  globally-unique names pay off — a `py_var_…__total` flows deterministically with no aliasing guesswork.
- **Operators carry meaning in the node** (`op_compare_gte`, `op_binop_mult`), consistent with the
  "meaning in the name, no hashes" law.

Built now: `pyprefix opgraph <path>` emits the AST-node layer from `ast` with `{file, line, col, scope,
code, defines, uses}`, `ast_child` edges, simple `control_next` edges, and conservative local
`data_def_use` edges. On `_repos/teleon/backend/src/teleon/runtime`, this currently yields 5,149 operation nodes and 7,088
edges. Remaining deeper work: full branch-aware CFG, interprocedural data flow, and typed-name-backed
exact def->use once the package migration is complete.

### 3b. Research-backed adjustments to the next phase

The current direction matches the useful parts of established tooling without adopting their opaque IDs:
Python's `ast` exposes definitions, arguments, calls, keywords, and locations; Python's `symtable` exposes
lexical binding/scope facts; CodeQL separates local flow from global/interprocedural flow; Joern/CPG models
AST + control flow + data flow as one queryable graph. The adjustment is practical: before the next rename
codemod applies changes, pyprefix should enrich reports with `symtable` binding facts and graph queries so
it can distinguish "local binding", "protocol/interface contract", "dataclass constructor field",
"serialization key", and "dynamic unresolved string" deterministically.

References used for this adjustment:
- Python `ast`: https://docs.python.org/3/library/ast.html
- Python `symtable`: https://docs.python.org/3/library/symtable.html
- CodeQL Python data flow: https://codeql.github.com/docs/codeql-language-guides/analyzing-data-flow-in-python/
- Joern Code Property Graph: https://docs.joern.io/code-property-graph/
- Rope project refactoring model: https://rope.readthedocs.io/en/latest/overview.html

### 3c. Teleon-generated code contract

Teleon writes code, so generated code must follow this methodology from the first draft. It should not
emit short, human-optimized names and then rely on a later cleanup pass. The generated artifact is a
candidate (`serves_truth=false`) and must carry enough structure for deterministic checks and LLM review:

- long AI-first pyprefix names (`py_<kind>_<file>__<scope>__<name>`);
- purpose, input shape, output shape, dependencies, and proof-to-run in docstrings or contract objects;
- scalar-or-sequence input normalization by default when a step may need batch processing later;
- bounded iteration with history, never unbounded generated `while` loops;
- dispatch tables / rule rows over rigid branch chains when cases can grow;
- arrays/maps over numbered scalar series (`item1`, `item2`, `item3`);
- strict parameter typing deferred until the runtime shape stabilizes and optimization begins.

Built now:

- `architecture/teleon_codegen_contracts.json` is the machine-readable contract.
- `_repos/teleon/backend/src/teleon/synthesis/primitive_blocks.py` provides scalar-to-sequence, batch-map, bounded-loop,
  dispatch-table, candidate-envelope, and generated-code-contract primitives.
- `scripts/check_teleon_codegen_contracts.py` proves those primitives and rules exist.
- `scripts/hybrid_repo_review_pipeline.py` turns deterministic findings + graph context into LLM review
  packets. The LLM can explain purpose/UX/product risk and propose fixes, but the packet remains
  candidate-only until deterministic proofs pass.

This is the answer to "will the graph help find poor logic?": yes. The operation graph plus review
pipeline surfaces magic literals, dynamic references, boolean flag control surfaces, mutable defaults,
rigid branch chains, repeated adjacent calls, scalar series that should be arrays/maps, and pyprefix drift.
The LLM then enriches those signals with candidate reasoning; it does not replace the deterministic
evidence.

## 4. Enforcement (no divergence, ever)

- `pyprefix check <path>` — every definition must equal its `qualified_name`; exit 1 otherwise.
- `scripts/check_pyprefix_conformance.py` (gate) — every path in `architecture/pyprefix_migration.json`
  `migrated` stays 100% conformant. A renamed package can never drift back.
- The required-functionality graph (`architecture/required_functionality.json`) checks "page X requires
  functionality Y" against the named structure.
- `scripts/check_teleon_codegen_contracts.py` — generated-code rules and primitive blocks stay present.
- `scripts/hybrid_repo_review_pipeline.py` — deterministic findings become candidate LLM review packets
  with graph context, never truth.

## 5. Migration — the massive rename, done safely

A whole-repo rename to these names is a **multi-phase, gate-verified migration**, not a single edit
(the proof gate has 730 checks; cross-file references + re-export facades + dynamic refs all break loudly,
which is correct — fix them FORWARD, never revert).

The engine is built and hermetically proven: `qualified_name` (the scheme), `cross_file_rename` (rewrites
def + from-imports + bare refs + qualified `M.x` across files, compile-verified + rollback), explicit
facade/`__all__` propagation, `safe_targets` / `globally_unique_targets` (find what's safe), scoped local
renames, module-scope renames, keyword-safe arg renames, and read-only contract reports for the remaining
high-risk surface. What remains for the migration to be turnkey:

1. **Migrate leaf-first** (import-graph order: modules with no importers first), package by package, full
   gate green after each, then add the path to the manifest. Use `pyprefix safe-targets`,
   `migrate-package`, and `migrate-module-scope`, widening only after dry-run + compile checks are clean.
2. **Phase 2/3 contract codemods**: remaining params (`py_arg_`) require signature + keyword-call rewrites;
   methods (`py_method_`) and instances (`py_inst_`) require receiver typing and protocol grouping;
   class/body vars require dataclass constructor keywords, attribute refs, and string-key surfaces to move
   together. Detection, reports, and operation-graph representation are built; module-scope, local-variable,
   and keyword-safe parameter automatic renaming are applied to `_repos/teleon/backend/src/teleon/runtime`.

**Pickup:** this spec — `docs/codex/ai-first-naming-and-graph-spec.md` is the formal repo-wide methodology (it
absorbed the former `deterministic-graph-migration-methodology.md`, now archived under `archive/legacy/`) — and
`_repos/shared-backend-components/context/codex/pyprefix-migration-and-functionality-graph.md` (per-package protocol). Run
`scripts/run_proofs.py` after every package; it is the only trustworthy oracle for cross-file + dynamic
safety. `hf-space` is the first completed package in `migrated`; `_repos/teleon/backend/src/teleon/runtime` is the first large
partial package and remains blocked on coordinated contract migration for args/methods/class fields.

## 6. The DATA-object plane (same law, second plane — hardened 2026-07-01)

pyprefix names CODE objects. Generated DATA objects (row/record/component ids) obey the same law through ONE
minting authority — `src.teleon.experiments.ids`:

- `canonical_id(prefix, *parts)` → `"{prefix}-{sha256(canonical_bytes(parts))[:16]}"`. Never truncation-only;
  never a re-implemented hash. `canonical_bytes` = sorted-key compact UTF-8 JSON, so formatting never creates a
  false identity and content changes are always detectable.
- **Version lives in `schema_version` METADATA** (`_repos/teleon/backend/src/teleon/io/governed_record.mint_record` envelope), never in
  a name or id — no `.vN`, no `@N`. External design briefs that carry `@1`-style ids (e.g. the primitive-database
  brief's `grp:...@1`) are adapted on intake: the `@N` moves into metadata.
- Baltor mints through the `_repos/baltor/backend/src/baltor/experiments/ids.py` re-export shim (dependency law: one runtime, one
  definition). The exception to "no hashes in names" is deliberate: DATA ids are *keys for millions of generated
  rows* (dedupe/index identity), not authored code objects — the hash suffix prevents daily-batch collapse, while
  the `prefix` stays the meaning-bearing part.
- **Enforcement:** `scripts/check_canonical_id_single_source.py` over `architecture/canonical_id_migration.json`.
  Direct `import hashlib` in `src/**` is the drift signal — the 71 legacy sites recorded 2026-07-01 (hand-rolled
  `\x1f` separators, missing `sort_keys`, `:12`/`:20` suffixes, `prefix+hash` formats) ratchet DOWN: migrating a
  file means importing from `ids.py` AND removing it from the baseline in the same change; any NEW site fails the
  gate. Known open decisions (owner): per-domain suffix lengths beyond 16; `type/slug` (catalog) vs
  `prefix-hash16` (generated) id-format boundary; migration order for the legacy sites.
