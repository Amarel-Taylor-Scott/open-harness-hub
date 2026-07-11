"""src.teleon.frameworks.framework_adapters — make Teleon capabilities interoperate with the common agent
frameworks, BOTH directions, governed.

  * EXPORT — turn a governed Teleon capability into a framework-NATIVE tool spec (MCP tool / OpenAI function /
    Anthropic tool / LangGraph node / CrewAI tool) so any of those frameworks can call it. The exported spec carries
    our governance (verified / receipt / serves_truth) under a vendor-permitted extension key, so the consumer gets
    a GOVERNED capability, not a bare function.
  * WRAP — turn a framework AGENT (a CrewAI/AutoGen/LangGraph/aider agent) into a governed CANDIDATE behind a port:
    it runs sandboxed, its output is a candidate (serves_truth False), and a gate dispositions it. Agents PROPOSE;
    Teleon DISPOSES (per the swarm-orchestration positioning: frameworks are candidates, never our runtime).

Pure + deterministic; Teleon-layer (never imports baltor, never imports a framework — it emits/【consumes】 specs,
it does not depend on the frameworks). A capability is a dict: {name, description, parameters(JSON-schema), governance}.
"""
from __future__ import annotations

SUPPORTED_FRAMEWORKS = ("mcp", "openai", "anthropic", "langgraph", "crewai", "autogen")
_GOV_KEY = "x_teleon_governance"   # vendor-permitted extension key carrying our governance on an exported tool


def _gov(capability: dict) -> dict:
    g = dict(capability.get("governance", {}))
    g.setdefault("serves_truth", False)
    return g


def to_openai_tool(capability: dict) -> dict:
    """A Teleon capability as an OpenAI / AutoGen function-tool spec."""
    return {"type": "function", "function": {
        "name": capability["name"], "description": capability.get("description", ""),
        "parameters": capability.get("parameters", {"type": "object", "properties": {}})},
        _GOV_KEY: _gov(capability)}   # top-level extension key (sibling of type/function), consistent across exporters


def to_anthropic_tool(capability: dict) -> dict:
    """A Teleon capability as an Anthropic / Claude-Agent-SDK tool spec."""
    return {"name": capability["name"], "description": capability.get("description", ""),
            "input_schema": capability.get("parameters", {"type": "object", "properties": {}}),
            _GOV_KEY: _gov(capability)}


def to_mcp_tool(capability: dict) -> dict:
    """A Teleon capability as an MCP tool definition."""
    return {"name": capability["name"], "description": capability.get("description", ""),
            "inputSchema": capability.get("parameters", {"type": "object", "properties": {}}),
            _GOV_KEY: _gov(capability)}


def to_langgraph_node(capability: dict) -> dict:
    """A Teleon capability as a LangGraph node descriptor (a callable node bound to the governed capability)."""
    return {"node": capability["name"], "kind": "tool_node", "binds_capability": capability["name"],
            "description": capability.get("description", ""), "governed": True, _GOV_KEY: _gov(capability)}


def to_crewai_tool(capability: dict) -> dict:
    """A Teleon capability as a CrewAI tool descriptor."""
    return {"name": capability["name"], "description": capability.get("description", ""),
            "args_schema": capability.get("parameters", {"type": "object", "properties": {}}),
            _GOV_KEY: _gov(capability)}


_EXPORTERS = {"openai": to_openai_tool, "autogen": to_openai_tool, "anthropic": to_anthropic_tool,
              "mcp": to_mcp_tool, "langgraph": to_langgraph_node, "crewai": to_crewai_tool}


def export_capability(capability: dict, framework: str) -> dict:
    """Export a governed capability as the given framework's native tool spec."""
    if framework not in _EXPORTERS:
        raise ValueError(f"unsupported framework {framework!r}; one of {sorted(_EXPORTERS)}")
    return _EXPORTERS[framework](capability)


def wrap_agent_as_candidate(framework: str, agent_id: str, *, capability_slot: str,
                            sandbox: str = "local_function_emulator") -> dict:
    """Wrap a framework AGENT as a governed candidate behind a port: sandboxed, output is candidate, never truth.
    The framework runs the agent; Teleon governs it (a gate dispositions the proposal)."""
    if framework not in SUPPORTED_FRAMEWORKS:
        raise ValueError(f"unsupported framework {framework!r}; one of {SUPPORTED_FRAMEWORKS}")
    return {
        "framework": framework, "agent_id": agent_id, "capability_slot": capability_slot,
        "binding": "ExecutionProviderPort", "sandbox": sandbox,
        "disposition": "candidate",           # discovery != trust; a gate promotes, never the agent
        "serves_truth": False,                # the agent PROPOSES; Teleon DISPOSES
        "note": "framework agent runs sandboxed as a bounded candidate; its output is evidence, not truth",
    }
