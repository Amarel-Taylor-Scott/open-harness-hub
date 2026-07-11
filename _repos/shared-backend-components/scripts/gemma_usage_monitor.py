#!/usr/bin/env python3
"""Monitor Open WebUI Gemma primitive-factory usage.

The monitor reads local candidate-generation artifacts and process state. It
does not call the model by default and never promotes model output to truth.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import datetime as dt
import html
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts._config import (  # noqa: E402
    OPENWEBUI_CDP_URL_ENV,
    OPENWEBUI_DEFAULT_BASE_URL,
    OPENWEBUI_DEFAULT_MODEL,
    PRIMITIVE_FACTORY_BATCH_RUNS_DIR,
    PRIMITIVE_FACTORY_FLEET_RUNS_DIR,
    PRIMITIVE_FACTORY_GEMMA_MONITOR_DEFAULT_PORT,
    PRIMITIVE_FACTORY_MODEL_GEMMA_CANDIDATE_WRITER,
    PRIMITIVE_FACTORY_MONITOR_DIST_DIR,
    PRIMITIVE_FACTORY_MONITOR_REFRESH_SECONDS,
    REPO_ROOT,
)
from scripts.verify_primitive_candidates import (  # noqa: E402
    _source_urls as _verification_source_urls,
    _valid_public_source_url as _verification_valid_public_source_url,
)

FACTORY_PROCESS_TERMS = (
    "run_primitive_provider_fleet_loop.py",
    "run_primitive_factory_batch_loop.py",
    "run_primitive_factory_model_worker.py",
)
CHROME_CDP_PROCESS_TERMS = ("--remote-debugging-port", "ui.iamretarded.net", "Open WebUI")
SOURCE_MATERIAL_FILES: tuple[tuple[str, str], ...] = (
    ("primitive_source_surfaces", "catalog/knowledge-packs/data/primitive-source-surface-map/surfaces.jsonl"),
    ("opportunity_sources", "catalog/knowledge-packs/data/opportunity-intelligence-source-map/sources.jsonl"),
    ("occupation_sources", "catalog/knowledge-packs/data/occupation-source-surface-map/surfaces.jsonl"),
    ("standards_sources", "catalog/knowledge-packs/data/standards-regulatory-source-map/surfaces.jsonl"),
    ("source_search_seeds", "catalog/knowledge-packs/data/aidevobserver-source-discovery-search-seeds/search-topics.jsonl"),
    ("rss_feeds", "catalog/knowledge-packs/data/aidevobserver-rss-source-feeds/feeds.jsonl"),
    ("markdown_indexes", "catalog/knowledge-packs/data/aidevobserver-markdown-index-sources/indexes.jsonl"),
    ("multilingual_scopes", "catalog/knowledge-packs/data/aidevobserver-multilingual-search-scopes/scopes.jsonl"),
    ("real_world_tasks", "catalog/knowledge-packs/data/aidevexplorer-real-world-build-tasks/tasks.jsonl"),
    ("business_scopes", "catalog/knowledge-packs/data/aidevobserver-business-operation-scopes/scopes.jsonl"),
    ("public_blueprints", "catalog/knowledge-packs/data/public-source-blueprint-catalog/blueprints.jsonl"),
    ("workflow_inspiration", "catalog/knowledge-packs/data/workflow-builder-inspiration/patterns.jsonl"),
    ("cross_domain_use_cases", "catalog/knowledge-packs/data/cross-domain-use-case-seeds/seeds.jsonl"),
    ("primitive_factory_lanes", "catalog/knowledge-packs/data/primitive-factory-5k-lanes/lanes.jsonl"),
    ("primitive_throughput_lanes", "catalog/knowledge-packs/data/primitive-throughput-lanes/lanes.jsonl"),
    ("context_source_candidates", "data/dev-intel/aidevobserver_context_foundry/source_candidates.jsonl"),
    ("context_candidate_rankings", "data/dev-intel/aidevobserver_context_foundry/candidate_rankings.jsonl"),
    ("context_primitive_drafts", "data/dev-intel/aidevobserver_context_foundry/primitive_drafts.jsonl"),
    ("source_lifecycle_search_cards", "data/dev-intel/primitive_source_lifecycle/primitive_search_cards.jsonl"),
    ("source_lifecycle_vector_export", "data/dev-intel/primitive_source_lifecycle/primitive_vector_export.jsonl"),
)


def _today_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).date().isoformat()


def _now_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"_read_error": "invalid_json", "_path": _rel(path)}
    return value if isinstance(value, dict) else {"_read_error": "not_object", "_path": _rel(path)}


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict):
            rows.append(row)
    return rows


def _count_jsonl_rows(path: Path) -> int:
    if not path.exists():
        return 0
    count = 0
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.strip():
            count += 1
    return count


def _count_jsonl_files(root: Path) -> tuple[int, int]:
    file_count = 0
    row_count = 0
    if not root.exists():
        return 0, 0
    for path in root.rglob("*.jsonl"):
        file_count += 1
        row_count += _count_jsonl_rows(path)
    return file_count, row_count


def _file_age_seconds(path: Path) -> float | None:
    if not path.exists():
        return None
    return round(time.time() - path.stat().st_mtime, 3)


def _usage(row: dict[str, Any]) -> dict[str, int]:
    usage = row.get("usage") if isinstance(row.get("usage"), dict) else {}
    return {
        "prompt_tokens": int(usage.get("prompt_tokens") or 0),
        "completion_tokens": int(usage.get("completion_tokens") or 0),
        "total_tokens": int(usage.get("total_tokens") or 0),
    }


def _sum_usage(rows: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "prompt_tokens": sum(_usage(row)["prompt_tokens"] for row in rows),
        "completion_tokens": sum(_usage(row)["completion_tokens"] for row in rows),
        "total_tokens": sum(_usage(row)["total_tokens"] for row in rows),
    }


def _safe_rate(numerator: float, denominator: float) -> float:
    return round(numerator / denominator, 3) if denominator else 0.0


def _short_text(value: Any, *, limit: int = 180) -> str:
    text = str(value or "")
    return text if len(text) <= limit else text[:limit - 3] + "..."


def _batch_root(run_date: str) -> Path:
    return _resource(PRIMITIVE_FACTORY_BATCH_RUNS_DIR) / run_date


def _fleet_root(run_date: str) -> Path:
    return _resource(PRIMITIVE_FACTORY_FLEET_RUNS_DIR) / run_date


def _verification_manifest_path(run_date: str) -> Path:
    return _resource("data") / "dev-intel" / "primitive_factory" / "verified_candidates" / run_date / "manifest.json"


def _verification_root() -> Path:
    return _resource("data") / "dev-intel" / "primitive_factory" / "verified_candidates"


def discover_run_dates(prefix: str) -> list[str]:
    if not prefix:
        return []
    names: set[str] = set()
    roots = [
        _resource(PRIMITIVE_FACTORY_BATCH_RUNS_DIR),
        _resource(PRIMITIVE_FACTORY_FLEET_RUNS_DIR),
        _verification_root(),
    ]
    for root in roots:
        if not root.exists():
            continue
        for path in root.glob(prefix + "*"):
            if path.is_dir():
                names.add(path.name)
    return sorted(names)


def resolve_run_date(run_date: str, aggregate_prefix: str = "") -> str:
    if run_date not in {"latest", "latest-active"}:
        return run_date
    prefix = aggregate_prefix or _today_utc()
    candidates = discover_run_dates(prefix)
    if not candidates:
        return prefix
    return candidates[-1]


def _is_gemma_manifest(manifest: dict[str, Any]) -> bool:
    return (
        str(manifest.get("provider") or "") == "openwebui"
        and str(manifest.get("model") or "") in {OPENWEBUI_DEFAULT_MODEL, PRIMITIVE_FACTORY_MODEL_GEMMA_CANDIDATE_WRITER}
    )


def _manifest_record(path: Path) -> dict[str, Any]:
    manifest = _read_json(path)
    usage = _usage(manifest)
    return {
        "path": _rel(path),
        "out_root": manifest.get("out_root") or _rel(path.parent),
        "provider": manifest.get("provider"),
        "model": manifest.get("model"),
        "mode": manifest.get("mode"),
        "workers": int(manifest.get("workers") or 0),
        "completed_batches": int(manifest.get("completed_batches") or 0),
        "selected_shards": int(manifest.get("selected_shards") or 0),
        "accepted_count": int(manifest.get("accepted_count") or 0),
        "rejected_count": int(manifest.get("rejected_count") or 0),
        "worker_error_count": int(manifest.get("worker_error_count") or manifest.get("error_count") or 0),
        "usage": usage,
        "duration_seconds": float(manifest.get("duration_seconds") or 0),
        "aggregate_completion_tps": float(manifest.get("aggregate_completion_tps") or 0),
        "aggregate_total_tps": float(manifest.get("aggregate_total_tps") or 0),
        "accepted_per_shard": float(manifest.get("accepted_per_shard") or 0),
        "accepted_per_1k_total_tokens": float(manifest.get("accepted_per_1k_total_tokens") or 0),
        "next_offset": int(manifest.get("next_offset") or 0),
        "created_at": manifest.get("created_at"),
        "age_seconds": _file_age_seconds(path),
        "candidate": manifest.get("candidate") is True,
        "serves_truth": manifest.get("serves_truth") is True,
        "read_error": manifest.get("_read_error"),
    }


def load_batch_manifests(run_date: str, *, gemma_only: bool) -> list[dict[str, Any]]:
    root = _batch_root(run_date)
    records: list[dict[str, Any]] = []
    for path in sorted(root.glob("*/manifest.json")):
        manifest = _read_json(path)
        if gemma_only and not _is_gemma_manifest(manifest):
            continue
        records.append(_manifest_record(path))
    return records


def load_recent_worker_batches(run_date: str, *, limit: int = 12) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(_batch_root(run_date).glob("*/batch_*/model/manifest.json")):
        manifest = _read_json(path)
        if not _is_gemma_manifest(manifest):
            continue
        usage = _usage(manifest)
        rows.append({
            "path": _rel(path),
            "batch": path.parents[1].name,
            "provider": manifest.get("provider"),
            "model": manifest.get("model"),
            "mode": manifest.get("mode"),
            "dry_run": manifest.get("dry_run") is True,
            "workers": int(manifest.get("workers") or 0),
            "selected_shards": int(manifest.get("selected_shards") or 0),
            "error_count": int(manifest.get("error_count") or 0),
            "usage": usage,
            "duration_seconds": float(manifest.get("duration_seconds") or 0),
            "aggregate_completion_tps": float(manifest.get("aggregate_completion_tps") or 0),
            "aggregate_total_tps": float(manifest.get("aggregate_total_tps") or 0),
            "age_seconds": _file_age_seconds(path),
            "mtime": path.stat().st_mtime if path.exists() else 0,
            "candidate": manifest.get("candidate") is True,
            "serves_truth": manifest.get("serves_truth") is True,
        })
    rows.sort(key=lambda row: float(row.get("mtime") or 0), reverse=True)
    for row in rows:
        row.pop("mtime", None)
    return rows[:limit]


def summarize_recent_gemma_health(recent_batches: list[dict[str, Any]], *, window: int = 6) -> dict[str, Any]:
    rows = recent_batches[:max(1, window)]
    selected = sum(int(row.get("selected_shards") or 0) for row in rows)
    errors = sum(int(row.get("error_count") or 0) for row in rows)
    usage = _sum_usage(rows)
    duration = sum(float(row.get("duration_seconds") or 0) for row in rows)
    latest = rows[0] if rows else {}
    latest_errors = int(latest.get("error_count") or 0)
    latest_selected = int(latest.get("selected_shards") or 0)
    historical_error_seen = any(int(row.get("error_count") or 0) > 0 for row in recent_batches[1:])
    return {
        "window": len(rows),
        "latest_batch": latest.get("batch") or "",
        "latest_selected_shards": latest_selected,
        "latest_error_count": latest_errors,
        "latest_total_tokens": int((latest.get("usage") or {}).get("total_tokens") or 0),
        "latest_total_tps": float(latest.get("aggregate_total_tps") or 0),
        "latest_age_seconds": latest.get("age_seconds"),
        "latest_ok": bool(latest_selected) and latest_errors == 0,
        "recent_selected_shards": selected,
        "recent_error_count": errors,
        "recent_error_rate_per_shard": _safe_rate(float(errors), float(selected)),
        "recent_total_tokens": usage["total_tokens"],
        "recent_total_tps_weighted": _safe_rate(float(usage["total_tokens"]), duration),
        "historical_error_seen": historical_error_seen,
        "recovered_after_error": bool(latest_selected) and latest_errors == 0 and historical_error_seen,
        "candidate": True,
        "serves_truth": False,
    }


def summarize_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    usage = _sum_usage(records)
    duration = sum(float(row.get("duration_seconds") or 0) for row in records)
    accepted = sum(int(row.get("accepted_count") or 0) for row in records)
    selected = sum(int(row.get("selected_shards") or 0) for row in records)
    rejected = sum(int(row.get("rejected_count") or 0) for row in records)
    errors = sum(int(row.get("worker_error_count") or 0) for row in records)
    workers_configured = sum(int(row.get("workers") or 0) for row in records)
    return {
        "manifests": len(records),
        "workers_configured_sum": workers_configured,
        "selected_shards": selected,
        "accepted_count": accepted,
        "rejected_count": rejected,
        "worker_error_count": errors,
        "usage": usage,
        "duration_seconds_sum": round(duration, 3),
        "completion_tps_weighted": _safe_rate(float(usage["completion_tokens"]), duration),
        "total_tps_weighted": _safe_rate(float(usage["total_tokens"]), duration),
        "accepted_per_shard": _safe_rate(float(accepted), float(selected)),
        "accepted_per_1k_total_tokens": _safe_rate(float(accepted) * 1000.0, float(usage["total_tokens"])),
        "candidate": True,
        "serves_truth": False,
    }


def load_fleet_status(run_date: str) -> dict[str, Any]:
    root = _fleet_root(run_date)
    loop_paths = sorted(
        root.glob("**/loop_manifest.json"),
        key=lambda path: path.stat().st_mtime if path.exists() else 0,
        reverse=True,
    )
    legacy_loop_path = root / "loop_manifest.json"
    if legacy_loop_path.exists() and legacy_loop_path not in loop_paths:
        loop_paths.append(legacy_loop_path)
    loops: list[dict[str, Any]] = []
    compact_lanes = []
    newest_loop: dict[str, Any] = {}
    newest_path = loop_paths[0] if loop_paths else legacy_loop_path
    for loop_path in loop_paths:
        loop = _read_json(loop_path)
        if not newest_loop:
            newest_loop = loop
        cycles = loop.get("cycles") if isinstance(loop.get("cycles"), list) else []
        latest_cycle = cycles[-1] if cycles else {}
        lane_results = latest_cycle.get("lane_results") if isinstance(latest_cycle.get("lane_results"), list) else []
        loops.append({
            "loop_manifest_path": _rel(loop_path),
            "loop_manifest_age_seconds": _file_age_seconds(loop_path),
            "run_label": loop.get("run_label") or loop_path.parent.name,
            "completed_cycles": int(loop.get("completed_cycles") or 0),
            "duration_seconds": float(loop.get("duration_seconds") or 0),
            "stop_file_present": loop.get("stop_file_present"),
            "dry_run": loop.get("dry_run"),
            "latest_cycle_index": latest_cycle.get("cycle_index"),
            "latest_cycle_duration_seconds": latest_cycle.get("duration_seconds"),
            "latest_cycle_returncode_max": latest_cycle.get("returncode_max"),
            "candidate": loop.get("candidate") is True or not loop,
            "serves_truth": loop.get("serves_truth") is True,
            "read_error": loop.get("_read_error"),
        })
        run_label = loop.get("run_label") or loop_path.parent.name
        for lane in lane_results:
            if not isinstance(lane, dict):
                continue
            batch_manifest = lane.get("batch_manifest") if isinstance(lane.get("batch_manifest"), dict) else {}
            compact_lanes.append({
                "run_label": run_label,
                "lane_id": lane.get("lane_id"),
                "provider": lane.get("provider"),
                "model": lane.get("model"),
                "mode": lane.get("mode"),
                "returncode": lane.get("returncode"),
                "planned_shards": lane.get("planned_shards"),
                "start_offset": lane.get("start_offset"),
                "end_offset_exclusive": lane.get("end_offset_exclusive"),
                "duration_seconds": lane.get("duration_seconds"),
                "log_path": lane.get("log_path"),
                "batch_manifest_path": lane.get("batch_manifest_path"),
                "accepted_count": batch_manifest.get("accepted_count"),
                "worker_error_count": batch_manifest.get("worker_error_count"),
                "usage": batch_manifest.get("usage") or {},
                "candidate": lane.get("candidate") is True,
                "serves_truth": lane.get("serves_truth") is True,
            })
    loop = newest_loop
    latest_cycle = {}
    if isinstance(loop.get("cycles"), list) and loop["cycles"]:
        latest_cycle = loop["cycles"][-1]
    compact_lanes.sort(key=lambda row: str(row.get("run_label") or "") + ":" + str(row.get("lane_id") or ""))
    return {
        "loop_manifest_path": _rel(newest_path),
        "loop_manifest_age_seconds": _file_age_seconds(newest_path),
        "completed_cycles": int(loop.get("completed_cycles") or 0),
        "duration_seconds": float(loop.get("duration_seconds") or 0),
        "stop_file_present": loop.get("stop_file_present"),
        "dry_run": loop.get("dry_run"),
        "loops": loops,
        "latest_cycle_index": latest_cycle.get("cycle_index"),
        "latest_cycle_duration_seconds": latest_cycle.get("duration_seconds"),
        "latest_cycle_returncode_max": latest_cycle.get("returncode_max"),
        "latest_lane_results": compact_lanes,
        "candidate": loop.get("candidate") is True or not loop,
        "serves_truth": loop.get("serves_truth") is True,
        "read_error": loop.get("_read_error"),
    }


def load_verification_status(run_date: str) -> dict[str, Any]:
    path = _verification_manifest_path(run_date)
    manifest = _read_json(path)
    verified = int(manifest.get("verified_count") or 0)
    source_rows = int(manifest.get("source_row_count") or 0)
    rejected = int(manifest.get("rejected_count") or 0)
    duplicates = int(manifest.get("duplicate_count") or 0)
    return {
        "manifest_path": _rel(path),
        "manifest_age_seconds": _file_age_seconds(path),
        "source_row_count": source_rows,
        "verified_count": verified,
        "duplicate_count": duplicates,
        "rejected_count": rejected,
        "verified_ratio": _safe_rate(float(verified), float(source_rows)),
        "verified_per_20k_source_rows": _safe_rate(float(verified) * 20000.0, float(source_rows)),
        "verified_candidate_level": manifest.get("verified_candidate_level") or "",
        "verified_path": manifest.get("verified_path") or "",
        "candidate": manifest.get("candidate") is True or not manifest,
        "serves_truth": manifest.get("serves_truth") is True,
        "read_error": manifest.get("_read_error"),
    }


def load_verification_aggregate(date_prefix: str) -> dict[str, Any]:
    run_dates = discover_run_dates(date_prefix)
    totals = {
        "source_row_count": 0,
        "verified_count": 0,
        "duplicate_count": 0,
        "rejected_count": 0,
    }
    kind_counts: dict[str, int] = {}
    provider_counts: dict[str, int] = {}
    model_counts: dict[str, int] = {}
    weak_source_ref_count = 0
    run_summaries: list[dict[str, Any]] = []
    latest_manifest_age: float | None = None
    for run_date in run_dates:
        path = _verification_manifest_path(run_date)
        manifest = _read_json(path)
        if manifest.get("_read_error") or not path.exists():
            continue
        source_rows = int(manifest.get("source_row_count") or 0)
        verified = int(manifest.get("verified_count") or 0)
        rejected = int(manifest.get("rejected_count") or 0)
        duplicates = int(manifest.get("duplicate_count") or 0)
        totals["source_row_count"] += source_rows
        totals["verified_count"] += verified
        totals["rejected_count"] += rejected
        totals["duplicate_count"] += duplicates
        age = _file_age_seconds(path)
        latest_manifest_age = age if latest_manifest_age is None else min(latest_manifest_age, age or latest_manifest_age)
        run_summaries.append({
            "run_date": run_date,
            "source_row_count": source_rows,
            "verified_count": verified,
            "rejected_count": rejected,
            "duplicate_count": duplicates,
            "manifest_age_seconds": age,
            "candidate": True,
            "serves_truth": False,
        })
        verified_path_value = manifest.get("verified_path")
        verified_path = _resource(str(verified_path_value or ""))
        if not verified_path.exists():
            continue
        for row in _read_jsonl(verified_path):
            kind = str(row.get("kind") or "unknown")
            kind_counts[kind] = kind_counts.get(kind, 0) + 1
            provider = str(row.get("source_provider") or "unknown")
            provider_counts[provider] = provider_counts.get(provider, 0) + 1
            model = str(row.get("source_model") or "unknown")
            model_counts[model] = model_counts.get(model, 0) + 1
            urls = _verification_source_urls(row.get("source_refs"))
            if not urls or not any(_verification_valid_public_source_url(url) for url in urls):
                weak_source_ref_count += 1
    run_summaries.sort(key=lambda row: str(row.get("run_date") or ""), reverse=True)
    return {
        "date_prefix": date_prefix,
        "run_count": len(run_dates),
        "manifest_count": len(run_summaries),
        "latest_manifest_age_seconds": latest_manifest_age,
        "source_row_count": totals["source_row_count"],
        "verified_count": totals["verified_count"],
        "duplicate_count": totals["duplicate_count"],
        "rejected_count": totals["rejected_count"],
        "verified_ratio": _safe_rate(float(totals["verified_count"]), float(totals["source_row_count"])),
        "verified_per_20k_source_rows": _safe_rate(float(totals["verified_count"]) * 20000.0, float(totals["source_row_count"])),
        "kind_counts": dict(sorted(kind_counts.items())),
        "source_provider_counts": dict(sorted(provider_counts.items())),
        "source_model_counts": dict(sorted(model_counts.items())),
        "weak_source_ref_count": weak_source_ref_count,
        "recent_runs": run_summaries[:12],
        "candidate": True,
        "serves_truth": False,
    }


def load_batch_aggregate(date_prefix: str) -> dict[str, Any]:
    run_dates = discover_run_dates(date_prefix)
    all_records: list[dict[str, Any]] = []
    gemma_records: list[dict[str, Any]] = []
    for run_date in run_dates:
        all_records.extend(load_batch_manifests(run_date, gemma_only=False))
        gemma_records.extend(load_batch_manifests(run_date, gemma_only=True))
    return {
        "date_prefix": date_prefix,
        "run_count": len(run_dates),
        "all_provider_totals": summarize_records(all_records),
        "gemma_totals": summarize_records(gemma_records),
        "candidate": True,
        "serves_truth": False,
    }


def load_source_material_status(run_date: str) -> dict[str, Any]:
    catalog_data_root = _resource("catalog") / "knowledge-packs" / "data"
    catalog_file_count, catalog_row_count = _count_jsonl_files(catalog_data_root)
    selected_files: list[dict[str, Any]] = []
    selected_row_count = 0
    present_count = 0
    for source_id, rel_path in SOURCE_MATERIAL_FILES:
        path = _resource(rel_path)
        rows = _count_jsonl_rows(path)
        present = path.exists()
        selected_row_count += rows
        present_count += 1 if present else 0
        selected_files.append({
            "source_id": source_id,
            "path": rel_path,
            "present": present,
            "row_count": rows,
            "age_seconds": _file_age_seconds(path),
            "candidate": True,
            "serves_truth": False,
        })
    shard_path = _resource("data") / "dev-intel" / "primitive_factory" / "daily_shards_20k" / run_date / "shards.jsonl"
    shard_manifest = _read_json(shard_path.with_name("manifest.json"))
    daily_shard_count = _count_jsonl_rows(shard_path)
    return {
        "catalog_jsonl_file_count": catalog_file_count,
        "catalog_jsonl_row_count": catalog_row_count,
        "selected_source_file_count": present_count,
        "selected_source_expected_count": len(SOURCE_MATERIAL_FILES),
        "selected_source_row_count": selected_row_count,
        "daily_20k_shard_count": daily_shard_count,
        "daily_20k_shard_manifest": shard_manifest,
        "files": selected_files,
        "candidate": True,
        "serves_truth": False,
    }


def load_linkable_card_status(date_prefix: str) -> dict[str, Any]:
    path = _resource("data") / "dev-intel" / "primitive_factory" / "linkable_cards" / date_prefix / "manifest.json"
    manifest = _read_json(path)
    return {
        "manifest_path": _rel(path),
        "manifest_age_seconds": _file_age_seconds(path),
        "card_count": int(manifest.get("card_count") or 0),
        "rejected_count": int(manifest.get("rejected_count") or 0),
        "high_leverage_card_count": int(manifest.get("high_leverage_card_count") or 0),
        "multistep_group_count": int(manifest.get("multistep_group_count") or 0),
        "multistep_coding_index_count": int(manifest.get("multistep_coding_index_count") or 0),
        "long_edge_card_count": int(manifest.get("long_edge_card_count") or 0),
        "estimated_saved_output_tokens_total": int(manifest.get("estimated_saved_output_tokens_total") or 0),
        "estimated_saved_output_tokens_avg": float(manifest.get("estimated_saved_output_tokens_avg") or 0),
        "edge_description_chars_avg": float(manifest.get("edge_description_chars_avg") or 0),
        "kind_counts": manifest.get("kind_counts") if isinstance(manifest.get("kind_counts"), dict) else {},
        "leverage_tier_counts": (
            manifest.get("leverage_tier_counts")
            if isinstance(manifest.get("leverage_tier_counts"), dict)
            else {}
        ),
        "reuse_class_counts": (
            manifest.get("reuse_class_counts")
            if isinstance(manifest.get("reuse_class_counts"), dict)
            else {}
        ),
        "side_effect_class_counts": (
            manifest.get("side_effect_class_counts")
            if isinstance(manifest.get("side_effect_class_counts"), dict)
            else {}
        ),
        "cards_path": manifest.get("cards_path") or "",
        "high_leverage_cards_path": manifest.get("high_leverage_cards_path") or "",
        "high_leverage_index_path": manifest.get("high_leverage_index_path") or "",
        "multistep_coding_index_path": manifest.get("multistep_coding_index_path") or "",
        "candidate": manifest.get("candidate") is True or not manifest,
        "serves_truth": manifest.get("serves_truth") is True,
        "read_error": manifest.get("_read_error"),
    }


def scan_processes() -> dict[str, Any]:
    namespace_hint = "unknown"
    try:
        init_cmd = Path("/proc/1/cmdline").read_bytes().replace(b"\x00", b" ").decode("utf-8", errors="replace")
        if "bwrap" in init_cmd or "codex-linux-sandbox" in init_cmd:
            namespace_hint = "sandbox_limited"
        else:
            namespace_hint = "host_or_shared"
    except OSError:
        namespace_hint = "unavailable"
    try:
        proc = subprocess.run(
            ["ps", "-eo", "pid,ppid,stat,etime,args"],
            cwd=REPO_ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5,
            check=False,
        )
    except Exception as exc:  # noqa: BLE001
        return {
            "status": "error",
            "error": f"{type(exc).__name__}: {exc}",
            "namespace_hint": namespace_hint,
            "processes": [],
        }
    rows: list[dict[str, Any]] = []
    for line in proc.stdout.splitlines()[1:]:
        parts = line.split(None, 4)
        if len(parts) < 5:
            continue
        pid, ppid, stat, etime, args = parts
        if "gemma_usage_monitor.py" in args and "--serve" not in args:
            continue
        matched = [term for term in FACTORY_PROCESS_TERMS + CHROME_CDP_PROCESS_TERMS if term in args]
        if not matched:
            continue
        rows.append({
            "pid": int(pid),
            "ppid": int(ppid),
            "stat": stat,
            "elapsed": etime,
            "matched_terms": matched,
            "args": args[:500],
        })
    return {
        "status": "ok" if proc.returncode == 0 else "error",
        "error": proc.stderr.strip() if proc.returncode else "",
        "namespace_hint": namespace_hint,
        "processes": rows,
        "factory_process_count": sum(1 for row in rows if any(term in row["matched_terms"] for term in FACTORY_PROCESS_TERMS)),
        "chrome_cdp_process_count": sum(1 for row in rows if any(term in row["matched_terms"] for term in CHROME_CDP_PROCESS_TERMS)),
    }


def check_cdp(cdp_url: str, *, enabled: bool = True) -> dict[str, Any]:
    if not enabled:
        return {"checked": False, "candidate": True, "serves_truth": False}
    url = cdp_url.rstrip("/") + "/json/list"
    started = time.time()
    try:
        with urllib.request.urlopen(url, timeout=2) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
        return {
            "checked": True,
            "status": "error",
            "url": url,
            "error": f"{type(exc).__name__}: {exc}",
            "latency_seconds": round(time.time() - started, 3),
            "candidate": True,
            "serves_truth": False,
        }
    targets = payload if isinstance(payload, list) else []
    openwebui_targets = [
        {
            "title": target.get("title"),
            "type": target.get("type"),
            "url": target.get("url"),
        }
        for target in targets
        if isinstance(target, dict) and "ui.iamretarded.net" in str(target.get("url") or "")
    ]
    return {
        "checked": True,
        "status": "ok",
        "url": url,
        "target_count": len(targets),
        "openwebui_target_count": len(openwebui_targets),
        "openwebui_targets": openwebui_targets[:5],
        "latency_seconds": round(time.time() - started, 3),
        "candidate": True,
        "serves_truth": False,
    }


def load_recent_logs(run_date: str, *, limit: int = 8) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(_fleet_root(run_date).glob("**/cycle_*/*.log")):
        text = path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
        lines = [line for line in text.splitlines() if line.strip()]
        rows.append({
            "path": _rel(path),
            "size_bytes": path.stat().st_size if path.exists() else 0,
            "age_seconds": _file_age_seconds(path),
            "last_lines": lines[-6:],
            "is_gemma_lane": "gemma" in path.name or "openwebui" in path.name,
            "mtime": path.stat().st_mtime if path.exists() else 0,
        })
    rows.sort(key=lambda row: float(row.get("mtime") or 0), reverse=True)
    for row in rows:
        row.pop("mtime", None)
    return rows[:limit]


def load_recent_call_events(run_date: str, *, limit: int = 60) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for path in sorted(_batch_root(run_date).glob("**/call_events.jsonl")):
        for row in _read_jsonl(path)[-limit:]:
            row = dict(row)
            row["error"] = _short_text(row.get("error"), limit=220)
            row["path"] = _rel(path)
            rows.append(row)
    rows.sort(key=lambda row: str(row.get("created_at") or ""))
    rows = rows[-limit:]
    started_by_shard: dict[str, dict[str, Any]] = {}
    finished_shards: set[str] = set()
    for row in rows:
        shard_id = str(row.get("shard_id") or "")
        if not shard_id:
            continue
        if row.get("event_type") == "call_started":
            started_by_shard[shard_id] = row
        elif row.get("event_type") == "call_finished":
            finished_shards.add(shard_id)
    active = [
        row for shard_id, row in started_by_shard.items()
        if shard_id not in finished_shards
    ]
    return {
        "recent": rows,
        "active": active[-50:],
        "recent_count": len(rows),
        "active_count": len(active),
        "candidate": True,
        "serves_truth": False,
    }


def load_raw_flywheel_status(run_date: str, *, recent_limit: int = 80) -> dict[str, Any]:
    """Summarize raw request/call/result telemetry before extraction quality gates."""
    root = _batch_root(run_date)
    by_model: dict[str, dict[str, Any]] = {}
    recent_results: list[dict[str, Any]] = []
    active_by_key: dict[str, dict[str, Any]] = {}
    finished_keys: set[str] = set()
    totals = {
        "worker_batch_count": 0,
        "selected_shards": 0,
        "call_event_count": 0,
        "call_started_count": 0,
        "call_retry_count": 0,
        "call_finished_count": 0,
        "call_success_count": 0,
        "call_error_count": 0,
        "model_output_receipt_count": 0,
        "model_output_success_count": 0,
        "model_output_error_count": 0,
        "failed_model_output_count": 0,
    }

    def stats_for(provider: str, model: str) -> dict[str, Any]:
        key = f"{provider}/{model}"
        if key not in by_model:
            by_model[key] = {
                "provider": provider,
                "model": model,
                "worker_batch_count": 0,
                "selected_shards": 0,
                "call_event_count": 0,
                "call_started_count": 0,
                "call_retry_count": 0,
                "call_finished_count": 0,
                "call_success_count": 0,
                "call_error_count": 0,
                "model_output_receipt_count": 0,
                "model_output_success_count": 0,
                "model_output_error_count": 0,
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                "candidate": True,
                "serves_truth": False,
            }
        return by_model[key]

    for path in sorted(root.glob("**/model/manifest.json")):
        manifest = _read_json(path)
        provider = str(manifest.get("provider") or "unknown")
        model = str(manifest.get("model") or "unknown")
        stats = stats_for(provider, model)
        selected = int(manifest.get("selected_shards") or 0)
        usage = _usage(manifest)
        totals["worker_batch_count"] += 1
        totals["selected_shards"] += selected
        stats["worker_batch_count"] += 1
        stats["selected_shards"] += selected
        for name, value in usage.items():
            stats["usage"][name] += int(value or 0)

    for path in sorted(root.glob("**/call_events.jsonl")):
        for row in _read_jsonl(path):
            provider = str(row.get("provider") or "unknown")
            model = str(row.get("model") or "unknown")
            stats = stats_for(provider, model)
            event_type = str(row.get("event_type") or "")
            call_key = f"{_rel(path)}::{row.get('shard_id') or ''}"
            totals["call_event_count"] += 1
            stats["call_event_count"] += 1
            if event_type == "call_started":
                totals["call_started_count"] += 1
                stats["call_started_count"] += 1
                active_by_key[call_key] = row | {"path": _rel(path)}
            elif event_type == "call_retry":
                totals["call_retry_count"] += 1
                stats["call_retry_count"] += 1
            elif event_type == "call_finished":
                totals["call_finished_count"] += 1
                stats["call_finished_count"] += 1
                finished_keys.add(call_key)
                if row.get("error"):
                    totals["call_error_count"] += 1
                    stats["call_error_count"] += 1
                else:
                    totals["call_success_count"] += 1
                    stats["call_success_count"] += 1

    for path in sorted(root.glob("**/model_outputs.jsonl")):
        for row in _read_jsonl(path):
            provider = str(row.get("provider") or "unknown")
            model = str(row.get("model") or "unknown")
            stats = stats_for(provider, model)
            usage = _usage(row)
            has_error = bool(row.get("error"))
            totals["model_output_receipt_count"] += 1
            stats["model_output_receipt_count"] += 1
            if has_error:
                totals["model_output_error_count"] += 1
                stats["model_output_error_count"] += 1
            else:
                totals["model_output_success_count"] += 1
                stats["model_output_success_count"] += 1
            recent_results.append({
                "path": _rel(path),
                "shard_id": row.get("shard_id"),
                "lane_id": row.get("lane_id"),
                "provider": provider,
                "model": model,
                "status": row.get("status"),
                "error": _short_text(row.get("error"), limit=180),
                "usage": usage,
                "duration_seconds": row.get("duration_seconds"),
                "candidate": row.get("candidate") is True,
                "serves_truth": row.get("serves_truth") is True,
            })

    for path in sorted(root.glob("**/failed_model_outputs.jsonl")):
        count = len(_read_jsonl(path))
        totals["failed_model_output_count"] += count

    active = [
        row for key, row in active_by_key.items()
        if key not in finished_keys
    ]
    totals["active_call_count"] = len(active)
    totals["candidate"] = True
    totals["serves_truth"] = False

    rows = sorted(
        by_model.values(),
        key=lambda row: (str(row.get("provider") or ""), str(row.get("model") or "")),
    )
    recent_results = recent_results[-recent_limit:]
    return {
        "totals": totals,
        "by_model": rows,
        "active_calls": active[-recent_limit:],
        "recent_results": recent_results,
        "candidate": True,
        "serves_truth": False,
    }


def build_console_payload(run_date: str, *, check_cdp_target: bool = True, aggregate_prefix: str = "") -> dict[str, Any]:
    """Build a compact console stream payload without exposing credentials."""
    snapshot = build_snapshot(run_date=run_date, aggregate_prefix=aggregate_prefix, check_cdp_target=check_cdp_target)
    entries: list[dict[str, Any]] = []
    totals = snapshot.get("all_provider_totals", {})
    gemma = snapshot.get("gemma", {}).get("totals", {})
    recent = snapshot.get("gemma", {}).get("recent_health", {})
    verification = snapshot.get("verification", {})
    entries.append({
        "kind": "summary",
        "source": "monitor",
        "message": (
            f"all accepted={totals.get('accepted_count', 0)} "
            f"all_tokens={(totals.get('usage') or {}).get('total_tokens', 0)} "
            f"verified_l3={verification.get('verified_count', 0)} "
            f"gemma accepted={gemma.get('accepted_count', 0)} "
            f"gemma_tps={gemma.get('total_tps_weighted', 0)} "
            f"gemma_latest={recent.get('latest_batch', '')} "
            f"latest_errors={recent.get('latest_error_count', 0)}"
        ),
    })
    raw = snapshot.get("raw_flywheel", {}).get("totals", {})
    entries.append({
        "kind": "raw",
        "source": "flywheel",
        "message": (
            f"started={raw.get('call_started_count', 0)} "
            f"finished={raw.get('call_finished_count', 0)} "
            f"active={raw.get('active_call_count', 0)} "
            f"retries={raw.get('call_retry_count', 0)} "
            f"outputs={raw.get('model_output_receipt_count', 0)} "
            f"output_errors={raw.get('model_output_error_count', 0)}"
        ),
    })
    for row in snapshot.get("processes", {}).get("processes", [])[:12]:
        entries.append({
            "kind": "process",
            "source": f"pid:{row.get('pid')}",
            "message": f"{row.get('elapsed')} {' '.join(row.get('matched_terms') or [])} {row.get('args')}",
        })
    for row in snapshot.get("call_events", {}).get("recent", [])[-24:]:
        usage = row.get("usage") or {}
        entries.append({
            "kind": str(row.get("event_type") or "call"),
            "source": str(row.get("shard_id") or row.get("path") or "call_event"),
            "message": (
                f"{row.get('provider')}/{row.get('model')} {row.get('status')} "
                f"duration={row.get('duration_seconds')}s "
                f"tokens={usage.get('total_tokens', 0)} error={row.get('error') or ''}"
            ),
        })
    for log in snapshot.get("recent_logs", [])[:8]:
        lines = log.get("last_lines") or []
        if not lines:
            entries.append({
                "kind": "log",
                "source": log.get("path"),
                "message": f"log exists but has no flushed lines yet; size={log.get('size_bytes', 0)} bytes",
            })
            continue
        for line in lines[-8:]:
            entries.append({
                "kind": "log",
                "source": log.get("path"),
                "message": line,
            })
    return {
        "record_type": "gemma_usage_monitor_console",
        "created_at": _now_utc(),
        "run_date": snapshot.get("run_date", run_date),
        "requested_run_date": run_date,
        "entries": entries[-120:],
        "candidate": True,
        "serves_truth": False,
    }


def build_alerts(snapshot: dict[str, Any]) -> list[dict[str, str]]:
    alerts: list[dict[str, str]] = []
    gemma_totals = snapshot.get("gemma", {}).get("totals", {})
    gemma_recent = snapshot.get("gemma", {}).get("recent_health", {})
    if int(gemma_recent.get("latest_error_count") or 0) > 0:
        alerts.append({"level": "warn", "message": "Latest Gemma batch still has worker errors; inspect recent batches/logs."})
    elif int(gemma_totals.get("worker_error_count") or 0) > 0 and gemma_recent.get("latest_ok"):
        alerts.append({"level": "info", "message": "Gemma has historical worker errors, but the latest batch is recovered."})
    cdp = snapshot.get("openwebui_cdp", {})
    if cdp.get("checked") and cdp.get("status") != "ok":
        alerts.append({"level": "warn", "message": "Open WebUI CDP target is not reachable."})
    if cdp.get("checked") and cdp.get("status") == "ok" and not cdp.get("openwebui_target_count"):
        alerts.append({"level": "warn", "message": "Chrome DevTools is up, but no Open WebUI page target was found."})
    processes = snapshot.get("processes", {})
    if processes.get("namespace_hint") == "sandbox_limited":
        alerts.append({
            "level": "info",
            "message": "Process scan is sandbox-limited; run the monitor outside the sandbox to see host worker threads.",
        })
    if int(processes.get("factory_process_count") or 0) == 0:
        alerts.append({"level": "info", "message": "No primitive factory generation process is visible right now."})
    if not snapshot.get("gemma", {}).get("manifests"):
        alerts.append({"level": "info", "message": "No Gemma batch manifest found for this date."})
    verification = snapshot.get("verification", {})
    if int(verification.get("source_row_count") or 0) and float(verification.get("verified_ratio") or 0) < 0.5:
        alerts.append({
            "level": "warn",
            "message": "Less than half of extracted rows pass L3 verification; tighten generator prompts or normalization.",
        })
    raw = snapshot.get("raw_flywheel", {}).get("totals", {})
    if int(raw.get("model_output_error_count") or 0) > 0:
        alerts.append({
            "level": "warn",
            "message": "Raw model-output receipts include errors; inspect the Raw Flywheel table before judging accepted counts.",
        })
    linkable = snapshot.get("linkable_cards", {})
    card_count = int(linkable.get("card_count") or 0)
    high_leverage_count = int(linkable.get("high_leverage_card_count") or 0)
    if card_count and high_leverage_count / card_count < 0.2:
        alerts.append({
            "level": "warn",
            "message": "High-leverage linkable cards are below 20% of packaged cards; push longer edge contracts and multistep groups.",
        })
    source_material = snapshot.get("source_material", {})
    if int(source_material.get("selected_source_row_count") or 0) < 10000:
        alerts.append({
            "level": "warn",
            "message": "Selected source-material rows are below 10k; expand source maps/tasks/seeds before scaling further.",
        })
    return alerts


def build_snapshot(
    *,
    run_date: str,
    aggregate_prefix: str = "",
    include_processes: bool = True,
    check_cdp_target: bool = True,
    cdp_url: str | None = None,
) -> dict[str, Any]:
    requested_run_date = run_date
    run_date = resolve_run_date(run_date, aggregate_prefix)
    gemma_records = load_batch_manifests(run_date, gemma_only=True)
    all_records = load_batch_manifests(run_date, gemma_only=False)
    recent_gemma_batches = load_recent_worker_batches(run_date)
    snapshot = {
        "record_type": "gemma_usage_monitor_snapshot",
        "created_at": _now_utc(),
        "run_date": run_date,
        "requested_run_date": requested_run_date,
        "provider_focus": "openwebui",
        "model_focus": PRIMITIVE_FACTORY_MODEL_GEMMA_CANDIDATE_WRITER,
        "openwebui_base_url": OPENWEBUI_DEFAULT_BASE_URL,
        "gemma": {
            "totals": summarize_records(gemma_records),
            "manifests": gemma_records,
            "recent_worker_batches": recent_gemma_batches,
            "recent_health": summarize_recent_gemma_health(recent_gemma_batches),
        },
        "fleet": load_fleet_status(run_date),
        "verification": load_verification_status(run_date),
        "all_provider_totals": summarize_records(all_records),
        "raw_flywheel": load_raw_flywheel_status(run_date),
        "source_material": load_source_material_status(run_date),
        "linkable_cards": load_linkable_card_status(aggregate_prefix or run_date),
        "call_events": load_recent_call_events(run_date),
        "recent_logs": load_recent_logs(run_date),
        "processes": scan_processes() if include_processes else {"status": "skipped", "processes": []},
        "openwebui_cdp": check_cdp(cdp_url or os.environ.get(OPENWEBUI_CDP_URL_ENV, "http://127.0.0.1:9222"), enabled=check_cdp_target),
        "candidate": True,
        "serves_truth": False,
    }
    if aggregate_prefix:
        snapshot["aggregate"] = {
            "verification": load_verification_aggregate(aggregate_prefix),
            "batch": load_batch_aggregate(aggregate_prefix),
            "candidate": True,
            "serves_truth": False,
        }
    snapshot["alerts"] = build_alerts(snapshot)
    return snapshot


def format_text(snapshot: dict[str, Any]) -> str:
    gemma = snapshot["gemma"]["totals"]
    all_totals = snapshot["all_provider_totals"]
    verification = snapshot.get("verification", {})
    raw = snapshot.get("raw_flywheel", {}).get("totals", {})
    source_material = snapshot.get("source_material", {})
    linkable_cards = snapshot.get("linkable_cards", {})
    recent = snapshot.get("gemma", {}).get("recent_health", {})
    aggregate = snapshot.get("aggregate", {})
    aggregate_verification = aggregate.get("verification", {}) if isinstance(aggregate, dict) else {}
    aggregate_batch = aggregate.get("batch", {}) if isinstance(aggregate, dict) else {}
    usage = gemma["usage"]
    processes = snapshot.get("processes", {})
    cdp = snapshot.get("openwebui_cdp", {})
    lines = [
        f"Gemma 4 primitive monitor - {snapshot['run_date']} ({snapshot['created_at']})",
        f"model={snapshot['model_focus']} provider={snapshot['provider_focus']} candidate={snapshot['candidate']} serves_truth={snapshot['serves_truth']}",
        "",
        "Gemma totals:",
        f"  accepted={gemma['accepted_count']} rejected={gemma['rejected_count']} selected_shards={gemma['selected_shards']} worker_errors={gemma['worker_error_count']}",
        f"  prompt_tokens={usage['prompt_tokens']} completion_tokens={usage['completion_tokens']} total_tokens={usage['total_tokens']}",
        f"  completion_tps={gemma['completion_tps_weighted']} total_tps={gemma['total_tps_weighted']} accepted/1k_tokens={gemma['accepted_per_1k_total_tokens']}",
        f"  recent_latest={recent.get('latest_batch', '')} latest_errors={recent.get('latest_error_count', 0)} latest_ok={recent.get('latest_ok', False)} recovered_after_error={recent.get('recovered_after_error', False)}",
        f"  recent_window={recent.get('window', 0)} recent_shards={recent.get('recent_selected_shards', 0)} recent_errors={recent.get('recent_error_count', 0)} recent_total_tps={recent.get('recent_total_tps_weighted', 0)}",
        "",
        "All provider totals:",
        f"  accepted={all_totals['accepted_count']} selected_shards={all_totals['selected_shards']} worker_errors={all_totals['worker_error_count']}",
        f"  total_tokens={all_totals['usage']['total_tokens']} total_tps={all_totals['total_tps_weighted']}",
        "",
        "Raw flywheel:",
        f"  calls started={raw.get('call_started_count', 0)} finished={raw.get('call_finished_count', 0)} active={raw.get('active_call_count', 0)} retries={raw.get('call_retry_count', 0)}",
        f"  model_outputs={raw.get('model_output_receipt_count', 0)} output_errors={raw.get('model_output_error_count', 0)} failed_outputs={raw.get('failed_model_output_count', 0)}",
        "",
        "Verification:",
        f"  verified_l3={verification.get('verified_count', 0)} source_rows={verification.get('source_row_count', 0)} rejected={verification.get('rejected_count', 0)} duplicates={verification.get('duplicate_count', 0)}",
        f"  ratio={verification.get('verified_ratio', 0)} per_20k_source_rows={verification.get('verified_per_20k_source_rows', 0)}",
        "",
    ]
    if aggregate_verification:
        aggregate_all = aggregate_batch.get("all_provider_totals", {}) if isinstance(aggregate_batch, dict) else {}
        aggregate_gemma = aggregate_batch.get("gemma_totals", {}) if isinstance(aggregate_batch, dict) else {}
        lines.extend([
            f"Aggregate across date prefix {aggregate_verification.get('date_prefix', '')}:",
            f"  runs={aggregate_verification.get('run_count', 0)} manifests={aggregate_verification.get('manifest_count', 0)} verified_l3={aggregate_verification.get('verified_count', 0)} source_rows={aggregate_verification.get('source_row_count', 0)}",
            f"  rejected={aggregate_verification.get('rejected_count', 0)} duplicates={aggregate_verification.get('duplicate_count', 0)} weak_source_refs={aggregate_verification.get('weak_source_ref_count', 0)}",
            f"  kind_counts={json.dumps(aggregate_verification.get('kind_counts', {}), sort_keys=True)}",
            f"  all_provider_accepted={aggregate_all.get('accepted_count', 0)} all_provider_tokens={(aggregate_all.get('usage') or {}).get('total_tokens', 0)}",
            f"  gemma_accepted={aggregate_gemma.get('accepted_count', 0)} gemma_tokens={(aggregate_gemma.get('usage') or {}).get('total_tokens', 0)}",
            "",
        ])
    lines.extend([
        "Source material:",
        f"  catalog_jsonl_files={source_material.get('catalog_jsonl_file_count', 0)} catalog_rows={source_material.get('catalog_jsonl_row_count', 0)} selected_source_rows={source_material.get('selected_source_row_count', 0)}",
        f"  daily_20k_shards={source_material.get('daily_20k_shard_count', 0)} selected_source_files={source_material.get('selected_source_file_count', 0)}/{source_material.get('selected_source_expected_count', 0)}",
        "",
        "Linkable cards:",
        f"  cards={linkable_cards.get('card_count', 0)} rejected={linkable_cards.get('rejected_count', 0)} kind_counts={json.dumps(linkable_cards.get('kind_counts', {}), sort_keys=True)}",
        f"  high_leverage={linkable_cards.get('high_leverage_card_count', 0)} multistep_groups={linkable_cards.get('multistep_group_count', 0)} multistep_coding={linkable_cards.get('multistep_coding_index_count', 0)} long_edges={linkable_cards.get('long_edge_card_count', 0)}",
        f"  est_saved_output_tokens={linkable_cards.get('estimated_saved_output_tokens_total', 0)} avg_saved={linkable_cards.get('estimated_saved_output_tokens_avg', 0)} avg_edge_desc_chars={linkable_cards.get('edge_description_chars_avg', 0)}",
        f"  leverage_tiers={json.dumps(linkable_cards.get('leverage_tier_counts', {}), sort_keys=True)}",
        f"  cards_path={linkable_cards.get('cards_path', '')}",
        f"  high_leverage_path={linkable_cards.get('high_leverage_cards_path', '')}",
        "",
        f"Processes: factory={processes.get('factory_process_count', 0)} chrome_cdp={processes.get('chrome_cdp_process_count', 0)}",
        f"Process namespace: {processes.get('namespace_hint', 'unknown')}",
        f"CDP: status={cdp.get('status', 'unchecked')} openwebui_targets={cdp.get('openwebui_target_count', 0)}",
        "",
        "Recent Gemma worker batches:",
    ])
    for row in snapshot["gemma"]["recent_worker_batches"][:6]:
        row_usage = row["usage"]
        lines.append(
            f"  {row['batch']} dry_run={row.get('dry_run', False)} shards={row['selected_shards']} errors={row['error_count']} "
            f"total_tokens={row_usage['total_tokens']} total_tps={row['aggregate_total_tps']} age_s={row['age_seconds']}"
        )
    if snapshot.get("alerts"):
        lines.append("")
        lines.append("Alerts:")
        for alert in snapshot["alerts"]:
            lines.append(f"  [{alert['level']}] {alert['message']}")
    return "\n".join(lines) + "\n"


def _metric_card(label: str, value: Any) -> str:
    return f"<section class='card'><div class='label'>{html.escape(label)}</div><div class='value'>{html.escape(str(value))}</div></section>"


def build_html(snapshot: dict[str, Any], *, refresh_seconds: int) -> str:
    initial_snapshot_json = json.dumps(snapshot, sort_keys=True).replace("</", "<\\/")
    refresh = max(1, int(refresh_seconds))
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Gemma 4 Primitive Monitor</title>
  <style>
    :root { color-scheme: light dark; --bg:#0f1115; --panel:#171b22; --panel2:#11151c; --line:#2a303a; --text:#eef2f7; --muted:#a7b0bf; --accent:#64c7a5; --blue:#70a7ff; --warn:#f2b84b; --bad:#ef6f6c; }
    body { margin:0; font:14px/1.45 system-ui, -apple-system, Segoe UI, sans-serif; background:var(--bg); color:var(--text); }
    header { padding:22px 28px 12px; border-bottom:1px solid var(--line); }
    h1 { margin:0 0 6px; font-size:26px; letter-spacing:0; }
    h2 { margin:0 0 12px; font-size:17px; }
    .muted { color:var(--muted); }
    .status { display:flex; flex-wrap:wrap; gap:10px 18px; color:var(--muted); }
    .status strong { color:var(--text); font-weight:650; }
    main { padding:20px 28px 32px; display:grid; gap:22px; }
    .grid { display:grid; grid-template-columns:repeat(auto-fit, minmax(170px, 1fr)); gap:12px; }
    .card { background:var(--panel); border:1px solid var(--line); border-radius:8px; padding:14px; min-height:74px; }
    .label { color:var(--muted); font-size:12px; text-transform:uppercase; }
    .value { font-size:24px; font-weight:650; margin-top:4px; word-break:break-word; }
    .delta { color:var(--accent); font-size:12px; margin-top:3px; min-height:17px; }
    section.panel { background:var(--panel); border:1px solid var(--line); border-radius:8px; padding:16px; overflow:auto; }
    .visuals { display:grid; grid-template-columns:minmax(280px, 1.5fr) minmax(260px, 1fr); gap:12px; align-items:stretch; }
    .chart { background:var(--panel2); border:1px solid var(--line); border-radius:8px; padding:12px; min-height:172px; }
    .chart-title { display:flex; justify-content:space-between; gap:12px; color:var(--muted); font-size:12px; text-transform:uppercase; }
    svg { display:block; width:100%; height:128px; overflow:visible; }
    .axis { stroke:var(--line); stroke-width:1; }
    .line { fill:none; stroke:var(--accent); stroke-width:2.4; vector-effect:non-scaling-stroke; }
    .line.blue { stroke:var(--blue); }
    .line.warn { stroke:var(--warn); }
    .bar { margin:10px 0 0; }
    .bar-top { display:flex; justify-content:space-between; gap:12px; color:var(--muted); font-size:12px; }
    .bar-track { height:10px; border-radius:999px; background:#252b35; overflow:hidden; margin-top:5px; }
    .bar-fill { height:100%; background:var(--accent); border-radius:999px; transition:width .25s ease; }
    .bar-fill.blue { background:var(--blue); }
    .bar-fill.warn { background:var(--warn); }
    .bar-fill.bad { background:var(--bad); }
    table { border-collapse:collapse; width:100%; min-width:760px; }
    th, td { border-bottom:1px solid var(--line); padding:8px 10px; text-align:left; vertical-align:top; }
    th { color:var(--muted); font-weight:600; }
    code { color:#cbd6e2; font-size:12px; white-space:pre-wrap; }
    ul { margin:0; padding-left:20px; }
    .warn { color:var(--warn); } .error { color:var(--bad); } .ok { color:var(--accent); }
    .console { background:#090b0f; border:1px solid var(--line); border-radius:8px; padding:12px; min-height:240px; max-height:420px; overflow:auto; font:12px/1.45 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }
    .console-line { display:grid; grid-template-columns:78px minmax(120px, 260px) 1fr; gap:10px; border-bottom:1px solid rgba(255,255,255,.05); padding:4px 0; }
    .console-line .kind { color:var(--accent); text-transform:uppercase; }
    .console-line .source { color:var(--muted); overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
    .console-line .message { color:#dfe7f3; white-space:pre-wrap; word-break:break-word; }
    .pulse { display:inline-block; width:8px; height:8px; border-radius:999px; background:var(--accent); box-shadow:0 0 0 0 rgba(100,199,165,.8); animation:pulse 1.8s infinite; margin-right:6px; }
    @keyframes pulse { 70% { box-shadow:0 0 0 8px rgba(100,199,165,0); } 100% { box-shadow:0 0 0 0 rgba(100,199,165,0); } }
    @media (max-width: 900px) { .visuals { grid-template-columns:1fr; } }
  </style>
</head>
<body>
  <header>
    <h1>Gemma 4 Primitive Monitor</h1>
    <div class="status">
      <span>Run date <strong id="run-date">-</strong></span>
      <span>Updated <strong id="updated-at">-</strong></span>
      <span>Poll <strong id="poll-state">starting</strong></span>
      <span>Candidate <strong id="candidate-state">-</strong></span>
      <span>Serves truth <strong id="truth-state">-</strong></span>
    </div>
  </header>
  <main>
    <div class="grid" id="metric-grid"></div>
    <section class="panel">
      <h2>Live Movement</h2>
      <div class="visuals">
        <div class="chart"><div class="chart-title"><span>All Provider Accepted</span><span id="history-count">0 samples</span></div><div id="accepted-chart"></div></div>
        <div class="chart"><div class="chart-title"><span>Latest Provider Lanes</span><span id="lane-count">0 lanes</span></div><div id="provider-bars"></div></div>
        <div class="chart"><div class="chart-title"><span>Gemma Tokens</span><span>total tokens</span></div><div id="token-chart"></div></div>
        <div class="chart"><div class="chart-title"><span>Throughput</span><span>Gemma TPS</span></div><div id="tps-chart"></div></div>
      </div>
    </section>
    <section class="panel"><h2>Alerts</h2><ul id="alerts"></ul></section>
    <section class="panel"><h2>Latest Fleet Lanes</h2><table><thead><tr><th>Run</th><th>Lane</th><th>Model</th><th>Return</th><th>Planned</th><th>Accepted</th><th>Errors</th><th>Total Tokens</th><th>Duration</th></tr></thead><tbody id="latest-lanes"></tbody></table></section>
    <section class="panel"><h2>Raw Flywheel By Model</h2><table><thead><tr><th>Provider / Model</th><th>Batches</th><th>Selected Shards</th><th>Started</th><th>Finished</th><th>Retries</th><th>Errors</th><th>Receipts</th><th>Output Errors</th><th>Total Tokens</th></tr></thead><tbody id="raw-by-model"></tbody></table></section>
    <section class="panel"><h2>Recent Gemma Worker Batches</h2><table><thead><tr><th>Batch</th><th>Dry Run</th><th>Shards</th><th>Errors</th><th>Total Tokens</th><th>Total TPS</th><th>Age Seconds</th></tr></thead><tbody id="recent-batches"></tbody></table></section>
    <section class="panel"><h2><span class="pulse"></span>Active Raw Calls</h2><table><thead><tr><th>Started</th><th>Lane</th><th>Provider / Model</th><th>Shard</th><th>Status</th></tr></thead><tbody id="active-calls"></tbody></table></section>
    <section class="panel"><h2>Recent Raw Results</h2><table><thead><tr><th>Provider / Model</th><th>Lane</th><th>Status</th><th>Tokens</th><th>Duration</th><th>Error</th><th>Shard</th></tr></thead><tbody id="recent-results"></tbody></table></section>
    <section class="panel"><h2>Source Material Inventory</h2><table><thead><tr><th>Source</th><th>Rows</th><th>Present</th><th>Age Seconds</th><th>Path</th></tr></thead><tbody id="source-material"></tbody></table></section>
    <section class="panel"><h2><span class="pulse"></span>Console Stream</h2><div class="console" id="console-stream"></div></section>
    <section class="panel"><h2>Live Processes</h2><table><thead><tr><th>PID</th><th>Elapsed</th><th>Match</th><th>Command</th></tr></thead><tbody id="processes"></tbody></table></section>
  </main>
  <script>
    const initialSnapshot = __INITIAL_SNAPSHOT__;
    const refreshSeconds = __REFRESH_SECONDS__;
    const maxHistory = 96;
    const maxConsoleLines = 240;
    const historyKey = `gemma-monitor-history:${initialSnapshot.run_date || "unknown"}`;
    let history = loadHistory();
    let consoleLines = [];
    let consoleSeen = new Set();

    function byId(id) { return document.getElementById(id); }
    function esc(value) {
      return String(value ?? "").replace(/[&<>"']/g, ch => ({
        "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
      }[ch]));
    }
    function num(value) { return Number(value || 0); }
    function fmt(value) { return Number.isFinite(num(value)) ? num(value).toLocaleString() : esc(value); }
    function get(obj, path, fallback = 0) {
      return path.split(".").reduce((cur, part) => cur && cur[part] !== undefined ? cur[part] : undefined, obj) ?? fallback;
    }
    function loadHistory() {
      try {
        const parsed = JSON.parse(localStorage.getItem(historyKey) || "[]");
        return Array.isArray(parsed) ? parsed.slice(-maxHistory) : [];
      } catch {
        return [];
      }
    }
    function saveHistory() {
      try { localStorage.setItem(historyKey, JSON.stringify(history.slice(-maxHistory))); } catch {}
    }
    function compactSample(snapshot) {
      return {
        t: Date.now(),
        created_at: snapshot.created_at,
        accepted: get(snapshot, "all_provider_totals.accepted_count", 0),
        rawStarted: get(snapshot, "raw_flywheel.totals.call_started_count", 0),
        rawOutputs: get(snapshot, "raw_flywheel.totals.model_output_receipt_count", 0),
        rawErrors: get(snapshot, "raw_flywheel.totals.model_output_error_count", 0),
        gemmaAccepted: get(snapshot, "gemma.totals.accepted_count", 0),
        gemmaTokens: get(snapshot, "gemma.totals.usage.total_tokens", 0),
        allTokens: get(snapshot, "all_provider_totals.usage.total_tokens", 0),
        verified: get(snapshot, "verification.verified_count", 0),
        linkableCards: get(snapshot, "linkable_cards.card_count", 0),
        highLeverageCards: get(snapshot, "linkable_cards.high_leverage_card_count", 0),
        multistepCoding: get(snapshot, "linkable_cards.multistep_coding_index_count", 0),
        savedOutputTokens: get(snapshot, "linkable_cards.estimated_saved_output_tokens_total", 0),
        gemmaTps: get(snapshot, "gemma.totals.total_tps_weighted", 0),
        allTps: get(snapshot, "all_provider_totals.total_tps_weighted", 0),
        factoryProcesses: get(snapshot, "processes.factory_process_count", 0)
      };
    }
    function appendHistory(snapshot) {
      const sample = compactSample(snapshot);
      const last = history[history.length - 1];
      if (!last || last.created_at !== sample.created_at || last.accepted !== sample.accepted || last.allTokens !== sample.allTokens) {
        history.push(sample);
        history = history.slice(-maxHistory);
        saveHistory();
      }
    }
    function delta(field) {
      if (history.length < 2) return "";
      const first = history[0][field] || 0;
      const last = history[history.length - 1][field] || 0;
      const diff = last - first;
      return diff ? `+${fmt(diff)} since page open` : "";
    }
    function metricCard(label, value, deltaText = "") {
      return `<section class="card"><div class="label">${esc(label)}</div><div class="value">${esc(value)}</div><div class="delta">${esc(deltaText)}</div></section>`;
    }
    function renderMetrics(snapshot) {
      const gemma = get(snapshot, "gemma.totals", {});
      const recent = get(snapshot, "gemma.recent_health", {});
      const usage = get(snapshot, "gemma.totals.usage", {});
      const all = get(snapshot, "all_provider_totals", {});
      const verification = get(snapshot, "verification", {});
      const aggregateVerification = get(snapshot, "aggregate.verification", {});
      const raw = get(snapshot, "raw_flywheel.totals", {});
      const source = get(snapshot, "source_material", {});
      const linkable = get(snapshot, "linkable_cards", {});
      const cards = [
        metricCard("Raw Calls Started", fmt(raw.call_started_count), delta("rawStarted")),
        metricCard("Active Raw Calls", fmt(raw.active_call_count)),
        metricCard("Model Output Receipts", fmt(raw.model_output_receipt_count), delta("rawOutputs")),
        metricCard("Output Errors", fmt(raw.model_output_error_count), delta("rawErrors")),
        metricCard("Retries", fmt(raw.call_retry_count)),
        metricCard("Selected Source Rows", fmt(source.selected_source_row_count)),
        metricCard("Catalog Source Rows", fmt(source.catalog_jsonl_row_count)),
        metricCard("20k Shards", fmt(source.daily_20k_shard_count)),
        metricCard("Verified L3 Candidates", fmt(verification.verified_count), delta("verified")),
        metricCard("Linkable Cards", fmt(linkable.card_count), delta("linkableCards")),
        metricCard("High-Leverage Cards", fmt(linkable.high_leverage_card_count), delta("highLeverageCards")),
        metricCard("Multistep Groups", fmt(linkable.multistep_group_count)),
        metricCard("Multistep Coding Cards", fmt(linkable.multistep_coding_index_count), delta("multistepCoding")),
        metricCard("Long Edge Cards", fmt(linkable.long_edge_card_count)),
        metricCard("Est. Saved Output Tokens", fmt(linkable.estimated_saved_output_tokens_total), delta("savedOutputTokens")),
        metricCard("Avg Saved/Card", linkable.estimated_saved_output_tokens_avg || 0),
        metricCard("Avg Edge Desc Chars", linkable.edge_description_chars_avg || 0),
        metricCard("Linkable Rejected", fmt(linkable.rejected_count)),
        metricCard("Verification Ratio", verification.verified_ratio || 0),
        metricCard("Gemma Accepted", fmt(gemma.accepted_count), delta("gemmaAccepted")),
        metricCard("Gemma Latest Batch", recent.latest_batch || "-"),
        metricCard("Gemma Latest Errors", fmt(recent.latest_error_count)),
        metricCard("Gemma Latest TPS", recent.latest_total_tps || 0),
        metricCard("Gemma Recent Error Rate", recent.recent_error_rate_per_shard || 0),
        metricCard("Gemma Total Tokens", fmt(usage.total_tokens), delta("gemmaTokens")),
        metricCard("Gemma Total TPS", gemma.total_tps_weighted || 0),
        metricCard("Worker Errors", fmt(gemma.worker_error_count)),
        metricCard("All Providers Accepted", fmt(all.accepted_count), delta("accepted")),
        metricCard("All Provider Tokens", fmt(get(snapshot, "all_provider_totals.usage.total_tokens", 0)), delta("allTokens")),
        metricCard("Factory Processes", fmt(get(snapshot, "processes.factory_process_count", 0))),
        metricCard("CDP Status", get(snapshot, "openwebui_cdp.status", "unchecked")),
        metricCard("Open WebUI Targets", fmt(get(snapshot, "openwebui_cdp.openwebui_target_count", 0)))
      ];
      if (aggregateVerification && aggregateVerification.date_prefix) {
        cards.splice(8, 0,
          metricCard("Aggregate Runs", fmt(aggregateVerification.run_count)),
          metricCard("Aggregate Verified L3", fmt(aggregateVerification.verified_count)),
          metricCard("Aggregate Kind Split", JSON.stringify(aggregateVerification.kind_counts || {})),
          metricCard("Weak Source Refs", fmt(aggregateVerification.weak_source_ref_count))
        );
      }
      byId("metric-grid").innerHTML = cards.join("");
    }
    function sparkline(samples, field, cssClass = "") {
      const values = samples.map(s => Number(s[field] || 0));
      if (!values.length) return "<div class='muted'>Waiting for samples...</div>";
      const w = 680, h = 118, pad = 8;
      const min = Math.min(...values);
      const max = Math.max(...values);
      const span = max - min || 1;
      const points = values.map((value, index) => {
        const x = pad + (index * (w - pad * 2) / Math.max(values.length - 1, 1));
        const y = h - pad - ((value - min) / span) * (h - pad * 2);
        return `${x.toFixed(1)},${y.toFixed(1)}`;
      }).join(" ");
      return `<svg viewBox="0 0 ${w} ${h}" role="img" aria-label="${esc(field)} trend"><line class="axis" x1="${pad}" y1="${h - pad}" x2="${w - pad}" y2="${h - pad}"></line><polyline class="line ${cssClass}" points="${points}"></polyline></svg><div class="muted">min ${fmt(min)} | max ${fmt(max)}</div>`;
    }
    function providerBars(snapshot) {
      const lanes = get(snapshot, "fleet.latest_lane_results", []);
      const total = lanes.reduce((sum, lane) => sum + num(lane.accepted_count), 0) || 1;
      byId("lane-count").textContent = `${lanes.length} lanes`;
      if (!lanes.length) return "<div class='muted'>Waiting for lane results...</div>";
      return lanes.map((lane, index) => {
        const accepted = num(lane.accepted_count);
        const width = Math.max(1, Math.round(accepted * 100 / total));
        const errors = num(lane.worker_error_count);
        const cls = errors ? "bad" : index % 2 ? "blue" : "";
        return `<div class="bar"><div class="bar-top"><span>${esc(lane.run_label || "")} ${esc(lane.model || lane.lane_id)}</span><span>${fmt(accepted)} accepted, ${fmt(errors)} errors</span></div><div class="bar-track"><div class="bar-fill ${cls}" style="width:${width}%"></div></div></div>`;
      }).join("");
    }
    function renderVisuals(snapshot) {
      byId("history-count").textContent = `${history.length} samples`;
      byId("accepted-chart").innerHTML = sparkline(history, "accepted", "");
      byId("token-chart").innerHTML = sparkline(history, "gemmaTokens", "blue");
      byId("tps-chart").innerHTML = sparkline(history, "gemmaTps", "warn");
      byId("provider-bars").innerHTML = providerBars(snapshot);
    }
    function renderAlerts(snapshot) {
      const alerts = snapshot.alerts || [];
      byId("alerts").innerHTML = alerts.length
        ? alerts.map(alert => `<li class="${esc(alert.level)}">${esc(alert.message)}</li>`).join("")
        : "<li class='ok'>No monitor alerts.</li>";
    }
    function renderLanes(snapshot) {
      const rows = get(snapshot, "fleet.latest_lane_results", []);
      byId("latest-lanes").innerHTML = rows.map(row => `<tr><td>${esc(row.run_label || "")}</td><td>${esc(row.lane_id)}</td><td>${esc(row.model)}</td><td>${esc(row.returncode)}</td><td>${fmt(row.planned_shards)}</td><td>${fmt(row.accepted_count)}</td><td>${fmt(row.worker_error_count)}</td><td>${fmt((row.usage || {}).total_tokens)}</td><td>${esc(row.duration_seconds || "")}</td></tr>`).join("");
    }
    function renderBatches(snapshot) {
      const rows = get(snapshot, "gemma.recent_worker_batches", []).slice(0, 12);
      byId("recent-batches").innerHTML = rows.map(row => `<tr><td>${esc(row.batch)}</td><td>${esc(row.dry_run)}</td><td>${fmt(row.selected_shards)}</td><td>${fmt(row.error_count)}</td><td>${fmt((row.usage || {}).total_tokens)}</td><td>${esc(row.aggregate_total_tps)}</td><td>${esc(row.age_seconds)}</td></tr>`).join("");
    }
    function renderRawByModel(snapshot) {
      const rows = get(snapshot, "raw_flywheel.by_model", []);
      byId("raw-by-model").innerHTML = rows.map(row => `<tr><td>${esc(row.provider)}/${esc(row.model)}</td><td>${fmt(row.worker_batch_count)}</td><td>${fmt(row.selected_shards)}</td><td>${fmt(row.call_started_count)}</td><td>${fmt(row.call_finished_count)}</td><td>${fmt(row.call_retry_count)}</td><td>${fmt(row.call_error_count)}</td><td>${fmt(row.model_output_receipt_count)}</td><td>${fmt(row.model_output_error_count)}</td><td>${fmt((row.usage || {}).total_tokens)}</td></tr>`).join("");
    }
    function renderRecentResults(snapshot) {
      const rows = get(snapshot, "raw_flywheel.recent_results", []).slice(-40).reverse();
      byId("recent-results").innerHTML = rows.map(row => `<tr><td>${esc(row.provider)}/${esc(row.model)}</td><td>${esc(row.lane_id || "")}</td><td>${esc(row.status || "")}</td><td>${fmt((row.usage || {}).total_tokens)}</td><td>${esc(row.duration_seconds || "")}</td><td>${row.error ? `<span class="error">${esc(row.error)}</span>` : ""}</td><td><code>${esc(row.shard_id || row.path || "")}</code></td></tr>`).join("");
    }
    function renderSourceMaterial(snapshot) {
      const rows = get(snapshot, "source_material.files", []);
      byId("source-material").innerHTML = rows.map(row => `<tr><td>${esc(row.source_id)}</td><td>${fmt(row.row_count)}</td><td>${esc(row.present)}</td><td>${esc(row.age_seconds ?? "")}</td><td><code>${esc(row.path)}</code></td></tr>`).join("");
    }
    function renderProcesses(snapshot) {
      const rows = get(snapshot, "processes.processes", []).slice(0, 16);
      byId("processes").innerHTML = rows.map(row => `<tr><td>${fmt(row.pid)}</td><td>${esc(row.elapsed)}</td><td>${esc((row.matched_terms || []).join(", "))}</td><td><code>${esc(row.args)}</code></td></tr>`).join("");
    }
    function commandSignal(args) {
      const text = String(args || "");
      const model = (text.match(/--model\s+([^\s]+)/) || [])[1] || "";
      const provider = (text.match(/--provider\s+([^\s]+)/) || [])[1] || "";
      const mode = (text.match(/--mode\s+([^\s]+)/) || [])[1] || "";
      const offset = (text.match(/--start-offset\s+([^\s]+)/) || [])[1] || "";
      const batch = (text.match(/--batch-size\s+([^\s]+)/) || [])[1] || "";
      const workers = (text.match(/--workers\s+([^\s]+)/) || [])[1] || "";
      const label = [provider, model, mode].filter(Boolean).join("/");
      const detail = [`offset=${offset}`, `batch=${batch}`, `workers=${workers}`].filter(part => !part.endsWith("=")).join(" ");
      return { label: label || "monitor/browser", detail };
    }
    function renderActiveCalls(snapshot) {
      const calls = get(snapshot, "raw_flywheel.active_calls", []).slice(-40).reverse();
      if (calls.length) {
        byId("active-calls").innerHTML = calls.map(row => `<tr><td>${esc(row.created_at || "")}</td><td>${esc(row.lane_id || "")}</td><td>${esc(row.provider || "")}/${esc(row.model || "")}</td><td><code>${esc(row.shard_id || row.path || "")}</code></td><td>${esc(row.status || "started")}</td></tr>`).join("");
        return;
      }
      const rows = get(snapshot, "processes.processes", []).filter(row =>
        (row.matched_terms || []).some(term => term.includes("run_primitive") || term.includes("remote-debugging"))
      ).slice(0, 20);
      byId("active-calls").innerHTML = rows.map(row => {
        const signal = commandSignal(row.args);
        return `<tr><td>${fmt(row.pid)}</td><td>${esc(row.elapsed)}</td><td>${esc((row.matched_terms || []).join(", "))}</td><td>${esc(signal.label)}<br><span class="muted">${esc(signal.detail)}</span></td><td><code>${esc(row.args)}</code></td></tr>`;
      }).join("");
    }
    function appendConsolePayload(payload) {
      for (const entry of payload.entries || []) {
        const key = `${payload.created_at}|${entry.kind}|${entry.source}|${entry.message}`;
        if (consoleSeen.has(key)) continue;
        consoleSeen.add(key);
        consoleLines.push({ ...entry, created_at: payload.created_at });
      }
      consoleLines = consoleLines.slice(-maxConsoleLines);
      if (consoleSeen.size > maxConsoleLines * 3) {
        consoleSeen = new Set(consoleLines.map(entry => `${entry.created_at}|${entry.kind}|${entry.source}|${entry.message}`));
      }
      renderConsole();
    }
    function renderConsole() {
      const el = byId("console-stream");
      const wasNearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 80;
      el.innerHTML = consoleLines.map(entry => `<div class="console-line"><span class="kind">${esc(entry.kind)}</span><span class="source" title="${esc(entry.source)}">${esc(entry.source)}</span><span class="message">${esc(entry.message)}</span></div>`).join("");
      if (wasNearBottom) el.scrollTop = el.scrollHeight;
    }
    function render(snapshot) {
      appendHistory(snapshot);
      byId("run-date").textContent = snapshot.run_date || "-";
      byId("updated-at").textContent = snapshot.created_at || "-";
      byId("candidate-state").textContent = String(snapshot.candidate);
      byId("truth-state").textContent = String(snapshot.serves_truth);
      renderMetrics(snapshot);
      renderVisuals(snapshot);
      renderAlerts(snapshot);
      renderLanes(snapshot);
      renderRawByModel(snapshot);
      renderBatches(snapshot);
      renderActiveCalls(snapshot);
      renderRecentResults(snapshot);
      renderSourceMaterial(snapshot);
      renderProcesses(snapshot);
    }
    async function poll() {
      try {
        byId("poll-state").textContent = "fetching";
        const response = await fetch(`/snapshot.json?ts=${Date.now()}`, { cache: "no-store" });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const snapshot = await response.json();
        render(snapshot);
        byId("poll-state").textContent = `ok every ${refreshSeconds}s`;
      } catch (error) {
        byId("poll-state").textContent = `error: ${error.message}`;
      }
    }
    async function pollConsole() {
      try {
        const response = await fetch(`/api/console?ts=${Date.now()}`, { cache: "no-store" });
        if (response.ok) appendConsolePayload(await response.json());
      } catch {}
    }
    function connectEvents() {
      if (!("EventSource" in window)) {
        setInterval(pollConsole, Math.max(1, refreshSeconds) * 1000);
        return;
      }
      const stream = new EventSource("/api/events");
      stream.addEventListener("open", () => { byId("poll-state").textContent = "sse connected"; });
      stream.addEventListener("snapshot", event => {
        try {
          const snapshot = JSON.parse(event.data);
          render(snapshot);
          byId("poll-state").textContent = `sse ok every ${refreshSeconds}s`;
        } catch (error) {
          byId("poll-state").textContent = `sse parse error: ${error.message}`;
        }
      });
      stream.addEventListener("console", event => {
        try { appendConsolePayload(JSON.parse(event.data)); } catch {}
      });
      stream.addEventListener("error", () => {
        byId("poll-state").textContent = "sse reconnecting";
      });
    }
    render(initialSnapshot);
    connectEvents();
    setInterval(poll, refreshSeconds * 4000);
    setInterval(pollConsole, Math.max(1, refreshSeconds) * 2000);
    setTimeout(poll, 500);
    setTimeout(pollConsole, 700);
  </script>
</body>
</html>
""".replace("__INITIAL_SNAPSHOT__", initial_snapshot_json).replace("__REFRESH_SECONDS__", str(refresh))


