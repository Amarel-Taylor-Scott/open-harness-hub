#!/usr/bin/env python3
"""primitive_microservice_packager — deterministically package a primitive/network as a runnable microservice.

Owner (2026-07-10): "services prepackaged into microservices … use LLMs and agentic deterministic tools to
package primitives into microservices." This is the DETERMINISTIC half of that: a manager emits a thin,
standard service scaffold from a primitive's declared contract and MOUNTS the verified primitive body verbatim
— the deterministic-composition → deploy rung of the delivery ladder made concrete. (The LLM's job is only the
NOVEL glue — a bespoke multi-step wiring or an unusual adapter — a declared seam here; the standard scaffold +
the verified code are deterministic, so a routine primitive becomes a service with 0 model tokens.)

For a primitive with `input_edge → output_edge`, it emits a service exposing `POST /invoke` (typed request →
typed response), a `/healthz`, a Dockerfile, a requirements.txt (from the deployment profiler's deps), and a
service manifest (endpoints + edges + the sized resource envelope + the recommended medium). Framework ZOO:
`fastapi` (default) + `flask` (extend = one row). Deterministic: same primitive → byte-identical scaffold. The
mounted body is the VERIFIED primitive, never regenerated; the response carries `serves_truth=false`.

    PYTHONPATH=. python3 scripts/primitive_microservice_packager.py --self-test
    PYTHONPATH=. python3 scripts/primitive_microservice_packager.py --package OfficerRowBatch
"""
from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path
from typing import Any, Optional

