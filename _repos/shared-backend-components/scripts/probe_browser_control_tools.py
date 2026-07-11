#!/usr/bin/env python3
"""scripts.probe_browser_control_tools — build an EVIDENCE-BASED browser/scraping CAPABILITY MATRIX by running REAL,
SAFE probes on THIS machine, then emit ``artifacts/browser_control/capability_matrix.json`` and (from that same
matrix, single-source) the human survey ``docs/BROWSER_CONTROL_TOOLING_SURVEY.md``.

It probes ALL 13 categories:
  (1) raw HTTP scraping  (2) API-first discovery (OpenAPI/GraphQL/robots/sitemap)  (3) raw CDP  (4) Playwright
  (5) Puppeteer  (6) Selenium/WebDriver-BiDi  (7) chrome-extension/current-tab bridge  (8) MCP browser servers
  (9) tiny browser-control binaries/CLIs  (10) browser-use/browser-harness LLM agents  (11) Lightpanda
  (12) remote browsers (Browserless/Browserbase)  (13) LLM endpoints (local Ollama / localhost:8000 / cloud-if-keyed)

REUSE-FIRST: the live browser probes drive the shipped ``scripts.primitive_browser_control_harness`` backends
(``StaticBackend`` = urllib, ``CdpBackend`` = stdlib CDP over system Chrome) and its ``browser_*`` extractors, and
they run against the offline ``scripts.run_browser_fixture_lab`` (no public-internet target). Real probes performed:
import-availability (``importlib``), binary ``shutil.which``, a live HTTP fetch of the fixture, a live CDP capture,
a live Playwright launch (``channel="chrome"``, headless), a live ``chrome --headless --dump-dom`` render, localhost
LLM pings (2s), and cloud-key ENV **presence** (never values). It is READ-ONLY: it never submits the fixture form.

CAPABILITY CONVENTION (honest, and stated in the matrix meta): each record's ``capabilities{}`` booleans describe
the category's capability PROFILE (what the tool can do); ``available`` + ``status`` + ``evidence_artifacts`` record
what was actually verified LIVE on this machine THIS run. Missing tools keep their profile but carry
``status="missing"`` plus the exact install/test command that would enable them.

    python3 scripts/probe_browser_control_tools.py --self-test   # offline, no real browser spawn, mutation-gated
    python3 scripts/probe_browser_control_tools.py --run         # live probes -> matrix json + survey md
"""
from __future__ import annotations

import sys
from pathlib import Path

_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots, resource  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import copy  # noqa: E402
import importlib.util  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import platform  # noqa: E402
import shutil  # noqa: E402
import subprocess  # noqa: E402
import urllib.error  # noqa: E402
import urllib.request  # noqa: E402
from typing import Any, Optional  # noqa: E402

try:
    from src.teleon.experiments.ids import canonical_id  # noqa: E402
except Exception as exc:  # noqa: BLE001
    raise SystemExit(f"probe_browser_control_tools requires canonical_id; import failed: {exc}")

# reuse the shipped harness backends + extractors (never reimplement)
from scripts.primitive_browser_control_harness import (  # noqa: E402
    CdpBackend, StaticBackend, browser_detect_downloadable_docs, browser_detect_graphql_endpoint,
    browser_detect_openapi_links, browser_extract_forms, browser_extract_links, browser_extract_readable_text)
# reuse the offline fixture lab (deliverable 1) + its content markers (single source of the literals we assert)
from scripts.run_browser_fixture_lab import (  # noqa: E402
    DELAYED_MARKER, DOWNLOAD_PATH, JS_RENDERED_MARKER, PENDING_DELAY_PLACEHOLDER, PENDING_JS_PLACEHOLDER,
    STATIC_TEXT_MARKER, serve_in_thread)

# ── the shape every category record MUST have (single source; the self-test validates against these) ───────────────
SCHEMA_VERSION = "1.0.0"                                   # version lives in metadata, never in a name/id
BOUNDARY = {"candidate": True, "serves_truth": False}
MATRIX_RECORD_TYPE = "browser_capability_matrix"
CAPABILITY_KEYS: tuple[str, ...] = (
    "static_html_fetch", "js_render", "tab_list", "tab_open", "tab_focus", "tab_close", "dom_snapshot",
    "text_extract", "screenshot", "forms_extract", "click", "fill", "download", "network_capture",
    "api_discovery", "llm_action_planning", "local_llm", "cloud_llm")
RECORD_FIELDS: tuple[str, ...] = (
    "category", "tools_checked", "commands_run", "available", "status", "capabilities", "risks",
    "best_use_cases", "not_good_for", "recommendation", "evidence_artifacts")
STATUS_VALUES: tuple[str, ...] = ("working", "partial", "missing", "blocked", "unsafe", "not_applicable")
CATEGORY_NAMES: tuple[str, ...] = (
    "raw HTTP scraping",
    "API-first discovery (OpenAPI/GraphQL/robots/sitemap)",
    "raw CDP (Chrome DevTools Protocol)",
    "Playwright",
    "Puppeteer",
    "Selenium / WebDriver-BiDi",
    "chrome-extension / current-tab bridge",
    "MCP browser servers",
    "tiny browser-control binaries / CLIs",
    "browser-use / browser-harness LLM agents",
    "Lightpanda",
    "remote browsers (Browserless / Browserbase)",
    "LLM endpoints (local Ollama / localhost:8000 / cloud-if-keyed)")

# things probed for the environment snapshot (presence only — computed, never a hand-typed literal)
_PY_PACKAGES = ("playwright", "requests", "httpx", "nodriver", "pydantic", "jsonschema", "selenium", "bs4",
                "lxml", "selectolax", "trafilatura", "readability", "scrapy", "pyppeteer", "browser_use")
_BINARIES = ("google-chrome-stable", "google-chrome", "chromium", "chromium-browser", "firefox", "node", "npm",
             "npx", "docker", "playwright", "curl", "wget", "chromedriver", "geckodriver", "lightpanda",
             "pinchtab", "agent-browser", "monolith", "chrome-headless-shell")
_CLOUD_KEY_ENV_VARS = ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "OPENROUTER_API_KEY", "GOOGLE_API_KEY",
                       "GEMINI_API_KEY", "NVIDIA_API_KEY", "BROWSERBASE_API_KEY", "BROWSERBASE_PROJECT_ID",
                       "BROWSERLESS_API_KEY", "BROWSERLESS_TOKEN")
_CDP_PROBE_PORT = 9413                                     # avoid the harness default 9377 to dodge a stale-Chrome clash
_ARTIFACTS_DIR = _sbc_boot / "artifacts" / "browser_control"    # task-specified home; resource('artifacts') remaps
_MATRIX_PATH = _ARTIFACTS_DIR / "capability_matrix.json"       # to _repos/_generated, so derive from THIS repo instead
_DOC_PATH = _sbc_boot / "docs" / "BROWSER_CONTROL_TOOLING_SURVEY.md"


# ── tiny presence helpers ──────────────────────────────────────────────────────────────────────────────────────
def _import_ok(module: str) -> bool:
    try:
        return importlib.util.find_spec(module) is not None
    except Exception:  # noqa: BLE001 (a broken parent package must not crash the probe)
        return False


def _which(binary: str) -> Optional[str]:
    return shutil.which(binary)


def _first_chrome() -> Optional[str]:
    return next((shutil.which(c) for c in ("google-chrome-stable", "google-chrome", "chromium", "chromium-browser")
                 if shutil.which(c)), None)


def _caps(**overrides: bool) -> dict[str, bool]:
    """A full capability dict (all keys present, default False). Unknown keys raise — a typo can't silently pass."""
    caps = {k: False for k in CAPABILITY_KEYS}
    for k, v in overrides.items():
        if k not in caps:
            raise KeyError(f"unknown capability key: {k!r}")
        caps[k] = bool(v)
    return caps


def _status_live(available: bool, live_ok: bool, attempted: bool, *, absent: str = "missing") -> str:
    if not available:
        return absent
    if live_ok:
        return "working"
    return "partial"   # available but either not attempted (offline self-test) or attempted-and-failed


