# AI Done Right — Claude-Design Family Handoff (current)

> **Read `docs/DESIGN-BIBLE.md` FIRST.** It is the single, designer-ready reference for the LIVE design system
> (478 lines: tokens · type scale · every component · routes · governance · the designer handoff). This file is the
> family orientation; the DESIGN-BIBLE is the canonical *how it looks + how it's built*. If they ever disagree, the
> DESIGN-BIBLE wins. Last reconciled **2026-06-26**. `serves_truth = false` (the surfaces render candidate output;
> only Baltor's governed source serves truth). A BYO key is used only for the request, never stored or logged.

## What is LIVE vs what is the richer REFERENCE

There are two layers here, and a designer needs both — but they play different roles:

1. **The LIVE design system** = **one config-driven server, `scripts/surface_server.py`**. It renders all **5
   surfaces** from ONE template + ONE **byte-identical** stylesheet (`_CSS_TEMPLATE`, ~7959 chars rendered); only the
   per-surface `--accent` and the copy differ. Light theme, **Inter** UI font (+ `ui-monospace` for code/labels).
   Enforced by `scripts/check_surface_server.py` (**122 assertions** — run it; the count is computed, never typed).
   The full reference for this system is **`docs/DESIGN-BIBLE.md`**.
2. **The richer aspirational REFERENCE** = the high-fidelity bundle in **`dist/sites/openharness-design/`** (the 3.2 MB
   Claude-Code-Max design handoff). The canonical tokens in the live server are **derived from** this bundle's
   `dir-a · theme-light` palette (`dist/sites/openharness-design/shared/oh-tokens.css`). The bundle remains the
   canonical *source of record* for the richer component library; the server is the canonical *renderer* for the 5
   shipped surfaces.

**The designer's job (the handoff):** *elevate the live `surface_server` pages toward the richness of the
`dist/sites/openharness-design/` bundle — WHILE keeping the byte-identical-CSS standardization law.* You never style a
single surface; you edit `_CSS_TEMPLATE` once and it propagates to all 5. Full SAFE-vs-LOCKED map: `docs/DESIGN-BIBLE.md` §11.

## The 5 surfaces (single source: `architecture/surface_capability_spec.json` → `scripts/_surface_accents.py`)

| Surface | `--accent` | role | live URL (ephemeral TryCloudflare quick tunnel) |
|---|---|---|---|
| **AI Done Right** | `#5a6b87` | parent / holding brand — the portfolio **HUB / index** | https://flags-employee-robinson-nevada.trycloudflare.com |
| **Teleon** | `#6d5ef0` | purpose-driven, eval-gated, self-adaptive compute runtime | https://commodities-cleaner-entities-dangerous.trycloudflare.com |
| **Baltor** | `#0e7c86` | managed, verified, provable context — governs TRUTH | https://marathon-crop-moore-logistics.trycloudflare.com |
| **AIDevObserver** | `#b25fd6` | watches AI USAGE — reviews the SESSION (post) + intra-session | https://somerset-evaluations-schedules-copying.trycloudflare.com |
| **OpenHubForAI** | `#3b6fd4` | the open store both products consume — carries the faceted **`/browse`** | https://chancellor-photography-coins-cir.trycloudflare.com |

> TryCloudflare URLs are **ephemeral** — they rotate on every launch. The live record is always `dist/surface-urls.json`;
> production uses the stable domains (`aidoneright.dev` · `teleon.dev` · `baltor.ai` · `aidevobserver.io` ·
> `openhubforai.io`). See `docs/DESIGN-BIBLE.md` §10.

## Read order (start to finish)

1. **`docs/DESIGN-BIBLE.md`** — the design system (tokens, type, components, routes, governance, SAFE-vs-LOCKED).
2. **`scripts/surface_server.py`** — THE live renderer (`_CSS_TEMPLATE` + the `render_*` helpers).
3. The **5 live URLs** above (or run `python3 scripts/surface_server.py <surface-id>` locally).
4. **`dist/sites/openharness-design/`** — the richer bundle to elevate toward (start at `START-HERE-CLAUDE-CODE.md`).
5. This file + `HANDOFF.md` here for family shape, the Baltor method spine, and production gaps.

## Brand

Parent company: **AI Done Right** (`aidoneright.dev`) · Tagline: **AI, done right.** · Thesis: **discovery is not trust**.
Legacy paths such as `context-is-everything/` and `context-enrichment/` stay in place in the bundle for prototype
cross-link stability. Displayed brand and product names are current.

## Family Shape

The live shipped model is the **5 surfaces** above. The wider design family (parent + Baltor + Teleon + the
Open\*Hub registries) is a **computed** count — never hand-counted. Recompute before changing docs, screenshots, or
Control Tower copy:

```bash
python3 scripts/check_ai_done_right_surface_family.py --self-test
```

The bundle (`dist/sites/openharness-design/shared/products.js`) is the single source for the wider registry roster.

## Baltor Method Spine

| Hub | Stage | Hero | Method family |
| --- | --- | --- | --- |
| OpenReconciliationHub.io | Reconcile | Cluster alignment. | dedupe; link evidence; surface conflicts |
| OpenHardeningHub.io | Harden | Robust object hardening. | detect fragile values; create durable objects; refresh over time |
| OpenEnrichmentHub.io | Enhance | Context enrichment. | add metadata; connect objects; increase robustness |
| OpenOptimizationHub.io | Optimize | Pack shaping. | summarize; structure; rank |
| OpenVerificationHub.io | Verify | Cited and provable. | bind claims to sources; prove by hash; hold out the unprovable |

These are private-first registry surfaces. They open the method language around Baltor's engine, but they do not become
truth authorities. Baltor governs truth.

## Branded-House Contract

- One shared design system — enforced now by the byte-identical-CSS law in `scripts/surface_server.py` (see DESIGN-BIBLE §1).
- One shared type scale, spacing system, surface primitive, and theme mechanism.
- One source of brand identity + accents: the live server reads `architecture/surface_capability_spec.json`; the bundle's
  roster source is `shared/products.js`.
- Private bench hubs use muted accents and a private-preview state until owner-gated release. Production must enforce
  private-first access server-side — the prototype only renders the intended state.

## Production Gaps

The bundle prototypes are design references. A production build still needs:

1. Vite/Next or equivalent with precompiled JSX (the live `surface_server` is the standardized server-rendered floor).
2. A real backend, API, datastore, ingest, verification, and engine pipeline.
3. Real auth, persistence, billing, tenant management, and audit.
4. Real registry data and source provenance.
5. Service-to-service auth and consumption per `docs/architecture/service-auth-and-consumption-model.md`.

## Do Not Regress

- Do not break the **byte-identical-CSS law** (accent + copy are the only per-surface variables — DESIGN-BIBLE §11 LOCKED).
- Do not rename legacy prototype folders unless every relative link is swept.
- Do not hardcode counts, colors, ports, or brand copy that has an owning source (recompute / read the spec).
- Do not present private bench hubs as public production surfaces.
- Do not present Open\*Hub discovery as trust.
- Do not let Teleon own Baltor truth or Baltor become a generic runtime.
