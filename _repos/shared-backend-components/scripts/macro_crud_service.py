#!/usr/bin/env python3
"""scripts.macro_crud_service — the decisive MACRO-primitive: a reusable HTTP JSON CRUD SERVICE FACTORY
(`make_crud_app(resource, id_field, required_fields, store, validate)`) that owns ALL the boilerplate bulk (HTTP
server, JSON parsing, route registration, create/list/get, standard error/duplicate/not-found responses). The
model writes only a ~7-line thin app.py = one factory call. This is the fix for the failed @route macro: a FACTORY
CALL is an API the model can use correctly (vs a novel routing DSL it can't).

Lane D (the product case) = compiled_route on this genome: the verified macro body is provided VERBATIM in the
workspace (0 prompt tokens), the model sees only the factory SIGNATURE and writes the thin entry -> so output
tokens drop hard AND input overhead stays small -> the first place TOTAL-token savings can go positive.
candidate=true / serves_truth=false.

    python3 scripts/macro_crud_service.py --self-test
    # then: run_large_project_ab.py --live --genome vendor_crud_macro__stdlib_http__v0 --treatment compiled_route
"""
from __future__ import annotations

import sys
from pathlib import Path

# ── substrate-root bootstrap (sentinel; mirrors scripts/http_scaffold_macro.py) ───────────────────────────────
_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import json  # noqa: E402
import subprocess  # noqa: E402
import tempfile  # noqa: E402
import time  # noqa: E402
from typing import Any  # noqa: E402

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
BENCHMARK_KIND = "real_project_buildout"

# ── the MACRO-primitive body: a CRUD-service factory owning the whole HTTP boilerplate bulk. ──────────────────
_MACRO_CRUD = (
    "import argparse\n"
    "import json\n"
    "from http.server import BaseHTTPRequestHandler, HTTPServer\n\n\n"
    "def make_crud_app(resource, id_field, required_fields, store, validate,\n"
    "                  create_status=201, duplicate_status=409, validation_status=400, not_found_status=404,\n"
    "                  health_path='/health'):\n"
    "    '''Build a JSON CRUD service. `store` needs add(obj)->bool(created), get(id)->obj|None, list()->[obj];\n"
    "    `validate` is fn(payload)->(ok, errors). RETURNS a BaseHTTPRequestHandler subclass — serve it with\n"
    "    run(handler) or HTTPServer((host, port), handler).serve_forever(). Routes: POST/GET /<resource>s,\n"
    "    GET /<resource>s/<id>, GET <health_path>. `resource` may be singular or plural.'''\n"
    "    base = resource if resource.startswith('/') else '/' + resource\n"
    "    coll = base if base.endswith('s') else base + 's'\n\n"
    "    class _H(BaseHTTPRequestHandler):\n"
    "        def _send(self, code, body):\n"
    "            raw = json.dumps(body).encode()\n"
    "            self.send_response(code)\n"
    "            self.send_header('Content-Type', 'application/json')\n"
    "            self.send_header('Content-Length', str(len(raw)))\n"
    "            self.end_headers()\n"
    "            self.wfile.write(raw)\n\n"
    "        def do_GET(self):\n"
    "            p = self.path.split('?')[0]\n"
    "            if p == health_path:\n"
    "                return self._send(200, {'status': 'ok', 'healthy': True})\n"
    "            if p == coll:\n"
    "                return self._send(200, {'items': store.list()})\n"
    "            if p.startswith(coll + '/'):\n"
    "                obj = store.get(p.rsplit('/', 1)[-1])\n"
    "                return self._send(200, obj) if obj else self._send(not_found_status, {'error': 'not_found'})\n"
    "            return self._send(not_found_status, {'error': 'not_found'})\n\n"
    "        def do_POST(self):\n"
    "            if self.path.split('?')[0] == coll:\n"
    "                n = int(self.headers.get('Content-Length', 0) or 0)\n"
    "                try:\n"
    "                    payload = json.loads(self.rfile.read(n) or b'{}')\n"
    "                except Exception:\n"
    "                    payload = {}\n"
    "                ok, errors = validate(payload)\n"
    "                if not ok:\n"
    "                    return self._send(validation_status, {'error': 'validation', 'errors': errors})\n"
    "                if not store.add(payload):\n"
    "                    return self._send(duplicate_status, {'error': 'duplicate', id_field: payload.get(id_field)})\n"
    "                return self._send(create_status, payload)\n"
    "            return self._send(not_found_status, {'error': 'not_found'})\n\n"
    "        def log_message(self, *a):\n"
    "            pass\n\n"
    "    return _H\n\n\n"
    "def run(handler, port=None):\n"
    "    '''Serve a handler class (from make_crud_app) on --port (argv) or an explicit port.'''\n"
    "    if port is None:\n"
    "        ap = argparse.ArgumentParser()\n"
    "        ap.add_argument('--port', type=int, default=8000)\n"
    "        port = ap.parse_args().port\n"
    "    HTTPServer(('127.0.0.1', port), handler).serve_forever()\n"
)
_VALIDATORS = (
    "def validate_vendor(payload):\n"
    '    """Validate a vendor payload; returns (ok, errors)."""\n'
    "    errors = []\n"
    "    if not payload.get('vendor_id'):\n"
    "        errors.append('missing_vendor_id')\n"
    "    if not payload.get('name'):\n"
    "        errors.append('missing_name')\n"
    "    return (len(errors) == 0, errors)\n"
)
_STORE = (
    "class VendorStore:\n"
    '    """Idempotent in-memory vendor store (add/get/list)."""\n'
    "    def __init__(self):\n"
    "        self._d = {}\n"
    "    def add(self, vendor):\n"
    "        vid = vendor['vendor_id']\n"
    "        if vid in self._d:\n"
    "            return False\n"
    "        self._d[vid] = dict(vendor)\n"
    "        return True\n"
    "    def get(self, vid):\n"
    "        return self._d.get(vid)\n"
    "    def list(self):\n"
    "        return list(self._d.values())\n"
)
# the THIN entry the model must write — ONE factory call. The macro owns everything else.
_APP_THIN = (
    "from macro_crud_service import make_crud_app, run\n"
    "from validators import validate_vendor\n"
    "from store import VendorStore\n\n"
    "Handler = make_crud_app('vendor', 'vendor_id', ['vendor_id', 'name'], VendorStore(), validate_vendor)\n\n"
    "if __name__ == '__main__':\n"
    "    run(Handler)\n"
)
_GOOD = {"macro_crud_service.py": _MACRO_CRUD, "validators.py": _VALIDATORS, "store.py": _STORE, "app.py": _APP_THIN}
_BAD = {"app.py": ("import argparse, json\n"
                   "from http.server import BaseHTTPRequestHandler, HTTPServer\n"
                   "class H(BaseHTTPRequestHandler):\n"
                   "    def do_GET(self):\n        self.send_response(200); self.send_header('Content-Length','2')\n"
                   "        self.end_headers(); self.wfile.write(b'{}')\n"
                   "    def do_POST(self):\n        self.do_GET()\n    def log_message(self,*a): pass\n"
                   "def main():\n    ap=argparse.ArgumentParser(); ap.add_argument('--port',type=int,default=8000)\n"
                   "    a=ap.parse_args(); HTTPServer(('127.0.0.1',a.port),H).serve_forever()\n"
                   "if __name__=='__main__': main()\n")}