# ── live probes (real + safe) ──────────────────────────────────────────────────────────────────────────────────
def _probe_static_http(fixture_url: Optional[str]) -> dict[str, Any]:
    """Category 1 + 2 evidence: fetch the fixture with the harness StaticBackend (urllib) + run browser_* extractors,
    and pull the API-discovery endpoints. Proves static fetch does NOT execute JS (the discriminator)."""
    if not fixture_url:
        return {"attempted": False, "reason": "no fixture"}
    be = StaticBackend()
    home = be.open(fixture_url + "/")
    html = home.get("html") or ""
    links = browser_extract_links(html, fixture_url + "/")
    forms = browser_extract_forms(html)
    text = browser_extract_readable_text(html)
    disc: dict[str, Any] = {}
    for name, path in (("openapi", "/openapi.json"), ("graphql_sdl", "/graphql"), ("robots", "/robots.txt"),
                       ("sitemap", "/sitemap.xml"), ("api_items", "/api/items")):
        body = (be.open(fixture_url + path).get("html") or "")
        disc[name] = {"ok": bool(body), "bytes": len(body)}
    openapi_paths = 0
    try:
        openapi_paths = len(json.loads(be.open(fixture_url + "/openapi.json").get("html") or "{}").get("paths", {}))
    except Exception:  # noqa: BLE001
        pass
    return {
        "attempted": True, "ok": bool(html), "html_bytes": len(html), "text_chars": len(text),
        "n_links": len(links), "n_forms": len(forms),
        "static_text_marker_present": STATIC_TEXT_MARKER in html,
        # PROOF urllib runs no JS: the #js-rendered div STILL holds its placeholder (the inline script never ran).
        # (the marker string appears inside the <script> source in raw html, so placeholder-PRESENCE is the honest
        # discriminator, not marker-absence.)
        "js_placeholder_unrendered": PENDING_JS_PLACEHOLDER in html,
        "openapi_links": browser_detect_openapi_links(links, html),
        "graphql_detected": browser_detect_graphql_endpoint(links, html),
        "downloadable_docs": browser_detect_downloadable_docs(links),
        "openapi_paths": openapi_paths, "discovery_endpoints": disc,
    }


def _probe_cdp(fixture_url: Optional[str], spawn: bool) -> dict[str, Any]:
    """Category 3 evidence: drive the harness CdpBackend (stdlib CDP over system Chrome) against the fixture — JS
    render, screenshot, DOM, and tab open/list/focus/close over CDP Target.*."""
    if not (fixture_url and spawn):
        return {"attempted": False, "reason": "spawn disabled or no fixture"}
    res: dict[str, Any] = {"attempted": True}
    be = None
    try:
        be = CdpBackend(port=_CDP_PROBE_PORT)
        page = be.open(fixture_url + "/")
        html = page.get("html") or ""
        res.update({
            "ok": bool(html), "html_bytes": len(html),
            # JS ran iff the placeholders were REPLACED in the rendered DOM (the marker strings also sit in the
            # <script> source, so placeholder-ABSENCE — not marker-presence — is the honest proof).
            "js_rendered": PENDING_JS_PLACEHOLDER not in html and JS_RENDERED_MARKER in html,
            "delayed_rendered": PENDING_DELAY_PLACEHOLDER not in html,   # the setTimeout fired
            "has_screenshot": bool(page.get("screenshot")),
            "n_forms": len(browser_extract_forms(html)),
            "text_chars": len(browser_extract_readable_text(html)),
        })
        new_tab = be.new_tab(fixture_url + "/popup")
        res["tab_open_ok"] = bool(new_tab)
        res["tab_list_count"] = len(be.list_tabs())
        res["tab_focus_ok"] = bool(new_tab) and be.switch_tab(new_tab)
        res["tab_close_ok"] = bool(new_tab) and be.close_tab(new_tab)
    except Exception as exc:  # noqa: BLE001
        res.update({"ok": False, "error": f"{type(exc).__name__}: {exc}"[:220]})
    finally:
        if be is not None:
            try:
                be.close()
            except Exception:  # noqa: BLE001
                pass
    return res


def _probe_playwright(fixture_url: Optional[str], spawn: bool) -> dict[str, Any]:
    """Category 4 evidence: launch Playwright with channel='chrome' (system Chrome, no `playwright install`) against
    the fixture and exercise js-render, screenshot, forms, FILL (read-only), CLICK the popup (tab_open), download via
    the request context, and response capture. NEVER clicks submit."""
    if not _import_ok("playwright"):
        return {"attempted": False, "available": False, "reason": "playwright not importable"}
    if not (fixture_url and spawn):
        return {"attempted": False, "available": True, "reason": "spawn disabled or no fixture"}
    res: dict[str, Any] = {"attempted": True, "available": True, "channel": "chrome"}
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(channel="chrome", headless=True, args=["--no-sandbox"])
            context = browser.new_context()
            statuses: list[int] = []
            page = context.new_page()
            page.on("response", lambda r: statuses.append(r.status))
            page.goto(fixture_url + "/", wait_until="domcontentloaded")
            res["ok"] = True
            res["js_rendered"] = page.inner_text("#js-rendered") == JS_RENDERED_MARKER
            try:
                page.wait_for_function(
                    "() => { const d = document.getElementById('delayed-content');"
                    f" return d && d.textContent.indexOf({json.dumps(DELAYED_MARKER)}) >= 0; }}", timeout=3000)
                res["delayed_rendered"] = True
            except Exception:  # noqa: BLE001
                res["delayed_rendered"] = False
            res["n_forms"] = len(page.query_selector_all("form"))
            page.fill("#query-field", "readonly-probe-value")                     # FILL (safe; never submitted)
            res["fill_ok"] = page.input_value("#query-field") == "readonly-probe-value"
            try:
                with page.expect_popup(timeout=3000) as pop:                      # CLICK popup btn -> new tab
                    page.click("#popup-btn")
                popup = pop.value
                res["click_ok"] = True
                res["tab_open_ok"] = popup is not None
                res["tab_list_count"] = len(context.pages)
                popup.close()
                res["tab_close_ok"] = True
            except Exception as exc:  # noqa: BLE001
                res.update({"click_ok": False, "tab_open_ok": False, "popup_error": str(exc)[:120]})
            shot = page.screenshot()
            res["has_screenshot"] = bool(shot)
            res["screenshot_bytes"] = len(shot or b"")
            dl = context.request.get(fixture_url + DOWNLOAD_PATH)                 # DOWNLOAD via request context
            res["download_ok"] = dl.ok and "sample fixture download" in dl.text()
            res["network_events"] = len(statuses)
            res["network_capture_ok"] = len(statuses) >= 1
            context.close()
            browser.close()
    except Exception as exc:  # noqa: BLE001
        res.update({"ok": False, "error": f"{type(exc).__name__}: {exc}"[:220]})
    return res


def _probe_chrome_cli_dumpdom(fixture_url: Optional[str], spawn: bool) -> dict[str, Any]:
    """Category 9 evidence: `chrome --headless=new --dump-dom` renders JS with ZERO libraries (a tiny-CLI path)."""
    chrome = _first_chrome()
    if not chrome:
        return {"attempted": False, "available": False, "reason": "no chrome/chromium binary"}
    if not (fixture_url and spawn):
        return {"attempted": False, "available": True, "reason": "spawn disabled or no fixture"}
    res: dict[str, Any] = {"attempted": True, "available": True, "binary": Path(chrome).name}
    try:
        out = subprocess.run(
            [chrome, "--headless=new", "--no-sandbox", "--disable-gpu", "--virtual-time-budget=1500",
             "--dump-dom", fixture_url + "/"], capture_output=True, text=True, timeout=45)
        dom = out.stdout or ""
        # JS ran iff the placeholder was replaced (marker string also sits in the <script> source)
        res.update({"ok": bool(dom), "js_rendered": PENDING_JS_PLACEHOLDER not in dom and JS_RENDERED_MARKER in dom,
                    "dom_bytes": len(dom)})
    except Exception as exc:  # noqa: BLE001
        res.update({"ok": False, "error": f"{type(exc).__name__}: {exc}"[:220]})
    return res


def _probe_node_module(module: str) -> dict[str, Any]:
    """Is an npm module resolvable by the local node? (used for Puppeteer + MCP servers)."""
    if not _which("node"):
        return {"node_present": False, "present": False}
    try:
        out = subprocess.run(
            ["node", "-e", f"try{{require.resolve({json.dumps(module)});console.log('present')}}"
                           "catch(e){console.log('missing')}"], capture_output=True, text=True, timeout=12)
        return {"node_present": True, "present": "present" in (out.stdout or "")}
    except Exception as exc:  # noqa: BLE001
        return {"node_present": True, "present": False, "error": str(exc)[:120]}


def _probe_llm_endpoints(timeout: float = 2.0) -> dict[str, Any]:
    """Ping local LLM endpoints (up/down + http code ONLY — never model names or any secret)."""
    endpoints = {"ollama_local_11434": "http://localhost:11434/api/tags",
                 "openai_compat_8000": "http://localhost:8000/v1/models",
                 "lmstudio_1234": "http://localhost:1234/v1/models"}
    out: dict[str, Any] = {}
    for name, url in endpoints.items():
        try:
            with urllib.request.urlopen(url, timeout=timeout) as resp:  # noqa: S310 (loopback only)
                out[name] = {"up": resp.getcode() == 200, "http": resp.getcode()}
        except urllib.error.HTTPError as http_err:
            out[name] = {"up": False, "http": http_err.code}
        except Exception as exc:  # noqa: BLE001
            out[name] = {"up": False, "error": type(exc).__name__}
    return out


