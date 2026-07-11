# Combined Code Intelligence Research Plan

This repo should keep the AI-first long-name system, but it should not rely on names alone. The stronger
system is layered:

1. **Meaningful source names** give LLM-visible context at every grep hit, stack trace, graph node, and
   review packet.
2. **Parsers and compiler facts** prove what the code actually does.
3. **Type/reference/data-flow tools** add evidence for contracts and flows the naming layer cannot infer
   by itself.
4. **LLM review** explains risk and remediation as a candidate, never as authority.

The source-level law remains:

```text
py_<kind>_<file>__<scope>__<name>
```

Long names are intentional. Humans are not the primary reader; LLMs and graph tools are.

## Why Source Names Help LLMs

Meaningful identifiers are one of the highest-signal parts of source code. A long name like
`py_function_src_teleon_synthesis_primitive_blocks__normalize_to_sequence` tells a model:

- it is a function;
- it lives in Teleon synthesis primitive blocks;
- it normalizes something to a sequence;
- it is meant to be found by exact grep and mapped into the graph.

That reduces ambiguity when a model sees a small snippet, an error line, a stack trace, or a graph node
without the whole file. It also improves deterministic tooling: the name itself is a searchable semantic
address.

Research and prior systems support the general direction:

- Identifier names encode semantic signals useful for code understanding and naming analysis.
- Code graphs and data-flow tools work better when symbols can be resolved reliably.
- Code-review LLMs are more useful when fed compact, structured evidence instead of entire files.

## Pros Of Long Meaningful Names

- **Context travels with the code.** A snippet, stack trace, or LLM packet still carries file/scope/purpose.
- **Exact grep becomes useful.** Search no longer depends only on a resolver or editor.
- **Graph nodes are self-describing.** Nodes can be read without dereferencing opaque IDs.
- **Generated code starts clean.** Teleon can emit graphable code instead of retrofitting it later.
- **Better review packets.** The LLM sees purpose in identifiers, not only prose.
- **Safer partial context.** If an LLM reads only a function body, long names reduce misread ownership.

## Cons And Failure Modes

- **Token and line bloat.** Very long locals repeated many times can add noise.
- **External contracts.** Framework hooks, CLI `main`, test discovery names, API handlers, and template
  `run(inputs)` cannot always be renamed directly. Use shim wrappers.
- **Dynamic code remains hard.** `getattr`, `setattr`, `globals`, string dispatch, JSON keys, monkey-patching,
  and plugin loading can bypass name-based resolution.
- **Diff churn.** Large renames touch many files and can hide behavior changes if not staged carefully.
- **False confidence.** A meaningful name can be wrong. Parser/type/data-flow evidence must validate it.
- **Interop cost.** Public APIs, serialized fields, dataclass constructor keys, and user-facing config keys
  may need shorter stable aliases.

The answer is not to shorten names. The answer is to combine long names with stronger evidence layers.

## Combined System Layers

### 1. Semantic Source Names

Status: built.

`scripts/pyprefix.py` enforces and migrates meaningful names:

- `py_class_`
- `py_function_`
- `py_method_`
- `py_const_`
- `py_inst_`
- `py_var_`
- `py_arg_`
- `py_local_`

Keep this. It is the source-level semantic address system.

### 2. Python AST + `symtable`

Status: AST built, `symtable` next.

The AST currently powers definitions, refs, calls, contains, inheritance, operation graph nodes, and many
codemods. Add Python `symtable` next so reports can distinguish:

- local bindings;
- globals;
- nonlocals/free vars;
- parameters;
- imported names;
- class-scope bindings;
- nested closure captures.

This will reduce false positives during local/arg/method migrations.

### 3. Multi-Language Parser Layer

Status: gap.

Use tree-sitter or a structural-search adapter for JS/TS/JSX/HTML/CSS. This is necessary because the
repo’s UI seams and buttons live outside Python. The target is a frontend graph:

```text
component -> view -> event handler -> fetch/seam -> backend route -> handler -> state
```

This layer should be version-pinned and deterministic.

### 4. Code Property Graph Layer

Status: operation-graph seed built.

`pyprefix opgraph` already emits:

- operation nodes;
- source location and code snippet;
- `ast_child` edges;
- `control_next` edges;
- local `data_def_use` edges.

Extend it toward a CPG-style graph:

- branch-aware CFG;
- interprocedural call/data flow;
- taint-style source/sink/sanitizer paths;
- queryable “bad logic” patterns.

This is where we identify poor logic, fragile logic, magic numbers, scalar-series, repeated calls, and
unbounded loops as graph queries.

### 5. Pattern/Taint Rule Layer

Status: repo-local heuristics built; Semgrep-style adapter next.

