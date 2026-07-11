#!/usr/bin/env python3
"""scripts.check_shared_openapi_asyncapi_specs — PROOF: the generated OpenAPI + AsyncAPI specs
(_repos/shared-backend-components/docs/contracts/{openapi,asyncapi}.generated.json) are a faithful, drift-free, projection-only machine view of
_repos/shared-backend-components/architecture/contract_registry.json — every registered HTTP route and every command/event/log channel is covered,
every $ref resolves to a real schema, and no raw key leaks.

Asserts (against scripts.build_contract_specs + the on-disk generated docs):
  A. DETERMINISM: build_openapi()/build_asyncapi() are byte-identical across two builds.
  B. NO DRIFT: the on-disk generated docs equal a fresh build (else: run build_contract_specs.py --write).
  C. ROUTE COVERAGE: every registered api_route (method+path) appears in the OpenAPI paths (and nothing extra).
  D. INFERENCE PLANE: the 7 /api/inference/* read routes are registered (api_routes) AND present in OpenAPI; the
     api_projection.ROUTES read/resolve routes are all covered; the compute route (structured-local) is intentionally
     NOT registered as a projection route (it executes the local stub) — kept honest, not silently dropped.
  E. EVENT/COMMAND COVERAGE: every command_type → CommandEnvelope message, every event_type → EventEnvelope
     (CloudEvents) message, every log_event → a log message, on the registered queue channels.
  F. REFS RESOLVE: every $ref in both docs resolves to a real schema file on disk.
  G. NO RAW KEY: no raw-key / secret-value pattern anywhere in either generated doc.
  H. PROJECTION-ONLY + ERROR CONTRACT: every OpenAPI operation carries x-projection-only=true and declares an
     ErrorEnvelope error response.

Deterministic + offline. Exit 0/1.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import json
import os
import re
import sys
from pathlib import Path

_REPO = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from scripts import build_contract_specs as B
from src.teleon.inference import api_projection as ap

_LEAK = re.compile(r"(sk-[A-Za-z0-9]{8,}|gsk_[A-Za-z0-9]{8,}|secret://[^\"]*?:[^\"]+|Bearer\s+[A-Za-z0-9._-]{8,})")
_CONTRACTS = _resource("docs") / "contracts"


def _refs(obj) -> list[str]:
    out = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "$ref" and isinstance(v, str):
                out.append(v)
            else:
                out.extend(_refs(v))
    elif isinstance(obj, list):
        for v in obj:
            out.extend(_refs(v))
    return out


def _self_test() -> int:
    fails: list[str] = []

    def check(n: str, ok: bool, d: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok:
            fails.append(n)

    oa, aa = B.build_openapi(), B.build_asyncapi()
    check("A: OpenAPI + AsyncAPI builds are deterministic",
          B._dump(B.build_openapi()) == B._dump(oa) and B._dump(B.build_asyncapi()) == B._dump(aa))

    check("B: on-disk generated docs are drift-free (== fresh build)", not B.check_drift(), str(B.check_drift()))

    reg = B._registry()
    want = {(r["route"].split(" ", 1)[0].lower(), B._path_template(r["route"].split(" ", 1)[1])) for r in reg["api_routes"]}
    have = {(m, p) for p, ops in oa["paths"].items() for m in ops}
    check("C: every registered api_route is covered (and no extra paths)", want == have,
          f"missing={sorted(want - have)[:3]} extra={sorted(have - want)[:3]}")

    inf_routes = {r["route"] for r in reg["api_routes"] if "/api/inference/" in r["route"]}
    check("D: the 7 /api/inference read routes are registered", len(inf_routes) == 7, str(sorted(inf_routes)))
    ap_read = {r for r in ap.ROUTES if not r.endswith("structured-local")}  # the read/resolve projection routes
    covered = {f"{m.upper()} {p}" for p, ops in oa["paths"].items() for m in ops}
    check("D: every api_projection read/resolve ROUTE is in the OpenAPI doc",
          all(r in covered for r in ap_read), str([r for r in ap_read if r not in covered]))
    check("D: the compute route (structured-local) is intentionally NOT a registered projection route",
          not any("structured-local" in r for r in inf_routes))

    ev = aa["channels"]["runtime.events"]["messages"]
    cmd_ch = aa["channels"].get("runtime.commands") or aa["channels"].get("pipeline.commands")
    logs = aa["channels"]["runtime.logs"]["messages"]
    check("E: every event_type → an EventEnvelope (CloudEvents) message",
          all(e["name"] in ev and ev[e["name"]]["payload"]["$ref"].endswith("EventEnvelope.schema.json")
              for e in reg["event_types"]))
    check("E: every command_type → a CommandEnvelope message",
          all(c["name"] in cmd_ch["messages"]
              and cmd_ch["messages"][c["name"]]["payload"]["$ref"].endswith("CommandEnvelope.schema.json")
              for c in reg["command_types"]))
    check("E: every log_event → a log channel message", all(l["name"] in logs for l in reg["log_events"]))

    bad_ref = []
    for doc in (oa, aa):
        for ref in _refs(doc):
            if not (_CONTRACTS / ref).resolve().is_file():
                bad_ref.append(ref)
    check("F: every $ref resolves to a real schema file on disk", not bad_ref, str(sorted(set(bad_ref))[:3]))

    blob = B._dump(oa) + B._dump(aa)
    leaks = _LEAK.findall(blob)
    check("G: no raw-key / secret-value pattern in either generated doc", not leaks, str(leaks[:3]))

    ops = [op for p, ops in oa["paths"].items() for op in ops.values()]
    check("H: every operation is x-projection-only + declares an ErrorEnvelope error response",
          bool(ops) and all(op.get("x-projection-only") is True
                            and any(r.get("content", {}).get("application/json", {}).get("schema", {}).get("$ref", "").endswith("ErrorEnvelope.schema.json")
                                    for code, r in op["responses"].items() if code != "200") for op in ops))

    print("\n" + ("PASS — check_shared_openapi_asyncapi_specs: the generated OpenAPI + AsyncAPI specs faithfully + "
                  "drift-free cover every registered route and every command/event/log channel (incl. the "
                  "/api/inference plane); every $ref resolves; no raw key leaks; every operation is projection-only "
                  "with an ErrorEnvelope error contract." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_shared_openapi_asyncapi_specs.py --self-test")
    raise SystemExit(0)