_STUB = {"app.py": "raise NotImplementedError('not built')\n"}

# ── hidden oracle: behavior, not implementation. create/list/get/duplicate-409/invalid-400/404/health (8 checks). ─
_CRUD_ORACLE = r'''
import json, os, sys, socket, subprocess, time, http.client


def _free_port():
    s = socket.socket(); s.bind(("127.0.0.1", 0)); p = s.getsockname()[1]; s.close(); return p


def _req(port, method, path, body=None):
    c = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
    c.request(method, path, body=json.dumps(body) if body is not None else None,
              headers={"Content-Type": "application/json"})
    r = c.getresponse(); raw = r.read().decode() or "{}"; c.close()
    try:
        return r.status, json.loads(raw)
    except Exception:
        return r.status, {}


port = _free_port()
proc = subprocess.Popen([sys.executable, "app.py", "--port", str(port)],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=os.getcwd())
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
        st, b = _req(port, "POST", "/vendors", {"vendor_id": "V1", "name": "Acme"})
        checks["create_2xx"] = (st in (200, 201))
        st, b = _req(port, "GET", "/vendors")
        checks["list_contains"] = (st == 200 and any(i.get("vendor_id") == "V1" for i in b.get("items", [])))
        st, b = _req(port, "GET", "/vendors/V1")
        checks["get_200_name"] = (st == 200 and b.get("name") == "Acme")
        st, b = _req(port, "POST", "/vendors", {"name": "NoId"})
        checks["invalid_400"] = (st == 400)
        st, b = _req(port, "POST", "/vendors", {"vendor_id": "V1", "name": "Acme"})
        checks["duplicate_conflict"] = (st in (409, 200))
        st, b = _req(port, "GET", "/vendors/UNKNOWN")
        checks["missing_404"] = (st == 404)
        st, b = _req(port, "GET", "/health")
        checks["health_ok"] = (st == 200 and b.get("healthy") is True)
finally:
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except Exception:
        proc.kill()
oracle_pass = len(checks) >= 8 and all(checks.values())
print("ORACLE " + json.dumps({"checks": checks, "oracle_pass": oracle_pass}))
'''

