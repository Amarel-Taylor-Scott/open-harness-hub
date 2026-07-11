#!/usr/bin/env python3
"""scripts.buildout_oracle_patterns — two more REAL hidden-oracle BuildoutForge genomes (top-down, EXECUTED).

Extends scripts/buildout_forge.py with two additional multi-file buildouts whose reference builds are EXECUTED
against a HIDDEN oracle the build never sees — nothing passes on plausibility. Same footing as buildout_forge:
a driver string is run under `python -I oracle.py`, seeds hidden fixtures, exercises the built code as a real
subprocess, and prints one `ORACLE {json}` line `{"checks": {...}, "oracle_pass": bool}`.

Two non-insurance genomes (the repo forbids insurance/insurance-adjacent verticals):

  1. queue_worker_service__stdlib__v0 — a background order-ingestion WORKER. `worker.process(queue_path,
     results_path, errors_path)` reads a JSON list of order-like events, processes each IDEMPOTENTLY (dedupe by
     "id"), writes accepted rows to results.json and invalid/poison events to errors.json. The hidden oracle runs
     the worker as a subprocess on a seeded queue containing a DUPLICATE id + an INVALID event, then asserts:
     each id appears exactly once (idempotent dedupe), the invalid event went to errors, a clean event was
     accepted. Multi-file (worker + validators + store) for real decomposition surface.

  2. csv_upload_service__stdlib_http__v0 — an upload-processing stdlib http.server app. POST /upload accepts
     JSON {"filename","content_b64"} (base64 CSV), validates the CSV header, stores it, returns {"rows":N,
     "accepted":true}; GET /health. The hidden oracle mirrors buildout_forge's HTTP driver: boot on a free port,
     POST a valid fixture CSV and assert rows==expected, POST a malformed upload (bad base64 / wrong header /
     missing field) and assert 400, GET /health. Multi-file (app + validators + store).

Isolation note (same as buildout_forge): a built app does REAL I/O (binds a localhost socket; reads/writes files
in its workspace) so the primitive I/O-ban sandbox does NOT apply here — these run in an ephemeral temp workspace
with a wall-clock timeout; the self-test here runs TRUSTED reference code. BENCHMARK_KIND=real_project_buildout;
candidate=true / serves_truth=false.

    python3 scripts/buildout_oracle_patterns.py --self-test
    python3 scripts/buildout_oracle_patterns.py --run --genome queue_worker_service__stdlib__v0 --solution good
"""
from __future__ import annotations

import sys
from pathlib import Path

# ── substrate-root bootstrap (sentinel; mirrors scripts/buildout_forge.py) ───────────────────────────────────
_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots, resource  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import json  # noqa: E402
import subprocess  # noqa: E402  (the oracle RUNNER + build booter, not model code)
import tempfile  # noqa: E402
import time  # noqa: E402
from typing import Any  # noqa: E402

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
BENCHMARK_KIND = "real_project_buildout"  # no_proxy_gate: passes only when the built code RUNS + a hidden oracle passes
ARTIFACT_DIR_REL = "data/dev-intel/buildout_oracle_patterns"
BUILDOUT_REALISM = "B6"  # the built code boots/runs locally AND a hidden oracle exercises real behavior/output

_WORKER_GENOME = "queue_worker_service__stdlib__v0"        # single-source genome ids (no magic strings)
_CSV_GENOME = "csv_upload_service__stdlib_http__v0"

