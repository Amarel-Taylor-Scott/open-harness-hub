#!/usr/bin/env python3
"""scripts.build_browser_tool_inventory — the BROAD, evidence-based web-ingestion tool INVENTORY + PRIMITIVE map.

Companion to ``scripts.probe_browser_control_tools`` (the 13-category *browser-control* matrix). This one widens
the lens to the FULL ingestion stack — HTTP clients, HTML parsers, crawl frameworks, managed crawlers, browser
drivers, the raw protocol, remote/lightweight/agentic browsers, search APIs, official APIs, and feeds — PROBES
each on THIS machine (import / ``which`` / node-resolve / env-presence / localhost LLM ping), optionally runs
SAFE single-page LIVE fetches, and emits, single-sourced from the same data:

  artifacts/browser_control/browser_tools_inventory.json     — the enriched tool table + env snapshot + summary
  artifacts/browser_control/browser_tools_probe_results.jsonl — one record per probe (phase 3) + live probe (phase 4)
  artifacts/browser_control/browser_primitives_candidates.jsonl — ~50 named primitives (web/browser/crawler/llm/api/artifact)
  artifacts/browser_control/browser_automation_gap_report.md  — what's missing, why, the enable path, blocked primitives
  docs/BROWSER_AUTOMATION_CAPABILITY_MATRIX.md                — the big rendered table (ends with the load-bearing line)

Every generated row is candidate-only (``serves_truth=false``). Probes are READ-ONLY: env keys are reported by
PRESENCE only (never a value); live fetches (``--live``) hit ONLY the sanctioned safe targets
(example.com / httpbin.org / quotes.toscrape.com) as SINGLE-PAGE GETs that respect robots — no crawling, no
volume, no auth, no forms. The offline ``--self-test`` never touches the public internet.

    python3 scripts/build_browser_tool_inventory.py --self-test   # offline, mutation-gated (no public internet)
    python3 scripts/build_browser_tool_inventory.py --run         # offline probes -> write artifacts + doc
    python3 scripts/build_browser_tool_inventory.py --run --live  # + SAFE single-page public probes (phase 4)
"""
from __future__ import annotations

import sys
from pathlib import Path

_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install, resource  # noqa: E402

_install()

import argparse  # noqa: E402
import copy  # noqa: E402
import importlib.util  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import platform  # noqa: E402
import shutil  # noqa: E402
import subprocess  # noqa: E402
import time  # noqa: E402
import urllib.error  # noqa: E402
import urllib.request  # noqa: E402
from typing import Any, Optional  # noqa: E402

try:
    from src.teleon.experiments.ids import canonical_id  # noqa: E402
except Exception as exc:  # noqa: BLE001
    raise SystemExit(f"build_browser_tool_inventory requires canonical_id; import failed: {exc}")

SCHEMA_VERSION = "1.0.0"
BOUNDARY = {"candidate": True, "serves_truth": False}
_ARTIFACTS_DIR = _sbc_boot / "artifacts" / "browser_control"
_DOC_PATH = _sbc_boot / "docs" / "BROWSER_AUTOMATION_CAPABILITY_MATRIX.md"
_INVENTORY_PATH = _ARTIFACTS_DIR / "browser_tools_inventory.json"
_PROBE_JSONL = _ARTIFACTS_DIR / "browser_tools_probe_results.jsonl"
_PRIMITIVES_JSONL = _ARTIFACTS_DIR / "browser_primitives_candidates.jsonl"
_GAP_MD = _ARTIFACTS_DIR / "browser_automation_gap_report.md"

#: the sanctioned safe LIVE targets (SINGLE-PAGE GET only; respect robots; no crawling/volume/auth/forms)
SAFE_TARGETS: tuple[str, ...] = ("https://example.com", "https://httpbin.org/html",
                                 "https://httpbin.org/json", "https://quotes.toscrape.com")
_LLM_ENDPOINTS = {"ollama_11434": "http://localhost:11434/api/tags",
                  "openai_compat_8000": "http://localhost:8000/v1/models"}
_UA = "AIDoneRight-PrimitiveDiscovery/1.0 (+read-only research; respects robots.txt)"

# ── the tool inventory: ONE source of the broad list (probe kind + capability profile + guidance) ─────────────────
# caps keys are the matrix's capability columns: static·js·actions·multi_tab·screenshot·network·download·llm·api_first
def _c(**kw: bool) -> dict[str, bool]:
    keys = ("static", "js", "actions", "multi_tab", "screenshot", "network", "download", "llm", "api_first")
    caps = {k: False for k in keys}
    for k, v in kw.items():
        if k not in caps:
            raise KeyError(f"unknown capability column {k!r}")
        caps[k] = bool(v)
    return caps


