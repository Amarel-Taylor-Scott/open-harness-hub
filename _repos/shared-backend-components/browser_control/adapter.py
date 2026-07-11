#!/usr/bin/env python3
"""browser_control.adapter — the DRIVER-NEUTRAL browser-control adapter interface.

One stable command surface (BrowserAdapter) that many interchangeable drivers back — the MULTI-PATH law
made literal for browsers: adding a driver is a subclass + a CAPABILITIES row, never a rewrite. The
guiding principle (owner spec 2026-07-08) is *"the important thing is not the driver, it is that every
action produces an evidence record"* — so every command returns a browser_action_receipt
(schemas/browser_action_receipt.schema.json), READ-ONLY by default, secrets redacted, candidate-only.

REUSE-FIRST: this module WRAPS the shipped harness — it NEVER re-implements CDP, HTTP, extraction, the
side-effect calculus, or the receipt shape:

    * backends            = scripts.primitive_browser_control_harness.BackendPort subclasses
                            (StaticBackend / CdpBackend / a fake / a Playwright backend)
    * command plane       = scripts.primitive_browser_control_harness.TabControlAPI (act/observe/verify +
                            its receipt minter and side-effect ladder over SIDE_EFFECT_LEVELS)
    * page primitives     = the harness browser_* pure functions (readable text / links / forms / detectors)
    * ids                 = src.teleon.experiments.ids.canonical_id (data-plane naming law)

The ONLY logic added here is a driver-neutral ADAPTER layer: multi-tab page caching, the
`{"supported": False, "reason": ...}` structured result an adapter returns for a capability it cannot back
(it NEVER raises), a stdlib <table> extractor the harness lacks, and receipt normalization to the schema.

    python3 browser_control/self_test.py --self-test      # offline, deterministic, mutation-gated
"""
from __future__ import annotations

import sys
from pathlib import Path

# ── bootstrap: put the code roots on sys.path so scripts.* / src.teleon.* / browser_control.* resolve ──────────────
_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install  # noqa: E402

_install()

import html as _htmlmod  # noqa: E402
import datetime as _dt  # noqa: E402
from html.parser import HTMLParser  # noqa: E402
from typing import Any, Callable, Optional  # noqa: E402

# REUSE-FIRST — every browser behavior below comes from the shipped harness; we wrap, never rebuild.
from scripts.primitive_browser_control_harness import (  # noqa: E402
    ACTION_RECEIPT_RECORD_TYPE,
    BOUNDARY,
    BackendPort,
    SIDE_EFFECT_LEVELS,
    TabControlAPI,
    _sha256,
    browser_detect_downloadable_docs,
    browser_detect_graphql_endpoint,
    browser_detect_login_wall,
    browser_detect_openapi_links,
    browser_extract_forms,
    browser_extract_links,
    browser_extract_readable_text,
    classify_trust_tier,
    redact_secrets,
)

try:
    from src.teleon.experiments.ids import canonical_id  # noqa: E402
except Exception as exc:  # noqa: BLE001
    raise SystemExit(f"browser_control.adapter requires canonical_id; import failed: {exc}")

#: the receipt record_type — single source from the harness (never a parallel literal)
RECEIPT_RECORD_TYPE = ACTION_RECEIPT_RECORD_TYPE          # "browser_action_receipt"
#: the SIDE_EFFECT_LEVELS ladder is re-exported (single source: the harness) so callers import it from one place
WRITE_THRESHOLD = "write"                                # >= this index needs human confirmation even when permitted
_DOM_TEXT_CAP = 4000                                     # bounded DOM text stored per snapshot (digest carries the rest)

#: the 17 capability flags every adapter advertises via capabilities() — the SINGLE SOURCE the capability
#: schema (schemas/browser_control_capability.schema.json) mirrors; self_test.py asserts the two never drift.
CAPABILITY_KEYS: tuple[str, ...] = (
    "session_lifecycle",   # start_session / stop_session
    "tab_control",         # list_tabs / open_tab / focus_tab / close_tab
    "navigate",            # navigate
    "snapshot",            # snapshot_tab
    "extract_text",        # extract_text
    "extract_dom",         # extract_dom
    "extract_links",       # extract_links
    "extract_forms",       # extract_forms
    "extract_tables",      # extract_tables
    "screenshot",          # capture_screenshot
    "network_capture",     # capture_network
    "click",               # click_ref
    "fill",                # fill_ref
    "wait_for_state",      # wait_for_state
    "downloads",           # download_artifacts
    "tab_graph",           # build_tab_graph
    "session_report",      # build_session_report
)


