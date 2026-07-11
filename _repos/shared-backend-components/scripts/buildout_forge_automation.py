#!/usr/bin/env python3
"""scripts.buildout_forge_automation — a LARGE, realistic AUTOMATION buildout genome for the executed A/B:
a signed-webhook INGEST WORKER (the owner's "entire integration worker" example). It is the buildout task that
AutomationDirectoryForge's `make_webhook_worker` molecule targets, so the compiled_route lane can mount the verified
molecule VERBATIM (0 generated tokens) and the model writes ONLY the thin wiring — the large-subsystem reuse case
where session-token savings actually matter.

The hidden oracle BOOTS the worker on a free port and drives REAL signed HTTP: valid signed event -> 202 accepted +
sunk once; same event again -> 202 duplicate + NOT re-sunk; bad HMAC -> 401; valid-sig-but-invalid-event -> 400;
/metrics counters correct; /health ok; unknown path -> 404. Never returns oracle_pass=True without all of that.
Registered into `run_large_project_ab._registry()`; benchmark_kind=real_project_buildout; serves_truth=false.

    python3 scripts/buildout_forge_automation.py --self-test
    python3 scripts/buildout_forge_automation.py --solution good     # or bad / stub
"""
from __future__ import annotations

import sys
from pathlib import Path

# ── substrate-root bootstrap (sentinel; mirrors scripts/buildout_forge.py) ────────────────────────────────────
_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import json  # noqa: E402
import subprocess  # noqa: E402  (the oracle boots the built worker — not model-generated code)
import tempfile  # noqa: E402
import time  # noqa: E402
from typing import Any  # noqa: E402

# single source of truth for the molecule — no duplication (NO-MAGIC-VALUES §6)
from scripts.automation_directory_forge import WEBHOOK_WORKER_MACRO_SOURCE  # noqa: E402

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
BENCHMARK_KIND = "real_project_buildout"
BUILDOUT_REALISM = "B5_integration_worker_signed_webhook"

# ── the hidden signed-webhook oracle: boot the worker on a free port, drive REAL HMAC-signed HTTP, check behavior ─
_WEBHOOK_ORACLE_DRIVER = r'''
import json, os, sys, socket, subprocess, time, http.client, hmac, hashlib

SECRET = "oracle_webhook_secret_v0"          # the oracle IS the test harness; the app reads it from WEBHOOK_SECRET


def _free_port():
    s = socket.socket(); s.bind(("127.0.0.1", 0)); p = s.getsockname()[1]; s.close(); return p


def _req(port, method, path, body_obj=None, sign=False, bad_sig=False):
    c = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
    headers = {"Content-Type": "application/json"}
    payload = None
    if body_obj is not None:
        payload = json.dumps(body_obj).encode()
        if sign:
            sig = hmac.new(SECRET.encode(), payload, hashlib.sha256).hexdigest()
            headers["X-Signature"] = "deadbeef" if bad_sig else sig
    c.request(method, path, body=payload, headers=headers)
    r = c.getresponse(); raw = r.read().decode() or "{}"; c.close()
    try:
        parsed = json.loads(raw)
    except Exception:
        parsed = {}
    return r.status, parsed


port = _free_port()
env = dict(os.environ, WEBHOOK_SECRET=SECRET)
proc = subprocess.Popen([sys.executable, "app.py", "--port", str(port)],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=os.getcwd(), env=env)
checks = {}
try:
    ready = False
    for _ in range(50):
        try:
            st, _b = _req(port, "GET", "/health")
            if st == 200:
                ready = True; break
        except Exception:
            time.sleep(0.1)
    checks["server_boots"] = ready
    if ready:
        evt = {"event_id": "e1", "amount": 5}
        st, b = _req(port, "POST", "/webhook", evt, sign=True)
        checks["accept_202"] = (st == 202 and b.get("status") == "accepted")
        st, b = _req(port, "POST", "/webhook", evt, sign=True)                  # same event -> duplicate
        checks["dup_202_not_resunk"] = (st == 202 and b.get("status") == "duplicate")
        st, b = _req(port, "POST", "/webhook", evt, sign=True, bad_sig=True)    # wrong signature
        checks["bad_sig_401"] = (st == 401)
        st, b = _req(port, "POST", "/webhook", {"event_id": "e3"}, sign=True)   # valid sig, missing amount
        checks["invalid_event_400"] = (st == 400)
        st, b = _req(port, "GET", "/metrics")
        checks["metrics_ok"] = (st == 200 and b.get("received") == 4 and b.get("accepted") == 1
                                and b.get("duplicates") == 1 and b.get("rejected") == 2)
        st, b = _req(port, "GET", "/health")
        checks["health_ok"] = (st == 200 and b.get("healthy") is True)
        st, b = _req(port, "GET", "/does-not-exist")
        checks["unknown_404"] = (st == 404)
finally:
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except Exception:
        proc.kill()
oracle_pass = len(checks) >= 8 and all(checks.values())
print("ORACLE " + json.dumps({"checks": checks, "oracle_pass": oracle_pass}))
'''

