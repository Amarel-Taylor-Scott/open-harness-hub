# Browser & Web-Ingestion Benchmark Plan

> How we measure the lanes so lane selection is receipt-backed, not habit. Everything below runs against the
> **offline fixture lab** (`scripts.run_browser_fixture_lab`) + the sanctioned safe public targets (single-page
> only), is candidate-only (`serves_truth=false`), and is mutation-gated + deterministic per the
> VERIFY-THE-VERIFIER law. Benchmark methodology mirrors the repo's standing rule: **audit → schema → generate
> → benchmark**, never generate before the gate exists.

## What we measure (per lane, on the same input)

| dimension | definition | how |
|---|---|---|
| **reach** | does the lane get the target content at all? | fixture markers (static vs JS-rendered vs delayed) |
| **fidelity** | correctness of extracted units (text/links/tables/metadata) | compare to fixture ground-truth |
| **latency** | wall-time per operation | `elapsed_ms` in the probe/live records |
| **cost** | browser launches, bytes fetched, LLM tokens | count launches / `bytes` / token proxy |
| **robustness** | behavior under noise (malformed HTML, 404, timeout, robots block) | fixture error surfaces |
| **safety** | robots honored, rate-limit honored, secrets redacted, writes gated | the safety self-test checks |
| **break-even N\*** | pages at which a heavier lane's fixed cost pays off vs a cheaper lane | latency/cost curves |

## The discriminators the fixture provides (already built)

`run_browser_fixture_lab` serves, on one page: static text + a data table (what raw HTTP sees), a
**JS-rendered** div (only a rendering browser sees the replaced marker), a **delayed** element (only a
"wait-for-render" lane sees it), a form + popup, a download, an error banner, and `/api/items` `/openapi.json`
`/graphql` `/robots.txt` `/sitemap.xml`. This is the deterministic target that turns "renders JS?" and "waits
for late render?" into an assertion, not an opinion — the cleanest reach discriminator between the fetch lane
and the render lane.

## Benchmark suites

### B1 — Fetch/parse fidelity (the cheap lanes)
Drive `FetchAdapter` (requests/httpx/urllib) + `ParserAdapter` over the fixture + the safe targets; assert
status, extracted `n_links`/`n_tables`/title vs ground-truth; record latency per backend. **Proves** the raw
lane reaches static content at ~0 browser cost. (Live evidence already captured:
`browser_tools_probe_results.jsonl` `live_fetch`/`live_parse` rows — e.g. example.com → title "Example Domain",
quotes.toscrape.com → 49 links.)

### B2 — Render reach (fetch vs render)
Same targets through the fetch lane vs a render lane (`chrome --dump-dom` / `CdpAdapter` / `PlaywrightAdapter`):
assert the fetch lane MISSES the JS-rendered marker (placeholder unreplaced) and the render lane HITS it.
**Proves** exactly when a browser is required — and therefore when it is pure overhead. (Live: chrome-cli
rendered example.com to a 561B DOM.)

### B3 — Crawl politeness + correctness
`CrawlerAdapter` over the fixture / an in-memory site: assert a `Disallow` page is skipped (never fetched), the
per-domain rate limit produces `skipped_rate_limited`, the page cap is honored, and `sitemap.xml` parses.
**Proves** the crawl lane is safe and bounded. (Covered by `ingestion_self_test`; live fixture crawl in the
`--live` records.)

### B4 — LLM extraction accuracy + the grounding gate
`LLMExtractionAdapter` offline stub vs (optional) live local endpoints: measure `extract_schema` field accuracy
vs labelled fixtures, and the **grounding verifier**'s ability to flag an ungrounded (hallucinated) value.
**Proves** the untrusted lane is gated by a trustworthy deterministic check before anything is trusted.

### B5 — Search-lane readiness
`SearchAdapter.providers()` / `search()`: with no key, assert every provider reports
`available_with_credentials` and results are empty (never fabricated). **Proves** the keyed lane is scaffolded
without fake keys; a real run is unblocked by setting one env var.

### B6 — Cost / break-even curves
Sweep page counts and record cumulative latency + launches + bytes per lane. Compute the break-even N\* where a
render/remote lane's fixed cost overtakes raw fetch — the number that justifies (or refuses) a browser.

## Verification discipline (every suite)

- **Mutation gate:** a real injected defect (redaction off, the gate auto-executing a write, robots ignored, an
  ungrounded value passing the verifier, a dropped schema field) must flip a check to red. Present in every
  `--self-test`.
- **Determinism gate:** artifacts (primitive rows, matrix doc, session report) rebuild byte-identical from a
  fresh injected clock.
- **Quality ratchet:** each headline metric is a floor computed from the fixture/manifest, never hand-typed; a
  regression below it is a hard failure; an unsupplied external metric is a gap record, not a fabricated pass.
- **Candidate boundary:** nothing a benchmark produces is served as truth; results rank lanes, they don't
  promote them.

## Reproduce

```bash
python3 scripts/run_browser_fixture_lab.py --self-test              # the offline target
python3 browser_control/self_test.py --self-test                   # command-plane adapters
python3 browser_control/ingestion_self_test.py --self-test         # fetch/parser/crawler/llm/search
python3 scripts/build_browser_tool_inventory.py --self-test        # inventory + primitives
python3 scripts/build_browser_tool_inventory.py --run --live       # phase-4 safe-target evidence
python3 scripts/probe_browser_control_tools.py --run               # the 13-category live matrix
```

Receipts land under `artifacts/browser_control/` (`browser_tools_probe_results.jsonl` carries the live latency
evidence). **Playwright is not the whole strategy. It is one adapter in a layered browser/data-ingestion
primitive architecture.**
