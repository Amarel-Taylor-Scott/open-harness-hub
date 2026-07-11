#!/usr/bin/env python3
"""browser_control.adapters.http_scrape_adapter — the keyless, offline-capable HTTP adapter.

Wraps the harness StaticBackend (urllib GET + html.parser; the same driver --self-test runs). Real and cheap:
it extracts readable text / links / forms / TABLES (via the shared stdlib table extractor) and lists
downloadable docs from the SERVER-DELIVERED HTML. It does NOT execute JavaScript, so JS-rendered DOM,
screenshots, and a live network panel are UNSUPPORTED — those return a structured
``{"supported": False, "reason": ...}`` result (route them to the cdp/playwright adapter). Highest-volume,
lowest-risk backend for static docs, OpenAPI/spec pages, and sitemap-style crawls.
"""
from __future__ import annotations

import sys
from pathlib import Path

_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[2])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install  # noqa: E402

_install()

from typing import Any, Callable, Optional  # noqa: E402

from scripts.primitive_browser_control_harness import BackendPort, StaticBackend  # noqa: E402

from browser_control.adapter import CAPABILITY_KEYS, _BackendAdapter, _wall_clock  # noqa: E402


class HttpScrapeAdapter(_BackendAdapter):
    """Offline/stdlib HTTP adapter — wraps the harness StaticBackend. No JS render, no screenshot, no live network."""

    name = "http_scrape"
    JS_RENDER = False
    CAPABILITIES = {**{k: False for k in CAPABILITY_KEYS}, **{
        "session_lifecycle": True, "tab_control": True, "navigate": True, "snapshot": True,
        "extract_text": True, "extract_dom": True, "extract_links": True, "extract_forms": True,
        "extract_tables": True, "wait_for_state": True, "downloads": True, "tab_graph": True,
        "session_report": True,
        # NOT supported — no JS execution / no interactive DOM (route to cdp/playwright):
        "screenshot": False, "network_capture": False, "click": False, "fill": False,
    }}

    def __init__(self, *, fetch: Optional[Callable[[str], Optional[str]]] = None, ua: Optional[str] = None,
                 robots_fetch: Optional[Callable[[str], Optional[str]]] = None,
                 clock: Optional[Callable[[], float]] = None, allow_side_effects: bool = False) -> None:
        super().__init__(clock=clock or _wall_clock(), allow_side_effects=allow_side_effects)
        self._fetch = fetch                 # injectable fetcher -> fully offline/deterministic tests
        self._ua = ua
        self._robots_fetch = robots_fetch   # injectable robots fetcher for the report path (else live)

    def _make_backend(self) -> BackendPort:
        kw: dict[str, Any] = {}
        if self._fetch is not None:
            kw["fetch"] = self._fetch
        if self._ua:
            kw["ua"] = self._ua
        return StaticBackend(**kw)


__all__ = ["HttpScrapeAdapter"]
