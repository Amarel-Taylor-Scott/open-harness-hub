#!/usr/bin/env python3
"""scripts.realistic_session_harness — a REALISTIC multi-turn, tool-using agentic session (what a senior dev
actually does), with FULL-SESSION token accounting, to measure primitive-DB savings where the tokens really go.

Owner (2026-07-09): are we doing long-context, fully-realistic, senior-dev-scale tasks that burn the tokens a real
agentic session burns, and measuring how much the DB saves THERE? The prior harnesses measured single-shot output
(~100-1100 tok) — the rounding error. A real session is INPUT-dominated: the growing conversation + read file
contents are re-sent EVERY turn across many turns, so input cost compounds with working-set size and session length.
This harness measures that mechanism directly:

  * a real multi-file WORKING SET (an existing service missing a feature) + a HIDDEN test
  * a text-tool agentic loop: LIST / READ <path> / WRITE <path> / TEST / PRIMITIVE <query> (WITH lane) / DONE
  * the FULL conversation is re-sent every turn -> input tokens GROW turn over turn (the realistic cost)
  * accounting sums input+output across ALL turns = the true session cost
  * two lanes: WITHOUT the DB (agent re-derives the capability from scratch) vs WITH (agent fetches a VERIFIED
    primitive via the PRIMITIVE tool and writes it verbatim) -> compare total session tokens + turns + pass

serves_truth=false. Report observed session measurements only; do not extrapolate a small run into a corpus- or
portfolio-scale savings claim.

    python3 scripts/realistic_session_harness.py --self-test
    python3 scripts/realistic_session_harness.py --live --provider openrouter --model z-ai/glm-4.6 --max-turns 25
"""
from __future__ import annotations

import sys
from pathlib import Path

_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots, resource  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import ast  # noqa: E402
import hashlib  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import re  # noqa: E402
import subprocess  # noqa: E402
import tempfile  # noqa: E402
from pathlib import PurePosixPath  # noqa: E402
from typing import Any, Callable  # noqa: E402

from scripts.reuse_experiment_policy import CODEX_OPENROUTER_KEY_COUNT, REPORTING_MIN_N  # noqa: E402

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
BENCHMARK_KIND = "realistic_agentic_session"
TASK_FAMILY = "webhook_hmac_feature_session__stdlib_http"
_CHARS_PER_TOKEN = 4  # proxy token count for accounting when a transport doesn't return usage (labeled as such)
VERIFIED_PRIMITIVE_MODULE = "verified_primitives.py"
VERIFIED_PRIMITIVE_IMPORT = "from verified_primitives import verify_webhook_signature"
SESSION_TRANSPORT_SYSTEM = "Follow the user's text-tool protocol exactly. Return one tool call and no prose."
PRIMITIVE_RECEIPT_ENV = "AIDEV_PRIMITIVE_RECEIPT"

# ── the WORKING SET: an existing event-ingest service MISSING HMAC signature verification (the feature to add) ──
_EXISTING_APP = (
    "import argparse, json, os\n"
    "from http.server import BaseHTTPRequestHandler, HTTPServer\n"
    "from store import EventStore\n\n"
    "store = EventStore()\n\n"
    "class Handler(BaseHTTPRequestHandler):\n"
    "    def _send(self, code, obj):\n"
    "        b = json.dumps(obj).encode(); self.send_response(code)\n"
    "        self.send_header('Content-Length', str(len(b))); self.end_headers(); self.wfile.write(b)\n"
    "    def do_GET(self):\n"
    "        if self.path == '/health':\n"
    "            return self._send(200, {'status': 'ok', 'healthy': True, 'events': store.count()})\n"
    "        return self._send(404, {'error': 'not_found'})\n"
    "    def do_POST(self):\n"
    "        # TODO(feature): verify the X-Signature HMAC-SHA256 over the raw body using the WEBHOOK_SECRET env var\n"
    "        # BEFORE accepting. On mismatch -> 401 {'error':'bad_signature'}. On valid -> store + 202 {'status':'accepted'}.\n"
    "        n = int(self.headers.get('Content-Length', 0) or 0)\n"
    "        body = self.rfile.read(n) if n else b''\n"
    "        event = json.loads(body or b'{}')\n"
    "        store.add(event)\n"
    "        return self._send(202, {'status': 'accepted'})\n"
    "    def log_message(self, *a):\n"
    "        pass\n\n"
    "def main():\n"
    "    ap = argparse.ArgumentParser(); ap.add_argument('--port', type=int, default=8000)\n"
    "    HTTPServer(('127.0.0.1', ap.parse_args().port), Handler).serve_forever()\n\n"
    "if __name__ == '__main__':\n"
    "    main()\n"
)
_EXISTING_STORE = (
    "class EventStore:\n"
    "    def __init__(self):\n        self._events = []\n"
    "    def add(self, event):\n        self._events.append(event)\n"
    "    def count(self):\n        return len(self._events)\n"
)
WORKING_SET = {"app.py": _EXISTING_APP, "store.py": _EXISTING_STORE,
               "README.md": "# Event Ingest Service\nPOST events to /, GET /health. Boots: python app.py --port N.\n"}

