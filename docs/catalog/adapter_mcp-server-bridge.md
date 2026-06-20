# MCP server bridge

*adapter* · `adapter/mcp-server-bridge` · v0.1.0 · experimental

Adapter that exposes Open Harness Hub catalog tools over a Model
Context Protocol (MCP) server. Wraps any tool registered in the
catalog's tool registry and surfaces it as an MCP tool definition
that any MCP-compatible host (Claude Desktop, Claude Code, custom
agents) can discover and call. Handles request translation between
the MCP JSON-RPC wire format and the catalog tool's parameter
schema, forwards the call to the backing implementation (callable,
HTTP, or shell), and returns an MCP-compliant response. Supports
optional API-key authentication via environment variable injection
so tenant-keyed tools remain secure behind the bridge.

| axis | value |
|---|---|
| industry | ai, cross_industry, software.devops |
| capability | routing, serving, tool_use, governance |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | mixed |
| license | MIT |



