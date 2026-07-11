#!/usr/bin/env python3
"""scripts.primitive_browser_control_harness — a READ-ONLY browser + tab-control research harness that turns web
surfaces into evidence-linked CapturedArtifact rows (candidate-only, serves_truth=false), the capture front-end of
the Primitive Discovery Factory.

Design (owner spec 2026-07-08): the browser is a BACKEND PORT — a zoo of interchangeable drivers behind one
interface (the MULTI-PATH law made literal), so adding a driver is a row, never a rewrite:

    static   — offline, stdlib-only (urllib GET + html.parser). The keyless default; what --self-test runs.
    cdp      — the ZERO-DEP live path: reuse scripts.browser_capture.CDP (one hand-rolled WebSocket to the
               INSTALLED Chrome over --remote-debugging-port). This IS the "thin editable CDP harness / one
               websocket to Chrome" pattern (cf. browser-use/browser-harness, keon/browser-control) — we already
               ship it, so we extend it (tab control + the primitive API + safety), we do not rebuild it.
    nodriver / playwright        — installed, richer tab/context + anti-detection; pluggable rows.
    browser-use / pinchtab / lightpanda — documented SEAMS (external agent/binary drivers) in BACKEND_ZOO.

On top of any backend, the owner's browser_* PRIMITIVES are pure functions over a captured page bundle
(readable-text, links, forms, DOM/screenshot/HAR/accessibility, and the openapi/postman/graphql/downloadable/
side-effect/login-wall/captcha detectors) plus TAB CONTROL (open/list/switch/close) and the safety rail
(robots respect, per-domain throttle, NEVER submit a form / bypass captcha or paywalls, secret redaction,
provenance hash). Raw bodies are NOT stored — only digests, bounded text, and extracted structured units.

    python3 scripts/primitive_browser_control_harness.py --self-test
    python3 scripts/primitive_browser_control_harness.py --list-backends
    python3 scripts/primitive_browser_control_harness.py --crawl https://example.com --backend cdp --live
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
import hashlib  # noqa: E402  (scripts/ may hash; the no-hashlib law is scoped to src/**. ids stay canonical_id.)
import html as _htmlmod  # noqa: E402
import json  # noqa: E402
import re  # noqa: E402
import time  # noqa: E402
import urllib.parse  # noqa: E402
import urllib.request  # noqa: E402
import urllib.robotparser  # noqa: E402
from html.parser import HTMLParser  # noqa: E402
from typing import Any, Callable, Optional  # noqa: E402

try:
    from src.teleon.experiments.ids import canonical_id  # noqa: E402
except Exception as exc:  # noqa: BLE001
    raise SystemExit(f"primitive_browser_control_harness requires canonical_id; import failed: {exc}")

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
ARTIFACT_RECORD_TYPE = "captured_artifact"
ACTION_RECEIPT_RECORD_TYPE = "browser_action_receipt"
STAGED_FILENAME = "captured_artifacts.jsonl"
#: the side-effect calculus ladder (owner spec): read_only auto-allowed … money_movement always needs approval.
#: The index is the authority — `>= index("write")` requires confirmation even when side-effects are permitted.
SIDE_EFFECT_LEVELS: tuple[str, ...] = ("read_only", "read", "write_possible", "write", "regulated", "money_movement")
_DATA_SUBDIR = "data/dev-intel/primitive_browser_control_harness"
_READABLE_TEXT_CAP = 4000          # bounded text stored per artifact (NOT the raw body); handle + digest carry the rest
_DEFAULT_MIN_INTERVAL_S = 2.0      # per-domain politeness floor
_UA = "AIDoneRight-PrimitiveDiscovery/1.0 (+read-only research crawler; respects robots.txt)"

# ── the backend ZOO (MULTI-PATH law: interchangeable drivers behind one port; adding one = a row) ──────────────
BACKEND_ZOO: dict[str, dict[str, Any]] = {
    "static":     {"control": "http_get", "deps": "stdlib",       "tab_control": False, "anti_detect": False,
                   "status": "implemented", "note": "offline urllib+html.parser; keyless default; self-test path"},
    "cdp":        {"control": "cdp_websocket", "deps": "stdlib+chrome", "tab_control": True, "anti_detect": False,
                   "status": "implemented", "note": "reuse browser_capture.CDP; one websocket to installed Chrome"},
    "nodriver":   {"control": "cdp_async", "deps": "nodriver",     "tab_control": True, "anti_detect": True,
                   "status": "available", "note": "pure-python CDP; strong tab/context + anti-detection"},
    "playwright": {"control": "cdp_driver", "deps": "playwright",  "tab_control": True, "anti_detect": True,
                   "status": "available", "note": "cleanest multi-context/tab API; channel=chrome uses system Chrome"},
    "browser_use":{"control": "llm_agent", "deps": "browser-use",  "tab_control": True, "anti_detect": True,
                   "status": "seam", "note": "LLM->browser agent; route via our cloud free lanes (no local LLM)"},
    "pinchtab":   {"control": "http_api", "deps": "pinchtab-binary","tab_control": True, "anti_detect": False,
                   "status": "seam", "note": "12MB Go binary exposing HTTP browser API; drive over localhost"},
    "lightpanda": {"control": "headless", "deps": "lightpanda",    "tab_control": True, "anti_detect": False,
                   "status": "seam", "note": "lightweight AI-headless browser (Zig); replayable PandaScript"},
    "agent_browser":{"control": "cli_cdp", "deps": "agent-browser","tab_control": True, "anti_detect": False,
                   "status": "seam", "note": "CLI over CDP/remote endpoints: snapshot/tab/close — clean adapter"},
    "browser_harness":{"control":"cdp_websocket","deps":"browser-harness","tab_control":True,"anti_detect":False,
                   "status": "seam", "note": "one-websocket self-healing harness; agent-written helpers QUARANTINED"},
    "pinchtab_http":{"control": "http_api", "deps": "pinchtab-binary","tab_control": True, "anti_detect": False,
                   "status": "seam", "note": "Go HTTP control plane; ANY client acts as the logged-in user -> auth gate"},
    "chrome_extension":{"control":"chrome.tabs","deps":"extension","tab_control":True,"anti_detect":False,
                   "status": "seam", "note": "current-tab digestion (TabMind/AI-Browser-Bridge); privacy-first, human-in-loop"},
}

# ── detection lexicons (single-source; extend a row, never a parallel literal) ─────────────────────────────────
_API_SPEC_RE = re.compile(r"(openapi\.json|swagger\.json|swagger-ui|/v3/api-docs|openapi\.ya?ml|asyncapi|"
                          r"postman[_-]?collection|\.postman|/graphql\b|graphiql|\.proto\b|\.avsc\b)", re.I)
_GRAPHQL_RE = re.compile(r"/graphql\b|graphiql|__schema", re.I)
_DOWNLOADABLE_RE = re.compile(r"\.(pdf|csv|tsv|xlsx?|zip|json|xml|parquet|avro|docx?|pptx?)(\?|#|$)", re.I)
_SIDE_EFFECT_WORDS = ("submit", "pay", "buy", "purchase", "checkout", "delete", "remove", "send", "confirm",
                      "place order", "sign up", "subscribe", "transfer", "book", "apply", "post ")
_LOGIN_RE = re.compile(r"type=[\"']?password|sign\s?in|log\s?in|\blogin\b|password", re.I)
_CAPTCHA_RE = re.compile(r"recaptcha|hcaptcha|cf-turnstile|g-recaptcha|\bcaptcha\b|challenge-platform", re.I)
#: secret shapes redacted before ANY artifact is written (never log secrets)
_SECRET_RE = re.compile(r"(sk-[A-Za-z0-9_\-]{12,}|Bearer\s+[A-Za-z0-9._\-]{12,}|AKIA[0-9A-Z]{12,}|"
                        r"(?:password|passwd|api[_-]?key|secret|token)\s*[:=]\s*\S{6,})", re.I)


def _sha256(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8", "ignore")).hexdigest()


def redact_secrets(text: str) -> tuple[str, int]:
    """Redact secret-shaped substrings; return (clean, n_redacted). Applied to every stored field."""
    n = 0

    def _sub(_m: "re.Match[str]") -> str:
        nonlocal n
        n += 1
        return "[REDACTED_SECRET]"

    return _SECRET_RE.sub(_sub, text), n


# ── stdlib HTML extraction (backend-agnostic; works on any backend's returned HTML) ────────────────────────────
class _Extract(HTMLParser):
    """One pass over HTML → readable text, links, forms+fields, and captcha/login markers. Stdlib-only."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.text_parts: list[str] = []
        self.links: list[str] = []
        self.forms: list[dict[str, Any]] = []
        self.buttons: list[str] = []
        self._skip = 0
        self._cur_form: Optional[dict[str, Any]] = None
        self._in_button = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, Optional[str]]]) -> None:
        a = {k: (v or "") for k, v in attrs}
        if tag in ("script", "style", "noscript", "template"):
            self._skip += 1
        elif tag == "a" and a.get("href"):
            self.links.append(a["href"])
        elif tag == "form":
            self._cur_form = {"action": a.get("action", ""), "method": (a.get("method") or "get").lower(),
                              "fields": []}
        elif tag in ("input", "select", "textarea") and self._cur_form is not None:
            self._cur_form["fields"].append({"name": a.get("name", ""), "type": a.get("type", tag)})
        elif tag in ("input", "select", "textarea"):
            # a field outside a <form> still signals interactivity (login walls often are formless)
            self.forms.append({"action": "", "method": "get",
                               "fields": [{"name": a.get("name", ""), "type": a.get("type", tag)}], "loose": True})
        elif tag == "button":
            self._in_button = True

    def handle_endtag(self, tag: str) -> None:
        if tag in ("script", "style", "noscript", "template") and self._skip:
            self._skip -= 1
        elif tag == "form" and self._cur_form is not None:
            self.forms.append(self._cur_form)
            self._cur_form = None
        elif tag == "button":
            self._in_button = False

    def handle_data(self, data: str) -> None:
        if self._skip:
            return
        s = data.strip()
        if s:
            self.text_parts.append(s)
            if self._in_button:
                self.buttons.append(s[:60])


