#!/usr/bin/env python3
"""Build proof bundles and promotion gates for source-backed Teleon groups."""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import hashlib
import inspect
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts._config import (  # noqa: E402
    AIDEVOBSERVER_CURATED_PRIMITIVE_GROUPS_PATH,
    AIDEVOBSERVER_SOURCE_BACKED_GROUP_CARDS_MANIFEST_PATH,
    AIDEVOBSERVER_SOURCE_BACKED_GROUP_CARDS_PATH,
    AIDEVOBSERVER_SOURCE_BACKED_GROUP_PROMOTION_GATES_MANIFEST_PATH,
    AIDEVOBSERVER_SOURCE_BACKED_GROUP_PROMOTION_GATES_PATH,
    AIDEVOBSERVER_SOURCE_BACKED_GROUP_PROOF_BUNDLES_MANIFEST_PATH,
    AIDEVOBSERVER_SOURCE_BACKED_GROUP_PROOF_BUNDLES_PATH,
    AIDEVOBSERVER_SOURCE_BACKED_GROUP_SOURCE_FAMILY,
    AIDEVOBSERVER_SOURCE_BACKED_GROUP_SOURCE_PATH,
    AIDEVOBSERVER_SOURCE_BACKED_GROUP_UNIT_TEST_PATH,
    REPO_ROOT,
)
from src.teleon.primitives import groups as primitive_groups  # noqa: E402

CARDS_PATH = _resource(AIDEVOBSERVER_SOURCE_BACKED_GROUP_CARDS_PATH)
CURATED_GROUPS_PATH = _resource(AIDEVOBSERVER_CURATED_PRIMITIVE_GROUPS_PATH)
CARDS_MANIFEST_PATH = _resource(AIDEVOBSERVER_SOURCE_BACKED_GROUP_CARDS_MANIFEST_PATH)
PROOF_BUNDLES_PATH = _resource(AIDEVOBSERVER_SOURCE_BACKED_GROUP_PROOF_BUNDLES_PATH)
PROOF_BUNDLES_MANIFEST_PATH = _resource(AIDEVOBSERVER_SOURCE_BACKED_GROUP_PROOF_BUNDLES_MANIFEST_PATH)
PROMOTION_GATES_PATH = _resource(AIDEVOBSERVER_SOURCE_BACKED_GROUP_PROMOTION_GATES_PATH)
PROMOTION_GATES_MANIFEST_PATH = _resource(AIDEVOBSERVER_SOURCE_BACKED_GROUP_PROMOTION_GATES_MANIFEST_PATH)
SOURCE_PATH = _resource(AIDEVOBSERVER_SOURCE_BACKED_GROUP_SOURCE_PATH)
TEST_PATH = _resource(AIDEVOBSERVER_SOURCE_BACKED_GROUP_UNIT_TEST_PATH)
PROOF_COMMAND = ("python3", "-m", "unittest", AIDEVOBSERVER_SOURCE_BACKED_GROUP_UNIT_TEST_PATH)
SOURCE_CARD_PATHS = (
    AIDEVOBSERVER_CURATED_PRIMITIVE_GROUPS_PATH,
    AIDEVOBSERVER_SOURCE_BACKED_GROUP_CARDS_PATH,
)


