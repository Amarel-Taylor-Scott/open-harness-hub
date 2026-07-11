#!/usr/bin/env python3
"""scripts.check_execution_backend_redteam — proof: execution-backend attacks fail safely. Generic cloud
functions are not chosen for browser/GPU tasks by default; missing credentials never crash (fallback);
the selector hardcodes no provider prices (reads the pricebook); candidate cloud adapters import no cloud
SDK at module load + return ProviderUnavailableResult unconfigured + never publish truth; the decision
schema is stable across backends.

CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_execution_backend_redteam.py --self-test
"""
from __future__ import annotations

import argparse
from pathlib import Path

from src.baltor.ports.execution_provider import py_class_src_teleon_runtime_execution_provider__ProviderUnavailableResult
from src.teleon.runtime.execution_backend_selector import py_const_src_teleon_runtime_execution_backend_selector__GENERIC_FUNCTIONS, py_function_src_teleon_runtime_execution_backend_selector__select_backend  # canonical Teleon home (Baltor re-exports)
from src.baltor.workers.execution_providers.gcp_cloud_run_function_candidate import py_class_src_teleon_runtime_execution_providers_gcp_cloud_run_function_candidate__GcpCloudRunFunctionCandidate

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])


def _self_test() -> int:
    fails: list[str] = []

    def chk(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    # 1 — generic function NOT chosen for a browser task even if creds + policy try to allow it implicitly
    br = {"capability_id": "browser.x", "worker_bucket": "browser", "requires_browser": True, "estimated_runtime_ms": 4000}
    d = py_function_src_teleon_runtime_execution_backend_selector__select_backend(br, policy_override={"preferred_backends": list(py_const_src_teleon_runtime_execution_backend_selector__GENERIC_FUNCTIONS)}, available_creds=py_const_src_teleon_runtime_execution_backend_selector__GENERIC_FUNCTIONS)
    chk("1 browser task not on a generic function (guard beats preference)", d["backend"] not in py_const_src_teleon_runtime_execution_backend_selector__GENERIC_FUNCTIONS, d["backend"])

    # 2 — generic function NOT chosen for a GPU task
    gpu = {"capability_id": "model.x", "worker_bucket": "model_inference", "requires_gpu": True, "estimated_runtime_ms": 9000}
    dg = py_function_src_teleon_runtime_execution_backend_selector__select_backend(gpu, policy_override={"preferred_backends": list(py_const_src_teleon_runtime_execution_backend_selector__GENERIC_FUNCTIONS)}, available_creds=py_const_src_teleon_runtime_execution_backend_selector__GENERIC_FUNCTIONS)
    chk("2 GPU task not on a generic function (guard)", dg["backend"] not in py_const_src_teleon_runtime_execution_backend_selector__GENERIC_FUNCTIONS)

    # 3 — missing credentials never crash; a decision is still returned
    dm = py_function_src_teleon_runtime_execution_backend_selector__select_backend({"capability_id": "u", "worker_bucket": "utility"},
                        policy_override={"preferred_backends": ["gcp_cloud_run_function@candidate"]}, available_creds=set())
    chk("3 missing creds → safe decision (no crash), not the function", "backend" in dm and dm["backend"] not in py_const_src_teleon_runtime_execution_backend_selector__GENERIC_FUNCTIONS)

    # 4 — the selector hardcodes NO provider prices (reads the pricebook); no literal cost numbers in logic
    sel_src = (_REPO / "_repos/teleon/backend/src/teleon/runtime/execution_backend_selector.py").read_text()  # selector now lives in Teleon
    chk("4 selector reads a pricebook (not hardcoded prices)", "pricebook" in sel_src and "_est_cost" in sel_src)
    # no suspicious hardcoded provider price literals like '0.05' tied to a backend id in the selector
    chk("4 no hardcoded per-backend price literal in selector", "gcp_cloud_run_function@candidate\": {\"duration" not in sel_src)

    # 5 — candidate cloud adapter imports no cloud SDK at module load + returns ProviderUnavailableResult
    adp_src = (_REPO / "_repos/teleon/backend/src/teleon/runtime/execution_providers/gcp_cloud_run_function_candidate.py").read_text()  # canonical Teleon home (Baltor re-exports)
    bad_imports = [t for t in ("import boto3", "from google.cloud", "import google.cloud", "import azure", "import functions_framework") if t in adp_src]
    chk("5 candidate adapter imports no cloud SDK at module load", bad_imports == [], str(bad_imports))
    r = py_class_src_teleon_runtime_execution_providers_gcp_cloud_run_function_candidate__GcpCloudRunFunctionCandidate().invoke({"task_id": "t", "capability_id": "u"})
    chk("5 unconfigured candidate → ProviderUnavailableResult (no crash, no truth)", isinstance(r, py_class_src_teleon_runtime_execution_provider__ProviderUnavailableResult))

    # 6 — decision schema is stable across backends (provider switch does not change the output shape)
    keys = lambda d: {"schema_version", "action", "backend", "reason"} <= set(d)
    a = py_function_src_teleon_runtime_execution_backend_selector__select_backend({"capability_id": "u", "worker_bucket": "utility"})
    b = py_function_src_teleon_runtime_execution_backend_selector__select_backend({"capability_id": "u", "worker_bucket": "utility"}, policy_override={"preferred_backends": ["k8s_deployment_worker@candidate"]}, available_creds={"k8s_deployment_worker@candidate"})
    chk("6 decision schema stable across backends", keys(a) and keys(b) and a["schema_version"] == b["schema_version"])

    # 7 — no execution backend is allowed to be marked as owning truth
    chk("7 candidate adapter owns_truth=False", py_class_src_teleon_runtime_execution_providers_gcp_cloud_run_function_candidate__GcpCloudRunFunctionCandidate().describe()["owns_truth"] is False)

    print(f"\n{'PASS — check_execution_backend_redteam: browser/GPU guarded off generic functions, missing-creds safe, no hardcoded prices, candidate adapter SDK-free at load + unavailable offline + no truth, stable decision schema.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv=None):
    p = argparse.ArgumentParser(); p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    return _self_test() if a.self_test else (p.print_help() or 0)


if __name__ == "__main__":
    raise SystemExit(_main())
