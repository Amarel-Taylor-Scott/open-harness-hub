# Browser & Web-Ingestion Primitive Architecture

> How the browser/ingestion stack is layered so that adding a driver, a client, or a data source is **one
> adapter/primitive row, never a rewrite** (the MULTI-PATH law made literal for the web). Candidate-only layer
> (`serves_truth=false`) — it returns pointers, shapes, and evidence, never truth.

## The four layers

```
  ┌───────────────────────────────────────────────────────────────────────────────────────┐
  │ L4  PRIMITIVES        web.* · browser.* · crawler.* · llm.* · api.* · artifact.*         │  ~50 named,
  │                       (browser_primitives_candidates.jsonl — typed I/O, tool order,      │  composable,
  │                        safety policy, verifiers, probe_status)                           │  candidate-only
  ├───────────────────────────────────────────────────────────────────────────────────────┤
  │ L3  ADAPTERS          BrowserAdapter family:  fake · http_scrape · cdp · playwright       │  driver-neutral
  │  (browser_control/)   Ingestion family:  Fetch · Parser · Crawler · LLMExtraction · Search │  + seams (md):
  │                       every method → structured result; unsupported ⇒ {"supported":False} │  puppeteer,
  │                       never raises; read-only by default; secrets redacted               │  selenium, mcp,
  │                                                                                          │  lightpanda, …
  ├───────────────────────────────────────────────────────────────────────────────────────┤
  │ L2  HARNESS           scripts.primitive_browser_control_harness:  BackendPort (Static/    │  the ONE impl
  │                       Cdp) · TabControlAPI (command plane + receipt minter + SIDE_EFFECT   │  of fetch, CDP,
  │                       ladder) · browser_* extractors · RateLimiter · robots policy ·      │  extraction,
  │                       redact_secrets · classify_trust_tier · crawl · capture_artifact     │  receipts
  ├───────────────────────────────────────────────────────────────────────────────────────┤
  │ L1  RUNTIME/EVIDENCE  urllib · requests/httpx · system Chrome (CDP) · Playwright ·        │  actual drivers
  │                       localhost LLM (Ollama/:8000) · canonical_id · schemas/*.json        │  + naming/ids
  └───────────────────────────────────────────────────────────────────────────────────────┘
```

**The invariant that makes it composable:** *the important thing is not the driver, it is that every action
produces an evidence record.* Every command returns a `browser_action_receipt`
(`schemas/browser_action_receipt.schema.json`) — read-only by default, secrets redacted, `candidate=true`,
`serves_truth=false` — so a `web.fetch_static` over `curl` and the same over `PlaywrightAdapter` are
interchangeable to everything downstream.

## L3 — two adapter families, one shape

Both families obey the same contract: a method it can't back returns `{"supported": False, "reason": ...}` and
**never raises**; every result carries the candidate/serves_truth boundary; secrets are redacted before
anything is returned or logged.

- **`BrowserAdapter` family** (the driver-neutral *command plane*, `browser_control/adapter.py`) — 21 commands
  (session/tab/navigate/snapshot/extract/screenshot/network/click/fill/wait/downloads/graph/report), 17
  capability flags, backed by a harness `BackendPort`. Real adapters: `FakeAdapter` (offline, all 17 caps),
  `HttpScrapeAdapter` (StaticBackend, no JS), `CdpAdapter` (system Chrome, zero pip deps), `PlaywrightAdapter`
  (channel=chrome). Design seams as markdown until promoted: puppeteer, selenium, mcp, lightpanda, extension,
  remote_browser, browser_use.
- **Ingestion family** (the composable *primitives around/below the command plane*, added 2026-07-08) —
  `FetchAdapter` (raw GET), `ParserAdapter` (HTML→structured, stdlib), `CrawlerAdapter` (sitemap/robots/BFS),
  `LLMExtractionAdapter` (untrusted extraction + a deterministic grounding verifier), `SearchAdapter` (keyed
  search seam, keyless ⇒ `available_with_credentials`). These are NOT `BrowserAdapter` subclasses — their
  surfaces are narrower — so they live in a parallel `INGESTION_ADAPTERS` registry; a router picks from **both**
  families by the capability a job needs.

