#!/usr/bin/env python3
"""scripts.check_parallel_path_redteam — STAGE 4 REDTEAM: every attack on the parallel-path experiment
ENGINE (src/baltor/experiments/) FAILS SAFELY. The engine must never serve a candidate as truth, never
promote a candidate without a passing PathPromotionDecision, never drop the baseline's source handles,
never leak a held-out fact, never compare two paths that saw DIFFERENT inputs, never accept a "cheaper"
claim when outputs are not equivalent, and never let a failed candidate destroy the baseline rollback
target.

This drives the SAME CFPB reconciliation invariant the rest of the stack rides on
(scripts/check_contextops_cfpb_reference.py + scripts/demo_offline_full_baltor.py): the agency FAQ says
"30 days"; Regulation E (source-of-law) says "10 business days"; the deterministic authority makes Reg-E
the WINNER and HOLDS OUT the FAQ "30 days". Each attack below tries to subvert the gate; each must be
blocked by the engine's own logic — not by this proof's bookkeeping.

ATTACKS (each must FAIL SAFELY):
  (1) PROMOTE WITHOUT A PASSING DECISION — there is NO code path that promotes a candidate except a
      PathPromotionDecision that is AUTHORIZED. We prove a candidate is "served as baseline" ONLY when
      path_promotion.is_promote_authorized re-derives promote from the decision's OWN gate booleans +
      promoted_path_id (never trusting decision=='promote' alone); a keep_baseline decision never carries a
      promoted_path_id; a hand-forged 'promote' missing fields is schema-rejected; and a SCHEMA-COMPLETE
      forgery (decision='promote' with ALL gates FALSE) is rejected BOTH by the contract's if/then gate
      constraint AND by is_promote_authorized (so "passes the schema" implies a legitimate promote shape).
  (2) CHEAPER CANDIDATE THAT DROPS SOURCE HANDLES — a candidate that is cheaper but drops the Reg-E
      handle fails source_handles_preserved → keep_baseline (cheapness can never buy out grounding).
  (3) CANDIDATE THAT SERVES THE HELD-OUT FAQ "30 days" — held_out_not_leaked is false → keep_baseline,
      and the held-out value never reaches the served output.
  (4) DIFFERENT-INPUT COMPARISON — REJECTED ON THE INPUT (not inferred from output divergence). Every
      per-path result carries an input_snapshot_hash ATTESTATION; the comparator's same_input gate fails
      whenever a candidate's hash != the run's (== the baseline's), routing it to 'investigate' →
      never promotable. (4b) a divergent-output spliced candidate is caught (not equivalent); (4c) the
      HARD case — a SAME-OUTPUT candidate that ran on a DIFFERENT input (output_equivalent=True so a pure
      output proxy is fooled) is STILL blocked by same_input=false; (4d) an honest run is self-consistent
      by construction (every per-path hash == the run hash); (4e) a runner that ATTESTS a different input
      than it was fed is refused by run_parallel at run time.
  (5) "CHEAPER" CLAIM WHEN OUTPUTS ARE NOT EQUIVALENT — a candidate with cost_delta < 0 but a different
      answer fails output_equivalent → keep_baseline (a cheap wrong answer is never promoted).
  (6) CANDIDATE OUTPUT SERVED AS TRUTH BEFORE PROMOTION — run_parallel pins served_path_id == baseline
      and candidate_served == False; served_output() structurally returns the baseline; the schema pins
      candidate_served to [false] so a tampered candidate_served=true run is REJECTED by the contract.
  (7) FAILED CANDIDATE DELETES/OVERWRITES THE BASELINE — a keep_baseline (failed) decision still sets
      rollback_target == baseline, and a rollback plan is a POINTER MOVE (deletes_paths=false,
      deletes_prior_runs=false) so the baseline definition + prior runs SURVIVE.

Deterministic, stdlib-only, offline (no network, no RNG, injected `now`, hashlib ids).
CLI: PYTHONPATH=. python3 scripts/check_parallel_path_redteam.py --self-test
"""
from __future__ import annotations

import argparse
import copy
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
    path_promotion,
    path_rollback,
)

