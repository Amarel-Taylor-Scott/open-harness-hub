"""src.teleon.ports.reward_provider — the SHARED REWARD-PROVIDER port (canonical TELEON home).

A reward provider SCORES one environment run against a declared :data:`RewardSpec` and returns a
``RewardResult``-shaped dict (see ``schemas/environments/RewardResult.v1``). Deterministic checkers are
preferred (``deterministic=True``); test runners / diff oracles are candidates behind the same port.

THE INVARIANT: **a reward result is EVIDENCE, never authority.** Every result carries ``is_truth=False``
(pinned const false by the schema) — a number + a per-check breakdown, scored deterministically against a
declared ruler. The ruler never makes the agent output true; ``passed`` is a convenience verdict only.

Teleon-owned: stdlib only; deterministic when ``now`` is injected (content-addressed ids; no RNG / wall-clock).
Never imports Baltor.
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable

#: pinned False on every reward result — THE INVARIANT, made a constant the proofs assert.
REWARD_IS_TRUTH = False


@runtime_checkable
class RewardProviderPort(Protocol):
    """One scorer the spine MAY route a RewardSpec to.

    ``score`` takes the ``EnvironmentRunResult``-shaped ``run_result`` dict + the ``RewardSpec``-shaped
    ``reward_spec`` dict and the injected ``now`` and returns a ``RewardResult``-shaped dict
    (``is_truth=False``). ``deterministic`` flags whether the scorer yields the SAME result for the same
    input+output (preferred — non-deterministic scorers are advisory only)."""
    provider_id: str
    deterministic: bool

    def score(self, run_result: dict, reward_spec: dict, *, now: str) -> dict:
        """Score ``run_result`` against ``reward_spec`` and return a RewardResult dict."""
        ...


__all__ = ["RewardProviderPort", "REWARD_IS_TRUTH"]
