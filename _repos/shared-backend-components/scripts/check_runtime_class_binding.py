#!/usr/bin/env python3
"""scripts.check_runtime_class_binding — PROOF (CTS-1): the runtime-class → backend binding maps an OCTS-portable
runtime CLASS to a CONCRETE backend by policy + credentials + health, and ALWAYS defers cloud after a local
equivalent.

Asserts:
  A. VOCAB well-formed: every class in capability_runtime_classes.json has a local_equivalent whose bare-id is a
     declared backend (matrix backends_enum) OR a BUILT local equivalent (matrix local_equivalents_built), AND
     routes to a real local executor (job emulator / worker pool / function-subprocess family).
  B. OFFLINE DEFAULT (no creds): every known class binds is_local_fallback=True to its own local equivalent —
     cloud-defer-only-after-local-equivalent holds with zero credentials.
  C. CLOUD chosen when credentialed+healthy: a class binds to a class vendor (action bind_cloud_backend) once
     that vendor has creds + health.
  D. UNHEALTHY cloud → local fallback even WITH creds.
  E. EXCLUSION honored: excluding the only credentialed vendor → local fallback.
  F. PREFERENCE honored: with two credentialed vendors, policy preferred_backends decides.
  G. CLASS-SCOPED guard: a browser/gpu class never offers a generic cloud function (its `considered` set excludes
     the serverless family) — the vocabulary scopes the hard guard for free.
  H. DENY-BY-DEFAULT: an unknown class → known_class=False, is_local_fallback=True, backend == offline default.
  I. bind_allowed: priority order — first class with a runnable cloud wins; none → local of the FIRST class;
     empty list → offline default.
  J. SINGLE SOURCE: injecting a custom vocabulary changes the binding (the module reads the vocab, not a literal).
  K. SCHEMA: every produced decision conforms to RuntimeClassBinding (required keys + action enum).
  L. COMPOSES with the execution selector: eligible_backends_for_classes feeds select_backend, which (offline)
     picks a LOCAL backend that is within the contract's allowed shapes.

Deterministic + offline. Exit 0/1.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

from src.baltor.purpose_tasks import runtime_binding as rb
from src.baltor.workers import execution_backend_selector as sel
from src.baltor.workers.execution_dispatch import _executor_for_backend

#: bare-id local backends routed by LocalFunctionEmulator — the function/subprocess family.
_FUNCTION_FAMILY = {"local_function_emulator@v1", "local_subprocess@v1", "managed_venv@v1"}


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    classes_doc = json.loads((Path(_REPO) / "architecture" / "capability_runtime_classes.json").read_text())
    matrix = json.loads((Path(_REPO) / "architecture" / "execution_backend_policy_matrix.json").read_text())
    schema = json.loads((Path(_REPO) / "schemas" / "purpose_tasks" / "RuntimeClassBinding.schema.json").read_text())
    backends_enum = set(matrix["backends_enum"])
    built = set(matrix["local_equivalents_built"])
    all_classes = [c["class"] for c in classes_doc["classes"]]
    generic = sel.py_function_src_teleon_runtime_execution_backend_selector__generic_functions(matrix)

    def validate_schema(d: dict) -> bool:
        if not all(k in d for k in schema["required"]):
            return False
        if d["action"] not in schema["properties"]["action"]["enum"]:
            return False
        return d["schema_version"] == "RuntimeClassBinding"

    # A. vocabulary well-formed
    for c in classes_doc["classes"]:
        cls = c["class"]
        eq = c.get("local_equivalent")
        check(f"A: {cls} declares local_equivalent", bool(eq))
        bare = rb.local_fallback_backend(cls)
        check(f"A: {cls} local equivalent is declared/built", bare in backends_enum or ("execution." + bare) in built, bare)
        check(f"A: {cls} local equivalent routes to a real executor (config-derived from the policy matrix)",
              _executor_for_backend(bare) is not None, bare)

    # B. offline default → every known class falls back local (cloud-defer-only-after-local-equivalent)
    for cls in all_classes:
        d = rb.bind(cls, available_creds=set(), provider_health={})
        ok = d["is_local_fallback"] and d["known_class"] and d["backend"] == rb.local_fallback_backend(cls) and validate_schema(d)
        check(f"B: offline → {cls} binds to its local equivalent", ok, json.dumps(d))

    # C. cloud chosen when credentialed + healthy
    vend = rb.class_vendor_backends("cloud-function")[0]   # e.g. aws_lambda@candidate
    d = rb.bind("cloud-function", available_creds={vend}, provider_health={vend: True})
    check("C: credentialed+healthy vendor → bind_cloud_backend",
          d["action"] == "bind_cloud_backend" and d["backend"] == vend and not d["is_local_fallback"], json.dumps(d))

    # D. unhealthy cloud → local fallback even with creds
    d = rb.bind("cloud-function", available_creds={vend}, provider_health={vend: False})
    check("D: credentialed but UNHEALTHY → local fallback",
          d["is_local_fallback"] and d["backend"] == rb.local_fallback_backend("cloud-function"), json.dumps(d))

    # E. exclusion of the only credentialed vendor → local fallback
    d = rb.bind("cloud-function", available_creds={vend}, provider_health={vend: True},
                policy_override={"excluded_backends": [vend]})
    check("E: excluding the only credentialed vendor → local fallback", d["is_local_fallback"], json.dumps(d))

    # F. preference honored with two credentialed vendors
    vends = rb.class_vendor_backends("cloud-function")
    if len(vends) >= 2:
        a, b = vends[0], vends[1]
        d = rb.bind("cloud-function", available_creds={a, b}, provider_health={a: True, b: True},
                    policy_override={"preferred_backends": [b]})
        check("F: policy preferred_backends decides among credentialed vendors", d["backend"] == b, json.dumps(d))
    else:
        check("F: (skipped — <2 vendors)", True)

    # G. class-scoped hard guard: gpu/browser classes never consider a generic cloud function
    for cls in ("gpu-worker", "browser-worker"):
        considered = set(rb.bind(cls, available_creds=set(), provider_health={})["considered"])
        check(f"G: {cls} never considers a generic cloud function", not (considered & generic), str(considered & generic))

    # H. deny-by-default: unknown class
    d = rb.bind("totally-made-up-class", available_creds={vend}, provider_health={vend: True})
    check("H: unknown class → deny-by-default (local, offline default, known_class False)",
          (not d["known_class"]) and d["is_local_fallback"] and d["backend"] == rb.offline_default_backend(), json.dumps(d))

    # I. bind_allowed priority + fallbacks
    da = rb.bind_allowed(["cloud-function", "kubernetes-job"], available_creds=set(), provider_health={})
    check("I: bind_allowed offline → local fallback of the FIRST class",
          da["is_local_fallback"] and da["backend"] == rb.local_fallback_backend("cloud-function"), json.dumps(da))
    kj = rb.class_vendor_backends("kubernetes-job")[0]
    da2 = rb.bind_allowed(["cloud-function", "kubernetes-job"], available_creds={kj}, provider_health={kj: True})
    check("I: bind_allowed picks the first class that has a runnable cloud vendor",
          da2["action"] == "bind_cloud_backend" and da2["backend"] == kj and da2["runtime_class"] == "kubernetes-job", json.dumps(da2))
    da3 = rb.bind_allowed([], available_creds=set(), provider_health={})
    check("I: bind_allowed empty list → offline default", da3["backend"] == rb.offline_default_backend() and not da3["known_class"])

    # J. single source — inject a custom vocabulary; the module must read IT, not a hardcoded list
    custom = {"classes": [{"class": "demo-only", "vendors": ["demo_vendor@candidate"],
                           "local_equivalent": "local_subprocess@v1"}]}
    dj = rb.bind("demo-only", available_creds=set(), provider_health={}, runtime_classes=custom)
    check("J: injected vocabulary is honored (reads vocab, not a literal)",
          dj["known_class"] and dj["backend"] == "local_subprocess@v1", json.dumps(dj))
    dj2 = rb.bind("cloud-function", available_creds=set(), provider_health={}, runtime_classes=custom)
    check("J: a real class is UNKNOWN under the injected vocab (proves no fallback to a hardcoded list)",
          not dj2["known_class"], json.dumps(dj2))

    # K. schema conformance across a spread of decisions
    spread = [rb.bind("cloud-function", available_creds={vend}, provider_health={vend: True}),
              rb.bind("local-subprocess", available_creds=set(), provider_health={}),
              rb.bind("gpu-worker", available_creds=set(), provider_health={}),
              rb.bind_allowed(["cloud-function"], available_creds=set(), provider_health={})]
    check("K: all decisions conform to RuntimeClassBinding", all(validate_schema(x) for x in spread))

    # L. composes with the execution selector (eligible set constrains the ranking; offline → a local backend)
    elig = rb.eligible_backends_for_classes(["cloud-function"])
    check("L: eligible set is non-empty and includes the local fallback",
          elig and rb.local_fallback_backend("cloud-function") in elig, str(elig))
    sd = sel.py_function_src_teleon_runtime_execution_backend_selector__select_backend({"capability_id": "x", "worker_bucket": "utility", "estimated_runtime_ms": 200},
                            policy_override={"eligible": elig})
    check("L: selector (offline) picks a backend within the contract's allowed shapes",
          sd["backend"] in elig and sd["backend"] in _FUNCTION_FAMILY, json.dumps(sd))

    # M. resolve_for_spec wires PurposeTaskSpec.allowed_runtime_classes through the binding
    spec = {"schema_version": "PurposeTaskSpec", "allowed_runtime_classes": ["cloud-function", "local-subprocess"]}
    dm = rb.resolve_for_spec(spec, available_creds=set(), provider_health={})
    check("M: resolve_for_spec offline → local fallback of the first allowed class",
          dm["is_local_fallback"] and dm["backend"] == rb.local_fallback_backend("cloud-function"), json.dumps(dm))

    print("\n" + ("PASS — check_runtime_class_binding: CTS-1 binds an OCTS runtime class to a concrete backend by "
                  "policy/creds/health; cloud is deferred until a credentialed+healthy class vendor exists, else the "
                  "class's BUILT local equivalent runs; class scoping enforces the browser/GPU guard; unknown class "
                  "denies by default; vocabulary is the single source; decisions conform to RuntimeClassBinding; "
                  "composes with the execution selector." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_runtime_class_binding.py --self-test")
    raise SystemExit(0)
