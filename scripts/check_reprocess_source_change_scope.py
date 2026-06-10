#!/usr/bin/env python3
"""scripts.check_reprocess_source_change_scope — proof: a source change yields a MINIMAL reprocessing plan.

A changed narrative sentence reruns sentence→allegation→emotion→conclusion→context_pack (and receipt) but
NOT the unrelated structured-field facts; a changed structured field reruns atomic_fact→conclusion→pack
(and receipt) but NOT the narrative grains.

CLI: python3 scripts/check_reprocess_source_change_scope.py --self-test
"""
from __future__ import annotations

import argparse

from scripts.pipeline_runtime.cfpb_artifacts import build_cfpb_artifacts
from scripts.pipeline_runtime.reprocess_planner import plan_for_source_change
from scripts.pipeline_runtime.source_graph import build_cfpb_source_graph
from scripts.security.tenant_catalog import TenantPolicy

REC = {"complaint_id": "CFPB-1", "product": "Credit card", "issue": "Billing dispute",
       "company": "Acme Bank", "state": "CA", "date_received": "2026-01-02",
       "consumer_complaint_narrative": "I was charged twice. The company refused to refund me. This is unfair."}


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    policy = TenantPolicy("acme")
    prior = build_cfpb_artifacts(REC, policy)["artifacts"]
    g0 = build_cfpb_source_graph(REC, policy)

    # ── change ONE narrative sentence ──
    rec_narr = dict(REC, consumer_complaint_narrative="I was charged once. The company refused to refund me. This is unfair.")
    plan_n = plan_for_source_change(g0, build_cfpb_source_graph(rec_narr, policy), prior)
    rerun_n = set(plan_n.steps_to_rerun)
    check("narrative sentence change requires a semantic reprocess", plan_n.semantic_reprocess_required)
    check("narrative change reruns sentence/allegation/emotion/conclusion/context_pack/receipt",
          {"sentence", "narrative_allegation", "emotion_signal", "conclusion", "context_pack", "receipt"} <= rerun_n, str(sorted(rerun_n)))
    check("narrative change does NOT rerun structured-field atomic_fact",
          "atomic_fact" in plan_n.steps_to_skip and "atomic_fact" not in rerun_n)
    check("affected derived artifacts are scoped to the rerun types (no atomic_fact)",
          all(a.artifact_type in rerun_n for a in prior if a.artifact_id in set(plan_n.affected_derived_artifacts))
          and not any(a.artifact_type == "atomic_fact" and a.artifact_id in set(plan_n.affected_derived_artifacts) for a in prior))

    # ── change ONE structured field ──
    rec_struct = dict(REC, state="NY")
    plan_s = plan_for_source_change(g0, build_cfpb_source_graph(rec_struct, policy), prior)
    rerun_s = set(plan_s.steps_to_rerun)
    check("structured field change reruns atomic_fact/conclusion/context_pack/receipt",
          {"atomic_fact", "conclusion", "context_pack", "receipt"} <= rerun_s, str(sorted(rerun_s)))
    check("structured field change does NOT rerun sentence/allegation/emotion",
          not ({"sentence", "narrative_allegation", "emotion_signal"} & rerun_s), str(sorted(rerun_s)))

    # ── no change → empty plan ──
    plan_none = plan_for_source_change(g0, build_cfpb_source_graph(REC, policy), prior)
    check("no source change → no semantic reprocess", not plan_none.semantic_reprocess_required)

    print(f"\n{'PASS — check_reprocess_source_change_scope: source changes produce minimal, correctly-scoped reprocessing plans (narrative vs structured isolated; downstream dependents included).' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: minimal source-change reprocessing scope.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
