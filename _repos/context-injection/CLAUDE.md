# CLAUDE.md — `aidoneright-context-injection` agent operating manual

> Filled from the portable **AI Done Right** operating template
> (`../dev-rules-context/CLAUDE.md`). It is the agent operating layer; the laws it inherits live in
> [`../dev-rules-context/standards/`](../dev-rules-context/standards/README.md) and win if this file ever
> disagrees with them. The laws section below is inherited verbatim — do not weaken it.

## Project

- **Name:** `aidoneright-context-injection`
- **Kind:** DEV TOOL (reusable infrastructure, product-neutral).
- **North star (one line):** The **"context is everything" plumbing** — assemble, pack, compress, and
  inject the right context into every agent prompt (context packs, headroom compression,
  retrieval-into-prompt).
- **What this repo exposes (its published interface):** `context-pack-builder`, `memory-store`,
  `prompt-composer`, `headroom-compressor`, `retrieval-injector`. Keep these stable — the surfaces below
  depend on them.
- **Depth before breadth:** the ONE thing proven here is a bounded, lineage-preserving context pack that
  fits the budget and lifts the model. Serve the surfaces that consume it — `teleon`, `baltor`,
  `aidevobserver`, `aidoneright` — before adding a composition mode no consumer has asked for. Breadth of
  packers without a consuming surface is the failure mode.
- **Reference implementation for the standards:** `../dev-rules-context/` (standards + gates) and this
  repo's own `context/` + `EDGES.md`.
- **Common truth for all components:** [`../dev-rules-context/_shared/`](../dev-rules-context/_shared/) —
  the shared standards statement, the glossary, the single-source config, and the id-minting authority.
  Read from there; never re-declare what already lives there.

## Read first

1. [`../dev-rules-context/standards/README.md`](../dev-rules-context/standards/README.md) — the laws
   index, in order (the two headline laws first).
2. This file — the operating layer.
3. `EDGES.md` — this repo's cross-repo contracts (its neighbors' published edges, never their internals).
4. The component you are touching under `context/<component>/` (its purpose, edges, paths, proofs, status).

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
    tools/check_*.py, _shared/*.
  - `shared-backend-components` (`aidoneright-shared-backend-components`) — registry, primitives, codegraph,
    eval-harness, storage-tiers, credential-plane.
- **Who consumes you (keep these interfaces stable):** `aidevobserver`, `aidoneright`, `baltor`, `teleon`.

Consume a neighbor ONLY through the `exposes` list above — never read or import its source.

## Default fast path

- Change one thing; validate and index **only the changed paths**; run the umbrella `run_proofs`; do not
  start with a full rebuild.
- **Reuse-first.** Before building any packer, memory store, composer, or compressor, check it does not
  already exist in this repo's `context/` or in `shared-backend-components`. *"This already exists, don't
  rebuild it"* is the highest-ROI decision.
- **Audit neighbors before and after a code change.** A green suite says the code runs; the dependency
  graph says what else the change can break — four surfaces consume this repo.

## Adding work

- **A new composition / compression strategy** = a new path behind the selector (§1), preserving lineage
  and source handles under lossless distillation (§7). Compression may shrink the text surface only if
  answer-critical facts + source handles + held-out warnings survive.
- **A new decision point** (which pack shape, which budget) = a portfolio behind one selector (§1), not an
  `if`.
- **A new generated id** = one call to the shared `canonical_id` (§2).

## Safety and scope

- **No real PII, secrets, confidential data, or proprietary dumps** in the `memory-store` or any pack.
  Synthetic or public metadata only. Never commit keys.
- **Tenant-private lineage never becomes global** (§7) — a context pack assembled for one tenant does not
  leak into a shared or global pack.
- **Sensitive domains** get review queues, verified facts, signed publishers, redaction, provenance, and
  deterministic gates — not "just ask the model."
- **Insurance pipelines are restricted** — do not add or expand insurance-related context flows.

## When stuck

If one path is blocked, switch paths — do not stop. Add proofs, readiness/audit tooling, a new
composition/compression strategy, or documentation that prevents a repeated slow or wrong path. Every
serious turn improves at least one durable thing.
