#!/usr/bin/env python3
"""Emit contract-valid stored vector rows from an embedding execution plan."""
from __future__ import annotations

import argparse
import json
import tempfile
import time
from pathlib import Path
from typing import Any

from scripts.db.vector_readiness_audit import audit_vector_readiness


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


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def _profile_dimensions(plan: dict[str, Any]) -> dict[str, int]:
    out: dict[str, int] = {}
    cost_by_profile = plan.get("cost_by_profile")
    if not isinstance(cost_by_profile, dict):
        return out
    for profile_id, profile in cost_by_profile.items():
        if not isinstance(profile, dict) or profile.get("dimensions") is None:
            continue
        out[str(profile_id)] = int(profile["dimensions"])
    return out


def _existing_plan_file(plan: dict[str, Any], key: str, embedding_plan_path: Path) -> Path:
    files = plan.get("files") if isinstance(plan.get("files"), dict) else {}
    raw = files.get(key)
    if raw:
        path = Path(str(raw))
        if path.exists():
            return path
        candidate = embedding_plan_path.parent / path.name
        if candidate.exists():
            return candidate
    fallback = embedding_plan_path.parent / {
        "embedding_batches": "embedding-batches.jsonl",
        "embedding_completion_stubs": "embedding-completion-stubs.jsonl",
    }[key]
    if not fallback.exists():
        raise FileNotFoundError(f"could not find {key} beside {embedding_plan_path}")
    return fallback


def build_local_embedding_worker_contract(
    *,
    embedding_plan: str | Path,
    output_dir: str | Path | None = None,
    run_id: str = "local-embedding-worker-contract",
    worker_id: str = "local-worker-contract-stub",
    storage_backend: str = "contract_stub",
    limit: int = 256,
) -> dict[str, Any]:
    if limit < 1:
        raise ValueError("limit must be >= 1")
    embedding_plan_path = Path(embedding_plan)
    plan = _read_json(embedding_plan_path)
    completion_path = _existing_plan_file(plan, "embedding_completion_stubs", embedding_plan_path)
    batch_path = _existing_plan_file(plan, "embedding_batches", embedding_plan_path)
    dimensions_by_profile = _profile_dimensions(plan)
    batch_rows = _read_jsonl(batch_path)
    dimensions_by_batch = {
        str(row.get("batch_id")): int(row.get("dimensions"))
        for row in batch_rows
        if row.get("batch_id") and row.get("dimensions") is not None
    }
    completion_rows = _read_jsonl(completion_path)
    sampled_completion_rows = completion_rows[:limit]
    out = Path(output_dir) if output_dir else Path(tempfile.mkdtemp(prefix="ohh-local-embedding-contract-"))
    generated_at = _utc_now()

    stored_rows: list[dict[str, Any]] = []
    for row in sampled_completion_rows:
        profile_id = str(row.get("profile_id") or "")
        batch_id = str(row.get("batch_id") or "")
        dimensions = dimensions_by_profile.get(profile_id) or dimensions_by_batch.get(batch_id)
        if not dimensions:
            raise ValueError(f"missing dimensions for profile={profile_id!r} batch={batch_id!r}")
        stored_rows.append({
            "embedding_id": row.get("embedding_id"),
            "subject_id": row.get("subject_id"),
            "subject_type": row.get("subject_type"),
            "text_hash": row.get("text_hash"),
            "batch_id": batch_id,
            "profile_id": profile_id,
            "dimensions": dimensions,
            "expected_dimensions": dimensions,
            "vector_stored": True,
            "status": "stored_contract_stub",
            "storage_backend": storage_backend,
            "worker_id": worker_id,
            "stored_at": generated_at,
            "contract_stub": True,
        })

    sampled_completion_path = out / "sampled-embedding-completion-stubs.jsonl"
    stored_vector_path = out / "stored-vector-contract-rows.jsonl"
    _write_jsonl(sampled_completion_path, sampled_completion_rows)
    _write_jsonl(stored_vector_path, stored_rows)

    readiness = audit_vector_readiness(
        completion_stubs_jsonl=sampled_completion_path,
        stored_vectors_jsonl=stored_vector_path,
        output_dir=out / "vector-readiness",
        run_id=f"{run_id}-readiness",
    )
    summary = {
        "ok": readiness["readiness_status"] == "ready",
        "run_id": run_id,
        "generated_at": generated_at,
        "embedding_plan": str(embedding_plan_path),
        "source_completion_rows": len(completion_rows),
        "sampled_completion_rows": len(sampled_completion_rows),
        "stored_vector_rows": len(stored_rows),
        "storage_backend": storage_backend,
        "worker_id": worker_id,
        "contract_status": "ready" if readiness["readiness_status"] == "ready" else "not_ready",
        "vector_readiness": readiness,
        "files": {
            "sampled_completion_stubs": str(sampled_completion_path),
            "stored_vector_contract_rows": str(stored_vector_path),
            "summary": str(out / "local-embedding-worker-contract-summary.json"),
        },
        "safety_notes": [
            "This contract output proves worker row shape, id matching, text hash matching, and dimension readiness.",
            "It does not calculate semantic embeddings and must not be loaded as production vectors.",
            "A production worker must replace contract_stub rows with actual embedding values or database vector writes.",
        ],
    }
    _write_json(out / "local-embedding-worker-contract-summary.json", summary)
    return summary


def _self_test() -> int:
    source = Path("dist/daily-embedding-execution/2026-05-31/embedding-plan/embedding-execution-plan.json")
    if not source.exists():
        raise FileNotFoundError("daily embedding execution plan is required")
    with tempfile.TemporaryDirectory() as tmp:
        result = build_local_embedding_worker_contract(embedding_plan=source, output_dir=tmp, limit=64)
        assert result["sampled_completion_rows"] == 64
        assert result["stored_vector_rows"] == 64
        assert result["vector_readiness"]["readiness_status"] == "ready"
    print(json.dumps({
        "ok": True,
        "sampled_completion_rows": result["sampled_completion_rows"],
        "stored_vector_rows": result["stored_vector_rows"],
        "readiness_status": result["vector_readiness"]["readiness_status"],
    }, indent=2, sort_keys=True))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build local embedding worker contract rows from an embedding execution plan.")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--embedding-plan")
    parser.add_argument("--output-dir")
    parser.add_argument("--run-id", default="local-embedding-worker-contract")
    parser.add_argument("--worker-id", default="local-worker-contract-stub")
    parser.add_argument("--storage-backend", default="contract_stub")
    parser.add_argument("--limit", type=int, default=256)
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    if not args.embedding_plan:
        parser.error("--embedding-plan is required unless --self-test is used")
    result = build_local_embedding_worker_contract(
        embedding_plan=args.embedding_plan,
        output_dir=args.output_dir,
        run_id=args.run_id,
        worker_id=args.worker_id,
        storage_backend=args.storage_backend,
        limit=args.limit,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
