#!/usr/bin/env python3
"""aidevobserver_mcp_server — a stdlib-only JSON-RPC 2.0 / MCP server (stdio) for the Teleon Observer.

Exposes the governed AI-usage Observer to any MCP client (Claude Code, an editor) over line-delimited JSON-RPC
on stdin/stdout — no `mcp` pip package, matching the repo's no-pip discipline. It reuses the existing engine:
``observer.sessions`` (discover Claude transcripts) + ``observer.cli`` (review_path / live_path) + the router.

Tools:
  list_sessions  {cwd?}                       -> discovered Claude Code sessions (metadata only, read-only).
  review_session {path?, latest?, cwd?}       -> governed post-session report (reinvention/waste candidates).
  live_review    {path?, latest?, cwd?, mode?}-> prospective findings the Observer would surface now + summary.

Every finding is a governed CANDIDATE (serves_truth=false; a human triages). The server is READ-ONLY: it reads
transcripts and never writes or republishes session content.

Register it with Claude Code:

  claude mcp add aidevobserver -- python3 /home/username/ai_harness_and_knowledge_facts_and_logic_website_sharing/scripts/aidevobserver_mcp_server.py

Run the proof:

  python3 scripts/aidevobserver_mcp_server.py --self-test
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:  # self-bootstrap so `src.teleon...` imports regardless of CWD/PYTHONPATH
    sys.path.insert(0, str(REPO))

from src.teleon.observer import cli, sessions  # noqa: E402

PROTOCOL_VERSION = "2024-11-05"  # MCP protocol revision this server implements
SERVER_NAME = "aidevobserver"
SERVER_VERSION = "0.1.0"

# JSON-RPC 2.0 error codes (the subset we use)
_PARSE_ERROR = -32700
_METHOD_NOT_FOUND = -32601
_INTERNAL_ERROR = -32603

# --- tool catalog (name + description + JSON Schema inputSchema) -------------------------------------------------
_SESSION_TARGET_PROPS = {
    "path": {"type": "string", "description": "Transcript file to review directly (wins over latest/cwd)."},
    "latest": {"type": "boolean", "description": "Use the most recent discovered session (default when no path)."},
    "cwd": {"type": "string", "description": "Project cwd to discover sessions for (default: server cwd)."},
}

TOOLS = [
    {
        "name": "list_sessions",
        "description": "Discover Claude Code session transcripts for a project working directory "
                       "(read-only, metadata only: session_id/path/mtime/project, newest first).",
        "inputSchema": {
            "type": "object",
            "properties": {"cwd": _SESSION_TARGET_PROPS["cwd"]},
            "additionalProperties": False,
        },
    },
    {
        "name": "review_session",
        "description": "Governed POST-SESSION review of a Claude transcript: confidence-ranked reinvention + "
                       "waste candidate findings (serves_truth=false; a human triages). Pass a path, or omit it "
                       "to review the latest session for the cwd.",
        "inputSchema": {
            "type": "object",
            "properties": dict(_SESSION_TARGET_PROPS),
            "additionalProperties": False,
        },
    },
    {
        "name": "live_review",
        "description": "Prospective findings the Observer WOULD surface live (in a LIVE mode) for a session, plus "
                       "a summary of what would interrupt. Returns {surfaced, summary, mode}. serves_truth=false.",
        "inputSchema": {
            "type": "object",
            "properties": {
                **_SESSION_TARGET_PROPS,
                "mode": {"type": "string", "enum": list(cli.LIVE_MODES), "default": cli.DEFAULT_LIVE_MODE,
                         "description": "Live restraint mode (advisory|active|enforcing)."},
            },
            "additionalProperties": False,
        },
    },
]


class ToolError(Exception):
    """A tool-level failure -> surfaced in-band via {isError: true} (so the model sees it), not a JSON-RPC error."""


# --- tool handlers (pure: arguments dict -> JSON-able result) ----------------------------------------------------
def _resolve_path(arguments: dict) -> str:
    if arguments.get("path"):
        return arguments["path"]
    path = sessions.latest_session(arguments.get("cwd"))
    if not path:
        raise ToolError("no Claude Code session found (pass `path`, or call from the project's cwd)")
    return path


def _tool_list_sessions(arguments: dict) -> list:
    return sessions.discover_sessions(arguments.get("cwd"))


def _tool_review_session(arguments: dict) -> dict:
    return cli.review_path(_resolve_path(arguments))


def _tool_live_review(arguments: dict) -> dict:
    mode = arguments.get("mode") or cli.DEFAULT_LIVE_MODE
    if mode not in cli.LIVE_MODES:
        raise ToolError(f"mode must be one of {cli.LIVE_MODES}; got {mode!r}")
    return cli.live_path(_resolve_path(arguments), mode)


_TOOL_HANDLERS = {
    "list_sessions": _tool_list_sessions,
    "review_session": _tool_review_session,
    "live_review": _tool_live_review,
}


# --- JSON-RPC / MCP method handlers -----------------------------------------------------------------------------
def handle_initialize(params: dict) -> dict:
    # echo the client's protocolVersion when given (compat), else advertise ours
    client_pv = (params or {}).get("protocolVersion")
    return {
        "protocolVersion": client_pv or PROTOCOL_VERSION,
        "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
        "capabilities": {"tools": {}},
    }


def handle_tools_list(params: dict) -> dict:
    return {"tools": TOOLS}


def handle_tools_call(params: dict) -> dict:
    name = (params or {}).get("name")
    arguments = (params or {}).get("arguments") or {}
    handler = _TOOL_HANDLERS.get(name)
    if handler is None:
        return {"content": [{"type": "text", "text": f"unknown tool: {name!r}"}], "isError": True}
    try:
        result = handler(arguments)
        return {"content": [{"type": "text", "text": json.dumps(result, indent=2)}], "isError": False}
    except ToolError as e:
        return {"content": [{"type": "text", "text": str(e)}], "isError": True}
    except Exception as e:  # noqa: BLE001 — any tool fault is reported in-band, never crashes the loop
        return {"content": [{"type": "text", "text": f"{type(e).__name__}: {e}"}], "isError": True}


def _error(req_id, code: int, message: str) -> dict:
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}


def dispatch(request: dict) -> dict | None:
    """Route one JSON-RPC request -> a response dict, or None for notifications (requests with no `id`)."""
    method = request.get("method")
    params = request.get("params") or {}
    req_id = request.get("id")
    is_notification = "id" not in request

    if method == "notifications/initialized":
        return None  # no-op notification (client confirming the handshake)
    try:
        if method == "initialize":
            result = handle_initialize(params)
        elif method == "tools/list":
            result = handle_tools_list(params)
        elif method == "tools/call":
            result = handle_tools_call(params)
        elif method == "ping":
            result = {}
        elif is_notification:
            return None  # unknown notification -> silently ignore (spec-compliant)
        else:
            return _error(req_id, _METHOD_NOT_FOUND, f"method not found: {method}")
    except Exception as e:  # noqa: BLE001
        return None if is_notification else _error(req_id, _INTERNAL_ERROR, f"{type(e).__name__}: {e}")
    return None if is_notification else {"jsonrpc": "2.0", "id": req_id, "result": result}


def serve(stdin=None, stdout=None) -> int:
    """The stdio main loop: read line-delimited JSON requests, dispatch, write+flush JSON-RPC responses."""
    stdin = stdin or sys.stdin
    stdout = stdout or sys.stdout
    for line in stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            stdout.write(json.dumps(_error(None, _PARSE_ERROR, "parse error")) + "\n")
            stdout.flush()
            continue
        response = dispatch(request)
        if response is not None:
            stdout.write(json.dumps(response) + "\n")
            stdout.flush()
    return 0


# --- proof: drive initialize + tools/list + tools/call by calling the handlers directly (no real stdio) ---------
_SYNTHETIC_TRANSCRIPT = [
    {"type": "mode", "mode": "opus"},  # noise the capture seam drops
    {"type": "user", "message": {"role": "user", "content": "let me write a pdf parser from scratch"}},
    {"type": "user", "message": {"role": "user", "content": "I'll implement my own address validation"}},
    {"type": "assistant", "message": {"role": "assistant", "content": [
        {"type": "thinking", "thinking": "private"},
        {"type": "text", "text": "ok, writing it"},
        {"type": "tool_use", "name": "Write", "input": {"file_path": "/x/pdf.py", "content": "def parse(): ..."}}]}},
]


def _self_test() -> int:
    import shutil
    import tempfile

    fails: list[str] = []
    checks = 0

    def ck(name: str, ok: bool, detail: str = "") -> None:
        nonlocal checks
        checks += 1
        if not ok:
            fails.append(name)
            print(f"  [XX] {name}{(' — ' + detail) if detail else ''}")

    # initialize
    init = handle_initialize({"protocolVersion": PROTOCOL_VERSION})
    ck("initialize returns a protocolVersion", isinstance(init.get("protocolVersion"), str))
    ck("initialize advertises serverInfo.name", init.get("serverInfo", {}).get("name") == SERVER_NAME)
    ck("initialize advertises a tools capability", "tools" in init.get("capabilities", {}))

    # tools/list
    listed = handle_tools_list({})["tools"]
    names = {t["name"] for t in listed}
    ck("tools/list returns 3 tools", len(listed) == 3, str(len(listed)))
    ck("the 3 expected tools are present", names == {"list_sessions", "review_session", "live_review"}, str(names))
    ck("each tool has a JSON Schema inputSchema", all(t.get("inputSchema", {}).get("type") == "object" for t in listed))
    ck("each tool has a non-empty description", all(t.get("description") for t in listed))

    # synthetic transcript in a UNIQUE tmp dir, reviewed via tools/call (handlers called directly, no stdio)
    tmp = Path(tempfile.mkdtemp(prefix="aidevobserver_mcp_selftest_"))
    transcript = tmp / "synthetic.jsonl"
    transcript.write_text("\n".join(json.dumps(r) for r in _SYNTHETIC_TRANSCRIPT) + "\n")
    try:
        call = handle_tools_call({"name": "review_session", "arguments": {"path": str(transcript)}})
        ck("tools/call review_session is not an error", call.get("isError") is False)
        ck("tools/call returns text content", call["content"][0]["type"] == "text")
        report = json.loads(call["content"][0]["text"])
        ck("review result serves_truth=false", report.get("serves_truth") is False)
        ck("review found candidate findings", report["summary"]["findings"] >= 1, str(report["summary"]["findings"]))
        ck("every finding is a governed candidate", all(
            f.get("candidate") is True and f.get("serves_truth") is False for f in report["report"]))

        live = json.loads(handle_tools_call(
            {"name": "live_review", "arguments": {"path": str(transcript), "mode": "advisory"}})["content"][0]["text"])
        ck("live_review returns a surfaced list", isinstance(live.get("surfaced"), list))
        ck("live_review reports its mode + summary", live.get("mode") == "advisory" and "summary" in live)

        bad = handle_tools_call({"name": "does_not_exist", "arguments": {}})
        ck("unknown tool sets isError", bad.get("isError") is True)

        # list_sessions tolerates a project with no sessions (read-only, graceful)
        empty = handle_tools_call({"name": "list_sessions", "arguments": {"cwd": "/no/such/project/xyz"}})
        ck("list_sessions tolerates none -> []", json.loads(empty["content"][0]["text"]) == [])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # dispatch envelope + notification no-op
    resp = dispatch({"jsonrpc": "2.0", "id": 7, "method": "tools/list", "params": {}})
    ck("dispatch wraps a result in the JSON-RPC envelope",
       resp.get("jsonrpc") == "2.0" and resp.get("id") == 7 and "result" in resp)
    ck("notifications/initialized is a no-op (no response)",
       dispatch({"jsonrpc": "2.0", "method": "notifications/initialized"}) is None)
    ck("unknown method -> JSON-RPC method-not-found",
       dispatch({"jsonrpc": "2.0", "id": 8, "method": "bogus"})["error"]["code"] == _METHOD_NOT_FOUND)

    if fails:
        print(f"\nFAIL - aidevobserver_mcp_server: {len(fails)} of {checks} assertions failed")
        return 1
    print(f"PASS - aidevobserver_mcp_server: stdlib MCP server over stdio (initialize + tools/list[3] + tools/call) "
          f"wrapping the governed Observer reviewer; {checks} assertions; serves_truth=false, read-only.")
    return 0


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        return _self_test()
    return serve()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