# ════════════════════════════════════════════════════════════════════════════════════════════════════════════
# GENOME 1 — background WORKER: reference multi-file build (worker + validators + dedupe/store helper).
# ════════════════════════════════════════════════════════════════════════════════════════════════════════════
_GOOD_WORKER_VALIDATORS = (
    "def validate_event(event):\n"
    '    """Validate an order-like event; returns (ok, errors)."""\n'
    "    errors = []\n"
    "    if not isinstance(event, dict):\n"
    "        return (False, ['not_a_dict'])\n"
    "    if not event.get('id'):\n"
    "        errors.append('missing_id')\n"
    "    if event.get('type') != 'order':\n"
    "        errors.append('bad_type')\n"
    "    amount = event.get('amount')\n"
    "    if isinstance(amount, bool) or not isinstance(amount, (int, float)) or amount <= 0:\n"
    "        errors.append('bad_amount')\n"
    "    return (len(errors) == 0, errors)\n"
)
_GOOD_WORKER_STORE = (
    "class ResultStore:\n"
    '    """Idempotent result store: dedupe accepted events by id (a duplicate id is a no-op)."""\n'
    "    def __init__(self):\n"
    "        self._seen = set()\n"
    "        self._results = []\n"
    "    def accept(self, event):\n"
    "        eid = event['id']\n"
    "        if eid in self._seen:\n"
    "            return False\n"
    "        self._seen.add(eid)\n"
    "        self._results.append({'id': eid, 'amount': event['amount'], 'status': 'accepted'})\n"
    "        return True\n"
    "    def results(self):\n"
    "        return list(self._results)\n"
)
_GOOD_WORKER = (
    "import json\n"
    "import sys\n"
    "from validators import validate_event\n"
    "from store import ResultStore\n\n\n"
    "def process(queue_path, results_path, errors_path):\n"
    '    """Read order-like events, process idempotently (dedupe by id), route poison events to errors."""\n'
    "    with open(queue_path, encoding='utf-8') as f:\n"
    "        events = json.load(f)\n"
    "    store = ResultStore()\n"
    "    errors = []\n"
    "    for event in events:\n"
    "        ok, errs = validate_event(event)\n"
    "        if not ok:\n"
    "            errors.append({'event': event, 'errors': errs})\n"
    "            continue\n"
    "        store.accept(event)\n"
    "    with open(results_path, 'w', encoding='utf-8') as f:\n"
    "        json.dump(store.results(), f)\n"
    "    with open(errors_path, 'w', encoding='utf-8') as f:\n"
    "        json.dump(errors, f)\n"
    "    return {'accepted': len(store.results()), 'errored': len(errors)}\n\n\n"
    "def main():\n"
    "    process(sys.argv[1], sys.argv[2], sys.argv[3])\n\n\n"
    "if __name__ == '__main__':\n"
    "    main()\n"
)
_GOOD_WORKER_BUILDOUT: dict[str, str] = {
    "validators.py": _GOOD_WORKER_VALIDATORS, "store.py": _GOOD_WORKER_STORE, "worker.py": _GOOD_WORKER}

# a BAD worker: it RUNS but accepts everything (no validation) and never dedupes (writes duplicates).
_BAD_WORKER = (
    "import json\n"
    "import sys\n\n\n"
    "def process(queue_path, results_path, errors_path):\n"
    "    with open(queue_path, encoding='utf-8') as f:\n"
    "        events = json.load(f)\n"
    "    results = [{'id': e.get('id'), 'status': 'accepted'} for e in events]  # no dedupe, no validation\n"
    "    with open(results_path, 'w', encoding='utf-8') as f:\n"
    "        json.dump(results, f)\n"
    "    with open(errors_path, 'w', encoding='utf-8') as f:\n"
    "        json.dump([], f)\n\n\n"
    "def main():\n"
    "    process(sys.argv[1], sys.argv[2], sys.argv[3])\n\n\n"
    "if __name__ == '__main__':\n"
    "    main()\n"
)
_BAD_WORKER_BUILDOUT: dict[str, str] = {"worker.py": _BAD_WORKER}
# a STUB worker: importing worker.py raises -> the worker never runs.
_STUB_WORKER_BUILDOUT: dict[str, str] = {"worker.py": "raise NotImplementedError('not built')\n"}

