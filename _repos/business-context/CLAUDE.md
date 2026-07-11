# CLAUDE.md — `aidoneright-business-context` agent operating manual

> Filled from the portable **AI Done Right** operating template
> (`../dev-rules-context/CLAUDE.md`). It is the agent operating layer; the laws it inherits live in
> [`../dev-rules-context/standards/`](../dev-rules-context/standards/README.md) and win if this file ever
> disagrees with them. The laws section below is inherited verbatim — do not weaken it.

## Project

- **Name:** `aidoneright-business-context`
- **Kind:** CONTEXT repo — **no product code**. Business memory, read by humans and agents for grounding,
  never imported as code.
- **North star (one line):** The durable **business memory** — decisions (with warrants), activity log,
  analytics, MCP configs, and strategy notes — that every surface can reference, kept separate from
  product code.
- **What this repo exposes (its published interface):** `decisions-ledger`, `activity-log`, `analytics`,
  `mcp-configs`, `business-notes`. Keep these stable — the surfaces below reference them.
- **Depth before breadth:** the ONE thing proven here is a trustworthy decisions ledger where every
  decision carries a warrant. Serve the surfaces that reference it — `aidoneright`, `teleon`, `baltor`,
  `aidevobserver` — before broadening into notes no surface consults. Notes nobody grounds on are the
  failure mode.
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
4. The area you are touching under `context/<area>/` (its purpose, edges, status).

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
- **Who consumes you (keep these interfaces stable):** `aidoneright`, `teleon`, `baltor`, `aidevobserver`.

This repo is **context-only, with no product code**. It carries no dependency on the substrate or any
product; it is *read* for grounding, never *imported* as code. Consume `dev-rules-context` ONLY through its
`exposes` list — never read or import its source.

## Default fast path

- Add or update one note / decision / ledger entry; validate only the changed paths; do not start with a
  full rebuild.
- **Reuse-first.** Before adding a note, check the decision or fact is not already recorded — a
  contradicting duplicate is worse than a gap. *"This already exists, don't rebuild it"* applies to
  business memory too.
- When a new decision supersedes an old one, **update or archive the stale entry in the same change** (§4,
  §8) — no orphaned contradictions in the ledger.

## Adding work

- **A new decision** = a `decisions-ledger` entry that **carries its warrant** (§4: user-intent quote,
  ≥2 corroborating sources, or a named principle). Design / brand / strategy / pricing decisions need clear
  user intent or strong corroboration — never a unilateral single-agent call.
- **A new note / analytics / MCP config** = added under its area in `context/`, dated, with its source.
- **A superseded decision** = updated in place or moved to `archive/legacy/` with a status label (§8),
  never deleted.

## Safety and scope

- **No real PII, secrets, confidential financials, or proprietary dumps.** Synthetic or public metadata
  only. Never commit keys or credentials into notes or MCP configs.
- **Context-only, no product code.** Nothing here is importable; surfaces reference it for grounding.
- **Sensitive domains** get review queues, verified facts, provenance, and deterministic gates — not "just
  ask the model."
- **Insurance pipelines are restricted** — do not add or expand insurance-related business flows.

## When stuck

If one note or source is blocked, switch paths — do not stop. Record a decision with its warrant, update an
activity-log entry, reconcile a stale contradiction, or add documentation that prevents a repeated wrong
path. Every serious turn improves at least one durable piece of business memory.
