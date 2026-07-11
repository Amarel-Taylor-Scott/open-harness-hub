#!/usr/bin/env python3
"""check_execution_provider_factory — proof of the multi-backend provider factory + control-plane dispatch.

More compute options than Cloudflare: the factory maps every backend (Cloudflare Workers, Kubernetes, the serverless
family — Lambda/GCP/Azure, local emulators) to an ExecutionProviderPort instance; the dispatcher routes a task to the
CONFIGURED compute per function and FALLS BACK to the local emulator when creds/network are absent — never crashes,
never runs silently on our infra, never owns truth. serves_truth=false.

CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_execution_provider_factory.py --self-test
"""
from __future__ import annotations

import json
import os
import sys

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _R not in sys.path:
        sys.path.insert(0, _R)

from src.teleon.runtime.execution_provider import py_class_src_teleon_runtime_execution_provider__ExecutionProviderPort, py_class_src_teleon_runtime_execution_provider__ProviderUnavailableResult
from src.teleon.runtime.execution_providers.factory import py_function_src_teleon_runtime_execution_providers_factory__get_execution_provider, py_function_src_teleon_runtime_execution_providers_factory__supported_backends
from src.teleon.runtime.dispatch import py_function_src_teleon_runtime_dispatch__dispatch as dispatch


def _self_test() -> int:
    fails = []
    def ck(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': '+detail) if detail and not ok else ''}")
        if not ok: fails.append(name)

    # factory covers more than Cloudflare
    ck("factory supports Cloudflare + Kubernetes + serverless family + local",
       {"cloudflare_workers", "k8s_deployment_worker", "aws_lambda", "gcp_cloud_run_function", "local_function_emulator"}
       <= set(py_function_src_teleon_runtime_execution_providers_factory__supported_backends()), str(py_function_src_teleon_runtime_execution_providers_factory__supported_backends()))
    ck("an unknown backend raises (no silent default)", _raises(lambda: py_function_src_teleon_runtime_execution_providers_factory__get_execution_provider("nope")))

    # each provider conforms to the port + declares its ownership/offline-equivalent
    for backend, exp_owner in [("cloudflare_workers", "customer_account"), ("k8s_deployment_worker", "customer_managed"),
                               ("aws_lambda", "customer_account"), ("azure_function", "customer_account")]:
        p = py_function_src_teleon_runtime_execution_providers_factory__get_execution_provider(backend)
        ck(f"{backend}: implements ExecutionProviderPort", isinstance(p, py_class_src_teleon_runtime_execution_provider__ExecutionProviderPort))
        ck(f"{backend}: compute_ownership = {exp_owner}", getattr(p, "compute_ownership", None) == exp_owner)

    # K8s + Lambda are eligible ONLY with customer creds (no silent run on our infra)
    k8s_no = py_function_src_teleon_runtime_execution_providers_factory__get_execution_provider("k8s_deployment_worker", secret_refs={"kube_api_endpoint": "secret://t/ep", "kube_token": "secret://t/tok"}, resolve_secret=lambda r: None)
    ck("k8s without creds is NOT eligible + invoke returns a non-consumable unavailable (falls back)",
       k8s_no.eligible({}, {})["eligible"] is False and isinstance(k8s_no.invoke({}), py_class_src_teleon_runtime_execution_provider__ProviderUnavailableResult))
    k8s_yes = py_function_src_teleon_runtime_execution_providers_factory__get_execution_provider("k8s_deployment_worker", secret_refs={"kube_api_endpoint": "secret://t/ep", "kube_token": "secret://t/tok"}, resolve_secret=lambda r: "K8S_TOKEN_SECRET_XYZ", network_ok=True)
    ck("k8s with creds becomes eligible (paste cluster endpoint + token -> ready)", k8s_yes.eligible({}, {})["eligible"] is True)
    ck("k8s never owns truth", k8s_yes.describe()["owns_truth"] is False)
    ck("the raw credential value is never in describe() output (only SecretRefs)", "K8S_TOKEN_SECRET_XYZ" not in json.dumps(k8s_yes.describe()))

    lam = py_function_src_teleon_runtime_execution_providers_factory__get_execution_provider("aws_lambda", secret_refs={"aws_access_key_id": "secret://t/k", "aws_secret_access_key": "secret://t/s"}, resolve_secret=lambda r: None)
    ck("aws_lambda is eligible only with AWS creds", lam.eligible({}, {})["eligible"] is False)
    ck("unknown serverless flavor raises", _raises(lambda: py_function_src_teleon_runtime_execution_providers_factory__get_execution_provider("totally_made_up_lambda")))

    # CONTROL-PLANE DISPATCH: routes to the configured compute, falls back to local when creds/network absent
    d = py_function_src_teleon_runtime_dispatch__dispatch("demo", "extraction", {"task_id": "t1", "input_text": "x"}, resolve_secret=lambda r: None, network_ok=False)
    ck("dispatch routes to the CONFIGURED compute (cloudflare for extraction)", d["requested_compute"] == "cloudflare_workers", str(d))
    ck("dispatch FALLS BACK to the local emulator when creds/network are absent (never crashes)",
       d["fell_back"] is True and "local" in d["ran_on"])
    ck("dispatch records compute_ownership + never serves truth", d["compute_ownership"] == "customer_account" and d["serves_truth"] is False)

    print("\n" + ("PASS - check_execution_provider_factory: more compute than Cloudflare — a factory mapping every "
                  "backend (Cloudflare/K8s/serverless/local) to an ExecutionProviderPort, each eligible only with "
                  "customer creds, and a control-plane dispatcher that routes to the configured compute per function + "
                  "falls back to the local emulator. Never owns truth; creds stay SecretRefs."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def _raises(fn, exc=Exception) -> bool:
    try:
        fn(); return False
    except exc:
        return True


def _main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--self-test" in argv:
        return _self_test()
    print("usage: check_execution_provider_factory.py --self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
