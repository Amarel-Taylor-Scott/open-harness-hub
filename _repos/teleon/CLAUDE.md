# CLAUDE.md — `aidoneright-teleon` agent operating manual

> The **AI Done Right** operating layer for the `teleon` repo. This file is the agent operating layer;
> the laws it inherits live in [`../dev-rules-context/standards/`](../dev-rules-context/standards/README.md)
> and win if this file ever disagrees with them. The laws section below is kept **verbatim** from the
> portable template — it is the inherited standard, linked (never copied). Everything Teleon-specific is
> grounded in this repo's own context under [`context/`](context/) and [`EDGES.md`](EDGES.md).

## Project

- **Name:** `aidoneright-teleon`
- **North star (one line):** the purpose-driven, eval-gated, self-adaptive compute **runtime SaaS** —
  you declare a capability in plain text and Teleon descends it to the cheapest **bounded** form within
  your guardrails, promoting only what a proof passes; it governs what becomes **EFFICIENT** (Baltor
  governs what becomes TRUE).
- **Target vertical(s) — depth before breadth:** the **first internal customer, Baltor** (tenant
  `baltor-internal`), proving ONE governed capability end-to-end through the full lifecycle
  (INTENT → GATE → COMPILE → RUN → RE-PROMOTE) — the healthcare-admin / sanctions-screening capability,
  not breadth of runtime features. Second customer class: **AI agents** calling the Agent Capability
  Gateway (agents are customers). Every new layer must serve one of these proven consumers; breadth of
  runtime cleverness without a real consumer is the failure mode.
- **Reference implementation:** this repo's [`context/`](context/) (start with
  [`context/blackbox.md`](context/blackbox.md) = what Teleon is/owns, then
  [`context/edges.md`](context/edges.md) = how it connects), plus the parent monorepo's `src/teleon/**`
  package and `docs/strategy/teleon-*.md` docs that the context files cite.
- **Common truth for all components:** [`../dev-rules-context/_shared/`](../dev-rules-context/_shared/)
  — the shared standards statement (`STANDARDS.md`), the glossary (`GLOSSARY.md`), and the overarching
  goal — plus the canonical architecture map at
  [`_repos/_shared/ARCHITECTURE-MAP.md`](../_shared/ARCHITECTURE-MAP.md) (the same map `context/edges.md`
  cites). Read from here; never re-declare what already lives here.

### Teleon identity locks (use exactly — do not reintroduce superseded terms)

- **Naming stack (LOCKED):** product = **Teleon**; core object = **PurposeTask** (product language),
  formal/spec synonym **CapabilityTask** (spec stewarded by OpenHubForAI); open standard = **Capability
  Task Specification (CTS)**; staff dashboard = **Teleon Control Tower**; customer dashboard =
  **Capability Assurance Portal**. Superseded, never reintroduce: "Purpose Runtime", "Anneal", "Cairn",
  "OCTS". Positioning caution: `teleon.ai` is an unrelated "deploy AI agents" product — lead with
  CapabilityTask / evidence-gated-promotion language, avoid "AI agent runtime" framing.
- **Vocabulary (fixed):** PurposeTask · ImplementationCandidate · RuntimeBinding · EvidenceLedger ·
  PromotionGate · BoundaryApproval · TaskOrientation · AssurancePortal. Version lives in
  `schema_version` metadata, never in a name or id.
- **The two standing invariants that make self-adaptation safe:** MEANS may auto-adapt (adaptation
  ladder L0–L3, each behind its own gate), **ENDS never do** (L4/L5 and `forbidden_autonomous` are
  human-only); and **`serves_truth = false` on every Teleon output** — capability output is EVIDENCE the
  caller receives, not a fact it can re-sell. Keep both pinned.

## Read first

1. [`../dev-rules-context/standards/README.md`](../dev-rules-context/standards/README.md) — the laws
   index, in order (the two headline laws first).
2. This file — the operating layer, including the Teleon identity locks above.
3. This repo's context for what you are touching: [`context/blackbox.md`](context/blackbox.md) (what
   Teleon is/owns), [`context/edges.md`](context/edges.md) + [`EDGES.md`](EDGES.md) (its connections and
   the boundary law), then the focused doc under `context/{architecture,strategy,codex,standards,status,goals,research}/`.

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

## Default fast path

- Change one thing; validate and index **only the changed paths**; run the umbrella `run_proofs`; do not
  start with a full rebuild. If a full rebuild is slow, capture the bottleneck and improve the incremental
  path — do not keep repeating the slow one.
- **Reuse-first.** Before building any component, server, engine, or "new" layer, check it does not already
  exist in `../dev-rules-context/_shared/`, in this repo's `context/`, or in the reference `src/teleon/**`.
  *"This already exists, don't rebuild it"* is the highest-ROI decision here — and the naming law (§2)
  exists so that check resolves exactly. Much of the runtime is already built (PurposeTask controller,
  adaptation ladder, Parallel-Path Engine, capability→runtime compiler, OIPS receipts, agent gateway) —
  read `context/blackbox.md` §3 before assuming a subsystem is missing.
- **Audit neighbors before and after a code change.** Before and after editing a symbol, check what depends
  on it and update load-bearing neighbors in the **same** change — a green suite says the code runs; the
  dependency graph says what else the change can break.

## Adding work

- **A new decision point** = a portfolio (§1), not an `if` — a new ImplementationCandidate / RuntimeBinding
  registered behind the selector, never a hardcoded default.
- **A new generated id** = one call to the shared `canonical_id` (`src.teleon.experiments.ids`, §2),
  stamped `candidate = true` (§3). Version goes in `schema_version` metadata.
- **A new frontend↔backend integration** = a service-plane service + a same-origin seam
  (`/api/teleon/...`, Observer via `/api/observer/...`) + `fetch('/api/<x>/...')`, never a hardcoded host
  and never a static stub over a rich app.
- **A new adaptation** = it changes MEANS only (L0–L3, gated); anything touching ENDS (purpose,
  permissions, connected systems, secrets, provider, risk) is a `BoundaryApproval` (L4/L5, human) — and
  the `forbidden_autonomous` set is never automatic.
- **Respect the boundary law when adding an import:** Teleon MUST NEVER import Baltor (`src.baltor.*`);
  it MAY consume OpenHubForAI artifacts and the registry/primitive substrate as candidates behind a port.
  See [`EDGES.md`](EDGES.md) / [`context/edges.md`](context/edges.md). Watch for lazy (inside-function)
  and underscore-private imports that a top-level grep misses and can silently recreate a `teleon → baltor`
  edge.

## Safety and scope

- **No real PII, secrets, confidential data, or proprietary dumps.** Synthetic or public metadata only.
  Never commit keys; secrets are `env://` refs, never values. Do not republish `_reference/`.
- **Sensitive domains** get review queues, verified facts, signed publishers, redaction, provenance, and
  deterministic gates — not "just ask the model."
- **Insurance pipelines are restricted** — do not start new insurance work and do not expand any legacy
  insurance example. The proven vertical is healthcare-**admin** (provider directory / sanctions
  screening), which is not insurance.
- **`serves_truth = false` stays pinned on Teleon output** — the gateway never emits the `served`
  use-level; Baltor's rail governs truth.

## When stuck

If one path is blocked, switch paths — do not stop. Generate proofs, add readiness/audit tooling (e.g.
`scripts/check_teleon_go_live_readiness.py`), add source-surface seeds, add repair planners for missing
pieces, or add documentation that prevents a repeated slow or wrong path. Do not stop because one scraper,
API, provider, or full rebuild is slow. Every serious turn improves at least one durable thing.
