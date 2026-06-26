#!/usr/bin/env python3
"""scripts.check_llm_router_policy — proof: the router is policy-aware. A tenant that disallows external APIs
NEVER routes to OpenAI (policy exclusion, not a transport retry); a tenant that allows it AND has a key
DOES select OpenAI and falls back to the stub on a retryable failure; restricted data never leaves to an
external provider.

CLI: python3 scripts/check_llm_router_policy.py --self-test
"""
from __future__ import annotations

import argparse
import os

from scripts.llm_gateway.router import LLMGateway
from scripts.llm_gateway.types import LLMRequest, RoutingPolicy
from scripts.security.tenant_catalog import TenantPolicy


def _req(*, classification="internal") -> LLMRequest:
    return LLMRequest(request_id="r", tenant_id="acme", task_type="conflict_explanation",
                      prompt_id="p", prompt_version="v1", schema_id="ConflictExplanation",
                      input_artifact_ids=["art-a"], data_classification=classification,
                      routing_policy=RoutingPolicy(preferred_providers=["openai.default"], fallback_providers=["stub.local"]))


def _status_for(resp, provider):
    return [a["status"] for a in resp.trace["attempts"] if a["provider"] == provider]


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    os.environ.pop("BALTOR_LLM_ALLOW_NETWORK", None)
    gw = LLMGateway()
    known = {"art-a"}

    # 1) tenant disallows external APIs → openai is POLICY-BLOCKED (not retried as transport), stub serves
    no_ext = TenantPolicy("acme", allow_external_api=False)
    r1 = gw.complete(_req(), no_ext, known_artifact_ids=known)
    check("external-disallowed tenant never gets an OK from openai", "ok" not in _status_for(r1, "openai.default"))
    check("openai is excluded as POLICY_BLOCKED (not a transport error)",
          _status_for(r1, "openai.default") == ["policy_blocked"], str(_status_for(r1, "openai.default")))
    check("the request still succeeds via the stub fallback", r1.provider == "stub.local" and r1.status == "ok")

    # 2) restricted data classification → external provider blocked even if tenant allows external APIs
    r_restr = gw.complete(_req(classification="restricted"), TenantPolicy("acme", allow_external_api=True,
                          allowed_llm_providers=["openai.default", "stub.local"]), known_artifact_ids=known)
    check("restricted data never routes to an external provider", _status_for(r_restr, "openai.default") == ["policy_blocked"])
    check("restricted request still served locally by the stub", r_restr.provider == "stub.local")

    # 3) tenant allows openai AND a key exists → openai is SELECTED, then falls back to stub on retryable failure
    os.environ["OPENAI_API_KEY"] = "test-present-not-a-real-key"  # presence only; network stays OFF
    try:
        gw2 = LLMGateway()
        r2 = gw2.complete(_req(), TenantPolicy("acme", allow_external_api=True,
                          allowed_llm_providers=["openai.default", "stub.local"]), known_artifact_ids=known)
        check("openai IS selected/attempted when allowed + key present", "error:network_disabled" in _status_for(r2, "openai.default"),
              str(_status_for(r2, "openai.default")))
        check("router FALLS BACK to the stub after a retryable openai failure", r2.provider == "stub.local" and r2.status == "ok")
        check("a retryable provider failure is marked retryable (not a policy violation)",
              any(a["provider"] == "openai.default" and a["reason"] == "retryable" for a in r2.trace["attempts"]))
    finally:
        os.environ.pop("OPENAI_API_KEY", None)

    print(f"\n{'PASS — check_llm_router_policy: policy-aware routing — external-disallowed/restricted excludes OpenAI (not retried as transport); allowed+keyed selects OpenAI then falls back to stub on retryable failure.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: policy-aware LLM routing + fallback.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