The hybrid review pipeline already detects:

- magic literals;
- dynamic refs;
- `**kwargs` contract risks;
- boolean flag control surfaces;
- mutable defaults;
- broad exceptions;
- rigid branch chains;
- scalar series;
- repeated adjacent calls;
- pyprefix drift.

Next: normalize Semgrep-style rule outputs into the same packet schema. Treat every finding as candidate
until a proof or explicit review accepts it.

### 6. Lint And Static Quality Layer

Status: gap.

Add a Ruff-compatible adapter for fast deterministic hygiene:

- unused imports;
- undefined names;
- broad exceptions;
- complexity;
- formatting;
- common Python errors.

Do not let autofix bypass pyprefix. Fixes go through the proof gate.

### 7. Type Contract Layer

Status: gap.

Add mypy/Pyright-compatible adapters for mature code. Teleon-generated code should not require strict
parameter typing in the first draft. The sequence should be:

1. flexible runtime shape;
2. proofed behavior;
3. observed stable contracts;
4. generated type hints / TypedDict / protocols;
5. type-checker gate.

This keeps early generation flexible while still enabling stronger optimization later.

### 8. Language Server / Reference Layer

Status: gap.

Use LSP/LSIF/SCIP-style data for references, rename plans, type hierarchy, and call hierarchy. This is
especially useful for cross-language surfaces and public contracts. Normalize outputs as evidence rows:

```json
{"tool":"lsp", "path":"...", "range": [line, col], "symbol":"...", "confidence":"tool_reported"}
```

Do not treat the language server as truth; compare it against pyprefix, AST, opgraph, and proofs.

### 9. LLM Candidate Review Layer

Status: built.

`scripts/hybrid_repo_review_pipeline.py` packages deterministic findings and graph context into LLM review
prompts. The LLM can add:

- purpose;
- poor-logic risk;
- UX/product impact;
- likely fix;
- proof to run;
- caveats.

It cannot satisfy a contract. It only proposes.

## Implementation Plan

### Phase 0: Keep The Current Core

- Keep `pyprefix`.
- Keep the operation graph.
- Keep the line-review loop.
- Keep hybrid review packets.
- Keep Teleon codegen primitive blocks.

### Phase 1: Normalize External Evidence

Add a common evidence schema:

```json
{
  "tool": "pyprefix|opgraph|semgrep|ruff|mypy|pyright|lsp|codeql",
  "tool_version": "...",
  "path": "...",
  "line": 1,
  "col": 0,
  "kind": "...",
  "severity": "info|low|medium|high|error",
  "message": "...",
  "confidence": "exact|tool_reported|heuristic|candidate",
  "serves_truth": false
}
```

All external systems write this shape.

### Phase 2: Add `symtable`

Use `symtable` to improve:

- local-vs-global rename safety;
- closure handling;
- arg migration reports;
- method/field contract reports.

### Phase 3: Add Tree-Sitter For Frontend

Build frontend edges:

- JSX component definitions;
- button/input handlers;
- fetch/API seams;
- route/state transitions;
- UI strings and feature flags.

Then connect to Python backend handlers and `required_functionality.json`.

### Phase 4: Add Rule Adapters

Add Semgrep/Ruff-compatible importers when available. If the tools are not installed, keep an offline
repo-local equivalent and report the adapter as unavailable, not failed.

### Phase 5: Add Type/Reference Adapters

Add mypy/Pyright/LSP/SCIP evidence only after generated code has stable runtime contracts. This prevents
types from freezing a bad first draft.

### Phase 6: Query Bad Logic As Graph Smells

Create graph queries for:

- magic scalar literal used in multiple operations;
- scalar-series candidates (`x1`, `x2`, `x3`);
- repeated adjacent calls;
- branch chain with many literal comparisons;
- unbounded loops;
- broad exception swallowing;
- mutable default arguments;
- dynamic refs blocking exact rename;
- UI button with no backend path;
- backend handler with no UI path;
- state mutation with no receipt/audit edge.

### Phase 7: Promote Only Through Proofs

Every suggested fix remains a candidate until:

- parser checks pass;
- pyprefix contract checks pass;
- targeted test/proof passes;
- full gate passes for package-wide migrations.

## Graphable / enrichable / verifiable framing, tool lanes, and current state (consolidated)

> Folds the durable design of the merged graphable-enrichable-verifiable-system plan — the same combined code-intelligence system framed as three properties (graphable, enrichable, verifiable), plus the blast-radius packet, the four tool lanes, the confusion-reduction rules, the Teleon-codegen obligations, and the built-now artifact list.

Operating principle: **names carry context · graphs carry structure · deterministic tools carry evidence · nondeterministic tools carry candidate enrichment · proofs carry acceptance.** This complements the long-name law above; it does not replace it.