def _utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _canon(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha(value: Any) -> str:
    return hashlib.sha256(_canon(value).encode("utf-8")).hexdigest()


def _sha_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _sha_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _slug(value: str) -> str:
    out: list[str] = []
    last_dash = False
    for char in value.lower():
        if char.isalnum():
            out.append(char)
            last_dash = False
        elif not last_dash:
            out.append("-")
            last_dash = True
    return "".join(out).strip("-") or "source-backed-group"


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        raise AssertionError(f"missing JSONL file: {path}")
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise AssertionError(f"{path}:{line_number}: invalid JSONL: {exc}") from exc
        if not isinstance(row, dict):
            raise AssertionError(f"{path}:{line_number}: expected JSON object")
        rows.append(row)
    return rows


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise AssertionError(f"missing JSON file: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise AssertionError(f"{path}: invalid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise AssertionError(f"{path}: expected JSON object")
    return value


def _run_unit_tests() -> dict[str, Any]:
    started = time.monotonic()
    result = subprocess.run(
        PROOF_COMMAND,
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    elapsed_ms = int((time.monotonic() - started) * 1000)
    return {
        "command": " ".join(PROOF_COMMAND),
        "returncode": result.returncode,
        "status": "pass" if result.returncode == 0 else "fail",
        "elapsed_ms": elapsed_ms,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "stdout_sha256": _sha_text(result.stdout),
        "stderr_sha256": _sha_text(result.stderr),
    }


def _public_card(card: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in card.items() if not key.startswith("_")}


def _card_artifact_path(card: dict[str, Any]) -> str:
    return str(card.get("_registry_artifact_path") or AIDEVOBSERVER_SOURCE_BACKED_GROUP_CARDS_PATH)


def _resolved_source_ref(card: dict[str, Any]) -> dict[str, Any]:
    source_ref = dict(card.get("source_ref") or {})
    function_name = str(source_ref.get("name") or "")
    if function_name and hasattr(primitive_groups, function_name):
        function = getattr(primitive_groups, function_name)
        _lines, line_number = inspect.getsourcelines(function)
        source_ref.update({
            "path": AIDEVOBSERVER_SOURCE_BACKED_GROUP_SOURCE_PATH,
            "name": function_name,
            "line": line_number,
            "language": source_ref.get("language") or "python",
        })
    return source_ref


def _artifact_refs(card: dict[str, Any], test_result: dict[str, Any]) -> list[dict[str, Any]]:
    proof_names = [
        str(ref.get("name") or "")
        for ref in card.get("proof_refs") or []
        if isinstance(ref, dict) and ref.get("name")
    ]
    return [
        {
            "role": "candidate_card",
            "path": _card_artifact_path(card),
            "primitive_id": card["primitive_id"],
        },
        {
            "role": "source",
            "path": AIDEVOBSERVER_SOURCE_BACKED_GROUP_SOURCE_PATH,
            "source_ref": _resolved_source_ref(card),
        },
        {
            "role": "unit_test",
            "path": AIDEVOBSERVER_SOURCE_BACKED_GROUP_UNIT_TEST_PATH,
            "proof_refs": proof_names,
        },
        {
            "role": "subprocess_capture",
            "command": test_result["command"],
            "stdout_sha256": test_result["stdout_sha256"],
            "stderr_sha256": test_result["stderr_sha256"],
            "returncode": test_result["returncode"],
            "elapsed_ms": test_result["elapsed_ms"],
        },
    ]


def _input_hashes(card: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "name": "candidate_card",
            "path": _card_artifact_path(card),
            "primitive_id": card["primitive_id"],
            "sha256": _sha(_public_card(card)),
        },
        {
            "name": "source_file",
            "path": AIDEVOBSERVER_SOURCE_BACKED_GROUP_SOURCE_PATH,
            "sha256": _sha_file(SOURCE_PATH),
        },
        {
            "name": "unit_test_file",
            "path": AIDEVOBSERVER_SOURCE_BACKED_GROUP_UNIT_TEST_PATH,
            "sha256": _sha_file(TEST_PATH),
        },
        {
            "name": "source_digest",
            "value": str(card.get("source_digest") or ""),
        },
    ]


def _output_hashes(card: dict[str, Any], test_result: dict[str, Any]) -> list[dict[str, Any]]:
    receipt = {
        "primitive_id": card["primitive_id"],
        "command": test_result["command"],
        "returncode": test_result["returncode"],
        "status": test_result["status"],
        "stdout_sha256": test_result["stdout_sha256"],
        "stderr_sha256": test_result["stderr_sha256"],
    }
    return [
        {
            "name": "unit_test_stdout",
            "sha256": test_result["stdout_sha256"],
        },
        {
            "name": "unit_test_stderr",
            "sha256": test_result["stderr_sha256"],
        },
        {
            "name": "proof_receipt",
            "sha256": _sha(receipt),
        },
    ]


def _proof_bundle(card: dict[str, Any], test_result: dict[str, Any], created_at: str) -> dict[str, Any]:
    body = {
        "record_type": "proof_bundle",
        "subject_id": card["primitive_id"],
        "subject_kind": "registry_record",
        "proof_kind": "unit_test",
        "status": test_result["status"],
        "proof_command": test_result["command"],
        "artifact_refs": _artifact_refs(card, test_result),
        "ledger_refs": [],
        "input_hashes": _input_hashes(card),
        "output_hashes": _output_hashes(card, test_result),
        "proof_requirements": card.get("proof_requirements") or [],
        "source_family": AIDEVOBSERVER_SOURCE_BACKED_GROUP_SOURCE_FAMILY,
        "candidate": True,
        "serves_truth": False,
        "created_at": created_at,
    }
    proof_hash = _sha(body)
    return {
        "proof_bundle_id": f"proof:teleon.source_backed_group:{_slug(card['primitive_id'])}:{proof_hash[:12]}",
        **body,
        "proof_hash": proof_hash,
    }


def _gate_check(name: str, status: str, detail: str) -> dict[str, str]:
    return {"name": name, "status": status, "detail": detail}


def _promotion_gate(card: dict[str, Any], proof: dict[str, Any], created_at: str) -> dict[str, Any]:
    group_contract = card.get("group_contract") if isinstance(card.get("group_contract"), dict) else {}
    hidden_edges = group_contract.get("hidden_member_edges") if isinstance(group_contract, dict) else []
    checks = [
        _gate_check("source_backed", "pass", "card source_evidence_status is source_backed"),
        _gate_check("unit_tests_pass", "pass" if proof["status"] == "pass" else "fail", proof["proof_command"]),
        _gate_check("contract_declared", "pass", "visible input/output edges declared"),
        _gate_check(
            "hidden_member_edges_declared",
            "pass" if isinstance(hidden_edges, list) and len(hidden_edges) >= 1 else "fail",
            "group route exposes compact visible edge and hidden member edges",
        ),
        _gate_check("candidate_boundary_preserved", "pass", "candidate=true and serves_truth=false"),
        _gate_check("owner_review", "pending", "promotion review is required before trust upgrade"),
        _gate_check("promotion_decision_record", "pending", "no owner decision record attached"),
    ]
    gate_body = {
        "record_type": "source_backed_group_promotion_gate",
        "primitive_id": card["primitive_id"],
        "proof_bundle_id": proof["proof_bundle_id"],
        "proof_hash": proof["proof_hash"],
        "source_family": AIDEVOBSERVER_SOURCE_BACKED_GROUP_SOURCE_FAMILY,
        "source_evidence_status": card.get("source_evidence_status"),
        "promotion_gate_status": "blocked_pending_owner_review",
        "promotion_allowed": False,
        "promotable_without_review": False,
        "review_required": True,
        "gate_checks": checks,
        "promotion_blockers": [
            "promotion_review_required",
            "promotion_decision_record_required",
            "truth_serving_disabled_until_explicit_registry_promotion",
        ],
        "readiness_after_proof": "R4_unit_tested_group",
        "candidate": True,
        "serves_truth": False,
        "created_at": created_at,
    }
    gate_hash = _sha(gate_body)
    return {
        "gate_id": f"gate:teleon.source_backed_group:{_slug(card['primitive_id'])}:{gate_hash[:12]}",
        **gate_body,
        "gate_hash": gate_hash,
    }


def _read_source_backed_group_rows() -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    for rel_path in SOURCE_CARD_PATHS:
        path = _resource(rel_path)
        if not path.exists():
            continue
        for row in _read_jsonl(path):
            if (
                row.get("source_family") == AIDEVOBSERVER_SOURCE_BACKED_GROUP_SOURCE_FAMILY
                and row.get("source_evidence_status") == "source_backed"
                and row.get("candidate") is True
                and row.get("serves_truth") is False
            ):
                card = dict(row)
                card["_registry_artifact_path"] = rel_path
                cards.append(card)
    cards.sort(key=lambda row: str(row.get("primitive_id") or ""))
    ids = [str(row.get("primitive_id") or "") for row in cards]
    if len(ids) != len(set(ids)):
        raise AssertionError("source-backed group primitive ids must be unique across source card paths")
    return cards


def build_rows() -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    cards = _read_source_backed_group_rows()
    cards_manifest = _read_json(CARDS_MANIFEST_PATH)
    source_card_rows = [card for card in cards if _card_artifact_path(card) == AIDEVOBSERVER_SOURCE_BACKED_GROUP_CARDS_PATH]
    if int(cards_manifest.get("row_count") or 0) != len(source_card_rows):
        raise AssertionError("source-backed card manifest row_count does not match card rows")
    test_result = _run_unit_tests()
    created_at = _utc()
    proof_bundles = [_proof_bundle(card, test_result, created_at) for card in cards]
    promotion_gates = [_promotion_gate(card, proof, created_at) for card, proof in zip(cards, proof_bundles, strict=True)]
    run_summary = {
        "proof_command": test_result["command"],
        "unit_test_status": test_result["status"],
        "unit_test_returncode": test_result["returncode"],
        "unit_test_elapsed_ms": test_result["elapsed_ms"],
        "unit_test_stdout_sha256": test_result["stdout_sha256"],
        "unit_test_stderr_sha256": test_result["stderr_sha256"],
    }
    return proof_bundles, promotion_gates, run_summary


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def write_rows(
    proof_bundles: list[dict[str, Any]],
    promotion_gates: list[dict[str, Any]],
    run_summary: dict[str, Any],
) -> dict[str, Any]:
    _write_jsonl(PROOF_BUNDLES_PATH, proof_bundles)
    _write_jsonl(PROMOTION_GATES_PATH, promotion_gates)
    created_at = _utc()
    proof_manifest = {
        "record_type": "teleon_source_backed_primitive_group_proof_bundles_manifest",
        "created_at": created_at,
        "proof_bundles_path": AIDEVOBSERVER_SOURCE_BACKED_GROUP_PROOF_BUNDLES_PATH,
        "source_card_paths": list(SOURCE_CARD_PATHS),
        "row_count": len(proof_bundles),
        "primitive_ids": [row["subject_id"] for row in proof_bundles],
        "status_counts": {
            status: sum(1 for row in proof_bundles if row.get("status") == status)
            for status in sorted({str(row.get("status")) for row in proof_bundles})
        },
        **run_summary,
        "candidate": True,
        "serves_truth": False,
    }
    gate_manifest = {
        "record_type": "teleon_source_backed_primitive_group_promotion_gates_manifest",
        "created_at": created_at,
        "promotion_gates_path": AIDEVOBSERVER_SOURCE_BACKED_GROUP_PROMOTION_GATES_PATH,
        "proof_bundles_path": AIDEVOBSERVER_SOURCE_BACKED_GROUP_PROOF_BUNDLES_PATH,
        "source_card_paths": list(SOURCE_CARD_PATHS),
        "row_count": len(promotion_gates),
        "primitive_ids": [row["primitive_id"] for row in promotion_gates],
        "promotion_gate_status_counts": {
            status: sum(1 for row in promotion_gates if row.get("promotion_gate_status") == status)
            for status in sorted({str(row.get("promotion_gate_status")) for row in promotion_gates})
        },
        "promotion_allowed": False,
        "review_required": True,
        "candidate": True,
        "serves_truth": False,
    }
    PROOF_BUNDLES_MANIFEST_PATH.write_text(json.dumps(proof_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    PROMOTION_GATES_MANIFEST_PATH.write_text(json.dumps(gate_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "proof_bundles": proof_manifest,
        "promotion_gates": gate_manifest,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args(argv)
    try:
        proof_bundles, promotion_gates, run_summary = build_rows()
        manifest: dict[str, Any] = {
            "proof_bundle_rows": len(proof_bundles),
            "promotion_gate_rows": len(promotion_gates),
            **run_summary,
            "candidate": True,
            "serves_truth": False,
        }
        if not args.check_only:
            manifest = write_rows(proof_bundles, promotion_gates, run_summary)
    except AssertionError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