# ── the reference GOOD build: thin app.py wiring over the verified molecule (webhook_worker.py) ────────────────
_GOOD_WEBHOOK_APP = (
    "import os\n"
    "from webhook_worker import make_webhook_worker, run\n\n"
    "_events = []  # in-memory sink; a real worker would enqueue/persist (kept simple for the oracle)\n\n\n"
    "def sink(event):\n"
    "    _events.append(event)\n\n\n"
    "Handler = make_webhook_worker(\n"
    "    os.environ.get('WEBHOOK_SECRET', ''),\n"
    "    {'event_id': 'str', 'amount': 'int'},\n"
    "    ['event_id'],\n"
    "    sink,\n"
    ")\n\n"
    "if __name__ == '__main__':\n"
    "    run(Handler)\n"
)
_GOOD_BUILDOUT: dict[str, str] = {"webhook_worker.py": WEBHOOK_WORKER_MACRO_SOURCE, "app.py": _GOOD_WEBHOOK_APP}

# ── a BAD build: boots, but acks EVERYTHING 202 (no signature check, no validation, no idempotency, no metrics) ─
_BAD_APP = (
    "import argparse, json\n"
    "from http.server import BaseHTTPRequestHandler, HTTPServer\n\n"
    "class Handler(BaseHTTPRequestHandler):\n"
    "    def _send(self, code, obj):\n"
    "        raw = json.dumps(obj).encode()\n"
    "        self.send_response(code)\n"
    "        self.send_header('Content-Length', str(len(raw)))\n"
    "        self.end_headers()\n"
    "        self.wfile.write(raw)\n"
    "    def do_GET(self):\n"
    "        if self.path == '/health':\n"
    "            return self._send(200, {'status': 'ok', 'healthy': True})\n"
    "        return self._send(200, {})\n"
    "    def do_POST(self):\n"
    "        self._send(202, {'status': 'accepted'})\n"
    "    def log_message(self, *a):\n"
    "        pass\n\n"
    "def main():\n"
    "    ap = argparse.ArgumentParser(); ap.add_argument('--port', type=int, default=8000)\n"
    "    a = ap.parse_args(); HTTPServer(('127.0.0.1', a.port), Handler).serve_forever()\n\n"
    "if __name__ == '__main__':\n"
    "    main()\n"
)
_BAD_BUILDOUT: dict[str, str] = {"app.py": _BAD_APP}
_STUB_BUILDOUT: dict[str, str] = {"app.py": "raise NotImplementedError('not built')\n"}

_GOAL = (
    "Build a signed-webhook INGEST WORKER (multi-file: app.py + a webhook_worker module; Python stdlib only; "
    "boots with `python app.py --port N`). It receives automation events over HTTP and must be safe to expose to a "
    "third-party sender. Every response body is JSON. The shared HMAC secret is read from the WEBHOOK_SECRET "
    "environment variable (NEVER hardcode it). Each event is a JSON object {\"event_id\": str, \"amount\": int}. "
    "Contract:\n"
    "- GET /health -> HTTP 200, body {\"status\": \"ok\", \"healthy\": true}.\n"
    "- POST /webhook with the raw JSON event body and an X-Signature header holding the lowercase hex "
    "HMAC-SHA256 of the RAW request body under WEBHOOK_SECRET. Process in this order: (1) verify the signature "
    "(constant-time) — on mismatch return HTTP 401 {\"error\": \"bad_signature\"}; (2) parse + validate the event "
    "(event_id must be a str, amount must be an int) — on invalid return HTTP 400; (3) apply idempotency keyed by "
    "event_id: a first-seen event returns HTTP 202 {\"status\": \"accepted\"} and is delivered to the sink EXACTLY "
    "once; a duplicate event_id returns HTTP 202 {\"status\": \"duplicate\"} and is NOT re-delivered.\n"
    "- GET /metrics -> HTTP 200 with integer counters {\"received\", \"accepted\", \"duplicates\", \"rejected\"} "
    "(received counts every POST /webhook; rejected counts bad-signature + invalid events).\n"
    "- Any other path -> HTTP 404."
)

_GENOMES: dict[str, dict[str, Any]] = {
    "webhook_ingest_worker__stdlib_http__v0": {
        "product_family": "automation_integration_worker", "prompt_style": "platform_engineer_brief",
        "stack": "python_stdlib_http", "solution_file": "app.py", "http_oracle": _WEBHOOK_ORACLE_DRIVER,
        "realism_level": BUILDOUT_REALISM, "goal": _GOAL,
        "primitive_targets": ["make_webhook_worker", "webhook_signature_verifier", "idempotency_gate",
                              "validate_event", "metrics_counters", "dedupe_key"],
        "good": _GOOD_BUILDOUT, "bad": _BAD_BUILDOUT, "stub": _STUB_BUILDOUT},
}