def _extract(html: str) -> _Extract:
    p = _Extract()
    try:
        p.feed(html or "")
    except Exception:  # noqa: BLE001 — malformed HTML never crashes capture
        pass
    return p


# ── the owner's browser_* PRIMITIVES (pure over a page bundle) ─────────────────────────────────────────────────
def browser_extract_readable_text(html: str, *, cap: int = _READABLE_TEXT_CAP) -> str:
    txt = _htmlmod.unescape(" ".join(_extract(html).text_parts))
    return re.sub(r"\s+", " ", txt).strip()[:cap]


def browser_extract_links(html: str, base_url: str) -> list[str]:
    out, seen = [], set()
    for href in _extract(html).links:
        try:
            u = urllib.parse.urljoin(base_url, href.strip())
        except Exception:  # noqa: BLE001
            continue
        if u.startswith(("http://", "https://")) and u not in seen:
            seen.add(u)
            out.append(u)
    return out


def browser_extract_forms(html: str) -> list[dict[str, Any]]:
    return _extract(html).forms


def browser_detect_side_effect_buttons(html: str) -> list[dict[str, Any]]:
    """Buttons/forms that would MUTATE state — the harness enumerates them but NEVER activates them."""
    ex = _extract(html)
    hits: list[dict[str, Any]] = []
    for b in ex.buttons:
        if any(w in b.lower() for w in _SIDE_EFFECT_WORDS):
            hits.append({"kind": "button", "label": b})
    for f in ex.forms:
        if f.get("method") == "post":
            hits.append({"kind": "form", "action": f.get("action", ""), "method": "post"})
    return hits


