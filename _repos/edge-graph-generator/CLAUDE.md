# CLAUDE.md — `aidoneright-edge-graph-generator` agent operating manual

> Filled from the portable **AI Done Right** operating template
> (`../dev-rules-context/CLAUDE.md`). It is the agent operating layer; the laws it inherits live in
> [`../dev-rules-context/standards/`](../dev-rules-context/standards/README.md) and win if this file ever
> disagrees with them. The laws section below is inherited verbatim — do not weaken it.

## Project

- **Name:** `aidoneright-edge-graph-generator`
- **Kind:** META DEV TOOL — reads contracts, generates cross-repo awareness. Reads **interface manifests
  only, never any repo's source**.
- **North star (one line):** Read the surface registry + each repo's published interface and **generate**
  per-repo edge digests + the global dependency graph, so every repo is **edge-aware, not
  everything-aware**.
- **What this repo exposes (its published interface):** `per-repo-edge-digest`, `repo-dependency-graph`,
  `surface-registry-validator`, `interface-manifest-validator`. Keep these stable — every repo in the org
  consumes them.
- **Depth before breadth:** the ONE thing proven here is that a session in repo X loads X plus its
  neighbors' EDGES and nothing of their internals. Serve the whole org (every surface consumes this) by
  keeping the digest correct and in sync with the registry — not by adding output formats nobody reads.
- **Reference implementation for the standards:** `../dev-rules-context/` (standards + gates) and this
  repo's own `context/` + `EDGES.md` + its three scripts.
- **Common truth for all components:** [`../dev-rules-context/_shared/`](../dev-rules-context/_shared/) —
  the shared standards statement, the glossary, the single-source config, and the id-minting authority.
  The single source of truth this tool reads is
  `../dev-rules-context/contracts/surface-registry.json`. Read from there; never re-declare it.

## Read first

1. [`../dev-rules-context/standards/README.md`](../dev-rules-context/standards/README.md) — the laws
   index, in order (the two headline laws first).
2. This file — the operating layer.
3. `EDGES.md` — this repo's own cross-repo contracts.
4. The registry it reads: `../dev-rules-context/contracts/surface-registry.json` (the single source of
   truth for every surface, its `exposes`, and its allowed/forbidden edges).

## The inherited laws (do not weaken; each links its full standard)

### 1. Non-commitment / multi-path is the default — [MULTI-PATH-DEVELOPMENT](../dev-rules-context/standards/MULTI-PATH-DEVELOPMENT.md)
Never hardwire one strategy where several are viable. A design choice is a **portfolio of
contract-substitutable paths behind one selector**, not an `if`. The current behavior is *one selectable
path* (`ACTIVE_DEFAULT`) that reproduces today exactly — adopting the portfolio replaces nothing. Adding a
strategy is a new row + a resolver entry, never a rewrite. Race every path on the **same input** via a fair
comparator, rank by **measured receipts** (cost + accuracy + budget), keep the losers as labelled
fallbacks, and re-benchmark to re-adapt. A candidate is **never** served as truth by the race.

### 2. Globally-unique naming — [GLOBALLY-UNIQUE-NAMING](../dev-rules-context/standards/GLOBALLY-UNIQUE-NAMING.md)
Code here is read by AI first. Every defined thing gets a **globally-unique, location-derived,
meaning-bearing** name so the name alone resolves it with zero ambiguity — long names are good (context the
model uses). Two planes, one law: **code objects** follow the `py_<kind>__<file>__<scope>__<name>` scheme;
**generated data ids** are minted only through the one `canonical_id(prefix, *parts)` authority over
canonical bytes. **Version lives in `schema_version` metadata — never in a name or id** (no `.vN`, no
`@N`). New / generated code follows the scheme from the first draft. User-facing names are full words, no
abbreviations, and records name their `input_edge` / `output_edge` so agents compose by reading names +
edges, not bodies.

### 3. Candidate / truth boundary — [CANDIDATE-TRUTH-BOUNDARY](../dev-rules-context/standards/CANDIDATE-TRUTH-BOUNDARY.md)
Every generated row is **born `candidate = true, serves_truth = false`**. Generation is not promotion.
Keep generated / staged / load-ready / promotion-ready / committed / search-ready as **distinct counts** —
never report raw generated lines as active components. A row becomes served truth only after **source
review + an executed passing proof + the gates**. Nothing promotes itself; no demo, model, or agent flips
the bit by assertion.

### 4. Change verification — a warrant before every change — [CHANGE-VERIFICATION](../dev-rules-context/standards/CHANGE-VERIFICATION.md)
Every change carries a **warrant**, cited in the commit and ledger, in one of three forms:
`warrant: user-intent — "<quote>"` · `warrant: corroboration — <≥2 independent sources>` ·
`warrant: principle — <which>`. Match it to the blast radius: **design / brand / strategy / vocabulary /
pricing / product-structure is NEVER a unilateral single-agent call** — it needs clear user intent or
strong corroboration. "It's green" is necessary, not sufficient. Supersede stale artifacts in the **same**
change; re-verify any doc/memory before relying on it; a different agent verifies than builds.

### 5. Verify the verifier — [VERIFY-THE-VERIFIER](../dev-rules-context/standards/VERIFY-THE-VERIFIER.md)
A green suite that cannot go red proves nothing. Every verifier ships (a) a **mutation gate** — a real
injected defect makes it go red (a pure `--self-test`); (b) a **determinism gate** — the artifact builds
**byte-identical** twice; (c) a **quality ratchet** — each headline metric is a **floor computed from a
manifest** (never hand-typed), a regression below it is a hard failure, and an unsupplied external metric
is a gap record, not a fabricated pass. Never seed a reproducible harness with `hash()`; run edit/restore
harnesses under `PYTHONDONTWRITEBYTECODE=1`. Wire every `--self-test` into one `run_proofs` umbrella.

