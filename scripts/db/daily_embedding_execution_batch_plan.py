#!/usr/bin/env python3
"""Plan embedding execution and vector readiness for a daily production run."""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

from scripts._config import DEFAULT_EMBEDDING_PROFILE_ID, embedding_model_profiles
from scripts.db.embedding_execution_plan import plan_embedding_execution
from scripts.db.vector_readiness_audit import audit_vector_readiness


def _utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def _object_embeddings_path(daily_run_dir: Path) -> Path:
    return daily_run_dir / "load-audit" / "merged-jsonl" / "object-embeddings.jsonl"


def build_daily_embedding_execution_batch_plan(
    *,
    daily_run_dir: str | Path,
    output_dir: str | Path,
    run_id: str | None = None,
    default_profile: str = DEFAULT_EMBEDDING_PROFILE_ID,
    max_items_per_batch: int = 256,
    max_tokens_per_batch: int = 24000,
    stored_vectors_jsonl: str | Path | None = None,
) -> dict[str, Any]:
    daily_dir = Path(daily_run_dir)
    out = Path(output_dir)
    summary = _read_json(daily_dir / "daily-production-run-summary.json")
    effective_run_id = run_id or f"daily-embedding-{summary.get('run_date', daily_dir.name)}"
    profiles_path = out / "embedding-model-profiles.json"
    _write_json(profiles_path, embedding_model_profiles(include_hosted_placeholder=True))

    embedding_plan = plan_embedding_execution(
        object_embeddings_jsonl=_object_embeddings_path(daily_dir),
        output_dir=out / "embedding-plan",
        run_id=effective_run_id,
        default_profile=default_profile,
        model_profiles_json=profiles_path,
        max_items_per_batch=max_items_per_batch,
        max_tokens_per_batch=max_tokens_per_batch,
    )
    vector_audit = audit_vector_readiness(
        completion_stubs_jsonl=embedding_plan["files"]["embedding_completion_stubs"],
        stored_vectors_jsonl=stored_vectors_jsonl,
        output_dir=out / "vector-readiness",
        run_id=f"{effective_run_id}-vector-readiness",
    )
    report = {
        "ok": bool(embedding_plan.get("ok")) and bool(vector_audit.get("ok")),
        "run_id": effective_run_id,
        "generated_at": _utc_now(),
        "daily_run_dir": str(daily_dir),
        "daily_run": {
            "run_date": summary.get("run_date"),
            "target_count": summary.get("target_count"),
            "matrix": summary.get("matrix"),
            "showcase_count": summary.get("showcase_count"),
        },
        "embedding_plan": {
            "input_embedding_rows": embedding_plan.get("input_embedding_rows"),
            "planned_batch_count": embedding_plan.get("planned_batch_count"),
            "planned_completion_rows": embedding_plan.get("planned_completion_rows"),
            "cost_by_profile": embedding_plan.get("cost_by_profile"),
            "files": embedding_plan.get("files"),
        },
        "vector_readiness": {
            "planned_rows": vector_audit.get("planned_rows"),
            "ready_rows": vector_audit.get("ready_rows"),
            "missing_vector_rows": vector_audit.get("missing_vector_rows"),
            "readiness_status": vector_audit.get("readiness_status"),
            "files": vector_audit.get("files"),
        },
        "decision": "embedding_execution_required" if vector_audit.get("readiness_status") != "ready" else "vector_ready",
        "next_actions": [
            "Dispatch planned embedding batches to local workers by default.",
            "Replace placeholder external pricing with a live pricing snapshot before hosted execution.",
            "Write stored vector metadata after worker completion.",
            "Rerun vector readiness audit before active promotion or tenant-visible vector search.",
        ],
        "files": {
            "model_profiles": str(profiles_path),
            "embedding_plan": embedding_plan["files"]["manifest"],
            "vector_readiness": vector_audit["files"]["summary"],
            "summary": str(out / "daily-embedding-execution-batch-plan.json"),
        },
        "safety_notes": [
            "This planner does not call embedding providers or write vectors.",
            "Local profiles are the default for synthetic/public staged rows.",
            "External profiles remain planning-only until pricing and trust boundaries are approved.",
        ],
    }
    _write_json(out / "daily-embedding-execution-batch-plan.json", report)
    return report


def _self_test() -> int:
    result = build_daily_embedding_execution_batch_plan(
        daily_run_dir="dist/daily-production-runs/2026-05-31",
        output_dir="dist/daily-embedding-execution/self-test",
        run_id="self-test",
    )
    assert result["embedding_plan"]["input_embedding_rows"] == 5000
    assert result["embedding_plan"]["planned_completion_rows"] == 5000
    assert result["vector_readiness"]["missing_vector_rows"] == 5000
    print("ok")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--daily-run-dir")
    parser.add_argument("--output-dir", default="dist/daily-embedding-execution")
    parser.add_argument("--run-id")
    parser.add_argument("--default-profile", default=DEFAULT_EMBEDDING_PROFILE_ID)
    parser.add_argument("--max-items-per-batch", type=int, default=256)
    parser.add_argument("--max-tokens-per-batch", type=int, default=24000)
    parser.add_argument("--stored-vectors-jsonl")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    if not args.daily_run_dir:
        parser.error("--daily-run-dir is required unless --self-test is used")
    result = build_daily_embedding_execution_batch_plan(
        daily_run_dir=args.daily_run_dir,
        output_dir=args.output_dir,
        run_id=args.run_id,
        default_profile=args.default_profile,
        max_items_per_batch=args.max_items_per_batch,
        max_tokens_per_batch=args.max_tokens_per_batch,
        stored_vectors_jsonl=args.stored_vectors_jsonl,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