# the hidden WORKER oracle: seed a queue (DUPLICATE id + INVALID event), RUN the worker as a subprocess, then
# check the output files. The build is never shown these fixtures.
_WORKER_ORACLE_DRIVER = r'''
import json, os, sys, subprocess

# hidden fixtures — a DUPLICATE id (idempotency) + an INVALID/poison event (must route to errors).
_QUEUE = [
    {"id": "E1", "type": "order", "amount": 10},
    {"id": "E1", "type": "order", "amount": 10},    # DUPLICATE id -> must be deduped (processed once)
    {"id": "E2", "type": "order", "amount": -3},     # INVALID (poison: non-positive amount) -> must go to errors
    {"id": "E3", "type": "order", "amount": 7},       # clean -> must be accepted
]
with open("queue.json", "w", encoding="utf-8") as f:
    json.dump(_QUEUE, f)

checks = {}
try:
    proc = subprocess.run(
        [sys.executable, "-c", "import worker; worker.process('queue.json', 'results.json', 'errors.json')"],
        cwd=os.getcwd(), capture_output=True, text=True, timeout=30)
    ran_ok = (proc.returncode == 0)
    child_err = proc.stderr or ""
except Exception as exc:                              # timeout / spawn failure -> the worker did not run
    ran_ok = False
    child_err = str(exc)
checks["worker_ran"] = ran_ok
if not ran_ok:
    sys.stderr.write(child_err)


def _load(name):
    if not os.path.exists(name):
        return None
    with open(name, encoding="utf-8") as fh:
        try:
            return json.load(fh)
        except Exception:
            return None


results = _load("results.json")
errors = _load("errors.json")
result_ids = [r.get("id") for r in (results or [])]
error_ids = [e.get("event", {}).get("id") for e in (errors or [])]
checks["results_written"] = results is not None
checks["errors_written"] = errors is not None
checks["idempotent_e1_once"] = (result_ids.count("E1") == 1)             # duplicate id processed exactly once
checks["each_id_unique"] = (len(result_ids) == len(set(result_ids)) and len(result_ids) > 0)
checks["clean_e3_accepted"] = ("E3" in result_ids)                      # a clean event was accepted
checks["invalid_e2_errored"] = ("E2" in error_ids)                      # the poison event went to errors
checks["e2_not_in_results"] = ("E2" not in result_ids and len(result_ids) > 0)
oracle_pass = len(checks) >= 8 and all(checks.values())
print("ORACLE " + json.dumps({"checks": checks, "oracle_pass": oracle_pass}))
'''

