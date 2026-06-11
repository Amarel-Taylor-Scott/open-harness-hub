"""src.teleon.exploration — the OPEN-ENDED EXPLORATION ESCALATION LADDER (Teleon-owned).

THE GAP this package fills: the deterministic DECISION layer that sits on the FAILURE path of the runtime
gate. When a task is open-ended (no template / known solution matches), or when the deterministic + LLM first
passes FAIL the gate, *something* must decide whether to (a) give up to a human or (b) hand the task to a
BOUNDED exploration agent (an OpenClaw/Hermes-class runtime) as a CANDIDATE producer. This package is that
connective tissue between the gate's failure path and the existing exploration PORTS — nothing more.

  * :mod:`ladder` — a PURE, deterministic ``escalation_decision(task, attempt_history, *, policy)`` that
    classifies a task onto the tiers T0..T4 (template match → deterministic primitive → LLM first pass →
    OPEN-ENDED EXPLORATION → human escalation) and returns the routing decision. No I/O, no clock, no RNG.
  * :mod:`dispatch` — a governed wrapper that, GIVEN a T3 decision, builds a BOUNDED
    :class:`~src.teleon.agents.agent_runtime_provider.AgentRuntimeRequest` (caps: time / steps / cost /
    sandbox / allowlisted sources) for a CATALOG candidate runtime and DEFAULTS to the offline
    ``local_emulator@v1`` invariant when no candidate is provisioned. Output is a CANDIDATE proposal carrying
    provenance + a receipt, ``serves_truth=False`` — it RE-ENTERS the gate, never publishes.

THE INVARIANTS (mirrors every Teleon agent/research/swarm port):
  * Agents DISCOVER/ACT and PROPOSE; Baltor STORES/VERIFIES/RECONCILES/CONSUMES. Exploration output is NEVER
    truth (``serves_truth=False``) — it is a CANDIDATE that must clear the SAME gate (lift + durability +
    receipts) and only a PROMOTED capability compiles to a runtime.
  * Candidate runtimes (OpenClaw/ClawLess, Hermes, ...) are CATALOG ENTRIES ONLY — this package NEVER imports,
    pip-installs, or executes them. The deterministic OFFLINE ``local_emulator@v1`` is the correctness
    invariant; an unprovisioned candidate degrades honestly (unavailable), never a fabricated result.
  * ENDS changes + forbidden-autonomous tasks are HUMAN-GATED (T4) — an open-ended explorer is never dispatched
    to redraw the box. The adaptation-ladder classifier (L0..L5) is the single source of that boundary.
  * This layer RIDES the existing ExecutionProviderPort + FleetLedger (via the agent-runtime port's
    ``select_backend`` delegation) — it is NOT a second worker/agent framework.

ARCHITECTURAL LAW (architecture/portfolio_dependency_law.json): Teleon-layer code. Imports only the stdlib +
``src.teleon`` siblings — NEVER ``src.baltor`` / ``src.openharnesshub``. Deterministic when ``now`` is injected
(content-addressed ids; no RNG / no wall-clock). Doc: docs/architecture/open-ended-exploration-ladder.md.
"""
from .ladder import (
    escalation_decision,
    EscalationDecision,
    TaskClass,
    Tier,
    EscalationPolicy,
    DEFAULT_POLICY,
    TASK_CLASSES,
    EXPLORATION_TASK_CLASSES,
    DEFAULT_MAX_LLM_ATTEMPTS,
)
from .dispatch import (
    dispatch_exploration,
    ExplorationProposal,
    DEFAULT_EXPLORATION_RUNTIME_ID,
    EXPLORATION_WORKER_BUCKET,
    DEFAULT_BOUNDS,
)

__all__ = [
    # ladder (the pure decision)
    "escalation_decision", "EscalationDecision", "TaskClass", "Tier", "EscalationPolicy",
    "DEFAULT_POLICY", "TASK_CLASSES", "EXPLORATION_TASK_CLASSES", "DEFAULT_MAX_LLM_ATTEMPTS",
    # dispatch (the governed wrapper)
    "dispatch_exploration", "ExplorationProposal", "DEFAULT_EXPLORATION_RUNTIME_ID",
    "EXPLORATION_WORKER_BUCKET", "DEFAULT_BOUNDS",
]
