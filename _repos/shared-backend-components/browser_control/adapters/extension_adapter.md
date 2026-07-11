# extension_adapter (DESIGN SEAM)

> Status: **design seam** — a browser **extension** (Manifest V3, `chrome.tabs` / `chrome.debugger`) that digests
> the user's CURRENT tab in their real, already-authenticated browser (the TabMind / AI-Browser-Bridge pattern).
> Privacy-first, human-in-the-loop. The extension is JS; the adapter is the Python side that receives its posts.

## Adapter shape

- **Class:** `ExtensionAdapter(BrowserAdapter)` — a **receive-only** adapter. The extension pushes a captured page
  bundle (`{url, html, screenshot?, forms, links}`) to a localhost seam; the adapter turns each push into the same
  `snapshot_tab` / `extract_*` results + `browser_action_receipt` records.
- **Backs:** `snapshot`, `extract_text`/`extract_dom`/`extract_links`/`extract_forms`/`extract_tables`,
  `capture_screenshot` (if the extension attaches one), `list_tabs`/`focus_tab` (via `chrome.tabs`),
  `build_session_report`. **Does NOT back** headless `navigate` of arbitrary URLs, `open_tab` of new automation
  contexts, or autonomous `click_ref`/`fill_ref` — those return structured unsupported (this is *current-tab
  digestion*, not automation).

## Install + test

```bash
# load the unpacked extension (chrome://extensions -> Developer mode -> Load unpacked)
# it POSTs the current tab to a localhost receiver; the adapter reads that receiver.
python3 scripts/scan_agent_skills.py --self-test        # scan the extension's declared perms before trust
```

## When to use

- **Route "the current tab" here.** Reading a page the human is already logged into (an internal dashboard, a
  gated report) WITHOUT storing their credentials — the human stays in the loop and initiates every capture.
- Consent-first capture for the primitive foundry (consent = gate #0).

## Risks

- The extension runs **as the logged-in user** in their live browser → strict **auth gate**: capture only on
  explicit user action, never auto-navigate or auto-submit, and mark artifacts `authenticated_internal` (never
  promote tenant-private/authenticated content to a global corpus).
- MV3 permissions are powerful (`chrome.debugger`, `<all_urls>`) — scan the manifest (`scan_agent_skills`) and keep
  the extension minimal + human-triggered.
- Never capture password/secret fields; redact before the bundle leaves the browser.