# ════════════════════════════════════════════════════════════════════════════════════════════════════════════
# GENOME 2 — upload-processing HTTP service: reference multi-file build (app + validators + store).
# ════════════════════════════════════════════════════════════════════════════════════════════════════════════
_GOOD_CSV_VALIDATORS = (
    "import csv\n"
    "import io\n\n"
    "REQUIRED_HEADER = ['id', 'name', 'amount']\n\n\n"
    "def validate_csv(text):\n"
    '    """Validate a decoded CSV: header must equal REQUIRED_HEADER; returns (ok, n_rows, errors)."""\n'
    "    errors = []\n"
    "    try:\n"
    "        rows = list(csv.reader(io.StringIO(text)))\n"
    "    except Exception:\n"
    "        return (False, 0, ['unparseable_csv'])\n"
    "    if not rows:\n"
    "        return (False, 0, ['empty_csv'])\n"
    "    header = [c.strip() for c in rows[0]]\n"
    "    if header != REQUIRED_HEADER:\n"
    "        errors.append('bad_header')\n"
    "    data_rows = [r for r in rows[1:] if any(c.strip() for c in r)]\n"
    "    return (len(errors) == 0, len(data_rows), errors)\n"
)
_GOOD_CSV_STORE = (
    "class UploadStore:\n"
    '    """In-memory store of accepted CSV uploads keyed by filename."""\n'
    "    def __init__(self):\n"
    "        self._d = {}\n"
    "    def put(self, filename, n_rows, text):\n"
    "        self._d[filename] = {'rows': n_rows, 'text': text}\n"
    "        return True\n"
    "    def get(self, filename):\n"
    "        return self._d.get(filename)\n"
    "    def count(self):\n"
    "        return len(self._d)\n"
)
_GOOD_CSV_APP = (
    "import argparse\n"
    "import base64\n"
    "import json\n"
    "from http.server import BaseHTTPRequestHandler, HTTPServer\n"
    "from validators import validate_csv\n"
    "from store import UploadStore\n\n"
    "_STORE = UploadStore()\n\n\n"
    "class Handler(BaseHTTPRequestHandler):\n"
    "    def _send(self, code, body):\n"
    "        raw = json.dumps(body).encode()\n"
    "        self.send_response(code)\n"
    "        self.send_header('Content-Type', 'application/json')\n"
    "        self.send_header('Content-Length', str(len(raw)))\n"
    "        self.end_headers()\n"
    "        self.wfile.write(raw)\n\n"
    "    def do_GET(self):\n"
    "        if self.path == '/health':\n"
    "            return self._send(200, {'status': 'ok', 'healthy': True, 'uploads': _STORE.count()})\n"
    "        return self._send(404, {'error': 'not_found'})\n\n"
    "    def do_POST(self):\n"
    "        if self.path == '/upload':\n"
    "            n = int(self.headers.get('Content-Length', 0) or 0)\n"
    "            try:\n"
    "                payload = json.loads(self.rfile.read(n) or b'{}')\n"
    "            except Exception:\n"
    "                return self._send(400, {'error': 'bad_json', 'accepted': False})\n"
    "            filename = payload.get('filename')\n"
    "            content_b64 = payload.get('content_b64')\n"
    "            if not filename or not content_b64:\n"
    "                return self._send(400, {'error': 'missing_fields', 'accepted': False})\n"
    "            try:\n"
    "                text = base64.b64decode(content_b64, validate=True).decode('utf-8')\n"
    "            except Exception:\n"
    "                return self._send(400, {'error': 'bad_base64', 'accepted': False})\n"
    "            ok, n_rows, errors = validate_csv(text)\n"
    "            if not ok:\n"
    "                return self._send(400, {'error': 'invalid_csv', 'errors': errors, 'accepted': False})\n"
    "            _STORE.put(filename, n_rows, text)\n"
    "            return self._send(200, {'rows': n_rows, 'accepted': True})\n"
    "        return self._send(404, {'error': 'not_found'})\n\n"
    "    def log_message(self, *a):\n"
    "        pass\n\n\n"
    "def main():\n"
    "    ap = argparse.ArgumentParser()\n"
    "    ap.add_argument('--port', type=int, default=8000)\n"
    "    args = ap.parse_args()\n"
    "    HTTPServer(('127.0.0.1', args.port), Handler).serve_forever()\n\n\n"
    "if __name__ == '__main__':\n"
    "    main()\n"
)
_GOOD_CSV_BUILDOUT: dict[str, str] = {
    "validators.py": _GOOD_CSV_VALIDATORS, "store.py": _GOOD_CSV_STORE, "app.py": _GOOD_CSV_APP}

