#!/usr/bin/env python3
"""scripts._mcp_stdio — the ONE MCP stdio transport (framing + serve loop), single-sourced.

MCP's stdio transport is **newline-delimited JSON**: each JSON-RPC message is exactly one line with no
embedded newline (modelcontextprotocol.io — transports, stdio). LSP-style ``Content-Length:`` framing is
**not** the MCP stdio spec — a server that reads Content-Length blocks forever against a spec client
(Claude Code, Cursor, …) that writes a bare JSON line, so it never answers a single request. This module
exists because the in-repo MCP servers had DIVERGED: the two gateways (baltor/teleon) spoke Content-Length
and were broken for their only wired client, while three others spoke NDJSON. One transport, one place,
spec-correct — protocol/dispatch stays per-server (separation of concerns).

  read_message(stream=sys.stdin)  -> dict | None   one JSON object per line; None at EOF; ValueError on bad JSON
  write_message(obj, stream=sys.stdout) -> None      compact JSON + "\n" + flush (the spec; no embedded newline)
  serve(handler, ...)                                read -> handler(request) -> write loop; parse error -> -32700

Text streams throughout (NDJSON is line-oriented text; matches the three servers that were already
correct). A handler returning None = a notification with no reply. A handler exception becomes a JSON-RPC
-32603 so a dispatch bug never kills the transport. serves_truth=false — this moves bytes, never truth.

    PYTHONPATH=. python3 scripts/_mcp_stdio.py --self-test
"""
from __future__ import annotations

import json
import sys
from typing import Callable, Optional, TextIO

# JSON-RPC 2.0 reserved error codes (single source; servers import these instead of re-typing the ints).
PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603


def error_response(msg_id, code: int, message: str) -> dict:
    """A JSON-RPC 2.0 error object. ``msg_id`` is echoed (null when the id is unknown, e.g. a parse error)."""
    return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": code, "message": message}}


def read_message(stream: Optional[TextIO] = None) -> Optional[dict]:
    """Read ONE newline-delimited JSON-RPC message (the MCP stdio spec) from ``stream`` (default stdin).

    Returns the parsed object, or None at EOF. Blank separator lines are skipped. A malformed line raises
    ``ValueError`` (``json.JSONDecodeError``) — the caller answers a -32700 parse error and continues.
    Bytes lines (if a caller passed a binary stream) are decoded as UTF-8 so framing is transport-safe.
    """
    reader = stream if stream is not None else sys.stdin
    while True:
        line = reader.readline()
        if line == "" or line == b"":          # EOF
            return None
        if isinstance(line, (bytes, bytearray)):
            line = line.decode("utf-8")
        if line.strip() == "":                  # blank separator -> next message
            continue
        return json.loads(line)


def write_message(obj: dict, stream: Optional[TextIO] = None) -> None:
    """Write ONE JSON-RPC message as NDJSON (the spec): compact JSON + a single trailing "\n" + flush.
    ``json.dumps`` with default separators never emits an embedded newline, so one message = one line."""
    writer = stream if stream is not None else sys.stdout
    writer.write(json.dumps(obj) + "\n")
    writer.flush()


def serve(
    handler: Callable[[dict], Optional[dict]],
    *,
    stream_in: Optional[TextIO] = None,
    stream_out: Optional[TextIO] = None,
) -> int:
    """The stdio serve loop, shared by every in-repo MCP server.

    Reads a request, dispatches to ``handler(request) -> response | None`` (None = a notification, no
    reply), and writes the response as NDJSON. A malformed line answers a JSON-RPC parse error (-32700)
    and keeps serving; a handler exception becomes -32603 (a dispatch bug must never kill the transport).
    Returns 0 at EOF. The per-server protocol (initialize / tools/list / tools/call) lives in ``handler``.
    """
    rin = stream_in if stream_in is not None else sys.stdin
    rout = stream_out if stream_out is not None else sys.stdout
    while True:
        try:
            request = read_message(rin)
        except ValueError:
            write_message(error_response(None, PARSE_ERROR, "parse error"), rout)
            continue
        if request is None:
            return 0
        try:
            response = handler(request)
        except Exception as exc:  # noqa: BLE001 — a handler bug must not crash the transport
            response = error_response(
                request.get("id") if isinstance(request, dict) else None,
                INTERNAL_ERROR,
                f"{type(exc).__name__}: {exc}",
            )
        if response is not None:
            write_message(response, rout)


