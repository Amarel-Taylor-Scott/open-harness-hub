# pyprefix migration + required-functionality graph — handoff for ChatGPT Codex

**Owner direction (2026-06-27):** implement our own pyprefix throughout ALL the code (mass-rename
functions, classes, methods, instantiated objects), institute contracts to avoid regression/divergence,
and add a required-functionality graph so we can say "page X requires functionality Y" and *check* it
against the structure. The goal: **deterministic code graphs without an LLM reading whole files.**

This document is the pickup point. The focused tooling gates are green; run the full proof gate after each
package migration. The formal repo-wide methodology is in
`docs/codex/deterministic-graph-migration-methodology.md`.

---

## 1. The standard (single source: `scripts/pyprefix.py`)

Encode each definition's kind, file, scope, and original meaning in its name so grep is an exact resolver
and a codemap needs no resolver:

| kind | pattern | example |
|---|---|---|
| class | `py_class_<file>__<scope>__<Pascal>` | `py_class_src_teleon_runtime_key_holder__KeyHolder` |
| function | `py_function_<file>__<scope>__<snake>` | `py_function_src_teleon_runtime_credentials__is_present` |
| method | `py_method_<file>__<scope>__<snake>` | `py_method_src_teleon_runtime_key_holder__KeyHolder__get` |
| instance | `py_inst_<file>__<scope>__<snake>` | `py_inst_src_teleon_runtime_credentials__client` |
| constant | `py_const_<file>__<scope>__<UPPER>` | `py_const_src_teleon_runtime_execution_backend_selector__GENERIC_FUNCTIONS` |
| variable | `py_var_<file>__<scope>__<snake>` | `py_var_scripts_pyprefix___OperationGraph__nodes` |
| argument | `py_arg_<file>__<scope>__<snake>` | `py_arg_scripts_pyprefix__codemod_file__path` |
| local | `py_local_<file>__<scope>__<snake>` | `py_local_scripts_pyprefix___self_test__fails` |

Idempotent for already-prefixed names. Dunders exempt (`__init__`). Underscores preserved inside the
original name segment.
**Entry points exempt** (`ENTRY_EXEMPT` in pyprefix.py: `main`, `_self_test`, `setup`, `teardown`, …) —
the proof gate + CLIs call these by name, so renaming them breaks the contract.

Relationship to `codegraph.py`: codegraph PARSES the AST to resolve structure (already deterministic, no
LLM). pyprefix makes the NAMES self-describing so even grep resolves. They compose — pyprefix `map`
feeds a clean typed symbol stream into codegraph / the hybrid-graph + contradiction mappers.

## 2. What exists now (built this session)

- **`scripts/pyprefix.py`** — stdlib-only. Commands: `standard`, `check <path>`, `map <path> [--json]`,
  `find <name> <path>`, `stats <path>`, `graph <path>`, `opgraph <path>`, **`apply <path> [--exempt a,b]`**,
  `arg-report <path>`, `contract-report <path>`, and `migrate-safe <path>`. Self-tested, gate-registered.
  - `apply` renames the SAFE kinds (functions, classes, constants, module variables) + their in-file bare-name references by
    exact position, then **`compile()`-verifies and ROLLS BACK** if the result would not parse. It can never
    leave broken syntax.
  - `cross_file_rename` rewrites defining modules, `from M import name`, bare post-import refs, qualified
    `M.name`, and explicit facade re-exports through `__all__`.
  - `opgraph` emits operation-level AST/CPG nodes with source locations/code/operands plus `ast_child`,
    `control_next`, and conservative local `data_def_use` edges.
  - `arg-report` and `contract-report` classify the high-risk remainder before any coordinated contract
    rename: keyword/dynamic-kwargs args, protocol methods, dataclass/class fields, attribute refs, dynamic
    refs, constructor keywords, and string-key/serialization exposure.
- **`architecture/pyprefix_migration.json`** — the migration manifest + contract. `migrated` currently
  includes `hf-space`; every listed path must stay 100% conformant. `partial_migrations` records live
  package progress. `planned_order` lists the package order. `safe_kinds_phase1` vs deferred rename kinds.
- **`scripts/check_pyprefix_conformance.py`** (gate) — every path in `migrated` must be 100% conformant
  (`pyprefix check` == 0). Empty manifest passes. This is the anti-regression contract: once a package is
  renamed, new/edited code can't diverge.
- **`architecture/required_functionality.json`** + **`scripts/check_required_functionality.py`** (gate) —
  the required-functionality graph (see §4).
- **`_repos/_shared/north-star/portfolio-functionality-and-wiring-spec.md`** — the full per-page/flow wiring audit
  (purpose / problem / solution / PMF / dependencies / communicates-with / status / gap). The remediation
  backlog. Several gaps there are also encoded as `gap` requirements in the functionality graph.

## 3. The migration — how to continue (THE protocol)

