#!/usr/bin/env python3
"""Validate source-backed Teleon proof bundles and promotion gates."""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import hashlib
import json
import sys
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
    AIDEVOBSERVER_SOURCE_BACKED_GROUP_UNIT_TEST_PATH,
    REPO_ROOT,
)

CARDS_PATH = _resource(AIDEVOBSERVER_SOURCE_BACKED_GROUP_CARDS_PATH)
CURATED_GROUPS_PATH = _resource(AIDEVOBSERVER_CURATED_PRIMITIVE_GROUPS_PATH)
CARDS_MANIFEST_PATH = _resource(AIDEVOBSERVER_SOURCE_BACKED_GROUP_CARDS_MANIFEST_PATH)
PROOF_BUNDLES_PATH = _resource(AIDEVOBSERVER_SOURCE_BACKED_GROUP_PROOF_BUNDLES_PATH)
PROOF_BUNDLES_MANIFEST_PATH = _resource(AIDEVOBSERVER_SOURCE_BACKED_GROUP_PROOF_BUNDLES_MANIFEST_PATH)
PROMOTION_GATES_PATH = _resource(AIDEVOBSERVER_SOURCE_BACKED_GROUP_PROMOTION_GATES_PATH)
PROMOTION_GATES_MANIFEST_PATH = _resource(AIDEVOBSERVER_SOURCE_BACKED_GROUP_PROMOTION_GATES_MANIFEST_PATH)

REQUIRED_PROOF_FIELDS: tuple[str, ...] = (
    "proof_bundle_id",
    "subject_id",
    "subject_kind",
    "proof_kind",
    "status",
    "proof_command",
    "artifact_refs",
    "ledger_refs",
    "input_hashes",
    "output_hashes",
    "proof_hash",
    "candidate",
    "serves_truth",
)
SOURCE_CARD_PATHS = (
    AIDEVOBSERVER_CURATED_PRIMITIVE_GROUPS_PATH,
    AIDEVOBSERVER_SOURCE_BACKED_GROUP_CARDS_PATH,
)
REQUIRED_GATE_FIELDS: tuple[str, ...] = (
    "gate_id",
    "primitive_id",
    "proof_bundle_id",
    "proof_hash",
    "promotion_gate_status",
    "promotion_allowed",
    "promotable_without_review",
    "review_required",
    "gate_checks",
    "promotion_blockers",
    "candidate",
    "serves_truth",
)