TASK = ("Add HMAC-SHA256 signature verification to POST /. The raw request body must be verified against the "
        "hex signature in the X-Signature header using a shared secret from the WEBHOOK_SECRET environment "
        "variable (constant-time compare). On mismatch return HTTP 401 {\"error\": \"bad_signature\"} and do NOT "
        "store. On a valid signature, store the event and return HTTP 202 {\"status\": \"accepted\"}. Keep /health "
        "working. When the hidden tests pass, respond DONE.")

# The semantic core is independently digestible; the mounted module adds only
# an optional local execution receipt.  The receipt contains no request body,
# secret, signature, path, or other user data.
_VERIFIED_PRIMITIVE_CORE = (
    "def verify_webhook_signature(secret: str, body: bytes, signature_hex: str) -> bool:\n"
    "    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()\n"
    "    return hmac.compare_digest(expected, signature_hex or '')\n"
)
VERIFIED_PRIMITIVE_CORE_DIGEST = hashlib.sha256(_VERIFIED_PRIMITIVE_CORE.encode()).hexdigest()
_VERIFIED_PRIMITIVE_SOURCE = (
    "import hashlib, hmac, json, os\n\n"
    f"PRIMITIVE_CORE_DIGEST = {VERIFIED_PRIMITIVE_CORE_DIGEST!r}\n"
    "_primitive_calls = 0\n\n"
    "def verify_webhook_signature(secret: str, body: bytes, signature_hex: str) -> bool:\n"
    "    '''Constant-time HMAC-SHA256 verify of a webhook body. VERIFIED primitive.'''\n"
    "    global _primitive_calls\n"
    "    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()\n"
    "    result = hmac.compare_digest(expected, signature_hex or '')\n"
    "    _primitive_calls += 1\n"
    f"    receipt_path = os.environ.get({PRIMITIVE_RECEIPT_ENV!r})\n"
    "    if receipt_path:\n"
    "        try:\n"
    "            with open(receipt_path, 'w', encoding='utf-8') as handle:\n"
    "                json.dump({'primitive_core_digest': PRIMITIVE_CORE_DIGEST, 'calls': _primitive_calls}, handle)\n"
    "        except OSError:\n"
    "            pass\n"
    "    return result\n"
)
VERIFIED_PRIMITIVE_BUNDLE_DIGEST = hashlib.sha256(_VERIFIED_PRIMITIVE_SOURCE.encode()).hexdigest()
_VERIFIED_PRIMITIVE = {"verify_webhook_signature": _VERIFIED_PRIMITIVE_SOURCE}
_ABLATED_VERIFIED_PRIMITIVE_SOURCE = (
    f"PRIMITIVE_CORE_DIGEST = {VERIFIED_PRIMITIVE_CORE_DIGEST!r}\n\n"
    "def verify_webhook_signature(secret: str, body: bytes, signature_hex: str) -> bool:\n"
    "    return False\n"
)

# ── the HIDDEN test (the oracle): boot the service, drive signed/unsigned HTTP ─────────────────────────────────
_HIDDEN_TEST = (
    "import json, os, sys, socket, subprocess, time, http.client, hmac, hashlib\n"
    "SECRET='sess_secret_v0'\n"
    "def _fp():\n s=socket.socket(); s.bind(('127.0.0.1',0)); p=s.getsockname()[1]; s.close(); return p\n"
    "def _req(port,method,path,body=None,sig=None):\n"
    " c=http.client.HTTPConnection('127.0.0.1',port,timeout=3); h={'Content-Type':'application/json'}\n"
    " payload=json.dumps(body).encode() if body is not None else None\n"
    " if sig is not None: h['X-Signature']=sig\n"
    " c.request(method,path,body=payload,headers=h); r=c.getresponse(); raw=r.read().decode() or '{}'; c.close()\n"
    " try:\n  return r.status, json.loads(raw)\n except Exception:\n  return r.status, {}\n"
    "port=_fp(); env=dict(os.environ, WEBHOOK_SECRET=SECRET)\n"
    "proc=subprocess.Popen([sys.executable,'app.py','--port',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,cwd=os.getcwd(),env=env)\n"
    "checks={}; observations={}\n"
    "try:\n"
    " ready=False\n"
    " for _ in range(50):\n"
    "  try:\n"
    "   if _req(port,'GET','/health')[0]==200: ready=True; break\n"
    "  except Exception: time.sleep(0.1)\n"
    " checks['boots']=ready\n"
    " if ready:\n"
    "  body=json.dumps({'event_id':'e1','v':1}).encode()\n"
    "  good=hmac.new(SECRET.encode(),body,hashlib.sha256).hexdigest()\n"
    "  st,b=_req(port,'POST','/',json.loads(body),sig=good); observations['good']=[st,b]; checks['good_sig_202']=(st==202 and b=={'status':'accepted'})\n"
    "  st,b=_req(port,'POST','/',json.loads(body),sig='deadbeef'); observations['bad']=[st,b]; checks['bad_sig_401']=(st==401 and b=={'error':'bad_signature'})\n"
    "  st,b=_req(port,'POST','/',json.loads(body),sig=None); observations['missing']=[st,b]; checks['missing_sig_401']=(st==401 and b=={'error':'bad_signature'})\n"
    "  st,b=_req(port,'GET','/health'); observations['health']=[st,b]; checks['only_one_stored']=(st==200 and b=={'status':'ok','healthy':True,'events':1})\n"
    "finally:\n"
    " proc.terminate()\n"
    " try:\n  proc.wait(timeout=5)\n except Exception:\n  proc.kill()\n"
    "receipt={}\n"
    f"receipt_path=os.environ.get({PRIMITIVE_RECEIPT_ENV!r},'')\n"
    "if receipt_path:\n"
    " try:\n"
    "  with open(receipt_path,encoding='utf-8') as handle: receipt=json.load(handle)\n"
    " except Exception: receipt={}\n"
    "op=len(checks)>=4 and all(checks.values())\n"
    "print('TESTRESULT '+json.dumps({'checks':checks,'observations':observations,'passed':op,'primitive_receipt':receipt}))\n"
)


