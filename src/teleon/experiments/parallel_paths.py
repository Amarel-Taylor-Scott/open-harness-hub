"""src/teleon/experiments/parallel_paths — run a baseline path + candidate paths on the SAME input.

``run_parallel(capability_slot, input_snapshot, baseline_path, candidate_paths, *, runner, now)`` executes
the baseline path AND each candidate path on the IDENTICAL ``input_snapshot`` (recording
``input_snapshot_hash`` = sha256 of its canonical bytes — the proof every path saw the same input), and
records each result's output, cost, latency, error, source-handle coverage and contract validation.

NON-NEGOTIABLE: the engine NEVER serves a candidate's output as truth. ``served_path_id`` is ALWAYS the
baseline path's id and ``candidate_served`` is ALWAYS ``False``. A candidate result is recorded for the
comparator to judge — it is never returned to a consumer.

Pure + deterministic: the actual path execution is delegated to a caller-supplied ``runner(path,
input_snapshot) -> RunnerResult``; ``now`` is injected; ids are content hashes. No wall-clock / RNG /
network here. Canonical TELEON home (experiments layer); imports its ids leaf from Teleon — never Baltor.
Baltor re-exports this via a shim at src/baltor/experiments/parallel_paths.py.
"""
from __future__ import annotations

from typing import Any, Callable

from scripts.runtime import schema_validator as _sv

from .ids import canonical_id, sha256_hex

#: a RunnerResult is what a caller's runner returns for one path on the input_snapshot:
#:   {"output": <any|None>, "output_contract": str, "cost": number, "latency_ms": number,
#:    "error": str|None, "source_handles": list[str]|set[str], "input_snapshot_hash": str|None}
#: input_snapshot_hash is the runner's ATTESTATION of the input it actually executed on. It is OPTIONAL —
#: when omitted the engine pins it to the run's single computed hash (an honest run is self-consistent by
#: construction). When present it MUST equal the run's computed hash, or the engine refuses the run (a
#: runner that ran on a different input than the engine fed it is rejected at the INPUT, not inferred from
#: output divergence). The recorded per-path input_snapshot_hash is the attestation the comparator checks.
RunnerResult = dict[str, Any]
#: runner(path_definition, input_snapshot) -> RunnerResult.
Runner = Callable[[dict[str, Any], Any], RunnerResult]

SCHEMA_VERSION = "ParallelPathRun"
#: the served result is ALWAYS one of these modes — never a candidate/shadow/canary (schema enum-bounds it).
SERVABLE_MODES = ("baseline", "fallback")
#: a challenger result carries one of these modes; recorded, never served (schema enum-bounds it).
CHALLENGER_MODES = ("candidate", "shadow", "canary", "fallback")


def _coverage(handles: Any, baseline_handles: list[str]) -> float:
    """Fraction in [0,1] of the BASELINE's grounding handles this path also grounded on.

    The baseline defines the reference set. With no baseline handles, coverage is 1.0 (nothing to preserve).
    """
    base = set(baseline_handles)
    if not base:
        return 1.0
    have = set(handles or [])
    return len(base & have) / len(base)


def _result_record(
    *,
    path: dict[str, Any],
    result: RunnerResult,
    mode_field: str,
    baseline_handles: list[str],
    run_input_snapshot_hash: str,
) -> dict[str, Any]:
    """Build one per-path result record (baseline or candidate) for the ParallelPathRun.

    source_handles are normalised to a SORTED list (deterministic); coverage is vs the baseline set.
    contract_validation is 'skipped' on error, else the runner-declared validation status (default 'pass').

    input_snapshot_hash is the per-path ATTESTATION of which input the path executed on. The runner may
    declare it; when it does it MUST equal ``run_input_snapshot_hash`` (the single hash the engine computed
    and fed to every path) — a divergent attestation is refused here, at the input. When the runner omits
    it, the engine pins it to the run hash so an honest run is self-consistent by construction.
    """
    handles = sorted(set(result.get("source_handles") or []))
    error = result.get("error")
    if error is not None:
        contract_validation = "skipped"
    else:
        contract_validation = result.get("contract_validation", "pass")
    declared_hash = result.get("input_snapshot_hash")
    if declared_hash is not None and declared_hash != run_input_snapshot_hash:
        raise ValueError(
            f"runner for path {path['path_id']!r} attested input_snapshot_hash {declared_hash!r} but the "
            f"engine fed it {run_input_snapshot_hash!r} — a path that ran on a DIFFERENT input than the run "
            f"snapshot is refused (a different-input comparison is rejected on the INPUT, never promoted)"
        )
    return {
        "path_id": path["path_id"],
        mode_field: path["mode"],
        "output": result.get("output"),
        "output_contract": result.get("output_contract", path.get("output_contract", "")),
        "cost": float(result.get("cost", 0.0)),
        "latency_ms": float(result.get("latency_ms", 0.0)),
        "error": error,
        "source_handle_coverage": _coverage(result.get("source_handles"), baseline_handles),
        "contract_validation": contract_validation,
        "source_handles": handles,
        # per-path input attestation: the input THIS path executed on (== the run hash for an honest run).
        "input_snapshot_hash": run_input_snapshot_hash,
    }


