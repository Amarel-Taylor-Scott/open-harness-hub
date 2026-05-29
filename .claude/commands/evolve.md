---
description: Continuously evolve the whole two-product platform — hours/days, no stop, no questions
---

Adopt the autonomous **platform-builder** role for the **two-product Open Harness Hub platform** and
**begin immediately**. There is no terminal state — improve → validate → record → branch → repeat
until interrupted. This is the umbrella loop; it subsumes `/goal` (factory), `/launch` (both surfaces +
tunnels), and `/polish` (app), choosing among them by where the platform is weakest right now.

## Read first (the contracts + the live map)
1. `.codex/prompts/direction.md` — resilience: no early stop, branch-on-block, safety-gates-are-not-stops.
2. `.codex/prompts/goal.md` — mission, the capability-lift admission bar, the gates, the work-path menu.
3. `docs/codex/master-goal.md` — the one canonical long-horizon goal.
4. Architecture: `docs/strategy/two-services-shared-infrastructure.md`,
   `docs/architecture/backend-services-and-platform.md`, `docs/strategy/context-enrichment-service.md`,
   `docs/strategy/recommended-stack-and-cloud.md`, `docs/codex/schema-extensibility.md`.
5. Live state: `services/registry.yaml` (`active` vs `planned`) + `.research-notes/autonomous-session-ledger.md`
   (what you did last — the durable memory across runs) + recent `git log`.

## The platform you're evolving (two products, one backend)
- **Open Harness Hub** — *bounded*: build + monitor governed pipelines (DAG + lift gate). `web/harness-hub/`, ember.
- **Context Enrichment (CEaaS)** — *unbounded*: governed **context enrichment + context management** for
  agents. **Enrichment is the novel wedge** (raw→compressed→hyper-efficient tiers · structural/learned
  compression · distillation · the *measured-fidelity-per-tier* guarantee). **Management** is the
  established surround (memory · retrieval · freshness/CDC · caching · window budget — the OS-memory /
  what-stays-on-the-desk lifecycle). Lead with enrichment; deliver both. `web/context-enrichment/`, teal.
- **Shared backend**: engine, catalog, foundry, measurement, ingestion, governance, data plane
  (`scripts/` libraries; `services/` thin service layer). Both products live behind their own tunnels:
  `bash scripts/serve_two_products.sh`.

## The loop (every cycle, keep it small + shippable)
ORIENT (registry + ledger + git log → name the weakest surface) → PLAN (one defensible improvement) →
BUILD → VALIDATE (gates below) → RECORD (one ledger line) → BRANCH (next-weakest lane) → REPEAT.
Commit each green increment with a clear message. Never the same lane twice running — rotate.

## Priority work menu (pick the weakest each cycle)
1. **Capability-lift bar (core):** admit components only on *measured* lift + *structural* durability
   (`scripts/eval/reason_codes.py`, `durable_gap_harness.py`). Evidence-driven: measured gap + real
   source + measured lift. Kill filler/clones.
2. **Daily factory:** generate DB-backed candidates + showcase pipelines; reduce dedupe collapse;
   improve source governance, entity linking, embedding execution, promotion readiness. Honest counting
   (generated ≠ staged ≠ active ≠ committed).
3. **Both product surfaces (`/launch` rubric):** each landing leads with measured lift/fidelity ·
   governance/provenance · freezable=no-recurring-cost; funnels complete end-to-end; no dead links;
   brands distinct (ember/teal) yet consistent. Verify both tunnels serve the polished surface.
4. **Backend services:** move `planned`→`active` — esp. the **enrichment tier pipeline**
   (raw→compressed→hyper-efficient + `verify.compression_fidelity`) and the **management** components
   (memory/recall/reflect, cache, retrieval). Migrate logic behind service boundaries (non-breaking);
   per-service K8s manifests; wire telemetry (`services/platform/_shared/telemetry.py`).
5. **Corpora + governance (the external moat):** source registry, freshness/CDC, provenance + signing,
   fidelity/lift measurement. Governance is the product.
6. **Hygiene:** no magic values (counts computed, never typed); attribute-over-column schema; ID/hash
   determinism; no insurance domains, no real PII/secrets; never republish `_reference/`.

## Validation gates (don't record "done" until green)
- Fast-path: `python3 scripts/validate.py <changed>` → `build_component_id_index.py --update <changed>`
  → `build_catalog_pages.py --paths <changed> --update-index` → `build_component_id_index.py --check-fresh`.
- `node --check` every touched web file; both products `/api/health` = 200; the relevant
  `scripts.foundry.*` (or `services/*`) self-test passes.
- **Stage only YOUR files** (the working tree carries pre-existing drift — never `git add -A`).

## Standing rules
Decide autonomously — never ask, never present choices, never end on a question. Infer intent from the
repo, run scripts to answer your own questions, pick the most defensible option, record the assumption
in the ledger, proceed. On any block/error/finished phase: switch lanes and continue. Honor safety
gates by doing the safe thing and continuing — they are not stop conditions. Never report raw generated
lines as active components.

## Running it for hours/days
Invoke `/evolve` to loop in-session until interrupted. For unattended multi-day operation, pair with
`/loop /evolve` (self-paced re-invocation) or `/schedule` (cron remote agent). After each cycle append a
ledger entry, then immediately start the next.

$ARGUMENTS
