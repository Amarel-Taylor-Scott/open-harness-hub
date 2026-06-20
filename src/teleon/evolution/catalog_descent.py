"""src.teleon.evolution.catalog_descent — run the unbounded->bounded DESCENT over the real capability catalog and
record EVERY attempt into the descent brain.

This is the convert-skills/tools demo wired to the brain: for each capability in architecture/
modality_capability_catalog.json (real pipelines with deterministic-spine vs model-core stages), compute the cheapest
bounded version the catalog says is achievable, and append a DescentAttempt to the DescentAttemptStore. The store then
holds the training corpus + meta-learner readout, so the system gets smarter at bounding over time.

The cost/tier numbers are an explicit, transparent ESTIMATE model from stage counts (like the cascade's fixtures) — the
point is the WIRING and the descent direction, recorded losslessly. In the live fleet the cheap brain (GLM-5.2 / Kimi,
the ollama lane) PROPOSES each conversion; here we use the catalog's already-governed `deterministic_achievable` signal
so the demo is offline + deterministic. serves_truth=false; Teleon-layer.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from src.teleon.evolution.descent_attempt_store import DescentAttempt, DescentAttemptStore

_REPO = Path(__file__).resolve().parents[3]
_CATALOG = _REPO / "architecture" / "modality_capability_catalog.json"

_MODEL_STAGE_COST = 0.05   # estimated cost of one non-deterministic (model-core) stage at frontier tier
_DET_STAGE_COST = 0.002    # estimated cost of one deterministic stage
_CHEAP_FACTOR = 0.1        # a cheap model runs a model-core stage at ~10% of the frontier cost


def load_catalog() -> list[dict]:
    return json.loads(_CATALOG.read_text(encoding="utf-8")).get("capabilities", [])


def _before(cap: dict) -> dict:
    """Before-state on the canonical descent axes: llm_usage = # model-core stages; freshness = deterministic fraction."""
    stages = cap.get("pipeline", [])
    n = len(stages) or 1
    n_model = sum(1 for s in stages if not s.get("deterministic"))
    det = round((n - n_model) / n, 4)
    return {"cost": round(n_model * _MODEL_STAGE_COST + (n - n_model) * _DET_STAGE_COST, 4),
            "determinism": det, "tokens_in": n_model * 400, "llm_usage": n_model, "freshness": det}


def descend(cap: dict) -> tuple[dict, str, str, tuple]:
    """Return (after_axes, strategy, outcome, losers) — the cheapest bounded version the catalog says is achievable."""
    stages = cap.get("pipeline", [])
    n = len(stages) or 1
    n_model = sum(1 for s in stages if not s.get("deterministic"))
    ach = cap.get("deterministic_achievable")
    before = _before(cap)
    if n_model == 0 or ach == "full":
        after = {"cost": round(n * _DET_STAGE_COST, 4), "determinism": 1.0, "tokens_in": 0,
                 "llm_usage": 0, "freshness": 1.0}
        return after, "llm_to_rule", "converged", ("model_downgrade",)
    if ach == "partial":
        after = {"cost": round(n_model * _MODEL_STAGE_COST * _CHEAP_FACTOR + (n - n_model) * _DET_STAGE_COST, 4),
                 "determinism": before["determinism"], "tokens_in": n_model * 200,
                 "llm_usage": n_model, "freshness": before["freshness"]}
        return after, "model_downgrade", "improved", ("llm_to_rule",)
    # 'none' / unknown: can't bound the structure; downgrade the model tier only (fewer/cheaper model calls)
    after = {"cost": round(before["cost"] * 0.5, 4), "determinism": before["determinism"],
             "tokens_in": before["tokens_in"] // 2, "llm_usage": before["llm_usage"], "freshness": before["freshness"]}
    outcome = "improved" if after["cost"] < before["cost"] else "no_change"
    return after, "model_downgrade", outcome, ("llm_to_rule",)


def convert_catalog(store: DescentAttemptStore, caps: list[dict] | None = None) -> dict:
    """Run the descent over every catalog capability and record each attempt into the brain. Returns a summary."""
    caps = caps if caps is not None else load_catalog()
    fully_bounded = improved = 0
    cost_saved = 0.0
    det_gain = 0.0
    for cap in caps:
        name = cap.get("capability", "?")
        before = _before(cap)
        after, strategy, outcome, losers = descend(cap)
        store.append(DescentAttempt(
            unit_id=f"catalog:{name}", strategy=strategy, before=before, after=after, outcome=outcome,
            losers=losers, rollback_target=f"catalog:{name}@unbounded",
            raw_ref=f"architecture/modality_capability_catalog.json#{name}"))
        cost_saved += before["cost"] - after["cost"]
        det_gain += after["determinism"] - before["determinism"]
        if outcome == "converged":
            fully_bounded += 1
        elif outcome == "improved":
            improved += 1
    n = len(caps)
    return {
        "capabilities": n, "fully_bounded": fully_bounded, "improved": improved,
        "total_cost_saved": round(cost_saved, 4),
        "mean_determinism_gain": round(det_gain / n, 4) if n else 0.0,
        "attempts_recorded": len(store.all()),
        "training_examples": len(store.training_examples()),
        "serves_truth": False,
    }


def demonstrate(store_path: str | Path) -> dict:
    """Run the conversion against the canonical brain store and return the summary + the meta-learner readout."""
    store = DescentAttemptStore(store_path)
    summary = convert_catalog(store)
    summary["best_strategy_low_determinism"] = store.best_strategy_for({"determinism": 0.5})
    summary["per_strategy_stats"] = store.stats()
    return summary