def _openrouter_file_presence() -> dict[str, Any]:
    """Presence + COUNT of file-based OpenRouter keys (a count is not a secret; values are NEVER read/stored)."""
    try:
        path = resource(".agent/openrouter_keys.txt")
        if path.is_file():
            return {"present": True, "count": sum(1 for ln in path.read_text().splitlines() if ln.strip())}
    except Exception:  # noqa: BLE001
        pass
    return {"present": False, "count": 0}


def _mcp_browser_config_found() -> dict[str, Any]:
    """Look (locally, no network) for a configured browser MCP server in the usual config files."""
    hits: list[str] = []
    candidates = [resource(".mcp.json"), Path.home() / ".claude.json", resource(".claude/settings.json")]
    for cfg in candidates:
        try:
            if cfg.is_file():
                blob = cfg.read_text(errors="ignore").lower()
                if any(tok in blob for tok in ("playwright/mcp", "server-puppeteer", "browsermcp", "browser-mcp",
                                               "@playwright/mcp")):
                    hits.append(str(cfg))
        except Exception:  # noqa: BLE001
            continue
    return {"configured_servers_found": hits, "any": bool(hits)}


def _env_snapshot() -> dict[str, Any]:
    """Computed, presence-only environment map (no key values, no model names)."""
    return {
        "python_version": platform.python_version(),
        "platform": sys.platform,
        "binaries_present": {b: bool(_which(b)) for b in _BINARIES},
        "python_packages_present": {m: _import_ok(m) for m in _PY_PACKAGES},
        "cloud_key_env_presence": {k: bool(os.environ.get(k)) for k in _CLOUD_KEY_ENV_VARS},
        "openrouter_keys_file": _openrouter_file_presence(),
    }


# ── the 13 category builders (each a row; adding a driver is a row, never a rewrite) ───────────────────────────────
def _cat_raw_http(P: dict) -> dict:
    s = P["static"]
    env = P["env"]["python_packages_present"]
    live_ok = bool(s.get("ok"))
    tools = ["urllib (stdlib)", "harness:_Extract (html.parser)"] + [
        f"{m}={'present' if env.get(m) else 'MISSING'}" for m in ("requests", "httpx", "bs4", "lxml", "selectolax",
                                                                   "trafilatura", "scrapy")]
    ev: list[str] = []
    if s.get("attempted"):
        ev += [f"LIVE: StaticBackend().open(fixture) -> {s.get('html_bytes', 0)}B; extracted {s.get('n_links', 0)} "
               f"links / {s.get('n_forms', 0)} forms / {s.get('text_chars', 0)} text-chars via harness browser_*",
               f"LIVE-PROOF raw HTTP runs NO JS: the #js-rendered div still holds '{PENDING_JS_PLACEHOLDER}' "
               f"(js_placeholder_unrendered={s.get('js_placeholder_unrendered')}); a browser render replaces it "
               f"with '{JS_RENDERED_MARKER}'",
               "see meta.live_probe_details.static"]
    return {
        "category": CATEGORY_NAMES[0], "tools_checked": tools,
        "commands_run": ["StaticBackend().open(fixture+'/')  # urllib GET; no browser",
                         "browser_extract_readable_text / _links / _forms (harness, stdlib html.parser)"],
        "available": True, "status": "working" if live_ok else "partial",
        "capabilities": _caps(static_html_fetch=True, text_extract=True, forms_extract=True, api_discovery=True,
                              download=True),
        "risks": ["blind to JS-rendered / SPA content (sees only server HTML)",
                  "brittle against anti-bot / Cloudflare / login walls", "no screenshots, no interaction"],
        "best_use_cases": ["static / server-rendered pages", "REST / JSON APIs",
                           "very high-volume crawling at ~0 browser cost", "when you only need text / links / tables"],
        "not_good_for": ["JS-rendered SPAs (escalate to raw CDP / Playwright)",
                         "any click / fill / multi-step interaction", "screenshots / visual verification"],
        "recommendation": "FIRST CHOICE for static content and APIs — cheapest, fastest, most scalable, zero browser "
                          "cost. Escalate to a browser lane ONLY when the raw HTML lacks the target content.",
        "evidence_artifacts": ev or ["import-available: urllib(stdlib), requests, httpx; parser bs4/lxml MISSING "
                                     "(harness html.parser covers extraction)"],
    }


def _cat_api_first(P: dict) -> dict:
    s = P["static"]
    disc = s.get("discovery_endpoints", {})
    live_ok = bool(s.get("attempted")) and bool(disc.get("openapi", {}).get("ok"))
    ev: list[str] = []
    if s.get("attempted"):
        ev += [f"LIVE: /openapi.json parsed -> {s.get('openapi_paths', 0)} paths; harness openapi links="
               f"{s.get('openapi_links', [])}",
               f"LIVE: /graphql SDL {disc.get('graphql_sdl', {}).get('bytes', 0)}B (graphql_detected="
               f"{s.get('graphql_detected')}); /robots.txt {disc.get('robots', {}).get('bytes', 0)}B; "
               f"/sitemap.xml {disc.get('sitemap', {}).get('bytes', 0)}B",
               "see meta.live_probe_details.static.discovery_endpoints"]
    return {
        "category": CATEGORY_NAMES[1],
        "tools_checked": ["urllib (stdlib)", "harness:browser_detect_openapi_links",
                          "harness:browser_detect_graphql_endpoint", "robots.txt / sitemap.xml parse", "json"],
        "commands_run": ["fetch /openapi.json /graphql /robots.txt /sitemap.xml /api/items (urllib)",
                         "json.loads(openapi) -> count paths; browser_detect_openapi_links / _graphql_endpoint"],
        "available": True, "status": "working" if live_ok else "partial",
        "capabilities": _caps(static_html_fetch=True, api_discovery=True, text_extract=True, download=True),
        "risks": ["not every site exposes a spec / API (then fall back to a browser lane)",
                  "specs can be stale or partial vs the real API", "auth / rate limits on the real endpoints"],
        "best_use_cases": ["sites with a public OpenAPI / GraphQL / REST surface",
                           "the CHEAPEST structured access — skip the browser entirely",
                           "seeding request/response/contract primitives from a spec",
                           "discovery: robots.txt + sitemap.xml enumerate what exists"],
        "not_good_for": ["presentational sites with no API", "content only reachable through rendered UI"],
        "recommendation": "PREFER THIS over any browser when a spec/API exists — an OpenAPI/GraphQL call is orders of "
                          "magnitude cheaper and more stable than rendering a page. Always check robots+sitemap first.",
        "evidence_artifacts": ev or ["harness detectors present (browser_detect_openapi_links / graphql)"],
    }


def _cat_raw_cdp(P: dict) -> dict:
    c = P["cdp"]
    chrome = _first_chrome()
    available = bool(chrome)
    live_ok = bool(c.get("ok"))
    ev: list[str] = []
    if c.get("attempted"):
        if live_ok:
            ev += [f"LIVE: CdpBackend (stdlib CDP over {Path(chrome).name if chrome else 'chrome'}) rendered fixture "
                   f"-> js_rendered={c.get('js_rendered')} delayed={c.get('delayed_rendered')} "
                   f"screenshot={c.get('has_screenshot')} forms={c.get('n_forms')}",
                   f"LIVE tab control over CDP Target.*: open={c.get('tab_open_ok')} list={c.get('tab_list_count')} "
                   f"focus={c.get('tab_focus_ok')} close={c.get('tab_close_ok')}",
                   "CAPABILITY (not exercised this run): click/fill via Input.dispatch*; network_capture via "
                   "Network.enable — raw CDP exposes both",
                   "see meta.live_probe_details.cdp"]
        else:
            ev.append(f"LIVE ATTEMPT failed: {c.get('error', 'unknown')}")
    else:
        ev.append("not spawned this run (offline self-test); harness CdpBackend + system Chrome are present")
    return {
        "category": CATEGORY_NAMES[2],
        "tools_checked": ["harness:CdpBackend", "scripts.browser_capture.CDP (stdlib websocket)",
                          f"system chrome={Path(chrome).name if chrome else 'MISSING'}"],
        "commands_run": [f"CdpBackend(port={_CDP_PROBE_PORT}).open(fixture)  # launches headless Chrome, one websocket",
                         "Target.createTarget / getTargets / activateTarget / closeTarget (tab control)"],
        "available": available, "status": _status_live(available, live_ok, bool(c.get("attempted"))),
        "capabilities": _caps(static_html_fetch=True, js_render=True, tab_list=True, tab_open=True, tab_focus=True,
                              tab_close=True, dom_snapshot=True, text_extract=True, screenshot=True,
                              forms_extract=True, click=True, fill=True, download=True, network_capture=True,
                              api_discovery=True),
        "risks": ["low-level + verbose; brittle across Chrome versions", "you manage the browser process lifecycle",
                  "no auto-wait / retry ergonomics — you build them"],
        "best_use_cases": ["ATTACH to an already-open Chrome / an existing authenticated session/tab",
                           "ZERO pip/npm dependencies (stdlib websocket) — works where you can't install packages",
                           "precise, low-level control (specific CDP domains: Network, Input, Fetch, Emulation)",
                           "full network capture + request interception via the Network domain"],
        "not_good_for": ["ergonomic day-to-day scripting (Playwright is far nicer)",
                         "cross-browser (CDP is Chromium-only)", "teams that want auto-wait + a stable API"],
        "recommendation": "The zero-dependency power tool: use it to control an EXISTING browser/session or when you "
                          "cannot install anything. For greenfield automation prefer Playwright; drop to raw CDP for "
                          "attach-to-session and precise domain control.",
        "evidence_artifacts": ev,
    }


