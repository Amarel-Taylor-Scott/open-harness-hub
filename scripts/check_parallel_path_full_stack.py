#!/usr/bin/env python3
"""scripts.check_parallel_path_full_stack — STAGE 4 MASTER PROOF for the parallel-path experiment ENGINE
(src/baltor/experiments/). It RUNS and ASSERTS every layer of the engine end to end and prints the
CAPABILITY | STATUS | PROOF | NOTES table:

  contracts        — scripts.check_parallel_path_contracts        (the 6 schemas enforce the semantics)
  implementation   — scripts.check_parallel_path_implementation   (the engine BEHAVES on the same input)
  promotion_gate   — scripts.check_parallel_path_promotion_gate   (CFPB recon gate blocks unsafe, keeps base)
  examples         — scripts.check_parallel_path_examples         (real anchors: backend drain + recon)
  redteam          — scripts.check_parallel_path_redteam          (every attack fails safely)

Each layer's ``_self_test()`` is invoked IN-PROCESS and MUST exit 0. Beyond running them, this master also
re-asserts the load-bearing invariant in-process (a composition smoke) so the table is not just "the
sub-proofs are registered" but "the engine, driven here, upholds the contract": a candidate is NEVER served
as truth, and a candidate is promoted ONLY through a passing PathPromotionDecision (with the baseline always
the rollback_target). Finally it verifies every parallel-path proof — INCLUDING this one — is REGISTERED in
the flywheel PROOF_MODULES so the suite actually runs them.

Deterministic, stdlib-only, offline (no network, no RNG, injected `now`, hashlib ids).
CLI: PYTHONPATH=. python3 scripts/check_parallel_path_full_stack.py --self-test
"""
from __future__ import annotations

import argparse
import io
import json
import sys
from contextlib import redirect_stdout
from pathlib import Path
from typing import Any, Callable

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from scripts.baltor_flywheel import PROOF_MODULES  # noqa: E402
from src.baltor.experiments import (  # noqa: E402
    RECONCILIATION_CAPABILITY_SLOT,
    parallel_paths,
    path_comparator,
    path_promotion,
    path_rollback,
)

import scripts.check_parallel_path_contracts as contracts_proof  # noqa: E402
import scripts.check_parallel_path_examples as examples_proof  # noqa: E402
import scripts.check_parallel_path_implementation as implementation_proof  # noqa: E402
import scripts.check_parallel_path_promotion_gate as promotion_gate_proof  # noqa: E402
import scripts.check_parallel_path_redteam as redteam_proof  # noqa: E402

#: (capability label, proof module-stem, the module's _self_test callable, NOTES) for each engine layer.
_LAYERS: list[tuple[str, str, Callable[[], int], str]] = [
    ("contracts", "check_parallel_path_contracts", contracts_proof._self_test,
     "6 schemas enforce the non-negotiable semantics (rollback_target, input_snapshot_hash, candidate_served=false)"),
    ("implementation", "check_parallel_path_implementation", implementation_proof._self_test,
     "engine behaves: same input snapshot, candidate never served, deterministic"),
    ("promotion_gate", "check_parallel_path_promotion_gate", promotion_gate_proof._self_test,
     "CFPB recon gate blocks unsafe candidate (leak/drop), allows equivalent, baseline always rollback"),
    ("examples", "check_parallel_path_examples", examples_proof._self_test,
     "real anchors: execution-backend drain (A) + reconciliation/CFPB safety (C) drive the engine"),
    ("redteam", "check_parallel_path_redteam", redteam_proof._self_test,
     "7 attacks fail safely (no early serve / promote-without-decision / dropped handle / held-out leak / different-input / cheap-non-equivalent / baseline survives)"),
]

# ── in-process composition smoke fixtures (the SAME CFPB invariant the stack rides on) ──────────────────
_NOW = "2026-06-06T00:00:00Z"
_SLOT = RECONCILIATION_CAPABILITY_SLOT
_OUTPUT_CONTRACT = "consumption/ContextResponse"
_REG_HANDLE = "ctx://public/source/ecfr/12-CFR-1005.11#para.c.1.i"
_HELD_OUT_FAQ = "30 days"
_SERVED_ANSWER = {"answer": "10 business days", "claim_status": "verified_current"}
_INPUT_SNAPSHOT = {"question": "deadline?", "candidates": [{"handle": _REG_HANDLE, "text": "10 business days"}]}


def _path(path_id: str, mode: str) -> dict[str, Any]:
    return {
        "schema_version": "PathDefinition", "path_id": path_id, "capability_slot": _SLOT,
        "input_contract": "consumption/ConsumptionRequest", "output_contract": _OUTPUT_CONTRACT,
        "mode": mode, "promotion_criteria": "criteria/recon-equivalence", "rollback_target": "path-fs-baseline",
        "defined_at": _NOW,
    }


