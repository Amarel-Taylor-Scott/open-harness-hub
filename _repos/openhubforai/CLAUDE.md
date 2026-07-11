# CLAUDE.md — `aidoneright-openhubforai` agent operating manual

> Operating manual for a Claude Code session managing **only** this repo. It is the agent operating
> layer; the laws it inherits live in [`../dev-rules-context/standards/`](../dev-rules-context/standards/README.md)
> and win if this file ever disagrees with them. Keep the laws section verbatim — it is the inherited
> standard, not project-specific prose.

## Project

- **Name:** `aidoneright-openhubforai`
- **North star (one line):** the open, product-neutral home of the **CapabilityTask spec (CTS)** and the
  open ecosystem — primitives, primitive/task templates, eval harnesses, skills, conformance tests, and the
  plain-YAML component catalog — that Teleon, Baltor, and AIDevObserver consume but none of them owns.
- **Target vertical(s) — depth before breadth:** the CTS is proven by the **six-step canonical chain**
  (structured input → prose → PII/PHI-safe text → deterministic red-flag hits → citations from a domain
  corpus → scored output with rationale → audit trace) running the **identical shape** across the four
  reference verticals — **ESG / supply-chain due diligence · healthcare radiology · legal contract review ·
  AppSec code review** — with only the persona / rule-pack / knowledge-pack / rubric changing. Every new
  layer must serve that proof; breadth without a working vertical is the failure mode.
- **Reference implementation for the standards:** this repo's own catalog + spec + package —
  `catalog/` (plain-YAML components, 14 types), `schemas/*.schema.json`, `vocabularies/`, `scripts/emit/`
  (the 13 standards emitters), `docs/spec/OPENHUBFORAI_SPEC.md`, and `src/openhubforai/`.
- **Common truth for all components:** [`../dev-rules-context/_shared/`](../dev-rules-context/_shared/) —
  the shared standards statement, the glossary, and the portfolio architecture map. Read from here; never
  re-declare what already lives here.

## What this repo is (the one boundary that governs everything)

OpenHubForAI is the **open registry storefront Teleon, Baltor, and AIDevObserver consume** and the **neutral home of the standard** — and
**none of its hubs is a truth authority (discovery ≠ trust)**. Its credibility is its neutrality:
`src/openhubforai/**` imports neither `src.teleon.*` nor `src.baltor.*` (enforced by
`scripts/check_portfolio_dependency_law.py`). This is what lets us say *"Teleon implements the open
CapabilityTask Spec,"* not "Teleon invented a proprietary task format." Do not weaken that import-freedom.

**The single most important reuse boundary:** the **registry federation query engine is Teleon-owned**
(`src/teleon/registry/{port,search,populate,...}.py`), NOT part of this repo. OpenHubForAI owns the
*catalog content, the spec, the schemas/vocabularies, and the storefront*; it **queries** the 103
registries through Teleon's `RegistryPort` over the `/registry/...` seam. When building browse UI, build
over that existing federated search — **do NOT rebuild the search.** Full detail: `context/edges.md` §3.

## Read first

1. [`../dev-rules-context/standards/README.md`](../dev-rules-context/standards/README.md) — the laws index,
   in order (the two headline laws first).
2. This file — the operating layer.
3. This repo's own context: [`context/blackbox.md`](context/blackbox.md) (what OpenHubForAI is and owns) +
   [`context/edges.md`](context/edges.md) (how it connects to the other five components + the compatibility
   contracts) + [`EDGES.md`](EDGES.md) (the machine-generated cross-repo edge list). The deeper source docs
   live under `context/{spec,architecture,design,handoff,howto,reference,research,status,...}/`.

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
- **Reuse-first.** Before building any component, server, engine, emitter, or "new" layer, check it does
  not already exist in `catalog/`, `scripts/emit/`, `src/openhubforai/`, `../dev-rules-context/_shared/`,
  or the Teleon-owned registry federation (the search you must not rebuild). *"This already exists, don't
  rebuild it"* is the highest-ROI decision here — and the naming law (§2) exists so that check resolves
  exactly.
- **Audit neighbors before and after a code change.** Before and after editing a symbol, check what depends
  on it and update load-bearing neighbors in the **same** change — a green suite says the code runs; the
  dependency graph says what else the change can break.

## Adding work

- **A new catalog component** = one YAML manifest under the right `catalog/<type>/` directory, validated
  against `schemas/*.schema.json` (envelope base `schemas/_common.schema.json`), using only controlled
  values from `vocabularies/`. `id` is `"<type>/<kebab-slug>"`, globally unique; `version` is semver in
  metadata (never in the id); it is born a candidate (§3) — publishing a spec is not promoting it to truth.
- **A new standards emitter** is a published surface — extend `scripts/emit/` additively; never silently
  drop or rename an existing emitter format (one manifest → 13 standards publications is a contract).
- **A new decision point** = a portfolio (§1), not an `if`.
- **A new generated id** = one call to the shared `canonical_id` authority (§2), stamped
  `candidate = true` (§3).
- **A new frontend↔backend integration** = a service + the same-origin `/registry/...` seam +
  `fetch('/registry/...')`, never a hardcoded host and never a static stub over the rich `web/openhubforai/`
  app. Query the catalog through Teleon's `RegistryPort` over the seam — do not fork the search.
- **Keep `maps_to_hub` consistent by hand.** It is the ONLY hub↔registry binding and nothing yet enforces
  it stays valid (a candidate contract); a session touching hub/registry structure must not leave it stale.

## Safety and scope

- **No real PII, secrets, confidential data, or proprietary dumps.** Synthetic or public metadata only.
  Never commit keys. Do not republish `_reference/`.
- **Sensitive domains** get review queues, verified facts, signed publishers, redaction, provenance, and
  deterministic gates — not "just ask the model."
- **Discovery ≠ trust — no OpenHubForAI record is served truth.** Every hub/registry surface (including the
  method-hubs and any discovery/meta registry) publishes candidates and pointers; truth is decided
  downstream in Baltor. Never present a catalog record as governed truth. **Insurance is restricted** — do
  not add or expand insurance-related examples.

## When stuck

If one path is blocked, switch paths — do not stop. Add a catalog component, add or harden an emitter, add
a conformance test, add spec/schema/vocabulary coverage, add readiness/audit tooling, or add documentation
that prevents a repeated slow or wrong path. Do not stop because one scraper, API, provider, or full
rebuild is slow. Every serious turn improves at least one durable thing — and never at the cost of the
import-freedom that makes the standard neutral.