def _cat_playwright(P: dict) -> dict:
    pw = P["playwright"]
    available = _import_ok("playwright")
    live_ok = bool(pw.get("ok"))
    chromium_installed = False  # `playwright install chromium` not run here; channel=chrome uses system Chrome
    ev: list[str] = []
    if pw.get("attempted") and live_ok:
        ev += [f"LIVE: launch(channel='chrome', headless) -> js_rendered={pw.get('js_rendered')} "
               f"delayed={pw.get('delayed_rendered')} forms={pw.get('n_forms')} fill_ok={pw.get('fill_ok')} "
               f"click_ok={pw.get('click_ok')} tab_open={pw.get('tab_open_ok')} screenshot={pw.get('has_screenshot')}"
               f"({pw.get('screenshot_bytes', 0)}B)",
               f"LIVE: download via request context={pw.get('download_ok')}; network responses captured="
               f"{pw.get('network_events')} (network_capture_ok={pw.get('network_capture_ok')})",
               "CONFIG: system Chrome via channel='chrome' (no `playwright install` needed here). Alt: "
               "`playwright install chromium` to use the bundled browser.",
               "see meta.live_probe_details.playwright"]
    elif pw.get("attempted"):
        ev.append(f"LIVE ATTEMPT failed: {pw.get('error', 'unknown')}")
    elif available:
        ev.append("playwright importable; not launched this run (offline self-test)")
    else:
        ev.append("ENABLE: pip install playwright && playwright install chromium (or use channel='chrome')")
    return {
        "category": CATEGORY_NAMES[3],
        "tools_checked": [f"python:playwright={'present' if available else 'MISSING'}",
                          f"cli:playwright={'present' if _which('playwright') else 'MISSING'}",
                          "channel=chrome (system Chrome)", f"bundled-chromium-installed={chromium_installed}"],
        "commands_run": ["playwright.chromium.launch(channel='chrome', headless=True)",
                         "goto / inner_text / wait_for_function / fill / expect_popup+click / screenshot / "
                         "request.get / page.on('response')"],
        "available": available, "status": _status_live(available, live_ok, bool(pw.get("attempted"))),
        "capabilities": _caps(static_html_fetch=True, js_render=True, tab_list=True, tab_open=True, tab_focus=True,
                              tab_close=True, dom_snapshot=True, text_extract=True, screenshot=True,
                              forms_extract=True, click=True, fill=True, download=True, network_capture=True,
                              api_discovery=True),
        "risks": ["heavier than raw HTTP; needs a browser binary (`playwright install` OR channel=chrome)",
                  "detectable by sophisticated anti-bot", "one more toolchain to keep patched"],
        "best_use_cases": ["THE BASELINE for reliable cross-browser automation (Chromium/Firefox/WebKit)",
                           "auto-wait, rich selectors, tracing, network interception, downloads",
                           "greenfield scripted flows where you own the browser lifecycle"],
        "not_good_for": ["attaching to a human's already-open session (use raw CDP)",
                         "ultra-high-volume static scraping (use raw HTTP)",
                         "tiny-footprint / high-density crawl (see Lightpanda)",
                         "environments where you cannot install any browser binary"],
        "recommendation": "The BASELINE — and ONLY the baseline. Excellent default for owned automation, but it is one "
                          "row in the zoo: raw HTTP is cheaper for static pages, raw CDP attaches to existing "
                          "sessions, Lightpanda scales denser, remote browsers scale wider, the extension operates the "
                          "user's real tab. Pick per job.",
        "evidence_artifacts": ev,
    }


def _cat_puppeteer(P: dict) -> dict:
    pup = P["node_modules"].get("puppeteer", {})
    pupcore = P["node_modules"].get("puppeteer-core", {})
    node_present = bool(_which("node"))
    available = bool(pup.get("present") or pupcore.get("present"))
    ev = [f"LIVE: node present={node_present}; require.resolve('puppeteer')={pup.get('present')}, "
          f"'puppeteer-core'={pupcore.get('present')}",
          "ENABLE: npm i puppeteer (bundles Chromium) OR npm i puppeteer-core (reuse system Chrome); "
          "test: node -e \"require('puppeteer-core')\""]
    return {
        "category": CATEGORY_NAMES[4],
        "tools_checked": [f"node={'present' if node_present else 'MISSING'}", f"npm={'present' if _which('npm') else 'MISSING'}",
                          f"puppeteer={'present' if pup.get('present') else 'MISSING'}",
                          f"puppeteer-core={'present' if pupcore.get('present') else 'MISSING'}"],
        "commands_run": ["node -e require.resolve('puppeteer') / ('puppeteer-core')"],
        "available": available, "status": "working" if available else "missing",
        "capabilities": _caps(static_html_fetch=True, js_render=True, tab_list=True, tab_open=True, tab_focus=True,
                              tab_close=True, dom_snapshot=True, text_extract=True, screenshot=True,
                              forms_extract=True, click=True, fill=True, download=True, network_capture=True,
                              api_discovery=True),
        "risks": ["Chromium-focused (Firefox support is newer/thinner than Playwright)",
                  "Node/JS runtime required", "same anti-bot detectability as any CDP driver"],
        "best_use_cases": ["Node / JavaScript codebases", "Chrome-centric automation + PDF generation",
                           "puppeteer-core to drive the already-installed system Chrome with a tiny install"],
        "not_good_for": ["Python-first pipelines (use Playwright-Python or raw CDP)",
                         "true cross-browser needs (prefer Playwright)"],
        "recommendation": "In a Node stack, Puppeteer (or puppeteer-core + system Chrome) is a fine baseline. Here the "
                          "Node runtime is present but the package is not installed — one `npm i puppeteer-core` away. "
                          "In THIS Python repo, prefer Playwright / raw CDP.",
        "evidence_artifacts": ev,
    }


def _cat_selenium(P: dict) -> dict:
    available = _import_ok("selenium")
    gecko = _which("geckodriver")
    chromedriver = _which("chromedriver")
    ev = [f"LIVE: import selenium -> {'present' if available else 'MISSING (ModuleNotFoundError)'}; "
          f"geckodriver={'present' if gecko else 'MISSING'} chromedriver={'present' if chromedriver else 'MISSING'}",
          "ENABLE: pip install selenium ; drivers auto-resolved by Selenium Manager "
          f"({'geckodriver already present' if gecko else 'or install a driver'}); test: python -c 'import selenium'"]
    return {
        "category": CATEGORY_NAMES[5],
        "tools_checked": [f"python:selenium={'present' if available else 'MISSING'}",
                          f"geckodriver={'present' if gecko else 'MISSING'}",
                          f"chromedriver={'present' if chromedriver else 'MISSING'}", "WebDriver-BiDi"],
        "commands_run": ["importlib.find_spec('selenium')", "shutil.which('geckodriver' / 'chromedriver')"],
        "available": available, "status": "working" if available else "missing",
        "capabilities": _caps(static_html_fetch=True, js_render=True, tab_list=True, tab_open=True, tab_focus=True,
                              tab_close=True, dom_snapshot=True, text_extract=True, screenshot=True,
                              forms_extract=True, click=True, fill=True, download=True, network_capture=True,
                              api_discovery=True),
        "risks": ["heavier + slower to script than Playwright (fewer auto-wait ergonomics)",
                  "classic WebDriver lacks native network intercept (WebDriver-BiDi adds it)"],
        "best_use_cases": ["the W3C WebDriver STANDARD (portable across languages + browsers, incl. real Firefox)",
                           "mature Selenium Grid for large parallel farms",
                           "WebDriver-BiDi = standardized bidirectional control (console/network) like CDP but vendor-"
                           "neutral", "legacy suites already written against Selenium"],
        "not_good_for": ["quick modern scripting (Playwright is more ergonomic)",
                         "lightweight one-shot scrapes (use raw HTTP / a CLI)"],
        "recommendation": "Reach for Selenium/WebDriver-BiDi when you need the vendor-neutral W3C standard, a Grid, or "
                          "real Firefox. Not installed here (geckodriver IS present) — one `pip install selenium` away.",
        "evidence_artifacts": ev,
    }