def _safe_workspace_path(raw: str) -> str | None:
    """Return a normalized relative path, rejecting absolute/traversal tool arguments."""
    candidate = PurePosixPath((raw or "").strip())
    if not candidate.parts or candidate.is_absolute() or ".." in candidate.parts:
        return None
    return str(candidate)


def _run_hidden_test(files: dict[str, str]) -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as ws:
        wsp = Path(ws)
        receipt_path = wsp / "_primitive_execution_receipt.json"
        for fn, content in files.items():
            safe_name = _safe_workspace_path(fn)
            if safe_name is None:
                return {"passed": False, "checks": {}, "error": f"unsafe_path:{fn}"}
            (wsp / safe_name).parent.mkdir(parents=True, exist_ok=True)
            (wsp / safe_name).write_text(content, encoding="utf-8")
        # Model-produced code must not inherit the operator's credentials.  The
        # hidden test injects only its synthetic WEBHOOK_SECRET into the child.
        child_env = {"PATH": os.environ.get("PATH", ""), "LANG": os.environ.get("LANG", "C.UTF-8"),
                     "PYTHONDONTWRITEBYTECODE": "1", PRIMITIVE_RECEIPT_ENV: str(receipt_path)}
        try:
            # -I plus -c keeps oracle imports and source outside the model
            # workspace; a generated json.py/sitecustomize.py cannot shadow it.
            proc = subprocess.run([sys.executable, "-I", "-c", _HIDDEN_TEST], cwd=ws,
                                  capture_output=True, text=True,
                                  timeout=90, env=child_env)
        except subprocess.TimeoutExpired:
            return {"passed": False, "checks": {}, "error": "timeout"}
        line = next((ln for ln in proc.stdout.splitlines() if ln.startswith("TESTRESULT ")), None)
        try:
            res = json.loads(line[len("TESTRESULT "):]) if line else {}
        except (TypeError, json.JSONDecodeError):
            res = {}
        required_checks = {"boots", "good_sig_202", "bad_sig_401", "missing_sig_401", "only_one_stored"}
        checks = res.get("checks") if isinstance(res, dict) else None
        observations = res.get("observations") if isinstance(res, dict) else None
        schema_valid = (
            isinstance(checks, dict) and set(checks) == required_checks
            and all(isinstance(value, bool) for value in checks.values())
            and isinstance(observations, dict)
            and isinstance(res.get("passed"), bool)
            and res["passed"] == all(checks.values())
            and isinstance(res.get("primitive_receipt", {}), dict)
        )
        if not schema_valid:
            res = {"checks": {}, "observations": {}, "primitive_receipt": {}, "passed": False,
                   "error": "invalid_oracle_receipt"}
        res["stderr_tail"] = (proc.stderr or "")[-200:] if not res["passed"] else ""
        return res


def _workspace_calls_verified_primitive(files: dict[str, str]) -> bool:
    """Find an actual imported call in any editable Python file, including aliases."""
    for filename, source in files.items():
        if not filename.endswith(".py") or filename == VERIFIED_PRIMITIVE_MODULE:
            continue
        try:
            tree = ast.parse(source or "")
        except SyntaxError:
            continue
        direct_names: set[str] = set()
        module_names: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == "verified_primitives":
                direct_names.update(
                    alias.asname or alias.name for alias in node.names
                    if alias.name == "verify_webhook_signature"
                )
            elif isinstance(node, ast.Import):
                module_names.update(
                    alias.asname or alias.name for alias in node.names
                    if alias.name == "verified_primitives"
                )
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if isinstance(node.func, ast.Name) and node.func.id in direct_names:
                return True
            if (isinstance(node.func, ast.Attribute) and node.func.attr == "verify_webhook_signature"
                    and isinstance(node.func.value, ast.Name) and node.func.value.id in module_names):
                return True
    return False


def _imports_verified_primitive(source: str) -> bool:
    """Backward-compatible one-file predicate used by mutation tests."""
    return _workspace_calls_verified_primitive({"app.py": source})


