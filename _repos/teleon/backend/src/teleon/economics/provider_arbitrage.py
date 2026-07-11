"""provider_arbitrage — cross-provider price arbitrage for the SAME model (backs registry #63).

Same model, different providers, different price. Reads _repos/shared-backend-components/architecture/model_index.json entries (each row is a
(model_id, provider, cost_per_mtok_in/out) tuple) and finds models served by >1 provider, computing the price
SPREAD (cheapest vs dearest) = the arbitrage opportunity + the savings.

Complements economics/routing_engine.route_model (which PICKS a viable route under a PreferenceProfile): this
surfaces WHERE the savings are across providers. Honest when a model has a single provider (no arbitrage) or the
price feed is missing — registry #63 records that a REAL-TIME cross-provider feed is still partial; this is the
static, registry-grounded version of it. serves_truth=false (prices are evidence, not a truth claim).
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import json
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[3])          # _repos/teleon/backend/src/teleon/economics/ -> repo root
_MODEL_INDEX = _resource("architecture") / "model_index.json"
_PCT = 100  # fraction -> percent


def _load_entries() -> list[dict]:
    return json.loads(_MODEL_INDEX.read_text()).get("entries", [])


def _blended_cost(entry: dict) -> float | None:
    """Blended $/Mtok = input + output (a 1:1 simplification; a workload-specific blend would weight by that
    workload's own input:output token ratio — stated, not a hidden constant)."""
    ci, co = entry.get("cost_per_mtok_in"), entry.get("cost_per_mtok_out")
    if ci is None or co is None:
        return None
    return float(ci) + float(co)


def arbitrage_for_model(model_id: str, entries: list[dict] | None = None) -> dict:
    """Price spread across providers serving `model_id`. available=False when unpriced/absent."""
    entries = entries if entries is not None else _load_entries()
    rows = []
    for e in entries:
        if e.get("model_id") != model_id:
            continue
        c = _blended_cost(e)
        if c is None:
            continue
        rows.append({"provider": e.get("provider"), "blended_cost": c,
                     "cost_per_mtok_in": e.get("cost_per_mtok_in"), "cost_per_mtok_out": e.get("cost_per_mtok_out")})
    if not rows:
        return {"model_id": model_id, "available": False, "reason": "no priced entry for model"}
    rows.sort(key=lambda r: r["blended_cost"])
    cheapest, dearest = rows[0], rows[-1]
    spread = None
    if len(rows) > 1 and dearest["blended_cost"] > 0:
        spread = (dearest["blended_cost"] - cheapest["blended_cost"]) / dearest["blended_cost"]
    return {
        "model_id": model_id, "available": True, "arbitrage": len(rows) > 1,
        "n_providers": len(rows), "cheapest": cheapest, "dearest": dearest,
        "spread_pct": round(spread * _PCT, 1) if spread is not None else None,
        "providers": rows,
    }


def all_arbitrage(entries: list[dict] | None = None) -> list[dict]:
    """Every model served by >1 provider, biggest price spread first (where the savings are)."""
    entries = entries if entries is not None else _load_entries()
    model_ids = sorted({e.get("model_id") for e in entries if e.get("model_id")})
    out = [a for mid in model_ids if (a := arbitrage_for_model(mid, entries)).get("arbitrage")]
    out.sort(key=lambda a: a.get("spread_pct") or 0, reverse=True)
    return out
