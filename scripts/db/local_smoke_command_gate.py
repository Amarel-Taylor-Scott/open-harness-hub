#!/usr/bin/env python3
"""Create an approval and dry-run ledger for local smoke-plan commands."""
from __future__ import annotations

import argparse
import hashlib
import json
import shlex
import tempfile
import time
from pathlib import Path
from typing import Any

from scripts._config import DEFAULT_POSTGRES_COMPOSE_FILE, LOCAL_DOCKER_PGVECTOR_COMPONENT_TARGET


DEFAULT_POLICY_PATH = "catalog/knowledge-packs/data/local-smoke-command-policies/policies.jsonl"


def _utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _read_json(path: str | Path) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def _read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_no, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path}:{line_no}: expected JSON object")
        rows.append(value)
    return rows


def _write_json(path: str | Path, payload: dict[str, Any]) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def _command_tokens(command: str) -> list[str]:
    try:
        return shlex.split(command)
    except ValueError:
        return []


def _command_hash(command: str) -> str:
    return "sha256:" + hashlib.sha256(command.encode("utf-8")).hexdigest()


def _policy_for(command: str, policies: list[dict[str, Any]]) -> dict[str, Any]:
    tokens = _command_tokens(command)
    first = tokens[0] if tokens else ""
    for policy in policies:
        prefixes = policy.get("command_prefixes", [])
        if not isinstance(prefixes, list):
            continue
        for prefix in prefixes:
            prefix_tokens = _command_tokens(str(prefix))
            if prefix_tokens and tokens[: len(prefix_tokens)] == prefix_tokens:
                return policy
            if str(prefix) == first:
                return policy
    return {
        "policy_id": "unknown-command",
        "risk": "high",
        "requires_approval": True,
        "allowed_by_default": False,
        "reason": "No command policy matched.",
    }


def build_local_smoke_command_gate(
    *,
    smoke_plan: str | Path,
    output: str | Path | None = None,
    policy_path: str | Path = DEFAULT_POLICY_PATH,
    run_id: str = "local-smoke-command-gate",
) -> dict[str, Any]:
    """Classify smoke-plan commands without executing them."""
    plan = _read_json(smoke_plan)
    policies = _read_jsonl(policy_path)
    commands = plan.get("commands")
    if not isinstance(commands, list):
        raise ValueError("smoke plan must contain commands array")

    command_rows: list[dict[str, Any]] = []
    approval_items: list[dict[str, Any]] = []
    for ordinal, command_entry in enumerate(commands, 1):
        if not isinstance(command_entry, dict):
            continue
        command = str(command_entry.get("command") or "")
        step = str(command_entry.get("step") or f"step-{ordinal:02d}")
        policy = _policy_for(command, policies)
        requires_approval = bool(policy.get("requires_approval", True))
        row = {
            "ordinal": ordinal,
            "step": step,
            "command_hash": _command_hash(command),
            "command": command,
            "tokens": _command_tokens(command),
            "policy_id": policy.get("policy_id", "unknown-command"),
            "risk": policy.get("risk", "high"),
            "allowed_by_default": bool(policy.get("allowed_by_default", False)),
            "requires_approval": requires_approval,
            "execution_status": "not_executed",
            "reason": policy.get("reason", ""),
        }
        command_rows.append(row)
        if requires_approval:
            approval_items.append({
                "ordinal": ordinal,
                "step": step,
                "policy_id": row["policy_id"],
                "risk": row["risk"],
                "approval_required": True,
                "operator_check": policy.get("operator_check", "Review command, destination, and expected side effects."),
            })

    risk_counts: dict[str, int] = {}
    for row in command_rows:
        risk = str(row["risk"])
        risk_counts[risk] = risk_counts.get(risk, 0) + 1

    report = {
        "ok": True,
        "run_id": run_id,
        "generated_at": _utc_now(),
        "smoke_plan": str(smoke_plan),
        "policy_path": str(policy_path),
        "target": plan.get("target", ""),
        "command_count": len(command_rows),
        "risk_counts": risk_counts,
        "approval_required_count": len(approval_items),
        "dry_run_only": True,
        "approval_items": approval_items,
        "execution_ledger": command_rows,
        "safety_notes": [
            "This gate does not execute commands.",
            "Commands that start Docker, mutate Postgres, pipe count output, or run local audit scripts remain operator-reviewed.",
            "Use this ledger before any controlled local execution mode is added.",
        ],
    }
    if output:
        _write_json(output, report)
    return report


def _self_test() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        plan = base / "smoke-plan.json"
        policies = base / "policies.jsonl"
        plan.write_text(
            json.dumps(
                {
                    "target": LOCAL_DOCKER_PGVECTOR_COMPONENT_TARGET,
                    "commands": [
                        {"step": "start", "command": f"docker compose -f {DEFAULT_POSTGRES_COMPOSE_FILE} up -d"},
                        {"step": "schema", "command": "psql \"postgresql://local\" -f db/postgres/schema.sql"},
                        {"step": "audit", "command": "python3 -m scripts.db.staged_vs_committed_load_audit --help"},
                    ],
                }
            ),
            encoding="utf-8",
        )
        policies.write_text(
            "\n".join(
                [
                    json.dumps({"policy_id": "docker-compose", "command_prefixes": ["docker compose"], "risk": "high", "requires_approval": True, "allowed_by_default": False}),
                    json.dumps({"policy_id": "psql", "command_prefixes": ["psql"], "risk": "high", "requires_approval": True, "allowed_by_default": False}),
                    json.dumps({"policy_id": "python-audit", "command_prefixes": ["python3 -m scripts.db.staged_vs_committed_load_audit"], "risk": "medium", "requires_approval": False, "allowed_by_default": True}),
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        result = build_local_smoke_command_gate(smoke_plan=plan, policy_path=policies)
        assert result["command_count"] == 3
        assert result["approval_required_count"] == 2
        assert result["dry_run_only"] is True
    print(json.dumps({"ok": True, "command_count": result["command_count"], "approval_required_count": result["approval_required_count"]}, indent=2, sort_keys=True))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--smoke-plan")
    parser.add_argument("--policy-path", default=DEFAULT_POLICY_PATH)
    parser.add_argument("--output")
    parser.add_argument("--run-id", default="local-smoke-command-gate")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    if not args.smoke_plan:
        parser.error("--smoke-plan is required unless --self-test is used")
    result = build_local_smoke_command_gate(
        smoke_plan=args.smoke_plan,
        policy_path=args.policy_path,
        output=args.output,
        run_id=args.run_id,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