# a BAD upload app: it BOOTS but accepts everything with 200 (never validates base64/header, never counts rows).
_BAD_CSV_APP = (
    "import argparse, json\n"
    "from http.server import BaseHTTPRequestHandler, HTTPServer\n\n"
    "class Handler(BaseHTTPRequestHandler):\n"
    "    def _send(self, code, body):\n"
    "        raw = json.dumps(body).encode()\n"
    "        self.send_response(code)\n"
    "        self.send_header('Content-Length', str(len(raw)))\n"
    "        self.end_headers()\n"
    "        self.wfile.write(raw)\n"
    "    def do_GET(self):\n"
    "        self._send(200, {'healthy': True})\n"
    "    def do_POST(self):\n"
    "        self._send(200, {'accepted': True, 'rows': 0})  # accepts everything, never validates\n"
    "    def log_message(self, *a):\n"
    "        pass\n\n"
    "def main():\n"
    "    ap = argparse.ArgumentParser(); ap.add_argument('--port', type=int, default=8000)\n"
    "    a = ap.parse_args(); HTTPServer(('127.0.0.1', a.port), Handler).serve_forever()\n\n"
    "if __name__ == '__main__':\n"
    "    main()\n"
)
_BAD_CSV_BUILDOUT: dict[str, str] = {"app.py": _BAD_CSV_APP}
# a STUB upload app: importing app.py raises -> the server never boots.
_STUB_CSV_BUILDOUT: dict[str, str] = {"app.py": "raise NotImplementedError('not built')\n"}

# the hidden UPLOAD-HTTP oracle: mirrors buildout_forge's HTTP driver (free port, boot-poll, terminate in finally,
# DEVNULL child stdio) and drives POST /upload (valid + malformed) and GET /health over real HTTP.
_HTTP_UPLOAD_ORACLE_DRIVER = r'''
import json, os, sys, socket, subprocess, time, http.client, base64


def _free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def _req(port, method, path, body=None):
    c = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
    payload = json.dumps(body) if body is not None else None
    c.request(method, path, body=payload, headers={"Content-Type": "application/json"})
    r = c.getresponse()
    raw = r.read().decode() or "{}"
    c.close()
    try:
        parsed = json.loads(raw)
    except Exception:
        parsed = {}
    return r.status, parsed


_VALID_CSV = "id,name,amount\n1,Acme,10\n2,Beta,20\n3,Gamma,30\n"      # 3 data rows under the required header
_BAD_HEADER_CSV = "foo,bar\n1,2\n"                                       # valid base64, WRONG header -> reject

port = _free_port()
proc = subprocess.Popen([sys.executable, "app.py", "--port", str(port)],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=os.getcwd())
checks = {}
try:
    ready = False
    for _ in range(50):                                   # up to ~5s for the server to boot
        try:
            st, _b = _req(port, "GET", "/health")
            if st == 200:
                ready = True
                break
        except Exception:
            time.sleep(0.1)
    checks["server_boots"] = ready
    if ready:
        good_b64 = base64.b64encode(_VALID_CSV.encode()).decode()
        st, b = _req(port, "POST", "/upload", {"filename": "a.csv", "content_b64": good_b64})
        checks["upload_accepted_200"] = (st == 200 and b.get("accepted") is True)
        checks["rows_counted"] = (b.get("rows") == 3)
        st, b = _req(port, "POST", "/upload", {"filename": "b.csv", "content_b64": "@@@not_base64@@@"})
        checks["bad_base64_400"] = (st == 400)
        bad_hdr_b64 = base64.b64encode(_BAD_HEADER_CSV.encode()).decode()
        st, b = _req(port, "POST", "/upload", {"filename": "c.csv", "content_b64": bad_hdr_b64})
        checks["bad_header_400"] = (st == 400)
        st, b = _req(port, "POST", "/upload", {"filename": "d.csv"})   # missing content_b64
        checks["missing_field_400"] = (st == 400)
        st, b = _req(port, "GET", "/health")
        checks["health_ok"] = (st == 200 and b.get("healthy") is True)
finally:
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except Exception:
        proc.kill()
oracle_pass = len(checks) >= 7 and all(checks.values())
print("ORACLE " + json.dumps({"checks": checks, "oracle_pass": oracle_pass}))
'''


