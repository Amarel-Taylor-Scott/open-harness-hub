"""src.teleon.evolution.descent_attempt_store — the BRAIN + data store for EVERY descent/distillation attempt.

The spine of the whole portfolio is moving each unit of work *unbounded & inefficient -> most-bounded & most-efficient*.
This is the canonical, append-only, content-addressed store of every attempt at that move — across all runners, units,
and strategies — so the system gets SMARTER OVER TIME: it is (1) the meta-learner's memory (the empirically-best
strategy per before-state, computed from records) and (2) the training corpus for a model that learns to pick the
descent move that bounds a unit cheapest.

LOSSLESS by design: it keeps FAILED and ROLLED-BACK attempts and the rejected 'losers' too — a descent-policy model
must learn from what did NOT work, not only the winners. Idempotent (content-hash dedupe), deterministic, offline.
serves_truth=false (an attempt record is evidence, never a truth claim). Internal infra now; a public-revenue
candidate later as **OpenDistillationHub** (the Amazon internal-infra -> public-registry strategy). Teleon-layer.
"""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path

#: the descent axes a unit is scored on (lower cost/tokens/stale-risk + higher determinism = more bounded/efficient).
AXES = ("cost", "determinism", "tokens", "model_tier", "stale_risk")
OUTCOMES = ("improved", "converged", "no_change", "failed", "rolled_back")
_SUCCESS = ("improved", "converged")   # the rest (no_change/failed/rolled_back) are retained NEGATIVES for training


@dataclass(frozen=True)
class DescentAttempt:
    unit_id: str                      # the capability/task the descent was applied to
    strategy: str                     # the descent move tried (e.g. model_downgrade, token_reduction, llm_to_rule)
    before: dict                      # axis values in the unbounded state
    after: dict                       # axis values after the move
    outcome: str                      # one of OUTCOMES
    losers: tuple = ()                # rejected strategies tried for this unit (kept for training negatives)
    rollback_target: str = ""         # what to restore to (lossless)
    raw_ref: str = ""                 # handle to the preserved raw layer
    serves_truth: bool = False

    def attempt_id(self) -> str:
        body = json.dumps({"unit_id": self.unit_id, "strategy": self.strategy, "before": self.before,
                           "after": self.after, "outcome": self.outcome}, sort_keys=True)
        return "att_" + hashlib.sha256(body.encode()).hexdigest()[:16]


def _reward(before: dict, after: dict) -> dict:
    """Computed deltas (the training reward signal): how much MORE bounded/efficient the unit became."""
    return {
        "cost_saved": round(before.get("cost", 0.0) - after.get("cost", 0.0), 6),
        "determinism_gain": round(after.get("determinism", 0.0) - before.get("determinism", 0.0), 6),
        "tokens_saved": before.get("tokens", 0) - after.get("tokens", 0),
        "model_tier_drop": before.get("model_tier", 0) - after.get("model_tier", 0),
        "stale_risk_drop": round(before.get("stale_risk", 0.0) - after.get("stale_risk", 0.0), 6),
    }


class DescentAttemptStore:
    """Append-only JSONL store of descent attempts; idempotent by attempt_id; lossless (keeps negatives)."""

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def all(self) -> list[dict]:
        if not self.path.exists():
            return []
        return [json.loads(ln) for ln in self.path.read_text(encoding="utf-8").splitlines() if ln.strip()]

    def append(self, attempt: DescentAttempt) -> dict:
        """Append an attempt; idempotent — re-appending the same attempt does NOT duplicate it."""
        if attempt.outcome not in OUTCOMES:
            raise ValueError(f"unknown outcome {attempt.outcome!r}")
        rec = asdict(attempt)
        rec["attempt_id"] = attempt.attempt_id()
        rec["reward"] = _reward(attempt.before, attempt.after)
        rec["success"] = attempt.outcome in _SUCCESS
        if any(r["attempt_id"] == rec["attempt_id"] for r in self.all()):
            return rec
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, sort_keys=True) + "\n")
        return rec

    def training_examples(self) -> list[dict]:
        """The supervised corpus for a descent-policy model: features = the before-state, label = the strategy tried,
        reward = the achieved deltas, success = whether it bounded the unit. INCLUDES negatives (failures/losers)."""
        out = []
        for r in self.all():
            out.append({"features": dict(r["before"]), "label": r["strategy"],
                        "reward": r["reward"], "success": r["success"], "outcome": r["outcome"]})
        return out

    def stats(self) -> dict:
        """Per-strategy success rate + mean cost saved — the meta-learner's aggregate readout (computed, not typed)."""
        by: dict[str, dict] = {}
        for r in self.all():
            s = by.setdefault(r["strategy"], {"n": 0, "wins": 0, "cost_saved": 0.0})
            s["n"] += 1
            s["wins"] += 1 if r["success"] else 0
            s["cost_saved"] += r["reward"]["cost_saved"]
        for s in by.values():
            s["success_rate"] = round(s["wins"] / s["n"], 4) if s["n"] else 0.0
            s["mean_cost_saved"] = round(s["cost_saved"] / s["n"], 6) if s["n"] else 0.0
        return by

    def best_strategy_for(self, before: dict) -> str | None:
        """The meta-learner readout: among SUCCESSFUL attempts on units that started near this before-state, the
        strategy with the highest mean cost saved. Computed from records — this is exactly what a trained model would
        later predict; until then it is the empirical recommendation."""
        det = round(before.get("determinism", 0.0), 1)   # coarse bucket by starting determinism
        cand: dict[str, list] = {}
        for r in self.all():
            if r["success"] and round(r["before"].get("determinism", 0.0), 1) == det:
                cand.setdefault(r["strategy"], []).append(r["reward"]["cost_saved"])
        if not cand:
            return None
        return max(cand, key=lambda s: sum(cand[s]) / len(cand[s]))
