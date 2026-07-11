#!/usr/bin/env python3
"""scripts.http_scaffold_macro — the MACRO-primitive experiment. Measured conclusion (see
buildout-decompose memory): micro primitives (validators/mappers) are ~50 tok of an ~800-tok build, so injecting
them never saves — the BULK is the HTTP-server + routing BOILERPLATE the model rewrites every time. This genome
extracts that boilerplate into a reusable `http_app` MACRO-primitive (a stdlib route-table micro-framework), so a
thin app.py = just handlers + routes. compiled_route provides http_app (the bulk) verbatim at 0 generated tokens,
and the model writes only the ~50-tok business logic. If reuse ever saves tokens on real builds, it is HERE.
candidate=true / serves_truth=false.

    python3 scripts/http_scaffold_macro.py --self-test
    # then: run_large_project_ab.py --live --genome vendor_scaffolded_service__stdlib_http__v0 --treatment compiled_route
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
from scripts._repo_paths import install as _install_code_roots, resource  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import json  # noqa: E402
import subprocess  # noqa: E402
import tempfile  # noqa: E402
import time  # noqa: E402
from typing import Any  # noqa: E402

from scripts.buildout_forge import _GENOMES as _BF_GENOMES  # noqa: E402  reuse the exact vendor hidden oracle

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
BENCHMARK_KIND = "real_project_buildout"
ARTIFACT_DIR_REL = "data/dev-intel/buildout_forge"
_VENDOR_ORACLE = _BF_GENOMES["vendor_onboarding_service__stdlib_http__v0"]["http_oracle"]

# ── the MACRO-primitive: a reusable stdlib HTTP route-table micro-framework (the BULK boilerplate). ────────────
_HTTP_APP = (
    "import argparse\n"
    "import json\n"
    "import re\n"
    "from http.server import BaseHTTPRequestHandler, HTTPServer\n\n"
    "_ROUTES = []\n\n\n"
    "def route(method, path):\n"
    "    pattern = '^' + re.sub(r'\\{(\\w+)\\}', r'(?P<\\1>[^/]+)', path) + '$'\n"
    "    rx = re.compile(pattern)\n"
    "    def deco(fn):\n"
    "        _ROUTES.append((method.upper(), rx, fn))\n"
    "        return fn\n"
    "    return deco\n\n\n"
    "class _Handler(BaseHTTPRequestHandler):\n"
    "    def _send(self, code, body):\n"
    "        raw = json.dumps(body).encode()\n"
    "        self.send_response(code)\n"
    "        self.send_header('Content-Type', 'application/json')\n"
    "        self.send_header('Content-Length', str(len(raw)))\n"
    "        self.end_headers()\n"
    "        self.wfile.write(raw)\n\n"
    "    def _dispatch(self, method):\n"
    "        n = int(self.headers.get('Content-Length', 0) or 0)\n"
    "        raw = self.rfile.read(n) if n else b''\n"
    "        try:\n"
    "            payload = json.loads(raw) if raw else {}\n"
    "        except Exception:\n"
    "            payload = {}\n"
    "        path = self.path.split('?')[0]\n"
    "        for m, rx, fn in _ROUTES:\n"
    "            if m != method:\n"
    "                continue\n"
    "            mo = rx.match(path)\n"
    "            if mo:\n"
    "                code, resp = fn(payload, dict(mo.groupdict()))\n"
    "                return self._send(code, resp)\n"
    "        self._send(404, {'error': 'not_found'})\n\n"
    "    def do_GET(self):\n"
    "        self._dispatch('GET')\n\n"
    "    def do_POST(self):\n"
    "        self._dispatch('POST')\n\n"
    "    def log_message(self, *a):\n"
    "        pass\n\n\n"
    "def run():\n"
    "    ap = argparse.ArgumentParser()\n"
    "    ap.add_argument('--port', type=int, default=8000)\n"
    "    args = ap.parse_args()\n"
    "    HTTPServer(('127.0.0.1', args.port), _Handler).serve_forever()\n"
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
    '    """Idempotent in-memory vendor store."""\n'
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
)
# ── the THIN entry: just handlers + routes. The bulk (server/router) is the http_app macro-primitive. ─────────
_APP_THIN = (
    "from http_app import route, run\n"
    "from validators import validate_vendor\n"
    "from store import VendorStore\n\n"
    "_STORE = VendorStore()\n\n\n"
    "@route('GET', '/health')\n"
    "def health(payload, params):\n"
    "    return 200, {'status': 'ok', 'healthy': True}\n\n\n"
    "@route('POST', '/vendors')\n"
    "def create_vendor(payload, params):\n"
    "    ok, errors = validate_vendor(payload)\n"
    "    if not ok:\n"
    "        return 400, {'error': 'invalid', 'errors': errors}\n"
    "    created = _STORE.add(payload)\n"
    "    return (201 if created else 200), {'vendor_id': payload['vendor_id']}\n\n\n"
    "@route('GET', '/vendors/{id}')\n"
    "def get_vendor(payload, params):\n"
    "    v = _STORE.get(params['id'])\n"
    "    return (200, v) if v else (404, {'error': 'not_found'})\n\n\n"
    "if __name__ == '__main__':\n"
    "    run()\n"
)
_GOOD = {"http_app.py": _HTTP_APP, "validators.py": _VALIDATORS, "store.py": _STORE, "app.py": _APP_THIN}
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

_GENOMES: dict[str, dict[str, Any]] = {
    "vendor_scaffolded_service__stdlib_http__v0": {
        "product_family": "vendor_onboarding_saas", "prompt_style": "founder_product_brief",
        "stack": "python_stdlib_http_scaffold", "solution_file": "app.py", "http_oracle": _VENDOR_ORACLE,
        "realism_level": "B6",
        "goal": ("Build a small vendor-onboarding HTTP service (stdlib only; boots with `python app.py --port N`). "
                 "GET /health -> 200 {\"status\":\"ok\",\"healthy\":true}. POST /vendors {\"vendor_id\",\"name\"}: "
                 "missing vendor_id/name -> 400; else persist idempotently -> 201 create / 200 duplicate, body "
                 "{\"vendor_id\":<id>}. GET /vendors/{id} -> 200 stored vendor or 404."),
        "primitive_targets": ["http_app", "route", "validate_vendor", "VendorStore"],
        "good": _GOOD, "bad": _BAD, "stub": _STUB},
}


def run_buildout(genome_id: str, files: dict[str, str], lane: str = "harness_alone",
                 extra_files: dict[str, str] | None = None) -> dict[str, Any]:
    """Write the build (subdir-safe) + hidden HTTP oracle, boot + probe. Mirrors buildout_forge.run_buildout."""
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
    """Mutation-gated + EXECUTED: the SCAFFOLDED good build (thin app.py over the http_app macro-primitive) BOOTS
    + passes the vendor hidden oracle; a bad build FAILS; a stub FAILS. Proves the macro-primitive composition
    runs — so compiled_route can provide http_app (the bulk) verbatim and the model writes only the thin entry."""
    gid = "vendor_scaffolded_service__stdlib_http__v0"
    good = run_buildout(gid, _GENOMES[gid]["good"])
    assert good["oracle_pass"] is True, f"scaffolded good build must pass the vendor oracle: {good.get('oracle_checks')}"
    assert good["oracle_checks"].get("server_boots") and all(good["oracle_checks"].values())
    bad = run_buildout(gid, _GENOMES[gid]["bad"])
    assert bad["oracle_pass"] is False, "bad build must fail"
    stub = run_buildout(gid, _GENOMES[gid]["stub"])
    assert stub["oracle_pass"] is False and stub["oracle_checks"].get("server_boots") is False, "stub must not boot"
    # the macro-primitive is the BULK: http_app is far larger than the thin app.py that composes it.
    app_lines = _APP_THIN.count("\n")
    scaffold_lines = _HTTP_APP.count("\n")
    assert scaffold_lines > app_lines, "the scaffold (macro-primitive) must be the bulk vs the thin entry"
    print(f"OK http_scaffold_macro self-test: scaffolded vendor build (thin {app_lines}-line app.py over a "
          f"{scaffold_lines}-line http_app MACRO-primitive) BOOTS + passes the vendor hidden oracle "
          f"({len(good['oracle_checks'])} checks); bad+stub FAIL; the reusable bulk (http_app) is now a verbatim "
          f"compiled_route primitive — model writes only the handlers; benchmark_kind=real_project_buildout; serves_truth=false")
    return True


def main() -> None:
    ap = argparse.ArgumentParser(description="Macro-primitive (http_app scaffold) genome for the compiled_route savings test.")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--run", action="store_true")
    args = ap.parse_args()
    if args.self_test or not args.run:
        self_test()
        return
    if args.run:
        res = run_buildout("vendor_scaffolded_service__stdlib_http__v0",
                           _GENOMES["vendor_scaffolded_service__stdlib_http__v0"]["good"])
        print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
