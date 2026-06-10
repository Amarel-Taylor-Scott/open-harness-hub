# PARITY REPORT — full-design transplant into the wired web/ apps

Date: 2026-06-10 · Per `dist/sites/openharness-design/DESIGN-CONTRACT.md` Rule 7/9.
Implementation: `scripts/port_full_design_to_web.py` (deterministic transplant + `--check` drift
gate) · seams: `scripts/showcase/server.py` · verification: `e2e/full_design_apps.mjs`
(27/27 checks green; screenshots in `e2e/artifacts/full-design/`).

## Scope

The three WIRED product front-ends now serve the full-design surfaces, wired to real local
backends. The other 21 design surfaces (Teleon + the Open*Hubs + internal planes) are served
verbatim from the bundle on every product origin (root mounts + `/design/`), so every
cross-surface link in the verbatim code resolves; the Demo Control Tower indexes them.

| Surface | Ref image | Routes pass | Copy verbatim | Tokens diff clean | Dark OK | Console clean | Parity |
|---|---|---|---|---|---|---|---|
| AI Done Right (web/context-is-everything) | 01 + live prototype | ✓ (single-page + tower) | ✓ | ✓ (kit byte-identical) | ✓ (kit toggle) | ✓ | ✓ |
| Demo Control Tower (served from parent origin) | 02 + live prototype | ✓ | ✓ | ✓ | n/a (dark surface) | ✓ | ✓ |
| Baltor.ai (web/baltor) | 03 + live prototype | ✓ 12/12 sampled (marketing + console + kit pages) | ✓ | ✓ | ✓ (kit toggle) | ✓ | ✓ |
| OpenHarnessHub (web/harness-hub) | 13 (broken — see D3) + live prototype | ✓ 8/8 sampled | ✓ | ✓ | ✓ (`ohp-mode` override, as prototype) | ✓ | ✓ |

Wired (REAL, with honest fallback when a service is down — the kit never fabricates state):

- **Identity**: kit `OhAuth` → `/api/identity/*` → `scripts/identity_local_service.py` (per-realm,
  no SSO). e2e creates a real account and observes the per-realm session (`oh-session-*`).
