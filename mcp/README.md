# Open Harness Hub — MCP server

Auto-generated from the hub's `tool/*` and `processor/*` manifests.
Re-run `python scripts/emit/mcp_server.py` to rebuild.

## What's in this directory

| File | Purpose |
|---|---|
| `tools.json` | Array of MCP Tool definitions (importable). |
| `tools-list-response.json` | Full JSON-RPC `tools/list` response (paste into a test fixture). |
| `server.py`  | Python MCP server stub using the `mcp` SDK. |
| `server.ts`  | TypeScript stub using `@modelcontextprotocol/sdk`. |

## Run the Python server

```bash
pip install mcp
python server.py
```

`server.py` runs over stdio. Wire it into Claude Desktop, Cursor,
cline, or any MCP host by adding to its config:

```json
{
  "mcpServers": {
    "open-harness-hub": {
      "command": "python",
      "args": ["/abs/path/to/dist/mcp/server.py"]
    }
  }
}
```

## Run the TypeScript server

```bash
npm install @modelcontextprotocol/sdk
npx tsx server.ts
```

## Tool count

See `tools.json` (`length`). Tools include every `tool/*` manifest plus
deterministic / idempotent `processor/*` manifests safe for model
invocation. Escalation, delivery, and audit processors are
deliberately excluded.

## Implementing handlers

Each `_run_<name>(args)` function (Python) / `HANDLERS.<name>(args)`
(TypeScript) is a stub. Replace the stub body with the real backend:

- For tools whose `implementations` declare `kind: openapi`, call the
  OpenAPI endpoint.
- For tools whose `implementations` declare `kind: callable`, import
  and call the Python module path.
- For tools with `kind: shell`, exec the command.
- For MCP-server tools (when `implementations` declares `kind: mcp`),
  delegate to the upstream MCP server.

## Trust & safety

The `_meta` field on each tool carries the hub's `industry`,
`capability`, `trustBoundary`, and `license` so the host can make
authorization decisions. Honor `annotations.readOnlyHint`,
`destructiveHint`, and `openWorldHint` when prompting the user for
confirmation.
