# AI Done Right — project & component template

> The portable **AI Done Right** standard. Clone this directory to start any new project — or any new
> component inside an existing one — with the same laws already installed: globally-unique naming,
> multi-path (non-commitment) development, change-verification warrants, verify-the-verifier gates,
> no-magic-values, lossless distillation, move-never-delete archival, and a per-component context
> architecture.

This is **not** a starter app. It is a set of load-bearing **laws + reference implementations** that make
every AI Done Right project read, verify, and compose the same way — so an agent (or a human) who has
worked in one project already knows how the next one is wired. The rules here are generic to *any* project;
every one is grounded in real, runnable code in the reference implementation
(`ai_harness_and_knowledge_facts_and_logic_website_sharing`), cited by path so you copy the mechanism, not
just the intent.

## What you get

- **The two headline laws**, read first:
  - **[standards/CHANGE-VERIFICATION.md](standards/CHANGE-VERIFICATION.md)** — every change carries a
    *warrant* (clear user intent · two-plus agreeing sources · an established principle). Design / brand /
    strategy / pricing / product-structure is never a unilateral single-agent call. "It's green" is
    necessary, not sufficient.
  - **[standards/LOSSLESS-DISTILLATION.md](standards/LOSSLESS-DISTILLATION.md)** — distillation is never
    replacement; every compression / promotion / LLM-to-rule conversion writes a new *versioned* layer
    while preserving raw + lineage + held-out + rejected + rollback. Omitted ≠ deleted.
- **The full laws index** — [standards/README.md](standards/README.md) links all eight: the two headline
  laws plus No Magic Values, Candidate / Truth Boundary, Verify the Verifier, Globally-Unique Naming, and
  Multi-Path Development.
- **Working reference implementations** of the mechanisms in [tools/](tools/) — adapt the bindings, keep
  the mechanism; each carries a pure `--self-test` that proves it has teeth.
- **A per-component context skeleton** you copy once per component ([context/_component-template/](context/_component-template/)).
- **A drop-in operating manual** for the new project's agents ([CLAUDE.md](CLAUDE.md)) — the same crisp,
  directive shape as the reference repo's `CLAUDE.md`, with `<PLACEHOLDER>` slots you fill.

## Layout

```
_repos/dev-rules-context/
├── README.md                      ← you are here: what this is + the bootstrap
├── CLAUDE.md                      ← portable agent operating manual (fill the <PLACEHOLDER>s)
├── FOR_CODEX.MD                   ← review brief for an agent reviewing the org
├── standards/                     ← the portable laws (one concise doc each, DO/DON'T + enforcement)
│   ├── README.md                  ← the laws index — READ FIRST, in order
│   ├── CHANGE-VERIFICATION.md     ← headline law: a warrant before every change
│   ├── LOSSLESS-DISTILLATION.md   ← headline law: distillation is never replacement
│   ├── NO-MAGIC-VALUES.md         ← single source of truth; counts are computed, never typed
│   ├── CANDIDATE-TRUTH-BOUNDARY.md← nothing promotes itself; candidate ≠ served truth
│   ├── VERIFY-THE-VERIFIER.md     ← a green suite that can't go red proves nothing
│   ├── GLOBALLY-UNIQUE-NAMING.md  ← two planes, one law: names resolve with zero ambiguity
│   ├── MULTI-PATH-DEVELOPMENT.md  ← non-commitment: a decision point is a PORTFOLIO, not an `if`
│   └── ARCHIVAL-MOVE-NEVER-DELETE.md ← superseded is moved under archive/legacy/, never deleted
├── _shared/                       ← the ONE common truth shared by every component in a project
├── context/
│   └── _component-template/       ← copy → context/<component>/ to add a component (managed separately)
├── tools/                         ← runnable reference implementations of the laws + portable org tools
│   ├── README.md
│   ├── example_portfolio_config.py  ← implements MULTI-PATH-DEVELOPMENT (portfolio + DecisionReceipt)
│   ├── example_quality_ratchet.py   ← implements VERIFY-THE-VERIFIER (computed floors + teeth)
│   ├── check_cross_repo_dependency_law.py ← portable cross-repo dependency-law CI gate
│   └── generate_repo_edges.py       ← edge-graph generator (surface-registry → per-repo EDGES + graph)
├── contracts/                     ← the single-source surface-registry.json + interface-manifest spec
├── skills/                        ← agent skills: add-new-component · check-organization · organize-and-refresh · split-repo
├── commands/                      ← slash-command briefs (find-reuse · refresh-primitives · review-session · review-output)
├── hooks/                         ← Claude Code hook briefs (pretooluse · posttooluse · stop)
├── mcp/                           ← MCP connection briefs (aidevobserver · connections)
├── prompts/                       ← portable build/spec prompts (component-specific prompts live in their component repo)
├── workflows/                     ← flywheel workflow specs (*.workflow.yaml)
├── templates/                     ← scaffold templates (api/config/docs/ingestion/proof/provider/ui/worker + schema-object mixins)
├── code-templates/                ← deterministic zero-LLM-cost processors (extract_email, validate_iban, …)
├── proofs/                        ← architectural fitness-function target tree (mirrors the product layers)
├── editor/                        ← editor integrations (aidevobserver-vscode extension)
└── examples/                      ← worked instances (migrant-worker-safety)
```

### `_shared/` vs `context/<component>/` — the per-component context architecture

