#!/usr/bin/env python3
"""Create and verify local smoke command approval records."""
from __future__ import annotations

import argparse
import hashlib
import json
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


def _stable_hash(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def build_local_smoke_command_approval_template(
    *,
    command_gate: str | Path,
    output: str | Path | None = None,
    approver_name: str = "operator",
    run_id: str = "local-smoke-command-approval",
) -> dict[str, Any]:
    gate = _read_json(command_gate)
    approvals = []
    for item in gate.get("approval_items", []):
        if not isinstance(item, dict):
            continue
        ordinal = int(item.get("ordinal", 0) or 0)
        command_hash = ""
        for row in gate.get("execution_ledger", []):
            if isinstance(row, dict) and int(row.get("ordinal", -1) or -1) == ordinal:
                command_hash = str(row.get("command_hash") or "")
                break
        approvals.append({
            "ordinal": ordinal,
            "step": item.get("step", ""),
            "command_hash": command_hash,
            "decision": "deferred",
            "reason": "Operator review required before execution.",
            "scope": "single_run",
        })
    record = {
        "approval_id": f"approval/{hashlib.sha256(f'{run_id}:{command_gate}'.encode('utf-8')).hexdigest()[:20]}",
        "run_id": run_id,
        "smoke_plan": gate.get("smoke_plan", ""),
        "command_gate": str(command_gate),
        "approver": {"name": approver_name},
        "created_at": _utc_now(),
        "decisions": approvals,
        "signature": {
            "method": "unsigned-template",
            "value": "",
        },
        "template_hash": "",
    }
    record["template_hash"] = _stable_hash({key: value for key, value in record.items() if key != "template_hash"})
    if output:
        _write_json(output, record)
    return record


def build_local_smoke_selective_approval(
    *,
    command_gate: str | Path,
    approve_steps: list[str],
    output: str | Path | None = None,
    approver_name: str = "operator",
    reason: str = "Approved for this local smoke run.",
    run_id: str = "local-smoke-command-selective-approval",
) -> dict[str, Any]:
    gate = _read_json(command_gate)
    approve_set = set(approve_steps)
    decisions = []
    for row in gate.get("execution_ledger", []):
        if not isinstance(row, dict):
            continue
        step = str(row.get("step") or "")
        if step not in approve_set:
            continue
        decisions.append({
            "ordinal": row.get("ordinal"),
            "step": step,
            "command_hash": row.get("command_hash", ""),
            "decision": "approved",
            "reason": reason,
            "scope": "single_run",
        })
    record = {
        "approval_id": f"approval/{hashlib.sha256(f'{run_id}:{command_gate}:{sorted(approve_set)}'.encode('utf-8')).hexdigest()[:20]}",
        "run_id": run_id,
        "smoke_plan": gate.get("smoke_plan", ""),
        "command_gate": str(command_gate),
        "approver": {"name": approver_name},
        "created_at": _utc_now(),
        "decisions": decisions,
        "signature": {
            "method": "unsigned-local-example",
            "value": "",
        },
        "template_hash": "",
    }
    record["template_hash"] = _stable_hash({key: value for key, value in record.items() if key != "template_hash"})
    if output:
        _write_json(output, record)
    return record


def verify_local_smoke_command_approvals(
    *,
    command_gate: str | Path,
    approval_record: str | Path,
    output: str | Path | None = None,
    run_id: str = "local-smoke-command-approval-verifier",
) -> dict[str, Any]:
    gate = _read_json(command_gate)
    approval = _read_json(approval_record)
    ledger = [row for row in gate.get("execution_ledger", []) if isinstance(row, dict)]
    decisions = {
        str(row.get("command_hash") or ""): row
        for row in approval.get("decisions", [])
        if isinstance(row, dict)
    }
    rows: list[dict[str, Any]] = []
    approved_count = 0
    rejected_count = 0
    missing_count = 0
    for row in ledger:
        command_hash = str(row.get("command_hash") or "")
        decision = decisions.get(command_hash)
        if not decision:
            status = "missing_approval"
            missing_count += 1
        elif decision.get("decision") == "approved":
            status = "approved_for_single_run"
            approved_count += 1
        elif decision.get("decision") == "rejected":
            status = "rejected"
            rejected_count += 1
        else:
            status = "deferred"
        rows.append({
            "ordinal": row.get("ordinal"),
            "step": row.get("step"),
            "command_hash": command_hash,
            "requires_approval": bool(row.get("requires_approval")),
            "policy_id": row.get("policy_id"),
            "risk": row.get("risk"),
            "approval_status": status,
            "reason": decision.get("reason", "") if decision else "",
            "execution_status": "not_executed",
        })
    report = {
        "ok": rejected_count == 0,
        "run_id": run_id,
        "generated_at": _utc_now(),
        "command_gate": str(command_gate),
        "approval_record": str(approval_record),
        "approval_id": approval.get("approval_id", ""),
        "command_count": len(rows),
        "approved_count": approved_count,
        "rejected_count": rejected_count,
        "missing_approval_count": missing_count,
        "rows": rows,
        "safety_notes": [
            "Approval verification does not execute commands.",
            "Approvals are command-hash and run scoped.",
            "A later executor must still enforce destination and command hash checks immediately before execution.",
        ],
    }
    if output:
        _write_json(output, report)
    return report


def _self_test() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        gate = Path(tmp) / "gate.json"
        gate.write_text(json.dumps({
            "smoke_plan": "plan.json",
            "approval_items": [{"ordinal": 1, "step": "apply", "policy_id": "psql", "risk": "high"}],
            "execution_ledger": [
                {"ordinal": 1, "step": "apply", "command_hash": "sha256:abc", "requires_approval": True, "policy_id": "psql", "risk": "high"},
                {"ordinal": 2, "step": "audit", "command_hash": "sha256:def", "requires_approval": False, "policy_id": "audit", "risk": "medium"},
            ],
        }), encoding="utf-8")
        template = build_local_smoke_command_approval_template(command_gate=gate, output=Path(tmp) / "approval.json")
        assert template["decisions"][0]["decision"] == "deferred"
        template["decisions"][0]["decision"] = "approved"
        template["decisions"][0]["reason"] = "Local test approval."
        approved_path = Path(tmp) / "approved.json"
        _write_json(approved_path, template)
        report = verify_local_smoke_command_approvals(command_gate=gate, approval_record=approved_path)
        assert report["approved_count"] == 1
        assert report["missing_approval_count"] == 1
        selective = build_local_smoke_selective_approval(command_gate=gate, approve_steps=["audit"])
        assert selective["decisions"][0]["command_hash"] == "sha256:def"
    print(json.dumps({"ok": True, "approved_count": report["approved_count"]}, indent=2, sort_keys=True))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--command-gate")
    parser.add_argument("--approval-record")
    parser.add_argument("--output")
    parser.add_argument("--run-id", default="local-smoke-command-approval")
    parser.add_argument("--approver-name", default="operator")
    parser.add_argument("--mode", choices=["template", "verify", "selective"], default="template")
    parser.add_argument("--approve-step", action="append", default=[])
    parser.add_argument("--reason", default="Approved for this local smoke run.")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    if not args.command_gate:
        parser.error("--command-gate is required unless --self-test is used")
    if args.mode == "template":
        result = build_local_smoke_command_approval_template(
            command_gate=args.command_gate,
            output=args.output,
            approver_name=args.approver_name,
            run_id=args.run_id,
        )
    elif args.mode == "selective":
        if not args.approve_step:
            parser.error("--approve-step is required in selective mode")
        result = build_local_smoke_selective_approval(
            command_gate=args.command_gate,
            approve_steps=args.approve_step,
            output=args.output,
            approver_name=args.approver_name,
            reason=args.reason,
            run_id=args.run_id,
        )
    else:
        if not args.approval_record:
            parser.error("--approval-record is required in verify mode")
        result = verify_local_smoke_command_approvals(
            command_gate=args.command_gate,
            approval_record=args.approval_record,
            output=args.output,
            run_id=args.run_id,
        )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
