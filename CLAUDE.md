# CLAUDE.md - Open Harness Hub Agent Instructions

This file is for Claude Code, Claude desktop/browser agents, and any Claude 4.x/4.8/4.7-style workflow that opens this repository. Follow `AGENTS.md` first; this file adds speed and organization rules for scaling Open Harness Hub.

## Portfolio (owner-decided 2026-06-06; updated 2026-06-09 — read FIRST)

Current parent display brand: **AI Done Right** (`aidoneright.dev`), tagline
**"AI, done right."** The prior ContextIsEverything language is preserved as
founding thesis and legacy path context, not as the parent display brand. The
high-fidelity Claude Code Max handoff lives in
`dist/sites/openharness-design/`: start with `START-HERE-CLAUDE-CODE.md`, then
`README.md`, `CLAUDE-CODE.md`, and `HANDOFF.md`.

Current design-family snapshot: parent + **Baltor** + **Teleon** + **22
Open*Hubs** (9 live open registries + 13 private-bench registries; the count is
computed by the family check, never hand-counted — don't trust this prose over
`scripts/check_ai_done_right_surface_family.py`). The private bench includes the
complete Baltor method spine (OpenReconciliationHub, OpenHardeningHub,
OpenEnrichmentHub, OpenOptimizationHub, OpenVerificationHub) and
OpenRoutingHub (model-routing policy; owner-proposed 2026-06-09). The owner-directed Codex loop for
this family is `docs/codex/ai-done-right-family-polish-goal.md`. The
parser-safe `/goal` entrypoint is
`/goal follow the instructions in docs/goals/aidoneright-portfolio-loop.md`.
Run `python3 scripts/check_ai_done_right_surface_family.py --self-test` before
trusting or editing family-surface counts. Run
`python3 scripts/check_handoff_docs_freshness.py --self-test` before handing the
bundle to another agent.

Service-to-service auth is an active architecture track. Read
`docs/architecture/service-auth-and-consumption-model.md` before implementing
API keys, service accounts, delegated calls, private-bench enforcement, or
cross-service consumption. For local testing without paid cloud, read
`docs/architecture/local-dev-tunnels-and-auth.md` and run
`python3 scripts/check_local_dev_tunnel_auth_runtime.py --self-test`.

Canonical portfolio architecture remains:
`docs/strategy/teleon-baltor-openharnesshub-portfolio.md`.

A holding company owns three product layers. **Teleon** (`teleon.dev`, domain owned) = the purpose-driven,
eval-gated, self-adaptive compute **runtime SaaS** — it owns PurposeTask/CapabilityTask, runtime selection,
evidence ledger, promotion/policy gates, boundary approvals, adapters, the assurance dashboard. **Baltor**
(`baltor.ai`) = the applied, customer-facing context product, **powered by Teleon** (a tenant). **OpenHarnessHub**
= the open ecosystem (evals/harnesses/templates/skills) + the **open CapabilityTask spec (CTS)**.