# ── the agentic tool loop ─────────────────────────────────────────────────────────────────────────────────────
_SYSTEM = (
    "You are a senior engineer working in an EXISTING codebase. Explore with tools, implement the task, run the "
    "hidden tests, and iterate until they pass. Respond with EXACTLY ONE tool call per message, nothing else:\n"
    "  LIST                       - list files\n"
    "  READ <path>                - print a file\n"
    "  WRITE <path>               - then a fenced ```python block with the FULL new file content\n"
    "  TEST                       - run the hidden test suite\n"
    "{primitive_tool}"
    "  DONE                       - only after TEST shows all checks passed\n"
)
_PRIMITIVE_TOOL = ("  PRIMITIVE <query>          - fetch a VERIFIED, tested primitive from the registry (use it "
                   "verbatim instead of writing security/parsing code yourself)\n")


def _parse_tool(text: str) -> tuple[str, str, str]:
    """Parse ONE tool call from the model message: (tool, arg, write_body)."""
    t = (text or "").strip()
    m = re.search(r"```(?:python)?\s*\n(.*?)```", t, re.S)
    body = m.group(1) if m else ""
    head = t.split("```", 1)[0]
    for line in head.splitlines():
        s = line.strip()
        for tool in ("LIST", "READ", "WRITE", "TEST", "PRIMITIVE", "DONE"):
            if s == tool or s.startswith(tool + " ") or s.startswith(tool + ":"):
                arg = s[len(tool):].lstrip(": ").strip()
                return tool, arg, body
    return "NOOP", "", body


def _search_primitive(query: str) -> dict[str, str] | None:
    q = query.lower()
    for name, src in _VERIFIED_PRIMITIVE.items():
        if any(w in name for w in q.split()) or "sign" in q or "hmac" in q or "webhook" in q:
            return {"name": name, "source": src, "module": VERIFIED_PRIMITIVE_MODULE,
                    "card": (f"VERIFIED primitive `{name}` is now mounted read-only as "
                             f"`{VERIFIED_PRIMITIVE_MODULE}`. Import it exactly with: "
                             f"`{VERIFIED_PRIMITIVE_IMPORT}`. Do not copy or rewrite its body.")}
    return None