def browser_detect_openapi_links(links: list[str], html: str) -> list[str]:
    return sorted({u for u in links if _API_SPEC_RE.search(u)} |
                  ({"inline:" + m.group(0) for m in _API_SPEC_RE.finditer(html or "")} if _API_SPEC_RE.search(html or "") else set()))


def browser_detect_graphql_endpoint(links: list[str], html: str) -> bool:
    return bool(any(_GRAPHQL_RE.search(u) for u in links) or _GRAPHQL_RE.search(html or ""))


def browser_detect_downloadable_docs(links: list[str]) -> list[str]:
    return sorted({u for u in links if _DOWNLOADABLE_RE.search(u)})


def browser_detect_login_wall(html: str) -> bool:
    return bool(_LOGIN_RE.search(html or ""))


def browser_detect_captcha(html: str) -> bool:
    return bool(_CAPTCHA_RE.search(html or ""))


def classify_trust_tier(url: str) -> str:
    """T0 official standard/spec · T1 official vendor docs · T2 reputable repo/paper · T3 community · T4 unknown."""
    host = (urllib.parse.urlparse(url).hostname or "").lower()
    if re.search(r"\b(iso\.org|w3\.org|ietf\.org|hl7\.org|x12\.org|iso20022\.org|nist\.gov|ncbi\.nlm\.nih\.gov)$", host):
        return "T0"
    if re.search(r"(docs\.|developer\.|api\.)", host) or host.endswith(".gov"):
        return "T1"
    if re.search(r"(github\.com|gitlab\.com|arxiv\.org|openml\.org|kaggle\.com|huggingface\.co)$", host):
        return "T2"
    if re.search(r"(medium\.com|substack\.com|blogspot\.|wordpress\.|dev\.to|stackoverflow\.com|reddit\.com)$", host):
        return "T3"
    return "T4"


# ── safety rail ────────────────────────────────────────────────────────────────────────────────────────────────
class RateLimiter:
    """Per-domain politeness throttle with an injected clock (deterministic under test)."""

    def __init__(self, min_interval: float = _DEFAULT_MIN_INTERVAL_S, clock: Callable[[], float] = time.monotonic):
        self.min_interval = min_interval
        self._clock = clock
        self._last: dict[str, float] = {}

    def ready(self, domain: str) -> bool:
        now = self._clock()
        last = self._last.get(domain)
        return last is None or (now - last) >= self.min_interval

    def mark(self, domain: str) -> None:
        self._last[domain] = self._clock()


def browser_respect_robots_policy(url: str, *, fetch: Optional[Callable[[str], Optional[str]]] = None,
                                  ua: str = _UA) -> bool:
    """True iff robots.txt permits `ua` to fetch `url`. `fetch(robots_url)->text|None` is injectable for offline
    tests; default fetches live. Absent/unreadable robots ⇒ allowed (standard crawler convention)."""
    parts = urllib.parse.urlparse(url)
    robots_url = f"{parts.scheme}://{parts.netloc}/robots.txt"
    if fetch is None:
        def fetch(u: str) -> Optional[str]:  # noqa: E306
            try:
                req = urllib.request.Request(u, headers={"User-Agent": ua})
                return urllib.request.urlopen(req, timeout=10).read().decode("utf-8", "ignore")
            except Exception:  # noqa: BLE001
                return None
    body = fetch(robots_url)
    if not body:
        return True
    rp = urllib.robotparser.RobotFileParser()
    rp.parse(body.splitlines())
    return rp.can_fetch(ua, url)


# ── backend port ───────────────────────────────────────────────────────────────────────────────────────────────
class BackendPort:
    """Uniform browser interface. A backend implements open()->PageBundle and (optionally) tab ops."""

    name = "base"

    def open(self, url: str) -> dict[str, Any]:
        raise NotImplementedError

    # tab control — default single-tab fallback; live backends (cdp/nodriver/playwright) override
    def list_tabs(self) -> list[dict[str, Any]]:
        return [{"id": "tab0", "active": True}]

    def new_tab(self, url: str = "about:blank") -> str:
        return "tab0"

    def switch_tab(self, tab_id: str) -> bool:
        return tab_id == "tab0"

    def close_tab(self, tab_id: str) -> bool:
        return False  # never close the last tab

    def close(self) -> None:
        pass