# ── the two BuildoutGenomes (each an EXECUTED hidden-oracle genome; the grid can expand this dict) ────────────
_GENOMES: dict[str, dict[str, Any]] = {
    _WORKER_GENOME: {
        "product_family": "order_ingestion_worker", "prompt_style": "founder_product_brief",
        "stack": "python_stdlib", "solution_file": "worker.py", "oracle_driver": _WORKER_ORACLE_DRIVER,
        "oracle_summary": "runs worker.py on a seeded queue + checks the results/errors output files",
        "boot_check": "worker_ran", "realism_level": BUILDOUT_REALISM,
        "goal": ("Build a small background order-ingestion worker: worker.process(queue_path, results_path, "
                 "errors_path) reads a JSON list of order-like events and processes each IDEMPOTENTLY (dedupe "
                 "by 'id'), writing accepted rows to results.json and invalid/poison events to errors.json. "
                 "Multi-file (worker + validators + store), stdlib only, runs with `python worker.py q r e`."),
        "primitive_targets": ["validate_event", "ResultStore", "idempotent_dedupe", "poison_event_routing"],
        "good": _GOOD_WORKER_BUILDOUT, "bad": _BAD_WORKER_BUILDOUT, "stub": _STUB_WORKER_BUILDOUT},
    _CSV_GENOME: {
        "product_family": "csv_upload_service", "prompt_style": "founder_product_brief",
        "stack": "python_stdlib_http", "solution_file": "app.py", "oracle_driver": _HTTP_UPLOAD_ORACLE_DRIVER,
        "oracle_summary": "boots app.py + drives POST /upload (valid + malformed) and GET /health over HTTP",
        "boot_check": "server_boots", "realism_level": BUILDOUT_REALISM,
        "goal": ("Build a small CSV-upload HTTP service: POST /upload accepts JSON {filename, content_b64} "
                 "(base64 CSV), validates the CSV header, stores it, returns {rows: N, accepted: true}; a "
                 "malformed upload (bad base64 / wrong header / missing field) returns 400; GET /health "
                 "returns healthy. Multi-file (app + validators + store), stdlib only, boots with "
                 "`python app.py --port N`."),
        "primitive_targets": ["validate_csv", "UploadStore", "base64_csv_decode", "json_http_error"],
        "good": _GOOD_CSV_BUILDOUT, "bad": _BAD_CSV_BUILDOUT, "stub": _STUB_CSV_BUILDOUT},
}


def run_buildout(genome_id: str, files: dict[str, str], lane: str = "harness_alone",
                 extra_files: dict[str, str] | None = None) -> dict[str, Any]:
    """Write the multi-file build to an ephemeral workspace, RUN it, run the HIDDEN oracle, receipt.
    Never returns oracle_pass=True without the built code executing + the hidden oracle passing."""
    genome = _GENOMES[genome_id]
    t0 = time.time()
    with tempfile.TemporaryDirectory() as ws:
        wsp = Path(ws)
        for fname, content in (extra_files or {}).items():        # pre-installed verified-primitive package (reuse lane)
            (wsp / fname).write_text(content, encoding="utf-8")
        for fname, content in files.items():                      # the buildout's own files
            (wsp / fname).write_text(content, encoding="utf-8")
        (wsp / "oracle.py").write_text(genome["oracle_driver"], encoding="utf-8")   # hidden oracle (never shown to the build)
        try:
            proc = subprocess.run([sys.executable, "-I", "oracle.py"], cwd=ws, capture_output=True,
                                  text=True, timeout=120)
        except subprocess.TimeoutExpired:
            return {"record_type": "buildout_run_receipt", "genome_id": genome_id, "lane": lane,
                    "benchmark_kind": BENCHMARK_KIND, "realism_level": genome["realism_level"],
                    "oracle_pass": False, "error": "timeout", **BOUNDARY}
        line = next((ln for ln in proc.stdout.splitlines() if ln.startswith("ORACLE ")), None)
        result = json.loads(line[len("ORACLE "):]) if line else {"checks": {}, "oracle_pass": False}
    return {"record_type": "buildout_run_receipt", "genome_id": genome_id,
            "product_family": genome["product_family"], "lane": lane, "benchmark_kind": BENCHMARK_KIND,
            "realism_level": genome["realism_level"], "n_files": len(files),
            "commands_run": [f"{Path(sys.executable).name} -I oracle.py ({genome['oracle_summary']})"],
            "oracle_checks": result["checks"], "oracle_pass": bool(result["oracle_pass"]),
            "wall_time_s": round(time.time() - t0, 3),
            "stderr_tail": (proc.stderr or "")[-160:] if not result["oracle_pass"] else "", **BOUNDARY}


