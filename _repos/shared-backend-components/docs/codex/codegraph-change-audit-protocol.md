# Code-Graph Change-Audit Protocol

**Law (short form):** before AND after you change a file, function, class, or method, audit its **strong
connections** on the code graph and update the load-bearing neighbors in the **same** change. A green test suite
is necessary, not sufficient — a graph audit tells you *what else* the change can break.

This is the standing application of the repo's change-verification contract
([[change-verification-contract]]) to code edits, and it is wired into the context pack so every agent sees it.

## The tool

`scripts/codegraph.py` is the unified, **weighted** code graph — it fuses the two AST graphs into one model and
ranks neighbors by strength so you review the load-bearing ones first:

| Layer | Source | Edge | Weight (strength) |
|---|---|---|---|
| **File / module** | `scripts/code_graph.py` | `import` (module → module) | # symbols crossing the boundary |
| **Symbol** | `scripts/symbol_graph.py` | `calls` / `inherits` (function/class/method) | # distinct call sites |
| **Strength** | computed | per-symbol load-bearing score | Σ weight·confidence over incoming calls |

Resolution is **confident-only**: a call binds to a symbol only via the caller's own module, an explicit import, a
globally-unique name, or a `self`/`cls`/imported-module attribute access. Ambiguous in-repo names and builtin-shadow
calls are **dropped and counted**, never guessed onto an arbitrary same-named def — so the strength ranking is
trustworthy (no `.get`/`read_text`/`set` false hubs). `serves_truth=false` — it is a static derivation; verify
behavior before relying on a specific edge.

## The protocol (run this on every code change)

```bash
# 1. Before editing — see what depends on the thing you're about to touch.
PYTHONPATH=. python3 scripts/codegraph.py --audit <file-path | dotted.module | symbol.name>

# 2. Make the change.

# 3. After editing — re-audit; update every strong caller/importer in THIS change (no orphaned breakage).
PYTHONPATH=. python3 scripts/codegraph.py --audit <same target>
```

What the audit surfaces, **ranked by strength** (strongest first), is the neighbor set to review:

- **File / module target** → the modules that **import** it (they break if its API changes), the external callers
  reaching into its symbols, its downstream dependencies, and its transitive **blast radius**.
- **Symbol target** → its **callers** (they break if you change the signature), its callees, base/derived classes,
  and its load-bearing rank. A high in-strength symbol is **shared infrastructure** — touch it deliberately.

A short name with several definitions returns the candidate list — re-run with the fully-qualified id.

## When the graph itself changes

The graph is a **seam**, so editing it follows the repo's own rule (altering a seam/count means updating its
asserting checks in the same change):

- `symbol_graph.py` / `code_graph.py` / `codegraph.py` all carry `--self-test`; all three are registered in
  `scripts/flywheel_proof_modules.py` and run by `PYTHONPATH=. python3 scripts/run_proofs.py`.
- The committed artifacts (`docs/context/codegraph.generated.{json,md}`,
  `docs/context/symbol-graph.generated.{json,md}`) are **generated** — regenerate, never hand-edit:

```bash
PYTHONPATH=. python3 scripts/codegraph.py --emit
PYTHONPATH=. python3 scripts/symbol_graph.py --emit
```

The persisted JSON is **bounded** (top load-bearing symbols + strongest edges; overflow is counted, not silently
dropped) so it stays committable; the full graph is always recomputable on demand.

## Scope / honest limits

- Covers the **Python** surface (`src`, `scripts`, `local_emulators`) — the substrate of this repo. JS/TS/JSX is
  not yet parsed (no tree-sitter dependency installed); the next rung would add a multi-language layer.
- Static name-resolution only — dynamic dispatch, `getattr`, and registry/callback indirection are invisible.
  Treat the audit as the **first** safety net, not the last; still run the relevant `--self-test`s.

Related: [[change-verification-contract]] · [[no-magic-values]] · [[lossless-distillation]].
