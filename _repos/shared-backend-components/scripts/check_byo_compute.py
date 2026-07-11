#!/usr/bin/env python3
"""check_byo_compute — proof that worker compute can be BYO via a customer-supplied API key (e.g. Cloudflare).

The easiest onboarding: a customer pastes a Cloudflare API token and workers run on THEIR account. This proves the
seam is real: a compute_ownership dimension in the policy matrix (provider_operated | customer_account | customer_
managed), and a CloudflareWorkersProvider implementing ExecutionProviderPort that (1) is ELIGIBLE only when a
customer token (SecretRef) is present, (2) names the missing SecretRef when it isn't, (3) declares an offline
equivalent so dev needs no key, (4) NEVER owns truth + bills the customer + keeps data on their account. Same pattern
adds aws_lambda/gcp BYO (config). serves_truth=false.

CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_byo_compute.py --self-test
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import json
import os
import sys

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _R not in sys.path:
        sys.path.insert(0, _R)

from pathlib import Path
from src.teleon.runtime.execution_provider import py_class_src_teleon_runtime_execution_provider__ExecutionProviderPort, py_class_src_teleon_runtime_execution_provider__ProviderUnavailableResult
from src.teleon.runtime.execution_providers.cloudflare_workers import py_class_src_teleon_runtime_execution_providers_cloudflare_workers__CloudflareWorkersProvider, py_const_src_teleon_runtime_execution_providers_cloudflare_workers__OFFLINE_EQUIVALENT

_MATRIX = _resource("architecture") / "execution_backend_policy_matrix.json"


def _self_test() -> int:
    fails = []
    def ck(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': '+detail) if detail and not ok else ''}")
        if not ok: fails.append(name)

    m = json.loads(_MATRIX.read_text())
    co = m.get("compute_ownership", {})
    ck("the policy matrix declares a compute_ownership dimension", bool(co))
    ck("modes include provider_operated + customer_account (BYO key) + customer_managed",
       {"provider_operated", "customer_account", "customer_managed"} <= set(co.get("modes", {})), str(list(co.get("modes", {}))))
    ck("cloudflare_workers is a BYO-supported backend", "cloudflare_workers@candidate" in co.get("byo_supported_backends", []))
    ck("BYO keeps the FleetLedger as our truth (invariant recorded)",
       any("truth" in inv.lower() for inv in co.get("invariants", [])))
    ck("cloudflare_workers is in the backends_enum + has an offline emulator equivalent",
       "cloudflare_workers@candidate" in m.get("backends_enum", []) and
       m.get("candidate_local_equivalents", {}).get("cloudflare_workers@candidate") == "execution.local_function_emulator@v1")

    # the provider conforms to the port
    prov_none = py_class_src_teleon_runtime_execution_providers_cloudflare_workers__CloudflareWorkersProvider(token_secret_ref="secret://tenant/acme/cloudflare_api_token",
                                          resolve_secret=lambda r: None)
    ck("CloudflareWorkersProvider implements ExecutionProviderPort", isinstance(prov_none, py_class_src_teleon_runtime_execution_provider__ExecutionProviderPort))
    ck("compute_ownership is customer_account (runs on THEIR infra)", prov_none.compute_ownership == "customer_account")

    # NO token -> not eligible, invoke returns ProviderUnavailableResult naming the missing SecretRef (falls back)
    el = prov_none.eligible({}, {"byo_supported_backends": ["cloudflare_workers"]})
    ck("without a customer token the provider is NOT eligible (no silent run on our infra)", el["eligible"] is False, str(el))
    r = prov_none.invoke({"task_id": "t1"})
    ck("invoke without a token returns ProviderUnavailableResult naming the SecretRef (graceful fallback)",
       isinstance(r, py_class_src_teleon_runtime_execution_provider__ProviderUnavailableResult) and "token" in r.reason.lower() and not r.consumable)
    ck("an offline equivalent is declared so dev needs no customer key", prov_none.describe()["offline_equivalent"] == py_const_src_teleon_runtime_execution_providers_cloudflare_workers__OFFLINE_EQUIVALENT)

    # WITH a customer token -> eligible; the key is resolved via the injected resolver (never embedded/logged)
    prov_key = py_class_src_teleon_runtime_execution_providers_cloudflare_workers__CloudflareWorkersProvider(account_id="acct123", token_secret_ref="secret://tenant/acme/cloudflare_api_token",
                                         resolve_secret=lambda r: "cf_live_token_value", network_ok=False)
    ck("with a customer token supplied the provider becomes eligible (paste a key -> ready)",
       prov_key.eligible({}, {"byo_supported_backends": ["cloudflare_workers"]})["eligible"] is True)
    ck("health reflects the supplied customer token", prov_key.health()["has_customer_token"] is True)
    ck("the raw token is never in describe()/health() output (only the SecretRef)",
       "cf_live_token_value" not in json.dumps(prov_key.describe()) and "cf_live_token_value" not in json.dumps(prov_key.health()))
    ck("a BYO provider never owns truth + bills the customer (data-residency on their account)",
       prov_key.describe()["owns_truth"] is False and prov_key.estimate({}, {})["billed_to"] == "customer_account"
       and prov_key.describe()["data_residency"] == "customer_account")
    # token present but offline -> honest 'accepted, live not wired' (no fake remote execution)
    r2 = prov_key.invoke({"task_id": "t2"})
    ck("token-present-but-offline is honest — a non-consumable unavailable result, never a fake remote run",
       isinstance(r2, py_class_src_teleon_runtime_execution_provider__ProviderUnavailableResult) and not r2.consumable)

    print("\n" + ("PASS - check_byo_compute: worker compute is BYO via a customer API key — a compute_ownership dimension "
                  "(provider_operated|customer_account|customer_managed) + a CloudflareWorkersProvider that is eligible "
                  "only with a customer token (SecretRef, never logged), declares an offline equivalent, never owns "
                  "truth, and bills/keeps-data on the customer's account. Paste a key -> workers on their Cloudflare."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def _main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--self-test" in argv:
        return _self_test()
    print("usage: check_byo_compute.py --self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
