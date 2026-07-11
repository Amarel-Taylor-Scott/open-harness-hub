# Goal: Dynamic Repo Polish Loop

This is a long-horizon goal for Codex, Claude Code, or another repo agent. It
should keep looping until the repository is demonstrably polished across the
actual current surface area: websites, demos, generated static sites, docs,
catalog/schema integrity, runtime entrypoints, launch/share flows, and release
hygiene.

The goal is intentionally discovery-driven. Do not anchor the loop on stale
phrases like "four sites" or any other fixed cardinality. Recompute the current
repo shape from owning sources every cycle, then fix the highest-impact gap.

## Mission

Polish this repository into a credible, shippable, review-ready platform:

- **Baltor** is a clear, working governed-context product.
- **OpenHubForAI** is a usable public standards/catalog and builder funnel.
- **Context is Everything / AI Done Right** explains the portfolio and why
  governed context is the durable control layer.
- **Teleon, OpenContextHub, OpenSkillsHub, OpenToolsHub, OpenHubForAI, and
  any newly added portfolio or design surfaces** have distinct, accurate,
  shareable boundaries.
- **Catalog, schemas, scripts, docs, generated artifacts, and launch manifests**
  are internally consistent and pass focused checks.

Do not stop after one improvement. Repeat the loop until every gate below is
green, or until the human interrupts.

## Read First

1. `AGENTS.md`
2. `README.md`
3. `taxonomy/SPEC.md`
4. `docs/codex/no-magic-values.md`
5. `_repos/_shared/codex/master-goal.md`
6. `docs/goals/aidoneright-portfolio-loop.md`
7. `docs/codex/ai-done-right-family-polish-goal.md`
8. `_repos/aidoneright/context/handoff/handoff-freshness.md`
9. `_repos/openhubforai/context/handoff/openhub-surface-counts.md`
10. `docs/codex/baltor-always-in-memory-context.md`
11. `docs/codex/baltor-clean-context.md`
12. `docs/codex/change-verification-contract.md`
13. `docs/architecture/service-auth-and-consumption-model.md`
14. `_repos/aidoneright/context/strategy/brand-architecture.md`
15. `services/registry.yaml`
16. `scripts/portfolio_lib.py`
17. `architecture/demo_surface_registry.json`

When these disagree, resolve the contradiction in the smallest defensible way.
Never silently delete context-bearing artifacts or `_inbox/` drafts.

## Surface Discovery First

Every cycle starts by deriving a fresh surface inventory from sources of truth.
Exact counts in prose, comments, checks, or old runbooks are assertions to
verify, not constraints to obey.

Read these owning sources before choosing a gate:

- `services/registry.yaml` for active product web roots, commands, env, tiers,
  and status.
- `web/**` for source HTML pages, product subpages, manifests, pipeline pages,
  stage pages, dashboards, and admin/demo source surfaces.
- `scripts/portfolio_lib.py` for portfolio site IDs, order, hub port, site
  ports, brand boundaries, required phrases, and generated portfolio content.
- `architecture/demo_surface_registry.json` for the Demo Control Tower view of
  active, candidate, and internal surfaces.
- `dist/sites/**` for rendered/generated static site roots and prototype/design
  pages that exist as reviewable outputs.
- `.agent/portfolio-sites/urls.json`, `dist/*url*`, `dist/*urls*`, and
  `dist/showcase-*url*` for captured local/public URL manifests.
- `mkdocs.yml`, `docs/**`, `hf-space/**`, `vercel.json`, `netlify.toml`,
  `_headers`, and `_redirects` for documentation and deployment surfaces.

Treat every mismatch as drift to reconcile. If a check says "4 sites" but the
registry says more, fix the check/doc/comment or make it compute from the
registry. Do not narrow the repo back to the stale number.

## Surface Classes To Recompute

Recompute these classes each loop before scoring work:

1. **Product web roots** from `services/registry.yaml`.
2. **Source website pages** from `web/**`, including Baltor pipeline/stage,
   dashboard, guided-demo, review, standards, native, memory, integration, and
   related subpages.
3. **Portfolio static sites and hub** from `scripts/portfolio_lib.py`.
4. **Demo/control/ops surfaces** from `architecture/demo_surface_registry.json`.
5. **Generated static outputs** from `dist/sites/**`, including design-system
   prototypes and special control-tower pages.
6. **Docs/deploy surfaces** from `mkdocs.yml`, `docs/**`, `hf-space/**`,
   Vercel/Netlify/Pages config, redirects, and headers.
7. **Live share surfaces** from URL manifests and active tunnel/server state.

The inventory should be recorded as a point-in-time trace, not a new permanent
source of truth. Prefer `.agent/repo-polish-surface-inventory.md` or the loop
log for traces.

## Definition Of Fully Polished

The repo is polished only when all of these are true:

1. **Workspace hygiene**
   - Git status is understood and summarized by category.
   - Accidental file-mode churn is removed or explicitly justified.
   - Generated artifacts are reproducible, intentionally tracked, or clearly
     documented as run output.
   - New sample data contains no secrets, real PII, or private dumps.

2. **Surface inventory and routing**
   - Every discovered active surface is accounted for with owner, source,
     status, local path/port when applicable, and launch/share expectations.
   - Active product roots and generated site roots serve locally when their
     launchers are expected to run.
   - Candidate/internal surfaces are honestly labeled and are not advertised as
     live public surfaces.
   - Stale fixed counts are eliminated or converted to computed assertions.

