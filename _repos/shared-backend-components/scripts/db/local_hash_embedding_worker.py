#!/usr/bin/env python3
"""Generate deterministic local embedding vectors for planned embedding rows."""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import hashlib
import json
import math
import re
import tempfile
import time
from pathlib import Path
from typing import Any

from scripts._config import DEFAULT_EMBEDDING_DIMENSIONS, DEFAULT_VECTOR_STORAGE_BACKEND
from scripts.db.vector_readiness_audit import audit_vector_readiness


TOKEN_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:/+-]{1,80}")


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
    fallback_name = {
        "embedding_batches": "embedding-batches.jsonl",
        "embedding_completion_stubs": "embedding-completion-stubs.jsonl",
    }[key]
    fallback = embedding_plan_path.parent / fallback_name
    if not fallback.exists():
        raise FileNotFoundError(f"could not find {key} beside {embedding_plan_path}")
    return fallback


def _input_embedding_path(plan: dict[str, Any], embedding_plan_path: Path) -> Path:
    raw = plan.get("input_path")
    if raw:
        path = Path(str(raw))
        if path.exists():
            return path
        candidate = embedding_plan_path.parent / path.name
        if candidate.exists():
            return candidate
    raise FileNotFoundError("embedding plan does not point to an existing object embedding JSONL input_path")


def _profile_dimensions(plan: dict[str, Any], fallback_dimensions: int) -> dict[str, int]:
    out: dict[str, int] = {}
    cost_by_profile = plan.get("cost_by_profile")
    if isinstance(cost_by_profile, dict):
        for profile_id, profile in cost_by_profile.items():
            if isinstance(profile, dict) and profile.get("dimensions") is not None:
                out[str(profile_id)] = int(profile["dimensions"])
    if not out:
        out["default"] = fallback_dimensions
    return out


def _row_text_by_embedding_id(path: Path) -> dict[str, str]:
    rows = _read_jsonl(path)
    out: dict[str, str] = {}
    for row in rows:
        embedding_id = str(row.get("embedding_id") or "")
        if embedding_id:
            out[embedding_id] = str(row.get("text") or "")
    return out


def _hash_embedding(text: str, dimensions: int) -> list[float]:
    vector = [0.0] * dimensions
    tokens = TOKEN_RE.findall(text.lower())
    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        bucket = int.from_bytes(digest[:4], "big") % dimensions
        sign = -1.0 if digest[4] & 1 else 1.0
        weight = 1.0 + min(len(token), 24) / 24.0
        vector[bucket] += sign * weight
    norm = math.sqrt(sum(value * value for value in vector))
    if not norm:
        seed = hashlib.sha256(text.encode("utf-8")).digest()
        bucket = int.from_bytes(seed[:4], "big") % dimensions
        vector[bucket] = 1.0
        return vector
    return [round(value / norm, 8) for value in vector]


