#!/usr/bin/env python3
"""Backs `processor/offline-fallback-gate` (process_kind ``gate.cost_ceiling``).

If-Statement gate: check connectivity (DNS/HTTP probe via an INJECTED prober
— the gate never owns sockets) and, when offline, rewrite the pipeline step
to consume the local Knowledge Corpus instead of the cloud call. Emits an
explicit ``gate_decision`` so downstream processors and audit logs always
know which path ran. The prober is ``probe(host, timeout_ms) ->
{"reached": bool, "latency_ms": float}``; without one the gate REFUSES —
a connectivity verdict is never guessed.

Contract: deterministic given the injected probe; side_effects=read;
on_error=raise. Inputs probe_host, probe_timeout_ms, online_step_ref,
offline_corpus_ref → gate_decision, selected_step_ref, latency_ms,
probe_host_reached.

CLI / self-test: python3 scripts/processors/offline_fallback_gate.py
"""
from __future__ import annotations

import json
from typing import Any, Callable

# ── Constants (No-Magic-Values) ───────────────────────────────────────────────

DECISION_ONLINE = "online"
DECISION_OFFLINE = "offline"

#: Default probe timeout: long enough for rural links, short enough that the
#: gate itself never becomes the latency problem.
DEFAULT_PROBE_TIMEOUT_MS = 2000

#: A reachable host slower than this still gates OFFLINE — a link that slow
#: will time out the real call anyway; the local corpus is the better path.
MAX_USABLE_LATENCY_MS = 1500


def run(*, probe_host: str, online_step_ref: str, offline_corpus_ref: str,
        probe_timeout_ms: int = DEFAULT_PROBE_TIMEOUT_MS,
        probe: Callable[[str, int], dict[str, Any]] | None = None) -> dict[str, Any]:
    """Probe connectivity via the injected prober; pick the step to run."""
    if not isinstance(probe_host, str) or not probe_host:
        raise ValueError("probe_host must be a non-empty hostname")
    if not isinstance(online_step_ref, str) or not online_step_ref:
        raise ValueError("online_step_ref must be a non-empty step reference")
    if not isinstance(offline_corpus_ref, str) or not offline_corpus_ref:
        raise ValueError("offline_corpus_ref must be a non-empty corpus reference")
    if not isinstance(probe_timeout_ms, int) or probe_timeout_ms < 1:
        raise ValueError(f"probe_timeout_ms must be a positive int, got {probe_timeout_ms!r}")
    if probe is None:
        raise RuntimeError("offline_fallback_gate requires an injected prober "
                           "(probe=(host, timeout_ms) -> {'reached', 'latency_ms'}); "
                           "a connectivity verdict is never guessed")
    result = probe(probe_host, probe_timeout_ms)
    if not isinstance(result, dict) or "reached" not in result:
        raise ValueError("prober returned no reached flag — malformed probe result")
    reached = bool(result["reached"])
    latency = float(result.get("latency_ms", probe_timeout_ms))
    online = reached and latency <= MAX_USABLE_LATENCY_MS
    decision = DECISION_ONLINE if online else DECISION_OFFLINE
    return {"gate_decision": decision,
            "selected_step_ref": online_step_ref if online else offline_corpus_ref,
            "latency_ms": latency,
            "probe_host_reached": reached,
            "rationale": ("link usable" if online else
                          ("host unreachable" if not reached else
                           f"latency {latency}ms > usable ceiling {MAX_USABLE_LATENCY_MS}ms")),
            "audit": {"probe_host": probe_host, "probe_timeout_ms": probe_timeout_ms,
                      "usable_latency_ceiling_ms": MAX_USABLE_LATENCY_MS}}


def _selftest() -> None:
    args = {"probe_host": "api.example.com", "online_step_ref": "step://cloud-translate",
            "offline_corpus_ref": "corpus://local-alert-templates"}
    # Healthy link → online step.
    on = run(**args, probe=lambda h, t: {"reached": True, "latency_ms": 80.0})
    assert on["gate_decision"] == DECISION_ONLINE
    assert on["selected_step_ref"] == "step://cloud-translate" and on["probe_host_reached"] is True
    # Unreachable → offline corpus, with the reason on the audit trail.
    off = run(**args, probe=lambda h, t: {"reached": False, "latency_ms": 2000.0})
    assert off["gate_decision"] == DECISION_OFFLINE
    assert off["selected_step_ref"] == "corpus://local-alert-templates"
    assert off["rationale"] == "host unreachable"
    # Reachable but unusably slow ALSO gates offline (the latency ceiling).
    slow = run(**args, probe=lambda h, t: {"reached": True, "latency_ms": 1800.0})
    assert slow["gate_decision"] == DECISION_OFFLINE and "ceiling" in slow["rationale"]
    # Boundary: exactly the ceiling is usable.
    edge = run(**args, probe=lambda h, t: {"reached": True, "latency_ms": float(MAX_USABLE_LATENCY_MS)})
    assert edge["gate_decision"] == DECISION_ONLINE
    # The decision is always explicit for the audit log.
    assert {on["gate_decision"], off["gate_decision"]} == {DECISION_ONLINE, DECISION_OFFLINE}
    assert on["audit"]["probe_host"] == "api.example.com"
    # Refusals: no prober, malformed probe result, bad args.
    for bad in (lambda: run(**args),
                lambda: run(**args, probe=lambda h, t: {"latency_ms": 5}),
                lambda: run(probe_host="", online_step_ref="s", offline_corpus_ref="c",
                            probe=lambda h, t: {"reached": True})):
        raised = False
        try:
            bad()
        except (RuntimeError, ValueError):
            raised = True
        assert raised
    # Deterministic given the same scripted probe.
    assert json.dumps(run(**args, probe=lambda h, t: {"reached": True, "latency_ms": 80.0}), sort_keys=True) == \
           json.dumps(run(**args, probe=lambda h, t: {"reached": True, "latency_ms": 80.0}), sort_keys=True)
    print("PASS — offline_fallback_gate: injected prober (verdicts never guessed), "
          "explicit online/offline decision with audit rationale, slow-link-counts-"
          "as-offline ceiling, step rewrite to the local corpus verified")


if __name__ == "__main__":
    _selftest()