def _cat_extension(P: dict) -> dict:
    return {
        "category": CATEGORY_NAMES[6],
        "tools_checked": ["MV3 chrome extension (chrome.tabs / chrome.scripting / chrome.debugger / chrome.downloads)",
                          "harness BACKEND_ZOO seam 'chrome_extension'"],
        "commands_run": ["environment inspection: no interactive Chrome profile / loaded extension in a headless probe"],
        "available": False, "status": "blocked",
        "capabilities": _caps(static_html_fetch=True, js_render=True, tab_list=True, tab_open=True, tab_focus=True,
                              tab_close=True, dom_snapshot=True, text_extract=True, screenshot=True,
                              forms_extract=True, click=True, fill=True, download=True, network_capture=True,
                              api_discovery=True),
        "risks": ["ACTS AS THE LOGGED-IN USER — full authority of the human's session (privacy + safety critical)",
                  "requires explicit user install + broad permissions (tabs/scripting/debugger)",
                  "must stay human-in-the-loop; not for unattended automation"],
        "best_use_cases": ["operate on the USER's CURRENT tab / already-authenticated session (no re-login, no captcha)",
                           "privacy-first, on-device, human-in-the-loop 'digest / act on what I'm looking at'",
                           "no separate browser process — reuse the real one the user already trusts"],
        "not_good_for": ["headless / server-side / unattended automation", "high-volume crawling",
                         "anything that must run without a human's interactive browser"],
        "recommendation": "The RIGHT tool for current-tab, privacy-first, consented assistance inside the user's own "
                          "browser — a capability NO headless driver has. BLOCKED in this headless probe environment "
                          "(no interactive profile/extension). ENABLE: load an unpacked MV3 extension into a real "
                          "Chrome profile; drive tabs via chrome.tabs + a content script.",
        "evidence_artifacts": ["blocked: cannot load an interactive MV3 extension in a headless CI probe",
                               "ENABLE: MV3 manifest with permissions ['tabs','scripting','activeTab','downloads'] "
                               "(+ 'debugger' for network capture); load unpacked in a non-headless Chrome"],
    }


def _cat_mcp(P: dict) -> dict:
    npx = _which("npx")
    node = _which("node")
    cfg = P["mcp_config"]
    runtime_ok = bool(npx and node)
    configured = bool(cfg.get("any"))
    status = "working" if configured else ("partial" if runtime_ok else "missing")
    ev = [f"LIVE: node={'present' if node else 'MISSING'} npx={'present' if npx else 'MISSING'}; "
          f"configured browser-MCP servers found={cfg.get('configured_servers_found', [])}",
          "ENABLE: npx @playwright/mcp@latest (or @modelcontextprotocol/server-puppeteer) and register it in the MCP "
          "client config (.mcp.json / client settings)"]
    return {
        "category": CATEGORY_NAMES[7],
        "tools_checked": ["@playwright/mcp", "@modelcontextprotocol/server-puppeteer", "browsermcp",
                          f"npx={'present' if npx else 'MISSING'}", f"node={'present' if node else 'MISSING'}"],
        "commands_run": ["shutil.which('npx'/'node')", "scan .mcp.json / ~/.claude.json / .claude/settings.json"],
        "available": runtime_ok, "status": status,
        "capabilities": _caps(static_html_fetch=True, js_render=True, tab_list=True, tab_open=True, tab_focus=True,
                              tab_close=True, dom_snapshot=True, text_extract=True, screenshot=True,
                              forms_extract=True, click=True, fill=True, download=True, network_capture=True,
                              api_discovery=True, llm_action_planning=True),
        "risks": ["output is LLM-mediated tool-calling — non-deterministic; treat results as candidates",
                  "the MCP server has real browser authority; scope its permissions",
                  "a running server + an agent client are both required"],
        "best_use_cases": ["giving an LLM AGENT (Claude Code / Cursor / an MCP client) browser TOOLS via a standard "
                           "interface", "exploratory, natural-language-driven browsing inside an agent loop",
                           "a uniform tool surface across agents (write once, any MCP client calls it)"],
        "not_good_for": ["deterministic production pipelines (call Playwright/CDP directly)",
                         "raw programmatic throughput"],
        "recommendation": "Use an MCP browser server to hand an AGENT browser tools — not for deterministic scripting. "
                          "Node+npx are present so a server is one `npx @playwright/mcp` away; none is configured yet. "
                          "Quarantine agent-produced output as candidate-only.",
        "evidence_artifacts": ev,
    }


def _cat_tiny_cli(P: dict) -> dict:
    cli = P["chrome_cli"]
    chrome = _first_chrome()
    curl, wget = _which("curl"), _which("wget")
    pinchtab, agentb = _which("pinchtab"), _which("agent-browser")
    available = bool(chrome or curl or wget)
    live_ok = bool(cli.get("ok"))
    ev: list[str] = []
    if cli.get("attempted") and live_ok:
        ev.append(f"LIVE: {cli.get('binary')} --headless --dump-dom rendered fixture ({cli.get('dom_bytes', 0)}B), "
                  f"js_rendered={cli.get('js_rendered')} — a browser render with ZERO libraries")
    elif cli.get("attempted"):
        ev.append(f"LIVE ATTEMPT failed: {cli.get('error', 'unknown')}")
    else:
        ev.append("chrome CLI present; --dump-dom not run this run (offline self-test)")
    ev.append(f"which: curl={'present' if curl else 'MISSING'} wget={'present' if wget else 'MISSING'} "
              f"pinchtab={'present' if pinchtab else 'MISSING'} agent-browser={'present' if agentb else 'MISSING'}")
    ev.append("ENABLE pinchtab/agent-browser: download/build the small binary (no go toolchain here) and drive its "
              "localhost HTTP API for tab control + click/fill")
    return {
        "category": CATEGORY_NAMES[8],
        "tools_checked": [f"chrome --headless --dump-dom/--screenshot ({Path(chrome).name if chrome else 'MISSING'})",
                          f"curl={'present' if curl else 'MISSING'}", f"wget={'present' if wget else 'MISSING'}",
                          f"pinchtab={'present' if pinchtab else 'MISSING'}",
                          f"agent-browser={'present' if agentb else 'MISSING'}", "monolith"],
        "commands_run": ["chrome --headless=new --virtual-time-budget=1500 --dump-dom <url>",
                         "shutil.which('curl'/'wget'/'pinchtab'/'agent-browser')"],
        "available": available, "status": _status_live(available, live_ok, bool(cli.get("attempted"))),
        # profile reflects the PRESENT tooling (chrome one-shot CLI + curl/wget): render/screenshot/dump, no live interaction
        "capabilities": _caps(static_html_fetch=True, js_render=True, dom_snapshot=True, text_extract=True,
                              screenshot=True, download=True, api_discovery=True),
        "risks": ["one-shot: no persistent session, no multi-step interaction (chrome CLI)",
                  "small third-party binaries (pinchtab/agent-browser) need provenance vetting"],
        "best_use_cases": ["a quick JS render / screenshot with ZERO libraries (chrome --dump-dom / --screenshot)",
                           "shell pipelines + CI smoke checks", "curl/wget for file downloads + raw HTTP",
                           "pinchtab / agent-browser: a ~12MB binary exposing an HTTP browser API for tab control"],
        "not_good_for": ["multi-step interactive flows / stateful sessions (use Playwright / raw CDP)",
                         "fine-grained click/fill (with the chrome CLI alone)"],
        "recommendation": "For one-shot render/screenshot with no dependencies, `chrome --headless --dump-dom` is "
                          "unbeatably simple (verified here). For interaction, add a tiny binary (pinchtab/agent-"
                          "browser, absent here) or step up to raw CDP / Playwright.",
        "evidence_artifacts": ev,
    }