# ── injected deterministic fixtures (no wall-clock, no RNG) ─────────────────────────────────────────────
_NOW = "2026-06-06T00:00:00Z"
_SLOT = RECONCILIATION_CAPABILITY_SLOT  # "reconciliation.answer"
_OUTPUT_CONTRACT = "consumption/ContextResponse.v1"
_REG_HANDLE = "ctx://public/source/ecfr/12-CFR-1005.11#para.c.1.i"
_FAQ_HANDLE = "ctx://public/source/cfpb-faq/error-resolution#q12"
#: the CFPB FAQ value the baseline deliberately HELD OUT — must NEVER leak into a candidate served output.
_HELD_OUT_FAQ = "30 days"
#: the reconciled, served answer (Reg-E wins) — the SAME invariant as demo_offline_full_baltor.
_SERVED_ANSWER = {"answer": "10 business days", "claim_status": "verified_current"}

#: the input EVERY path sees — identical bytes for the baseline + every candidate (apples to apples).
_INPUT_SNAPSHOT = {
    "question": "How long does the bank have to investigate a disputed transaction?",
    "candidates": [
        {"handle": _REG_HANDLE, "text": "10 business days", "source_type": "regulation"},
        {"handle": _FAQ_HANDLE, "text": "30 days", "source_type": "agency_faq"},
    ],
}
#: a DIFFERENT snapshot used only by attack (4) — its hash must differ from _INPUT_SNAPSHOT's.
_OTHER_SNAPSHOT = {
    "question": "How long does the bank have to investigate a disputed transaction?",
    "candidates": [
        {"handle": _REG_HANDLE, "text": "10 business days", "source_type": "regulation"},
        {"handle": _FAQ_HANDLE, "text": "30 days", "source_type": "agency_faq"},
        {"handle": "ctx://public/source/extra#tampered", "text": "tampered", "source_type": "blog"},
    ],
}


def _path(path_id: str, mode: str, *, output_contract: str = _OUTPUT_CONTRACT) -> dict[str, Any]:
    return {
        "schema_version": "PathDefinition.v1",
        "path_id": path_id,
        "capability_slot": _SLOT,
        "input_contract": "consumption/ConsumptionRequest.v1",
        "output_contract": output_contract,
        "mode": mode,
        "promotion_criteria": "criteria/recon-equivalence-cost-ceiling",
        "rollback_target": "path-recon-baseline-authority",
        "defined_at": _NOW,
    }


_BASELINE = _path("path-recon-baseline-authority", "baseline")
_CAND_GOOD = _path("path-recon-good-cand", "candidate")            # equivalent, cheaper, keeps handle
_CAND_CHEAP_DROP = _path("path-recon-cheap-drop", "candidate")     # cheaper BUT drops the Reg-E handle
_CAND_LEAK = _path("path-recon-leak-30days", "candidate")          # serves the held-out FAQ "30 days"
_CAND_CHEAP_WRONG = _path("path-recon-cheap-wrong", "candidate")   # cheaper BUT a different answer


