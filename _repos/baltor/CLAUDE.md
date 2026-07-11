# CLAUDE.md — `aidoneright-baltor` agent operating manual

> The **AI Done Right** operating manual for this repo. It is the agent operating layer; the laws it
> inherits live in [`../dev-rules-context/standards/`](../dev-rules-context/standards/README.md) and win
> if this file ever disagrees with them. The laws section below is the inherited standard — kept verbatim,
> not project-specific prose. Everything Baltor-specific is grounded in this repo's own context
> (`context/blackbox.md`, `context/edges.md`, `EDGES.md`).

## Project

- **Name:** `aidoneright-baltor`
- **North star (one line):** Keep enterprise agent context **verified, current, reconciled, traceable,
  and ready to serve** — the applied, customer-facing governed-context product (powered by Teleon as the
  tenant `baltor-internal`), whose durable moat is **governed data + receipts** (provenance, signed facts,
  source trust, change/revocation handling), never the technique.
- **Target vertical(s) — depth before breadth:** consumer-finance regulation — **CFPB / Reg E** is the
  reference vertical (the proven end-to-end spine returning "10 business days" with FAQ-30 held out as a
  warning). Second proven feed: **sanctions / export-controls screening** (the first live governed feed).
  Additional guided verticals exist as demos (EUDR, airworthiness, dangerous-goods, accounting-standard,
  context-governance) but every new layer must serve the ONE vertical being proven to a real user; breadth
  without a proven vertical is the failure mode. **Insurance is out of scope** — see Safety and scope.
- **Reference implementation for the standards:** the built-out source lives in the parent monorepo under
  `src/baltor/` (package root) and `web/baltor/` (the served app); this repo's `context/` is the
  consolidated, source-cited briefing for it. Start at `context/blackbox.md` (what Baltor is/owns/does) and
  `context/edges.md` (how it connects), then the topic folders under `context/` (`contextops/`,
  `determinism/`, `distillation/`, `native/`, `runtime/`, `security/`, `strategy/`, `status/`, …).
- **Common truth for all components:** [`../dev-rules-context/_shared/`](../dev-rules-context/_shared/) — the
  shared standards statement (`STANDARDS.md`), the glossary (`GLOSSARY.md`), the six-component
  architecture map (`ARCHITECTURE-MAP.md`), and the overarching goal. Read from here; never re-declare what
  already lives here.

## Read first

1. [`../dev-rules-context/standards/README.md`](../dev-rules-context/standards/README.md) — the laws index,
   in order (the two headline laws first).
2. This file — the operating layer.
3. `context/blackbox.md` + `context/edges.md` + `EDGES.md` — what Baltor is/owns and its published edges
   (the ONLY cross-repo context a session here needs — neighbors' edges, never their internals). Then the
   `context/<topic>/` folder for the subsystem you are touching (its purpose, edges, paths, proofs, status).

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

## Baltor-specific invariants (the moat mechanics — honor these exactly)

These follow directly from the eight laws above, applied to what Baltor governs. Full statements and the
proof names that enforce them are in `context/edges.md` ("Compatibility contracts") and `context/blackbox.md`.

- **Dependency direction is LAW:** `Baltor → Teleon → OpenHubForAI`, never the reverse. Baltor calls Teleon
  only through the versioned tenant client `src/baltor/teleon_client/` as tenant `baltor-internal`; Teleon
  must never import Baltor. Branch on the layer + edge, never a brand display name.
- **Agents propose, Baltor disposes.** No agent or LLM ever serves a fact directly; only reconciliation /
  native_export / distillation / human-gate workers publish truth (the worker-taxonomy safety split).
- **Fact adoption needs corroboration:** ≥2 independent supporting sources, OR one source only if it is the
  authoritative source of record; if sources disagree, the fact stays OUT of served context until
  precedence / effective-date / scope resolve. Every adopted fact records its sources, roles, timestamps,
  hashes, trust score, adoption decision, and fact-state lineage.
- **Dashboards are projection-only** — no truth or secrets leak through any `/api/*` projection.
- **Tenant isolation** — `tenant_private` never trains or updates `global_public`.
- **Native format preservation** — same-shape-in/out; the ORIGINAL is never overwritten; every verified
  change carries a diff + receipt.
- **Graceful degrade** — Baltor never hard-fails because Teleon is down; it degrades to a local fallback
  behind a circuit breaker and records the fallback in the per-call receipt.

## Default fast path

- Change one thing; validate and index **only the changed paths**; run the umbrella `run_proofs`; do not
  start with a full rebuild. If a full rebuild is slow, capture the bottleneck and improve the incremental
  path — do not keep repeating the slow one.
- **Reuse-first.** Before building any component, server, engine, or "new" layer, check it does not already
  exist in `../dev-rules-context/_shared/`, in another `context/<topic>/`, or in the reference source
  (`src/baltor/`). *"This already exists, don't rebuild it"* is the highest-ROI decision here — and the
  naming law (§2) exists so that check resolves exactly.
- **Serve the built-out app, never a skinny replacement.** The Baltor surface is the rich app in
  `web/baltor/` served by the showcase over the shared kit, wired to backends through same-origin seams
  (live-ops, `/api/identity/`, `/registry/`, `/api/teleon/`, `/api/observer/`). Never stand up a static
  stub over it; if a backend call 501s, wire the seam + a service, never stub it.
- **Audit neighbors before and after a code change.** Before and after editing a symbol, check what depends
  on it and update load-bearing neighbors in the **same** change — a green suite says the code runs; the
  dependency graph says what else the change can break.

## Adding work

- **A new decision point** = a portfolio (§1), not an `if` — a new row + a resolver entry behind one
  selector, with an `ACTIVE_DEFAULT` that reproduces current behavior.
- **A new generated id** = one call to the shared `canonical_id` (§2), stamped `candidate = true` (§3);
  Baltor mints via `src.teleon.experiments.ids` and keeps `src/baltor/experiments/ids.py` a shim — no
  parallel implementation, no `import hashlib` in `src/**`.
- **A new fact adopted into served context** = corroboration or authoritative source of record + source
  review + an executed passing proof + the gates. Nothing promotes itself.
- **A new frontend↔backend integration** = a service + a same-origin seam + `fetch('/api/<x>/...')`, never
  a hardcoded host and never a static stub over the rich app.
- **Consume a neighbor** only through its published edge listed in `EDGES.md` — never read or import a
  neighbor repo's source.

## Safety and scope

- **No real PII, secrets, confidential data, or proprietary dumps.** Synthetic or public metadata only.
  Never commit keys. Do not republish `_reference/`.
- **Sensitive domains** get review queues, verified facts, signed publishers, redaction, provenance, and
  deterministic gates — not "just ask the model."
- **Insurance is a restricted domain** — do not start new insurance pipelines and do not expand any legacy
  insurance examples. Target the proven adjacent verticals (CFPB / Reg E, sanctions / export-controls) and
  the claims-shape adjacencies, never insurance itself.

## When stuck

If one path is blocked, switch paths — do not stop. Generate proofs, add readiness/audit tooling, add
source-surface seeds, add repair planners for missing pieces, or add documentation that prevents a repeated
slow or wrong path. Do not stop because one scraper, API, provider, or full rebuild is slow. Every serious
turn improves at least one durable thing.