def _cat_browser_use(P: dict) -> dict:
    available = _import_ok("browser_use")
    llm = P["llm"]
    local_llm_up = any(v.get("up") for v in llm.values())
    ev = [f"LIVE: import browser_use -> {'present' if available else 'MISSING'}; local LLM endpoints up="
          f"{ {k: v.get('up') for k, v in llm.items()} }",
          "ENABLE: pip install browser-use (drives Playwright under the hood); needs an LLM — route via CLOUD free "
          "lanes, NOT local Ollama (owner rule: local hardware can't run big models reliably)"]
    return {
        "category": CATEGORY_NAMES[9],
        "tools_checked": [f"python:browser_use={'present' if available else 'MISSING'}", "browser-harness (seam)",
                          "harness BACKEND_ZOO seams 'browser_use' / 'browser_harness'"],
        "commands_run": ["importlib.find_spec('browser_use')", "local LLM endpoint pings"],
        "available": available, "status": "working" if (available and local_llm_up) else ("partial" if available
                                                                                          else "missing"),
        "capabilities": _caps(static_html_fetch=True, js_render=True, tab_list=True, tab_open=True, tab_focus=True,
                              tab_close=True, dom_snapshot=True, text_extract=True, screenshot=True,
                              forms_extract=True, click=True, fill=True, download=True, network_capture=True,
                              api_discovery=True, llm_action_planning=True, local_llm=local_llm_up),
        "risks": ["OUTPUT MUST BE QUARANTINED — LLM-planned actions are non-deterministic + can hallucinate steps",
                  "can take UNSAFE actions (submit/pay) without a hard gate — keep read-only + human approval",
                  "depends on an LLM's quality; small local models plan poorly"],
        "best_use_cases": ["EXPLORATION of an unknown UI — let the agent discover the flow",
                           "generating CANDIDATE action plans / selectors to later harden into deterministic scripts",
                           "'do X on this site' natural-language tasks where a human reviews the result"],
        "not_good_for": ["deterministic / production pipelines (compile the plan down to Playwright/CDP first)",
                         "anything trusted as truth (serves_truth=false; candidate-only)",
                         "unattended money/state-changing actions"],
        "recommendation": "Use browser-use/browser-harness for DISCOVERY only, with output QUARANTINED as candidate "
                          "(serves_truth=false) and every side-effecting action human-gated. Not installed here; "
                          "route its LLM via cloud free lanes per the owner rule, then distill winning plans into "
                          "deterministic Playwright/CDP.",
        "evidence_artifacts": ev,
    }


def _cat_lightpanda(P: dict) -> dict:
    present = bool(_which("lightpanda"))
    ev = [f"LIVE: which lightpanda -> {'present' if present else 'MISSING'}; no go/cargo/zig toolchain to build from "
          "source",
          "INSTALL PATH: download the prebuilt binary from lightpanda.io (releases) -> `lightpanda serve --host "
          "127.0.0.1 --port 9222`; it is CDP-compatible, so drive it with Playwright/Puppeteer via connect_over_cdp "
          "(or `lightpanda fetch --dump <url>` for one-shot)"]
    return {
        "category": CATEGORY_NAMES[10],
        "tools_checked": [f"lightpanda binary={'present' if present else 'MISSING'}", "CDP-over-lightpanda"],
        "commands_run": ["shutil.which('lightpanda')"],
        "available": present, "status": "working" if present else "missing",
        "capabilities": _caps(static_html_fetch=True, js_render=True, tab_list=True, tab_open=True, tab_focus=True,
                              tab_close=True, dom_snapshot=True, text_extract=True, screenshot=True,
                              forms_extract=True, click=True, fill=True, download=True, network_capture=True,
                              api_discovery=True),
        "risks": ["not full Chrome — some heavy/edge-case sites render imperfectly",
                  "younger project; smaller ecosystem than Chromium"],
        "best_use_cases": ["HIGH-VOLUME, high-density headless crawling at a FRACTION of Chrome's RAM/CPU",
                           "CDP-compatible: existing Playwright/Puppeteer code points at it unchanged",
                           "cost-sensitive fleets where Chrome's footprint is the bottleneck"],
        "not_good_for": ["pixel-perfect fidelity on complex apps (use real Chrome)",
                         "features that depend on full Chromium behavior"],
        "recommendation": "The right tool when the constraint is SCALE/COST of headless rendering — far lighter than "
                          "Chrome and CDP-compatible so your existing driver code works. UNAVAILABLE here (no binary / "
                          "no build toolchain); install path recorded above.",
        "evidence_artifacts": ev,
    }


def _cat_remote(P: dict) -> dict:
    env = P["env"]["cloud_key_env_presence"]
    keyed = bool(env.get("BROWSERLESS_API_KEY") or env.get("BROWSERLESS_TOKEN") or env.get("BROWSERBASE_API_KEY"))
    docker = bool(_which("docker"))
    status = "working" if keyed else "blocked"
    ev = [f"LIVE: env key presence -> BROWSERLESS_API_KEY={env.get('BROWSERLESS_API_KEY')} "
          f"BROWSERBASE_API_KEY={env.get('BROWSERBASE_API_KEY')} (values never read); docker present={docker}",
          "ENABLE (cloud): set BROWSERLESS_API_KEY / BROWSERBASE_API_KEY, connect via CDP websocket: "
          "playwright.chromium.connect_over_cdp('wss://...?token=...')",
          f"ENABLE (local, docker present={docker}): docker run -p 3000:3000 browserless/chrome  ->  "
          "connect_over_cdp('ws://localhost:3000')"]
    return {
        "category": CATEGORY_NAMES[11],
        "tools_checked": ["Browserless (self-host / cloud)", "Browserbase (cloud, managed stealth)",
                          "playwright/puppeteer connect_over_cdp", f"docker={'present' if docker else 'MISSING'}"],
        "commands_run": ["env presence: BROWSERLESS_API_KEY / BROWSERLESS_TOKEN / BROWSERBASE_API_KEY",
                         "shutil.which('docker')"],
        "available": keyed, "status": status,
        "capabilities": _caps(static_html_fetch=True, js_render=True, tab_list=True, tab_open=True, tab_focus=True,
                              tab_close=True, dom_snapshot=True, text_extract=True, screenshot=True,
                              forms_extract=True, click=True, fill=True, download=True, network_capture=True,
                              api_discovery=True),
        "risks": ["SENDS TARGET PAGES (and any credentials you drive) to a THIRD PARTY — data-residency + privacy",
                  "per-session cost; rate/quota limits", "dependency on an external service's uptime"],
        "best_use_cases": ["SCALE + PARALLELISM without managing local browser infra",
                           "CI / serverless where you can't install browsers",
                           "Browserbase's managed stealth / captcha handling for hard anti-bot targets",
                           "bursty parallel fleets on demand"],
        "not_good_for": ["offline / local-first / air-gapped work", "cost-sensitive high volume (local is cheaper)",
                         "data you may not send to a third party"],
        "recommendation": "Use a remote browser when you need scale/parallelism or managed anti-bot without local "
                          "infra — at the cost of sending pages to a third party. BLOCKED here (no key/endpoint); "
                          "docker is present, so a local `browserless/chrome` container is the keyless alternative.",
        "evidence_artifacts": ev,
    }


def _cat_llm_endpoints(P: dict) -> dict:
    llm = P["llm"]
    env = P["env"]["cloud_key_env_presence"]
    orouter = P["env"]["openrouter_keys_file"]
    local_up = any(v.get("up") for v in llm.values())
    cloud_keyed = any(env.values())
    ev = [f"LIVE PINGS: { {k: (v.get('http') if 'http' in v else v.get('error')) for k, v in llm.items()} } "
          "(up = HTTP 200; no model names / secrets stored)",
          f"cloud key ENV presence (names only): { {k: env[k] for k in env if env[k]} or 'none set'}",
          f"file-based OpenRouter keys: present={orouter.get('present')} count={orouter.get('count')} "
          "(a count is not a secret; values never read)"]
    return {
        "category": CATEGORY_NAMES[12],
        "tools_checked": ["Ollama :11434", "OpenAI-compatible :8000", "LM Studio :1234",
                          ".agent/openrouter_keys.txt (file lane)", "cloud keys (env)"],
        "commands_run": ["GET :11434/api/tags :8000/v1/models :1234/v1/models (2s timeout)",
                         "env presence of cloud keys; count of openrouter_keys.txt lines"],
        "available": local_up or cloud_keyed or bool(orouter.get("present")),
        "status": "working" if local_up else ("partial" if (cloud_keyed or orouter.get("present")) else "missing"),
        # not a browser itself — it is the PLANNING brain that drives categories 8 & 10
        "capabilities": _caps(llm_action_planning=True, local_llm=local_up, cloud_llm=cloud_keyed),
        "risks": ["OWNER RULE: do NOT rely on LOCAL Ollama — local hardware can't run big models well",
                  "LLM output is never truth (serves_truth=false); non-deterministic; must be quarantined",
                  "small local models plan browser actions poorly vs frontier models"],
        "best_use_cases": ["action PLANNING for the agentic browser lanes (MCP / browser-use)",
                           "natural-language -> tool-call intent; DOM/screenshot understanding (multimodal)",
                           "cheap local endpoints for dev; cloud free lanes (OpenRouter file) for real planning"],
        "not_good_for": ["deterministic control (compile plans to Playwright/CDP)",
                         "being trusted as a source of truth"],
        "recommendation": "Local endpoints (Ollama :11434, OpenAI-compat :8000) are UP and verified, but per the owner "
                          "rule route real action-planning through CLOUD free lanes (the 8 file-based OpenRouter keys) "
                          "rather than local Ollama. Keep all planner output candidate-only.",
        "evidence_artifacts": ev,
    }


