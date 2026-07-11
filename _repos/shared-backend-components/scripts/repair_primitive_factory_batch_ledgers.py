#!/usr/bin/env python3
"""Repair primitive-factory batch ledgers after dry-run pollution.

Dry-run rows are useful for planning but should not affect live aggregate
metrics. This utility removes dry-run rows from provider ledgers and rebuilds
the live manifest from the remaining rows.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts._config import (  # noqa: E402
    PRIMITIVE_FACTORY_20K_DAILY_SHARDS_DIR,
    PRIMITIVE_FACTORY_BATCH_RUNS_DIR,
    PRIMITIVE_FACTORY_DAILY_SHARDS_DIR,
    REPO_ROOT,
)


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def _rel(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT) if path.is_relative_to(REPO_ROOT) else path)


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        raise AssertionError(f"missing JSONL file: {path}")
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise AssertionError(f"{path}:{line_number}: expected object")
        rows.append(value)
    return rows


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _default_shards_path(run_date: str, target_profile: str) -> Path:
    base = PRIMITIVE_FACTORY_20K_DAILY_SHARDS_DIR if target_profile == "20k" else PRIMITIVE_FACTORY_DAILY_SHARDS_DIR
    return _resource(base) / run_date / "shards.jsonl"


def _sum_usage(rows: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "prompt_tokens": sum(int((row.get("usage") or {}).get("prompt_tokens") or 0) for row in rows),
        "completion_tokens": sum(int((row.get("usage") or {}).get("completion_tokens") or 0) for row in rows),
        "total_tokens": sum(int((row.get("usage") or {}).get("total_tokens") or 0) for row in rows),
    }


def repair_run_root(run_root: Path) -> dict[str, Any]:
    ledger_path = run_root / "batch_ledger.jsonl"
    rows = _read_jsonl(ledger_path)
    live_rows = sorted(
        [
            row for row in rows
            if not row.get("dry_run")
            and not (
                int(row.get("worker_error_count") or 0) > 0
                and int(row.get("accepted_count") or 0) == 0
                and int((row.get("usage") or {}).get("total_tokens") or 0) == 0
            )
        ],
        key=lambda row: int(row.get("offset") or 0),
    )
    removed = len(rows) - len(live_rows)
    _write_jsonl(ledger_path, live_rows)
    total_usage = _sum_usage(live_rows)
    duration = round(sum(float(row.get("duration_seconds") or 0) for row in live_rows), 3)
    accepted = sum(int(row.get("accepted_count") or 0) for row in live_rows)
    selected = sum(int(row.get("selected_shards") or 0) for row in live_rows)
    first = live_rows[0] if live_rows else {}
    last = live_rows[-1] if live_rows else {}
    run_date = str(first.get("run_date") or "")
    target_profile = str(first.get("target_profile") or "")
    shards_path = _default_shards_path(run_date, target_profile) if run_date and target_profile else Path()
    available_shards = (
        sum(1 for line in shards_path.read_text(encoding="utf-8").splitlines() if line.strip())
        if shards_path.exists() else 0
    )
    manifest = {
        "record_type": "primitive_factory_batch_loop_manifest",
        "run_date": run_date,
        "target_profile": target_profile,
        "shards_path": _rel(shards_path) if shards_path.exists() else "",
        "out_root": _rel(run_root),
        "ledger_path": _rel(ledger_path),
        "available_shards": available_shards,
        "completed_batches": len(live_rows),
        "selected_shards": selected,
        "start_offset": first.get("offset", 0),
        "next_offset": int(last.get("offset") or 0) + int(last.get("limit") or 0) if live_rows else 0,
        "batch_size": last.get("limit", 0),
        "workers": last.get("workers", 0),
        "provider": first.get("provider", ""),
        "model": first.get("model", ""),
        "mode": first.get("mode", ""),
        "dry_run": False,
        "worker_error_count": sum(int(row.get("worker_error_count") or 0) for row in live_rows),
        "accepted_count": accepted,
        "rejected_count": sum(int(row.get("rejected_count") or 0) for row in live_rows),
        "usage": total_usage,
        "duration_seconds": duration,
        "invocation_duration_seconds": 0,
        "aggregate_completion_tps": (
            round(total_usage["completion_tokens"] / duration, 3)
            if duration and total_usage["completion_tokens"] else 0
        ),
        "aggregate_total_tps": (
            round(total_usage["total_tokens"] / duration, 3)
            if duration and total_usage["total_tokens"] else 0
        ),
        "accepted_per_shard": round(accepted / selected, 3) if selected else 0,
        "accepted_per_1k_total_tokens": (
            round(accepted * 1000 / total_usage["total_tokens"], 3)
            if total_usage["total_tokens"] else 0
        ),
        "created_at": _now(),
        "candidate": True,
        "serves_truth": False,
        "repair_removed_nonlive_rows": removed,
    }
    (run_root / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def _self_test() -> int:
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        ledger = root / "batch_ledger.jsonl"
        _write_jsonl(ledger, [
            {"offset": 0, "limit": 1, "selected_shards": 1, "accepted_count": 2, "usage": {"total_tokens": 10}, "duration_seconds": 1, "dry_run": False, "run_date": "2026-07-01", "target_profile": "20k", "provider": "x", "model": "m", "mode": "direct"},
            {"offset": 1, "limit": 1, "selected_shards": 1, "accepted_count": 0, "usage": {}, "duration_seconds": 0, "dry_run": True},
        ])
        manifest = repair_run_root(root)
        ok = manifest["repair_removed_nonlive_rows"] == 1 and manifest["accepted_count"] == 2
    print("PASS - primitive factory batch ledger repair removes dry-run rows." if ok else "FAIL")
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_roots", nargs="*")
    parser.add_argument("--date", default="")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)

    if args.self_test:
        return _self_test()

    roots = [Path(value) for value in args.run_roots]
    if not roots:
        if not args.date:
            print("FAIL: pass run roots or --date", file=sys.stderr)
            return 1
        roots = sorted((_resource(PRIMITIVE_FACTORY_BATCH_RUNS_DIR) / args.date).glob("20k_*"))
    repaired = []
    try:
        for root in roots:
            if not root.is_absolute():
                root = _resource(root)
            if (root / "batch_ledger.jsonl").exists():
                repaired.append(repair_run_root(root))
    except AssertionError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({"repaired": repaired, "candidate": True, "serves_truth": False}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
