#!/usr/bin/env python3
"""browser_control.adapters.playwright_adapter — the regression-grade adapter (Playwright, channel=chrome).

Real when Playwright is importable AND a Chrome/Chromium can launch: navigation, screenshot, and multi-tab
control via Playwright's sync API over the system Chrome (channel="chrome", falling back to the bundled
Chromium). Playwright's clean multi-context/tab model and auto-waiting make it the best backend for
deterministic REGRESSION scripts.

Everything is LAZY and degrades: the Playwright import and browser launch happen only in start_session(); if
either fails (no Playwright, no launchable browser, sandbox block), start_session returns a structured
``{"supported": False, "reason": ...}`` result and NEVER raises. This adapter is never required by the
offline test suite.
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

import base64  # noqa: E402
from typing import Any, Callable, Optional  # noqa: E402

from scripts.primitive_browser_control_harness import BackendPort, _sha256  # noqa: E402

from browser_control.adapter import CAPABILITY_KEYS, _BackendAdapter, _wall_clock  # noqa: E402


class _PlaywrightBackend(BackendPort):
    """A harness BackendPort backed by Playwright. Constructed lazily (imports + launches on __init__); a launch
    failure raises, and PlaywrightAdapter.start_session() catches it and degrades to an unsupported result."""

    name = "playwright"

    def __init__(self, channel: str = "chrome", headless: bool = True) -> None:
        from playwright.sync_api import sync_playwright  # may ImportError -> caught by start_session
        self._pw = sync_playwright().start()
        try:
            self._browser = self._pw.chromium.launch(channel=channel, headless=headless)
        except Exception:  # noqa: BLE001 — channel=chrome may be unavailable; fall back to bundled Chromium
            self._browser = self._pw.chromium.launch(headless=headless)
        self._ctx = self._browser.new_context()
        self._pages: dict[str, Any] = {"tab0": self._ctx.new_page()}
        self._active = "tab0"

    def open(self, url: str) -> dict[str, Any]:
        page = self._pages[self._active]
        try:
            page.goto(url, wait_until="load", timeout=30000)
            html = page.content()
            shot = page.screenshot()
            return {"url": url, "html": html, "screenshot": True,
                    "screenshot_hash": _sha256(base64.b64encode(shot).decode()), "har": None, "a11y": None}
        except Exception as exc:  # noqa: BLE001
            return {"url": url, "html": "", "screenshot": None, "har": None, "a11y": None,
                    "error": f"{type(exc).__name__}: {exc}"}

    def list_tabs(self) -> list[dict[str, Any]]:
        out = []
        for tid, pg in self._pages.items():
            try:
                url = pg.url
            except Exception:  # noqa: BLE001
                url = ""
            out.append({"id": tid, "url": url, "active": tid == self._active})
        return out

    def new_tab(self, url: str = "about:blank") -> str:
        tid = f"tab{len(self._pages)}"
        self._pages[tid] = self._ctx.new_page()
        self._active = tid
        return tid

    def switch_tab(self, tab_id: str) -> bool:
        if tab_id in self._pages:
            self._active = tab_id
            return True
        return False

    def close_tab(self, tab_id: str) -> bool:
        if tab_id in self._pages and len(self._pages) > 1:
            try:
                self._pages.pop(tab_id).close()
            except Exception:  # noqa: BLE001
                self._pages.pop(tab_id, None)
            self._active = next(iter(self._pages))
            return True
        return False

    def close(self) -> None:
        try:
            self._browser.close()
            self._pw.stop()
        except Exception:  # noqa: BLE001
            pass


class PlaywrightAdapter(_BackendAdapter):
    """Regression-grade adapter over Playwright (channel=chrome). Real if launchable; else degrades to unsupported."""

    name = "playwright"
    JS_RENDER = True
    CAPABILITIES = {k: True for k in CAPABILITY_KEYS}

    def __init__(self, *, channel: str = "chrome", headless: bool = True,
                 clock: Optional[Callable[[], float]] = None, allow_side_effects: bool = False) -> None:
        super().__init__(clock=clock or _wall_clock(), allow_side_effects=allow_side_effects)
        self._channel = channel
        self._headless = headless

    def _make_backend(self) -> BackendPort:
        return _PlaywrightBackend(channel=self._channel, headless=self._headless)


__all__ = ["PlaywrightAdapter"]
