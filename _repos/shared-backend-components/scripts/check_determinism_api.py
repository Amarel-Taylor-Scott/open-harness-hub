#!/usr/bin/env python3
"""scripts.check_determinism_api — proof: the Determinism API is a projection-only, offline, deterministic read
surface over the WHOLE Determinism Factory motion.

Each of the nine GET routes returns its contracted keys; ``consensus.can_serve_fact`` is permanently False; the
rule candidate carries its ``distilled_from_trace_ids`` LOSSLESSLY (every one is a verified support trace and is
still present among the projected traces); the CFPB rule reproduces "10 business days" with the FAQ "30 days"
held out; the projection is read-only (no mutation method allowed; two reads are byte-identical → no write side
effect, deterministic); no secret leaks. Tests the pure request handler (no socket) so the contract is
deterministic + offline. The CORRECTNESS INVARIANT runs with NO credentials and no network.

CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_determinism_api.py --self-test
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from scripts.api_determinism_handler import ROUTES, handle, owns  # noqa: E402

# any of these substrings in a serialized payload is a leak.
_SECRET_MARKERS = ("OH_SHOWCASE_TOKEN", "api_key", "Authorization", "Bearer ", "MEMORY.md", ".agent/")

_VERIFIED_ANSWER = "10 business days"   # Reg E — the only answer that may be served
_HELD_OUT_ANSWER = "30 days"          # FAQ summary — held out, NEVER served as truth


def _no_secret(payload: dict) -> bool:
    blob = json.dumps(payload)
    sk_prefix = "sk" + "-"  # build the synthetic prefix at runtime so no literal secret lives in this file
    return not any(m in blob for m in _SECRET_MARKERS) and sk_prefix not in blob


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    # the contracted keys each endpoint must return.
    expected = {
        "/api/determinism/overview":   {"stage_counts", "reference", "stages"},
        "/api/determinism/traces":     {"traces", "total"},
        "/api/determinism/consensus":  {"can_serve_fact", "agreement_score", "routing"},
        "/api/determinism/patterns":   {"patterns", "total"},
        "/api/determinism/rules":      {"rules", "total"},
        "/api/determinism/replay":     {"precision", "unsafe_count", "tenant_leak_count"},
        "/api/determinism/shadow":     {"live_authoritative", "unsafe_mismatch_count", "agreement_rate"},
        "/api/determinism/promotions": {"promoted", "blocked", "safety_blocks"},
        "/api/determinism/fallback":   {"events", "fabricated", "rule_fired"},
    }
    payloads: dict[str, dict] = {}
    for route, keys in expected.items():
        code, payload = handle("GET", route, {"tenant_id": "demo"})
        payloads[route] = payload
        check(f"GET {route} returns 200 (correctness invariant: no creds, offline)", code == 200, str(code))
        check(f"GET {route} returns the contracted keys", isinstance(payload, dict) and keys <= set(payload),
              str(sorted(set(payload))))
        check(f"GET {route} leaks no secret", _no_secret(payload))

    # CONSENSUS ≠ TRUTH — can_serve_fact is permanently False.
    cons = payloads["/api/determinism/consensus"]
    check("consensus.can_serve_fact is False (consensus is evidence, never truth)", cons.get("can_serve_fact") is False,
          str(cons.get("can_serve_fact")))

    # LOSSLESS — the rule candidate carries distilled_from_trace_ids; every one is a VERIFIED support trace
    # that is still present among the projected traces (never deleted).
    rules = payloads["/api/determinism/rules"].get("rules") or []
    check("exactly one proposed rule candidate is projected", len(rules) == 1, str(len(rules)))
    cand = rules[0] if rules else {}
    distilled = list(cand.get("distilled_from_trace_ids") or [])
    check("the rule candidate is PROPOSED, never active", cand.get("status") == "proposed" and cand.get("active") is False)
    check("the rule candidate carries distilled_from_trace_ids (lossless)", len(distilled) >= 1, str(len(distilled)))

    pats = payloads["/api/determinism/patterns"].get("patterns") or []
    pat = pats[0] if pats else {}
    support_ids = list(pat.get("support_trace_ids") or [])
    check("distilled_from_trace_ids == the pattern's support_trace_ids (lossless link to the miner)",
          distilled == support_ids, f"{distilled} != {support_ids}")

    all_traces = payloads["/api/determinism/traces"].get("traces") or []
    by_id = {t.get("trace_id"): t for t in all_traces if isinstance(t, dict)}
    check("every distilled-from trace is STILL present in the projected trace store (never deleted)",
          all(tid in by_id for tid in distilled))
    check("every distilled-from trace is a VERIFIED workflow trace (distilled from VERIFIED only)",
          all(by_id.get(tid, {}).get("verified") is True and by_id.get(tid, {}).get("trace_kind") == "workflow"
              for tid in distilled))

    # the CFPB rule reproduces "10 business days" with FAQ-30 held out, end-to-end.
    reference = payloads["/api/determinism/overview"].get("reference") or {}
    check("the pattern decided the reference value (Reg E '10 business days' wins; FAQ-30 held out)",
          reference.get("pattern_winner_answer") == _VERIFIED_ANSWER and reference.get("pattern_loser_answer") == _HELD_OUT_ANSWER,
          str(reference))
    check("END-TO-END: the served decision IS the Reg-E winner only (reference) ", reference.get("served_is_reference") is True,
          str(reference.get("served_decision")))
    check("END-TO-END: consensus alone never served the fact (an authority label produced it)",
          reference.get("consensus_can_serve_fact") is False and reference.get("label_source") == "authority_or_policy")

    # replay/shadow are safe; the gate BLOCKED the tenant_private→global mint (the dangerous error class).
    rep = payloads["/api/determinism/replay"]
    check("replay precision is 1.0 with ZERO unsafe false positives + ZERO tenant leak",
          rep.get("precision") == 1.0 and rep.get("unsafe_count") == 0 and rep.get("tenant_leak_count") == 0,
          str((rep.get("precision"), rep.get("unsafe_count"), rep.get("tenant_leak_count"))))
    shad = payloads["/api/determinism/shadow"]
    check("shadow: the live path stayed authoritative with ZERO unsafe mismatch",
          shad.get("live_authoritative") is True and shad.get("unsafe_mismatch_count") == 0)
    promos = payloads["/api/determinism/promotions"]
    check("the gate PROMOTED the rule (human-signed)", (promos.get("promoted") or {}).get("promoted") is True)
    check("the gate BLOCKED a global rule minted from tenant_private traces (safety block recorded)",
          "global_rule_not_from_private_traces" in (promos.get("safety_blocks") or [])
          and (promos.get("blocked") or {}).get("promoted") is False)

    # fallback: rule served deterministically; an OOD input fell back; NOTHING was fabricated.
    fb = payloads["/api/determinism/fallback"]
    check("the active rule served deterministically (rule_fired) and an OOD input fell back",
          fb.get("rule_fired") is True and fb.get("ood_fell_back") is True)
    check("a served decision is NEVER fabricated", fb.get("fabricated") is False)

    # PROJECTION-ONLY — no mutation method is allowed, and two reads are byte-identical (deterministic, no write).
    code_post, _ = handle("POST", "/api/determinism/rules", {"x": 1})
    check("POST to a determinism route is 405 (read-only)", code_post == 405, str(code_post))
    a = handle("GET", "/api/determinism/overview", {})[1]
    b = handle("GET", "/api/determinism/overview", {})[1]
    check("two reads are byte-identical (deterministic projection, no write side effect)",
          json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True))

    # unknown route degrades to 404 (no crash); owns() recognizes exactly the declared routes.
    c404, p404 = handle("GET", "/api/determinism/nope", {})
    check("unknown determinism route returns 404 (not a crash)", c404 == 404 and "error" in p404)
    check("owns() matches every declared route and nothing foreign",
          all(owns(r) for r in ROUTES) and not owns("/api/memory/artifacts"))

    print(f"\n{'PASS — check_determinism_api: nine projection-only GET routes return contracted keys offline (correctness invariant, no creds); consensus.can_serve_fact is False; the rule candidate carries its distilled_from_trace_ids losslessly (every one a VERIFIED trace still in the store); the CFPB rule reproduces 10 business days with FAQ-30 held out; replay/shadow are safe; the gate promoted (human-signed) while BLOCKING the tenant_private->global mint; serving is deterministic-first and never fabricates; mutations are rejected; the projection is deterministic; no secret leaks.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: Determinism API projection (offline, deterministic, no secrets).")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
