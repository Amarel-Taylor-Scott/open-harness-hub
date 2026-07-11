# Browser / Web-Ingestion Tool Decision Tree

> Given a job, which lane? Walk the branches top-to-bottom and stop at the first that fits — they are ordered
> **cheapest-and-safest first**. Every branch names the repo adapter/primitive that already covers it. This is
> the operational form of the layered architecture (`docs/BROWSER_PRIMITIVE_ARCHITECTURE.md`); the per-tool
> LIVE availability is in the generated `docs/BROWSER_AUTOMATION_CAPABILITY_MATRIX.md`.

## Branch 0 — SAFETY GATE (always first, non-negotiable)

> **Would this require defeating a control, or touching data we must not?** If ANY of: solving/bypassing a
> CAPTCHA · defeating a paywall/login you don't own · using another user's auth/session without consent ·
> submitting a form or performing a money/state-changing action without an approval gate · collecting real PII
> · ignoring `robots.txt` · a target on the Prohibited list → **STOP.** Detect-and-report only
> (`web.detect_captcha`, `web.detect_login_wall`). See `docs/BROWSER_SAFETY_AND_COMPLIANCE.md`. Only if this
> gate passes do you continue.

## The 10 branches

**1. Is there an official API / OpenAPI / GraphQL / REST spec?**
→ Use it. It is the cheapest, most stable structured access — skip the browser entirely. Check
`robots.txt` + `sitemap.xml` + `/openapi.json` + `/graphql` first.
**Lane:** `api.discover_openapi` → `api.parse_openapi_paths` / `api.introspect_graphql` → `api.call_endpoint`
(over `FetchAdapter` + harness detectors).

**2. Is the content already in the server HTML (no JavaScript needed)?**
→ Raw HTTP fetch + parse. ~0 browser cost, highest throughput. (Verify: does a `curl`/`FetchAdapter` GET
contain the target text? If yes, you're done.)
**Lane:** `web.fetch_static` (`FetchAdapter`: requests→httpx→urllib) → `web.extract_readable_text` /
`web.extract_tables` / `web.extract_links` / `web.extract_metadata` (`ParserAdapter`, stdlib).

**3. Do you need MANY pages of ONE site?**
→ Seed from the sitemap/feed, then a robots-gated, rate-limited, same-origin BFS. Don't hand-roll a crawler;
don't crawl when one page answers the question.
**Lane:** `crawler.fetch_sitemap` / `crawler.parse_feed` → `crawler.bfs_crawl` (`CrawlerAdapter` over the
harness `crawl` + `RateLimiter` + robots gate); `scrapy`/`crawlee` are the higher-scale engine seams.

**4. Does the content require JavaScript to render?**
→ Escalate to a headless render — but pick the *lightest* one:
  - need the user's existing LOGIN/session? → **attach** to an open Chrome over raw CDP (`browser.attach_to_session`, `CdpAdapter`) — consent-gated.
  - just need a one-shot rendered DOM/screenshot with zero libraries? → `chrome --headless --dump-dom` (`browser.dump_dom`).
  - owned, repeatable automation? → **Playwright** (`browser.render_page`, `PlaywrightAdapter`, channel=chrome).

**5. Do you need INTERACTION (click / fill / multi-step)?**
→ The driver-neutral command plane with the side-effect gate. Read-only by default; `write`+ needs explicit
human confirmation; forms are never auto-submitted.
**Lane:** `browser.click_ref` / `browser.fill_ref` / `browser.wait_for_state` (`BrowserAdapter` cdp/playwright).

**6. Do you need SCALE / parallelism, or managed anti-bot, without local infra?**
→ A remote or lightweight browser.
  - many parallel headless sessions, keyless & local? → `browserless/chrome` in Docker via `connect_over_cdp`.
  - managed stealth/captcha at scale (keyed, pages leave your infra)? → Browserbase.
  - high-density crawl at a fraction of Chrome's RAM? → **Lightpanda** (CDP-compatible; existing driver code
    points at it unchanged).
**Lane:** `remote_browser` / `lightweight_browser` seams.

**7. Must you operate the USER's real, logged-in tab (privacy-first, human-in-the-loop)?**
→ A chrome-extension / current-tab bridge — a capability no headless driver has (acts as the user's own
trusted browser). Human-in-the-loop only; never unattended.
**Lane:** the `extension` seam (`chrome.tabs`/`chrome.scripting`/`chrome.debugger`).

**8. Is the UI unknown and you need to DISCOVER the flow?**
→ An agentic LLM browser — for exploration ONLY. Output is non-deterministic and QUARANTINED
(`serves_truth=false`); every side-effecting step is human-gated; distill winning plans to deterministic
Playwright/CDP.
**Lane:** `llm.plan_browser_actions` (`browser-use` / `stagehand` seams).

**9. Do you need to FIND pages about a topic (not a known URL)?**
→ A search API. Keyless ⇒ `available_with_credentials` (names the env var to set); never fabricated.
**Lane:** `api.web_search` (`SearchAdapter`: Tavily / Exa / SerpAPI / Brave / Bing).

**10. Do you need STRUCTURED FACTS from messy prose?**
→ LLM extraction — then VERIFY. The extraction is UNTRUSTED; the grounding check is a real deterministic
gate. Nothing promotes to truth without it.
**Lane:** `llm.extract_schema` / `llm.extract_primitives` / `llm.ask_questions` (UNTRUSTED) →
`llm.verify_extraction` (deterministic grounding) → foundry as candidates.

## One-line rule of thumb

```
API / spec  >  raw HTTP + parse  >  sitemap/feed-seeded crawl  >  headless render (CDP-attach | one-shot CLI |
Playwright)  >  interaction (gated)  >  remote/lightweight browser for scale  >  search API (keyed)  >
agentic LLM browser (quarantined, human-gated)  —  and ALWAYS behind Branch 0.
```

Pick the cheapest lane that reaches the content; escalate only when the current lane provably can't. Every
lane is one adapter row — switching lanes is a config choice, not a rewrite.

**Playwright is not the whole strategy. It is one adapter in a layered browser/data-ingestion primitive
architecture.**