## L4 — primitives are the composition unit

`artifacts/browser_control/browser_primitives_candidates.jsonl` holds ~50 primitives across six namespaces,
each with a **full schema**: `input_schema`, `output_schema`, `implementation_options`, `preferred_tool_order`,
`fallback_tools`, `side_effects` (`read_only` | `gated_side_effect`), `required_permissions`, `safety_policy`,
`failure_modes`, `verifiers`, `test_fixture`, `probe_status` (derived from live tool availability), and
`recommended_next_action`. Namespaces:

| namespace | what it owns | example primitives |
|---|---|---|
| `web.*` | fetch + parse a single page | `web.fetch_static`, `web.extract_tables`, `web.detect_api_spec_links` |
| `browser.*` | render + interact (gated) | `browser.render_page`, `browser.screenshot`, `browser.click_ref` |
| `crawler.*` | multi-page, politely | `crawler.bfs_crawl`, `crawler.fetch_sitemap`, `crawler.robots_gate` |
| `llm.*` | untrusted extraction + a real verifier | `llm.extract_schema`, `llm.verify_extraction` |
| `api.*` | spec/API-first access | `api.discover_openapi`, `api.call_endpoint`, `api.web_search` |
| `artifact.*` | evidence / provenance | `artifact.capture_page`, `artifact.action_receipt`, `artifact.redact_secrets` |

Composition is **read the names + edges, not the bodies**: `preferred_tool_order` + `fallback_tools` name the
lanes, `input_schema`/`output_schema` name the seams, so a planner chains `api.discover_openapi →
api.parse_openapi_paths → api.call_endpoint` or `crawler.fetch_sitemap → crawler.bfs_crawl → web.extract_tables
→ artifact.capture_page` without reading any implementation.

## Extension points — where a NEW method plugs in (one row each)

| To add a… | The seam (one row) |
|---|---|
| browser driver (command plane) | a `_BackendAdapter` subclass + a `CAPABILITIES` row → register in `ADAPTERS` |
| HTTP client backend | a `FetchAdapter` backend branch in `HTTP_BACKENDS` |
| HTML parse engine | a `ParserAdapter` optional-engine branch (`OPTIONAL_ENGINES`) |
| crawl engine | a `CrawlerAdapter` engine option (`scrapy`/`crawlee` are the worked seams) |
| search provider | a `SearchAdapter.PROVIDERS` row |
| LLM provider/lane | an `LLMExtractionAdapter` provider branch (offline stub stays default) |
| a new tool in the inventory | a `TOOLS` row in `scripts/build_browser_tool_inventory.py` (probe kind + caps) |
| a new primitive | a `_prim(...)` row in the same script (namespace + shapes + tool order + safety) |
| a design-only driver | a markdown seam under `browser_control/adapters/` until promoted |

## Proofs (all offline, mutation-gated, in `run_proofs`-style umbrellas)

- `browser_control/self_test.py` — the `BrowserAdapter` family (28 checks: tabs/state-hash/receipts/side-effect
  gate/redaction/schema/determinism).
- `browser_control/ingestion_self_test.py` — the five ingestion adapters (23 checks: robots gate, rate-limit,
  page cap, sitemap parse, schema-exact extraction, the grounding-verifier mutation gate, keyless search).
- `scripts/build_browser_tool_inventory.py --self-test` — the inventory + ~50 primitives (structure,
  determinism, mutation gates).
- `scripts/probe_browser_control_tools.py --self-test` — the 13-category browser-control matrix.
- `scripts/run_browser_fixture_lab.py --self-test` — the offline stdlib fixture that every live probe drives.

**Playwright is not the whole strategy. It is one adapter in a layered browser/data-ingestion primitive
architecture.**
