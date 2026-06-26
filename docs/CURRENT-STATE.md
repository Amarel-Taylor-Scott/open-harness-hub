# Current State — Baltor / Teleon / AI Done Right portfolio

_Snapshot: 2026-06-09 · **flywheel GREEN** (live count: `python3 scripts/baltor_flywheel.py --once`) · orientation doc for the multi-day loop. Counts are never frozen here — see the live signal (guarded by `scripts/check_current_state_freshness.py`)._

## 1. What this is
A holding company (**AI Done Right**, with legacy `contextiseverything` code paths preserved) owns three product layers + an open ecosystem:
- **Teleon** (`teleon.dev`) — purpose-driven, eval-gated, self-adaptive **runtime SaaS** (owns PurposeTask/
  CapabilityTask, runtime selection, evidence ledger, promotion/policy gates, boundary approvals, adapters).
- **Baltor** (`baltor.ai`) — applied **governed-context** product, a **tenant of Teleon** (intake → reconcile →
  anti-fragile → enhance → optimize → consume, under a continuous-verification rail; source handles + receipts).
- **Open ecosystem:** the current design-family proof covers 21 OpenHubForAI registry prototype surfaces: 9 live open hubs
  plus 12 private-bench hubs, including the full Baltor method spine
  Reconcile → Harden → Enhance → Optimize → Verify.

**Dependency law (enforced):** Baltor → Teleon → OpenHarnessHub/hubs, **never reverse**. None of the open hubs is
a truth authority — Baltor governs truth, Teleon runs capabilities.

## 2. Health
- **Flywheel:** GREEN — every registered deterministic proof passes. The live proof count comes from
  `scripts/baltor_flywheel.py --once` (modules registered in `scripts/flywheel_proof_modules.py`); it is deliberately
  not frozen in this doc. Watchdog runs `--watch --interval 600` (restart by EXACT pid only on a PROOF_MODULES change
  or if dead).
- **Running surfaces (local + TryCloudflare tunnels):** the Baltor SPA, the portfolio_lib static launch sites, the Demo Control
  Tower, and the Baltor admin/demo server. Live URLs + ports drift, so they are **not frozen here** — read the
  aggregators `dist/cloudflare-urls.md` and `dist/demo-all-urls.md`.
- **Generated status reports** (computed, not hand-written): `docs/status/baltor-current-state-and-opportunities.md`
  (from `scripts/report_current_state.py`) + `docs/status/current-state.md`. THIS doc is the hand-written orientation;
  those are the machine-generated maturity/opportunity reports.
- **Every web surface (pages · views · routes · primitives):** the full itemized inventory of all sites — the Baltor
  SPA + the admin page/API routes, the portfolio_lib static launch sites, the OpenHubForAI app, plus the UI design-system and
  product primitives, each with status + gaps — lives in `docs/DESIGN-BIBLE.md` (canonical; the 2026-06-09 snapshot is `docs/portfolio-web-surface-inventory.md`). The
  orientation stays here; the exhaustive page/view/route enumeration lives there.

## 3. Built recently (this period)
- **Shared I/O + Resource Spine** (`architecture/shared_io_spine.json`): 6 layers ratified + proven against their
  live runtimes — object_shell · resources · command/work · events (CloudEvents) · inference · eval/promotion
  (incl. the boundary-expansion **HumanApprovalReceipt** gate). Code in `src/teleon/{io,resources,inference,
  templates}` + `schemas/{shared,resources,io,inference,governance}`.
- **Inference Gateway + OIPS** (`src/teleon/inference`): object-level model preferences → numeric provider graph →
  governed fallback → ModelInvocationReceipt (actual model used). Secrets are refs only; LLM output never truth.
  Now **served end-to-end + visible**: `scripts/api_inference_handler.py` backs `/api/inference/*`, the read-only UI is
  `web/baltor/inference-plane.html`, and a governed inference step fires inside `run_full_pipeline` (rendered on the
  Live Ops dashboard as candidate-not-truth). Adversarially proven by `scripts/check_inference_pipeline_redteam.py`.
- **Free/Limited LLM Endpoint Intelligence** (`src/teleon/inference/free_endpoint_intel.py`): ClawLess=runtime not
  endpoint; official=candidate; discovery=metadata; gateway-repo=lab; shared-key/bypass=quarantine; Together=paid.
- **OpenBenchmarkHub is real**: `schemas/benchmarks/*` + `architecture/open_benchmark_registry.json`; first-party
  **Baltor CFPB Context-Governance benchmark** anchored to the real demo facts; **benchmark result = evidence, not
  authority** (no benchmark gate in `path_promotion.GATES`).
- **Competitive provider mappings** (`architecture/competitive_provider_mappings.json`): Crusoe/Nscale→Execution
  backend, **Fireworks→live inference-gateway candidate node**, Cursor/Cognition→sandboxed CodegenAgent, etc. — all
  candidates behind ports, output never truth. Market map: `research/companies/_market-map.md`.
