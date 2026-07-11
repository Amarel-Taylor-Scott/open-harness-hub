"""src.baltor.workers.failure_taxonomy — loader for _repos/shared-backend-components/architecture/worker_failure_taxonomy.json.

Single source for: is a failure retryable? does it open a provider circuit? what records must it emit?
Imported by the circuit breaker, the telemetry roll-up, and the redteam proof. `unknown` is the safe
default for any unclassified error (retryable=false → never loops forever).
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import json
from functools import lru_cache
from pathlib import Path

_PATH = _resource("architecture") / "worker_failure_taxonomy.json"


@lru_cache(maxsize=1)
def _taxonomy() -> dict:
    data = json.loads(_PATH.read_text())
    return {f["failure_type"]: f for f in data["failures"]}


def failure_types() -> set:
    return set(_taxonomy())


def failure_policy(failure_type: str) -> dict:
    """Return the taxonomy entry for a failure type, falling back to `unknown` for anything unclassified."""
    tax = _taxonomy()
    return tax.get(failure_type, tax["unknown"])


def is_retryable(failure_type: str) -> bool:
    return bool(failure_policy(failure_type).get("retryable", False))


def opens_circuit(failure_type: str) -> bool:
    return bool(failure_policy(failure_type).get("opens_circuit", False))


__all__ = ["failure_types", "failure_policy", "is_retryable", "opens_circuit"]