3. **Live sharing**
   - When the task is to share demos, every required public URL is a real
     `*.trycloudflare.com` URL captured from the launcher or manifest.
   - A URL is not reported as working until it returns HTTP 200 for the
     expected health path.
   - Server/tunnel status, stop, restart, and manifest locations are clear.

4. **Frontend polish**
   - No overlapping text, broken layout, dead primary links, inaccessible
     buttons, or incoherent responsive behavior at desktop and mobile widths.
   - Pages show actual product/workflow content first; demos do not collapse
     into marketing-only splash pages.
   - Repeated UI primitives follow existing local design conventions.
   - Brand markers and cross-links make ownership legible without blurring
     product boundaries.

5. **Documentation polish**
   - Docs explain the current architecture, not stale names or counts.
   - Long-running goals, launch instructions, and share-URL instructions match
     current scripts and manifests.
   - Research notes are marked as candidate intelligence unless implemented and
     tested.
   - Counts, ports, model IDs, schema families, thresholds, paths, and URLs are
     computed or read from owning sources, not hand-copied as durable truth.

6. **Catalog and taxonomy integrity**
   - Catalog manifests validate.
   - Component IDs and slugs follow the no-version-in-name rule.
   - Pipelines never wire raw rule packs directly to models; rule packs reach
     models through harnesses.
   - Every harness declares `model_targets`, including `none`.
   - Volatile facts live in tools or knowledge packs, not personas.

7. **Runtime and worker integrity**
   - Advertised backend entrypoints start without import/runtime errors.
   - Queue, worker, ingestion, memory, inference, export, and admin paths shown
     by the UI have working implementations or honest planned/disabled states.
   - Logs and generated receipts point to real artifacts.

8. **Verification**
   - Run focused checks for touched areas.
   - Run broader repo checks when the blast radius touches shared schemas,
     catalog generation, product launch, routing, or common UI helpers.
   - Any skipped check is recorded with the exact reason.

## The Loop

```text
ORIENT
  Read the canonical docs, git status, current branch, active servers, and
  generated URL/state files.

DISCOVER SURFACES
  Derive the current inventory from registry files, web source files,
  portfolio_lib, demo_surface_registry, dist/sites, docs/deploy config, and
  URL manifests. Do not hand-type parallel lists.

SCORE
  Pick the highest-impact failing polish gate using this order:
  1. active user-visible surface down, unlaunched, misrouted, or missing from inventory
  2. public share URL missing, fake, stale, or not returning HTTP 200
  3. runtime/import error in an advertised entrypoint
  4. data/security/privacy risk
  5. invalid catalog/schema/build or broken generated artifact
  6. misleading product claim, brand-boundary confusion, or stale architecture doc
  7. visible frontend/layout/accessibility problem
  8. stale fixed count, magic value, duplicated source of truth, or reproducibility gap
  9. cleanup, consolidation, and final pass

BUILD
  Make the smallest durable change that clears the selected gate. Prefer
  existing scripts, schemas, helpers, registries, and design primitives.

VALIDATE
  Run the focused proof for the changed area. If a command fails because the
  environment is missing a dependency or network access, use the approved path
  or record the exact blocker and switch to another gate.

RECORD
  Update the surface inventory trace, loop log, runbook, generated share file,
  or docs page with what changed, what passed, what failed, and what remains.

REPEAT
  Re-run discovery and score. Continue until every gate is green.
```

## Launch And Share Surface Checks

Use repo launchers and manifests before inventing ports:

- Product surfaces: `bash scripts/serve_all_sites.sh`
- Product tunnel verification: `python3 -m scripts.showcase.verify_tunnels`
- Portfolio local servers: `PYTHONPATH=. python3 scripts/serve_portfolio_sites.py --restart`
- Portfolio tunnels: `PYTHONPATH=. python3 scripts/launch_portfolio_trycloudflare.py --restart`
- Portfolio URL manifest: `.agent/portfolio-sites/urls.json`
- Product URL artifacts: `dist/showcase-share-url-<id>.txt`
- Demo/control tower registry: `architecture/demo_surface_registry.json`
- Consolidated share outputs: `dist/demo-all-urls.*`, `dist/cloudflare-urls.md`,
  and related `dist/*url*` manifests.

If a tunnel helper captures a URL but it returns a Cloudflare error, verify the
local port first, then restart the tunnel in detached mode or fix the launcher.
Do not report a public URL as working until it returns HTTP 200.

## Documentation And Research Rules

- Candidate tools stay candidates until separately evaluated.
- External research claims need dates, links, and clear source attribution when
  they affect product, market, security, legal, or dependency choices.
- For context-engineering, memory, compression, code graph, and tool-output
  isolation research, preserve the distinction between:
  - token/waste observability;
  - context compression;
  - tool-output isolation;
  - repo/code context selection;
  - memory/RAG dedupe and conflict detection.
- A generalized Context Auditor is a product gap to document as a proposal, not
  a runtime claim, unless implemented and tested.

## Stop Conditions

Stop only when one of these is true:

- Every gate in **Definition Of Fully Polished** is green and the final status
  report lists checks plus verified URLs when live sharing is in scope.
- The human explicitly interrupts or redirects the task.
- A hard safety issue blocks all safe work. In that case, record the blocker,
  attempted workarounds, and the exact user decision needed.

Do not stop merely because one path is blocked. Switch to the next highest-value
failing gate and continue.

## Final Report Shape

When the loop is complete, report:

- current branch and workspace hygiene status;
- discovered surface classes and any launched/verified URLs;
- files changed;
- checks run and results;
- remaining risks, if any;
- next recommended gate only if the repo is not fully polished.
