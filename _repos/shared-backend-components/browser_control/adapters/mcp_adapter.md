# mcp_adapter (DESIGN SEAM)

> Status: **design seam** — a driver whose "browser" is an **MCP server** (e.g. Playwright MCP, a browser-MCP, or
> our own MCP that fronts the `cdp`/`playwright` adapters). Lets any MCP-speaking agent (Claude Code included) drive
> the same driver-neutral command surface through tools, with every action still producing a receipt.

## Adapter shape

- **Two directions:**
  1. **Consume** an external browser MCP: `McpBrowserAdapter(BrowserAdapter)` whose methods call MCP tools
     (`browser.navigate`, `browser.snapshot`, `browser.click`, …) over stdio/HTTP. Map each tool result into a
     `browser_action_receipt` via `normalize_receipt`; a tool the server lacks → structured unsupported.
  2. **Expose** our adapters AS an MCP server: one tool per `BrowserAdapter` method (schemas already exist —
     `browser_action_receipt` / `browser_control_capability`), so `capabilities()` becomes the tool manifest.
- **Backs:** whatever the fronted server backs; when it fronts our own `cdp`/`playwright`, all 17.

## Install + test

```bash
npx -y @playwright/mcp@latest --help            # example external browser MCP (Node v22 + npx present here)
# manifest scan of any MCP server (reuse the shipped scanner, do not rebuild):
python3 scripts/scan_mcp_manifests.py --self-test
python3 scripts/security/skill_scanner.py --self-test    # scan any tool/skill payload before trusting it
```

## When to use

- The workflow is **already agent/MCP-driven** and you want browser control as governed MCP tools rather than a
  Python import.
- To give Claude Code / another agentic framework a **read-only, receipt-backed** browser without handing it a raw
  CDP socket.

## Risks

- An MCP server is **third-party code + a tool surface** — scan its manifest and any bundled skill
  (`scan_mcp_manifests` / `skill_scanner`) before trust; treat tool descriptions as untrusted (prompt-injection).
- The server may run with its own browser profile/auth → apply the same "acts as the logged-in user" auth gate as
  the extension/remote seams.
- Keep the side-effect ladder on OUR side of the tool call — never let a remote tool auto-execute a `write`+.
