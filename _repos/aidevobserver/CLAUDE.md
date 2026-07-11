# CLAUDE.md — `aidoneright-aidevobserver` agent operating manual

> Operating manual for this repo (the future `aidoneright-aidevobserver` package — the AI-usage layer).
> It is the agent operating layer; the laws it inherits live in
> [`../dev-rules-context/standards/`](../dev-rules-context/standards/README.md) and win if this file ever
> disagrees with them. The laws section below is the inherited standard — kept verbatim, links repointed to
> the sibling `dev-rules-context` repo. Work inside this repo's own context (`context/`) + its published
> edges (`EDGES.md`); a session opening ONLY this folder needs nothing else.

## Project

- **Name:** `aidoneright-aidevobserver`
- **North star (one line):** the AI-usage layer — watch how intelligence is used in real AI coding
  sessions and coach on it (session **review**, not code review), surfacing every finding as governed
  **candidate** advice a human triages, never as served truth.
- **Target vertical(s) — depth before breadth:** AI coding sessions / AI-usage coaching (the **POST-session
  review report** is the lead adoption wedge; the **WHILE-session** pop-ups — reinvention / adversarial
  question / cheaper path / token waste — are the second surface, governed by a global interruption budget).
  Every new module must serve that one proven wedge; breadth of detectors without an adopted review report
  is the failure mode.
- **Reference implementation for the standards:** the engine lives **inside the Teleon package** in the
  reference repo — `src/teleon/observer/` (router · review · capture · session_store · sessions · agentic ·
  consent · registry_search), `src/teleon/knowledge/` (dependency/product/repo/genome graphs),
  `src/teleon/economics/` (cost/waste). Surfaces: `scripts/observer_local_service.py` (HTTP backend),
  `scripts/aidevobserver_mcp_server.py` (MCP), `src/teleon/observer/cli.py` (CLI),
  `editor/aidevobserver-vscode/` (extension), `web/aidevobserver/` (SPA). See `context/blackbox.md`.
- **Common truth for all components:** [`../dev-rules-context/_shared/`](../dev-rules-context/_shared/) —
  the shared standards statement, the glossary, the one config module of single-source constants, and the
  one id-minting authority. Read from here; never re-declare what already lives here.

## Read first

1. [`../dev-rules-context/standards/README.md`](../dev-rules-context/standards/README.md) — the laws index,
   in order (the two headline laws first).
2. This file — the operating layer.
3. This repo's own context: `context/blackbox.md` (what this component internally is/owns/does),
   `context/edges.md` (how it connects to the other five components + `_shared`), and `EDGES.md` (the
   generated cross-repo edge contract). Deeper docs: `context/codex/` and `context/design/`.

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

## The invariants that make this repo AIDevObserver (never weaken — from `context/edges.md`)

These are this component's non-negotiable contracts. The other five components depend on them; break one and
the portfolio breaks.

- **It reviews AI USAGE / the session, NOT the code.** It is not a PR/diff/code-correctness reviewer. Two
  moments: **POST** (a post-session review report — the wedge) and **WHILE** (intra-session pop-ups under a
  global interruption budget, failing open to silence). Do not reframe it as code/PR review.
- **Candidate-only invariant.** Every finding and every seam / CLI / MCP response carries
  `serves_truth=false`. AIDevObserver **proposes**; Teleon proof/promotion and Baltor governance **dispose**.
  No surface, demo, model, or agent may emit truth.
- **Read-only + privacy invariant.** Never store or republish raw transcripts, absolute local paths, or
  evidence snippets; footgun evidence stays redacted (`<redacted match>`); `consent.py` is **gate #0** for
  any retention (default-deny, granular, revocable, time-bounded, redaction-always); revoke-and-delete
  propagates.
- **Dependency-law invariant.** The engine lives in `src/teleon/` → for the import checker it **IS Teleon**
  and inherits Teleon's constraints: it may consume OpenHubForAI and the Backend registry, but **no
  `src/teleon/observer/**` (or `knowledge/` / `economics/`) file — nor its tooling under `scripts/` /
  `editor/` — may ever import Baltor.** The only path to Baltor is
  `observation → Teleon proof/promotion → Baltor-governed truth`, never direct.
- **Restraint invariant — the product is the threshold.** The global interruption budget + graduated modes
  (silent_record → review_only → advisory → active → enforcing) + per-type floors are load-bearing. Do not
  add detectors that erode them; a tool that won't shut up is the anti-product.
