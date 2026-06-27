# AI Done Right — Tracked Design Handoff (current · reconciled 2026-06-26)

> **Read `DESIGN-BIBLE.md` FIRST** — the single, designer-ready reference for the LIVE design system
> (tokens · type scale · every component · routes · governance · the SAFE-vs-LOCKED designer handoff, 478 lines).
> This file is the **family + production handoff**: the family shape, the Baltor method spine, service-to-service
> auth, and the production gaps. The companion orientation next to it is `FAMILY-README.md`. If any of these
> disagree with the DESIGN-BIBLE, the DESIGN-BIBLE wins. `serves_truth = false` (the surfaces render candidate
> output; only Baltor's governed source serves truth). A BYO key is used only for the request, never stored or logged.

## The LIVE design system (what a designer ships into)

ONE config-driven server — **`scripts/surface_server.py`** — renders all **5 surfaces** from ONE template + ONE
**byte-identical** stylesheet (`_CSS_TEMPLATE`, ~7959 chars rendered); only the per-surface `--accent` and the copy
differ. Light theme, **Inter** UI font (+ `ui-monospace` for code/labels). Enforced by
`scripts/check_surface_server.py` (**122 assertions** — run it; the count is computed, never typed). The richer
aspirational REFERENCE the canonical tokens derive from is the high-fidelity bundle `dist/sites/openharness-design/`
(`dir-a · theme-light` palette in `dist/sites/openharness-design/shared/oh-tokens.css`).

**The designer's job:** *elevate the live `surface_server` pages toward the richness of the
`dist/sites/openharness-design/` bundle — WHILE keeping the byte-identical-CSS law.* You never style one surface; you
edit `_CSS_TEMPLATE` once and it propagates to all 5. Full SAFE-vs-LOCKED map: `DESIGN-BIBLE.md` §11.

### The 5 surfaces (single source: `architecture/surface_capability_spec.json` → `scripts/_surface_accents.py`)

| Surface | `--accent` | role | live URL (ephemeral TryCloudflare quick tunnel) |
|---|---|---|---|
| **AI Done Right** | `#5a6b87` | parent / holding brand — the portfolio **HUB / index** | https://flags-employee-robinson-nevada.trycloudflare.com |
| **Teleon** | `#6d5ef0` | purpose-driven, eval-gated, self-adaptive compute runtime | https://commodities-cleaner-entities-dangerous.trycloudflare.com |
| **Baltor** | `#0e7c86` | managed, verified, provable context — governs TRUTH | https://marathon-crop-moore-logistics.trycloudflare.com |
| **AIDevObserver** | `#b25fd6` | watches AI USAGE — reviews the SESSION (post) + intra-session | https://somerset-evaluations-schedules-copying.trycloudflare.com |
| **OpenHubForAI** | `#3b6fd4` | the open store both products consume — carries the faceted **`/browse`** | https://chancellor-photography-coins-cir.trycloudflare.com |

> TryCloudflare URLs are **ephemeral** — they rotate on every launch. The live record is always `dist/surface-urls.json`;
> production uses the stable domains (`aidoneright.dev` · `teleon.dev` · `baltor.ai` · `aidevobserver.io` ·
> `openhubforai.io`). See `DESIGN-BIBLE.md` §10.

## Read order (Claude design / Claude Code Max)

1. **`DESIGN-BIBLE.md`** — the design system (tokens, type, components, routes, governance, SAFE-vs-LOCKED).
2. **`scripts/surface_server.py`** — THE live renderer (`_CSS_TEMPLATE` + the `render_*` helpers).
3. The **5 live URLs** above (or run `python3 scripts/surface_server.py <surface-id>` locally).
4. **`dist/sites/openharness-design/`** — the richer bundle to elevate toward, and the source of the production React
   kit. Start at `START-HERE-CLAUDE-CODE.md`, then `README.md`, `CLAUDE-CODE.md`, `HANDOFF.md`,
   `IMPLEMENTATION-GUIDANCE.md`, `BACKEND-STACK.md` (the detailed port steps + backend stack live there).
5. **`docs/architecture/service-auth-and-consumption-model.md`** — service-to-service auth + consumption model.

## Family shape (computed — never hand-counted)

The live shipped model is the **5 surfaces** above. The wider design family (parent + Baltor + Teleon + the
OpenHubForAI registries — 9 live open registries + private-bench registries) is a **computed** count, never typed into
prose. Recompute before editing docs, screenshots, or Control Tower copy:

```bash
python3 scripts/check_ai_done_right_surface_family.py --self-test
```

The bundle's `dist/sites/openharness-design/shared/products.js` is the single source for the wider registry roster.

## Baltor method spine

The private-first method hubs open the method language around Baltor's engine — they do **not** become truth
authorities (Baltor governs truth):

```text
Reconcile → Harden → Enhance → Optimize → Verify
OpenReconciliationHub.io · OpenHardeningHub.io · OpenEnrichmentHub.io · OpenOptimizationHub.io · OpenVerificationHub.io
```

## Service-to-service auth (not API keys)

Do **not** treat API keys as the internal service-to-service model. Production needs: user OIDC/session auth; scoped
external API keys or OAuth clients; service accounts + short-lived scoped service tokens; mTLS/SPIFFE or cloud
workload identity for internal production calls; private-bench access enforcement; tenant/object/purpose/data-class
authorization; audit events + receipts for privileged calls. Brief:
`docs/architecture/service-auth-and-consumption-model.md`.

## Production gaps (the bundle is a design reference, not a deploy)

1. A precompiled build (Vite/Next or equivalent) — the live `surface_server` is the standardized server-rendered
   floor; the production React kit is the bundle's own port path (`IMPLEMENTATION-GUIDANCE.md`).
2. A real backend, API, datastore, ingest, verification, and engine pipeline (`BACKEND-STACK.md`).
3. Real auth, persistence, billing, tenant management, and audit.
4. Real registry data and source provenance.
5. Service-to-service auth + consumption per the brief above.

## Verification gates (do not regress)

- `python3 scripts/check_surface_server.py --self-test` stays green — the **byte-identical-CSS law**: accent + copy
  are the only per-surface variables (DESIGN-BIBLE §1 / §11 LOCKED). Never add a per-surface stylesheet or a second
  accent-like token.
- `serves_truth = false` + the governance footer + the never-store / never-echo BYO-key contract are present on
  every page.
- Brand + accent values come from the owning source (`architecture/surface_capability_spec.json`); route maps and
  surface counts are generated / recomputed, never typed.
- Private-first is not claimed as production security until enforced server-side.
- OpenHubForAI discovery is never presented as trust; Teleon never owns Baltor truth, and Baltor never becomes a
  generic runtime.

## Do not regress (brand + structure)

- Do not break the byte-identical-CSS law (DESIGN-BIBLE §11 LOCKED).
- Do not rename legacy prototype folders in the bundle unless every relative link is swept.
- Do not hardcode counts, colors, ports, or brand copy that has an owning source (recompute / read the spec).
- Do not present private-bench hubs as public production surfaces.
- **Inter UI + `ui-monospace`** are the canonical fonts; changing the type *system* is a design decision requiring
  owner intent (resizing within the scale is safe).
