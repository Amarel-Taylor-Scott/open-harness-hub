#!/usr/bin/env python3
"""scripts.buildout_forge — BuildoutForge Wave-0 kernel: the TOP-DOWN loop the bottom-up registry lacks. A real
multi-file project is BUILT, BOOTED as a running service, and verified by a HIDDEN HTTP oracle that exercises
real endpoints — the only footing on which a real "does reuse save tokens on real software" number can stand.

Owner (2026-07-09): "generate a SaaS that does X ... build it out ... run against a hidden oracle ... decompose
into primitives ... rebuild with primitives injected ... measure real lift." REAL means executed: this module
starts the built app in a subprocess and drives it over real HTTP (realism level B6). Nothing passes on
plausibility. BENCHMARK_KIND=real_project_buildout; candidate=true / serves_truth=false.

This kernel proves the executed footing on ONE non-insurance genome (a vendor-onboarding service slice — the
repo forbids insurance/insurance-adjacent verticals, so dental-insurance/prior-auth/RCM/stripe-reconciliation
families from the spec are swapped for approved adjacent ones). The buildout A/B (bare vs primitives-injected,
both executed) and the BuildoutGenome grid build on top of this footing.

Isolation note: a built app does REAL I/O (binds a localhost socket) so the primitive I/O-ban sandbox does NOT
apply here; buildouts run in an ephemeral temp workspace with a wall-clock timeout. UNTRUSTED (model-written)
buildouts in the live lane must additionally run under container/network isolation (docker is available) — the
self-test here runs TRUSTED reference code.

    python3 scripts/buildout_forge.py --self-test
    python3 scripts/buildout_forge.py --run --solution good   # boot the reference build + run the hidden oracle
"""
from __future__ import annotations

import sys
from pathlib import Path

# ── substrate-root bootstrap (sentinel; mirrors scripts/ml_lifecycle_primitive_minter.py) ────────────────────
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
BENCHMARK_KIND = "real_project_buildout"  # no_proxy_gate: passes only when the built app BOOTS + a hidden HTTP oracle passes
ARTIFACT_DIR_REL = "data/dev-intel/buildout_forge"
BUILDOUT_REALISM = "B6"  # built repo boots locally AND a hidden HTTP oracle exercises real endpoints

# ── the hidden HTTP oracle: launch the built app on a free port, drive it over real HTTP, check behavior. ─────
#    It is the PARENT that boots `app.py` as a child and probes it; the app is never shown these fixtures.
_HTTP_ORACLE_DRIVER = r'''
import json, os, sys, socket, subprocess, time, http.client


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
        st, b = _req(port, "POST", "/vendors", {"vendor_id": "V1", "name": "Acme"})
        checks["create_201"] = (st == 201)
        st, b = _req(port, "GET", "/vendors/V1")
        checks["get_200_name"] = (st == 200 and b.get("name") == "Acme")
        st, b = _req(port, "POST", "/vendors", {"name": "NoId"})       # invalid: missing vendor_id
        checks["invalid_400"] = (st == 400)
        st, b = _req(port, "POST", "/vendors", {"vendor_id": "V1", "name": "Acme"})  # duplicate
        checks["idempotent_dupe"] = (st in (200, 409))
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
oracle_pass = len(checks) >= 7 and all(checks.values())
print("ORACLE " + json.dumps({"checks": checks, "oracle_pass": oracle_pass}))
'''