def write_dashboard(snapshot: dict[str, Any], *, out_dir: Path, refresh_seconds: int) -> dict[str, str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    snapshot_path = out_dir / "snapshot.json"
    index_path = out_dir / "index.html"
    snapshot_path.write_text(json.dumps(snapshot, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    index_path.write_text(build_html(snapshot, refresh_seconds=refresh_seconds), encoding="utf-8")
    return {"snapshot_path": _rel(snapshot_path), "index_path": _rel(index_path)}


def serve(
    run_date: str,
    *,
    host: str,
    port: int,
    refresh_seconds: int,
    check_cdp_target: bool,
    aggregate_prefix: str = "",
) -> None:
    class Handler(BaseHTTPRequestHandler):
        def _send(self, status: int, body: bytes, content_type: str) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:  # noqa: N802
            path = urllib.parse.urlparse(self.path).path
            if path == "/api/events":
                return self._send_events()
            snapshot = build_snapshot(run_date=run_date, aggregate_prefix=aggregate_prefix, check_cdp_target=check_cdp_target)
            if path in {"/snapshot.json", "/api/snapshot"}:
                body = json.dumps(snapshot, indent=2, sort_keys=True).encode("utf-8")
                return self._send(200, body, "application/json")
            if path == "/api/console":
                payload = build_console_payload(run_date, check_cdp_target=check_cdp_target, aggregate_prefix=aggregate_prefix)
                body = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
                return self._send(200, body, "application/json")
            if path in {"/", "/index.html"}:
                body = build_html(snapshot, refresh_seconds=refresh_seconds).encode("utf-8")
                return self._send(200, body, "text/html; charset=utf-8")
            return self._send(404, b'{"error":"not_found","serves_truth":false}\n', "application/json")

        def _sse_event(self, event: str, payload: dict[str, Any]) -> None:
            body = json.dumps(payload, sort_keys=True)
            self.wfile.write(f"event: {event}\n".encode("utf-8"))
            for line in body.splitlines() or ["{}"]:
                self.wfile.write(f"data: {line}\n".encode("utf-8"))
            self.wfile.write(b"\n")
            self.wfile.flush()

        def _send_events(self) -> None:
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Connection", "keep-alive")
            self.end_headers()
            try:
                self.wfile.write(b"retry: 3000\n\n")
                self.wfile.flush()
                for _ in range(3600):
                    snapshot = build_snapshot(run_date=run_date, aggregate_prefix=aggregate_prefix, check_cdp_target=check_cdp_target)
                    console = build_console_payload(run_date, check_cdp_target=check_cdp_target, aggregate_prefix=aggregate_prefix)
                    self._sse_event("snapshot", snapshot)
                    self._sse_event("console", console)
                    time.sleep(max(1, int(refresh_seconds)))
            except (BrokenPipeError, ConnectionResetError):
                return

        def log_message(self, fmt: str, *args: Any) -> None:
            sys.stderr.write("gemma-monitor: " + (fmt % args) + "\n")

    server = ThreadingHTTPServer((host, port), Handler)
    print(f"Gemma 4 primitive monitor serving http://{host}:{port}/ for {run_date}", flush=True)
    server.serve_forever()


def _self_test() -> int:
    snapshot = build_snapshot(run_date="1900-01-01", include_processes=False, check_cdp_target=False)
    text = format_text(snapshot)
    html_doc = build_html(snapshot, refresh_seconds=PRIMITIVE_FACTORY_MONITOR_REFRESH_SECONDS)
    ok = (
        snapshot["candidate"] is True
        and snapshot["serves_truth"] is False
        and "Gemma 4 primitive monitor" in text
        and "Gemma 4 Primitive Monitor" in html_doc
        and "/api/events" in html_doc
        and "Console Stream" in html_doc
        and snapshot["gemma"]["totals"]["usage"]["total_tokens"] == 0
    )
    print("PASS - Gemma usage monitor builds candidate-only text/HTML snapshots." if ok else "FAIL")
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default=_today_utc())
    parser.add_argument("--aggregate-prefix", default="")
    parser.add_argument("--format", choices=["text", "json", "html"], default="text")
    parser.add_argument("--write-dashboard", action="store_true")
    parser.add_argument("--out-dir", default=str(_resource(PRIMITIVE_FACTORY_MONITOR_DIST_DIR)))
    parser.add_argument("--no-processes", action="store_true")
    parser.add_argument("--no-cdp-check", action="store_true")
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=PRIMITIVE_FACTORY_GEMMA_MONITOR_DEFAULT_PORT)
    parser.add_argument("--refresh-seconds", type=int, default=PRIMITIVE_FACTORY_MONITOR_REFRESH_SECONDS)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)

    if args.self_test:
        return _self_test()
    if args.serve:
        serve(
            args.date,
            host=args.host,
            port=args.port,
            refresh_seconds=args.refresh_seconds,
            check_cdp_target=not args.no_cdp_check,
            aggregate_prefix=args.aggregate_prefix,
        )
        return 0

    snapshot = build_snapshot(
        run_date=args.date,
        aggregate_prefix=args.aggregate_prefix,
        include_processes=not args.no_processes,
        check_cdp_target=not args.no_cdp_check,
    )
    if args.write_dashboard:
        written = write_dashboard(snapshot, out_dir=Path(args.out_dir), refresh_seconds=args.refresh_seconds)
        snapshot["written"] = written
    if args.format == "json":
        print(json.dumps(snapshot, indent=2, sort_keys=True))
    elif args.format == "html":
        print(build_html(snapshot, refresh_seconds=args.refresh_seconds))
    else:
        print(format_text(snapshot), end="")
        if args.write_dashboard:
            print(f"Dashboard written: {snapshot['written']['index_path']}")
            print(f"Snapshot written: {snapshot['written']['snapshot_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
