#!/usr/bin/env python3
"""teleon_capability_gateway_mcp — a stdlib-only JSON-RPC 2.0 / MCP server (stdio) for the Teleon Agent Capability Gateway.

Wraps the in-process ``TeleonMcpProjection`` (the LOCAL projection of the Agent Capability Gateway — exactly
FIVE stable tools: teleon_list_capabilities / teleon_describe_capability / teleon_run_capability /
teleon_get_receipt / teleon_request_boundary_expansion) and speaks JSON-RPC over stdio with newline-delimited
framing (the MCP stdio spec) via the shared ``scripts._mcp_stdio`` transport. It executes NOTHING itself: every ``tools/call`` delegates to the
projection, which delegates to the gateway — agents ASK, Teleon EXECUTES, Baltor governs truth
(``serves_truth=false`` on every result). Deterministic/offline: no HTTP, no live model, no ``mcp`` pip package.

Bootstrap: it makes ``scripts`` importable then calls ``scripts._repo_paths.install()`` so ``src.teleon...``
resolves from a BARE shell (any cwd, no PYTHONPATH) after the ``_repos/`` migration.

Register with Claude Code:
  claude mcp add teleon-capability-gateway -- python3 _repos/shared-backend-components/scripts/teleon_capability_gateway_mcp.py

Run the proof (lists the five tools without a live client):
  python3 _repos/shared-backend-components/scripts/teleon_capability_gateway_mcp.py --self-test
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# --- bootstrap: expose `scripts`, then install every _repos code root so a bare shell resolves `src.teleon...` ---
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # _repos/shared-backend-components (holds the `scripts` pkg)
import scripts._repo_paths as _repo_paths  # noqa: E402

_repo_paths.install()  # prepends repo root + every _repos/*/backend so `from src.teleon...` resolves from any cwd

from scripts import _mcp_stdio  # noqa: E402  the ONE newline-delimited (spec) MCP stdio transport, shared by every server

from src.teleon.agent_gateway.mcp_projection import (  # noqa: E402
    py_class_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection as _TeleonMcpProjection,
    py_const_src_teleon_agent_gateway_mcp_projection__EXPOSED_TOOL_COUNT as _EXPOSED_TOOL_COUNT,
    py_const_src_teleon_agent_gateway_mcp_projection__TOOL_NAMES as _TOOL_NAMES,
)

SERVER_NAME = "teleon-capability-gateway"
SERVER_VERSION = "0.1.0"
PROTOCOL_VERSION = "2025-11-25"  # MCP protocol revision echoed on initialize (matches the sibling gateway bridge)
_PROJECTION = _TeleonMcpProjection()  # the ONE gateway-backed projection; holds no state of its own


def _now() -> str:
    """Real UTC clock injected at the transport boundary — a live MCP call happens now; the projection stays pure."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def mcp_tools() -> list[dict[str, Any]]:
    """The five MCP tool descriptors, mapping the projection's ``input_schema`` -> MCP's ``inputSchema`` key."""
    return [{"name": d["name"], "description": d["description"], "inputSchema": d["input_schema"]}
            for d in _PROJECTION.tool_descriptors()]


def handle_rpc(message: dict[str, Any]) -> dict[str, Any] | None:
    """Handle one JSON-RPC request; return the response dict (or None for a notification / no-id message)."""
    method = str(message.get("method") or "")
    request_id = message.get("id")
    params = message.get("params") if isinstance(message.get("params"), dict) else {}
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": request_id, "result": {
            "protocolVersion": PROTOCOL_VERSION,
            "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
            "capabilities": {"tools": {"listChanged": False}}}}
    if method == "notifications/initialized":
        return None
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": request_id, "result": {"tools": mcp_tools()}}
    if method == "tools/call":
        arguments = params.get("arguments") if isinstance(params.get("arguments"), dict) else {}
        result = _PROJECTION.call_tool(str(params.get("name") or ""), arguments, now=_now())
        return {"jsonrpc": "2.0", "id": request_id, "result": {
            "content": [{"type": "text", "text": json.dumps(result, indent=2, sort_keys=True)}],
            "isError": "error" in result}}
    if request_id is None:
        return None
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32601, "message": f"method not found: {method}"}}


# Transport (framing + serve loop) is the single-sourced scripts._mcp_stdio (newline-delimited JSON — the
# MCP stdio spec). This server owns only PROTOCOL/dispatch (handle_rpc); main() runs _mcp_stdio.serve(handle_rpc).


def self_test() -> dict[str, Any]:
    """Prove the wrap WITHOUT a live client: tools/list returns exactly the five projection tools, and a
    tools/call for teleon_list_capabilities dispatches through to the gateway and returns content."""
    listed = handle_rpc({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
    tools = (listed or {}).get("result", {}).get("tools", [])
    names = [t.get("name") for t in tools]
    called = handle_rpc({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                         "params": {"name": _TOOL_NAMES[0], "arguments": {}}})
    call_result = (called or {}).get("result", {})
    call_ok = bool(call_result.get("content")) and call_result.get("isError") is False
    return {
        "ok": len(tools) == _EXPOSED_TOOL_COUNT == 5 and names == list(_TOOL_NAMES) and call_ok,
        "server": SERVER_NAME,
        "tool_count": len(tools),
        "expected_tool_count": _EXPOSED_TOOL_COUNT,
        "tools": names,
        "tools_call_ok": call_ok,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    parser.add_argument("--self-test", action="store_true", help="list the five tools without a live client, then exit")
    args = parser.parse_args(argv)
    if args.self_test:
        result = self_test()
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result.get("ok") else 1
    return _mcp_stdio.serve(handle_rpc)


if __name__ == "__main__":
    raise SystemExit(main())
