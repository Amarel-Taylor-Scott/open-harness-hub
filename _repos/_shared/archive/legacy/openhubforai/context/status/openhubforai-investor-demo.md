# OpenHubForAI.io — investor demo (public URL, fully wired)

Status 2026-06-10: **live and verified end-to-end through the public URL.**

- **Share URL (with access token):** `dist/showcase-share-url-openhubforai.txt`
- Tunnel hostname only: `dist/showcase-tunnel-url-openhubforai.txt`
- Compute endpoints (`/api/build`, `/api/export`) are token-gated; the share link carries the
  token and the app remembers it per browser. Catalog/identity/registry/analytics reads are open.

## Proof it works (all run against the PUBLIC URL, not localhost)

| Gate | Result |
|---|---|
| `e2e/ohh_public_gate.mjs` — the investor journey through the tunnel | **10/10** (landing · REAL build · live catalog · REAL sign-up + session · workspace · identity/registry seams · beacon 202 · console clean) |
| `e2e/ohh_route_audit.mjs <tunnel>` — every route, logged-out AND logged-in | **46/46 + 46/46**, zero console errors |
| Live catalog | browse pool **1,771 components** (of **2,411** catalog rows incl. 386 pipelines), real governance fields (license / lifecycle / industry / provenance) from the catalog YAMLs |
| Honesty checks | live pipelines show **“— unproven”** (never a fabricated lift number); fixture exemplars remain only on designed sample surfaces |
| Backend self-tests | identity runtime (realm isolation, hash-only keys, restart-safe persistence) · registry backend (promotion gate, separation of duties, lossless revoke) · services health — all PASS |

Screenshots: `e2e/artifacts/full-design/public-live-preview.png`, `public-workspace.png`,
`ohh-live-browse.png`, `ohh-live-detail.png` · journey video: `artifacts/e2e/videos/journey-1-openhubforai.mp4`.

## Suggested click path for the investor

1. Open the share link → the full-design landing.
2. Type a task (e.g. *“screen supplier disclosures for forced labor and cite the exact
   regulations”*) → **Build** → watch the REAL backend assemble a governed flow (steps, stage
   groups, cost band, deterministic-vs-model selection — live data, honest labels).
3. **Explore components** → the real 2,400+-row registry with facets; open any component for
   governance detail (license, lifecycle, provenance when recorded).
4. **Start free** → create a real account (own identity realm; sessions are real, passphrase
   never stored) → the signed-in workspace, Foundry, Governance, Settings.
5. Pricing → `#/checkout` / `#/upgrade` show the commercial surfaces (payment is emulated).

## What is real vs. designed sample (so nobody oversells)

- **Real:** the build engine (`/api/build` over the 2,411-component index + embeddings),
  the browse/detail catalog with YAML governance metadata, accounts/sessions/API-key mint
  (identity service, disk-persisted), registry workspace seams, analytics ingest, all 46 routes.
- **Designed sample (intentionally, captioned in data):** tier cards on `/results`, the `/flow`
  canvas exemplar, workspace activity fixtures, billing/checkout (emulated — no charges).

## Ops — if the link stops answering

The tunnel is a detached `cloudflared` quick tunnel; the hostname changes if it is recreated.

```bash
# servers + services (token-gated compute):
OH_SHOWCASE_TOKEN=$(cat dist/showcase-token.txt) python3 scripts/start_local_services.py
# tunnel (writes a NEW hostname → refresh both dist url files):
setsid ~/.local/bin/cloudflared tunnel --no-autoupdate --url http://127.0.0.1:8000 \
  >> dist/local-services/cloudflared-openhubforai.log 2>&1 &
# then re-verify the journey against the new URL:
node e2e/ohh_public_gate.mjs "$(cat dist/showcase-share-url-openhubforai.txt)"
```