def run_session(agent: Callable[[str], dict], *, with_db: bool, max_turns: int = 25,
                token_budget: int = 2_000_000) -> dict[str, Any]:
    """Run the agentic session. The FULL conversation is re-sent each turn (realistic input growth). Returns
    per-turn + total session tokens, turns, pass, and whether the verified primitive was used."""
    files = dict(WORKING_SET)
    system = _SYSTEM.format(primitive_tool=_PRIMITIVE_TOOL if with_db else "")
    convo = f"{system}\nTASK: {TASK}\n"
    turns = []
    read_only_files: set[str] = set()
    in_tok = out_tok = 0
    passed = False
    primitive_fetched = False
    proxy_input_turns = proxy_output_turns = 0
    transport_error: str | None = None
    termination_reason = "max_turns"
    last_test_result: dict[str, Any] = {}
    for turn in range(max_turns):
        try:
            gen = agent(convo)
        except Exception as exc:  # noqa: BLE001 - preserve a retryable attempt instead of sinking the grid
            gen = {"code": "", "error": f"session_agent:{exc}"[:140]}
        if gen.get("error"):
            transport_error = str(gen["error"])[:140]
            # Provider errors did not execute the benchmark.  Do not invent
            # char/4 token usage for them and do not continue issuing calls.
            ti = gen.get("input_tokens", 0) or 0
            to = gen.get("completion_tokens", 0) or 0
            input_source = (gen.get("input_token_source") or
                            ("provider_unverified" if ti > 0 else "missing"))
            output_source = (gen.get("output_token_source") or
                             ("provider_unverified" if to > 0 else "missing"))
            if input_source != "provider":
                proxy_input_turns += 1
            if output_source != "provider":
                proxy_output_turns += 1
            in_tok += ti
            out_tok += to
            turns.append({"turn": turn, "tool": "TRANSPORT_ERROR", "in": ti, "out": to,
                          "input_source": input_source, "output_source": output_source})
            passed = None
            termination_reason = "transport_error"
            break
        reported_input = gen.get("input_tokens")
        reported_output = gen.get("completion_tokens")
        declared_input_source = gen.get("input_token_source")
        declared_output_source = gen.get("output_token_source")
        if isinstance(reported_input, (int, float)) and reported_input > 0:
            ti = int(reported_input)
            input_source = declared_input_source or "provider_unverified"
            if input_source != "provider":
                proxy_input_turns += 1
        else:
            ti = len(convo) // _CHARS_PER_TOKEN  # explicitly tracked structural proxy
            proxy_input_turns += 1
            input_source = "chars_per_token_proxy"
        if isinstance(reported_output, (int, float)) and reported_output > 0:
            to = int(reported_output)
            output_source = declared_output_source or "provider_unverified"
            if output_source != "provider":
                proxy_output_turns += 1
        else:
            to = len(gen.get("code", "")) // _CHARS_PER_TOKEN
            proxy_output_turns += 1
            output_source = "chars_per_token_proxy"
        in_tok += ti; out_tok += to
        msg = gen.get("code", "") or ""
        tool, arg, body = _parse_tool(msg)
        result = ""
        if tool == "LIST":
            result = "FILES: " + ", ".join(sorted(files))
        elif tool == "READ":
            safe_name = _safe_workspace_path(arg)
            if safe_name is None:
                result = f"ERROR: unsafe path {arg!r}"
            elif safe_name in read_only_files:
                result = (f"READ DENIED: {safe_name} is a mounted verified module; use its compact import card "
                          "instead of loading the implementation body into context.")
            else:
                result = files.get(safe_name, f"ERROR: no such file {arg!r}")
        elif tool == "WRITE":
            safe_name = _safe_workspace_path(arg)
            if safe_name is None:
                result = f"ERROR: unsafe path {arg!r}"
            elif safe_name in read_only_files:
                result = f"ERROR: {safe_name} is a read-only verified mount"
            else:
                files[safe_name] = body
                result = f"wrote {safe_name} ({len(body)} chars)"
        elif tool == "PRIMITIVE" and with_db:
            prim = _search_primitive(arg)
            if prim:
                files[prim["module"]] = prim["source"]
                read_only_files.add(prim["module"])
                primitive_fetched = True
                result = prim["card"]
            else:
                result = "no matching verified primitive"
        elif tool == "TEST":
            tr = _run_hidden_test(files)
            last_test_result = tr
            passed = bool(tr["passed"])
            result = f"TEST {'PASSED' if passed else 'FAILED'}: {json.dumps(tr.get('checks', {}))}" + (
                f" stderr:{tr.get('stderr_tail')}" if not passed and tr.get('stderr_tail') else "")
        elif tool == "DONE":
            tr = _run_hidden_test(files)
            last_test_result = tr
            passed = bool(tr["passed"])
            termination_reason = "done_passed" if passed else "done_failed"
            turns.append({"turn": turn, "tool": "DONE", "in": ti, "out": to,
                          "input_source": input_source, "output_source": output_source})
            break
        else:
            result = ("Unrecognized. Use exactly one of LIST/READ/WRITE/TEST/" + ("PRIMITIVE/" if with_db else "")
                      + "DONE.")
        # Full transcript replay is the mechanism under test.  Receipt rows stay
        # compact, but the next model turn receives the complete prior exchange.
        convo += f"\n--- turn {turn} ---\nASSISTANT: {msg}\nTOOL_RESULT ({tool}): {result}\n"
        turns.append({"turn": turn, "tool": tool, "in": ti, "out": to,
                      "input_source": input_source, "output_source": output_source})
        if passed:
            termination_reason = "test_passed"
            break
        if in_tok + out_tok > token_budget:
            termination_reason = "token_budget"
            break
    token_accounting = ("transport_incomplete" if transport_error else
                        ("reported" if proxy_input_turns == 0 and proxy_output_turns == 0 else "proxy_mixed"))
    mounted_source = files.get(VERIFIED_PRIMITIVE_MODULE, "")
    runtime_receipt = last_test_result.get("primitive_receipt") or {}
    raw_runtime_calls = runtime_receipt.get("calls", 0)
    runtime_calls = int(raw_runtime_calls) if isinstance(raw_runtime_calls, (int, float)) else 0
    adoption_evidence_present = bool(
        passed is True
        and primitive_fetched
        and VERIFIED_PRIMITIVE_MODULE in read_only_files
        and hashlib.sha256(mounted_source.encode()).hexdigest() == VERIFIED_PRIMITIVE_BUNDLE_DIGEST
        and _workspace_calls_verified_primitive(files)
        and runtime_receipt.get("primitive_core_digest") == VERIFIED_PRIMITIVE_CORE_DIGEST
        and runtime_calls > 0
    )
    ablation_result: dict[str, Any] = {}
    if adoption_evidence_present:
        ablation_result = _run_hidden_test({**files, VERIFIED_PRIMITIVE_MODULE: _ABLATED_VERIFIED_PRIMITIVE_SOURCE})
    ablation_checks = ablation_result.get("checks") or {}
    primitive_causally_required = bool(
        adoption_evidence_present
        and ablation_result.get("passed") is False
        and ablation_checks.get("boots") is True
        and ablation_checks.get("good_sig_202") is False
    )
    primitive_adopted = primitive_causally_required
    return {"lane": "with_db" if with_db else "without_db", "family": TASK_FAMILY,
            "passed": passed, "oracle_pass": passed, "turns": len(turns),
            "input_tokens": in_tok, "output_tokens": out_tok, "total_tokens": in_tok + out_tok,
            "primitive_fetched": primitive_fetched, "primitive_adopted": primitive_adopted,
            "used_verified_primitive": primitive_adopted, "termination_reason": termination_reason,
            "primitive_bundle_digest": (VERIFIED_PRIMITIVE_BUNDLE_DIGEST if primitive_fetched else None),
            "primitive_runtime_calls": runtime_calls,
            "oracle_checks": last_test_result.get("checks") or {},
            "oracle_observations": last_test_result.get("observations") or {},
            "primitive_causally_required": primitive_causally_required,
            "primitive_ablation_checks": ablation_checks,
            "turn_log": turns,
            "token_accounting": token_accounting, "proxy_input_turns": proxy_input_turns,
            "proxy_output_turns": proxy_output_turns, "error": transport_error}