def _canon(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha(value: Any) -> str:
    return hashlib.sha256(_canon(value).encode("utf-8")).hexdigest()


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        raise AssertionError(f"missing JSONL file: {path}")
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise AssertionError(f"{path}:{line_number}: invalid JSONL: {exc}") from exc
        if not isinstance(value, dict):
            raise AssertionError(f"{path}:{line_number}: expected JSON object")
        rows.append(value)
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


def _require_fields(row: dict[str, Any], fields: tuple[str, ...], row_id: str) -> None:
    missing = sorted(field for field in fields if field not in row)
    if missing:
        raise AssertionError(f"{row_id} missing fields: {missing}")


def _list(row: dict[str, Any], field: str, row_id: str, *, min_len: int = 1) -> list[Any]:
    value = row.get(field)
    if not isinstance(value, list) or len(value) < min_len:
        raise AssertionError(f"{row_id} must declare {field} with at least {min_len} item(s)")
    return value


def _proof_hash_body(row: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in row.items() if key not in {"proof_bundle_id", "proof_hash"}}


def _gate_hash_body(row: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in row.items() if key not in {"gate_id", "gate_hash"}}


def _source_backed_group_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
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
                rows.append(row)
    rows.sort(key=lambda row: str(row.get("primitive_id") or ""))
    return rows


def _check_manifests(
    cards: list[dict[str, Any]],
    proofs: list[dict[str, Any]],
    gates: list[dict[str, Any]],
) -> None:
    card_manifest = _read_json(CARDS_MANIFEST_PATH)
    proof_manifest = _read_json(PROOF_BUNDLES_MANIFEST_PATH)
    gate_manifest = _read_json(PROMOTION_GATES_MANIFEST_PATH)
    source_card_rows = [
        card
        for card in _read_jsonl(CARDS_PATH)
        if (
            card.get("source_family") == AIDEVOBSERVER_SOURCE_BACKED_GROUP_SOURCE_FAMILY
            and card.get("source_evidence_status") == "source_backed"
            and card.get("candidate") is True
            and card.get("serves_truth") is False
        )
    ]
    if int(card_manifest.get("row_count") or 0) != len(source_card_rows):
        raise AssertionError("card manifest row_count must match card rows")
    if int(proof_manifest.get("row_count") or 0) != len(proofs):
        raise AssertionError("proof manifest row_count must match proof rows")
    if int(gate_manifest.get("row_count") or 0) != len(gates):
        raise AssertionError("gate manifest row_count must match gate rows")
    if proof_manifest.get("candidate") is not True or proof_manifest.get("serves_truth") is not False:
        raise AssertionError("proof manifest must remain candidate=true and serves_truth=false")
    if gate_manifest.get("candidate") is not True or gate_manifest.get("serves_truth") is not False:
        raise AssertionError("gate manifest must remain candidate=true and serves_truth=false")
    if gate_manifest.get("promotion_allowed") is not False or gate_manifest.get("review_required") is not True:
        raise AssertionError("gate manifest must block promotion pending review")
    if proof_manifest.get("unit_test_status") != "pass":
        raise AssertionError("unit test command must pass before proof bundles are usable")


def self_test() -> dict[str, Any]:
    cards = _source_backed_group_rows()
    proofs = _read_jsonl(PROOF_BUNDLES_PATH)
    gates = _read_jsonl(PROMOTION_GATES_PATH)
    _check_manifests(cards, proofs, gates)

    card_ids = {str(card.get("primitive_id") or "") for card in cards}
    proof_subject_ids = {str(proof.get("subject_id") or "") for proof in proofs}
    gate_primitive_ids = {str(gate.get("primitive_id") or "") for gate in gates}
    if card_ids != proof_subject_ids:
        raise AssertionError("proof subject ids must match source-backed card primitive ids")
    if card_ids != gate_primitive_ids:
        raise AssertionError("promotion gate primitive ids must match source-backed card primitive ids")

    proof_ids: set[str] = set()
    proof_hashes: set[str] = set()
    proofs_by_id: dict[str, dict[str, Any]] = {}
    for proof in proofs:
        proof_id = str(proof.get("proof_bundle_id") or "")
        _require_fields(proof, REQUIRED_PROOF_FIELDS, proof_id or "proof")
        if proof_id in proof_ids:
            raise AssertionError(f"duplicate proof_bundle_id: {proof_id}")
        proof_ids.add(proof_id)
        proofs_by_id[proof_id] = proof
        if proof.get("candidate") is not True or proof.get("serves_truth") is not False:
            raise AssertionError(f"{proof_id} must remain candidate=true and serves_truth=false")
        if proof.get("subject_kind") != "registry_record" or proof.get("proof_kind") != "unit_test":
            raise AssertionError(f"{proof_id} must be a registry_record unit_test proof")
        if proof.get("status") != "pass":
            raise AssertionError(f"{proof_id} must be pass before promotion gate evaluation")
        command = str(proof.get("proof_command") or "")
        if AIDEVOBSERVER_SOURCE_BACKED_GROUP_UNIT_TEST_PATH not in command:
            raise AssertionError(f"{proof_id} proof_command must include unit test path")
        _list(proof, "artifact_refs", proof_id, min_len=3)
        _list(proof, "input_hashes", proof_id, min_len=3)
        _list(proof, "output_hashes", proof_id, min_len=3)
        proof_hash = str(proof.get("proof_hash") or "")
        if len(proof_hash) != 64:
            raise AssertionError(f"{proof_id} must declare a full sha256 proof_hash")
        if proof_hash in proof_hashes:
            raise AssertionError(f"duplicate proof_hash: {proof_hash}")
        proof_hashes.add(proof_hash)
        if _sha(_proof_hash_body(proof)) != proof_hash:
            raise AssertionError(f"{proof_id} proof_hash does not match proof body")
        if proof.get("source_family") != AIDEVOBSERVER_SOURCE_BACKED_GROUP_SOURCE_FAMILY:
            raise AssertionError(f"{proof_id} has unexpected source_family")

    gate_ids: set[str] = set()
    for gate in gates:
        gate_id = str(gate.get("gate_id") or "")
        _require_fields(gate, REQUIRED_GATE_FIELDS, gate_id or "gate")
        if gate_id in gate_ids:
            raise AssertionError(f"duplicate gate_id: {gate_id}")
        gate_ids.add(gate_id)
        if gate.get("candidate") is not True or gate.get("serves_truth") is not False:
            raise AssertionError(f"{gate_id} must remain candidate=true and serves_truth=false")
        if gate.get("promotion_allowed") is not False:
            raise AssertionError(f"{gate_id} must not allow promotion")
        if gate.get("promotable_without_review") is not False or gate.get("review_required") is not True:
            raise AssertionError(f"{gate_id} must require explicit owner review")
        if gate.get("promotion_gate_status") != "blocked_pending_owner_review":
            raise AssertionError(f"{gate_id} must remain blocked pending owner review")
        blockers = _list(gate, "promotion_blockers", gate_id, min_len=2)
        if "promotion_review_required" not in blockers:
            raise AssertionError(f"{gate_id} must include promotion_review_required blocker")
        proof_id = str(gate.get("proof_bundle_id") or "")
        proof = proofs_by_id.get(proof_id)
        if not proof:
            raise AssertionError(f"{gate_id} references unknown proof bundle: {proof_id}")
        if gate.get("proof_hash") != proof.get("proof_hash"):
            raise AssertionError(f"{gate_id} proof hash must match referenced proof bundle")
        checks = _list(gate, "gate_checks", gate_id, min_len=5)
        checks_by_name = {
            str(check.get("name")): check
            for check in checks
            if isinstance(check, dict) and check.get("name")
        }
        if checks_by_name.get("unit_tests_pass", {}).get("status") != "pass":
            raise AssertionError(f"{gate_id} must record passing unit tests")
        if checks_by_name.get("owner_review", {}).get("status") != "pending":
            raise AssertionError(f"{gate_id} owner review check must remain pending")
        gate_hash = str(gate.get("gate_hash") or "")
        if len(gate_hash) != 64:
            raise AssertionError(f"{gate_id} must declare a full sha256 gate_hash")
        if _sha(_gate_hash_body(gate)) != gate_hash:
            raise AssertionError(f"{gate_id} gate_hash does not match gate body")

    return {
        "proof_bundles": len(proofs),
        "promotion_gates": len(gates),
        "candidate": True,
        "serves_truth": False,
        "promotion_allowed": False,
        "statuses": {
            "proof": sorted({str(proof.get("status")) for proof in proofs}),
            "gate": sorted({str(gate.get("promotion_gate_status")) for gate in gates}),
        },
    }


def main() -> int:
    try:
        result = self_test()
    except AssertionError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