- **Reuse the engine, never rebuild it in a surface.** All surfaces go through `src/teleon/observer/` and
  `registry_search.py` — review = `route_session(mode="review_only")`, live = `route_session`, intake =
  `capture.from_transcript`, discovery = `sessions.discover_sessions`. Serve the built-out `web/aidevobserver/`
  app via the showcase over the `/api/observer/` seam; never a skinny replacement server (a page that renders
  but 501s on `/api/observer/*` is not done).

## The seam (keep stable — from `EDGES.md` / `context/edges.md`)

- **This repo exposes:** `/api/observer`, session-review, mcp-server, cli, extension.
- **Seam:** the web frontend never hardcodes a host — it calls same-origin **`/api/observer/...`**; the
  showcase rewrites it. Registry id `observer_runtime`; cloud override `OH_SEAM_OBSERVER_BASE`; the strip is
  **`""`** (full path forwarded, so the service answers both `/review` and `/api/observer/review`); the port
  is **single-sourced** from `architecture/local_service_registry.json` (never hardcode it).

## Cross-repo edges (from `EDGES.md` — consume via published interface ONLY)

- **You may consume:** `dev-rules-context` (`aidoneright-dev-rules-context`) → `standards/*`,
  `contracts/surface-registry.json`, `tools/check_*.py`, `_shared/*`; **shared-backend-components**
  (`aidoneright-shared-backend-components`) → registry, primitives, primitive templates, codegraph,
  eval-harness, storage-tiers, credential-plane (this is the reinvention-grounding + reuse-card source — the moat);
  **openhubforai** (`aidoneright-openhubforai`) → CapabilityTask spec, task/pipeline templates,
  eval harnesses, conformance tests, and skills.
- **Who consumes you (keep stable):** `aidoneright` (the parent).
- Consume a neighbor ONLY via its exposed interface listed in `EDGES.md` — never read or import its source.

## Default fast path

- Change one thing; validate and index **only the changed paths**; run the umbrella `run_proofs`; do not
  start with a full rebuild. If a full rebuild is slow, capture the bottleneck and improve the incremental
  path — do not keep repeating the slow one.
- **Reuse-first.** Before building any component, server, engine, or "new" layer, check it does not already
  exist in `../dev-rules-context/_shared/`, in this repo's `context/`, or in the reference implementation
  (`src/teleon/observer/`, `src/teleon/knowledge/`, `src/teleon/economics/`, the five surfaces). *"This
  already exists, don't rebuild it"* is the highest-ROI decision here — and the naming law (§2) exists so
  that check resolves exactly. AIDevObserver's own reinvention guard is the product's core; apply it to your
  own work.
- **Audit neighbors before and after a code change.** Before and after editing a symbol, check what depends
  on it and update load-bearing neighbors in the **same** change — a green suite says the code runs; the
  dependency graph says what else the change can break.

## Adding work

- **A new detector / intervention module** = a typed module the router wakes, reading its patterns from the
  single-sourced `architecture/behavioral_heuristics.json` (no magic values), grounded against the registry
  via `registry_search.py`, respecting the per-type floor + global interruption budget. Never add a module
  that erodes restraint.
- **A new decision point** = a portfolio (§1), not an `if`.
- **A new generated id** = one call to the shared `canonical_id` (§2), stamped `candidate = true` (§3).
- **A new frontend↔backend integration** = a service + the same-origin `/api/observer/...` seam +
  `fetch('/api/observer/...')`, never a hardcoded host and never a static stub over the rich app.

## Safety and scope

- **No real PII, secrets, confidential data, or proprietary dumps.** Synthetic or public session text only.
  Never commit keys. Do not republish `_reference/` or any raw transcript.
- **Sensitive domains** get review queues, verified facts, redaction, provenance, and deterministic gates —
  not "just ask the model." Footgun evidence stays redacted; consent gate #0 governs retention.
- **Stay away from insurance-related pipelines** in new work; do not expand any legacy insurance examples.

## When stuck

If one path is blocked, switch paths — do not stop. Generate proofs, add readiness/audit tooling, add
source-surface seeds, add repair planners for missing pieces, or add documentation that prevents a repeated
slow or wrong path. Do not stop because one scraper, API, provider, or full rebuild is slow. Every serious
turn improves at least one durable thing.