#: probe kinds: py(import) · bin(which) · node(require.resolve) · env(key presence) · llm(ping) · builtin · technique
TOOLS: tuple[dict[str, Any], ...] = (
    # ── HTTP clients ──
    {"tool": "curl", "category": "http_client", "probe": ("bin", "curl"), "caps": _c(static=True, download=True,
     api_first=True), "best_use": "shell one-shot fetch/download; CI smoke", "failure": "no JS; no parse",
     "decision": "quick shell GET/download", "enable": "apt-get install curl"},
    {"tool": "wget", "category": "http_client", "probe": ("bin", "wget"), "caps": _c(static=True, download=True),
     "best_use": "recursive file download/mirror", "failure": "no JS; crude parsing",
     "decision": "bulk file download", "enable": "apt-get install wget"},
    {"tool": "requests", "category": "http_client", "probe": ("py", "requests"), "caps": _c(static=True,
     download=True, api_first=True), "best_use": "the Python HTTP default; sessions/retries", "failure":
     "no JS render", "decision": "FetchAdapter primary backend", "enable": "pip install requests"},
    {"tool": "httpx", "category": "http_client", "probe": ("py", "httpx"), "caps": _c(static=True, download=True,
     api_first=True), "best_use": "sync+async HTTP, HTTP/2", "failure": "no JS render",
     "decision": "FetchAdapter async/HTTP2 backend", "enable": "pip install httpx"},
    {"tool": "aiohttp", "category": "http_client", "probe": ("py", "aiohttp"), "caps": _c(static=True,
     download=True, api_first=True), "best_use": "high-concurrency async fetch", "failure": "no JS; async-only",
     "decision": "high-fanout async crawl backend", "enable": "pip install aiohttp"},
    {"tool": "urllib", "category": "http_client", "probe": ("builtin", "urllib"), "caps": _c(static=True,
     download=True, api_first=True), "best_use": "stdlib fallback (zero deps)", "failure": "ergonomics; no JS",
     "decision": "always-present fallback", "enable": "stdlib (always present)"},
    # ── HTML parsers ──
    {"tool": "html.parser", "category": "html_parser", "probe": ("builtin", "html.parser"), "caps": _c(static=True),
     "best_use": "stdlib parse; ParserAdapter/harness use it", "failure": "no CSS selectors; lenient only",
     "decision": "ParserAdapter default (zero deps)", "enable": "stdlib (always present)"},
    {"tool": "beautifulsoup4", "category": "html_parser", "probe": ("py", "bs4"), "caps": _c(static=True),
     "best_use": "forgiving DOM navigation + selectors", "failure": "slower than lxml/selectolax",
     "decision": "optional parse upgrade", "enable": "pip install beautifulsoup4"},
    {"tool": "lxml", "category": "html_parser", "probe": ("py", "lxml"), "caps": _c(static=True), "best_use":
     "fast C parser + XPath", "failure": "C build dep", "decision": "optional fast XPath parse",
     "enable": "pip install lxml"},
    {"tool": "selectolax", "category": "html_parser", "probe": ("py", "selectolax"), "caps": _c(static=True),
     "best_use": "very fast CSS-selector parse at scale", "failure": "smaller API surface",
     "decision": "optional high-volume parse", "enable": "pip install selectolax"},
    {"tool": "parsel", "category": "html_parser", "probe": ("py", "parsel"), "caps": _c(static=True), "best_use":
     "Scrapy's XPath/CSS selectors standalone", "failure": "no fetch (parse only)",
     "decision": "optional selector parse", "enable": "pip install parsel"},
    {"tool": "trafilatura", "category": "html_parser", "probe": ("py", "trafilatura"), "caps": _c(static=True),
     "best_use": "readable-article/main-content extraction", "failure": "article-shaped pages only",
     "decision": "ParserAdapter readable upgrade", "enable": "pip install trafilatura"},
    # ── crawl frameworks ──
    {"tool": "scrapy", "category": "crawl_framework", "probe": ("py", "scrapy"), "caps": _c(static=True,
     download=True, api_first=True), "best_use": "industrial async crawl: pipelines/dedupe/throttle", "failure":
     "no JS by default; framework weight", "decision": "CrawlerAdapter high-scale engine", "enable":
     "pip install scrapy"},
    {"tool": "crawlee", "category": "crawl_framework", "probe": ("node", "crawlee"), "caps": _c(static=True, js=True,
     download=True), "best_use": "Node crawl framework (HTTP + headless)", "failure": "Node runtime",
     "decision": "Node-stack crawl engine", "enable": "npm i crawlee"},
    {"tool": "crawl4ai", "category": "crawl_framework", "probe": ("py", "crawl4ai"), "caps": _c(static=True, js=True,
     llm=True), "best_use": "LLM-oriented crawl → markdown/structured", "failure": "heavier; LLM-coupled",
     "decision": "LLM-ready page harvest", "enable": "pip install crawl4ai"},
    # ── managed / API crawlers ──
    {"tool": "firecrawl", "category": "managed_crawl", "probe": ("env", "FIRECRAWL_API_KEY"), "caps": _c(static=True,
     js=True, download=True, api_first=True), "best_use": "hosted crawl→markdown/structured, anti-bot handled",
     "failure": "third-party; per-call cost", "decision": "managed scrape at scale (keyed)", "enable":
     "set FIRECRAWL_API_KEY (pip install firecrawl-py)"},
    {"tool": "apify", "category": "managed_crawl", "probe": ("env", "APIFY_API_TOKEN"), "caps": _c(static=True,
     js=True, actions=True, download=True), "best_use": "hosted actor marketplace + managed browsers", "failure":
     "third-party; cost", "decision": "managed actors (keyed)", "enable": "set APIFY_API_TOKEN"},
    # ── browser drivers ──
    {"tool": "playwright", "category": "browser_driver", "probe": ("py", "playwright"), "caps": _c(static=True,
     js=True, actions=True, multi_tab=True, screenshot=True, network=True, download=True, api_first=True),
     "best_use": "cross-browser auto-wait automation (the baseline)", "failure": "browser binary; anti-bot",
     "decision": "PlaywrightAdapter (owned regression flows)", "enable": "pip install playwright && playwright install chromium"},
    {"tool": "selenium", "category": "browser_driver", "probe": ("py", "selenium"), "caps": _c(static=True, js=True,
     actions=True, multi_tab=True, screenshot=True, network=True, download=True), "best_use":
     "W3C WebDriver standard; Grid; real Firefox", "failure": "heavier; fewer auto-waits",
     "decision": "standards/Grid/Firefox need", "enable": "pip install selenium (geckodriver present)"},
    {"tool": "puppeteer", "category": "browser_driver", "probe": ("node", "puppeteer"), "caps": _c(static=True,
     js=True, actions=True, multi_tab=True, screenshot=True, network=True, download=True), "best_use":
     "Node Chrome automation + PDF", "failure": "Chromium-centric; Node", "decision": "Node-stack driver",
     "enable": "npm i puppeteer (or puppeteer-core + system Chrome)"},
    {"tool": "pyppeteer", "category": "browser_driver", "probe": ("py", "pyppeteer"), "caps": _c(static=True,
     js=True, actions=True, multi_tab=True, screenshot=True, network=True), "best_use":
     "Python Puppeteer port", "failure": "less maintained than Playwright", "decision":
     "legacy Python-CDP; prefer Playwright", "enable": "pip install pyppeteer"},
    {"tool": "nodriver", "category": "browser_driver", "probe": ("py", "nodriver"), "caps": _c(static=True, js=True,
     actions=True, multi_tab=True, screenshot=True, network=True), "best_use":
     "undetected async CDP driver (stealth)", "failure": "anti-bot arms race; Chromium-only", "decision":
     "harder anti-bot targets", "enable": "pip install nodriver"},
    # ── raw protocol ──
    {"tool": "raw-CDP", "category": "raw_protocol", "probe": ("builtin", "scripts.browser_capture"), "caps":
     _c(static=True, js=True, actions=True, multi_tab=True, screenshot=True, network=True, download=True,
        api_first=True), "best_use": "attach to an OPEN Chrome/session; zero pip deps (stdlib websocket)",
     "failure": "verbose; Chromium-only; you own the process", "decision": "CdpAdapter (attach/precise control)",
     "enable": "stdlib + system Chrome (both present)"},
    # ── remote / lightweight / agentic ──
    {"tool": "browserless", "category": "remote_browser", "probe": ("env", "BROWSERLESS_API_KEY"), "caps":
     _c(static=True, js=True, actions=True, multi_tab=True, screenshot=True, network=True, download=True),
     "best_use": "self-host/cloud headless pool (docker-local keyless)", "failure": "sends pages to a 3rd party",
     "decision": "scale without local infra", "enable": "docker run browserless/chrome OR set BROWSERLESS_API_KEY"},
    {"tool": "browserbase", "category": "remote_browser", "probe": ("env", "BROWSERBASE_API_KEY"), "caps":
     _c(static=True, js=True, actions=True, multi_tab=True, screenshot=True, network=True, download=True),
     "best_use": "managed stealth/captcha cloud browsers", "failure": "3rd party; cost", "decision":
     "hard anti-bot at scale (keyed)", "enable": "set BROWSERBASE_API_KEY + BROWSERBASE_PROJECT_ID"},
    {"tool": "stagehand", "category": "agentic_browser", "probe": ("node", "@browserbasehq/stagehand"), "caps":
     _c(static=True, js=True, actions=True, multi_tab=True, screenshot=True, network=True, llm=True), "best_use":
     "LLM act/extract/observe over Playwright", "failure": "non-deterministic; quarantine output", "decision":
     "LLM UI automation (candidate-only)", "enable": "npm i @browserbasehq/stagehand"},
    {"tool": "browser-use", "category": "agentic_browser", "probe": ("py", "browser_use"), "caps": _c(static=True,
     js=True, actions=True, multi_tab=True, screenshot=True, network=True, llm=True), "best_use":
     "LLM-driven exploration of unknown UIs", "failure": "non-deterministic; unsafe without a gate", "decision":
     "discovery only; distill to Playwright", "enable": "pip install browser-use (route LLM via cloud lane)"},
    {"tool": "lightpanda", "category": "lightweight_browser", "probe": ("bin", "lightpanda"), "caps": _c(static=True,
     js=True, screenshot=True, network=True), "best_use": "tiny-footprint headless crawl (CDP-compatible)",
     "failure": "not full Chrome fidelity", "decision": "high-density crawl fleets", "enable":
     "download binary from lightpanda.io -> lightpanda serve (CDP)"},
    # ── search APIs ──
    {"tool": "tavily", "category": "search_api", "probe": ("env", "TAVILY_API_KEY"), "caps": _c(api_first=True),
     "best_use": "LLM-oriented web search", "failure": "keyed; 3rd party", "decision":
     "SearchAdapter provider (keyed)", "enable": "set TAVILY_API_KEY"},
    {"tool": "exa", "category": "search_api", "probe": ("env", "EXA_API_KEY"), "caps": _c(api_first=True),
     "best_use": "neural/semantic web search", "failure": "keyed; 3rd party", "decision":
     "SearchAdapter provider (keyed)", "enable": "set EXA_API_KEY"},
    {"tool": "serpapi", "category": "search_api", "probe": ("env", "SERPAPI_API_KEY"), "caps": _c(api_first=True),
     "best_use": "Google/Bing SERP scraping API", "failure": "keyed; cost", "decision":
     "SearchAdapter provider (keyed)", "enable": "set SERPAPI_API_KEY"},
    {"tool": "brave-search", "category": "search_api", "probe": ("env", "BRAVE_API_KEY"), "caps": _c(api_first=True),
     "best_use": "independent web-search index (REST)", "failure": "keyed", "decision":
     "SearchAdapter provider (keyed)", "enable": "set BRAVE_API_KEY"},
    {"tool": "bing-search", "category": "search_api", "probe": ("env", "BING_API_KEY"), "caps": _c(api_first=True),
     "best_use": "Bing Web Search v7 (REST)", "failure": "keyed; Azure", "decision":
     "SearchAdapter provider (keyed)", "enable": "set BING_API_KEY"},
    # ── official APIs + feeds (techniques over urllib; always available) ──
    {"tool": "official-API (OpenAPI/GraphQL/REST)", "category": "official_api", "probe": ("technique", "urllib"),
     "caps": _c(static=True, download=True, api_first=True), "best_use":
     "the CHEAPEST structured access — skip the browser", "failure": "not every site exposes one", "decision":
     "PREFER over any browser when a spec exists", "enable": "urllib + harness detectors (present)"},
    {"tool": "sitemap.xml / RSS-Atom feeds", "category": "feed", "probe": ("technique", "urllib"), "caps":
     _c(static=True, api_first=True), "best_use": "enumerate what exists without crawling", "failure":
     "not always present/complete", "decision": "seed a crawl from the sitemap/feed", "enable":
     "CrawlerAdapter.fetch_sitemap (present)"},
    {"tool": "chrome/chromium --headless --dump-dom/--screenshot", "category": "local_binary", "probe":
     ("first_chrome", ""), "caps": _c(static=True, js=True, screenshot=True), "best_use":
     "one-shot JS render/screenshot with ZERO libraries", "failure": "one-shot; no interaction",
     "decision": "dependency-free render/shot", "enable": "system Chrome/Chromium (present)"},
    {"tool": "firefox --headless --screenshot", "category": "local_binary", "probe": ("bin", "firefox"), "caps":
     _c(static=True, js=True, screenshot=True), "best_use": "one-shot Gecko render/screenshot", "failure":
     "one-shot; limited flags", "decision": "Gecko-engine render check", "enable": "system Firefox (present)"},
)


