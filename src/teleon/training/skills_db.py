"""src.teleon.training.skills_db — the SKILLS / DISTILLATION DATABASE: the queryable store + training dataset
of capabilities and how each was (or should be) distilled toward determinism.

Each capability becomes a feature row; each distillation outcome (a DistillationRecord) becomes the LABEL. The
join is the supervised dataset a policy/model/LoRA trains on to learn the most efficient non-deterministic ->
deterministic path. This module builds + splits + exports + queries that dataset. Pure + deterministic (a
content-hash split, no clock/RNG); Teleon-layer — never imports src.baltor; a dataset row is evidence, never truth.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from src.teleon.evolution.meta_learner import determinism_band

#: the feature names a policy/model learns from (a capability's model-independent descriptors).
FEATURE_KEYS = ("category", "determinism_band", "determinism_ceiling", "deterministic_coverage_estimate",
                "source_kind", "intent_tokens")


def feature_vector(candidate: dict) -> dict:
    """Model-independent features for a capability candidate (what a distillation policy generalizes over)."""
    intent = str(candidate.get("intent", ""))
    src = candidate.get("source") if isinstance(candidate.get("source"), dict) else {}
    dc = float(candidate.get("determinism_ceiling", 0.0))
    return {
        "category": candidate.get("category", "other"),
        "determinism_band": determinism_band(dc),
        "determinism_ceiling": dc,
        "deterministic_coverage_estimate": float(candidate.get("deterministic_coverage_estimate", 0.0)),
        "source_kind": src.get("kind") or candidate.get("source_kind", "other"),
        "intent_tokens": len(intent.split()),
    }


@dataclass(frozen=True)
class DistillationExample:
    """One training row: a capability's features + (if distilled) its outcome label. ``label_strategy`` is the
    distillation strategy that was applied; ``efficiency`` is the coverage-saving per distill-cost (the target to
    maximize). ``labeled`` is False for capabilities not yet distilled (features-only, for prediction)."""
    capability_slot: str
    features: dict
    labeled: bool
    label_strategy: str = ""
    coverage: float = 0.0
    efficiency: float = 0.0

    def as_dict(self) -> dict:
        return {"capability_slot": self.capability_slot, "features": self.features, "labeled": self.labeled,
                "label_strategy": self.label_strategy, "coverage": self.coverage, "efficiency": self.efficiency}


def _efficiency(rec: dict) -> float:
    saving = float(rec.get("coverage", 0.0)) * (float(rec.get("per_call_cost_before", 0.0))
                                                - float(rec.get("per_call_cost_after", 0.0)))
    return saving / (float(rec.get("distill_cost", 0.0)) or 1e-9)


def build_dataset(candidates: list[dict], records: list[dict]) -> "DistillationDataset":
    """Join capability features with their distillation outcomes into a dataset. A capability with a record is a
    LABELED example (features -> the applied strategy); one without is an unlabeled (prediction) example."""
    rec_by_slot = {r["capability_slot"]: r for r in records if r.get("applied")}
    examples = []
    for c in candidates:
        slot = c["capability_slot"]
        feats = feature_vector(c)
        r = rec_by_slot.get(slot)
        if r is not None:
            examples.append(DistillationExample(slot, feats, True, r["strategy"], float(r.get("coverage", 0.0)),
                                                round(_efficiency(r), 6)))
        else:
            examples.append(DistillationExample(slot, feats, False))
    return DistillationDataset(examples)


class DistillationDataset:
    """A built dataset of DistillationExamples with deterministic train/holdout split, export, and class queries."""

    def __init__(self, examples: list[DistillationExample]) -> None:
        self.examples = list(examples)

    @property
    def labeled(self) -> list[DistillationExample]:
        return [e for e in self.examples if e.labeled]

    def split(self, *, holdout_fraction: float = 0.25):
        """Deterministic split of the LABELED examples by content hash (no RNG): the same dataset always splits the
        same way, so training is reproducible. Returns (train, holdout)."""
        train, holdout = [], []
        for e in self.labeled:
            h = int(hashlib.sha256(e.capability_slot.encode("utf-8")).hexdigest()[:8], 16) / 0xFFFFFFFF
            (holdout if h < holdout_fraction else train).append(e)
        return train, holdout

    def by_class(self) -> dict:
        """Labeled examples grouped by class (category|band) — the skills-DB view used to read the best path."""
        out: dict = {}
        for e in self.labeled:
            out.setdefault(f"{e.features['category']}|{e.features['determinism_band']}", []).append(e)
        return out

    def export_jsonl(self, path: str | Path) -> int:
        """Write the dataset as portable JSONL training data (one example per line). Returns the row count."""
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("w", encoding="utf-8") as fh:
            for e in self.examples:
                fh.write(json.dumps(e.as_dict(), sort_keys=True, ensure_ascii=False) + "\n")
        return len(self.examples)

    def summary(self) -> dict:
        return {"total": len(self.examples), "labeled": len(self.labeled), "classes": len(self.by_class()),
                "feature_keys": list(FEATURE_KEYS), "serves_truth": False}
