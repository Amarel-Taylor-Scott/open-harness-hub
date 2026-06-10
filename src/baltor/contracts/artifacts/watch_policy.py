#!/usr/bin/env python3
"""contracts/artifacts/watch_policy — the re-verification CADENCE + escalation rule for a class of facts.

A ``WatchPolicy`` says HOW OFTEN a fact of a given volatility must be re-verified, whether a conflict forces
human review, and whether the fact is immutable (``no_refresh`` — demo fixtures / settled-law constants).
The classifier recommends one of these per fact; FragilityMetadata then carries its id. Deterministic +
offline: ``watch_policy_id`` is content-addressed; ``refresh_interval_seconds`` is a plain int.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from src.baltor.contracts.artifacts.fragility_metadata import VOLATILITY_CLASSES


def _content_id(prefix: str, body: dict) -> str:
    return prefix + "-" + hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()[:16]


@dataclass(frozen=True)
class WatchPolicy:
    name: str
    volatility_class: str           # one of VOLATILITY_CLASSES this policy applies to
    refresh_interval_seconds: int   # how long a fact stays fresh under this policy (0 when no_refresh)
    no_refresh: bool = False        # immutable / demo source — fact never goes stale
    escalate_on_conflict: bool = False  # a contested refresh routes to human review (needs_human)
    max_staleness_seconds: int = 0  # 0 == no hard cap beyond the refresh interval

    def __post_init__(self) -> None:
        if self.volatility_class not in VOLATILITY_CLASSES:
            raise ValueError(f"volatility_class {self.volatility_class!r} not in {VOLATILITY_CLASSES}")
        if not self.no_refresh and self.refresh_interval_seconds <= 0:
            raise ValueError("a refreshable policy needs refresh_interval_seconds > 0")

    @property
    def watch_policy_id(self) -> str:
        return _content_id("wp", {"n": self.name, "vc": self.volatility_class,
                                  "ri": self.refresh_interval_seconds, "nr": self.no_refresh,
                                  "esc": self.escalate_on_conflict, "max": self.max_staleness_seconds})

    def next_verify_at(self, last_verified_at: int) -> int | None:
        """The absolute epoch the fact is due for re-verification, or None for immutable facts."""
        if self.no_refresh:
            return None
        return last_verified_at + self.refresh_interval_seconds

    def to_dict(self) -> dict:
        return {"schema_version": "WatchPolicy.v1", "watch_policy_id": self.watch_policy_id, "name": self.name,
                "volatility_class": self.volatility_class, "refresh_interval_seconds": self.refresh_interval_seconds,
                "no_refresh": self.no_refresh, "escalate_on_conflict": self.escalate_on_conflict,
                "max_staleness_seconds": self.max_staleness_seconds}