- **Canonical 5-surface consolidation (2026-06-26)**: the fragmented site systems (dark/Hanken demos +
  light/Inter showcase + portfolio duplicates) collapsed to ONE config-driven scaffolding
  (`scripts/surface_server.py`) → **5 surfaces, 5 URLs** — AI Done Right (hub) · Teleon · Baltor · AIDevObserver ·
  OpenHubForAI — sharing a **byte-identical** light/Inter stylesheet (per-surface accent + copy the only
  difference), each with `/demo`, OpenHubForAI carrying the faceted `/browse` over the registries.
  Playwright-verified live (font=Inter, bg=`#faf7f0`, 0 console errors). Full design reference:
  `docs/DESIGN-BIBLE.md`; enforced by `scripts/check_surface_server.py`. The full hub catalog is still tracked by
  `python3 scripts/check_ai_done_right_surface_family.py --self-test`.
- **Sales safety gate** (`src/baltor/sales/claim_guard.py`) + a configurable Chatbot Guardrail Audit
  (`src/baltor/sales/diagnostics/`) — appears-not-illegal, private-first, authorized-inputs-only, draft-only outreach.

## 4. Prioritized backlog (what the loop should pick from, in order)
1. **Shared I/O spine — finish:** OpenAPI + AsyncAPI generation ✅ DONE (`scripts/build_contract_specs.py` +
   `scripts/check_shared_openapi_asyncapi_specs.py`); standalone I/O redteam ✅ DONE
   (`scripts/check_shared_io_resource_redteam.py`). REMAINING: migrate object families to explicitly conform to
   `ObjectShell` (one family per cycle) + a single I/O full-stack roll-up proof.
2. **Design rollout:** the shared Oh\* kit account pages (auth/billing/usage/settings/dashboard) via `oh-site.jsx`;
   `makeHub` registry sites; MARKETING.md canonical copy; sites for the 3 new hubs.
3. **Hub build-out:** OpenBenchmarkHub contracts/website/API remainder; OpenMCP + OpenCompression contracts +
   **Context Efficiency Spine** + the bake-off harness; the skill-digestion conformance harness.
4. **Competitive intelligence:** `CompanyArtifact`/`SalesWedge` schemas + `competitive_company_registry` +
   per-company `research/companies/*.md`; seed Crusoe/Nscale into the execution-backend catalogs as real candidates.
5. **Repair sweep (every cycle):** JSON-parse + py-compile changed files; `flywheel --once`; heal any flake at the
   source (e.g. raise a too-tight poll timeout), never just re-run.

## 5. HELD — needs owner authorization (do NOT build unilaterally)
- The sales **lead-funnel target maps + any outreach** + **real named-company seeds** + **live third-party
  diagnostics** (probing a third party's production chatbot needs written authorization). See
  `prompts/portfolio-sales-lead-funnel-and-problem-proof-tools.md` and `..._competitive-intelligence...md`.
- Owner-decision items: HoldCo name confirmation; domain/trademark clearance for the new `.io` hubs (marked
  proposed/unverified); the portfolio app/console identity model (see `prompts/portfolio-app-console-build-brief.md`).

## 6. Invariants (the laws — every change honors these)
No-magic-values (one source, computed counts) · Lossless distillation (never replacement) · Change-verification
(warrant before change; design/brand/strategy = owner intent, never unilateral) · discovery≠trust · output≠truth ·
**benchmark result≠promotion authority** · candidate≠active · agents propose / Baltor disposes · branded-house
(only `--accent` differs; never hardcode a hex in a site stylesheet) · exact-pid process management (no `pkill`) ·
no `golden` nomenclature · projection-only dashboards · **no commit/push, no pip (vendor), no containers/cloud, no
network LLM** unless explicitly authorized.

## 7. Run the multi-day loop
The durable EXTERNAL runner makes stopping recoverable (the model may stop; the process should not):
```bash
# validate the contract (launches nothing):
scripts/run_north_star_loop.sh --check
# launch the multi-day loop (run in tmux/screen/nohup so it survives terminal close):
CLAUDE_CODE_CMD='claude -p' nohup scripts/run_north_star_loop.sh > .agent/logs/runner.out 2>&1 &
# stop after the current cycle:  touch .agent/STOP_REQUESTED
# resume:                        rm .agent/STOP_REQUESTED
```
It feeds `prompts/baltor-north-star-continuous-builder.md` each cycle, resumes from
`.agent/north-star-loop-state.json` (refreshed to this snapshot), logs to `.agent/logs/`, and relaunches on a
soft-stop. Each cycle: repair sweep → pick the highest-priority backlog item (§4) → build ONE proven increment →
register its proof + keep the flywheel GREEN → restart the watchdog by exact pid if PROOF_MODULES changed → write a
receipt to `.agent/baltor-goal-loop-log.md`. Receipts are the audit trail; this doc is the orientation.