The hard part is **cross-file** references and runtime behavior. `apply` only rewrites IN-FILE references.
Use `cross_file_rename` / package migrations for public symbols. Main hazards:

1. **Cross-file references to functions/classes/constants/module vars** (imports + `module.name`). The
   cross-file codemod covers imports, qualified attrs, and explicit `__all__` facades, but the full proof
   gate remains the oracle.
2. **Methods + instances** are referenced as attributes (`obj.method`) which static analysis cannot resolve
   across duck-typed receivers. These are **phase 2** — rename per file with the test suite as the oracle,
   never blanket.
3. **Arguments** are detected and graphed. `arg-report` identifies args with visible keyword-call or
   dynamic-kwargs risk, and `migrate-safe-args` only renames the keyword-safe subset. Remaining risky args
   require coordinated signature + caller rewrites.
4. **Class/body vars** include dataclass fields, protocol attributes, constructor keyword names, and
   string/JSON keys. `contract-report` exposes those risks before field renames.
5. **Locals** have `migrate-scoped --kinds local`; it handles closure reads, skips parameter reassignments
   unless args migrate too, and fails closed if a planned token cannot be edited exactly.

**Per-package loop (do this for each package in `planned_order`):**
1. `python3 scripts/pyprefix.py check <pkg>` — see the violations + their target names.
2. Start with `python3 scripts/pyprefix.py safe-targets <pkg>` / `migrate-safe <pkg>` for strictly local symbols.
3. For public symbols, use `python3 scripts/pyprefix.py migrate-package <pkg>` first (dry-run), then
   `--apply` only for a package-sized run with zero compile failures.
4. `PYTHONPATH=. python3 scripts/run_proofs.py` — **the gate is the oracle.** It must stay green. If red,
   fix or `git checkout` the package and try a smaller slice.
5. Only when green: add the package path to `migrated` in `architecture/pyprefix_migration.json`. From then
   on `check_pyprefix_conformance` holds the line.

**Completed leaf migration (2026-06-28):** `hf-space` is now 100% conformant: 36/36 symbols, 0
violations, full proof gate `730/730 green`, and the path is in `architecture/pyprefix_migration.json`
`migrated`, so `scripts/check_pyprefix_conformance.py` now prevents drift.

**First large partial package migration (2026-06-28):** `python3 scripts/pyprefix.py migrate-package
_repos/teleon/backend/src/teleon/runtime --apply` renamed 68 globally-unique class/function/const/module-var symbols and rewrote
57 importer/facade files. Four stale old-name references in tests were fixed forward. Then
`python3 scripts/pyprefix.py migrate-scoped _repos/teleon/backend/src/teleon/runtime --kinds local --apply` renamed 108 scoped
local definitions across 13 files; the analyzer was hardened for parameter reassignments and f-string local
references. A follow-up exception-binding cleanup cleared the last local violations. Then
`python3 scripts/pyprefix.py migrate-module-scope _repos/teleon/backend/src/teleon/runtime --apply` renamed 25 additional
module-scope targets by resolved module edges, handling repeated private names like `_REPO` without
confusing unrelated modules. Then `python3 scripts/pyprefix.py migrate-safe-args _repos/teleon/backend/src/teleon/runtime --apply`
renamed 93 keyword-safe parameters. Full proof gate after every phase: `730/730 green`. The package is
still a **partial** migration: `pyprefix stats _repos/teleon/backend/src/teleon/runtime` reports 318/476 conforming symbols
(66.8%) and `pyprefix check _repos/teleon/backend/src/teleon/runtime` reports 158 remaining violations under the expanded
8-kind law: args=74, methods=49, class/body vars=35.
Do not add it to `migrated` until phase-2/3 codemods reach check==0 and the full gate stays green.

**Current repo-wide audit (owned source only):** `python3 scripts/pyprefix.py audit .` reports 1,783 Python
files, 79,561 symbols, 77,561 violations, and 2.5% conformance. Largest roots are `scripts` and `src`.
Corner cases include f-strings, comprehensions, lambdas, decorators, dataclasses, Protocol/ABC classes,
dynamic `getattr`/`hasattr`, dynamic imports, dynamic `**kwargs`, and `eval`/`exec`/`globals`/`locals`.

**Next improvement to build:** coordinated contract migration. Current reports say `arg-report` has 0
remaining keyword-safe args; all 74 remaining args are keyword-call or dynamic-kwargs risky.
`contract-report` says 0/49 remaining methods and 0/35 remaining class/body vars are candidate-safe. The
next codemod therefore has to rename the contract surface as a unit: signatures + callers, protocol/base
methods + implementers + attribute calls, dataclass/class fields + constructor keywords + string-key
surfaces. Keep compile-verify + the full proof gate as the oracle.

## 4. The required-functionality graph (`architecture/required_functionality.json`)

Each requirement is a NODE: "surface/page X requires functionality Y", with a deterministic `check` EDGE to
the code that must satisfy it (a regex over a file, resolved with zero LLM).

