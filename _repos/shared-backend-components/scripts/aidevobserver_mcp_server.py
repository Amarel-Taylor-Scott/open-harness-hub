#!/usr/bin/env python3
"""aidevobserver_mcp_server — a stdlib-only JSON-RPC 2.0 / MCP server (stdio) for the Teleon Observer.

Exposes the governed AI-usage Observer to any MCP client (Claude Code, an editor) over line-delimited JSON-RPC
on stdin/stdout — no `mcp` pip package, matching the repo's no-pip discipline. It reuses the existing engine:
``observer.sessions`` (discover Claude transcripts) + ``observer.cli`` (review_path / live_path) + the router,
and folds in the capability-retrieval MCP catalog so an adopter needs ONE AIDevObserver connection.

Tools:
  list_sessions  {cwd?}                       -> discovered Claude Code sessions (metadata only, read-only).
  review_session {path?, latest?, cwd?}       -> governed post-session report (reinvention/waste candidates).
  live_review    {path?, latest?, cwd?, mode?}-> prospective findings the Observer would surface now + summary.
  primitive_search / find_reuse / capability_compose
                                                -> the existing fast retrieval + reuse + composition tools.

Every finding is a governed CANDIDATE (serves_truth=false; a human triages). The server never writes or
republishes transcript/source-corpus content. Full-corpus search may advance a derived local index checkpoint so
appended primitive rows become searchable; that checkpoint is not promotion.

Register it with Claude Code:

  claude mcp add aidevobserver -- python3 \
    /home/username/ai_harness_and_knowledge_facts_and_logic_website_sharing/_repos/shared-backend-components/scripts/aidevobserver_mcp_server.py

Run the proof:

  python3 _repos/shared-backend-components/scripts/aidevobserver_mcp_server.py --self-test
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_SBC = Path(__file__).resolve().parents[1]  # shared-backend-components root (holds scripts/) — on path so `import scripts.*` works
if str(_SBC) not in sys.path:
    sys.path.insert(0, str(_SBC))
from scripts._repo_paths import install as _install  # noqa: E402
_install()  # add every _repos/*/backend root so `src.teleon...` imports regardless of CWD/PYTHONPATH (fixes `claude mcp add` from a bare shell)

from scripts import _mcp_stdio  # noqa: E402  the ONE newline-delimited (spec) MCP stdio transport, shared by every server
from scripts import capability_retrieval_mcp_server as _capability_mcp  # noqa: E402
from src.teleon.observer import cli, sessions  # noqa: E402

PROTOCOL_VERSION = "2024-11-05"  # MCP protocol revision this server implements
SERVER_NAME = "aidevobserver"
SERVER_VERSION = "0.2.0"

# JSON-RPC 2.0 error codes — single-sourced from the shared transport (scripts._mcp_stdio). Parse errors are
# owned by _mcp_stdio.serve, so dispatch only references method-not-found + internal.
_METHOD_NOT_FOUND = _mcp_stdio.METHOD_NOT_FOUND
_INTERNAL_ERROR = _mcp_stdio.INTERNAL_ERROR
_INVALID_REQUEST = _mcp_stdio.INVALID_REQUEST
_INVALID_PARAMS = _mcp_stdio.INVALID_PARAMS

MAX_SESSION_PATH_CHARS = 4_096
MAX_SESSION_CONTRACT_CHARS = 8_192

# --- tool catalog (name + description + JSON Schema inputSchema) -------------------------------------------------
_SESSION_TARGET_PROPS = {
    "path": {"type": "string", "minLength": 1, "maxLength": MAX_SESSION_PATH_CHARS,
             "description": "Transcript file to review directly (wins over latest/cwd)."},
    "latest": {"type": "boolean", "description": "Use the most recent discovered session (default when no path)."},
    "cwd": {"type": "string", "minLength": 1, "maxLength": MAX_SESSION_PATH_CHARS,
            "description": "Project cwd to discover sessions for (default: server cwd)."},
    "registry_cwd": {"type": "string", "minLength": 1, "maxLength": MAX_SESSION_PATH_CHARS,
                     "description": "Optional repo root for opt-in local registry/source-ref enrichment."},
    "requested_input": {"type": "string", "maxLength": MAX_SESSION_CONTRACT_CHARS,
                        "description": "Optional requested input edge/contract for registry enrichment."},
    "requested_output": {"type": "string", "maxLength": MAX_SESSION_CONTRACT_CHARS,
                         "description": "Optional requested output edge/contract for registry enrichment."},
}

_SESSION_TOOLS = [
    {
        "name": "list_sessions",
        "description": "Discover Claude Code session transcripts for a project working directory "
                       "(read-only, metadata only: session_id/path/mtime/project, newest first).",
        "inputSchema": {
            "type": "object",
            "properties": {"cwd": _SESSION_TARGET_PROPS["cwd"]},
            "required": [],
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
            "required": [],
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
            "required": [],
            "additionalProperties": False,
        },
    },
]

# ONE product connection: session observation and capability retrieval share the same MCP transport. Keep the
# capability implementation in its owning module; this catalog composition is the only integration seam.
TOOLS = [*_SESSION_TOOLS, *_capability_mcp.TOOLS]


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
    return cli.review_path(
        _resolve_path(arguments),
        registry_cwd=arguments.get("registry_cwd"),
        requested_input=arguments.get("requested_input"),
        requested_output=arguments.get("requested_output"),
    )


def _tool_live_review(arguments: dict) -> dict:
    mode = arguments.get("mode") or cli.DEFAULT_LIVE_MODE
    if mode not in cli.LIVE_MODES:
        raise ToolError(f"mode must be one of {cli.LIVE_MODES}; got {mode!r}")
    return cli.live_path(_resolve_path(arguments), mode)


_SESSION_TOOL_HANDLERS = {
    "list_sessions": _tool_list_sessions,
    "review_session": _tool_review_session,
    "live_review": _tool_live_review,
}
_TOOL_HANDLERS = {**_capability_mcp._TOOL_HANDLERS, **_SESSION_TOOL_HANDLERS}  # noqa: SLF001


# --- JSON-RPC / MCP method handlers -----------------------------------------------------------------------------
def handle_initialize(params: dict) -> dict:
    # echo the client's protocolVersion when given (compat), else advertise ours
    client_pv = (params or {}).get("protocolVersion")
    if not isinstance(client_pv, str) or not client_pv.isprintable() or len(client_pv) > 64:
        client_pv = None
    return {
        "protocolVersion": client_pv or PROTOCOL_VERSION,
        "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
        "capabilities": {"tools": {}},
    }


def handle_tools_list(params: dict) -> dict:
    return {"tools": TOOLS}


def _session_tool_schema(name: str) -> dict | None:
    return next((tool["inputSchema"] for tool in _SESSION_TOOLS if tool["name"] == name), None)


def _public_text(value: object) -> str:
    return _capability_mcp._public_text(value)  # noqa: SLF001 - one shared sanitized MCP error surface


def handle_tools_call(params: object) -> dict:
    if not isinstance(params, dict):
        return {"content": [{"type": "text", "text": "tools/call params must be an object"}], "isError": True}
    name = params.get("name")
    arguments = params.get("arguments", {})
    if not isinstance(name, str) or name not in _TOOL_HANDLERS:
        return {"content": [{"type": "text", "text": "unknown tool"}], "isError": True}
    if arguments is None:
        arguments = {}
    # Capability handlers validate their owning schemas internally (including their Python-only fixture marker).
    # Session handlers had no such gate, so enforce exactly their advertised object schemas before any path read.
    if name in _SESSION_TOOL_HANDLERS:
        schema = _session_tool_schema(name)
        schema_failure = (
            _capability_mcp._schema_error(arguments, schema or {})  # noqa: SLF001 - shared stdlib validator
            if schema is not None
            else "tool schema unavailable"
        )
        if schema_failure:
            return {"content": [{"type": "text", "text": _public_text(schema_failure)}], "isError": True}
    handler = _TOOL_HANDLERS.get(name)
    try:
        result = handler(arguments)
        return {"content": [{"type": "text", "text": json.dumps(result, indent=2)}], "isError": False}
    except (ToolError, _capability_mcp.ToolError) as e:
        return {"content": [{"type": "text", "text": _public_text(e)}], "isError": True}
    except Exception:  # noqa: BLE001 — never expose transcript paths, exception types, or internal details
        return {"content": [{"type": "text", "text": "tool execution failed"}], "isError": True}


def _error(req_id, code: int, message: str) -> dict:
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}


def dispatch(request: dict) -> dict | None:
    """Route one JSON-RPC request -> a response dict, or None for notifications (requests with no `id`)."""
    if not isinstance(request, dict):
        return _error(None, _INVALID_REQUEST, "invalid request")
    method = request.get("method")
    params = request.get("params", {})
    req_id = request.get("id")
    is_notification = "id" not in request

    if not isinstance(method, str):
        return None if is_notification else _error(req_id, _INVALID_REQUEST, "invalid request")
    if params is None:
        params = {}
    if not isinstance(params, dict):
        return None if is_notification else _error(req_id, _INVALID_PARAMS, "params must be an object")

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
            return _error(req_id, _METHOD_NOT_FOUND, "method not found")
    except Exception:  # noqa: BLE001 — public transport errors are deliberately detail-free
        return None if is_notification else _error(req_id, _INTERNAL_ERROR, "internal error")
    return None if is_notification else {"jsonrpc": "2.0", "id": req_id, "result": result}


def serve(stdin=None, stdout=None) -> int:
    """The stdio main loop — delegates to the shared newline-delimited (MCP-spec) transport
    (scripts._mcp_stdio.serve): one JSON request per line, dispatch, write+flush non-None responses;
    a malformed line answers a -32700 parse error. Signature preserved for the self-test's stream injection."""
    return _mcp_stdio.serve(dispatch, stream_in=stdin, stream_out=stdout)


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
    capability_names = {tool["name"] for tool in _capability_mcp.TOOLS}
    expected_names = {"list_sessions", "review_session", "live_review"} | capability_names
    ck("tools/list returns the unified Observer + capability catalog", names == expected_names, str(names))
    ck("each tool has a JSON Schema inputSchema", all(t.get("inputSchema", {}).get("type") == "object" for t in listed))
    ck("each tool has a non-empty description", all(t.get("description") for t in listed))
    ck("every session schema rejects undeclared fields and declares required inputs",
       all(tool["inputSchema"].get("additionalProperties") is False
           and isinstance(tool["inputSchema"].get("required"), list)
           for tool in _SESSION_TOOLS))
    ck("session path/contract strings have explicit maximum lengths",
       all(
           "maxLength" in prop
           for prop in _SESSION_TARGET_PROPS.values()
           if prop.get("type") == "string"
       ))

    # synthetic transcript in a UNIQUE tmp dir, reviewed via tools/call (handlers called directly, no stdio)
    tmp = Path(tempfile.mkdtemp(prefix="aidevobserver_mcp_selftest_"))
    transcript = tmp / "synthetic.jsonl"
    transcript.write_text("\n".join(json.dumps(r) for r in _SYNTHETIC_TRANSCRIPT) + "\n")
    (tmp / "pdf_utils.py").write_text(
        "def parse_pdf_text(path: str) -> str:\n"
        "    \"\"\"Extract text from a PDF document.\"\"\"\n"
        "    return ''\n",
        encoding="utf-8",
    )
    # Unit isolation: the product default may expose the multi-million-row global primitive corpus. This proof
    # exercises MCP wiring and a tiny injected capability index; loading the global corpus here would make a
    # supposedly hermetic self-test consume gigabytes and compete with live grid/observer processes.
    from src.teleon.observer import registry_search as _registry_search
    previous_global_override = _registry_search._GLOBAL_PRIMITIVES_ENABLED_OVERRIDE  # noqa: SLF001
    _registry_search.set_global_primitives_enabled(False)
    try:
        call = handle_tools_call({"name": "review_session", "arguments": {"path": str(transcript)}})
        ck("tools/call review_session is not an error", call.get("isError") is False)
        ck("tools/call returns text content", call["content"][0]["type"] == "text")
        report = json.loads(call["content"][0]["text"])
        ck("review result serves_truth=false", report.get("serves_truth") is False)
        ck("review found candidate findings", report["summary"]["findings"] >= 1, str(report["summary"]["findings"]))
        ck("every finding is a governed candidate", all(
            f.get("candidate") is True and f.get("serves_truth") is False for f in report["report"]))

        from src.teleon.observer.registry_search import LOCAL_REGISTRY_ENV
        prev_registry = os.environ.get(LOCAL_REGISTRY_ENV)
        os.environ[LOCAL_REGISTRY_ENV] = "1"
        try:
            enriched_call = handle_tools_call({
                "name": "review_session",
                "arguments": {"path": str(transcript), "registry_cwd": str(tmp)},
            })
            enriched = json.loads(enriched_call["content"][0]["text"])
            enriched_blob = json.dumps(enriched, sort_keys=True)
            ck("review_session can attach opt-in local registry source refs through MCP",
               enriched_call.get("isError") is False
               and (enriched.get("local_registry") or {}).get("hits_attached", 0) >= 1
               and "parse_pdf_text" in enriched_blob,
               enriched_blob)
            ck("MCP registry enrichment stays candidate-only",
               enriched.get("serves_truth") is False
               and all(f.get("serves_truth") is False for f in enriched.get("report", [])),
               enriched_blob)
        finally:
            if prev_registry is None:
                os.environ.pop(LOCAL_REGISTRY_ENV, None)
            else:
                os.environ[LOCAL_REGISTRY_ENV] = prev_registry

        live = json.loads(handle_tools_call(
            {"name": "live_review", "arguments": {"path": str(transcript), "mode": "advisory"}})["content"][0]["text"])
        ck("live_review returns a surfaced list", isinstance(live.get("surfaced"), list))
        ck("live_review reports its mode + summary", live.get("mode") == "advisory" and "summary" in live)

        valid_session_args = {
            "list_sessions": {"cwd": str(tmp)},
            "review_session": {"path": str(transcript)},
            "live_review": {"path": str(transcript), "mode": "advisory"},
        }
        for tool_name, tool_args in valid_session_args.items():
            rejected = handle_tools_call({
                "name": tool_name,
                "arguments": {**tool_args, "undeclared_fixture_seam": True},
            })
            ck(f"{tool_name} rejects undeclared arguments before execution",
               rejected.get("isError") is True
               and "undeclared field" in rejected["content"][0]["text"])
        ck("session tools reject non-object arguments",
           handle_tools_call({"name": "list_sessions", "arguments": []}).get("isError") is True)
        ck("session path bounds are enforced before filesystem access",
           handle_tools_call({"name": "review_session", "arguments": {
               "path": "x" * (MAX_SESSION_PATH_CHARS + 1),
           }}).get("isError") is True)
        ck("session contract bounds are enforced",
           handle_tools_call({"name": "review_session", "arguments": {
               "path": str(transcript),
               "requested_input": "x" * (MAX_SESSION_CONTRACT_CHARS + 1),
           }}).get("isError") is True)
        ck("live_review mode enum is enforced by the advertised schema",
           handle_tools_call({"name": "live_review", "arguments": {
               "path": str(transcript), "mode": "invented",
           }}).get("isError") is True)
        private_path = "/private/absolute/path/that-must-not-leak/aidevobserver.jsonl"
        private_error = handle_tools_call({"name": "review_session", "arguments": {"path": private_path}})
        ck("unexpected session failures expose no exception type or absolute path",
           private_error.get("isError") is True
           and private_error["content"][0]["text"] == "tool execution failed"
           and private_path not in private_error["content"][0]["text"])

        # The product-level server must execute (not merely list) a capability tool through the same dispatch seam.
        search_call = handle_tools_call({
            "name": "primitive_search",
            "arguments": {
                "query": "ofac sanctions screening entityrecord",
                "limit": 3,
                "index": _capability_mcp._synthetic_search_index(),  # noqa: SLF001 - hermetic injection seam
            },
        })
        search_result = json.loads(search_call["content"][0]["text"])
        ck("unified MCP executes primitive_search through the capability engine",
           search_call.get("isError") is False
           and search_result.get("results", [{}])[0].get("primitive_id") == "prim:test:target")
        ck("unified capability results preserve the candidate boundary",
           search_result.get("candidate") is True and search_result.get("serves_truth") is False)

        bad = handle_tools_call({"name": "does_not_exist", "arguments": {}})
        ck("unknown tool sets isError", bad.get("isError") is True)

        # list_sessions tolerates a project with no sessions (read-only, graceful)
        empty = handle_tools_call({"name": "list_sessions", "arguments": {"cwd": "/no/such/project/xyz"}})
        ck("list_sessions tolerates none -> []", json.loads(empty["content"][0]["text"]) == [])
    finally:
        _registry_search.set_global_primitives_enabled(previous_global_override)
        shutil.rmtree(tmp, ignore_errors=True)

    # dispatch envelope + notification no-op
    resp = dispatch({"jsonrpc": "2.0", "id": 7, "method": "tools/list", "params": {}})
    ck("dispatch wraps a result in the JSON-RPC envelope",
       resp.get("jsonrpc") == "2.0" and resp.get("id") == 7 and "result" in resp)
    ck("notifications/initialized is a no-op (no response)",
       dispatch({"jsonrpc": "2.0", "method": "notifications/initialized"}) is None)
    ck("unknown method -> JSON-RPC method-not-found",
       dispatch({"jsonrpc": "2.0", "id": 8, "method": "bogus"})["error"]["code"] == _METHOD_NOT_FOUND)
    ck("non-object JSON-RPC params are rejected without internal details",
       dispatch({"jsonrpc": "2.0", "id": 9, "method": "tools/call", "params": []})["error"]["code"]
       == _INVALID_PARAMS)
    ck("non-object JSON-RPC requests are rejected",
       dispatch([])["error"]["code"] == _INVALID_REQUEST)  # type: ignore[arg-type]

    if fails:
        print(f"\nFAIL - aidevobserver_mcp_server: {len(fails)} of {checks} assertions failed")
        return 1
    print(f"PASS - aidevobserver_mcp_server: one stdlib MCP server over stdio exposes the unified Observer + "
          f"capability-retrieval catalog ({len(TOOLS)} tools) and executes both review_session and "
          f"primitive_search through tools/call; {checks} assertions; serves_truth=false; transcripts/source "
          f"corpus read-only (derived search checkpoint may advance).")
    return 0


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        return _self_test()
    return serve()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