def run_local_hash_embedding_worker(
    *,
    embedding_plan: str | Path,
    output_dir: str | Path | None = None,
    run_id: str = "local-hash-embedding-worker",
    worker_id: str = "local-hash-worker",
    storage_backend: str = DEFAULT_VECTOR_STORAGE_BACKEND,
    limit: int = 256,
    fallback_dimensions: int = DEFAULT_EMBEDDING_DIMENSIONS,
) -> dict[str, Any]:
    if limit < 1:
        raise ValueError("limit must be >= 1")
    embedding_plan_path = Path(embedding_plan)
    plan = _read_json(embedding_plan_path)
    completion_path = _existing_plan_file(plan, "embedding_completion_stubs", embedding_plan_path)
    batch_path = _existing_plan_file(plan, "embedding_batches", embedding_plan_path)
    input_path = _input_embedding_path(plan, embedding_plan_path)
    dimensions_by_profile = _profile_dimensions(plan, fallback_dimensions)
    batch_rows = _read_jsonl(batch_path)
    dimensions_by_batch = {
        str(row.get("batch_id")): int(row.get("dimensions"))
        for row in batch_rows
        if row.get("batch_id") and row.get("dimensions") is not None
    }
    text_by_embedding_id = _row_text_by_embedding_id(input_path)
    completion_rows = _read_jsonl(completion_path)
    sampled_completion_rows = completion_rows[:limit]
    out = Path(output_dir) if output_dir else Path(tempfile.mkdtemp(prefix="ohh-local-hash-embedding-worker-"))
    generated_at = _utc_now()

    completed_rows: list[dict[str, Any]] = []
    stored_rows: list[dict[str, Any]] = []
    missing_text_rows = 0
    for row in sampled_completion_rows:
        embedding_id = str(row.get("embedding_id") or "")
        profile_id = str(row.get("profile_id") or "")
        batch_id = str(row.get("batch_id") or "")
        dimensions = dimensions_by_profile.get(profile_id) or dimensions_by_batch.get(batch_id) or fallback_dimensions
        text = text_by_embedding_id.get(embedding_id, "")
        if not text:
            missing_text_rows += 1
        vector = _hash_embedding(text or embedding_id, dimensions)
        completed_rows.append({
            **row,
            "status": "completed",
            "vector_stored": True,
            "completed_at": generated_at,
            "error": "",
            "dimensions": dimensions,
            "worker_id": worker_id,
            "storage_backend": storage_backend,
        })
        stored_rows.append({
            "embedding_id": embedding_id,
            "subject_id": row.get("subject_id"),
            "subject_type": row.get("subject_type"),
            "text_hash": row.get("text_hash"),
            "batch_id": batch_id,
            "profile_id": profile_id,
            "dimensions": dimensions,
            "expected_dimensions": dimensions,
            "vector": vector,
            "vector_stored": True,
            "status": "stored",
            "storage_backend": storage_backend,
            "worker_id": worker_id,
            "stored_at": generated_at,
            "embedding_runtime": "local_hashing_vectorizer",
            "embedding_model": "hashing-vectorizer-v1",
        })

    sampled_completion_path = out / "sampled-embedding-completion-stubs.jsonl"
    completed_completion_path = out / "completed-embedding-rows.jsonl"
    stored_vector_path = out / "stored-vector-rows.jsonl"
    _write_jsonl(sampled_completion_path, sampled_completion_rows)
    _write_jsonl(completed_completion_path, completed_rows)
    _write_jsonl(stored_vector_path, stored_rows)

    readiness = audit_vector_readiness(
        completion_stubs_jsonl=completed_completion_path,
        stored_vectors_jsonl=stored_vector_path,
        output_dir=out / "vector-readiness",
        run_id=f"{run_id}-readiness",
    )
    summary = {
        "ok": readiness["readiness_status"] == "ready" and missing_text_rows == 0,
        "run_id": run_id,
        "generated_at": generated_at,
        "embedding_plan": str(embedding_plan_path),
        "source_embedding_rows_path": str(input_path),
        "source_completion_rows": len(completion_rows),
        "sampled_completion_rows": len(sampled_completion_rows),
        "completed_embedding_rows": len(completed_rows),
        "stored_vector_rows": len(stored_rows),
        "missing_text_rows": missing_text_rows,
        "storage_backend": storage_backend,
        "worker_id": worker_id,
        "embedding_runtime": "local_hashing_vectorizer",
        "embedding_model": "hashing-vectorizer-v1",
        "vector_readiness": readiness,
        "files": {
            "sampled_completion_stubs": str(sampled_completion_path),
            "completed_embedding_rows": str(completed_completion_path),
            "stored_vector_rows": str(stored_vector_path),
            "summary": str(out / "local-hash-embedding-worker-summary.json"),
        },
        "safety_notes": [
            "This worker is local and deterministic; it does not call a model provider or network service.",
            "Hashing vectors are useful for execution, storage, replay, and readiness tests, but semantic search quality should be evaluated before tenant-visible use.",
            "A sentence-transformers, TEI, vLLM, or hosted embedding worker can replace this runtime while preserving the same row contract.",
        ],
    }
    _write_json(out / "local-hash-embedding-worker-summary.json", summary)
    return summary


def _self_test() -> int:
    source = _resource("dist/daily-embedding-execution/2026-05-31/embedding-plan/embedding-execution-plan.json")
    if not source.exists():
        raise FileNotFoundError("daily embedding execution plan is required")
    with tempfile.TemporaryDirectory() as tmp:
        result = run_local_hash_embedding_worker(embedding_plan=source, output_dir=tmp, limit=32)
        assert result["completed_embedding_rows"] == 32
        assert result["stored_vector_rows"] == 32
        assert result["missing_text_rows"] == 0
        assert result["vector_readiness"]["readiness_status"] == "ready"
    print(json.dumps({
        "ok": True,
        "completed_embedding_rows": result["completed_embedding_rows"],
        "stored_vector_rows": result["stored_vector_rows"],
        "readiness_status": result["vector_readiness"]["readiness_status"],
    }, indent=2, sort_keys=True))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate deterministic local hash embeddings for planned embedding rows.")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--embedding-plan")
    parser.add_argument("--output-dir")
    parser.add_argument("--run-id", default="local-hash-embedding-worker")
    parser.add_argument("--worker-id", default="local-hash-worker")
    parser.add_argument("--storage-backend", default=DEFAULT_VECTOR_STORAGE_BACKEND)
    parser.add_argument("--limit", type=int, default=256)
    parser.add_argument("--fallback-dimensions", type=int, default=DEFAULT_EMBEDDING_DIMENSIONS)
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    if not args.embedding_plan:
        parser.error("--embedding-plan is required unless --self-test is used")
    result = run_local_hash_embedding_worker(
        embedding_plan=args.embedding_plan,
        output_dir=args.output_dir,
        run_id=args.run_id,
        worker_id=args.worker_id,
        storage_backend=args.storage_backend,
        limit=args.limit,
        fallback_dimensions=args.fallback_dimensions,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
