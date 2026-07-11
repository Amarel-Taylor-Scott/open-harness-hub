# Browser Control — Decision Framework (routing table)

> Given a task, which backend? The `browser_control` adapters are interchangeable behind one interface, so routing
> is a **data decision, not a code fork**. Pick the CHEAPEST backend that meets the need, escalate only when a
> capability is missing, and always keep the read-only + confirmation gate on. A router reads
> `BrowserAdapter.capabilities()` (17 bools) and this table; it never guesses.

## The table

| Task / signal | Preferred backend | Why / fallback |
|---|---|---|
| **Static docs, spec pages, sitemap crawl** | `http_scrape` (HTTP) | no JS needed; stdlib, keyless, highest-volume, lowest-risk. Fallback `cdp` if the page is client-rendered. |
| **OpenAPI / GraphQL / Postman surface** | the **API importer** (→ `api_discovery_report`) | don't drive a browser to read a spec — parse it into method/path pairs + endpoint primitive candidates. Capture the page with `http_scrape` first if the spec is linked. |
| **The user's CURRENT tab** | `extension` (seam) | read a page the human is already logged into, human-in-the-loop, no stored creds. Mark `authenticated_internal`. |
| **A real authenticated session** | `cdp` (attached) / `remote_browser` | drive the logged-in browser over CDP; never re-auth in code. Auth gate applies. |
| **Deterministic regression script** | `playwright` (channel=chrome) | clean multi-context/tab model + auto-waiting = stable reruns. Fallback `cdp`. |
| **Unknown / one-off workflow** | `browser_use` (seam) → **compile** | let the agent DISCOVER the steps as receipts, then compile the proven path into a deterministic primitive and drop the LLM. Output QUARANTINED until gated. |
| **High-volume / high-fan-out** | `lightpanda` (seam) or `http_scrape` | lightweight JS engine when full Chrome is too heavy; `http_scrape` when no JS is needed at all. |
| **Tabs / popups / downloads / screenshots** | `cdp` or `playwright` | real multi-tab + `Target.*`/context control + real screenshot bytes; `http_scrape` returns these unsupported. |
| **Any side-effecting action (submit/pay/delete)** | **dry-run + human gate** on `cdp`/`playwright` | the model PROPOSES; `>= write` needs explicit human confirmation; never auto-execute; never submit/bypass. |
| **Any LLM step (classify/plan/decompose/schema/verifier)** | **local LLM first** | `localhost:8000` (OpenAI-compat) / OpenWebUI before any cloud lane (owner rule); cloud only with configured keys; output `untrusted=true`. |

## Decision order (first match wins)

1. **Is it a machine-readable API spec?** → API importer (`api_discovery_report`), not a browser.
2. **Does it need JavaScript / a screenshot / a real network panel / interactive click-fill?**
   - No → `http_scrape` (cheapest).
   - Yes → a real browser: `cdp` (zero-pip, live) or `playwright` (regression). `lightpanda` for high volume.
3. **Is it behind auth?** → the user's current tab (`extension`) or an attached logged-in session (`cdp`) —
   never re-authenticate in code; apply the auth gate; mark `authenticated_internal`.
4. **Is the workflow unknown?** → `browser_use` to discover → **compile to a deterministic primitive** → re-route
   the now-known task to step 2/3.
5. **Does the task mutate state?** → dry-run, emit the receipt, require human confirmation for `>= write`.
6. **Is a required key/dep absent?** (selenium not installed; `BROWSERBASE_API_KEY`/`BROWSERLESS_URL` unset) →
   that backend is **unavailable** — degrade to the next viable row, never block the loop.

## Environment note (2026-07-08)

Real + importable here: `http_scrape`, `cdp` (system Chrome/Chromium/Firefox present), `playwright` + `nodriver`
installed, `requests`/`httpx` present. **Absent** here: `selenium`/`bs4`/`lxml`/`scrapy`/`pyppeteer`;
`BROWSERBASE_API_KEY`/`BROWSERLESS_URL`; cloud LLM env vars (cloud keys are file-based). Node v22 + `npx` present
(enables the MCP / puppeteer seams). A backend whose deps/keys are absent routes to the next row and is reported
`available=false` in its `browser_control_capability` row — the router degrades, it does not fail.

## The one rule behind the table

Every backend produces the SAME `browser_action_receipt`, so switching drivers changes cost/capability, never the
evidence contract. Route for cost and capability; the safety rail (read-only default, `>= write` confirmation, no
raw bodies, redaction, `serves_truth=false`) is identical on every row.
