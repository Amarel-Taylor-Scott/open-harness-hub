"""src.teleon.intel.intelligence_intake — plan a constant intelligence stream from FREE, LEGITIMATE sources.

Reads _repos/shared-backend-components/architecture/intelligence_source_registry.json (RSS + official REST APIs, keyless or free-key, ToS-clean)
and: (a) selects the best free sources for a need given which keys you have, (b) assembles a "news sweep plan"
across all needs (top repos / AI news / papers / newsletters / search), and (c) PULLS via governed-feed-intake —
the legitimate-paths-only intake that refuses ToS-violating scraping/evasion. Items are CANDIDATES (discovery !=
trust); the live pull is network/owner-gated; serves_truth is False. Teleon-layer; never imports baltor.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import json
from pathlib import Path

from src.teleon.seeds import all_seeds

_REGISTRY = _resource("architecture") / "intelligence_source_registry.json"
#: map a source's access mode → the governed-feed-intake legitimate access method.
_ACCESS_TO_FEED = {"rss": "rss", "rest_api": "official_api"}


def load_sources() -> list[dict]:
    return list(json.loads(_REGISTRY.read_text())["sources"])


def needs() -> list[str]:
    return list(json.loads(_REGISTRY.read_text())["needs"])


def select_sources(need: str, *, available_keys: tuple = ()) -> list[dict]:
    """Free sources for a need whose required keys are available — keyless preferred (lowest setup friction)."""
    have = {k.upper() for k in available_keys}
    usable = [s for s in load_sources() if s["need"] == need
              and (s["keyless"] or set(k.upper() for k in s["requires_keys"]) <= have)]
    return sorted(usable, key=lambda s: (0 if not s["requires_keys"] else 1, s["id"]))


def plan_news_sweep(*, available_keys: tuple = ()) -> dict:
    """A complete free news-sweep plan: the selected legitimate sources per need (the rate-limit-proof alternative
    to ad-hoc web search)."""
    plan = {n: [s["id"] for s in select_sources(n, available_keys=available_keys)] for n in needs()}
    return {"plan": plan, "n_sources": sum(len(v) for v in plan.values()),
            "keyless_only": all(not s["requires_keys"] for n in plan for s in select_sources(n)),
            "serves_truth": False}


def _feed_intake():
    return next(s for s in all_seeds() if s.slot == "governed-feed-intake")


def pull(source_id: str, *, items: tuple = (), available_keys: tuple = ()) -> dict:
    """Pull a source via governed-feed-intake (legitimate path only). Offline/sandbox: pass `items` (owner-pasted /
    emulated); live network pull is owner-gated. A key-requiring source with no key is logged unfetchable, not faked."""
    src = next((s for s in load_sources() if s["id"] == source_id), None)
    if not src:
        return {"source_id": source_id, "error": "unknown source", "serves_truth": False}
    have = {k.upper() for k in available_keys}
    if src["requires_keys"] and not set(k.upper() for k in src["requires_keys"]) <= have:
        return {"source_id": source_id, "fetched": False, "unfetchable_logged": True,
                "reason": f"missing key(s) {src['requires_keys']}", "serves_truth": False}
    method = _ACCESS_TO_FEED.get(src["access"], "official_api")
    res = _feed_intake().run({"source": src["source"], "access_method": method, "items": list(items)})["output"]
    return {"source_id": source_id, "access_method": method, "tos_clean": src["tos_clean"],
            "intake": res, "serves_truth": False}