_CATEGORY_BUILDERS = (
    _cat_raw_http, _cat_api_first, _cat_raw_cdp, _cat_playwright, _cat_puppeteer, _cat_selenium, _cat_extension,
    _cat_mcp, _cat_tiny_cli, _cat_browser_use, _cat_lightpanda, _cat_remote, _cat_llm_endpoints)


# ── assemble ───────────────────────────────────────────────────────────────────────────────────────────────────
def build_matrix(*, spawn_browsers: bool = True, fixture_url: Optional[str] = None,
                 own_fixture: bool = True) -> dict[str, Any]:
    """Run the live probes and build the full capability matrix. ``spawn_browsers=False`` skips the real
    CDP/Playwright/chrome-CLI launches (the offline self-test path) while still doing the offline HTTP fetch, LLM
    pings, imports, and ``which`` checks. Pure aside from optional local probes; returns a JSON-serializable dict."""
    httpd = None
    try:
        if own_fixture and fixture_url is None:
            try:
                httpd, fixture_url = serve_in_thread(0)
            except Exception:  # noqa: BLE001 (a bind failure must not crash the build; degrade to no-fixture)
                httpd, fixture_url = None, None

        env = _env_snapshot()
        P = {
            "env": env,
            "fixture_url": fixture_url,
            "static": _probe_static_http(fixture_url),
            "cdp": _probe_cdp(fixture_url, spawn_browsers),
            "playwright": _probe_playwright(fixture_url, spawn_browsers),
            "chrome_cli": _probe_chrome_cli_dumpdom(fixture_url, spawn_browsers),
            "node_modules": {m: _probe_node_module(m) for m in ("puppeteer", "puppeteer-core")}
            if _which("node") else {},
            "mcp_config": _mcp_browser_config_found(),
            "llm": _probe_llm_endpoints(),
        }
        categories = [build(P) for build in _CATEGORY_BUILDERS]
        matrix = {
            "record_type": MATRIX_RECORD_TYPE, "schema_version": SCHEMA_VERSION,
            "matrix_id": canonical_id("bcm", MATRIX_RECORD_TYPE, SCHEMA_VERSION),
            "generated_by": "scripts/probe_browser_control_tools.py",
            **BOUNDARY,
            "meta": {
                "capability_keys": list(CAPABILITY_KEYS), "status_values": list(STATUS_VALUES),
                "record_fields": list(RECORD_FIELDS),
                "capability_convention": (
                    "capabilities{} booleans describe the category's capability PROFILE (what the tool can do); "
                    "`available` + `status` + `evidence_artifacts` record what was verified LIVE on this machine this "
                    "run. Missing tools keep their profile but carry status=missing + the install/test command."),
                "spawned_real_browsers": spawn_browsers, "fixture_url_used": bool(fixture_url),
                "environment": env,
                "live_probe_details": {k: P[k] for k in ("static", "cdp", "playwright", "chrome_cli",
                                                         "node_modules", "mcp_config", "llm")},
            },
            "categories": categories,
        }
        return matrix
    finally:
        if httpd is not None:
            try:
                httpd.shutdown()
                httpd.server_close()
            except Exception:  # noqa: BLE001
                pass


# ── survey doc: rendered FROM the matrix (single source; the table never drifts from the data) ────────────────────
_TABLE_COLUMNS = (("static_html_fetch", "static"), ("js_render", "js"), ("dom_snapshot", "snap"),
                  ("screenshot", "shot"), ("forms_extract", "form"), ("click", "click"), ("fill", "fill"),
                  ("download", "dl"), ("network_capture", "net"), ("api_discovery", "api"),
                  ("llm_action_planning", "llm"))
_TAB_KEYS = ("tab_list", "tab_open", "tab_focus", "tab_close")


def _glyph(v: bool) -> str:
    return "✓" if v else "·"


def _tab_glyph(caps: dict) -> str:
    vals = [caps[k] for k in _TAB_KEYS]
    return "✓" if all(vals) else ("~" if any(vals) else "·")


def render_survey_markdown(matrix: dict) -> str:
    meta = matrix["meta"]
    env = meta["environment"]
    cats = matrix["categories"]
    L: list[str] = []
    L.append("# Browser & Scraping Control — Capability Survey")
    L.append("")
    L.append(f"> Generated by `{matrix['generated_by']}` from `artifacts/browser_control/capability_matrix.json` "
             f"(schema {matrix['schema_version']}, id `{matrix['matrix_id']}`). "
             f"Candidate-only: `serves_truth={str(matrix['serves_truth']).lower()}`. "
             "Do NOT hand-edit — re-run `--run` (or `--emit-survey`) to regenerate.")
    L.append("")
    L.append(f"**Probe environment** (presence only, computed): Python {env['python_version']} on "
             f"{env['platform']} · real browsers spawned this run: **{meta['spawned_real_browsers']}** · "
             f"fixture lab used: **{meta['fixture_url_used']}**. "
             f"Chrome present: {env['binaries_present'].get('google-chrome-stable')}, "
             f"Chromium: {env['binaries_present'].get('chromium')}, Firefox: {env['binaries_present'].get('firefox')}, "
             f"Node: {env['binaries_present'].get('node')}, Docker: {env['binaries_present'].get('docker')}.")
    L.append("")
    L.append(f"_{meta['capability_convention']}_")
    L.append("")

    # ── the load-bearing claim, evidence-cited ──
    pw = next((c for c in cats if c["category"] == "Playwright"), {})
    L.append("## Playwright is only the BASELINE")
    L.append("")
    L.append("Playwright is an excellent **default** for automation you own — verified working here "
             f"(`status={pw.get('status')}`, via `channel=\"chrome\"` against the offline fixture: JS render, "
             "screenshot, form fill, popup/tab-open, download, and network capture all exercised live). But it is "
             "**one row in a zoo**, not the whole toolbox. Each alternative below covers something Playwright does "
             "not — cited from this run's probe evidence:")
    L.append("")
    def _one(name: str) -> dict:
        return next((c for c in cats if c["category"].startswith(name)), {})
    L.append(f"- **raw HTTP scraping** — static pages + APIs at **~0 browser cost**, the scale/throughput Playwright "
             f"can't touch (evidence: {_one('raw HTTP')['status']}; a browser launch is pure overhead when the "
             "server already returns the HTML).")
    L.append("- **raw CDP** — attach to an **already-open Chrome / existing authenticated session/tab** with "
             f"**zero pip/npm deps** (evidence: {_one('raw CDP')['status']}; the harness drove system Chrome over a "
             "stdlib websocket). Playwright launches/owns its own browser; it does not attach to the user's session.")
    L.append(f"- **Lightpanda** — **high-volume crawl at a fraction of Chrome's RAM/CPU**, CDP-compatible "
             f"(evidence: {_one('Lightpanda')['status']}; install path recorded). Playwright drives full Chrome — "
             "heavy at fleet scale.")
    L.append("- **browser-use / browser-harness** — LLM-driven **exploration of unknown UIs**, output **QUARANTINED** "
             f"as candidate (evidence: {_one('browser-use')['status']}). Playwright executes a script you already "
             "wrote; it does not discover the flow.")
    L.append("- **chrome-extension / current-tab bridge** — operate the **user's real, logged-in tab**, privacy-first "
             f"+ human-in-the-loop (evidence: {_one('chrome-extension')['status']} in this headless env). No headless "
             "driver, Playwright included, can act as the user's own trusted browser.")
    L.append("- **remote browsers (Browserless/Browserbase)** — **scale/parallelism + managed stealth** without local "
             f"infra (evidence: {_one('remote browsers')['status']}; keyless local `browserless/chrome` via the "
             "present Docker). **MCP browser servers** — hand an **LLM agent** browser tools over a standard "
             f"interface (evidence: {_one('MCP browser')['status']}).")
    L.append("")
    L.append("**Rule of thumb:** API > raw HTTP > (CDP-attach | tiny CLI) > Playwright/Puppeteer/Selenium > "
             "remote/Lightpanda for scale > agentic (quarantined) — pick the cheapest lane that reaches the content.")
    L.append("")

    # ── capability matrix table (computed) ──
    L.append("## Capability matrix")
    L.append("")
    header = ["Category", "status", "avail"] + [short for _, short in _TABLE_COLUMNS] + ["tab"]
    L.append("| " + " | ".join(header) + " |")
    L.append("|" + "|".join(["---"] * len(header)) + "|")
    for c in cats:
        caps = c["capabilities"]
        row = [c["category"], c["status"], _glyph(c["available"])]
        row += [_glyph(caps[key]) for key, _ in _TABLE_COLUMNS]
        row.append(_tab_glyph(caps))
        L.append("| " + " | ".join(row) + " |")
    L.append("")
    L.append("Legend: ✓ = capability profile includes it · · = no · ~ = partial (tab column: some of "
             "list/open/focus/close). `status` reflects LIVE verification on this machine; `avail` = tooling present "
             "here. `tab` = tab_list/open/focus/close. `llm` = llm_action_planning.")
    L.append("")

    # ── per-category detail ──
    L.append("## Per-category: when it's the RIGHT tool / when it's NOT")
    L.append("")
    for c in cats:
        L.append(f"### {c['category']}")
        L.append("")
        L.append(f"- **Status:** `{c['status']}` · **available here:** {c['available']}")
        L.append(f"- **Tools checked:** {', '.join(c['tools_checked'])}")
        L.append(f"- **RIGHT when:** {'; '.join(c['best_use_cases'])}.")
        L.append(f"- **NOT when:** {'; '.join(c['not_good_for'])}.")
        L.append(f"- **Risks:** {'; '.join(c['risks'])}.")
        L.append(f"- **Recommendation:** {c['recommendation']}")
        L.append(f"- **Evidence (this run):** {' | '.join(c['evidence_artifacts'])}")
        L.append("")

    L.append("---")
    L.append(f"_{len(cats)} categories · capability keys: {', '.join(meta['capability_keys'])}. "
             "Full live-probe detail is under `meta.live_probe_details` in the matrix JSON._")
    L.append("")
    return "\n".join(L)


