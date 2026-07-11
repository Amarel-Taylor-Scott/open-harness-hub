# Graphable, Enrichable, Verifiable System

The goal is a code-intelligence system that maximizes context and understanding while reducing confusion,
misread files, missed blast radius, and unsupported promotion.

The operating principle:

```text
names carry context
graphs carry structure
deterministic tools carry evidence
nondeterministic tools carry candidate enrichment
proofs carry acceptance
```

This complements the long-name system; it does not replace it.

## 1. Graphable

Every object should be addressable as a graph node or edge when feasible:

- source definitions: class, function, method, const, var, arg, local;
- references and imports;
- calls, contains, inherits;
- assignments, operators, comparisons, returns, branches, loops;
- data-flow def/use edges;
- UI view/button/handler/backend-route/state edges;
- requirement-to-code edges;
- generated-code contracts.

Long names make graph nodes readable:

```text
py_function_src_teleon_synthesis_primitive_blocks__normalize_to_sequence
```

That name is not only an identifier. It is context: kind, file, package, purpose.

## 2. Enrichable

A graph node is not enough. It must be enrichable with candidate explanations:

- purpose;
- problem solved;
- input shape;
- output shape;
- UI/UX impact;
- product impact;
- risk notes;
- likely remediation;
- proof to run;
- caveats.

The enrichment can come from LLMs or humans, but it remains candidate-only. It helps understanding; it
does not satisfy a contract.

## 3. Verifiable

Every claim should have a verification lane:

- deterministic parser/linter/graph evidence;
- source file and line;
- proof command;
- proof status;
- source refs when facts are external;
- confidence class;
- `serves_truth=false` until promoted.

LLM output can propose that a branch chain should become a dispatch table. The deterministic layer must
show the branch chain exists, and the proof gate must accept the fix.

## 4. Blast Radius

A review packet must make blast radius visible before a fix is attempted:

- direct callers and callees;
- imports/exported symbols;
- contains/inherits edges;
- operation nodes;
- data-flow edges;
- dynamic unresolved markers;
- frontend/backend seams;
- requirement edges.

The first implementation is a conservative packet-level hint: direct node/edge counts and edge types.
That prevents the worst failure mode: treating a finding as isolated when the graph says it is connected.

## 5. Tool Lanes

### Deterministic Lane

Authority for evidence:

- `pyprefix`
- `repo_line_review_loop`
- `codegraph`
- `symbol_graph`
- `opgraph`
- `required_functionality`
- registered proof gate

### Hybrid Lane

Packetization and reconciliation:

- `hybrid_repo_review_pipeline`
- artifact-fed full-repo packet builds
- deterministic findings + graph context + LLM prompts

### Nondeterministic Lane

Candidate enrichment:

- OpenAI-compatible LLMs;
- multi-model review;
- purpose/UX/product analysis;
- fix hypotheses.

This lane cannot promote anything alone.

### Human/Owner Review Lane

Risk acceptance and policy judgment. Needed for security-like findings, dynamic refs, public API breaks,
or product-facing changes.

## 6. Confusion-Reduction Rules

- Keep long source names for context.
- Attach file/line/source excerpts to every finding.
- Attach graph context where available.
- Mark dynamic or reflection-based references unresolved.
- Use external-entrypoint shims instead of blindly renaming public contracts.
- Treat LLM output as candidate-only.
- Require proof gates before promotion.
- Prefer artifact-fed/resumable full-repo pipelines over monolithic recomputation.

## 7. Teleon Codegen

Teleon-generated code must obey this system from the first draft:

- long pyprefix names;
- purpose/input/output contract objects or docstrings;
- scalar-or-sequence primitive blocks;
- bounded loops;
- dispatch tables;
- arrays/maps over numbered scalars;
- candidate envelopes;
- deferred strict parameter typing until the shape stabilizes;
- proof-before-promotion.

This means generated code is graphable and scalable before optimization.

## 8. Current Implementation

Built now:

- `architecture/graphable_enrichable_verifiable_system.json`
- `scripts/check_graphable_enrichable_verifiable_system.py`
- `scripts/hybrid_repo_review_pipeline.py` packets with:
  - deterministic evidence;
  - graph context;
  - blast-radius hint;
  - verification lanes;
  - context policy;
  - LLM prompt.
- `architecture/teleon_codegen_contracts.json`
- `_repos/teleon/backend/src/teleon/synthesis/primitive_blocks.py`
- `architecture/combined_code_intelligence_systems.json`

Next improvements:

1. Add `symtable` binding facts to pyprefix reports.
2. Add tree-sitter/structural parser evidence for JSX/TS/HTML/CSS.
3. Add Ruff/Semgrep/mypy/Pyright/LSP adapters as normalized evidence rows.
4. Add graph queries for poor logic and blast-radius scoring.
5. Connect UI requirement nodes to backend handler paths as graph paths, not only regex checks.
