# Baltor browser E2E + recording

Drives the **live** Baltor demo console in a **real Chrome** (Playwright, system `channel: 'chrome'`),
asserts real DOM outcomes, and captures a recording — proving the demo is actually wired up, not just
that the Python self-tests pass.

## Prereqs
- Node 18+ and a system Chrome/Chromium (the harness uses `channel: 'chrome'`, so Playwright does
  **not** download a browser).
- Python 3 (to serve the static demo).

## Run (one command)
```bash
bash e2e/run.sh        # serves web/baltor on :8000 if needed, npm installs, drives, makes the gif
```
Or step by step:
```bash
cd web/baltor && python3 -m http.server 8000 &      # serve the demo
cd e2e && PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 npm install
node record_demo.mjs                                 # drive + 15 assertions + trace + screenshots
node make_gif.mjs                                    # filmstrip → artifacts/baltor-demo.gif
```

## What it verifies (15 assertions, all in a real browser)
Acme: page loads, headline renders **answer 5**, the graph draws 8 nodes, 5 lift bars; ▶Run animates
all 7 stages to 100%; clicking the stale runbook node opens its detail + **version timeline (v1→v2
proposed, pending review)**; **Expand source** returns a granted real excerpt; **Try restricted** is
denied (no raw). Corpus switch to **CFPB** runs and renders **answer 10**. The review queue shows ≥2
open reviews and approving records a demo-local `steward-review-decision`.

## Artifacts (`e2e/artifacts/`, gitignored)
- `trace.zip` — interactive frame-by-frame replay: `npx playwright show-trace e2e/artifacts/trace.zip`
- `baltor-demo.gif` — animated filmstrip of the 8 key moments (plays in any browser/viewer)
- `01..08-*.png` — the individual frames

## Video note
Playwright's native MP4/WebM recording needs its ffmpeg helper, which has no prebuilt for this OS
(Ubuntu 26.04). The **trace** is a superior frame-accurate replay, and the **GIF** is a quick watch.
For a continuous MP4, install system `ffmpeg` and switch the context to
`recordVideo: { dir: 'artifacts/video' }` (the code path is in git history of `record_demo.mjs`).