def _runner_results() -> dict[str, dict[str, Any]]:
    """The deterministic per-path RunnerResults driving the redteam. Baseline grounds on the Reg-E handle
    and serves "10 business days" (FAQ "30 days" held out). Each candidate encodes one attack."""
    base_cost = 1.0
    cheaper = 0.1  # strictly cheaper than the baseline (the "cheaper" lure for attacks 2 & 5)
    return {
        _BASELINE["path_id"]: {
            "output": dict(_SERVED_ANSWER), "output_contract": _OUTPUT_CONTRACT,
            "cost": base_cost, "latency_ms": 1800.0, "error": None,
            "contract_validation": "pass", "source_handles": [_REG_HANDLE],
        },
        _CAND_GOOD["path_id"]: {  # equivalent facts, same contract, keeps the handle, cheaper, no leak
            "output": dict(_SERVED_ANSWER), "output_contract": _OUTPUT_CONTRACT,
            "cost": cheaper, "latency_ms": 12.0, "error": None,
            "contract_validation": "pass", "source_handles": [_REG_HANDLE],
        },
        _CAND_CHEAP_DROP["path_id"]: {  # CHEAPER but DROPS the Reg-E grounding handle (attack 2)
            "output": dict(_SERVED_ANSWER), "output_contract": _OUTPUT_CONTRACT,
            "cost": cheaper, "latency_ms": 12.0, "error": None,
            "contract_validation": "pass", "source_handles": [],
        },
        _CAND_LEAK["path_id"]: {  # serves the held-out FAQ "30 days" (attack 3)
            "output": {"answer": "the bank has 30 days to investigate", "claim_status": "verified_current"},
            "output_contract": _OUTPUT_CONTRACT, "cost": cheaper, "latency_ms": 12.0, "error": None,
            "contract_validation": "pass", "source_handles": [_REG_HANDLE],
        },
        _CAND_CHEAP_WRONG["path_id"]: {  # CHEAPER but a DIFFERENT (wrong) answer (attack 5)
            "output": {"answer": "5 business days", "claim_status": "verified_current"},
            "output_contract": _OUTPUT_CONTRACT, "cost": cheaper, "latency_ms": 12.0, "error": None,
            "contract_validation": "pass", "source_handles": [_REG_HANDLE],
        },
    }


def _make_runner(results: dict[str, dict[str, Any]]) -> parallel_paths.Runner:
    def runner(path: dict[str, Any], input_snapshot: Any) -> dict[str, Any]:
        return dict(results[path["path_id"]])
    return runner


def _decide(report: dict[str, Any], candidate_path_id: str, *, criteria: dict[str, Any] | None = None,
            cost_acceptable: bool | None = None) -> dict[str, Any]:
    return path_promotion.decide(
        report, criteria or {"max_cost_delta": 0.0}, candidate_path_id=candidate_path_id,
        now=_NOW, cost_acceptable=cost_acceptable,
    )


def _authorized_served_path(run: dict[str, Any], decision: dict[str, Any] | None) -> str:
    """The ONLY function that may name a NON-baseline served path: a candidate is served only when a
    PathPromotionDecision is AUTHORIZED — i.e. path_promotion.is_promote_authorized re-derives promote from
    the decision's own gate booleans + promoted_path_id (never trusting decision=='promote' alone). A
    forged-but-schema-valid 'promote' with false gates therefore authorizes NOTHING and the baseline serves.
    There is deliberately no other path to a candidate's output anywhere in the engine or this proof.
    """
    promoted = path_promotion.authorized_promoted_path_id(decision) if decision is not None else None
    if promoted is not None:
        return promoted
    return parallel_paths.served_output(run)["path_id"]