# ── clocks (injected for determinism; the naming/verify laws forbid wall-time seeds under test) ────────────────────
def make_counter_clock(start: float = 0.0, step: float = 10.0) -> Callable[[], float]:
    """A deterministic monotonically-increasing clock (fresh instance = identical sequence → byte-stable ids)."""
    state = {"n": start}

    def _clock() -> float:
        state["n"] += step
        return state["n"]

    return _clock


def _wall_clock() -> Callable[[], float]:
    """A real UTC-seconds clock for live adapters (never used under --self-test)."""
    return lambda: _dt.datetime.now(_dt.timezone.utc).timestamp()


# ── stdlib <table> extractor (the harness _Extract handles text/links/forms, NOT tables — this fills the gap) ──────
class _TableExtractor(HTMLParser):
    """One stdlib pass over HTML → list of tables (rows of cell-text). Backend-agnostic; malformed HTML is safe."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tables: list[dict[str, Any]] = []
        self._table: Optional[dict[str, Any]] = None
        self._row: Optional[list[str]] = None
        self._cell: Optional[list[str]] = None
        self._first_row_is_header = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, Optional[str]]]) -> None:
        if tag == "table":
            self._table = {"rows": [], "header": [], "_saw_th_first_row": False}
        elif tag == "tr" and self._table is not None:
            self._row = []
        elif tag in ("td", "th") and self._row is not None:
            self._cell = []
            if tag == "th" and not self._table["rows"]:
                self._table["_saw_th_first_row"] = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "table" and self._table is not None:
            rows = self._table["rows"]
            header = rows[0] if (rows and self._table["_saw_th_first_row"]) else (rows[0] if rows else [])
            self.tables.append({"rows": rows, "header": header,
                                "n_rows": len(rows), "n_cols": max((len(r) for r in rows), default=0)})
            self._table = None
        elif tag == "tr" and self._row is not None and self._table is not None:
            self._table["rows"].append(self._row)
            self._row = None
        elif tag in ("td", "th") and self._cell is not None and self._row is not None:
            self._row.append(" ".join(self._cell).strip())
            self._cell = None

    def handle_data(self, data: str) -> None:
        if self._cell is not None:
            s = data.strip()
            if s:
                self._cell.append(s)


def extract_tables_from_html(html: str, *, max_tables: int = 20, max_rows: int = 200) -> list[dict[str, Any]]:
    """Extract <table> rows as text (stdlib-only). Returns bounded rows/header per table (no raw HTML)."""
    p = _TableExtractor()
    try:
        p.feed(html or "")
    except Exception:  # noqa: BLE001 — malformed HTML never crashes extraction
        pass
    out: list[dict[str, Any]] = []
    for t in p.tables[:max_tables]:
        rows = t["rows"][:max_rows]
        out.append({"n_rows": len(rows), "n_cols": t["n_cols"],
                    "header": [_htmlmod.unescape(c) for c in t["header"]],
                    "rows": [[_htmlmod.unescape(c) for c in r] for r in rows]})
    return out


# ── receipt normalization (harness receipt → the driver-neutral browser_action_receipt schema shape) ──────────────
def normalize_receipt(rec: dict[str, Any]) -> dict[str, Any]:
    """Map a harness TabControlAPI receipt to schemas/browser_action_receipt.schema.json: guarantees `timestamp`
    (renamed from the harness `ts`), every schema-required key, and the candidate/serves_truth boundary. Never
    invents data — only fills required keys and renames; the harness receipt keys ride along (additionalProperties)."""
    out = dict(rec)
    out.setdefault("record_type", RECEIPT_RECORD_TYPE)
    if out.get("timestamp") is None:
        out["timestamp"] = out.get("ts")
    out.setdefault("command_id", canonical_id("bcmd", str(out.get("action", "")), str(out.get("ts", ""))))
    out.setdefault("backend", "unknown")
    out.setdefault("action", "unknown")
    out.setdefault("input", {})
    out.setdefault("before_state_hash", None)
    out.setdefault("after_state_hash", None)
    out.setdefault("side_effect_level", "read_only")
    out.setdefault("requires_confirmation", False)
    out.setdefault("verifier_result", "ok")
    out.setdefault("artifact_refs", [])
    out.setdefault("error", None)
    out["candidate"] = True
    out["serves_truth"] = False
    return out


# ── the abstract driver-neutral interface ─────────────────────────────────────────────────────────────────────────
class BrowserAdapter:
    """Driver-neutral browser-control interface. A concrete adapter subclasses this and overrides the methods it
    can back; every method it does NOT back returns a structured ``{"supported": False, "reason": ...}`` result and
    NEVER raises. ``capabilities()`` advertises the 17 CAPABILITY_KEYS bools so a router can pick a backend by need.

    The 21 commands: start_session · stop_session · list_tabs · open_tab · focus_tab · close_tab · navigate ·
    snapshot_tab · extract_text · extract_dom · extract_links · extract_forms · extract_tables ·
    capture_screenshot · capture_network · click_ref · fill_ref · wait_for_state · download_artifacts ·
    build_tab_graph · build_session_report.
    """

    name = "base"
    #: whether this backend renders JavaScript (server-HTML backends set False; real browsers True)
    JS_RENDER = False
    #: each concrete adapter overrides — which of the 17 CAPABILITY_KEYS it serves (default: none)
    CAPABILITIES: dict[str, bool] = {k: False for k in CAPABILITY_KEYS}

    def capabilities(self) -> dict[str, Any]:
        """Advertise the 17 capability bools + summary — what a decision-framework router reads to pick a backend."""
        caps = {k: bool(self.CAPABILITIES.get(k, False)) for k in CAPABILITY_KEYS}
        return {"backend": self.name, "js_render": bool(self.JS_RENDER), "capabilities": caps,
                "n_supported": sum(caps.values()), "capability_keys": list(CAPABILITY_KEYS), **BOUNDARY}

    def _unsupported(self, method: str, reason: str = "") -> dict[str, Any]:
        """The structured (non-raising) result an adapter returns for a capability it cannot back."""
        return {"supported": False, "backend": self.name, "method": method,
                "reason": reason or f"the {self.name} adapter does not support {method}", **BOUNDARY}

    # default implementations = unsupported; concrete adapters override the ones they can back
    def start_session(self, **kw: Any) -> dict[str, Any]:
        return self._unsupported("start_session")

    def stop_session(self) -> dict[str, Any]:
        return self._unsupported("stop_session")

    def list_tabs(self) -> dict[str, Any]:
        return self._unsupported("list_tabs")

    def open_tab(self, url: str = "about:blank", **kw: Any) -> dict[str, Any]:
        return self._unsupported("open_tab")

    def focus_tab(self, tab_id: str) -> dict[str, Any]:
        return self._unsupported("focus_tab")

    def close_tab(self, tab_id: str) -> dict[str, Any]:
        return self._unsupported("close_tab")

    def navigate(self, url: str, **kw: Any) -> dict[str, Any]:
        return self._unsupported("navigate")

    def snapshot_tab(self, **kw: Any) -> dict[str, Any]:
        return self._unsupported("snapshot_tab")

    def extract_text(self, **kw: Any) -> dict[str, Any]:
        return self._unsupported("extract_text")

    def extract_dom(self, **kw: Any) -> dict[str, Any]:
        return self._unsupported("extract_dom")

    def extract_links(self, **kw: Any) -> dict[str, Any]:
        return self._unsupported("extract_links")

    def extract_forms(self, **kw: Any) -> dict[str, Any]:
        return self._unsupported("extract_forms")

    def extract_tables(self, **kw: Any) -> dict[str, Any]:
        return self._unsupported("extract_tables")

    def capture_screenshot(self, **kw: Any) -> dict[str, Any]:
        return self._unsupported("capture_screenshot")

    def capture_network(self, **kw: Any) -> dict[str, Any]:
        return self._unsupported("capture_network")

    def click_ref(self, ref: str, **kw: Any) -> dict[str, Any]:
        return self._unsupported("click_ref")

    def fill_ref(self, ref: str, value: str, **kw: Any) -> dict[str, Any]:
        return self._unsupported("fill_ref")

    def wait_for_state(self, **kw: Any) -> dict[str, Any]:
        return self._unsupported("wait_for_state")

    def download_artifacts(self, **kw: Any) -> dict[str, Any]:
        return self._unsupported("download_artifacts")

    def build_tab_graph(self, **kw: Any) -> dict[str, Any]:
        return self._unsupported("build_tab_graph")

    def build_session_report(self, **kw: Any) -> dict[str, Any]:
        return self._unsupported("build_session_report")


# ── the harness-backed concrete base (real adapters subclass this) ────────────────────────────────────────────────
class _BackendAdapter(BrowserAdapter):
    """A BrowserAdapter backed by a harness BackendPort + TabControlAPI. Subclasses supply ``_make_backend()`` and
    set ``CAPABILITIES``; this base delegates every command to the harness (no CDP/HTTP/extraction logic here) and
    adds only the driver-neutral layer: a per-tab page cache, capability gating, and receipt normalization."""

    name = "backend"

    def __init__(self, *, clock: Optional[Callable[[], float]] = None, allow_side_effects: bool = False) -> None:
        self._clock = clock or _wall_clock()
        self._allow = bool(allow_side_effects)
        self._backend: Optional[BackendPort] = None
        self._api: Optional[TabControlAPI] = None
        self._pages: dict[str, dict[str, Any]] = {}     # tab_id -> {url, page, html, state_hash}
        self._tab_urls: dict[str, str] = {}             # tab_id -> current url
        self._visited: list[str] = []                   # ordered unique urls navigated (feeds report/graph)
        self._receipts: list[dict[str, Any]] = []       # normalized receipts (schema shape)
        self._robots_fetch: Optional[Callable[[str], Optional[str]]] = None
        self._started = False

    # subclasses provide the driver
    def _make_backend(self) -> BackendPort:
        raise NotImplementedError

    # -- small helpers --
    def _cap(self, key: str) -> bool:
        return bool(self.CAPABILITIES.get(key, False))

    def _require(self, cap_key: Optional[str], method: str) -> Optional[dict[str, Any]]:
        """Guard: returns a structured unsupported result (or None to proceed). Never raises."""
        if not self._started or self._api is None:
            return self._unsupported(method, "no active session; call start_session first")
        if cap_key and not self._cap(cap_key):
            return self._unsupported(method, f"the {self.name} adapter does not support '{cap_key}'")
        return None

    def _rec(self, receipt: dict[str, Any]) -> dict[str, Any]:
        nr = normalize_receipt(receipt)
        self._receipts.append(nr)
        return nr

    def _emit(self, action: str, inp: dict[str, Any], *, side_effect: str = "read_only",
              verifier_result: str = "ok", executed: bool = True, before: Any = None, after: Any = None,
              requires_confirmation: bool = False, artifact_refs: Optional[list] = None,
              error: Any = None) -> dict[str, Any]:
        """Mint an adapter-level receipt for a command the harness's TabControlAPI does not itself model
        (focus/screenshot/network/tables/dom/graph/report) — reusing the harness's OWN receipt minter so the
        receipt SHAPE has a single source, then normalizing to the schema."""
        rec = self._api._receipt(action, inp, before=before, after=after, side_effect=side_effect,  # noqa: SLF001
                                 requires_confirmation=requires_confirmation, verifier_result=verifier_result,
                                 executed=executed, artifact_refs=artifact_refs, error=error)
        return self._rec(rec)

    def _active_tab(self) -> str:
        try:
            for t in self._backend.list_tabs():
                if t.get("active"):
                    return str(t.get("id"))
        except Exception:  # noqa: BLE001
            pass
        return "tab0"

    def _html(self, tab_id: str) -> str:
        return (self._pages.get(tab_id) or {}).get("html", "")

    def _url(self, tab_id: str) -> str:
        return (self._pages.get(tab_id) or {}).get("url", self._tab_urls.get(tab_id, ""))

    def _sync_api_last(self, tab_id: str) -> None:
        """Feed the current tab's state into TabControlAPI so its act/verify commands see the right before-hash."""
        p = self._pages.get(tab_id) or {}
        self._api._last = {"url": p.get("url", ""), "html": p.get("html", ""),  # noqa: SLF001
                           "state_hash": p.get("state_hash")}

    def _capture(self, url: str, tab_id: str, action: str) -> tuple[dict[str, Any], str, str, dict[str, Any]]:
        """Open ONE url, cache the full page bundle, and emit a read-only receipt whose after-hash matches the
        harness TabControlAPI.tab_snapshot formula exactly (so state hashes are identical across the two layers)."""
        page = self._backend.open(url)
        html = page.get("html") or ""
        state_hash = _sha256((url or "") + "\n" + html)          # identical formula to TabControlAPI.tab_snapshot
        prev = (self._pages.get(tab_id) or {}).get("state_hash")
        self._pages[tab_id] = {"url": url, "page": page, "html": html, "state_hash": state_hash}
        self._tab_urls[tab_id] = url
        if url not in self._visited:
            self._visited.append(url)
        rec = self._emit(action, {"url": url, "tab_id": tab_id}, before=prev, after=state_hash,
                         verifier_result="captured" if html else "empty", executed=True, error=page.get("error"))
        return page, html, state_hash, rec

    # -- session lifecycle --
    def start_session(self, *, allow_side_effects: Optional[bool] = None,
                      session_id: Optional[str] = None) -> dict[str, Any]:
        if allow_side_effects is not None:
            self._allow = bool(allow_side_effects)
        try:
            self._backend = self._make_backend()                 # may launch a real browser (degrade, never raise)
        except BaseException as exc:  # noqa: BLE001 — SystemExit/ImportError/launch failures degrade to unsupported
            return self._unsupported("start_session", f"backend launch failed: {type(exc).__name__}: {exc}")
        self._api = TabControlAPI(self._backend, clock=self._clock, allow_side_effects=self._allow,
                                  session_id=session_id)
        self._started = True
        return {"supported": True, "backend": self.name, "session_id": self._api.session_id,
                "allow_side_effects": self._allow, "js_render": bool(self.JS_RENDER),
                "capabilities": self.capabilities()["capabilities"], **BOUNDARY}

    def stop_session(self) -> dict[str, Any]:
        if not self._started or self._api is None:
            return self._unsupported("stop_session", "no active session")
        try:
            n_tabs = len(self._backend.list_tabs())
        except Exception:  # noqa: BLE001
            n_tabs = 0
        summary = {"supported": True, "backend": self.name, "session_id": self._api.session_id,
                   "n_receipts": len(self._receipts), "n_visited": len(self._visited), "n_tabs": n_tabs,
                   "receipts": list(self._receipts), **BOUNDARY}
        try:
            self._backend.close()
        except Exception:  # noqa: BLE001
            pass
        self._started = False
        return summary

    # -- tab control (delegated to TabControlAPI / BackendPort; each receipted) --
    def list_tabs(self) -> dict[str, Any]:
        g = self._require("tab_control", "list_tabs")
        if g:
            return g
        res = self._api.tabs_list()
        rec = self._rec(self._api.receipts[-1])
        return {"supported": True, "backend": self.name, "tabs": res["tabs"], "receipt": rec, **BOUNDARY}

    def open_tab(self, url: str = "about:blank", **kw: Any) -> dict[str, Any]:
        g = self._require("tab_control", "open_tab")
        if g:
            return g
        res = self._api.tab_open(url)
        rec = self._rec(self._api.receipts[-1])
        tid = res["tab_id"]
        self._tab_urls[tid] = url
        return {"supported": True, "backend": self.name, "tab_id": tid, "receipt": rec, **BOUNDARY}

    def focus_tab(self, tab_id: str) -> dict[str, Any]:
        g = self._require("tab_control", "focus_tab")
        if g:
            return g
        ok = bool(self._backend.switch_tab(tab_id))
        rec = self._emit("focus_tab", {"tab_id": tab_id}, verifier_result="focused" if ok else "not_found",
                         executed=ok)
        return {"supported": True, "backend": self.name, "focused": ok, "tab_id": tab_id, "receipt": rec, **BOUNDARY}

    def close_tab(self, tab_id: str) -> dict[str, Any]:
        g = self._require("tab_control", "close_tab")
        if g:
            return g
        res = self._api.tab_close(tab_id)
        rec = self._rec(self._api.receipts[-1])
        if res["closed"]:
            self._pages.pop(tab_id, None)
            self._tab_urls.pop(tab_id, None)
        return {"supported": True, "backend": self.name, "closed": res["closed"], "tab_id": tab_id,
                "receipt": rec, **BOUNDARY}

    # -- navigate / snapshot (read-only) --
    def navigate(self, url: str, *, tab_id: Optional[str] = None) -> dict[str, Any]:
        g = self._require("navigate", "navigate")
        if g:
            return g
        tid = tab_id or self._active_tab()
        _, html, sh, rec = self._capture(url, tid, "navigate")
        return {"supported": True, "backend": self.name, "tab_id": tid, "url": url, "state_hash": sh,
                "login_wall": browser_detect_login_wall(html), "receipt": rec, **BOUNDARY}

    def snapshot_tab(self, *, tab_id: Optional[str] = None) -> dict[str, Any]:
        g = self._require("snapshot", "snapshot_tab")
        if g:
            return g
        tid = tab_id or self._active_tab()
        url = self._url(tid)
        if not url:
            return self._unsupported("snapshot_tab", "tab has no url yet; navigate first")
        page, html, sh, rec = self._capture(url, tid, "tab_snapshot")
        return {"supported": True, "backend": self.name, "tab_id": tid, "url": url, "state_hash": sh,
                "login_wall": browser_detect_login_wall(html),
                "n_links": len(browser_extract_links(html, url)), "n_forms": len(browser_extract_forms(html)),
                "has_screenshot": bool(page.get("screenshot")), "receipt": rec, **BOUNDARY}

    # -- extraction (read-only, secrets redacted, no raw body) --
    def extract_text(self, *, tab_id: Optional[str] = None) -> dict[str, Any]:
        g = self._require("extract_text", "extract_text")
        if g:
            return g
        tid = tab_id or self._active_tab()
        text, n = redact_secrets(browser_extract_readable_text(self._html(tid)))
        return {"supported": True, "backend": self.name, "text": text, "chars": len(text),
                "secrets_redacted": n, **BOUNDARY}

    def extract_dom(self, *, tab_id: Optional[str] = None) -> dict[str, Any]:
        g = self._require("extract_dom", "extract_dom")
        if g:
            return g
        tid = tab_id or self._active_tab()
        html = self._html(tid)
        bounded, n = redact_secrets(html[:_DOM_TEXT_CAP])
        return {"supported": True, "backend": self.name, "dom_hash": _sha256(html), "dom_bytes": len(html),
                "bounded_dom": bounded, "secrets_redacted": n, "js_rendered": bool(self.JS_RENDER), **BOUNDARY}

    def extract_links(self, *, tab_id: Optional[str] = None) -> dict[str, Any]:
        g = self._require("extract_links", "extract_links")
        if g:
            return g
        tid = tab_id or self._active_tab()
        links = browser_extract_links(self._html(tid), self._url(tid))
        return {"supported": True, "backend": self.name, "links": links, "n_links": len(links), **BOUNDARY}

    def extract_forms(self, *, tab_id: Optional[str] = None) -> dict[str, Any]:
        g = self._require("extract_forms", "extract_forms")
        if g:
            return g
        tid = tab_id or self._active_tab()
        forms = browser_extract_forms(self._html(tid))
        return {"supported": True, "backend": self.name, "forms": forms, "n_forms": len(forms), **BOUNDARY}

    def extract_tables(self, *, tab_id: Optional[str] = None) -> dict[str, Any]:
        g = self._require("extract_tables", "extract_tables")
        if g:
            return g
        tid = tab_id or self._active_tab()
        tables = extract_tables_from_html(self._html(tid))
        return {"supported": True, "backend": self.name, "tables": tables, "n_tables": len(tables), **BOUNDARY}

    # -- screenshot / network (backend-specific; base derives what it can from the cached page) --
    def capture_screenshot(self, *, tab_id: Optional[str] = None) -> dict[str, Any]:
        g = self._require("screenshot", "capture_screenshot")
        if g:
            return g
        tid = tab_id or self._active_tab()
        page = (self._pages.get(tid) or {}).get("page", {})
        shot = page.get("screenshot_hash") or page.get("screenshot")
        if not shot:
            return self._unsupported("capture_screenshot", "no screenshot available from this backend/page")
        digest = shot if isinstance(shot, str) else _sha256(f"screenshot:{tid}:{page.get('url', '')}")
        rec = self._emit("capture_screenshot", {"tab_id": tid}, verifier_result="captured", artifact_refs=[digest])
        return {"supported": True, "backend": self.name, "screenshot_hash": digest, "receipt": rec, **BOUNDARY}

    def capture_network(self, *, tab_id: Optional[str] = None) -> dict[str, Any]:
        g = self._require("network_capture", "capture_network")
        if g:
            return g
        tid = tab_id or self._active_tab()
        html, url = self._html(tid), self._url(tid)
        links = browser_extract_links(html, url)
        artifacts: list[dict[str, Any]] = [
            {"kind": "openapi", "url": u, "source": "page_reference", "trust_tier": classify_trust_tier(u)}
            for u in browser_detect_openapi_links(links, html)]
        if browser_detect_graphql_endpoint(links, html):
            artifacts.append({"kind": "graphql", "url": url, "source": "page_reference",
                              "trust_tier": classify_trust_tier(url)})
        rec = self._emit("capture_network", {"tab_id": tid}, verifier_result="captured",
                         artifact_refs=[a["url"] for a in artifacts])
        return {"supported": True, "backend": self.name, "network_artifacts": artifacts, "receipt": rec, **BOUNDARY}

    # -- act (GATED — read-only-refused by default; write+ needs confirmation; the harness owns the calculus) --
    def click_ref(self, ref: str, *, tab_id: Optional[str] = None,
                  side_effect: str = "write_possible") -> dict[str, Any]:
        g = self._require("click", "click_ref")
        if g:
            return g
        self._sync_api_last(tab_id or self._active_tab())
        r = self._api.tab_click_ref(ref, side_effect=side_effect)
        rec = self._rec(r)
        return {"supported": True, "backend": self.name, "executed": r["executed"],
                "requires_confirmation": r["requires_confirmation"], "receipt": rec, **BOUNDARY}

    def fill_ref(self, ref: str, value: str, *, tab_id: Optional[str] = None,
                 side_effect: str = "read") -> dict[str, Any]:
        g = self._require("fill", "fill_ref")
        if g:
            return g
        self._sync_api_last(tab_id or self._active_tab())
        r = self._api.tab_fill_ref(ref, value, side_effect=side_effect)   # the harness redacts the value in-receipt
        rec = self._rec(r)
        return {"supported": True, "backend": self.name, "executed": r["executed"],
                "requires_confirmation": r["requires_confirmation"], "receipt": rec, **BOUNDARY}

    # -- verify (read-only) --
    def wait_for_state(self, *, contains: Optional[str] = None, url_is: Optional[str] = None,
                       tab_id: Optional[str] = None, timeout_s: float = 0.0) -> dict[str, Any]:
        g = self._require("wait_for_state", "wait_for_state")
        if g:
            return g
        tid = tab_id or self._active_tab()
        self._sync_api_last(tid)
        if contains is not None:
            r = self._rec(self._api.verify_text(contains))
        elif url_is is not None:
            r = self._rec(self._api.verify_url(url_is))
        else:
            sh = (self._pages.get(tid) or {}).get("state_hash")
            r = self._emit("verify_state", {"tab_id": tid}, before=sh, after=sh,
                           verifier_result="passed" if sh else "failed")
        return {"supported": True, "backend": self.name, "passed": r["verifier_result"] == "passed",
                "receipt": r, **BOUNDARY}

    # -- downloads (LISTS downloadable docs; NEVER fetches binaries — read-only research) --
    def download_artifacts(self, *, tab_id: Optional[str] = None) -> dict[str, Any]:
        g = self._require("downloads", "download_artifacts")
        if g:
            return g
        tid = tab_id or self._active_tab()
        links = browser_extract_links(self._html(tid), self._url(tid))
        docs = browser_detect_downloadable_docs(links)
        downloads = [{"url": u, "ext": u.rsplit(".", 1)[-1].split("?")[0].split("#")[0].lower(),
                      "trust_tier": classify_trust_tier(u)} for u in docs]
        rec = self._emit("download_artifacts", {"tab_id": tid}, side_effect="read", verifier_result="listed",
                         artifact_refs=[d["url"] for d in downloads])
        return {"supported": True, "backend": self.name, "downloads": downloads, "n_downloads": len(downloads),
                "receipt": rec, **BOUNDARY}

    # -- report / graph (REUSE the sibling session-report builder when present; degrade to a compact report) --
    def _session_artifacts(self) -> list[dict[str, Any]]:
        """Re-capture each visited url as a harness CapturedArtifact (the row family the report builder consumes)."""
        from scripts.primitive_browser_control_harness import capture_artifact  # local import: optional path
        arts: list[dict[str, Any]] = []
        for url in self._visited:
            arts.append(capture_artifact(self._backend, url, ts=self._clock(), robots_fetch=self._robots_fetch))
        return arts

    def build_session_report(self, *, mode: str = "read_only") -> dict[str, Any]:
        g = self._require("session_report", "build_session_report")
        if g:
            return g
        arts = self._session_artifacts()
        try:
            from scripts.browser_session_report import build_session_report as _bsr   # REUSE the sibling builder
            report = _bsr(arts, clock=self._clock, mode=mode)
            report["builder"] = "scripts.browser_session_report"
        except Exception as exc:  # noqa: BLE001 — degrade to a compact internal report, never raise
            report = self._compact_report(arts, mode, f"{type(exc).__name__}: {exc}")
        report["candidate"] = True
        report["serves_truth"] = False
        return {"supported": True, "backend": self.name, "report": report, "n_artifacts": len(arts), **BOUNDARY}

    def build_tab_graph(self, *, mode: str = "read_only") -> dict[str, Any]:
        g = self._require("tab_graph", "build_tab_graph")
        if g:
            return g
        rep = self.build_session_report(mode=mode)
        if not rep.get("supported"):
            return rep
        graph = rep["report"].get("tab_graph") or {"nodes": [], "edges": [], "openers": {},
                                                    "cross_origin_transitions": [], "popups": [],
                                                    "duplicate_groups": []}
        rec = self._emit("build_tab_graph", {"n_nodes": len(graph.get("nodes", []))}, verifier_result="built")
        return {"supported": True, "backend": self.name, "tab_graph": graph, "receipt": rec, **BOUNDARY}

    def _compact_report(self, arts: list[dict[str, Any]], mode: str, reason: str) -> dict[str, Any]:
        """Self-contained fallback report (distinct record_type — the rich browser_session_report schema is owned
        by another component; we never claim it) when the sibling builder is unavailable."""
        captured = [a for a in arts if a.get("captured")]
        seed = [a.get("source_hash", "") for a in captured] or [a.get("url", "") for a in arts] or ["empty"]
        nodes = [a.get("url", "") for a in arts]
        return {"record_type": "browser_control_session_report", "builder": "browser_control.compact",
                "fallback_reason": reason, "session_id": canonical_id("bcr", mode, *seed), "mode": mode,
                "visited_urls": nodes, "n_tabs": len(arts), "n_captured": len(captured),
                "tab_graph": {"nodes": nodes, "edges": [], "openers": {}, "cross_origin_transitions": [],
                              "popups": [], "duplicate_groups": []},
                "candidate": True, "serves_truth": False}


__all__ = [
    "BrowserAdapter", "CAPABILITY_KEYS", "RECEIPT_RECORD_TYPE", "SIDE_EFFECT_LEVELS", "WRITE_THRESHOLD",
    "normalize_receipt", "extract_tables_from_html", "make_counter_clock",
]
