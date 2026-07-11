# E2E Review Index — what to open and in what order

Generated 2026-06-09 by the Browser E2E + Local Service Emulation Gate. Everything below was
recorded in **real Chrome** against the **running local stack** (no mocks of the flows themselves;
the identity service, sessions, and API keys are real local objects).

## 0. THE FULL USER JOURNEY (watch this first) — landing → consumption

**`artifacts/e2e/videos/full-journey.mp4`** — one continuous recording of the whole arc on the
real running surfaces, every action real:
**landing** (OpenHubForAI) → **register** a real account (live identity service) → **sign
up / onboard** (real realm session) → **configure** the governed pipeline → **integrate** (mint
the API key your agent calls with — server-verified, blurred in every frame) → **ingestion**
(the source→reconcile→harden pipeline runs) → **consumption** (governed, cited output) →
**Baltor engine climax** (the animated Source→Reconciliation→Anti-Fragility→Enhancement→
Optimization→Consumption canvas + served verified answer with receipt). 11 labeled stages;
stills `journey-01…11-*.png`; report `journey-full-report.md`.

## 1. The auth end-to-end story

- **`artifacts/e2e/videos/portal-register-login-keys.mp4`** (webm twin alongside) — one
  CONTINUOUS native recording: sign-up → register (real account in the `openharnesshub` realm) →
  onboarding → account activation + auto-login (real realm session) → API-keys console → mint
  (key blurred in every frame; verified server-side) → revoke → logout → sign back in → session
  restored.
- Step-by-step stills: `artifacts/e2e/screenshots/portal-01-*.png` … `portal-10-*.png`
- Machine report: `artifacts/e2e/reports/portal-flow-report.md` (10/10 PASS)

## 2. Every running surface (one video + 3 screenshots each)

- Videos: `artifacts/e2e/videos/crawl-<surface>.mp4` + `.webm` (11 surfaces: portfolio hub 9100,
  the 7 launch sites 9101–9107, harness-hub app 8000, baltor app 8001, context-is-everything 8002)
- Screenshots: `artifacts/e2e/screenshots/<surface>-{1440,1280,390}px.png`
- HTML snapshots: `artifacts/e2e/html/` · Console captures: `artifacts/e2e/console/`
- Crawl report: `artifacts/e2e/reports/crawl-report.md` (11/11 loaded, 0 page errors, 0 overflow)

## 3. Honest findings & held items

- **Dead links: FIXED — 0 portfolio-wide.** The crawler originally caught 7 dead cross-site links
  per launch site (hub-rooted links 404'd on per-port servers). Fixed at the server seam:
  `scripts/portfolio_site_server.py` 302-redirects sibling paths to their own ports. A residual
  design-bundle link (`openenvironmenthub/` full-words path vs the legacy `openenvhub/` folder)
  was corrected per the legacy-path law. The crawl now covers **16 surfaces** including the Demo
  Control Tower (9000) and the design-bundle preview + its 3 internal consoles (9210) — both
  formerly held, now live (the tower's RED proof traced to an un-propagated brand rename in
  `demo_surface_registry.json`, now green).
- **Video format:** native continuous webm + mp4 renders, enabled by a STATIC ffmpeg 7.0.2
  (md5-verified, owner-authorized download 2026-06-09; lives in `~/.local/share/aidr-tools/` and at
  Playwright's helper path — repo dependency state untouched). The GIF frame-capture fallback
  remains in `e2e/gate_common.mjs` for environments without it.
- **Not crawled (held/planned, with reasons):** demo control tower (RED proof), design-bundle
  preview (no verified start script), and the 8 planned emulators — see
  `architecture/local_service_registry.json`.

## 4. Secrets policy (gated by `scripts/check_no_raw_secrets_in_e2e_artifacts.py`)

Raw API keys are blurred in every video frame and redacted to `aidr_demo_sk_redacted_…` before
stills; the demo passphrase is never written to any artifact; the proof scans every text artifact
for key/ref/passphrase patterns.