def summarize_session_pair(wo: dict[str, Any], wd: dict[str, Any]) -> dict[str, Any]:
    """Classify one diagnostic pair; only an aggregate of MIN_N pairs may headline."""
    both = wo["passed"] is True and wd["passed"] is True
    saved = wo["total_tokens"] - wd["total_tokens"] if both else None
    exact_accounting = wo["token_accounting"] == wd["token_accounting"] == "reported"
    reuse_proven = wd.get("primitive_adopted") is True
    if wo["passed"] is None or wd["passed"] is None:
        verdict = "transport_incomplete"
    elif both and not reuse_proven:
        verdict = "both_pass_unattributed_treatment"
    elif both and saved is not None and saved > 0:
        verdict = "measured_savings" if exact_accounting else "measured_savings_proxy_only"
    elif both and saved == 0:
        verdict = "both_pass_no_savings"
    elif both:
        verdict = "both_pass_treatment_cost_regression"
    elif wd["passed"] and not wo["passed"]:
        verdict = "capability_lift" if reuse_proven else "unattributed_treatment_only_pass"
    elif wo["passed"] and not wd["passed"]:
        verdict = "treatment_regressed"
    else:
        verdict = "inconclusive_both_fail"
    return {"total_tokens_saved": saved, "verdict": verdict, "both_pass": both,
            "exact_token_accounting": exact_accounting,
            "reuse_proven": reuse_proven,
            "n_pairs": 1, "reportable": False, "headline_eligible": False,
            "status": f"diagnostic pair only; aggregate requires >= {REPORTING_MIN_N} both-pass pairs"}


def run_ab(agent: Callable[[str], dict], *, max_turns: int = 25) -> dict[str, Any]:
    wo = run_session(agent, with_db=False, max_turns=max_turns)
    wd = run_session(agent, with_db=True, max_turns=max_turns)
    paired = summarize_session_pair(wo, wd)
    return {"record_type": "realistic_session_ab", "benchmark_kind": BENCHMARK_KIND,
            "family": TASK_FAMILY,
            "without_db": {k: wo[k] for k in ("passed", "turns", "total_tokens", "input_tokens", "output_tokens",
                                                        "token_accounting", "termination_reason", "error")},
            "with_db": {k: wd[k] for k in ("passed", "turns", "total_tokens", "input_tokens", "output_tokens",
                                           "primitive_fetched", "primitive_adopted", "used_verified_primitive",
                                           "primitive_causally_required",
                                           "token_accounting", "termination_reason", "error")},
            **paired, **BOUNDARY}


# ── mock agents for the self-test (scripted tool sequences; no network) ────────────────────────────────────────
def _correct_app_from_scratch() -> str:
    return _EXISTING_APP.replace(
        "        # TODO(feature): verify the X-Signature HMAC-SHA256 over the raw body using the WEBHOOK_SECRET env var\n"
        "        # BEFORE accepting. On mismatch -> 401 {'error':'bad_signature'}. On valid -> store + 202 {'status':'accepted'}.\n"
        "        n = int(self.headers.get('Content-Length', 0) or 0)\n"
        "        body = self.rfile.read(n) if n else b''\n"
        "        event = json.loads(body or b'{}')\n"
        "        store.add(event)\n"
        "        return self._send(202, {'status': 'accepted'})\n",
        "        import hmac, hashlib\n"
        "        n = int(self.headers.get('Content-Length', 0) or 0)\n"
        "        body = self.rfile.read(n) if n else b''\n"
        "        secret = os.environ.get('WEBHOOK_SECRET', '')\n"
        "        expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()\n"
        "        if not hmac.compare_digest(expected, self.headers.get('X-Signature', '')):\n"
        "            return self._send(401, {'error': 'bad_signature'})\n"
        "        store.add(json.loads(body or b'{}'))\n"
        "        return self._send(202, {'status': 'accepted'})\n").replace(
        "from store import EventStore\n", "import os\nfrom store import EventStore\n")


def _correct_app_using_verified_primitive() -> str:
    """Reference treatment: thin task wiring imports the read-only mounted primitive."""
    return _EXISTING_APP.replace(
        "from store import EventStore\n",
        f"from store import EventStore\n{VERIFIED_PRIMITIVE_IMPORT}\n",
    ).replace(
        "        # TODO(feature): verify the X-Signature HMAC-SHA256 over the raw body using the WEBHOOK_SECRET env var\n"
        "        # BEFORE accepting. On mismatch -> 401 {'error':'bad_signature'}. On valid -> store + 202 {'status':'accepted'}.\n"
        "        n = int(self.headers.get('Content-Length', 0) or 0)\n"
        "        body = self.rfile.read(n) if n else b''\n"
        "        event = json.loads(body or b'{}')\n"
        "        store.add(event)\n"
        "        return self._send(202, {'status': 'accepted'})\n",
        "        n = int(self.headers.get('Content-Length', 0) or 0)\n"
        "        body = self.rfile.read(n) if n else b''\n"
        "        if not verify_webhook_signature(os.environ.get('WEBHOOK_SECRET', ''), body,\n"
        "                                        self.headers.get('X-Signature', '')):\n"
        "            return self._send(401, {'error': 'bad_signature'})\n"
        "        store.add(json.loads(body or b'{}'))\n"
        "        return self._send(202, {'status': 'accepted'})\n",
    )