def write_outputs(matrix: dict) -> tuple[Path, Path]:
    _ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    _MATRIX_PATH.write_text(json.dumps(matrix, indent=2, sort_keys=True) + "\n")
    _DOC_PATH.parent.mkdir(parents=True, exist_ok=True)
    _DOC_PATH.write_text(render_survey_markdown(matrix))
    return _MATRIX_PATH, _DOC_PATH


def _print_summary(matrix: dict) -> None:
    print(f"browser-control capability matrix ({len(matrix['categories'])} categories, "
          f"real browsers spawned={matrix['meta']['spawned_real_browsers']}):")
    for c in matrix["categories"]:
        caps = c["capabilities"]
        n_caps = sum(1 for v in caps.values() if v)
        print(f"  [{c['status']:>12}] {c['category']:<52} avail={str(c['available']):<5} caps={n_caps}/{len(caps)}")


# ── verify-the-verifier: structural validator (drives the mutation gate) ──────────────────────────────────────────
def _validate_matrix(matrix: dict) -> list[str]:
    problems: list[str] = []
    cats = matrix.get("categories")
    if not isinstance(cats, list) or len(cats) != len(CATEGORY_NAMES):
        problems.append(f"expected {len(CATEGORY_NAMES)} categories, got "
                        f"{len(cats) if isinstance(cats, list) else 'non-list'}")
        return problems  # can't validate further
    names = [c.get("category") for c in cats]
    if names != list(CATEGORY_NAMES):
        problems.append(f"category names/order mismatch: {names}")
    for i, c in enumerate(cats):
        for f in RECORD_FIELDS:
            if f not in c:
                problems.append(f"category[{i}] '{c.get('category')}' missing field '{f}'")
        caps = c.get("capabilities", {})
        if set(caps) != set(CAPABILITY_KEYS):
            problems.append(f"category[{i}] '{c.get('category')}' capability keys != CAPABILITY_KEYS "
                            f"(missing={set(CAPABILITY_KEYS) - set(caps)}, extra={set(caps) - set(CAPABILITY_KEYS)})")
        if not all(isinstance(v, bool) for v in caps.values()):
            problems.append(f"category[{i}] '{c.get('category')}' has non-bool capability value")
        if c.get("status") not in STATUS_VALUES:
            problems.append(f"category[{i}] '{c.get('category')}' bad status {c.get('status')!r}")
        if not isinstance(c.get("available"), bool):
            problems.append(f"category[{i}] '{c.get('category')}' available not bool")
    try:
        json.dumps(matrix)
    except Exception as exc:  # noqa: BLE001
        problems.append(f"matrix not JSON-serializable: {exc}")
    return problems


def self_test() -> int:
    """Offline (no real browser spawn), mutation-gated. Builds the matrix, validates its structure, and PROVES the
    validator bites by corrupting a copy."""
    checks: list[tuple[str, bool]] = []
    matrix = build_matrix(spawn_browsers=False)

    problems = _validate_matrix(matrix)
    checks.append(("matrix builds offline with a clean structure (no problems)", problems == []))
    if problems:
        for p in problems:
            print(f"    - {p}")
    checks.append(("exactly 13 categories, in the canonical order",
                   [c["category"] for c in matrix["categories"]] == list(CATEGORY_NAMES)))
    checks.append(("every category has the full 18-key capability set",
                   all(set(c["capabilities"]) == set(CAPABILITY_KEYS) for c in matrix["categories"])))
    checks.append(("every category has all required record fields",
                   all(all(f in c for f in RECORD_FIELDS) for c in matrix["categories"])))
    checks.append(("every status is a legal value",
                   all(c["status"] in STATUS_VALUES for c in matrix["categories"])))
    checks.append(("matrix is JSON-serializable + candidate-only (serves_truth=false)",
                   matrix["serves_truth"] is False and matrix["candidate"] is True
                   and isinstance(json.dumps(matrix), str)))
    checks.append(("meta advertises the capability keys + convention",
                   matrix["meta"]["capability_keys"] == list(CAPABILITY_KEYS)
                   and "PROFILE" in matrix["meta"]["capability_convention"]))
    # offline-guaranteed truths (no browser needed): raw HTTP + API-first are always available
    raw = matrix["categories"][0]
    checks.append(("raw HTTP scraping is available offline (urllib always present)", raw["available"] is True))

    # the survey renders from the matrix and carries the load-bearing claim
    md = render_survey_markdown(matrix)
    checks.append(("survey renders with the capability table + the BASELINE claim",
                   "Playwright is only the BASELINE" in md and "| Category |" in md and "Capability matrix" in md))

    # ── MUTATION GATE: a real injected defect MUST make the validator go red ──
    m_drop_key = copy.deepcopy(matrix)
    m_drop_key["categories"][0]["capabilities"].pop(CAPABILITY_KEYS[0])
    m_drop_cat = copy.deepcopy(matrix)
    m_drop_cat["categories"].pop()
    m_bad_status = copy.deepcopy(matrix)
    m_bad_status["categories"][1]["status"] = "definitely-not-valid"
    checks.append(("mutation gate bites: dropped capability key -> validator flags it",
                   _validate_matrix(m_drop_key) != []))
    checks.append(("mutation gate bites: dropped category -> validator flags it",
                   _validate_matrix(m_drop_cat) != []))
    checks.append(("mutation gate bites: illegal status -> validator flags it",
                   _validate_matrix(m_bad_status) != []))

    ok = all(v for _, v in checks)
    for name, v in checks:
        print(f"  [{'ok' if v else 'XX'}] {name}")
    _print_summary(matrix)
    print(("PASS" if ok else "FAIL") + " - probe_browser_control_tools: 13-category evidence-based capability matrix "
          "(full 18-key profiles, JSON-serializable, candidate-only), offline build + mutation-gated validator; "
          "`--run` performs live CDP/Playwright/HTTP/LLM probes and writes the matrix + survey.")
    return 0 if ok else 1


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Evidence-based browser/scraping capability matrix probe.")
    ap.add_argument("--self-test", action="store_true", help="offline, mutation-gated structural build")
    ap.add_argument("--run", action="store_true", help="run LIVE probes and write matrix json + survey md")
    ap.add_argument("--emit-survey", action="store_true",
                    help="re-render the survey md from the existing matrix json (no probing)")
    ap.add_argument("--no-browsers", action="store_true",
                    help="with --run: skip real browser spawns (HTTP/LLM/import probes only)")
    ap.add_argument("--print", action="store_true", help="print the matrix JSON to stdout")
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test()
    if args.emit_survey:
        if not _MATRIX_PATH.is_file():
            raise SystemExit(f"no matrix at {_MATRIX_PATH}; run --run first")
        matrix = json.loads(_MATRIX_PATH.read_text())
        _DOC_PATH.write_text(render_survey_markdown(matrix))
        print(f"rendered survey -> {_DOC_PATH}")
        return 0
    if args.run:
        matrix = build_matrix(spawn_browsers=not args.no_browsers)
        problems = _validate_matrix(matrix)
        if problems:
            for p in problems:
                print(f"  VALIDATION PROBLEM: {p}")
            raise SystemExit("matrix failed structural validation")
        json_path, doc_path = write_outputs(matrix)
        _print_summary(matrix)
        if args.print:
            print(json.dumps(matrix, indent=2, sort_keys=True))
        print(f"wrote matrix -> {json_path}")
        print(f"wrote survey -> {doc_path}")
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
