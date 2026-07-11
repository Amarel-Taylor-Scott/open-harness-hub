#!/usr/bin/env python3
"""Build daily work shards for primitive factory useful-candidate targets.

This script does not call models and does not promote truth. It turns the lane
plan into concrete parallel work packets for Codex orchestration, Kimi candidate
writing, GLM contract review, and deterministic validation.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import datetime as dt
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts._config import (
    OPPORTUNITY_INTELLIGENCE_GROUP_CANDIDATES_PATH,
    OPPORTUNITY_INTELLIGENCE_SOURCE_MAP_PATH,
    PRIMITIVE_CANDIDATE_OUTPUT_CONTRACT,
    PRIMITIVE_CANDIDATE_PROMPT_EXAMPLE_ROW,
    PRIMITIVE_FACTORY_20K_DAILY_SHARDS_DIR,
    PRIMITIVE_FACTORY_20K_TARGET_DAILY_RAW,
    PRIMITIVE_FACTORY_20K_TARGET_DAILY_USEFUL,
    PRIMITIVE_FACTORY_20K_TARGET_MULTIPLIER,
    PRIMITIVE_FACTORY_5K_LANES_PATH,
    PRIMITIVE_FACTORY_DAILY_SHARDS_DIR,
    PRIMITIVE_FACTORY_DEFAULT_SHARD_USEFUL_TARGET,
    PRIMITIVE_FACTORY_MODEL_GEMMA_CANDIDATE_WRITER,
    PRIMITIVE_FACTORY_MODEL_GLM_CONTRACT_REVIEWER,
    PRIMITIVE_FACTORY_MODEL_KIMI_CANDIDATE_WRITER,
    PRIMITIVE_FACTORY_TARGET_DAILY_RAW,
    PRIMITIVE_FACTORY_TARGET_DAILY_USEFUL,
    REPO_ROOT,
)

LANES_PATH = _resource(PRIMITIVE_FACTORY_5K_LANES_PATH)
SOURCE_MAP_PATH = _resource(OPPORTUNITY_INTELLIGENCE_SOURCE_MAP_PATH)
GROUP_CANDIDATES_PATH = _resource(OPPORTUNITY_INTELLIGENCE_GROUP_CANDIDATES_PATH)
DEFAULT_OUT_DIR = _resource(PRIMITIVE_FACTORY_DAILY_SHARDS_DIR)
DEFAULT_20K_OUT_DIR = _resource(PRIMITIVE_FACTORY_20K_DAILY_SHARDS_DIR)
TARGET_PROFILES = {
    "5k": {
        "lane_multiplier": 1,
        "configured_raw_target": PRIMITIVE_FACTORY_TARGET_DAILY_RAW,
        "configured_useful_target": PRIMITIVE_FACTORY_TARGET_DAILY_USEFUL,
    },
    "20k": {
        "lane_multiplier": PRIMITIVE_FACTORY_20K_TARGET_MULTIPLIER,
        "configured_raw_target": PRIMITIVE_FACTORY_20K_TARGET_DAILY_RAW,
        "configured_useful_target": PRIMITIVE_FACTORY_20K_TARGET_DAILY_USEFUL,
    },
}

HIGH_LEVERAGE_EDGE_DESCRIPTION_MIN_CHARS = 240
HIGH_LEVERAGE_GROUP_MIN_HIDDEN_EDGES = 5
HIGH_LEVERAGE_TARGET_GROUP_RATIO = 0.65
HIGH_LEVERAGE_REUSE_CLASSES = (
    "multistep_coding_group",
    "long_edge_contract",
    "workflow_route_group",
    "adapter_mutator_chain",
)


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


def _sha(value: Any, *, n: int = 16) -> str:
    data = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(data.encode("utf-8")).hexdigest()[:n]


def _split_count(total: int, parts: int) -> list[int]:
    if parts <= 0:
        raise AssertionError("parts must be positive")
    base, remainder = divmod(total, parts)
    return [base + (1 if index < remainder else 0) for index in range(parts)]


def _rotate(values: list[str], index: int, count: int) -> list[str]:
    if not values:
        return []
    return [values[(index + offset) % len(values)] for offset in range(min(count, len(values)))]


def _source_lookup() -> dict[str, dict[str, Any]]:
    return {str(row.get("id")): row for row in _read_jsonl(SOURCE_MAP_PATH)}


def _group_lookup() -> dict[str, dict[str, Any]]:
    return {str(row.get("primitive_id")): row for row in _read_jsonl(GROUP_CANDIDATES_PATH)}


def _source_refs(source_ids: list[str], sources: dict[str, dict[str, Any]]) -> list[dict[str, str]]:
    refs: list[dict[str, str]] = []
    for source_id in source_ids:
        source = sources.get(source_id, {})
        refs.append({
            "id": source_id,
            "title": str(source.get("title") or source_id),
            "url": str(source.get("url") or ""),
        })
    return refs


def _base_groups(group_ids: list[str], groups: dict[str, dict[str, Any]]) -> list[dict[str, str]]:
    selected: list[dict[str, str]] = []
    for group_id in group_ids:
        group = groups.get(group_id, {})
        selected.append({
            "primitive_id": group_id,
            "title": str(group.get("title") or group_id),
            "input_edge": str(group.get("input_edge") or ""),
            "output_edge": str(group.get("output_edge") or ""),
        })
    return selected


def _candidate_prompt(
    lane: dict[str, Any],
    source_refs: list[dict[str, str]],
    base_groups: list[dict[str, str]],
    *,
    raw_candidate_target: int,
    useful_candidate_target: int,
) -> str:
    source_lines = "; ".join(f"{ref['id']}={ref['url']}" for ref in source_refs)
    group_lines = "; ".join(
        f"{group['primitive_id']}:{group['input_edge']}->{group['output_edge']}"
        for group in base_groups
    )
    return (
        PRIMITIVE_CANDIDATE_OUTPUT_CONTRACT
        + "Generate source-backed primitive or primitive-group candidates as JSONL only. "
        "Start the response with a JSON object. Do not include markdown, prose, or analysis. "
        "Keep candidate=true and serves_truth=false. "
        f"Emit at least {useful_candidate_target} useful rows for this shard; "
        f"do not emit more than {raw_candidate_target} rows. "
        "Prefer compact primitive-group rows when a visible edge can hide 3+ member edges. "
        f"Optimize for high-leverage reuse, not tiny rows: at least {int(HIGH_LEVERAGE_TARGET_GROUP_RATIO * 100)}% "
        "of useful rows should be primitive_group rows or multi-step coding primitives that would save a future "
        "coding model substantial output tokens. "
        f"Lane: {lane['id']}. Sources: {source_lines}. Base groups: {group_lines}. "
        "Each row must pass this deterministic verifier shape exactly: "
        "kind is either primitive or primitive_group, never primitive-group; "
        "contract is a JSON object, never a string, with at least summary, input, output, and errors keys; "
        "edge_contract is a JSON object with input_edge_description, output_edge_description, preconditions, "
        "postconditions, failure_modes, and composition_notes; descriptions should explain what a downstream "
        "coding model needs to compile/link this primitive without seeing implementation internals; "
        f"input_edge_description and output_edge_description should each be at least "
        f"{HIGH_LEVERAGE_EDGE_DESCRIPTION_MIN_CHARS} characters when the route is non-trivial; "
        "edge_contract.composition_notes should contain concrete wiring guidance, adapter choices, idempotency or "
        "receipt handling, and what tests must run before reuse; "
        "blackbox is a concise string, not a boolean; "
        "effects is a non-empty array of objects with type and description; "
        "source_refs is a non-empty array of objects with label and url where url starts with https://; "
        "mutators is a non-empty array of strings or objects; "
        "proof_requirements is an array with at least two concrete tests; "
        "promotion_blockers is a non-empty array; "
        "dedupe_key is stable and edge-shaped. "
        "For kind=primitive_group, group_contract is required as an object with visible_input exactly equal to input_edge, "
        "visible_output exactly equal to output_edge, and hidden_member_edges containing at least three internal member edges; "
        f"prefer at least {HIGH_LEVERAGE_GROUP_MIN_HIDDEN_EDGES} hidden member edges for high-leverage groups. "
        "Add reuse_profile as an object with reuse_class, estimated_saved_output_tokens, reusable_build_tasks, "
        "implementation_surfaces, compile_strategy, and linking_instructions. reuse_class should be one of "
        f"{', '.join(HIGH_LEVERAGE_REUSE_CLASSES)} unless the row is deliberately atomic. "
        "Every row needs primitive_id, kind, title, input_edge, output_edge, input_edge_description, "
        "output_edge_description, edge_contract, contract, group_contract when applicable, blackbox, effects, "
        "source_refs, mutators, proof_requirements, promotion_blockers, reuse_profile, dedupe_key, "
        "candidate=true, serves_truth=false. "
        + PRIMITIVE_CANDIDATE_PROMPT_EXAMPLE_ROW
    )


def _review_prompt(lane: dict[str, Any]) -> str:
    return (
        "Review candidate primitive/group JSONL for missing source refs, weak visible edges, "
        "missing hidden member edges, missing proof requirements, duplicate edge shapes, "
        f"and violations of this lane rejection policy: {lane['rejection_policy']}"
    )


def build_shards(
    *,
    run_date: str,
    shard_useful_target: int,
    target_profile: str = "5k",
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if target_profile not in TARGET_PROFILES:
        raise AssertionError(f"unknown target profile: {target_profile}")
    profile = TARGET_PROFILES[target_profile]
    lane_multiplier = int(profile["lane_multiplier"])
    lanes = _read_jsonl(LANES_PATH)
    sources = _source_lookup()
    groups = _group_lookup()
    shards: list[dict[str, Any]] = []

    raw_total = 0
    useful_total = 0
    for lane in lanes:
        lane_id = str(lane["id"])
        lane_raw = int(lane["daily_raw_candidate_target"]) * lane_multiplier
        lane_useful = int(lane["daily_useful_candidate_target"]) * lane_multiplier
        shard_count = max(1, math.ceil(lane_useful / shard_useful_target))
        raw_counts = _split_count(lane_raw, shard_count)
        useful_counts = _split_count(lane_useful, shard_count)
        lane_source_ids = [str(value) for value in lane["source_ref_ids"]]
        lane_group_ids = [str(value) for value in lane["base_group_ids"]]

        for shard_index in range(shard_count):
            selected_source_ids = _rotate(lane_source_ids, shard_index, 3)
            selected_group_ids = _rotate(lane_group_ids, shard_index, 2)
            selected_sources = _source_refs(selected_source_ids, sources)
            selected_groups = _base_groups(selected_group_ids, groups)
            shard_key = {
                "run_date": run_date,
                "lane_id": lane_id,
                "shard_index": shard_index + 1,
                "source_ref_ids": selected_source_ids,
                "base_group_ids": selected_group_ids,
            }
            shard_id = f"pfs:{run_date.replace('-', '')}:{lane_id}:{shard_index + 1:04d}:{_sha(shard_key, n=10)}"
            shard = {
                "record_type": "primitive_factory_shard",
                "shard_id": shard_id,
                "run_date": run_date,
                "lane_id": lane_id,
                "lane_title": lane["title"],
                "shard_index": shard_index + 1,
                "shard_count": shard_count,
                "raw_candidate_target": raw_counts[shard_index],
                "useful_candidate_target": useful_counts[shard_index],
                "target_candidate_level": lane["target_candidate_level"],
                "minimum_group_ratio": lane["minimum_group_ratio"],
                "output_mix": lane["output_mix"],
                "source_ref_ids": selected_source_ids,
                "source_refs": selected_sources,
                "base_group_ids": selected_group_ids,
                "base_groups": selected_groups,
                "model_roles": lane["model_roles"],
                "auxiliary_model_roles": {
                    "openwebui_gemma_candidate_writer": PRIMITIVE_FACTORY_MODEL_GEMMA_CANDIDATE_WRITER,
                },
                "deterministic_validators": lane["deterministic_validators"],
                "usefulness_gates": lane["usefulness_gates"],
                "proof_gates": lane["proof_gates"],
                "acceptance_criteria": [
                    "emit_jsonl_only",
                    "source_ref_resolution",
                    "visible_edge_contract",
                    "long_edge_descriptions_for_nontrivial_routes",
                    "reuse_profile_attached",
                    "high_leverage_primitive_groups_preferred",
                    "proof_plan_attached",
                    "dedupe_key_attached",
                    "candidate_true_serves_truth_false",
                ],
                "high_leverage_requirements": {
                    "target_group_ratio": HIGH_LEVERAGE_TARGET_GROUP_RATIO,
                    "edge_description_min_chars": HIGH_LEVERAGE_EDGE_DESCRIPTION_MIN_CHARS,
                    "preferred_group_min_hidden_edges": HIGH_LEVERAGE_GROUP_MIN_HIDDEN_EDGES,
                    "reuse_classes": list(HIGH_LEVERAGE_REUSE_CLASSES),
                    "candidate": True,
                    "serves_truth": False,
                },
                "artifact_outputs": [
                    "candidate_cards.jsonl",
                    "proof_plans.jsonl",
                    "review_findings.jsonl",
                    "rejected.jsonl",
                ],
                "candidate_writer_prompt": _candidate_prompt(
                    lane,
                    selected_sources,
                    selected_groups,
                    raw_candidate_target=raw_counts[shard_index],
                    useful_candidate_target=useful_counts[shard_index],
                ),
                "contract_reviewer_prompt": _review_prompt(lane),
                "dedupe_namespace": _sha({"lane": lane_id, "date": run_date, "sources": selected_source_ids}),
                "status": "planned",
                "candidate": True,
                "serves_truth": False,
            }
            shards.append(shard)
            raw_total += raw_counts[shard_index]
            useful_total += useful_counts[shard_index]

    manifest = {
        "record_type": "primitive_factory_daily_shard_manifest",
        "target_profile": target_profile,
        "lane_multiplier": lane_multiplier,
        "run_date": run_date,
        "lane_count": len(lanes),
        "shard_count": len(shards),
        "daily_raw_candidate_target": raw_total,
        "daily_useful_candidate_target": useful_total,
        "configured_daily_raw_target": profile["configured_raw_target"],
        "configured_daily_useful_target": profile["configured_useful_target"],
        "shard_useful_target": shard_useful_target,
        "candidate_writer_model": PRIMITIVE_FACTORY_MODEL_KIMI_CANDIDATE_WRITER,
        "auxiliary_candidate_writer_model": PRIMITIVE_FACTORY_MODEL_GEMMA_CANDIDATE_WRITER,
        "contract_reviewer_model": PRIMITIVE_FACTORY_MODEL_GLM_CONTRACT_REVIEWER,
        "candidate_boundary": "candidate=true; serves_truth=false",
        "candidate": True,
        "serves_truth": False,
    }
    if raw_total < int(profile["configured_raw_target"]):
        raise AssertionError("daily raw candidate target is below configured target")
    if useful_total < int(profile["configured_useful_target"]):
        raise AssertionError("daily useful candidate target is below configured target")
    return shards, manifest


def write_run(run_date: str, shards: list[dict[str, Any]], manifest: dict[str, Any], out_dir: Path) -> dict[str, str]:
    run_dir = out_dir / run_date
    run_dir.mkdir(parents=True, exist_ok=True)
    shards_path = run_dir / "shards.jsonl"
    manifest_path = run_dir / "manifest.json"
    shards_path.write_text(
        "".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in shards),
        encoding="utf-8",
    )
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "run_dir": str(run_dir.relative_to(REPO_ROOT)),
        "shards_path": str(shards_path.relative_to(REPO_ROOT)),
        "manifest_path": str(manifest_path.relative_to(REPO_ROOT)),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default=_today_utc())
    parser.add_argument("--target-profile", choices=sorted(TARGET_PROFILES), default="5k")
    parser.add_argument("--shard-useful-target", type=int, default=PRIMITIVE_FACTORY_DEFAULT_SHARD_USEFUL_TARGET)
    parser.add_argument("--out-dir", default="")
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args(argv)

    if args.shard_useful_target <= 0:
        print("FAIL: --shard-useful-target must be positive", file=sys.stderr)
        return 1

    try:
        shards, manifest = build_shards(
            run_date=args.date,
            shard_useful_target=args.shard_useful_target,
            target_profile=args.target_profile,
        )
        default_out = DEFAULT_20K_OUT_DIR if args.target_profile == "20k" else DEFAULT_OUT_DIR
        paths = {} if args.check_only else write_run(args.date, shards, manifest, Path(args.out_dir) if args.out_dir else default_out)
    except AssertionError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    print(json.dumps({**manifest, **paths}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