def _scripted_agent(script: list[str]) -> Callable[[str], dict]:
    state = {"i": 0}

    def agent(convo: str) -> dict:
        msg = script[min(state["i"], len(script) - 1)]
        state["i"] += 1
        return {"code": msg, "completion_tokens": len(msg) // 4, "input_tokens": len(convo) // 4,
                "input_token_source": "chars_per_token_proxy",
                "output_token_source": "chars_per_token_proxy"}
    return agent


def self_test() -> bool:
    """Mutation-gated + REAL: (1) the hidden test FAILS on the untouched working set (feature missing) and PASSES on
    a correct implementation; (2) a WITHOUT-lane scripted agent that implements HMAC from scratch drives the loop to
    a real PASS with FULL-session token accounting (input grows across turns); (3) a WITH-lane agent that fetches the
    verified primitive PASSES using it (used_verified_primitive=True); (4) input tokens dominate (multi-turn re-send);
    (5) an agent that never fixes it FAILS (loop doesn't fake success)."""
    assert _run_hidden_test(WORKING_SET)["passed"] is False, "untouched service must FAIL (feature missing)"
    assert _run_hidden_test({**WORKING_SET, "app.py": _correct_app_from_scratch()})["passed"] is True, \
        "a correct implementation must PASS the hidden test"
    shadow_attempt = {**WORKING_SET, "json.py": (
        "print('TESTRESULT {\"checks\":{},\"passed\":true}')\n"
        "import os\nos._exit(0)\n"
    )}
    assert _run_hidden_test(shadow_attempt)["passed"] is False, \
        "a workspace json.py must not shadow/forge the isolated oracle"

    # (2) WITHOUT lane: explore then implement from scratch then test then done
    app = _correct_app_from_scratch()
    without = run_session(_scripted_agent(["LIST", "READ app.py", "READ store.py",
                                           f"WRITE app.py\n```python\n{app}```", "TEST", "DONE"]),
                          with_db=False)
    assert without["passed"] is True, f"scripted from-scratch session must pass: {without['turn_log']}"
    assert without["input_tokens"] > without["output_tokens"], "realistic sessions are INPUT-dominated"

    # (3) WITH lane: the primitive is mounted read-only behind a compact card;
    # the task-specific edit imports it rather than reimplementing HMAC.
    with_app = _correct_app_using_verified_primitive()
    withdb = run_session(_scripted_agent(["LIST", "PRIMITIVE verify webhook signature", "READ app.py",
                                          f"WRITE app.py\n```python\n{with_app}```", "TEST", "DONE"]),
                         with_db=True)
    assert withdb["passed"] is True and withdb["primitive_adopted"] is True, "WITH lane must adopt the primitive"
    assert withdb["primitive_runtime_calls"] >= 1, "adoption requires a runtime execution receipt"
    assert "hmac.new" not in with_app and "hashlib.sha256" not in with_app, "treatment must not rewrite HMAC"

    comment_only = with_app.replace(
        VERIFIED_PRIMITIVE_IMPORT,
        f"# {VERIFIED_PRIMITIVE_IMPORT}\nfrom verified_primitives import PRIMITIVE_CORE_DIGEST",
    )
    assert not _imports_verified_primitive(comment_only), "an import-looking comment must not prove adoption"

    # Fetching is not adoption: a from-scratch implementation can pass while
    # the reuse telemetry correctly stays false.
    fetched_not_adopted = run_session(
        _scripted_agent(["PRIMITIVE verify webhook signature",
                         f"WRITE app.py\n```python\n{_correct_app_from_scratch()}```", "TEST"]),
        with_db=True,
    )
    assert fetched_not_adopted["passed"] is True and fetched_not_adopted["primitive_fetched"] is True
    assert fetched_not_adopted["primitive_adopted"] is False

    ignored_call_app = _correct_app_from_scratch().replace(
        "from store import EventStore\n",
        f"from store import EventStore\n{VERIFIED_PRIMITIVE_IMPORT}\n",
    ).replace(
        "        secret = os.environ.get('WEBHOOK_SECRET', '')\n",
        "        secret = os.environ.get('WEBHOOK_SECRET', '')\n"
        "        verify_webhook_signature(secret, body, self.headers.get('X-Signature', ''))  # ignored\n",
    )
    ignored_call = run_session(
        _scripted_agent(["PRIMITIVE verify webhook signature",
                         f"WRITE app.py\n```python\n{ignored_call_app}```", "TEST"]),
        with_db=True,
    )
    assert ignored_call["passed"] is True and ignored_call["primitive_runtime_calls"] > 0
    assert ignored_call["primitive_causally_required"] is False and ignored_call["primitive_adopted"] is False, \
        "calling but ignoring a primitive must not count as causal adoption"
    assert _workspace_calls_verified_primitive({
        "helper.py": "import verified_primitives as vp\nresult = vp.verify_webhook_signature('s', b'b', 'x')\n",
    }), "module-alias calls in helper files are legitimate adoption evidence"

    # (5) a non-fixing agent must FAIL (no fake success)
    stuck = run_session(_scripted_agent(["LIST", "READ app.py", "TEST", "DONE"]), with_db=False)
    assert stuck["passed"] is False, "an agent that never implements the feature must NOT pass"

    # Transport failures are retryable attempts, never hidden-oracle failures,
    # and char/4 proxy accounting must not be fabricated for them.
    transport = run_session(
        lambda _prompt: {"code": "", "input_tokens": 12, "completion_tokens": 3, "error": "http503"},
        with_db=True,
    )
    assert transport["passed"] is None and transport["error"] == "http503", transport
    assert transport["input_tokens"] == 12 and transport["output_tokens"] == 3, transport
    assert transport["token_accounting"] == "transport_incomplete", transport
    assert _safe_workspace_path("../escape.py") is None and _safe_workspace_path("/tmp/escape.py") is None

    def pair_arm(passed: bool | None, total: int, accounting: str = "reported",
                 adopted: bool = False) -> dict[str, Any]:
        return {"passed": passed, "total_tokens": total, "token_accounting": accounting,
                "primitive_adopted": adopted}

    diagnostic_pair = summarize_session_pair(pair_arm(True, 100), pair_arm(True, 80, adopted=True))
    assert diagnostic_pair["verdict"] == "measured_savings" and not diagnostic_pair["headline_eligible"]
    assert summarize_session_pair(pair_arm(True, 100), pair_arm(True, 100, adopted=True))["verdict"] == \
        "both_pass_no_savings"
    assert summarize_session_pair(pair_arm(True, 80), pair_arm(True, 100, adopted=True))["verdict"] == \
        "both_pass_treatment_cost_regression"
    proxy_pair = summarize_session_pair(pair_arm(True, 100), pair_arm(True, 80, "proxy_mixed", adopted=True))
    assert proxy_pair["verdict"] == "measured_savings_proxy_only" and not proxy_pair["headline_eligible"]
    unattributed = summarize_session_pair(pair_arm(False, 100), pair_arm(True, 80, adopted=False))
    assert unattributed["verdict"] == "unattributed_treatment_only_pass"
    assert summarize_session_pair(pair_arm(None, 0), pair_arm(True, 80))["verdict"] == "transport_incomplete"

    print(f"OK realistic_session_harness self-test: hidden test fails on the untouched service + passes on a correct "
          f"impl; a WITHOUT-lane scripted session (explore->implement HMAC->test->done) reaches a REAL pass in "
          f"{without['turns']} turns with FULL-session accounting (in={without['input_tokens']} > "
          f"out={without['output_tokens']}, INPUT-dominated as real sessions are); the WITH-lane session mounts + "
          f"imports the verified primitive (adopted=True), while fetch-without-import is detected; unsafe paths are "
          f"rejected; a non-fixing agent FAILS; provider errors stay retryable "
          f"(passed=None) without fabricated proxy tokens. serves_truth=false")
    return True


