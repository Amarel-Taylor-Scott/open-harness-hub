"""src.teleon.evolution.registry_descent — run the unbounded->bounded DESCENT across ALL capability-bearing registries
and record every attempt into the descent brain (more registries -> more training data).

Registries the converter now spans:
  - architecture/modality_capability_catalog.json   (pipelines: deterministic-spine vs model-core)   [via catalog_descent]
  - architecture/capability_implementation_registry.json  (each capability's impl options: cost_tier + determinism)
  - architecture/tunable_task_catalog.json           (each task's cost-ranked tiers, cheapest-that-meets)

Note: the model / context / harness / skill registries are the SELECTION SUBSTRATE a capability is bounded *against*
(Teleon consumes them), not themselves items to bound — so the converter spans the capability/impl/task registries and
selects from the others. Each attempt records before/after on the 5 descent axes + lineage to the registry. Offline +
deterministic; the live cheap brain (GLM-5.2 / Kimi) proposes conversions in the fleet. serves_truth=false; Teleon-layer.
"""
from __future__ import annotations

import json
from pathlib import Path

from src.teleon.evolution import catalog_descent
from src.teleon.evolution.descent_attempt_store import DescentAttempt, DescentAttemptStore

_REPO = Path(__file__).resolve().parents[3]
_IMPL = _REPO / "architecture" / "capability_implementation_registry.json"
_TUNABLE = _REPO / "architecture" / "tunable_task_catalog.json"

_COST_TIER = {"free": 0.0, "low": 0.01, "mid": 0.05, "high": 0.20, "frontier": 0.30}
_DET_FLOOR = 0.8   # the requirement a bounded pick must still meet


def _axes(cost: float, det: float) -> dict:
    return {"cost": round(cost, 4), "determinism": round(det, 4), "tokens": int(cost * 4000),
            "model_tier": 0 if det >= 0.99 else 60, "stale_risk": round(1.0 - det, 4)}


def _strategy_outcome(before: dict, after: dict) -> tuple:
    if after["determinism"] >= 0.99 and before["determinism"] < 0.99:
        return "llm_to_rule", "converged"
    if after["cost"] < before["cost"]:
        return "model_downgrade", "improved"
    return "model_downgrade", "no_change"


def _impl_registry_attempts() -> list[DescentAttempt]:
    out = []
    for cap in json.loads(_IMPL.read_text(encoding="utf-8")).get("capabilities", []):
        impls = cap.get("implementations", [])
        if not impls:
            continue
        name = cap.get("capability", "?")
        # naive baseline = the most expensive option; bounded pick = cheapest impl that still meets the determinism floor
        before_impl = max(impls, key=lambda im: _COST_TIER.get(im.get("cost_tier"), 0.3))
        meeting = [im for im in impls if im.get("determinism_ceiling", 0.0) >= _DET_FLOOR] or impls
        after_impl = min(meeting, key=lambda im: (_COST_TIER.get(im.get("cost_tier"), 0.3), -im.get("determinism_ceiling", 0.0)))
        before = _axes(_COST_TIER.get(before_impl.get("cost_tier"), 0.3), before_impl.get("determinism_ceiling", 0.5))
        after = _axes(_COST_TIER.get(after_impl.get("cost_tier"), 0.3), after_impl.get("determinism_ceiling", 0.5))
        strat, outcome = _strategy_outcome(before, after)
        out.append(DescentAttempt(unit_id=f"impl-registry:{name}", strategy=strat, before=before, after=after,
                                  outcome=outcome, losers=(before_impl.get("impl_id", ""),),
                                  rollback_target=f"impl:{before_impl.get('impl_id','')}",
                                  raw_ref=f"architecture/capability_implementation_registry.json#{name}"))
    return out


def _tunable_task_attempts() -> list[DescentAttempt]:
    out = []
    for task in json.loads(_TUNABLE.read_text(encoding="utf-8")).get("tasks", []):
        tiers = task.get("tiers", [])
        if not tiers:
            continue
        name = task.get("task_id", "?")
        before_tier = max(tiers, key=lambda t: t.get("cost_rank", 0))                  # unbounded = priciest tier
        after_tier = min(tiers, key=lambda t: (t.get("cost_rank", 0), not t.get("deterministic")))  # cheapest, deterministic-first
        before = _axes(before_tier.get("cost_rank", 0) * 0.02, 1.0 if before_tier.get("deterministic") else 0.2)
        after = _axes(after_tier.get("cost_rank", 0) * 0.02, 1.0 if after_tier.get("deterministic") else 0.2)
        strat, outcome = _strategy_outcome(before, after)
        out.append(DescentAttempt(unit_id=f"tunable-task:{name}", strategy=strat, before=before, after=after,
                                  outcome=outcome, losers=(before_tier.get("tier", ""),),
                                  rollback_target=f"tier:{before_tier.get('tier','')}",
                                  raw_ref=f"architecture/tunable_task_catalog.json#{name}"))
    return out


def convert_all_registries(store: DescentAttemptStore) -> dict:
    """Run the descent across every capability-bearing registry, recording each attempt into the brain."""
    per: dict[str, int] = {}
    # modality catalog (records itself + returns a summary)
    modality = catalog_descent.convert_catalog(store)
    per["modality_capability_catalog"] = modality["capabilities"]
    for label, attempts in (("capability_implementation_registry", _impl_registry_attempts()),
                            ("tunable_task_catalog", _tunable_task_attempts())):
        for a in attempts:
            store.append(a)
        per[label] = len(attempts)
    return {
        "registries": per,
        "items_total": sum(per.values()),
        "attempts_recorded": len(store.all()),
        "training_examples": len(store.training_examples()),
        "best_strategy_low_determinism": store.best_strategy_for({"determinism": 0.2}),
        "serves_truth": False,
    }


def demonstrate(store_path: str | Path) -> dict:
    return convert_all_registries(DescentAttemptStore(store_path))
