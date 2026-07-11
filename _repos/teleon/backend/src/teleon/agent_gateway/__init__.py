"""src.teleon.agent_gateway — the TELEON AGENT CAPABILITY GATEWAY (agents are the customers).

An AI agent burns tokens re-deriving the same answers, re-reading the same corpora, and re-deciding the same
checks on every turn. The gateway flips that: it exposes a SMALL, STABLE set of receipt-backed
**capabilities** (~5, not 300) that an agent CALLS instead of reasoning from scratch. Teleon EXECUTES the
capability on the cheapest correct runtime (deterministic-first token ladder); Baltor GOVERNS truth. The agent
gets back a COMPACT, receipt-backed result — never a raw corpus dump, never a fact it can re-sell as truth.

THE LAW (mirrors every other Teleon port): **agents ASK, Teleon EXECUTES, Baltor governs truth.**
  * deterministic-first — the token ladder is cache → deterministic → api → local-calc → small-model →
    browser → provider → llm-fallback → human; the gateway always tries the cheapest correct rung first;
  * an LLM fallback is reached ONLY when the card opts in (``llm_fallback_allowed``) AND policy allows it — an
    agent can NEVER force an LLM rung (and the self-test never reaches a live model);
  * every result carries ``serves_truth=False`` — a capability output is EVIDENCE returned to the agent, never
    a CanonicalFact; for governed domains (e.g. CFPB Reg E) Teleon returns the authoritative value + held-out
    contradiction + source handle as evidence, and Baltor's rail is what governs it as truth;
  * an agent CANNOT self-expand its boundary, read secret VALUES (env:// refs only), call a forbidden tool,
    or weaken success criteria — a boundary-expansion request is ``pending_human_approval`` /
    ``auto_applied=False``, NEVER auto-applied;
  * every run writes an :class:`AgentCapabilityReceipt` recording the ``runtime_path`` actually taken.

Teleon-owned: imports only the stdlib + Teleon runtime selection (``bind_capability_task``) + Teleon
experiments ids + the Teleon-infra CFPB governed environment. It NEVER imports ``src.baltor``. Deterministic
when ``now`` is injected (content-addressed ids/hashes; no RNG / no wall-clock). Stdlib only; offline.
"""
from src.teleon.agent_gateway.gateway import (
    py_const_src_teleon_agent_gateway_gateway__AGENT_GATEWAY_SERVES_TRUTH,
    py_class_src_teleon_agent_gateway_gateway__AgentBoundaryExpansionRequest,
    py_class_src_teleon_agent_gateway_gateway__AgentCapabilityCard,
    py_class_src_teleon_agent_gateway_gateway__AgentCapabilityGateway,
    py_class_src_teleon_agent_gateway_gateway__AgentCapabilityReceipt,
    py_class_src_teleon_agent_gateway_gateway__AgentCapabilityRunResult,
    py_class_src_teleon_agent_gateway_gateway__AgentConsumer,
    py_const_src_teleon_agent_gateway_gateway__RUNTIME_PATH_DETERMINISTIC,
    py_const_src_teleon_agent_gateway_gateway__TOKEN_LADDER,
)

__all__ = [
    "py_class_src_teleon_agent_gateway_gateway__AgentCapabilityGateway",
    "py_class_src_teleon_agent_gateway_gateway__AgentCapabilityCard",
    "py_class_src_teleon_agent_gateway_gateway__AgentCapabilityRunResult",
    "py_class_src_teleon_agent_gateway_gateway__AgentCapabilityReceipt",
    "py_class_src_teleon_agent_gateway_gateway__AgentBoundaryExpansionRequest",
    "py_class_src_teleon_agent_gateway_gateway__AgentConsumer",
    "py_const_src_teleon_agent_gateway_gateway__AGENT_GATEWAY_SERVES_TRUTH",
    "py_const_src_teleon_agent_gateway_gateway__RUNTIME_PATH_DETERMINISTIC",
    "py_const_src_teleon_agent_gateway_gateway__TOKEN_LADDER",
]
