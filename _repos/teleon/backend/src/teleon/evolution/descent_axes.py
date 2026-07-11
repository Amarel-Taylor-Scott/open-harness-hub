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
from scripts._repo_paths import resource as _resource

import json
from pathlib import Path

_STRATEGY_REGISTRY_PATH = _resource("architecture") / "descent_strategy_registry.json"

#: the canonical descent axes — name -> (direction, unit, what improving it means). Single source of truth.
#: Add an axis here + a strategy in _repos/shared-backend-components/architecture/descent_strategy_registry.json and the generic descender + the
#: measurement harness pick it up automatically — no other code change.
DESCENT_AXES = {
    # ── efficiency / correctness (the first wave) ──
    "determinism": {"direction": "higher", "unit": "0..1", "meaning": "non-deterministic -> deterministic"},
    "cost": {"direction": "lower", "unit": "relative/call", "meaning": "expensive -> cheaper"},
    "latency": {"direction": "lower", "unit": "ms", "meaning": "slow -> faster (speed)"},
    "llm_usage": {"direction": "lower", "unit": "model calls", "meaning": "more -> fewer LLM/agent calls"},
    "tokens_in": {"direction": "lower", "unit": "input tokens/call",
                  "meaning": "smaller prompt/context/skill -> fewer INPUT tokens (compress the prompt, even a skill)"},
    "tokens_out": {"direction": "lower", "unit": "output tokens/call",
                   "meaning": "more concise output -> fewer OUTPUT tokens"},
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

#: fragile-context volatility_class (stable|low|medium|high|realtime — from _repos/shared-backend-components/architecture/fragile_context_taxonomy.json)
#: -> the sync cadence that keeps the capability current. e.g. monthly-changing regulations => 'monthly'.
_VOLATILITY_SYNC_CADENCE = {
    "realtime": "continuous", "high": "daily", "medium": "weekly", "low": "monthly", "stable": "on_change_only",
}
_DEFAULT_CADENCE = "weekly"


def is_axis(name: str) -> bool:
    return name in DESCENT_AXES


def _strategy_list(registry: dict | None = None) -> list:
    data = registry if registry is not None else json.loads(_STRATEGY_REGISTRY_PATH.read_text(encoding="utf-8"))
    return list(data.get("strategies", []))


def descent_strategies(*, registry: dict | None = None) -> dict:
    """The PRIMARY descent strategy per axis (first registered wins). Config, not code — the single source of the
    fork mechanism per axis. (An axis may have multiple strategies; use all_descent_strategies / descent_strategy
    to reach alternates like formal_proof_verification.)"""
    out: dict = {}
    for s in _strategy_list(registry):
        out.setdefault(s["axis"], s)
    return out


def all_descent_strategies(*, registry: dict | None = None) -> dict:
    """Every descent strategy keyed by strategy_id (supports multiple strategies per axis)."""
    return {s["strategy_id"]: s for s in _strategy_list(registry)}


def descent_strategy(strategy_id: str, *, registry: dict | None = None) -> dict:
    """One descent strategy by id (e.g. 'formal_proof_verification'). Raises on an unknown id — never a silent pick."""
    strategies = all_descent_strategies(registry=registry)
    if strategy_id not in strategies:
        raise KeyError(f"unknown descent strategy {strategy_id!r}; have: {sorted(strategies)}")
    return strategies[strategy_id]


def strategies_for_axis(axis: str, *, registry: dict | None = None) -> list:
    """All strategies registered for an axis (e.g. verifiability -> [receipt_binding, formal_proof_verification])."""
    return [s for s in _strategy_list(registry) if s["axis"] == axis]


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
