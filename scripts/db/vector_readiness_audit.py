#!/usr/bin/env python3
"""Audit planned embedding completions against stored vector records."""
from __future__ import annotations

import argparse
import json
import tempfile
import time
from pathlib import Path
from typing import Any


def _utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    p = Path(path)
    if not p.exists():
        return rows
    for line_no, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
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


def _key(row: dict[str, Any]) -> str:
    return str(row.get("embedding_id") or row.get("id") or row.get("vector_id") or "")


def audit_vector_readiness(
    *,
    completion_stubs_jsonl: str | Path,
    stored_vectors_jsonl: str | Path | None = None,
    output_dir: str | Path | None = None,
    run_id: str = "vector-readiness-audit",
) -> dict[str, Any]:
    out = Path(output_dir) if output_dir else Path(tempfile.mkdtemp(prefix="ohh-vector-audit-"))
    planned = _read_jsonl(completion_stubs_jsonl)
    stored = _read_jsonl(stored_vectors_jsonl) if stored_vectors_jsonl else []
    stored_by_id = {_key(row): row for row in stored if _key(row)}

    audit_rows: list[dict[str, Any]] = []
    missing_count = 0
    ready_count = 0
    dimension_mismatch_count = 0
    text_hash_mismatch_count = 0
    planned_ids = {_key(row) for row in planned if _key(row)}

    for row in planned:
        embedding_id = _key(row)
        stored_row = stored_by_id.get(embedding_id)
        status = "missing_vector"
        vector_stored = False
        issues: list[str] = []
        stored_dimensions = None
        if stored_row:
            vector = stored_row.get("vector")
            if isinstance(vector, list):
                stored_dimensions = len(vector)
            elif stored_row.get("dimensions") is not None:
                stored_dimensions = stored_row.get("dimensions")
            vector_stored = bool(stored_row.get("vector_stored", True))
            status = "ready" if vector_stored else "present_not_stored"
            if row.get("text_hash") and stored_row.get("text_hash") and row.get("text_hash") != stored_row.get("text_hash"):
                issues.append("text_hash_mismatch")
                text_hash_mismatch_count += 1
            expected_dimensions = row.get("dimensions") or stored_row.get("expected_dimensions")
            if expected_dimensions and stored_dimensions and int(expected_dimensions) != int(stored_dimensions):
                issues.append("dimension_mismatch")
                dimension_mismatch_count += 1
            if issues:
                status = "needs_review"
            elif status == "ready":
                ready_count += 1
        else:
            missing_count += 1

        audit_rows.append({
            "embedding_id": embedding_id,
            "subject_id": row.get("subject_id"),
            "subject_type": row.get("subject_type"),
            "batch_id": row.get("batch_id"),
            "profile_id": row.get("profile_id"),
            "planned_text_hash": row.get("text_hash"),
            "stored_text_hash": stored_row.get("text_hash") if stored_row else "",
            "stored_dimensions": stored_dimensions,
            "vector_stored": vector_stored,
            "status": status,
            "issues": issues,
        })

    orphan_rows = [row for key, row in stored_by_id.items() if key not in planned_ids]
    summary = {
        "ok": True,
        "run_id": run_id,
        "generated_at": _utc_now(),
        "planned_rows": len(planned),
        "stored_rows": len(stored),
        "ready_rows": ready_count,
        "missing_vector_rows": missing_count,
        "needs_review_rows": dimension_mismatch_count + text_hash_mismatch_count,
        "dimension_mismatch_rows": dimension_mismatch_count,
        "text_hash_mismatch_rows": text_hash_mismatch_count,
        "orphan_stored_rows": len(orphan_rows),
        "readiness_status": "ready" if planned and ready_count == len(planned) and not orphan_rows else "not_ready",
        "files": {
            "audit_rows": str(out / "vector-readiness-rows.jsonl"),
            "orphan_rows": str(out / "vector-orphan-rows.jsonl"),
            "summary": str(out / "vector-readiness-summary.json"),
        },
        "safety_notes": [
            "The audit reads only planned completion metadata and optional stored vector metadata.",
            "It does not generate embeddings, call providers, or write to a vector database.",
            "Text hashes are compared without requiring raw text or PII in audit output.",
        ],
    }
    _write_jsonl(out / "vector-readiness-rows.jsonl", audit_rows)
    _write_jsonl(out / "vector-orphan-rows.jsonl", orphan_rows)
    _write_json(out / "vector-readiness-summary.json", summary)
    return summary


def _self_test() -> int:
    source = Path("dist/source-surface-scan-partitions/seed/embedding-plan/embedding-completion-stubs.jsonl")
    if not source.exists():
        raise FileNotFoundError("embedding completion stubs are required")
    with tempfile.TemporaryDirectory() as tmp:
        report = audit_vector_readiness(completion_stubs_jsonl=source, output_dir=tmp)
        assert report["planned_rows"] > 0
        assert report["missing_vector_rows"] == report["planned_rows"]
        assert Path(report["files"]["audit_rows"]).exists()
    print(json.dumps({
        "ok": True,
        "planned_rows": report["planned_rows"],
        "readiness_status": report["readiness_status"],
    }, indent=2, sort_keys=True))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit planned embedding completion rows against stored vector rows.")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--completion-stubs-jsonl")
    parser.add_argument("--stored-vectors-jsonl")
    parser.add_argument("--output-dir")
    parser.add_argument("--run-id", default="vector-readiness-audit")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    if not args.completion_stubs_jsonl:
        parser.error("--completion-stubs-jsonl is required unless --self-test is used")
    result = audit_vector_readiness(
        completion_stubs_jsonl=args.completion_stubs_jsonl,
        stored_vectors_jsonl=args.stored_vectors_jsonl,
        output_dir=args.output_dir,
        run_id=args.run_id,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
