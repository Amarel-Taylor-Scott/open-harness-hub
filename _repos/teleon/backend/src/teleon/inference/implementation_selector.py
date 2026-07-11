"""src.teleon.inference.implementation_selector — pick the best IMPLEMENTATION COMBINATION for a capability.

A capability (entity-resolution, grounded-search, image-processing, …) is facilitated by a VARIETY of options —
internal repos, libraries, API hubs, models, LLMs. Each declares the tools/models/API-keys it needs (keys by NAME,
env refs only), a cost tier, and a determinism ceiling. This selector chooses the best option for a tenant given
(a) which API keys/models they actually have, and (b) their objective (cheapest capable / most deterministic),
excluding options whose required keys are missing, and returning the ordered fallbacks. Reads
_repos/shared-backend-components/architecture/capability_implementation_registry.json. A selection is evidence, never truth (serves_truth False).
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import json
from pathlib import Path

_REGISTRY = _resource("architecture") / "capability_implementation_registry.json"
#: cost ordering for "cheapest" (lower is cheaper).
_COST_RANK = {"free": 0, "low": 1, "mid": 2, "per_call": 3}
_DET_FLOOR = 0.9  # "require_deterministic" admits only options at/above this determinism ceiling


def load_registry() -> dict:
    return json.loads(_REGISTRY.read_text())


def implementations_for(capability: str) -> list[dict]:
    for c in load_registry()["capabilities"]:
        if c["capability"] == capability:
            return list(c["implementations"])
    return []


def select_implementation(capability: str, *, available_keys: tuple = (), objective: str = "cheapest",
                          require_deterministic: bool = False) -> dict:
    """Pick the best implementation whose required API keys are ALL available, by objective. Returns the pick +
    the ordered fallbacks + what was excluded for missing keys."""
    have = {k.upper() for k in available_keys}
    impls = implementations_for(capability)
    runnable, blocked = [], []
    for im in impls:
        missing = [k for k in im.get("api_keys", []) if k.upper() not in have]
        (blocked if missing else runnable).append((im, missing))
    pool = [im for im, _ in runnable]
    if require_deterministic:
        pool = [im for im in pool if im["determinism_ceiling"] >= _DET_FLOOR]

    def key(im):
        if objective == "most_deterministic":
            return (-im["determinism_ceiling"], _COST_RANK.get(im["cost_tier"], 9), im["impl_id"])
        return (_COST_RANK.get(im["cost_tier"], 9), -im["determinism_ceiling"], im["impl_id"])  # cheapest, det tiebreak

    pool.sort(key=key)
    pick = pool[0] if pool else None
    return {
        "capability": capability,
        "picked": pick["impl_id"] if pick else None,
        "kind": pick["kind"] if pick else None,
        "needs_keys": pick["api_keys"] if pick else None,
        "determinism_ceiling": pick["determinism_ceiling"] if pick else None,
        "fallbacks": [im["impl_id"] for im in pool[1:]],
        "excluded_missing_keys": {im["impl_id"]: miss for im, miss in blocked},
        "reason": (f"best '{objective}' implementation whose required keys are available"
                   + (" (deterministic-only)" if require_deterministic else "")) if pick
                  else "no implementation's required keys are available (provision a key or add a key-free option)",
        "serves_truth": False,
    }
