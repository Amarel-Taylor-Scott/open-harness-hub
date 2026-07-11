# Teleon.dev — wired demo (public URL, verified end to end)

Status 2026-06-10: **live and verified through the public URL.**

- **Share URL:** `dist/showcase-share-url-teleon.txt` (no token needed — Teleon's surfaces don't
  use the gated compute endpoints)
- Local: `http://127.0.0.1:8003/` (`teleon_app` in `_repos/shared-backend-components/architecture/local_service_registry.json`,
  `OH_PRODUCT=teleon` → `_repos/teleon/frontend/`, transplanted by `_repos/shared-backend-components/scripts/port_full_design_to_web.py`)

## Proof (all checks also run against the PUBLIC URL)

`e2e/teleon_gate.mjs <url>` — **14/14**:
27/27 routes logged-out AND signed-in, console-clean · REAL sign-up on the `teleon` identity
realm (session verified) · REAL API-key mint with shown-once reveal + real revoke (the kit
`OhApiKeys` live seam) · registry seam 200 · analytics beacon 202 · A/B engine `?exp=teleon_hero:D`
forcing verified · theme toggle light/dark · ⌘K command palette (app shell) · PurposeTask Control
Tower page console-clean.

Parity: front page matches `screens/04-teleon.png` (differences = the `teleon_hero` /
`teleon_landing` experiment variants — the A/B chip displays the active variant by design).

Video: `artifacts/e2e/videos/journey-4-teleon.mp4` (88s, 25 chapters, recorded through the
tunnel; manifest in `_repos/shared-backend-components/docs/status/user-journey-videos.md`).

## What is real vs. designed (honest split — updated after the carbon-copy pass)

- **Real:** every route; per-realm accounts/sessions (disk-persisted); API-key mint/revoke
  (hash-only at rest); registry + analytics seams; the A/B engine with URL forcing; ⌘K; themes;
  **and the capability lifecycle** — `_repos/shared-backend-components/scripts/teleon_local_runtime.py` really executes the
  seeded deterministic capabilities ("Build capability" runs the example suite NOW: receipts
  with hashes/timing, the promotion gate applied to the real pass-rate, version bumps), and the
  Capabilities table, dashboard counters, and usage all read that real state (18/18 gate, local
  + public tunnel).
- **Designed (by design, not simulation):** the evidence/library pages are copy pages in the
  spec; billing/checkout is EMULATED (captioned — no charges). The full PurposeTask runtime
  (model-calling, self-adapting) remains the separate greenfield build
  (`_repos/dev-rules-context/prompts/teleon-build-kit.md`); the local runtime is its honest deterministic demo plane.

## Ops

```bash
OH_SHOWCASE_TOKEN=$(cat dist/showcase-token.txt) python3 _repos/shared-backend-components/scripts/start_local_services.py
setsid ~/.local/bin/cloudflared tunnel --no-autoupdate --url http://127.0.0.1:8003 \
  >> dist/local-services/cloudflared-teleon.log 2>&1 &
node e2e/teleon_gate.mjs "$(cat dist/showcase-tunnel-url-teleon.txt)"
```