The architecture separates **common truth** from **per-component context** so a project can grow to many
components without any of them drifting from the shared law:

- **`_shared/` holds the single common truth** every component in the project reads and nothing overrides:
  the shared standards statement (the two-plane naming law and boundaries stated as component laws — the
  standards docs cite this as `_repos/_shared/STANDARDS.md` in the reference repo), the canonical
  glossary, the one config module of single-source constants (No Magic Values §2), and the one id-minting
  authority (Globally-Unique Naming, plane 2). One definition here, imported everywhere.
- **`context/<component>/` holds one component's local context**, copied from `_component-template/` and
  owned by that component alone: its purpose, its `input_edge` / `output_edge` contracts, its paths
  portfolio, its proofs and their floors, and its promotion status (`candidate` → `serves_truth`). A
  component is **managed separately** — added, benchmarked, promoted, or archived on its own — while it
  still resolves every shared constant and law from `_shared/`. Adding a component is copying a skeleton and
  filling it, never editing another component.

## Bootstrap

### A. Start a NEW project from this template

1. **Copy the template as the project root.**
   ```bash
   cp -r _repos/dev-rules-context/ ../<new-project>/ && cd ../<new-project>
   ```
2. **Fill `CLAUDE.md`.** Replace every `<PLACEHOLDER>` (project name, one-line north-star, target
   vertical(s), the reference-implementation paths once they exist). Keep the laws section verbatim — it is
   the inherited standard.
3. **Seed `_shared/`** with the project's single common truth: the shared `STANDARDS.md` statement, the
   glossary, the one config module (embedding dimension, model routes, canonical paths, thresholds), and
   the one `canonical_id` minting module. Nothing project-specific belongs in a component yet.
4. **Adapt the `tools/`.** Point `example_portfolio_config.py` at your project's real decision points and
   `example_quality_ratchet.py` at your project's headline metrics; wire both `--self-test`s into a single
   `run_proofs` umbrella (Verify the Verifier). Confirm the ratchet catches a simulated regression and the
   portfolio's planned paths raise rather than silently no-op.
5. **Read [standards/README.md](standards/README.md) in order** — the two headline laws first. These now
   govern every change in the project.
6. **Install the enforcement gates** the standards name (a code-name conformance lint, a "migrated stays
   conformant" gate, a single-source id ratchet, the quality ratchet, a determinism check) and run them
   green before the first feature. A law with no gate is a suggestion.

### B. Add a NEW component to an existing project

Each component is managed separately; `_shared/` stays the common truth.

1. **Copy the skeleton** into a named, full-word component directory:
   ```bash
   cp -r context/_component-template/ context/<full-word-component-name>/
   ```
2. **Fill its local context**: purpose; the `input_edge` / `output_edge` it exposes (so agents compose by
   reading names + edges, not bodies — Globally-Unique Naming, plane 3); the paths portfolio for any
   internal decision point (Multi-Path Development); the proofs and their floors (Verify the Verifier);
   and its promotion status, born `candidate = true, serves_truth = false` (Candidate / Truth Boundary).
3. **Read shared truth from `_shared/`, never re-declare it** — import the config constants, the glossary
   terms, and the one `canonical_id`. A value that already lives in `_shared/` is never re-typed in a
   component (No Magic Values).
4. **Name every defined thing from the first draft** with the globally-unique scheme (Globally-Unique
   Naming, plane 1 for code, plane 2 for generated ids) — do not emit short names and plan a cleanup pass.
5. **Race, don't hardwire.** If the component has a real design choice (which retriever, which parser),
   express it as a portfolio behind one selector with an `ACTIVE_DEFAULT` that reproduces current behavior,
   and let receipts pick the winner (Multi-Path Development).
6. **Prove before you promote.** A component becomes `serves_truth = true` only after source review and an
   executed passing proof — never by assertion, never as a side effect of generation.
7. **Carry a warrant** proportional to blast radius on every change, and record it in the commit/ledger
   (Change Verification).
8. **Retire by moving, not deleting.** When a component is superseded, move it under `archive/legacy/`
   with a recorded status (Archival — Move, Never Delete).

### C. Push to a NEW GitHub account

No network is performed here; these are the steps the project owner runs.

1. **Confirm the tree is clean of secrets and real PII** — synthetic or public metadata only (see the
   Safety section in `CLAUDE.md`). Never commit keys.
2. **Initialize and make the first commit** with a warrant citation in the message:
   ```bash
   git init
   git add -A
   git commit -m "chore: bootstrap <new-project> from AI Done Right template

   warrant: principle — inherits template-repo standards"
   ```
3. **Create the empty repository under the new account** (via that account's `gh auth login` or the web
   UI), then set the remote and push:
   ```bash
   git remote add origin git@github.com:<new-account>/<new-project>.git
   git branch -M main
   git push -u origin main
   ```
4. **Do not republish `_reference/`** or any borrowed corpus; keep the new repo to your own work plus this
   portable template.
5. **Keep the laws index and `CLAUDE.md` at the repo root** so the next agent that opens the project
   inherits the standard on the first read.

## The one rule behind all of it

Reuse before you build. Before adding any component, server, engine, or "new" layer, check it does not
already exist in `_shared/`, in another component, or in the reference implementation. *"This already
exists, don't rebuild it"* is the highest-ROI decision in the architecture — the globally-unique naming law
exists precisely so that check resolves exactly.
