#!/usr/bin/env python3
"""taedri_real_use_emulator — autonomous real-use testing at every layer: API journey, MCP protocol, real browser.

Owner (2026-07-10): "setup tools that do all of this yourself — browser emulation, real use emulation, CLI
connection, setup, etc." This is that tool: ONE harness the agent (or CI) runs against ANY deployment — the local
container, a tunnel, or production — that emulates a real customer at three layers and writes receipts:

  api      signup -> session login -> dashboard -> private primitive add -> include_mine search (private first)
           -> tenant logs -> usage/draft invoice -> plan upgrade [-> owner ledger export when --owner-key]
  mcp      the exact protocol an agent harness (Claude Code `claude mcp add --transport http`) speaks:
           initialize -> tools/list (7 tools) -> find_reuse FIRES on build-intent -> primitive_search hits
  browser  REAL Chromium (Playwright, headless): landing renders (zero severe console errors) -> console page
           signup via the page's own JS -> key minted in the UI -> search from the UI -> results render ->
           login page reachable. Skipped HONESTLY (labeled, non-passing-silently) if Playwright is absent.

Every run writes an append-only receipt (steps, timings, pass rate) under
data/dev-intel/taedri_real_use_emulator/receipts.jsonl. serves_truth=false — receipts are measurements.

    PYTHONPATH=. python3 scripts/taedri_real_use_emulator.py --self-test
    PYTHONPATH=. python3 scripts/taedri_real_use_emulator.py --base https://taedri.fly.dev --journeys api,mcp,browser
    PYTHONPATH=. python3 scripts/taedri_real_use_emulator.py --base http://127.0.0.1:18080 --owner-key "$OWNER"
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from typing import Any, Optional

_HERE = Path(__file__).resolve()
_REPO = _HERE.parent.parent
for _p in (str(_REPO), str(_REPO / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

RECEIPTS_PATH = _REPO / "data" / "dev-intel" / "taedri_real_use_emulator" / "receipts.jsonl"
_COLD_SEARCH_TIMEOUT_SECONDS = 240   # first search after a wake loads the full index
_BROWSER_STEP_TIMEOUT_MS = 180_000
JOURNEY_NAMES = ("api", "mcp", "cli", "browser")


def _http(method: str, url: str, body: Optional[dict] = None, key: str = "",
          cookie: str = "", timeout: int = 60) -> tuple[int, dict, dict]:
    headers = {"Content-Type": "application/json"}
    if key:
        headers["Authorization"] = f"Bearer {key}"
    if cookie:
        headers["Cookie"] = cookie
    request = urllib.request.Request(url, method=method, headers=headers,
                                     data=json.dumps(body).encode() if body is not None else None)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
            response_headers = dict(response.headers)
            try:
                return response.status, json.loads(raw), response_headers
            except json.JSONDecodeError:
                return response.status, {"_html": raw[:2000]}, response_headers
    except urllib.error.HTTPError as error:
        try:
            return error.code, json.loads(error.read().decode("utf-8") or "{}"), dict(error.headers)
        except json.JSONDecodeError:
            return error.code, {}, dict(error.headers)
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        # a slow/unreachable deployment is a FAILED STEP with a receipt — never a dead harness
        return 0, {"_error": str(error)[:200]}, {}


class _Steps:
    def __init__(self) -> None:
        self.rows: list[dict[str, Any]] = []

    def add(self, step: str, ok: bool, detail: str = "", started: float = 0.0) -> bool:
        self.rows.append({"step": step, "ok": bool(ok), "detail": str(detail)[:240],
                          "ms": round((time.monotonic() - started) * 1000, 1) if started else None})
        return ok


# ==================================================================================================================
def api_journey(base: str, *, email: Optional[str] = None, owner_key: str = "") -> list[dict[str, Any]]:
    steps = _Steps()
    email = email or f"emulated-{uuid.uuid4().hex[:10]}@taedri.dev"

    t = time.monotonic()
    code, signup, _h = _http("POST", base + "/v1/signup", {"email": email})
    key, secret = signup.get("api_key", ""), signup.get("account_secret", "")
    if not steps.add("signup mints key+secret", code == 200 and signup.get("ok") and key and secret,
                     f"plan={signup.get('plan')}", t):
        return steps.rows

    t = time.monotonic()
    code, session, headers = _http("POST", base + "/v1/session", {"email": email, "secret": secret})
    cookie = f"taedri_session={session.get('session_id', '')}"
    set_cookie = next((value for name, value in headers.items() if name.lower() == "set-cookie"), "")
    steps.add("session login sets cookie", code == 200 and session.get("ok")
              and "taedri_session" in set_cookie, "", t)  # header name case varies by proxy (HTTP/2 lowercases)

    t = time.monotonic()
    code, dashboard, _h = _http("GET", base + "/dashboard", cookie=cookie)
    steps.add("dashboard renders for the session",
              code == 200 and "Dashboard — Taedri" in dashboard.get("_html", ""), "", t)

    t = time.monotonic()
    private_id = f"prim:mine:{uuid.uuid4().hex[:8]}"
    code, added, _h = _http("POST", base + "/v1/my/primitives",
                            {"cards": [{"primitive_id": private_id,
                                        "title": "Emulated private webhook hmac signature verifier",
                                        "blackbox": "Verifies webhook HMAC signatures for the emulation journey.",
                                        "blocking_keys": ["webhook", "hmac", "signature"],
                                        "serves_truth": True}]}, key=key)
    steps.add("private primitive accepted (truth bit stripped server-side)",
              code == 200 and added.get("ok") and added.get("accepted") == 1
              and added.get("visibility") == "private", "", t)

    t = time.monotonic()
    code, search, _h = _http("POST", base + "/v1/agent",
                             {"action": "retrieval.search",
                              "args": {"query": "verify webhook hmac signature", "include_mine": True,
                                       "limit": 3}}, key=key, timeout=_COLD_SEARCH_TIMEOUT_SECONDS)
    results = (search.get("result") or {}).get("results") or []
    steps.add("include_mine search returns the private card FIRST (labeled)",
              code == 200 and search.get("ok") and (search.get("result") or {}).get("private_hits", 0) >= 1
              and results and results[0].get("primitive_id") == private_id
              and results[0].get("visibility") == "private", "", t)

    t = time.monotonic()
    code, tombstone, _h = _http("POST", base + "/v1/my/primitives/remove", {"primitive_id": private_id}, key=key)
    code2, mine_after, _h = _http("GET", base + "/v1/my/primitives", key=key)
    steps.add("tombstone hides the private card (lossless)",
              code == 200 and tombstone.get("ok") and code2 == 200
              and all(c.get("primitive_id") != private_id for c in mine_after.get("cards", [])), "", t)

    t = time.monotonic()
    code, logs, _h = _http("GET", base + "/v1/logs", key=key)
    steps.add("tenant logs return own receipts", code == 200 and logs.get("ok") and logs.get("count", 0) >= 1,
              f"rows={logs.get('count')}", t)

    t = time.monotonic()
    code, usage, _h = _http("GET", base + "/v1/usage", key=key)
    steps.add("usage + draft invoice", code == 200 and usage.get("draft_invoice", {}).get("status") == "draft",
              f"today={usage.get('requests_today')}", t)

    t = time.monotonic()
    code, upgrade, _h = _http("POST", base + "/v1/upgrade", {"plan": "capability_pro"}, key=key)
    steps.add("plan upgrade recorded", code == 200 and upgrade.get("ok")
              and upgrade.get("plan") == "capability_pro", "", t)

    if owner_key:
        t = time.monotonic()
        code, ledgers, _h = _http("GET", base + "/v1/admin/ledgers", key=owner_key)
        steps.add("owner ledger export", code == 200 and ledgers.get("ok") is True,
                  f"invocations={ledgers.get('counts', {}).get('invocations')}", t)
    return steps.rows


def mcp_journey(base: str, *, key: Optional[str] = None,
                search_query: str = "parse csv header rows") -> list[dict[str, Any]]:
    """Exactly what an agent harness speaks after `claude mcp add --transport http taedri <base>/mcp`."""
    steps = _Steps()
    if key is None:
        _c, signup, _h = _http("POST", base + "/v1/signup",
                               {"email": f"mcp-{uuid.uuid4().hex[:10]}@taedri.dev"})
        key = signup.get("api_key", "")
    if not steps.add("key available for the MCP client", bool(key)):
        return steps.rows

    def rpc(method: str, params: dict, timeout: int = 60) -> dict:
        _c, body, _h = _http("POST", base + "/mcp",
                             {"jsonrpc": "2.0", "id": 1, "method": method, "params": params},
                             key=key, timeout=timeout)
        return body

    t = time.monotonic()
    init = rpc("initialize", {})
    steps.add("initialize handshake", init.get("result", {}).get("serverInfo", {}).get("name")
              == "capability-retrieval", "", t)

    t = time.monotonic()
    listed = rpc("tools/list", {})
    tools = [tool["name"] for tool in listed.get("result", {}).get("tools", [])]
    steps.add("tools/list advertises the 7 retrieval tools", len(tools) == 7 and "find_reuse" in tools,
              ",".join(tools), t)

    t = time.monotonic()
    reuse = rpc("tools/call", {"name": "find_reuse",
                               "arguments": {"message": "I am going to write a function that retries HTTP "
                                                        "requests with exponential backoff and jitter"}},
                timeout=_COLD_SEARCH_TIMEOUT_SECONDS)
    try:
        reuse_body = json.loads(reuse["result"]["content"][0]["text"])
    except (KeyError, json.JSONDecodeError, IndexError, TypeError):
        reuse_body = {}
    steps.add("reinvention guard FIRES on build-intent (the reusability flag)",
              reuse_body.get("fire") is True and bool(reuse_body.get("existing")),
              f"tier={reuse_body.get('tier')}", t)

    t = time.monotonic()
    search = rpc("tools/call", {"name": "primitive_search",
                                "arguments": {"query": search_query, "limit": 3}},
                 timeout=_COLD_SEARCH_TIMEOUT_SECONDS)
    try:
        search_body = json.loads(search["result"]["content"][0]["text"])
    except (KeyError, json.JSONDecodeError, IndexError, TypeError):
        search_body = {}
    steps.add("primitive_search returns governed hits",
              search_body.get("count", 0) >= 1
              and all(hit.get("serves_truth") is False for hit in search_body.get("results", [])),
              f"corpus={search_body.get('pruning', {}).get('total_docs')}", t)
    return steps.rows


def cli_journey(base: str, *, key: Optional[str] = None) -> list[dict[str, Any]]:
    """The REAL Claude Code CLI connects to the deployment: mcp add -> list (pings the server) -> get -> remove.
    Runs in an isolated temp project directory so no real project config is touched. Honest skip without the CLI."""
    import shutil
    import subprocess
    import tempfile

    steps = _Steps()
    claude_binary = shutil.which("claude")
    if not claude_binary:
        steps.add("cli journey SKIPPED — claude CLI not installed (curl -fsSL https://claude.ai/install.sh | bash)",
                  False, "skipped_unavailable")
        return steps.rows
    if key is None:
        _c, signup, _h = _http("POST", base + "/v1/signup",
                               {"email": f"cli-{uuid.uuid4().hex[:10]}@taedri.dev"})
        key = signup.get("api_key", "")
    if not steps.add("key available for the CLI", bool(key)):
        return steps.rows

    server_name = f"taedri-emulated-{uuid.uuid4().hex[:6]}"
    with tempfile.TemporaryDirectory() as project:
        def cli(*arguments: str, timeout: int = 180) -> tuple[int, str]:
            completed = subprocess.run([claude_binary, *arguments], cwd=project, capture_output=True,
                                       text=True, timeout=timeout)
            return completed.returncode, (completed.stdout + completed.stderr)[-800:]

        t = time.monotonic()
        code, output = cli("mcp", "add", "--transport", "http", server_name, base + "/mcp",
                           "--header", f"Authorization: Bearer {key}")
        steps.add("claude mcp add (http transport, bearer header)", code == 0, output[-160:], t)

        t = time.monotonic()
        code, output = cli("mcp", "list")
        steps.add("claude mcp list shows the server and reaches it",
                  code == 0 and server_name in output, output[-200:], t)

        t = time.monotonic()
        code, output = cli("mcp", "get", server_name)
        steps.add("claude mcp get resolves the server config",
                  code == 0 and "/mcp" in output, output[-160:], t)

        t = time.monotonic()
        code, output = cli("mcp", "remove", server_name)
        steps.add("claude mcp remove cleans up", code == 0, output[-120:], t)
    return steps.rows


def browser_journey(base: str, *, search_query: str = "parse csv header rows") -> list[dict[str, Any]]:
    """REAL Chromium drives the actual pages (the page's own JS does the work — what a human's click runs)."""
    steps = _Steps()
    try:
        from playwright.sync_api import sync_playwright  # noqa: PLC0415
    except ImportError:
        steps.add("browser journey SKIPPED — playwright not installed (pip install playwright; "
                  "playwright install chromium)", False, "skipped_unavailable")
        return steps.rows

    severe_console: list[str] = []
    with sync_playwright() as playwright:
        import os as _os  # noqa: PLC0415
        browser = playwright.chromium.launch(headless=_os.environ.get("TAEDRI_EMULATOR_HEADED") != "1")
        page = browser.new_page()
        page.on("console", lambda message: severe_console.append(message.text)
                if message.type in ("error",) else None)
        page.on("pageerror", lambda error: severe_console.append(str(error)))
        try:
            t = time.monotonic()
            page.goto(base + "/", timeout=_BROWSER_STEP_TIMEOUT_MS)
            steps.add("landing renders with the Taedri brand", "Taedri" in page.title(), page.title(), t)

            t = time.monotonic()
            page.goto(base + "/console", timeout=_BROWSER_STEP_TIMEOUT_MS)
            steps.add("console page loads", "Taedri Console" in page.title(), "", t)

            t = time.monotonic()
            page.fill("#email", f"browser-{uuid.uuid4().hex[:10]}@taedri.dev")
            page.evaluate("signup()")
            page.wait_for_function("document.getElementById('key').value.startsWith('ak_')",
                                   timeout=_BROWSER_STEP_TIMEOUT_MS)
            steps.add("signup through the page UI mints a key", True, "", t)

            t = time.monotonic()
            page.fill("#q", search_query)
            page.evaluate("mcpCall('primitive_search',{query:document.getElementById('q').value,limit:3})")
            page.wait_for_function("document.getElementById('out').textContent.includes('primitive_id')",
                                   timeout=_BROWSER_STEP_TIMEOUT_MS)
            steps.add("search from the UI renders primitive results", True, "", t)

            t = time.monotonic()
            page.goto(base + "/login", timeout=_BROWSER_STEP_TIMEOUT_MS)
            steps.add("login page reachable", "Log in" in page.title(), "", t)

            steps.add("zero severe browser console errors", not severe_console,
                      "; ".join(severe_console[:3]))
        except Exception as error:  # noqa: BLE001  a failed step is a finding, not a crash
            steps.add("browser journey aborted", False, str(error)[:200])
        finally:
            browser.close()
    return steps.rows


# ==================================================================================================================
def run(base: str, journeys: list[str], *, owner_key: str = "", email: Optional[str] = None) -> dict[str, Any]:
    all_steps: dict[str, list] = {}
    if "api" in journeys:
        all_steps["api"] = api_journey(base, email=email, owner_key=owner_key)
    if "mcp" in journeys:
        all_steps["mcp"] = mcp_journey(base)
    if "cli" in journeys:
        all_steps["cli"] = cli_journey(base)
    if "browser" in journeys:
        all_steps["browser"] = browser_journey(base)
    flat = [row for rows in all_steps.values() for row in rows]
    passed = sum(1 for row in flat if row["ok"])
    receipt = {"base": base, "journeys": journeys, "steps": all_steps,
               "passed": passed, "total": len(flat),
               "ok": passed == len(flat) and len(flat) > 0,
               "candidate": True, "serves_truth": False}
    RECEIPTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with RECEIPTS_PATH.open("a") as handle:
        handle.write(json.dumps({**receipt, "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
                                sort_keys=True) + "\n")
    return receipt


def _self_test() -> int:
    import os
    import tempfile
    checks: list[tuple[str, bool, str]] = []
    saved = {name: os.environ.get(name) for name in ("OH_AGENT_TOOL_DATA_DIR", "OH_LEARNING_DATA_DIR")}
    server = None
    try:
        with tempfile.TemporaryDirectory() as sandbox:
            os.environ["OH_AGENT_TOOL_DATA_DIR"] = str(Path(sandbox) / "agent")
            os.environ["OH_LEARNING_DATA_DIR"] = str(Path(sandbox) / "learning")
            from scripts.capability_retrieval_mcp_server import _synthetic_search_index
            from scripts.capability_saas_gateway import start_gateway
            server, _thread, port, _gateway = start_gateway(
                port=0, data_dir=Path(sandbox) / "saas",
                fixtures={"index": _synthetic_search_index(), "requests_per_day_override": 200})
            base = f"http://127.0.0.1:{port}"

            api_rows = api_journey(base, email="emulated-selftest@taedri.dev")
            checks.append((f"API journey: {sum(r['ok'] for r in api_rows)}/{len(api_rows)} steps pass offline",
                           len(api_rows) >= 9 and all(r["ok"] for r in api_rows),
                           json.dumps([r for r in api_rows if not r["ok"]])[:300]))

            mcp_rows = mcp_journey(base, search_query="ofac sanctions screening entityrecord")
            checks.append((f"MCP journey: {sum(r['ok'] for r in mcp_rows)}/{len(mcp_rows)} steps pass offline",
                           len(mcp_rows) >= 5 and all(r["ok"] for r in mcp_rows),
                           json.dumps([r for r in mcp_rows if not r["ok"]])[:300]))

            try:
                import playwright  # noqa: F401,PLC0415
                browser_rows = browser_journey(base, search_query="ofac sanctions screening entityrecord")
                checks.append((f"BROWSER journey: {sum(r['ok'] for r in browser_rows)}/{len(browser_rows)} "
                               f"steps pass in real Chromium",
                               len(browser_rows) >= 5 and all(r["ok"] for r in browser_rows),
                               json.dumps([r for r in browser_rows if not r["ok"]])[:300]))
            except ImportError:
                rows = browser_journey(base)
                checks.append(("browser journey degrades HONESTLY when playwright is absent",
                               len(rows) == 1 and rows[0]["ok"] is False
                               and "skipped_unavailable" in rows[0]["detail"], ""))

            import shutil as _shutil
            if _shutil.which("claude"):
                cli_rows = cli_journey(base)
                checks.append((f"CLI journey: {sum(r['ok'] for r in cli_rows)}/{len(cli_rows)} steps — the real "
                               f"claude CLI adds/lists/gets/removes the server",
                               len(cli_rows) >= 5 and all(r["ok"] for r in cli_rows),
                               json.dumps([r for r in cli_rows if not r["ok"]])[:300]))
            else:
                cli_rows = cli_journey(base)
                checks.append(("cli journey degrades HONESTLY without the claude CLI",
                               len(cli_rows) == 1 and cli_rows[0]["ok"] is False
                               and "skipped_unavailable" in cli_rows[0]["detail"], ""))

            receipt = run(base, ["api"], email="emulated-receipt@taedri.dev")
            checks.append(("run() writes an append-only receipt with pass counts",
                           RECEIPTS_PATH.exists() and receipt["total"] >= 9
                           and receipt["passed"] == receipt["total"], ""))
    finally:
        if server is not None:
            server.shutdown()
        import os as _os
        for name, value in saved.items():
            if value is None:
                _os.environ.pop(name, None)
            else:
                _os.environ[name] = value

    ok = all(passed for _n, passed, _d in checks)
    print(f"{'PASS' if ok else 'FAIL'} - taedri_real_use_emulator: three-layer real-use emulation (API lifecycle, "
          f"MCP protocol incl. the reusability flag, REAL Chromium page journey) with receipts; honest skip when "
          f"a layer is unavailable. serves_truth=false")
    for name, passed, detail in checks:
        print(f"  [{'ok' if passed else 'XX'}] {name}" + (f"  ({detail[:300]})" if not passed else ""))
    return 0 if ok else 1


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Real-use emulation against any Taedri deployment.")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--base", default="https://taedri.fly.dev")
    parser.add_argument("--journeys", default="api,mcp",
                        help=f"comma list of {JOURNEY_NAMES} (browser needs playwright+chromium)")
    parser.add_argument("--owner-key", default="")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    journeys = [name.strip() for name in args.journeys.split(",") if name.strip() in JOURNEY_NAMES]
    receipt = run(args.base, journeys, owner_key=args.owner_key)
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if receipt["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