- **Registry**: kit workspace/dashboard pages → `/registry/*` → `scripts/registry_local_service.py`.
- **Analytics**: page beacon → `/analytics/*` → `scripts/events_local_service.py` (202 verified).
- **Build**: OHH landing task → `/api/build` → the real component index; the logged-out preview
  renders the REAL assembled flow (steps, stage groups, cost, model-vs-deterministic selection).
  Live builds show no fixture lift number (the wired app's honesty rule; designed sample keeps it).
- **Baltor live ops**: legacy pages (`dashboard.html`, `demo-console.html`, …) now work on the
  product origin through the seam proxy to `baltor_admin_demo_server` (port single-sourced in
  `architecture/local_service_registry.json`).

## Discrepancies found and resolved from source (Rule 9 — repo is truth)

- **D1 — `screens/01` is a stale capture.** The private bench now renders 13 chips (incl.
  OpenRoutingHub, OpenReconciliationHub, …) because `shared/products.js` grew after the capture.
  Implementation follows `products.js` (single source). No action; reference predates the roster.
- **D2 — headline/subhead/CTA differ between captures.** Sticky per-visitor A/B assignment
  (`oh-experiments.js`) picking different variants (e.g. Baltor HEADLINE B vs C). All variant copy
  is verbatim design copy; `?exp=` forcing verified. Working as designed.
- **D3 — `screens/13-openharnesshub.png` is a broken reference** (blank dark frame with only the
  theme switcher; capture-time failure). Parity was gated against the LIVE prototype
  (`:9210/openharnesshub/…`) instead — structures match 1:1.
- **D4 — bundle beacon bug fixed at source.** `shared/oh-identity.js` sent an empty `name` when a
  surface is served at `/` (impossible at `file://`/`:9210` where pages are `*.html`), and the
  events plane 400s empty names. Fixed in the bundle (`|| "/"` fallback) — wiring fix, no design
  change; `check_bundle_full_design_wiring` still green.
- **D5 — SSE is not proxied.** `/api/events/stream` answers 501 on product origins by design; the
  live dashboard's documented polling fallback covers it (deduped client-side). Direct
  `baltor_admin_demo_server` origin still serves SSE.

## Addendum 2026-06-10 (later) — journey videos + two wiring deepenings

- **Recorded user-journey videos** (`e2e/record_user_journeys.mjs` → `artifacts/e2e/videos/`,
  manifest `docs/status/user-journey-videos.md`): full lifecycle per app — landing → browsing →
  REAL per-realm sign-up → emulated billing (captioned EMULATED) → product use (REAL `/api/build`
  preview · REAL pipeline run on the live event bus) → configuration (REAL API-key mint/revoke on
  an open hub). Frame-verified: live preview steps/cost, signed-in dark workspace, streaming
  pipeline events (+0.5769 lift run), shown-once key reveal (`ak_opencontexthub_…`).
- **Kit `OhApiKeys` wired at the bundle source** (same honesty contract as OhAuth): "+ Create key"
  mints through `OHIdentity.mintKey` against the signed-in realm; one-time raw-key reveal; minted
  rows individually revocable; fixture rows stay design data; signed-out / service-down → honest
  note, never a fabricated key. (makeHub's own hub console keys page was already live-wired.)
- **Real-session → app-mode bridge** (recorded patch, `proto-main.jsx`): a real OHH realm session
  flips the proto's signed-in mode on mount/route-change. Reflects real state only — the
  prototype's `ohp-auth` demo flag keeps working; no fake sessions.

## Addendum 2026-06-10 (OHH investor pass) — live catalog + a tunnel-only bug fixed at source

- **OHH browse/detail wired to the REAL registry**: `/api/components` now carries the catalog
  YAMLs' real governance fields (license/lifecycle/industry/modality/provenance — 2,664 rows,
  cached with a locked background pre-warm); `ohh-live.js` hydrates the design's
  COMPONENTS/BY_SLUG globals (2,411 rows, 1,771 components + pipelines) with recorded re-render
  patches. Honesty patches: live pipelines without measured lift render “— unproven” (the fixture
  default would have fabricated `+0.40`), provenance/cost cells show real values or “—”.
- **D6 — falsy same-origin override (found ONLY by the public gate):** `oh-identity.js#base()`
  used `window.OHH_IDENTITY_BASE || DEFAULT` — the injected `''` (same-origin) is falsy, so auth
  silently fell back to `127.0.0.1:9410`: fine locally, CORS-dead through a tunnel. Fixed at the
  bundle source (`== null` check). Lesson recorded: tunnel-origin verification is part of the
  definition of done for seams.
- **Public investor gate green**: `e2e/ohh_public_gate.mjs` 10/10 and the full route audit
  (46/46 ×2 modes) against the live trycloudflare URL; brief:
  `docs/status/openharnesshub-investor-demo.md`.

## Decisions (recorded; revisit when deepening the wiring)

- The OHH logged-in console pages (`/build` confirm, `/results` tiers, `/flow` canvas) keep their
  designed exemplar data this increment; the logged-out funnel (landing → preview) is live. The
  legacy builder UI with its data-driven DAG renderer stays reachable at `/legacy.html` (lossless).
- Old front pages preserved as `web/<app>/legacy.html`; every legacy functional page
  (`admin-demo`, `dashboard.html`, guided pipeline/stage pages, …) keeps its URL.
- In-browser Babel + pinned vendored React (`web/vendor/`) exactly as the prototypes pin them;
  precompiled-JSX production tooling stays a later step (IMPLEMENTATION-GUIDANCE “judgment calls”).