def _self_test() -> int:  # noqa: C901 - a redteam reads best as one linear list of attacks
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    results = _runner_results()
    runner = _make_runner(results)
    candidates = [_CAND_GOOD, _CAND_CHEAP_DROP, _CAND_LEAK, _CAND_CHEAP_WRONG]
    run = parallel_paths.run_parallel(_SLOT, _INPUT_SNAPSHOT, _BASELINE, candidates, runner=runner, now=_NOW)
    report = path_comparator.compare(run, now=_NOW, held_out_strings=[_HELD_OUT_FAQ], unsafe_strings=[])
    decisions = {c["path_id"]: _decide(report, c["path_id"]) for c in candidates}

    # ── ATTACK 1 · promote a candidate with NO passing PathPromotionDecision ────────────────────────────
    # The engine has exactly one promotion authority: a PathPromotionDecision with decision == 'promote'.
    # Without one, the served path is structurally the baseline.
    no_decision_served = _authorized_served_path(run, None)
    check("ATTACK-1: with NO decision the served path is the BASELINE (no promotion can happen)",
          no_decision_served == _BASELINE["path_id"], no_decision_served)
    # a keep_baseline decision NEVER carries a promoted_path_id (can't be smuggled into the served path).
    drop_dec = decisions[_CAND_CHEAP_DROP["path_id"]]
    check("ATTACK-1: a keep_baseline decision has promoted_path_id == null (cannot authorize a serve)",
          drop_dec["decision"] == "keep_baseline" and drop_dec["promoted_path_id"] is None)
    check("ATTACK-1: even handed a keep_baseline decision, the served path stays the BASELINE",
          _authorized_served_path(run, drop_dec) == _BASELINE["path_id"])
    # a hand-forged "decision" that is NOT a schema-valid promote is rejected by the contract layer.
    forged = {"decision": "promote", "promoted_path_id": _CAND_LEAK["path_id"]}  # missing every gate/id
    check("ATTACK-1: a hand-forged 'promote' object missing the gates is REJECTED by the schema",
          _sv.validate_ref(forged, "experiments/PathPromotionDecision.v1") != [])
    # a SCHEMA-COMPLETE forgery: every required field present, decision='promote', but ALL gates FALSE.
    # the contract's if/then constraint now REJECTS this (passing the schema implies a legitimate promote
    # shape), AND the runtime barrier is_promote_authorized re-derives the gates and refuses to serve it.
    forged_full = {
        "schema_version": "PathPromotionDecision.v1", "decision_id": "ppd-forged",
        "report_id": report["report_id"], "run_id": run["run_id"], "capability_slot": _SLOT,
        "candidate_path_id": _CAND_LEAK["path_id"], "baseline_path_id": _BASELINE["path_id"],
        "decision": "promote", "promoted_path_id": _CAND_LEAK["path_id"],
        "same_input": False, "same_output_contract": False, "output_equivalent": False,
        "source_handles_preserved": False, "held_out_not_leaked": False, "safety_ok": False,
        "cost_acceptable": False, "rollback_target": _BASELINE["path_id"],
        "reason": "forged", "decided_at": _NOW,
    }
    check("ATTACK-1: a SCHEMA-COMPLETE forged 'promote' with ALL gates FALSE is REJECTED by the contract (if/then)",
          _sv.validate_ref(forged_full, "experiments/PathPromotionDecision.v1") != [])
    check("ATTACK-1: is_promote_authorized() refuses the all-false-gate forgery (label != authorization)",
          path_promotion.is_promote_authorized(forged_full) is False)
    check("ATTACK-1: even fed the forged 'promote', the serve layer keeps serving the BASELINE (no candidate)",
          _authorized_served_path(run, forged_full) == _BASELINE["path_id"])
    # and a decision that is schema-valid 'promote' BUT names a different promoted_path_id than the candidate
    # it judged is also unauthorized (is_promote_authorized requires promoted_path_id == candidate_path_id).
    good_dec = decisions[_CAND_GOOD["path_id"]]
    mismatched = copy.deepcopy(good_dec); mismatched["promoted_path_id"] = _CAND_LEAK["path_id"]
    check("ATTACK-1: a 'promote' whose promoted_path_id != candidate_path_id is NOT authorized to serve",
          path_promotion.is_promote_authorized(mismatched) is False
          and _authorized_served_path(run, mismatched) == _BASELINE["path_id"])
    # a LEGITIMATE promote (from decide()) IS authorized and names the candidate — the barrier isn't always-deny.
    check("ATTACK-1: a LEGITIMATE decide() 'promote' IS authorized and serves the GOOD candidate",
          path_promotion.is_promote_authorized(good_dec) is True
          and _authorized_served_path(run, good_dec) == _CAND_GOOD["path_id"])

    # ── ATTACK 2 · a CHEAPER candidate that DROPS source handles ────────────────────────────────────────
    drop_v = next(v for v in report["candidate_verdicts"] if v["candidate_path_id"] == _CAND_CHEAP_DROP["path_id"])
    check("ATTACK-2: the cheaper handle-dropping candidate IS cheaper (cost_delta < 0 — the lure is real)",
          drop_v["cost_delta"] < 0.0, str(drop_v["cost_delta"]))
    check("ATTACK-2: source_handles_preserved is FALSE for the handle-dropping candidate",
          drop_v["source_handles_preserved"] is False)
    check("ATTACK-2: the cheaper handle-dropping candidate is BLOCKED (keep_baseline) — cheapness can't buy grounding",
          drop_dec["decision"] == "keep_baseline" and drop_dec["promoted_path_id"] is None)
    check("ATTACK-2: the blocked candidate's rollback_target is still the baseline",
          drop_dec["rollback_target"] == _BASELINE["path_id"])

    # ── ATTACK 3 · a candidate that serves the held-out FAQ "30 days" ───────────────────────────────────
    leak_v = next(v for v in report["candidate_verdicts"] if v["candidate_path_id"] == _CAND_LEAK["path_id"])
    leak_dec = decisions[_CAND_LEAK["path_id"]]
    check("ATTACK-3: held_out_not_leaked is FALSE for the candidate serving the FAQ '30 days'",
          leak_v["held_out_not_leaked"] is False)
    check("ATTACK-3: safety_ok is FALSE for the leaking candidate", leak_v["safety_ok"] is False)
    check("ATTACK-3: the FAQ-'30 days' leaker is BLOCKED (keep_baseline, never promoted)",
          leak_dec["decision"] == "keep_baseline" and leak_dec["promoted_path_id"] is None)
    served_text = json.dumps(parallel_paths.served_output(run)["output"], sort_keys=True)
    check("ATTACK-3: the held-out '30 days' is NOT in the served output (it never reaches the consumer)",
          _HELD_OUT_FAQ not in served_text)

    # ── ATTACK 4 · a comparison run where baseline and candidate used DIFFERENT inputs ──────────────────
    # 4a — a real run is structurally immune: run_parallel runs EVERY path on ONE snapshot, so there is one
    #      input_snapshot_hash per run (a run cannot represent two different inputs).
    check("ATTACK-4a: a real run carries exactly ONE input_snapshot_hash (every path saw the same input)",
          run["input_snapshot_hash"] == parallel_paths.sha256_hex(_INPUT_SNAPSHOT))
    check("ATTACK-4a: the two snapshots really differ (the attack premise is real)",
          parallel_paths.sha256_hex(_OTHER_SNAPSHOT) != parallel_paths.sha256_hex(_INPUT_SNAPSHOT))
    # 4b — a TAMPERED run: splice a candidate result produced on _OTHER_SNAPSHOT into the run, and tamper the
    #      recorded input_snapshot_hash to claim it. The independent recompute catches the divergence, and the
    #      forged candidate's output is NOT equivalent to the baseline → never promoted.
    other_runner = _make_runner({
        **results,
        # a divergent candidate result that reflects the OTHER input (an extra tampered fact in the answer)
        _CAND_GOOD["path_id"]: {
            "output": {"answer": "10 business days (tampered)", "claim_status": "verified_current"},
            "output_contract": _OUTPUT_CONTRACT, "cost": 0.1, "latency_ms": 12.0, "error": None,
            "contract_validation": "pass", "source_handles": [_REG_HANDLE],
        },
    })
    other_run = parallel_paths.run_parallel(_SLOT, _OTHER_SNAPSHOT, _BASELINE, [_CAND_GOOD],
                                            runner=other_runner, now=_NOW)
    tampered = copy.deepcopy(run)
    # splice the divergent candidate output in, then forge the hash to claim it came from _INPUT_SNAPSHOT.
    spliced_cand = next(c for c in other_run["candidate_results"] if c["path_id"] == _CAND_GOOD["path_id"])
    tampered["candidate_results"] = [spliced_cand] + [
        c for c in tampered["candidate_results"] if c["path_id"] != _CAND_GOOD["path_id"]
    ]
    # the baseline ran on _INPUT_SNAPSHOT; the spliced candidate ran on _OTHER_SNAPSHOT — they DIVERGE.
    recomputed_base_hash = parallel_paths.sha256_hex(_INPUT_SNAPSHOT)
    spliced_cand_hash = other_run["input_snapshot_hash"]
    check("ATTACK-4b: the spliced candidate came from a DIFFERENT input than the run claims (hashes diverge)",
          recomputed_base_hash != spliced_cand_hash)
    tamper_report = path_comparator.compare(tampered, now=_NOW, held_out_strings=[_HELD_OUT_FAQ], unsafe_strings=[])
    tamper_v = next(v for v in tamper_report["candidate_verdicts"] if v["candidate_path_id"] == _CAND_GOOD["path_id"])
    check("ATTACK-4b: the spliced different-input candidate is NOT output_equivalent (divergence is caught)",
          tamper_v["output_equivalent"] is False)
    tamper_dec = _decide(tamper_report, _CAND_GOOD["path_id"])
    check("ATTACK-4b: the different-input candidate is BLOCKED (keep_baseline, never promoted)",
          tamper_dec["decision"] == "keep_baseline" and tamper_dec["promoted_path_id"] is None)

    # 4c — the HARD case the old proof never tested: a SAME-OUTPUT candidate that ran on a DIFFERENT input.
    # Its output is byte-identical to the baseline's (so output_equivalent is True — a pure output proxy is
    # FOOLED), but it executed on _OTHER_SNAPSHOT, so its recorded input_snapshot_hash differs from the run's.
    # The same_input gate (checked on the INPUT, not the output) catches it: same_input=false → investigate →
    # NEVER promoted. This is the root fix; before it, this candidate was promoted.
    same_out_other_runner = _make_runner({
        **results,
        # SAME canonical output as the baseline, but produced on _OTHER_SNAPSHOT.
        _CAND_GOOD["path_id"]: dict(results[_BASELINE["path_id"]]),
    })
    other_run_same_out = parallel_paths.run_parallel(
        _SLOT, _OTHER_SNAPSHOT, _BASELINE, [_CAND_GOOD], runner=same_out_other_runner, now=_NOW)
    spliced_same_out = next(c for c in other_run_same_out["candidate_results"]
                            if c["path_id"] == _CAND_GOOD["path_id"])
    splice4c = copy.deepcopy(run)  # the SNAP_A run (baseline saw _INPUT_SNAPSHOT)
    splice4c["candidate_results"] = [spliced_same_out] + [
        c for c in splice4c["candidate_results"] if c["path_id"] != _CAND_GOOD["path_id"]
    ]
    check("ATTACK-4c: the spliced SAME-OUTPUT candidate carries a DIFFERENT input_snapshot_hash than the run",
          spliced_same_out["input_snapshot_hash"] != run["input_snapshot_hash"]
          and spliced_same_out["input_snapshot_hash"] == parallel_paths.sha256_hex(_OTHER_SNAPSHOT))
    rpt4c = path_comparator.compare(splice4c, now=_NOW, held_out_strings=[_HELD_OUT_FAQ], unsafe_strings=[])
    v4c = next(v for v in rpt4c["candidate_verdicts"] if v["candidate_path_id"] == _CAND_GOOD["path_id"])
    check("ATTACK-4c: output_equivalent is TRUE (a pure output proxy WOULD be fooled — the hole's premise)",
          v4c["output_equivalent"] is True)
    check("ATTACK-4c: but same_input is FALSE (the divergence is caught on the INPUT, not the output)",
          v4c["same_input"] is False)
    check("ATTACK-4c: the comparator routes a different-input candidate to 'investigate' (not keep/promote)",
          v4c["recommended_action"] == "investigate")
    dec4c = _decide(rpt4c, _CAND_GOOD["path_id"])
    check("ATTACK-4c: the SAME-OUTPUT different-input candidate is NOT promoted (same_input gate blocks it)",
          dec4c["decision"] == "keep_baseline" and dec4c["promoted_path_id"] is None
          and dec4c["same_input"] is False)
    check("ATTACK-4c: is_promote_authorized refuses it AND the serve layer keeps the BASELINE",
          path_promotion.is_promote_authorized(dec4c) is False
          and _authorized_served_path(splice4c, dec4c) == _BASELINE["path_id"])
    # 4d — an HONEST run is self-consistent by construction: every per-path input_snapshot_hash == run hash.
    honest_hashes = [run["baseline_result"]["input_snapshot_hash"]] + [
        c["input_snapshot_hash"] for c in run["candidate_results"]]
    check("ATTACK-4d: in an honest run every per-path input_snapshot_hash == the run hash (same-input by construction)",
          all(h == run["input_snapshot_hash"] for h in honest_hashes))
    # 4e — a runner that ATTESTS a different input than the engine fed it is refused at run time (on the INPUT).
    def _lying_runner(path: dict[str, Any], snap: Any) -> dict[str, Any]:
        r = dict(results[path["path_id"]])
        r["input_snapshot_hash"] = parallel_paths.sha256_hex(_OTHER_SNAPSHOT)  # claim a different input
        return r
    lying_refused = False
    try:
        parallel_paths.run_parallel(_SLOT, _INPUT_SNAPSHOT, _BASELINE, [_CAND_GOOD],
                                    runner=_lying_runner, now=_NOW)
    except ValueError:
        lying_refused = True
    check("ATTACK-4e: a runner that attests a DIFFERENT input than fed is REFUSED by run_parallel (on the input)",
          lying_refused)

    # ── ATTACK 5 · a "cheaper" claim when outputs are NOT equivalent ────────────────────────────────────
    wrong_v = next(v for v in report["candidate_verdicts"] if v["candidate_path_id"] == _CAND_CHEAP_WRONG["path_id"])
    wrong_dec = decisions[_CAND_CHEAP_WRONG["path_id"]]
    check("ATTACK-5: the cheap-wrong candidate IS cheaper (cost_delta < 0 — the lure is real)",
          wrong_v["cost_delta"] < 0.0, str(wrong_v["cost_delta"]))
    check("ATTACK-5: output_equivalent is FALSE for the cheap-but-different-answer candidate",
          wrong_v["output_equivalent"] is False)
    check("ATTACK-5: the cheap-wrong candidate is BLOCKED (keep_baseline) — a cheap wrong answer is never promoted",
          wrong_dec["decision"] == "keep_baseline" and wrong_dec["promoted_path_id"] is None)
    # even forcing the cost gate open (justified override) cannot promote it — the other gates still fail.
    forced = _decide(report, _CAND_CHEAP_WRONG["path_id"], cost_acceptable=True)
    check("ATTACK-5: even with the cost gate forced open, a non-equivalent candidate stays keep_baseline",
          forced["cost_acceptable"] is True and forced["output_equivalent"] is False
          and forced["decision"] == "keep_baseline")

    # ── ATTACK 6 · a candidate output served as truth BEFORE promotion ──────────────────────────────────
    check("ATTACK-6: run pins served_path_id == baseline and candidate_served == False (no early serve)",
          run["served_path_id"] == _BASELINE["path_id"] and run["candidate_served"] is False)
    check("ATTACK-6: served_output() structurally returns the BASELINE (no branch returns a candidate)",
          parallel_paths.served_output(run)["path_id"] == _BASELINE["path_id"])
    # tamper the run to flip candidate_served=true and serve a candidate → the schema REJECTS it.
    forged_serve = copy.deepcopy(run)
    forged_serve["candidate_served"] = True
    forged_serve["served_path_id"] = _CAND_GOOD["path_id"]
    check("ATTACK-6: a forged candidate_served=true run is REJECTED by the ParallelPathRun.v1 contract",
          _sv.validate_ref(forged_serve, "experiments/ParallelPathRun.v1") != [])
    # and a real run is schema-clean (the contract is doing real work, not always-failing).
    check("ATTACK-6: the honest run validates clean against ParallelPathRun.v1",
          _sv.validate_ref(run, "experiments/ParallelPathRun.v1") == [])

    # ── ATTACK 7 · a failed candidate attempts to delete/overwrite the baseline (rollback must survive) ──
    # the leak candidate FAILED; its decision must still preserve the baseline as the rollback target, and a
    # rollback plan is a POINTER MOVE that deletes nothing — the baseline definition + prior runs survive.
    check("ATTACK-7: the FAILED leak candidate's decision still names the baseline as rollback_target",
          leak_dec["rollback_target"] == _BASELINE["path_id"])
    fail_plan = path_rollback.build_rollback_plan(leak_dec, now=_NOW)
    check("ATTACK-7: a rollback from a FAILED candidate reverts the pointer to the baseline",
          fail_plan["rollback_target_path_id"] == _BASELINE["path_id"])
    check("ATTACK-7: rollback NEVER deletes — deletes_paths=false AND deletes_prior_runs=false (baseline survives)",
          fail_plan["deletes_paths"] is False and fail_plan["deletes_prior_runs"] is False)
    check("ATTACK-7: the rollback plan validates against experiments/PathRollbackPlan.v1",
          _sv.validate_ref(fail_plan, "experiments/PathRollbackPlan.v1") == [])
    # the baseline definition + the prior run object are UNTOUCHED by any decision/plan (still readable).
    check("ATTACK-7: the baseline PathDefinition is unchanged after the failed-candidate motion",
          _BASELINE["path_id"] == "path-recon-baseline-authority" and _BASELINE["mode"] == "baseline")
    check("ATTACK-7: the prior ParallelPathRun is still readable (its baseline_result intact)",
          run["baseline_result"]["path_id"] == _BASELINE["path_id"]
          and "10 business days" in json.dumps(run["baseline_result"]["output"], sort_keys=True))

    # ── EXACTLY ONE candidate (the GOOD one) is promotable; every attack candidate is blocked. ──────────
    promotable = [cpid for cpid, d in decisions.items() if d["decision"] == "promote"]
    check("OVERALL: EXACTLY the GOOD candidate is promotable — every attack candidate is blocked",
          promotable == [_CAND_GOOD["path_id"]], str(promotable))
    for cpid, dec in decisions.items():
        check(f"OVERALL: decision for {cpid} preserves the baseline as rollback_target",
              dec["rollback_target"] == _BASELINE["path_id"])

    # ── DETERMINISTIC: a second full redteam pass is byte-identical. ────────────────────────────────────
    run2 = parallel_paths.run_parallel(_SLOT, _INPUT_SNAPSHOT, _BASELINE, candidates,
                                       runner=_make_runner(_runner_results()), now=_NOW)
    report2 = path_comparator.compare(run2, now=_NOW, held_out_strings=[_HELD_OUT_FAQ], unsafe_strings=[])
    check("DETERMINISTIC: a second redteam pass is byte-identical (no wall-clock / RNG)",
          json.dumps(run, sort_keys=True) == json.dumps(run2, sort_keys=True)
          and json.dumps(report, sort_keys=True) == json.dumps(report2, sort_keys=True))

    ok = not fails
    print(
        "\n" + ("PASS — check_parallel_path_redteam: EVERY attack on the parallel-path engine FAILS SAFELY — "
                "(1) a candidate is served ONLY via an AUTHORIZED PathPromotionDecision — is_promote_authorized "
                "re-derives promote from the decision's own gates + promoted_path_id (a keep_baseline carries no "
                "promoted_path_id; a forged 'promote' missing fields is schema-rejected; a SCHEMA-COMPLETE forgery "
                "with all gates FALSE is rejected by the contract's if/then AND by is_promote_authorized; a "
                "mismatched promoted_path_id is unauthorized); (2) a CHEAPER candidate that drops the Reg-E handle "
                "is BLOCKED (source_handles_preserved=false); (3) a candidate serving the held-out FAQ '30 days' "
                "is BLOCKED (held_out_not_leaked=false) and the value never reaches the served output; (4) a "
                "different-input comparison is REJECTED ON THE INPUT via the per-path input_snapshot_hash same_input "
                "gate — a divergent-output splice (4b), a SAME-OUTPUT different-input splice (4c, the closed hole), "
                "and a lying runner (4e) are all caught, and an honest run is self-consistent by construction (4d); "
                "(5) a 'cheaper' candidate whose answer is NOT equivalent is BLOCKED even with "
                "the cost gate forced open; (6) candidate_served is pinned false and a forged candidate_served=true "
                "run is schema-rejected (no early serve); (7) a FAILED candidate cannot delete/overwrite the "
                "baseline — rollback is a pointer move (deletes nothing) so the baseline + prior runs survive; "
                "EXACTLY the GOOD candidate is promotable; deterministic."
                if ok else f"{len(fails)} FAILURES: {fails}"))
    return 0 if ok else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="STAGE 4 REDTEAM: every attack on the parallel-path experiment engine fails safely "
                    "(no early serve, no promote-without-decision, no dropped handles, no held-out leak, "
                    "no different-input compare, no cheap-non-equivalent promote, baseline rollback survives).")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
