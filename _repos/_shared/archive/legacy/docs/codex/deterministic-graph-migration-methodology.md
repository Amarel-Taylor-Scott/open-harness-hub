# Deterministic Graph Migration Methodology

This repo is moving toward AI-first Python source where every defined name carries enough context to be
resolved by grep and by deterministic graph tooling without an LLM reading whole files.

The core rule is:

```text
py_<kind>_<file>__<scope>__<name>
```

This is intentionally long. The name carries the kind, file, scope, and original meaning. We do not use
hashes or opaque IDs because they remove the context an AI needs.

## What Exists

- `scripts/pyprefix.py`
  - `check`, `stats`, `audit`
  - `graph` for definition/call/contains/inherits edges
  - `opgraph` for operation-level AST/control/data edges
  - `migrate-package`, `migrate-module-scope`, `migrate-scoped`, `migrate-safe-args`
  - `arg-report` and `contract-report` for high-risk migration surfaces
- `architecture/pyprefix_migration.json`
  - `migrated` is the enforcement list.
  - `partial_migrations` records package progress that is green but not yet 100%.
- `scripts/check_pyprefix_conformance.py`
  - every path in `migrated` must stay at `pyprefix check == 0`.
- `scripts/run_proofs.py`
  - the runtime oracle; compile checks are necessary but not sufficient.

## Current Repo Scale

`pyprefix audit .` scopes to owned Python source only. It excludes virtualenvs, `_reference`, archives,
generated dist/site/artifacts, data, caches, and assistant scratch.

Current owned-source audit:

- Python files: 1,783
- Symbols: 79,561
- Conforming: 2,000
- Violations: 77,561
- Conformance: 2.5%

Largest roots:

- `scripts`: 62,209 symbols, 60,905 violations
- `src`: 17,075 symbols, 16,421 violations
- `code-templates`: 146 symbols, 146 violations
- `templates`: 95 symbols, 89 violations
- `hf-space`: complete, 36/36 conforming, in `migrated`

Important corner-case counts from the audit:

- f-strings: 10,408
- comprehensions: 7,553
- lambdas: 912
- decorated definitions: 475
- dataclasses: 217
- protocol/ABC classes: 63
- dynamic `getattr`: 185
- dynamic `hasattr`: 42
- dynamic imports: 23
- dynamic `**kwargs` calls: 97
- `eval`/`exec`/`globals`/`locals`/`setattr`: present and must be treated as unresolved risk

These counts are why a broad one-shot rename is not acceptable. Full migration means a sequence of
verified package migrations.

## Migration Rules

1. Owned source only.
   Do not migrate virtualenvs, `_reference`, generated `dist`/`site`, archives, data, or assistant scratch.

2. Package-sized changes only.
   Run a dry-run first, apply one package/slice, then run the full proof gate.

3. Compile is not the oracle.
   `compile()` catches syntax. `scripts/run_proofs.py` catches runtime contracts.

4. Only 100% conformant packages enter `migrated`.
   A partial package is documented in `partial_migrations` but not enforced as complete.

5. Candidate-safe names can move automatically.
   Module-level functions/classes/constants/module-vars, scoped locals, and keyword-safe args can be
   migrated by the current codemods when dry-run and compile checks are clean.

6. Contract-risky names require coordinated migration.
   Args with keyword or `**kwargs` callers, methods with protocol/attribute refs, and dataclass/class fields
   with constructor/string-key/attribute exposure must move with all their call sites and surfaces.

7. Dynamic references are unresolved until proven otherwise.
   `getattr(obj, "x")`, `globals()["x"]`, `importlib.import_module`, JSON/string keys, and monkey patching
   are risk markers. The tool should report them; it should not pretend they are statically safe.

8. External entrypoints use compatibility shims.
   Names required by outside runtimes or specs, such as CLI `main`, test-runner discovery names, template
   `run(inputs)`, API `serve`/`handle`, or framework hooks, should not be blindly renamed. Keep a small
   exempt wrapper only when it delegates immediately to a typed implementation. The wrapper is the external
   contract; the implementation carries the AI-first name.

9. Every new edge or rule must be deterministic.
   Prefer AST, symtable, import tables, call/keyword indexes, and operation graph queries over prose.

## Completed Example

`hf-space` is the first fully completed leaf migration:

```bash
python3 scripts/pyprefix.py migrate-package hf-space --apply
python3 scripts/pyprefix.py migrate-module-scope hf-space --apply
python3 scripts/pyprefix.py migrate-scoped hf-space --kinds local --apply
python3 scripts/pyprefix.py migrate-safe-args hf-space --apply
python3 scripts/pyprefix.py check hf-space
PYTHONPATH=. python3 scripts/run_proofs.py
```

Result:

- 36/36 conforming symbols
- 0 violations
- full proof gate: 730/730 green
- `hf-space` added to `architecture/pyprefix_migration.json:migrated`

## Benefits

- Greppable exactness: a symbol name says what kind of thing it is and where it lives.
- Deterministic graphs: definitions, calls, contains, inheritance, assignments, operators, control flow,
  and local data flow can be represented as graph nodes/edges without asking an LLM to infer structure.
- Safer refactors: every migration phase is dry-run, compile-checked, proof-gated, and manifest-locked.
- Better AI context: long names carry file/scope/meaning into every prompt, stack trace, grep hit, and graph
  node.
- Regression prevention: once a package is in `migrated`, the conformance gate prevents drift.
- Honest uncertainty: dynamic refs and contract surfaces are flagged instead of silently guessed.

## Next Work

1. Build coordinated contract codemods:
   - signature args + keyword callers + `**kwargs` risk handling
   - protocol/base methods + implementers + attribute calls
   - dataclass/class fields + constructor keywords + string-key surfaces
2. Build external-entrypoint shim support for names like template `run(inputs)`, API `serve`/`handle`,
   framework hooks, and test discovery names.
3. Add `symtable` binding facts to reports so local/global/free/nonlocal bindings are classified with
   Python's compiler view.
4. Add graph queries for resolved call paths and requirement-to-handler paths.
5. Continue leaf migrations:
   - `code-templates`
   - `templates`
   - self-contained `scripts/check_*.py`
   - broader `src/teleon` packages after `src/teleon/runtime` contract codemods are complete.
