"""src.teleon.evolution.descent_axes — the canonical DESCENT AXES + the freshness (anti-fragility) policy.

A capability can descend (improve) along several axes, not just toward determinism. This is the single source of
the axis vocabulary so strategies, records, and the measurement harness never drift:

  determinism  (higher better)  non-deterministic -> deterministic rule
  cost         (lower better)   expensive -> cheaper model/runtime/endpoint
  latency      (lower better)   slow -> faster (speed: cache/precompute/faster lane)        [the SPEED axis]
  llm_usage    (lower better)   more -> less LLM / lower context
  freshness    (higher better)  fragile/stale -> robust, auto-synced to the authoritative source (CDC re-ingest)

The freshness axis answers fragility: if a capability relies on facts that CHANGE (regulations, laws, fees,
rates, prices), descend it to a fork BOUND to the authoritative source with a sync cadence matched to how fast
the facts move (the fragile-context volatility_class) + a CDC re-heal trigger, so it always ingests the current
facts instead of going stale. Pure + deterministic; Teleon-layer — never imports src.baltor; never serves truth.
"""
from __future__ import annotations

import json
from pathlib import Path

_STRATEGY_REGISTRY_PATH = Path(__file__).resolve().parents[3] / "architecture" / "descent_strategy_registry.json"

#: the canonical descent axes — name -> (direction, unit, what improving it means). Single source of truth.
#: Add an axis here + a strategy in architecture/descent_strategy_registry.json and the generic descender + the
#: measurement harness pick it up automatically — no other code change.
DESCENT_AXES = {
    # ── efficiency / correctness (the first wave) ──
    "determinism": {"direction": "higher", "unit": "0..1", "meaning": "non-deterministic -> deterministic"},
    "cost": {"direction": "lower", "unit": "relative/call", "meaning": "expensive -> cheaper"},
    "latency": {"direction": "lower", "unit": "ms", "meaning": "slow -> faster (speed)"},
    "llm_usage": {"direction": "lower", "unit": "model calls/tokens", "meaning": "more -> less LLM / lower context"},
    "freshness": {"direction": "higher", "unit": "0..1 currency",
                  "meaning": "fragile/stale -> robust, auto-synced to the authoritative source"},
    # ── trust / robustness (the second wave) ──
    "verifiability": {"direction": "higher", "unit": "0..1 provenance",
                      "meaning": "unverified -> every output carries source handles + a lineage receipt"},
    "reliability": {"direction": "higher", "unit": "0..1 / #providers",
                    "meaning": "single fragile provider -> multi-provider failover (redundancy)"},
    "locality": {"direction": "higher", "unit": "0..1 sovereignty",
                 "meaning": "external egress -> local/on-prem (data sovereignty, air-gap)"},
    "specialization": {"direction": "higher", "unit": "0..1 narrowness",
                       "meaning": "general frontier model -> a narrow specialized small model / LoRA"},
    "privacy": {"direction": "higher", "unit": "0..1",
                "meaning": "PII-exposing -> redacted / tokenized / synthetic-safe"},
    # ── durability / openness (newly proposed) ──
    "reproducibility": {"direction": "higher", "unit": "0..1",
                        "meaning": "non-reproducible -> pinned + versioned + replayable (same input+version -> same output)"},
    "portability": {"direction": "higher", "unit": "0..1",
                    "meaning": "vendor-locked -> portable / open-format (OKF, no lock-in)"},
    "resilience": {"direction": "higher", "unit": "0..1",
                   "meaning": "brittle -> self-healing (auto-recovers from breaks, not just source change)"},
    "energy": {"direction": "lower", "unit": "relative kWh/call",
               "meaning": "high-energy -> low-energy / green compute (local CPU, small model, cached)"},
    "safety": {"direction": "higher", "unit": "0..1 least-privilege",
               "meaning": "ungated -> least-privilege, sandboxed, policy-bounded"},
}
LOWER_IS_BETTER_AXES = tuple(a for a, m in DESCENT_AXES.items() if m["direction"] == "lower")
HIGHER_IS_BETTER_AXES = tuple(a for a, m in DESCENT_AXES.items() if m["direction"] == "higher")

#: fragile-context volatility_class (stable|low|medium|high|realtime — from architecture/fragile_context_taxonomy.json)
#: -> the sync cadence that keeps the capability current. e.g. monthly-changing regulations => 'monthly'.
_VOLATILITY_SYNC_CADENCE = {
    "realtime": "continuous", "high": "daily", "medium": "weekly", "low": "monthly", "stable": "on_change_only",
}
_DEFAULT_CADENCE = "weekly"


def is_axis(name: str) -> bool:
    return name in DESCENT_AXES


def descent_strategies(*, registry: dict | None = None) -> dict:
    """The descent-strategy registry keyed by axis (the fork mechanism per axis — single source, config not code)."""
    data = registry if registry is not None else json.loads(_STRATEGY_REGISTRY_PATH.read_text(encoding="utf-8"))
    return {s["axis"]: s for s in data.get("strategies", [])}


def improves(axis: str, before: float, after: float) -> bool:
    """True if going before->after is an improvement on ``axis`` (respecting its direction). Used by the harness."""
    if axis not in DESCENT_AXES:
        raise KeyError(f"unknown descent axis {axis!r}; known: {sorted(DESCENT_AXES)}")
    return (after < before) if DESCENT_AXES[axis]["direction"] == "lower" else (after > before)


def freshness_policy(volatility_class: str) -> dict:
    """The robustness/freshness binding for a capability whose facts change: a sync CADENCE matched to its
    volatility, a CDC re-heal trigger (on a 'changed'/'new' source event -> re-ingest + re-verify via
    src.teleon.self_healing), and the requirement to bind an AUTHORITATIVE source. Higher volatility => tighter
    cadence (regulations that change monthly -> 'monthly'; live rates -> 'continuous')."""
    cadence = _VOLATILITY_SYNC_CADENCE.get(volatility_class, _DEFAULT_CADENCE)
    return {
        "volatility_class": volatility_class,
        "sync_cadence": cadence,
        "cdc_reheal": True,            # a freshness CDC 'changed' event triggers self_healing.reheal_on_source_change
        "authoritative_source_required": True,
        "stale_behavior": "hold_out",  # serve nothing stale — held out until re-synced (the lossless held-out status)
        "serves_truth": False,
    }