def _composition_smoke() -> tuple[bool, dict[str, bool]]:
    """Drive the engine in-process and assert the load-bearing invariant directly (not via sub-proofs):
    a candidate is NEVER served; a GOOD candidate promotes only through a passing decision (with the
    baseline as rollback_target); a LEAK candidate is blocked and the held-out '30 days' never serves.
    Returns (all_ok, per-check map)."""
    baseline = _path("path-fs-baseline", "baseline")
    good = _path("path-fs-good", "candidate")
    leak = _path("path-fs-leak", "candidate")
    results = {
        baseline["path_id"]: {"output": dict(_SERVED_ANSWER), "output_contract": _OUTPUT_CONTRACT,
                              "cost": 1.0, "latency_ms": 1.0, "error": None,
                              "contract_validation": "pass", "source_handles": [_REG_HANDLE]},
        good["path_id"]: {"output": dict(_SERVED_ANSWER), "output_contract": _OUTPUT_CONTRACT,
                          "cost": 0.1, "latency_ms": 1.0, "error": None,
                          "contract_validation": "pass", "source_handles": [_REG_HANDLE]},
        leak["path_id"]: {"output": {"answer": "30 days", "claim_status": "verified_current"},
                          "output_contract": _OUTPUT_CONTRACT, "cost": 0.1, "latency_ms": 1.0, "error": None,
                          "contract_validation": "pass", "source_handles": [_REG_HANDLE]},
    }

    def runner(path: dict[str, Any], snap: Any) -> dict[str, Any]:
        return dict(results[path["path_id"]])

    run = parallel_paths.run_parallel(_SLOT, _INPUT_SNAPSHOT, baseline, [good, leak], runner=runner, now=_NOW)
    report = path_comparator.compare(run, now=_NOW, held_out_strings=[_HELD_OUT_FAQ], unsafe_strings=[])
    good_dec = path_promotion.decide(report, {"max_cost_delta": 0.0}, candidate_path_id=good["path_id"], now=_NOW)
    leak_dec = path_promotion.decide(report, {"max_cost_delta": 0.0}, candidate_path_id=leak["path_id"], now=_NOW)
    served_text = json.dumps(parallel_paths.served_output(run)["output"], sort_keys=True)
    plan = path_rollback.build_rollback_plan(good_dec, now=_NOW)

    checks = {
        "candidate never served": run["served_path_id"] == baseline["path_id"] and run["candidate_served"] is False,
        "held-out '30 days' not in served output": _HELD_OUT_FAQ not in served_text,
        "GOOD candidate promotes only via a passing decision": (
            good_dec["decision"] == "promote" and good_dec["promoted_path_id"] == good["path_id"]
            and all(good_dec[g] is True for g in path_promotion.GATES)),
        "LEAK candidate is blocked (keep_baseline, never promoted)": (
            leak_dec["decision"] == "keep_baseline" and leak_dec["promoted_path_id"] is None),
        "baseline is always the rollback_target": (
            good_dec["rollback_target"] == baseline["path_id"]
            and leak_dec["rollback_target"] == baseline["path_id"]),
        "rollback is a pointer move (deletes nothing)": (
            plan["deletes_paths"] is False and plan["deletes_prior_runs"] is False),
    }
    return all(checks.values()), checks


def _run_layer(self_test: Callable[[], int]) -> int:
    """Invoke a sub-proof's _self_test() in-process, capturing its (verbose) stdout; return its exit code."""
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = self_test()
    return rc


def _self_test() -> int:
    fails: list[str] = []
    registered = {name for _, name in PROOF_MODULES}

    # ── run every engine layer's self-test (each MUST exit 0). ──────────────────────────────────────────
    statuses: dict[str, bool] = {}
    for label, stem, self_test, _notes in _LAYERS:
        rc = _run_layer(self_test)
        ok = rc == 0
        statuses[stem] = ok
        if not ok:
            fails.append(f"{label}:{stem} self-test exited {rc}")
        # the layer must also be REGISTERED so the suite runs it (not only this master).
        if stem not in registered:
            fails.append(f"{label}:{stem} not registered in PROOF_MODULES")

    # ── in-process composition smoke: the engine, driven here, upholds the contract directly. ───────────
    smoke_ok, smoke_checks = _composition_smoke()
    for cname, cok in smoke_checks.items():
        if not cok:
            fails.append(f"composition-smoke: {cname}")

    # ── this master proof itself must be registered. ────────────────────────────────────────────────────
    this_stem = "check_parallel_path_full_stack"
    if this_stem not in registered:
        fails.append(f"{this_stem} (this master) not registered in PROOF_MODULES")

    # ── print the CAPABILITY | STATUS | PROOF | NOTES table. ────────────────────────────────────────────
    print("CAPABILITY | STATUS | PROOF | NOTES")
    for label, stem, _self_test_fn, notes in _LAYERS:
        ran_ok = statuses.get(stem, False)
        reg_ok = stem in registered
        status = "GREEN" if (ran_ok and reg_ok) else "RED"
        reg_note = "" if reg_ok else " [NOT REGISTERED]"
        print(f"  {label} | {status} | {stem} | {notes}{reg_note}")
    print(f"  composition-smoke | {'GREEN' if smoke_ok else 'RED'} | (in-process) | "
          f"candidate never served; GOOD promotes only via passing decision; LEAK blocked; baseline always rollback")
    print(f"  master-registered | {'GREEN' if this_stem in registered else 'RED'} | {this_stem} | "
          f"this master proof is registered in the flywheel PROOF_MODULES")

    ok = not fails
    print(
        "\n" + ("PASS — check_parallel_path_full_stack: the parallel-path experiment ENGINE is green end to end "
                "— contracts + implementation + promotion_gate + examples + redteam all self-test to exit 0 and "
                "are registered in the flywheel; the in-process composition smoke proves the engine, driven here, "
                "never serves a candidate, promotes a GOOD candidate only through a passing PathPromotionDecision, "
                "blocks the held-out-'30 days' LEAK candidate, keeps the baseline as the rollback_target on every "
                "decision, and rolls back by a pointer move that deletes nothing."
                if ok else f"{len(fails)} FAILURES: {fails}"))
    return 0 if ok else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="STAGE 4 MASTER: run/assert the parallel-path engine's contracts + implementation + "
                    "promotion_gate + examples + redteam and print the CAPABILITY | STATUS | PROOF | NOTES table.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
