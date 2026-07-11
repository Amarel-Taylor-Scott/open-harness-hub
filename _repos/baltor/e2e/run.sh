#!/usr/bin/env bash
# One command to wire up + verify the Baltor demo in a real browser, with a recording.
# Prereqs: node + a system Chrome/Chromium (channel 'chrome'); first run does `npm install`.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HERE/.." && pwd)"
PORT="${PORT:-8000}"
export BASE="http://localhost:${PORT}"

# 1. serve the demo (_repos/baltor/frontend) if not already up
if ! curl -s -o /dev/null "http://localhost:${PORT}/demo-console.html"; then
  echo "starting static server on :${PORT} (_repos/baltor/frontend)…"
  ( cd "$REPO/web/baltor" && python3 -m http.server "$PORT" >/tmp/baltor_http.log 2>&1 & )
  sleep 1
fi

# 2. deps (use system Chrome via channel 'chrome' — skip Playwright's browser download)
[ -d "$HERE/node_modules" ] || ( cd "$HERE" && PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 npm install )

# 3. drive (assert) + 4. filmstrip gif
cd "$HERE"
node record_demo.mjs
node make_gif.mjs
echo "Artifacts in $HERE/artifacts (trace.zip, *.png, baltor-demo.gif)."
echo "Interactive replay: npx playwright show-trace $HERE/artifacts/trace.zip"
