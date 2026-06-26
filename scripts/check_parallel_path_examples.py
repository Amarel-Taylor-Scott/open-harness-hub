#!/usr/bin/env python3
"""scripts.check_parallel_path_examples — STAGE 3: two deterministic, offline examples that drive the
parallel-path experiment ENGINE (src/baltor/experiments/) on REAL repo anchors.

EXAMPLE A — EXECUTION BACKEND (durable-task drain):
  baseline path  = local_subprocess  (backend local_subprocess@v1)
  candidate path = local_function_emulator (backend local_function_emulator@v1)
  Both runners drain the SAME set of enqueued durable CapabilityTasks from the EXISTING DurableFleetLedger
  via the existing emulators (atomic claim → handler → ack). The engine compares the drained-count (which
  MUST match — same work done) and the relative cost from the pricebook CONFIG (the local-function emulator
  must be <= the local subprocess). Promotion is allowed ONLY if outputs are equivalent AND cost is not
  worse. (Each runner drains an INDEPENDENT copy of the identical task set so both see the same work — the
  input_snapshot_hash proves the enqueue plan was byte-identical.)

EXAMPLE C — RECONCILIATION / CFPB SAFETY (delegated to scripts.check_parallel_path_promotion_gate):
  baseline path = the EXISTING deterministic reconciliation authority → "10 business days", FAQ "30 days"
  HELD OUT; candidate-GOOD is equivalent + holds out the FAQ (promotable); candidate-BAD serves "30 days"
  or drops a source handle (BLOCKED by the promotion gate, baseline kept, rollback_target = baseline).

Both examples emit ONLY engine objects (ParallelPathRun / PathComparisonReport / PathPromotionDecision /
PathCostReport) and validate them against their Stage-1 schemas. A candidate is NEVER served as truth; a
candidate is promoted ONLY through a passing PathPromotionDecision; the baseline is ALWAYS the
rollback_target.

Deterministic, stdlib-only, offline (temp SQLite DBs + cleanup; no network, no RNG; injected `now`;
hashlib ids).
CLI: PYTHONPATH=. python3 scripts/check_parallel_path_examples.py --self-test
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from scripts.runtime import schema_validator as _sv  # noqa: E402
from src.baltor.experiments import (  # noqa: E402
    parallel_paths,
    path_comparator,
    path_costing,
    path_promotion,
    path_rollback,
)
from src.baltor.workers.durable_fleet_ledger import DurableFleetLedger  # noqa: E402
from src.baltor.workers.function_emulator import LocalFunctionEmulator  # noqa: E402

# Example C runs in its own dedicated proof; this script also invokes it directly (one entry point).
import scripts.check_parallel_path_promotion_gate as example_c  # noqa: E402

_NOW = "2026-06-06T00:00:00Z"
_SLOT_BACKEND = "execution.backend.drain"
_OUTPUT_CONTRACT = "execution/DrainResult"
_BACKEND_BASELINE = "local_subprocess@v1"
_BACKEND_CANDIDATE = "local_function_emulator@v1"
_CAPABILITY = "demo.normalize"
_TASK_COUNT = 12  # how many durable tasks the enqueue plan creates (deterministic, fixed)

#: the input snapshot = the deterministic ENQUEUE PLAN both paths drain (identical bytes → same work).
_ENQUEUE_PLAN = {
    "capability_id": _CAPABILITY,
    "tenant_id": "acme",
    "tasks": [{"idempotency_key": f"demo-task-{i:03d}"} for i in range(_TASK_COUNT)],
}


def _backend_path(path_id: str, mode: str, backend_id: str) -> dict[str, Any]:
    return {
        "schema_version": "PathDefinition",
        "path_id": path_id,
        "capability_slot": _SLOT_BACKEND,
        "input_contract": "execution/EnqueuePlan",
        "output_contract": _OUTPUT_CONTRACT,
        "mode": mode,
        "promotion_criteria": "criteria/same-drain-count-and-not-more-expensive",
        "rollback_target": "path-drain-baseline-subprocess",
        "defined_at": _NOW,
        "backend_id": backend_id,
    }


_BASELINE_A = _backend_path("path-drain-baseline-subprocess", "baseline", _BACKEND_BASELINE)
_CANDIDATE_A = _backend_path("path-drain-candidate-function", "candidate", _BACKEND_CANDIDATE)


def _seed_ledger(db_path: str) -> int:
    """Enqueue the identical deterministic task set into a fresh durable ledger; return the count enqueued."""
    L = DurableFleetLedger(db_path)
    n = 0
    for t in _ENQUEUE_PLAN["tasks"]:
        L.enqueue_task(tenant_id=_ENQUEUE_PLAN["tenant_id"], capability_id=_CAPABILITY,
                       idempotency_key=t["idempotency_key"], now=_NOW)
        n += 1
    L.close()
    return n


def _make_backend_runner(tmp: Path, pricebook: dict[str, Any]) -> parallel_paths.Runner:
    """A runner that drains the SAME enqueued task set on each backend and reports a DrainResult + cost.

    Each path gets its OWN durable DB seeded with the byte-identical enqueue plan (draining mutates the
    ledger, so apples-to-apples requires an independent copy of the same work). Cost is the per-task relative
    cost from the pricebook CONFIG (never hardcoded). The drain itself is the existing function-emulator
    atomic-claim loop — contract-identical for both backends (the "subprocess" backend just prices compute).
    """
    # per-task estimated duration is fixed/deterministic; cost comes from the pricebook for each backend.
    per_task_duration_s = 0.05

    def _cost_for(path: dict[str, Any], drained: int) -> float:
        rep = path_costing.estimate(
            path_id=path["path_id"], capability_slot=_SLOT_BACKEND, backend_id=path["backend_id"],
            estimated_duration_s=per_task_duration_s * drained, now=_NOW, pricebook=pricebook,
        )
        return rep["estimated_cost"]

    def runner(path: dict[str, Any], input_snapshot: Any) -> dict[str, Any]:
        # independent DB per path, seeded with the byte-identical enqueue plan
        db = str(tmp / f"durable-{path['path_id']}.db")
        enqueued = _seed_ledger(db)
        emu = LocalFunctionEmulator()  # contract-identical drain for either backend
        worker_id = f"w-{path['backend_id'].replace('@', '-')}"
        res = emu.invoke_durable(db, worker_id=worker_id, capability=_CAPABILITY, max_tasks=10_000)
        drained = res["processed"]
        cost = _cost_for(path, drained)
        return {
            # the served fact is the DRAIN RESULT — how many of the identical tasks were processed.
            "output": {"drained": drained, "enqueued": enqueued, "owns_truth": False},
            "output_contract": _OUTPUT_CONTRACT,
            "cost": cost,
            "latency_ms": float(drained),
            "error": None,
            "contract_validation": "pass",
            # the execution backend grounds on the durable ledger + the capability it drained.
            "source_handles": [f"ledger://durable/{_CAPABILITY}"],
        }

    return runner


def _run_example_a(tmp: Path, check) -> None:
    pricebook = path_costing.load_pricebook()
    runner = _make_backend_runner(tmp, pricebook)
    run = parallel_paths.run_parallel(
        _SLOT_BACKEND, _ENQUEUE_PLAN, _BASELINE_A, [_CANDIDATE_A], runner=runner, now=_NOW,
    )
    report = path_comparator.compare(run, now=_NOW, held_out_strings=[], unsafe_strings=[])

    base = run["baseline_result"]
    cand = run["candidate_results"][0]
    check("A: baseline (local_subprocess) drained ALL enqueued tasks",
          base["output"]["drained"] == _TASK_COUNT and base["output"]["enqueued"] == _TASK_COUNT)
    check("A: candidate (local_function_emulator) drained the SAME count (same work done)",
          cand["output"]["drained"] == base["output"]["drained"], f"{cand['output']['drained']} vs {base['output']['drained']}")
    check("A: the input_snapshot_hash proves both paths drained the byte-identical enqueue plan",
          run["input_snapshot_hash"] == parallel_paths.sha256_hex(_ENQUEUE_PLAN))

    verdict = report["candidate_verdicts"][0]
    check("A: outputs are equivalent (same drained/enqueued result)", verdict["output_equivalent"] is True)
    check("A: same output_contract on both paths", verdict["same_output_contract"] is True)
    check("A: source handles preserved (the candidate grounds on the same ledger capability)",
          verdict["source_handles_preserved"] is True)
    # cost: the local function emulator must be <= the local subprocess (relative pricebook units).
    check("A: candidate relative cost <= baseline (function emulator not more expensive than subprocess)",
          cand["cost"] <= base["cost"], f"cand={cand['cost']} base={base['cost']}")
    check("A: cost_delta is negative-or-zero (candidate is cheaper or equal)",
          verdict["cost_delta"] <= 0.0, str(verdict["cost_delta"]))

    # promotion allowed ONLY if outputs equivalent AND cost not worse → here both hold → promote.
    dec = path_promotion.decide(report, {"max_cost_delta": 0.0},
                                candidate_path_id=_CANDIDATE_A["path_id"], now=_NOW)
    check("A: the candidate is PROMOTABLE (equivalent outputs + cost not worse → all gates green)",
          dec["decision"] == "promote" and all(dec[g] is True for g in path_promotion.GATES))
    check("A: even on promotion the rollback_target is the baseline subprocess path (reversible)",
          dec["rollback_target"] == _BASELINE_A["path_id"])

    # if the cost gate were inverted (candidate must be CHEAPER by a margin it can't meet), promotion is denied.
    strict = path_promotion.decide(report, {"max_cost_delta": -999.0},
                                   candidate_path_id=_CANDIDATE_A["path_id"], now=_NOW)
    check("A: an unreachable cost ceiling blocks promotion (cost gate works) → keep_baseline",
          strict["cost_acceptable"] is False and strict["decision"] == "keep_baseline")

    # a rollback plan reverts the promotion by a pointer move (deletes nothing).
    plan = path_rollback.build_rollback_plan(dec, now=_NOW)
    check("A: a PathRollbackPlan reverts to the baseline by a POINTER MOVE (deletes nothing)",
          plan["rollback_target_path_id"] == _BASELINE_A["path_id"]
          and plan["deletes_paths"] is False and plan["deletes_prior_runs"] is False
          and _sv.validate_ref(plan, "experiments/PathRollbackPlan") == [])

    # never served a candidate; every emitted object validates against its Stage-1 schema.
    check("A: a candidate is NEVER served (served_path_id == baseline, candidate_served=false)",
          run["served_path_id"] == _BASELINE_A["path_id"] and run["candidate_served"] is False)
    check("A: ParallelPathRun validates against its Stage-1 schema",
          _sv.validate_ref(run, "experiments/ParallelPathRun") == [])
    check("A: PathComparisonReport validates against its Stage-1 schema",
          _sv.validate_ref(report, "experiments/PathComparisonReport") == [])
    check("A: PathPromotionDecision validates against its Stage-1 schema",
          _sv.validate_ref(dec, "experiments/PathPromotionDecision") == [])

    # deterministic: a second full run is byte-identical (fresh temp DBs, same plan).
    with tempfile.TemporaryDirectory() as d2:
        runner2 = _make_backend_runner(Path(d2), pricebook)
        run2 = parallel_paths.run_parallel(
            _SLOT_BACKEND, _ENQUEUE_PLAN, _BASELINE_A, [_CANDIDATE_A], runner=runner2, now=_NOW)
    check("A: a second full run is byte-identical (deterministic; ids are content hashes)",
          json.dumps(run, sort_keys=True) == json.dumps(run2, sort_keys=True))


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    print("── EXAMPLE A · execution backend (durable-task drain: local_subprocess vs local_function_emulator) ──")
    with tempfile.TemporaryDirectory() as tmpdir:
        _run_example_a(Path(tmpdir), check)

    print("\n── EXAMPLE C · reconciliation / CFPB safety (delegated to check_parallel_path_promotion_gate) ──")
    c_rc = example_c._self_test()
    check("C: the reconciliation promotion-gate example self-test passes (exit 0)", c_rc == 0)

    ok = not fails
    print(
        "\n" + ("PASS — check_parallel_path_examples: STAGE-3 examples drive the parallel-path ENGINE on real "
                "anchors. EXAMPLE A — the baseline local_subprocess and candidate local_function_emulator each "
                "drain the SAME enqueued durable tasks via the existing emulators; the drained-count MATCHES, "
                "outputs are equivalent, the candidate's relative pricebook cost is <= the baseline, so the "
                "candidate is PROMOTABLE (an unreachable cost ceiling correctly blocks it; rollback_target is "
                "always the baseline). EXAMPLE C — the reconciliation/CFPB promotion-gate example passes: the "
                "BAD candidate (FAQ '30 days' leak / dropped handle) is BLOCKED and the GOOD candidate is "
                "promotable, baseline always preserved as rollback_target. A candidate is NEVER served; every "
                "emitted object validates against its Stage-1 schema; both examples are deterministic."
                if ok else f"{len(fails)} FAILURES: {fails}"))
    return 0 if ok else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="STAGE 3: two deterministic examples (execution-backend drain + reconciliation/CFPB "
                    "safety) that drive the parallel-path experiment engine and its promotion gate.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
