#!/usr/bin/env python3
"""scripts.check_pipeline_run_fingerprint — proof: a run fingerprint composes source × pipeline × processor
× security; identical inputs are idempotent (same run id) and changing ANY one dimension yields a distinct
run id.

CLI: python3 _repos/shared-backend-components/scripts/check_pipeline_run_fingerprint.py --self-test
"""
from __future__ import annotations

import argparse

from scripts.pipeline_runtime.source_graph import build_cfpb_source_graph
from scripts.pipeline_runtime.specs import PipelineSpec, PipelineStepSpec
from scripts.pipeline_runtime.versioning import ProcessorSpec, run_fingerprint
from scripts.security.tenant_catalog import TenantPolicy

REC = {"complaint_id": "CFPB-1", "product": "Credit card", "company": "Acme Bank", "state": "CA",
       "consumer_complaint_narrative": "I was charged twice. The company refused to refund me."}


def _spec(pkg_ver: str = "v1") -> PipelineSpec:
    return PipelineSpec("cfpb_multigrain", "v1", "", "active", "", "", "tenant_id", "",
                        steps=[PipelineStepSpec("decompose", "decompose.structured", "v1"),
                               PipelineStepSpec("package", "package.context_pack", pkg_ver)])


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    policy = TenantPolicy("acme", "shared_row")
    sg = build_cfpb_source_graph(REC, policy)
    procs = [ProcessorSpec("decompose.structured", "v1", code_hash="dc1"),
             ProcessorSpec("package.context_pack", "v1", code_hash="pk1")]

    def fp(*, graph=sg, spec=None, ps=None, sec=None, trig=""):
        return run_fingerprint(tenant_id="acme", isolation_mode="shared_row", source_graph=graph,
                               spec=spec or _spec(), procs=ps or procs,
                               security_policy_hash=sec or policy.security_policy_hash(), trigger_id=trig)

    base = fp()
    comp = base.components()
    check("fingerprint includes all four hash dimensions",
          all(comp.get(k) for k in ("source_snapshot_hash", "pipeline_config_hash", "processor_set_hash", "security_policy_hash")),
          str(comp))

    check("same source + pipeline + processors + security is IDEMPOTENT (same run_id)",
          fp().run_id == base.run_id)
    check("re-trigger with a different trigger_id is still idempotent (content-based id)",
          fp(trig="manual-retry").run_id == base.run_id)

    # change SOURCE
    sg2 = build_cfpb_source_graph(dict(REC, state="NY"), policy)
    check("changing the SOURCE snapshot → distinct run_id", fp(graph=sg2).run_id != base.run_id)
    # change PIPELINE config
    check("changing the PIPELINE config → distinct run_id", fp(spec=_spec("v2")).run_id != base.run_id)
    # change PROCESSOR set
    procs2 = [ProcessorSpec("decompose.structured", "v1", code_hash="dc1"),
              ProcessorSpec("package.context_pack", "v2", code_hash="pk2")]
    check("changing the PROCESSOR set → distinct run_id", fp(ps=procs2).run_id != base.run_id)
    # change SECURITY policy
    check("changing the SECURITY policy → distinct run_id",
          fp(sec=TenantPolicy("acme", "shared_row", kms_key_version="2").security_policy_hash()).run_id != base.run_id)

    print(f"\n{'PASS — check_pipeline_run_fingerprint: the run fingerprint composes source × pipeline × processor × security; identical inputs are idempotent and any single change yields a distinct run id.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: run fingerprint over source × pipeline × processor × security.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