- `status: "satisfied"` → REGRESSION-GUARDED. If the code that satisfies it vanishes (or a forbidden
  anti-pattern with `expect: "absent"` returns), `check_required_functionality` FAILS the gate.
- `status: "gap"` → the live remediation backlog. Reported, not failing, until built. When its code lands,
  the checker flags it "resolved" — then flip `status` to `satisfied`.

**To add a requirement:** append `{id, surface, page, requires, check:{type, file, pattern|patterns, expect},
status, rationale}`. `type` is `regex_in_file` or `all_regex_in_file`; `expect` is `present`|`absent`.
**To close a gap:** implement it, change `status` to `satisfied`, run the gate.

**Open gaps seeded from the wiring review (work these next):**
- `id-keys-list-on-mount` — `/keys` never calls `listKeys()` on mount, so real keys vanish after reload
  while 3 fake keys (`sk_live_*`) always show. Add a `useEffect` in `OhApiKeys` (oh-site.jsx) that calls
  `OHIdentity.listKeys()`; drop the fixtures.
- `teleon-new-account-empty` — demo fixtures (Ada Lovelace team, "usury-rate finder promoted" activity,
  "$249 invoice", 4 seeded capabilities) leak into a brand-new account. Gate them behind a demo/test
  account; default new accounts to empty. (teleon-main.jsx + the teleon PATCHES in port_full_design_to_web.py.)

Also in the north-star spec but not yet encoded: signup `Name` field is dropped (oh-identity.js register
sends only identifier+secret); `/dashboard` is not gated on `OHIdentity.validate()`; Teleon's richer
capability experience (generated-code review, GitHub/GitLab-style versions+forks, license/guardrail
selection, export, runtime metadata, component bill-of-materials) is unbuilt.

## 5. Verification (always)

```
PYTHONPATH=. python3 scripts/pyprefix.py --self-test
PYTHONPATH=. python3 scripts/check_pyprefix_conformance.py --self-test
PYTHONPATH=. python3 scripts/check_required_functionality.py --self-test   # or --report
PYTHONPATH=. python3 scripts/run_proofs.py                                  # the full gate is the oracle
```

Never add a path to `migrated` unless the FULL gate is green. The compile-verify guarantees syntactic
safety; only the gate guarantees the cross-file callers still work.

## 6. Roadmap — improvements to the graph-driven knowledge (priority order)

Built so far: AI-first location-derived convention + `check/map/find/stats/apply`, structural graph
(`graph` — nodes + contains/calls/inherits edges), operation graph (`opgraph` — AST operation nodes,
control/data edges), cross-file rename with facade/`__all__` propagation, sounder safe-target finder
(`safe-targets`, now counting `module.SYMBOL` attribute refs), `migrate-safe`, `migrate-package`,
`migrate-module-scope`, `migrate-scoped`, `arg-report`, `migrate-safe-args`, `contract-report`, the
conformance contract, and the required-functionality graph.

**Tier 1 — the enablers (unlock "throughout ALL the code"):**
1. **Phase-2/3 contract codemods.** Methods/instances need receiver typing and protocol grouping; args
   need signature + keyword-call rewrites; dataclass/class fields need constructor keywords, attribute refs,
   and string-key surfaces migrated together.
2. **Resolved edges (not name-matched).** Resolve each `calls`/`uses` edge to its actual defining
   module+symbol via the import table; mark edges `resolved` vs `ambiguous` (as codegraph does). Turns the
   graph from name-ambiguous into an exact call graph — same machinery as #1.

**Tier 2 — richer structure:**
3. Method/instance resolution (phase 2): track receiver types (`x = Cls()` → `x.method` ⇒ `Cls.method`) so
   methods can be renamed + method-call edges are precise.
4. More edge types: imports (dependency graph), decorators, type annotations (`p: Cls` ⇒ uses), attr
   read/write.
5. A **JS/JSX analyzer** — the surfaces' wiring + most open required-functionality gaps live in `.jsx`; a JS
   symbol/edge extractor extends the graph to the frontend.

**Tier 3 — validations / contracts on the graph (deterministic, no LLM):**
6. Dead-code / orphans: defs with 0 references; requirement nodes with no satisfying edge.
7. Cycle detection: import cycles + call cycles.
8. Architectural-rule edges: generalize the portfolio law (Baltor ↛ Teleon) into checkable edge constraints
   for any layer.
9. **Graph-based** required-functionality checks: verify "button X reaches backend handler Y" as a graph
   PATH (seam → route → handler), not a regex — makes the functionality graph truly structural.

**Tier 4 — operational:**
10. Persist the graph as an artifact + a freshness gate (regenerate-on-change) + a structural diff across
    commits. 11. Quality tests: `apply`→`check` idempotence per package; codemod fuzz on random valid
    Python; graph-from-typed-names == graph-from-AST consistency. 12. Import-graph-ordered migration (leaves
    first, so importers migrate after their dependencies).
