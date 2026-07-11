# puppeteer_adapter (DESIGN SEAM)

> Status: **design seam** — not yet a real `BrowserAdapter` class. Promote to `puppeteer_adapter.py` (one class +
> a `CAPABILITIES` row + a `BackendPort`) when a Node/Puppeteer path is needed. In THIS Python environment the
> already-real `cdp_adapter` and `playwright_adapter` cover the same ground with zero Node bridge, so Puppeteer is
> documented, not built.

## Adapter shape

- **Class:** `PuppeteerAdapter(_BackendAdapter)` backed by a `_PuppeteerBackend(BackendPort)`.
- **Bridge:** Puppeteer is a **Node** library; Python drives it either (a) over the SAME CDP websocket the
  `cdp_adapter` already uses (Puppeteer just launches Chrome with `--remote-debugging-port`, then reuse
  `scripts.browser_capture.CDP`), or (b) via a thin `node` sidecar exposing `open/list/new/switch/close` over
  stdio/HTTP. Prefer (a) — it needs no new transport and keeps one receipt path.
- **Backs:** all 17 capabilities (`JS_RENDER = True`) — `navigate`, `snapshot`, DOM/text/links/forms/tables,
  `screenshot`, `capture_network` (CDP `Network.*`), tab control (CDP `Target.*`), `click_ref`/`fill_ref` (gated),
  `download_artifacts`, `build_tab_graph`, `build_session_report`.

## Install + test

```bash
node -v && npm -v                       # v22 present here
npm i -g puppeteer-core                 # or `puppeteer` to fetch a matched Chromium
# smoke: launch Chrome with a debug port, then drive it via the EXISTING cdp path
python3 browser_control/adapters/cdp_adapter.py --help 2>/dev/null || true
# (promoted) python3 -c "from browser_control import get_adapter; a=get_adapter('puppeteer'); print(a.start_session())"
```

## When to use

- A team already standardized on Puppeteer/Node fixtures and wants to reuse them from the Python factory.
- Otherwise **route to `cdp` or `playwright`** — they back the identical capability set here with no Node bridge.

## Risks

- **Two runtimes** (Python + Node) = a fragile bridge + version skew between `puppeteer-core` and system Chrome.
- Same live-browser risks as CDP/Playwright: real navigation is a side effect — keep read-only default, honor the
  `write`+ confirmation gate, never submit a form or bypass a login/captcha.
