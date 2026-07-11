# CLAUDE.md — `aidoneright-parent` agent operating manual

> The **AI Done Right** operating manual for this repo (`_repos/aidoneright/`, canonical id
> `aidoneright-parent`). It is the agent operating layer; the laws it inherits live in
> [`../dev-rules-context/standards/`](../dev-rules-context/standards/README.md) and win if this file ever
> disagrees with them. Keep the laws section verbatim — it is the inherited standard, not project-specific
> prose. Grounding for this repo: `context/blackbox.md` (what the parent owns), `context/edges.md` and
> `EDGES.md` (how it connects).

## Project

- **Name:** `aidoneright-parent` — the PARENT BRAND / portfolio umbrella (display brand **AI Done Right**,
  domain `aidoneright.dev`, tagline **"AI, done right."**; stable code slug / company id stays
  `contextiseverything`).
- **North star (one line):** Be the parent brand and portfolio umbrella that turns open, discoverable AI
  building blocks into **governed, evidence-backed capability** — a house of brands that owns the brands,
  standards, shared research/security/governance, and the design system, but **owns no runtime code and no
  customer data** (thesis across every property: *discovery is not trust*).
- **Target surface(s) — depth before breadth:** the **parent portfolio / house-of-brands site**
  (`web/context-is-everything/`, the "AI Done Right" landing + portfolio index) and the **Demo Control
  Tower** (the operator "Start Here" console indexing every site, demo, dashboard, and hub). Prove the
  branded-house narrative on these owned surfaces before adding breadth; the parent adds no product logic.
- **Reference implementation for the standards:** the design prototype bundle `dist/sites/aidoneright-design/`
  (start `START-HERE-CLAUDE-CODE.md`) and the live app `web/context-is-everything/` in the main repo; the
  Claude Design family handoff `docs/design/aidoneright-claude-design/`.
- **Common truth for all components:** [`../_shared/`](../_shared/) — the shared standards statement, the
  glossary, the architecture map (`ARCHITECTURE-MAP.md`, parent = component #1), and the single-source
  constants. Read from here; never re-declare what already lives here.

## Read first

1. [`../dev-rules-context/standards/README.md`](../dev-rules-context/standards/README.md) — the laws index,
   in order (the two headline laws first).
2. This file — the operating layer.
3. This repo's own context: `context/blackbox.md` (what the parent is and owns), `context/edges.md` +
   `EDGES.md` (inbound/outbound interfaces, seams, compatibility contracts).

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

## The parent's own compatibility contracts (enforce alongside the laws)

These are this repo's specific hard boundaries, from `context/edges.md`. Break none of them:

1. **Owns no runtime code and no customer data.** Keep `contextiseverything.owned_runtime_surfaces == []`;
   never add a runtime surface or a customer datastore under the parent
   (`scripts/check_company_portfolio_boundaries.py`, clause B).
2. **The dependency law is untouched by parent changes.** Baltor → Teleon → OpenHubForAI, never the reverse;
   Teleon never imports Baltor; OpenHubForAI imports neither
   (`scripts/check_portfolio_dependency_law.py`).
3. **`products.js` is the single source of brand identity.** Renames are one-line edits there; other
   surfaces read from it — do not fork brand names, taglines, or accents into per-surface copy (this is
   Law #6 applied to brand identity).
4. **Legacy slug and paths are stable.** The slug stays `contextiseverything`; legacy folders
   (`context-is-everything/`, `context-enrichment/`, root `openharness/`) are not renamed without a full
   cross-link sweep (~20 links in hub footers and the Demo Control Tower).
5. **The one design law holds.** The shared kit (`shared/` → `web/<brand>/kit/`) is the only style source;
   accent and copy are the only per-surface variables. Do not design against `scripts/surface_server.py`
   (a demoted fallback).
6. **The family count is computed, never hand-typed** (Law #6): verify with
   `python3 scripts/check_ai_done_right_surface_family.py --self-test` before trusting or editing any
   surface-family count.
7. **Discovery is not trust.** Never present private-bench hubs as public production surfaces, or
   OpenHubForAI discovery as governed truth — only Baltor's governed source serves truth.

## Default fast path

- Change one thing; validate and index **only the changed paths**; run the umbrella `run_proofs`; do not
  start with a full rebuild. If a full rebuild is slow, capture the bottleneck and improve the incremental
  path — do not keep repeating the slow one.
- **Reuse-first.** Before building any surface, server, engine, or "new" layer, check it does not already
  exist in `../_shared/`, in a neighbor's published interface (see `EDGES.md`), or in the reference bundle
  `dist/sites/aidoneright-design/` / `web/context-is-everything/`. *"This already exists, don't rebuild it"*
  is the highest-ROI decision here — and the naming law (§2) exists so that check resolves exactly.
- **Audit neighbors before and after a code change.** Before and after editing a symbol, check what depends
  on it and update load-bearing neighbors in the **same** change — a green suite says the code runs; the
  dependency graph says what else the change can break.

## Adding work

- **This repo is one component — the parent brand.** It exposes only `portfolio-site` and `brand`; it adds
  no product logic. Work stays inside this repo's own context (`context/` + `EDGES.md`); never edit a
  neighbor to add something here.
- **Consume neighbors via their published interface only** (`EDGES.md`): dev-rules-context (`standards/*`,
  `tools/check_*.py`, `_shared/*`), teleon (`/api/teleon`), baltor (`/api/baltor`), aidevobserver
  (`/api/observer`), openhubforai (the CapabilityTask spec + harnesses). Never read or import a neighbor's
  source.
- **A new decision point** = a portfolio (§1), not an `if`.
- **A new generated id** = one call to the shared `canonical_id` (§2), stamped `candidate = true` (§3).
- **A new frontend↔backend integration** = a service + a same-origin seam + `fetch('/api/<x>/...')`, never
  a hardcoded host and never a static stub over a rich app. The four load-bearing seams are
  `/api/identity/`, `/registry/`, `/api/teleon/`, `/api/observer/`.

## Safety and scope

- **No real PII, secrets, confidential data, or proprietary dumps.** Synthetic or public metadata only.
  Never commit keys. Do not republish `_reference/`.
- **Sensitive domains** get review queues, verified facts, signed publishers, redaction, provenance, and
  deterministic gates — not "just ask the model."
- **Restricted domains:** insurance pipelines are restricted portfolio-wide — do not expand insurance
  examples; and the parent must never add a runtime surface or a customer datastore
  (`owned_runtime_surfaces == []`), or present private-bench hubs / open discovery as governed public truth.

## When stuck

If one path is blocked, switch paths — do not stop. Generate proofs, add readiness/audit tooling, add
source-surface seeds, add repair planners for missing pieces, or add documentation that prevents a repeated
slow or wrong path. Do not stop because one scraper, API, provider, or full rebuild is slow. Every serious
turn improves at least one durable thing.
