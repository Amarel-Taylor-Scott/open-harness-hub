#!/usr/bin/env python3
"""Run primitive factory model batches and extract candidate JSONL.

This is the first operational loop for learning toward 20k useful primitive
candidates/day. It runs small shard offset windows, extracts accepted
candidate rows immediately, and writes a batch ledger plus an aggregate
manifest. It does not promote truth.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import datetime as dt
import json
import sys
import time
from pathlib import Path
from typing import Any

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts._config import (  # noqa: E402
    LLM_HIGH_CEILING_MAX_OUTPUT_TOKENS,
    OPENWEBUI_DEFAULT_MODEL,
    PRIMITIVE_FACTORY_20K_DAILY_SHARDS_DIR,
    PRIMITIVE_FACTORY_BATCH_RUNS_DIR,
    PRIMITIVE_FACTORY_DAILY_SHARDS_DIR,
    REPO_ROOT,
)
from scripts.extract_primitive_model_candidates import extract_candidates  # noqa: E402
from scripts.run_primitive_factory_model_worker import run_worker  # noqa: E402

DEFAULT_BATCH_SIZE = 25
DEFAULT_WORKERS = 2
DEFAULT_MAX_TOKENS = LLM_HIGH_CEILING_MAX_OUTPUT_TOKENS
DEFAULT_TIMEOUT = 240


def _today_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).date().isoformat()


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


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
            raise AssertionError(f"{path}:{line_number}: expected object")
        rows.append(row)
    return rows


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _rel(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT) if path.is_relative_to(REPO_ROOT) else path)


def _default_shards_path(run_date: str, target_profile: str) -> Path:
    base = PRIMITIVE_FACTORY_20K_DAILY_SHARDS_DIR if target_profile == "20k" else PRIMITIVE_FACTORY_DAILY_SHARDS_DIR
    return _resource(base) / run_date / "shards.jsonl"


def _safe_name(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in {"-", "_"} else "-" for ch in value).strip("-") or "model"


def _default_out_root(run_date: str, target_profile: str, provider: str, model: str, mode: str) -> Path:
    return _resource(PRIMITIVE_FACTORY_BATCH_RUNS_DIR) / run_date / f"{target_profile}_{provider}_{_safe_name(model)}_{mode}"


def _sum_usage(rows: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "prompt_tokens": sum(int((row.get("usage") or {}).get("prompt_tokens") or 0) for row in rows),
        "completion_tokens": sum(int((row.get("usage") or {}).get("completion_tokens") or 0) for row in rows),
        "total_tokens": sum(int((row.get("usage") or {}).get("total_tokens") or 0) for row in rows),
    }


def _model_receipts(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return _read_jsonl(path)


def _failed_model_receipts(path: Path) -> list[dict[str, Any]]:
    return [row for row in _model_receipts(path) if row.get("error")]


def run_batches(
    *,
    run_date: str,
    target_profile: str,
    shards_path: Path,
    out_root: Path,
    provider: str,
    model: str,
    mode: str,
    cdp_url: str,
    start_offset: int,
    batch_size: int,
    max_batches: int,
    workers: int,
    max_tokens: int,
    timeout: int,
    dry_run: bool,
    prompt_raw_candidate_target: int = 0,
    prompt_useful_candidate_target: int = 0,
) -> dict[str, Any]:
    if batch_size <= 0:
        raise AssertionError("batch_size must be positive")
    if workers <= 0:
        raise AssertionError("workers must be positive")

    shards = _read_jsonl(shards_path)
    out_root.mkdir(parents=True, exist_ok=True)
    started = time.time()
    ledger_path = out_root / "batch_ledger.jsonl"
    existing_rows = _read_jsonl(ledger_path) if ledger_path.exists() else []
    batch_by_id = {str(row.get("batch_id")): row for row in existing_rows if row.get("batch_id")}

    offset = max(0, start_offset)
    batch_index = 0
    while offset < len(shards):
        if max_batches and batch_index >= max_batches:
            break
        limit = min(batch_size, len(shards) - offset)
        batch_id = f"batch_{offset:06d}_{limit:04d}"
        batch_dir = out_root / batch_id
        model_dir = batch_dir / "model"
        extract_dir = batch_dir / "extracted"

        worker_manifest = run_worker(
            shards_path=shards_path,
            out_dir=model_dir,
            provider_name=provider,
            model=model,
            prompt_field="candidate_writer_prompt",
            workers=workers,
            limit=limit,
            offset=offset,
            max_tokens=max_tokens,
            timeout=timeout,
            dry_run=dry_run,
            mode=mode,
            cdp_url=cdp_url,
            prompt_raw_candidate_target=prompt_raw_candidate_target,
            prompt_useful_candidate_target=prompt_useful_candidate_target,
        )
        worker_error_count = int(worker_manifest.get("error_count") or 0)
        model_outputs_path = model_dir / "model_outputs.jsonl"
        failed_model_outputs = _failed_model_receipts(model_outputs_path)
        failed_outputs_path = batch_dir / "failed_model_outputs.jsonl"
        if not dry_run:
            _write_jsonl(failed_outputs_path, failed_model_outputs)
        extraction_manifest: dict[str, Any] = {
            "accepted_count": 0,
            "rejected_count": 0,
            "receipt_count": 0,
            "candidate": True,
            "serves_truth": False,
            "skipped": dry_run,
        }
        extraction_error = ""
        if not dry_run:
            try:
                extraction_manifest = extract_candidates(model_outputs_path, extract_dir)
            except AssertionError as exc:
                extraction_error = str(exc)
                extraction_manifest = {
                    "accepted_count": 0,
                    "rejected_count": 0,
                    "receipt_count": 0,
                    "candidate": True,
                    "serves_truth": False,
                    "skipped": True,
                    "error": extraction_error,
                }

        batch_record = {
            "record_type": "primitive_factory_batch_run",
            "batch_id": batch_id,
            "run_date": run_date,
            "target_profile": target_profile,
            "offset": offset,
            "limit": limit,
            "provider": provider,
            "model": model,
            "mode": mode,
            "workers": workers,
            "dry_run": dry_run,
            "worker_manifest_path": _rel(model_dir / "manifest.json"),
            "extraction_manifest_path": _rel(extract_dir / "manifest.json") if not dry_run else "",
            "failed_model_outputs_path": _rel(failed_outputs_path) if not dry_run else "",
            "selected_shards": worker_manifest.get("selected_shards", 0),
            "worker_error_count": worker_error_count,
            "failed_model_output_count": len(failed_model_outputs),
            "partial_failure": bool(worker_error_count),
            "extraction_error": extraction_error,
            "accepted_count": extraction_manifest.get("accepted_count", 0),
            "rejected_count": extraction_manifest.get("rejected_count", 0),
            "usage": worker_manifest.get("usage") or {},
            "duration_seconds": worker_manifest.get("duration_seconds", 0),
            "aggregate_completion_tps": worker_manifest.get("aggregate_completion_tps", 0),
            "aggregate_total_tps": worker_manifest.get("aggregate_total_tps", 0),
            "accepted_per_shard": (
                round(float(extraction_manifest.get("accepted_count", 0)) / float(limit), 3)
                if limit else 0
            ),
            "accepted_per_1k_total_tokens": (
                round(float(extraction_manifest.get("accepted_count", 0)) * 1000 / float((worker_manifest.get("usage") or {}).get("total_tokens") or 0), 3)
                if (worker_manifest.get("usage") or {}).get("total_tokens") else 0
            ),
            "candidate": True,
            "serves_truth": False,
        }
        batch_by_id[batch_id] = batch_record
        if not dry_run:
            _write_jsonl(ledger_path, sorted(batch_by_id.values(), key=lambda row: int(row.get("offset") or 0)))

        offset += limit
        batch_index += 1

    batch_rows = sorted(
        (row for row in batch_by_id.values() if dry_run or not row.get("dry_run")),
        key=lambda row: int(row.get("offset") or 0),
    )
    total_usage = _sum_usage(batch_rows)
    invocation_elapsed = round(time.time() - started, 3)
    summed_batch_duration = round(sum(float(row.get("duration_seconds") or 0) for row in batch_rows), 3)
    accepted_total = sum(int(row.get("accepted_count") or 0) for row in batch_rows)
    selected_total = sum(int(row.get("selected_shards") or 0) for row in batch_rows)
    manifest = {
        "record_type": "primitive_factory_batch_loop_manifest",
        "run_date": run_date,
        "target_profile": target_profile,
        "shards_path": _rel(shards_path),
        "out_root": _rel(out_root),
        "ledger_path": _rel(ledger_path),
        "available_shards": len(shards),
        "completed_batches": len(batch_rows),
        "selected_shards": selected_total,
        "start_offset": start_offset,
        "next_offset": offset,
        "batch_size": batch_size,
        "workers": workers,
        "provider": provider,
        "model": model,
        "mode": mode,
        "dry_run": dry_run,
        "prompt_raw_candidate_target": prompt_raw_candidate_target,
        "prompt_useful_candidate_target": prompt_useful_candidate_target,
        "worker_error_count": sum(int(row.get("worker_error_count") or 0) for row in batch_rows),
        "failed_model_output_count": sum(int(row.get("failed_model_output_count") or 0) for row in batch_rows),
        "partial_failure_count": sum(1 for row in batch_rows if row.get("partial_failure")),
        "accepted_count": accepted_total,
        "rejected_count": sum(int(row.get("rejected_count") or 0) for row in batch_rows),
        "usage": total_usage,
        "duration_seconds": summed_batch_duration,
        "invocation_duration_seconds": invocation_elapsed,
        "aggregate_completion_tps": (
            round(total_usage["completion_tokens"] / summed_batch_duration, 3)
            if summed_batch_duration and total_usage["completion_tokens"] else 0
        ),
        "aggregate_total_tps": (
            round(total_usage["total_tokens"] / summed_batch_duration, 3)
            if summed_batch_duration and total_usage["total_tokens"] else 0
        ),
        "accepted_per_shard": round(accepted_total / selected_total, 3) if selected_total else 0,
        "accepted_per_1k_total_tokens": (
            round(accepted_total * 1000 / total_usage["total_tokens"], 3)
            if total_usage["total_tokens"] else 0
        ),
        "created_at": _now(),
        "candidate": True,
        "serves_truth": False,
    }
    manifest_name = "dry_run_manifest.json" if dry_run else "manifest.json"
    (out_root / manifest_name).write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def _self_test() -> int:
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        shards_path = root / "shards.jsonl"
        shards = [
            {
                "record_type": "primitive_factory_shard",
                "shard_id": f"pfs:test:{index}",
                "run_date": "2026-06-30",
                "lane_id": "test",
                "candidate_writer_prompt": "Emit candidate JSONL.",
                "candidate": True,
                "serves_truth": False,
            }
            for index in range(3)
        ]
        _write_jsonl(shards_path, shards)
        manifest = run_batches(
            run_date="2026-06-30",
            target_profile="5k",
            shards_path=shards_path,
            out_root=root / "out",
            provider="openwebui",
            model=OPENWEBUI_DEFAULT_MODEL,
            mode="direct",
            cdp_url="",
            start_offset=0,
            batch_size=2,
            max_batches=1,
            workers=1,
            max_tokens=64,
            timeout=5,
            dry_run=True,
        )
        ok = (
            manifest["completed_batches"] == 1
            and manifest["selected_shards"] == 2
            and manifest["dry_run"] is True
            and manifest["candidate"] is True
            and manifest["serves_truth"] is False
        )
        original_run_worker = run_worker

        def _fake_partial_worker(**kwargs: Any) -> dict[str, Any]:
            out_dir = Path(kwargs["out_dir"])
            out_dir.mkdir(parents=True, exist_ok=True)
            good_row = {
                "primitive_id": "prim:test.partial",
                "kind": "primitive",
                "title": "Partial Success Candidate",
                "input_edge": "InputA",
                "output_edge": "OutputB",
                "source_refs": [{"label": "Example", "url": "https://example.invalid/partial"}],
                "proof_requirements": ["schema_validation"],
                "promotion_blockers": ["review_required"],
                "dedupe_key": "InputA->OutputB",
                "candidate": True,
                "serves_truth": False,
            }
            receipts = [
                {
                    "output_id": "pfmo:ok",
                    "shard_id": "pfs:test:0",
                    "provider": "openwebui",
                    "model": OPENWEBUI_DEFAULT_MODEL,
                    "assistant_content": json.dumps(good_row, sort_keys=True),
                    "usage": {"prompt_tokens": 5, "completion_tokens": 7, "total_tokens": 12},
                    "error": None,
                    "candidate": True,
                    "serves_truth": False,
                },
                {
                    "output_id": "pfmo:error",
                    "shard_id": "pfs:test:1",
                    "provider": "openwebui",
                    "model": OPENWEBUI_DEFAULT_MODEL,
                    "assistant_content": "",
                    "usage": {},
                    "error": "HTTP Error 429: Too Many Requests",
                    "candidate": True,
                    "serves_truth": False,
                },
            ]
            _write_jsonl(out_dir / "model_outputs.jsonl", receipts)
            (out_dir / "manifest.json").write_text(
                json.dumps(
                    {
                        "selected_shards": 2,
                        "error_count": 1,
                        "usage": {"prompt_tokens": 5, "completion_tokens": 7, "total_tokens": 12},
                        "duration_seconds": 1.0,
                        "aggregate_completion_tps": 7.0,
                        "aggregate_total_tps": 12.0,
                    },
                    sort_keys=True,
                ),
                encoding="utf-8",
            )
            return {
                "selected_shards": 2,
                "error_count": 1,
                "usage": {"prompt_tokens": 5, "completion_tokens": 7, "total_tokens": 12},
                "duration_seconds": 1.0,
                "aggregate_completion_tps": 7.0,
                "aggregate_total_tps": 12.0,
            }

        try:
            globals()["run_worker"] = _fake_partial_worker
            partial_manifest = run_batches(
                run_date="2026-06-30",
                target_profile="5k",
                shards_path=shards_path,
                out_root=root / "partial",
                provider="openwebui",
                model=OPENWEBUI_DEFAULT_MODEL,
                mode="direct",
                cdp_url="",
                start_offset=0,
                batch_size=2,
                max_batches=1,
                workers=1,
                max_tokens=64,
                timeout=5,
                dry_run=False,
            )
        finally:
            globals()["run_worker"] = original_run_worker
        ok = ok and (
            partial_manifest["completed_batches"] == 1
            and partial_manifest["worker_error_count"] == 1
            and partial_manifest["failed_model_output_count"] == 1
            and partial_manifest["accepted_count"] == 1
            and (root / "partial" / "batch_000000_0002" / "failed_model_outputs.jsonl").exists()
        )
    print("PASS - primitive factory batch loop preserves partial successes." if ok else "FAIL")
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default=_today_utc())
    parser.add_argument("--target-profile", choices=["5k", "20k"], default="20k")
    parser.add_argument("--shards", default="")
    parser.add_argument("--out-root", default="")
    parser.add_argument("--provider", default="openwebui", choices=["openwebui", "ollama", "openrouter"])
    parser.add_argument("--model", default=OPENWEBUI_DEFAULT_MODEL)
    parser.add_argument("--mode", choices=["direct", "cdp"], default="cdp")
    parser.add_argument("--cdp-url", default="")
    parser.add_argument("--start-offset", type=int, default=0)
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    parser.add_argument("--max-batches", type=int, default=1)
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS)
    parser.add_argument("--max-tokens", type=int, default=DEFAULT_MAX_TOKENS)
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    parser.add_argument("--prompt-raw-candidate-target", type=int, default=0,
                        help="Override shard prompts to emit no more than this many raw rows.")
    parser.add_argument("--prompt-useful-candidate-target", type=int, default=0,
                        help="Override shard prompts to emit exactly this many useful rows.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)

    if args.self_test:
        return _self_test()

    shards_path = Path(args.shards) if args.shards else _default_shards_path(args.date, args.target_profile)
    if not shards_path.is_absolute():
        shards_path = _resource(shards_path)
    out_root = Path(args.out_root) if args.out_root else _default_out_root(
        args.date,
        args.target_profile,
        args.provider,
        args.model,
        args.mode,
    )
    if not out_root.is_absolute():
        out_root = _resource(out_root)

    try:
        manifest = run_batches(
            run_date=args.date,
            target_profile=args.target_profile,
            shards_path=shards_path,
            out_root=out_root,
            provider=args.provider,
            model=args.model,
            mode=args.mode,
            cdp_url=args.cdp_url,
            start_offset=args.start_offset,
            batch_size=args.batch_size,
            max_batches=args.max_batches,
            workers=args.workers,
            max_tokens=args.max_tokens,
            timeout=args.timeout,
            dry_run=args.dry_run,
            prompt_raw_candidate_target=args.prompt_raw_candidate_target,
            prompt_useful_candidate_target=args.prompt_useful_candidate_target,
        )
    except AssertionError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