def run_parallel(
    capability_slot: str,
    input_snapshot: Any,
    baseline_path: dict[str, Any],
    candidate_paths: list[dict[str, Any]],
    *,
    runner: Runner,
    now: str,
    validate: bool = True,
) -> dict[str, Any]:
    """Run the baseline + each candidate on the SAME ``input_snapshot``; return a ``ParallelPathRun`` dict.

    - Records ``input_snapshot_hash`` = sha256 of the canonical bytes of ``input_snapshot`` (the proof that
      baseline and every candidate saw IDENTICAL input).
    - Captures each path's output, cost, latency_ms, error, source_handle_coverage (vs the baseline set),
      contract_validation and source_handles.
    - NEVER serves a candidate: ``served_path_id`` is the baseline's path_id and ``candidate_served`` is
      ``False``. The candidate outputs live only in ``candidate_results`` for the comparator to judge.

    The baseline path's mode must be servable (baseline/fallback). ``runner`` performs the actual execution
    so this function stays pure. ``now`` is injected. With ``validate=True`` the result is checked against
    the ParallelPathRun schema before returning (a contract breach raises).
    """
    if baseline_path.get("mode") not in SERVABLE_MODES:
        raise ValueError(
            f"baseline_path.mode must be one of {SERVABLE_MODES} (the served result is never a candidate); "
            f"got {baseline_path.get('mode')!r}"
        )

    input_snapshot_hash = sha256_hex(input_snapshot)

    # baseline FIRST — its source_handles define the reference set every candidate's coverage is measured against.
    baseline_raw = runner(baseline_path, input_snapshot)
    baseline_handles = sorted(set(baseline_raw.get("source_handles") or []))
    baseline_result = _result_record(
        path=baseline_path, result=baseline_raw, mode_field="mode", baseline_handles=baseline_handles,
        run_input_snapshot_hash=input_snapshot_hash,
    )

    candidate_results: list[dict[str, Any]] = []
    for cand in candidate_paths:
        if cand.get("mode") not in CHALLENGER_MODES:
            raise ValueError(
                f"candidate path {cand.get('path_id')!r} mode must be one of {CHALLENGER_MODES}; "
                f"got {cand.get('mode')!r}"
            )
        cand_raw = runner(cand, input_snapshot)
        candidate_results.append(
            _result_record(path=cand, result=cand_raw, mode_field="mode", baseline_handles=baseline_handles,
                           run_input_snapshot_hash=input_snapshot_hash)
        )

    run_id = canonical_id(
        "ppr",
        capability_slot,
        input_snapshot_hash,
        baseline_path["path_id"],
        *[c["path_id"] for c in candidate_paths],
    )

    run: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "capability_slot": capability_slot,
        "input_snapshot_hash": input_snapshot_hash,
        "baseline_result": baseline_result,
        "candidate_results": candidate_results,
        # the served output is ALWAYS the baseline's — a candidate is NEVER served as truth.
        "served_path_id": baseline_path["path_id"],
        "candidate_served": False,
        "ran_at": now,
    }

    if validate:
        errs = _sv.validate_ref(run, f"experiments/{SCHEMA_VERSION}")
        if errs:
            raise ValueError(f"ParallelPathRun failed contract validation: {errs[:5]}")
    return run


def served_output(run: dict[str, Any]) -> dict[str, Any]:
    """Return the ONLY output the engine may serve: the baseline result.

    There is no code path that returns a candidate result here — the served output is structurally the
    baseline's. Callers that need "the answer" call this; they can never reach a candidate's output.
    """
    return run["baseline_result"]