_HERE = Path(__file__).resolve()
_SBC = _HERE.parent.parent
_ROOT = _SBC.parent.parent
for _p in (str(_SBC), str(_SBC / "scripts"), str(_ROOT), str(_ROOT / "_repos" / "teleon" / "backend")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    from src.teleon.experiments.ids import canonical_id  # noqa: E402  the ONE id authority (data plane law)
except Exception as exc:  # noqa: BLE001
    raise SystemExit(f"primitive_microservice_packager requires canonical_id; import failed: {exc}")

STAGE_DIR = _SBC / "dist" / "primitive-microservices"
SERVICE_ID_PREFIX = "psvc"
_CANDIDATE_BITS = {"candidate": True, "serves_truth": False}


def _slug(text: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in str(text).lower()).strip("_")[:48] or "primitive"


def _fastapi_main(primitive: dict[str, Any], mounted_body: str, entry: str) -> str:
    """Deterministic FastAPI app: POST /invoke (input_edge -> output_edge) mounting the verified body verbatim."""
    in_edge = primitive.get("input_edge") or "Input"
    out_edge = primitive.get("output_edge") or "Output"
    title = primitive.get("title") or primitive.get("primitive_id") or "primitive"
    return (
        '"""Auto-packaged microservice for a verified primitive. The body below is MOUNTED verbatim '
        '(deterministic composition — not regenerated); serves_truth=false until promoted."""\n'
        "from fastapi import FastAPI\n"
        "from pydantic import BaseModel\n"
        "from typing import Any\n\n"
        f"PRIMITIVE_ID = {json.dumps(primitive.get('primitive_id') or primitive.get('card_id'))}\n"
        f"INPUT_EDGE = {json.dumps(in_edge)}\n"
        f"OUTPUT_EDGE = {json.dumps(out_edge)}\n\n"
        "# ── mounted verified primitive (verbatim) ──\n"
        f"{mounted_body}\n"
        "# ── /mounted ──\n\n"
        f"app = FastAPI(title={json.dumps(str(title))})\n\n"
        "class InvokeRequest(BaseModel):\n"
        "    payload: Any\n\n"
        "class InvokeResponse(BaseModel):\n"
        "    input_edge: str\n"
        "    output_edge: str\n"
        "    result: Any\n"
        "    candidate: bool = True\n"
        "    serves_truth: bool = False\n\n"
        '@app.get("/healthz")\n'
        "def healthz() -> dict:\n"
        '    return {"ok": True, "primitive_id": PRIMITIVE_ID, "serves_truth": False}\n\n'
        '@app.post("/invoke", response_model=InvokeResponse)\n'
        "def invoke(request: InvokeRequest) -> InvokeResponse:\n"
        f"    result = {entry}(request.payload)\n"
        "    return InvokeResponse(input_edge=INPUT_EDGE, output_edge=OUTPUT_EDGE, result=result)\n"
    )


def _flask_main(primitive: dict[str, Any], mounted_body: str, entry: str) -> str:
    in_edge = primitive.get("input_edge") or "Input"
    out_edge = primitive.get("output_edge") or "Output"
    return (
        '"""Auto-packaged Flask microservice for a verified primitive (body mounted verbatim). '
        'serves_truth=false."""\n'
        "from flask import Flask, request, jsonify\n\n"
        f"PRIMITIVE_ID = {json.dumps(primitive.get('primitive_id') or primitive.get('card_id'))}\n"
        f"INPUT_EDGE, OUTPUT_EDGE = {json.dumps(in_edge)}, {json.dumps(out_edge)}\n\n"
        f"{mounted_body}\n\n"
        "app = Flask(__name__)\n\n"
        '@app.get("/healthz")\n'
        "def healthz():\n"
        '    return jsonify(ok=True, primitive_id=PRIMITIVE_ID, serves_truth=False)\n\n'
        '@app.post("/invoke")\n'
        "def invoke():\n"
        f"    result = {entry}((request.get_json(silent=True) or {{}}).get('payload'))\n"
        "    return jsonify(input_edge=INPUT_EDGE, output_edge=OUTPUT_EDGE, result=result,\n"
        "                   candidate=True, serves_truth=False)\n"
    )


FRAMEWORKS: dict[str, dict[str, Any]] = {
    "fastapi": {"main": _fastapi_main, "run_deps": ["fastapi", "uvicorn", "pydantic"],
                "cmd": 'CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]'},
    "flask": {"main": _flask_main, "run_deps": ["flask", "gunicorn"],
              "cmd": 'CMD ["gunicorn", "-b", "0.0.0.0:8080", "main:app"]'},
}
#: LLM seam: a NOVEL multi-step network whose glue is not a single mounted body needs bespoke wiring — that is
#: the model's job (opt-in), never run in this deterministic 0-token lane.
_LLM_WIRING_SEAM = "novel multi-step wiring is a declared LLM seam; the deterministic lane mounts a single body"


def _dockerfile(framework: str, deps: list[str]) -> str:
    spec = FRAMEWORKS[framework]
    return (
        "# Auto-packaged primitive microservice — deterministic scaffold + verified body.\n"
        "FROM python:3.11-slim\n"
        "WORKDIR /svc\n"
        "COPY requirements.txt .\n"
        "RUN pip install --no-cache-dir -r requirements.txt\n"
        "COPY main.py .\n"
        "EXPOSE 8080\n"
        f"{spec['cmd']}\n"
    )


def package_microservice(primitive: dict[str, Any], *, framework: str = "fastapi",
                         write: bool = False) -> dict[str, Any]:
    """Emit a deterministic microservice scaffold for one primitive. Returns the files (and stages them on
    disk if write=True). Resources/deps come from the deployment profiler (reuse-first)."""
    if framework not in FRAMEWORKS:
        raise ValueError(f"unknown framework {framework!r}; known: {sorted(FRAMEWORKS)}")
    spec = FRAMEWORKS[framework]
    entry = str(primitive.get("entry") or primitive.get("impl_name") or "run")
    body = primitive.get("executable_body") or (
        f"def {entry}(payload):\n"
        f"    # verified body not attached — this primitive is a governance spec ({primitive.get('title')!r}).\n"
        f"    # A packaged spec-only primitive returns its contract, honestly, until a body is mounted.\n"
        '    return {"note": "spec-only primitive; no executable body mounted", "serves_truth": False}\n')

    # deps + resources from the deployment profiler (reuse-first)
    deps = list(spec["run_deps"])
    resources: dict[str, Any] = {}
    try:
        from scripts.primitive_deployment_profiler import profile_primitive  # noqa: PLC0415
        prof = profile_primitive(primitive)
        deps = sorted(set(deps) | set(prof.get("dependencies", [])))
        resources = prof.get("base_resources", {})
    except Exception:  # noqa: BLE001
        pass

    main_py = spec["main"](primitive, body, entry)
    requirements = "\n".join(deps) + "\n"
    dockerfile = _dockerfile(framework, deps)
    manifest = {
        "service_id": canonical_id(SERVICE_ID_PREFIX, str(primitive.get("primitive_id")
                                                          or primitive.get("card_id") or ""), framework),
        "record_type": "primitive_microservice_manifest",
        "primitive_id": primitive.get("primitive_id") or primitive.get("card_id"),
        "framework": framework,
        "endpoints": [{"method": "POST", "path": "/invoke", "consumes": primitive.get("input_edge"),
                       "produces": primitive.get("output_edge")},
                      {"method": "GET", "path": "/healthz"}],
        "dependencies": deps, "base_resources": resources,
        "body_mounted": bool(primitive.get("executable_body")),
        "llm_wiring": _LLM_WIRING_SEAM,
        "note": "deterministic scaffold + verified body mounted verbatim (0-token composition); the service "
                "answers serves_truth=false until the primitive is promoted",
        **_CANDIDATE_BITS,
    }
    files = {"main.py": main_py, "requirements.txt": requirements, "Dockerfile": dockerfile,
             "service_manifest.json": json.dumps(manifest, indent=2, sort_keys=True) + "\n"}
    if write:
        out = STAGE_DIR / _slug(primitive.get("primitive_id") or primitive.get("card_id") or "primitive")
        out.mkdir(parents=True, exist_ok=True)
        for name, content in files.items():
            (out / name).write_text(content)
        manifest["staged_dir"] = str(out)
    return {"manifest": manifest, "files": files}


def _self_test() -> int:
    checks: list[tuple[str, bool, str]] = []
    primitive = {
        "primitive_id": "prim:example:csv_sniff", "title": "CSV dialect sniffer",
        "input_edge": "CsvSample", "output_edge": "DialectSpec", "entry": "run",
        "executable_body": "def run(payload):\n    return {'delimiter': ',', 'sample': payload}\n",
        "blocking_keys": ["parse", "csv"],
    }
    pkg = package_microservice(primitive, framework="fastapi")
    files = pkg["files"]

    # (1) the emitted main.py is SYNTACTICALLY VALID Python (a real, runnable scaffold, not a template string).
    valid = True
    try:
        ast.parse(files["main.py"])
    except SyntaxError:
        valid = False
    checks.append(("the emitted FastAPI main.py parses as valid Python (a real runnable service scaffold)",
                   valid and '@app.post("/invoke"' in files["main.py"], ""))

    # (2) the verified body is MOUNTED VERBATIM (deterministic composition — not regenerated); /invoke calls it.
    checks.append(("the verified primitive body is mounted verbatim + wired to POST /invoke (0-token compose)",
                   "def run(payload):" in files["main.py"] and "return {'delimiter'" in files["main.py"]
                   and "result = run(request.payload)" in files["main.py"], ""))

    # (3) the manifest carries the typed endpoints + reuses the deployment profiler's deps/resources.
    manifest = pkg["manifest"]
    invoke_ep = next(e for e in manifest["endpoints"] if e["path"] == "/invoke")
    checks.append(("manifest: /invoke consumes input_edge, produces output_edge; deps + resources from the "
                   "deployment profiler (reuse-first)",
                   invoke_ep["consumes"] == "CsvSample" and invoke_ep["produces"] == "DialectSpec"
                   and "fastapi" in manifest["dependencies"]
                   and manifest["base_resources"].get("rec_mem_mb", 0) > 0, ""))

    # (4) Dockerfile + requirements are emitted and coherent (the service is deployable).
    checks.append(("a Dockerfile (slim python + the run cmd) and requirements.txt are emitted — the service is "
                   "deployable as-is",
                   "FROM python:3.11-slim" in files["Dockerfile"] and "uvicorn" in files["Dockerfile"]
                   and "fastapi" in files["requirements.txt"], ""))

    # (5) framework ZOO: flask emits a valid alternative; body still mounted; endpoints preserved.
    flask_pkg = package_microservice(primitive, framework="flask")
    flask_valid = True
    try:
        ast.parse(flask_pkg["files"]["main.py"])
    except SyntaxError:
        flask_valid = False
    checks.append(("framework zoo: flask emits a valid alternative scaffold (same primitive, gunicorn Docker cmd)",
                   flask_valid and "gunicorn" in flask_pkg["files"]["Dockerfile"]
                   and "def run(payload):" in flask_pkg["files"]["main.py"], ""))

    # (6) spec-only primitive (no body) packages HONESTLY: an emitted body that returns its contract, not a fake.
    spec_only = {"primitive_id": "prim:spec:x", "title": "governance spec", "input_edge": "In",
                 "output_edge": "Out", "blocking_keys": ["gate"]}
    spec_pkg = package_microservice(spec_only)
    checks.append(("a spec-only primitive (no executable body) packages honestly — manifest.body_mounted=false "
                   "+ a scaffold that returns the contract, never a fabricated impl",
                   spec_pkg["manifest"]["body_mounted"] is False
                   and "spec-only primitive" in spec_pkg["files"]["main.py"], ""))

    # (7) determinism + candidate-only + LLM wiring is a declared seam.
    a = package_microservice(primitive)["files"]["main.py"]
    b = package_microservice(primitive)["files"]["main.py"]
    checks.append(("deterministic (byte-identical scaffold on re-run); candidate-only; the novel-wiring LLM "
                   "lane is a DECLARED seam, not run",
                   a == b and manifest["serves_truth"] is False and "LLM seam" in manifest["llm_wiring"], ""))

    ok = all(passed for _n, passed, _d in checks)
    print(f"{'PASS' if ok else 'FAIL'} - primitive_microservice_packager: deterministically package a verified "
          f"primitive as a runnable microservice — a valid FastAPI/Flask scaffold with the verified body MOUNTED "
          f"verbatim (0-token composition), typed /invoke endpoint, Dockerfile + requirements (deps/resources "
          f"from the deployment profiler); spec-only primitives package honestly; the novel-wiring LLM lane is a "
          f"declared seam. serves_truth=false")
    for name, passed, detail in checks:
        print(f"  [{'ok' if passed else 'XX'}] {name}" + (f"  ({detail[:200]})" if not passed else ""))
    return 0 if ok else 1


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Package a verified primitive as a runnable microservice.")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--package", help="a primitive id / output_edge / title from the corporate pack")
    parser.add_argument("--framework", default="fastapi", choices=list(FRAMEWORKS))
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.package:
        from scripts.corporate_records_scraping_primitive_pack import build_cards  # noqa: PLC0415
        card = next((c for c in build_cards() if args.package in (c.get("card_id"), c.get("primitive_id"),
                                                                  c.get("output_edge"), c.get("title"))), None)
        if card is None:
            print(json.dumps({"error": f"no primitive matches {args.package!r}"}))
            return 1
        result = package_microservice(card, framework=args.framework, write=True)
        print(json.dumps(result["manifest"], indent=2, sort_keys=True))
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
