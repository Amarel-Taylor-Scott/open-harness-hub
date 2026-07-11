#!/usr/bin/env python3
"""Validate generated daily primitive-factory shards."""
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

from scripts._config import (
    PRIMITIVE_FACTORY_5K_LANES_PATH,
    PRIMITIVE_FACTORY_DAILY_SHARDS_DIR,
    PRIMITIVE_FACTORY_MODEL_GLM_CONTRACT_REVIEWER,
    PRIMITIVE_FACTORY_MODEL_KIMI_CANDIDATE_WRITER,
    PRIMITIVE_FACTORY_REQUIRED_MODEL_ROLES,
    PRIMITIVE_FACTORY_TARGET_DAILY_RAW,
    PRIMITIVE_FACTORY_TARGET_DAILY_USEFUL,
    REPO_ROOT,
)

LANES_PATH = _resource(PRIMITIVE_FACTORY_5K_LANES_PATH)
DEFAULT_SHARDS_DIR = _resource(PRIMITIVE_FACTORY_DAILY_SHARDS_DIR)


def _today_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).date().isoformat()


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


def _lane_ids() -> set[str]:
    return {str(row.get("id")) for row in _read_jsonl(LANES_PATH)}


def self_test(*, run_date: str, shards_dir: Path) -> dict[str, Any]:
    run_dir = shards_dir / run_date
    manifest = _read_json(run_dir / "manifest.json")
    shards = _read_jsonl(run_dir / "shards.jsonl")
    known_lane_ids = _lane_ids()
    required_roles = set(PRIMITIVE_FACTORY_REQUIRED_MODEL_ROLES)

    if manifest.get("candidate") is not True or manifest.get("serves_truth") is not False:
        raise AssertionError("manifest must keep candidate=true and serves_truth=false")
    if manifest.get("candidate_writer_model") != PRIMITIVE_FACTORY_MODEL_KIMI_CANDIDATE_WRITER:
        raise AssertionError("manifest must use configured Kimi candidate writer")
    if manifest.get("contract_reviewer_model") != PRIMITIVE_FACTORY_MODEL_GLM_CONTRACT_REVIEWER:
        raise AssertionError("manifest must use configured GLM contract reviewer")

    raw_total = 0
    useful_total = 0
    shard_ids: list[str] = []
    lane_ids: set[str] = set()
    for row in shards:
        shard_id = str(row.get("shard_id") or "")
        if not shard_id:
            raise AssertionError("each shard must declare shard_id")
        shard_ids.append(shard_id)
        lane_id = str(row.get("lane_id") or "")
        if lane_id not in known_lane_ids:
            raise AssertionError(f"{shard_id} references unknown lane_id {lane_id!r}")
        lane_ids.add(lane_id)
        if row.get("candidate") is not True or row.get("serves_truth") is not False:
            raise AssertionError(f"{shard_id} must keep candidate=true and serves_truth=false")
        raw_target = int(row.get("raw_candidate_target") or 0)
        useful_target = int(row.get("useful_candidate_target") or 0)
        if raw_target <= 0 or useful_target <= 0 or raw_target < useful_target:
            raise AssertionError(f"{shard_id} must declare valid raw/useful targets")
        raw_total += raw_target
        useful_total += useful_target
        if not row.get("source_ref_ids") or not row.get("source_refs"):
            raise AssertionError(f"{shard_id} must carry source refs")
        if not row.get("base_group_ids") or not row.get("base_groups"):
            raise AssertionError(f"{shard_id} must carry base groups")
        roles = row.get("model_roles")
        if not isinstance(roles, dict):
            raise AssertionError(f"{shard_id} must carry model_roles")
        missing_roles = required_roles - set(roles)
        if missing_roles:
            raise AssertionError(f"{shard_id} missing model roles: {sorted(missing_roles)}")
        if roles.get("kimi_candidate_writer") != PRIMITIVE_FACTORY_MODEL_KIMI_CANDIDATE_WRITER:
            raise AssertionError(f"{shard_id} must use configured Kimi candidate writer")
        if roles.get("glm_contract_reviewer") != PRIMITIVE_FACTORY_MODEL_GLM_CONTRACT_REVIEWER:
            raise AssertionError(f"{shard_id} must use configured GLM contract reviewer")
        acceptance = set(row.get("acceptance_criteria") or [])
        if "candidate_true_serves_truth_false" not in acceptance:
            raise AssertionError(f"{shard_id} must enforce candidate/truth boundary acceptance")
        if not row.get("candidate_writer_prompt") or not row.get("contract_reviewer_prompt"):
            raise AssertionError(f"{shard_id} must include writer and reviewer prompts")

    if len(shard_ids) != len(set(shard_ids)):
        raise AssertionError("shard ids must be unique")
    if len(shards) != int(manifest.get("shard_count") or -1):
        raise AssertionError("manifest shard_count must match shard rows")
    if raw_total != int(manifest.get("daily_raw_candidate_target") or -1):
        raise AssertionError("manifest raw target must match shard row total")
    if useful_total != int(manifest.get("daily_useful_candidate_target") or -1):
        raise AssertionError("manifest useful target must match shard row total")
    configured_raw = int(manifest.get("configured_daily_raw_target") or PRIMITIVE_FACTORY_TARGET_DAILY_RAW)
    configured_useful = int(manifest.get("configured_daily_useful_target") or PRIMITIVE_FACTORY_TARGET_DAILY_USEFUL)
    if raw_total < configured_raw:
        raise AssertionError("daily raw target is below configured target")
    if useful_total < configured_useful:
        raise AssertionError("daily useful target is below configured target")

    return {
        "run_date": run_date,
        "shards": len(shards),
        "lanes_covered": len(lane_ids),
        "daily_raw_candidate_target": raw_total,
        "daily_useful_candidate_target": useful_total,
        "configured_daily_raw_target": configured_raw,
        "configured_daily_useful_target": configured_useful,
        "candidate_boundary": "candidate=true; serves_truth=false",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default=_today_utc())
    parser.add_argument("--shards-dir", default=str(DEFAULT_SHARDS_DIR))
    args = parser.parse_args(argv)

    try:
        result = self_test(run_date=args.date, shards_dir=Path(args.shards_dir))
    except AssertionError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
