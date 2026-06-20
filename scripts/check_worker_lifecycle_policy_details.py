#!/usr/bin/env python3
"""scripts.check_worker_lifecycle_policy_details — proof (C-FLEET-2): worker_lifecycle_policies.json has
the 10 required policies, each with the full ramp-up/ramp-down field set, a batch_policy_id that REFERENCES
a real batch policy (no duplicated thresholds), and valid priority/autoscale/k8s enums.

CLI: PYTHONPATH=. python3 scripts/check_worker_lifecycle_policy_details.py --self-test
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

_A = Path(__file__).resolve().parents[1] / "architecture"
_REQUIRED_POLICIES = {"cold_start_each_task", "burst_keepalive", "warm_pool", "hot_pool", "batch_min_5",
                      "batch_min_25", "batch_min_100", "scheduled_batch_window", "high_priority_on_demand",
                      "cooldown_drain"}
_REQUIRED_FIELDS = ("min_workers", "max_workers", "batch_policy_id", "keepalive_after_task_seconds",
                    "idle_shutdown_seconds", "drain_new_work_before_shutdown", "startup_budget_ms",
                    "max_idle_burn_ms", "allowed_priorities", "allowed_capabilities", "autoscale_signal",
                    "k8s_mapping")


def _self_test() -> int:
    fails: list[str] = []

    def chk(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    d = json.loads((_A / "worker_lifecycle_policies.json").read_text())
    pols = {p["lifecycle_policy_id"]: p for p in d["policies"]}
    batch_ids = {b["batch_policy_id"] for b in json.loads((_A / "worker_batch_policies.json").read_text())["policies"]}
    pri_enum = set(d["priority_enum"]); sig_enum = set(d["autoscale_signal_enum"]); k8s_enum = set(d["k8s_mapping_enum"])

    chk("all 10 required lifecycle policies present", _REQUIRED_POLICIES <= set(pols),
        str(_REQUIRED_POLICIES - set(pols)))
    for pid, p in pols.items():
        missing = [f for f in _REQUIRED_FIELDS if f not in p]
        chk(f"{pid} has all required fields", missing == [], str(missing))
        chk(f"{pid} batch_policy_id references a real batch policy", p.get("batch_policy_id") in batch_ids,
            str(p.get("batch_policy_id")))
        chk(f"{pid} allowed_priorities valid", set(p.get("allowed_priorities", [])) <= pri_enum,
            str(p.get("allowed_priorities")))
        chk(f"{pid} autoscale_signal valid", p.get("autoscale_signal") in sig_enum, str(p.get("autoscale_signal")))
        chk(f"{pid} k8s_mapping valid", p.get("k8s_mapping") in k8s_enum, str(p.get("k8s_mapping")))

    # semantic spot-checks: the policies encode the intended ramp behavior
    chk("cold_start does not keep alive", pols["cold_start_each_task"]["keepalive_after_task_seconds"] == 0)
    chk("hot_pool never scales to zero", pols["hot_pool"]["min_workers"] >= 1)
    chk("high_priority_on_demand is P0/P1 only", set(pols["high_priority_on_demand"]["allowed_priorities"]) == {"P0", "P1"})
    chk("cooldown_drain drains before shutdown", pols["cooldown_drain"]["drain_new_work_before_shutdown"] is True)

    print(f"\n{'PASS — check_worker_lifecycle_policy_details: 10 policies, full ramp field set, batch thresholds referenced (not duplicated), valid enums, intended ramp semantics.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv=None):
    p = argparse.ArgumentParser(); p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    return _self_test() if a.self_test else (p.print_help() or 0)


if __name__ == "__main__":
    raise SystemExit(_main())
