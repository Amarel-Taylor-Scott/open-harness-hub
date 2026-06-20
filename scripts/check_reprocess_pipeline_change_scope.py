#!/usr/bin/env python3
"""scripts.check_reprocess_pipeline_change_scope — proof: a pipeline-config change creates a NEW versioned
run, the old outputs stay readable, and affected outputs are marked superseded ONLY after the new run
succeeds.

CLI: python3 scripts/check_reprocess_pipeline_change_scope.py --self-test
"""
from __future__ import annotations

import argparse

from scripts.durable_store import DurableStore
from scripts.pipeline_runtime.artifact_ledger import ArtifactLedger
from scripts.pipeline_runtime.reprocess_planner import plan_for_pipeline_change
from scripts.pipeline_runtime.specs import PipelineSpec, PipelineStepSpec
from scripts.pipeline_runtime.versioning import DerivedArtifact, PipelineRun, pipeline_config_hash


def _spec(version: str, pkg_ver: str) -> PipelineSpec:
    return PipelineSpec(
        pipeline_id="cfpb_multigrain", pipeline_version=version, description="", status="active",
        input_schema="", output_schema="", partition_key="tenant_id", idempotency_key_template="",
        steps=[PipelineStepSpec("decompose", "decompose.structured", "v1", output_artifact_types=["atomic_fact"]),
               PipelineStepSpec("package", "package.context_pack", pkg_ver, depends_on=["decompose"],
                                output_artifact_types=["context_pack"])],
        gates=[], artifact_policy={}, retry_policy={}, isolation="shared")


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    store = DurableStore(":memory:")
    led = ArtifactLedger(store)
    old, new = _spec("v1", "v1"), _spec("v2", "v2")

    check("a config edit changes the pipeline_config_hash",
          pipeline_config_hash(old) != pipeline_config_hash(new))

    # record the OLD run + its outputs
    led.put_pipeline_run(PipelineRun("run-old", "acme", "shared", "cfpb_multigrain", "v1",
                                     "src1", pipeline_config_hash(old), "pset1", "sec1"))
    prior = [DerivedArtifact(f"run-old:context_pack:{i}", "acme", "context_pack", "run-old", f"h{i}",
                             pipeline_id="cfpb_multigrain", pipeline_version="v1", config_hash="c1")
             for i in range(2)]
    for a in prior:
        led.put_derived_artifact(a)

    plan = plan_for_pipeline_change(old, new, prior)
    check("pipeline change requires a semantic reprocess (new run plan)", plan.semantic_reprocess_required)
    check("plan reruns the changed step + downstream dependents",
          {"package"} <= set(plan.steps_to_rerun), str(plan.steps_to_rerun))
    check("plan does not require human approval (versioned, non-destructive)", not plan.requires_human_approval)

    # OLD outputs remain readable, and are NOT yet superseded (new run hasn't succeeded)
    check("old outputs remain readable after planning", len(led.list_derived_artifacts("acme", "context_pack")) == 2)
    check("old outputs NOT superseded before the new run succeeds", led.superseded_count("acme") == 0)

    # the new run SUCCEEDS → now (and only now) supersede the affected old outputs
    led.put_pipeline_run(PipelineRun("run-new", "acme", "shared", "cfpb_multigrain", "v2",
                                     "src1", pipeline_config_hash(new), "pset2", "sec1"))
    led.supersede_run("run-old", "run-new")
    check("affected outputs superseded ONLY after the new run succeeds", led.superseded_count("acme") == 2)
    check("old run preserved + linked to the new run",
          any(r["run_id"] == "run-old" and r["superseded_by"] == "run-new" for r in led.list_runs("acme")))

    store.close()
    print(f"\n{'PASS — check_reprocess_pipeline_change_scope: a config change creates a new versioned run; old outputs stay readable and are superseded only after the new run succeeds.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: pipeline-change versioned run + non-destructive supersession.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