def main() -> None:
    ap = argparse.ArgumentParser(description="Realistic multi-turn agentic session A/B (full-session token accounting).")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--provider", default="openrouter")
    ap.add_argument("--model", default="")
    ap.add_argument("--max-turns", type=int, default=25)
    args = ap.parse_args()
    if args.self_test:
        raise SystemExit(0 if self_test() else 1)
    if args.live:
        import scripts.run_large_project_ab as rlp  # noqa: PLC0415
        if args.provider == "openwebui":
            from scripts.reuse_experiment_grid import _openwebui_agent  # noqa: PLC0415
            agent = lambda p: _openwebui_agent(  # noqa: E731
                p, args.model or "gemma-4-coding", system=SESSION_TRANSPORT_SYSTEM, max_tokens=4000,
            )
        else:
            from scripts.primitive_token_savings_ab import live_model  # noqa: PLC0415
            base_url, keyfile, default_model = rlp._PROVIDERS[args.provider]
            pool = rlp._load_key_file(keyfile) if keyfile else rlp._load_key_file(f"{args.provider}_keys.txt")
            if args.provider == "openrouter":
                pool = pool[:CODEX_OPENROUTER_KEY_COUNT]
            model = args.model or default_model
            agent = lambda p: live_model(p, pool, model, max_tokens=4000, strip=False, base_url=base_url)  # noqa: E731
        rep = run_ab(agent, max_turns=args.max_turns)
        out = resource("data/dev-intel/realistic_session_harness"); out.mkdir(parents=True, exist_ok=True)
        (out / f"ab_{args.provider}.json").write_text(json.dumps(rep, indent=2, sort_keys=True), encoding="utf-8")
        print(json.dumps({k: v for k, v in rep.items() if k != "turn_log"}, indent=2, sort_keys=True))
        return
    ap.print_help()


if __name__ == "__main__":
    main()