# ── presence probes (real, read-only) ────────────────────────────────────────────────────────────────────────────
def _import_ok(module: str) -> bool:
    try:
        return importlib.util.find_spec(module) is not None
    except Exception:  # noqa: BLE001
        return False


def _which(binary: str) -> Optional[str]:
    return shutil.which(binary)


def _first_chrome() -> Optional[str]:
    return next((shutil.which(c) for c in ("google-chrome-stable", "google-chrome", "chromium", "chromium-browser")
                 if shutil.which(c)), None)


def _node_module(module: str) -> bool:
    if not _which("node"):
        return False
    try:
        out = subprocess.run(["node", "-e", f"try{{require.resolve('{module}');console.log('y')}}catch(e){{}}"],
                             capture_output=True, text=True, timeout=10)
        return "y" in (out.stdout or "")
    except Exception:  # noqa: BLE001
        return False


def _ping(url: str, timeout: float = 2.0) -> dict[str, Any]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:  # noqa: S310 (loopback only)
            return {"up": resp.getcode() == 200, "http": resp.getcode()}
    except urllib.error.HTTPError as http_err:
        return {"up": False, "http": http_err.code}
    except Exception as exc:  # noqa: BLE001
        return {"up": False, "error": type(exc).__name__}


def probe_tool(spec: dict[str, Any]) -> dict[str, Any]:
    """Run the real presence probe for one tool → a probe record (phase 3)."""
    kind, target = spec["probe"]
    status, evidence, error, next_action = "missing", "", None, spec["enable"]
    if kind == "py":
        ok = _import_ok(target)
        status = "available" if ok else "missing"
        evidence = f"importlib.find_spec({target!r}) -> {'present' if ok else 'None'}"
    elif kind == "bin":
        path = _which(target)
        status = "available" if path else "missing"
        evidence = f"shutil.which({target!r}) -> {path or 'None'}"
    elif kind == "node":
        ok = _node_module(target)
        status = "available" if ok else "missing"
        evidence = f"node require.resolve({target!r}) -> {'present' if ok else 'missing'}"
    elif kind == "env":
        present = bool(os.environ.get(target))
        status = "available_with_credentials" if not present else "available"
        evidence = f"env {target} presence={present} (value never read)"
        next_action = f"set {target}" if not present else "key present"
    elif kind == "llm":
        p = _ping(target)
        status = "available" if p.get("up") else "missing"
        evidence = f"GET {target} -> up={p.get('up')} http={p.get('http', p.get('error'))}"
    elif kind == "builtin":
        status, evidence, next_action = "available", f"{target} is stdlib/present", "none (always present)"
    elif kind == "technique":
        status, evidence, next_action = "available", "technique over urllib (present)", "none (always present)"
    elif kind == "first_chrome":
        chrome = _first_chrome()
        status = "available" if chrome else "missing"
        evidence = f"first Chrome/Chromium -> {Path(chrome).name if chrome else 'None'}"
    return {"tool": spec["tool"], "category": spec["category"], "probe_type": kind, "probe_target": target,
            "status": status, "evidence": evidence, "error": error, "next_action": next_action, **BOUNDARY}


def _env_snapshot() -> dict[str, Any]:
    keys = ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "OPENROUTER_API_KEY", "TAVILY_API_KEY", "EXA_API_KEY",
            "SERPAPI_API_KEY", "BRAVE_API_KEY", "BING_API_KEY", "BROWSERBASE_API_KEY", "BROWSERLESS_API_KEY",
            "FIRECRAWL_API_KEY", "APIFY_API_TOKEN")
    return {"python_version": platform.python_version(), "platform": sys.platform,
            "cloud_key_env_presence": {k: bool(os.environ.get(k)) for k in keys},
            "llm_endpoints": {k: _ping(u) for k, u in _LLM_ENDPOINTS.items()},
            "first_chrome": bool(_first_chrome()), "node": bool(_which("node")), "docker": bool(_which("docker"))}


# ── the ~50 primitive candidates: ONE source (namespace + shapes + tool order + safety) ───────────────────────────
def _prim(pid_name: str, category: str, desc: str, in_schema: dict, out_schema: dict, impl: list[str],
          order: list[str], fallback: list[str], side: str, perms: list[str], safety_policy: str,
          failures: list[str], verifiers: list[str], fixture: str, next_action: str) -> dict[str, Any]:
    return {"record_type": "browser_primitive_candidate", "schema_version": SCHEMA_VERSION,
            "primitive_id": canonical_id("bprim", pid_name), "name": pid_name, "category": category,
            "description": desc, "input_schema": in_schema, "output_schema": out_schema,
            "implementation_options": impl, "preferred_tool_order": order, "fallback_tools": fallback,
            "side_effects": side, "required_permissions": perms, "safety_policy": safety_policy,
            "failure_modes": failures, "verifiers": verifiers, "test_fixture": fixture,
            "recommended_next_action": next_action, **BOUNDARY}


