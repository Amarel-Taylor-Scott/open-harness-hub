# CLAUDE.md — `<PROJECT_NAME>` agent operating manual

> Portable **AI Done Right** operating template. Copy it to a new project's root and fill every
> `<PLACEHOLDER>`. It is the agent operating layer; the laws it inherits live in
> [`standards/`](standards/README.md) and win if this file ever disagrees with them. Keep the laws section
> verbatim — it is the inherited standard, not project-specific prose.

## Project

- **Name:** `<PROJECT_NAME>`
- **North star (one line):** `<ONE_LINE_NORTH_STAR>`
- **Target vertical(s) — depth before breadth:** `<VERTICAL_1>` (`<VERTICAL_2>` …). Every new layer must
  serve the ONE vertical being proven to a real user; breadth without a proven vertical is the failure mode.
- **Reference implementation for the standards:** `<REFERENCE_REPO_OR_THIS_REPO_PATHS>`.
- **Common truth for all components:** [`_shared/`](_shared/) — the shared standards statement, the
  glossary, the one config module of single-source constants, and the one id-minting authority. Read from
  here; never re-declare what already lives here.

## Read first

1. [`standards/README.md`](standards/README.md) — the laws index, in order (the two headline laws first).
2. This file — the operating layer.
3. The component you are touching: `context/<component>/` (its purpose, edges, paths, proofs, status).

## The inherited laws (do not weaken; each links its full standard)

### 1. Non-commitment / multi-path is the default — [MULTI-PATH-DEVELOPMENT](standards/MULTI-PATH-DEVELOPMENT.md)
Never hardwire one strategy where several are viable. A design choice is a **portfolio of
contract-substitutable paths behind one selector**, not an `if`. The current behavior is *one selectable
path* (`ACTIVE_DEFAULT`) that reproduces today exactly — adopting the portfolio replaces nothing. Adding a
strategy is a new row + a resolver entry, never a rewrite. Race every path on the **same input** via a fair
comparator, rank by **measured receipts** (cost + accuracy + budget), keep the losers as labelled
fallbacks, and re-benchmark to re-adapt. A candidate is **never** served as truth by the race.

### 2. Globally-unique naming — [GLOBALLY-UNIQUE-NAMING](standards/GLOBALLY-UNIQUE-NAMING.md)
Code here is read by AI first. Every defined thing gets a **globally-unique, location-derived,
meaning-bearing** name so the name alone resolves it with zero ambiguity — long names are good (context the
model uses). Two planes, one law: **code objects** follow the `py_<kind>__<file>__<scope>__<name>` scheme;
**generated data ids** are minted only through the one `canonical_id(prefix, *parts)` authority over
canonical bytes. **Version lives in `schema_version` metadata — never in a name or id** (no `.vN`, no
`@N`). New / generated code follows the scheme from the first draft. User-facing names are full words, no
abbreviations, and records name their `input_edge` / `output_edge` so agents compose by reading names +
edges, not bodies.

### 3. Candidate / truth boundary — [CANDIDATE-TRUTH-BOUNDARY](standards/CANDIDATE-TRUTH-BOUNDARY.md)
Every generated row is **born `candidate = true, serves_truth = false`**. Generation is not promotion.
Keep generated / staged / load-ready / promotion-ready / committed / search-ready as **distinct counts** —
never report raw generated lines as active components. A row becomes served truth only after **source
review + an executed passing proof + the gates**. Nothing promotes itself; no demo, model, or agent flips
the bit by assertion.

### 4. Change verification — a warrant before every change — [CHANGE-VERIFICATION](standards/CHANGE-VERIFICATION.md)
Every change carries a **warrant**, cited in the commit and ledger, in one of three forms:
`warrant: user-intent — "<quote>"` · `warrant: corroboration — <≥2 independent sources>` ·
`warrant: principle — <which>`. Match it to the blast radius: **design / brand / strategy / vocabulary /
pricing / product-structure is NEVER a unilateral single-agent call** — it needs clear user intent or
strong corroboration. "It's green" is necessary, not sufficient. Supersede stale artifacts in the **same**
change; re-verify any doc/memory before relying on it; a different agent verifies than builds.

