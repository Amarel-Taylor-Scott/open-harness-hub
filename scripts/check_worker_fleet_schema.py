#!/usr/bin/env python3
"""scripts.check_worker_fleet_schema — proof: fleet contracts + policy registries are well-formed and
internally consistent (capabilities reference real lifecycle/batch/sla policies)."""
from __future__ import annotations
import argparse, json
from pathlib import Path
_R = Path(__file__).resolve().parents[1]; _S = _R / "schemas" / "workers"; _A = _R / "architecture"
_SCHEMAS = ["CapabilityTask","CapabilityWorker","WorkerFleetSupervisorDecision","WorkerLifecyclePolicy","WorkerBatchPolicy","WorkerSlaPolicy"]
def _self_test() -> int:
    fails=[]
    def chk(n,ok,d=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': '+d) if d and not ok else ''}");
        (fails.append(n) if not ok else None)
    for n in _SCHEMAS:
        fp=_S/f"{n}.v1.schema.json"; chk(f"{n}.v1 schema parses",fp.exists() and json.loads(fp.read_text()).get("$id")==f"workers/{n}.v1")
    life={p["lifecycle_policy_id"] for p in json.loads((_A/"worker_lifecycle_policies.json").read_text())["policies"]}
    batch={p["batch_policy_id"] for p in json.loads((_A/"worker_batch_policies.json").read_text())["policies"]}
    sla={p["sla_policy_id"] for p in json.loads((_A/"worker_sla_policies.json").read_text())["policies"]}
    chk("lifecycle policies present",{"cold_start_each_task","burst_keepalive","warm_pool","hot_pool"}<=life)
    chk("batch policies present",{"on_demand_immediate","batch_min_5","batch_min_25","batch_min_100"}<=batch)
    chk("sla policies present",{"interactive_10s","interactive_30s","standard_2m","batch_15m"}<=sla)
    caps=json.loads((_A/"worker_capability_registry.json").read_text())["capabilities"]
    chk("capabilities present",len(caps)>=6)
    bad=[c["capability_id"] for c in caps if c["default_lifecycle_policy_id"] not in life or c["default_batch_policy_id"] not in batch or c["default_sla_policy_id"] not in sla]
    chk("every capability references real policies",bad==[],str(bad))
    bad2=[c["capability_id"] for c in caps if c["fallback_order"] and c["fallback_order"][0] not in c["providers"]]
    chk("fallback_order providers are real",bad2==[],str(bad2))
    print(f"\n{'PASS — check_worker_fleet_schema: contracts + lifecycle/batch/sla policies + capability registry consistent.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1
def _main(a=None):
    p=argparse.ArgumentParser(); p.add_argument("--self-test",action="store_true"); ns=p.parse_args(a)
    return _self_test() if ns.self_test else (p.print_help() or 0)
if __name__=="__main__": raise SystemExit(_main())
