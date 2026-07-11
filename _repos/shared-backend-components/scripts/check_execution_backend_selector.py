#!/usr/bin/env python3
"""scripts.check_execution_backend_selector — proof: the execution backend is chosen by POLICY + PRICEBOOK
+ health + credentials, and is SWITCHABLE without code changes. The same task can route to the local
emulator, a Kubernetes worker, or a cloud function by policy/pricing. Hard guards keep browser/GPU off
generic cloud functions by default. Missing creds / unhealthy providers fall back to the local correctness invariant.

CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_execution_backend_selector.py --self-test
"""
from __future__ import annotations

import argparse

from src.baltor.workers.execution_backend_selector import py_const_src_teleon_runtime_execution_backend_selector__GENERIC_FUNCTIONS, py_function_src_teleon_runtime_execution_backend_selector__select_backend


def _self_test() -> int:
    fails: list[str] = []

    def chk(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    util = {"capability_id": "utility.hash", "worker_bucket": "utility", "estimated_runtime_ms": 300}

    # default: utility → local function emulator (cheapest, available offline)
    d = py_function_src_teleon_runtime_execution_backend_selector__select_backend(util)
    chk("utility task defaults to local function emulator", d["backend"] == "local_function_emulator@v1", d["backend"])

    # SWITCH BY POLICY → Kubernetes worker (no code change, just policy_override)
    dk = py_function_src_teleon_runtime_execution_backend_selector__select_backend(util, policy_override={"preferred_backends": ["k8s_deployment_worker@candidate"]},
                        available_creds={"k8s_deployment_worker@candidate"})
    chk("same task switches to k8s by policy", dk["backend"] == "k8s_deployment_worker@candidate" and dk["action"] == "use_k8s_deployment_worker")

    # SWITCH BY POLICY → cloud function (creds available)
    dc = py_function_src_teleon_runtime_execution_backend_selector__select_backend(util, policy_override={"preferred_backends": ["gcp_cloud_run_function@candidate"]},
                        available_creds={"gcp_cloud_run_function@candidate"})
    chk("same task switches to cloud function by policy", dc["backend"] == "gcp_cloud_run_function@candidate" and dc["action"] == "use_cloud_function")

    # PRICING-DRIVEN SWITCH (no code change): two candidate backends, flip the pricebook → flip the choice
    elig = {"eligible": ["k8s_deployment_worker@candidate", "gcp_cloud_run_function@candidate"]}
    creds = {"k8s_deployment_worker@candidate", "gcp_cloud_run_function@candidate"}
    pb_k8s_cheap = {"backends": {"k8s_deployment_worker@candidate": {"duration_cost_per_s": 0.01},
                                 "gcp_cloud_run_function@candidate": {"duration_cost_per_s": 0.10}}}
    pb_fn_cheap = {"backends": {"k8s_deployment_worker@candidate": {"duration_cost_per_s": 0.10},
                                "gcp_cloud_run_function@candidate": {"duration_cost_per_s": 0.01}}}
    d1 = py_function_src_teleon_runtime_execution_backend_selector__select_backend(util, policy_override=elig, available_creds=creds, pricebook=pb_k8s_cheap)
    d2 = py_function_src_teleon_runtime_execution_backend_selector__select_backend(util, policy_override=elig, available_creds=creds, pricebook=pb_fn_cheap)
    chk("pricebook A (k8s cheap) → k8s chosen", d1["backend"] == "k8s_deployment_worker@candidate", d1["backend"])
    chk("pricebook B (function cheap) → function chosen (pricing-driven, no code change)", d2["backend"] == "gcp_cloud_run_function@candidate", d2["backend"])

    # HARD GUARD: browser task is never a generic cloud function by default
    br = {"capability_id": "browser.research", "worker_bucket": "browser", "estimated_runtime_ms": 5000, "requires_browser": True}
    db = py_function_src_teleon_runtime_execution_backend_selector__select_backend(br, available_creds=py_const_src_teleon_runtime_execution_backend_selector__GENERIC_FUNCTIONS | {"browser_pool@candidate"})
    chk("browser task NOT routed to a generic cloud function", db["backend"] not in py_const_src_teleon_runtime_execution_backend_selector__GENERIC_FUNCTIONS, db["backend"])

    # HARD GUARD: GPU/model task is never a generic cloud function by default
    gpu = {"capability_id": "model.infer", "worker_bucket": "model_inference", "estimated_runtime_ms": 8000, "requires_gpu": True}
    dg = py_function_src_teleon_runtime_execution_backend_selector__select_backend(gpu, available_creds=py_const_src_teleon_runtime_execution_backend_selector__GENERIC_FUNCTIONS | {"gpu_pool@candidate"})
    chk("GPU task NOT routed to a generic cloud function", dg["backend"] not in py_const_src_teleon_runtime_execution_backend_selector__GENERIC_FUNCTIONS, dg["backend"])

    # MISSING CREDENTIALS → fall back to local correctness invariant
    dm = py_function_src_teleon_runtime_execution_backend_selector__select_backend(util, policy_override={"preferred_backends": ["gcp_cloud_run_function@candidate"]}, available_creds=set())
    chk("missing cloud creds → fall back to local (not the function)", dm["backend"] in ("local_function_emulator@v1", "local_subprocess@v1"))

    # PROVIDER HEALTH FAILURE: the unhealthy preferred backend is NOT chosen (a healthy one is)
    dh = py_function_src_teleon_runtime_execution_backend_selector__select_backend(util, policy_override={"preferred_backends": ["k8s_deployment_worker@candidate"]},
                        available_creds={"k8s_deployment_worker@candidate"},
                        provider_health={"k8s_deployment_worker@candidate": False})
    chk("unhealthy preferred backend is NOT chosen", dh["backend"] != "k8s_deployment_worker@candidate", dh["backend"])
    # when NOTHING eligible is runnable (only an unhealthy backend eligible) → explicit fallback action
    dh2 = py_function_src_teleon_runtime_execution_backend_selector__select_backend(util, policy_override={"eligible": ["k8s_deployment_worker@candidate"]},
                         available_creds={"k8s_deployment_worker@candidate"},
                         provider_health={"k8s_deployment_worker@candidate": False})
    chk("no runnable backend → explicit fallback to local", dh2["action"] == "fallback_due_to_provider_health"
        and dh2["backend"] in ("local_function_emulator@v1", "local_subprocess@v1"), str(dh2))

    # determinism
    chk("deterministic", py_function_src_teleon_runtime_execution_backend_selector__select_backend(util) == py_function_src_teleon_runtime_execution_backend_selector__select_backend(util))

    print(f"\n{'PASS — check_execution_backend_selector: backend choice is policy+pricebook+health+creds driven; same task switches local↔k8s↔cloud-function without code; browser/GPU guarded off generic functions; missing-creds/unhealthy fall back to local.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv=None):
    p = argparse.ArgumentParser(); p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    return _self_test() if a.self_test else (p.print_help() or 0)


if __name__ == "__main__":
    raise SystemExit(_main())
