#!/usr/bin/env python3
"""Emit MCP (Model Context Protocol) server artifacts from every `tool/*`
manifest and from `processor/*` manifests that are safe to invoke from a
model (deterministic, idempotent, no escalation).

Outputs:

  dist/mcp/tools.json             # array of MCP Tool definitions
  dist/mcp/tools-list-response.json  # full JSON-RPC tools/list response
  dist/mcp/server.py              # Python MCP server stub (mcp SDK)
  dist/mcp/server.ts              # TypeScript stub (@modelcontextprotocol/sdk)
  dist/mcp/README.md              # how to run / extend

Spec: https://modelcontextprotocol.io/specification/2025-11-25/server/tools
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from scripts.emit._lib import (  # noqa: E402
    DIST, by_type, load_catalog, slug_only, write_json,
)

# MCP tool names: A-Za-z0-9 _ - . — no slashes. We strip the type/ prefix and
# keep hyphens; dots become underscores for safety.
NAME_RE = re.compile(r"[^A-Za-z0-9_.\-]")


def mcp_name(artifact_id: str) -> str:
    return NAME_RE.sub("_", slug_only(artifact_id))


def is_model_callable_processor(p: dict) -> bool:
    """A processor is safe to expose as an MCP tool when:
       - it's deterministic OR idempotent (so retries don't break state); AND
       - its side_effects are not 'external_call' that triggers escalations or sends
         to a human reviewer (which the model shouldn't trigger autonomously).
    """
    kind = p.get("process_kind", "")
    if kind.startswith("escalate."):
        return False
    if kind.startswith("deliver."):
        return False
    if kind.startswith("audit."):
        return False
    if p.get("side_effects") == "external_call":
        # External calls are OK only if the processor is read-only-ish.
        if not (p.get("deterministic") or p.get("idempotent")):
            return False
    return True


def normalize_schema(s: Any) -> dict:
    """Ensure an inputSchema is a valid JSON Schema object (not null)."""
    if not isinstance(s, dict):
        return {"type": "object", "additionalProperties": False}
    schema = dict(s)
    schema.setdefault("type", "object")
    if schema.get("type") == "object" and "properties" not in schema and "additionalProperties" not in schema:
        schema["additionalProperties"] = False
    return schema


def to_mcp_tool(manifest: dict) -> dict:
    """Map a hub tool/* or processor/* manifest to an MCP Tool object."""
    name        = mcp_name(manifest["id"])
    description = manifest.get("description", "").strip()
    title       = manifest.get("name", name)

    annotations: dict[str, Any] = {}
    if manifest.get("type") == "tool":
        side = manifest.get("side_effects")
        if side == "read":
            annotations["readOnlyHint"] = True
            annotations["destructiveHint"] = False
        elif side == "write":
            annotations["destructiveHint"] = True
        elif side == "external_call":
            annotations["openWorldHint"] = True

    if manifest.get("type") == "processor":
        annotations["readOnlyHint"] = bool(manifest.get("deterministic")) and manifest.get("side_effects") in ("none", "read", None)

    tool: dict[str, Any] = {
        "name":        name,
        "title":       title,
        "description": description,
        "inputSchema": normalize_schema(manifest.get("parameters") or {}),
    }
    if manifest.get("returns"):
        tool["outputSchema"] = normalize_schema(manifest["returns"])
    if annotations:
        tool["annotations"] = annotations

    # Hub-specific extension so consumers can trace back to the manifest.
    tool["_meta"] = {
        "ohh:artifactId": manifest["id"],
        "ohh:version":    manifest.get("version"),
        "ohh:license":    manifest.get("license"),
        "ohh:industry":   manifest.get("industry", []),
        "ohh:capability": manifest.get("capability", []),
        "ohh:trustBoundary": manifest.get("trust_boundary"),
    }
    return tool


PYTHON_STUB = '''"""Open Harness Hub — MCP server stub (auto-generated).

Run:
  pip install mcp
  python server.py

This stub exposes every tool/* manifest from the hub plus model-callable
processors. Implement the body of each `_run_<name>(args)` function with the
real backend (HTTP call, Python callable, etc.) — the schema validation and
JSON-RPC plumbing are handled by the SDK.
"""
from __future__ import annotations

import asyncio
import json
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

# ── Tool definitions (auto-generated, do not edit) ─────────────────────────

TOOLS: list[dict] = {tools_json}

# ── Server wiring ──────────────────────────────────────────────────────────

server = Server("open-harness-hub")


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name=t["name"],
            title=t.get("title"),
            description=t.get("description", ""),
            inputSchema=t["inputSchema"],
        )
        for t in TOOLS
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    handler = HANDLERS.get(name)
    if handler is None:
        return [TextContent(type="text", text=f"unknown tool: {{name!r}}")]
    result = await handler(arguments)
    if not isinstance(result, str):
        result = json.dumps(result, indent=2)
    return [TextContent(type="text", text=result)]


# ── Tool implementations (TODO: fill these in) ─────────────────────────────

{handler_defs}

HANDLERS = {{
{handler_map}
}}


async def main() -> None:
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
'''

TS_STUB = '''/**
 * Open Harness Hub — MCP server stub (auto-generated).
 *
 * Run:
 *   npm install @modelcontextprotocol/sdk
 *   node server.ts          # or: tsx server.ts
 *
 * Implement the body of each handler with the real backend.
 */
import {{ Server }} from "@modelcontextprotocol/sdk/server/index.js";
import {{ StdioServerTransport }} from "@modelcontextprotocol/sdk/server/stdio.js";
import {{ ListToolsRequestSchema, CallToolRequestSchema }} from "@modelcontextprotocol/sdk/types.js";

// ── Tool definitions (auto-generated, do not edit) ────────────────────────

const TOOLS = {tools_json} as const;

// ── Server wiring ─────────────────────────────────────────────────────────

const server = new Server(
  {{ name: "open-harness-hub", version: "0.1.0" }},
  {{ capabilities: {{ tools: {{ listChanged: false }} }} }},
);

server.setRequestHandler(ListToolsRequestSchema, async () => {{
  return {{ tools: TOOLS }};
}});

server.setRequestHandler(CallToolRequestSchema, async (request) => {{
  const {{ name, arguments: args }} = request.params;
  const handler = HANDLERS[name as keyof typeof HANDLERS];
  if (!handler) {{
    return {{
      content: [{{ type: "text", text: `unknown tool: ${{name}}` }}],
      isError: true,
    }};
  }}
  const result = await handler(args ?? {{}});
  return {{
    content: [{{ type: "text", text: typeof result === "string" ? result : JSON.stringify(result, null, 2) }}],
  }};
}});

// ── Tool implementations (TODO: fill these in) ────────────────────────────

const HANDLERS: Record<string, (args: any) => Promise<unknown>> = {{
{ts_handlers}
}};

// ── Entrypoint ────────────────────────────────────────────────────────────

(async () => {{
  const transport = new StdioServerTransport();
  await server.connect(transport);
}})();
'''


def render_python_server(tools: list[dict]) -> str:
    tools_json = json.dumps(tools, indent=4)
    handler_defs_lines: list[str] = []
    handler_map_lines: list[str] = []
    for t in tools:
        n = t["name"]
        py_name = n.replace("-", "_").replace(".", "_")
        handler_defs_lines.append(
            f"async def _run_{py_name}(args: dict[str, Any]) -> Any:\n"
            f"    \"\"\"{t['title']} — {t.get('description', '').splitlines()[0] if t.get('description') else ''}\"\"\"\n"
            f"    # TODO: implement {t['_meta']['ohh:artifactId']!r}\n"
            f"    return {{'received': args, 'tool': {n!r}, 'status': 'stub'}}"
        )
        handler_map_lines.append(f"    {n!r}: _run_{py_name},")
    return PYTHON_STUB.format(
        tools_json=tools_json,
        handler_defs="\n\n\n".join(handler_defs_lines),
        handler_map="\n".join(handler_map_lines),
    )


def render_ts_server(tools: list[dict]) -> str:
    tools_json = json.dumps(tools, indent=2)
    ts_handlers_lines: list[str] = []
    for t in tools:
        n = t["name"]
        safe_key = n if all(c.isalnum() or c == "_" for c in n) else f'"{n}"'
        ts_handlers_lines.append(
            f"  {safe_key}: async (args: any) => {{\n"
            f"    // TODO: implement {t['_meta']['ohh:artifactId']}\n"
            f"    return {{ received: args, tool: {n!r}, status: 'stub' }};\n"
            f"  }},"
        )
    return TS_STUB.format(
        tools_json=tools_json,
        ts_handlers="\n".join(ts_handlers_lines),
    )


README = """# Open Harness Hub — MCP server

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
"""


def main() -> int:
    catalog = load_catalog()

    tools_manifests: list[tuple[Path, dict]] = []
    for path, m in by_type(catalog, "tool"):
        tools_manifests.append((path, m))
    for path, m in by_type(catalog, "processor"):
        if is_model_callable_processor(m):
            tools_manifests.append((path, m))

    tools = [to_mcp_tool(m) for _, m in tools_manifests]

    out_dir = DIST / "mcp"
    out_dir.mkdir(parents=True, exist_ok=True)

    write_json(out_dir / "tools.json", tools)
    write_json(out_dir / "tools-list-response.json", {
        "jsonrpc": "2.0",
        "id":      1,
        "result":  {"tools": tools},
    })

    (out_dir / "server.py").write_text(render_python_server(tools))
    (out_dir / "server.ts").write_text(render_ts_server(tools))
    (out_dir / "README.md").write_text(README)

    print(f"wrote {len(tools)} tools to dist/mcp/")
    print("  dist/mcp/tools.json")
    print("  dist/mcp/tools-list-response.json")
    print("  dist/mcp/server.py")
    print("  dist/mcp/server.ts")
    print("  dist/mcp/README.md")
    print("\ntool names:")
    for t in tools:
        meta = t["_meta"]
        print(f"  {t['name']:40s}  ({meta['ohh:artifactId']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