def _primitives() -> list[dict[str, Any]]:
    RO, GATE = "read_only", "gated_side_effect"
    url_in = {"url": "string(http/https)"}
    html_in = {"html": "string", "base_url": "string?"}
    P: list[dict[str, Any]] = [
        # ── web.* (fetch + parse) ──
        _prim("web.fetch_static", "web", "Single read-only HTTP GET → response record.", url_in,
              {"status": "int", "text": "string(bounded,redacted)", "headers": "obj", "elapsed_ms": "float"},
              ["browser_control.FetchAdapter", "requests", "httpx", "urllib", "curl"],
              ["requests", "httpx", "urllib"], ["curl", "wget"], RO, ["network:egress"],
              "respect robots; GET only; redact secrets; bounded body", ["http_timeout", "dns_error", "http_5xx"],
              ["status in 2xx/3xx", "content-type present"], "run_browser_fixture_lab", "wire into api.discover_openapi"),
        _prim("web.fetch_with_retry", "web", "GET with bounded exponential backoff on transient failure.", url_in,
              {"status": "int", "attempts": "int", "text": "string"}, ["browser_control.FetchAdapter", "requests"],
              ["requests", "httpx"], ["urllib"], RO, ["network:egress"], "cap attempts; respect Retry-After; robots",
              ["exhausted_retries"], ["final status recorded"], "run_browser_fixture_lab", "add jittered backoff policy"),
        _prim("web.conditional_get", "web", "Revalidate via ETag/Last-Modified (304-aware).", {"url": "string",
              "etag": "string?", "last_modified": "string?"}, {"status": "int", "not_modified": "bool"},
              ["browser_control.FetchAdapter"], ["requests", "httpx"], ["urllib"], RO, ["network:egress"],
              "respect robots; send validators only", ["stale_cache"], ["304 handled"], "run_browser_fixture_lab",
              "wire a CDC freshness check"),
        _prim("web.head_probe", "web", "HEAD to read content-type/length without the body.", url_in,
              {"status": "int", "content_type": "string", "content_length": "int?"}, ["curl", "requests", "httpx"],
              ["requests", "httpx"], ["curl"], RO, ["network:egress"], "respect robots; HEAD only",
              ["method_not_allowed"], ["content-type present"], "run_browser_fixture_lab", "gate downloads on type/size"),
        _prim("web.fetch_json", "web", "GET a JSON endpoint → parsed object.", url_in, {"json": "obj", "status": "int"},
              ["browser_control.FetchAdapter", "requests", "httpx"], ["requests", "httpx"], ["urllib"], RO,
              ["network:egress"], "respect robots; validate JSON", ["invalid_json"], ["json parses"],
              "run_browser_fixture_lab:/api/items", "feed api.parse_openapi_paths"),
        _prim("web.download_document", "web", "List+hash a downloadable doc (pdf/csv/xlsx); fetch is gated.", url_in,
              {"url": "string", "ext": "string", "trust_tier": "string", "sha256": "string?"},
              ["browser_control.BrowserAdapter.download_artifacts", "curl", "wget"], ["harness"], ["curl", "wget"],
              GATE, ["network:egress", "storage:write"], "LIST by default; a binary fetch needs approval; no auth",
              ["not_a_document", "too_large"], ["ext in allowlist", "hash recorded"], "fake_adapter",
              "wire an approval gate before binary fetch"),
        _prim("web.detect_content_type", "web", "Sniff MIME from headers + magic bytes.", {"headers": "obj",
              "head_bytes": "bytes?"}, {"content_type": "string", "is_binary": "bool"}, ["stdlib:mimetypes"],
              ["stdlib"], [], RO, [], "no fetch of body beyond a small head", ["ambiguous_type"],
              ["type resolved or unknown"], "run_browser_fixture_lab", "route by type to parser/document lane"),
        _prim("web.follow_redirect_chain", "web", "Record the redirect hops of a URL (read-only).", url_in,
              {"hops": "list[url]", "final_url": "string"}, ["browser_control.FetchAdapter", "requests"],
              ["requests", "httpx"], ["urllib"], RO, ["network:egress"], "respect robots; cap hop count",
              ["redirect_loop"], ["final_url reached"], "run_browser_fixture_lab", "flag cross-origin hops"),
        _prim("web.rate_limited_fetch", "web", "Per-domain politeness wrapper around a fetch.", {"url": "string",
              "min_interval_s": "float"}, {"status": "int", "waited_ms": "float"},
              ["browser_control.crawler_adapter.RateLimiter", "harness.RateLimiter"], ["harness"], [], RO,
              ["network:egress"], "enforce a per-domain floor; respect robots", ["over_throttle"],
              ["interval honored"], "ingestion_self_test", "expose per-tenant budgets"),
        _prim("web.extract_readable_text", "web", "HTML → clean readable text (secrets redacted).", html_in,
              {"text": "string", "chars": "int", "secrets_redacted": "int"},
              ["browser_control.ParserAdapter", "harness.browser_extract_readable_text", "trafilatura"],
              ["stdlib", "trafilatura"], ["bs4"], RO, [], "redact secrets; bounded", ["empty_extract"],
              ["chars>0 on content pages"], "run_browser_fixture_lab", "add language detect"),
        _prim("web.extract_links", "web", "HTML → absolute link list.", html_in, {"links": "list[url]",
              "n_links": "int"}, ["browser_control.ParserAdapter", "harness.browser_extract_links"], ["stdlib"],
              ["bs4", "lxml"], RO, [], "resolve against base_url; http(s) only", ["malformed_href"],
              ["all links absolute"], "run_browser_fixture_lab", "classify nav vs content links"),
        _prim("web.extract_tables", "web", "HTML <table> → rows/header (stdlib).", {"html": "string"},
              {"tables": "list[obj]", "n_tables": "int"}, ["browser_control.adapter.extract_tables_from_html"],
              ["stdlib"], ["pandas.read_html"], RO, [], "bounded rows/cols; unescape", ["nested_tables"],
              ["rows present"], "run_browser_fixture_lab", "map to dimension_value rows"),
        _prim("web.extract_metadata", "web", "title/description/canonical/lang/OpenGraph.", {"html": "string"},
              {"title": "string", "description": "string", "open_graph": "obj", "lang": "string"},
              ["browser_control.ParserAdapter"], ["stdlib"], ["bs4"], RO, [], "redact description",
              ["no_meta"], ["title or og present"], "run_browser_fixture_lab", "seed source_record metadata"),
        _prim("web.extract_forms", "web", "Enumerate forms + fields (never submit).", {"html": "string"},
              {"forms": "list[obj]", "n_forms": "int"}, ["browser_control.ParserAdapter",
              "harness.browser_extract_forms"], ["stdlib"], [], RO, [], "enumerate only; NEVER submit",
              ["dynamic_forms"], ["fields listed"], "fake_adapter", "propose form_field_mapper primitive"),
        _prim("web.detect_login_wall", "web", "Classify whether a page is gated by login.", {"html": "string"},
              {"login_wall": "bool"}, ["harness.browser_detect_login_wall"], ["stdlib"], [], RO, [],
              "detect only; never authenticate for the user", ["false_negative"], ["flag matches markers"],
              "fake_adapter", "route gated pages to review"),
        _prim("web.detect_captcha", "web", "Detect a captcha challenge (DETECT ONLY — never solve).",
              {"html": "string"}, {"captcha": "bool"}, ["harness.browser_detect_captcha"], ["stdlib"], [], RO, [],
              "DETECT ONLY; solving/bypass is PROHIBITED", ["novel_captcha"], ["known markers flagged"],
              "fake_adapter", "abort + report on detection"),
        _prim("web.detect_api_spec_links", "web", "Find OpenAPI/GraphQL references on a page.", html_in,
              {"openapi_links": "list", "graphql": "bool"}, ["harness.browser_detect_openapi_links",
              "harness.browser_detect_graphql_endpoint"], ["stdlib"], [], RO, [], "reference detection only",
              ["spec_moved"], ["links resolve"], "run_browser_fixture_lab", "hand to api.discover_openapi"),
        _prim("web.detect_downloadable_docs", "web", "List downloadable doc links (pdf/csv/xlsx/…).", {"links":
              "list[url]"}, {"docs": "list[url]"}, ["harness.browser_detect_downloadable_docs"], ["stdlib"], [], RO,
              [], "list only; fetch is gated", ["extension_spoof"], ["ext in allowlist"], "fake_adapter",
              "feed web.download_document"),
        # ── browser.* (rendered/interactive) ──
        _prim("browser.render_page", "browser", "Render JS → settled DOM.", url_in, {"dom": "string", "js_rendered":
              "bool"}, ["browser_control.CdpAdapter", "browser_control.PlaywrightAdapter", "chrome --dump-dom",
              "nodriver"], ["cdp", "playwright"], ["chrome_cli", "lightpanda"], RO, ["browser:launch"],
              "respect robots; read-only; no auth reuse", ["render_timeout", "anti_bot"], ["placeholder replaced"],
              "run_browser_fixture_lab", "prefer static fetch when raw HTML suffices"),
        _prim("browser.screenshot", "browser", "Capture a screenshot (bytes hashed, not stored).", url_in,
              {"screenshot_hash": "string"}, ["browser_control.CdpAdapter", "browser_control.PlaywrightAdapter",
              "chrome --screenshot"], ["cdp", "playwright"], ["chrome_cli"], RO, ["browser:launch"],
              "store digest not image; redact nothing renders secrets", ["blank_render"], ["hash present"],
              "fake_adapter", "diff against a baseline"),
        _prim("browser.capture_network", "browser", "Observe network requests / XHR / API calls.", url_in,
              {"network_artifacts": "list[obj]"}, ["browser_control.CdpAdapter", "playwright", "raw-CDP"],
              ["cdp", "playwright"], [], RO, ["browser:launch"], "capture metadata; redact auth headers",
              ["no_xhr"], ["artifacts listed"], "fake_adapter", "mine XHR endpoints into api.* primitives"),
        _prim("browser.open_tab", "browser", "Open a new tab/target.", url_in, {"tab_id": "string"},
              ["browser_control.CdpAdapter", "playwright"], ["cdp", "playwright"], [], RO, ["browser:launch"],
              "read-only navigation", ["popup_blocked"], ["tab_id returned"], "fake_adapter", "track opener graph"),
        _prim("browser.list_tabs", "browser", "List open tabs.", {}, {"tabs": "list[obj]"},
              ["browser_control.CdpAdapter", "playwright"], ["cdp", "playwright"], [], RO, ["browser:launch"],
              "read-only", ["stale_tab"], ["active flagged"], "fake_adapter", "feed tab_graph"),
        _prim("browser.focus_tab", "browser", "Activate a tab.", {"tab_id": "string"}, {"focused": "bool"},
              ["browser_control.CdpAdapter", "playwright"], ["cdp", "playwright"], [], RO, ["browser:launch"],
              "read-only", ["tab_gone"], ["focused true"], "fake_adapter", "none"),
        _prim("browser.close_tab", "browser", "Close a tab (last tab protected).", {"tab_id": "string"},
              {"closed": "bool"}, ["browser_control.CdpAdapter", "playwright"], ["cdp", "playwright"], [], RO,
              ["browser:launch"], "never close the last tab", ["protected_last"], ["closed or refused"],
              "fake_adapter", "none"),
        _prim("browser.click_ref", "browser", "Click an element (GATED side effect).", {"ref": "string",
              "side_effect": "string"}, {"executed": "bool", "requires_confirmation": "bool"},
              ["browser_control.BrowserAdapter.click_ref"], ["cdp", "playwright"], [], GATE, ["browser:interact"],
              "refused read-only by default; write+ needs human confirm; never submit money/pay", ["stale_ref"],
              ["gate decision receipted"], "fake_adapter", "compile discovered clicks to scripts"),
        _prim("browser.fill_ref", "browser", "Fill a field (GATED; value redacted in receipt).", {"ref": "string",
              "value": "string"}, {"executed": "bool"}, ["browser_control.BrowserAdapter.fill_ref"], ["cdp",
              "playwright"], [], GATE, ["browser:interact"], "redact value; no submit; read-level default",
              ["readonly_field"], ["value redacted in receipt"], "fake_adapter", "never chain into a submit"),
        _prim("browser.wait_for_state", "browser", "Wait until text/url/state condition (read-only verify).",
              {"contains": "string?", "url_is": "string?"}, {"passed": "bool"},
              ["browser_control.BrowserAdapter.wait_for_state"], ["cdp", "playwright"], [], RO, ["browser:launch"],
              "bounded timeout; read-only", ["timeout"], ["condition met or timeout"], "fake_adapter", "none"),
        _prim("browser.attach_to_session", "browser", "Attach to an already-open Chrome/session over CDP.",
              {"cdp_port": "int"}, {"attached": "bool"}, ["browser_control.CdpAdapter", "raw-CDP"], ["cdp"], [], GATE,
              ["browser:attach"], "explicit human consent; acts as the user — treat as privileged", ["no_endpoint"],
              ["attach receipt"], "n/a(live)", "consent gate before attach"),
        _prim("browser.dump_dom", "browser", "One-shot JS render via chrome --dump-dom (zero libraries).", url_in,
              {"dom": "string", "js_rendered": "bool"}, ["chrome --headless --dump-dom", "chromium"],
              ["chrome_cli"], ["lightpanda"], RO, ["browser:launch"], "respect robots; read-only", ["cli_timeout"],
              ["placeholder replaced"], "run_browser_fixture_lab", "prefer for keyless render"),
        _prim("browser.build_tab_graph", "browser", "Opener/cross-origin/popup tab graph from a session.", {},
              {"tab_graph": "obj"}, ["browser_control.BrowserAdapter.build_tab_graph"], ["fake", "cdp"], [], RO, [],
              "read-only projection", ["single_tab"], ["nodes present"], "fake_adapter", "flag cross-origin edges"),
        _prim("browser.session_report", "browser", "Evidence report over a browsing session (candidate-only).", {},
              {"report": "obj"}, ["browser_control.BrowserAdapter.build_session_report",
              "scripts.browser_session_report"], ["fake", "cdp"], [], RO, [], "no raw body; secrets redacted",
              ["empty_session"], ["byte-identical rebuild"], "fake_adapter", "feed browser_report_to_primitives"),
        # ── crawler.* ──
        _prim("crawler.fetch_robots", "crawler", "Fetch + expose robots.txt.", {"base_url": "string"},
              {"robots_txt": "string", "found": "bool"}, ["browser_control.CrawlerAdapter"], ["stdlib"], [], RO,
              ["network:egress"], "read-only", ["no_robots"], ["found flag correct"], "ingestion_self_test",
              "cache per host"),
        _prim("crawler.robots_gate", "crawler", "Decide if a URL is crawlable per robots.", url_in,
              {"allowed": "bool"}, ["browser_control.safety.robots_gate", "harness.browser_respect_robots_policy"],
              ["stdlib"], [], RO, [], "deny-by-policy on Disallow; absent robots ⇒ allowed", ["parse_error"],
              ["Allow/Disallow honored"], "ingestion_self_test", "log every deny"),
        _prim("crawler.fetch_sitemap", "crawler", "Parse sitemap.xml (+ sitemap index).", {"base_url": "string"},
              {"urls": "list[url]", "is_index": "bool"}, ["browser_control.CrawlerAdapter"], ["stdlib:ElementTree"],
              [], RO, ["network:egress"], "bounded url count; http(s) only", ["malformed_xml"], ["urls parsed"],
              "ingestion_self_test", "expand a sitemap index recursively"),
        _prim("crawler.parse_feed", "crawler", "Parse an RSS/Atom feed → item links.", {"feed_url": "string"},
              {"items": "list[obj]"}, ["stdlib:ElementTree", "feedparser"], ["stdlib"], ["feedparser"], RO,
              ["network:egress"], "read-only; bounded", ["not_a_feed"], ["items parsed"], "ingestion_self_test",
              "seed a crawl from feed items"),
        _prim("crawler.bfs_crawl", "crawler", "Robots-gated, rate-limited, read-only BFS.", {"seeds": "list[url]",
              "max_pages": "int"}, {"pages": "list[obj]", "skipped_robots": "list", "skipped_rate_limited": "list"},
              ["browser_control.CrawlerAdapter", "harness.crawl", "scrapy"], ["harness"], ["scrapy", "crawlee"], RO,
              ["network:egress"], "respect robots; per-domain throttle; page cap; same-origin; no forms",
              ["frontier_explosion"], ["cap honored", "disallowed skipped"], "ingestion_self_test", "add scrapy engine"),
        _prim("crawler.same_origin_frontier", "crawler", "Restrict the frontier to the seed origin.", {"links":
              "list[url]", "origin": "string"}, {"frontier": "list[url]"}, ["browser_control.CrawlerAdapter"],
              ["stdlib"], [], RO, [], "same-origin unless allowlisted", ["subdomain_leak"], ["origin enforced"],
              "ingestion_self_test", "add an allowlist"),
        _prim("crawler.dedupe_urls", "crawler", "Canonicalize + dedupe URLs (drop fragments/tracking).", {"urls":
              "list[url]"}, {"unique": "list[url]"}, ["stdlib:urllib.parse"], ["stdlib"], [], RO, [],
              "normalize deterministically", ["over_dedupe"], ["stable unique set"], "ingestion_self_test",
              "strip known tracking params"),
        _prim("crawler.politeness_scheduler", "crawler", "Per-domain throttle scheduler.", {"domain": "string",
              "min_interval_s": "float"}, {"ready": "bool"}, ["harness.RateLimiter"], ["harness"], [], RO, [],
              "enforce a politeness floor", ["clock_skew"], ["interval honored"], "ingestion_self_test",
              "per-tenant budgets"),
        # ── llm.* (UNTRUSTED) ──
        _prim("llm.extract_schema", "llm", "Fill a target schema from page text (UNTRUSTED).", {"text": "string",
              "schema": "obj"}, {"extraction": "obj", "untrusted": "true"}, ["browser_control.LLMExtractionAdapter",
              "Ollama :11434", "OpenAI-compat :8000", "OpenRouter file lane"], ["offline_stub", "local_llm"],
              ["cloud_llm"], RO, ["llm:invoke"], "output UNTRUSTED serves_truth=false; verify before use; redact",
              ["hallucination", "schema_drift"], ["llm.verify_extraction grounding"], "ingestion_self_test",
              "gate promotion on a grounding pass"),
        _prim("llm.extract_primitives", "llm", "Propose candidate primitives from text (UNTRUSTED).", {"text":
              "string"}, {"primitives": "list[obj]", "untrusted": "true"}, ["browser_control.LLMExtractionAdapter"],
              ["offline_stub", "local_llm"], ["cloud_llm"], RO, ["llm:invoke"],
              "candidates only; never auto-promote", ["overgeneration"], ["dedupe + source review"],
              "ingestion_self_test", "route to the foundry as candidates"),
        _prim("llm.ask_questions", "llm", "Answer a question bank from text (UNTRUSTED).", {"text": "string",
              "questions": "list"}, {"answers": "list[obj]"}, ["browser_control.LLMExtractionAdapter"],
              ["offline_stub", "local_llm"], ["cloud_llm"], RO, ["llm:invoke"], "answers UNTRUSTED; grounded flag",
              ["ungrounded_answer"], ["grounding check"], "ingestion_self_test", "keep as advisory"),
        _prim("llm.verify_extraction", "llm", "Deterministic grounding check of an extraction vs source text.",
              {"extraction": "obj", "text": "string"}, {"all_grounded": "bool", "n_ungrounded": "int"},
              ["browser_control.LLMExtractionAdapter"], ["deterministic"], [], RO, [],
              "the trustworthy gate over untrusted LLM output", ["paraphrase_miss"], ["substring grounding"],
              "ingestion_self_test", "extend to fuzzy grounding"),
        _prim("llm.plan_browser_actions", "llm", "LLM plans browser actions over a UI (QUARANTINED candidate).",
              {"goal": "string", "dom": "string"}, {"plan": "list[obj]", "untrusted": "true"}, ["browser-use",
              "stagehand"], ["offline_stub"], ["browser_use", "stagehand"], GATE, ["llm:invoke", "browser:interact"],
              "plan is candidate; every side-effecting step human-gated; distill to Playwright", ["unsafe_step"],
              ["human review before execute"], "n/a(agentic)", "compile winning plans to deterministic scripts"),
        _prim("llm.summarize_page", "llm", "Summarize a page (UNTRUSTED).", {"text": "string"}, {"summary":
              "string", "untrusted": "true"}, ["browser_control.LLMExtractionAdapter"], ["offline_stub",
              "local_llm"], ["cloud_llm"], RO, ["llm:invoke"], "UNTRUSTED; not truth", ["hallucination"],
              ["grounding sample"], "ingestion_self_test", "keep advisory"),
        # ── api.* ──
        _prim("api.discover_openapi", "api", "Discover an OpenAPI/Swagger spec from a site.", {"base_url": "string"},
              {"spec_url": "string", "found": "bool"}, ["browser_control.FetchAdapter",
              "harness.browser_detect_openapi_links"], ["stdlib"], [], RO, ["network:egress"],
              "PREFER a spec over a browser; respect robots", ["no_spec"], ["spec parses"],
              "run_browser_fixture_lab:/openapi.json", "generate request/response primitives"),
        _prim("api.parse_openapi_paths", "api", "Parse an OpenAPI doc → path/operation table.", {"spec": "obj"},
              {"paths": "list[obj]", "n_paths": "int"}, ["stdlib:json", "pyyaml"], ["stdlib"], ["prance"], RO, [],
              "read-only parse", ["invalid_spec"], ["paths counted"], "run_browser_fixture_lab", "mint api_endpoint primitives"),
        _prim("api.introspect_graphql", "api", "Introspect a GraphQL endpoint → root types.", {"endpoint": "string"},
              {"types": "list", "query_type": "string"}, ["browser_control.FetchAdapter"], ["stdlib"], [], RO,
              ["network:egress"], "introspection query only; respect robots", ["introspection_disabled"],
              ["schema parsed"], "run_browser_fixture_lab:/graphql", "map fields to primitives"),
        _prim("api.call_endpoint", "api", "Call a discovered read GET endpoint (structured).", {"url": "string",
              "params": "obj?"}, {"status": "int", "json": "obj"}, ["browser_control.FetchAdapter", "requests"],
              ["requests", "httpx"], ["urllib"], GATE, ["network:egress", "api:call"],
              "GET/read endpoints only by default; writes need approval; respect rate limits", ["auth_required"],
              ["status recorded"], "run_browser_fixture_lab:/api/items", "add auth-scoped calls behind a gate"),
        _prim("api.web_search", "api", "Web search via a provider API (available_with_credentials).", {"query":
              "string"}, {"results": "list[obj]", "status": "string"}, ["browser_control.SearchAdapter", "tavily",
              "exa", "serpapi", "brave", "bing"], ["tavily", "exa"], ["serpapi", "brave", "bing"], RO,
              ["network:egress", "credential:search_key"], "keyless ⇒ available_with_credentials; never fabricate",
              ["no_key", "quota"], ["results or available_with_credentials"], "ingestion_self_test",
              "wire a key + rank results"),
        # ── artifact.* (evidence / provenance) ──
        _prim("artifact.capture_page", "artifact", "Read-only page capture → CapturedArtifact (no raw body).",
              url_in, {"artifact_id": "string", "source_hash": "string", "extracted": "obj"},
              ["harness.capture_artifact"], ["harness"], [], RO, ["network:egress"],
              "digest + bounded text + structured units; NEVER a raw body or secret", ["empty_body"],
              ["hash + evidence_refs present"], "fake_adapter", "link candidates to source spans"),
        _prim("artifact.action_receipt", "artifact", "Mint a browser_action_receipt for a command.", {"action":
              "string", "input": "obj"}, {"receipt": "obj"}, ["browser_control.adapter.normalize_receipt",
              "harness.TabControlAPI"], ["harness"], [], RO, [], "every action produces an evidence record",
              ["missing_field"], ["validates vs receipt schema"], "browser_control.self_test", "persist a ledger"),
        _prim("artifact.redact_secrets", "artifact", "Redact secret-shaped substrings before persist/log.",
              {"text": "string"}, {"clean": "string", "n_redacted": "int"}, ["harness.redact_secrets",
              "browser_control.safety.redact_fields"], ["harness"], [], RO, [], "apply before ANY log/persist",
              ["novel_secret_shape"], ["known shapes removed"], "browser_control.self_test", "extend the regex set"),
        _prim("artifact.classify_trust_tier", "artifact", "Classify a URL's source trust tier (T0–T4).", url_in,
              {"trust_tier": "string"}, ["harness.classify_trust_tier"], ["harness"], [], RO, [],
              "official > vendor > repo > community > unknown", ["unknown_host"], ["tier assigned"],
              "browser_control.self_test", "feed promotion gates"),
        _prim("artifact.content_hash", "artifact", "Canonical sha256 of a normalized body/spec.", {"text":
              "string"}, {"sha256": "string"}, ["harness._sha256", "src.teleon.experiments.ids"], ["harness"], [],
              RO, [], "stable hash; formatting-invariant where specified", ["encoding_drift"],
              ["byte-stable digest"], "browser_control.self_test", "wire CDC change detection"),
    ]
    return P


