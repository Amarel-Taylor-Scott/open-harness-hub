"""src.teleon.hub_freshness — a Teleon CAPABILITY: "continuously update this hub" descended unbounded → bounded.

The killer use case the owner named: give Teleon a plain-text capability per hub —
    "continuously update <hub> with public information, repos, skills, etc."
— and let Teleon DESCEND it. The UNBOUNDED phase runs the stateless OpenClaw/Hermes finders across the WHOLE tool
repository (every tool, incl. the expensive scrape) to discover broadly; the candidates are digested into the hub
(ingest → the hub's verify/version lifecycle); then Teleon MEASURES which tool actually carried the freshness and
DESCENDS to the cheapest BOUNDED tool that still meets the freshness bar — recording the move into the ONE descent
brain so future runs are cheap. Same motion as every Teleon capability: unbounded+inefficient → bounded+efficient.

Teleon consumes the open layer (dependency law: teleon may_depend_on openharnesshub) + the descent brain. The hub
imports neither Baltor nor Teleon; Teleon orchestrates. serves_truth=false (discovered items are candidates).
"""
from __future__ import annotations

import re


def _key(cand: dict) -> tuple:
    raw = cand.get("raw")
    name = raw.get("name") if isinstance(raw, dict) else str(raw)
    return (cand.get("content_kind"), re.sub(r"[^a-z0-9]+", "-", str(name).lower()).strip("-"))


def keep_hub_fresh(hub: str, intent: str, *, hub_engines: dict, openclaw, tools: list,
                   brain=None, freshness_floor: float = 0.5, tenant: str = "_global") -> dict:
    """Run the freshness capability for one hub and DESCEND the discovery cost. Returns a governed summary.

    1. UNBOUNDED: measure each tool's yield (run the hub's plugins with that single tool); union = max freshness.
    2. DIGEST: ingest the union into the hub (its engine digests → unverified versions → the verify gate decides serving).
    3. DESCEND: pick the cheapest tool whose yield ≥ freshness_floor × the unbounded union → the bounded path.
    4. RECORD the descent (unbounded all-tools cost → bounded single-tool cost) into the descent brain.
    """
    # 1. unbounded exploration — per-tool yield + the union
    per_tool, union = [], {}
    for t in tools:
        cands = openclaw.discover(hub, intent, tools=[t])
        per_tool.append({"tool": t.name, "tier": t.tier, "cost": int(t.cost), "yield": len(cands)})
        for c in cands:
            union[_key(c)] = c
    unbounded_cost = sum(pt["cost"] for pt in per_tool) or 1
    unbounded_yield = len(union)

    # 2. digest the union into the hub (continuous append; governed)
    ingested = 0
    eng = hub_engines.get(hub)
    if eng is not None:
        for c in union.values():
            raw = c["raw"]
            body = dict(raw) if isinstance(raw, dict) else {"name": str(raw)}
            body["discovered_via"], body["tool"] = c.get("via_plugin"), c.get("via_tool")
            eng.ingest(body, tenant=tenant)
            ingested += 1

    # 3. descend — cheapest BOUNDED tool that still meets the freshness bar
    bar = max(1, int(freshness_floor * unbounded_yield))
    eligible = sorted([pt for pt in per_tool if pt["yield"] >= bar], key=lambda pt: (pt["cost"], pt["tier"]))
    bounded = eligible[0] if eligible else max(per_tool, key=lambda pt: pt["yield"], default={"tool": None, "cost": unbounded_cost, "yield": 0})
    bounded_cost = int(bounded["cost"])
    saved = unbounded_cost - bounded_cost
    pct = round(100 * saved / unbounded_cost, 1) if unbounded_cost else 0.0

    # 4. record the descent into the ONE brain (unbounded all-tools → bounded single cheap tool)
    if brain is not None:
        try:
            from src.teleon.evolution.descent_attempt_store import DescentAttempt
            brain.append(DescentAttempt(
                unit_id=f"hub_freshness:{hub}", strategy="tool_descent",
                before={"cost": float(unbounded_cost), "determinism": 0.3, "tokens_in": 0, "llm_usage": 0, "freshness": 1.0},
                after={"cost": float(bounded_cost), "determinism": 0.3, "tokens_in": 0, "llm_usage": 0,
                       "freshness": round(bounded["yield"] / unbounded_yield, 3) if unbounded_yield else 1.0},
                outcome="improved" if saved > 0 else "no_change",
                losers=tuple(pt["tool"] for pt in per_tool if pt["tool"] != bounded["tool"]),
                rollback_target="all-tools (unbounded)",
                raw_ref="src/teleon/hub_freshness.py", substrate_ref=f"openclaw:{hub}"))
        except Exception:  # noqa: BLE001 — recording is annotation; never block freshness
            pass

    return {"hub": hub, "intent": intent, "discovered": unbounded_yield, "ingested": ingested,
            "unbounded_cost": unbounded_cost, "bounded_tool": bounded["tool"], "bounded_cost": bounded_cost,
            "pct_saved": pct, "serves_truth": False}


__all__ = ["keep_hub_fresh"]
