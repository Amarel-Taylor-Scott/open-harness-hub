#!/usr/bin/env python3
"""scripts.check_worker_taxonomy_full_stack — proof: the worker taxonomy holds end-to-end. Prints a
BUCKET | DETERMINISM | RISK | QUEUE | CAN_PUBLISH_TRUTH | RESOURCE | STATUS table for all 18 buckets and
asserts the safety split + that every classified worker routes to its declared bucket via the router.

CLI: python3 scripts/check_worker_taxonomy_full_stack.py --self-test   (run from repo root)
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.baltor.workers.worker_router import route, can_publish_truth, TRUTH_BUCKETS

_A = Path(__file__).resolve().parents[1] / "architecture"


def _self_test() -> int:
    fails: list[str] = []

    def chk(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    buckets = json.loads((_A / "worker_bucket_registry.json").read_text())["buckets"]
    workers = json.loads((_A / "worker_registry.json").read_text())["workers"]

    print("BUCKET | DETERMINISM | RISK | QUEUE | CAN_PUBLISH_TRUTH | RESOURCE | STATUS")
    for b in buckets:
        status = "GREEN" if (b["queue_prefix"] and b["resource_classes"]) else "INCOMPLETE"
        print(f"  {b['bucket_id']} | {b['determinism']} | {b['risk_level']} | {b['queue_prefix']} | "
              f"{b['can_publish_truth']} | {b['resource_classes'][0]} | {status}")

    chk("18 buckets", len(buckets) == 18, str(len(buckets)))
    # the safety split: exactly the gated buckets publish truth; the evidence/candidate buckets never do
    truth = {b["bucket_id"] for b in buckets if can_publish_truth(b)}
    chk("only gated buckets publish truth (== TRUTH_BUCKETS)", truth == TRUTH_BUCKETS, str(truth ^ TRUTH_BUCKETS))
    for ev in ("open_ended_agent", "browser", "model_inference", "utility"):
        bb = next(b for b in buckets if b["bucket_id"] == ev)
        chk(f"{ev} produces evidence/candidates, never truth", not can_publish_truth(bb))

    # every classified worker routes (via the real router) to its declared bucket
    bad = []
    for w in workers:
        cmds = w.get("command_types") or []
        for c in cmds:
            try:
                got = route(c)["bucket_id"]
            except Exception as e:  # noqa: BLE001
                got = f"ERR:{e}"
            if got != w["bucket_id"]:
                bad.append(f"{w['worker_id']}:{c}->{got}!={w['bucket_id']}")
    chk("every classified worker's command_types route to its bucket", bad == [], str(bad[:6]))
    chk("flywheel_worker + consumption_service + reconciliation classified",
        {"flywheel_worker", "consumption_service", "reconciliation"} <= {w["worker_id"] for w in workers})

    print(f"\n{'PASS — check_worker_taxonomy_full_stack: 18 buckets inventoried; the safety split holds (only verification/reconciliation/consumption/human gates publish truth; open-ended/browser/model produce evidence+candidates); every classified worker routes to its bucket.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: worker taxonomy full stack.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
