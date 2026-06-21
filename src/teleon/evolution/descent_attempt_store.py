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

from src.teleon.evolution.descent_axes import LOWER_IS_BETTER_AXES, is_axis

#: the axes the brain scores attempts on — a SUBSET of the canonical single source (descent_axes.DESCENT_AXES), so brain
#: records never drift from the strategies / measurement harness (cost/tokens_in/llm_usage lower-better;
#: determinism/freshness higher-better). Validated against the canonical vocabulary at import.
AXES = ("cost", "determinism", "tokens_in", "llm_usage", "freshness")
assert all(is_axis(a) for a in AXES), "brain axes must be canonical descent_axes names"
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
    substrate_ref: str = ""           # the CONCRETE substrate row this descent selected INTO (model/source/skill) — lineage
    serves_truth: bool = False

    def attempt_id(self) -> str:
        body = json.dumps({"unit_id": self.unit_id, "strategy": self.strategy, "before": self.before,
                           "after": self.after, "outcome": self.outcome}, sort_keys=True)
        return "att_" + hashlib.sha256(body.encode()).hexdigest()[:16]


def _reward(before: dict, after: dict) -> dict:
    """Computed deltas (the training reward signal) — derived GENERICALLY from the canonical axis directions, so a new
    axis needs no new code: lower-is-better axes report *_saved (before-after); higher-is-better report *_gain."""
    r: dict = {}
    for axis in AXES:
        b, a = before.get(axis, 0.0), after.get(axis, 0.0)
        if axis in LOWER_IS_BETTER_AXES:
            r[f"{axis}_saved"] = round(b - a, 6)
        else:
            r[f"{axis}_gain"] = round(a - b, 6)
    return r


class DescentAttemptStore:
    """Append-only JSONL store of descent attempts; idempotent by attempt_id; lossless (keeps negatives)."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self._store = None   # lazily-opened backend-swappable append-only store (record_store)

    def _open(self):
        """Open the append-only store behind the JSONL durability contract: SQLite-WAL primary + a
        durable JSONL mirror via src.teleon.storage.record_store, with O(1) content-addressed
        idempotency. Lazy so merely constructing the store never creates an index file. The storage
        backend is a CONFIG choice (architecture/storage_tier_policy.json: descent_attempts -> history
        tier) — local sqlite_wal now, the warehouse swap for the trillion-row scale, no caller change."""
        if self._store is None:
            from src.teleon.storage.record_store import LocalRecordStore
            self._store = LocalRecordStore(self.path)
        return self._store

    def all(self) -> list[dict]:
        if self._store is None and not self.path.exists():
            return []
        return self._open().all()

    def append(self, attempt: DescentAttempt) -> dict:
        """Append an attempt; IDEMPOTENT by content-hash attempt_id — an O(1) INDEXED dedupe (no O(n)
        full-file rescan), so the brain scales to billions of attempts. The durable JSONL mirror is
        preserved (lossless); failures/losers are kept as training negatives."""
        if attempt.outcome not in OUTCOMES:
            raise ValueError(f"unknown outcome {attempt.outcome!r}")
        bad = sorted({k for k in (*attempt.before, *attempt.after) if not is_axis(k)})
        if bad:
            raise ValueError(f"non-canonical axis keys {bad} — use descent_axes names (single source)")
        rec = asdict(attempt)
        rec["attempt_id"] = attempt.attempt_id()
        rec["reward"] = _reward(attempt.before, attempt.after)
        rec["success"] = attempt.outcome in _SUCCESS
        self._open().append(rec, idem_key=rec["attempt_id"])   # O(1) idempotent (was an O(n) rescan)
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