class StaticBackend(BackendPort):
    """Offline/stdlib backend: HTTP GET (or an injected fetcher) → HTML. No JS, no screenshot. Self-test path."""

    name = "static"

    def __init__(self, fetch: Optional[Callable[[str], Optional[str]]] = None, ua: str = _UA):
        self._fetch = fetch
        self._ua = ua
        self._tabs: list[str] = ["tab0"]

    def open(self, url: str) -> dict[str, Any]:
        if self._fetch is not None:
            body = self._fetch(url)
        else:
            try:
                req = urllib.request.Request(url, headers={"User-Agent": self._ua})
                body = urllib.request.urlopen(req, timeout=20).read().decode("utf-8", "ignore")
            except Exception as exc:  # noqa: BLE001
                return {"url": url, "html": "", "screenshot": None, "har": None, "a11y": None,
                        "error": f"{type(exc).__name__}: {exc}"}
        return {"url": url, "html": body or "", "screenshot": None, "har": None, "a11y": None}

    def list_tabs(self) -> list[dict[str, Any]]:
        return [{"id": t, "active": i == len(self._tabs) - 1} for i, t in enumerate(self._tabs)]

    def new_tab(self, url: str = "about:blank") -> str:
        tid = f"tab{len(self._tabs)}"
        self._tabs.append(tid)
        return tid

    def switch_tab(self, tab_id: str) -> bool:
        if tab_id in self._tabs:
            self._tabs.remove(tab_id)
            self._tabs.append(tab_id)  # move-to-front-of-active
            return True
        return False

    def close_tab(self, tab_id: str) -> bool:
        if tab_id in self._tabs and len(self._tabs) > 1:
            self._tabs.remove(tab_id)
            return True
        return False