_GENOMES: dict[str, dict[str, Any]] = {
    "vendor_crud_macro__stdlib_http__v0": {
        "product_family": "vendor_onboarding_saas", "prompt_style": "founder_product_brief",
        "stack": "python_stdlib_http_crud_macro", "solution_file": "app.py", "http_oracle": _CRUD_ORACLE,
        "realism_level": "B6",
        "goal": ("Build a small vendor CRUD HTTP service (stdlib only; boots with `python app.py --port N`). "
                 "GET /health -> 200 {\"healthy\":true}. POST /vendors {\"vendor_id\",\"name\"}: missing "
                 "vendor_id/name -> 400; else persist -> 201 (or 200); a duplicate vendor_id -> 409 (or 200). "
                 "GET /vendors -> 200 {\"items\":[...]} containing created vendors. GET /vendors/{id} -> 200 the "
                 "stored vendor or 404."),
        "primitive_targets": ["make_crud_app", "validate_vendor", "VendorStore"],
        "good": _GOOD, "bad": _BAD, "stub": _STUB},
}


def run_buildout(genome_id: str, files: dict[str, str], lane: str = "harness_alone",
                 extra_files: dict[str, str] | None = None) -> dict[str, Any]:
    """Write build (subdir-safe) + hidden oracle, boot + probe. Mirrors http_scaffold_macro.run_buildout."""
    genome = _GENOMES[genome_id]
    t0 = time.time()
    with tempfile.TemporaryDirectory() as ws:
        wsp = Path(ws)
        for fname, content in (extra_files or {}).items():
            (wsp / fname).parent.mkdir(parents=True, exist_ok=True)
            (wsp / fname).write_text(content, encoding="utf-8")
        for fname, content in files.items():
            (wsp / fname).parent.mkdir(parents=True, exist_ok=True)
            (wsp / fname).write_text(content, encoding="utf-8")
        (wsp / "oracle.py").write_text(genome["http_oracle"], encoding="utf-8")
        try:
            proc = subprocess.run([sys.executable, "-I", "oracle.py"], cwd=ws, capture_output=True,
                                  text=True, timeout=120)
        except subprocess.TimeoutExpired:
            return {"record_type": "buildout_run_receipt", "genome_id": genome_id, "lane": lane,
                    "benchmark_kind": BENCHMARK_KIND, "oracle_pass": False, "error": "timeout", **BOUNDARY}
        line = next((ln for ln in proc.stdout.splitlines() if ln.startswith("ORACLE ")), None)
        result = json.loads(line[len("ORACLE "):]) if line else {"checks": {}, "oracle_pass": False}
    return {"record_type": "buildout_run_receipt", "genome_id": genome_id, "lane": lane,
            "benchmark_kind": BENCHMARK_KIND, "realism_level": genome["realism_level"], "n_files": len(files),
            "oracle_checks": result["checks"], "oracle_pass": bool(result["oracle_pass"]),
            "wall_time_s": round(time.time() - t0, 3),
            "stderr_tail": (proc.stderr or "")[-160:] if not result["oracle_pass"] else "", **BOUNDARY}


def self_test() -> bool:
    """Mutation-gated + EXECUTED: the thin app.py (ONE make_crud_app call) over the verbatim macro BOOTS + passes
    the 8-check CRUD oracle; bad+stub FAIL; the macro is the BULK vs the tiny entry."""
    gid = "vendor_crud_macro__stdlib_http__v0"
    good = run_buildout(gid, _GENOMES[gid]["good"])
    assert good["oracle_pass"] is True, f"macro-CRUD good build must pass the oracle: {good.get('oracle_checks')}"
    assert all(good["oracle_checks"].values())
    assert run_buildout(gid, _GENOMES[gid]["bad"])["oracle_pass"] is False, "bad build must fail"
    stub = run_buildout(gid, _GENOMES[gid]["stub"])
    assert stub["oracle_pass"] is False and stub["oracle_checks"].get("server_boots") is False
    macro_lines = _MACRO_CRUD.count("\n")
    app_lines = _APP_THIN.count("\n")
    assert macro_lines > 4 * app_lines, "the macro must be the BULK vs the ~7-line entry"
    print(f"OK macro_crud_service self-test: thin {app_lines}-line app.py (ONE make_crud_app call) over a "
          f"{macro_lines}-line CRUD MACRO-primitive BOOTS + passes the {len(good['oracle_checks'])}-check hidden "
          f"oracle; bad+stub FAIL. Lane D (compiled_route) provides the macro verbatim (0 prompt tokens) — the "
          f"model writes only the factory call; benchmark_kind=real_project_buildout; serves_truth=false")
    return True


def main() -> None:
    ap = argparse.ArgumentParser(description="Macro CRUD-service factory genome for the decisive savings test.")
    ap.add_argument("--self-test", action="store_true")
    ap.parse_args()
    self_test()


if __name__ == "__main__":
    main()