# ── reference GOOD buildout: a real multi-file vendor-onboarding service (stdlib only → boots here, no deps). ──
_GOOD_VALIDATORS = (
    "def validate_vendor(payload):\n"
    '    """Validate a vendor onboarding payload; returns (ok, errors)."""\n'
    "    errors = []\n"
    "    if not payload.get('vendor_id'):\n"
    "        errors.append('missing_vendor_id')\n"
    "    if not payload.get('name'):\n"
    "        errors.append('missing_name')\n"
    "    return (len(errors) == 0, errors)\n"
)
_GOOD_STORE = (
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
_GOOD_APP = (
    "import argparse\n"
    "import json\n"
    "from http.server import BaseHTTPRequestHandler, HTTPServer\n"
    "from validators import validate_vendor\n"
    "from store import VendorStore\n\n"
    "_STORE = VendorStore()\n\n\n"
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
    "            return self._send(200, {'status': 'ok', 'healthy': True})\n"
    "        if self.path.startswith('/vendors/'):\n"
    "            vid = self.path.rsplit('/', 1)[-1]\n"
    "            v = _STORE.get(vid)\n"
    "            return self._send(200, v) if v else self._send(404, {'error': 'not_found'})\n"
    "        return self._send(404, {'error': 'not_found'})\n\n"
    "    def do_POST(self):\n"
    "        if self.path == '/vendors':\n"
    "            n = int(self.headers.get('Content-Length', 0) or 0)\n"
    "            payload = json.loads(self.rfile.read(n) or b'{}')\n"
    "            ok, errors = validate_vendor(payload)\n"
    "            if not ok:\n"
    "                return self._send(400, {'error': 'invalid', 'errors': errors})\n"
    "            created = _STORE.add(payload)\n"
    "            return self._send(201 if created else 200, {'vendor_id': payload['vendor_id'], 'created': created})\n"
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
_GOOD_BUILDOUT: dict[str, str] = {"validators.py": _GOOD_VALIDATORS, "store.py": _GOOD_STORE, "app.py": _GOOD_APP}

# a BAD buildout: a server that boots but returns 200 for everything (no validation, no store, no health flag).
_BAD_APP = (
    "import argparse, json\n"
    "from http.server import BaseHTTPRequestHandler, HTTPServer\n\n"
    "class Handler(BaseHTTPRequestHandler):\n"
    "    def _ok(self):\n"
    "        raw = b'{}'\n"
    "        self.send_response(200)\n"
    "        self.send_header('Content-Length', str(len(raw)))\n"
    "        self.end_headers()\n"
    "        self.wfile.write(raw)\n"
    "    def do_GET(self):\n"
    "        self._ok()\n"
    "    def do_POST(self):\n"
    "        self._ok()\n"
    "    def log_message(self, *a):\n"
    "        pass\n\n"
    "def main():\n"
    "    ap = argparse.ArgumentParser(); ap.add_argument('--port', type=int, default=8000)\n"
    "    a = ap.parse_args(); HTTPServer(('127.0.0.1', a.port), Handler).serve_forever()\n\n"
    "if __name__ == '__main__':\n"
    "    main()\n"
)
_BAD_BUILDOUT: dict[str, str] = {"app.py": _BAD_APP}
# a STUB buildout: importing app.py raises -> the server never boots.
_STUB_BUILDOUT: dict[str, str] = {"app.py": "raise NotImplementedError('not built')\n"}


# ── the BuildoutGenome (one concrete, non-insurance genome for Wave 0; the grid expands this dict) ────────────
_GENOMES: dict[str, dict[str, Any]] = {
    "vendor_onboarding_service__stdlib_http__v0": {
        "product_family": "vendor_onboarding_saas", "prompt_style": "founder_product_brief",
        "stack": "python_stdlib_http", "solution_file": "app.py", "http_oracle": _HTTP_ORACLE_DRIVER,
        "realism_level": BUILDOUT_REALISM,
        "goal": ("Build a small vendor-onboarding HTTP service (multi-file: app.py + validators + store; Python "
                 "stdlib only; boots with `python app.py --port N`). Every response body is JSON. Endpoint "
                 "contract:\n"
                 "- GET /health -> HTTP 200, body {\"status\": \"ok\", \"healthy\": true}.\n"
                 "- POST /vendors with body {\"vendor_id\", \"name\"}: if vendor_id OR name is missing/empty -> "
                 "HTTP 400. Otherwise persist idempotently and return HTTP 201 on first create (HTTP 200 on a "
                 "duplicate vendor_id, without double-storing), body {\"vendor_id\": <id>}.\n"
                 "- GET /vendors/{id} -> HTTP 200 with the stored vendor JSON, or HTTP 404 if unknown."),
        "primitive_targets": ["validate_vendor", "VendorStore", "idempotent_upsert", "json_http_error"],
        "good": _GOOD_BUILDOUT, "bad": _BAD_BUILDOUT, "stub": _STUB_BUILDOUT},
}


def run_buildout(genome_id: str, files: dict[str, str], lane: str = "harness_alone",
                 extra_files: dict[str, str] | None = None) -> dict[str, Any]:
    """Write the multi-file build to an ephemeral workspace, BOOT it, run the HIDDEN HTTP oracle, receipt.
    Never returns oracle_pass=True without the app booting + the executed HTTP oracle passing."""
    genome = _GENOMES[genome_id]
    t0 = time.time()
    with tempfile.TemporaryDirectory() as ws:
        wsp = Path(ws)
        for fname, content in (extra_files or {}).items():        # pre-installed verified-primitive package (reuse lane)
            (wsp / fname).parent.mkdir(parents=True, exist_ok=True)
            (wsp / fname).write_text(content, encoding="utf-8")
        for fname, content in files.items():                      # the buildout's own files
            (wsp / fname).parent.mkdir(parents=True, exist_ok=True)
            (wsp / fname).write_text(content, encoding="utf-8")
        (wsp / "oracle.py").write_text(genome["http_oracle"], encoding="utf-8")   # hidden oracle (never shown to the build)
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
            "commands_run": [f"{Path(sys.executable).name} -I oracle.py (boots app.py + HTTP probes)"],
            "oracle_checks": result["checks"], "oracle_pass": bool(result["oracle_pass"]),
            "wall_time_s": round(time.time() - t0, 3),
            "stderr_tail": (proc.stderr or "")[-160:] if not result["oracle_pass"] else "", **BOUNDARY}


def self_test() -> bool:
    """Mutation-gated + REAL: the reference multi-file build BOOTS and passes the hidden HTTP oracle; a bad
    build (boots but wrong behavior) FAILS; a stub build (never boots) FAILS. Real running service, real HTTP."""
    gid = "vendor_onboarding_service__stdlib_http__v0"
    good = run_buildout(gid, _GENOMES[gid]["good"])
    assert good["oracle_pass"] is True, f"reference build must BOOT + pass the hidden HTTP oracle: {good}"
    assert good["oracle_checks"].get("server_boots") is True and all(good["oracle_checks"].values())

    bad = run_buildout(gid, _GENOMES[gid]["bad"])
    assert bad["oracle_pass"] is False, f"a boots-but-wrong build MUST fail the HTTP oracle (else it's fake): {bad}"
    assert bad["oracle_checks"].get("server_boots") is True, "the bad build should still boot (it fails on behavior)"

    stub = run_buildout(gid, _GENOMES[gid]["stub"])
    assert stub["oracle_pass"] is False and stub["oracle_checks"].get("server_boots") is False, \
        "a stub that never boots must fail with server_boots=False"

    assert BENCHMARK_KIND == "real_project_buildout" and good["realism_level"] == "B6"
    assert good["candidate"] is True and good["serves_truth"] is False
    print(f"OK buildout_forge self-test: reference {good['n_files']}-file build BOOTS + passes a HIDDEN HTTP "
          f"oracle ({len(good['oracle_checks'])} real endpoint checks) in {good['wall_time_s']}s; a "
          f"boots-but-wrong build FAILS on behavior; a stub that never boots FAILS; "
          f"benchmark_kind=real_project_buildout realism={good['realism_level']}; serves_truth=false")
    return True


def main() -> None:
    ap = argparse.ArgumentParser(description="BuildoutForge Wave-0: boot a real build + hidden HTTP oracle.")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--genome", default="vendor_onboarding_service__stdlib_http__v0", choices=list(_GENOMES))
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
