"""src.openharnesshub.discovery — STATELESS OpenClaw (finder) + Hermes (router) that keep every Open*Hub fresh.

Two stateless engines that continuously add/append/update each hub's content:
  * **OpenClaw** — a stateless, PLUGIN-based finder. Each plugin targets one hub + content kind (repos, harnesses,
    context, skills, skill→tool, MCP, compression, ...). It runs each plugin with the cheapest, MOST BOUNDED available
    tool (the unbounded→bounded descent: a bounded API beats a search beats a raw scrape) drawn from the injected TOOL
    REPOSITORY (web search / JS scraping / github API / research_radar — our unbounded→bounded tool catalog).
  * **Hermes** — a stateless request ROUTER. It maps a request (hub + query) to OpenClaw discovery and delivers the
    candidates into that hub's HubEngine.ingest → the hub's lifecycle (digest→verify→version→serve). Continuous append.

STATELESS by design: both hold only their config (plugins); all persistence lives in the ComponentStore + the durable
logs. Tools + hub engines are INJECTED (ports) — offline-testable with deterministic stubs; real tools wired by the
operator layer (so this open-layer module imports no dev tool; plane-clean + dependency-law clean). Governed:
discovered items are CANDIDATES (serves_truth=false; discovery≠trust) — they only serve after the hub's verify gate.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable

#: tool tiers, MOST BOUNDED → least bounded (the descent prefers the lowest rank that can serve the plugin).
_TIER_RANK = {"api": 0, "search": 1, "scrape": 2}


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(s).lower()).strip("-") or "item"


@dataclass(frozen=True)
class Tool:
    """An entry in the unbounded→bounded TOOL REPOSITORY. fn: (query)->list[raw]. Lower tier+cost = more bounded/cheaper."""
    name: str
    tier: str                       # "api" (bounded) | "search" | "scrape" (unbounded)
    cost: int                       # 1..5 (lower = cheaper)
    fn: Callable[[str], list]


@dataclass(frozen=True)
class Plugin:
    """A stateless OpenClaw finder for ONE hub + content kind. finder: (query, Tool)->list[raw candidates]."""
    name: str
    target_hub: str
    content_kind: str
    tool_tier: str = "search"       # the LEAST-bounded tier it will accept (it prefers more-bounded if available)
    finder: Callable[[str, Tool], list] = field(default=None)  # type: ignore[assignment]


class OpenClaw:
    """Stateless plugin-based finder. Holds only the plugin registry; discover() is pure given (hub, query, tools)."""

    def __init__(self, plugins: list[Plugin]):
        self.plugins = tuple(plugins)

    def plugins_for(self, hub: str) -> list[Plugin]:
        return [p for p in self.plugins if p.target_hub == hub]

    def pick_tool(self, plugin: Plugin, tools: list[Tool]) -> Tool | None:
        """The unbounded→bounded DESCENT: among tools at-or-more-bounded than the plugin's tier, pick the most bounded,
        then the cheapest. Falls back to any tool if none match the tier."""
        max_rank = _TIER_RANK.get(plugin.tool_tier, 2)
        elig = [t for t in tools if _TIER_RANK.get(t.tier, 2) <= max_rank] or list(tools)
        return min(elig, key=lambda t: (_TIER_RANK.get(t.tier, 2), t.cost)) if elig else None

    def discover(self, hub: str, query: str, *, tools: list[Tool]) -> list[dict]:
        out: list[dict] = []
        for p in self.plugins_for(hub):
            tool = self.pick_tool(p, tools)
            if not tool or not p.finder:
                continue
            try:
                raws = p.finder(query, tool)
            except Exception:  # noqa: BLE001 — a failing source never stops discovery
                raws = []
            for raw in raws:
                out.append({"hub": hub, "content_kind": p.content_kind, "via_plugin": p.name,
                            "via_tool": tool.name, "tool_tier": tool.tier, "raw": raw, "serves_truth": False})
        return out


class Hermes:
    """Stateless request ROUTER: discover for a hub via OpenClaw, then deliver candidates into that hub's engine."""

    def handle(self, hub: str, query: str, *, openclaw: OpenClaw, hub_engines: dict, tools: list[Tool],
               tenant: str = "_global") -> dict:
        candidates = openclaw.discover(hub, query, tools=tools)
        eng = hub_engines.get(hub)
        ingested = 0
        if eng is not None:
            for c in candidates:
                raw = c["raw"]
                body = dict(raw) if isinstance(raw, dict) else {"name": str(raw)}
                body.setdefault("name", body.get("title") or body.get("id") or _slug(str(raw)))
                body["discovered_via"] = c["via_plugin"]
                body["tool"] = c["via_tool"]
                eng.ingest(body, tenant=tenant)
                ingested += 1
        return {"hub": hub, "query": query, "discovered": len(candidates), "ingested": ingested, "serves_truth": False}

    def sweep(self, query: str, *, openclaw: OpenClaw, hub_engines: dict, tools: list[Tool]) -> list[dict]:
        """Route ONE query across every hub that has a plugin — the continuous freshness pass."""
        hubs = sorted({p.target_hub for p in openclaw.plugins})
        return [self.handle(h, query, openclaw=openclaw, hub_engines=hub_engines, tools=tools) for h in hubs]


# ── default plugin set (content kind → target hub) + offline stub tools ───────────────────────────────────────
#: which hub each content kind feeds (single map; extend by adding a Plugin).
_DEFAULT_PLUGIN_MAP = [
    ("repos", "OpenToolsHub", "api"),
    ("harnesses", "OpenHarnessHub", "search"),
    ("context", "OpenContextHub", "api"),
    ("skills", "OpenSkillsHub", "search"),
    ("skill_to_tool", "OpenSkillToTool", "search"),
    ("mcp", "OpenMCPHub", "api"),
    ("compression", "OpenCompressionHub", "search"),
]


def _finder(content_kind: str) -> Callable[[str, Tool], list]:
    def find(query: str, tool: Tool) -> list:
        return tool.fn(f"{content_kind} {query}")
    return find


def default_plugins() -> list[Plugin]:
    """A finder per content kind. Real deployments add/override plugins; the finder uses whatever tool OpenClaw picks."""
    return [Plugin(name=f"find_{ck}", target_hub=hub, content_kind=ck, tool_tier=tier, finder=_finder(ck))
            for ck, hub, tier in _DEFAULT_PLUGIN_MAP]


def stub_tools() -> list[Tool]:
    """Deterministic offline TOOL REPOSITORY (so discovery is testable with no network). Real deployments inject
    web-search / JS-scraping / github-API / research_radar-backed tools at these same tiers (unbounded→bounded)."""
    def _gen(prefix: str):
        def fn(q: str) -> list:
            return [{"name": f"{_slug(q)}-{i}", "source": prefix, "query": q} for i in range(2)]
        return fn
    return [Tool("stub_api", "api", 1, _gen("api")), Tool("stub_search", "search", 2, _gen("search")),
            Tool("stub_scrape", "scrape", 4, _gen("scrape"))]


__all__ = ["Tool", "Plugin", "OpenClaw", "Hermes", "default_plugins", "stub_tools"]