class CdpBackend(BackendPort):
    """Live, ZERO-PIP backend: launch the installed Chrome headless + drive it via scripts.browser_capture.CDP.
    Real DOM/screenshot + TAB control over CDP Target.*. Constructed lazily so --self-test needs no browser."""

    name = "cdp"

    def __init__(self, port: int = 9377, chrome: Optional[str] = None):
        import shutil
        import subprocess
        self._sub = subprocess
        self._port = port
        chrome = chrome or next((shutil.which(c) for c in
                                 ("google-chrome-stable", "google-chrome", "chromium", "chromium-browser")
                                 if shutil.which(c)), None)
        if not chrome:
            raise SystemExit("CdpBackend: no Chrome/Chromium on PATH (needed for --backend cdp)")
        self._proc = subprocess.Popen(
            [chrome, "--headless=new", "--no-sandbox", "--disable-gpu", "--hide-scrollbars",
             f"--remote-debugging-port={port}", "--window-size=1280,1200", "about:blank"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(40):
            try:
                urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version", timeout=2)
                break
            except Exception:  # noqa: BLE001
                time.sleep(0.5)
        from scripts.browser_capture import CDP  # reuse the shipped stdlib CDP transport
        self._cdp = CDP(port)
        self._cdp.call("Page.enable")

    def open(self, url: str) -> dict[str, Any]:
        self._cdp.call("Page.navigate", {"url": url})
        time.sleep(1.5)
        html = self._cdp.js("document.documentElement.outerHTML") or ""
        shot = self._cdp.call("Page.captureScreenshot", {"format": "png"}).get("data")
        return {"url": url, "html": html, "screenshot": bool(shot), "har": None, "a11y": None}

    def list_tabs(self) -> list[dict[str, Any]]:
        ts = self._cdp.call("Target.getTargets").get("targetInfos", [])
        return [{"id": t.get("targetId"), "url": t.get("url"), "active": t.get("attached")}
                for t in ts if t.get("type") == "page"]

    def new_tab(self, url: str = "about:blank") -> str:
        return self._cdp.call("Target.createTarget", {"url": url}).get("targetId", "")

    def switch_tab(self, tab_id: str) -> bool:
        self._cdp.call("Target.activateTarget", {"targetId": tab_id})
        return True

    def close_tab(self, tab_id: str) -> bool:
        return bool(self._cdp.call("Target.closeTarget", {"targetId": tab_id}).get("success", True))

    def close(self) -> None:
        try:
            self._proc.terminate()
        except Exception:  # noqa: BLE001
            pass


def make_backend(name: str, **kw: Any) -> BackendPort:
    if name == "static":
        return StaticBackend(**kw)
    if name == "cdp":
        return CdpBackend(**kw)
    raise SystemExit(f"backend '{name}' is a documented ZOO seam (BACKEND_ZOO), not an in-process driver; "
                     f"implemented backends: static, cdp")


# ── capture → CapturedArtifact (candidate-only, evidence-linked, no raw body) ──────────────────────────────────
def capture_artifact(backend: BackendPort, url: str, *, ts: float, robots_fetch=None,
                     rate: Optional[RateLimiter] = None) -> dict[str, Any]:
    """Read-only capture of ONE url → a CapturedArtifact row. Enforces robots + throttle; stores digest + bounded
    text + extracted structured units, NEVER the raw body, NEVER a secret."""
    domain = (urllib.parse.urlparse(url).hostname or "").lower()
    robots_ok = browser_respect_robots_policy(url, fetch=robots_fetch)
    base = {"record_type": ARTIFACT_RECORD_TYPE, "url": url, "domain": domain,
            "trust_tier": classify_trust_tier(url), "ts": ts, "backend": backend.name, **BOUNDARY}
    if not robots_ok:
        return {**base, "robots_allowed": False, "captured": False, "reason": "robots_disallow"}
    if rate is not None and not rate.ready(domain):
        return {**base, "robots_allowed": True, "captured": False, "reason": "rate_limited_domain"}
    if rate is not None:
        rate.mark(domain)

    page = backend.open(url)
    html = page.get("html") or ""
    if page.get("error") or not html:
        return {**base, "robots_allowed": True, "captured": False, "reason": page.get("error", "empty_body")}

    links = browser_extract_links(html, url)
    forms = browser_extract_forms(html)
    readable, red_txt = redact_secrets(browser_extract_readable_text(html))
    api_specs = browser_detect_openapi_links(links, html)
    side_effects = browser_detect_side_effect_buttons(html)
    source_hash = _sha256(html)
    art_id = canonical_id("cap", url, source_hash)
    extracted = {
        "readable_text": readable, "readable_text_chars": len(readable),
        "n_links": len(links), "links_sample": links[:25],
        "n_forms": len(forms), "forms": forms[:12],
        "api_spec_links": api_specs, "graphql": browser_detect_graphql_endpoint(links, html),
        "downloadable_docs": browser_detect_downloadable_docs(links)[:25],
        "side_effect_controls": side_effects[:20],
        "login_wall": browser_detect_login_wall(html), "captcha": browser_detect_captcha(html),
        "has_screenshot": bool(page.get("screenshot")), "has_har": bool(page.get("har")),
        "has_accessibility_tree": bool(page.get("a11y")),
    }
    # provenance / evidence: how the factory links a downstream primitive candidate back to source spans
    evidence_refs = [{"kind": "source_hash", "value": source_hash},
                     *[{"kind": "api_spec", "value": u} for u in api_specs[:5]],
                     *[{"kind": "form", "value": f.get("action", "")} for f in forms[:5]]]
    return {**base, "artifact_id": art_id, "robots_allowed": True, "captured": True,
            "source_hash": source_hash, "source_bytes": len(html), "secrets_redacted": red_txt,
            "extracted": extracted, "evidence_refs": evidence_refs,
            # capability hints the decomposition stage consumes to propose interface/browser/form primitives
            "primitive_opportunities": _opportunities(extracted)}


def _opportunities(ex: dict[str, Any]) -> list[str]:
    """Map an extracted page to candidate primitive FAMILIES (decomposition seed; not the primitives themselves)."""
    ops: list[str] = []
    if ex["api_spec_links"]:
        ops += ["api_endpoint_primitive", "request_schema_validator", "response_normalizer", "error_mapper",
                "mock_server", "contract_test"]
    if ex["graphql"]:
        ops.append("graphql_introspection_parser")
    if ex["downloadable_docs"]:
        ops += ["document_ingestor", "table_extractor"]
    if ex["n_forms"]:
        ops += ["form_field_mapper", "form_validation_error_parser", "safe_submit_gate"]
    if ex["side_effect_controls"]:
        ops.append("side_effect_gate")
    if ex["login_wall"]:
        ops += ["page_state_classifier", "login_state_detector"]
    if ex["captcha"]:
        ops.append("captcha_present_detector")  # detect only — NEVER solve/bypass
    return sorted(set(ops))


def crawl(seeds: list[str], *, backend: BackendPort, clock: Callable[[], float], max_pages: int = 20,
          robots_fetch=None, min_interval: float = _DEFAULT_MIN_INTERVAL_S,
          follow_links: bool = True) -> list[dict[str, Any]]:
    """Read-only research crawl: robots-check → capture → emit CapturedArtifact + enqueue discovered same-host links
    (bounded). Never submits a form, never activates a side-effect control, never bypasses a login/captcha."""
    rate = RateLimiter(min_interval, clock)
    queue = list(dict.fromkeys(seeds))
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    while queue and len(out) < max_pages:
        url = queue.pop(0)
        if url in seen:
            continue
        seen.add(url)
        art = capture_artifact(backend, url, ts=clock(), robots_fetch=robots_fetch, rate=rate)
        out.append(art)
        if follow_links and art.get("captured") and not art["extracted"]["login_wall"]:
            host = art["domain"]
            for u in art["extracted"]["links_sample"]:
                if (urllib.parse.urlparse(u).hostname or "").lower() == host and u not in seen:
                    queue.append(u)
    return out


def write_artifacts(rows: list[dict[str, Any]], out_path: Optional[Path] = None) -> Path:
    out_path = out_path or (resource(_DATA_SUBDIR) / STAGED_FILENAME)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("a") as fh:
        for r in rows:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    return out_path


# ── driver-neutral TAB-CONTROL command plane (owner spec: one stable API, the driver is just an adapter) ───────
class TabControlAPI:
    """The stable command surface the registry + LLM lanes talk to; a BackendPort (any zoo driver) sits underneath.
    Every command returns an ACTION RECEIPT — "the important thing is not the driver, it is that every action
    produces an evidence record." READ-ONLY by DEFAULT: act commands (click/fill/press/submit) are REFUSED unless
    allow_side_effects=True, and even then `write`+ levels emit requires_confirmation (never auto-executed)."""

    OBSERVE = ("tab_snapshot", "tab_text", "tab_links", "tab_forms", "tab_state_hash")
    ACT = ("tab_click_ref", "tab_fill_ref", "tab_press", "tab_select", "tab_submit")
    VERIFY = ("verify_text", "verify_url", "verify_state")
    SESSION = ("session_start", "session_stop", "tabs_list", "tab_open", "tab_focus", "tab_close")

    def __init__(self, backend: BackendPort, *, clock: Callable[[], float],
                 allow_side_effects: bool = False, session_id: Optional[str] = None):
        self.be = backend
        self._clock = clock
        self.allow_side_effects = allow_side_effects
        self.session_id = session_id or canonical_id("bsession", backend.name, str(clock()))
        self.receipts: list[dict[str, Any]] = []
        self._last: dict[str, Any] = {}

    def commands(self) -> list[str]:
        return list(self.SESSION + self.OBSERVE + self.ACT + self.VERIFY)

    def _receipt(self, action: str, inp: dict, *, before, after, side_effect: str, requires_confirmation: bool,
                 verifier_result: str, executed: bool, artifact_refs=None, error=None) -> dict[str, Any]:
        rec = {"record_type": ACTION_RECEIPT_RECORD_TYPE, "session_id": self.session_id, "backend": self.be.name,
               "command_id": canonical_id("bcmd", self.session_id, action, str(self._clock())),
               "ts": self._clock(), "action": action, "input": inp, "before_state_hash": before,
               "after_state_hash": after, "side_effect_level": side_effect,
               "requires_confirmation": requires_confirmation, "executed": executed,
               "verifier_result": verifier_result, "artifact_refs": artifact_refs or [], "error": error, **BOUNDARY}
        self.receipts.append(rec)
        return rec

    # observe (read-only) — snapshot underpins state_hash + verify
    def tab_snapshot(self, url: str) -> dict[str, Any]:
        page = self.be.open(url)
        html = page.get("html") or ""
        readable, _ = redact_secrets(browser_extract_readable_text(html))
        sh = _sha256((url or "") + "\n" + html)
        self._last = {"url": url, "html": html, "state_hash": sh}
        self._receipt("tab_snapshot", {"url": url}, before=None, after=sh, side_effect="read_only",
                      requires_confirmation=False, verifier_result="captured" if html else "empty",
                      executed=True, error=page.get("error"))
        return {"url": url, "state_hash": sh, "readable_text": readable, "login_wall": browser_detect_login_wall(html),
                "captcha": browser_detect_captcha(html), "forms": browser_extract_forms(html),
                "n_links": len(browser_extract_links(html, url)), "has_screenshot": bool(page.get("screenshot"))}

    # act (GATED — refused read-only by default; write+ needs confirmation even when permitted)
    def _act(self, action: str, inp: dict, side_effect: str) -> dict[str, Any]:
        before = self._last.get("state_hash")
        if not self.allow_side_effects:
            return self._receipt(action, inp, before=before, after=before, side_effect=side_effect,
                                 requires_confirmation=True, verifier_result="refused_read_only",
                                 executed=False, error="side_effects_disabled")
        needs_conf = SIDE_EFFECT_LEVELS.index(side_effect) >= SIDE_EFFECT_LEVELS.index("write")
        return self._receipt(action, inp, before=before, after=before, side_effect=side_effect,
                             requires_confirmation=needs_conf, verifier_result="gated_pending_confirmation"
                             if needs_conf else "gated_executed", executed=not needs_conf)

    def tab_click_ref(self, ref: str, *, side_effect: str = "write_possible") -> dict[str, Any]:
        return self._act("tab_click_ref", {"ref": ref}, side_effect)

    def tab_fill_ref(self, ref: str, value: str, *, side_effect: str = "read") -> dict[str, Any]:
        red, _ = redact_secrets(value)  # a filled value may be a secret — redact before the receipt
        return self._act("tab_fill_ref", {"ref": ref, "value": red[:80]}, side_effect)

    def tab_submit(self, ref: str = "", *, side_effect: str = "write") -> dict[str, Any]:
        return self._act("tab_submit", {"ref": ref}, side_effect)

    # verify (read-only)
    def verify_text(self, needle: str) -> dict[str, Any]:
        ok = needle.lower() in browser_extract_readable_text(self._last.get("html", "")).lower()
        return self._receipt("verify_text", {"needle": needle[:60]}, before=self._last.get("state_hash"),
                             after=self._last.get("state_hash"), side_effect="read_only",
                             requires_confirmation=False, verifier_result="passed" if ok else "failed", executed=True)

    def verify_url(self, expected: str) -> dict[str, Any]:
        cur = self._last.get("url", "")
        ok = cur == expected or (expected in cur)
        return self._receipt("verify_url", {"expected": expected}, before=None, after=None, side_effect="read_only",
                             requires_confirmation=False, verifier_result="passed" if ok else "failed", executed=True)

    # session / tab passthrough (each receipted)
    def tabs_list(self) -> dict[str, Any]:
        tabs = self.be.list_tabs()
        self._receipt("tabs_list", {}, before=None, after=None, side_effect="read_only",
                      requires_confirmation=False, verifier_result="ok", executed=True)
        return {"tabs": tabs}

    def tab_open(self, url: str = "about:blank") -> dict[str, Any]:
        tid = self.be.new_tab(url)
        self._receipt("tab_open", {"url": url}, before=None, after=None, side_effect="read",
                      requires_confirmation=False, verifier_result="ok", executed=True, artifact_refs=[tid])
        return {"tab_id": tid}

    def tab_close(self, tab_id: str) -> dict[str, Any]:
        ok = self.be.close_tab(tab_id)
        self._receipt("tab_close", {"tab_id": tab_id}, before=None, after=None, side_effect="write_possible",
                      requires_confirmation=False, verifier_result="closed" if ok else "protected_last_tab",
                      executed=ok)
        return {"closed": ok}


# ── self-test (offline, deterministic, mutation-gated) ─────────────────────────────────────────────────────────
_FIXTURE_HTML = """<!doctype html><html><head><title>Payer Dev Portal</title></head><body>
<h1>Eligibility API</h1><p>Create an <b>invoice</b> and check coverage. API key: sk-live-SHOULDNOTLEAK123456.</p>
<a href="/docs/openapi.json">OpenAPI spec</a> <a href="/downloads/companion-guide.pdf">Companion Guide (PDF)</a>
<a href="https://other.example.org/blog">external blog</a> <a href="/graphql">GraphQL</a>
<form action="/submit-claim" method="post"><input name="member_id" type="text"><button>Submit Claim</button></form>
<form action="/search" method="get"><input name="q" type="text"><button>Search</button></form>
<input name="password" type="password">
<div class="g-recaptcha"></div>
<script>var token="Bearer abcdef1234567890";</script></body></html>"""


def self_test() -> int:
    checks: list[tuple[str, bool]] = []

    # deterministic clock (no wall-time; the naming/verify laws forbid Date.now-style seeds)
    _t = {"n": 0.0}

    def clock() -> float:
        _t["n"] += 10.0
        return _t["n"]

    fixture_pages = {"https://portal.example.com/": _FIXTURE_HTML}
    fetch = lambda u: fixture_pages.get(u)  # noqa: E731  (offline fetcher; no network)
    robots_fetch = lambda u: "User-agent: *\nAllow: /\n"  # noqa: E731  (permissive robots; no network)
    be = StaticBackend(fetch=fetch)

    art = capture_artifact(be, "https://portal.example.com/", ts=clock(), robots_fetch=robots_fetch)
    ex = art.get("extracted", {})
    checks.append(("capture succeeds + evidence-linked + candidate-only",
                   art.get("captured") and art["artifact_id"].startswith("cap-")
                   and art["serves_truth"] is False and art["candidate"] is True
                   and any(e["kind"] == "source_hash" for e in art["evidence_refs"])))
    checks.append(("readable text extracted, raw body NOT stored",
                   "raw" not in art and ex["readable_text_chars"] > 0 and "html" not in art))
    checks.append(("SECRET redaction: no sk-/Bearer token survives into the row",
                   "sk-live-SHOULDNOTLEAK" not in json.dumps(art) and "Bearer abcdef" not in json.dumps(art)
                   and art["secrets_redacted"] >= 1))
    checks.append(("OpenAPI spec link detected", any("openapi.json" in u for u in ex["api_spec_links"])))
    checks.append(("GraphQL endpoint detected", ex["graphql"] is True))
    checks.append(("downloadable PDF detected", any(u.endswith(".pdf") for u in ex["downloadable_docs"])))
    checks.append(("login wall + captcha detected (detect only)", ex["login_wall"] and ex["captcha"]))
    checks.append(("POST form flagged as side-effect control; harness never submits",
                   any(s["kind"] == "form" for s in ex["side_effect_controls"])))
    checks.append(("primitive opportunities mapped (api + form + side_effect families)",
                   {"api_endpoint_primitive", "safe_submit_gate", "side_effect_gate"} <= set(art["primitive_opportunities"])))
    checks.append(("trust tier classified", art["trust_tier"] in ("T0", "T1", "T2", "T3", "T4")))

    # robots DISALLOW blocks capture
    art_block = capture_artifact(be, "https://portal.example.com/", ts=clock(),
                                 robots_fetch=lambda u: "User-agent: *\nDisallow: /\n")
    checks.append(("robots Disallow blocks capture", art_block["captured"] is False
                   and art_block["reason"] == "robots_disallow"))

    # per-domain rate limit blocks the immediate second hit
    rl = RateLimiter(min_interval=100.0, clock=lambda: 0.0)
    a1 = capture_artifact(be, "https://portal.example.com/", ts=0.0, robots_fetch=robots_fetch, rate=rl)
    a2 = capture_artifact(be, "https://portal.example.com/", ts=0.0, robots_fetch=robots_fetch, rate=rl)
    checks.append(("per-domain throttle: 1st captures, 2nd rate-limited",
                   a1["captured"] and a2["captured"] is False and a2["reason"] == "rate_limited_domain"))

    # TAB control (open/list/switch/close; never closes the last tab)
    t1 = be.new_tab("https://a"); t2 = be.new_tab("https://b")
    tabs = be.list_tabs()
    closed_ok = be.close_tab(t2)
    while be.close_tab("tab0"):
        pass  # try to drain
    checks.append(("tab control: open/list/switch/close, last tab protected",
                   len(tabs) >= 3 and be.switch_tab(t1) and closed_ok and len(be.list_tabs()) >= 1))

    # crawl loop stays same-host + bounded
    rows = crawl(["https://portal.example.com/"], backend=StaticBackend(fetch=fetch), clock=clock,
                 max_pages=5, robots_fetch=robots_fetch)
    checks.append(("crawl emits CapturedArtifact rows (bounded, same-host)",
                   len(rows) >= 1 and all(r["record_type"] == ARTIFACT_RECORD_TYPE for r in rows)))

    # backend zoo integrity (implemented vs seams)
    checks.append(("backend zoo: static+cdp implemented, 10+ driver rows incl. named tools as seams",
                   BACKEND_ZOO["static"]["status"] == "implemented" and BACKEND_ZOO["cdp"]["status"] == "implemented"
                   and BACKEND_ZOO["cdp"]["tab_control"] is True and len(BACKEND_ZOO) >= 10
                   and {"browser_harness", "pinchtab_http", "chrome_extension"} <= set(BACKEND_ZOO)))

    # ── driver-neutral command plane + action receipts ──
    api = TabControlAPI(StaticBackend(fetch=fetch), clock=clock)  # read-only by default
    snap = api.tab_snapshot("https://portal.example.com/")
    checks.append(("command plane: >=16 stable commands over any backend",
                   len(api.commands()) >= 16 and "tab_snapshot" in api.commands() and "verify_text" in api.commands()))
    checks.append(("every command emits an action receipt (evidence record), candidate-only",
                   len(api.receipts) >= 1 and api.receipts[-1]["record_type"] == ACTION_RECEIPT_RECORD_TYPE
                   and api.receipts[-1]["serves_truth"] is False and snap["state_hash"].startswith("sha256:")))
    r_refuse = api.tab_click_ref("button.submit")  # read-only default -> REFUSED
    checks.append(("act command REFUSED in read-only mode (never performs the side-effect)",
                   r_refuse["executed"] is False and r_refuse["requires_confirmation"] is True
                   and r_refuse["verifier_result"] == "refused_read_only"))
    api2 = TabControlAPI(StaticBackend(fetch=fetch), clock=clock, allow_side_effects=True)
    api2.tab_snapshot("https://portal.example.com/")
    r_click = api2.tab_click_ref("button.next", side_effect="write_possible")   # < write -> executes
    r_submit = api2.tab_submit("form.claim", side_effect="write")               # >= write -> needs confirmation
    checks.append(("side-effect calculus: write_possible executes, write+ needs confirmation",
                   r_click["executed"] is True and r_submit["executed"] is False
                   and r_submit["requires_confirmation"] is True))
    r_fill = api2.tab_fill_ref("input.key", "sk-live-SECRETVALUE1234567", side_effect="read")
    checks.append(("filled value redacted in the receipt (never log secrets)",
                   "sk-live-SECRETVALUE" not in json.dumps(r_fill)))
    checks.append(("verify_text passes on captured text (read-only verifier)",
                   api.verify_text("Eligibility")["verifier_result"] == "passed"))

    ok = all(v for _, v in checks)
    for name, v in checks:
        print(f"  [{'ok' if v else 'XX'}] {name}")
    n_prims = len([p for p in globals() if p.startswith("browser_")])
    print(("PASS" if ok else "FAIL") + f" - primitive_browser_control_harness: read-only backend zoo "
          f"({len(BACKEND_ZOO)} drivers, static+cdp implemented), {n_prims} browser_* primitives, tab control, "
          "robots+throttle+secret-redaction safety, evidence-linked CapturedArtifact (serves_truth=false).")
    return 0 if ok else 1


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Read-only browser + tab-control research harness (candidate-only).")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--list-backends", action="store_true")
    ap.add_argument("--crawl", nargs="+", metavar="URL", help="seed URL(s) to crawl (read-only)")
    ap.add_argument("--backend", default="static", choices=["static", "cdp"])
    ap.add_argument("--live", action="store_true", help="permit real network/browser (required for --backend cdp)")
    ap.add_argument("--max-pages", type=int, default=20)
    ap.add_argument("--min-interval", type=float, default=_DEFAULT_MIN_INTERVAL_S)
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test()
    if args.list_backends:
        print(json.dumps(BACKEND_ZOO, indent=2, sort_keys=True))
        return 0
    if args.crawl:
        if args.backend == "cdp" and not args.live:
            raise SystemExit("--backend cdp requires --live (it launches a real browser).")
        be = make_backend(args.backend)
        import datetime as _dt
        clock = lambda: _dt.datetime.now(_dt.timezone.utc).timestamp()  # noqa: E731
        try:
            rows = crawl(args.crawl, backend=be, clock=clock, max_pages=args.max_pages, min_interval=args.min_interval)
        finally:
            be.close()
        path = write_artifacts(rows)
        captured = sum(1 for r in rows if r.get("captured"))
        print(f"captured {captured}/{len(rows)} pages via '{args.backend}' → {path}")
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
