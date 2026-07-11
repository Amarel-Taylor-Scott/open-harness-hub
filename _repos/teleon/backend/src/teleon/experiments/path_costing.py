"""src/teleon/experiments/path_costing — relative-cost estimate for a path, from the pricebook CONFIG.

The cost of running a path is NOT hardcoded in business logic: it is read from
``_repos/shared-backend-components/architecture/execution_backend_pricebook.json`` (CONFIG, single source of cost — see CLAUDE.md "No Magic
Values"). ``estimate(...)`` returns a ``PathCostReport`` dict carrying the pricebook-derived relative
cost, the ``pricebook_version`` it was computed from (reproducibility), and the per-entry ``confidence``
(a 'low' placeholder price must never silently drive a production decision).

Pure + deterministic: the pricebook bytes and ``now`` are injected; the only formula is
``estimated_cost = request_cost + duration_cost_per_s*estimated_duration_s + idle_cost_per_s*estimated_idle_s``.

Canonical TELEON home (experiments layer); imports its ids leaf from Teleon — never Baltor. Baltor re-exports
this via a shim at _repos/baltor/backend/src/baltor/experiments/path_costing.py.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import json
from pathlib import Path
from typing import Any

from .ids import canonical_id

#: repo root = .../src/teleon/experiments/path_costing.py -> parents[3] (same depth as the former baltor home).
_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[3])
#: the single source of execution-backend cost (CONFIG, never a parallel literal in code).
PRICEBOOK_PATH = _resource("architecture") / "execution_backend_pricebook.json"

SCHEMA_VERSION = "PathCostReport"
#: the pricebook pins this; cost reports mirror it (the validator enum-bounds it).
COST_CURRENCY = "relative-unit"


def load_pricebook(*, pricebook_bytes: bytes | None = None) -> dict[str, Any]:
    """Return the pricebook dict. ``pricebook_bytes`` may be injected (tests/offline); otherwise read CONFIG."""
    raw = pricebook_bytes if pricebook_bytes is not None else PRICEBOOK_PATH.read_bytes()
    return json.loads(raw)


def estimate(
    *,
    path_id: str,
    capability_slot: str,
    backend_id: str,
    estimated_duration_s: float,
    now: str,
    estimated_idle_s: float = 0.0,
    baseline_cost: float | None = None,
    pricebook: dict[str, Any] | None = None,
    pricebook_bytes: bytes | None = None,
) -> dict[str, Any]:
    """Relative-cost ``PathCostReport`` for a path on ``backend_id``, from the pricebook CONFIG.

    The pricebook is the single source of cost: ``request_cost``, ``duration_cost_per_s``,
    ``idle_cost_per_s`` and ``confidence`` are carried straight from the named backend entry — never typed
    into this code. ``estimated_cost`` is the documented formula. ``cost_delta_vs_baseline`` (when
    ``baseline_cost`` is supplied) is the number the promotion cost gate reads. ``now`` is injected.
    """
    pb = pricebook if pricebook is not None else load_pricebook(pricebook_bytes=pricebook_bytes)
    backends = pb.get("backends", {})
    if backend_id not in backends:
        raise KeyError(f"backend_id {backend_id!r} not in pricebook (config is the single source of cost)")
    entry = backends[backend_id]
    request_cost = float(entry["request_cost"])
    duration_cost_per_s = float(entry["duration_cost_per_s"])
    idle_cost_per_s = float(entry["idle_cost_per_s"])
    confidence = entry["confidence"]  # enum-bounded {high,low} by the schema; carried straight from config.

    estimated_cost = (
        request_cost
        + duration_cost_per_s * float(estimated_duration_s)
        + idle_cost_per_s * float(estimated_idle_s)
    )

    report: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "report_id": canonical_id(
            "pcost",
            path_id,
            capability_slot,
            backend_id,
            pb.get("version", ""),
            f"{estimated_duration_s}",
            f"{estimated_idle_s}",
        ),
        "path_id": path_id,
        "capability_slot": capability_slot,
        "backend_id": backend_id,
        "pricebook_version": pb.get("version", ""),
        "currency": COST_CURRENCY,
        "request_cost": request_cost,
        "duration_cost_per_s": duration_cost_per_s,
        "idle_cost_per_s": idle_cost_per_s,
        "estimated_duration_s": float(estimated_duration_s),
        "estimated_idle_s": float(estimated_idle_s),
        "estimated_cost": estimated_cost,
        "confidence": confidence,
        "estimated_at": now,
    }
    if baseline_cost is not None:
        report["cost_delta_vs_baseline"] = estimated_cost - float(baseline_cost)
    return report
