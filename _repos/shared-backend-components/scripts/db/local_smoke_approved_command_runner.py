#!/usr/bin/env python3
"""Plan or run approved low-risk commands from a local smoke command gate."""
from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any


def _utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _read_json(path: str | Path) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def _write_json(path: str | Path, payload: dict[str, Any]) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def _eligible(row: dict[str, Any]) -> bool:
    return bool(row.get("allowed_by_default")) and not bool(row.get("requires_approval"))


def _approved_hashes(path: str | Path | None) -> dict[str, dict[str, Any]]:
    if not path:
        return {}
    approval = _read_json(path)
    out: dict[str, dict[str, Any]] = {}
    for row in approval.get("decisions", []):
        if not isinstance(row, dict):
            continue
        if row.get("decision") == "approved":
            command_hash = str(row.get("command_hash") or "")
            if command_hash:
                out[command_hash] = row
    return out


def _run_command(command: str, timeout_seconds: int) -> dict[str, Any]:
    started = _utc_now()
    try:
        completed = subprocess.run(
            command,
            shell=True,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
        return {
            "started_at": started,
            "finished_at": _utc_now(),
            "returncode": completed.returncode,
            "stdout": completed.stdout[-4000:],
            "stderr": completed.stderr[-4000:],
            "timed_out": False,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "started_at": started,
            "finished_at": _utc_now(),
            "returncode": None,
            "stdout": (exc.stdout or "")[-4000:] if isinstance(exc.stdout, str) else "",
            "stderr": (exc.stderr or "")[-4000:] if isinstance(exc.stderr, str) else "",
            "timed_out": True,
        }


def build_or_run_approved_local_smoke_commands(
    *,
    command_gate: str | Path,
    approval_record: str | Path | None = None,
    output: str | Path | None = None,
    run_id: str = "local-smoke-approved-command-runner",
    execute: bool = False,
    require_approval_record: bool = False,
    timeout_seconds: int = 30,
) -> dict[str, Any]:
    """Create an execution ledger, optionally running only policy-approved commands."""
    gate = _read_json(command_gate)
    approved_hashes = _approved_hashes(approval_record)
    ledger = gate.get("execution_ledger")
    if not isinstance(ledger, list):
        raise ValueError("command gate must contain execution_ledger array")

    rows: list[dict[str, Any]] = []
    blocked_count = 0
    eligible_count = 0
    executed_count = 0
    failed_count = 0
    for raw in ledger:
        if not isinstance(raw, dict):
            continue
        command = str(raw.get("command") or "")
        command_hash = str(raw.get("command_hash") or "")
        policy_eligible = _eligible(raw)
        approval = approved_hashes.get(command_hash)
        approval_eligible = bool(approval)
        eligible = approval_eligible if require_approval_record else (policy_eligible or approval_eligible)
        if not eligible:
            status = "blocked_requires_approval"
        elif approval_eligible and (require_approval_record or not policy_eligible):
            status = "planned_operator_approved"
        else:
            status = "planned_policy_approved"
        if eligible:
            eligible_count += 1
        else:
            blocked_count += 1
        execution: dict[str, Any] = {}
        if execute and eligible:
            execution = _run_command(command, timeout_seconds=timeout_seconds)
            executed_count += 1
            status = "executed_ok" if execution.get("returncode") == 0 and not execution.get("timed_out") else "executed_failed"
            if status == "executed_failed":
                failed_count += 1
        rows.append({
            "ordinal": raw.get("ordinal"),
            "step": raw.get("step"),
            "command_hash": command_hash,
            "command": command,
            "policy_id": raw.get("policy_id"),
            "risk": raw.get("risk"),
            "eligible_for_unattended_execution": eligible,
            "policy_eligible": policy_eligible,
            "approval_eligible": approval_eligible,
            "approval_reason": approval.get("reason", "") if approval else "",
            "approval_record_required": require_approval_record,
            "status": status,
            "execution": execution,
        })

    report = {
        "ok": failed_count == 0,
        "run_id": run_id,
        "generated_at": _utc_now(),
        "command_gate": str(command_gate),
        "approval_record": str(approval_record) if approval_record else "",
        "approval_record_required": require_approval_record,
        "mode": "execute_approved" if execute else "plan_only",
        "timeout_seconds": timeout_seconds,
        "command_count": len(rows),
        "eligible_count": eligible_count,
        "blocked_count": blocked_count,
        "executed_count": executed_count,
        "failed_count": failed_count,
        "rows": rows,
        "safety_notes": [
            "Commands requiring approval are eligible only when a matching approved command hash is supplied.",
            "When approval-record-required mode is enabled, even policy-approved commands need an approved command hash.",
            "Docker and psql mutation commands remain blocked unless a run-scoped approval record explicitly approves their command hashes.",
            "Plan-only mode is the default and does not execute anything.",
        ],
    }
    if output:
        _write_json(output, report)
    return report


def _self_test() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        gate = Path(tmp) / "gate.json"
        gate.write_text(
            json.dumps(
                {
                    "execution_ledger": [
                        {
                            "ordinal": 1,
                            "step": "blocked",
                            "command": "python3 -c 'print(\"approved-blocked\")'",
                            "command_hash": "sha256:blocked",
                            "policy_id": "psql",
                            "risk": "high",
                            "allowed_by_default": False,
                            "requires_approval": True,
                        },
                        {
                            "ordinal": 2,
                            "step": "approved",
                            "command": "python3 -c 'print(\"ok\")'",
                            "command_hash": "sha256:approved",
                            "policy_id": "python-audit",
                            "risk": "medium",
                            "allowed_by_default": True,
                            "requires_approval": False,
                        },
                    ]
                }
            ),
            encoding="utf-8",
        )
        approval = Path(tmp) / "approval.json"
        approval.write_text(
            json.dumps({
                "decisions": [
                    {
                        "command_hash": "sha256:blocked",
                        "decision": "approved",
                        "reason": "Self-test approval.",
                    }
                ]
            }),
            encoding="utf-8",
        )
        planned = build_or_run_approved_local_smoke_commands(command_gate=gate)
        assert planned["eligible_count"] == 1
        assert planned["blocked_count"] == 1
        assert planned["executed_count"] == 0
        executed = build_or_run_approved_local_smoke_commands(command_gate=gate, execute=True)
        assert executed["executed_count"] == 1
        assert executed["failed_count"] == 0
        assert executed["rows"][0]["status"] == "blocked_requires_approval"
        approved_plan = build_or_run_approved_local_smoke_commands(command_gate=gate, approval_record=approval)
        assert approved_plan["eligible_count"] == 2
        assert approved_plan["blocked_count"] == 0
        approved_exec = build_or_run_approved_local_smoke_commands(command_gate=gate, approval_record=approval, execute=True)
        assert approved_exec["executed_count"] == 2
        assert approved_exec["failed_count"] == 0
        strict_plan = build_or_run_approved_local_smoke_commands(command_gate=gate, approval_record=approval, require_approval_record=True)
        assert strict_plan["eligible_count"] == 1
        assert strict_plan["blocked_count"] == 1
        assert strict_plan["rows"][1]["status"] == "blocked_requires_approval"
        strict_exec = build_or_run_approved_local_smoke_commands(command_gate=gate, approval_record=approval, require_approval_record=True, execute=True)
        assert strict_exec["executed_count"] == 1
        assert strict_exec["failed_count"] == 0
    print(json.dumps({"ok": True, "eligible_count": approved_plan["eligible_count"], "executed_count": approved_exec["executed_count"]}, indent=2, sort_keys=True))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--command-gate")
    parser.add_argument("--approval-record")
    parser.add_argument("--output")
    parser.add_argument("--run-id", default="local-smoke-approved-command-runner")
    parser.add_argument("--execute-approved", action="store_true")
    parser.add_argument("--require-approval-record", action="store_true")
    parser.add_argument("--timeout-seconds", type=int, default=30)
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    if not args.command_gate:
        parser.error("--command-gate is required unless --self-test is used")
    result = build_or_run_approved_local_smoke_commands(
        command_gate=args.command_gate,
        approval_record=args.approval_record,
        output=args.output,
        run_id=args.run_id,
        execute=args.execute_approved,
        require_approval_record=args.require_approval_record,
        timeout_seconds=args.timeout_seconds,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
