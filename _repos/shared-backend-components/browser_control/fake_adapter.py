#!/usr/bin/env python3
"""browser_control.fake_adapter — a deterministic, in-memory BrowserAdapter for OFFLINE tests.

FakeAdapter needs no network and no browser: an injected clock (deterministic ids/hashes), a fixed fixture
site, and a fake BackendPort that simulates multiple tabs, a cross-origin popup, forms, a download, an
OpenAPI reference, and a table. It backs ALL 17 capabilities so a test can exercise the whole command
surface — tab open/list/focus/close, stable state hashes, action receipts with before/after hashes, the
side-effect confirmation gate, screenshot/network/download, the tab graph, and the session report — with
byte-identical output across runs. It is the harness's StaticBackend pattern, in memory, with screenshots.
"""
from __future__ import annotations

import sys
from pathlib import Path

_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install  # noqa: E402

_install()

from typing import Any, Callable, Optional  # noqa: E402

from scripts.primitive_browser_control_harness import BackendPort, _sha256  # noqa: E402

from browser_control.adapter import CAPABILITY_KEYS, _BackendAdapter, make_counter_clock  # noqa: E402

# ── the fixture site (deterministic; carries a SECRET-shaped token to prove end-to-end redaction) ─────────────────
FIXTURE_HOME = "https://fixture.example/"
FIXTURE_CHILD = "https://fixture.example/child"
FIXTURE_POPUP = "https://external.example/popup"           # cross-origin -> a popup/cross-origin edge in the graph

_HOME_HTML = """<!doctype html><html><head><title>Payer Dev Portal</title></head><body>
<h1>Eligibility API</h1>
<p>Create an <b>invoice</b> and check coverage. API key: sk-live-SHOULDNOTLEAK1234567 (do not commit).</p>
<a href="/child">Coverage detail</a>
<a href="https://external.example/popup">Open partner portal</a>
<a href="/docs/openapi.json">OpenAPI spec</a>
<a href="/files/companion-guide.pdf">Companion Guide (PDF)</a>
<a href="/graphql">GraphQL</a>
<form action="/submit-claim" method="post"><input name="member_id" type="text"><button>Submit Claim</button></form>
<form action="/search" method="get"><input name="q" type="text"><button>Search</button></form>
<input name="password" type="password">
<table><tr><th>Code</th><th>Description</th></tr>
<tr><td>99213</td><td>Office visit</td></tr><tr><td>99214</td><td>Extended visit</td></tr></table>
<div class="g-recaptcha"></div>
<script>var token="Bearer abcdef1234567890abcdef";</script></body></html>"""

_CHILD_HTML = ("<!doctype html><html><head><title>Coverage detail</title></head><body>"
               "<h1>Coverage detail</h1><p>Member is active.</p><a href=\"/\">Back</a></body></html>")

_POPUP_HTML = ("<!doctype html><html><head><title>Partner portal</title></head><body>"
               "<h1>Partner portal</h1><p>External partner content.</p></body></html>")

FIXTURE_PAGES: dict[str, str] = {FIXTURE_HOME: _HOME_HTML, FIXTURE_CHILD: _CHILD_HTML, FIXTURE_POPUP: _POPUP_HTML}


class _FakeBackend(BackendPort):
    """In-memory BackendPort: fixed pages + deterministic screenshots + a simulated multi-tab model (last tab
    protected). Extra page-bundle keys (screenshot_hash / har) let the adapter surface screenshot + network."""

    name = "fake"

    def __init__(self, pages: dict[str, str]) -> None:
        self._pages = dict(pages)
        self._tabs: list[dict[str, Any]] = [{"id": "tab0", "url": "about:blank", "active": True}]

    def open(self, url: str) -> dict[str, Any]:
        html = self._pages.get(url, "")
        return {"url": url, "html": html, "screenshot": True,
                "screenshot_hash": _sha256(f"fixture-screenshot:{url}"),   # deterministic image digest (no bytes)
                "har": {"entries": []}, "a11y": None,
                "error": None if html else "not_found_in_fixture"}

    def list_tabs(self) -> list[dict[str, Any]]:
        return [dict(t) for t in self._tabs]

    def new_tab(self, url: str = "about:blank") -> str:
        tid = f"tab{len(self._tabs)}"
        for t in self._tabs:
            t["active"] = False
        self._tabs.append({"id": tid, "url": url, "active": True})
        return tid

    def switch_tab(self, tab_id: str) -> bool:
        found = False
        for t in self._tabs:
            active = t["id"] == tab_id
            t["active"] = active
            found = found or active
        return found

    def close_tab(self, tab_id: str) -> bool:
        if len(self._tabs) > 1 and any(t["id"] == tab_id for t in self._tabs):
            self._tabs = [t for t in self._tabs if t["id"] != tab_id]
            if not any(t["active"] for t in self._tabs):
                self._tabs[-1]["active"] = True
            return True
        return False


class FakeAdapter(_BackendAdapter):
    """Deterministic offline BrowserAdapter — backs all 17 capabilities over an in-memory fixture site."""

    name = "fake"
    JS_RENDER = True
    CAPABILITIES = {k: True for k in CAPABILITY_KEYS}

    def __init__(self, *, clock: Optional[Callable[[], float]] = None, allow_side_effects: bool = False,
                 pages: Optional[dict[str, str]] = None) -> None:
        super().__init__(clock=clock or make_counter_clock(), allow_side_effects=allow_side_effects)
        self._fixture_pages = dict(pages) if pages else dict(FIXTURE_PAGES)
        # permissive, offline robots for the report path (no network); the harness policy takes an injected fetch
        self._robots_fetch = lambda u: "User-agent: *\nAllow: /\n"

    def _make_backend(self) -> BackendPort:
        return _FakeBackend(self._fixture_pages)

    def capture_network(self, *, tab_id: Optional[str] = None) -> dict[str, Any]:
        """Extend the base (page-referenced openapi/graphql) with a simulated observed XHR — a fake HAR entry."""
        res = super().capture_network(tab_id=tab_id)
        if res.get("supported"):
            res["network_artifacts"] = list(res["network_artifacts"]) + [
                {"kind": "xhr", "url": FIXTURE_HOME + "api/eligibility", "source": "har_observed",
                 "trust_tier": "T4"}]
        return res


__all__ = ["FakeAdapter", "FIXTURE_PAGES", "FIXTURE_HOME", "FIXTURE_CHILD", "FIXTURE_POPUP"]
