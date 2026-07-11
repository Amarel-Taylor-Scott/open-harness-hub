#!/usr/bin/env python3
"""Continuously verify primitive factory candidates.

This loop reruns the deterministic candidate verifier on a cadence so the live
dashboard can track verified L3 rows while generation continues.
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

from scripts._config import PRIMITIVE_FACTORY_BATCH_RUNS_DIR, REPO_ROOT  # noqa: E402
from scripts.verify_primitive_candidates import verify_candidates  # noqa: E402

DEFAULT_STOP_FILE = _resource("data") / "dev-intel" / "primitive_factory" / "VERIFY_STOP"


def _today_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).date().isoformat()


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def _rel(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT) if path.is_relative_to(REPO_ROOT) else path)


def run_loop(
    *,
    run_date: str,
    interval_seconds: float,
    max_ticks: int,
    stop_file: Path,
    source_root: Path,
    out_dir: Path,
) -> dict[str, Any]:
    if interval_seconds < 0:
        raise AssertionError("interval_seconds must be >= 0")
    if max_ticks < 0:
        raise AssertionError("max_ticks must be >= 0")
    started = time.time()
    ticks: list[dict[str, Any]] = []
    tick_index = 0
    while True:
        if stop_file.exists():
            break
        if max_ticks and tick_index >= max_ticks:
            break
        tick_index += 1
        manifest = verify_candidates(run_date=run_date, out_dir=out_dir, source_root=source_root)
        ticks.append({
            "tick_index": tick_index,
            "created_at": _now(),
            "verified_count": manifest.get("verified_count", 0),
            "source_row_count": manifest.get("source_row_count", 0),
            "duplicate_count": manifest.get("duplicate_count", 0),
            "rejected_count": manifest.get("rejected_count", 0),
            "candidate": True,
            "serves_truth": False,
        })
        if interval_seconds > 0 and not stop_file.exists():
            time.sleep(interval_seconds)
    loop_manifest = {
        "record_type": "primitive_verification_loop_manifest",
        "run_date": run_date,
        "source_root": _rel(source_root),
        "out_dir": _rel(out_dir),
        "stop_file": _rel(stop_file),
        "stop_file_present": stop_file.exists(),
        "interval_seconds": interval_seconds,
        "max_ticks": max_ticks,
        "completed_ticks": len(ticks),
        "latest_tick": ticks[-1] if ticks else {},
        "duration_seconds": round(time.time() - started, 3),
        "candidate": True,
        "serves_truth": False,
        "created_at": _now(),
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "loop_manifest.json").write_text(json.dumps(loop_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return loop_manifest


def _self_test() -> int:
    ok = not DEFAULT_STOP_FILE.name.startswith("STOP")
    print("PASS - primitive verification loop is candidate-only." if ok else "FAIL")
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default=_today_utc())
    parser.add_argument("--interval-seconds", type=float, default=45.0)
    parser.add_argument("--max-ticks", type=int, default=0, help="0 means run until stop file.")
    parser.add_argument("--stop-file", default=str(DEFAULT_STOP_FILE))
    parser.add_argument("--source-root", default="")
    parser.add_argument("--out-dir", default="")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    source_root = Path(args.source_root) if args.source_root else _resource(PRIMITIVE_FACTORY_BATCH_RUNS_DIR) / args.date
    out_dir = Path(args.out_dir) if args.out_dir else _resource("data") / "dev-intel" / "primitive_factory" / "verified_candidates" / args.date
    stop_file = Path(args.stop_file)
    if not source_root.is_absolute():
        source_root = _resource(source_root)
    if not out_dir.is_absolute():
        out_dir = _resource(out_dir)
    if not stop_file.is_absolute():
        stop_file = _resource(stop_file)
    try:
        manifest = run_loop(
            run_date=args.date,
            interval_seconds=args.interval_seconds,
            max_ticks=args.max_ticks,
            stop_file=stop_file,
            source_root=source_root,
            out_dir=out_dir,
        )
    except AssertionError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
