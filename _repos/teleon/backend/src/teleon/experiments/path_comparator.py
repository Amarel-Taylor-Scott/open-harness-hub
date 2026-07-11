"""src/teleon/experiments/path_comparator — judge each candidate against the baseline (never serve one).

``compare(run, *, now, held_out_strings=..., unsafe_strings=...) -> PathComparisonReport`` produces one
verdict per candidate in a :func:`parallel_paths.run_parallel` result. The comparator ONLY judges; it
never serves a candidate. Each verdict carries the gates the promotion decision reads:

  - same_input               — the candidate provably ran on the SAME input as the baseline: its
                               per-candidate input_snapshot_hash equals the run's (== baseline's). A
                               DIFFERENT-input comparison (a spliced candidate that executed on another
                               snapshot) is REJECTED on the INPUT here — not inferred from output divergence.
  - same_output_contract     — candidate declared the SAME output_contract as the baseline.
  - output_equivalent        — the candidate's served facts are equivalent to the baseline's (and the
                               candidate did not error).
  - source_handles_preserved — candidate kept AT LEAST the baseline's grounding handles
                               (coverage >= baseline coverage AND its handle set ⊇ the baseline's).
  - held_out_not_leaked      — a fact the baseline deliberately HELD OUT (e.g. the CFPB FAQ "30 days")
                               does NOT appear anywhere in the candidate's output.
  - safety_ok                — no unsafe / ungrounded / held-out / leaked content in the candidate output.
  - cost_delta               — candidate.cost - baseline.cost (negative = cheaper).

recommended_action is 'promote' ONLY when every boolean gate is green; 'investigate' when same_input is
false (a different-input comparison — never silently a keep_baseline) or the candidate errored / its
contract did not validate; otherwise 'keep_baseline'. Pure + deterministic: ``now`` and the held-out /
unsafe string sets are injected; no wall-clock / RNG / network.

Canonical TELEON home (experiments layer); imports its ids leaf from Teleon — never Baltor. Baltor re-exports
this via a shim at _repos/baltor/backend/src/baltor/experiments/path_comparator.py.
"""
from __future__ import annotations

import json
from typing import Any, Iterable

from scripts.runtime import schema_validator as _sv

from .ids import canonical_id

SCHEMA_VERSION = "PathComparisonReport"
ACTION_PROMOTE = "promote"
ACTION_KEEP = "keep_baseline"
ACTION_INVESTIGATE = "investigate"


def _output_text(output: Any) -> str:
    """A deterministic, lower-cased string view of any JSON output, for held-out / unsafe substring checks.

    None -> "" (an errored candidate has no output to leak). Strings/numbers/objects are flattened via
    canonical JSON so a held-out value buried in a nested field is still detectable.
    """
    if output is None:
        return ""
    if isinstance(output, str):
        return output.lower()
    return json.dumps(output, sort_keys=True, ensure_ascii=False).lower()


def _leaks_any(output: Any, needles: Iterable[str]) -> bool:
    """True iff any needle (case-insensitive) appears in the output's flattened text."""
    text = _output_text(output)
    return any(n.lower() in text for n in needles if n)


def _facts_equivalent(baseline_output: Any, candidate_output: Any) -> bool:
    """Candidate's served facts are equivalent to the baseline's.

    Equivalence is canonical-bytes equality of the outputs (order/whitespace-insensitive). A candidate that
    errored (output None) while the baseline produced an output is NOT equivalent.
    """
    if candidate_output is None and baseline_output is not None:
        return False
    return json.dumps(baseline_output, sort_keys=True, ensure_ascii=False) == json.dumps(
        candidate_output, sort_keys=True, ensure_ascii=False
    )


