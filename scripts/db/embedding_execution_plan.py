#!/usr/bin/env python3
"""Plan embedding execution batches from staged object_embedding rows."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import tempfile
import time
from pathlib import Path
from typing import Any

from scripts._config import DEFAULT_EMBEDDING_PROFILE_ID, embedding_model_profiles


def _utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


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


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def _safe_slug(value: str, limit: int = 96) -> str:
    out: list[str] = []
    for ch in value.lower():
        if ch.isalnum():
            out.append(ch)
        elif out and out[-1] != "-":
            out.append("-")
    return "".join(out).strip("-")[:limit] or "item"


def _hash_json(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _estimated_tokens(text: str) -> int:
    return max(1, math.ceil(len(text) / 4))


def _load_profiles(path: str | Path | None) -> dict[str, dict[str, Any]]:
    if not path:
        return embedding_model_profiles()
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("model profiles file must contain a JSON object")
    profiles = embedding_model_profiles()
    for key, profile in value.items():
        if isinstance(profile, dict):
            profiles[str(key)] = profile
    return profiles


def _select_profile(row: dict[str, Any], profiles: dict[str, dict[str, Any]], default_profile: str) -> tuple[str, dict[str, Any]]:
    metadata = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
    requested = metadata.get("embedding_profile") or row.get("embedding_profile") or default_profile
    profile_id = str(requested)
    if profile_id not in profiles:
        profile_id = default_profile
    return profile_id, profiles[profile_id]


def _batch_rows(rows: list[dict[str, Any]], max_items_per_batch: int, max_tokens_per_batch: int) -> list[list[dict[str, Any]]]:
    batches: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []
    current_tokens = 0
    for row in rows:
        tokens = int(row["_estimated_tokens"])
        if current and (len(current) >= max_items_per_batch or current_tokens + tokens > max_tokens_per_batch):
            batches.append(current)
            current = []
            current_tokens = 0
        current.append(row)
        current_tokens += tokens
    if current:
        batches.append(current)
    return batches


def plan_embedding_execution(
    *,
    object_embeddings_jsonl: str | Path,
    output_dir: str | Path | None = None,
    run_id: str = "embedding-execution-plan",
    default_profile: str = DEFAULT_EMBEDDING_PROFILE_ID,
    model_profiles_json: str | Path | None = None,
    max_items_per_batch: int = 128,
    max_tokens_per_batch: int = 12000,
) -> dict[str, Any]:
    profiles = _load_profiles(model_profiles_json)
    if default_profile not in profiles:
        raise ValueError(f"default profile {default_profile!r} is not defined")
    out = Path(output_dir) if output_dir else Path(tempfile.mkdtemp(prefix="ohh-embedding-plan-"))
    rows = _read_jsonl(object_embeddings_jsonl)
    enriched: list[dict[str, Any]] = []
    for row in rows:
        text = str(row.get("text") or "")
        profile_id, profile = _select_profile(row, profiles, default_profile)
        enriched.append({
            **row,
            "_profile_id": profile_id,
            "_profile": profile,
            "_estimated_tokens": _estimated_tokens(text),
        })
    by_profile: dict[str, list[dict[str, Any]]] = {}
    for row in enriched:
        by_profile.setdefault(str(row["_profile_id"]), []).append(row)

    batch_rows: list[dict[str, Any]] = []
    completion_rows: list[dict[str, Any]] = []
    cost_by_profile: dict[str, dict[str, Any]] = {}
    for profile_id, profile_rows in sorted(by_profile.items()):
        profile = profiles[profile_id]
        batches = _batch_rows(profile_rows, max_items_per_batch, max_tokens_per_batch)
        token_total = sum(int(row["_estimated_tokens"]) for row in profile_rows)
        price = profile.get("usd_per_million_tokens")
        estimated_usd = None if price is None else round((token_total / 1_000_000) * float(price), 6)
        cost_by_profile[profile_id] = {
            "provider": profile.get("provider"),
            "model": profile.get("model"),
            "runtime": profile.get("runtime"),
            "trust_boundary": profile.get("trust_boundary"),
            "dimensions": profile.get("dimensions"),
            "row_count": len(profile_rows),
            "estimated_tokens": token_total,
            "usd_per_million_tokens": price,
            "estimated_usd": estimated_usd,
            "notes": profile.get("notes", []),
        }
        for index, batch in enumerate(batches, 1):
            batch_id = f"embedding-batch/{_safe_slug(run_id)}/{_safe_slug(profile_id)}/{index:05d}"
            text_hashes = [str(row.get("text_hash") or "") for row in batch]
            subject_ids = [str(row.get("subject_id") or "") for row in batch]
            batch_rows.append({
                "batch_id": batch_id,
                "run_id": run_id,
                "profile_id": profile_id,
                "provider": profile.get("provider"),
                "model": profile.get("model"),
                "runtime": profile.get("runtime"),
                "trust_boundary": profile.get("trust_boundary"),
                "dimensions": profile.get("dimensions"),
                "status": "planned",
                "item_count": len(batch),
                "estimated_tokens": sum(int(row["_estimated_tokens"]) for row in batch),
                "subject_ids": subject_ids,
                "embedding_ids": [str(row.get("embedding_id") or "") for row in batch],
                "text_hashes": text_hashes,
                "content_hash": _hash_json({"subject_ids": subject_ids, "text_hashes": text_hashes, "profile_id": profile_id}),
            })
            for row in batch:
                completion_rows.append({
                    "embedding_id": row.get("embedding_id"),
                    "subject_id": row.get("subject_id"),
                    "subject_type": row.get("subject_type"),
                    "text_hash": row.get("text_hash"),
                    "batch_id": batch_id,
                    "profile_id": profile_id,
                    "status": "planned",
                    "vector_stored": False,
                    "completed_at": "",
                    "error": "",
                })

    _write_jsonl(out / "embedding-batches.jsonl", batch_rows)
    _write_jsonl(out / "embedding-completion-stubs.jsonl", completion_rows)
    manifest = {
        "ok": True,
        "run_id": run_id,
        "generated_at": _utc_now(),
        "input_path": str(object_embeddings_jsonl),
        "output_dir": str(out),
        "input_embedding_rows": len(rows),
        "planned_batch_count": len(batch_rows),
        "planned_completion_rows": len(completion_rows),
        "max_items_per_batch": max_items_per_batch,
        "max_tokens_per_batch": max_tokens_per_batch,
        "cost_by_profile": cost_by_profile,
        "files": {
            "embedding_batches": str(out / "embedding-batches.jsonl"),
            "embedding_completion_stubs": str(out / "embedding-completion-stubs.jsonl"),
            "manifest": str(out / "embedding-execution-plan.json"),
        },
        "safety_notes": [
            "This planner does not call embedding providers or write vectors.",
            "External pricing profiles are placeholders unless a run-scoped pricing snapshot is supplied.",
            "Rows preserve trust boundaries so private text can be routed to local-only profiles.",
        ],
    }
    _write_json(out / "embedding-execution-plan.json", manifest)
    return manifest


def _self_test() -> int:
    source = Path("dist/source-surface-scan-partitions/seed/rows/object-embeddings.jsonl")
    if not source.exists():
        raise FileNotFoundError("dist/source-surface-scan-partitions/seed/rows/object-embeddings.jsonl is required")
    with tempfile.TemporaryDirectory() as tmp:
        plan = plan_embedding_execution(object_embeddings_jsonl=source, output_dir=tmp, max_items_per_batch=200)
        assert plan["input_embedding_rows"] > 0
        assert plan["planned_completion_rows"] == plan["input_embedding_rows"]
        assert Path(plan["files"]["embedding_batches"]).exists()
    print(json.dumps({"ok": True, "input_embedding_rows": plan["input_embedding_rows"], "planned_batch_count": plan["planned_batch_count"]}, indent=2, sort_keys=True))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Plan embedding batches from staged object_embedding JSONL rows.")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--object-embeddings-jsonl")
    parser.add_argument("--output-dir")
    parser.add_argument("--run-id", default="embedding-execution-plan")
    parser.add_argument("--default-profile", default="local-bge-small-en")
    parser.add_argument("--model-profiles-json")
    parser.add_argument("--max-items-per-batch", type=int, default=128)
    parser.add_argument("--max-tokens-per-batch", type=int, default=12000)
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    if not args.object_embeddings_jsonl:
        parser.error("--object-embeddings-jsonl is required unless --self-test is used")
    result = plan_embedding_execution(
        object_embeddings_jsonl=args.object_embeddings_jsonl,
        output_dir=args.output_dir,
        run_id=args.run_id,
        default_profile=args.default_profile,
        model_profiles_json=args.model_profiles_json,
        max_items_per_batch=args.max_items_per_batch,
        max_tokens_per_batch=args.max_tokens_per_batch,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