### 5. Verify the verifier — [VERIFY-THE-VERIFIER](standards/VERIFY-THE-VERIFIER.md)
A green suite that cannot go red proves nothing. Every verifier ships (a) a **mutation gate** — a real
injected defect makes it go red (a pure `--self-test`); (b) a **determinism gate** — the artifact builds
**byte-identical** twice; (c) a **quality ratchet** — each headline metric is a **floor computed from a
manifest** (never hand-typed), a regression below it is a hard failure, and an unsupplied external metric
is a gap record, not a fabricated pass. Never seed a reproducible harness with `hash()`; run edit/restore
harnesses under `PYTHONDONTWRITEBYTECODE=1`. Wire every `--self-test` into one `run_proofs` umbrella.

### 6. No magic values — single source of truth — [NO-MAGIC-VALUES](standards/NO-MAGIC-VALUES.md)
Never hand-type a value used in more than one place; at scale a value typed twice is a value that drifts.
Repo-state numbers (counts, totals, versions, build dates) are **computed from the source of truth**, never
typed into prose. One definition, many readers; build strings from the constant
(`f"vector({DEFAULT_SCHEMA_DIMENSIONS})"`), never a parallel literal. Canonical lists live in
`vocabularies/` / `schemas/`, not re-enumerated in code. Where a value must be mirrored, add a CI check
that recomputes both sides and fails on drift.

### 7. Lossless distillation — distillation is never replacement — [LOSSLESS-DISTILLATION](standards/LOSSLESS-DISTILLATION.md)
Any distillation, decomposition, compression, optimization, reconciliation, promotion, or
LLM-to-deterministic-rule conversion creates a new **versioned** derived layer while **preserving** the raw
layer, intermediates, lineage, source handles, held-out items, rejected candidates, model/tool traces,
configs, and a rollback target. Omitted ≠ deleted; held-out ≠ forgotten; rejected ≠ erased; superseded ≠
deleted. Run side-by-side before promotion, shadow new rules, and prove rehydration. Tenant-private lineage
never becomes global.

### 8. Archival — move, never delete; never untrack — [ARCHIVAL-MOVE-NEVER-DELETE](standards/ARCHIVAL-MOVE-NEVER-DELETE.md)
Outdated context is **moved, not deleted, and not untracked** — relocated under
`archive/legacy/<original-path>`, kept in git for lineage, with a **mandatory status label** recorded in
the manifest and status index. Archived files leave the model context but stay on disk. Restore is a
`git mv`. Never mislabel live or generated data as "legacy."

## Default fast path

- Change one thing; validate and index **only the changed paths**; run the umbrella `run_proofs`; do not
  start with a full rebuild. If a full rebuild is slow, capture the bottleneck and improve the incremental
  path — do not keep repeating the slow one.
- **Reuse-first.** Before building any component, server, engine, or "new" layer, check it does not already
  exist in `_shared/`, in another `context/<component>/`, or in the reference implementation. *"This already
  exists, don't rebuild it"* is the highest-ROI decision here — and the naming law (§2) exists so that check
  resolves exactly.
- **Audit neighbors before and after a code change.** Before and after editing a symbol, check what depends
  on it and update load-bearing neighbors in the **same** change — a green suite says the code runs; the
  dependency graph says what else the change can break.

## Adding work

- **A new component** = copy `context/_component-template/` → `context/<full-word-name>/`, fill its purpose
  / edges / paths / proofs / status, and read every shared constant from `_shared/`. Managed separately;
  never edit another component to add one.
- **A new decision point** = a portfolio (§1), not an `if`.
- **A new generated id** = one call to the shared `canonical_id` (§2), stamped `candidate = true` (§3).
- **A new frontend↔backend integration** = a service + a same-origin seam + `fetch('/api/<x>/...')`, never
  a hardcoded host and never a static stub over a rich app.

## Safety and scope

- **No real PII, secrets, confidential data, or proprietary dumps.** Synthetic or public metadata only.
  Never commit keys. Do not republish `_reference/`.
- **Sensitive domains** get review queues, verified facts, signed publishers, redaction, provenance, and
  deterministic gates — not "just ask the model."
- `<PROJECT_SPECIFIC_RESTRICTED_DOMAINS>` — do not expand restricted-domain examples.

## When stuck

If one path is blocked, switch paths — do not stop. Generate proofs, add readiness/audit tooling, add
source-surface seeds, add repair planners for missing pieces, or add documentation that prevents a repeated
slow or wrong path. Do not stop because one scraper, API, provider, or full rebuild is slow. Every serious
turn improves at least one durable thing.
