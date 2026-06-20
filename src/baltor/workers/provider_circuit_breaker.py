"""src.baltor.workers.provider_circuit_breaker — per-provider CIRCUIT BREAKER (C-FLEET-2).

States: closed → (failures) → open → (after open_seconds) → half_open → (probe ok) → closed
                                                            → (probe fails) → open

Opens on any of: consecutive failures ≥ threshold, failure rate over a window > threshold, timeout rate >
threshold, or a forced signal (provider health-check failed / rate-limited). While open it rejects work so
the fleet routes to a fallback provider; after a cooldown it admits a few probes (half_open). Deterministic
(injected `now`; bounded sliding window). Whether a failure counts toward opening is taken from the
failure taxonomy.
"""
from __future__ import annotations

from collections import deque

from .failure_taxonomy import opens_circuit
from .fleet_ledger import _age_s

CLOSED, OPEN, HALF_OPEN = "closed", "open", "half_open"

# defaults — single source; overridable per provider
_CONSEC_THRESHOLD = 5
_RATE_THRESHOLD = 0.5
_TIMEOUT_RATE_THRESHOLD = 0.5
_WINDOW = 20
_OPEN_SECONDS = 60
_HALF_OPEN_PROBES = 2


class CircuitBreaker:
    def __init__(self, provider_id: str, *, consec_threshold: int = _CONSEC_THRESHOLD,
                 rate_threshold: float = _RATE_THRESHOLD, timeout_rate_threshold: float = _TIMEOUT_RATE_THRESHOLD,
                 window: int = _WINDOW, open_seconds: int = _OPEN_SECONDS, half_open_probes: int = _HALF_OPEN_PROBES):
        self.provider_id = provider_id
        self.consec_threshold = consec_threshold
        self.rate_threshold = rate_threshold
        self.timeout_rate_threshold = timeout_rate_threshold
        self.window = window
        self.open_seconds = open_seconds
        self.half_open_probes = half_open_probes
        self._outcomes: deque = deque(maxlen=window)   # "success" | "failure" | "timeout"
        self._consec = 0
        self._state = CLOSED
        self._opened_at: str | None = None
        self._probes = 0

    def state(self, *, now: str) -> str:
        """Current state, advancing open→half_open once the cooldown has elapsed."""
        if self._state == OPEN and self._opened_at and _age_s(self._opened_at, now) >= self.open_seconds:
            self._state = HALF_OPEN
            self._probes = 0
        return self._state

    def allow(self, *, now: str) -> bool:
        """May a request go to this provider right now?"""
        st = self.state(now=now)
        if st == CLOSED:
            return True
        if st == HALF_OPEN:
            if self._probes < self.half_open_probes:
                self._probes += 1
                return True
            return False
        return False  # open

    def _rate(self, kind: str) -> float:
        if not self._outcomes:
            return 0.0
        return sum(1 for o in self._outcomes if o == kind) / len(self._outcomes)

    def record_success(self, *, now: str) -> None:
        self._outcomes.append("success")
        self._consec = 0
        if self.state(now=now) == HALF_OPEN:
            self._state = CLOSED          # a successful probe closes the circuit
            self._opened_at = None

    def record_failure(self, failure_type: str, *, now: str, timeout: bool = False) -> None:
        self._outcomes.append("timeout" if timeout else "failure")
        # only failures the taxonomy marks as opens_circuit count toward tripping
        if not opens_circuit(failure_type):
            return
        self._consec += 1
        if self.state(now=now) == HALF_OPEN:
            self._trip(now)               # a failed probe re-opens immediately
            return
        full = len(self._outcomes) >= self.window
        if (self._consec >= self.consec_threshold
                or (full and self._rate("failure") + self._rate("timeout") > self.rate_threshold)
                or (full and self._rate("timeout") > self.timeout_rate_threshold)):
            self._trip(now)

    def force_open(self, *, now: str) -> None:
        """Forced open from a health-check failure or rate-limit signal."""
        self._trip(now)

    def _trip(self, now: str) -> None:
        self._state = OPEN
        self._opened_at = now
        self._probes = 0


__all__ = ["CircuitBreaker", "CLOSED", "OPEN", "HALF_OPEN"]