- **Architectural law (enforced by `scripts/check_portfolio_dependency_law.py` over
  `architecture/portfolio_dependency_law.json`):** Baltor → Teleon → OpenHarnessHub, **never the reverse**.
  Teleon must never import Baltor; OpenHarnessHub imports neither. PurposeTask is **Teleon**, not a Baltor
  subsystem — generic runtime code is being extracted `src/baltor/` → `src/teleon/` incrementally (lossless;
  see the law file's `migration_status`).
- **Naming:** product = **Teleon**; staff dashboard = **Teleon Control Tower**; customer dashboard =
  **Capability Assurance Portal**; object = **PurposeTask** (formal/spec synonym **CapabilityTask**). Brand
  doc: `docs/strategy/teleon-naming-and-domain.md`. ("Purpose Runtime"/"Anneal"/"Cairn"/"OCTS" are superseded.)
  Teleon's control & trust plane is a **separate greenfield TS build**: `prompts/teleon-build-kit.md`.
- **Hosting:** Teleon + Baltor deploy **same region/private network** (low Baltor→Teleon latency) but stay
  **separable** (separate service/data/identity/IaC + a versioned API + graceful local fallback).

## North Star

Active `/goal` runs are now Baltor-first. Read
`docs/codex/baltor-clean-context.md` and
`docs/codex/baltor-autonomous-goal.md` before older factory-scale context. The
component registry remains the substrate; Baltor context control is the product
focus.

Build a database-backed registry of reusable AI pipeline components and subcomponents that can scale from thousands to millions of rows without turning every row into a public static file.

The product is not a pile of static definitions. It is a component network:

- pre-LLM components: intake, OCR, normalization, source governance, entity linking, dedupe, routing, cost gates;
- LLM/model components: local models, hosted model routes, browser models, embedding models, rerankers, fine-tuning/training jobs, multimodal generators;
- post-LLM components: verification, scoring, review queues, CDC propagation, signed publisher updates, deployment blueprints;
- runtimes: local Python, Docker, Render workers, Cloud Run, Kubernetes, MCP servers, pgvector, BigQuery/ClickHouse telemetry, object storage.

Use "components" and "subcomponents" in new prose and user-facing docs. Avoid introducing new uses of "artifact" or "manifest" unless quoting an existing schema, filename, or legacy phrase. ("Primitive" IS canonical for the seven-primitive model — Input · Knowledge Corpus · If Statement · Action · Loop · Stop/End · Output; see `docs/concepts/component-taxonomy-and-stages.md`.) Product vocabulary: **Knowledge Corpus** (not "knowledge pack"), **If Statement** (not "rule pack"/"logic pack"), **Action** (a persona/tool/processor/harness/rubric is an Action). Version lives in metadata, never in names or IDs.

## Capability-Gap Framework (canonical — read before deciding what to build/collect)

We build for the **negative space** — where base models lack capability — not the head of the distribution. Two load-bearing rules:

- **Two-axis admission:** a component must lift (`pipeline_score − bare_model_score > 0`) AND the lift must be **structural** (won't close when the next model ships), not transient. Single source of the taxonomy (lift_reason → durability_class, mechanisms, retrievability tiers, decay_signal): `scripts/eval/reason_codes.py` — never re-define these enums elsewhere. Sorter: `scripts/eval/durable_gap_harness.py`.
- **Screen before you collect:** cheap Stage-1 gap screen (`scripts/acquisition/gap_screen.py`, weighted toward MODEL-INDEPENDENT signals so the model can't draw its own map) → expensive Stage-2 confirm on a sample. The owner feeds research areas at `data/research-queue/areas.jsonl` → `scripts/acquisition/research_queue.py` ranks them.

Canonical reading: `docs/concepts/capability-valleys.md`, `docs/strategy/north-stars.md` (+ `corpus-acquisition-grid-spec.md`, `gap-detection-screen-spec.md`, `external-research-brief-2026-05-28.md`). Governance/provenance is the external moat; the lift bar is the internal selection criterion.

## Default Fast Path

Do not start with full catalog rebuilds. The normal loop is:

```bash
python3 scripts/validate.py <changed catalog paths>
python3 scripts/build_component_id_index.py --update <changed catalog paths>
python3 scripts/build_catalog_pages.py --paths <changed catalog paths> --update-index
python3 scripts/validate.py --global-ref-check <changed pipeline paths>
python3 scripts/build_component_id_index.py --check-fresh
```

Use full release gates only when explicitly requested or when changing schemas, vocabularies, or broad catalog references:

```bash
python3 scripts/validate.py
python3 scripts/build_catalog_pages.py
```

If a full rebuild takes too long, do not keep repeating it. Capture the bottleneck and improve the incremental path.

## Code-Graph Change Audit (audit neighbors before/after a code change)

Before AND after editing a `.py` file/function/class/method, audit its **strong connections** on the unified
weighted code graph and update load-bearing neighbors in the **same** change — a green suite says the code runs, the
graph says what else the change can break:

```bash
PYTHONPATH=. python3 scripts/codegraph.py --audit <file-path | dotted.module | symbol.name>
```

It ranks (by strength = call-sites × resolution-confidence) the importers/callers that break if the API changes,
plus the transitive blast radius. Resolution is confident-only (ambiguous/builtin-shadow calls are dropped+counted,
never guessed), so the ranking is trustworthy. The graph is a seam: `codegraph.py` / `symbol_graph.py` /
`code_graph.py` carry `--self-test` (in `run_proofs.py`); regenerate artifacts with `scripts/codegraph.py --emit`.
Full protocol: `docs/codex/codegraph-change-audit-protocol.md`.

## Daily Factory Target

Every serious development turn should improve at least one of these:

- generate 1,000 to 5,000 database-backed component candidates per day;
- generate 5 to 25 showcase pipelines per day;
- reduce duplicate collapse during row merges;
- improve source governance, entity linking, fuzzy dedupe, index records, review routing, embedding execution, or promotion readiness;
- make staged rows easier to load into Postgres/pgvector safely;
- make component IDs, hashes, CDC events, and index deltas more deterministic.

High-volume rows belong in JSONL staging and Postgres/pgvector load plans, not thousands of new hand-written static pages.

## Required Row Families

A scalable factory batch should emit or preserve:

- `source_record`
- `normalized_object`
- `canonical_entity`
- `object_entity_ref`
- `dedupe_cluster`
- `label_assignment`
- `dimension_value`
- `object_embedding`
- `index_record`
- `review_ticket` when risk warrants review

Do not report raw generated lines as active components. Separate:

- generated candidate rows;
- unique staged rows;
- candidate-table load readiness;
- active promotion readiness;
- committed Postgres rows;
- vector search product readiness.

## ID And Hash Discipline

Never rely on truncation alone for generated IDs. Long generated component IDs must include stable hash suffixes so daily batches do not collapse during dedupe, index merge, or CSV load planning.

Use canonical hashes for:

- normalized object body;
- component version definition;
- source content;
- index record identity;
- command approval records;
- replay and CDC events.

Formatting changes should not create false versions. Source content changes should be detectable even when the wrapper stays the same.

## No Magic Values (Single Source Of Truth)

Never hand-type a value that has to be remembered and updated in more than
one place. At scale, a value typed twice is a value that drifts.

- Numbers that describe the repo (component counts, totals per type, "N
  emitters", spec/catalog version, build date) are **computed**, never typed
  into prose. The README count drifting from `172` to thousands is the
  canonical bug — do not reintroduce it.
- A value used in more than one place (embedding dimension, model IDs,
  thresholds, canonical paths, row-family/type names) gets **one definition**
  and is imported everywhere else. Put shared constants in a config module;
  put shared lists in `vocabularies/`/`schemas/` and read them.
- A string that embeds a constant's value is built from the constant
  (`f"vector({DEFAULT_SCHEMA_DIMENSIONS})"`), never a parallel literal
  (`"vector(384)"`).
- Every meaningful literal in logic is a named constant with a unit/rationale
  comment. Where a value must be mirrored, add a validate/CI check that fails
  on drift.

Full rules, examples, and remediation: `docs/codex/no-magic-values.md`.

## Change Verification (warrant before change)

Every update or design change carries a **warrant** before it is committed — one of: **clear user
intent** (cite it in the commit/ledger), **≥2 independent agreeing sources**, or **an established repo
principle**. Match the bar to the blast radius: trivial/reversible → a principle suffices; **design /
brand / strategy / vocabulary / pricing / product-structure → clear user intent OR strong corroboration,
NEVER a unilateral single-agent call**; irreversible / outward-facing → explicit intent + confirmation.
"It's green" is necessary, not sufficient. Exceptions (small + reversible) are allowed but **recorded in
the ledger**. Verifiers — and the autonomous loop — check the *warrant*, not just that it passed; when a
decision supersedes an earlier one, update/delete the stale artifact in the **same** change (no orphaned
contradictions); a memory/doc that names a file or flag is a claim about a past state — re-verify it
before relying on it. Full contract: `docs/codex/change-verification-contract.md`.

## Lossless Distillation (distillation is never replacement)

**Distillation is never replacement.** Any distillation, decomposition, compression, optimization,
reconciliation, promotion, or LLM→deterministic-rule conversion creates a new **versioned** derived
layer while PRESERVING the raw layer, intermediates, lineage, source handles, held-out items, rejected
candidates, model/tool traces, configs, receipts, and a rollback target. Omitted / held-out / rejected /
superseded ≠ deleted. No destructive overwrite, irreversible compression, lossy promotion of truth-bearing
facts, or a winner without lineage to the losers. Compression may shrink the text surface only if
answer-critical facts + source handles + held-out warnings survive; tenant-private lineage never becomes
global. Run side-by-side before promotion, shadow new rules, monitor after, and prove rehydration. Carry
the **LOSSLESS DISTILLATION CLAUSE** in every workflow prompt. Full law:
`docs/codex/lossless-distillation.md`.

## Archived / Legacy Files (move, never delete; never untrack)

Outdated / superseded context is **moved, not deleted, and not untracked** — it stays in git for lineage + rollback,
relocated under **`archive/legacy/<original-path>`** with its status recorded. Rules:

- **Mover:** `scripts/archive_legacy_docs.py` (`--scan` to list, `--apply` to move losslessly). Conservative,
  header-marker detection only (superseded-by / deprecated / do-not-use) so a live doc is never archived.
- **Status label is mandatory:** every move is recorded in `archive/legacy/_manifest.jsonl` (original_path, reason,
  status, reversible) and surfaced in **`archive/legacy/README.md`** (the human status index + restore instructions).
- **Codemap/context exclude `archive/`** (`scripts/context_pack_builder.py` `_TREE_EXCLUDE`) so archived files drop
  out of the model context automatically — but stay on disk + in git.
- **Restore** = `git mv archive/legacy/<path> <path>` (the manifest has the exact origin).
- **Status accuracy law:** never mislabel LIVE/GENERATED data as "legacy." The component catalog (root `catalog/` =
  live registry read by `dev_status.py`/the build; `docs/catalog/*.md` = GENERATED output of
  `scripts/build_catalog_pages.py`, only `index.md` in the mkdocs nav) is **not** legacy — it carries a `_STATUS.md`
  marking it generated/live, and is never archived as outdated.

## Promotion Boundary

Candidate-table load readiness is not active publication readiness.

A candidate can be structurally load-ready when it has source, dedupe, content hash, embedding work, and index records. It must not become tenant-visible while it has:

- open review tickets;
- high-risk review requirements;
- placeholder embeddings;
- unresolved source or signature questions;
- volatile public facts without CDC/revocation handling.

Use `scripts.db.daily_promotion_readiness_plan` after large row generation.

## Safety And Scope

Do not store real PII, secrets, confidential data, or proprietary dumps. Use synthetic or public metadata only. Do not republish `_reference/`.

Stay away from insurance-related pipelines in new work. If legacy insurance examples already exist, do not expand them.

For sensitive domains, prefer review queues, verified facts, signed publishers, redaction, provenance, and deterministic gates over "just ask the model."

## What To Do When Stuck

If one source path is blocked, switch paths:

- generate showcase pipelines;
- add promotion/readiness tooling;
- improve load audits;
- add source-surface seeds;
- add repair planners for missing row families;
- add documentation that prevents repeated slow or incorrect paths.

Do not stop because one scraper, API, provider, or full rebuild is slow.
