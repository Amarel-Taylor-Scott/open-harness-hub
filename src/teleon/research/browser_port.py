"""src.teleon.research.browser_port — the BROWSER ABSTRACTION LAYER: any browser engine behind ONE uniform port.

Why (owner 2026-06-21): more browsers keep arriving. Components must depend on an engine-AGNOSTIC port, never a
specific engine, so a FUTURE browser drops in with ZERO component change. The selectable browsers are POPULATED FROM
the registry (architecture/web_browsing_stack_registry.json) — a browser added there is selectable here; a chromium-
engine browser reuses the Playwright adapter automatically; a new ENGINE = register one adapter; a declared-but-unwired
engine returns an HONEST 'not wired' error, never a fabricated page. serves_truth=false.

  port = select_browser("auto")          # the default engine adapter (Playwright/chromium)
  port = select_browser("crawl4ai")      # a registry browser id → its engine's adapter
  page = port.render(url)                # uniform {title, text, links} | {error}
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Callable, Protocol, runtime_checkable

_REPO = Path(__file__).resolve().parents[3]
_RENDER_MJS = _REPO / "e2e" / "scrape_url.mjs"
_REGISTRY = _REPO / "architecture" / "web_browsing_stack_registry.json"


@runtime_checkable
class BrowserPort(Protocol):
    name: str
    def render(self, url: str) -> dict: ...


class CallableBrowser:
    """Wrap any (url)->dict render callable (tests / custom integrations)."""
    def __init__(self, fn: Callable[[str], dict], *, name: str = "callable"):
        self._fn, self.name = fn, name
    def render(self, url: str) -> dict:
        try:
            return self._fn(url) or {"error": "empty"}
        except Exception as e:  # noqa: BLE001
            return {"error": str(e)[:80]}


class PlaywrightBrowser:
    """The chromium adapter (via e2e/scrape_url.mjs). Honest 'render unavailable' when node/chromium/network is missing."""
    name = "playwright"
    def render(self, url: str, *, timeout: int = 40, mode: str = "headless") -> dict:
        """mode = headless (default) | headed — a rung on architecture/browser_escalation_ladder.json."""
        try:
            r = subprocess.run(["node", str(_RENDER_MJS), url, mode], cwd=str(_REPO), capture_output=True, text=True, timeout=timeout)
            line = (r.stdout or "{}").strip().splitlines()[-1] if (r.stdout or "").strip() else "{}"
            return json.loads(line)
        except Exception as e:  # noqa: BLE001
            return {"error": f"render unavailable: {type(e).__name__}: {str(e)[:80]}"}


class StubBrowser:
    name = "stub"
    def render(self, url: str) -> dict:
        return {"title": "stub", "text": "", "links": []}


class NotWiredBrowser:
    """A browser DECLARED in the registry whose engine adapter isn't wired yet — honest, never fabricates a page."""
    def __init__(self, name: str, engine: str):
        self.name, self._engine = name, engine
    def render(self, url: str) -> dict:
        return {"error": f"browser '{self.name}' (engine '{self._engine}') not wired — register a '{self._engine}' adapter"}


#: engine -> adapter factory. A FUTURE engine = register one adapter; every chromium-engine browser in the registry
#: reuses Playwright automatically (zero code).
_ENGINE_ADAPTERS: dict[str, Callable[[], BrowserPort]] = {"chromium": PlaywrightBrowser}
#: name/id -> adapter factory (explicit overrides + non-engine entries).
_NAME_ADAPTERS: dict[str, Callable[[], BrowserPort]] = {
    "auto": PlaywrightBrowser, "playwright": PlaywrightBrowser, "stub": StubBrowser,
}


def register_browser_adapter(name: str, factory: Callable[[], BrowserPort], *, engine: bool = False) -> None:
    """Register a new browser adapter — by NAME, or by ENGINE (engine=True) so every registry browser on that engine
    uses it. The future-proofing hook: components consuming select_browser() never change."""
    (_ENGINE_ADAPTERS if engine else _NAME_ADAPTERS)[str(name)] = factory


def _registry() -> dict:
    try:
        return json.loads(_REGISTRY.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {"browsers": []}


def available_browsers() -> dict:
    """Selectable browsers, POPULATED FROM the registry: every browser id + the registered name/engine adapters.
    Adding a browser to web_browsing_stack_registry.json makes it selectable here (no code change for a known engine)."""
    reg = _registry()
    return {"registry_browsers": sorted(b["id"] for b in reg.get("browsers", [])),
            "name_adapters": sorted(_NAME_ADAPTERS), "engine_adapters": sorted(_ENGINE_ADAPTERS), "serves_truth": False}


def select_browser(engine_or_id: str = "auto", **kw) -> BrowserPort:
    """Resolve a name / engine / registry-browser-id to a BrowserPort. A registry browser maps to its engine's adapter
    (chromium → Playwright); a declared-but-unwired engine → an honest NotWiredBrowser; 'auto' → Playwright. Never raises."""
    if engine_or_id in _NAME_ADAPTERS:
        return _NAME_ADAPTERS[engine_or_id]()
    if engine_or_id in _ENGINE_ADAPTERS:
        return _ENGINE_ADAPTERS[engine_or_id]()
    for b in _registry().get("browsers", []):                 # a registry browser id → its engine's adapter
        if b.get("id") == engine_or_id:
            eng = (b.get("engine") or "").split(",")[0].strip()
            return _ENGINE_ADAPTERS[eng]() if eng in _ENGINE_ADAPTERS else NotWiredBrowser(b["id"], eng or "unknown")
    return PlaywrightBrowser()


__all__ = ["BrowserPort", "CallableBrowser", "PlaywrightBrowser", "StubBrowser", "NotWiredBrowser",
           "register_browser_adapter", "available_browsers", "select_browser"]