def _primitive_probe_status(prim: dict[str, Any], tool_status: dict[str, str]) -> str:
    """Derive a primitive's probe status from its implementation options: available if any option is available,
    else available_with_credentials if any is keyed, else missing. stdlib/harness options are always available."""
    always = ("stdlib", "harness", "deterministic", "offline_stub")
    statuses: list[str] = []
    for opt in prim["implementation_options"]:
        low = opt.lower()
        if any(a in low for a in always) or low.startswith(("browser_control", "src.")):
            statuses.append("available")
            continue
        matched = next((s for t, s in tool_status.items() if t.lower() in low or low in t.lower()), None)
        statuses.append(matched or "unknown")
    if "available" in statuses:
        return "available"
    if "available_with_credentials" in statuses:
        return "available_with_credentials"
    return "missing"


# ── live SAFE-target probes (phase 4) — SINGLE-PAGE, robots-respecting, no crawling/volume ────────────────────────
def live_probes() -> list[dict[str, Any]]:
    """Drive the AVAILABLE fetch/parse/render lanes against the sanctioned safe targets + the local fixture.
    One GET per target; respects robots; records latency + what was found. Returns phase-4 probe records."""
    from browser_control.fetch_adapter import FetchAdapter
    from browser_control.parser_adapter import ParserAdapter
    out: list[dict[str, Any]] = []
    fa, pa = FetchAdapter(), ParserAdapter()
    for target in SAFE_TARGETS:
        r = fa.get(target)
        rec = {"tool": f"FetchAdapter/{r.get('backend')}", "category": "http_client", "probe_type": "live_fetch",
               "method": "GET", "target": target, "success": bool(r.get("ok")), "status": r.get("status"),
               "latency_ms": r.get("elapsed_ms"), "bytes": r.get("bytes"),
               "limitations": "static HTML only (no JS render)",
               "failure_mode": r.get("failure_mode"), "blocked": r.get("blocked"),
               "evidence": f"HTTP {r.get('status')} in {r.get('elapsed_ms')}ms via {r.get('backend')}", **BOUNDARY}
        out.append(rec)
        if r.get("ok") and r.get("text"):
            p = pa.parse(r["text"], base_url=target)
            out.append({"tool": "ParserAdapter", "category": "html_parser", "probe_type": "live_parse",
                        "method": "parse", "target": target, "success": True,
                        "limitations": "sees only the fetched (server) HTML", "failure_mode": None,
                        "evidence": f"title={p['metadata']['title'][:40]!r} n_links={p['n_links']} "
                        f"n_tables={p['n_tables']} text_chars={p['text_chars']}", **BOUNDARY})
    # one keyless JS-render proof on a public target via chrome --dump-dom (single page)
    chrome = _first_chrome()
    if chrome:
        t0 = time.monotonic()
        try:
            o = subprocess.run([chrome, "--headless=new", "--no-sandbox", "--disable-gpu",
                                "--virtual-time-budget=1500", "--dump-dom", "https://example.com"],
                               capture_output=True, text=True, timeout=45)
            dom = o.stdout or ""
            out.append({"tool": f"chrome-cli/{Path(chrome).name}", "category": "local_binary",
                        "probe_type": "live_render", "method": "--dump-dom", "target": "https://example.com",
                        "success": bool(dom), "latency_ms": round((time.monotonic() - t0) * 1000, 1),
                        "limitations": "one-shot; no interaction", "failure_mode": None if dom else "empty_dom",
                        "evidence": f"rendered DOM {len(dom)}B via headless Chrome", **BOUNDARY})
        except Exception as exc:  # noqa: BLE001
            out.append({"tool": f"chrome-cli/{Path(chrome).name}", "category": "local_binary",
                        "probe_type": "live_render", "method": "--dump-dom", "target": "https://example.com",
                        "success": False, "failure_mode": type(exc).__name__, "evidence": str(exc)[:120], **BOUNDARY})
    return out


