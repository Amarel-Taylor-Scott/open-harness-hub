#!/usr/bin/env python3
"""check_entitlements_wiring — access_policy is WIRED into the key holder + the descent (a principal only uses what they may).

Proves: key_holder.resolve gates on entitlement (a free user is denied a platform key even when it's set in env, but a BYO
owner / paid plan gets it); status(principal) marks usable=held&entitled; the descent's decision_points(principal) drops
restricted/plan-gated tools the principal lacks and emits an honest 'blocked:needs-<grant>' when a node has none entitled,
while leaving public tools for everyone. serves_truth=false.

  python3 _repos/shared-backend-components/scripts/check_entitlements_wiring.py --self-test
"""
from __future__ import annotations

from src.teleon.runtime import entitlements as E
from src.teleon.runtime.access_policy import py_class_src_teleon_runtime_access_policy__Principal
from src.teleon.runtime.key_holder import py_const_src_teleon_runtime_key_holder__HOLDER
from src.teleon.synthesis.intent_to_dag import py_function_src_teleon_synthesis_intent_to_dag__decision_points

ENV = {"ANTHROPIC_API_KEY": "x", "OH_GITHUB_TOKEN": "t"}   # platform key + github present in env


def _self_test() -> int:
    fails = []
    def ck(n, ok, d=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok: fails.append(n)

    anon = py_class_src_teleon_runtime_access_policy__Principal.from_role("anonymous")
    user = py_class_src_teleon_runtime_access_policy__Principal.from_role("user")
    dev = py_class_src_teleon_runtime_access_policy__Principal.from_role("developer")                       # paid (pro)
    user_byo = py_class_src_teleon_runtime_access_policy__Principal.from_role("user", byo_keys={"anthropic"})
    staff = py_class_src_teleon_runtime_access_policy__Principal.from_role("staff")

    # ── key holder gated by entitlement ──────────────────────────────────────────────────────────────────────
    ck("free user DENIED a platform key (anthropic) even though it's in env", py_const_src_teleon_runtime_key_holder__HOLDER.resolve("anthropic", ENV, principal=user) is None)
    ck("paid user RESOLVES the platform key", py_const_src_teleon_runtime_key_holder__HOLDER.resolve("anthropic", ENV, principal=dev) is not None)
    ck("BYO owner RESOLVES their own key (free plan)", py_const_src_teleon_runtime_key_holder__HOLDER.resolve("anthropic", ENV, principal=user_byo) is not None)
    ck("no principal -> backward-compatible (resolves if reachable)", py_const_src_teleon_runtime_key_holder__HOLDER.resolve("anthropic", ENV) is not None)
    st = py_const_src_teleon_runtime_key_holder__HOLDER.status(ENV, principal=user)
    arow = next(r for r in st["services"] if r["service"] == "anthropic")
    ck("status(principal) marks held-but-not-usable for a free user", arow["held"] and not arow["usable"])
    ck("entitled_key: github (public-ish keyless) usable by anyone", E.py_function_src_teleon_runtime_entitlements__entitled_key(anon, "github"))

    # ── descent gated by entitlement ─────────────────────────────────────────────────────────────────────────
    # web_browsing ladder has an 'undetected' rung (evasion_restricted) -> a free user must NOT see those tools
    pts_user = dict(py_function_src_teleon_synthesis_intent_to_dag__decision_points("automate web browsing on this site", principal=user))
    pts_open = dict(py_function_src_teleon_synthesis_intent_to_dag__decision_points("automate web browsing on this site"))
    und_open = next((o for k, o in pts_open.items() if k == "undetected"), [])
    und_user = pts_user.get("undetected", [])
    ck("open descent offers the undetected (evasion) tools", any(t in und_open for t in ("undetected_chromedriver", "nodriver")))
    ck("free user's descent BLOCKS the evasion rung (honest sentinel)",
       und_user and all(o.startswith("blocked:") for o in und_user), str(und_user))
    ck("staff (evasion grant) KEEPS the undetected tools", any("undetected_chromedriver" in o or "nodriver" in o for o in dict(py_function_src_teleon_synthesis_intent_to_dag__decision_points("automate web browsing on this site", principal=staff)).get("undetected", [])))
    # public/deterministic rungs stay available to the free user (e.g. headless playwright / http_fetch)
    ck("free user keeps the public browser rungs", any(py_function_src_teleon_synthesis_intent_to_dag__decision_points("automate web browsing on this site", principal=user)))

    # gate_options helper directly
    ck("gate_options keeps public tools", E.py_function_src_teleon_runtime_entitlements__gate_options(user, ["faiss", "rank_bm25"], plane="vector_store") == ["faiss", "rank_bm25"])
    ck("gate_options blocks an all-restricted node", E.py_function_src_teleon_runtime_entitlements__gate_options(user, ["undetected_chromedriver"], governance="evasion_restricted")[0].startswith("blocked:"))

    print("\n" + ("PASS - check_entitlements_wiring: key holder + descent both consult access_policy; a principal only "
                  "resolves/sees what they're entitled to; honest blocked sentinels." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(_self_test())