def _verdict(
    *,
    baseline: dict[str, Any],
    cand: dict[str, Any],
    run_input_snapshot_hash: str,
    held_out_strings: list[str],
    unsafe_strings: list[str],
) -> dict[str, Any]:
    """One per-candidate verdict with the gates + a recommended_action.

    same_input is checked on the INPUT: the candidate's recorded input_snapshot_hash MUST equal the run's
    (== the baseline's). A DIFFERENT-input comparison fails this gate and is routed to 'investigate' — it is
    NEVER promotable, regardless of whether the output happens to be equivalent.
    """
    errored = cand.get("error") is not None
    contract_failed = cand.get("contract_validation") == "fail"

    # input attestation: the candidate must provably have run on the SAME input the baseline did.
    same_input = (
        cand.get("input_snapshot_hash") == run_input_snapshot_hash
        and run_input_snapshot_hash == baseline.get("input_snapshot_hash")
    )

    same_output_contract = cand.get("output_contract") == baseline.get("output_contract")
    output_equivalent = (not errored) and _facts_equivalent(baseline.get("output"), cand.get("output"))

    # >= baseline coverage AND the candidate's handle set is a superset of the baseline's (kept AT LEAST).
    base_handles = set(baseline.get("source_handles") or [])
    cand_handles = set(cand.get("source_handles") or [])
    source_handles_preserved = (
        cand.get("source_handle_coverage", 0.0) >= baseline.get("source_handle_coverage", 0.0)
        and base_handles <= cand_handles
    )

    # a baseline-held-out value (e.g. FAQ "30 days") must NOT appear in the candidate output.
    held_out_not_leaked = not _leaks_any(cand.get("output"), held_out_strings)
    # safety: grounded (no error/contract fail), nothing held-out leaked, no unsafe needle present.
    safety_ok = (
        (not errored)
        and (not contract_failed)
        and held_out_not_leaked
        and not _leaks_any(cand.get("output"), unsafe_strings)
    )

    cost_delta = float(cand.get("cost", 0.0)) - float(baseline.get("cost", 0.0))

    all_gates_green = (
        same_input
        and same_output_contract
        and output_equivalent
        and source_handles_preserved
        and held_out_not_leaked
        and safety_ok
    )
    if not same_input:
        # a different-input comparison is NOT a quiet keep_baseline — it is an integrity fault to investigate.
        action = ACTION_INVESTIGATE
        note = (f"investigate: same_input=false — candidate input_snapshot_hash "
                f"{cand.get('input_snapshot_hash')!r} != run/baseline {run_input_snapshot_hash!r} "
                f"(different-input comparison; never promotable)")
    elif all_gates_green:
        action = ACTION_PROMOTE
        note = ("all gates green: same input, same contract, equivalent facts, handles preserved, "
                "no held-out leak, safe")
    elif errored or contract_failed:
        action = ACTION_INVESTIGATE
        note = f"investigate: error={cand.get('error')!r}, contract_validation={cand.get('contract_validation')!r}"
    else:
        failed = [
            g
            for g, v in (
                ("same_input", same_input),
                ("same_output_contract", same_output_contract),
                ("output_equivalent", output_equivalent),
                ("source_handles_preserved", source_handles_preserved),
                ("held_out_not_leaked", held_out_not_leaked),
                ("safety_ok", safety_ok),
            )
            if not v
        ]
        action = ACTION_KEEP
        note = f"keep_baseline: failing gate(s) {failed}"

    return {
        "candidate_path_id": cand["path_id"],
        "same_input": same_input,
        "same_output_contract": same_output_contract,
        "output_equivalent": output_equivalent,
        "source_handles_preserved": source_handles_preserved,
        "held_out_not_leaked": held_out_not_leaked,
        "safety_ok": safety_ok,
        "cost_delta": cost_delta,
        "recommended_action": action,
        "notes": note,
    }


def compare(
    run: dict[str, Any],
    *,
    now: str,
    held_out_strings: Iterable[str] | None = None,
    unsafe_strings: Iterable[str] | None = None,
    validate: bool = True,
) -> dict[str, Any]:
    """Compare every candidate in ``run`` against its baseline; return a ``PathComparisonReport`` dict.

    ``held_out_strings`` are values the baseline deliberately held out (e.g. the CFPB FAQ "30 days") that
    must not leak into a candidate output. ``unsafe_strings`` are additional content that, if present,
    makes a candidate unsafe. ``now`` is injected. The comparator NEVER serves a candidate.
    """
    held = list(held_out_strings or [])
    unsafe = list(unsafe_strings or [])
    baseline = run["baseline_result"]
    run_input_snapshot_hash = run["input_snapshot_hash"]

    verdicts = [
        _verdict(baseline=baseline, cand=cand, run_input_snapshot_hash=run_input_snapshot_hash,
                 held_out_strings=held, unsafe_strings=unsafe)
        for cand in run.get("candidate_results", [])
    ]

    report: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "report_id": canonical_id("pcr", run["run_id"], *[v["candidate_path_id"] for v in verdicts]),
        "run_id": run["run_id"],
        "capability_slot": run["capability_slot"],
        "baseline_path_id": baseline["path_id"],
        "candidate_verdicts": verdicts,
        "compared_at": now,
    }
    if validate:
        errs = _sv.validate_ref(report, f"experiments/{SCHEMA_VERSION}")
        if errs:
            raise ValueError(f"PathComparisonReport failed contract validation: {errs[:5]}")
    return report