### 6. No magic values — single source of truth — [NO-MAGIC-VALUES](../dev-rules-context/standards/NO-MAGIC-VALUES.md)
Never hand-type a value used in more than one place; at scale a value typed twice is a value that drifts.
Repo-state numbers (counts, totals, versions, build dates) are **computed from the source of truth**, never
typed into prose. One definition, many readers; build strings from the constant
(`f"vector({DEFAULT_SCHEMA_DIMENSIONS})"`), never a parallel literal. Canonical lists live in
`vocabularies/` / `schemas/`, not re-enumerated in code. Where a value must be mirrored, add a CI check
that recomputes both sides and fails on drift.

### 7. Lossless distillation — distillation is never replacement — [LOSSLESS-DISTILLATION](../dev-rules-context/standards/LOSSLESS-DISTILLATION.md)
Any distillation, decomposition, compression, optimization, reconciliation, promotion, or
LLM-to-deterministic-rule conversion creates a new **versioned** derived layer while **preserving** the raw
layer, intermediates, lineage, source handles, held-out items, rejected candidates, model/tool traces,
configs, and a rollback target. Omitted ≠ deleted; held-out ≠ forgotten; rejected ≠ erased; superseded ≠
deleted. Run side-by-side before promotion, shadow new rules, and prove rehydration. Tenant-private lineage
never becomes global.

### 8. Archival — move, never delete; never untrack — [ARCHIVAL-MOVE-NEVER-DELETE](../dev-rules-context/standards/ARCHIVAL-MOVE-NEVER-DELETE.md)
Outdated context is **moved, not deleted, and not untracked** — relocated under
`archive/legacy/<original-path>`, kept in git for lineage, with a **mandatory status label** recorded in
the manifest and status index. Archived files leave the model context but stay on disk. Restore is a
`git mv`. Never mislabel live or generated data as "legacy."

## This repo's edges (from `EDGES.md` / the surface registry)

- **You may consume (via their published interface only):**
  - `dev-rules-context` (`aidoneright-dev-rules-context`) — standards/*, contracts/surface-registry.json,
    tools/check_*.py, _shared/*. **This tool reads `contracts/surface-registry.json` (and each repo's
    published interface manifest) — contracts only, never any repo's source.**
- **Who consumes you (keep these interfaces stable):** every surface —
  `aidoneright`, `teleon`, `baltor`, `aidevobserver`, `shared-backend-components`, `openhubforai`,
  `api-endpoint-wrappers`, `scraping`, `context-injection`, `business-context`.

Because the whole org depends on this tool's output, a change to the digest/graph format or the checker is
high blast radius — carry a warrant (§4) and keep output byte-deterministic (§5).

## The three scripts

- `generate_repo_edges.py` — turns the surface registry into per-repo `*.EDGES.md` digests + `*.edges.json`
  + the global `graph.json` / `GRAPH.md`. Offline, deterministic, `--self-test`-able. Reads contracts only.
- `check_cross_repo_dependency_law.py` — the portable enforcement of the registry: every `may_depend_on`
  points at a real surface and is not a forbidden edge, the graph is acyclic, and a repo's declared
  `--consumes` is neither forbidden nor undeclared. Offline, deterministic, `--self-test`-able.
- `interface_manifests.py` — generate + check each repo's versioned `interface.json` (the
  `interface-manifest-validator`): every consumed capability is one the provider EXPOSES and every consumed
  provider is in the surface's `may_depend_on`. Offline, deterministic, `--self-test`-able.

`generate_repo_edges.py` and `check_cross_repo_dependency_law.py` default their registry path to a sibling
`contracts/` dir; from this repo pass `--registry ../dev-rules-context/contracts/surface-registry.json`
explicitly. `interface_manifests.py` resolves the shared registry directly (no `--registry`). See the
README for exact commands.

## Default fast path

- Change one thing; run the three scripts' `--self-test`; do not start with a full regeneration.
- **Reuse-first.** The registry is the single source of truth — never hand-maintain an edge that the
  generator can compute from it. *"This already exists, don't rebuild it"* — the whole point of this tool.
- **The registry is the single source of truth (§6).** Never hand-type an edge, count, or `exposes` list
  that the registry already holds; regenerate digests from it and let the checker fail on drift.

## Adding work

- **A new output format or digest field** = a new path behind the generator's selector (§1), byte-
  deterministic (§5), with a `--self-test` mutation gate wired into `run_proofs`.
- **A new invariant** = a check in `check_cross_repo_dependency_law.py` with a `--self-test` that a real
  injected violation makes go red (§5).
- **A registry change** (new surface / edge) lives in `dev-rules-context`, not here — this tool only reads
  it. Regenerate every repo's `EDGES.md` after a registry change so no digest goes stale (§4).

## Safety and scope

- **Reads contracts only, never any repo's source.** That boundary is what makes "edge-aware, not
  everything-aware" real — do not add a code-reading path.
- **No real PII, secrets, or proprietary dumps.** The registry holds public surface metadata only.
- **Insurance pipelines are restricted** — not applicable to this meta-tool, but do not add
  insurance-specific surfaces to the registry here.

## When stuck

If regeneration or a check is blocked, switch paths — do not stop. Add a `--self-test` mutation gate,
tighten an invariant, make the output more deterministic, or document the exact command that was slow or
wrong. Every serious turn improves at least one durable thing.