- **Graphable** — every object is addressable as a node/edge when feasible: source definitions (class/function/method/const/var/arg/local), references + imports, calls/contains/inherits, assignments/operators/comparisons/returns/branches/loops, data-flow def/use edges, UI view→button→handler→backend-route→state edges, requirement-to-code edges, generated-code contracts. Long names make nodes self-describing (kind, file, package, purpose).
- **Enrichable** — a node is enrichable with candidate-only explanations (purpose, problem solved, input/output shape, UI/UX + product impact, risk notes, likely remediation, proof to run, caveats) from LLMs or humans; enrichment helps understanding but never satisfies a contract.
- **Verifiable** — every claim has a verification lane: deterministic parser/linter/graph evidence, source file+line, proof command + status, source refs for external facts, confidence class, and `serves_truth=false` until promoted. An LLM may *propose* that a branch chain become a dispatch table; the deterministic layer must show the branch chain exists and the proof gate must accept the fix.

**Blast radius** must be visible before a fix is attempted: direct callers/callees, imports/exported symbols, contains/inherits edges, operation nodes, data-flow edges, dynamic-unresolved markers, frontend/backend seams, requirement edges. The conservative first implementation is a packet-level hint (direct node/edge counts + edge types) — enough to prevent the worst failure mode: treating a finding as isolated when the graph says it is connected.

**Four tool lanes:** (1) **deterministic** — the authority for evidence: `pyprefix`, `repo_line_review_loop`, `codegraph`, `symbol_graph`, `opgraph`, `required_functionality`, the registered proof gate; (2) **hybrid** — packetization + reconciliation: `hybrid_repo_review_pipeline`, artifact-fed full-repo packet builds (deterministic findings + graph context + LLM prompts); (3) **nondeterministic** — candidate enrichment only (OpenAI-compatible LLMs, multi-model review, purpose/UX/product analysis, fix hypotheses) — promotes nothing alone; (4) **human/owner review** — risk acceptance + policy judgment, required for security-like findings, dynamic refs, public-API breaks, or product-facing changes.

**Confusion-reduction rules:** keep long source names for context; attach file/line/source excerpts and graph context to every finding; mark dynamic/reflection refs unresolved; use external-entrypoint shims instead of blindly renaming public contracts; treat LLM output as candidate-only; require proof gates before promotion; prefer artifact-fed/resumable full-repo pipelines over monolithic recomputation.

**Teleon-generated code obeys this system from the first draft:** long pyprefix names; purpose/input/output contract objects or docstrings; scalar-or-sequence primitive blocks; bounded loops; dispatch tables; arrays/maps over numbered scalars; candidate envelopes; deferred strict parameter typing until the shape stabilizes; proof-before-promotion — so generated code is graphable and scalable before optimization.

**Built now:** `architecture/graphable_enrichable_verifiable_system.json`, `scripts/check_graphable_enrichable_verifiable_system.py`, `scripts/hybrid_repo_review_pipeline.py` (packets carrying deterministic evidence + graph context + blast-radius hint + verification lanes + context policy + LLM prompt), `architecture/teleon_codegen_contracts.json`, `_repos/teleon/backend/src/teleon/synthesis/primitive_blocks.py`, and `architecture/combined_code_intelligence_systems.json`. Next: `symtable` binding facts in pyprefix reports; tree-sitter/structural evidence for JSX/TS/HTML/CSS; Ruff/Semgrep/mypy/Pyright/LSP adapters as normalized evidence rows; graph queries for poor logic + blast-radius scoring; connect UI requirement nodes to backend handler paths as graph paths (not only regex).

## Research References

Primary/official technical references:

- CodeQL Python data flow: <https://codeql.github.com/docs/codeql-language-guides/analyzing-data-flow-in-python/>
- Joern Code Property Graph: <https://docs.joern.io/code-property-graph/>
- Semgrep taint mode: <https://docs.semgrep.dev/writing-rules/data-flow/taint-mode/overview>
- tree-sitter parser usage: <https://tree-sitter.github.io/tree-sitter/using-parsers/>
- Language Server Protocol 3.17: <https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/>
- Ruff: <https://docs.astral.sh/ruff/>
- mypy type hints: <https://mypy.readthedocs.io/en/stable/cheat_sheet_py3.html>

Research papers / emerging systems:

- Identifier/name semantic analysis: <https://arxiv.org/abs/2007.08033>
- LLM readability and identifiers: <https://arxiv.org/abs/2507.05289>
- Semantic code graph for LLM code understanding: <https://arxiv.org/abs/2310.02128>

These references support the combined approach: names help, but parser/type/data-flow/query layers make
the system robust.
