# lightpanda_adapter (DESIGN SEAM)

> Status: **design seam** — Lightpanda is a lightweight, AI-oriented **headless browser** (written in Zig) that
> speaks CDP and is built for high-volume, low-memory automation with replayable scripts. Not installed here; a real
> `LightpandaAdapter` would degrade to structured unsupported until the binary is present.

## Adapter shape

- **Class:** `LightpandaAdapter(_BackendAdapter)` backed by a `_LightpandaBackend(BackendPort)`.
- **Bridge:** Lightpanda exposes a **CDP endpoint** → reuse `scripts.browser_capture.CDP` exactly like the
  `cdp_adapter` (point it at Lightpanda's `--remote-debugging-port` instead of system Chrome). Adding it is
  effectively a one-line backend swap.
- **Backs:** `navigate`, `snapshot`, DOM/text/links/forms/tables, tab control, `wait_for_state`,
  `download_artifacts`, graph/report (`JS_RENDER = True`). `screenshot`/rich `capture_network` depend on the
  build's CDP coverage — advertise via `capabilities()` after a probe, not by assumption.

## Install + test

```bash
# install the lightpanda binary (see lightpanda.io), then:
lightpanda --remote-debugging-port=9377 &      # CDP endpoint
# (promoted) python3 -c "from browser_control import get_adapter; print(get_adapter('lightpanda', port=9377).start_session())"
```

## When to use

- **High-volume / high-fan-out** crawling where full Chrome is too heavy (memory/startup) but you still need JS
  rendering — the sweet spot between the `http_scrape` adapter (no JS, cheapest) and `cdp`/`playwright` (full Chrome).
- Replayable, scriptable capture pipelines.

## Risks

- Newer engine → **partial web-platform coverage**; some sites render differently than Chrome. Probe capabilities;
  fall back to `cdp`/`playwright` for sites it can't render.
- Still a live browser: read-only default, `write`+ confirmation gate, never submit / bypass a login/captcha.
