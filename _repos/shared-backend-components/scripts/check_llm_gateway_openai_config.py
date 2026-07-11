#!/usr/bin/env python3
"""scripts.check_llm_gateway_openai_config — proof: the OpenAI provider loads its key ONLY from
env://OPENAI_API_KEY; when the env var is missing it is simply UNAVAILABLE (the system stays green and falls
back to the stub); and NO network call is made during a self-test (network is gated off).

CLI: python3 _repos/shared-backend-components/scripts/check_llm_gateway_openai_config.py --self-test
"""
from __future__ import annotations

import argparse
import os

from scripts.llm_gateway.providers import OpenAIResponsesAdapter, _network_allowed, default_registry
from scripts.llm_gateway.router import LLMGateway
from scripts.llm_gateway.secrets import SecretsResolver
from scripts.llm_gateway.types import LLMRequest, RoutingPolicy
from scripts.security.tenant_catalog import TenantPolicy


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    # guarantee a clean, offline, key-less environment for this proof
    os.environ.pop("OPENAI_API_KEY", None)
    os.environ.pop("BALTOR_LLM_ALLOW_NETWORK", None)

    spec = default_registry().get("openai.default")
    check("openai provider config references env://OPENAI_API_KEY (no raw key)", spec.api_key_ref == "env://OPENAI_API_KEY")
    check("network is OFF by default (no call during self-test)", _network_allowed() is False)

    adapter = OpenAIResponsesAdapter()
    check("with no env key, the openai provider is UNAVAILABLE", adapter.available(spec) is False)
    check("SecretsResolver.has() agrees the key is absent", SecretsResolver.has(spec.api_key_ref) is False)

    # gateway with openai preferred + stub fallback → openai unavailable → stub serves → system GREEN
    gw = LLMGateway()
    req = LLMRequest(request_id="r", tenant_id="acme", task_type="conflict_explanation",
                     prompt_id="p", prompt_version="v1", schema_id="ConflictExplanation",
                     input_artifact_ids=["art-a"],
                     routing_policy=RoutingPolicy(preferred_providers=["openai.default"], fallback_providers=["stub.local"]))
    resp = gw.complete(req, TenantPolicy("acme"), known_artifact_ids={"art-a"})
    check("missing key → provider unavailable but system stays GREEN (falls back to stub)",
          resp.status == "ok" and resp.provider == "stub.local", f"{resp.provider}/{resp.status}")
    check("trace shows openai was considered + marked unavailable (not a crash)",
          any(a["provider"] == "openai.default" and a["status"] == "unavailable" for a in resp.trace["attempts"]),
          str([(a["provider"], a["status"]) for a in resp.trace["attempts"]]))
    check("no network attempt recorded (no error:network_disabled while key absent)",
          not any("network" in a.get("status", "") for a in resp.trace["attempts"]))

    print(f"\n{'PASS — check_llm_gateway_openai_config: OpenAI provider is env-key-only, optional, network-gated; absent key → unavailable + stub fallback; no network in self-test.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: OpenAI provider config (env-only, optional, offline-safe).")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
