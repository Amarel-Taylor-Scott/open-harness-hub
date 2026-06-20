#!/usr/bin/env python3
"""scripts.check_cfpb_multi_grain_artifacts — proof: one CFPB record emits distinct, separately-governed,
lineaged artifact types (sentence / atomic_fact / narrative_allegation / emotion_signal / conclusion /
context_pack / receipt), with the governance and lineage contract enforced.

CLI: python3 scripts/check_cfpb_multi_grain_artifacts.py --self-test
"""
from __future__ import annotations

import argparse

from scripts.pipeline_runtime import artifact_types as AT
from scripts.pipeline_runtime.cfpb_artifacts import build_cfpb_artifacts
from scripts.security.tenant_catalog import TenantPolicy

REC = {"complaint_id": "CFPB-1", "product": "Credit card", "issue": "Billing dispute",
       "company": "Acme Bank", "state": "CA", "date_received": "2026-01-02",
       "consumer_complaint_narrative": "I was charged twice. The company refused to refund me. This is unfair and I am furious."}


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    out = build_cfpb_artifacts(REC, TenantPolicy("acme"))
    bt = out["by_type"]
    need = {"sentence", "atomic_fact", "narrative_allegation", "emotion_signal", "conclusion", "context_pack", "receipt"}
    check("one record emits all required grain types", need <= set(bt), str(sorted(set(bt))))

    check("atomic facts are promotion-eligible", all(a.promotion_eligible for a in bt["atomic_fact"]))
    check("narrative allegations are NOT promotion-eligible", all(not a.promotion_eligible for a in bt["narrative_allegation"]))
    check("narrative allegations are source-grounded (registry)", AT.get("narrative_allegation").source_grounded)

    em = bt["emotion_signal"][0]
    check("emotion_signal is model_interpretation (model_dependent type) + NOT promotion-eligible",
          AT.get("emotion_signal").model_dependent and not em.promotion_eligible)
    check("emotion_signal records processor_id@version + config_hash",
          em.processor_ref and em.config_hash, f"{em.processor_ref} / {em.config_hash}")

    co = bt["conclusion"][0]
    check("conclusion cites supporting artifacts", bool(co.citations), str(co.citations[:2]))
    cited_types = {a.artifact_type for a in out["artifacts"] if a.artifact_id in set(co.citations)}
    check("conclusion cites at least one SOURCE-GROUNDED artifact",
          any(AT.get(t).source_grounded for t in cited_types), str(cited_types))
    check("conclusion is NOT promotion-eligible by default + requires review",
          not co.promotion_eligible and AT.get("conclusion").requires_human_review)

    # lineage: every derived artifact records full lineage
    check("every derived artifact records full lineage (source ids/pipeline/processor/config/run/tenant)",
          all(a.lineage_complete() for a in out["artifacts"]))
    # every MODEL-DEPENDENT artifact records processor metadata
    md = [a for a in out["artifacts"] if AT.is_model_dependent(a.artifact_type)]
    check("every model-dependent artifact records processor_id@version + config_hash",
          bool(md) and all(a.processor_ref and a.config_hash for a in md))

    print(f"\n{'PASS — check_cfpb_multi_grain_artifacts: facts / allegations / emotion / conclusion are distinct governed types; conclusions cite source-grounded support; model-dependent artifacts carry processor metadata; full lineage recorded.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: CFPB multi-grain typed/governed/lineaged artifacts.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
