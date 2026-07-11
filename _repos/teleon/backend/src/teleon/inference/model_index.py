"""src.teleon.inference.model_index — pick the best + cheapest STILL-EFFECTIVE model from a UNIFIED model index,
governed by FRESHNESS.

Model facts (cost, live endpoint, download location, quality) are volatile — a stale price or a dead endpoint is
worse than none. So selection runs ONLY over FRESH entries: an entry whose `last_verified` is older than its
volatility-matched cadence (or that took a CDC 'changed' event) is HELD OUT and never selected until re-verified.
This is the freshness wedge applied to the routing layer — the same rule the freshness_runtime applies to facts.

Selection = cheapest (by output then input cost) among entries meeting a quality floor + the caller's kind/data
filters, ties broken toward higher quality, deterministic. Reads _repos/shared-backend-components/architecture/model_index.json (which consolidates
the lowcost/free endpoint registries + quality tiers and adds download_location + unified cost + freshness). A
selection is evidence, never truth (serves_truth False).
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import json
from pathlib import Path

from src.teleon.evolution.descent_axes import freshness_policy

_INDEX_PATH = _resource("architecture") / "model_index.json"
STATUS_FRESH = "fresh"
STATUS_HELD_OUT_STALE = "held_out"
#: volatility-matched sync cadence → the max age (days) a fact may be before it is held out as stale.
_CADENCE_MAX_AGE_DAYS = {"continuous": 0, "daily": 1, "weekly": 7, "monthly": 31, "on_change_only": 36500}


def load_index() -> list[dict]:
    return [dict(e, freshness=dict(e["freshness"])) for e in json.loads(_INDEX_PATH.read_text())["entries"]]


def _days_between(a: str, b: str) -> int:
    from datetime import date
    return (date.fromisoformat(b) - date.fromisoformat(a)).days


def apply_staleness(entries: list[dict], *, now: str) -> list[dict]:
    """Hold out any entry whose `last_verified` is older than its volatility-matched cadence (kept-up-to-date rule)."""
    out = []
    for e in entries:
        e = dict(e, freshness=dict(e["freshness"]))
        cadence = freshness_policy(e["freshness"]["volatility_class"])["sync_cadence"]
        max_age = _CADENCE_MAX_AGE_DAYS.get(cadence, 31)
        if _days_between(e["freshness"]["last_verified"], now) > max_age:
            e["freshness"]["status"] = STATUS_HELD_OUT_STALE
        out.append(e)
    return out


def mark_stale(entries: list[dict], model_id: str) -> list[dict]:
    """A CDC 'changed' event for a model's facts → hold it out until re-verified."""
    return [dict(e, freshness=dict(e["freshness"], status=STATUS_HELD_OUT_STALE)) if e["model_id"] == model_id
            else e for e in entries]


def resync(entries: list[dict], model_id: str, *, now: str) -> list[dict]:
    """Re-verify a model's facts → fresh again (selectable)."""
    return [dict(e, freshness=dict(e["freshness"], status=STATUS_FRESH, last_verified=now)) if e["model_id"] == model_id
            else e for e in entries]


def select_best(entries: list[dict], *, quality_floor_rank: int = 0, kinds: tuple = (), max_cost_out=None,
                prefer_local: bool = False) -> dict:
    """Pick the cheapest FRESH model meeting the quality floor (+ optional kind/cost filters). Stale entries are
    excluded — never select model facts we can't vouch are current. Returns the pick + the reasoning."""
    fresh = [e for e in entries if e["freshness"]["status"] == STATUS_FRESH]
    held_out = [e["model_id"] for e in entries if e["freshness"]["status"] != STATUS_FRESH]
    pool = [e for e in fresh if e["quality_rank"] >= quality_floor_rank
            and (not kinds or e["kind"] in kinds)
            and (max_cost_out is None or e["cost_per_mtok_out"] <= max_cost_out)]

    def key(e):
        local_pref = 0 if (prefer_local and e["kind"] == "local_weights") else 1
        return (local_pref, e["cost_per_mtok_out"], e["cost_per_mtok_in"], -e["quality_rank"], e["model_id"])

    pool.sort(key=key)
    pick = pool[0] if pool else None
    return {
        "picked": pick["model_id"] if pick else None,
        "endpoint": pick["live_endpoint"] if pick else None,
        "download_location": pick["download_location"] if pick else None,
        "cost_per_mtok_out": pick["cost_per_mtok_out"] if pick else None,
        "reason": ("cheapest fresh model meeting the quality floor" if pick else "no fresh model meets the constraints"),
        "considered": [e["model_id"] for e in pool],
        "excluded_stale": sorted(held_out),
        "serves_truth": False,
    }