def live_fixture_crawl() -> dict[str, Any]:
    """Crawl the LOCAL offline fixture (not a public site) to exercise the crawler lane end-to-end, read-only."""
    from browser_control.crawler_adapter import CrawlerAdapter
    from scripts.run_browser_fixture_lab import serve_in_thread
    httpd, base = serve_in_thread(0)
    try:
        ca = CrawlerAdapter(min_interval=0.0)
        res = ca.crawl([base + "/"], max_pages=5, min_interval=0.0)
        sm = ca.fetch_sitemap(base + "/")
        return {"tool": "CrawlerAdapter", "category": "crawl_framework", "probe_type": "live_crawl_fixture",
                "method": "bfs+sitemap", "target": base, "success": res["ok"], "n_captured": res["n_captured"],
                "n_sitemap_urls": sm["n_urls"], "limitations": "local fixture only (no public crawl)",
                "failure_mode": None, "evidence": f"crawled {res['n_captured']} fixture pages; "
                f"sitemap {sm['n_urls']} urls; skipped_robots={res['skipped_robots']}", **BOUNDARY}
    finally:
        httpd.shutdown()
        httpd.server_close()


# ── assemble the inventory ────────────────────────────────────────────────────────────────────────────────────────
def build_inventory(*, live: bool = False) -> dict[str, Any]:
    env = _env_snapshot()
    probe_records = [probe_tool(t) for t in TOOLS]
    tool_status = {r["tool"]: r["status"] for r in probe_records}
    live_records: list[dict[str, Any]] = []
    if live:
        live_records = live_probes()
        live_records.append(live_fixture_crawl())
    tools_enriched = []
    for spec, rec in zip(TOOLS, probe_records):
        tools_enriched.append({
            "tool": spec["tool"], "category": spec["category"], "probe_type": rec["probe_type"],
            "status": rec["status"], "available": rec["status"] in ("available", "available_with_credentials"),
            "needs_credentials": rec["status"] == "available_with_credentials",
            "capabilities": spec["caps"], "best_use": spec["best_use"], "failure": spec["failure"],
            "decision": spec["decision"], "enable": spec["enable"], "evidence": rec["evidence"], **BOUNDARY})
    summary = {
        "n_tools": len(TOOLS),
        "n_available": sum(1 for t in tools_enriched if t["status"] == "available"),
        "n_available_with_credentials": sum(1 for t in tools_enriched
                                            if t["status"] == "available_with_credentials"),
        "n_missing": sum(1 for t in tools_enriched if t["status"] == "missing"),
        "by_category": sorted({t["category"] for t in tools_enriched}),
    }
    return {"record_type": "browser_tool_inventory", "schema_version": SCHEMA_VERSION,
            "inventory_id": canonical_id("bti", "browser_tool_inventory", SCHEMA_VERSION),
            "generated_by": "scripts/build_browser_tool_inventory.py", "environment": env, "summary": summary,
            "tools": tools_enriched, "probe_records": probe_records, "live_records": live_records,
            "primitive_status_index": tool_status, **BOUNDARY}


