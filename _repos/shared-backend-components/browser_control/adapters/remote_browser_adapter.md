# remote_browser_adapter (DESIGN SEAM)

> Status: **design seam** — a cloud/remote browser (Browserbase, Browserless, Steel, or a self-hosted
> Chrome-over-HTTP like pinchtab) reached over CDP/WebSocket or an HTTP control plane. **UNAVAILABLE here:** the
> required keys/URLs are absent (`BROWSERBASE_API_KEY`, `BROWSERLESS_URL`, `BROWSERBASE_PROJECT_ID` are not set;
> cloud keys in this env are file-based only). So a real `RemoteBrowserAdapter` would `start_session()` →
> structured `{"supported": False, "reason": "BROWSERBASE_API_KEY / BROWSERLESS_URL not configured"}`.

## Adapter shape

- **Class:** `RemoteBrowserAdapter(_BackendAdapter)` backed by a `_RemoteBackend(BackendPort)` that connects to a
  remote CDP endpoint (`wss://…?apiKey=…`) — reuse `scripts.browser_capture.CDP` against the remote URL, so the
  adapter body is nearly identical to `cdp_adapter`.
- **Config:** keys/URLs are `env://` / file references, **never** inline (`BROWSERBASE_API_KEY`,
  `BROWSERLESS_URL`); the adapter reads a reference and reports `available=false` when unresolved.
- **Backs:** all 17 when connected (`JS_RENDER = True`) — remote managed Chrome behaves like local CDP, plus
  built-in proxy/stealth/session-record features exposed as extra receipt fields.

## Install + test

```bash
export BROWSERBASE_API_KEY=...          # ABSENT here -> adapter degrades to unsupported
export BROWSERLESS_URL=wss://...        # or a self-hosted browserless/pinchtab endpoint
# (promoted) python3 -c "from browser_control import get_adapter; print(get_adapter('remote_browser').start_session())"
```

## When to use

- **Scale-out / managed** browsing: many concurrent sessions, rotating IPs, or a stable managed Chrome when local
  Chrome is unavailable in the runtime.
- Local → cloud swap is **config-only** (a key + a URL) — build against `cdp` locally, point at the remote endpoint
  in production.

## Risks

- **"Any client that can reach the control plane acts as the logged-in user."** A self-hosted HTTP browser API
  (pinchtab/browserless without auth) hands full browser control — and any live auth session — to whoever can hit
  the port → **mandatory auth gate + network isolation**; never expose it unauthenticated.
- Third-party remote = data leaves the machine → do not send secrets/PII; keep raw bodies out; digests only.
- A key is required and ABSENT here — treat as unavailable, not broken; degrade, never block the loop.