def self_test() -> bool:
    """Mutation-gated + REAL, for BOTH genomes: the reference GOOD build RUNS + passes its hidden oracle; a
    runs-but-wrong build FAILS on behavior; a stub that never runs FAILS. Real subprocess execution each time."""
    goods: dict[str, dict[str, Any]] = {}
    for gid, genome in _GENOMES.items():
        good = run_buildout(gid, genome["good"])
        assert good["oracle_pass"] is True, f"[{gid}] reference GOOD build must RUN + pass its hidden oracle: {good}"
        assert len(good["oracle_checks"]) >= 6 and all(good["oracle_checks"].values()), \
            f"[{gid}] every hidden-oracle check must pass for the GOOD build: {good}"
        goods[gid] = good

        bad = run_buildout(gid, genome["bad"])
        assert bad["oracle_pass"] is False, f"[{gid}] a runs-but-wrong build MUST fail its hidden oracle: {bad}"
        assert bad["oracle_checks"].get(genome["boot_check"]) is True, \
            f"[{gid}] the bad build should still boot/run (it fails on BEHAVIOR, not by crashing): {bad}"

        stub = run_buildout(gid, genome["stub"])
        assert stub["oracle_pass"] is False, f"[{gid}] a stub that never boots/runs must fail: {stub}"
        assert not stub["oracle_checks"].get(genome["boot_check"]), \
            f"[{gid}] the stub must fail to boot/run (boot_check falsey): {stub}"

        assert good["candidate"] is True and good["serves_truth"] is False
        assert good["realism_level"] == BUILDOUT_REALISM

    assert BENCHMARK_KIND == "real_project_buildout"
    wk, cs = goods[_WORKER_GENOME], goods[_CSV_GENOME]
    print(f"OK buildout_oracle_patterns self-test: {len(_GENOMES)} EXECUTED hidden-oracle genomes — "
          f"queue_worker ({wk['n_files']}-file build RUNS as a subprocess; {len(wk['oracle_checks'])} output "
          f"checks: idempotent dedupe + poison->errors + clean accepted) and csv_upload ({cs['n_files']}-file "
          f"stdlib-http app BOOTS; {len(cs['oracle_checks'])} endpoint checks: valid rows==N + "
          f"bad-base64/bad-header/missing 400 + /health); each GOOD PASSES, each runs-but-wrong FAILS on "
          f"behavior, each never-runs stub FAILS; benchmark_kind={BENCHMARK_KIND} realism={BUILDOUT_REALISM}; "
          f"serves_truth=false")
    return True


def main() -> None:
    ap = argparse.ArgumentParser(description="BuildoutForge oracle patterns: EXECUTED worker + upload-http genomes.")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--genome", default=_WORKER_GENOME, choices=list(_GENOMES))
    ap.add_argument("--solution", default="good", choices=["good", "bad", "stub"])
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return
    if args.run:
        res = run_buildout(args.genome, _GENOMES[args.genome][args.solution])
        out_dir = resource(ARTIFACT_DIR_REL)
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / f"{args.genome}_{args.solution}_receipt.json").write_text(
            json.dumps(res, indent=2, sort_keys=True), encoding="utf-8")
        print(json.dumps(res, indent=2))
        return
    self_test()


if __name__ == "__main__":
    main()
