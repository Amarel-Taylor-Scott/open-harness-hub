#!/usr/bin/env python3
"""check_access_policy — the authorization layer (who may use a tool/key) is real, deny-by-default, and BYO-aware.

Owner: not every tool/key is accessible to every user. Proves: real resources classify to the right tier (evasion ->
restricted, social/ToS -> restricted, platform key -> plan_gated, private-bench -> internal, keyless deterministic ->
public); the resolver DENIES BY DEFAULT (anonymous can't touch platform keys / restricted / internal); a paid plan or a
BYO key unlocks plan_gated; restricted needs an explicit grant; internal is staff-only; a BYO key never grants a
restricted tool. serves_truth=false.

  python3 _repos/shared-backend-components/scripts/check_access_policy.py --self-test
"""
from __future__ import annotations

import json
from pathlib import Path

from src.teleon.runtime.access_policy import py_class_src_teleon_runtime_access_policy__Principal, py_function_src_teleon_runtime_access_policy__accessible, py_function_src_teleon_runtime_access_policy__can_access, py_function_src_teleon_runtime_access_policy__classify

REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource


def _load(name):
    return json.loads((_resource("architecture") / name).read_text(encoding="utf-8"))


def _self_test() -> int:
    fails = []
    def ck(n, ok, d=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok: fails.append(n)

    # resources built from the REAL registries (the fields the policy reads)
    undetected = {"id": "undetected_chromedriver", "governance": "evasion_restricted"}          # web_browsing_stack
    fb = {"id": "fb_page_scrape", "plane": "social_scrape", "governance": "ToS_sensitive"}        # external_api
    anthropic = {"id": "anthropic", "key_ownership": "both", "key_service": "anthropic"}          # credential (platform)
    serpapi = {"id": "serpapi", "key_ownership": "byo", "key_service": "serpapi"}                 # credential (byo)
    faiss = {"id": "faiss", "keyless": True, "deterministic": True}                               # tool_registry permissive
    brain = {"id": "descent_attempt_store", "internal": True}                                     # internal

    ck("evasion tool -> restricted/evasion", py_function_src_teleon_runtime_access_policy__classify(undetected)["tier"] == "restricted" and py_function_src_teleon_runtime_access_policy__classify(undetected)["grant"] == "evasion")
    ck("social/ToS API -> restricted/social_scrape", py_function_src_teleon_runtime_access_policy__classify(fb)["grant"] == "social_scrape")
    ck("platform key -> plan_gated", py_function_src_teleon_runtime_access_policy__classify(anthropic)["tier"] == "plan_gated")
    ck("byo key -> plan_gated (BYO satisfies)", py_function_src_teleon_runtime_access_policy__classify(serpapi)["tier"] == "plan_gated")
    ck("keyless deterministic tool -> public", py_function_src_teleon_runtime_access_policy__classify(faiss)["tier"] == "public")
    ck("private-bench / brain -> internal", py_function_src_teleon_runtime_access_policy__classify(brain)["tier"] == "internal")

    anon = py_class_src_teleon_runtime_access_policy__Principal.from_role("anonymous")
    user = py_class_src_teleon_runtime_access_policy__Principal.from_role("user")
    dev = py_class_src_teleon_runtime_access_policy__Principal.from_role("developer")               # plan pro
    staff = py_class_src_teleon_runtime_access_policy__Principal.from_role("staff")                 # internal + all grants
    user_byo = py_class_src_teleon_runtime_access_policy__Principal.from_role("user", byo_keys={"anthropic"})
    user_evasion = py_class_src_teleon_runtime_access_policy__Principal(id="u2", role="user", plan="free", grants={"evasion"})

    # deny-by-default for sensitive
    ck("anonymous DENIED a platform key", not py_function_src_teleon_runtime_access_policy__can_access(anon, anthropic)[0])
    ck("anonymous DENIED an evasion tool", not py_function_src_teleon_runtime_access_policy__can_access(anon, undetected)[0])
    ck("anonymous DENIED internal", not py_function_src_teleon_runtime_access_policy__can_access(anon, brain)[0])
    ck("everyone gets a public tool (even anonymous)", py_function_src_teleon_runtime_access_policy__can_access(anon, faiss)[0])
    # plan / BYO unlock plan_gated
    ck("free user DENIED a platform key (cost)", not py_function_src_teleon_runtime_access_policy__can_access(user, anthropic)[0])
    ck("paid (developer) gets a platform key", py_function_src_teleon_runtime_access_policy__can_access(dev, anthropic)[0])
    ck("BYO key unlocks the platform-key gate for a free user", py_function_src_teleon_runtime_access_policy__can_access(user_byo, anthropic)[0])
    ck("byo-only key DENIED without the user's own key", not py_function_src_teleon_runtime_access_policy__can_access(user, serpapi)[0])
    # restricted needs an explicit grant; BYO does NOT grant a restricted tool
    ck("user without grant DENIED the evasion tool", not py_function_src_teleon_runtime_access_policy__can_access(user, undetected)[0])
    ck("user WITH the evasion grant gets it", py_function_src_teleon_runtime_access_policy__can_access(user_evasion, undetected)[0])
    ck("BYO key does NOT grant a restricted tool", not py_function_src_teleon_runtime_access_policy__can_access(user_byo, undetected)[0])
    # internal staff-only
    ck("staff gets internal", py_function_src_teleon_runtime_access_policy__can_access(staff, brain)[0])
    ck("developer (pro, not staff) DENIED internal", not py_function_src_teleon_runtime_access_policy__can_access(dev, brain)[0])

    # accessible() filters a mixed set; reasons are honest
    pool = [faiss, anthropic, undetected, fb, serpapi, brain]
    anon_can = {r["id"] for r in py_function_src_teleon_runtime_access_policy__accessible(anon, pool)}
    ck("anonymous accessible set = only the public tool", anon_can == {"faiss"}, str(anon_can))
    staff_can = {r["id"] for r in py_function_src_teleon_runtime_access_policy__accessible(staff, pool)}
    ck("staff accessible set spans all tiers (incl. restricted+internal)", {"undetected_chromedriver", "fb_page_scrape", "descent_attempt_store"} <= staff_can)

    cfg = _load("access_policy.json")
    ck("tiers ordered least->most privileged", [t["rank"] for t in cfg["tiers"]] == sorted(t["rank"] for t in cfg["tiers"]))
    ck("serves_truth=false", cfg.get("serves_truth") is False)

    print("\n" + ("PASS - check_access_policy: classifies real resources, deny-by-default, plan/BYO/grant/staff gates, BYO "
                  "never grants restricted tools." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(_self_test())
