#!/usr/bin/env python3
"""Build a resumable stage ledger for daily component factory runs."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import tempfile
from pathlib import Path
from typing import Any


DEFAULT_STAGE_CONTRACTS = "catalog/knowledge-packs/data/daily-factory-stage-contracts/stages.jsonl"


def _utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path}:{line_no}: expected JSON object")
        records.append(value)
    return records


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def _format_template(value: str, *, run_dir: Path, run_date: str, run_id: str) -> str:
    return value.format(run_dir=str(run_dir), run_date=run_date, run_id=run_id)


def _resolve_path(value: str, *, run_dir: Path, run_date: str, run_id: str) -> Path:
    rendered = _format_template(value, run_dir=run_dir, run_date=run_date, run_id=run_id)
    path = Path(rendered)
    if path.is_absolute():
        return path
    return (run_dir / path).resolve()


def _stage_summary_path(
    contract: dict[str, Any],
    *,
    run_dir: Path,
    run_date: str,
    run_id: str,
    daily_summary: dict[str, Any],
) -> Path | None:
    paths = daily_summary.get("paths") if isinstance(daily_summary.get("paths"), dict) else {}
    summary_path_key = str(contract.get("summary_path_key") or "")
    if summary_path_key and summary_path_key in paths:
        raw = str(paths[summary_path_key])
        path = Path(raw)
        return path if path.is_absolute() else path.resolve()

    expected = str(contract.get("expected_path") or "")
    if expected:
        return _resolve_path(expected, run_dir=run_dir, run_date=run_date, run_id=run_id)
    return None


def _load_stage_json(path: Path | None) -> tuple[dict[str, Any] | None, str | None]:
    if path is None:
        return None, "no_summary_path"
    if not path.exists():
        return None, "missing_summary"
    try:
        return _read_json(path), None
    except (json.JSONDecodeError, ValueError) as exc:
        return None, str(exc)


def _skip_reason(contract: dict[str, Any], daily_summary: dict[str, Any]) -> str | None:
    stage_id = str(contract.get("stage_id") or "")
    if stage_id == "gap_fill":
        coverage = daily_summary.get("coverage") if isinstance(daily_summary.get("coverage"), dict) else {}
        if int(coverage.get("missing_request_count") or 0) == 0:
            return "coverage reported no missing component requests"
    return None


def _stage_status(
    contract: dict[str, Any],
    *,
    run_dir: Path,
    run_date: str,
    run_id: str,
    daily_summary: dict[str, Any],
    completed_stage_ids: set[str],
) -> dict[str, Any]:
    stage_id = str(contract.get("stage_id") or "")
    prerequisites = [str(value) for value in contract.get("prerequisite_stage_ids", [])]
    blocked_by = [stage for stage in prerequisites if stage not in completed_stage_ids]
    summary_path = _stage_summary_path(
        contract,
        run_dir=run_dir,
        run_date=run_date,
        run_id=run_id,
        daily_summary=daily_summary,
    )
    stage_json, error = _load_stage_json(summary_path)
    skip_reason = _skip_reason(contract, daily_summary)

    if skip_reason:
        status = "skipped"
        ok = True
    elif blocked_by:
        status = "blocked"
        ok = False
    elif stage_json is not None:
        ok = bool(stage_json.get("ok", True))
        status = "complete" if ok else "failed"
    else:
        ok = False
        status = "missing"

    resume_template = str(contract.get("resume_command_template") or "")
    resume_command = (
        _format_template(resume_template, run_dir=run_dir, run_date=run_date, run_id=run_id)
        if resume_template
        else ""
    )
    if summary_path is not None and "{summary_path}" in resume_command:
        resume_command = resume_command.replace("{summary_path}", str(summary_path))

    return {
        "stage_id": stage_id,
        "name": contract.get("name", stage_id),
        "status": status,
        "ok": ok,
        "summary_path": str(summary_path) if summary_path else "",
        "summary_exists": bool(summary_path and summary_path.exists()),
        "prerequisite_stage_ids": prerequisites,
        "blocked_by": blocked_by,
        "required_for_closeout": bool(contract.get("required_for_closeout", True)),
        "resume_command": resume_command,
        "skip_reason": skip_reason or "",
        "error": error or "",
    }


def build_daily_stage_ledger(
    *,
    run_dir: str | Path,
    stage_contract_path: str | Path = DEFAULT_STAGE_CONTRACTS,
    output_path: str | Path | None = None,
) -> dict[str, Any]:
    """Inspect a daily run directory and emit resumable stage state."""
    run_dir_path = Path(run_dir).resolve()
    daily_summary_path = run_dir_path / "daily-production-run-summary.json"
    daily_summary = _read_json(daily_summary_path) if daily_summary_path.exists() else {}
    run_date = str(daily_summary.get("run_date") or run_dir_path.name)
    run_id = str(daily_summary.get("run_id") or f"daily-production-{run_date}")
    contracts = _read_jsonl(Path(stage_contract_path))

    stages: list[dict[str, Any]] = []
    completed_stage_ids: set[str] = set()
    for contract in contracts:
        stage = _stage_status(
            contract,
            run_dir=run_dir_path,
            run_date=run_date,
            run_id=run_id,
            daily_summary=daily_summary,
            completed_stage_ids=completed_stage_ids,
        )
        stages.append(stage)
        if stage["status"] in {"complete", "skipped"} and stage["ok"]:
            completed_stage_ids.add(stage["stage_id"])

    status_counts: dict[str, int] = {}
    for stage in stages:
        status = str(stage["status"])
        status_counts[status] = status_counts.get(status, 0) + 1

    next_stage = next(
        (
            stage
            for stage in stages
            if stage["status"] in {"missing", "failed", "blocked"} and stage["required_for_closeout"]
        ),
        None,
    )
    closeout_ready = all(
        stage["status"] in {"complete", "skipped"} for stage in stages if stage["required_for_closeout"]
    )
    ledger = {
        "version": "0.1.0",
        "generated_at": _utc_now(),
        "ok": closeout_ready,
        "run_dir": str(run_dir_path),
        "run_date": run_date,
        "run_id": run_id,
        "daily_summary_path": str(daily_summary_path),
        "daily_summary_exists": daily_summary_path.exists(),
        "stage_contract_path": str(stage_contract_path),
        "stage_count": len(stages),
        "status_counts": status_counts,
        "closeout_ready": closeout_ready,
        "next_stage": next_stage or {},
        "resume_actions": [
            {
                "stage_id": stage["stage_id"],
                "status": stage["status"],
                "command": stage["resume_command"],
                "blocked_by": stage["blocked_by"],
            }
            for stage in stages
            if stage["status"] in {"missing", "failed", "blocked"} and stage["resume_command"]
        ],
        "stages": stages,
        "notes": [
            "The ledger is an audit and resume planner; it does not execute generation, load SQL, or mutate Postgres.",
            "Stages marked complete are proven only by the presence and parseability of their stage summary files plus ok=true where available.",
            "Operator approval is still required before applying emitted SQL or promoting candidates.",
        ],
    }
    if output_path:
        _write_json(Path(output_path), ledger)
    return ledger


def _self_test() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        contracts = base / "stages.jsonl"
        contracts.write_text(
            "\n".join(
                json.dumps(row, sort_keys=True)
                for row in [
                    {
                        "stage_id": "component_generation",
                        "name": "Component generation",
                        "summary_path_key": "component_summary",
                        "required_for_closeout": True,
                        "resume_command_template": "generate-components {run_date}",
                    },
                    {
                        "stage_id": "coverage_audit",
                        "name": "Coverage audit",
                        "summary_path_key": "coverage_summary",
                        "prerequisite_stage_ids": ["component_generation"],
                        "required_for_closeout": True,
                        "resume_command_template": "coverage {run_dir}",
                    },
                    {
                        "stage_id": "gap_fill",
                        "name": "Gap fill",
                        "summary_path_key": "gap_summary",
                        "prerequisite_stage_ids": ["coverage_audit"],
                        "required_for_closeout": False,
                        "resume_command_template": "gap-fill {run_dir}",
                    },
                    {
                        "stage_id": "load_audit",
                        "name": "Load audit",
                        "summary_path_key": "load_audit_summary",
                        "prerequisite_stage_ids": ["coverage_audit"],
                        "required_for_closeout": True,
                        "resume_command_template": "load-audit {run_dir}",
                    },
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        run_dir = base / "2026-05-26"
        component_summary = run_dir / "component-batch" / "daily-thousand-component-batch.json"
        coverage_summary = run_dir / "showcase-coverage" / "showcase-candidate-coverage-summary.json"
        load_audit_summary = run_dir / "load-audit" / "summary.json"
        for path in [component_summary, coverage_summary, load_audit_summary]:
            _write_json(path, {"ok": True})
        _write_json(
            run_dir / "daily-production-run-summary.json",
            {
                "ok": True,
                "run_date": "2026-05-26",
                "run_id": "daily-production-2026-05-26",
                "coverage": {"missing_request_count": 0},
                "paths": {
                    "component_summary": str(component_summary),
                    "coverage_summary": str(coverage_summary),
                    "gap_summary": str(run_dir / "showcase-gap-components" / "showcase-gap-component-summary.json"),
                    "load_audit_summary": str(load_audit_summary),
                },
            },
        )
        result = build_daily_stage_ledger(run_dir=run_dir, stage_contract_path=contracts)
        assert result["ok"] is True
        assert result["status_counts"]["complete"] == 3
        assert result["status_counts"]["skipped"] == 1
        assert result["closeout_ready"] is True
    print("ok")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--run-dir")
    parser.add_argument("--stage-contract-path", default=DEFAULT_STAGE_CONTRACTS)
    parser.add_argument("--output")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    if not args.run_dir:
        parser.error("--run-dir is required unless --self-test is set")
    result = build_daily_stage_ledger(
        run_dir=args.run_dir,
        stage_contract_path=args.stage_contract_path,
        output_path=args.output,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["daily_summary_exists"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
