# Web-Ingestion Tool Survey

> Companion to the generated `docs/BROWSER_AUTOMATION_CAPABILITY_MATRIX.md` (the computed per-tool table with
> LIVE presence on this host) and `docs/BROWSER_CONTROL_TOOLING_SURVEY.md` (the 13-category browser-control
> matrix). This survey is the human narrative over the tool FAMILIES: what each family is for, when it is the
> right lane, when it is the wrong one, and which adapter/primitive in this repo already covers it. Candidate
> guidance (`serves_truth=false`); the numbers live in the matrix JSON, never hand-typed here.

The mistake this survey exists to prevent: **reaching for a full browser (Playwright) when a cheaper lane
already reaches the content.** Fetching, parsing, crawling, rendering, interacting, searching, and
LLM-extraction are *separate* primitives you compose — not one monolithic "scrape it" call. Pick the cheapest
lane that reaches the content; escalate only when the current lane provably can't.

## The families, cheapest-first

### 1. Official API / spec (`official_api`, `search_api`) — the cheapest structured access
An OpenAPI/GraphQL/REST call is orders of magnitude cheaper and more stable than rendering a page. Always
check `robots.txt` + `sitemap.xml` + `/openapi.json` + `/graphql` first. **Repo coverage:** `api.*` primitives
(`api.discover_openapi`, `api.parse_openapi_paths`, `api.introspect_graphql`, `api.call_endpoint`) over
`FetchAdapter` + the harness detectors; `api.web_search` over `SearchAdapter` (Tavily/Exa/SerpAPI/Brave/Bing,
keyless ⇒ `available_with_credentials`). **Right when** a spec/API exists. **Wrong when** the content only
exists in rendered UI.

### 2. HTTP clients (`http_client`) — raw fetch at ~0 browser cost
`requests` / `httpx` / `aiohttp` / `curl` / `wget` / stdlib `urllib`. The highest-throughput, lowest-risk lane
for static/server-rendered pages and JSON. **Repo coverage:** `browser_control.FetchAdapter` (requests → httpx
→ urllib, read-only GET, robots-gated, secrets redacted, cookies dropped) and the harness `StaticBackend`.
**Right when** the server already returns the HTML/JSON. **Wrong when** the content is injected by JavaScript
(escalate to a render lane).

### 3. HTML parsers (`html_parser`) — bytes → structured data
Stdlib `html.parser` (always present) covers text/links/tables/metadata; `beautifulsoup4` / `lxml` /
`selectolax` / `parsel` / `trafilatura` are optional upgrades (CSS/XPath, speed, readable-article). **Repo
coverage:** `browser_control.ParserAdapter` (stdlib default; trafilatura/readability as an opt-in readable
lane) reusing the harness `browser_*` extractors + `extract_tables_from_html`. **Right when** you have HTML and
want text/links/tables/metadata. **Wrong when** the DOM you need doesn't exist until JS runs.

### 4. Crawl frameworks (`crawl_framework`) — many pages, politely
`scrapy` (Python), `crawlee` (Node), `crawl4ai` (LLM-oriented). For breadth you usually don't need a framework:
a robots-gated, rate-limited BFS over the harness engine handles the common case. **Repo coverage:**
`browser_control.CrawlerAdapter` — `fetch_robots`, `robots_allows`, `fetch_sitemap` (incl. sitemap-index), and
a `crawl()` that reuses the harness `crawl` (per-domain `RateLimiter`, robots gate, same-origin frontier, page
cap, no-raw-body rows); scrapy/crawlee are optional higher-scale engines behind the seam. **Right when** you
need many same-origin pages. **Wrong when** one page/API answers the question (don't crawl).

### 5. Managed crawlers (`managed_crawl`) — someone else runs the browser
`firecrawl`, `apify`. Hosted crawl→markdown/structured with anti-bot handled — keyed and paid, and your target
pages leave your infrastructure. **Repo coverage:** seam only (env-key detected; no key here). **Right when**
you need managed scale + anti-bot and may send pages to a third party. **Wrong when** offline/air-gapped or
cost-sensitive.

### 6. Browser drivers (`browser_driver`) — render + interact
`playwright` (the cross-browser baseline), `selenium` (W3C WebDriver + Grid + Firefox), `puppeteer` (Node),
`pyppeteer`, `nodriver` (stealth). **Repo coverage:** `PlaywrightAdapter` (real when Playwright + a launchable
Chrome are present) and the driver-neutral `BrowserAdapter` command surface (21 commands, receipts, side-effect
gate). **Right when** you own the automation and need JS + interaction. **Wrong when** raw HTTP suffices, or you
need to attach to a human's existing session (use raw CDP).

### 7. Raw protocol (`raw_protocol`) — zero-dependency power tool
Raw CDP over the shipped stdlib websocket (`scripts.browser_capture.CDP`). Attaches to an already-open Chrome /
authenticated session/tab with **zero pip/npm deps**. **Repo coverage:** `CdpAdapter` (harness `CdpBackend`).
**Right when** you must attach to an existing session or can't install packages. **Wrong when** you want
ergonomic day-to-day scripting (Playwright is nicer) or cross-browser.

### 8. Remote / lightweight browsers (`remote_browser`, `lightweight_browser`) — scale
`browserless` (self-host/docker/cloud), `browserbase` (managed stealth), `lightpanda` (tiny-footprint,
CDP-compatible, high-density crawl). **Repo coverage:** seams; a local keyless `browserless/chrome` container is
reachable via `connect_over_cdp` since Docker is present. **Right when** the constraint is scale/parallelism or
anti-bot without local infra. **Wrong when** local is cheaper / data can't leave.

### 9. Agentic browsers (`agentic_browser`) — discover an unknown flow
`browser-use` (Python), `stagehand` (Node). An LLM plans actions over a UI. **Repo coverage:** seam +
`llm.plan_browser_actions` (QUARANTINED). Output is non-deterministic — every side-effecting step is
human-gated and winning plans are distilled to deterministic Playwright/CDP scripts. **Right when** exploring an
unknown UI, output reviewed by a human. **Wrong when** you need determinism, truth, or unattended money/state
changes.

### 10. LLM extraction (`llm.*`) — messy text → structured candidates
`LLMExtractionAdapter`: `extract_schema` / `extract_primitives` / `ask_questions` (all UNTRUSTED) +
`verify_extraction` (a REAL deterministic grounding check — the trustworthy gate over untrusted output).
Offline deterministic stub by default; live routes to local Ollama/OpenAI-compat or the OpenRouter file lane.
**Right when** you need best-effort structure from prose and will verify it. **Wrong when** the answer must be
trusted without a grounding pass (it never is at this layer — `serves_truth=false`).

## How to read the generated matrix

`BROWSER_AUTOMATION_CAPABILITY_MATRIX.md` has, per tool: `available` / `creds` / `probed` / `result` (LIVE on
this host) and the capability profile (`static·js·actions·multi-tab·screenshot·network·download·llm·api-first`)
plus best-use / failure / decision. Regenerate it with
`python3 scripts/build_browser_tool_inventory.py --run` (add `--live` for the phase-4 safe-target evidence). The
gap report (`artifacts/browser_control/browser_automation_gap_report.md`) lists what's missing + the enable
path + which primitives it blocks.

**Playwright is not the whole strategy. It is one adapter in a layered browser/data-ingestion primitive
architecture.**
