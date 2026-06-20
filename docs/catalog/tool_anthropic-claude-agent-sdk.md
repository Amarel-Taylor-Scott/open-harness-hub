# Anthropic Claude Agent SDK

*tool* · `tool/anthropic-claude-agent-sdk` · v0.1.0 · stable

The official Anthropic SDK for building custom Claude-powered agents with
structured tool use, multi-turn conversation management, prompt caching,
and first-class support for the Model Context Protocol (MCP). Provides
Python and TypeScript clients covering: synchronous and streaming message
calls, tool/function definitions with typed schemas, vision and document
inputs, token-usage tracking, batching, and native MCP server/client
adapters. The canonical integration layer for any pipeline component that
calls Claude models.

Unlike third-party harnesses, the Agent SDK is maintained by Anthropic,
versioned with stable semver, and ships with an official support SLA. Use
this as the base transport for building custom agents rather than wrapping
the HTTP API directly.

| axis | value |
|---|---|
| industry | ai, cross_industry |
| capability | agent_loop, tool_use, planning |
| modality | text, code, structured |
| lifecycle | stable |
| trust_boundary | external |
| license | MIT |