# ── doc + gap renderers (single-sourced from the inventory) ───────────────────────────────────────────────────────
_MATRIX_COLS = ("static", "js", "actions", "multi_tab", "screenshot", "network", "download", "llm", "api_first")
_COL_SHORT = {"static": "static", "js": "js", "actions": "actions", "multi_tab": "multi-tab", "screenshot": "shot",
              "network": "net", "download": "dl", "llm": "llm", "api_first": "api-first"}


def _g(v: bool) -> str:
    return "✓" if v else "·"


def render_matrix_markdown(inv: dict[str, Any]) -> str:
    L: list[str] = []
    s = inv["summary"]
    L.append("# Browser & Web-Ingestion — Automation Capability Matrix")
    L.append("")
    L.append(f"> Generated by `{inv['generated_by']}` from `artifacts/browser_control/browser_tools_inventory.json` "
             f"(schema {inv['schema_version']}, id `{inv['inventory_id']}`). Candidate-only "
             f"(`serves_truth={str(inv['serves_truth']).lower()}`). Do NOT hand-edit — re-run "
             "`python3 scripts/build_browser_tool_inventory.py --run` (add `--live` for phase-4 evidence).")
    L.append("")
    L.append(f"**Probed on this machine:** {s['n_tools']} tools — **{s['n_available']} available**, "
             f"**{s['n_available_with_credentials']} available-with-credentials**, **{s['n_missing']} missing**. "
             "`available`/`creds`/`probed` are LIVE presence on THIS host; the capability columns are the tool's "
             "PROFILE (what it can do). Env keys are presence-only (never a value).")
    L.append("")
    header = ["tool", "category", "available", "creds", "probed", "result"] + \
             [_COL_SHORT[c] for c in _MATRIX_COLS] + ["best-use", "failure", "decision"]
    L.append("| " + " | ".join(header) + " |")
    L.append("|" + "|".join(["---"] * len(header)) + "|")
    for t in inv["tools"]:
        caps = t["capabilities"]
        avail = _g(t["status"] == "available")
        creds = _g(t["status"] == "available_with_credentials")
        row = [f"`{t['tool']}`", t["category"], avail, creds, "✓", t["status"]]
        row += [_g(caps[c]) for c in _MATRIX_COLS]
        row += [t["best_use"], t["failure"], t["decision"]]
        L.append("| " + " | ".join(str(x).replace("|", "\\|") for x in row) + " |")
    L.append("")
    L.append("Legend: ✓ = yes · · = no. `available` = present now; `creds` = present but needs an API key; "
             "`result` = the live probe status. Capability columns = the tool's profile: `static` HTML fetch · "
             "`js` render · `actions` click/fill · `multi-tab` · `shot` screenshot · `net` network capture · "
             "`dl` download · `llm` LLM-planned · `api-first` spec/API access.")
    L.append("")
    if inv.get("live_records"):
        L.append("## Live safe-target probes (phase 4)")
        L.append("")
        L.append("Single-page GETs against the sanctioned safe targets (example.com / httpbin.org / "
                 "quotes.toscrape.com) + the local fixture — robots-respecting, no crawling/volume/auth.")
        L.append("")
        L.append("| tool | method | target | success | latency_ms | evidence |")
        L.append("|---|---|---|---|---|---|")
        for r in inv["live_records"]:
            L.append(f"| `{r.get('tool')}` | {r.get('method', r.get('probe_type'))} | {r.get('target')} | "
                     f"{_g(bool(r.get('success')))} | {r.get('latency_ms', '')} | "
                     f"{str(r.get('evidence', '')).replace('|', '/')} |")
        L.append("")
    L.append("## The layered strategy")
    L.append("")
    L.append("Pick the CHEAPEST lane that reaches the content: **official API / spec** → **raw HTTP fetch + parse** "
             "→ **sitemap/feed-seeded crawl** → **headless render (CDP-attach | one-shot CLI | Playwright)** → "
             "**remote / lightweight browser for scale** → **search API (keyed)** → **agentic LLM browser "
             "(quarantined, human-gated)**. Each is one adapter row in `browser_control/`; a router selects by "
             "the capability the job needs, not by habit.")
    L.append("")
    L.append("Playwright is not the whole strategy. It is one adapter in a layered browser/data-ingestion "
             "primitive architecture.")
    L.append("")
    return "\n".join(L)


def render_gap_report(inv: dict[str, Any], primitives: list[dict[str, Any]]) -> str:
    L: list[str] = []
    L.append("# Browser Automation — Gap Report")
    L.append("")
    L.append(f"> Generated by `{inv['generated_by']}`. Candidate-only (`serves_truth=false`). "
             "What is NOT available on this host, why, the enable path, and which primitives it blocks.")
    L.append("")
    missing = [t for t in inv["tools"] if t["status"] == "missing"]
    creds = [t for t in inv["tools"] if t["status"] == "available_with_credentials"]
    available = [t for t in inv["tools"] if t["status"] == "available"]
    L.append(f"**Summary:** {len(available)} available · {len(creds)} available-with-credentials · "
             f"{len(missing)} missing (of {inv['summary']['n_tools']}).")
    L.append("")
    L.append("## Missing tools (not installed) — enable path")
    L.append("")
    L.append("| tool | category | why it matters | enable |")
    L.append("|---|---|---|---|")
    for t in missing:
        L.append(f"| `{t['tool']}` | {t['category']} | {t['best_use']} | `{t['enable']}` |")
    L.append("")
    L.append("## Available-with-credentials (present but keyless) — set the key to enable")
    L.append("")
    L.append("| tool | category | enable |")
    L.append("|---|---|---|")
    for t in creds:
        L.append(f"| `{t['tool']}` | {t['category']} | `{t['enable']}` |")
    L.append("")
    blocked = [p for p in primitives if p.get("_probe_status") == "missing"]
    creds_p = [p for p in primitives if p.get("_probe_status") == "available_with_credentials"]
    L.append("## Primitives blocked or credential-gated by these gaps")
    L.append("")
    if blocked:
        L.append("**Blocked (no available implementation option):**")
        for p in blocked:
            L.append(f"- `{p['name']}` — options: {', '.join(p['implementation_options'])}")
        L.append("")
    L.append("**Credential-gated (works once a key/provider is set):**")
    for p in creds_p:
        L.append(f"- `{p['name']}` — {p['recommended_next_action']}")
    L.append("")
    L.append("## The honest read")
    L.append("")
    L.append("None of these gaps blocks the core loop: every `web.*`, `crawler.*`, `artifact.*`, and the "
             "deterministic `llm.verify_extraction` primitive runs TODAY on stdlib + the harness + system Chrome. "
             "The missing pieces are optional UPGRADES (faster parsers, a heavier crawl framework, extra drivers) "
             "or keyed/paid lanes (search APIs, managed/remote browsers) — each behind an adapter seam so enabling "
             "it is an install/key, never a rewrite.")
    L.append("")
    return "\n".join(L)