def _self_test() -> int:
    import io

    checks: list[tuple[str, bool]] = []

    # A. read_message parses NDJSON, skips blanks, returns None at EOF.
    r = io.StringIO('{"jsonrpc":"2.0","id":1,"method":"ping"}\n\n{"id":2}\n')
    m1 = read_message(r)
    m2 = read_message(r)  # blank line skipped
    m3 = read_message(r)  # EOF
    checks.append(("read_message parses line 1", m1 == {"jsonrpc": "2.0", "id": 1, "method": "ping"}))
    checks.append(("read_message skips blank, parses line 2", m2 == {"id": 2}))
    checks.append(("read_message returns None at EOF", m3 is None))

    # B. read_message raises ValueError on a malformed line (caller answers -32700).
    try:
        read_message(io.StringIO("{not json}\n"))
        checks.append(("read_message raises on malformed JSON", False))
    except ValueError:
        checks.append(("read_message raises on malformed JSON", True))

    # C. write_message emits compact JSON + exactly one trailing newline, no embedded newline.
    w = io.StringIO()
    write_message({"jsonrpc": "2.0", "id": 1, "result": {"a": 1, "b": "x\ny"}}, w)
    out = w.getvalue()
    checks.append(("write_message ends with a single newline", out.endswith("\n") and out.count("\n") == 1))
    checks.append(("write_message round-trips", json.loads(out) == {"jsonrpc": "2.0", "id": 1, "result": {"a": 1, "b": "x\ny"}}))

    # D. serve: read -> dispatch -> write; notification (None) is not answered; EOF returns 0.
    sin = io.StringIO('{"id":1,"method":"echo","params":{"v":7}}\n{"method":"note"}\n{"id":2,"method":"echo","params":{"v":9}}\n')
    sout = io.StringIO()

    def handler(req):
        if req.get("id") is None:
            return None  # notification
        return {"jsonrpc": "2.0", "id": req["id"], "result": req.get("params", {}).get("v")}

    rc = serve(handler, stream_in=sin, stream_out=sout)
    replies = [json.loads(ln) for ln in sout.getvalue().splitlines() if ln.strip()]
    checks.append(("serve returns 0 at EOF", rc == 0))
    checks.append(("serve answers requests, skips the notification", replies == [
        {"jsonrpc": "2.0", "id": 1, "result": 7},
        {"jsonrpc": "2.0", "id": 2, "result": 9},
    ]))

    # E. serve turns a malformed line into a -32700 and keeps serving the next valid request.
    sin2 = io.StringIO('{bad}\n{"id":5,"method":"echo","params":{"v":1}}\n')
    sout2 = io.StringIO()
    serve(handler, stream_in=sin2, stream_out=sout2)
    replies2 = [json.loads(ln) for ln in sout2.getvalue().splitlines() if ln.strip()]
    checks.append(("serve: bad line -> -32700 then keeps serving", (
        len(replies2) == 2
        and replies2[0]["error"]["code"] == PARSE_ERROR
        and replies2[1] == {"jsonrpc": "2.0", "id": 5, "result": 1}
    )))

    # F. serve: a handler exception becomes -32603 (transport survives).
    sin3 = io.StringIO('{"id":1,"method":"boom"}\n')
    sout3 = io.StringIO()

    def boom(_req):
        raise RuntimeError("kaboom")

    serve(boom, stream_in=sin3, stream_out=sout3)
    err = json.loads(sout3.getvalue())
    checks.append(("serve: handler exception -> -32603 (id echoed)", (
        err["id"] == 1 and err["error"]["code"] == INTERNAL_ERROR and "kaboom" in err["error"]["message"]
    )))

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print("\nPASS - _mcp_stdio: ONE newline-delimited (spec) MCP stdio transport — read/write/serve, "
          "parse error -> -32700, handler crash -> -32603, notifications unanswered. No Content-Length.")
    return 0


if __name__ == "__main__":
    raise SystemExit(_self_test() if "--self-test" in sys.argv else _self_test())
