"""src.baltor.workers.provider_fallback — contract-driven PROVIDER FALLBACK (C-FLEET-2).

For a capability with several providers sharing one input/output contract, route work to the first
provider whose circuit breaker allows it (primary first, then fallbacks). On failure, the breaker may
trip and the next request routes onward. Every result is stamped with the `provider_id` that produced
it. A single task selects exactly ONE provider per attempt — no duplicate side effects.

Deterministic (injected `now`). The provider ORDER is the only configuration; breakers are per provider.
"""
from __future__ import annotations

from .provider_circuit_breaker import CircuitBreaker


class FallbackRouter:
    def __init__(self, ordered_providers: list[str], **breaker_kwargs):
        if not ordered_providers:
            raise ValueError("FallbackRouter needs at least one provider")
        self.order = list(ordered_providers)
        self.breakers = {p: CircuitBreaker(p, **breaker_kwargs) for p in self.order}

    def select(self, *, now: str) -> str | None:
        """The first provider (primary → fallbacks) whose breaker currently admits work, or None
        (all providers' circuits are open → the supervisor should hold)."""
        for p in self.order:
            if self.breakers[p].allow(now=now):
                return p
        return None

    def record_success(self, provider_id: str, *, now: str) -> None:
        self.breakers[provider_id].record_success(now=now)

    def record_failure(self, provider_id: str, failure_type: str, *, now: str, timeout: bool = False) -> None:
        self.breakers[provider_id].record_failure(failure_type, now=now, timeout=timeout)

    def force_open(self, provider_id: str, *, now: str) -> None:
        self.breakers[provider_id].force_open(now=now)

    def states(self, *, now: str) -> dict:
        return {p: b.state(now=now) for p, b in self.breakers.items()}

    @staticmethod
    def mark_output(provider_id: str, output: dict) -> dict:
        """Stamp a result with the provider that produced it (provenance for fallback results)."""
        return {**output, "provider_id": provider_id}


__all__ = ["FallbackRouter"]
