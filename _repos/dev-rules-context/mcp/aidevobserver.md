# AIDevObserver MCP

Purpose: expose AIDevObserver review tools to Claude Code through MCP.

Tools:
- `list_sessions`
- `review_session`
- `live_review`

Setup:
`claude mcp add aidevobserver -- python3 _repos/shared-backend-components/scripts/aidevobserver_mcp_server.py`

Trust: read-only, candidate findings only, serves_truth=false.
