"""src.teleon.evolution.substrate_selector — select the CONCRETE substrate row a capability descends INTO.

A descent axis is only real if a capability can descend into a concrete row of the SELECTION SUBSTRATE — the
model / context / harness / skill registries Teleon consumes. Until now the model-downgrade descent used a GUESSED
constant (cheap_factor ~ 0.1) and named no model, so the model registry was decorative: deepening it changed
nothing. This module is the thin adapter from a descent axis to a real registry pick, REUSING the existing
objective / model-index selectors (never a parallel selector), so deepening a substrate registry MEASURABLY improves
the descent — the registries become load-bearing.

Pure + deterministic + offline (model_index.select_best uses no clock; entries are pre-marked fresh). A selection is
evidence, never truth (serves_truth False); Teleon-layer — never imports src.baltor.
"""
from __future__ import annotations

from src.teleon.inference import model_index

#: fallback ONLY when the model registry has no fresh model meeting the floor — documented so it is never a silent
#: magic value. A frontier->cheap downgrade lands well under this; the registry-derived factor is used whenever a
#: fresh model qualifies. This is the ONLY estimate; the real path is sourced from architecture/model_index.json.
_FALLBACK_DOWNGRADE_FACTOR = 0.1


def model_downgrade(*, quality_floor_rank: int = 0, entries: list[dict] | None = None) -> dict:
    """The REAL cost-downgrade for the ``cost`` axis: the cheapest FRESH model meeting the quality floor vs the most
    expensive (frontier) FRESH model, both from architecture/model_index.json. Returns the registry-derived factor
    plus the concrete lineage (which model was picked, which it replaced, what was considered) — replacing a guessed
    constant with a sourced, load-bearing number. Falls back to the documented constant only when no fresh model
    qualifies (and flags ``registry_derived=False`` so callers never mistake the estimate for a sourced pick)."""
    entries = entries if entries is not None else model_index.load_index()
    pick = model_index.select_best(entries, quality_floor_rank=quality_floor_rank)
    fresh = [e for e in entries if e["freshness"]["status"] == model_index.STATUS_FRESH]
    frontier = max(fresh, key=lambda e: e["cost_per_mtok_out"]) if fresh else None
    picked_id = pick["picked"]
    if picked_id and frontier and frontier["cost_per_mtok_out"] > 0:
        factor = round(pick["cost_per_mtok_out"] / frontier["cost_per_mtok_out"], 6)
        registry_derived = True
    else:
        factor, registry_derived = _FALLBACK_DOWNGRADE_FACTOR, False
    return {
        "factor": factor,
        "registry_derived": registry_derived,
        "picked_model": picked_id,
        "frontier_model": frontier["model_id"] if frontier else None,
        "considered": pick["considered"],
        "substrate_ref": f"architecture/model_index.json#{picked_id}" if picked_id else "",
        "serves_truth": False,
    }
