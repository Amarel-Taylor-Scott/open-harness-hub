#!/usr/bin/env python3
"""scripts.check_worker_bucket_registry — proof: the worker taxonomy registries are complete + honest +
enforce the safety split. Validates worker_bucket_registry + worker_resource_classes + worker_tool_policy +
worker_registry together: 18 buckets with all fields + unique queue prefixes; the capability-matrix
invariants hold (open-ended/browser/model can't publish truth; only the gated buckets can; utility forbids
the LLM gateway; model emits ModelTrace; gpu compute has a gpu resource class); every classified worker maps
to a real bucket; every bucket has a tool policy + real resource classes.

CLI: python3 scripts/check_worker_bucket_registry.py --self-test
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_A = _REPO / "architecture"
_REQUIRED_BUCKETS = {
    "control_plane", "open_ended_agent", "browser", "utility", "ingestion_sync", "parser_document",
    "decomposition_text_understanding", "verification_fact_check", "reconciliation_policy", "model_inference",
    "cpu_gpu_compute", "vector_graph", "optimization_evaluation", "distillation_determinism", "memory_context",
    "native_export", "observability_monitoring", "human_review_signoff"}
_FIELDS = ("bucket_id", "description", "determinism", "risk_level", "queue_prefix", "allowed_command_prefixes",
           "allowed_outputs", "forbidden_outputs", "resource_classes", "network_policy", "tenant_scope_required",
           "sandbox_required", "review_required", "can_write_artifacts", "can_publish_truth", "autoscale_metric",
           "retry_policy", "dlq_policy", "proof_scripts", "docs")
_TRUTH_BUCKETS = {"reconciliation_policy", "native_export", "distillation_determinism", "human_review_signoff"}
_NEVER_TRUTH = {"open_ended_agent", "browser", "model_inference", "utility", "parser_document",
                "decomposition_text_understanding", "vector_graph", "memory_context", "observability_monitoring"}


def _self_test() -> int:
    fails: list[str] = []

    def chk(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    reg = json.loads((_A / "worker_bucket_registry.json").read_text())
    buckets = {b["bucket_id"]: b for b in reg["buckets"]}
    rc = {c["class_id"] for c in json.loads((_A / "worker_resource_classes.json").read_text())["classes"]}
    rc_gpu = {c["class_id"]: c for c in json.loads((_A / "worker_resource_classes.json").read_text())["classes"]}
    pol = {p["bucket_id"]: p for p in json.loads((_A / "worker_tool_policy.json").read_text())["policies"]}
    workers = json.loads((_A / "worker_registry.json").read_text())["workers"]

    chk("all 18 required buckets present", _REQUIRED_BUCKETS <= set(buckets), str(sorted(_REQUIRED_BUCKETS - set(buckets))))
    missing = [f"{bid}.{f}" for bid, b in buckets.items() for f in _FIELDS if f not in b]
    chk("every bucket declares all required fields", missing == [], str(missing[:6]))
    prefixes = [b["queue_prefix"] for b in buckets.values()]
    chk("every queue_prefix is unique", len(prefixes) == len(set(prefixes)), str(prefixes))
    chk("every queue_prefix ends with '.'", all(p.endswith(".") for p in prefixes), str([p for p in prefixes if not p.endswith(".")]))

    # capability-matrix invariants
    bad_truth = [bid for bid in _NEVER_TRUTH if buckets.get(bid, {}).get("can_publish_truth")]
    chk("open-ended/browser/model/utility/etc CANNOT publish truth", bad_truth == [], str(bad_truth))
    truth_yes = {bid for bid, b in buckets.items() if b.get("can_publish_truth")}
    chk("only the gated buckets publish truth", truth_yes <= _TRUTH_BUCKETS, str(truth_yes - _TRUTH_BUCKETS))
    for bid in ("open_ended_agent", "browser", "model_inference"):
        fo = set(buckets[bid]["forbidden_outputs"])
        chk(f"{bid} forbids CanonicalFact.v1 + ContextResponse.v1", {"CanonicalFact.v1", "ContextResponse.v1"} <= fo)
    chk("model_inference must emit ModelTrace", "ModelTrace.v1" in buckets["model_inference"]["allowed_outputs"])
    chk("cpu_gpu_compute has a gpu resource class", any(c.startswith("gpu_") for c in buckets["cpu_gpu_compute"]["resource_classes"]))
    chk("utility forbids the LLM gateway", "LLMGatewayPort" in pol["utility"]["forbidden_ports"])
    chk("open_ended_agent requires sandbox + review", buckets["open_ended_agent"]["sandbox_required"] and buckets["open_ended_agent"]["review_required"])

    # resource classes + tool policy completeness
    bad_rc = [f"{bid}:{c}" for bid, b in buckets.items() for c in b["resource_classes"] if c not in rc]
    chk("every bucket resource_class exists in worker_resource_classes", bad_rc == [], str(bad_rc[:6]))
    chk("every gpu_* class has gpu_required=true", all(c["gpu_required"] for cid, c in rc_gpu.items() if cid.startswith("gpu_")))
    chk("every bucket has a tool policy", set(buckets) <= set(pol), str(set(buckets) - set(pol)))

    bad_wb = [w["worker_id"] for w in workers if w["bucket_id"] not in buckets]
    chk("every classified worker maps to a real bucket", bad_wb == [], str(bad_wb))
    chk("the existing flywheel_worker is classified", any(w["worker_id"] == "flywheel_worker" for w in workers))

    print(f"\n{'PASS — check_worker_bucket_registry: 18 buckets complete + unique prefixes; the safety split holds (only gated buckets publish truth); resource classes + tool policies + classified workers all consistent.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: worker taxonomy registries.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
