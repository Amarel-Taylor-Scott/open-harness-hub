#!/usr/bin/env python3
"""scripts.check_parallel_path_implementation — proof (PARALLEL-PATH ENGINE MODE): the engine BEHAVES.

Stage-1 (scripts/check_parallel_path_contracts.py) proved the 6 contract SCHEMAS enforce the
non-negotiable parallel-path semantics. This proof exercises the Stage-2 RUNTIME under
``src/baltor/experiments/`` and proves it actually does the right thing — not that files exist:

  (a) SAME INPUT — run_parallel feeds the baseline AND each candidate the IDENTICAL input_snapshot and
      records ONE input_snapshot_hash (= sha256 of the canonical bytes) for the run.
  (b) MATCHING CONTRACT — the baseline result and an equivalent candidate result carry matching
      output_contract; the comparator's same_output_contract gate reflects it, and a candidate that
      declares a DIFFERENT output_contract is caught (gate=false, not promoted).
  (c) SOURCE HANDLES SURVIVE — a candidate that grounds on AT LEAST the baseline's handles passes
      source_handles_preserved (coverage >= baseline); a candidate that DROPS a handle fails it.
  (d) CANDIDATE NEVER SERVED — run_parallel pins served_path_id == baseline.path_id and
      candidate_served == False, even when a candidate is faster/cheaper/contract-valid; served_output()
      structurally returns the baseline; the held-out CFPB FAQ "30 days" never becomes a served fact;
      and a candidate is promoted ONLY through a passing PathPromotionDecision (held-out leak / dropped
      handle / different contract each block promotion, with rollback_target always = baseline).
  (e) DETERMINISTIC — two independent runs with the SAME injected inputs produce byte-identical
      ParallelPathRun / PathComparisonReport / PathPromotionDecision objects (no wall-clock / RNG).
  (+) every emitted object validates against its Stage-1 versioned schema, and cost comes from the
      pricebook CONFIG (a 'low' placeholder confidence is carried, never silently upgraded).

Deterministic, stdlib-only, offline (no network, no RNG, no wall-clock — `now` + the runner are injected).
CLI: PYTHONPATH=. python3 scripts/check_parallel_path_implementation.py --self-test
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from scripts.runtime import schema_validator as _sv  # noqa: E402
from src.baltor.experiments import (  # noqa: E402
    RECONCILIATION_CAPABILITY_SLOT,
    parallel_paths,
    path_comparator,
    path_costing,
    path_promotion,
)

# ── injected, deterministic fixtures (no wall-clock, no RNG) ────────────────────────────────────────────
_NOW = "2026-06-06T00:00:00Z"
_SLOT = RECONCILIATION_CAPABILITY_SLOT  # "reconciliation.answer"
_OUTPUT_CONTRACT = "consumption/ContextResponse"
_REG_HANDLE = "ctx://public/cfpb/reg-e/1005.11#10-business-days"
#: the CFPB FAQ value the baseline deliberately HELD OUT — must never leak into a candidate output.
_HELD_OUT_FAQ = "30 days"
#: the reconciled, served answer (Reg-E wins) — the SAME invariant as demo_offline_full_baltor.
_SERVED_ANSWER = {"answer": "10 business days", "claim_status": "verified_current"}

#: the input every path sees — identical bytes for baseline + candidates (apples to apples).
_INPUT_SNAPSHOT = {
    "question": "How long does the bank have to investigate a disputed transaction?",
    "candidates": [
        {"handle": _REG_HANDLE, "text": "10 business days", "source_type": "regulation"},
        {"handle": "ctx://public/source/cfpb-faq/error-resolution#q12", "text": "30 days", "source_type": "agency_faq"},
    ],
}


def _path(path_id: str, mode: str, *, output_contract: str = _OUTPUT_CONTRACT) -> dict[str, Any]:
    """A minimal PathDefinition-shaped dict (the engine names contracts; the runner executes)."""
    return {
        "schema_version": "PathDefinition",
        "path_id": path_id,
        "capability_slot": _SLOT,
        "input_contract": "consumption/ConsumptionRequest",
        "output_contract": output_contract,
        "mode": mode,
        "promotion_criteria": "criteria/recon-equivalence-cost-ceiling",
        "rollback_target": "path-recon-baseline-llm-0099",
        "defined_at": _NOW,
    }


_BASELINE = _path("path-recon-baseline-llm-0099", "baseline")
_CAND_GOOD = _path("path-recon-deterministic-1a2b3c4d", "candidate")  # equivalent + cheaper + handles kept
_CAND_LEAK = _path("path-recon-leaky-9z8y7x", "candidate")            # leaks the held-out FAQ "30 days"
_CAND_DROP = _path("path-recon-drophandle-77", "candidate")           # drops the baseline's source handle
_CAND_DIFF = _path("path-recon-othercontract-88", "candidate", output_contract="consumption/Other")


def _make_runner() -> parallel_paths.Runner:
    """A deterministic caller-supplied runner: maps each path_id to a fixed RunnerResult on the snapshot.

    The runner records which input_snapshot it was handed per path so the proof can assert every path saw
    the IDENTICAL object. Costs come from the pricebook via path_costing (config-driven, not hardcoded).
    """
    pb = path_costing.load_pricebook()
    # baseline runs on an LLM-grade backend (slow, low-confidence price); candidate on the local emulator.
    baseline_cost = path_costing.estimate(
        path_id=_BASELINE["path_id"], capability_slot=_SLOT, backend_id="cloud_run_job@candidate",
        estimated_duration_s=1.8, now=_NOW, pricebook=pb,
    )["estimated_cost"]
    cand_cost = path_costing.estimate(
        path_id=_CAND_GOOD["path_id"], capability_slot=_SLOT, backend_id="local_function_emulator@v1",
        estimated_duration_s=0.012, now=_NOW, pricebook=pb,
    )["estimated_cost"]

    results: dict[str, dict[str, Any]] = {
        _BASELINE["path_id"]: {
            "output": dict(_SERVED_ANSWER), "output_contract": _OUTPUT_CONTRACT,
            "cost": baseline_cost, "latency_ms": 1800.0, "error": None,
            "contract_validation": "pass", "source_handles": [_REG_HANDLE],
        },
        _CAND_GOOD["path_id"]: {  # equivalent facts, same contract, keeps the handle, cheaper, no leak
            "output": dict(_SERVED_ANSWER), "output_contract": _OUTPUT_CONTRACT,
            "cost": cand_cost, "latency_ms": 12.0, "error": None,
            "contract_validation": "pass", "source_handles": [_REG_HANDLE],
        },
        _CAND_LEAK["path_id"]: {  # leaks the held-out FAQ "30 days" into the answer
            "output": {"answer": "10 business days or 30 days", "claim_status": "verified_current"},
            "output_contract": _OUTPUT_CONTRACT, "cost": cand_cost, "latency_ms": 12.0, "error": None,
            "contract_validation": "pass", "source_handles": [_REG_HANDLE],
        },
        _CAND_DROP["path_id"]: {  # drops the baseline's grounding handle (coverage < baseline)
            "output": dict(_SERVED_ANSWER), "output_contract": _OUTPUT_CONTRACT,
            "cost": cand_cost, "latency_ms": 12.0, "error": None,
            "contract_validation": "pass", "source_handles": [],
        },
        _CAND_DIFF["path_id"]: {  # declares a DIFFERENT output_contract
            "output": dict(_SERVED_ANSWER), "output_contract": "consumption/Other",
            "cost": cand_cost, "latency_ms": 12.0, "error": None,
            "contract_validation": "pass", "source_handles": [_REG_HANDLE],
        },
    }
    seen_inputs: list[tuple[str, int]] = []

    def runner(path: dict[str, Any], input_snapshot: Any) -> dict[str, Any]:
        seen_inputs.append((path["path_id"], id(input_snapshot)))
        return dict(results[path["path_id"]])

    runner.seen_inputs = seen_inputs  # type: ignore[attr-defined]
    return runner


def _run_engine(candidates: list[dict[str, Any]]):
    """Run the full engine motion once and return (run, report, decisions, runner)."""
    runner = _make_runner()
    run = parallel_paths.run_parallel(
        _SLOT, _INPUT_SNAPSHOT, _BASELINE, candidates, runner=runner, now=_NOW,
    )
    report = path_comparator.compare(
        run, now=_NOW, held_out_strings=[_HELD_OUT_FAQ], unsafe_strings=[],
    )
    criteria = {"max_cost_delta": 0.0}  # candidate must be same-price or cheaper
    decisions = {
        c["path_id"]: path_promotion.decide(
            report, criteria, candidate_path_id=c["path_id"], now=_NOW,
        )
        for c in candidates
    }
    return run, report, decisions, runner


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    all_candidates = [_CAND_GOOD, _CAND_LEAK, _CAND_DROP, _CAND_DIFF]
    run, report, decisions, runner = _run_engine(all_candidates)

    # ── (a) SAME INPUT: one input_snapshot_hash; every path saw the identical object. ───────────────────
    expected_hash = parallel_paths.sha256_hex(_INPUT_SNAPSHOT)
    check("(a) run records input_snapshot_hash = sha256 of the canonical input bytes",
          run["input_snapshot_hash"] == expected_hash, run["input_snapshot_hash"])
    seen_ids = {iid for (_pid, iid) in runner.seen_inputs}  # type: ignore[attr-defined]
    check("(a) baseline + every candidate were handed the IDENTICAL input_snapshot object (apples to apples)",
          len(seen_ids) == 1 and len(runner.seen_inputs) == 1 + len(all_candidates),  # type: ignore[attr-defined]
          str(runner.seen_inputs))  # type: ignore[attr-defined]
    check("(a) the run covers the baseline + all candidates",
          run["baseline_result"]["path_id"] == _BASELINE["path_id"]
          and {c["path_id"] for c in run["candidate_results"]} == {c["path_id"] for c in all_candidates})

    # ── (b) MATCHING CONTRACT: baseline + good candidate match; a different-contract candidate is caught. ─
    good_v = next(v for v in report["candidate_verdicts"] if v["candidate_path_id"] == _CAND_GOOD["path_id"])
    diff_v = next(v for v in report["candidate_verdicts"] if v["candidate_path_id"] == _CAND_DIFF["path_id"])
    base_oc = run["baseline_result"]["output_contract"]
    good_oc = next(c["output_contract"] for c in run["candidate_results"] if c["path_id"] == _CAND_GOOD["path_id"])
    check("(b) baseline + equivalent candidate carry matching output_contract", base_oc == good_oc, f"{base_oc} vs {good_oc}")
    check("(b) same_output_contract gate is TRUE for the equivalent candidate", good_v["same_output_contract"] is True)
    check("(b) same_output_contract gate is FALSE for the different-contract candidate",
          diff_v["same_output_contract"] is False)
    check("(b) the different-contract candidate is NOT promoted (kept baseline)",
          decisions[_CAND_DIFF["path_id"]]["decision"] == "keep_baseline")

    # ── (c) SOURCE HANDLES SURVIVE: equivalent candidate keeps them; the dropping candidate fails. ──────
    base_cov = run["baseline_result"]["source_handle_coverage"]
    good_cov = next(c["source_handle_coverage"] for c in run["candidate_results"] if c["path_id"] == _CAND_GOOD["path_id"])
    drop_v = next(v for v in report["candidate_verdicts"] if v["candidate_path_id"] == _CAND_DROP["path_id"])
    check("(c) baseline source_handle_coverage is 1.0 (it defines the reference set)", base_cov == 1.0, str(base_cov))
    check("(c) equivalent candidate coverage >= baseline coverage (handles survive)", good_cov >= base_cov, f"{good_cov} vs {base_cov}")
    check("(c) source_handles_preserved gate is TRUE for the handle-keeping candidate", good_v["source_handles_preserved"] is True)
    check("(c) source_handles_preserved gate is FALSE for the handle-DROPPING candidate", drop_v["source_handles_preserved"] is False)
    check("(c) the handle-dropping candidate is NOT promoted", decisions[_CAND_DROP["path_id"]]["decision"] == "keep_baseline")

    # ── (d) CANDIDATE NEVER SERVED AS TRUTH. ────────────────────────────────────────────────────────────
    check("(d) served_path_id is ALWAYS the baseline's path_id", run["served_path_id"] == _BASELINE["path_id"])
    check("(d) candidate_served is pinned False (a candidate output is never served)", run["candidate_served"] is False)
    served = parallel_paths.served_output(run)
    check("(d) served_output() structurally returns the BASELINE result (not any candidate)",
          served["path_id"] == _BASELINE["path_id"] and served["mode"] in parallel_paths.SERVABLE_MODES)
    served_text = json.dumps(served["output"], sort_keys=True)
    check("(d) the served output is the reconciled Reg-E answer (10 business days)", "10 business days" in served_text)
    check("(d) the held-out CFPB FAQ '30 days' is NOT in the served output", _HELD_OUT_FAQ not in served_text)
    # the held-out leak candidate: gate false -> keep_baseline (a leak can NEVER be promoted/served).
    leak_v = next(v for v in report["candidate_verdicts"] if v["candidate_path_id"] == _CAND_LEAK["path_id"])
    check("(d) the leaking candidate's held_out_not_leaked gate is FALSE", leak_v["held_out_not_leaked"] is False)
    check("(d) the leaking candidate is NOT promoted (a held-out leak blocks promotion)",
          decisions[_CAND_LEAK["path_id"]]["decision"] == "keep_baseline")
    # every keep_baseline decision still names a rollback_target = baseline (always reversible).
    for cpid, dec in decisions.items():
        check(f"(d) decision for {cpid} sets rollback_target = baseline path_id (reversible)",
              dec["rollback_target"] == _BASELINE["path_id"])
        if dec["decision"] == "keep_baseline":
            check(f"(d) keep_baseline decision for {cpid} has promoted_path_id == null", dec["promoted_path_id"] is None)
    # the ONLY candidate that may be promoted is the all-gates-green one — and only via a 'promote' decision.
    good_dec = decisions[_CAND_GOOD["path_id"]]
    check("(d) ONLY the all-gates-green candidate is promoted (and only through a passing decision)",
          good_dec["decision"] == "promote" and good_dec["promoted_path_id"] == _CAND_GOOD["path_id"]
          and all(good_dec[g] is True for g in path_promotion.GATES))
    promoted = [cpid for cpid, d in decisions.items() if d["decision"] == "promote"]
    check("(d) exactly ONE candidate is promoted (the equivalent one)", promoted == [_CAND_GOOD["path_id"]], str(promoted))

    # a cost ceiling that REJECTS the candidate flips even the good candidate to keep_baseline (gate works).
    strict = path_promotion.decide(report, {"max_cost_delta": -10.0}, candidate_path_id=_CAND_GOOD["path_id"], now=_NOW)
    check("(d) a too-strict cost ceiling makes cost_acceptable=false and keeps the baseline",
          strict["cost_acceptable"] is False and strict["decision"] == "keep_baseline")

    # ── (e) DETERMINISTIC: a second independent run is byte-identical. ──────────────────────────────────
    run2, report2, decisions2, _ = _run_engine(all_candidates)
    check("(e) ParallelPathRun is byte-identical across two runs (deterministic)",
          json.dumps(run, sort_keys=True) == json.dumps(run2, sort_keys=True))
    check("(e) PathComparisonReport is byte-identical across two runs", json.dumps(report, sort_keys=True) == json.dumps(report2, sort_keys=True))
    check("(e) PathPromotionDecisions are byte-identical across two runs",
          json.dumps(decisions, sort_keys=True) == json.dumps(decisions2, sort_keys=True))
    check("(e) input_snapshot_hash is stable across runs", run["input_snapshot_hash"] == run2["input_snapshot_hash"])
    check("(e) run_id / report_id / decision ids are content hashes (stable across runs)",
          run["run_id"] == run2["run_id"] and report["report_id"] == report2["report_id"]
          and good_dec["decision_id"] == decisions2[_CAND_GOOD["path_id"]]["decision_id"])

    # ── (+) every emitted object validates against its Stage-1 schema; cost is config-driven. ───────────
    check("(+) ParallelPathRun validates against experiments/ParallelPathRun",
          _sv.validate_ref(run, "experiments/ParallelPathRun") == [])
    check("(+) PathComparisonReport validates against experiments/PathComparisonReport",
          _sv.validate_ref(report, "experiments/PathComparisonReport") == [])
    for cpid, dec in decisions.items():
        check(f"(+) PathPromotionDecision for {cpid} validates against experiments/PathPromotionDecision",
              _sv.validate_ref(dec, "experiments/PathPromotionDecision") == [])
    # cost report comes from the pricebook CONFIG and carries the per-entry confidence (placeholder = 'low').
    pb = path_costing.load_pricebook()
    cheap = path_costing.estimate(path_id=_CAND_GOOD["path_id"], capability_slot=_SLOT,
                                  backend_id="local_function_emulator@v1", estimated_duration_s=0.012,
                                  now=_NOW, baseline_cost=0.082, pricebook=pb)
    check("(+) PathCostReport validates against experiments/PathCostReport",
          _sv.validate_ref(cheap, "experiments/PathCostReport") == [])
    check("(+) PathCostReport pricebook_version mirrors the pricebook config (reproducible)",
          cheap["pricebook_version"] == pb.get("version"))
    check("(+) PathCostReport carries the pricebook entry's confidence ('high' for the offline emulator)",
          cheap["confidence"] == pb["backends"]["local_function_emulator@v1"]["confidence"])
    placeholder = path_costing.estimate(path_id=_BASELINE["path_id"], capability_slot=_SLOT,
                                        backend_id="cloud_run_job@candidate", estimated_duration_s=1.8, now=_NOW, pricebook=pb)
    check("(+) a placeholder backend's 'low' confidence is carried, never silently upgraded",
          placeholder["confidence"] == "low")
    check("(+) cost_delta_vs_baseline = candidate cost - baseline cost (the promotion cost gate's number)",
          abs(cheap["cost_delta_vs_baseline"] - (cheap["estimated_cost"] - 0.082)) < 1e-9)

    ok = not fails
    print(
        "\n" + (
            "PASS — check_parallel_path_implementation: the parallel-path ENGINE behaves — baseline + every "
            "candidate run on the IDENTICAL input_snapshot (one sha256 input_snapshot_hash); the equivalent "
            "candidate matches output_contract and keeps the baseline's source handles while a "
            "different-contract / handle-dropping candidate fails its gate; a candidate's output is NEVER "
            "served (served_path_id == baseline, candidate_served=false, served_output() returns the baseline, "
            "the held-out CFPB FAQ '30 days' never leaks into a served fact), and a candidate is promoted ONLY "
            "through a passing PathPromotionDecision (held-out leak / dropped handle / different contract / "
            "too-strict cost each block it, rollback_target always = baseline); two independent runs are "
            "byte-identical; and every emitted object validates against its Stage-1 schema with cost driven "
            "by the pricebook CONFIG."
            if ok else f"{len(fails)} FAILURES: {fails}"
        )
    )
    return 0 if ok else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: the parallel-path experiment ENGINE behaves (same input, never-serve-candidate, deterministic).")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
