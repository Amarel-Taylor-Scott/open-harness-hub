#!/usr/bin/env python3
"""contracts/artifacts/fragility_metadata — how perishable a fact is, and when it must be re-verified.

``FragilityMetadata`` is the freshness contract the C40 verification gate reads (see
``scripts.runtime.verification_gate._stale``): a fact is stale once ``now`` passes its refresh horizon. The
horizon is ``next_verify_at`` (an injected absolute epoch) OR derived from ``last_verified_at + ttl_seconds``;
``volatility_class`` ('stable' or ``no_refresh=True`` never go stale). Every fragile fact MUST carry
``last_verified_at`` + a horizon (``next_verify_at`` OR ``ttl_seconds``) + ``watch_policy_id``. Deterministic +
offline: ``fragility_id`` is content-addressed; all times are injected ints.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

#: how fast a fact decays. Drives the watch cadence; 'stable' / no_refresh never expire.
VOLATILITY_CLASSES = ("stable", "low", "medium", "high", "realtime")


def _content_id(prefix: str, body: dict) -> str:
    return prefix + "-" + hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()[:16]


@dataclass(frozen=True)
class FragilityMetadata:
    fact_id: str
    volatility_class: str           # one of VOLATILITY_CLASSES
    last_verified_at: int           # injected epoch seconds — never wall-clock
    watch_policy_id: str
    next_verify_at: int | None = None
    ttl_seconds: int | None = None
    no_refresh: bool = False        # immutable / demo-fixture facts never go stale
    conflict_prone: bool = False
    decay_signal: str = ""          # why it decays (e.g. 'regulatory_amendment', 'fee_schedule_change')

    def __post_init__(self) -> None:
        if self.volatility_class not in VOLATILITY_CLASSES:
            raise ValueError(f"volatility_class {self.volatility_class!r} not in {VOLATILITY_CLASSES}")
        if not self.watch_policy_id:
            raise ValueError("watch_policy_id is required")
        # a refreshable fragile fact MUST declare a horizon; immutable/stable facts are exempt.
        exempt = self.no_refresh or self.volatility_class == "stable"
        if not exempt and self.next_verify_at is None and self.ttl_seconds is None:
            raise ValueError("a refreshable fragile fact needs next_verify_at OR ttl_seconds")

    @property
    def fragility_id(self) -> str:
        return _content_id("frag", {"f": self.fact_id, "vc": self.volatility_class,
                                    "lva": self.last_verified_at, "nva": self.next_verify_at,
                                    "ttl": self.ttl_seconds, "nr": self.no_refresh, "wp": self.watch_policy_id})

    def horizon(self) -> int | None:
        """The absolute epoch at which this fact goes stale, or None if it never does."""
        if self.no_refresh or self.volatility_class == "stable":
            return None
        if self.next_verify_at is not None:
            return self.next_verify_at
        if self.ttl_seconds is not None:
            return self.last_verified_at + self.ttl_seconds
        return None

    def is_stale(self, now: int) -> bool:
        h = self.horizon()
        return h is not None and now > h

    def to_dict(self) -> dict:
        # NOTE: this dict IS the ``fragility`` shape the C40 gate's _stale() reads (no_refresh / volatility_class
        # / next_verify_at / last_verified_at / ttl_seconds). Keep keys aligned with verification_gate._stale.
        return {"schema_version": "FragilityMetadata.v1", "fragility_id": self.fragility_id,
                "fact_id": self.fact_id, "volatility_class": self.volatility_class,
                "last_verified_at": self.last_verified_at, "next_verify_at": self.next_verify_at,
                "ttl_seconds": self.ttl_seconds, "no_refresh": self.no_refresh,
                "watch_policy_id": self.watch_policy_id, "conflict_prone": self.conflict_prone,
                "decay_signal": self.decay_signal}