def run_buildout(genome_id: str, files: dict[str, str], lane: str = "harness_alone",
                 extra_files: dict[str, str] | None = None) -> dict[str, Any]:
    """Write the build to an ephemeral workspace, BOOT the worker, run the HIDDEN signed-webhook oracle, receipt.
    Never returns oracle_pass=True without the worker booting + the executed signed-HTTP oracle passing."""
    genome = _GENOMES[genome_id]
    t0 = time.time()
    with tempfile.TemporaryDirectory() as ws:
        wsp = Path(ws)
        for fname, content in (extra_files or {}).items():        # pre-installed verified molecule (reuse lane)
            (wsp / fname).parent.mkdir(parents=True, exist_ok=True)
            (wsp / fname).write_text(content, encoding="utf-8")
        for fname, content in files.items():                      # the buildout's own files
            (wsp / fname).parent.mkdir(parents=True, exist_ok=True)
            (wsp / fname).write_text(content, encoding="utf-8")
        (wsp / "oracle.py").write_text(genome["http_oracle"], encoding="utf-8")
        try:
            proc = subprocess.run([sys.executable, "oracle.py"], cwd=ws, capture_output=True, text=True, timeout=120)
        except subprocess.TimeoutExpired:
            return {"record_type": "buildout_run_receipt", "genome_id": genome_id, "lane": lane,
                    "benchmark_kind": BENCHMARK_KIND, "realism_level": genome["realism_level"],
                    "oracle_pass": False, "error": "timeout", **BOUNDARY}
        line = next((ln for ln in proc.stdout.splitlines() if ln.startswith("ORACLE ")), None)
        result = json.loads(line[len("ORACLE "):]) if line else {"checks": {}, "oracle_pass": False}
    return {"record_type": "buildout_run_receipt", "genome_id": genome_id,
            "product_family": genome["product_family"], "lane": lane, "benchmark_kind": BENCHMARK_KIND,
            "realism_level": genome["realism_level"], "n_files": len(files),
            "commands_run": [f"{Path(sys.executable).name} oracle.py (boots app.py worker + signed HTTP probes)"],
            "oracle_checks": result["checks"], "oracle_pass": bool(result["oracle_pass"]),
            "wall_time_s": round(time.time() - t0, 3),
            "stderr_tail": (proc.stderr or "")[-200:] if not result["oracle_pass"] else "", **BOUNDARY}


def self_test() -> bool:
    """Mutation-gated + REAL: the reference thin-app-over-molecule build BOOTS + passes the hidden signed-webhook
    oracle (8 checks incl. HMAC-401, idempotent-duplicate, metrics); a bad build (acks everything, no signature
    check) FAILS; a stub build (never boots) FAILS. Real running worker, real HMAC-signed HTTP."""
    gid = "webhook_ingest_worker__stdlib_http__v0"
    good = run_buildout(gid, _GENOMES[gid]["good"])
    assert good["oracle_pass"] is True, f"reference build must BOOT + pass the hidden webhook oracle: {good}"
    assert good["oracle_checks"].get("bad_sig_401") is True and good["oracle_checks"].get("dup_202_not_resunk") is True
    assert len(good["oracle_checks"]) >= 8 and all(good["oracle_checks"].values()), good["oracle_checks"]

    bad = run_buildout(gid, _GENOMES[gid]["bad"])
    assert bad["oracle_checks"].get("server_boots") is True, "the bad build should still BOOT (it fails on behavior)"
    assert bad["oracle_pass"] is False, f"the bad build (no signature check) must FAIL the oracle: {bad}"

    stub = run_buildout(gid, _GENOMES[gid]["stub"])
    assert stub["oracle_pass"] is False and stub["oracle_checks"].get("server_boots") is False, \
        f"the stub build must never boot: {stub}"

    # compiled_route reuse: the molecule is provided VERBATIM, the model writes ONLY app.py -> same pass
    reuse = run_buildout(gid, {"app.py": _GOOD_WEBHOOK_APP}, lane="compiled_route",
                         extra_files={"webhook_worker.py": WEBHOOK_WORKER_MACRO_SOURCE})
    assert reuse["oracle_pass"] is True, f"molecule-mounted reuse lane must pass with ONLY app.py written: {reuse}"

    print(f"OK buildout_forge_automation self-test: signed-webhook ingest worker BOOTS + passes the hidden oracle "
          f"({len(good['oracle_checks'])} real signed-HTTP checks incl. HMAC-401 + idempotent-duplicate + metrics) "
          f"in {good['wall_time_s']}s; bad build (acks everything) FAILS; stub FAILS; molecule-mounted reuse lane "
          f"passes writing ONLY app.py ({len(_GOOD_WEBHOOK_APP)} chars over a "
          f"{len(WEBHOOK_WORKER_MACRO_SOURCE)}-char verified molecule); benchmark_kind={BENCHMARK_KIND}; "
          f"serves_truth=false")
    return True


def main() -> None:
    ap = argparse.ArgumentParser(description="Automation integration-worker buildout genome (signed-webhook worker).")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--solution", default="good", choices=["good", "bad", "stub"])
    args = ap.parse_args()
    if args.self_test:
        raise SystemExit(0 if self_test() else 1)
    gid = "webhook_ingest_worker__stdlib_http__v0"
    print(json.dumps(run_buildout(gid, _GENOMES[gid][args.solution]), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
