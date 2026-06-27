"""src.openhubforai.research_catalog — research/web-browse as a DESCENT-SELECTABLE, GUARDED catalog of components.

The substrate behind "hundreds of shared research + web-browsing components": an agent runner enriching a hub names the
DETAIL it needs (a capability) + what it has available (network/api_key/browser_runtime/llm) + a cost budget; the
descent returns the CHEAPEST eligible component whose capabilities cover that need and that passes the research
guardrails. Cheap structured feeds/APIs first; the expensive LLM-driven browser ONLY when nothing cheaper can get the
detail (deep_detail / js_render / interaction).

Two single sources: architecture/research_component_catalog.json (the components) + architecture/research_guardrail_policy.json
(robots/ToS, login-walled refusal, per-host rate, per-cycle cost ceiling, jurisdiction, PII). Everything stays a
CANDIDATE (serves_truth=false; discovery≠trust). Open layer: stdlib only; no src.teleon / src.baltor import.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

_REPO = Path(__file__).resolve().parents[2]
_CATALOG = _REPO / "architecture" / "research_component_catalog.json"
_GUARDRAILS = _REPO / "architecture" / "research_guardrail_policy.json"
_DEFAULT_TIERS = {"feed": 0, "api": 1, "search": 2, "extract": 3, "render": 4, "browse": 5}


@dataclass(frozen=True)
class ResearchComponent:
    id: str
    name: str
    tier: str
    cost: int
    capabilities: frozenset
    needs: frozenset
    guardrail_ref: str
    status: str
    feeds_hub: str
    hosts: tuple = ()
    serves_truth: bool = False


def _load(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}


def load_catalog(path: Path | None = None) -> tuple[list[ResearchComponent], dict]:
    """Return (components, tier_rank). tier_rank single-sourced from the catalog's `tiers` (fallback to defaults)."""
    d = _load(path or _CATALOG)
    tiers = d.get("tiers", _DEFAULT_TIERS)
    comps = [ResearchComponent(
        id=c["id"], name=c.get("name", c["id"]), tier=c.get("tier", "api"), cost=int(c.get("cost", 3)),
        capabilities=frozenset(c.get("capabilities", [])), needs=frozenset(c.get("needs", [])),
        guardrail_ref=c.get("guardrail_ref", "default_api"), status=c.get("status", "candidate"),
        feeds_hub=c.get("feeds_hub", ""), hosts=tuple(c.get("hosts", [])), serves_truth=False)
        for c in d.get("components", [])]
    return comps, tiers


def load_guardrails(path: Path | None = None) -> dict:
    return _load(path or _GUARDRAILS)


def _host(url_or_host: str) -> str:
    if not url_or_host:
        return ""
    if "://" in url_or_host:
        return (urlparse(url_or_host).hostname or "").lower()
    return url_or_host.lower()


def host_allowed(url_or_host: str, guardrails: dict) -> tuple[bool, str]:
    """Guardrail gate for a host: login-walled hosts are REFUSED (use owner --ingest); jurisdiction deny-list honored."""
    h = _host(url_or_host)
    if not h:
        return True, "no host (local/api component)"
    walled = set(guardrails.get("login_walled_hosts", []))
    if h in walled or any(h.endswith("." + w) for w in walled):
        return False, f"login-walled host refused ({h}) — use owner --ingest with provided material"
    juris = guardrails.get("jurisdiction", {})
    if h in set(juris.get("deny_hosts", [])):
        return False, f"jurisdiction-denied host ({h})"
    return True, "allowed"


def eligible(capability: str, *, host: str = "", available: set | None = None, budget: int | None = None,
             catalog=None, guardrails: dict | None = None) -> list[ResearchComponent]:
    """All components that can get `capability`, in DESCENT order (cheapest tier, then cost). Filters by:
      - capability coverage, - guardrail host gate, - `available` resources (needs minus *_optional), - cost budget
        and the component's guardrail policy `max_cost_per_cycle`."""
    comps, tiers = catalog if catalog else load_catalog()
    g = guardrails if guardrails is not None else load_guardrails()
    policies = g.get("policies", {})
    avail = available if available is not None else {"network"}
    ok_host, _ = host_allowed(host, g) if host else (True, "")
    out = []
    for c in comps:
        if capability not in c.capabilities:
            continue
        if host and not ok_host:
            continue
        hard_needs = {n for n in c.needs if not n.endswith("_optional")}
        if not hard_needs.issubset(avail):
            continue
        pol = policies.get(c.guardrail_ref, {})
        ceiling = pol.get("max_cost_per_cycle")
        if budget is not None and c.cost > budget:
            continue
        if ceiling is not None and c.cost > ceiling:
            continue
        out.append(c)
    return sorted(out, key=lambda c: (tiers.get(c.tier, 9), c.cost, c.id))


def select_component(capability: str, **kw) -> ResearchComponent | None:
    """THE descent over research components: the single cheapest eligible component for the needed detail, or None
    (honest — nothing eligible / over budget / needs unavailable). Escalates to the LLM-driven browser only when it
    is the cheapest thing that can get the detail (e.g. deep_detail)."""
    e = eligible(capability, **kw)
    return e[0] if e else None


def descent_plan(capability: str, **kw) -> dict:
    """A governed selection record: the chosen component + the cheaper-to-costlier fallbacks (try cheap, escalate)."""
    order = eligible(capability, **kw)
    return {"capability": capability, "selected": order[0].id if order else None,
            "escalation": [c.id for c in order], "serves_truth": False,
            "reason": ("cheapest eligible" if order else "no eligible component (budget/needs/guardrail)")}


__all__ = ["ResearchComponent", "load_catalog", "load_guardrails", "host_allowed", "eligible",
           "select_component", "descent_plan"]
