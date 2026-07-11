#!/usr/bin/env python3
"""scripts.check_parallel_path_promotion_gate — STAGE 3 / EXAMPLE C (reconciliation/CFPB safety): the
parallel-path PROMOTION GATE blocks an unsafe candidate, allows a safe one, and ALWAYS keeps the baseline as
the rollback target.

This drives the Stage-2 engine (_repos/baltor/backend/src/baltor/experiments/) on the canonical CFPB reconciliation invariant —
the SAME one _repos/shared-backend-components/scripts/check_contextops_cfpb_reference.py + _repos/shared-backend-components/scripts/demo_offline_full_baltor.py ride on:

    the agency FAQ says "30 days"; Regulation E (source-of-law) says "10 business days". The deterministic
    reconciliation authority makes Reg-E the WINNER and HOLDS OUT the FAQ "30 days".

The baseline path runs the REAL reconciliation authority (_repos/shared-backend-components/scripts/artifact_graph/reconciliation.py) on the
deterministic-extractor candidates: it yields the served answer "10 business days", grounds on the Reg-E
source handle, and HOLDS OUT the FAQ "30 days". Then three candidate paths challenge it on the IDENTICAL
input snapshot:

  - candidate-GOOD   — an equivalent path: same output_contract, same served facts ("10 business days"),
                       keeps the Reg-E handle, holds out the FAQ "30 days". → PROMOTABLE (all gates green).
  - candidate-BAD-leak — a path that would SERVE the held-out FAQ "30 days". → BLOCKED (held_out_not_leaked
                       gate is false; decide() returns keep_baseline, baseline kept, rollback_target=baseline).
  - candidate-BAD-drophandle — a path that DROPS the Reg-E source handle. → BLOCKED (source_handles_preserved
                       gate is false; keep_baseline, baseline kept, rollback_target=baseline).

ASSERTIONS:
  * the BAD candidates are BLOCKED — decide() returns decision='keep_baseline', promoted_path_id is null,
    the baseline is kept, and rollback_target == the baseline path_id;
  * the GOOD candidate is PROMOTABLE — decide() returns 'promote' with ALL gates true, and even after a
    promotion the rollback_target (a real, schema-valid PathRollbackPlan) still points at the baseline;
  * the baseline is ALWAYS preserved as rollback_target on EVERY decision (promote or keep);
  * the served output is ALWAYS the baseline's "10 business days" — a candidate is NEVER served, and the
    held-out FAQ "30 days" never reaches the served answer;
  * the baseline's won value is byte-equivalent to the EXISTING reconciliation authority (this example
    REPRODUCES that authority, it never builds a second one).

Deterministic, stdlib-only, offline (no network, no RNG, injected `now`, hashlib ids).
CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_parallel_path_promotion_gate.py --self-test
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from scripts.artifact_graph.artifact_ledger import Artifact, Conflict, chash  # noqa: E402
from scripts.artifact_graph.reconciliation import reconcile  # noqa: E402
from scripts.runtime import schema_validator as _sv  # noqa: E402
from src.baltor.contextops.extractor_snippets import extract_duration  # noqa: E402
from src.baltor.experiments import (  # noqa: E402
    RECONCILIATION_CAPABILITY_SLOT,
    parallel_paths,
    path_comparator,
    path_promotion,
    path_rollback,
)

# ── injected deterministic fixtures (no wall-clock, no RNG) ─────────────────────────────────────────────
_NOW = "2026-06-06T00:00:00Z"
_NOW_EPOCH = 1_780_000_000  # injected epoch seconds (never a clock read)
_SLOT = RECONCILIATION_CAPABILITY_SLOT  # "reconciliation.answer"
_OUTPUT_CONTRACT = "consumption/ContextResponse"
_TENANT = "acme"
_FACT_KEY = "reg_e.error_resolution.deadline"
_REG_HANDLE = "ctx://public/source/ecfr/12-CFR-1005.11#para.c.1.i"
_FAQ_HANDLE = "ctx://public/source/cfpb-faq/error-resolution#q12"
#: the CFPB FAQ value the baseline deliberately HELD OUT — must NEVER leak into a candidate served output.
_HELD_OUT_FAQ = "30 days"

#: OFFLINE fixtures — the deterministic duration_parser reads these (no network).
_REG_FIXTURE = ("§1005.11(c)(1)(i) The financial institution shall complete its investigation within "
                "10 business days of receiving a notice of error.")
_FAQ_FIXTURE = "Q12: How long does the bank have? The bank generally has 30 days to investigate an error."

#: source-authority ranks the EXISTING reconciliation authority reads (regulation/law > FAQ).
_REG_RANK = 100
_FAQ_RANK = 10

#: the input EVERY path sees — identical bytes for the baseline + every candidate (apples to apples).
_INPUT_SNAPSHOT = {
    "question": "How long does the bank have to investigate a disputed transaction?",
    "fact_key": _FACT_KEY,
    "candidates": [
        {"handle": _REG_HANDLE, "fixture": _REG_FIXTURE, "source_type": "regulation"},
        {"handle": _FAQ_HANDLE, "fixture": _FAQ_FIXTURE, "source_type": "agency_faq"},
    ],
}


def _path(path_id: str, mode: str, *, output_contract: str = _OUTPUT_CONTRACT) -> dict[str, Any]:
    return {
        "schema_version": "PathDefinition",
        "path_id": path_id,
        "capability_slot": _SLOT,
        "input_contract": "consumption/ConsumptionRequest",
        "output_contract": output_contract,
        "mode": mode,
        "promotion_criteria": "criteria/recon-equivalence-cost-ceiling",
        "rollback_target": "path-recon-baseline-authority",
        "defined_at": _NOW,
    }


_BASELINE = _path("path-recon-baseline-authority", "baseline")
_CAND_GOOD = _path("path-recon-deterministic-good", "candidate")
_CAND_LEAK = _path("path-recon-leak-faq-30days", "candidate")
_CAND_DROP = _path("path-recon-drops-reg-handle", "candidate")


def _ledger_artifact(*, key: str, value, unit: str, rank: int, authority: str, handle: str,
                     source_version: str) -> Artifact:
    """A ledger Artifact built from a DETERMINISTIC extractor candidate's value — never from a model. The
    payload carries the source_rank the EXISTING reconciliation authority reads (precedence comes from the
    discovery/reliability stages, this proof never invents it)."""
    text = f"{value} {unit}"
    payload = {"topic": "investigation_deadline", "value": value, "unit": unit,
               "source_rank": rank, "authority": authority}
    return Artifact(
        artifact_id=f"run-recon-gate:atomic_fact:{key}", tenant_id=_TENANT, source_id=key,
        source_version=source_version, artifact_type="atomic_fact", schema_version="v1", text=text,
        payload_json=payload, content_hash=chash({"t": "atomic_fact", "text": text, "p": payload}),
        parent_artifact_id=None, source_handles_json=[handle], pipeline_id="parallel_path_recon_gate",
        pipeline_version="v1", processor_id="extractor.duration_parser", processor_version="v1",
        run_id="run-recon-gate", claim_status="fact", promotion_eligible=True, created_at=_NOW)


def _run_real_reconciliation() -> dict[str, Any]:
    """Run the EXISTING deterministic reconciliation authority on the extractor candidates.

    Returns {answer, claim_status, won_artifact_id, held_out_ids, rec} — the SAME invariant the CFPB
    reference proves: Reg-E "10 business days" WINS, the FAQ "30 days" is HELD OUT.
    """
    reg_cl = extract_duration(_REG_FIXTURE, fact_key=_FACT_KEY, source_handle=_REG_HANDLE,
                              extracted_at=_NOW_EPOCH, tenant_id=_TENANT)
    faq_cl = extract_duration(_FAQ_FIXTURE, fact_key=_FACT_KEY, source_handle=_FAQ_HANDLE,
                              extracted_at=_NOW_EPOCH, tenant_id=_TENANT)
    reg_art = _ledger_artifact(key="reg_e_deadline", value=reg_cl.value, unit=reg_cl.unit, rank=_REG_RANK,
                               authority="Regulation E", handle=_REG_HANDLE, source_version="reg-e-2025")
    faq_art = _ledger_artifact(key="faq_deadline", value=faq_cl.value, unit=faq_cl.unit, rank=_FAQ_RANK,
                               authority="FAQ", handle=_FAQ_HANDLE, source_version="faq-2026")
    by_id = {reg_art.artifact_id: reg_art, faq_art.artifact_id: faq_art}
    conflict = Conflict(
        conflict_id="conf-recon-gate-deadline", tenant_id=_TENANT, artifact_a_id=reg_art.artifact_id,
        artifact_b_id=faq_art.artifact_id, conflict_type="value_conflict", detector="parallel_path.recon_gate",
        severity="high", evidence_json={"fact_key": _FACT_KEY}, status="open")
    rec = reconcile([conflict], by_id, tenant_id=_TENANT, now=_NOW)
    won_id = rec["winners"].get(conflict.conflict_id)
    won_art = by_id[won_id]
    # the served answer is the WINNING artifact's value rendered "10 business days" — never the FAQ value.
    answer = f"{won_art.payload_json['value']} business days"
    return {
        "answer": answer,
        "claim_status": "verified_current",
        "won_artifact_id": won_id,
        "held_out_ids": list(rec["held_out_ids"]),
        "reg_art_id": reg_art.artifact_id,
        "faq_art_id": faq_art.artifact_id,
        "rec": rec,
        "conflict_id": conflict.conflict_id,
    }


def _make_runner(recon: dict[str, Any]) -> parallel_paths.Runner:
    """A deterministic runner: the baseline runs the REAL reconciliation answer; candidates are fixed paths.

    baseline → "10 business days" grounded on the Reg-E handle, FAQ "30 days" held out.
    GOOD     → equivalent answer, same handle, no leak (promotable).
    LEAK     → would serve the held-out FAQ "30 days" (must be blocked).
    DROP     → drops the Reg-E source handle (must be blocked).
    """
    served = {"answer": recon["answer"], "claim_status": recon["claim_status"]}
    # baseline + good run on the local function emulator; candidates priced same/cheaper via pricebook in the
    # examples proof — here the gate logic is what matters, so costs are equal (cost gate not the focus).
    results: dict[str, dict[str, Any]] = {
        _BASELINE["path_id"]: {
            "output": dict(served), "output_contract": _OUTPUT_CONTRACT,
            "cost": 0.0, "latency_ms": 1.0, "error": None,
            "contract_validation": "pass", "source_handles": [_REG_HANDLE],
        },
        _CAND_GOOD["path_id"]: {  # equivalent facts, same contract, keeps the handle, no leak
            "output": dict(served), "output_contract": _OUTPUT_CONTRACT,
            "cost": 0.0, "latency_ms": 1.0, "error": None,
            "contract_validation": "pass", "source_handles": [_REG_HANDLE],
        },
        _CAND_LEAK["path_id"]: {  # would SERVE the held-out FAQ "30 days"
            "output": {"answer": "the bank has 30 days to investigate", "claim_status": "verified_current"},
            "output_contract": _OUTPUT_CONTRACT, "cost": 0.0, "latency_ms": 1.0, "error": None,
            "contract_validation": "pass", "source_handles": [_REG_HANDLE],
        },
        _CAND_DROP["path_id"]: {  # DROPS the Reg-E source handle (coverage < baseline)
            "output": dict(served), "output_contract": _OUTPUT_CONTRACT,
            "cost": 0.0, "latency_ms": 1.0, "error": None,
            "contract_validation": "pass", "source_handles": [],
        },
    }

    def runner(path: dict[str, Any], input_snapshot: Any) -> dict[str, Any]:
        return dict(results[path["path_id"]])

    return runner


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    # ── 0 · the REAL reconciliation authority decides the baseline answer (Reg-E wins, FAQ held out). ──
    recon = _run_real_reconciliation()
    check("AUTHORITY: the EXISTING reconciliation authority makes Reg-E '10 business days' the served answer",
          recon["answer"] == "10 business days" and recon["won_artifact_id"] == recon["reg_art_id"])
    check("AUTHORITY: the FAQ '30 days' artifact is HELD OUT by the authority (not served)",
          recon["faq_art_id"] in recon["held_out_ids"])
    recon2 = _run_real_reconciliation()
    check("AUTHORITY: the reconciliation is byte-equivalent on a re-run (reproduced, not a second authority)",
          json.dumps(recon["rec"]["reconciliations"][0].receipt_json, sort_keys=True)
          == json.dumps(recon2["rec"]["reconciliations"][0].receipt_json, sort_keys=True))

    # ── 1 · run the engine: baseline + 3 candidates on the IDENTICAL input snapshot. ──
    runner = _make_runner(recon)
    candidates = [_CAND_GOOD, _CAND_LEAK, _CAND_DROP]
    run = parallel_paths.run_parallel(_SLOT, _INPUT_SNAPSHOT, _BASELINE, candidates, runner=runner, now=_NOW)
    report = path_comparator.compare(run, now=_NOW, held_out_strings=[_HELD_OUT_FAQ], unsafe_strings=[])
    criteria = {"max_cost_delta": 0.0}
    decisions = {
        c["path_id"]: path_promotion.decide(report, criteria, candidate_path_id=c["path_id"], now=_NOW)
        for c in candidates
    }

    # ── 2 · the served output is ALWAYS the baseline; a candidate is NEVER served; no held-out leak. ──
    served = parallel_paths.served_output(run)
    check("SERVE: served_path_id is ALWAYS the baseline (a candidate is never served)",
          run["served_path_id"] == _BASELINE["path_id"] and run["candidate_served"] is False)
    served_text = json.dumps(served["output"], sort_keys=True)
    check("SERVE: the served answer is the reconciled Reg-E '10 business days'", "10 business days" in served_text)
    check("SERVE: the held-out FAQ '30 days' is NOT in the served output", _HELD_OUT_FAQ not in served_text)

    # ── 3 · the BAD candidates are BLOCKED by the promotion gate. ──
    leak_dec = decisions[_CAND_LEAK["path_id"]]
    drop_dec = decisions[_CAND_DROP["path_id"]]
    check("GATE-BAD: the FAQ-'30 days' LEAK candidate has held_out_not_leaked=false",
          leak_dec["held_out_not_leaked"] is False)
    check("GATE-BAD: the LEAK candidate is BLOCKED — decide() returns keep_baseline (not promoted)",
          leak_dec["decision"] == "keep_baseline" and leak_dec["promoted_path_id"] is None)
    check("GATE-BAD: the LEAK candidate's rollback_target == the baseline path_id (baseline kept)",
          leak_dec["rollback_target"] == _BASELINE["path_id"])
    check("GATE-BAD: the handle-DROPPING candidate has source_handles_preserved=false",
          drop_dec["source_handles_preserved"] is False)
    check("GATE-BAD: the DROP candidate is BLOCKED — decide() returns keep_baseline (not promoted)",
          drop_dec["decision"] == "keep_baseline" and drop_dec["promoted_path_id"] is None)
    check("GATE-BAD: the DROP candidate's rollback_target == the baseline path_id (baseline kept)",
          drop_dec["rollback_target"] == _BASELINE["path_id"])

    # ── 4 · the GOOD candidate is PROMOTABLE (ALL gates green, incl. same_input). ──
    good_dec = decisions[_CAND_GOOD["path_id"]]
    check("GATE-GOOD: the equivalent candidate is PROMOTABLE — decide() returns 'promote'",
          good_dec["decision"] == "promote" and good_dec["promoted_path_id"] == _CAND_GOOD["path_id"])
    check("GATE-GOOD: ALL six promotion gates are true for the GOOD candidate",
          all(good_dec[g] is True for g in path_promotion.GATES), str({g: good_dec[g] for g in path_promotion.GATES}))
    check("GATE-GOOD: even a PROMOTE decision sets rollback_target == the baseline (always reversible)",
          good_dec["rollback_target"] == _BASELINE["path_id"])

    # ── 5 · the baseline is ALWAYS preserved as rollback_target on EVERY decision. ──
    for cpid, dec in decisions.items():
        check(f"ROLLBACK: decision for {cpid} preserves the baseline as rollback_target",
              dec["rollback_target"] == _BASELINE["path_id"])
    promoted = [cpid for cpid, d in decisions.items() if d["decision"] == "promote"]
    check("GATE: EXACTLY one candidate (the GOOD one) is promotable — both BAD candidates are blocked",
          promoted == [_CAND_GOOD["path_id"]], str(promoted))

    # ── 6 · a real PathRollbackPlan reverts the promotion by a POINTER MOVE — deletes nothing. ──
    plan = path_rollback.build_rollback_plan(good_dec, now=_NOW)
    check("ROLLBACK-PLAN: a PathRollbackPlan reverts the GOOD promotion to the baseline pointer",
          plan["rollback_target_path_id"] == _BASELINE["path_id"]
          and plan["from_path_id"] == _CAND_GOOD["path_id"])
    check("ROLLBACK-PLAN: rollback is a POINTER MOVE — deletes_paths=false, deletes_prior_runs=false (lossless)",
          plan["deletes_paths"] is False and plan["deletes_prior_runs"] is False)
    check("ROLLBACK-PLAN: the plan validates against experiments/PathRollbackPlan",
          _sv.validate_ref(plan, "experiments/PathRollbackPlan") == [])
    check("ROLLBACK-PLAN: the plan references the promotion decision it reverses",
          plan["promotion_decision_id"] == good_dec["decision_id"])

    # ── 7 · every emitted engine object validates against its Stage-1 schema. ──
    check("(+) ParallelPathRun validates against experiments/ParallelPathRun",
          _sv.validate_ref(run, "experiments/ParallelPathRun") == [])
    check("(+) PathComparisonReport validates against experiments/PathComparisonReport",
          _sv.validate_ref(report, "experiments/PathComparisonReport") == [])
    for cpid, dec in decisions.items():
        check(f"(+) PathPromotionDecision for {cpid} validates against experiments/PathPromotionDecision",
              _sv.validate_ref(dec, "experiments/PathPromotionDecision") == [])

    # ── 8 · deterministic: a second full run is byte-identical. ──
    runner2 = _make_runner(_run_real_reconciliation())
    run2 = parallel_paths.run_parallel(_SLOT, _INPUT_SNAPSHOT, _BASELINE, candidates, runner=runner2, now=_NOW)
    report2 = path_comparator.compare(run2, now=_NOW, held_out_strings=[_HELD_OUT_FAQ], unsafe_strings=[])
    check("DETERMINISTIC: a second full engine run is byte-identical (no wall-clock / RNG)",
          json.dumps(run, sort_keys=True) == json.dumps(run2, sort_keys=True)
          and json.dumps(report, sort_keys=True) == json.dumps(report2, sort_keys=True))

    ok = not fails
    print(
        "\n" + ("PASS — check_parallel_path_promotion_gate: EXAMPLE C (reconciliation/CFPB safety) — the "
                "baseline path runs the EXISTING deterministic reconciliation authority (Reg-E '10 business "
                "days' WINS, FAQ '30 days' HELD OUT, byte-reproduced); on the IDENTICAL input snapshot the "
                "promotion gate BLOCKS the BAD candidates (a FAQ-'30 days' LEAK → held_out_not_leaked=false; a "
                "DROPPED Reg-E handle → source_handles_preserved=false → both keep_baseline, not promoted) and "
                "ALLOWS the equivalent GOOD candidate (all gates green → promote); the baseline is ALWAYS "
                "preserved as rollback_target on EVERY decision; the served output is always the baseline's '10 "
                "business days' (a candidate is never served, the held-out '30 days' never reaches it); a real "
                "schema-valid PathRollbackPlan reverts a promotion by a POINTER MOVE (deletes nothing); and the "
                "whole motion is deterministic."
                if ok else f"{len(fails)} FAILURES: {fails}"))
    return 0 if ok else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="STAGE 3 / EXAMPLE C: the parallel-path promotion gate blocks an unsafe reconciliation "
                    "candidate, allows a safe one, and always keeps the baseline as rollback_target.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
