# Driver-Neutral Browser Control

> One stable command surface (`browser_control.BrowserAdapter`) that many interchangeable browser drivers back —
> the MULTI-PATH law made literal for browsers. **The driver does not matter; the evidence does:** every command
> returns a `browser_action_receipt` (`schemas/browser_action_receipt.schema.json`). Read-only by default, secrets
> redacted, `candidate=true, serves_truth=false` on everything.
>
> Package: `browser_control/`. Backend/receipt/extraction engine (WRAPPED, never rebuilt):
> `scripts/primitive_browser_control_harness.py`. Proof: `python3 browser_control/self_test.py --self-test`.

## Why an adapter layer

The shipped harness already gives us a backend ZOO (`BackendPort`: static HTTP, live CDP, …), a command plane with
receipts + a side-effect ladder (`TabControlAPI`), and pure `browser_*` extractors. The adapter layer adds ONE
thing on top: a **driver-neutral interface** so the registry, the LLM lanes, and a routing table talk to *one*
surface and swap drivers by name — `static docs → http`, `real-auth tab → cdp`, `regression → playwright` — without
any caller change. Adding a driver is a subclass + a `CAPABILITIES` row, **never** a rewrite.

## The interface (21 commands)

`start_session` · `stop_session` · `list_tabs` · `open_tab` · `focus_tab` · `close_tab` · `navigate` ·
`snapshot_tab` · `extract_text` · `extract_dom` · `extract_links` · `extract_forms` · `extract_tables` ·
`capture_screenshot` · `capture_network` · `click_ref` · `fill_ref` · `wait_for_state` · `download_artifacts` ·
`build_tab_graph` · `build_session_report`.

- **Unsupported ≠ exception.** A command a driver cannot back returns a **structured, non-raising**
  `{"supported": False, "backend": ..., "method": ..., "reason": ...}`. An adapter NEVER raises for a missing
  capability — a router reads `capabilities()` (17 bools) up front and degrades gracefully.
- **Every command → a receipt.** `navigate`/`snapshot` (read-only), the gated `click_ref`/`fill_ref`, `focus_tab`,
  `capture_screenshot`, `download_artifacts`, verifiers — each appends a normalized `browser_action_receipt` with
  `before/after_state_hash`, `side_effect_level`, `requires_confirmation`, `verifier_result`, `artifact_refs`.
- **17 capability flags** (`browser_control.adapter.CAPABILITY_KEYS`, the SINGLE SOURCE the capability schema
  mirrors): `session_lifecycle, tab_control, navigate, snapshot, extract_text, extract_dom, extract_links,
  extract_forms, extract_tables, screenshot, network_capture, click, fill, wait_for_state, downloads, tab_graph,
  session_report`.

```python
from browser_control import FakeAdapter, get_adapter
a = FakeAdapter()                       # or get_adapter("http_scrape"|"cdp"|"playwright")
a.start_session(allow_side_effects=False)
a.navigate("https://portal.example/")   # -> {state_hash, receipt, ...}
a.extract_forms(); a.extract_tables(); a.download_artifacts()
a.capture_screenshot()                  # http adapter -> {"supported": False, "reason": "..."}; cdp/pw -> digest
report = a.build_session_report()["report"]   # reuses scripts.browser_session_report when present
```

## Drivers shipped

| adapter | backend it wraps | js | screenshot | network | tabs | click/fill | notes |
|---|---|---|---|---|---|---|---|
| `fake` | in-memory fixture | ✓ | ✓ | ✓ | ✓ | gated | offline, deterministic — what `--self-test` runs |
| `http_scrape` | harness `StaticBackend` | ✗ | ✗ | ✗ | ✓ | ✗ | stdlib HTTP GET; highest-volume, lowest-risk |
| `cdp` | harness `CdpBackend` + `TabControlAPI` | ✓ | ✓ (live) | ✓ | ✓ | gated | zero-pip, system Chrome, live-only/lazy |
| `playwright` | `_PlaywrightBackend` (channel=chrome) | ✓ | ✓ | ✓ | ✓ | gated | regression-grade; degrades if no launchable Chrome |

## Adding a driver later (one row, never a rewrite)

Every future driver already has a **design seam** in `browser_control/adapters/*.md`
(puppeteer · selenium · mcp · **lightpanda** · **extension** · **remote_browser (Browserbase/Browserless/pinchtab)**
· **browser_use**). To promote a seam to a real adapter:

1. Write a `BackendPort` subclass for the driver (`open(url)->page`, `list/new/switch/close` tabs). For any
   **CDP-speaking** driver (Lightpanda, PinchTab, a remote Chrome), reuse `scripts.browser_capture.CDP` against its
   debug endpoint — the body is nearly identical to `cdp_adapter`.
2. Subclass `_BackendAdapter`, set `name`, `JS_RENDER`, and the `CAPABILITIES` dict; supply `_make_backend()`.
   Override only the driver-specific method (e.g. `cdp_adapter` overrides `capture_screenshot` to hash real bytes).
3. Register it in `browser_control/__init__.py:ADAPTERS`. `capabilities()` and the routing table pick it up.

The interface, the receipt shape, the side-effect ladder, and extraction are all inherited — you write the driver,
not the plumbing. `PinchTab`/`extension` are **receive-or-attach** drivers (current tab / logged-in session): back
`snapshot`/`extract_*`, mark artifacts `authenticated_internal`, and keep autonomous navigation/act unsupported.

## Invariants (never weaken)

- **Read-only by default**; an act is refused unless side effects are enabled; `>= write` needs human confirmation.
- **No raw bodies** — digests, bounded redacted text, and extracted structured units only.
- **Secrets redacted** before any receipt/extract/report is written (delegated to the harness redactor).
- **`serves_truth=false`** on every emitted row; a receipt is evidence, never truth.
