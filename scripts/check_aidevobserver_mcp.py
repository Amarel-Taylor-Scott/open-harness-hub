#!/usr/bin/env python3
"""check_aidevobserver_mcp — proof for the AIDevObserver MCP server + CLI bridge + Claude session discovery.

Drives the whole surface on a SYNTHETIC transcript (a UNIQUE tmp dir + the OBSERVER_PROJECTS_DIR override, so it
never touches the real ~/.claude): session discovery (tolerating none), the CLI review/live path (review_path /
live_path + the argparse `main`), and the MCP JSON-RPC handlers (initialize / tools/list / tools/call). Asserts
the governed shapes — serves_truth=false, candidate findings, the 3 tool names, a live `surfaced` list — and that
the registration command is documented. serves_truth=false; read-only (synthetic content only).

  PYTHONPATH=. python3 scripts/check_aidevobserver_mcp.py --self-test
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

import scripts.aidevobserver_mcp_server as mcp  # noqa: E402
from src.teleon.observer import cli, sessions  # noqa: E402

# a Claude-shape transcript that reliably fires the reinvention catch (pdf / address) -> >= 1 candidate finding
_SYNTHETIC = [
    {"type": "mode", "mode": "opus"},  # noise the capture seam drops
    {"type": "user", "message": {"role": "user", "content": "let me write a pdf parser from scratch"}},
    {"type": "user", "message": {"role": "user", "content": "I'll implement my own address validation"}},
    {"type": "assistant", "message": {"role": "assistant", "content": [
        {"type": "thinking", "thinking": "private reasoning"},
        {"type": "text", "text": "ok, writing it"},
        {"type": "tool_use", "name": "Write", "input": {"file_path": "/x/pdf.py", "content": "def parse(): ..."}}]}},
]


def _self_test() -> int:
    fails: list[str] = []
    checks = 0

    def ck(name: str, ok: bool, detail: str = "") -> None:
        nonlocal checks
        checks += 1
        if not ok:
            fails.append(name)
            print(f"  [XX] {name}{(' — ' + detail) if detail else ''}")

    # 1) discovery tolerates a project with no sessions; real-cwd discovery is metadata-only (no content read)
    ck("discover_sessions tolerates none -> []", sessions.discover_sessions("/no/such/project/xyz") == [])
    ck("latest_session tolerates none -> None", sessions.latest_session("/no/such/project/xyz") is None)
    ck("discover_sessions(real cwd) returns a list", isinstance(sessions.discover_sessions(), list))

    # registration command is documented in the server module (a task contract)
    doc = mcp.__doc__ or ""
    ck("server docstring documents the `claude mcp add` command",
       "claude mcp add aidevobserver -- python3 " in doc and "aidevobserver_mcp_server.py" in doc)

    # 2) isolated synthetic projects tree (unique tmp dir + env override -> never touches ~/.claude)
    tmp = Path(tempfile.mkdtemp(prefix="check_aidevobserver_mcp_"))
    fake_cwd = "/home/tester/aidevobserver.demo"
    proj = tmp / sessions.encode_cwd(fake_cwd)
    proj.mkdir(parents=True)
    transcript = proj / "synthetic-session.jsonl"
    transcript.write_text("\n".join(json.dumps(r) for r in _SYNTHETIC) + "\n")

    prev = os.environ.get("OBSERVER_PROJECTS_DIR")
    os.environ["OBSERVER_PROJECTS_DIR"] = str(tmp)
    try:
        found = sessions.discover_sessions(fake_cwd)
        ck("discovers the synthetic session", len(found) == 1 and found[0]["session_id"] == "synthetic-session")
        latest = sessions.latest_session(fake_cwd)
        ck("latest_session resolves to the synthetic transcript", latest == str(transcript))

        # 3) CLI module functions: review_path + the argparse main (end-to-end), both governed
        report = cli.review_path(latest)
        ck("cli.review_path serves_truth=false", report.get("serves_truth") is False)
        ck("cli.review_path found candidate findings", report["summary"]["findings"] >= 1,
           str(report["summary"]["findings"]))
        ck("every CLI finding is a governed candidate",
           all(f.get("candidate") is True and f.get("serves_truth") is False for f in report["report"]))

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = cli.main(["review", "--latest", "--cwd", fake_cwd, "--json"])
        cli_out = json.loads(buf.getvalue())
        ck("cli `review --latest --json` exits 0", rc == 0)
        ck("cli review --json prints the raw review dict (serves_truth=false)", cli_out.get("serves_truth") is False)
        ck("cli review --json == review_path (same engine, JSON-normalized)",
           cli_out == json.loads(json.dumps(report)))

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = cli.main(["live", "--latest", "--cwd", fake_cwd, "--mode", "advisory", "--json"])
        cli_live = json.loads(buf.getvalue())
        ck("cli `live --json` exits 0", rc == 0)
        ck("cli live returns a surfaced list + summary",
           isinstance(cli_live.get("surfaced"), list) and "summary" in cli_live)

        # 4) MCP JSON-RPC handlers: initialize / tools/list / tools/call (over the same synthetic session)
        init = mcp.handle_initialize({"protocolVersion": mcp.PROTOCOL_VERSION})
        ck("MCP initialize advertises serverInfo + tools capability",
           init["serverInfo"]["name"] == mcp.SERVER_NAME and "tools" in init["capabilities"])

        tool_names = [t["name"] for t in mcp.handle_tools_list({})["tools"]]
        ck("MCP tools/list returns the 3 tool names",
           set(tool_names) == {"list_sessions", "review_session", "live_review"}, str(tool_names))

        call = mcp.handle_tools_call({"name": "review_session", "arguments": {"latest": True, "cwd": fake_cwd}})
        ck("MCP tools/call review_session is not an error", call.get("isError") is False)
        mcp_report = json.loads(call["content"][0]["text"])
        ck("MCP review_session serves_truth=false + candidate findings",
           mcp_report.get("serves_truth") is False and bool(mcp_report["report"])
           and all(f.get("candidate") is True for f in mcp_report["report"]))

        live_call = mcp.handle_tools_call(
            {"name": "live_review", "arguments": {"latest": True, "cwd": fake_cwd, "mode": "advisory"}})
        mcp_live = json.loads(live_call["content"][0]["text"])
        ck("MCP live_review returns a surfaced list", isinstance(mcp_live.get("surfaced"), list))

        ls_call = mcp.handle_tools_call({"name": "list_sessions", "arguments": {"cwd": fake_cwd}})
        ck("MCP list_sessions returns the discovered session",
           len(json.loads(ls_call["content"][0]["text"])) == 1)
    finally:
        if prev is None:
            os.environ.pop("OBSERVER_PROJECTS_DIR", None)
        else:
            os.environ["OBSERVER_PROJECTS_DIR"] = prev
        shutil.rmtree(tmp, ignore_errors=True)

    # 5) the server's own self-test passes (integration; suppress its chatter)
    with contextlib.redirect_stdout(io.StringIO()):
        server_rc = mcp._self_test()
    ck("aidevobserver_mcp_server --self-test passes", server_rc == 0)

    if fails:
        print(f"\nFAIL - check_aidevobserver_mcp: {len(fails)} of {checks} assertions failed: {fails}")
        return 1
    print(f"PASS - check_aidevobserver_mcp: session discovery + CLI bridge + MCP server (3 tools, governed review/"
          f"live) over a synthetic transcript; {checks} assertions; serves_truth=false, read-only.")
    return 0


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        return _self_test()
    print("usage: check_aidevobserver_mcp.py --self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
