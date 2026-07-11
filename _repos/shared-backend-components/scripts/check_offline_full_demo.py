#!/usr/bin/env python3
"""scripts.check_offline_full_demo — proof (North Star): the full offline demo runs the WHOLE governed
context motion across every core section AND the CFPB correctness invariant holds. The mandatory "fully working,
all components" gate, offline + deterministic.

CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_offline_full_demo.py --self-test
"""
from __future__ import annotations

import argparse

from scripts.demo_offline_full_baltor import run_offline_full_demo

# every core section the demo must exercise (North Star)
_REQUIRED_SECTIONS = {
    "intake_ingestion", "source_artifacts", "decomposition_structured", "atomic_facts",
    "narrative_allegations", "artifact_ledger", "deterministic_graph", "temporal_fact_graph",
    "conflict_detection", "reconciliation", "fragility_detection", "verification_gate",
    "optimization_suite", "consumption_service", "native_format_sidecars", "memory_context",
    "worker_flywheel_control_plane", "receipts",
}
_OK_STATUSES = {"ok", "m6_candidate", "m8_ui"}


def _self_test() -> int:
    fails: list[str] = []

    def chk(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    out = run_offline_full_demo()
    sec = {s["section"]: s["status"] for s in out["sections"]}

    chk("every core section ran", _REQUIRED_SECTIONS <= set(sec), str(_REQUIRED_SECTIONS - set(sec)))
    bad = {n: st for n, st in sec.items() if st not in _OK_STATUSES}
    chk("no section is broken/absent", bad == {}, str(bad))

    # CFPB correctness invariant
    g = out["reference"]
    chk("answer = '10 business days'", g["answer_correct"], str(out.get("answer")))
    chk("FAQ '30 days' held out (never served as fact)", g["faq_30_held_out"])
    chk("the reconciled winner is NOT held out", g["winner_not_held_out"])
    chk("narrative allegation held out", g["allegation_held_out"])
    chk("source/authority lineage preserved on the served fact", g["source_lineage_preserved"])
    chk("a receipt is issued", g["receipt_present"])
    chk("only the reconciled winner is served (no unverified truth)", g["only_winner_served"] and g["no_allegation_or_faq_served"])
    chk("demo reports overall ok", out["ok"])

    # determinism
    out2 = run_offline_full_demo()
    chk("deterministic (same reference result)", out2["reference"] == out["reference"])

    print(f"\n{'PASS — check_offline_full_demo: the full offline demo runs all 18 core sections + the CFPB correctness invariant (10 business days; FAQ-30 + allegation held out; lineage + receipt; only the winner served); deterministic.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv=None):
    p = argparse.ArgumentParser(); p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    return _self_test() if a.self_test else (p.print_help() or 0)


if __name__ == "__main__":
    raise SystemExit(_main())
