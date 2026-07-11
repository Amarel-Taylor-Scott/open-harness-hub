#!/usr/bin/env python3
"""Retry failed primitive-factory shard calls through working fallbacks.

The normal provider planner reserves shard windows once a batch is attempted.
This loop recovers the individual failed shard receipts into a separate retry
tree so failures are not silently lost. Outputs remain candidate-only and still
flow through deterministic extraction and verification.
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
    PRIMITIVE_FACTORY_20K_DAILY_SHARDS_DIR,
    PRIMITIVE_FACTORY_BATCH_RUNS_DIR,
    REPO_ROOT,
)
from scripts.extract_primitive_model_candidates import extract_candidates  # noqa: E402
from scripts.run_primitive_factory_model_worker import run_worker  # noqa: E402


DEFAULT_INTERVAL_SECONDS = 900
DEFAULT_MAX_SHARDS = 24


def _today_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).date().isoformat()


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def _stamp() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _rel(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT) if path.is_relative_to(REPO_ROOT) else path)


def _safe(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in {"-", "_"} else "-" for ch in value).strip("-") or "retry"


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
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


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _append_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _shards_path(run_date: str) -> Path:
    return _resource(PRIMITIVE_FACTORY_20K_DAILY_SHARDS_DIR) / run_date / "shards.jsonl"


def _batch_root(run_date: str) -> Path:
    return _resource(PRIMITIVE_FACTORY_BATCH_RUNS_DIR) / run_date


def _retry_root(run_date: str) -> Path:
    return _batch_root(run_date) / "failed_shard_retries"


def _retry_ledger_path(run_date: str) -> Path:
    return _retry_root(run_date) / "retry_ledger.jsonl"


def _shards_by_id(run_date: str) -> dict[str, dict[str, Any]]:
    return {
        str(row.get("shard_id")): row
        for row in _read_jsonl(_shards_path(run_date))
        if row.get("shard_id")
    }


def _successful_shard_ids(run_date: str) -> set[str]:
    successful: set[str] = set()
    for path in _batch_root(run_date).glob("**/model_outputs.jsonl"):
        for row in _read_jsonl(path):
            shard_id = row.get("shard_id")
            if shard_id and not row.get("error") and str(row.get("assistant_content") or "").strip():
                successful.add(str(shard_id))
    return successful


def _failed_receipts(run_date: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(_batch_root(run_date).glob("**/failed_model_outputs.jsonl")):
        for row in _read_jsonl(path):
            if not row.get("shard_id"):
                continue
            rows.append({**row, "failed_receipt_path": _rel(path)})
    return rows


def _retry_key(row: dict[str, Any], target: dict[str, Any]) -> str:
    return "::".join(
        str(part)
        for part in (
            row.get("shard_id"),
            target["provider"],
            target["model"],
            target["mode"],
        )
    )


def _retried_keys(run_date: str) -> set[str]:
    return {str(row.get("retry_key")) for row in _read_jsonl(_retry_ledger_path(run_date)) if row.get("retry_key")}


def _target_for_failure(row: dict[str, Any]) -> dict[str, Any]:
    provider = str(row.get("provider") or "")
    model = str(row.get("model") or "")
    error = str(row.get("error") or "")
    if provider == "openwebui":
        return {
            "provider": "openwebui",
            "model": "gemma-4-coding",
            "mode": "cdp",
            "workers": 2,
            "timeout": 420,
            "fallback_reason": "openwebui_cdp_timeout_recovery",
        }
    if provider == "ollama" and model == "kimi-k2.7-code":
        return {
            "provider": "ollama",
            "model": "glm-5.2",
            "mode": "direct",
            "workers": 2,
            "timeout": 420,
            "fallback_reason": "kimi_timeout_to_glm_reliable_fallback",
        }
    if provider == "ollama" and (model == "glm-4.5" or "not found" in error.lower()):
        return {
            "provider": "ollama",
            "model": "glm-5.2",
            "mode": "direct",
            "workers": 2,
            "timeout": 420,
            "fallback_reason": "obsolete_model_to_glm_5_2",
        }
    return {
        "provider": provider or "ollama",
        "model": model or "glm-5.2",
        "mode": "direct" if provider == "ollama" else "cdp",
        "workers": 2,
        "timeout": 420,
        "fallback_reason": "same_provider_timeout_retry",
    }


def run_once(
    *,
    run_date: str,
    max_shards: int,
    include_retried: bool,
    retry_if_any_success: bool,
    dry_run: bool,
) -> dict[str, Any]:
    started = time.time()
    shards = _shards_by_id(run_date)
    successful = set() if retry_if_any_success else _successful_shard_ids(run_date)
    already_retried = set() if include_retried else _retried_keys(run_date)
    selected: list[tuple[dict[str, Any], dict[str, Any]]] = []
    skipped_success = 0
    skipped_retried = 0
    skipped_missing_shard = 0

    for failed in _failed_receipts(run_date):
        shard_id = str(failed.get("shard_id") or "")
        if shard_id not in shards:
            skipped_missing_shard += 1
            continue
        if shard_id in successful:
            skipped_success += 1
            continue
        target = _target_for_failure(failed)
        key = _retry_key(failed, target)
        if key in already_retried:
            skipped_retried += 1
            continue
        selected.append((failed, target))
        already_retried.add(key)
        if max_shards and len(selected) >= max_shards:
            break

    groups: dict[str, list[tuple[dict[str, Any], dict[str, Any]]]] = {}
    for failed, target in selected:
        group_key = "::".join([target["provider"], target["model"], target["mode"]])
        groups.setdefault(group_key, []).append((failed, target))

    tick_id = _stamp()
    retry_records: list[dict[str, Any]] = []
    group_manifests: list[dict[str, Any]] = []
    for group_key, items in groups.items():
        target = items[0][1]
        group_dir = _retry_root(run_date) / tick_id / _safe(group_key)
        retry_shards = [shards[str(failed["shard_id"])] for failed, _target in items]
        retry_shards_path = group_dir / "shards.jsonl"
        _write_jsonl(retry_shards_path, retry_shards)
        model_dir = group_dir / "model"
        extract_dir = group_dir / "extracted"
        worker_manifest = run_worker(
            shards_path=retry_shards_path,
            out_dir=model_dir,
            provider_name=target["provider"],
            model=target["model"],
            prompt_field="candidate_writer_prompt",
            workers=int(target["workers"]),
            limit=len(retry_shards),
            offset=0,
            max_tokens=LLM_HIGH_CEILING_MAX_OUTPUT_TOKENS,
            timeout=int(target["timeout"]),
            dry_run=dry_run,
            mode=target["mode"],
            cdp_url="",
        )
        extraction_manifest: dict[str, Any] = {"skipped": True, "candidate": True, "serves_truth": False}
        if not dry_run:
            extraction_manifest = extract_candidates(model_dir / "model_outputs.jsonl", extract_dir)
        group_manifest = {
            "record_type": "primitive_failed_shard_retry_group",
            "run_date": run_date,
            "group_key": group_key,
            "target": target,
            "retry_shards_path": _rel(retry_shards_path),
            "worker_manifest": worker_manifest,
            "extraction_manifest": extraction_manifest,
            "candidate": True,
            "serves_truth": False,
        }
        _write_json(group_dir / "manifest.json", group_manifest)
        group_manifests.append(group_manifest)
        outputs_by_shard = {
            str(row.get("shard_id")): row
            for row in _read_jsonl(model_dir / "model_outputs.jsonl")
        }
        for failed, _target in items:
            output = outputs_by_shard.get(str(failed.get("shard_id"))) or {}
            retry_records.append(
                {
                    "record_type": "primitive_failed_shard_retry_receipt",
                    "retry_key": _retry_key(failed, target),
                    "run_date": run_date,
                    "source_failed_receipt_path": failed.get("failed_receipt_path"),
                    "source_provider": failed.get("provider"),
                    "source_model": failed.get("model"),
                    "source_error": failed.get("error"),
                    "shard_id": failed.get("shard_id"),
                    "target_provider": target["provider"],
                    "target_model": target["model"],
                    "target_mode": target["mode"],
                    "fallback_reason": target["fallback_reason"],
                    "retry_status": output.get("status") or "planned",
                    "retry_error": output.get("error"),
                    "output_id": output.get("output_id"),
                    "created_at": _now(),
                    "candidate": True,
                    "serves_truth": False,
                }
            )

    if retry_records and not dry_run:
        _append_jsonl(_retry_ledger_path(run_date), retry_records)

    manifest = {
        "record_type": "primitive_failed_shard_retry_loop_tick",
        "run_date": run_date,
        "selected_failed_shards": len(selected),
        "retried_shards": len(retry_records),
        "group_count": len(group_manifests),
        "skipped_already_successful": skipped_success,
        "skipped_already_retried": skipped_retried,
        "skipped_missing_shard": skipped_missing_shard,
        "dry_run": dry_run,
        "duration_seconds": round(time.time() - started, 3),
        "group_manifests": group_manifests,
        "candidate": True,
        "serves_truth": False,
        "created_at": _now(),
    }
    _write_json(_retry_root(run_date) / "latest_retry_status.json", manifest)
    return manifest


def run_loop(args: argparse.Namespace) -> dict[str, Any]:
    tick = 0
    latest: dict[str, Any] = {}
    while True:
        tick += 1
        latest = run_once(
            run_date=args.date,
            max_shards=args.max_shards,
            include_retried=args.include_retried,
            retry_if_any_success=args.retry_if_any_success,
            dry_run=args.dry_run,
        )
        latest["tick_index"] = tick
        _write_json(_retry_root(args.date) / "latest_retry_status.json", latest)
        if args.max_ticks and tick >= args.max_ticks:
            break
        if args.once:
            break
        time.sleep(args.interval_seconds)
    return latest


def _self_test() -> int:
    obsolete = _target_for_failure({"provider": "ollama", "model": "glm-4.5", "error": "model not found"})
    kimi = _target_for_failure({"provider": "ollama", "model": "kimi-k2.7-code", "error": "TimeoutError"})
    gemma = _target_for_failure({"provider": "openwebui", "model": "gemma-4-coding", "error": "TimeoutError"})
    ok = (
        obsolete["model"] == "glm-5.2"
        and kimi["model"] == "glm-5.2"
        and gemma["mode"] == "cdp"
        and obsolete["provider"] == "ollama"
    )
    print("PASS - primitive failed shard retry loop maps failures to candidate-only fallbacks." if ok else "FAIL")
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default=_today_utc())
    parser.add_argument("--max-shards", type=int, default=DEFAULT_MAX_SHARDS)
    parser.add_argument("--interval-seconds", type=float, default=DEFAULT_INTERVAL_SECONDS)
    parser.add_argument("--max-ticks", type=int, default=1)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--include-retried", action="store_true")
    parser.add_argument("--retry-if-any-success", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.max_shards <= 0:
        print("FAIL: --max-shards must be positive", file=sys.stderr)
        return 1
    manifest = run_loop(args)
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