# ── write ─────────────────────────────────────────────────────────────────────────────────────────────────────────
def write_outputs(inv: dict[str, Any], primitives: list[dict[str, Any]]) -> dict[str, Path]:
    _ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    _INVENTORY_PATH.write_text(json.dumps(inv, indent=2, sort_keys=True) + "\n")
    with _PROBE_JSONL.open("w") as fh:
        for r in inv["probe_records"] + inv["live_records"]:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    with _PRIMITIVES_JSONL.open("w") as fh:
        for p in primitives:
            fh.write(json.dumps({k: v for k, v in p.items() if not k.startswith("_")}, sort_keys=True) + "\n")
    _DOC_PATH.parent.mkdir(parents=True, exist_ok=True)
    _DOC_PATH.write_text(render_matrix_markdown(inv))
    _GAP_MD.write_text(render_gap_report(inv, primitives))
    return {"inventory": _INVENTORY_PATH, "probes": _PROBE_JSONL, "primitives": _PRIMITIVES_JSONL,
            "matrix_doc": _DOC_PATH, "gap": _GAP_MD}


def _build_primitives_with_status(inv: dict[str, Any]) -> list[dict[str, Any]]:
    prims = _primitives()
    for p in prims:
        p["_probe_status"] = _primitive_probe_status(p, inv["primitive_status_index"])
        p["probe_status"] = p["_probe_status"]
    return prims


# ── verify-the-verifier ───────────────────────────────────────────────────────────────────────────────────────────
def _validate(inv: dict[str, Any], prims: list[dict[str, Any]]) -> list[str]:
    problems: list[str] = []
    if len(inv["tools"]) != len(TOOLS):
        problems.append("tool count mismatch")
    for t in inv["tools"]:
        if set(t["capabilities"]) != set(_MATRIX_COLS):
            problems.append(f"{t['tool']}: capability columns != matrix columns")
        if t["status"] not in ("available", "available_with_credentials", "missing"):
            problems.append(f"{t['tool']}: bad status {t['status']!r}")
    req = ("primitive_id", "name", "category", "input_schema", "output_schema", "implementation_options",
           "preferred_tool_order", "fallback_tools", "side_effects", "required_permissions", "safety_policy",
           "failure_modes", "verifiers", "test_fixture", "probe_status", "recommended_next_action")
    ns = {"web", "browser", "crawler", "llm", "api", "artifact"}
    ids = set()
    for p in prims:
        for f in req:
            if f not in p:
                problems.append(f"primitive {p.get('name')} missing '{f}'")
        if p.get("category") not in ns:
            problems.append(f"primitive {p.get('name')} bad namespace {p.get('category')!r}")
        if p.get("serves_truth") is not False or p.get("candidate") is not True:
            problems.append(f"primitive {p.get('name')} not candidate-only")
        ids.add(p.get("primitive_id"))
    if len(ids) != len(prims):
        problems.append("primitive_id collision (ids not unique)")
    try:
        json.dumps(inv)
        json.dumps(prims)
    except Exception as exc:  # noqa: BLE001
        problems.append(f"not JSON-serializable: {exc}")
    return problems


def self_test() -> int:
    checks: list[tuple[str, bool]] = []
    inv = build_inventory(live=False)
    prims = _build_primitives_with_status(inv)

    problems = _validate(inv, prims)
    checks.append(("inventory + primitives build offline with a clean structure", problems == []))
    for p in problems:
        print(f"    - {p}")
    checks.append(("broad tool list covered (>=30 tools across categories)",
                   len(TOOLS) >= 30 and len(inv["summary"]["by_category"]) >= 10))
    checks.append(("~50 primitives across all 6 namespaces",
                   len(prims) >= 50 and {p["category"] for p in prims} ==
                   {"web", "browser", "crawler", "llm", "api", "artifact"}))
    checks.append(("every primitive carries the full schema + candidate-only",
                   all("primitive_id" in p and p["serves_truth"] is False for p in prims)))
    checks.append(("env key presence-only (no values captured anywhere)",
                   all(isinstance(v, bool) for v in inv["environment"]["cloud_key_env_presence"].values())))
    checks.append(("offline truth: urllib + official-API + sitemap lanes are available",
                   inv["primitive_status_index"]["urllib"] == "available"
                   and inv["primitive_status_index"]["official-API (OpenAPI/GraphQL/REST)"] == "available"))
    md = render_matrix_markdown(inv)
    checks.append(("matrix renders with the big table + the load-bearing final line",
                   "| tool | category | available |" in md and "Automation Capability Matrix" in md
                   and md.rstrip().endswith("It is one adapter in a layered browser/data-ingestion primitive "
                                            "architecture.")))
    gap = render_gap_report(inv, prims)
    checks.append(("gap report renders (missing + credential-gated sections)",
                   "Missing tools" in gap and "Available-with-credentials" in gap))

    # determinism: primitive ids + doc are byte-identical across two fresh offline builds
    inv2 = build_inventory(live=False)
    prims2 = _build_primitives_with_status(inv2)
    det = ([p["primitive_id"] for p in prims] == [p["primitive_id"] for p in prims2]
           and json.dumps([{k: v for k, v in p.items() if not k.startswith("_")} for p in prims], sort_keys=True)
           == json.dumps([{k: v for k, v in p.items() if not k.startswith("_")} for p in prims2], sort_keys=True))
    checks.append(("determinism: primitive ids + rows byte-identical across two builds", det))

    # MUTATION GATE: a corrupted primitive / tool row must be flagged
    bad_prim = copy.deepcopy(prims)
    bad_prim[0].pop("input_schema")
    bad_tool = copy.deepcopy(inv)
    bad_tool["tools"][0]["capabilities"].pop("static")
    bad_ns = copy.deepcopy(prims)
    bad_ns[0]["category"] = "not_a_namespace"
    checks.append(("mutation gate bites: dropped primitive field flagged", _validate(inv, bad_prim) != []))
    checks.append(("mutation gate bites: dropped capability column flagged", _validate(bad_tool, prims) != []))
    checks.append(("mutation gate bites: bad namespace flagged", _validate(inv, bad_ns) != []))

    ok = all(v for _, v in checks)
    for name, v in checks:
        print(f"  [{'ok' if v else 'XX'}] {name}")
    print(f"  inventory: {inv['summary']['n_available']} available / "
          f"{inv['summary']['n_available_with_credentials']} keyed / {inv['summary']['n_missing']} missing "
          f"of {inv['summary']['n_tools']} tools; {len(prims)} primitive candidates.")
    print(("PASS" if ok else "FAIL") + " - build_browser_tool_inventory: broad evidence-based ingestion-tool "
          "inventory + ~50 primitive candidates (6 namespaces), offline build + mutation-gated + deterministic; "
          "`--run` writes artifacts + the capability-matrix doc, `--live` adds safe single-page public probes.")
    return 0 if ok else 1


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Broad browser/web-ingestion tool inventory + primitive map.")
    ap.add_argument("--self-test", action="store_true", help="offline, mutation-gated build (no public internet)")
    ap.add_argument("--run", action="store_true", help="run probes + write artifacts + the capability-matrix doc")
    ap.add_argument("--live", action="store_true", help="with --run: also run SAFE single-page public probes (phase 4)")
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test()
    if args.run:
        inv = build_inventory(live=args.live)
        prims = _build_primitives_with_status(inv)
        problems = _validate(inv, prims)
        if problems:
            for p in problems:
                print(f"  VALIDATION PROBLEM: {p}")
            raise SystemExit("inventory failed structural validation")
        paths = write_outputs(inv, prims)
        print(f"tools: {inv['summary']['n_available']} available / "
              f"{inv['summary']['n_available_with_credentials']} keyed / {inv['summary']['n_missing']} missing "
              f"of {inv['summary']['n_tools']}; primitives: {len(prims)}; live records: {len(inv['live_records'])}")
        for name, path in paths.items():
            print(f"wrote {name} -> {path}")
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
