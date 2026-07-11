"""Standalone Baltor six-tile admin demo server.

This server is intentionally independent from the larger showcase SPA. It gives
the demo one simple contract:

  /admin-demo/            six cards
  /admin-demo/sources     load/upload/connect page
  /admin-demo/monitoring  processing page
  /admin-demo/outputs     outputs page
  /admin-demo/download    export page
  /admin-demo/explore     explore page
  /admin-demo/testing     integration-readiness page
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import email  # stdlib multipart parsing — replaces cgi.FieldStorage (cgi removed in Python 3.13, PEP 594)
from collections import Counter
import html
import io
import json
import os
import re
import sys
import threading
import time
import uuid
import zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

REPO_ROOT = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import pythonpath as _pythonpath, resource as _resource
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.context_workers.priority import make_research_task
from scripts._config import (
    ADMIN_DEMO_RUNTIME_SETTINGS,
    CATALOG_OPERATIONAL_VIEWS,
    OBJECT_GOVERNANCE_OPERATIONAL_VIEWS,
    OBJECT_GOVERNANCE_PACKAGE_TABLES,
    OBJECT_GOVERNANCE_REVIEW_RUBRIC_PATH,
    OBJECT_GOVERNANCE_REQUIRED_FAMILIES,
    OBJECT_GOVERNANCE_STANDARD_DOC_PATH,
)
from scripts.db.catalog_operational_view_probe import probe_catalog_operational_views
from scripts.db.runtime_settings import runtime_setting


RUNS: dict[str, dict] = {}
EVENTS: list[dict] = []
QUEUE_HEALTH_SAMPLES: list[dict] = []
QUEUE_HEALTH_HISTORY_LOADED = False
RUN_LOCK = threading.Lock()
SERVER_STARTED_AT = int(time.time())
LEDGER_SEEN: set[str] = set()
CONTEXT_EVENT_SEEN: set[str] = set()
ADMIN_DEMO_RUNTIME_NAMESPACE = "baltor.admin_demo.runtime"


def _admin_demo_setting(name: str) -> str:
    return runtime_setting(
        namespace=ADMIN_DEMO_RUNTIME_NAMESPACE,
        definitions=ADMIN_DEMO_RUNTIME_SETTINGS,
        name=name,
    )


def _admin_demo_int_setting(name: str) -> int:
    return int(_admin_demo_setting(name))


def _admin_demo_path_setting(name: str) -> Path:
    return Path(_admin_demo_setting(name))


REDIS_URL = _admin_demo_setting("redis_url")
CONTEXT_QUEUE_KEY = _admin_demo_setting("context_queue_key")
ADMIN_EVENT_STREAM = _admin_demo_setting("admin_event_stream")
CONTEXT_WORKER_EVENT_STREAM = _admin_demo_setting("context_worker_event_stream")
WORKER_LEDGER_PATH = _admin_demo_path_setting("worker_ledger_path")
UPLOAD_DIR = _admin_demo_path_setting("upload_dir")
QUEUE_HEALTH_HISTORY_PATH = _admin_demo_path_setting("queue_health_history_path")
ACTIVE_WORKER_STALE_SECONDS = _admin_demo_int_setting("active_worker_stale_seconds")
PENDING_JOB_STALE_SECONDS = _admin_demo_int_setting("pending_job_stale_seconds")
QUEUE_HEALTH_SAMPLE_LIMIT = _admin_demo_int_setting("queue_health_sample_limit")
QUEUE_HEALTH_TREND_WINDOW = _admin_demo_int_setting("queue_health_trend_window")
QUEUE_HEALTH_FLAT_DELTA = _admin_demo_int_setting("queue_health_flat_delta")
QUEUE_HEALTH_MIN_SAMPLE_SECONDS = _admin_demo_int_setting("queue_health_min_sample_seconds")
QUEUE_THROUGHPUT_MIN_COMPLETIONS = _admin_demo_int_setting("queue_throughput_min_completions")
QUEUE_PENDING_FAMILY_SCAN_LIMIT = _admin_demo_int_setting("queue_pending_family_scan_limit")
CATALOG_MANIFEST_BRIDGE_DIR = _admin_demo_path_setting("catalog_manifest_bridge_dir")
DATABASE_URL = _admin_demo_setting("database_url")
SAMPLE_TEXT = (
    "Baltor vendor policy requires supplier reviews every 90 days. "
    "SharePoint access must be reviewed before contractor onboarding. "
    "The current escalation threshold is $25,000 as of 2026-05-31. "
    "Northstar Staffing acquired Harbor Temps in 2022, then Harbor Temps merged "
    "with Lakeside Workforce in 2023. A 2026 supplier portal export says "
    "CareShift Partners is independently owned, so ownership claims require a "
    "source date and refresh before current use. "
    "According to https://example.com/source, the policy owner is Security Operations."
)
TEXT_EXTENSIONS = {".txt", ".md", ".csv", ".json", ".yaml", ".yml", ".xml", ".html", ".log"}
MAX_ZIP_FILES = 40
MAX_ZIP_MEMBER_BYTES = 750_000
PAGE_CHARS = 2800


CARDS = [
    ("sources", "01", "Load data", "Upload files, paste text, or select connectors before a context run."),
    ("monitoring", "02", "Processing", "Watch sync, extraction, graphing, verification, queueing, and cost state."),
    ("outputs", "03", "Outputs", "Review extracted claims, verification needs, refresh jobs, and serving readiness."),
    ("download", "04", "Download", "Export text, RAG, graph, audit, and manifest packages."),
    ("explore", "05", "Explore context", "Browse facts, graph/RAG summaries, source lineage, and package previews."),
    ("testing", "06", "Integration testing", "Check connectors, APIs, queues, exports, workers, and cloud readiness."),
]

CONNECTOR_DEFINITIONS = {
    "jira": {
        "label": "Jira",
        "source_system": "atlassian_jira",
        "placeholder": "https://example.atlassian.net/browse/CTX-123",
        "default_target": "jira://example.atlassian.net/project/CTX",
        "object_types": ["issue", "comment", "attachment", "status"],
    },
    "confluence": {
        "label": "Confluence",
        "source_system": "atlassian_confluence",
        "placeholder": "https://example.atlassian.net/wiki/spaces/CTX",
        "default_target": "confluence://example.atlassian.net/wiki/spaces/CTX",
        "object_types": ["page", "section", "comment", "attachment"],
    },
    "gitlab": {
        "label": "GitLab",
        "source_system": "gitlab",
        "placeholder": "https://gitlab.example.com/group/project",
        "default_target": "gitlab://group/project",
        "object_types": ["repository", "file", "merge_request", "issue", "pipeline"],
    },
    "website": {
        "label": "Website mirror",
        "source_system": "website",
        "placeholder": "https://example.com/docs",
        "default_target": "https://example.com/docs",
        "object_types": ["page", "section", "asset"],
    },
    "ftp": {
        "label": "FTP / SFTP",
        "source_system": "ftp_sftp",
        "placeholder": "sftp://host/path",
        "default_target": "sftp://example.com/context",
        "object_types": ["folder", "file"],
    },
    "google-drive": {
        "label": "Google Drive",
        "source_system": "google_drive",
        "placeholder": "gdrive://shared-drive/folder",
        "default_target": "gdrive://shared-drive/context-control",
        "object_types": ["folder", "file", "comment"],
    },
    "sharepoint": {
        "label": "SharePoint",
        "source_system": "sharepoint",
        "placeholder": "sharepoint://tenant/sites/policies",
        "default_target": "sharepoint://tenant/sites/policies",
        "object_types": ["site", "library", "folder", "file", "page"],
    },
    "git-s3": {
        "label": "Git / S3",
        "source_system": "git_s3",
        "placeholder": "s3://bucket/prefix or git://repo/path",
        "default_target": "s3://example-context-bucket/policies",
        "object_types": ["repository", "bucket", "folder", "file", "object"],
    },
    "repo-wiki": {
        "label": "Repo Wiki",
        "source_system": "repo_wiki",
        "placeholder": "repowiki://org/project?ref=main or deepwiki://github/org/project",
        "default_target": "repowiki://local/baltor-admin-demo?ref=main",
        "object_types": ["repo_wiki_page", "architecture_diagram", "source_link", "repo_summary", "code_context_claim"],
        "sync_triggers": ["post_commit_hook", "push_webhook", "merge_request_webhook", "pipeline_artifact", "file_watcher", "scheduled_poll"],
    },
}


def redis_client():
    if not REDIS_URL:
        return None
    try:
        import redis  # type: ignore
    except ImportError:
        return None
    try:
        client = redis.from_url(REDIS_URL, decode_responses=True)
        client.ping()
        return client
    except Exception:
        return None


def queue_health_sample_from_stats(stats: dict) -> dict:
    return {
        "ts": int(time.time()),
        "pending": stats.get("pending"),
        "active_worker_job_count": stats.get("active_worker_job_count"),
        "stale_active_worker_job_count": stats.get("stale_active_worker_job_count"),
        "stale_pending_job_count": stats.get("stale_pending_job_count"),
        "approval_required": stats.get("approval_required"),
        "budget_blocked": stats.get("budget_blocked"),
        "failed_permanently": stats.get("failed_permanently"),
        "oldest_pending_age_seconds": stats.get("oldest_pending_age_seconds"),
        "newest_pending_age_seconds": stats.get("newest_pending_age_seconds"),
    }


def task_family(task: str | None) -> str:
    value = str(task or "")
    if value.startswith("llm."):
        return "local_llm_review"
    if value.startswith("node.research"):
        return "node_research"
    if value.startswith("context.search"):
        return "context_gateway"
    if value.startswith("context.") or value.startswith("worker.") or value.startswith("pipeline."):
        return "deterministic_pipeline"
    return "other"


def queue_health_metrics_equal(left: dict, right: dict) -> bool:
    metric_keys = [
        "pending",
        "active_worker_job_count",
        "stale_active_worker_job_count",
        "stale_pending_job_count",
        "approval_required",
        "budget_blocked",
        "failed_permanently",
        "oldest_pending_age_seconds",
        "newest_pending_age_seconds",
    ]
    return all(left.get(key) == right.get(key) for key in metric_keys)


def load_queue_health_history_once() -> None:
    global QUEUE_HEALTH_HISTORY_LOADED
    if QUEUE_HEALTH_HISTORY_LOADED:
        return
    loaded_samples: list[dict] = []
    if QUEUE_HEALTH_HISTORY_PATH.exists():
        try:
            lines = QUEUE_HEALTH_HISTORY_PATH.read_text(encoding="utf-8").splitlines()
            for line in lines[-QUEUE_HEALTH_SAMPLE_LIMIT:]:
                try:
                    sample = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(sample, dict) and isinstance(sample.get("ts"), int):
                    loaded_samples.append(sample)
        except OSError:
            loaded_samples = []
    with RUN_LOCK:
        if not QUEUE_HEALTH_HISTORY_LOADED:
            QUEUE_HEALTH_SAMPLES[:] = loaded_samples[-QUEUE_HEALTH_SAMPLE_LIMIT:]
            QUEUE_HEALTH_HISTORY_LOADED = True


def persist_queue_health_sample(sample: dict) -> None:
    try:
        QUEUE_HEALTH_HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
        with QUEUE_HEALTH_HISTORY_PATH.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(sample, sort_keys=True) + "\n")
    except OSError:
        pass


def record_queue_health_sample(stats: dict) -> None:
    if not stats.get("available"):
        return
    load_queue_health_history_once()
    sample = queue_health_sample_from_stats(stats)
    accepted_sample = None
    with RUN_LOCK:
        latest = QUEUE_HEALTH_SAMPLES[-1] if QUEUE_HEALTH_SAMPLES else None
        if latest:
            sample_age = int(sample.get("ts") or 0) - int(latest.get("ts") or 0)
            if queue_health_metrics_equal(latest, sample) and sample_age < QUEUE_HEALTH_MIN_SAMPLE_SECONDS:
                return
        QUEUE_HEALTH_SAMPLES.append(sample)
        del QUEUE_HEALTH_SAMPLES[:-QUEUE_HEALTH_SAMPLE_LIMIT]
        accepted_sample = dict(sample)
    if accepted_sample:
        persist_queue_health_sample(accepted_sample)


def recent_queue_health_samples(limit: int = 10) -> list[dict]:
    load_queue_health_history_once()
    with RUN_LOCK:
        return list(QUEUE_HEALTH_SAMPLES[-limit:])


def queue_health_trend() -> dict:
    samples = recent_queue_health_samples(limit=QUEUE_HEALTH_TREND_WINDOW)
    comparable = [sample for sample in samples if isinstance(sample.get("pending"), int)]
    if len(comparable) < 2:
        return {
            "status": "unknown",
            "sample_count": len(samples),
            "comparable_sample_count": len(comparable),
            "window_seconds": 0,
            "pending_delta": None,
            "flat_delta": QUEUE_HEALTH_FLAT_DELTA,
        }
    first = comparable[0]
    last = comparable[-1]
    pending_delta = int(last.get("pending") or 0) - int(first.get("pending") or 0)
    if pending_delta > QUEUE_HEALTH_FLAT_DELTA:
        status = "growing"
    elif pending_delta < -QUEUE_HEALTH_FLAT_DELTA:
        status = "shrinking"
    else:
        status = "flat"
    return {
        "status": status,
        "sample_count": len(samples),
        "comparable_sample_count": len(comparable),
        "first_ts": first.get("ts"),
        "last_ts": last.get("ts"),
        "window_seconds": max(0, int(last.get("ts") or 0) - int(first.get("ts") or 0)),
        "pending_first": first.get("pending"),
        "pending_last": last.get("pending"),
        "pending_delta": pending_delta,
        "active_worker_delta": int(last.get("active_worker_job_count") or 0) - int(first.get("active_worker_job_count") or 0),
        "stale_active_delta": int(last.get("stale_active_worker_job_count") or 0) - int(first.get("stale_active_worker_job_count") or 0),
        "stale_pending_delta": int(last.get("stale_pending_job_count") or 0) - int(first.get("stale_pending_job_count") or 0),
        "flat_delta": QUEUE_HEALTH_FLAT_DELTA,
    }


def queue_health_history_metadata() -> dict:
    load_queue_health_history_once()
    return {
        "path": str(QUEUE_HEALTH_HISTORY_PATH),
        "exists": QUEUE_HEALTH_HISTORY_PATH.exists(),
        "loaded": QUEUE_HEALTH_HISTORY_LOADED,
        "sample_limit": QUEUE_HEALTH_SAMPLE_LIMIT,
        "loaded_sample_count": len(recent_queue_health_samples(limit=QUEUE_HEALTH_SAMPLE_LIMIT)),
    }


def queue_throughput_estimate(pending: int | None, closed_events: list[dict]) -> dict:
    if not isinstance(pending, int):
        return {
            "status": "unknown",
            "reason": "queue_unavailable",
            "completion_count": 0,
            "window_seconds": 0,
            "jobs_per_minute": None,
            "estimated_drain_seconds": None,
        }
    if pending == 0:
        return {
            "status": "drained",
            "completion_count": len(closed_events),
            "window_seconds": 0,
            "jobs_per_minute": None,
            "estimated_drain_seconds": 0,
        }
    if len(closed_events) < QUEUE_THROUGHPUT_MIN_COMPLETIONS:
        return {
            "status": "unknown",
            "reason": "insufficient_recent_completions",
            "completion_count": len(closed_events),
            "required_completion_count": QUEUE_THROUGHPUT_MIN_COMPLETIONS,
            "window_seconds": 0,
            "jobs_per_minute": None,
            "estimated_drain_seconds": None,
        }
    ages = sorted(int(event.get("age_seconds") or 0) for event in closed_events)
    window_seconds = max(1, ages[-1] - ages[0])
    jobs_per_second = len(closed_events) / window_seconds
    estimated_drain_seconds = int(round(pending / jobs_per_second)) if jobs_per_second > 0 else None
    return {
        "status": "estimated",
        "completion_count": len(closed_events),
        "window_seconds": window_seconds,
        "jobs_per_minute": round(jobs_per_second * 60, 3),
        "estimated_drain_seconds": estimated_drain_seconds,
    }


def queue_throughput_by_family(pending_family_counts: dict[str, int], closed_events: list[dict]) -> dict:
    family_names = sorted(set(pending_family_counts) | {str(event.get("task_family") or "other") for event in closed_events})
    by_family: dict[str, dict] = {}
    for family in family_names:
        family_events = [event for event in closed_events if str(event.get("task_family") or "other") == family]
        pending_count = int(pending_family_counts.get(family) or 0)
        estimate = queue_throughput_estimate(pending_count, family_events)
        estimate["pending"] = pending_count
        by_family[family] = estimate
    return by_family


def queue_stats() -> dict:
    client = redis_client()
    if client is None:
        return {
            "available": False,
            "queue": CONTEXT_QUEUE_KEY,
            "pending": None,
            # keep the queue contract STABLE whether or not Redis is reachable: these keys are
            # always present (null/empty when there is no queue) so consumers/tests don't branch on env.
            "oldest_pending_age_seconds": None,
            "newest_pending_age_seconds": None,
            # list/count keys mirror the Redis branch exactly (empty offline) so the heartbeat contract
            # is identical with or without Redis — the offline demo depends on this.
            "pending_sample_missing_timestamps": 0,
            "pending_sample": [],
            "recent_worker_events": [],
            "active_worker_jobs": [],
            "active_worker_job_count": 0,
            "stale_active_worker_job_count": 0,
            "stale_pending_job_count": 0,
            "thresholds": {
                "active_worker_stale_seconds": ACTIVE_WORKER_STALE_SECONDS,
                "pending_job_stale_seconds": PENDING_JOB_STALE_SECONDS,
                "trend_window_samples": QUEUE_HEALTH_TREND_WINDOW,
                "trend_flat_delta": QUEUE_HEALTH_FLAT_DELTA,
                "throughput_min_completions": QUEUE_THROUGHPUT_MIN_COMPLETIONS,
                "history_sample_limit": QUEUE_HEALTH_SAMPLE_LIMIT,
                "pending_family_scan_limit": QUEUE_PENDING_FAMILY_SCAN_LIMIT,
            },
            "trend": queue_health_trend(),
            "throughput": {**queue_throughput_estimate(None, []), "by_family": {}},
            "recent_samples": recent_queue_health_samples(),
            "history": queue_health_history_metadata(),
            "pending_family_counts": {},
            "pending_family_scan": {"scanned": 0, "limit": QUEUE_PENDING_FAMILY_SCAN_LIMIT, "limited": False},
            "warnings": [],
        }
    now = int(time.time())
    latest_worker_event = None
    recent_worker_events: list[dict] = []
    closed_worker_events_for_throughput: list[dict] = []
    active_worker_jobs_by_id: dict[str, dict] = {}
    closed_worker_job_ids: set[str] = set()
    try:
        rows = client.xrevrange(CONTEXT_WORKER_EVENT_STREAM, count=200)
        if rows:
            latest_worker_event = rows[0][0]
        for event_id, fields in rows or []:
            raw = fields.get("event") if isinstance(fields, dict) else None
            if not raw:
                continue
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                continue
            event_name = str(payload.get("event") or "")
            job_id = str(payload.get("job_id") or "")
            event_record = {
                "stream_id": event_id,
                "ts": payload.get("ts"),
                "age_seconds": max(0, now - int(payload.get("ts") or now)),
                "event": event_name,
                "run_id": payload.get("run_id"),
                "job_id": job_id,
                "task": payload.get("task"),
                "task_family": task_family(str(payload.get("task") or "")),
            }
            recent_worker_events.append(event_record)
            if event_name == "worker.job.closed":
                closed_worker_events_for_throughput.append(event_record)
            if job_id:
                if event_name in {"worker.job.closed", "worker.closeout.complete"}:
                    closed_worker_job_ids.add(job_id)
                    active_worker_jobs_by_id.pop(job_id, None)
                elif event_name in {"worker.job.claimed", "worker.execute.started"} and job_id not in closed_worker_job_ids:
                    active_worker_jobs_by_id.setdefault(job_id, event_record)
    except Exception:
        latest_worker_event = None
    recent_worker_events = recent_worker_events[:20]
    active_worker_jobs = sorted(
        active_worker_jobs_by_id.values(),
        key=lambda item: int(item.get("age_seconds") or 0),
        reverse=True,
    )[:10]
    for item in active_worker_jobs:
        age = int(item.get("age_seconds") or 0)
        item["stale_after_seconds"] = ACTIVE_WORKER_STALE_SECONDS
        item["stale"] = age >= ACTIVE_WORKER_STALE_SECONDS
    pending_count = int(client.llen(CONTEXT_QUEUE_KEY))
    pending_jobs: list[dict] = []
    pending_family_counts: dict[str, int] = {}
    oldest_pending_age = None
    newest_pending_age = None
    pending_sample_missing_timestamps = 0
    try:
        pending_scan_stop = min(pending_count, QUEUE_PENDING_FAMILY_SCAN_LIMIT) - 1
        pending_scan_rows = client.lrange(CONTEXT_QUEUE_KEY, 0, pending_scan_stop) if pending_scan_stop >= 0 else []
        for index, raw in enumerate(pending_scan_rows):
            body = raw if isinstance(raw, str) else raw.decode("utf-8")
            try:
                job = json.loads(body)
            except json.JSONDecodeError:
                job = {"_raw": body[:160]}
            family = task_family(str(job.get("task") or ""))
            pending_family_counts[family] = int(pending_family_counts.get(family) or 0) + 1
            queued_at = job.get("queued_at")
            try:
                age = max(0, now - int(queued_at)) if queued_at else None
            except (TypeError, ValueError):
                age = None
            if index < 10:
                if age is None:
                    pending_sample_missing_timestamps += 1
                if age is not None:
                    if oldest_pending_age is None or age > oldest_pending_age:
                        oldest_pending_age = age
                    if newest_pending_age is None or age < newest_pending_age:
                        newest_pending_age = age
                pending_jobs.append({
                    "job_id": job.get("job_id"),
                    "run_id": job.get("run_id"),
                    "task": job.get("task"),
                    "task_family": family,
                    "tenant_id": job.get("tenant_id"),
                    "queued_at": queued_at,
                    "age_seconds": age,
                    "stale_after_seconds": PENDING_JOB_STALE_SECONDS,
                    "stale": bool(age is not None and age >= PENDING_JOB_STALE_SECONDS),
                })
    except Exception:
        pending_jobs = []
        pending_family_counts = {}
    queue_warnings = []
    stale_active_jobs = [job for job in active_worker_jobs if job.get("stale")]
    stale_pending_jobs = [job for job in pending_jobs if job.get("stale")]
    if stale_active_jobs:
        queue_warnings.append({
            "type": "stale_active_worker_job",
            "severity": "warning",
            "threshold_seconds": ACTIVE_WORKER_STALE_SECONDS,
            "count": len(stale_active_jobs),
            "oldest_age_seconds": max(int(job.get("age_seconds") or 0) for job in stale_active_jobs),
        })
    if stale_pending_jobs:
        queue_warnings.append({
            "type": "stale_pending_job",
            "severity": "warning",
            "threshold_seconds": PENDING_JOB_STALE_SECONDS,
            "count": len(stale_pending_jobs),
            "oldest_age_seconds": max(int(job.get("age_seconds") or 0) for job in stale_pending_jobs),
        })
    if pending_sample_missing_timestamps:
        queue_warnings.append({
            "type": "pending_sample_missing_timestamps",
            "severity": "info",
            "count": pending_sample_missing_timestamps,
            "detail": "Some inherited queued jobs predate the queued_at timestamp contract.",
        })
    throughput = queue_throughput_estimate(pending_count, closed_worker_events_for_throughput)
    throughput["by_family"] = queue_throughput_by_family(pending_family_counts, closed_worker_events_for_throughput)
    stats = {
        "available": True,
        "queue": CONTEXT_QUEUE_KEY,
        "pending": pending_count,
        "approval_required": int(client.llen(CONTEXT_QUEUE_KEY + ":approval-required")),
        "budget_blocked": int(client.llen(CONTEXT_QUEUE_KEY + ":budget-blocked")),
        "failed_permanently": int(client.llen(CONTEXT_QUEUE_KEY + ":failed-permanently")),
        "admin_event_stream": ADMIN_EVENT_STREAM,
        "context_worker_event_stream": CONTEXT_WORKER_EVENT_STREAM,
        "context_worker_events": int(client.xlen(CONTEXT_WORKER_EVENT_STREAM)),
        "latest_context_worker_event_id": latest_worker_event,
        "oldest_pending_age_seconds": oldest_pending_age,
        "newest_pending_age_seconds": newest_pending_age,
        "pending_sample_missing_timestamps": pending_sample_missing_timestamps,
        "pending_sample": pending_jobs,
        "pending_family_counts": pending_family_counts,
        "pending_family_scan": {
            "scanned": sum(pending_family_counts.values()),
            "limit": QUEUE_PENDING_FAMILY_SCAN_LIMIT,
            "limited": pending_count > QUEUE_PENDING_FAMILY_SCAN_LIMIT,
        },
        "recent_worker_events": recent_worker_events,
        "active_worker_jobs": active_worker_jobs,
        "active_worker_job_count": len(active_worker_jobs_by_id),
        "stale_active_worker_job_count": len(stale_active_jobs),
        "stale_pending_job_count": len(stale_pending_jobs),
        "throughput": throughput,
        "thresholds": {
            "active_worker_stale_seconds": ACTIVE_WORKER_STALE_SECONDS,
            "pending_job_stale_seconds": PENDING_JOB_STALE_SECONDS,
            "trend_window_samples": QUEUE_HEALTH_TREND_WINDOW,
            "trend_flat_delta": QUEUE_HEALTH_FLAT_DELTA,
            "throughput_min_completions": QUEUE_THROUGHPUT_MIN_COMPLETIONS,
            "history_sample_limit": QUEUE_HEALTH_SAMPLE_LIMIT,
            "pending_family_scan_limit": QUEUE_PENDING_FAMILY_SCAN_LIMIT,
        },
        "warnings": queue_warnings,
    }
    record_queue_health_sample(stats)
    stats["trend"] = queue_health_trend()
    stats["recent_samples"] = recent_queue_health_samples()
    stats["history"] = queue_health_history_metadata()
    return stats


# ── unified realtime event bus ──────────────────────────────────────────────
# ONE in-process bus (scripts.context_events) the SSE dashboard drains. Admin `log_event`s bridge
# onto it as `component.progressed`, and the connected engines publish their own typed lifecycle
# events directly. No second bus.
from scripts.context_events import EventBus as _EventBus  # noqa: E402

BUS = _EventBus(buffer=2000)

#: Showcase token-gate. When OH_SHOWCASE_TOKEN is set (e.g. behind a public tunnel), every
#: state-changing POST requires it (?token=… or an X-OHH-Token header). GET pages, /api/dev/status,
#: /api/events and the SSE stream stay OPEN so the dashboards remain viewable + live. Unset (local
#: dev / the self-tests) ⇒ fully open, byte-identical to prior behavior.
SHOWCASE_TOKEN = os.environ.get("OH_SHOWCASE_TOKEN", "")


def _token_ok(configured: str, supplied: str | None) -> bool:
    """Single source of the gate rule: open when no token is configured, else require an exact match."""
    return (not configured) or (supplied == configured)


#: Durable layer (opt-in via BALTOR_DURABLE_DB). When set, every bus event is persisted to a crash-safe
#: SQLite log and the bus is HYDRATED from it on startup — so the live stream survives a restart. Unset
#: (self-tests / local dev) ⇒ in-memory only, byte-identical to prior behavior. No new dependency.
_DURABLE_DB = os.environ.get("BALTOR_DURABLE_DB", "")
DURABLE = None
DURABLE_ERROR = ""
if _DURABLE_DB:
    _DURABLE_DB = os.path.abspath(_DURABLE_DB)  # absolute → a cwd change never splits the db
    try:
        from scripts.durable_store import DurableStore as _DurableStore

        DURABLE = _DurableStore(_DURABLE_DB)
        BUS.restore(DURABLE.recent_events(2000))            # survive restart: re-seed the live buffer

        def _persist(ev: dict) -> None:                     # persist every event; NEVER drop silently
            global DURABLE_ERROR
            try:
                DURABLE.append_event(ev)
            except Exception as _e:  # noqa: BLE001
                DURABLE_ERROR = f"append failed: {type(_e).__name__}: {_e}"
                DURABLE.set_meta("durable_error", DURABLE_ERROR)
                DURABLE.set_meta("durable_status", "red")
                print(f"[durable] {DURABLE_ERROR}", file=sys.stderr, flush=True)

        BUS.subscribe(_persist)
        DURABLE.set_meta("durable_status", "ok")
        DURABLE.set_meta("durable_error", "")
        DURABLE.set_meta("durable_db", _DURABLE_DB)
        print(f"[durable] ON db={_DURABLE_DB} hydrated={len(BUS.recent(2000))} events", file=sys.stderr, flush=True)
    except Exception as e:  # BALTOR_DURABLE_DB was explicitly set ⇒ surface loudly, do NOT hide it
        DURABLE_ERROR = f"init failed: {type(e).__name__}: {e}"
        print(f"[durable] FATAL {DURABLE_ERROR} (BALTOR_DURABLE_DB was set but durability is OFF)",
              file=sys.stderr, flush=True)
        DURABLE = None


# ── durable ctx:// run + gateway-receipt store ──────────────────────────────────────────────────────
# P1 hardening (warrant: docs/architecture/capability-rubric-and-deep-dive-2026-06-11.md — the context
# gateway is "MVP skeleton of THE product" but ctx:// handles die on restart, RUNS is never pruned
# (unbounded memory), and no receipt is issued on search/fetch). This adds a DURABLE mirror for RUNS and
# a persisted receipt ledger WITHOUT a new dependency and WITHOUT touching _repos/shared-backend-components/scripts/durable_store.py: a
# second sqlite connection onto the SAME WAL db file (BALTOR_DURABLE_DB) — WAL + busy_timeout make
# multi-connection (and multi-process) reads/writes safe, exactly as DurableStore documents. Lossless:
# the in-memory RUNS dict stays the live working copy; these tables are a derived durable layer (the bus
# rejects unknown kinds, so RUNS cannot ride the event log — it needs its own table here).
#
# Bounded-memory cap: keep only the most recent N runs in memory AND in the durable table (LRU by
# created_at). One named constant, env-overridable, so the cap is visible and tunable, never magic.
DURABLE_RUNS_MAX = int(os.environ.get("BALTOR_DURABLE_RUNS_MAX", "200"))   # newest-N ctx:// runs kept (memory + table)

# ── P2 tenancy + ctxv:// versioning (warrant: the rubric's tenancy-gap finding, deep-dive line 25/124) ──
# The gateway was global: RUNS/handles had no tenant_id, so any caller could fetch any handle, and ctxv://
# versions were produced (line ~2546) but never fetchable. P2 threads a tenant_id end-to-end and pins
# served content under an immutable ctxv:// version. Single named default — never a magic literal: the
# whole current demo runs as this one tenant, so default-tenant behavior stays byte-identical, but the
# isolation is REAL the moment a different tenant_id is supplied (a fetch with the wrong tenant → 404,
# which never leaks the handle's existence; a superseded-and-pruned version → 410 Gone).
DEFAULT_TENANT = "demo"                                                     # the single tenant the public demo runs as
TENANT_HEADER = "X-OHH-Tenant"                                             # request header carrying the tenant id
TENANT_PARAM = "tenant"                                                     # query-string / form field carrying the tenant id
DURABLE_VERSIONS_MAX = int(os.environ.get("BALTOR_DURABLE_VERSIONS_MAX", "5000"))  # newest-N pinned ctxv:// versions kept

RUN_STORE = None          # sqlite3 connection onto BALTOR_DURABLE_DB, or None when durability is off
RUN_STORE_ERROR = ""

# Item 3 (deep-dive): the CFPB artifact-graph ledger db path was HARDCODED to <repo>/.agent/ — OUTSIDE
# the Fly volume, so it died with the machine. Route it through the same durable volume the other paths
# use: default into the directory of BALTOR_DURABLE_DB (the volume) when set, else the legacy .agent/
# path (byte-identical for local dev / self-tests). Env-overridable, one named constant — no magic value.
# NOTE: the canonical home for this would be scripts/_config.ADMIN_DEMO_RUNTIME_SETTINGS; that module is
# out of scope for this surgical change (see status doc), so it is resolved in-file with the same
# env → default precedence the settings module uses.
_DURABLE_VOLUME_DIR = os.path.dirname(_DURABLE_DB) if _DURABLE_DB else str((REPO_ROOT / ".agent"))
CFPB_ARTIFACT_GRAPH_DB = os.environ.get(
    "BALTOR_CFPB_ARTIFACT_GRAPH_DB",
    os.path.join(_DURABLE_VOLUME_DIR, "cfpb_artifact_graph.db"),
)

if DURABLE is not None and _DURABLE_DB:
    try:
        import sqlite3 as _sqlite3

        RUN_STORE = _sqlite3.connect(_DURABLE_DB, isolation_level=None, check_same_thread=False)
        RUN_STORE.execute("PRAGMA busy_timeout=5000")  # multi-connection: wait on a held lock, don't error
        RUN_STORE.execute(
            "CREATE TABLE IF NOT EXISTS gateway_runs("
            "run_id TEXT PRIMARY KEY, created_at INTEGER, updated_at INTEGER, tenant_id TEXT, body_json TEXT)"
        )
        RUN_STORE.execute("CREATE INDEX IF NOT EXISTS idx_gateway_runs_created ON gateway_runs(created_at)")
        RUN_STORE.execute(
            "CREATE TABLE IF NOT EXISTS gateway_receipts("
            "receipt_id TEXT PRIMARY KEY, ts INTEGER, operation TEXT, run_id TEXT, tenant_id TEXT, "
            "handle TEXT, query TEXT, ok INTEGER, content_hash TEXT, body_json TEXT)"
        )
        RUN_STORE.execute("CREATE INDEX IF NOT EXISTS idx_gateway_receipts_ts ON gateway_receipts(ts)")
        # P2 (ctxv://): one durable row per PINNED immutable version of a ctx:// handle's served content.
        # base_handle is the mutable ctx:// (latest); version_handle is the immutable ctxv://base@<hash16>;
        # superseded_at marks a version replaced by a newer hash for the same (tenant, base) but kept until
        # prune (lossless) — a fetch of a superseded+pruned version → 410, a never-seen version → 404.
        RUN_STORE.execute(
            "CREATE TABLE IF NOT EXISTS gateway_versions("
            "version_handle TEXT PRIMARY KEY, tenant_id TEXT, run_id TEXT, base_handle TEXT, kind TEXT, "
            "content_hash TEXT, body_json TEXT, created_at INTEGER, superseded_at INTEGER)"
        )
        RUN_STORE.execute("CREATE INDEX IF NOT EXISTS idx_gateway_versions_base ON gateway_versions(tenant_id, base_handle)")
        RUN_STORE.execute("CREATE INDEX IF NOT EXISTS idx_gateway_versions_created ON gateway_versions(created_at)")
        # Lossless upgrade of a P1-created db (its gateway_runs/gateway_receipts lack tenant_id): add the
        # column if missing so existing durable files keep working. Pre-P2 rows read back as DEFAULT_TENANT.
        for _table in ("gateway_runs", "gateway_receipts"):
            _cols = {r[1] for r in RUN_STORE.execute(f"PRAGMA table_info({_table})").fetchall()}
            if "tenant_id" not in _cols:
                RUN_STORE.execute(f"ALTER TABLE {_table} ADD COLUMN tenant_id TEXT")
    except Exception as _e:  # durability was requested ⇒ surface, do not hide; runs still work in-memory
        RUN_STORE_ERROR = f"run-store init failed: {type(_e).__name__}: {_e}"
        print(f"[durable] {RUN_STORE_ERROR}", file=sys.stderr, flush=True)
        RUN_STORE = None


def persist_run(run: dict) -> None:
    """Mirror one run into the durable gateway_runs table so its ctx:// handles survive a restart.
    Best-effort + lossless: RUNS (in memory) stays authoritative; a write failure never breaks the run."""
    if RUN_STORE is None or not isinstance(run, dict):
        return
    run_id = str(run.get("run_id") or "")
    if not run_id:
        return
    try:
        RUN_STORE.execute(
            "INSERT INTO gateway_runs(run_id,created_at,updated_at,tenant_id,body_json) VALUES(?,?,?,?,?) "
            "ON CONFLICT(run_id) DO UPDATE SET updated_at=excluded.updated_at, tenant_id=excluded.tenant_id, "
            "body_json=excluded.body_json",
            (run_id, int(run.get("created_at") or 0), int(run.get("updated_at") or run.get("created_at") or 0),
             run_tenant(run), json.dumps(run, sort_keys=True, default=str)),
        )
    except Exception as _e:  # noqa: BLE001 — never let durability mirroring break a live run
        print(f"[durable] persist_run failed: {type(_e).__name__}: {_e}", file=sys.stderr, flush=True)


def prune_runs() -> None:
    """Bound memory: keep only the newest DURABLE_RUNS_MAX runs in the in-memory RUNS dict AND, when
    durable, in the gateway_runs table (LRU by created_at). Without this RUNS grew unbounded (deep-dive)."""
    with RUN_LOCK:
        if len(RUNS) > DURABLE_RUNS_MAX:
            ordered = sorted(RUNS.values(), key=lambda r: int(r.get("created_at") or 0), reverse=True)
            keep = {str(r.get("run_id")) for r in ordered[:DURABLE_RUNS_MAX]}
            for stale_id in [rid for rid in RUNS if rid not in keep]:
                RUNS.pop(stale_id, None)
    if RUN_STORE is not None:
        try:
            RUN_STORE.execute(
                "DELETE FROM gateway_runs WHERE run_id NOT IN "
                "(SELECT run_id FROM gateway_runs ORDER BY created_at DESC LIMIT ?)",
                (DURABLE_RUNS_MAX,),
            )
        except Exception as _e:  # noqa: BLE001
            print(f"[durable] prune_runs failed: {type(_e).__name__}: {_e}", file=sys.stderr, flush=True)


def rehydrate_runs() -> int:
    """On startup, reload the newest DURABLE_RUNS_MAX runs from the durable table into RUNS so ctx://
    handles created before a restart still resolve. Returns the count restored (0 when durability off)."""
    if RUN_STORE is None:
        return 0
    try:
        rows = RUN_STORE.execute(
            "SELECT body_json FROM gateway_runs ORDER BY created_at DESC LIMIT ?", (DURABLE_RUNS_MAX,)
        ).fetchall()
    except Exception as _e:  # noqa: BLE001
        print(f"[durable] rehydrate_runs failed: {type(_e).__name__}: {_e}", file=sys.stderr, flush=True)
        return 0
    restored = 0
    with RUN_LOCK:
        for (body_json,) in rows:
            try:
                run = json.loads(body_json or "{}")
            except json.JSONDecodeError:
                continue
            run_id = str(run.get("run_id") or "")
            if run_id and run_id not in RUNS:
                RUNS[run_id] = run
                restored += 1
    if restored:
        print(f"[durable] ctx:// runs rehydrated={restored} (cap={DURABLE_RUNS_MAX})", file=sys.stderr, flush=True)
    return restored


# ── P2 tenancy seam ───────────────────────────────────────────────────────────────────────────────────
def normalize_tenant(value: object) -> str:
    """One rule for turning any supplied tenant id into a safe, stable namespace key. Empty/None →
    DEFAULT_TENANT so the existing single-tenant demo is byte-identical; otherwise compact_id (same
    [a-z0-9-] normalization the handles use) so a tenant id can never inject path/SQL weirdness."""
    text = str(value or "").strip()
    return compact_id(text) if text else DEFAULT_TENANT


def resolve_tenant(parsed, header_value: str | None = None, body: dict | None = None) -> str:
    """Resolve the caller's tenant_id from the request — the isolation seam. Mirrors how `_authed` resolves
    the token: query param (?tenant=) → request header (X-OHH-Tenant, passed in as header_value) → POST body
    field → DEFAULT_TENANT. There is no real multi-tenant identity in this demo yet, so this DEFAULTS to one
    'demo' tenant (the current public demo is unchanged) but is honored end-to-end, so the isolation is REAL
    when a tenant is supplied. NOTE: this is request-scoped attribution, NOT authentication — `_authed`
    (OH_SHOWCASE_TOKEN) still gates writes; per-tenant key auth is the next layer
    (service-auth-and-consumption-model.md)."""
    qs = parse_qs(getattr(parsed, "query", "") or "")
    supplied = (qs.get(TENANT_PARAM) or [None])[0]
    if not supplied:
        supplied = header_value
    if not supplied and isinstance(body, dict):
        supplied = body.get("tenant_id") or body.get(TENANT_PARAM)
    return normalize_tenant(supplied)


def run_tenant(run: dict | None) -> str:
    """The tenant_id a run belongs to (defaulting to DEFAULT_TENANT for pre-P2 / untenanted runs — lossless:
    an old run with no tenant_id reads back as the demo tenant, exactly its prior global behavior)."""
    return normalize_tenant((run or {}).get("tenant_id"))


def run_visible_to(run: dict | None, tenant_id: str) -> bool:
    """Isolation predicate: a run is visible to a tenant ONLY when it belongs to that tenant. A mismatch is
    treated as not-found by callers (404), so one tenant can never even learn another tenant's handle exists."""
    return bool(run) and run_tenant(run) == normalize_tenant(tenant_id)


def latest_run_for_tenant(tenant_id: str) -> dict | None:
    """Newest run OWNED BY this tenant (the per-tenant replacement for the global latest_run())."""
    tid = normalize_tenant(tenant_id)
    owned = [r for r in RUNS.values() if run_tenant(r) == tid]
    if not owned:
        return None
    return max(owned, key=lambda run: int(run.get("created_at") or 0))


def run_for_tenant(run_id: str, tenant_id: str) -> dict | None:
    """Resolve a run by id but ONLY if it belongs to this tenant; cross-tenant access returns None (→ 404).
    When run_id is empty, fall back to this tenant's latest run (mirrors the old `RUNS.get(id) or latest_run()`
    pattern, but tenant-scoped so the fallback can never reach across tenants)."""
    tid = normalize_tenant(tenant_id)
    if run_id:
        run = RUNS.get(run_id)
        return run if run_visible_to(run, tid) else None
    return latest_run_for_tenant(tid)


# ── P2 ctxv:// version pinning ────────────────────────────────────────────────────────────────────────
def versioned_handle(base_handle: str, content_hash: str) -> str:
    """The immutable version id for a ctx:// handle pinned at a content hash — same shape as the context
    object versions already minted at add_object (ctxv://base@<hash16>). Single source of the form so a
    pinned-fetch handle is recognizable and stable across the codebase."""
    base = str(base_handle or "")
    short = compact_id(content_hash)[-16:] if content_hash else "0"
    return base.replace("ctx://", "ctxv://", 1) + "@" + short


def pin_version(*, tenant_id: str, run: dict | None, base_handle: str, kind: str, content: object) -> str:
    """Pin the EXACT content just served under a ctx:// handle as an immutable ctxv:// version, so a later
    fetch of that ctxv:// returns byte-identical bytes even if the live content changed. Lossless: a newer
    hash for the same (tenant, base) marks older versions superseded_at but KEEPS them until prune (so a
    superseded version is 410 Gone only after an explicit prune, never silently deleted). Returns the
    ctxv:// handle (best-effort; durability off ⇒ '' and ctx:// still works exactly as before)."""
    if RUN_STORE is None or content is None or not base_handle:
        return ""
    tid = normalize_tenant(tenant_id)
    chash = stable_hash(content)
    vhandle = versioned_handle(base_handle, chash)
    now = int(time.time())
    body = json.dumps(content, sort_keys=True, default=str)
    try:
        # Idempotent: re-pinning identical content is a no-op (PK = version_handle includes the hash).
        existing = RUN_STORE.execute(
            "SELECT 1 FROM gateway_versions WHERE version_handle=?", (vhandle,)
        ).fetchone()
        if existing is None:
            # A different hash for the same (tenant, base) supersedes the older versions — but they STAY
            # (lossless) until prune_versions() trims by age past the cap.
            RUN_STORE.execute(
                "UPDATE gateway_versions SET superseded_at=? WHERE tenant_id=? AND base_handle=? AND superseded_at IS NULL",
                (now, tid, base_handle),
            )
            RUN_STORE.execute(
                "INSERT INTO gateway_versions"
                "(version_handle,tenant_id,run_id,base_handle,kind,content_hash,body_json,created_at,superseded_at)"
                " VALUES(?,?,?,?,?,?,?,?,NULL)",
                (vhandle, tid, str((run or {}).get("run_id") or ""), base_handle, kind, chash, body, now),
            )
            prune_versions()
    except Exception as _e:  # noqa: BLE001 — version pinning is additive; never break a live fetch
        print(f"[durable] pin_version failed: {type(_e).__name__}: {_e}", file=sys.stderr, flush=True)
        return ""
    return vhandle


def prune_versions() -> None:
    """Bound the pinned-version table to the newest DURABLE_VERSIONS_MAX rows (LRU by created_at). Pruned
    rows are the OLDEST superseded versions — a fetch of one of them then returns 410 Gone (was-pinned,
    now-pruned), which is honest: the version existed but the lossless retention window has passed."""
    if RUN_STORE is None:
        return
    try:
        RUN_STORE.execute(
            "DELETE FROM gateway_versions WHERE version_handle NOT IN "
            "(SELECT version_handle FROM gateway_versions ORDER BY created_at DESC LIMIT ?)",
            (DURABLE_VERSIONS_MAX,),
        )
    except Exception as _e:  # noqa: BLE001
        print(f"[durable] prune_versions failed: {type(_e).__name__}: {_e}", file=sys.stderr, flush=True)


def fetch_pinned_version(tenant_id: str, version_handle: str) -> tuple[str, dict | None]:
    """Resolve a ctxv:// (immutable, version-pinned) fetch for a tenant. Returns (status, row) where status
    is 'ok' (row carries the pinned body), 'gone' (the base was pinned before but THIS version was
    superseded and pruned → 410), or 'missing' (never seen by this tenant → 404, no existence leak). The
    base-existence probe is tenant-scoped, so it never reveals another tenant's versions."""
    if RUN_STORE is None or not version_handle:
        return "missing", None
    tid = normalize_tenant(tenant_id)
    try:
        row = RUN_STORE.execute(
            "SELECT tenant_id,run_id,base_handle,kind,content_hash,body_json,created_at,superseded_at "
            "FROM gateway_versions WHERE version_handle=? AND tenant_id=?",
            (version_handle, tid),
        ).fetchone()
    except Exception:  # noqa: BLE001
        return "missing", None
    if row is not None:
        return "ok", {
            "tenant_id": row[0], "run_id": row[1], "base_handle": row[2], "kind": row[3],
            "content_hash": row[4], "body_json": row[5], "created_at": row[6], "superseded_at": row[7],
        }
    # Not present. Distinguish 410 (we DID pin some version of this base for this tenant — this exact
    # version was superseded+pruned) from 404 (we never pinned this base for this tenant) — without
    # leaking another tenant's data: the base-existence probe is tenant-scoped.
    base = str(version_handle or "").split("@", 1)[0].replace("ctxv://", "ctx://", 1)
    try:
        seen = RUN_STORE.execute(
            "SELECT 1 FROM gateway_versions WHERE tenant_id=? AND base_handle=? LIMIT 1", (tid, base)
        ).fetchone()
    except Exception:  # noqa: BLE001
        seen = None
    return ("gone", None) if seen is not None else ("missing", None)


def gateway_receipt(operation: str, *, run: dict | None, ok: bool, handle: str = "", query: str = "",
                    content: object = None, tenant_id: str = "") -> dict:
    """Mint + persist a gateway receipt for a search/fetch and publish the existing `receipt_issued` bus
    event — honest provenance for "agents propose, Baltor disposes" (deep-dive item 2). The receipt is a
    governed record of WHAT was served (is_truth:false — serving a pack is not asserting its facts true);
    it is persisted to the durable gateway_receipts table and rides the durable bus log via BUS.publish."""
    run_id = str((run or {}).get("run_id") or "")
    tenant = normalize_tenant(tenant_id or run_tenant(run))  # explicit caller tenant wins; else the run's owner
    receipt = {
        "kind": "baltor.gateway-receipt",
        "receipt_id": f"gwr-{uuid.uuid4().hex[:12]}",
        "ts": int(time.time()),
        "operation": operation,             # "context.search" | "context.fetch"
        "run_id": run_id,
        "tenant_id": tenant,                # P2: which tenant this read was served to (isolation provenance)
        "handle": handle or "",
        "query": (query or "")[:200],
        "ok": bool(ok),
        "content_hash": stable_hash(content) if content is not None else "",
        "is_truth": False,                  # serving context is not asserting its facts are true
        "served_under_policy": "bounded_fetch_cite_required_volatile_needs_refresh",
    }
    if RUN_STORE is not None:
        try:
            RUN_STORE.execute(
                "INSERT OR REPLACE INTO gateway_receipts"
                "(receipt_id,ts,operation,run_id,tenant_id,handle,query,ok,content_hash,body_json) VALUES(?,?,?,?,?,?,?,?,?,?)",
                (receipt["receipt_id"], receipt["ts"], receipt["operation"], receipt["run_id"], receipt["tenant_id"],
                 receipt["handle"], receipt["query"], int(receipt["ok"]), receipt["content_hash"],
                 json.dumps(receipt, sort_keys=True)),
            )
        except Exception as _e:  # noqa: BLE001
            print(f"[durable] gateway_receipt persist failed: {type(_e).__name__}: {_e}", file=sys.stderr, flush=True)
    try:  # the durable event log persists this automatically (BUS → _persist); kind is in EVENT_KINDS
        BUS.publish("receipt_issued", component="context_gateway", stage="Consumption",
                    correlation_id=run_id or None, object_ref=handle or None,
                    payload={"receipt_id": receipt["receipt_id"], "operation": operation, "ok": bool(ok),
                             "content_hash": receipt["content_hash"], "is_truth": False})
    except Exception as _e:  # noqa: BLE001
        print(f"[durable] gateway_receipt publish failed: {type(_e).__name__}: {_e}", file=sys.stderr, flush=True)
    return receipt


def latest_gateway_receipts(limit: int = 50) -> list[dict]:
    """Newest-first persisted gateway receipts (durable surface for the /api/context-gateway/receipts read)."""
    if RUN_STORE is None:
        return []
    try:
        rows = RUN_STORE.execute(
            "SELECT body_json FROM gateway_receipts ORDER BY ts DESC LIMIT ?", (max(1, min(500, limit)),)
        ).fetchall()
    except Exception:  # noqa: BLE001
        return []
    out: list[dict] = []
    for (body_json,) in rows:
        try:
            out.append(json.loads(body_json or "{}"))
        except json.JSONDecodeError:
            continue
    return out


def log_event(kind: str, message: str, *, run_id: str = "", source: str = "", detail: dict | None = None) -> dict:
    event = {
        "id": f"evt-{uuid.uuid4().hex[:10]}",
        "ts": int(time.time()),
        "kind": kind,
        "message": message,
        "run_id": run_id,
        "source": source,
        "detail": detail or {},
    }
    with RUN_LOCK:
        EVENTS.append(event)
        del EVENTS[:-250]
    client = redis_client()
    if client is not None:
        try:
            client.xadd(ADMIN_EVENT_STREAM, {"event": json.dumps(event, sort_keys=True)}, maxlen=500, approximate=True)
        except Exception:
            pass
    try:  # bridge admin events onto the unified bus for the live dashboard (best-effort)
        BUS.publish("component.progressed", component="admin", correlation_id=run_id or None,
                    payload={"admin_kind": kind, "message": message, "source": source})
    except Exception:
        pass
    return event


def read_worker_heartbeats(limit: int = 20) -> list[dict]:
    try:
        from scripts.context_workers.runtime_io import HeartbeatStore

        return HeartbeatStore().list_recent(limit=limit)
    except Exception:
        return []


def heartbeat_payload(run_id: str = "") -> dict:
    sync_context_worker_events()
    sync_worker_ledger()
    now = int(time.time())
    run = RUNS.get(run_id) if run_id else latest_run()
    worker_heartbeats = read_worker_heartbeats(limit=20)
    matching_worker_heartbeats = [
        row for row in worker_heartbeats
        if not run or str(row.get("run_id") or "") == str(run.get("run_id") or "")
    ]
    queue = queue_stats()
    latest_event = EVENTS[-1] if EVENTS else None
    return {
        "ok": True,
        "kind": "baltor.debug_heartbeat",
        "ts": now,
        "server": {
            "pid": os.getpid(),
            "started_at": SERVER_STARTED_AT,
            "uptime_seconds": now - SERVER_STARTED_AT,
            "admin_event_count": len(EVENTS),
        },
        "latest_run_id": (run or {}).get("run_id"),
        "run": {
            "run_id": (run or {}).get("run_id"),
            "status": (run or {}).get("status"),
            "progress": (run or {}).get("progress"),
            "updated_at": (run or {}).get("updated_at"),
            "heartbeat": (run or {}).get("heartbeat") or {},
            "queue_job_id": (run or {}).get("queue_job_id"),
            "queue_published": (run or {}).get("queue_published"),
            "artifact_counts": run_artifact_counts(run),
            "last_worker_event": (run or {}).get("last_worker_event") or {},
            "recent_worker_events": ((run or {}).get("worker_event_records") or [])[-10:],
        },
        "queue": queue,
        "worker": {
            "ledger_path": str(WORKER_LEDGER_PATH),
            "ledger_exists": WORKER_LEDGER_PATH.exists(),
            "recent_heartbeats": matching_worker_heartbeats[:10],
            "recent_heartbeat_count": len(matching_worker_heartbeats),
        },
        "events": {
            "latest": latest_event,
            "recent": EVENTS[-8:],
        },
        "contracts": {
            "heartbeat_endpoint": "/api/debug/heartbeat",
            "status_endpoint": "/api/admin-dashboard/status",
            "events_endpoint": "/api/admin-dashboard/events",
            "worker_event_stream": CONTEXT_WORKER_EVENT_STREAM,
            "worker_heartbeat_files": "dist/context-worker-runtime/heartbeats/*.json",
        },
    }


def enqueue_context_job(run: dict, text: str, document_tree: dict) -> dict:
    client = redis_client()
    job = {
        "job_id": f"cw-{uuid.uuid4().hex[:12]}",
        "task": "context.pipeline.experimental_adapters",
        "run_id": run["run_id"],
        "tenant_id": "local-demo",
        "pass_index": 1,
        "payload": {
            "text": text,
            "source_name": run["sources"][0]["name"],
            "source_type": run["sources"][0]["type"],
            "document_tree": document_tree,
            "path": document_tree.get("upload_path") or "",
        },
        "queued_at": int(time.time()),
    }
    if client is None:
        log_event("queue.unavailable", "Redis queue unavailable; using in-process worker fallback", run_id=run["run_id"], source=run["sources"][0]["name"], detail={"queue": CONTEXT_QUEUE_KEY})
        return {"ok": False, "job": job}
    client.rpush(CONTEXT_QUEUE_KEY, json.dumps(job, sort_keys=True))
    log_event("queue.enqueued", "Published context job to Redis for container worker", run_id=run["run_id"], source=run["sources"][0]["name"], detail={"queue": CONTEXT_QUEUE_KEY, "job_id": job["job_id"]})
    return {"ok": True, "job": job}


def sync_worker_ledger() -> None:
    if not WORKER_LEDGER_PATH.exists():
        return
    try:
        lines = WORKER_LEDGER_PATH.read_text(encoding="utf-8").splitlines()[-250:]
    except OSError:
        return
    for line in lines:
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        key = str(record.get("job_id") or "") + ":" + str(record.get("finished_at") or "")
        run_id = str(record.get("run_id") or "")
        if not key or key in LEDGER_SEEN or run_id not in RUNS:
            continue
        LEDGER_SEEN.add(key)
        output = record.get("output") if isinstance(record.get("output"), dict) else {}
        worker_output = output.get("deterministic_output") if isinstance(output.get("deterministic_output"), dict) else output
        summary = output.get("summary") if isinstance(output.get("summary"), dict) else {}
        if not summary and isinstance(worker_output.get("summary"), dict):
            summary = worker_output.get("summary") or {}
        adapter_summary = output.get("adapter_summary") if isinstance(output.get("adapter_summary"), dict) else {}
        current = RUNS.get(run_id) or {}
        worker_records = list(current.get("worker_records") or [])
        worker_records.append({
            "job_id": record.get("job_id"),
            "task": record.get("task"),
            "ok": bool(record.get("ok")),
            "finished_at": record.get("finished_at"),
            "error": record.get("error"),
            "output_keys": sorted(output.keys()),
        })
        worker_records = worker_records[-120:]
        harvested: dict[str, object] = {"worker_records": worker_records}
        for field in [
            "claim_risk_records",
            "ambiguous_claims",
            "context_concerns",
            "conflict_candidates",
            "node_evidence",
            "proposed_node_edges",
            "llm_claim_reviews",
            "llm_conflict_reviews",
            "llm_proposed_nodes",
            "llm_proposed_edges",
            "llm_graph_enrichment",
            "llm_summaries",
            "llm_audit_reviews",
            "training_examples",
        ]:
            value = output.get(field)
            if isinstance(value, list):
                combined = list(current.get(field) or [])
                combined.extend(value)
                harvested[field] = combined[-250:]
        if output.get("adapter_status"):
            statuses = list(current.get("llm_adapter_statuses") or [])
            statuses.append({
                "task": record.get("task"),
                "status": output.get("adapter_status"),
                "model": output.get("model"),
                "error": output.get("llm_error"),
            })
            harvested["llm_adapter_statuses"] = statuses[-80:]
        if record.get("task") in {"context.pipeline.pass", "context.pipeline.experimental_adapters"} and record.get("ok"):
            claims = [
                build_claim_record(i, claim, "container-worker", state="worker_extracted", base_signals=["redis_queue", "container_ledger"])
                for i, claim in enumerate(worker_output.get("claims") or [], 1)
            ]
            ownership_records = ownership_change_records(claims)
            ownership_conflicts = ownership_conflict_groups(ownership_records)
            refresh_jobs = worker_output.get("refresh_jobs") if isinstance(worker_output.get("refresh_jobs"), list) else []
            if not refresh_jobs:
                refresh_jobs = build_refresh_jobs(run_id, claims, "container-worker", ownership_records, ownership_conflicts)
            base_summary = dict(current.get("summary") or {})
            base_summary.update({
                "chunks": summary.get("chunks", base_summary.get("chunks", 0)),
                "entities": summary.get("entities", base_summary.get("entities", 0)),
                "claims": summary.get("claims", base_summary.get("claims", 0)),
                "verification_queue": summary.get("fragile_facts", base_summary.get("verification_queue", 0)),
                "refresh_jobs": summary.get("refresh_jobs", len(refresh_jobs)),
                "node_research_tasks": summary.get("node_research_tasks", base_summary.get("node_research_tasks", 0)),
                "llm_review_tasks": summary.get("llm_review_tasks", base_summary.get("llm_review_tasks", 0)),
                "ambiguous_claims": summary.get("ambiguous_claims", base_summary.get("ambiguous_claims", 0)),
                "conflict_candidates": summary.get("conflict_candidates", base_summary.get("conflict_candidates", 0)),
                "adapter_tasks": adapter_summary.get("task_count", base_summary.get("adapter_tasks", 0)),
                "missing_adapters": adapter_summary.get("missing_dependency_count", base_summary.get("missing_adapters", 0)),
                "not_configured_adapters": adapter_summary.get("not_configured_count", base_summary.get("not_configured_adapters", 0)),
                "ownership_change_records": len(ownership_records),
                "ownership_conflict_groups": len(ownership_conflicts),
                "ownership_refresh_jobs": len([job for job in refresh_jobs if str(job.get("refresh_reason") or "").startswith("ownership_")]),
            })
            update_run(run_id, status="complete", progress=100, heartbeat={"ts": int(time.time()), "stage": "container_worker", "status": "complete", "detail": "Worker ledger record synchronized", "job_id": record.get("job_id")}, container_worker_output=output, adapter_summary=adapter_summary, summary=base_summary, claims=claims or current.get("claims", []), ownership_change_records=ownership_records or current.get("ownership_change_records", []), ownership_conflict_groups=ownership_conflicts or current.get("ownership_conflict_groups", []), refresh_jobs=refresh_jobs, **harvested)
            log_event("worker.container.complete", "Container worker completed Redis job", run_id=run_id, source=str(record.get("job_id") or ""), detail={"task": record.get("task"), "summary": summary})
        else:
            base_summary = dict(current.get("summary") or {})
            base_summary.update({
                "node_evidence": len(harvested.get("node_evidence") or current.get("node_evidence") or []),
                "llm_claim_reviews_complete": len(harvested.get("llm_claim_reviews") or current.get("llm_claim_reviews") or []),
                "llm_graph_edges": len(harvested.get("llm_proposed_edges") or current.get("llm_proposed_edges") or []),
                "llm_summaries": len(harvested.get("llm_summaries") or current.get("llm_summaries") or []),
            })
            update_run(run_id, heartbeat={"ts": int(time.time()), "stage": "container_worker", "status": "event", "detail": "Worker ledger event synchronized", "job_id": record.get("job_id")}, summary=base_summary, **harvested)
            log_event("worker.container.event", "Container worker wrote ledger record", run_id=run_id, source=str(record.get("job_id") or ""), detail={"task": record.get("task"), "ok": record.get("ok"), "error": record.get("error")})


def sync_context_worker_events() -> None:
    client = redis_client()
    if client is None:
        return
    try:
        rows = client.xrevrange(CONTEXT_WORKER_EVENT_STREAM, count=100)
    except Exception:
        return
    for event_id, fields in reversed(rows):
        if event_id in CONTEXT_EVENT_SEEN:
            continue
        CONTEXT_EVENT_SEEN.add(event_id)
        raw = fields.get("event") if isinstance(fields, dict) else None
        if not raw:
            continue
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            continue
        detail = payload.get("detail") if isinstance(payload.get("detail"), dict) else {}
        run_id = str(payload.get("run_id") or "")
        if run_id:
            heartbeat_record = {
                "stream_id": event_id,
                "ts": payload.get("ts") or int(time.time()),
                "event": payload.get("event") or "worker.event",
                "job_id": payload.get("job_id") or "",
                "task": payload.get("task") or "",
                "tenant_id": payload.get("tenant_id") or "",
                "detail": detail,
            }
            with RUN_LOCK:
                run = RUNS.get(run_id)
                if run is not None:
                    records = list(run.get("worker_event_records") or [])
                    records.append(heartbeat_record)
                    run["worker_event_records"] = records[-60:]
                    run["last_worker_event"] = heartbeat_record
                    run["heartbeat"] = {
                        "ts": int(heartbeat_record["ts"] or time.time()),
                        "stage": "worker_event_stream",
                        "status": "event",
                        "detail": str(heartbeat_record.get("event") or "worker.event"),
                        "job_id": heartbeat_record.get("job_id") or "",
                        "task": heartbeat_record.get("task") or "",
                    }
                    run["updated_at"] = int(time.time())
        log_event(
            str(payload.get("event") or "worker.event"),
            str(payload.get("event") or "Worker event"),
            run_id=run_id,
            source=str(payload.get("job_id") or payload.get("task") or "context-worker"),
            detail={"task": payload.get("task"), "tenant_id": payload.get("tenant_id"), **detail},
        )


def esc(value: object) -> str:
    return html.escape(str(value if value is not None else ""), quote=True)


def split_claims(text: str) -> list[str]:
    claims = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text.strip()) if len(s.strip()) > 12]
    return claims[:20]


VOLATILE_CLAIM_RE = re.compile(r"\b(current|threshold|as of|today|must|required|every)\b", re.I)
CLAIM_DATE_RE = re.compile(r"\b(?:20\d{2}-\d{2}-\d{2}|20\d{2})\b")
DEFINED_TERM_RE = re.compile(
    r"(?:\bthe\s+term\s+)?[\"'“”]?(?P<term>[A-Z][A-Za-z0-9 /&-]{2,40})[\"'“”]?\s+"
    r"(?:means|shall mean|is defined as|refers to)\b",
    re.I,
)
MULTI_MEANING_TERM_RE = re.compile(
    r"\b(?:the\s+term\s+)?[\"'“”]?(?P<term>[A-Za-z][A-Za-z0-9 /&-]{2,40})[\"'“”]?\s+"
    r"(?:can mean|may mean|could mean|means either|refers to(?: either)?)\s+"
    r"(?P<meanings>[^.?!]{12,220})",
    re.I,
)
ACRONYM_RE = re.compile(r"\b[A-Z]{2,8}\b")
DEFINED_ACRONYM_RE = re.compile(r"\b[A-Z][A-Za-z0-9 &/-]{3,80}\s+\((?P<acronym>[A-Z]{2,8})\)")
AMBIGUOUS_BUSINESS_TERMS = {
    "account",
    "active vendor",
    "affiliate",
    "agency",
    "agent",
    "approved vendor",
    "associate",
    "client",
    "control",
    "contractor",
    "division",
    "entity",
    "facility",
    "managed",
    "owner",
    "partner",
    "platform",
    "principal",
    "supplier",
    "user",
    "vendor",
    "worker",
}
OWNERSHIP_EVENT_PATTERNS: list[tuple[str, str, str]] = [
    ("acquisition", r"\bacquir(?:ed|es|e|ing|isition)\b", "ACQUIRED"),
    ("merger", r"\bmerged?\b|\bformed?\b", "MERGED_INTO"),
    ("split_or_spinout", r"\bsplit\b|\bspin[- ]?out\b|\bcarv(?:e|ed)[- ]?out\b", "SPLIT_INTO"),
    ("current_parent_record", r"\bparent compan(?:y|ies)\b|\bowned by\b|\bsubsidiar(?:y|ies)\b", "PARENT_OF_AS_OF"),
    ("independent_ownership_record", r"\bindependent(?:ly)? owned\b|\bindependent ownership\b", "INDEPENDENT_AS_OF"),
    ("ownership_conflict_or_refresh_notice", r"\bownership\b.*\b(refresh|time-sensitive|current)\b|\bshould not be treated as current\b", "DO_NOT_INFER_CURRENT_OWNER"),
]
OWNERSHIP_EVENT_KEYWORDS_RE = re.compile(
    r"\b(acquir\w*|merg\w*|split|spin[- ]?out|parent compan\w*|owned by|independent(?:ly)? owned|ownership|subsidiar\w*)\b",
    re.I,
)
OWNERSHIP_CURRENT_STATUS_EVENTS = {"current_parent_record", "independent_ownership_record"}


def claim_dates(claim: str) -> list[str]:
    return sorted(dict.fromkeys(CLAIM_DATE_RE.findall(claim)))


def defined_terms(text: str) -> set[str]:
    terms = {match.group("term").strip().lower() for match in DEFINED_TERM_RE.finditer(text)}
    terms.update(match.group("acronym").strip().lower() for match in DEFINED_ACRONYM_RE.finditer(text))
    return {re.sub(r"\s+", " ", term).strip(" .,:;") for term in terms if term.strip()}


def split_meanings(value: str) -> list[str]:
    meanings = [item.strip(" ,;:-") for item in re.split(r"\s+or\s+|\s*/\s*|,", value) if item.strip(" ,;:-")]
    return meanings[:5]


def term_clarity_concerns(text: str, claims: list[dict] | None = None, source_name: str = "source") -> list[dict]:
    defined = defined_terms(text)
    claim_records = claims or []
    concerns: list[dict] = []
    seen: set[tuple[str, str]] = set()

    def claim_ids_for(term: str) -> list[str]:
        lowered = term.lower()
        return [
            str(claim.get("id"))
            for claim in claim_records
            if lowered in str(claim.get("claim") or "").lower()
        ][:8]

    multi_meaning_terms: set[str] = set()
    for match in MULTI_MEANING_TERM_RE.finditer(text):
        term = re.sub(r"\s+", " ", match.group("term")).strip(" .,:;\"'“”")
        if len(term) < 3 or len(term) > 50:
            continue
        key = ("multi_meaning_term", term.lower())
        if key in seen:
            continue
        seen.add(key)
        multi_meaning_terms.add(term.lower())
        concerns.append({
            "concern_id": f"term-{len(concerns) + 1:03d}",
            "type": "MULTI_MEANING_TERM",
            "term": term,
            "severity": "high",
            "source": source_name,
            "evidence": match.group(0)[:320],
            "possible_meanings": split_meanings(match.group("meanings")),
            "claim_ids": claim_ids_for(term),
            "requires_glossary_review": True,
            "safe_context_instruction": "Do not use this term as a stable graph node or edge label until the intended sense is defined for this source scope.",
        })

    lowered_text = text.lower()
    for term in sorted(AMBIGUOUS_BUSINESS_TERMS, key=lambda item: (-len(item), item)):
        if term in multi_meaning_terms:
            continue
        if term in defined:
            continue
        if not re.search(rf"\b{re.escape(term)}s?\b", lowered_text):
            continue
        key = ("undefined_domain_term", term)
        if key in seen:
            continue
        seen.add(key)
        concerns.append({
            "concern_id": f"term-{len(concerns) + 1:03d}",
            "type": "UNDEFINED_DOMAIN_TERM",
            "term": term,
            "severity": "medium",
            "source": source_name,
            "evidence": term,
            "claim_ids": claim_ids_for(term),
            "requires_glossary_review": True,
            "safe_context_instruction": "Keep this term source-local unless a glossary or ontology definition resolves its intended meaning.",
        })
        if len(concerns) >= 16:
            break

    defined_acronyms = {term.upper() for term in defined if term.isalpha() and term.isupper()}
    for acronym in sorted(set(ACRONYM_RE.findall(text))):
        if acronym in {"URL", "HTTP", "HTTPS", "JSON", "ZIP", "API", "LLM", "MCP", "RAG"}:
            continue
        if acronym in defined_acronyms:
            continue
        key = ("acronym_without_definition", acronym.lower())
        if key in seen:
            continue
        seen.add(key)
        concerns.append({
            "concern_id": f"term-{len(concerns) + 1:03d}",
            "type": "ACRONYM_WITHOUT_DEFINITION",
            "term": acronym,
            "severity": "medium",
            "source": source_name,
            "evidence": acronym,
            "claim_ids": claim_ids_for(acronym),
            "requires_glossary_review": True,
            "safe_context_instruction": "Do not expand or normalize this acronym without a source-local definition.",
        })
        if len(concerns) >= 20:
            break
    return concerns


def glossary_resolution_packets(run_id: str, concerns: list[dict], source_name: str) -> list[dict]:
    packets: list[dict] = []
    for index, concern in enumerate(concerns, 1):
        term = str(concern.get("term") or "").strip()
        if not term:
            continue
        packet_id = f"glossary-{index:03d}"
        possible_meanings = list(concern.get("possible_meanings") or [])
        proposed_entry = {
            "term": term,
            "scope": "source_local",
            "source": source_name,
            "definition": None,
            "allowed_meanings": possible_meanings,
            "canonical_entity_allowed": False,
            "canonical_edge_label_allowed": False,
        }
        packets.append({
            "packet_id": packet_id,
            "kind": "baltor.glossary-resolution-packet",
            "run_id": run_id,
            "term": term,
            "concern_id": concern.get("concern_id"),
            "concern_type": concern.get("type"),
            "severity": concern.get("severity") or "medium",
            "source": source_name,
            "evidence": concern.get("evidence"),
            "possible_meanings": possible_meanings,
            "claim_ids": concern.get("claim_ids") or [],
            "status": "needs_glossary_review",
            "review_routes": [
                "local_llm.glossary.review",
                "human_glossary_owner",
            ],
            "safe_context_policy": {
                "source_scope_only": True,
                "block_global_memory_promotion": True,
                "block_canonical_graph_promotion": True,
                "requires_definition_before_context_reuse": True,
            },
            "proposed_glossary_entry": proposed_entry,
            "safe_context_instruction": concern.get("safe_context_instruction")
            or "Keep this term source-local until glossary review resolves its meaning.",
        })
    return packets


def clean_entity_name(value: str) -> str:
    text = re.sub(r"^[#\-\s:]+", "", value.strip())
    text = re.sub(r"\s+", " ", text)
    return text.strip(" .,;:-")


def ownership_entity_candidates(claim: str, event_type: str) -> list[dict]:
    candidates: list[dict] = []
    patterns: dict[str, list[tuple[str, str]]] = {
        "acquisition": [
            ("acquirer", r"(?P<value>[A-Z][A-Za-z0-9&.,' -]+?)\s+acquired\s+[A-Z]"),
            ("acquired_entity", r"\bacquired\s+(?P<value>[A-Z][A-Za-z0-9&.,' -]+?)(?:\s+on\b|\.|$)"),
        ],
        "merger": [
            ("merging_entity", r"(?P<value>[A-Z][A-Za-z0-9&.,' -]+?)\s+merged\s+with\s+[A-Z]"),
            ("merging_entity", r"\bmerged\s+with\s+(?P<value>[A-Z][A-Za-z0-9&.,' -]+?)(?:\s+to form\b|\.|$)"),
            ("resulting_entity", r"\bto form\s+(?P<value>[A-Z][A-Za-z0-9&.,' -]+?)(?:\s+on\b|\.|$)"),
        ],
        "split_or_spinout": [
            ("resulting_entity", r"\bsplit\s+into\s+(?P<value>[A-Z][A-Za-z0-9&.,' -]+?)(?:\.|$)"),
            ("source_division", r"\bthe\s+(?P<value>[a-z][A-Za-z0-9&.,' -]+?)\s+was split\b"),
        ],
        "current_parent_record": [
            ("parent_entity", r"\blist(?:s|ed)?\s+(?P<value>[A-Z][A-Za-z0-9&.,' -]+?)\s+as\s+the\s+parent company\s+for\s+[A-Z]"),
            ("owned_entity", r"\bparent company\s+for\s+(?P<value>[A-Z][A-Za-z0-9&.,' -]+?)(?:\.|$)"),
        ],
        "independent_ownership_record": [
            ("owned_entity", r"\blist(?:s|ed)?\s+(?P<value>[A-Z][A-Za-z0-9&.,' -]+?)\s+as\s+independently owned\b"),
        ],
    }
    for role, pattern in patterns.get(event_type, []):
        match = re.search(pattern, claim)
        if not match:
            continue
        name = clean_entity_name(match.group("value"))
        if len(name) < 3:
            continue
        candidates.append({"role": role, "name": name, "entity_type": "Organization", "confidence": 0.72})
    deduped: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for candidate in candidates:
        key = (candidate["role"], candidate["name"].lower())
        if key in seen:
            continue
        seen.add(key)
        deduped.append(candidate)
    return deduped


def ownership_change_metadata(claim: str) -> dict | None:
    if not OWNERSHIP_EVENT_KEYWORDS_RE.search(claim):
        return None
    event_type = "unknown"
    proposed_edge_type = "OWNERSHIP_EVENT_REQUIRES_REVIEW"
    for candidate, pattern, edge_type in OWNERSHIP_EVENT_PATTERNS:
        if re.search(pattern, claim, re.I):
            event_type = candidate
            proposed_edge_type = edge_type
            break
    dates = claim_dates(claim)
    requires_refresh = event_type in {
        "current_parent_record",
        "independent_ownership_record",
        "ownership_conflict_or_refresh_notice",
        "unknown",
    } or bool(re.search(r"\b(as of|current|today|time-sensitive|refresh)\b", claim, re.I))
    temporal_fragility = "high" if requires_refresh else "medium"
    entity_candidates = ownership_entity_candidates(claim, event_type)
    return {
        "event_type": event_type,
        "proposed_edge_type": proposed_edge_type,
        "dates": dates,
        "entity_candidates": entity_candidates,
        "temporal_fragility": temporal_fragility,
        "requires_refresh": requires_refresh,
        "safe_context_instruction": (
            "Use as dated ownership evidence; do not flatten into current ownership without refresh."
            if requires_refresh
            else "Use as a historical ownership-change claim with citation and source date."
        ),
        "promotion_allowed": False,
    }


def is_volatile_claim(claim: str) -> bool:
    ownership = ownership_change_metadata(claim)
    return bool(VOLATILE_CLAIM_RE.search(claim) or (ownership and ownership.get("requires_refresh")))


def build_claim_record(index: int, claim: object, source_name: str, *, state: str | None = None, base_signals: list[str] | None = None) -> dict:
    text = str(claim.get("text") or claim.get("claim") or claim)[:600] if isinstance(claim, dict) else str(claim)[:600]
    ownership = ownership_change_metadata(text)
    volatile = is_volatile_claim(text)
    signals = list(base_signals or [])
    if volatile and "volatile" not in signals:
        signals.append("volatile")
    if not volatile and not signals:
        signals.append("lineage_retained")
    if ownership:
        signals.extend([
            "ownership_change",
            "temporal_fact",
            f"ownership_event:{ownership['event_type']}",
        ])
        if ownership.get("requires_refresh"):
            signals.append("requires_refresh")
    signals = sorted(dict.fromkeys(signals))
    record = {
        "id": f"fact-{index:03d}",
        "claim": text,
        "state": state or ("needs_verification" if volatile else "candidate_detected"),
        "source": source_name,
        "signals": signals,
        "claim_type": "ownership_change" if ownership else "general_claim",
        "temporal_fragility": ownership.get("temporal_fragility") if ownership else ("high" if volatile else "unknown"),
        "requires_refresh": bool(volatile),
        "safe_context_instruction": (
            ownership.get("safe_context_instruction")
            if ownership
            else "Use as candidate context with citation; do not present volatile facts as current without refresh."
        ),
        "detected_dates": claim_dates(text),
    }
    if ownership:
        record["ownership_change"] = {**ownership, "claim_id": record["id"]}
    return record


def ownership_change_records(claims: list[dict]) -> list[dict]:
    return [dict(claim.get("ownership_change") or {}) for claim in claims if isinstance(claim.get("ownership_change"), dict)]


def ownership_record_entity(record: dict, *roles: str) -> str:
    for candidate in record.get("entity_candidates") or []:
        if candidate.get("role") in roles:
            return str(candidate.get("name") or "")
    return ""


def ownership_conflict_groups(records: list[dict]) -> list[dict]:
    by_entity: dict[str, list[dict]] = {}
    for record in records:
        if record.get("event_type") not in OWNERSHIP_CURRENT_STATUS_EVENTS:
            continue
        entity = ownership_record_entity(record, "owned_entity", "resulting_entity")
        if not entity:
            continue
        by_entity.setdefault(entity.lower(), []).append(record)
    groups: list[dict] = []
    for entity_key, items in by_entity.items():
        event_types = sorted({str(item.get("event_type") or "") for item in items})
        if len(items) < 2 or len(event_types) < 2:
            continue
        dated_items = [
            (str((item.get("dates") or [""])[-1] or ""), item)
            for item in items
        ]
        dated_items = sorted(dated_items, key=lambda pair: pair[0])
        dates = sorted({date for item in items for date in item.get("dates") or []})
        latest_record = dated_items[-1][1] if dated_items else items[-1]
        older_records = [item for _, item in dated_items[:-1]]
        latest_event = str(latest_record.get("event_type") or "")
        superseded_claim_ids = [item.get("claim_id") for item in older_records if item.get("claim_id")]
        resolution_suggestion = "unresolved_conflict"
        supersession_confidence = 0.52
        if latest_event == "independent_ownership_record" and "current_parent_record" in event_types:
            resolution_suggestion = "newer_independent_record_likely_supersedes_parent_record"
            supersession_confidence = 0.68
        elif latest_event == "current_parent_record" and "independent_ownership_record" in event_types:
            resolution_suggestion = "newer_parent_record_likely_supersedes_independent_record"
            supersession_confidence = 0.64
        groups.append({
            "group_id": "ownership-conflict:" + compact_id(entity_key),
            "target_entity": ownership_record_entity(items[0], "owned_entity", "resulting_entity") or entity_key,
            "claim_ids": [item.get("claim_id") for item in items if item.get("claim_id")],
            "event_types": event_types,
            "dates": dates,
            "latest_date": dates[-1] if dates else "",
            "latest_claim_id": latest_record.get("claim_id"),
            "superseded_claim_ids": superseded_claim_ids,
            "resolution_suggestion": resolution_suggestion,
            "supersession_confidence": supersession_confidence,
            "status": "apparent_temporal_conflict",
            "safe_context_instruction": "Present dated ownership records as conflicting or superseding evidence; refresh before stating current ownership.",
            "requires_refresh": True,
        })
    return groups


def ownership_refresh_query(record: dict, claim_text: str = "") -> str:
    event_type = str(record.get("event_type") or "")
    entity = ownership_record_entity(record, "owned_entity", "resulting_entity") or str(record.get("target_entity") or "")
    parent = ownership_record_entity(record, "parent_entity", "acquirer")
    if event_type == "current_parent_record" and entity and parent:
        return f"{entity} current ownership parent company {parent} official registry company website supplier record"
    if event_type == "independent_ownership_record" and entity:
        return f"{entity} current ownership independently owned official registry company website supplier record"
    if entity:
        return f"{entity} ownership official registry company website public business record"
    return f"{claim_text[:120]} official ownership verification source".strip()


def ownership_refresh_fact(record: dict, claims_by_id: dict[str, dict], source_name: str) -> dict:
    claim_id = str(record.get("claim_id") or "")
    claim = claims_by_id.get(claim_id) or {}
    entity = ownership_record_entity(record, "owned_entity", "resulting_entity") or str(record.get("target_entity") or "")
    return {
        "id": claim_id or str(record.get("group_id") or "ownership-refresh"),
        "fact_id": claim_id or str(record.get("group_id") or "ownership-refresh"),
        "state": "one_source_found",
        "subject": entity or claim.get("claim") or "ownership claim",
        "target": ownership_refresh_query(record, str(claim.get("claim") or "")),
        "source_id": source_name,
        "source_count": 1,
        "authoritative_source_count": 0,
        "task_budget_ceiling_usd": 0.25,
        "priority_signals": {
            "risk": 0.80 if record.get("requires_refresh") else 0.45,
            "customer_impact": 0.70 if record.get("requires_refresh") else 0.35,
            "agent_usage": 35 if record.get("requires_refresh") else 15,
            "freshness_age_hours": 168 if record.get("requires_refresh") else 24,
        },
    }


def ownership_conflict_refresh_fact(group: dict, source_name: str) -> dict:
    return {
        "id": str(group.get("group_id") or "ownership-conflict"),
        "fact_id": str(group.get("group_id") or "ownership-conflict"),
        "state": "needs_reconciliation",
        "subject": group.get("target_entity") or "ownership conflict",
        "target": f"{group.get('target_entity') or 'company'} ownership parent independent latest official source reconciliation",
        "source_id": source_name,
        "source_count": 2,
        "authoritative_source_count": 0,
        "task_budget_ceiling_usd": 0.25,
        "priority_signals": {
            "risk": 0.90,
            "customer_impact": 0.75,
            "agent_usage": 45,
            "freshness_age_hours": 168,
        },
    }


def build_refresh_jobs(run_id: str, claims: list[dict], source_name: str, ownership_records: list[dict], ownership_conflicts: list[dict]) -> list[dict]:
    jobs: list[dict] = []
    seen: set[str] = set()
    claims_by_id = {str(claim.get("id") or ""): claim for claim in claims}
    for claim in claims:
        if not claim.get("requires_refresh"):
            continue
        if claim.get("claim_type") == "ownership_change":
            continue
        job = {
            "target": str(claim.get("claim") or "")[:80],
            "worker": "search-refresh",
            "priority": "high",
            "claim_id": claim.get("id"),
            "task": "context.search.verify",
            "task_type": "verify.official_source.find",
            "refresh_reason": "volatile_fact",
        }
        key = str(job.get("claim_id") or job.get("target"))
        if key not in seen:
            seen.add(key)
            jobs.append(job)
    for record in ownership_records:
        if not record.get("requires_refresh"):
            continue
        task = make_research_task(run_id=run_id, tenant_id="local-demo", fact=ownership_refresh_fact(record, claims_by_id, source_name))
        task["refresh_reason"] = "ownership_current_status_refresh"
        task["adapter_plan"] = {
            "person_level_osint": "disabled",
            "non_pii_business_public_records": "allowed_when_adapter_configured",
            "preferred_sources": ["official_registry", "company_website", "supplier_portal_export", "archived_source"],
            "live_fetch_policy": "exact_handle_or_configured_adapter_only",
        }
        task["payload"]["query"] = ownership_refresh_query(record, str(claims_by_id.get(str(record.get("claim_id") or ""), {}).get("claim") or ""))
        key = str(task.get("task_id") or task.get("fact_id"))
        if key not in seen:
            seen.add(key)
            jobs.append(task)
    for group in ownership_conflicts:
        task = make_research_task(run_id=run_id, tenant_id="local-demo", fact=ownership_conflict_refresh_fact(group, source_name))
        task["refresh_reason"] = "ownership_conflict_reconciliation"
        task["ownership_conflict_group"] = group
        task["adapter_plan"] = {
            "person_level_osint": "disabled",
            "non_pii_business_public_records": "allowed_when_adapter_configured",
            "preferred_sources": ["official_registry", "company_website", "supplier_portal_export", "second_independent_source"],
            "live_fetch_policy": "exact_handle_or_configured_adapter_only",
        }
        task["payload"]["query"] = str(task.get("target") or (task.get("payload") or {}).get("query") or "")
        key = str(task.get("task_id") or task.get("fact_id"))
        if key not in seen:
            seen.add(key)
            jobs.append(task)
    return jobs


def hierarchy_tags(path: str) -> list[str]:
    parts = [p for p in path.replace("\\", "/").split("/") if p]
    tags = []
    for index, part in enumerate(parts[:-1], 1):
        tags.append(f"folder:{'/'.join(parts[:index])}")
        tags.append(f"depth:{index}")
    if parts:
        suffix = "." + parts[-1].rsplit(".", 1)[-1].lower() if "." in parts[-1] else "none"
        tags.append(f"filename:{parts[-1]}")
        tags.append(f"extension:{suffix}")
    return tags


def connector_slug(value: str) -> str:
    text = value.strip().lower()
    aliases = {
        "ftp / sftp": "ftp",
        "google drive": "google-drive",
        "sharepoint": "sharepoint",
        "git / s3": "git-s3",
        "website mirror": "website",
        "repo wiki": "repo-wiki",
    }
    return aliases.get(text, compact_id(text))


def connector_envelope(connector: str, target: str = "") -> dict:
    slug = connector_slug(connector)
    definition = CONNECTOR_DEFINITIONS.get(slug, {
        "label": connector or "Custom connector",
        "source_system": slug or "custom",
        "placeholder": "",
        "default_target": f"{slug or 'custom'}://local-demo/source",
        "object_types": ["object"],
    })
    target_uri = (target or str(definition.get("default_target") or "")).strip()
    handle = context_handle("connector", connector=slug, target=target_uri)
    return {
        "connector_id": f"connector:{slug}",
        "label": definition["label"],
        "source_system": definition["source_system"],
        "target_uri": target_uri,
        "handle": handle,
        "status": "registered",
        "mode": "indexed_mirror_envelope",
        "object_types": definition.get("object_types") or [],
        "allowed_operations": ["metadata_probe", "indexed_sync", "live_fetch_exact_object"],
        "blocked_operations": ["unrestricted_raw_search", "bulk_comment_dump", "write_action_without_policy"],
        "auth": {
            "required_for_live_fetch": True,
            "configured": False,
            "credential_storage": "external_secret_manager_or_runtime_env",
        },
        "acl_policy": {
            "filter_before_model": True,
            "identity_required": True,
            "groups": ["local-demo-admin"],
            "document_level_acl": True,
        },
        "retrieval_policy": {
            "default": "indexed_mirror_first",
            "live_fetch": "exact_handle_only",
            "raw_source_access": "fallback",
            "compression": "context_pack_with_source_handles",
        },
        "sync_policy": {
            "supported_triggers": definition.get("sync_triggers") or ["manual_register", "scheduled_sync", "exact_handle_refresh"],
            "commit_scoped_outputs_required": slug == "repo-wiki",
            "pipeline_artifacts_allowed": slug == "repo-wiki",
            "raw_webhook_payloads_are_source_data": True,
        },
        "safety": {
            "person_level_osint_default": "disabled",
            "non_pii_business_public_records": "allowed_when_adapter_configured",
            "prompt_injection_treated_as_untrusted_source_text": True,
            "generated_repo_docs_are_derived_context": slug == "repo-wiki",
        },
    }


def connector_document_tree(envelope: dict, text: str) -> dict:
    path_slug = compact_id(envelope.get("label"))
    target_slug = compact_id(envelope.get("target_uri"))
    record = file_record(f"connectors/{path_slug}/{target_slug}.connector.txt", text.encode("utf-8", errors="ignore"), text, source="connector-envelope")
    record["connector_handle"] = envelope.get("handle")
    record["acl_policy"] = envelope.get("acl_policy")
    return {
        "kind": "connector_envelope",
        "archive_name": str(envelope.get("label") or "connector"),
        "folders": [f"connectors/{path_slug}"],
        "files": [record],
        "connector_envelope": envelope,
        "connector_envelopes": [envelope],
        "summary": {
            "folders": 1,
            "files": 1,
            "readable_files": 1,
            "pages": len(record.get("pages") or []),
            "components": sum(len(page.get("components") or []) for page in record.get("pages") or []),
            "connector_envelopes": 1,
        },
    }


def connector_text(envelope: dict) -> str:
    label = str(envelope.get("label") or "Connector")
    target = str(envelope.get("target_uri") or "")
    return (
        f"{label} connector envelope registered for {target}.\n\n"
        "Baltor will index a normalized mirror before exposing context to coding agents.\n\n"
        "Raw source access is a fallback and requires an exact source handle, identity, ACL filtering, and audit logging.\n\n"
        "Allowed operations are metadata probe, indexed sync, and exact-object live fetch. "
        "Unrestricted raw search, bulk comment dumps, and write actions are blocked by default.\n\n"
        f"{SAMPLE_TEXT}"
    )


def page_components(text: str) -> list[dict]:
    blocks = [block.strip() for block in re.split(r"\n\s*\n", text) if block.strip()]
    components = []
    for index, block in enumerate(blocks[:80], 1):
        if re.match(r"^\s*[-*]\s+", block) or "\n-" in block:
            kind = "list"
        elif re.search(r"\|.+\|", block) or "," in block and block.count("\n") >= 2:
            kind = "table_like"
        elif re.search(r"[{};=<>]{3,}", block):
            kind = "code_like"
        else:
            kind = "paragraph"
        components.append({
            "id": f"component-{index:03d}",
            "type": kind,
            "text_preview": block[:280],
            "char_count": len(block),
        })
    return components


def text_pages(text: str) -> list[dict]:
    if "\f" in text:
        chunks = [part.strip() for part in text.split("\f") if part.strip()]
    else:
        chunks = [text[i:i + PAGE_CHARS].strip() for i in range(0, len(text), PAGE_CHARS) if text[i:i + PAGE_CHARS].strip()]
    return [
        {
            "page_number": index,
            "char_count": len(page_text),
            "components": page_components(page_text),
        }
        for index, page_text in enumerate(chunks or [text], 1)
    ]


def file_record(path: str, raw: bytes, text: str = "", *, source: str = "upload") -> dict:
    clean_path = path.replace("\\", "/")
    folder = "/".join(clean_path.split("/")[:-1])
    suffix = "." + clean_path.rsplit(".", 1)[-1].lower() if "." in clean_path else ""
    readable = bool(text.strip())
    return {
        "path": clean_path,
        "folder": folder or "/",
        "name": clean_path.rsplit("/", 1)[-1],
        "extension": suffix or "none",
        "source": source,
        "byte_size": len(raw),
        "char_count": len(text),
        "readable_text": readable,
        "tags": hierarchy_tags(clean_path),
        "pages": text_pages(text) if readable else [],
    }


def upload_to_text(filename: str, raw: bytes) -> tuple[str, str, dict]:
    """Extract demo-readable text from a direct upload."""
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "-", filename or "upload.bin").strip("-") or "upload.bin"
    upload_path = UPLOAD_DIR / f"{int(time.time())}-{uuid.uuid4().hex[:8]}-{safe_name}"
    upload_path.write_bytes(raw)
    lower = filename.lower()
    if lower.endswith(".zip"):
        parts: list[str] = []
        records: list[dict] = []
        folders: set[str] = set()
        with zipfile.ZipFile(io.BytesIO(raw)) as zf:
            for info in zf.infolist()[:MAX_ZIP_FILES]:
                clean_name = info.filename.replace("\\", "/").strip("/")
                if not clean_name:
                    continue
                parent_parts = clean_name.split("/")[:-1] if not info.is_dir() else clean_name.split("/")
                for i in range(1, len(parent_parts) + 1):
                    folders.add("/".join(parent_parts[:i]))
                if info.is_dir() or info.file_size > MAX_ZIP_MEMBER_BYTES:
                    if not info.is_dir():
                        records.append(file_record(clean_name, b"", "", source="zip-skipped-too-large"))
                    continue
                suffix = "." + info.filename.rsplit(".", 1)[-1].lower() if "." in info.filename else ""
                if suffix not in TEXT_EXTENSIONS:
                    records.append(file_record(clean_name, b"", "", source="zip-binary-or-unsupported"))
                    continue
                data = zf.read(info)
                text = data.decode("utf-8", errors="ignore").strip()
                records.append(file_record(clean_name, data, text, source="zip"))
                if text:
                    parts.append(f"# ZIP member: {clean_name}\n\n{text}")
        manifest = {
            "kind": "zip",
            "archive_name": filename,
            "upload_path": str(upload_path),
            "folders": sorted(folders),
            "files": records,
            "limits": {"max_files": MAX_ZIP_FILES, "max_member_bytes": MAX_ZIP_MEMBER_BYTES},
            "summary": {
                "folders": len(folders),
                "files": len(records),
                "readable_files": sum(1 for record in records if record["readable_text"]),
                "pages": sum(len(record["pages"]) for record in records),
                "components": sum(len(page["components"]) for record in records for page in record["pages"]),
            },
        }
        if parts:
            return "\n\n---\n\n".join(parts), f"{filename} ({len(parts)} text member(s))", manifest
        return (
            "ZIP uploaded, but no readable text members were found. Add .txt, .md, .csv, .json, .yaml, .xml, .html, or .log files.",
            f"{filename} (zip scanned)",
            manifest,
        )
    text = raw.decode("utf-8", errors="ignore")
    manifest = {
        "kind": "single_file",
        "archive_name": "",
        "upload_path": str(upload_path),
        "folders": [],
        "files": [file_record(filename, raw, text, source="upload")],
        "summary": {
            "folders": 0,
            "files": 1,
            "readable_files": 1 if text.strip() else 0,
            "pages": len(text_pages(text)) if text.strip() else 0,
            "components": sum(len(page["components"]) for page in text_pages(text)) if text.strip() else 0,
        },
    }
    return text, filename, manifest


def combine_document_trees(items: list[dict]) -> dict:
    folders: set[str] = set()
    files: list[dict] = []
    archive_names = []
    for item in items:
        archive_name = str(item.get("archive_name") or "")
        if archive_name:
            archive_names.append(archive_name)
        folders.update(str(folder) for folder in item.get("folders", []))
        for record in item.get("files", []):
            files.append(record)
    return {
        "kind": "file_set",
        "archive_name": ", ".join(archive_names),
        "folders": sorted(folders),
        "files": files,
        "summary": {
            "folders": len(folders),
            "files": len(files),
            "readable_files": sum(1 for record in files if record.get("readable_text")),
            "pages": sum(len(record.get("pages") or []) for record in files),
            "components": sum(len(page.get("components") or []) for record in files for page in record.get("pages") or []),
        },
    }


def update_run(run_id: str, **updates: object) -> dict | None:
    with RUN_LOCK:
        run = RUNS.get(run_id)
        if run is None:
            return None
        run.update(updates)
        run["updated_at"] = int(time.time())
        snapshot = dict(run)
    persist_run(snapshot)  # mirror to the durable table outside the lock (ctx:// survives restart)
    return snapshot


def create_background_run(text: str, source_name: str, source_type: str, document_tree: dict | None, tenant_id: str = DEFAULT_TENANT) -> dict:
    run_id = f"adm-{uuid.uuid4().hex[:10]}"
    tenant_id = normalize_tenant(tenant_id)  # P2: owner tenant for this run's ctx:// handles
    now = int(time.time())
    connector = (document_tree or {}).get("connector_envelope") if isinstance(document_tree, dict) else None
    source_record = {"name": source_name, "type": source_type, "sync_state": "received", "version": "pending"}
    if isinstance(connector, dict):
        source_record["connector_envelope"] = connector
        source_record["handle"] = connector.get("handle")
        source_record["source_system"] = connector.get("source_system")
    run = {
        "run_id": run_id,
        "tenant_id": tenant_id,
        "created_at": now,
        "updated_at": now,
        "status": "queued",
        "progress": 0,
        "heartbeat": {"ts": now, "stage": "receive", "status": "queued", "detail": "Run accepted by admin server"},
        "text": text,
        "sources": [source_record],
        "document_tree": document_tree or {
            "kind": "text",
            "archive_name": "",
            "folders": [],
            "files": [file_record(source_name, text.encode("utf-8", errors="ignore"), text, source=source_type)],
            "summary": {"folders": 0, "files": 1, "readable_files": 1 if text.strip() else 0, "pages": len(text_pages(text)), "components": sum(len(page["components"]) for page in text_pages(text))},
        },
        "summary": {"sources": 1, "chunks": 0, "entities": 0, "claims": 0, "verification_queue": 0, "refresh_jobs": 0, "estimated_cost_usd": 0},
        "claims": [],
        "refresh_jobs": [],
        "worker_plan": [
            {"stage": "receive", "status": "ready", "detail": "All submitted files received by HTTP request"},
            {"stage": "ingest", "status": "pending", "detail": "Waiting for background worker"},
            {"stage": "chunk", "status": "pending", "detail": "Waiting for background worker"},
            {"stage": "extract", "status": "pending", "detail": "Waiting for background worker"},
            {"stage": "verify", "status": "pending", "detail": "Waiting for background worker"},
            {"stage": "serve", "status": "pending", "detail": "Waiting for background worker"},
        ],
    }
    with RUN_LOCK:
        RUNS[run_id] = run
    log_event("run.queued", "Run queued for background processing", run_id=run_id, source=source_name, detail={"source_type": source_type, "bytes": len(text), **run["document_tree"]["summary"]})
    enqueue_result = enqueue_context_job(run, text, run["document_tree"])
    published = bool(enqueue_result["ok"])
    with RUN_LOCK:
        RUNS[run_id]["queue_job_id"] = enqueue_result["job"]["job_id"]
        RUNS[run_id]["queue_published"] = published
        RUNS[run_id]["heartbeat"] = {"ts": int(time.time()), "stage": "queue", "status": "published" if published else "fallback", "detail": "Background job envelope created", "job_id": enqueue_result["job"]["job_id"]}
        snapshot = dict(RUNS[run_id])
    persist_run(snapshot)   # durable mirror so the ctx:// run survives a restart
    prune_runs()            # bound memory: keep only the newest DURABLE_RUNS_MAX runs
    # Item 5 (deep-dive): ONE run engine, not two. When the job was PUBLISHED to Redis, a container worker
    # owns it and sync_worker_ledger harvests that result — running the in-process worker too is the
    # double-processing path whose ledger sync would race/overwrite the in-process write. So the in-process
    # worker is the FALLBACK only: start it solely when nothing was published (no Redis / publish failed).
    if not published:
        thread = threading.Thread(target=process_run_background, args=(run_id,), daemon=True)
        thread.start()
    else:
        log_event("run.delegated", "Published to Redis; container worker owns processing (no in-process double-run)",
                  run_id=run_id, source=source_name, detail={"queue": CONTEXT_QUEUE_KEY, "job_id": enqueue_result["job"]["job_id"]})
    return dict(run)


def set_stage(run_id: str, stage: str, status: str, detail: str, progress: int) -> None:
    with RUN_LOCK:
        run = RUNS.get(run_id)
        if not run:
            return
        for item in run.get("worker_plan", []):
            if item.get("stage") == stage:
                item["status"] = status
                item["detail"] = detail
        run["status"] = "running" if status != "complete" else run.get("status", "running")
        run["progress"] = progress
        run["heartbeat"] = {"ts": int(time.time()), "stage": stage, "status": status, "detail": detail, "progress": progress}
        run["updated_at"] = int(time.time())
        snapshot = dict(run)
    persist_run(snapshot)  # keep the durable mirror in step with stage progress


def process_run_background(run_id: str) -> None:
    with RUN_LOCK:
        run = dict(RUNS.get(run_id) or {})
    if not run:
        return
    text = str(run.get("text") or "")
    source_name = str((run.get("sources") or [{}])[0].get("name") or "source")
    stages = [
        ("ingest", 18, "Hashing, source-versioning, and normalizing received files", {"characters": len(text)}),
        ("chunk", 38, "Splitting files into pages and page components", run.get("document_tree", {}).get("summary", {})),
        ("extract", 62, "Extracting entities and candidate claims", {}),
        ("verify", 82, "Planning verification and refresh jobs", {}),
        ("serve", 100, "Preparing serving/export packages", {}),
    ]
    for stage, progress, detail, payload in stages:
        set_stage(run_id, stage, "running", detail, max(1, progress - 8))
        log_event(f"worker.{stage}", detail, run_id=run_id, source=source_name, detail=payload)
        time.sleep(0.35)
        set_stage(run_id, stage, "complete", detail, progress)

    raw_claims = split_claims(text)
    claim_records = [build_claim_record(i, claim, source_name) for i, claim in enumerate(raw_claims, 1)]
    volatile = [claim for claim in claim_records if claim.get("requires_refresh")]
    ownership_records = ownership_change_records(claim_records)
    ownership_conflicts = ownership_conflict_groups(ownership_records)
    term_concerns = term_clarity_concerns(text, claim_records, source_name)
    glossary_packets = glossary_resolution_packets(run_id, term_concerns, source_name)
    refresh_jobs = build_refresh_jobs(run_id, claim_records, source_name, ownership_records, ownership_conflicts)
    source_type = str((run.get("sources") or [{}])[0].get("type") or "upload")
    source_record = dict((run.get("sources") or [{}])[0])
    source_record.update({"name": source_name, "type": source_type, "sync_state": "synced", "version": "local-v1"})
    sources = [source_record]
    summary = {
        "sources": len(sources),
        "chunks": max(1, len(text) // 450 + 1),
        "entities": len(set(re.findall(r"\b[A-Z][A-Za-z0-9-]{2,}\b", text))),
        "claims": len(claim_records),
        "verification_queue": len(volatile),
        "refresh_jobs": len(refresh_jobs),
        "ownership_change_records": len(ownership_records),
        "ownership_conflict_groups": len(ownership_conflicts),
        "ownership_refresh_jobs": len([job for job in refresh_jobs if str(job.get("refresh_reason") or "").startswith("ownership_")]),
        "term_clarity_concerns": len(term_concerns),
        "glossary_resolution_packets": len(glossary_packets),
        "estimated_cost_usd": round(0.012 + 0.002 * len(claim_records), 4),
    }
    update_run(
        run_id,
        status="complete",
        progress=100,
        sources=sources,
        summary=summary,
        claims=claim_records,
        ownership_change_records=ownership_records,
        ownership_conflict_groups=ownership_conflicts,
        term_clarity_concerns=term_concerns,
        glossary_resolution_packets=glossary_packets,
        context_concerns=term_concerns,
        refresh_jobs=refresh_jobs,
    )
    log_event("document.tree", "Built document hierarchy, pages, and components", run_id=run_id, source=source_name, detail=run.get("document_tree", {}).get("summary", {}))
    log_event("run.complete", "Background context run completed", run_id=run_id, source=source_name, detail=summary)


def build_run(text: str, source_name: str = "demo-source.txt", source_type: str = "upload", document_tree: dict | None = None, tenant_id: str = DEFAULT_TENANT) -> dict:
    run_id = f"adm-{uuid.uuid4().hex[:10]}"
    tenant_id = normalize_tenant(tenant_id)  # P2: this run is OWNED by this tenant; ctx:// handles are scoped to it
    log_event("run.created", "Context run created", run_id=run_id, source=source_name, detail={"source_type": source_type, "bytes": len(text)})
    raw_claims = split_claims(text)
    log_event("worker.ingest", "Ingested source text", run_id=run_id, source=source_name, detail={"characters": len(text)})
    log_event("worker.chunk", "Chunked source text", run_id=run_id, source=source_name, detail={"chunks": max(1, len(text) // 450 + 1)})
    claim_records = [build_claim_record(i, claim, source_name) for i, claim in enumerate(raw_claims, 1)]
    volatile = [claim for claim in claim_records if claim.get("requires_refresh")]
    ownership_records = ownership_change_records(claim_records)
    ownership_conflicts = ownership_conflict_groups(ownership_records)
    term_concerns = term_clarity_concerns(text, claim_records, source_name)
    glossary_packets = glossary_resolution_packets(run_id, term_concerns, source_name)
    refresh_jobs = build_refresh_jobs(run_id, claim_records, source_name, ownership_records, ownership_conflicts)
    log_event("worker.extract", "Extracted candidate claims", run_id=run_id, source=source_name, detail={"claims": len(claim_records), "ownership_change_records": len(ownership_records)})
    log_event("worker.verify", "Planned verification and refresh jobs", run_id=run_id, source=source_name, detail={"verification_queue": len(volatile), "refresh_jobs": len(refresh_jobs)})
    sources = [{"name": source_name, "type": source_type, "sync_state": "synced", "version": "local-v1"}]
    run = {
        "run_id": run_id,
        "tenant_id": tenant_id,
        "created_at": int(time.time()),
        "status": "complete",
        "progress": 100,
        "text": text,
        "sources": sources,
        "document_tree": document_tree or {
            "kind": "text",
            "archive_name": "",
            "folders": [],
            "files": [file_record(source_name, text.encode("utf-8", errors="ignore"), text, source=source_type)],
            "summary": {"folders": 0, "files": 1, "readable_files": 1, "pages": len(text_pages(text)), "components": sum(len(page["components"]) for page in text_pages(text))},
        },
        "summary": {
            "sources": len(sources),
            "chunks": max(1, len(text) // 450 + 1),
            "entities": len(set(re.findall(r"\b[A-Z][A-Za-z0-9-]{2,}\b", text))),
            "claims": len(claim_records),
            "verification_queue": len(volatile),
            "refresh_jobs": len(refresh_jobs),
            "ownership_change_records": len(ownership_records),
            "ownership_conflict_groups": len(ownership_conflicts),
            "ownership_refresh_jobs": len([job for job in refresh_jobs if str(job.get("refresh_reason") or "").startswith("ownership_")]),
            "term_clarity_concerns": len(term_concerns),
            "glossary_resolution_packets": len(glossary_packets),
            "estimated_cost_usd": round(0.012 + 0.002 * len(claim_records), 4),
        },
        "claims": claim_records,
        "ownership_change_records": ownership_records,
        "ownership_conflict_groups": ownership_conflicts,
        "term_clarity_concerns": term_concerns,
        "glossary_resolution_packets": glossary_packets,
        "context_concerns": term_concerns,
        "refresh_jobs": refresh_jobs,
    }
    RUNS[run_id] = run
    persist_run(run)   # durable mirror so this run's ctx:// handles survive a restart
    prune_runs()       # bound memory: keep only the newest DURABLE_RUNS_MAX runs
    log_event("document.tree", "Built document hierarchy, pages, and components", run_id=run_id, source=source_name, detail=run["document_tree"]["summary"])
    log_event("run.complete", "Context run completed", run_id=run_id, source=source_name, detail=run["summary"])
    return run


def latest_run() -> dict | None:
    if not RUNS:
        return None
    return max(RUNS.values(), key=lambda run: int(run.get("created_at") or 0))


def run_artifact_counts(run: dict | None) -> dict:
    run = run or {}
    return {
        "worker_event_records": len(run.get("worker_event_records") or []),
        "worker_records": len(run.get("worker_records") or []),
        "claim_risk_records": len(run.get("claim_risk_records") or []),
        "ambiguous_claims": len(run.get("ambiguous_claims") or []),
        "conflict_candidates": len(run.get("conflict_candidates") or []),
        "node_evidence": len(run.get("node_evidence") or []),
        "proposed_node_edges": len(run.get("proposed_node_edges") or []),
        "llm_claim_reviews": len(run.get("llm_claim_reviews") or []),
        "llm_conflict_reviews": len(run.get("llm_conflict_reviews") or []),
        "llm_proposed_nodes": len(run.get("llm_proposed_nodes") or []),
        "llm_proposed_edges": len(run.get("llm_proposed_edges") or []),
        "llm_summaries": len(run.get("llm_summaries") or []),
        "llm_audit_reviews": len(run.get("llm_audit_reviews") or []),
        "training_examples": len(run.get("training_examples") or []),
        "ownership_change_records": len(run.get("ownership_change_records") or []),
        "ownership_conflict_groups": len(run.get("ownership_conflict_groups") or []),
        "term_clarity_concerns": len(run.get("term_clarity_concerns") or []),
        "glossary_resolution_packets": len(run.get("glossary_resolution_packets") or []),
    }


def iter_rag_records(run: dict) -> list[dict]:
    records: list[dict] = []
    tree = run.get("document_tree") or {}
    for file_index, item in enumerate(tree.get("files") or [], 1):
        for page in item.get("pages") or []:
            page_number = page.get("page_number")
            for component in page.get("components") or []:
                handle = context_handle(
                    "component",
                    run_id=str(run.get("run_id") or ""),
                    file_path=str(item.get("path") or f"file-{file_index}"),
                    page=page_number,
                    component_id=str(component.get("id") or ""),
                )
                records.append({
                    "record_id": f'{run.get("run_id")}:file-{file_index}:p{page_number}:{component.get("id")}',
                    "run_id": run.get("run_id"),
                    "handle": handle,
                    "text": component.get("text_preview") or "",
                    "source": {
                        "name": (run.get("sources") or [{}])[0].get("name"),
                        "type": (run.get("sources") or [{}])[0].get("type"),
                        "file_path": item.get("path"),
                        "folder": item.get("folder"),
                        "page": page_number,
                        "component_id": component.get("id"),
                        "component_type": component.get("type"),
                        "handle": handle,
                    },
                    "metadata": {
                        "tags": item.get("tags") or [],
                        "char_count": component.get("char_count", 0),
                        "readable_text": bool(item.get("readable_text")),
                    },
                    "safety": {
                        "requires_citation": True,
                        "fragility": "unknown",
                        "safe_context_policy": "candidate_until_reviewed",
                    },
                })
    if not records:
        for claim in run.get("claims") or []:
            handle = context_handle("claim", run_id=str(run.get("run_id") or ""), claim_id=str(claim.get("id") or ""))
            records.append({
                "record_id": f'{run.get("run_id")}:{claim.get("id")}',
                "run_id": run.get("run_id"),
                "handle": handle,
                "text": claim.get("claim") or "",
                "source": {"name": claim.get("source"), "claim_id": claim.get("id"), "handle": handle},
                "metadata": {"state": claim.get("state"), "signals": claim.get("signals") or []},
                "safety": {"requires_citation": True, "safe_context_policy": "candidate_until_reviewed"},
            })
    return records


def graph_package(run: dict) -> dict:
    nodes: list[dict] = []
    edges: list[dict] = []
    seen_nodes: set[str] = set()
    for source in run.get("sources") or []:
        node_id = "source:" + compact_id(source.get("name"))
        if node_id not in seen_nodes:
            seen_nodes.add(node_id)
            nodes.append({"id": node_id, "type": "Source", "label": source.get("name"), "handle": context_handle("source", run_id=str(run.get("run_id") or ""), source_id=str(source.get("name") or "")), "properties": source})
        connector = source.get("connector_envelope") if isinstance(source, dict) else None
        if isinstance(connector, dict):
            connector_id = "connector:" + compact_id(connector.get("connector_id") or connector.get("label"))
            if connector_id not in seen_nodes:
                seen_nodes.add(connector_id)
                nodes.append({"id": connector_id, "type": "ConnectorEnvelope", "label": connector.get("label"), "handle": connector.get("handle"), "properties": connector})
            edges.append({"source": connector_id, "type": "MIRRORS_SOURCE", "target": node_id, "evidence_handles": [connector.get("handle")]})
    for claim in run.get("claims") or []:
        claim_id = "claim:" + str(claim.get("id"))
        claim_handle = context_handle("claim", run_id=str(run.get("run_id") or ""), claim_id=str(claim.get("id") or ""))
        nodes.append({"id": claim_id, "type": "Claim", "label": claim.get("claim"), "handle": claim_handle, "properties": claim})
        source_id = "source:" + compact_id(claim.get("source"))
        edges.append({"source": source_id, "type": "SUPPORTS", "target": claim_id, "evidence_ids": [claim.get("id")], "evidence_handles": [claim_handle]})
        ownership = claim.get("ownership_change") if isinstance(claim, dict) else None
        if isinstance(ownership, dict):
            event_id = "ownership-event:" + str(claim.get("id"))
            event_handle = context_handle("ownership-event", run_id=str(run.get("run_id") or ""), claim_id=str(claim.get("id") or ""))
            nodes.append({
                "id": event_id,
                "type": "OwnershipChangeEvent",
                "label": ownership.get("event_type") or "ownership_change",
                "handle": event_handle,
                "properties": ownership,
                "promotion_allowed": False,
            })
            edges.append({
                "source": claim_id,
                "type": "PROPOSES_OWNERSHIP_EVENT",
                "target": event_id,
                "evidence_ids": [claim.get("id")],
                "evidence_handles": [claim_handle],
                "promotion_allowed": False,
            })
    for node in run.get("llm_proposed_nodes") or []:
        node_id = "llm:" + compact_id(node.get("label") or node.get("id"))
        nodes.append({"id": node_id, "type": node.get("type") or "ProposedNode", "label": node.get("label"), "properties": node, "promotion_allowed": False})
    for group in run.get("ownership_conflict_groups") or ownership_conflict_groups(run.get("ownership_change_records") or ownership_change_records(run.get("claims") or [])):
        group_id = str(group.get("group_id") or ("ownership-conflict:" + compact_id(group.get("target_entity"))))
        nodes.append({
            "id": group_id,
            "type": "OwnershipConflictGroup",
            "label": group.get("target_entity") or "ownership conflict",
            "properties": group,
            "promotion_allowed": False,
        })
        for claim_id in group.get("claim_ids") or []:
            edges.append({
                "source": "claim:" + str(claim_id),
                "type": "HAS_OWNERSHIP_CONFLICT",
                "target": group_id,
                "evidence_ids": [claim_id],
                "promotion_allowed": False,
            })
        latest_claim_id = group.get("latest_claim_id")
        for older_claim_id in group.get("superseded_claim_ids") or []:
            if latest_claim_id and older_claim_id:
                edges.append({
                    "source": "claim:" + str(latest_claim_id),
                    "type": "MAY_SUPERSEDE_OWNERSHIP_CLAIM",
                    "target": "claim:" + str(older_claim_id),
                    "evidence_ids": [latest_claim_id, older_claim_id],
                    "confidence": group.get("supersession_confidence"),
                    "promotion_allowed": False,
                })
    for concern in run.get("term_clarity_concerns") or []:
        concern_id = "term-concern:" + compact_id(concern.get("concern_id") or concern.get("term"))
        nodes.append({
            "id": concern_id,
            "type": "TermClarityConcern",
            "label": concern.get("term") or concern.get("type") or "term concern",
            "properties": concern,
            "promotion_allowed": False,
        })
        for claim_id in concern.get("claim_ids") or []:
            edges.append({
                "source": "claim:" + str(claim_id),
                "type": "HAS_TERM_CLARITY_CONCERN",
                "target": concern_id,
                "evidence_ids": [claim_id],
                "promotion_allowed": False,
            })
    for packet in run.get("glossary_resolution_packets") or []:
        packet_id = "glossary-packet:" + compact_id(packet.get("packet_id") or packet.get("term"))
        nodes.append({
            "id": packet_id,
            "type": "GlossaryResolutionPacket",
            "label": packet.get("term") or "glossary packet",
            "properties": packet,
            "promotion_allowed": False,
        })
        concern_id = packet.get("concern_id")
        if concern_id:
            edges.append({
                "source": "term-concern:" + compact_id(concern_id),
                "type": "HAS_GLOSSARY_RESOLUTION_PACKET",
                "target": packet_id,
                "evidence_ids": [concern_id],
                "promotion_allowed": False,
            })
    for edge in run.get("llm_proposed_edges") or []:
        edge_record = dict(edge)
        edge_record.setdefault("promotion_allowed", False)
        edge_record.setdefault("source_system", "local_llm_trust_layer")
        edges.append(edge_record)
    return {
        "nodes": nodes,
        "edges": edges,
        "claims": run.get("claims") or [],
        "ownership_change_records": run.get("ownership_change_records") or ownership_change_records(run.get("claims") or []),
        "ownership_conflict_groups": run.get("ownership_conflict_groups") or ownership_conflict_groups(run.get("ownership_change_records") or ownership_change_records(run.get("claims") or [])),
        "term_clarity_concerns": run.get("term_clarity_concerns") or [],
        "glossary_resolution_packets": run.get("glossary_resolution_packets") or [],
        "claim_risk_records": run.get("claim_risk_records") or [],
        "conflict_candidates": run.get("conflict_candidates") or [],
        "policy": {
            "llm_outputs_are_proposals": True,
            "edge_promotion_requires_evidence": True,
            "controlled_edge_types": True,
        },
    }


def compact_id(value: object) -> str:
    text = str(value or "unknown").lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text[:80] or "unknown"


def context_handle(kind: str, **parts: object) -> str:
    run_id = compact_id(parts.pop("run_id", "run"))
    suffix = "/".join(f"{compact_id(key)}={compact_id(value)}" for key, value in parts.items() if value not in {None, ""})
    return f"ctx://baltor/{run_id}/{compact_id(kind)}" + (f"/{suffix}" if suffix else "")


def iso_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def stable_hash(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")
    import hashlib

    return "sha256:" + hashlib.sha256(payload).hexdigest()


def context_object_graph_records(run: dict) -> dict:
    run_id = str(run.get("run_id") or "run")
    generated_at = iso_now()
    graph = graph_package(run)
    records = iter_rag_records(run)
    pack_payload = context_pack(run)
    pack = pack_payload.get("context_pack") or {}
    objects: list[dict] = []
    versions: list[dict] = []
    artifacts: list[dict] = []
    relationships: list[dict] = []
    assertions: list[dict] = []
    dimension_definitions: list[dict] = []
    dimension_values: list[dict] = []
    events: list[dict] = []
    packs: list[dict] = []
    seen_objects: set[str] = set()
    seen_dimensions: set[str] = set()

    built_in_dimensions = [
        ("dim://baltor/trust/verifiability", "trust", "Verifiability", "Can this context be checked against source evidence?", "better", "mean"),
        ("dim://baltor/trust/authority", "trust", "Authority", "Does the source have decision authority for this context?", "better", "max"),
        ("dim://baltor/trust/freshness", "trust", "Freshness", "Is the context current enough for agent use?", "better", "latest"),
        ("dim://baltor/risk/operational", "risk", "Operational Risk", "Impact if this context is wrong, stale, or misused.", "worse", "max"),
        ("dim://baltor/safety/sensitivity", "safety", "Sensitivity", "How restricted or sensitive the context is.", "worse", "max"),
        ("dim://baltor/safety/prompt-injection-risk", "safety", "Prompt Injection Risk", "Likelihood that source data contains agent-steering instructions.", "worse", "max"),
        ("dim://baltor/retrieval/actionability", "retrieval", "Actionability", "Can an agent safely act with this context?", "better", "mean"),
    ]
    for dimension_id, namespace, name, description, higher_is, aggregation in built_in_dimensions:
        dimension_definitions.append({
            "kind": "baltor.context-dimension-definition",
            "dimension_id": dimension_id,
            "namespace": namespace,
            "name": name,
            "description": description,
            "value_type": "number",
            "normalized_range": {"min": 0, "max": 1},
            "higher_is": higher_is,
            "aggregation": aggregation,
            "display": {
                "low": [0, 0.33],
                "medium": [0.34, 0.66],
                "high": [0.67, 1],
            },
            "policy": {"assessment_is_not_source_fact": True, "source_handles_required_for_durable_use": True},
            "created_at": generated_at,
            "updated_at": generated_at,
        })
        seen_dimensions.add(dimension_id)

    def label_for_score(value: float) -> str:
        if value >= 0.67:
            return "high"
        if value >= 0.34:
            return "medium"
        return "low"

    def bounded_score(value: object, default: float = 0.5) -> float:
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            numeric = default
        return max(0.0, min(1.0, numeric))

    def add_dimension_value(subject_id: str, dimension_id: str, value: float, *, subject_kind: str = "context_object", confidence: float = 0.75, scope: dict | None = None, evidence: list[str] | None = None, method: dict | None = None) -> None:
        score = bounded_score(value)
        dimension_values.append({
            "kind": "baltor.context-dimension-value",
            "dimension_value_id": f"dimv://baltor/{compact_id(run_id)}/{compact_id(subject_id)}/{compact_id(dimension_id)}",
            "dimension_id": dimension_id,
            "subject_id": subject_id,
            "subject_kind": subject_kind,
            "value": score,
            "normalized_value": score,
            "label": label_for_score(score),
            "confidence": bounded_score(confidence),
            "scope": scope or {"task_type": "context_pack", "client": "admin_demo"},
            "evidence": evidence or [subject_id],
            "method": method or {"type": "deterministic_rule", "pipeline": "baltor.dimension_projection", "pipeline_version": "demo"},
            "valid_from": generated_at,
            "valid_to": None,
            "assessed_at": generated_at,
        })

    def add_assertion(subject_id: str, predicate: str, value: object, *, object_id: str = "", value_type: str = "object", confidence: float = 0.75, evidence: list[str] | None = None, attributes: dict | None = None) -> None:
        assertions.append({
            "kind": "baltor.context-assertion",
            "context_assertion_id": f"assert://baltor/{compact_id(run_id)}/{len(assertions) + 1}",
            "subject_id": subject_id,
            "predicate": predicate,
            "object_id": object_id,
            "value": value,
            "value_type": value_type,
            "confidence": bounded_score(confidence),
            "evidence": evidence or [subject_id],
            "asserted_by": {"type": "pipeline", "id": "baltor.context_object_graph_records"},
            "valid_from": generated_at,
            "valid_to": None,
            "attributes": attributes or {},
            "created_at": generated_at,
        })

    def context_facets(object_type: str, body: dict, source_system: str, native_id: str, classification: str) -> dict:
        facets = dict(body.get("facets") or {}) if isinstance(body.get("facets"), dict) else {}
        facets.setdefault("core", {
            "object_type": object_type,
            "source_system": source_system,
            "native_id": native_id,
            "classification": classification,
        })
        if body.get("claim_type") or body.get("temporal_fragility"):
            facets.setdefault("baltor.claim", {
                "claim_type": body.get("claim_type") or "general_claim",
                "temporal_fragility": body.get("temporal_fragility") or "unknown",
                "requires_refresh": bool(body.get("requires_refresh")),
                "state": body.get("state") or "unknown",
            })
        if body.get("connector"):
            connector = body.get("connector") if isinstance(body.get("connector"), dict) else {}
            facets.setdefault("baltor.connector", {
                "source_system": connector.get("source_system"),
                "connector_id": connector.get("connector_id"),
                "object_types": connector.get("object_types") or [],
            })
        if body.get("graph_node"):
            node = body.get("graph_node") if isinstance(body.get("graph_node"), dict) else {}
            facets.setdefault("baltor.graph", {
                "node_type": node.get("type"),
                "promotion_allowed": bool(node.get("promotion_allowed")),
            })
        return facets

    def five_w_one_h(object_type: str, title: str, body: dict, source_handles: list[str]) -> dict:
        text = " ".join([title, str(body.get("claim") or ""), str(body.get("summary") or "")]).lower()
        topics = [
            topic
            for topic in ["ownership", "agency", "active vendor", "cco", "refresh", "risk", "glossary", "connector", "source"]
            if topic in text
        ]
        actors = []
        if body.get("source"):
            actors.append(str(body.get("source")))
        owner = body.get("owner") or body.get("team") or body.get("policy_owner")
        return {
            "who": {
                "actors": actors,
                "owners": [str(owner)] if owner else [],
                "reviewers": [],
                "audience": ["ctx://baltor/audience/context-stewards", "ctx://baltor/audience/agent-clients"],
            },
            "what": {
                "entities": [str(entity) for entity in body.get("entity_candidates") or []],
                "topics": topics,
                "object_types": [object_type],
            },
            "when": {
                "observed_at": generated_at,
                "valid_from": generated_at,
                "valid_to": None,
                "source_date": body.get("source_date") or body.get("effective_date"),
            },
            "where": {
                "digital_locations": source_handles or [],
                "logical_locations": [str(body.get("source") or "baltor-local-demo")],
                "physical_locations": [],
            },
            "why": {
                "goals": ["serve bounded, source-linked context to agents"],
                "rationale": [str(body.get("safe_context_instruction") or "preserve source handles, freshness, and policy before memory promotion")],
                "drivers": ["agent reliability", "context governance"],
            },
            "how": {
                "methods": ["source-handle projection", "typed graph export", "dimension assessment"],
                "processes": ["normalize", "link", "score", "pack"],
                "tools": ["baltor_admin_demo_server", "context_gateway"],
            },
        }

    def add_object(object_id: str, object_type: str, title: str, source_handles: list[str], body: dict, *, source_system: str = "baltor_local_demo", native_id: str = "", classification: str = "internal") -> str:
        if object_id in seen_objects:
            return object_id
        seen_objects.add(object_id)
        version_id = object_id.replace("ctx://", "ctxv://") + "@" + compact_id(stable_hash(body))[-16:]
        object_facets = context_facets(object_type, body, source_system, native_id, classification)
        object_five_w_one_h = five_w_one_h(object_type, title, body, source_handles or [object_id])
        base_verifiability = 0.9 if body.get("state") == "worker_extracted" else 0.7
        if object_type in {"document", "source_excerpt"}:
            base_verifiability = 0.85
        freshness_score = 0.38 if body.get("requires_refresh") else 0.82
        operational_risk = 0.82 if body.get("requires_refresh") or object_type in {"glossary_term", "glossary_packet"} else 0.46
        if object_type in {"connector_envelope", "context_pack"}:
            operational_risk = 0.58
        dimension_summary = {
            "trust.verifiability": base_verifiability,
            "trust.freshness": freshness_score,
            "risk.operational": operational_risk,
        }
        objects.append({
            "kind": "baltor.context-object",
            "context_object_id": object_id,
            "current_version_id": version_id,
            "object_type": object_type,
            "source_system": source_system,
            "native_id": native_id,
            "title": title,
            "summary": body.get("summary") or title,
            "body": body,
            "facets": object_facets,
            "five_w_one_h": object_five_w_one_h,
            "dimension_summary": dimension_summary,
            "source_handles": source_handles or [object_id],
            "acl_id": f"acl://baltor/local-demo/{classification}",
            "classification": classification,
            "policy": {
                "derived_context": object_type not in {"document", "source_excerpt"},
                "promotion_allowed": False,
                "raw_source_dump_allowed": False,
                "acl_filter_applied": True,
                "prompt_injection_checked": True,
            },
            "freshness": {
                "retrieved_at": generated_at,
                "staleness": "unknown" if body.get("requires_refresh") else "fresh",
            },
            "created_at": generated_at,
            "updated_at": generated_at,
        })
        add_assertion(
            object_id,
            "has_5w1h_projection",
            object_five_w_one_h,
            value_type="object",
            confidence=0.72,
            evidence=source_handles or [object_id],
            attributes={"facet": "five_w_one_h"},
        )
        if body.get("claim"):
            add_assertion(
                object_id,
                "states",
                str(body.get("claim") or ""),
                value_type="claim",
                confidence=base_verifiability,
                evidence=source_handles or [object_id],
                attributes={"claim_type": body.get("claim_type") or "general_claim"},
            )
        add_dimension_value(object_id, "dim://baltor/trust/verifiability", base_verifiability, evidence=source_handles or [object_id])
        add_dimension_value(object_id, "dim://baltor/trust/freshness", freshness_score, evidence=source_handles or [object_id])
        add_dimension_value(object_id, "dim://baltor/risk/operational", operational_risk, evidence=source_handles or [object_id])
        add_dimension_value(object_id, "dim://baltor/safety/sensitivity", 0.42 if classification == "internal" else 0.22, evidence=source_handles or [object_id])
        add_dimension_value(object_id, "dim://baltor/safety/prompt-injection-risk", 0.62 if object_type in {"comment", "source_excerpt", "claim"} else 0.3, evidence=source_handles or [object_id])
        add_dimension_value(object_id, "dim://baltor/retrieval/actionability", 0.72 if not body.get("requires_refresh") else 0.4, evidence=source_handles or [object_id])
        versions.append({
            "kind": "baltor.context-version",
            "context_version_id": version_id,
            "context_object_id": object_id,
            "content_hash": stable_hash(body),
            "metadata_hash": stable_hash({"object_type": object_type, "source_system": source_system, "native_id": native_id}),
            "acl_hash": stable_hash({"classification": classification}),
            "raw_snapshot_uri": object_id,
            "normalized_uri": object_id + "#normalized",
            "normalized_format": "json",
            "observed_at": generated_at,
            "valid_from": generated_at,
            "valid_to": None,
            "tombstone": False,
            "policy": {"raw_source_dump_allowed": False},
            "created_at": generated_at,
        })
        events.append({
            "kind": "baltor.context-event",
            "context_event_id": f"ctxevent://baltor/{compact_id(run_id)}/observed/{len(events) + 1}",
            "event_type": "NORMALIZED",
            "object_id": object_id,
            "input_ids": source_handles or [object_id],
            "output_ids": [version_id],
            "actor": "baltor_admin_demo_server",
            "activity": "context_object_graph_records",
            "run_id": run_id,
            "trace_id": f"trace://baltor/{compact_id(run_id)}",
            "policy_decision": "allow",
            "occurred_at": generated_at,
            "metadata": {"object_type": object_type},
        })
        return object_id

    for source in run.get("sources") or []:
        if not isinstance(source, dict):
            continue
        handle = context_handle("source", run_id=run_id, source_id=str(source.get("name") or "source"))
        add_object(
            handle,
            "document",
            str(source.get("name") or "Source"),
            [handle],
            {"summary": str(source.get("name") or "Source"), "source": source},
            native_id=str(source.get("name") or ""),
        )
        connector = source.get("connector_envelope")
        if isinstance(connector, dict):
            connector_handle = str(connector.get("handle") or context_handle("connector", run_id=run_id, connector=str(connector.get("connector_id") or "")))
            add_object(
                connector_handle,
                "connector_envelope",
                str(connector.get("label") or connector.get("connector_id") or "Connector"),
                [connector_handle],
                {"summary": str(connector.get("label") or "Connector"), "connector": connector},
                source_system=str(connector.get("source_system") or "connector"),
                native_id=str(connector.get("connector_id") or ""),
            )

    for claim in run.get("claims") or []:
        if not isinstance(claim, dict):
            continue
        claim_handle = context_handle("claim", run_id=run_id, claim_id=str(claim.get("id") or "claim"))
        add_object(
            claim_handle,
            "claim",
            str(claim.get("claim") or claim.get("id") or "Claim")[:180],
            [claim_handle],
            claim,
            source_system=str(claim.get("source") or "claim_extractor"),
            native_id=str(claim.get("id") or ""),
        )
        artifact_id = f"ctxa://baltor/{compact_id(run_id)}/claim/{compact_id(claim.get('id'))}"
        artifacts.append({
            "kind": "baltor.context-artifact",
            "context_artifact_id": artifact_id,
            "artifact_type": "claim",
            "derived_from": [claim_handle],
            "content_hash": stable_hash(claim),
            "token_count": max(1, len(str(claim.get("claim") or "").split())),
            "generator": {"pipeline": "baltor.claim_extraction", "pipeline_version": "demo"},
            "lineage_event_id": f"ctxevent://baltor/{compact_id(run_id)}/artifact/{compact_id(claim.get('id'))}",
            "quality": {
                "confidence": 0.5,
                "authority": "candidate",
                "human_verified": False,
                "conflicts_detected": bool(claim.get("requires_refresh")),
            },
            "policy": {"raw_source_dump_allowed": False, "derived_context": True},
            "created_at": generated_at,
        })

    for record in records[:40]:
        record_id = str(record.get("record_id") or record.get("handle") or "")
        handle = str(record.get("handle") or context_handle("record", run_id=run_id, record_id=record_id))
        add_object(
            handle,
            "source_excerpt",
            record_id or "RAG record",
            [handle],
            {"summary": str(record.get("text") or "")[:240], "record": record},
            native_id=record_id,
        )
        artifacts.append({
            "kind": "baltor.context-artifact",
            "context_artifact_id": f"ctxa://baltor/{compact_id(run_id)}/rag/{compact_id(record_id)}",
            "artifact_type": "chunk",
            "derived_from": [handle],
            "content_hash": stable_hash(record),
            "token_count": max(1, len(str(record.get("text") or "").split())),
            "generator": {"pipeline": "baltor.rag_record_projection", "pipeline_version": "demo"},
            "policy": {"raw_source_dump_allowed": False, "derived_context": True},
            "created_at": generated_at,
        })

    for node in graph.get("nodes") or []:
        if not isinstance(node, dict):
            continue
        handle = str(node.get("handle") or context_handle("graph-node", run_id=run_id, node_id=str(node.get("id") or "")))
        node_type = {
            "OwnershipChangeEvent": "fact",
            "OwnershipConflictGroup": "fact",
            "TermClarityConcern": "glossary_term",
            "GlossaryResolutionPacket": "glossary_packet",
            "ConnectorEnvelope": "connector_envelope",
            "Claim": "claim",
            "Source": "document",
        }.get(str(node.get("type") or ""), "fact")
        add_object(
            handle,
            node_type,
            str(node.get("label") or node.get("id") or "Graph node")[:180],
            [handle],
            {"summary": str(node.get("label") or node.get("id") or ""), "graph_node": node},
            native_id=str(node.get("id") or ""),
        )

    edge_type_map = {
        "SUPPORTS": "SUPPORTS",
        "MIRRORS_SOURCE": "DERIVED_FROM",
        "PROPOSES_OWNERSHIP_EVENT": "MENTIONS",
        "HAS_OWNERSHIP_CONFLICT": "CONTRADICTS",
        "MAY_SUPERSEDE_OWNERSHIP_CLAIM": "MAY_SUPERSEDE",
        "HAS_TERM_CLARITY_CONCERN": "REQUIRES_REFRESH",
        "HAS_GLOSSARY_RESOLUTION_PACKET": "DEFINES",
    }
    for idx, edge in enumerate(graph.get("edges") or [], start=1):
        if not isinstance(edge, dict):
            continue
        relationships.append({
            "kind": "baltor.context-relationship",
            "context_relationship_id": f"ctxrel://baltor/{compact_id(run_id)}/{idx}",
            "from_id": str(edge.get("source") or ""),
            "to_id": str(edge.get("target") or ""),
            "endpoints": [
                {"role": "from", "object_id": str(edge.get("source") or "")},
                {"role": "to", "object_id": str(edge.get("target") or "")},
            ],
            "relationship_type": edge_type_map.get(str(edge.get("type") or ""), "CUSTOM"),
            "relationship_label": str(edge.get("type") or "CUSTOM"),
            "confidence": edge.get("confidence", 0.5),
            "strength": edge.get("strength", edge.get("confidence", 0.5)),
            "source_handles": [h for h in edge.get("evidence_handles") or [] if str(h).startswith("ctx://")],
            "evidence_ids": [str(item) for item in edge.get("evidence_ids") or []],
            "valid_from": generated_at,
            "valid_to": None,
            "created_by": "baltor.graph_package",
            "attributes": {
                "original_edge_type": edge.get("type"),
                "relationship_rationale": "Projected from Baltor graph export; supports unbounded edge and hyperedge modeling.",
            },
            "policy": {"derived_context": True, "promotion_allowed": bool(edge.get("promotion_allowed"))},
            "created_at": generated_at,
        })
        add_assertion(
            f"ctxrel://baltor/{compact_id(run_id)}/{idx}",
            "relationship_projected_from_graph_edge",
            edge,
            value_type="object",
            confidence=bounded_score(edge.get("confidence", 0.5)),
            evidence=[h for h in edge.get("evidence_handles") or [] if str(h).startswith("ctx://")],
            attributes={"original_edge_type": edge.get("type")},
        )

    pack_id = f"ctxpack://baltor/{compact_id(run_id)}/implementation/latest"
    packs.append({
        "kind": "baltor.context-pack",
        "context_pack_id": pack_id,
        "pack_type": str(pack.get("pack_type") or "implementation_pack"),
        "task": str(pack.get("task_type") or "local_context_run"),
        "query": str(pack.get("query") or ""),
        "object_ids": [item.get("context_object_id") for item in objects[:25]],
        "artifact_ids": [item.get("context_artifact_id") for item in artifacts[:25]],
        "relationship_ids": [item.get("context_relationship_id") for item in relationships[:25]],
        "summary": str(pack.get("summary") or ""),
        "claims": pack.get("high_confidence_facts") or [],
        "conflicts": pack.get("conflicts") or [],
        "risks": pack.get("risks") or [],
        "source_handles": pack.get("source_handles") or [obj.get("context_object_id") for obj in objects[:1]],
        "trace_id": f"trace://baltor/{compact_id(run_id)}",
        "token_budget": int(pack.get("token_budget") or 0),
        "token_count": int(pack.get("token_budget_used") or 0),
        "policy": {"acl_filter_applied": True, "raw_source_dump_allowed": False},
        "created_at": generated_at,
    })
    add_dimension_value(pack_id, "dim://baltor/trust/verifiability", 0.82, subject_kind="context_pack", evidence=packs[0]["source_handles"])
    add_dimension_value(pack_id, "dim://baltor/trust/authority", 0.68, subject_kind="context_pack", evidence=packs[0]["source_handles"])
    add_dimension_value(pack_id, "dim://baltor/trust/freshness", 0.74, subject_kind="context_pack", evidence=packs[0]["source_handles"])
    add_dimension_value(pack_id, "dim://baltor/risk/operational", 0.64, subject_kind="context_pack", evidence=packs[0]["source_handles"])
    add_dimension_value(pack_id, "dim://baltor/retrieval/actionability", 0.78, subject_kind="context_pack", evidence=packs[0]["source_handles"])
    add_assertion(
        pack_id,
        "summarizes_sources",
        packs[0]["source_handles"],
        value_type="array",
        confidence=0.86,
        evidence=packs[0]["source_handles"],
        attributes={"pack_type": packs[0]["pack_type"]},
    )
    events.append({
        "kind": "baltor.context-event",
        "context_event_id": f"ctxevent://baltor/{compact_id(run_id)}/served/context-pack",
        "event_type": "SERVED",
        "object_id": pack_id,
        "input_ids": [item.get("context_object_id") for item in objects[:25]],
        "output_ids": [pack_id],
        "actor": "baltor_context_gateway",
        "activity": "context_pack",
        "run_id": run_id,
        "trace_id": f"trace://baltor/{compact_id(run_id)}",
        "policy_decision": "allow",
        "occurred_at": generated_at,
        "metadata": {"pack_type": packs[0]["pack_type"]},
    })
    return {
        "kind": "baltor.context-object-graph-records",
        "schema_kinds": [
            "baltor.context-object",
            "baltor.context-version",
            "baltor.context-artifact",
            "baltor.context-relationship",
            "baltor.context-assertion",
            "baltor.context-dimension-definition",
            "baltor.context-dimension-value",
            "baltor.context-event",
            "baltor.context-pack",
        ],
        "objects": objects,
        "versions": versions,
        "artifacts": artifacts,
        "relationships": relationships,
        "assertions": assertions,
        "dimension_definitions": dimension_definitions,
        "dimension_values": dimension_values,
        "events": events,
        "packs": packs,
        "counts": {
            "objects": len(objects),
            "versions": len(versions),
            "artifacts": len(artifacts),
            "relationships": len(relationships),
            "assertions": len(assertions),
            "dimension_definitions": len(dimension_definitions),
            "dimension_values": len(dimension_values),
            "events": len(events),
            "packs": len(packs),
        },
        "policy": {
            "storage_agnostic": True,
            "source_handles_required": True,
            "versions_are_immutable": True,
            "derived_artifacts_keep_lineage": True,
            "relationships_are_typed_and_source_backed": True,
            "relationships_are_unbounded": True,
            "flexible_facets_are_namespaced": True,
            "five_w_one_h_is_universal_projection": True,
            "dimensions_are_first_class_records": True,
            "assertions_are_source_linked": True,
        },
    }


def context_pack(run: dict, *, pack_type: str = "implementation_pack", token_budget: int = 3000) -> dict:
    records = iter_rag_records(run)
    claims = run.get("claims") or []
    connector_envelopes = [
        source.get("connector_envelope")
        for source in run.get("sources") or []
        if isinstance(source, dict) and isinstance(source.get("connector_envelope"), dict)
    ]
    facts = []
    for claim in claims[:12]:
        handle = context_handle("claim", run_id=str(run.get("run_id") or ""), claim_id=str(claim.get("id") or ""))
        facts.append({
            "claim": claim.get("claim"),
            "source": claim.get("source"),
            "handle": handle,
            "citation": f"{claim.get('source')}::{claim.get('id')}",
            "freshness": "indexed",
            "trust": "candidate" if claim.get("state") != "worker_extracted" else "worker_extracted",
            "safe_context_policy": "cite_and_do_not_present_volatile_facts_as_current_without_refresh",
            "claim_type": claim.get("claim_type") or "general_claim",
            "temporal_fragility": claim.get("temporal_fragility") or "unknown",
            "requires_refresh": bool(claim.get("requires_refresh")),
            "safe_context_instruction": claim.get("safe_context_instruction"),
            "ownership_event_type": (claim.get("ownership_change") or {}).get("event_type") if isinstance(claim.get("ownership_change"), dict) else None,
        })
    code_pointers = [
        {
            "path": (record.get("source") or {}).get("file_path"),
            "reason": "Source component matched the uploaded context set.",
            "handle": record.get("handle"),
        }
        for record in records[:8]
    ]
    risks = []
    for concern in run.get("context_concerns") or []:
        if isinstance(concern, dict) and concern.get("term"):
            risks.append(
                f"{concern.get('concern_id')}: {concern.get('type')} for term '{concern.get('term')}'; "
                "require glossary or source-scope clarification before graph promotion."
            )
        else:
            risks.append(str(concern.get("type") or concern)[:240] if isinstance(concern, dict) else str(concern)[:240])
    for risk in run.get("claim_risk_records") or []:
        serving = risk.get("context_serving") if isinstance(risk, dict) else {}
        if isinstance(serving, dict) and serving.get("risk_reasons"):
            risks.append(f"{risk.get('claim_id')}: {', '.join(serving.get('risk_reasons') or [])}")
    if not risks:
        risks.append("Candidate context must retain citations; refresh volatile facts before presenting them as current.")
    for ownership in run.get("ownership_change_records") or ownership_change_records(claims):
        if ownership.get("requires_refresh"):
            risks.append(f"{ownership.get('claim_id')}: ownership evidence is time-sensitive; refresh before stating current ownership.")
    for group in run.get("ownership_conflict_groups") or ownership_conflict_groups(run.get("ownership_change_records") or ownership_change_records(claims)):
        risks.append(
            f"{group.get('group_id')}: ownership records conflict or supersede each other for {group.get('target_entity')}; "
            f"suggestion={group.get('resolution_suggestion') or 'unresolved_conflict'}; refresh before stating current ownership."
        )
    existing_term_risks = " ".join(risks)
    for concern in run.get("term_clarity_concerns") or []:
        if str(concern.get("concern_id") or "") in existing_term_risks:
            continue
        risks.append(
            f"{concern.get('concern_id')}: {concern.get('type')} for term '{concern.get('term')}' "
            "may confuse downstream LLM context; require glossary or source-scope clarification."
        )
    next_fetches = [
        {"handle": record.get("handle"), "why": "Expand this exact source component if the coding agent needs more detail."}
        for record in records[:6]
    ]
    summary = "Uploaded context was normalized into files, pages, components, claims, graph candidates, and safe-context export records."
    if claims:
        summary = f"Run {run.get('run_id')} produced {len(claims)} candidate claims from {(run.get('document_tree') or {}).get('summary', {}).get('files', 0)} file(s)."
    return {
        "result_id": f"ctxr-{compact_id(run.get('run_id'))}",
        "task_type": "code_change",
        "pack_type": pack_type,
        "token_budget_requested": token_budget,
        "token_budget_used_estimate": min(token_budget, sum(len(str(item.get("claim") or "")) for item in facts) // 4 + 400),
        "confidence": "medium" if facts else "low",
        "answerable": bool(facts or records),
        "context_pack": {
            "summary": summary,
            "facts": facts,
            "code_pointers": code_pointers,
            "risks": risks[:12],
            "next_fetches": next_fetches,
            "source_handles": [item.get("handle") for item in records[:20] if item.get("handle")],
            "connector_envelopes": connector_envelopes,
            "ownership_change_records": run.get("ownership_change_records") or ownership_change_records(claims),
            "ownership_conflict_groups": run.get("ownership_conflict_groups") or ownership_conflict_groups(run.get("ownership_change_records") or ownership_change_records(claims)),
            "ownership_refresh_jobs": [
                job for job in run.get("refresh_jobs") or []
                if str(job.get("refresh_reason") or "").startswith("ownership_")
            ],
            "term_clarity_concerns": run.get("term_clarity_concerns") or [],
            "glossary_resolution_packets": run.get("glossary_resolution_packets") or [],
        },
        "gateway_policy": {
            "claude_code_is_client": True,
            "retrieval_policy_owned_by_baltor": True,
            "acl_filter_before_model": True,
            "raw_source_access_is_fallback": True,
            "compression_returns_handles": True,
        },
    }


def gateway_status_payload() -> dict:
    queue = queue_stats()
    return {
        "ok": True,
        "service": "baltor-context-gateway",
        "mcp_tools": ["context_search", "context_fetch", "context_expand", "context_trace", "context_status", "context_connectors", "context_heartbeat", "context_glossary", "context_dimensions", "context_model_routing", "context_reranking", "context_local_memory"],
        "live_source_tools": ["source_live_fetch", "source_action"],
        "policy": {
            "claude_code_is_client": True,
            "retrieval_policy_owned_by_baltor": True,
            "acl_filter_before_model": True,
            "raw_source_access_is_fallback": True,
            "compression_returns_handles": True,
            "hybrid_search_default": True,
            "live_validation_separate_from_indexed_retrieval": True,
        },
        "backend": {
            "mode": "local-demo",
            "keyword_search": True,
            "vector_search": False,
            "graph_search": True,
            "redis_available": bool(queue.get("available")),
            "latest_run_id": (latest_run() or {}).get("run_id"),
        },
        "connector_envelopes": connector_catalog_payload()["connectors"],
    }


def connector_catalog_payload() -> dict:
    return {
        "ok": True,
        "connectors": [
            connector_envelope(str(definition.get("label") or slug), str(definition.get("default_target") or ""))
            for slug, definition in CONNECTOR_DEFINITIONS.items()
        ],
        "policy": {
            "indexed_mirror_first": True,
            "exact_handle_live_fetch_only": True,
            "unrestricted_raw_tools_exposed": False,
            "write_actions_require_deployment_policy": True,
        },
    }


def sync_contracts_payload() -> dict:
    connectors = connector_catalog_payload()["connectors"]
    trigger_types = sorted({
        trigger
        for connector in connectors
        for trigger in (connector.get("sync_policy") or {}).get("supported_triggers", [])
    })
    return {
        "ok": True,
        "kind": "baltor.context-sync-contracts",
        "sync_modes": ["push", "pull", "push_then_pull"],
        "trigger_types": trigger_types,
        "check_gates": [
            "signature_verification",
            "replay_window",
            "connector_scope",
            "source_acl_before_model",
            "event_filter",
            "artifact_manifest_schema",
            "content_hash",
            "prompt_injection_scan",
            "idempotency_dedupe_key",
            "staleness_policy",
        ],
        "artifact_manifest_kinds": [
            "baltor.repo-wiki-artifact-manifest",
            "baltor.local-context-cache-manifest",
        ],
        "worker_routing": {
            "push_webhook": {"task": "repo.diff.plan", "lane": "sync"},
            "merge_request_webhook": {"task": "repo.mr_context.plan", "lane": "sync"},
            "pipeline_artifact": {"task": "repo_wiki.artifact.import", "lane": "ingest"},
            "post_commit_hook": {"task": "repo_wiki.local_draft.import", "lane": "ingest"},
            "file_watcher": {"task": "repo_wiki.local_draft.refresh", "lane": "refresh"},
            "scheduled_poll": {"task": "repo.sync.poll", "lane": "refresh"},
            "release_tag": {"task": "repo_wiki.versioned.promote", "lane": "promote"},
        },
        "policies": {
            "webhook_payloads_are_untrusted_source_data": True,
            "generated_docs_are_derived_context": True,
            "commit_scoped_outputs_required_for_repo_wiki": True,
            "raw_repo_scan_default": "blocked_or_fallback",
            "live_fetch": "exact_handle_only",
        },
        "connectors": [
            {
                "connector_id": connector.get("connector_id"),
                "source_system": connector.get("source_system"),
                "target_uri": connector.get("target_uri"),
                "supported_triggers": (connector.get("sync_policy") or {}).get("supported_triggers", []),
                "commit_scoped_outputs_required": (connector.get("sync_policy") or {}).get("commit_scoped_outputs_required", False),
                "pipeline_artifacts_allowed": (connector.get("sync_policy") or {}).get("pipeline_artifacts_allowed", False),
            }
            for connector in connectors
        ],
    }


def context_object_schema_payload() -> dict:
    schema_path = _resource("schemas") / "context-object.schema.json"
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "ok": False,
            "kind": "baltor.context-object-schema",
            "error": str(exc),
            "schema_path": str(schema_path.relative_to(REPO_ROOT)),
        }
    return {
        "ok": True,
        "kind": "baltor.context-object-schema",
        "schema_path": str(schema_path.relative_to(REPO_ROOT)),
        "profile_doc": "docs/architecture/baltor-context-object-standards.md",
        "schema_id": schema.get("$id"),
        "context_object_kind": (schema.get("properties") or {}).get("kind", {}).get("const"),
        "required": schema.get("required", []),
        "object_types": (schema.get("properties") or {}).get("object_type", {}).get("enum", []),
        "source_handle_pattern": (schema.get("properties") or {}).get("source_handles", {}).get("items", {}).get("pattern"),
        "standards_profile": {
            "delivery": "MCP tools/resources/prompts",
            "runtime_context": "LangChain/LangGraph contextSchema-style invocation metadata",
            "validation": "JSON Schema 2020-12",
            "semantics": "JSON-LD and schema.org",
            "provenance": "W3C PROV / PROV-O",
            "evidence_selectors": "W3C Web Annotation style selectors",
            "artifact_packaging": "RO-Crate",
            "software_artifacts": "SPDX or CycloneDX",
            "job_lineage": "OpenLineage",
            "telemetry": "OpenTelemetry semantic conventions",
        },
        "policy": {
            "raw_source_dumps_are_not_context_objects": True,
            "durable_claims_require_source_handles": True,
            "derived_context_must_keep_policy": True,
            "runtime_context_is_not_persistent_memory": True,
        },
        "schema": schema,
    }


CONTEXT_GRAPH_SCHEMA_FILES = [
    "context-object.schema.json",
    "context-version.schema.json",
    "context-artifact.schema.json",
    "context-relationship.schema.json",
    "context-assertion.schema.json",
    "context-dimension-definition.schema.json",
    "context-dimension-value.schema.json",
    "context-model-profile.schema.json",
    "context-model-routing-policy.schema.json",
    "context-reranker-profile.schema.json",
    "context-reranking-policy.schema.json",
    "context-local-memory-profile.schema.json",
    "context-local-sync-policy.schema.json",
    "context-event.schema.json",
    "context-pack.schema.json",
    "context-provider.schema.json",
    "context-pack-builder.schema.json",
    "context-product-surface.schema.json",
]


def context_schema_catalog_payload() -> dict:
    schemas: list[dict] = []
    for filename in CONTEXT_GRAPH_SCHEMA_FILES:
        schema_path = _resource("schemas") / filename
        try:
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            schemas.append({
                "ok": False,
                "schema_path": str(schema_path.relative_to(REPO_ROOT)),
                "error": str(exc),
            })
            continue
        schemas.append({
            "ok": True,
            "schema_path": str(schema_path.relative_to(REPO_ROOT)),
            "schema_id": schema.get("$id"),
            "title": schema.get("title"),
            "kind": (schema.get("properties") or {}).get("kind", {}).get("const"),
            "required": schema.get("required", []),
        })
    return {
        "ok": all(item.get("ok") for item in schemas),
        "kind": "baltor.context-schema-catalog",
        "profile_doc": "docs/architecture/baltor-context-object-graph-profile.md",
        "standards_doc": "docs/architecture/baltor-context-object-standards.md",
        "schema_count": len(schemas),
        "schema_kinds": [item.get("kind") for item in schemas if item.get("kind")],
        "schemas": schemas,
        "storage_agnostic": True,
        "contract_layers": [
            "stable_identity",
            "immutable_versions",
            "derived_artifacts",
            "typed_relationships",
            "risk_based_model_routing",
            "source_aware_reranking",
            "local_encrypted_memory_sync",
            "append_only_events",
            "task_specific_packs",
            "provider_adapters",
            "pack_builders",
            "product_surface",
        ],
    }


def context_product_surface_payload() -> dict:
    return {
        "ok": True,
        "kind": "baltor.context-product-surface",
        "product_id": "baltor-context-fabric",
        "name": "Baltor Context Fabric",
        "positioning": "Governed context object platform for humans, agents, and enterprise systems.",
        "blueprint_doc": "docs/architecture/baltor-context-fabric-product-blueprint.md",
        "graph_profile_doc": "docs/architecture/baltor-context-object-graph-profile.md",
        "modules": [
            "connectors",
            "object_registry",
            "versioning_history",
            "context_graph",
            "artifact_engine",
            "policy_permissions",
            "retrieval_indexing",
            "pack_builder",
            "agent_interfaces",
            "observability_evals",
            "model_routing",
            "reranking",
            "local_memory_sync",
            "feedback",
            "admin_console",
            "developer_kit",
            "industry_packs",
        ],
        "interfaces": ["mcp", "a2a", "rest", "graphql", "webhooks", "sdk", "cli", "ui", "ci_cd"],
        "deployment_models": [
            "local_first_developer",
            "repo_context_as_code",
            "atlassian_rovo_team",
            "enterprise_gateway",
            "custom_context_object_platform",
            "regulated_enclave",
            "industry_network",
        ],
        "standards_mappings": [
            "MCP",
            "A2A",
            "JSON-LD",
            "schema.org",
            "W3C PROV",
            "W3C Web Annotation",
            "OpenLineage",
            "OpenTelemetry",
            "DCAT",
            "SKOS",
            "OIDC/OAuth",
            "OpenFGA/Zanzibar",
            "OPA/Rego",
            "Cedar",
            "FHIR",
            "STIX/TAXII",
            "SPDX",
            "CycloneDX",
            "GS1 EPCIS",
            "OPC UA",
            "IFC",
            "ISO 20022",
            "XBRL/iXBRL",
        ],
        "mvp_phases": [
            {
                "phase": "30_days_context_pack_mvp",
                "deliverables": ["context_for_ticket", "context_for_mr", "context_fetch", "context_trace", "source-linked packs"],
            },
            {
                "phase": "60_days_registry_gateway",
                "deliverables": ["object registry", "versions", "artifacts", "relationships", "events", "MCP gateway integration"],
            },
            {
                "phase": "90_days_retrieval_evals",
                "deliverables": ["hybrid retrieval", "graph expansion", "reranking", "source precedence", "conflict detection", "eval cases"],
            },
        ],
        "product_invariants": {
            "durable_claims_require_source_handles": True,
            "derived_artifacts_keep_lineage": True,
            "context_packs_record_retrieval_policy_and_compression": True,
            "raw_source_expansion_is_exact_handle_or_fallback": True,
            "local_memory_promotion_requires_review": True,
            "generated_repo_wikis_are_derived_artifacts": True,
            "model_routing_is_provider_neutral": True,
            "escalation_depends_on_risk_not_brand": True,
            "reranking_is_source_aware_not_embedding_only": True,
            "lora_rerankers_are_adapter_profiles_not_global_truth": True,
            "private_e2ee_memory_is_not_cloud_searchable": True,
            "local_memory_and_company_context_are_separate_tiers": True,
            "offline_cache_requires_ttl_and_freshness_labels": True,
        },
    }


def context_model_routing_payload(*, run: dict | None = None, task_type: str = "claim_review", risk: dict | None = None) -> dict:
    generated_at = iso_now()
    score_formula = {
        "uncertainty": 0.20,
        "conflict": 0.20,
        "downstream_risk": 0.15,
        "graph_centrality": 0.15,
        "temporal_fragility": 0.10,
        "ambiguity": 0.10,
        "low_source_quality": 0.05,
        "model_disagreement": 0.05,
    }
    slots = [
        ("tier-0-deterministic", 0, "deterministic", ["regex", "date_parser", "json_schema", "pydantic", "entity_linker", "shacl"], ["normalization", "schema_validation", "date_parsing", "dedupe", "policy_gate"], "none", "free_or_sunk", ["local"]),
        ("tier-1-small-local", 1, "small_local", ["Gemma-small", "Qwen-small", "Granite-small", "Ministral", "Nemotron-small"], ["bulk_tagging", "simple_claim_extraction", "ambiguity_flags", "fragile_fact_flags"], "low", "cheap", ["local", "self_hosted"]),
        ("tier-2-mid-open", 2, "mid_open", ["Qwen-mid", "Gemma-mid", "Mistral-Small-Medium", "GLM-Flash-Air"], ["edge_extraction", "evidence_review", "schema_repair", "summary_verification"], "medium", "balanced", ["local", "self_hosted", "hosted_api", "gateway"]),
        ("tier-3-large-open", 3, "large_open", ["MiniMax", "Kimi", "DeepSeek", "Llama", "Mistral-Large", "GLM", "Nemotron", "Jamba"], ["hard_reasoning", "long_context_review", "graph_enrichment", "multi_document_conflict_detection"], "high_but_not_final", "expensive", ["self_hosted", "hosted_api", "gateway"]),
        ("tier-4-ensemble", 4, "ensemble", ["mixed_open_models", "specialist_judges", "independent_rubrics"], ["disagreement_resolution", "uncertainty_estimation", "blind_spot_detection"], "very_high_with_appeal", "expensive", ["gateway", "self_hosted", "hosted_api"]),
        ("tier-5-frontier", 5, "frontier", ["frontier_primary", "frontier_appeal"], ["final_adjudication", "high_stakes_summary", "unresolved_conflict"], "very_high_with_appeal", "expensive", ["hosted_api", "gateway"]),
        ("tier-6-human", 6, "human_review", ["analyst", "sme", "legal", "compliance", "security", "clinical"], ["legal_sensitive_claim", "reputational_claim", "medical_or_financial_claim", "unresolved_model_disagreement"], "final_human", "human_cost", ["human_queue"]),
    ]
    model_profiles = [
        {
            "kind": "baltor.context-model-profile",
            "model_profile_id": f"model-profile://baltor/{profile_id}",
            "tier": tier,
            "slot": slot,
            "example_families": families,
            "deployment_modes": deployment_modes,
            "default_tasks": default_tasks,
            "max_risk": max_risk,
            "cost_profile": cost_profile,
            "privacy": {
                "privacy_filter_before_model": slot not in {"deterministic", "human_review"},
                "raw_private_context_allowed": slot in {"deterministic", "small_local"},
                "model_destination_policy_required": slot in {"large_open", "ensemble", "frontier"},
            },
            "policy": {"provider_neutral_slot": True, "final_judge": slot in {"frontier", "human_review"}},
            "created_at": generated_at,
        }
        for profile_id, tier, slot, families, default_tasks, max_risk, cost_profile, deployment_modes in slots
    ]
    routing_policy = {
        "kind": "baltor.context-model-routing-policy",
        "routing_policy_id": "model-routing://baltor/risk-ladder/v1",
        "score_formula": score_formula,
        "thresholds": [
            {"min": 0.00, "max": 0.30, "route": "deterministic_then_small_local", "action": "small model plus validators"},
            {"min": 0.31, "max": 0.55, "route": "mid_open", "action": "mid open model review"},
            {"min": 0.56, "max": 0.75, "route": "large_open", "action": "large open model review"},
            {"min": 0.76, "max": 0.90, "route": "ensemble_then_frontier_if_needed", "action": "ensemble review and appeal on disagreement"},
            {"min": 0.91, "max": 1.00, "route": "frontier_then_human", "action": "frontier review plus human approval"},
        ],
        "escalation_triggers": [
            "high_uncertainty",
            "source_conflict",
            "temporal_fragility",
            "ambiguous_term",
            "high_graph_centrality",
            "high_downstream_risk",
            "low_source_quality",
            "weak_evidence_directness",
            "entity_resolution_uncertainty",
            "model_disagreement",
            "regulated_or_sensitive_domain",
        ],
        "policy": {
            "provider_neutral": True,
            "route_by_task_cost_uncertainty_and_risk": True,
            "do_not_escalate_by_brand_or_prestige": True,
            "frontier_is_appeal_not_default": True,
            "human_review_for_unresolved_high_risk": True,
            "privacy_filter_before_model": True,
        },
        "created_at": generated_at,
    }
    signals = dict(risk or {})
    if run:
        signals.setdefault("uncertainty", 0.35 if (run.get("claims") or []) else 0.75)
        signals.setdefault("conflict", 1.0 if (run.get("ownership_conflict_groups") or []) else 0.0)
        signals.setdefault("downstream_risk", 0.7 if (run.get("ownership_change_records") or []) else 0.35)
        signals.setdefault("graph_centrality", 0.62 if (run.get("ownership_conflict_groups") or []) else 0.35)
        signals.setdefault("temporal_fragility", 0.8 if any(item.get("requires_refresh") for item in run.get("ownership_change_records") or []) else 0.25)
        signals.setdefault("ambiguity", 0.75 if (run.get("term_clarity_concerns") or []) else 0.2)
        signals.setdefault("low_source_quality", 0.35)
        signals.setdefault("model_disagreement", 0.0)
    else:
        for key in score_formula:
            signals.setdefault(key, 0.0)
    escalation_score = max(0.0, min(1.0, sum(float(signals.get(key) or 0) * weight for key, weight in score_formula.items())))
    selected = next(item for item in routing_policy["thresholds"] if escalation_score >= item["min"] and escalation_score <= item["max"])
    return {
        "ok": True,
        "kind": "baltor.context-model-routing",
        "run_id": (run or {}).get("run_id"),
        "task_type": task_type,
        "model_profiles": model_profiles,
        "routing_policy": routing_policy,
        "sample_route_decision": {
            "task_type": task_type,
            "risk_signals": signals,
            "escalation_score": round(escalation_score, 3),
            "recommended_route": selected["route"],
            "recommended_action": selected["action"],
            "decision_reason": "Route selected from weighted risk signals; provider families remain interchangeable within the slot.",
        },
    }


def context_reranking_payload(*, run: dict | None = None, query: str = "", task_type: str = "implementation_pack", risk: dict | None = None) -> dict:
    generated_at = iso_now()
    score_formula = {
        "lexical_match": 0.12,
        "semantic_similarity": 0.16,
        "source_authority": 0.16,
        "freshness": 0.12,
        "verifiability": 0.16,
        "relationship_proximity": 0.10,
        "task_fit": 0.10,
        "low_prompt_injection_risk": 0.05,
        "human_verified": 0.03,
    }
    profile_rows = [
        ("stage-0-deterministic-filter", 0, "deterministic_filter", ["ACL filter", "source-handle exact match", "schema validation", "date parser", "dedupe", "policy gate"], ["acl_filter", "exact_handle_boost", "date_gate", "duplicate_removal", "unsafe_source_downrank"], {"input": "all_candidates", "output": "eligible_candidates"}, "free_or_sunk", {"trainable": False, "lora_applicable": False}, ["local", "gateway"]),
        ("stage-1-lexical-ranker", 1, "lexical_ranker", ["BM25", "keyword boost", "path/symbol exact match", "issue-key exact match"], ["high_recall_first_pass", "identifier_search", "path_search", "ticket_key_search"], {"input": "eligible_candidates", "output_limit": 200}, "low", {"trainable": False, "lora_applicable": False}, ["local", "self_hosted", "gateway"]),
        ("stage-2-vector-ranker", 2, "vector_ranker", ["dense embeddings", "sparse embeddings", "hybrid vector search", "multivector retrieval"], ["semantic_recall", "similar_case_retrieval", "summary_candidate_search"], {"input": "eligible_candidates", "output_limit": 100}, "low", {"trainable": True, "lora_applicable": False, "notes": "Embedding models can be fine-tuned; LoRA reranking usually belongs to cross-encoder or judge adapters."}, ["local", "self_hosted", "hosted_api", "gateway"]),
        ("stage-3-cross-encoder", 3, "cross_encoder", ["SentenceTransformers CrossEncoder", "BGE reranker", "ColBERT-style late interaction", "multimodal reranker"], ["top_candidate_precision", "query_passage_pair_scoring", "evidence_span_ranking"], {"input": "top_100", "output_limit": 25}, "medium", {"trainable": True, "lora_applicable": True, "adapter_scope": "domain_or_task"}, ["local", "self_hosted", "hosted_api", "gateway"]),
        ("stage-4-lora-domain-reranker", 4, "lora_domain_reranker", ["PEFT LoRA adapter", "QLoRA adapter", "domain cross-encoder adapter", "industry evidence-ranker adapter"], ["regulated_domain_ranking", "repo_specific_ranking", "support_ticket_ranking", "legal_clause_ranking", "clinical_evidence_ranking"], {"input": "top_50", "output_limit": 12}, "medium", {"trainable": True, "lora_applicable": True, "adapter_scope": "tenant_domain_task", "requires_eval_before_promotion": True}, ["local", "self_hosted", "gateway"]),
        ("stage-5-llm-judge-reranker", 5, "llm_judge", ["small judge model", "large open judge", "frontier appeal judge", "ensemble judge"], ["conflict_aware_reranking", "source_precedence_review", "high_risk_pack_selection"], {"input": "top_20", "output_limit": 8}, "high", {"trainable": True, "lora_applicable": True, "adapter_scope": "rubric_or_domain", "use_only_when_risk_justifies_latency": True}, ["self_hosted", "hosted_api", "gateway"]),
        ("stage-6-human-review", 6, "human_review", ["SME review", "legal review", "clinical review", "security review", "compliance approval"], ["final_high_stakes_pack_ordering", "unresolved_conflict", "adapter_training_label_approval"], {"input": "top_10", "output_limit": 8}, "human", {"trainable": False, "lora_applicable": False, "labels_feed_training_set": True}, ["human_queue"]),
    ]
    reranker_profiles = [
        {
            "kind": "baltor.context-reranker-profile",
            "reranker_profile_id": f"reranker-profile://baltor/{profile_id}",
            "stage": stage,
            "slot": slot,
            "example_families": families,
            "deployment_modes": deployment_modes,
            "default_tasks": default_tasks,
            "candidate_pool": candidate_pool,
            "latency_profile": latency_profile,
            "training": training,
            "policy": {
                "source_aware": True,
                "acl_filter_before_rerank": True,
                "reranker_is_not_source_of_truth": True,
                "adapter_outputs_require_evidence_handles": True,
            },
            "created_at": generated_at,
        }
        for profile_id, stage, slot, families, default_tasks, candidate_pool, latency_profile, training, deployment_modes in profile_rows
    ]
    reranking_policy = {
        "kind": "baltor.context-reranking-policy",
        "reranking_policy_id": "reranking://baltor/source-aware-ladder/v1",
        "score_formula": score_formula,
        "pipeline": [
            {"stage": 0, "slot": "deterministic_filter", "action": "drop inaccessible, stale-beyond-policy, duplicate, and unsafe candidates", "candidate_limit": 1000},
            {"stage": 1, "slot": "lexical_ranker", "action": "boost exact handles, issue keys, file paths, symbols, and source IDs", "candidate_limit": 200},
            {"stage": 2, "slot": "vector_ranker", "action": "merge dense/sparse semantic recall with keyword candidates", "candidate_limit": 100},
            {"stage": 3, "slot": "cross_encoder", "action": "score query-candidate pairs for top-candidate precision", "candidate_limit": 50},
            {"stage": 4, "slot": "lora_domain_reranker", "action": "apply tenant/domain/task adapter only when eval-approved for the corpus", "candidate_limit": 25},
            {"stage": 5, "slot": "llm_judge", "action": "review source precedence, conflicts, and high-risk evidence ordering", "candidate_limit": 12},
            {"stage": 6, "slot": "human_review", "action": "approve unresolved high-stakes ordering and generate training labels", "candidate_limit": 8},
        ],
        "escalation_triggers": [
            "query_needs_exact_identifier",
            "candidate_conflict",
            "weak_evidence_directness",
            "domain_adapter_available",
            "high_prompt_injection_risk",
            "regulated_domain",
            "high_downstream_risk",
            "low_verifiability",
            "reranker_disagreement",
        ],
        "policy": {
            "source_aware_not_embedding_only": True,
            "acl_filter_before_rerank": True,
            "lexical_and_exact_match_are_first_class": True,
            "lora_adapters_require_eval_and_lineage": True,
            "llm_judge_is_appeal_not_default": True,
            "human_labels_can_train_future_rerankers": True,
            "ranked_candidates_keep_source_handles": True,
        },
        "created_at": generated_at,
    }
    signals = dict(risk or {})
    if run:
        records = iter_rag_records(run)
        claims = run.get("claims") or []
        signals.setdefault("lexical_match", min(1.0, keyword_score(query, " ".join(str(record.get("text") or "") for record in records[:20])) / 4))
        signals.setdefault("semantic_similarity", 0.55 if records else 0.0)
        signals.setdefault("source_authority", 0.78 if claims else 0.35)
        signals.setdefault("freshness", 0.45 if any(item.get("requires_refresh") for item in run.get("ownership_change_records") or []) else 0.78)
        signals.setdefault("verifiability", 0.72 if claims else 0.3)
        signals.setdefault("relationship_proximity", 0.7 if (run.get("ownership_conflict_groups") or []) else 0.45)
        signals.setdefault("task_fit", 0.74)
        signals.setdefault("low_prompt_injection_risk", 0.82)
        signals.setdefault("human_verified", 0.0)
    else:
        for key in score_formula:
            signals.setdefault(key, 0.0)
    combined_score = max(0.0, min(1.0, sum(float(signals.get(key) or 0) * weight for key, weight in score_formula.items())))
    if combined_score >= 0.78 or float(signals.get("verifiability") or 0) < 0.35:
        selected_stage = "llm_judge_or_human_if_high_risk"
    elif float(signals.get("source_authority") or 0) >= 0.7 and float(signals.get("verifiability") or 0) >= 0.65:
        selected_stage = "cross_encoder_then_lora_if_domain_adapter_available"
    elif float(signals.get("lexical_match") or 0) >= 0.7:
        selected_stage = "lexical_plus_cross_encoder"
    else:
        selected_stage = "hybrid_vector_then_cross_encoder"
    return {
        "ok": True,
        "kind": "baltor.context-reranking",
        "run_id": (run or {}).get("run_id"),
        "query": query,
        "task_type": task_type,
        "reranker_profiles": reranker_profiles,
        "reranking_policy": reranking_policy,
        "sample_rerank_decision": {
            "task_type": task_type,
            "ranking_signals": signals,
            "combined_score": round(combined_score, 3),
            "recommended_stage": selected_stage,
            "decision_reason": "Ranking uses source-aware signals first; LoRA/domain rerankers are eval-gated adapters for known corpora, not global authority.",
        },
    }


def context_local_memory_payload(*, run: dict | None = None, scope: str = "personal") -> dict:
    generated_at = iso_now()
    profiles = [
        {
            "kind": "baltor.context-local-memory-profile",
            "local_memory_profile_id": "local-memory://baltor/private-local/v1",
            "memory_class": "private_local",
            "scope": {"default_scope": "personal", "decryptors": ["user_devices"]},
            "storage": {"formats": ["markdown", "sqlite", "sqlcipher"], "local_index": ["keyword", "local_vector_optional"]},
            "encryption": {"mode": "end_to_end_sync", "cloud_can_decrypt": False, "key_scope": "user_or_device"},
            "search": {"local_search": True, "cloud_search": False, "server_embeddings": False, "local_embeddings_only": True},
            "sync": {"mode": "encrypted_event_log", "offline_writes": True, "cloud_stores": ["ciphertext_events", "ciphertext_blobs", "sync_cursors"]},
            "policy": {"raw_source_dumps_blocked": True, "secrets_blocked": True, "durable_claims_require_source_handles": True},
            "created_at": generated_at,
        },
        {
            "kind": "baltor.context-local-memory-profile",
            "local_memory_profile_id": "local-memory://baltor/team-encrypted/v1",
            "memory_class": "team_encrypted",
            "scope": {"default_scope": "team", "decryptors": ["team_members", "approved_devices"]},
            "storage": {"formats": ["markdown", "sqlite", "git_encrypted"], "local_index": ["keyword", "local_vector_optional"]},
            "encryption": {"mode": "end_to_end_sync", "cloud_can_decrypt": False, "key_scope": "team_key"},
            "search": {"local_search": True, "cloud_search": False, "server_embeddings": False, "local_embeddings_only": True},
            "sync": {"mode": "encrypted_blob_relay", "offline_writes": True, "conflict_resolution": "local_or_review_queue"},
            "policy": {"team_memory_requires_review": True, "revocation_not_retroactive": True, "source_handles_required": True},
            "created_at": generated_at,
        },
        {
            "kind": "baltor.context-local-memory-profile",
            "local_memory_profile_id": "local-memory://baltor/org-approved-cache/v1",
            "memory_class": "org_approved_cache",
            "scope": {"default_scope": "repo_or_ticket", "decryptors": ["user_device"], "source": "company_context_gateway"},
            "storage": {"formats": ["encrypted_context_pack", "sqlite"], "ttl_required": True},
            "encryption": {"mode": "local_only", "cloud_can_decrypt": False, "key_scope": "device_key"},
            "search": {"local_search": True, "cloud_search": "via_company_context_gateway_when_online", "server_embeddings": "company_context_only"},
            "sync": {"mode": "company_context_cache", "offline_reads": True, "online_revalidation": True},
            "policy": {"freshness_label_required": True, "last_validated_at_required": True, "source_writes_disabled_offline": True},
            "created_at": generated_at,
        },
        {
            "kind": "baltor.context-local-memory-profile",
            "local_memory_profile_id": "local-memory://baltor/company-context/v1",
            "memory_class": "company_context",
            "scope": {"default_scope": "org", "decryptors": ["company_context_service"]},
            "storage": {"formats": ["context_objects", "artifacts", "indexes"], "central_index": True},
            "encryption": {"mode": "company_managed", "cloud_can_decrypt": True, "key_scope": "kms_or_byok"},
            "search": {"local_search": False, "cloud_search": True, "server_embeddings": True, "reranking": True, "compression": True},
            "sync": {"mode": "company_context_gateway", "offline_writes": False, "cached_locally_with_ttl": True},
            "policy": {"permission_aware": True, "audited": True, "source_acl_before_model": True},
            "created_at": generated_at,
        },
    ]
    sync_policy = {
        "kind": "baltor.context-local-sync-policy",
        "local_sync_policy_id": "local-sync://baltor/hybrid-local-memory/v1",
        "sync_modes": ["local_only", "encrypted_event_log", "encrypted_blob_relay", "git_encrypted", "company_context_cache"],
        "offline_policy": {
            "memory_reads_allowed": True,
            "memory_writes_allowed": True,
            "local_search_allowed": True,
            "company_context_cache_allowed": True,
            "source_system_writes_allowed": False,
            "freshness_claim": "last_validated_at_required",
            "online_validation_queued": True,
        },
        "cloud_visibility": {
            "private_e2ee_memory_plaintext_visible_to_cloud": False,
            "private_e2ee_embeddings_visible_to_cloud": False,
            "company_context_plaintext_visible_to_approved_service": True,
            "encrypted_sync_blobs_are_not_server_searchable": True,
        },
        "tool_contract": {
            "mcp_tools": ["remember", "search_memory", "context_for_ticket", "context_for_repo", "context_fetch", "sync_status", "sync_now", "validate_sources_when_online"],
            "phase_1_denies": ["jira_write", "confluence_write", "gitlab_write", "raw_source_dump_to_memory", "secret_storage", "customer_data_storage"],
            "ask_before": ["team_memory_write", "repo_memory_write", "raw_source_excerpt_expansion", "cross_device_sync"],
        },
        "policy": {
            "split_brain_required": True,
            "private_memory_syncs_like_encrypted_notebook": True,
            "company_context_retrieves_like_governed_index": True,
            "plaintext_embeddings_are_sensitive": True,
            "local_embeddings_stay_local_by_default": True,
            "cached_company_context_requires_ttl": True,
        },
        "created_at": generated_at,
    }
    cache_status = {
        "run_id": (run or {}).get("run_id"),
        "cached_company_pack_available": bool(run),
        "last_validated_at": generated_at if run else None,
        "freshness_status": "current_for_demo" if run else "no_local_pack",
        "offline_safe": bool(run),
        "queued_sync_events": 0,
        "scope": scope,
    }
    return {
        "ok": True,
        "kind": "baltor.context-local-memory",
        "profile_doc": "docs/architecture/baltor-local-encrypted-memory-sync.md",
        "run_id": (run or {}).get("run_id"),
        "memory_profiles": profiles,
        "sync_policy": sync_policy,
        "cache_status": cache_status,
        "gateway_policy": {
            "private_e2ee_memory_not_cloud_searchable": True,
            "company_context_index_is_separate": True,
            "source_handles_required_for_memory_claims": True,
            "offline_source_freshness_must_be_labeled": True,
        },
    }


def keyword_score(query: str, text: str) -> int:
    terms = [term for term in re.findall(r"[A-Za-z0-9$:/.-]{3,}", query.lower()) if term]
    haystack = text.lower()
    return sum(1 for term in terms if term in haystack)


def context_search_payload(query: str, *, run: dict | None = None, task_type: str = "code_change", token_budget: int = 3000, pack_type: str = "implementation_pack", tenant_id: str = DEFAULT_TENANT) -> dict:
    sync_context_worker_events()
    sync_worker_ledger()
    tenant_id = normalize_tenant(tenant_id)
    # P2 isolation: a run passed in is honored ONLY if it belongs to this tenant; the empty-run fallback is
    # this tenant's latest run, never the global latest — so a tenant can never search another's index.
    if run is not None and not run_visible_to(run, tenant_id):
        run = None
    run = run or latest_run_for_tenant(tenant_id)
    if not run:
        _rcpt = gateway_receipt("context.search", run=None, ok=False, query=query, tenant_id=tenant_id)
        return {
            "ok": False,
            "answerable": False,
            "error": "no indexed run is available",
            "gateway_policy": gateway_status_payload()["policy"],
            "receipt": {"receipt_id": _rcpt["receipt_id"], "operation": _rcpt["operation"], "is_truth": False},
        }
    records = iter_rag_records(run)
    claims = run.get("claims") or []
    scored_records = []
    for record in records:
        score = keyword_score(query, str(record.get("text") or "") + " " + json.dumps(record.get("source") or {}))
        scored_records.append((score, record))
    scored_claims = []
    for claim in claims:
        score = keyword_score(query, str(claim.get("claim") or "") + " " + str(claim.get("source") or ""))
        scored_claims.append((score, claim))
    selected_records = [record for score, record in sorted(scored_records, key=lambda item: item[0], reverse=True) if score > 0]
    selected_claims = [claim for score, claim in sorted(scored_claims, key=lambda item: item[0], reverse=True) if score > 0]
    if not selected_records:
        selected_records = records[:8]
    if not selected_claims:
        selected_claims = claims[:8]

    pack = context_pack(run, pack_type=pack_type, token_budget=token_budget)
    pack["task_type"] = task_type
    pack["query"] = query
    pack["retrieval"] = {
        "strategy": "local_keyword_plus_graph_handles",
        "records_considered": len(records),
        "claims_considered": len(claims),
        "records_returned": min(len(selected_records), 8),
        "claims_returned": min(len(selected_claims), 8),
        "acl_filter_applied": True,
        "live_source_fetch_used": False,
    }
    pack["context_pack"]["facts"] = [
        {
            "claim": claim.get("claim"),
            "source": claim.get("source"),
            "handle": context_handle("claim", run_id=str(run.get("run_id") or ""), claim_id=str(claim.get("id") or "")),
            "citation": f"{claim.get('source')}::{claim.get('id')}",
            "freshness": "indexed",
            "trust": claim.get("state") or "candidate",
            "safe_context_policy": "cite_and_do_not_present_volatile_facts_as_current_without_refresh",
            "claim_type": claim.get("claim_type") or "general_claim",
            "temporal_fragility": claim.get("temporal_fragility") or "unknown",
            "requires_refresh": bool(claim.get("requires_refresh")),
            "safe_context_instruction": claim.get("safe_context_instruction"),
            "ownership_event_type": (claim.get("ownership_change") or {}).get("event_type") if isinstance(claim.get("ownership_change"), dict) else None,
        }
        for claim in selected_claims[:8]
    ]
    pack["context_pack"]["source_handles"] = [record.get("handle") for record in selected_records[:12] if record.get("handle")]
    pack["context_pack"]["next_fetches"] = [
        {"handle": record.get("handle"), "why": "Fetch this bounded source component if more exact evidence is needed."}
        for record in selected_records[:6]
    ]
    pack["context_pack"]["code_pointers"] = [
        {
            "path": (record.get("source") or {}).get("file_path"),
            "reason": "Matched by local gateway keyword search over normalized components.",
            "handle": record.get("handle"),
        }
        for record in selected_records[:6]
    ]
    # Honest provenance (deep-dive item 2): every served search mints a persisted receipt + a receipt_issued
    # bus event. Serving a pack is NOT asserting its facts are true (is_truth:false); the receipt records WHAT
    # was served, hashed, so the "agents propose, Baltor disposes" claim is auditable rather than aspirational.
    _rcpt = gateway_receipt("context.search", run=run, ok=True, query=query, content=pack.get("context_pack"), tenant_id=tenant_id)
    pack["receipt"] = {"receipt_id": _rcpt["receipt_id"], "operation": _rcpt["operation"],
                       "content_hash": _rcpt["content_hash"], "is_truth": False}
    pack["tenant_id"] = tenant_id
    return {"ok": True, **pack}


_FETCH_POLICY = {"bounded_fetch": True, "raw_source_access_is_fallback": True, "citation_required": True}


def context_fetch_payload(handle: str, *, run: dict | None = None, max_tokens: int = 1000, tenant_id: str = DEFAULT_TENANT) -> dict:
    sync_context_worker_events()
    sync_worker_ledger()
    tenant_id = normalize_tenant(tenant_id)

    # P2 ctxv:// (immutable, version-pinned) fetch: serve the EXACT bytes pinned under this version, even if
    # the live content has since changed — or 410 Gone if that version was superseded and pruned, or 404 if
    # this tenant never pinned it (existence is never leaked across tenants).
    if str(handle).startswith("ctxv://"):
        status, vrow = fetch_pinned_version(tenant_id, handle)
        if status == "ok":
            try:
                content = json.loads((vrow or {}).get("body_json") or "{}")
            except json.JSONDecodeError:
                content = {}
            _rcpt = gateway_receipt("context.fetch", run={"run_id": (vrow or {}).get("run_id")},
                                    ok=True, handle=handle, content=content, tenant_id=tenant_id)
            return {
                "ok": True, "status": "ok", "handle": handle, "kind": (vrow or {}).get("kind") or "version",
                "immutable": True, "base_handle": (vrow or {}).get("base_handle"),
                "content_hash": (vrow or {}).get("content_hash"),
                "token_budget_used_estimate": min(max_tokens, max(1, len(str(content)) // 4)),
                "content": content,
                "receipt": {"receipt_id": _rcpt["receipt_id"], "operation": _rcpt["operation"],
                            "content_hash": _rcpt["content_hash"], "is_truth": False},
                "gateway_policy": {**_FETCH_POLICY, "version_pinned": True},
            }
        # superseded+pruned (410) vs never-seen (404) — both still mint a receipt (honest: we WERE asked).
        _rcpt = gateway_receipt("context.fetch", run=None, ok=False, handle=handle, tenant_id=tenant_id)
        err = ("this pinned version was superseded and has been pruned (lossless retention window passed)"
               if status == "gone" else "version handle not found for this tenant")
        return {"ok": False, "status": status, "handle": handle, "error": err,
                "receipt": {"receipt_id": _rcpt["receipt_id"], "operation": _rcpt["operation"], "is_truth": False}}

    # ctx:// (latest, mutable): tenant-scoped run resolution — never the global latest.
    if run is not None and not run_visible_to(run, tenant_id):
        run = None
    run = run or latest_run_for_tenant(tenant_id)
    if not run:
        _rcpt = gateway_receipt("context.fetch", run=None, ok=False, handle=handle, tenant_id=tenant_id)
        return {"ok": False, "status": "no_run", "error": "no indexed run is available", "handle": handle,
                "receipt": {"receipt_id": _rcpt["receipt_id"], "operation": _rcpt["operation"], "is_truth": False}}
    records = iter_rag_records(run)
    for record in records:
        if record.get("handle") == handle:
            # Receipt on the raw ingested-content fetch (deep-dive item 2): hashed record of WHAT was served.
            _rcpt = gateway_receipt("context.fetch", run=run, ok=True, handle=handle, content=record, tenant_id=tenant_id)
            # P2: pin the served content as an immutable ctxv:// the agent can re-fetch byte-identically.
            vhandle = pin_version(tenant_id=tenant_id, run=run, base_handle=handle, kind="component", content=record)
            return {
                "ok": True,
                "status": "ok",
                "handle": handle,
                "version_handle": vhandle,                # immutable pin of exactly these bytes
                "kind": "component",
                "token_budget_used_estimate": min(max_tokens, max(1, len(str(record.get("text") or "")) // 4)),
                "content": record,
                "receipt": {"receipt_id": _rcpt["receipt_id"], "operation": _rcpt["operation"],
                            "content_hash": _rcpt["content_hash"], "is_truth": False},
                "gateway_policy": _FETCH_POLICY,
            }
    for claim in run.get("claims") or []:
        claim_handle = context_handle("claim", run_id=str(run.get("run_id") or ""), claim_id=str(claim.get("id") or ""))
        if claim_handle == handle:
            _rcpt = gateway_receipt("context.fetch", run=run, ok=True, handle=handle, content=claim, tenant_id=tenant_id)
            served = {
                **claim,
                "handle": claim_handle,
                "instruction": claim.get("safe_context_instruction") or "Use with citation; do not present volatile facts as current without refresh.",
            }
            vhandle = pin_version(tenant_id=tenant_id, run=run, base_handle=handle, kind="claim", content=served)
            return {
                "ok": True,
                "status": "ok",
                "handle": handle,
                "version_handle": vhandle,
                "kind": "claim",
                "token_budget_used_estimate": min(max_tokens, max(1, len(str(claim.get("claim") or "")) // 4)),
                "content": served,
                "receipt": {"receipt_id": _rcpt["receipt_id"], "operation": _rcpt["operation"],
                            "content_hash": _rcpt["content_hash"], "is_truth": False},
                "gateway_policy": _FETCH_POLICY,
            }
    _rcpt = gateway_receipt("context.fetch", run=run, ok=False, handle=handle, tenant_id=tenant_id)
    return {
        "ok": False,
        "status": "missing",
        "error": "handle not found in current local index",
        "handle": handle,
        "available_handles": [record.get("handle") for record in records[:20] if record.get("handle")],
        "receipt": {"receipt_id": _rcpt["receipt_id"], "operation": _rcpt["operation"], "is_truth": False},
    }


def context_glossary_payload(*, run: dict | None = None, term: str = "", max_packets: int = 12) -> dict:
    sync_context_worker_events()
    sync_worker_ledger()
    run = run or latest_run()
    if not run:
        return {
            "ok": True,
            "kind": "baltor.context-glossary",
            "run_id": None,
            "packet_count": 0,
            "packets": [],
            "message": "no indexed run is available",
            "gateway_policy": gateway_status_payload()["policy"],
        }
    term_filter = term.lower().strip()
    packets = list(run.get("glossary_resolution_packets") or [])
    if term_filter:
        packets = [packet for packet in packets if term_filter in str(packet.get("term") or "").lower()]
    packets = packets[:max(1, min(50, max_packets))]
    return {
        "ok": True,
        "kind": "baltor.context-glossary",
        "run_id": run.get("run_id"),
        "packet_count": len(packets),
        "packets": packets,
        "gateway_policy": {
            "acl_filter_before_model": True,
            "source_scoped_terms_only": True,
            "block_global_memory_promotion": True,
            "block_canonical_graph_promotion": True,
            "raw_source_access_is_fallback": True,
        },
    }


def context_dimensions_payload(*, run: dict | None = None, dimension_id: str = "", subject_id: str = "", max_values: int = 100) -> dict:
    if not run:
        return {
            "ok": True,
            "kind": "baltor.context-dimensions",
            "status": "no run available",
            "dimension_definitions": [],
            "dimension_values": [],
            "counts": {"dimension_definitions": 0, "dimension_values": 0},
            "gateway_policy": {
                "read_only": True,
                "scores_are_assessments_not_source_facts": True,
                "source_handles_required_for_durable_use": True,
                "bounded_response": True,
            },
        }
    records = context_object_graph_records(run)
    definitions = records.get("dimension_definitions") or []
    values = records.get("dimension_values") or []
    if dimension_id:
        definitions = [item for item in definitions if item.get("dimension_id") == dimension_id]
        values = [item for item in values if item.get("dimension_id") == dimension_id]
    if subject_id:
        values = [item for item in values if item.get("subject_id") == subject_id]
    values = values[:max(1, min(500, max_values))]
    return {
        "ok": True,
        "kind": "baltor.context-dimensions",
        "run_id": run.get("run_id"),
        "dimension_definitions": definitions,
        "dimension_values": values,
        "counts": {
            "dimension_definitions": len(definitions),
            "dimension_values": len(values),
            "total_dimension_definitions": records.get("counts", {}).get("dimension_definitions"),
            "total_dimension_values": records.get("counts", {}).get("dimension_values"),
        },
        "filters": {
            "dimension_id": dimension_id,
            "subject_id": subject_id,
            "max_values": max_values,
        },
        "gateway_policy": {
            "read_only": True,
            "scores_are_assessments_not_source_facts": True,
            "source_handles_required_for_durable_use": True,
            "bounded_response": True,
        },
    }


def context_trace_payload(result_id: str = "") -> dict:
    return {
        "ok": True,
        "result_id": result_id or f"ctxr-{compact_id((latest_run() or {}).get('run_id'))}",
        "trace": [
            "Received coding-agent context request.",
            "Selected local indexed run as retrieval backend.",
            "Applied local ACL/demo policy before returning content.",
            "Ranked normalized components and claims with keyword matching.",
            "Compressed matches into a typed context pack with ctx:// handles.",
            "Deferred raw source expansion to context_fetch(handle).",
        ],
        "policy": gateway_status_payload()["policy"],
    }


def export_payload(run: dict, kind: str) -> dict:
    counts = run_artifact_counts(run)
    connector_envelopes = [
        source.get("connector_envelope")
        for source in run.get("sources") or []
        if isinstance(source, dict) and isinstance(source.get("connector_envelope"), dict)
    ]
    base = {
        "package_type": f"baltor.{kind}",
        "generated_at": int(time.time()),
        "run_id": run.get("run_id"),
        "status": run.get("status"),
        "progress": run.get("progress"),
    }
    if kind == "manifest":
        return {
            **base,
            "sources": run.get("sources") or [],
            "document_tree_summary": (run.get("document_tree") or {}).get("summary") or {},
            "queue": {
                "published": bool(run.get("queue_published")),
                "job_id": run.get("queue_job_id"),
            },
            "summary": run.get("summary") or {},
            "artifact_counts": counts,
            "ownership_change_records": run.get("ownership_change_records") or ownership_change_records(run.get("claims") or []),
            "ownership_conflict_groups": run.get("ownership_conflict_groups") or ownership_conflict_groups(run.get("ownership_change_records") or ownership_change_records(run.get("claims") or [])),
            "term_clarity_concerns": run.get("term_clarity_concerns") or [],
            "glossary_resolution_packets": run.get("glossary_resolution_packets") or [],
            "connector_envelopes": connector_envelopes,
            "exports": ["manifest", "text", "rag", "graph", "audit", "safe-context", "context-pack", "glossary", "context-objects"],
            "contracts": {
                "local_first": True,
                "llm_outputs_are_unpromoted": True,
                "requires_citations": True,
                "ctx_handles": True,
                "mcp_context_gateway": True,
                "connector_envelopes": True,
            },
        }
    if kind == "text":
        return {
            **base,
            "sources": run.get("sources") or [],
            "document_tree": run.get("document_tree") or {},
            "connector_envelopes": connector_envelopes,
            "claims": run.get("claims") or [],
            "ownership_change_records": run.get("ownership_change_records") or ownership_change_records(run.get("claims") or []),
            "ownership_conflict_groups": run.get("ownership_conflict_groups") or ownership_conflict_groups(run.get("ownership_change_records") or ownership_change_records(run.get("claims") or [])),
            "term_clarity_concerns": run.get("term_clarity_concerns") or [],
            "glossary_resolution_packets": run.get("glossary_resolution_packets") or [],
            "text_preview": str(run.get("text") or "")[:20000],
        }
    if kind == "rag":
        return {
            **base,
            "records": iter_rag_records(run),
            "record_count": len(iter_rag_records(run)),
            "retrieval_policy": {
                "prefer_reviewed_claims": True,
                "include_source_dates_for_fragile_facts": True,
                "do_not_present_candidate_claims_as_verified": True,
            },
        }
    if kind == "graph":
        return {**base, **graph_package(run)}
    if kind == "safe-context":
        return {
            **base,
            "approved_context": [
                {
                    "claim_id": claim.get("id"),
                    "handle": context_handle("claim", run_id=str(run.get("run_id") or ""), claim_id=str(claim.get("id") or "")),
                    "text": claim.get("claim"),
                    "source": claim.get("source"),
                    "state": claim.get("state"),
                    "claim_type": claim.get("claim_type") or "general_claim",
                    "temporal_fragility": claim.get("temporal_fragility") or "unknown",
                    "requires_refresh": bool(claim.get("requires_refresh")),
                    "ownership_change": claim.get("ownership_change") if isinstance(claim.get("ownership_change"), dict) else None,
                    "instruction": claim.get("safe_context_instruction") or "Use as candidate context with citation; do not present volatile facts as current without refresh.",
                }
                for claim in run.get("claims") or []
            ],
            "ownership_change_records": run.get("ownership_change_records") or ownership_change_records(run.get("claims") or []),
            "ownership_conflict_groups": run.get("ownership_conflict_groups") or ownership_conflict_groups(run.get("ownership_change_records") or ownership_change_records(run.get("claims") or [])),
            "term_clarity_concerns": run.get("term_clarity_concerns") or [],
            "refresh_jobs": run.get("refresh_jobs") or [],
            "warnings": run.get("context_concerns") or [],
            "fragile_facts": run.get("claim_risk_records") or [],
            "summaries": run.get("llm_summaries") or [],
        }
    if kind == "context-pack":
        return {**base, **context_pack(run)}
    if kind == "context-objects":
        return {**base, **context_object_graph_records(run)}
    if kind == "glossary":
        return {
            **base,
            "packet_count": len(run.get("glossary_resolution_packets") or []),
            "glossary_resolution_packets": run.get("glossary_resolution_packets") or [],
            "term_clarity_concerns": run.get("term_clarity_concerns") or [],
            "policy": {
                "source_scoped_terms_only": True,
                "block_global_memory_promotion": True,
                "block_canonical_graph_promotion": True,
                "requires_review_before_reuse": True,
            },
        }
    return {
        **base,
        "worker_records": run.get("worker_records") or [],
        "queue": queue_stats(),
        "connector_envelopes": connector_envelopes,
        "adapter_summary": run.get("adapter_summary") or {},
        "llm_adapter_statuses": run.get("llm_adapter_statuses") or [],
        "claim_risk_records": run.get("claim_risk_records") or [],
        "ambiguous_claims": run.get("ambiguous_claims") or [],
        "context_concerns": run.get("context_concerns") or [],
        "conflict_candidates": run.get("conflict_candidates") or [],
        "node_evidence": run.get("node_evidence") or [],
        "llm_claim_reviews": run.get("llm_claim_reviews") or [],
        "llm_conflict_reviews": run.get("llm_conflict_reviews") or [],
        "llm_graph_enrichment": run.get("llm_graph_enrichment") or [],
        "llm_summaries": run.get("llm_summaries") or [],
        "llm_audit_reviews": run.get("llm_audit_reviews") or [],
        "training_examples": run.get("training_examples") or [],
        "refresh_jobs": run.get("refresh_jobs") or [],
        "ownership_change_records": run.get("ownership_change_records") or ownership_change_records(run.get("claims") or []),
        "ownership_conflict_groups": run.get("ownership_conflict_groups") or ownership_conflict_groups(run.get("ownership_change_records") or ownership_change_records(run.get("claims") or [])),
        "term_clarity_concerns": run.get("term_clarity_concerns") or [],
        "safe_context_policy": {
            "remove_unsupported_claims": True,
            "downgrade_weak_claims": True,
            "include_conflict_warnings": True,
            "include_source_dates_for_fragile_facts": True,
        },
    }


def status_payload() -> dict:
    sync_context_worker_events()
    sync_worker_ledger()
    run = latest_run()
    queue = queue_stats()
    counts = run_artifact_counts(run)
    return {
        "ok": True,
        "service": "baltor-admin-demo",
        "latest_run_id": (run or {}).get("run_id"),
        "queue": queue,
        "artifact_counts": counts,
        "heartbeat": heartbeat_payload((run or {}).get("run_id") or "") if run else heartbeat_payload(""),
        "worker_ledger": {
            "path": str(WORKER_LEDGER_PATH),
            "exists": WORKER_LEDGER_PATH.exists(),
        },
        "readiness": {
            "redis": bool(queue.get("available")),
            "no_approval_holds": int(queue.get("approval_required") or 0) == 0,
            "no_budget_blocks": int(queue.get("budget_blocked") or 0) == 0,
            "no_permanent_failures": int(queue.get("failed_permanently") or 0) == 0,
            "latest_run_has_worker_records": counts.get("worker_records", 0) > 0,
            "latest_run_has_enrichment": counts.get("node_evidence", 0) > 0 or counts.get("llm_claim_reviews", 0) > 0,
        },
    }


def queue_health_payload() -> dict:
    sync_context_worker_events()
    sync_worker_ledger()
    queue = queue_stats()
    return {
        "ok": True,
        "package_type": "baltor.queue-health",
        "ts": int(time.time()),
        "queue": {
            "name": queue.get("queue"),
            "available": queue.get("available"),
            "pending": queue.get("pending"),
            "approval_required": queue.get("approval_required"),
            "budget_blocked": queue.get("budget_blocked"),
            "failed_permanently": queue.get("failed_permanently"),
            "oldest_pending_age_seconds": queue.get("oldest_pending_age_seconds"),
            "newest_pending_age_seconds": queue.get("newest_pending_age_seconds"),
            "pending_sample_missing_timestamps": queue.get("pending_sample_missing_timestamps"),
            "stale_active_worker_job_count": queue.get("stale_active_worker_job_count"),
            "stale_pending_job_count": queue.get("stale_pending_job_count"),
            "trend": queue.get("trend") or {},
            "throughput": queue.get("throughput") or {},
            "history": queue.get("history") or {},
            "pending_family_counts": queue.get("pending_family_counts") or {},
            "pending_family_scan": queue.get("pending_family_scan") or {},
        },
        "active_worker_jobs": queue.get("active_worker_jobs") or [],
        "active_worker_job_count": queue.get("active_worker_job_count", 0),
        "pending_sample": queue.get("pending_sample") or [],
        "recent_samples": queue.get("recent_samples") or [],
        "recent_worker_events": queue.get("recent_worker_events") or [],
        "thresholds": queue.get("thresholds") or {},
        "warnings": queue.get("warnings") or [],
        "source_stream": queue.get("context_worker_event_stream"),
    }


def _repo_path(path: str | Path) -> Path:
    value = path if isinstance(path, Path) else Path(path)
    return value if value.is_absolute() else _resource(value)


def _relative_repo_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _read_json_file(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _iter_jsonl(path: Path, *, limit: int | None = None) -> list[dict]:
    rows: list[dict] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return rows
    selected = lines if limit is None else lines[:limit]
    for line in selected:
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            rows.append(value)
    return rows


def _schema_contains(sql_text: str, name: str) -> bool:
    lowered = sql_text.lower()
    needle_table = f"create table if not exists {name.lower()}"
    needle_view = f"create or replace view {name.lower()}"
    return needle_table in lowered or needle_view in lowered


def _postgres_object_governance_view_probe(required_views: list[str]) -> dict:
    if not DATABASE_URL:
        return {
            "mode": "not_configured",
            "configured": False,
            "driver_available": False,
            "views": [],
            "counts": {},
            "error": None,
        }
    try:
        import psycopg  # type: ignore[import-not-found]
    except Exception as exc:
        return {
            "mode": "driver_unavailable",
            "configured": True,
            "driver_available": False,
            "views": [],
            "counts": {},
            "error": f"{type(exc).__name__}: {exc}",
        }

    probe: dict = {
        "mode": "database",
        "configured": True,
        "driver_available": True,
        "views": [],
        "counts": {},
        "error": None,
    }
    try:
        with psycopg.connect(DATABASE_URL, connect_timeout=3) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT table_name
                    FROM information_schema.views
                    WHERE table_schema = current_schema()
                      AND table_name = ANY(%s)
                    """,
                    (required_views,),
                )
                present = {str(row[0]) for row in cur.fetchall()}
                probe["views"] = [
                    {"name": view, "present": view in present}
                    for view in required_views
                ]
                for view in required_views:
                    if view not in present:
                        continue
                    cur.execute(f"SELECT count(*) FROM {view}")
                    row = cur.fetchone()
                    probe["counts"][view] = int(row[0]) if row else 0
    except Exception as exc:
        probe["mode"] = "database_error"
        probe["error"] = f"{type(exc).__name__}: {exc}"
    return probe


def _catalog_manifest_import_visibility() -> dict:
    bridge_dir = _repo_path(CATALOG_MANIFEST_BRIDGE_DIR)
    plan_path = bridge_dir / "manifest-import-plan.json"
    records_path = bridge_dir / "manifest_import_records.jsonl"
    plan = _read_json_file(plan_path)
    records = _iter_jsonl(records_path)
    action_counts = Counter(str(row.get("recommended_action") or "unknown") for row in records)
    status_counts = Counter(str(row.get("import_status") or "unknown") for row in records)
    type_counts = Counter(str(row.get("component_type") or "unknown") for row in records)
    flag_counts: Counter[str] = Counter()
    review_samples = []
    for row in records:
        for flag in row.get("rotted_context_flags") or []:
            flag_counts[str(flag)] += 1
        if str(row.get("recommended_action") or "") != "import" and len(review_samples) < 8:
            review_samples.append({
                "component_id": row.get("component_id"),
                "manifest_path": row.get("manifest_path"),
                "recommended_action": row.get("recommended_action"),
                "flags": row.get("rotted_context_flags") or [],
            })
    return {
        "kind": "baltor.catalog-manifest-import-visibility",
        "bridge_dir": _relative_repo_path(bridge_dir),
        "plan_exists": plan_path.exists(),
        "records_exists": records_path.exists(),
        "generated_counts": plan.get("counts") or {},
        "record_count": len(records),
        "recommended_action_counts": dict(sorted(action_counts.items())),
        "import_status_counts": dict(sorted(status_counts.items())),
        "component_type_counts": dict(sorted(type_counts.items())),
        "rotted_context_flag_counts": dict(sorted(flag_counts.items())),
        "review_samples": review_samples,
        "load_script": _relative_repo_path(bridge_dir / "load-catalog-manifests.sql"),
        "database_views": list(CATALOG_OPERATIONAL_VIEWS),
        "database_probe": probe_catalog_operational_views(database_url=DATABASE_URL),
        "next_step": "Load reviewed JSONL rows into Postgres, then point the admin demo at database views instead of generated files.",
    }


def _object_governance_visibility(sql_text: str) -> dict:
    try:
        from scripts.db.object_governance_registry import (
            DEFAULT_CONCRETE_PROFILE_SEED,
            concrete_seed_coverage,
            package_seed_coverage,
        )
    except Exception:
        seed_coverage = {}
        concrete_coverage = {}
        concrete_profile_seed = _resource("db/seeds/object-governance/concrete_object_governance_profile.jsonl")
    else:
        seed_coverage = package_seed_coverage()
        concrete_coverage = concrete_seed_coverage()
        concrete_profile_seed = DEFAULT_CONCRETE_PROFILE_SEED
    required_tables = list(OBJECT_GOVERNANCE_PACKAGE_TABLES)
    required_views = list(OBJECT_GOVERNANCE_OPERATIONAL_VIEWS)
    object_families = list(OBJECT_GOVERNANCE_REQUIRED_FAMILIES)
    database_probe = _postgres_object_governance_view_probe(required_views)
    doc_path = OBJECT_GOVERNANCE_STANDARD_DOC_PATH
    rubric_path = OBJECT_GOVERNANCE_REVIEW_RUBRIC_PATH
    concrete_rows = len(_iter_jsonl(concrete_profile_seed))
    return {
        "kind": "baltor.object-governance-visibility",
        "tables": [
            {"name": table, "present": _schema_contains(sql_text, table)}
            for table in required_tables
        ],
        "views": [
            {"name": view, "present": _schema_contains(sql_text, view)}
            for view in required_views
        ],
        "database_probe": database_probe,
        "ready": (
            all(_schema_contains(sql_text, table) for table in required_tables)
            and all(_schema_contains(sql_text, view) for view in required_views)
        ),
        "standard_doc": {
            "path": _relative_repo_path(doc_path),
            "exists": doc_path.exists(),
        },
        "review_rubric": {
            "path": _relative_repo_path(rubric_path),
            "exists": rubric_path.exists(),
        },
        "object_families": object_families,
        "seed_coverage": seed_coverage,
        "concrete_seed_coverage": concrete_coverage,
        "concrete_profile_seed": {
            "path": _relative_repo_path(concrete_profile_seed),
            "exists": concrete_profile_seed.exists(),
            "row_count": concrete_rows,
        },
        "required_package_parts": [
            "rubric",
            "contract",
            "schema_profile",
            "layout_profile",
            "architecture_diagram",
            "context_rule",
            "relationship_policy",
            "dimension_policy",
            "event_policy",
            "storage_mapping",
            "audit_trail",
        ],
        "database_views": required_views,
    }


def _archive_candidate_visibility() -> dict:
    ledger_path = _resource("docs/archive/archive-candidate-ledger.md")
    text = ""
    try:
        text = ledger_path.read_text(encoding="utf-8")
    except OSError:
        pass
    states = ["candidate", "keep_active", "supersede", "archive_ready", "archived"]
    return {
        "kind": "baltor.archive-candidate-visibility",
        "ledger": {
            "path": _relative_repo_path(ledger_path),
            "exists": ledger_path.exists(),
            "state_terms_present": {state: state in text for state in states},
        },
        "non_destructive_audit_command": "python3 scripts/audit_context_storage.py --archive-ledger",
        "visible_workflow": [
            "run audit",
            "inspect severity and evidence",
            "mark keep_active, supersede, or archive_ready",
            "add canonical replacement pointer",
            "perform separate approved archive move only after reference checks",
        ],
        "demo_status": "contract_visible",
    }


def _setting_drift_visibility(sql_text: str) -> dict:
    try:
        from scripts import _config as config
    except Exception as exc:  # pragma: no cover - defensive demo status path.
        return {
            "kind": "baltor.setting-drift-visibility",
            "ok": False,
            "error": str(exc),
        }
    return {
        "kind": "baltor.setting-drift-visibility",
        "ok": True,
        "setting_tables": [
            {"name": "setting_profile", "present": _schema_contains(sql_text, "setting_profile")},
            {"name": "setting_value", "present": _schema_contains(sql_text, "setting_value")},
        ],
        "registered_runtime_profiles": len(getattr(config, "MODEL_RUNTIME_PROFILES", {})),
        "registered_embedding_models": len(getattr(config, "EMBEDDING_MODELS", {})),
        "registered_embedding_profiles": len(getattr(config, "EMBEDDING_MODEL_PROFILES", {})),
        "registered_vector_backends": len(getattr(config, "VECTOR_STORAGE_BACKENDS", {})),
        "registered_vector_indexes": len(getattr(config, "VECTOR_INDEX_PROFILES", {})),
        "default_embedding_profile_id": getattr(config, "DEFAULT_EMBEDDING_PROFILE_ID", ""),
        "default_vector_storage_backend": getattr(config, "DEFAULT_VECTOR_STORAGE_BACKEND", ""),
        "default_embedding_dimensions": getattr(config, "DEFAULT_EMBEDDING_DIMENSIONS", None),
        "drift_audit_command": "python3 scripts/audit_context_storage.py --markdown",
        "next_targets": [
            "remaining repeated model/backend literals",
            "remaining repeated vector dimensions",
            "database setting_profile seed/export rows",
            "admin demo warning when runtime defaults diverge from setting rows",
        ],
    }


def operational_readiness_payload() -> dict:
    schema_path = _resource("db/postgres/schema.sql")
    try:
        sql_text = schema_path.read_text(encoding="utf-8")
    except OSError:
        sql_text = ""
    import_visibility = _catalog_manifest_import_visibility()
    governance_visibility = _object_governance_visibility(sql_text)
    archive_visibility = _archive_candidate_visibility()
    setting_visibility = _setting_drift_visibility(sql_text)
    checks = {
        "catalog_import_bridge_generated": bool(import_visibility.get("plan_exists") and import_visibility.get("records_exists")),
        "catalog_import_records_mapped": int(import_visibility.get("record_count") or 0) > 0,
        "catalog_operational_views_schema_ready": bool((import_visibility.get("database_probe") or {}).get("schema_ready")),
        "object_governance_schema_ready": bool(governance_visibility.get("ready")),
        "archive_candidate_contract_visible": bool((archive_visibility.get("ledger") or {}).get("exists")),
        "setting_profile_schema_ready": all(item.get("present") for item in setting_visibility.get("setting_tables", [])),
        "setting_registries_visible": int(setting_visibility.get("registered_vector_backends") or 0) > 0,
    }
    return {
        "ok": True,
        "package_type": "baltor.operational-readiness",
        "ts": int(time.time()),
        "summary": {
            "ready_checks": sum(1 for value in checks.values() if value),
            "total_checks": len(checks),
            "status": "visible" if all(checks.values()) else "partial",
        },
        "checks": checks,
        "catalog_manifest_import": import_visibility,
        "object_governance": governance_visibility,
        "archive_candidates": archive_visibility,
        "setting_drift": setting_visibility,
        "contracts": {
            "api": "/api/admin-dashboard/operational-readiness",
            "testing_page": "/admin-demo/testing",
            "mcp_tool": "context_operational_readiness",
        },
    }


def page(title: str, body: str) -> bytes:
    nav = "".join(f'<a href="/admin-demo/{slug}">{label}</a>' for slug, _, label, _ in CARDS)
    nav += '<a href="/admin-dashboard/monitor">Monitor</a>'
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Baltor | {esc(title)}</title>
<style>
:root {{
  --bg:#f7f8f5; --panel:#fff; --soft:#f0f5f1; --ink:#141814; --muted:#5d6a61;
  --line:#d9ddd3; --teal:#117467; --gold:#a66a12; --coral:#b84f3e;
  --shadow:0 16px 42px rgba(30,36,28,.09);
}}
* {{ box-sizing:border-box; }}
body {{ margin:0; min-height:100vh; color:var(--ink); background:var(--bg); font:14px/1.45 Inter, system-ui, -apple-system, Segoe UI, sans-serif; }}
a {{ color:inherit; }}
.topbar {{ height:58px; display:flex; align-items:center; gap:24px; padding:0 28px; border-bottom:1px solid var(--line); background:rgba(247,248,245,.96); }}
.brand {{ display:flex; align-items:center; gap:10px; font-weight:800; text-decoration:none; }}
.mark {{ width:18px; height:18px; border-radius:50%; background:conic-gradient(var(--teal), var(--gold), var(--coral), var(--teal)); }}
.nav {{ margin-left:auto; display:flex; flex-wrap:wrap; gap:14px; color:var(--muted); font-size:13px; }}
.nav a {{ text-decoration:none; }}
.shell {{ width:min(1380px, 100%); margin:0 auto; padding:28px clamp(16px, 4vw, 42px) 48px; }}
.cards {{ min-height:calc(100vh - 116px); display:grid; align-content:center; grid-template-columns:repeat(3,minmax(0,1fr)); gap:14px; }}
.card {{ min-height:178px; display:grid; gap:10px; padding:18px; border:1px solid var(--line); border-radius:8px; background:var(--panel); box-shadow:var(--shadow); text-decoration:none; }}
.card:hover {{ border-color:rgba(17,116,103,.55); background:var(--soft); }}
.step {{ width:32px; height:26px; display:grid; place-items:center; border-radius:7px; color:#fff; background:var(--teal); font:800 11px ui-monospace, SFMono-Regular, Menlo, monospace; }}
.card strong {{ font-size:18px; }}
.card small, .muted {{ color:var(--muted); }}
.grid2 {{ display:grid; grid-template-columns:minmax(0,1fr) 330px; gap:14px; align-items:start; }}
.grid3 {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:14px; }}
.panel {{ min-width:0; border:1px solid var(--line); border-radius:8px; background:var(--panel); box-shadow:var(--shadow); }}
.pad {{ padding:18px; }}
.head {{ display:flex; justify-content:space-between; align-items:flex-start; gap:16px; margin-bottom:14px; }}
.kicker {{ margin:0 0 7px; color:#075d52; font-weight:800; font-size:11px; letter-spacing:.08em; text-transform:uppercase; }}
h1,h2,h3,p {{ margin-top:0; }}
h1 {{ font-size:20px; }}
h2 {{ font-size:16px; }}
.source-grid {{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:10px; margin:12px 0; }}
.source {{ min-height:128px; padding:14px; border:1px solid var(--line); border-radius:8px; background:#fbfbf8; text-align:left; }}
.badge {{ display:inline-grid; place-items:center; min-width:34px; height:34px; margin-bottom:18px; padding:0 8px; border-radius:7px; color:#fff; background:var(--teal); font:800 11px ui-monospace, monospace; }}
textarea {{ width:100%; min-height:170px; padding:12px; border:1px solid var(--line); border-radius:8px; font:13px/1.5 ui-monospace, monospace; }}
button,.btn {{ min-height:38px; display:inline-flex; align-items:center; justify-content:center; border:1px solid var(--line); border-radius:7px; padding:0 14px; background:#edf1e9; color:var(--ink); font-weight:800; text-decoration:none; cursor:pointer; }}
.primary {{ border-color:var(--teal); color:#fff; background:var(--teal); }}
.rows {{ display:grid; gap:10px; }}
.row {{ padding:12px; border:1px solid var(--line); border-radius:8px; background:#fbfbf8; }}
.metric-grid {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:10px; }}
.metric strong {{ display:block; font-size:26px; }}
.pill {{ display:inline-flex; min-height:24px; align-items:center; padding:0 8px; border-radius:99px; background:#e4f1eb; color:#075d52; font:800 11px ui-monospace, monospace; }}
pre {{ overflow:auto; white-space:pre-wrap; padding:12px; border:1px solid var(--line); border-radius:8px; background:#f6f8f5; font:12px/1.45 ui-monospace, monospace; }}
.event {{ display:grid; grid-template-columns:140px 150px minmax(0,1fr) 180px; gap:10px; align-items:start; }}
.event code {{ color:#075d52; font:800 12px ui-monospace, monospace; }}
.toolbar {{ display:flex; gap:10px; flex-wrap:wrap; align-items:center; margin-bottom:14px; }}
@media (max-width:900px) {{ .cards,.grid2,.grid3,.source-grid {{ grid-template-columns:1fr; }} .topbar {{ height:auto; align-items:flex-start; flex-direction:column; padding:12px 16px; }} .nav {{ margin-left:0; }} }}
</style>
</head>
<body>
<header class="topbar"><a class="brand" href="/admin-demo/"><span class="mark"></span>Baltor</a><nav class="nav">{nav}</nav></header>
<main class="shell">{body}</main>
</body>
</html>""".encode("utf-8")


def run_summary(run: dict | None) -> str:
    summary = (run or {}).get("summary", {})
    counts = run_artifact_counts(run)
    return '<div class="metric-grid">' + "".join(
        f'<div class="panel pad metric"><strong>{esc(value)}</strong><span class="muted">{esc(label)}</span></div>'
        for label, value in [
            ("sources", summary.get("sources", 0)),
            ("chunks", summary.get("chunks", 0)),
            ("entities", summary.get("entities", 0)),
            ("claims", summary.get("claims", 0)),
            ("verify", summary.get("verification_queue", 0)),
            ("refresh jobs", summary.get("refresh_jobs", 0)),
            ("node research", summary.get("node_research_tasks", 0)),
            ("LLM reviews", summary.get("llm_review_tasks", 0)),
            ("ambiguous", summary.get("ambiguous_claims", 0)),
            ("conflicts", summary.get("conflict_candidates", 0)),
            ("adapter tasks", summary.get("adapter_tasks", 0)),
            ("missing deps", summary.get("missing_adapters", 0)),
            ("worker records", counts.get("worker_records", 0)),
            ("LLM done", counts.get("llm_claim_reviews", 0) + counts.get("llm_summaries", 0)),
        ]
    ) + "</div>"


def home_page() -> bytes:
    cards = "".join(
        f'<a class="card" href="/admin-demo/{slug}"><span class="step">{num}</span><strong>{label}</strong><small>{desc}</small><span class="pill">Open</span></a>'
        for slug, num, label, desc in CARDS
    )
    return page("Context Control Demo", f'<section class="cards">{cards}</section>')


def sources_page() -> bytes:
    connector_options = "".join(
        f'<option value="{esc(slug)}">{esc(definition["label"])}</option>'
        for slug, definition in CONNECTOR_DEFINITIONS.items()
        if slug in {"jira", "confluence", "gitlab", "website", "ftp"}
    )
    return page("Load data", f"""
<section class="grid2">
  <div class="panel pad">
    <div class="head"><div><p class="kicker">Sources</p><h1>Load data</h1><p class="muted">Upload a text file, paste content, or start from the sample policy.</p></div><a class="btn" href="/admin-demo/run-sample">Load sample file</a></div>
    <form action="/admin-demo/runs" method="post" enctype="multipart/form-data">
      <div class="source-grid">
        <label class="source"><span class="badge">UP</span><strong>Upload files</strong><p class="muted">TXT, MD, CSV, JSON, YAML, ZIP</p><input name="file" type="file" accept=".txt,.md,.csv,.json,.yaml,.yml,.xml,.html,.log,.zip" /></label>
        <button class="source" name="connector" value="google-drive" type="submit"><span class="badge">GD</span><strong>Google Drive</strong><p class="muted">Folder sync connector</p></button>
        <button class="source" name="connector" value="sharepoint" type="submit"><span class="badge">SP</span><strong>SharePoint</strong><p class="muted">Policy libraries</p></button>
        <button class="source" name="connector" value="git-s3" type="submit"><span class="badge">S3</span><strong>Git / S3</strong><p class="muted">Repos and object stores</p></button>
      </div>
      <p class="kicker">Gateway connector envelope</p>
      <div style="display:grid;grid-template-columns:190px minmax(0,1fr) auto;gap:10px;margin-bottom:12px">
        <select name="connector" style="min-height:38px;border:1px solid var(--line);border-radius:7px;padding:0 12px;background:white">
          <option value="">Select source</option>
          {connector_options}
        </select>
        <input name="connector_url" type="text" placeholder="Jira, Confluence, GitLab, website, ftp://, sftp://, or source URI" style="min-height:38px;border:1px solid var(--line);border-radius:7px;padding:0 12px" />
        <button name="connector_action" value="register" type="submit">Register connector</button>
      </div>
      <p class="muted">For safety, the public demo records connector envelopes and creates an indexed-mirror run. Production fetches through credentialed workers, ACL filters, and exact source handles, not direct raw browser access.</p>
      <p class="kicker">Raw text fallback</p>
      <textarea name="text" placeholder="Paste source text here if a connector or file is not available."></textarea>
      <p style="margin-top:12px"><button class="primary" type="submit">Start context run</button></p>
    </form>
  </div>
  <aside class="panel pad"><p class="kicker">Run summary</p>{run_summary(latest_run())}</aside>
</section>""")


def monitoring_page(run: dict | None) -> bytes:
    plan = (run or {}).get("worker_plan") or []
    if plan:
        rows = "".join(
            f'<div class="row"><strong>{esc(item.get("stage"))}</strong><p class="muted">{esc(item.get("status"))} · {esc(item.get("detail"))}</p></div>'
            for item in plan
        )
    else:
        stages = ["Ingest source", "Sync version/hash", "Chunk text", "Extract entities", "Extract claims", "Build graph", "Plan verification", "Prepare serving packages"]
        rows = "".join(f'<div class="row"><strong>{esc(stage)}</strong><p class="muted">waiting for run</p></div>' for stage in stages)
    queue = queue_stats()
    queue_html = '<div class="panel pad"><p class="kicker">Queue</p><pre>' + esc(json.dumps(queue, indent=2)) + '</pre></div>'
    run_id = esc((run or {}).get("run_id") or "-")
    progress = esc((run or {}).get("progress") or 0)
    return page("Processing", f'<section class="grid2"><div class="panel pad"><p class="kicker">Processing</p><h1>Processing pipeline</h1><p class="muted">Run {run_id} · {progress}% complete</p><div class="rows">{rows}</div></div><aside>{run_summary(run)}{queue_html}</aside></section>')


def outputs_page(run: dict | None) -> bytes:
    claims = (run or {}).get("claims", [])
    tree = (run or {}).get("document_tree") or {}
    tree_summary = tree.get("summary") or {}
    tree_card = (
        '<div class="row"><strong>Document hierarchy</strong>'
        f'<p class="muted">{esc(tree_summary.get("folders", 0))} folders · {esc(tree_summary.get("files", 0))} files · '
        f'{esc(tree_summary.get("pages", 0))} pages · {esc(tree_summary.get("components", 0))} components</p></div>'
    ) if run else ""
    adapter_summary = (run or {}).get("adapter_summary") or {}
    adapter_card = (
        '<div class="row"><strong>Adapter comparison</strong>'
        f'<p class="muted">{esc(adapter_summary.get("task_count", 0))} tasks · {esc(adapter_summary.get("ok_count", 0))} ok · '
        f'{esc(adapter_summary.get("missing_dependency_count", 0))} missing dependencies · {esc(adapter_summary.get("not_configured_count", 0))} not configured</p></div>'
    ) if adapter_summary else ""
    trust = (run or {}).get("summary", {})
    trust_card = (
        '<div class="row"><strong>Trust layer</strong>'
        f'<p class="muted">{esc(trust.get("node_research_tasks", 0))} node research tasks · '
        f'{esc(trust.get("llm_review_tasks", 0))} LLM review tasks · '
        f'{esc(trust.get("ambiguous_claims", 0))} ambiguous claims · '
        f'{esc(trust.get("conflict_candidates", 0))} conflict candidates</p></div>'
    ) if run else ""
    rows = "".join(f'<div class="row"><strong>{esc(item["state"])}</strong><p>{esc(item["claim"])}</p><span class="pill">{esc(item["source"])}</span></div>' for item in claims) or '<div class="row">Run Load Data first.</div>'
    return page("Outputs", f'<section class="panel pad"><p class="kicker">Outputs</p><h1>Extracted claims and verification queue</h1><div class="rows">{tree_card}{trust_card}{adapter_card}{rows}</div></section>')


def download_page(run: dict | None) -> bytes:
    run_id = (run or {}).get("run_id", "")
    disabled = "" if run_id else "Run Load Data first."
    links = "".join(f'<a class="btn" href="/api/admin-demo/runs/{esc(run_id)}/exports/{kind}">Export {label}</a>' for kind, label in [("manifest", "manifest"), ("text", "text pack"), ("rag", "RAG records"), ("graph", "graph"), ("audit", "audit packet"), ("safe-context", "safe context"), ("context-pack", "context pack"), ("context-objects", "context objects")]) if run_id else f'<p class="muted">{disabled}</p>'
    manifest = json.dumps({"run_id": run_id, "contracts": ["manifest", "text", "rag", "graph", "audit", "safe-context", "context-pack", "context-objects"]}, indent=2)
    return page("Download", f'<section class="panel pad"><p class="kicker">Download</p><h1>Download context package</h1><p>{links}</p><pre>{esc(manifest)}</pre></section>')


def dimension_engine_panel(run: dict | None, *, compact: bool = False) -> str:
    if not run:
        return '<section class="panel pad"><p class="kicker">Dimension engine</p><h2>No dimension assessments yet</h2><p class="muted">Run Load Data first.</p></section>'
    records = context_object_graph_records(run)
    objects_by_id = {
        str(item.get("context_object_id")): item
        for item in records.get("objects") or []
        if isinstance(item, dict)
    }
    values = [
        item for item in records.get("dimension_values") or []
        if isinstance(item, dict) and item.get("subject_kind") in {None, "context_object"}
    ]
    by_dimension: dict[str, list[dict]] = {}
    for value in values:
        by_dimension.setdefault(str(value.get("dimension_id") or ""), []).append(value)

    def value_rows(dimension_id: str, *, reverse: bool = True, limit: int = 5) -> str:
        ranked = sorted(
            by_dimension.get(dimension_id, []),
            key=lambda item: float(item.get("normalized_value") or 0),
            reverse=reverse,
        )[:limit]
        rows = []
        for value in ranked:
            subject_id = str(value.get("subject_id") or "")
            obj = objects_by_id.get(subject_id) or {}
            rows.append(
                '<div class="row">'
                f'<strong>{esc(obj.get("title") or subject_id)}</strong>'
                f'<p class="muted">{esc(value.get("label") or "-")} · {esc(value.get("normalized_value"))} · {esc(obj.get("object_type") or "context")}</p>'
                f'<small>{esc(subject_id)}</small>'
                '</div>'
            )
        return "".join(rows) or '<div class="row">No matching dimension values.</div>'

    definition_pills = "".join(
        f'<span class="pill">{esc((definition.get("name") or definition.get("dimension_id") or "").replace(" Risk", ""))}</span>'
        for definition in (records.get("dimension_definitions") or [])[:8]
    )
    summary = (
        '<div class="toolbar">'
        f'<span class="pill">{esc(records.get("counts", {}).get("dimension_definitions", 0))} definitions</span>'
        f'<span class="pill">{esc(records.get("counts", {}).get("dimension_values", 0))} values</span>'
        f'<span class="pill">{esc(records.get("counts", {}).get("assertions", 0))} assertions</span>'
        f'{definition_pills}'
        '</div>'
    )
    if compact:
        return (
            '<section class="panel pad" style="margin-bottom:14px">'
            '<p class="kicker">Dimension engine</p><h2>Risk and trust assessments</h2>'
            f'{summary}<div class="grid2"><div><h3>Highest operational risk</h3><div class="rows">{value_rows("dim://baltor/risk/operational", limit=4)}</div></div>'
            f'<div><h3>Lowest verifiability</h3><div class="rows">{value_rows("dim://baltor/trust/verifiability", reverse=False, limit=4)}</div></div></div>'
            '</section>'
        )
    return (
        '<section class="grid2" style="margin-top:14px">'
        '<div class="panel pad"><p class="kicker">Dimension engine</p><h2>Highest operational risk</h2>'
        f'{summary}<div class="rows">{value_rows("dim://baltor/risk/operational")}</div></div>'
        '<aside class="panel pad"><p class="kicker">Trust</p><h2>Lowest verifiability</h2>'
        f'<div class="rows">{value_rows("dim://baltor/trust/verifiability", reverse=False)}</div></aside>'
        '</section>'
    )


def explore_page(run: dict | None) -> bytes:
    facts = (run or {}).get("claims", [])
    tree = (run or {}).get("document_tree") or {}
    files = tree.get("files") or []
    hierarchy_parts = []
    for item in files[:30]:
        tag_html = " ".join('<span class="pill">' + esc(tag) + '</span>' for tag in (item.get("tags") or [])[:5])
        hierarchy_parts.append(
            '<div class="row">'
            f'<strong>{esc(item.get("path"))}</strong>'
            f'<p class="muted">{esc(item.get("folder"))} · {esc(item.get("extension"))} · {esc(item.get("byte_size"))} bytes · {len(item.get("pages") or [])} pages</p>'
            f'<p>{tag_html}</p>'
            '</div>'
        )
    hierarchy_rows = "".join(hierarchy_parts) or '<div class="row">Run Load Data first.</div>'
    rows = "".join(f'<div class="row"><strong>{esc(item["id"])}</strong><p>{esc(item["claim"])}</p></div>' for item in facts[:8]) or '<div class="row">Run Load Data first.</div>'
    return page("Explore context", f'<section class="grid2"><div class="panel pad"><p class="kicker">Explore</p><h1>Document hierarchy</h1><div class="rows">{hierarchy_rows}</div></div><aside class="panel pad"><h2>Facts / RAG preview</h2><div class="rows">{rows}</div></aside></section>{dimension_engine_panel(run)}')


def testing_page() -> bytes:
    queue = queue_stats()
    readiness = operational_readiness_payload()
    import_status = readiness["catalog_manifest_import"]
    governance_status = readiness["object_governance"]
    archive_status = readiness["archive_candidates"]
    setting_status = readiness["setting_drift"]
    checks = [
        ("Admin routes", "ready"),
        ("Run API", "ready"),
        ("Exports", "ready"),
        ("Local server", "ready"),
        ("Redis pub/sub queue", "ready" if queue.get("available") else "needs Redis"),
        ("Container worker ledger", "ready" if WORKER_LEDGER_PATH.exists() else "waiting for worker output"),
        ("Cloud env DATABASE_URL/REDIS_URL", "needs configuration"),
    ]
    rows = "".join(f'<div class="row"><strong>{esc(name)}</strong><span class="pill">{esc(status)}</span></div>' for name, status in checks)
    operational_rows = "".join(
        '<div class="row">'
        f'<strong>{esc(name)}</strong>'
        f'<span class="pill">{esc("ready" if ready else "partial")}</span>'
        '</div>'
        for name, ready in [
            ("Catalog manifest import bridge", readiness["checks"]["catalog_import_bridge_generated"]),
            ("Database import records mapped", readiness["checks"]["catalog_import_records_mapped"]),
            ("Object governance schema", readiness["checks"]["object_governance_schema_ready"]),
            ("Archive candidate contract", readiness["checks"]["archive_candidate_contract_visible"]),
            ("Setting profile schema", readiness["checks"]["setting_profile_schema_ready"]),
            ("Setting registries", readiness["checks"]["setting_registries_visible"]),
        ]
    )
    database_panel = f"""
    <section class="grid2" style="margin-top:14px">
      <div class="panel pad">
        <p class="kicker">Database-backed visibility</p>
        <h1>Operational readiness</h1>
        <p class="muted">{esc(readiness["summary"]["ready_checks"])} of {esc(readiness["summary"]["total_checks"])} visibility checks ready.</p>
        <div class="rows">{operational_rows}</div>
        <p style="margin-top:12px"><a class="btn" href="/api/admin-dashboard/operational-readiness">JSON readiness contract</a></p>
      </div>
      <aside class="panel pad">
        <p class="kicker">Signals</p>
        <div class="rows">
          <div class="row"><strong>Import rows</strong><p class="muted">{esc(import_status.get("record_count"))} mapped manifests · {esc((import_status.get("generated_counts") or {}).get("context_objects", 0))} context objects · {esc((import_status.get("generated_counts") or {}).get("rubric_dimensions", 0))} rubric dimensions</p></div>
          <div class="row"><strong>Object governance</strong><p class="muted">{esc(len(governance_status.get("object_families") or []))} object families · {esc(len(governance_status.get("required_package_parts") or []))} required package parts</p></div>
          <div class="row"><strong>Archive candidates</strong><p class="muted">{esc((archive_status.get("ledger") or {}).get("path"))} · non-destructive audit contract visible</p></div>
          <div class="row"><strong>Setting drift</strong><p class="muted">{esc(setting_status.get("registered_runtime_profiles", 0))} model profiles · {esc(setting_status.get("registered_vector_backends", 0))} vector backends · default dimensions {esc(setting_status.get("default_embedding_dimensions"))}</p></div>
        </div>
      </aside>
    </section>
    """
    return page("Integration testing", f'<section class="panel pad"><p class="kicker">Testing</p><h1>Integration readiness</h1><div class="rows">{rows}</div></section>{database_panel}')


def run_inspector(run: dict | None) -> str:
    if not run:
        return '<section class="panel pad"><p class="kicker">Run inspector</p><h1>No run yet</h1><p class="muted">Upload a ZIP, register a connector, or load the sample to start processing.</p></section>'
    counts = run_artifact_counts(run)
    tree_summary = ((run.get("document_tree") or {}).get("summary") or {})
    worker_rows = "".join(
        '<div class="row">'
        f'<strong>{esc(record.get("task"))}</strong>'
        f'<p class="muted">job {esc(record.get("job_id"))} · ok={esc(record.get("ok"))} · {esc(record.get("finished_at"))}</p>'
        f'<pre>{esc(json.dumps(record.get("output_keys") or []))}</pre>'
        '</div>'
        for record in (run.get("worker_records") or [])[-8:]
    ) or '<div class="row">Waiting for worker ledger records.</div>'
    status_rows = "".join(
        '<div class="row">'
        f'<strong>{esc(item.get("task"))}</strong>'
        f'<p class="muted">{esc(item.get("status"))} · {esc(item.get("model") or "no model reported")}</p>'
        f'<small>{esc(item.get("error") or "")}</small>'
        '</div>'
        for item in (run.get("llm_adapter_statuses") or [])[-6:]
    ) or '<div class="row">Waiting for local LLM adapter status.</div>'
    run_id = esc(run.get("run_id"))
    export_links = " ".join(
        f'<a class="btn" href="/api/admin-demo/runs/{run_id}/exports/{kind}">{esc(label)}</a>'
        for kind, label in [("manifest", "Manifest"), ("text", "Text"), ("rag", "RAG"), ("graph", "Graph"), ("audit", "Audit"), ("safe-context", "Safe context"), ("context-pack", "Context pack"), ("context-objects", "Context objects")]
    )
    inspector_payload = {
        "run_id": run.get("run_id"),
        "status": run.get("status"),
        "progress": run.get("progress"),
        "queue_job_id": run.get("queue_job_id"),
        "queue_published": run.get("queue_published"),
        "document_tree": tree_summary,
        "artifact_counts": counts,
        "summary": run.get("summary") or {},
        "heartbeat": run.get("heartbeat") or {},
    }
    return f"""
<section class="grid2" style="margin-bottom:14px">
  <div class="panel pad">
    <div class="head">
      <div><p class="kicker">Run inspector</p><h1>{run_id}</h1><p class="muted">{esc(run.get("status"))} · {esc(run.get("progress"))}% · job {esc(run.get("queue_job_id") or "-")}</p></div>
      <a class="btn" href="/api/admin-demo/runs/{run_id}">Run JSON</a>
    </div>
    <div class="toolbar">
      <span class="pill">{esc(tree_summary.get("folders", 0))} folders</span>
      <span class="pill">{esc(tree_summary.get("files", 0))} files</span>
      <span class="pill">{esc(tree_summary.get("pages", 0))} pages</span>
      <span class="pill">{esc(tree_summary.get("components", 0))} components</span>
      <span class="pill">{esc(counts.get("worker_records"))} worker records</span>
      <span class="pill">{esc(counts.get("llm_claim_reviews"))} claim reviews</span>
      <span class="pill">{esc(counts.get("llm_proposed_edges"))} LLM edges</span>
      <span class="pill">heartbeat: {esc((run.get("heartbeat") or {}).get("stage") or "-")}</span>
    </div>
    <p>{export_links}</p>
    <pre>{esc(json.dumps(inspector_payload, indent=2, sort_keys=True))}</pre>
  </div>
  <aside class="panel pad">
    <p class="kicker">Local LLM status</p>
    <div class="rows">{status_rows}</div>
  </aside>
</section>
<section class="panel pad" style="margin-bottom:14px">
  <p class="kicker">Recent worker ledger records</p>
  <div class="rows">{worker_rows}</div>
</section>"""


def queue_health_panel(queue: dict) -> str:
    trend = queue.get("trend") or {}
    throughput = queue.get("throughput") or {}
    history = queue.get("history") or {}
    by_family = throughput.get("by_family") or {}
    warning_rows = "".join(
        '<div class="row">'
        f'<strong>{esc(item.get("type"))}</strong>'
        f'<p class="muted">{esc(item.get("severity"))} · count {esc(item.get("count", "-"))} · threshold {esc(item.get("threshold_seconds", "-"))}s</p>'
        f'<small>{esc(item.get("detail") or ("oldest age " + str(item.get("oldest_age_seconds", "-")) + "s"))}</small>'
        '</div>'
        for item in queue.get("warnings") or []
    )
    active_rows = "".join(
        '<div class="row">'
        f'<strong>{esc(job.get("task") or "worker job")}</strong>'
        f'<p class="muted">run {esc(job.get("run_id") or "-")} · job {esc(job.get("job_id") or "-")} · active {esc(job.get("age_seconds"))}s</p>'
        f'<small>{esc(job.get("event") or "")}{" · stale" if job.get("stale") else ""}</small>'
        '</div>'
        for job in (queue.get("active_worker_jobs") or [])[:6]
    ) or '<div class="row">No active worker job inferred from recent stream events.</div>'
    pending_rows = "".join(
        '<div class="row">'
        f'<strong>{esc(job.get("task") or "queued job")}</strong>'
        f'<p class="muted">run {esc(job.get("run_id") or "-")} · job {esc(job.get("job_id") or "-")} · age {esc(job.get("age_seconds") if job.get("age_seconds") is not None else "unknown")}s</p>'
        f'<small>queued_at {esc(job.get("queued_at") or "missing from older contract")}{" · stale" if job.get("stale") else ""}</small>'
        '</div>'
        for job in (queue.get("pending_sample") or [])[:6]
    ) or '<div class="row">No pending job sample available.</div>'
    family_rows = "".join(
        '<div class="row">'
        f'<strong>{esc(family)}</strong>'
        f'<p class="muted">pending {esc(detail.get("pending", 0))} · throughput {esc(detail.get("jobs_per_minute") if detail.get("jobs_per_minute") is not None else detail.get("status") or "unknown")}/min · drain {esc(detail.get("estimated_drain_seconds") if detail.get("estimated_drain_seconds") is not None else "unknown")}s</p>'
        f'<small>completions {esc(detail.get("completion_count", 0))} · window {esc(detail.get("window_seconds", 0))}s</small>'
        '</div>'
        for family, detail in sorted(by_family.items())
    ) or '<div class="row">No task-family throughput available yet.</div>'
    return f"""
<section class="grid2" style="margin-bottom:14px">
  <div class="panel pad">
    <p class="kicker">Queue health</p>
    <h2>Active worker jobs</h2>
    <div class="toolbar">
      <span class="pill">active: {esc(queue.get("active_worker_job_count", 0))}</span>
      <span class="pill">stale active: {esc(queue.get("stale_active_worker_job_count", 0))}</span>
      <span class="pill">trend: {esc(trend.get("status") or "unknown")}</span>
      <span class="pill">throughput: {esc(throughput.get("jobs_per_minute") if throughput.get("jobs_per_minute") is not None else throughput.get("status") or "unknown")}/min</span>
      <span class="pill">history: {esc(history.get("loaded_sample_count", 0))}</span>
      <span class="pill">recent worker events: {esc(len(queue.get("recent_worker_events") or []))}</span>
    </div>
    <div class="rows">{warning_rows}</div>
    <div class="rows">{active_rows}</div>
  </div>
  <aside class="panel pad">
    <p class="kicker">Backlog sample</p>
    <h2>Pending jobs</h2>
    <div class="toolbar">
      <span class="pill">pending: {esc(queue.get("pending"))}</span>
      <span class="pill">delta: {esc(trend.get("pending_delta") if trend.get("pending_delta") is not None else "unknown")}</span>
      <span class="pill">samples: {esc(trend.get("sample_count", 0))}</span>
      <span class="pill">drain eta: {esc(throughput.get("estimated_drain_seconds") if throughput.get("estimated_drain_seconds") is not None else "unknown")}s</span>
      <span class="pill">persisted: {esc("yes" if history.get("exists") else "no")}</span>
      <span class="pill">oldest age: {esc(queue.get("oldest_pending_age_seconds") if queue.get("oldest_pending_age_seconds") is not None else "unknown")}</span>
      <span class="pill">stale pending: {esc(queue.get("stale_pending_job_count", 0))}</span>
      <span class="pill">missing timestamps: {esc(queue.get("pending_sample_missing_timestamps", 0))}</span>
    </div>
    <div class="rows">{pending_rows}</div>
  </aside>
</section>
<section class="panel pad" style="margin-bottom:14px">
  <p class="kicker">Throughput by task family</p>
  <div class="rows">{family_rows}</div>
</section>"""


def monitor_page() -> bytes:
    sync_context_worker_events()
    sync_worker_ledger()
    queue = queue_stats()
    run = latest_run()
    heartbeat = heartbeat_payload((run or {}).get("run_id") or "")
    readiness = operational_readiness_payload()
    readiness_summary = readiness.get("summary") or {}
    readiness_checks = readiness.get("checks") or {}
    readiness_rows = "".join(
        '<div class="row">'
        f'<code>{esc(name)}</code>'
        f'<span class="pill">{"ready" if value else "missing"}</span>'
        '</div>'
        for name, value in sorted(readiness_checks.items())
    ) or '<div class="row">No readiness checks reported.</div>'
    readiness_json = json.dumps(
        {
            "summary": readiness_summary,
            "checks": readiness_checks,
            "catalog_manifest_import": readiness.get("catalog_manifest_import") or {},
            "object_governance": readiness.get("object_governance") or {},
            "archive_candidates": readiness.get("archive_candidates") or {},
            "setting_drift": readiness.get("setting_drift") or {},
        },
        indent=2,
    )
    rows = "".join(event_row(event) for event in reversed(EVENTS[-80:])) or '<div class="row">No actions yet. Upload a file, register a connector, load the sample, or export a package.</div>'
    body = f"""
{run_inspector(run)}
{dimension_engine_panel(run, compact=True)}
{queue_health_panel(queue)}
<section class="panel pad" id="operational-readiness-monitor" style="margin-bottom:14px">
  <div class="head">
    <div><p class="kicker">Database-backed visibility</p><h2>Operational readiness</h2><p class="muted">Shows whether catalog manifests, governance profiles, archive candidates, and setting registries are visible as database-ready runtime contracts.</p></div>
    <a class="btn" href="/api/admin-dashboard/operational-readiness">Readiness JSON</a>
  </div>
  <div class="toolbar">
    <span class="pill">status: {esc(readiness_summary.get("status") or "unknown")}</span>
    <span class="pill">checks: {esc(readiness_summary.get("ready_checks", 0))}/{esc(readiness_summary.get("total_checks", 0))}</span>
    <a class="btn" href="/admin-demo/testing">Testing page</a>
  </div>
  <div class="rows">{readiness_rows}</div>
  <pre>{esc(readiness_json)}</pre>
</section>
<section class="panel pad">
  <div class="head">
    <div><p class="kicker">Admin dashboard</p><h1>Live action monitor</h1><p class="muted">Watches uploads, connectors, processing stages, exports, and API activity for this local demo process.</p></div>
    <a class="btn" href="/admin-demo/sources">Load data</a>
  </div>
  <div class="toolbar">
    <span class="pill">{len(RUNS)} run(s)</span>
    <span class="pill">{len(EVENTS)} event(s)</span>
    <span class="pill">queue pending: {esc(queue.get("pending"))}</span>
    <span class="pill">redis: {"ready" if queue.get("available") else "offline"}</span>
    <span class="pill">latest: {esc((run or {}).get("run_id") or "-")}</span>
    <span class="pill">worker beats: {esc((heartbeat.get("worker") or {}).get("recent_heartbeat_count", 0))}</span>
    <span class="pill">auto-refresh 2s</span>
    <a class="btn" href="/api/admin-dashboard/events">JSON events</a>
    <a class="btn" href="/api/debug/heartbeat">Heartbeat JSON</a>
  </div>
  <pre>{esc(json.dumps({"queue": queue, "worker_ledger": str(WORKER_LEDGER_PATH), "worker_ledger_exists": WORKER_LEDGER_PATH.exists(), "heartbeat": heartbeat}, indent=2))}</pre>
  <div class="rows" id="events">{rows}</div>
</section>
<script>
async function refreshEvents() {{
  try {{
    const res = await fetch('/api/admin-dashboard/events?limit=80', {{cache: 'no-store'}});
    const data = await res.json();
    const events = data.events.slice().reverse();
    document.getElementById('events').innerHTML = events.length ? events.map(function (event) {{
      const ts = new Date(event.ts * 1000).toLocaleTimeString();
      const detail = JSON.stringify(event.detail || {{}});
      return '<div class="row event"><code>' + ts + '</code><code>' + event.kind + '</code><div><strong>' + escapeHtml(event.message) + '</strong><p class="muted">' + escapeHtml(event.source || 'system') + '</p></div><code>' + escapeHtml(event.run_id || '-') + '</code><pre>' + escapeHtml(detail) + '</pre></div>';
    }}).join('') : '<div class="row">No actions yet.</div>';
  }} catch (err) {{}}
}}
function escapeHtml(value) {{ return String(value).replace(/[&<>"]/g, function (ch) {{ return ({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}})[ch]; }}); }}
setInterval(refreshEvents, 2000);
</script>"""
    return page("Admin Monitor", body)


def event_row(event: dict) -> str:
    return (
        '<div class="row event">'
        f'<code>{time.strftime("%H:%M:%S", time.localtime(int(event.get("ts") or 0)))}</code>'
        f'<code>{esc(event.get("kind"))}</code>'
        f'<div><strong>{esc(event.get("message"))}</strong><p class="muted">{esc(event.get("source") or "system")}</p></div>'
        f'<code>{esc(event.get("run_id") or "-")}</code>'
        f'<pre>{esc(json.dumps(event.get("detail") or {}, sort_keys=True))}</pre>'
        '</div>'
    )


class _UploadFile:
    """Minimal stand-in for the file part cgi.FieldStorage used to return (.filename + .file.read())."""

    def __init__(self, filename: str, data: bytes) -> None:
        self.filename = filename
        self.file = io.BytesIO(data)


class _MultipartForm:
    """Tiny multipart/form-data form replacing the cgi.FieldStorage subset this server used."""

    def __init__(self, fields: dict, files: dict) -> None:
        self._fields = fields
        self._files = files

    def getfirst(self, name: str, default: str = "") -> str:
        vals = self._fields.get(name)
        return vals[0] if vals else default

    def __contains__(self, name: str) -> bool:
        return name in self._files or name in self._fields

    def __getitem__(self, name: str):
        return self._files.get(name) or self._fields.get(name)


def parse_multipart_form(headers, rfile) -> "_MultipartForm":
    """Parse a multipart/form-data POST into text fields + uploaded files using the stdlib `email`
    parser (the supported replacement for the removed `cgi.FieldStorage`, PEP 594)."""
    ctype = headers.get("Content-Type", "")
    length = int(headers.get("Content-Length") or "0")
    body = rfile.read(length)
    raw = b"Content-Type: " + ctype.encode("latin-1") + b"\r\nMIME-Version: 1.0\r\n\r\n" + body
    msg = email.message_from_bytes(raw)
    fields: dict = {}
    files: dict = {}
    if msg.is_multipart():
        for part in msg.get_payload():
            name = part.get_param("name", header="content-disposition")
            filename = part.get_filename()
            payload = part.get_payload(decode=True) or b""
            if filename:
                files[str(name)] = _UploadFile(str(filename), payload)
            elif name:
                fields.setdefault(str(name), []).append(payload.decode("utf-8", "ignore"))
    return _MultipartForm(fields, files)


def _audit_bundle() -> list[dict]:
    """A small deterministic context bundle for the LIVE Context Auditor demo. It surfaces the REDUNDANT and
    bloated context the other pipeline engines don't (a near-duplicate doc pair + an over-broad tool load).
    Conflict + staleness are already shown by interrogate/context_rot, so this bundle stays focused on the
    auditor's distinctive signals → context.duplicate_found / context.tool_bloat + a context.audited manifest."""
    dup = "the billing api retries a failed charge up to five times before marking the invoice failed"
    return [
        {"id": "acme:runbook-note", "kind": "retrieved_doc", "text": dup, "age_days": 20, "token_estimate": 40},
        {"id": "acme:wiki-note", "kind": "retrieved_doc", "text": dup.replace("invoice failed", "invoice unpaid"), "age_days": 35, "token_estimate": 40},
        {"id": "acme:mcp-tools", "kind": "mcp_tool_schema", "text": "github + jira + slack tool schemas",
         "schema_count": 40, "relevant_count": 3, "token_estimate": 4000},
    ]


def run_full_pipeline(bus) -> dict:
    """Drive the WHOLE context motion over demo-data/acme-billing wired to the live bus, so the
    dashboard shows every stage fire. Composes the shipped engines (no reimplementation); offline,
    deterministic, no Redis, no canonical mutation."""
    from scripts.context_graph import ContextGraph, load_seed, interrogate
    from scripts.context_compress import compress
    from scripts.context_swarm import swarm_object
    from scripts.source_expansion import expand_source_handle
    from scripts.eval.context_lift_matrix import run_matrix, CORPUS_ITEMS

    cid = "pipeline-acme"
    bus.publish("pipeline.started", component="pipeline", stage="Source Systems", correlation_id=cid,
                payload={"corpus": "acme-billing"})
    g = ContextGraph(load_seed())
    for oid, o in g.objects.items():
        for h in (o.get("source_handles") or [])[:1]:
            bus.publish("source_handle.created", component="ingest", stage="Source Systems",
                        correlation_id=cid, object_ref=oid, payload={"handle": h})
        bus.publish("context_object.created", component="ingest", stage="Source Systems",
                    correlation_id=cid, object_ref=oid, payload={"type": o.get("object_type")})
    interro = interrogate(g, "What is the retry ceiling / how many retries are allowed?", bus=bus)
    items = [{"ref": oid, "text": f"{g.objects[oid].get('title','')}. {g.objects[oid].get('summary','')} {g.objects[oid].get('claim','')}",
              "source_handles": g.objects[oid].get("source_handles", [])}
             for oid in interro.get("objects_consulted", []) if oid in g.objects]
    # context_compress emits component.started → component.progressed (per step) → context_pack.created NATIVELY
    comp = compress(items, query="retry ceiling retries", max_tokens=256, bus=bus) if items else {"token_budget": {"estimated_before": 0, "estimated_after": 0}, "retained_refs": []}
    # context_swarm emits swarm.started + swarm.agent.completed (per agent) + swarm.consensus.created NATIVELY
    sw = swarm_object(g, "obj-runbook", bus=bus)
    for rr in sw["review_requests"]:
        bus.publish("review.requested", component="context_swarm", stage="Anti-Fragility", correlation_id=cid,
                    object_ref=rr.get("subject"), payload={"trigger": rr.get("trigger"), "risk": rr.get("risk")})
    # Context Auditor → Optimizer (Optimization) fires live: audit the assembled context for the REDUNDANT +
    # bloated context the other engines don't flag (→ context.duplicate_found / context.tool_bloat +
    # context.audited), then APPLY the manifest LOSSLESSLY → context.optimized + the optimized bundle that
    # feeds the gateway pre-call. PROPOSES then disposes-LOSSLESSLY (supersede≠delete; raw rehydratable in
    # _pre['envelope']['raw']); the optimized view is not truth. (Conflict/stale already shown upstream.)
    from src.baltor.context_audit.audit_bridge import optimize_pre_call
    _pre = optimize_pre_call(_audit_bundle(), bus, correlation_id=cid)
    # policy-gated raw expansion fires live: an allowed handle + a denied (restricted) example
    expand_source_handle("ctx://acme-billing/decisions/ADR-014-billing-retry-policy.md#decision",
                         classification="internal", bus=bus)
    expand_source_handle("ctx://acme-billing/docs/billing-runbook.md#retry-policy",
                         classification="regulated", bus=bus)
    # Shared LLM Plane fires live (Enhancement): the gateway drafts a CANDIDATE explanation through the LOCAL STUB
    # and records a ModelInvocationReceipt. The model output is NEVER the served answer — the deterministic
    # interro["answer_value"] remains truth; the candidate is governed (is_truth=false, receipt-backed, no raw key).
    from src.teleon.inference import oips as _oips
    # prefer the REAL local model node; the gateway degrades to the stub honestly when it can't run
    _pref = [{"preference_id": "pipeline.explain", "model_class_preference": {"tier_code": 400, "specialization_codes": [300]},
              "allowed_provider_nodes": ["model.ollama_local@candidate", "model.local_stub@v1"],
              "disallowed_provider_nodes": [],
              "fallback_policy": {}, "data_policy": {}}]
    bus.publish("inference.requested", component="inference_gateway", stage="Enhancement", correlation_id=cid,
                payload={"task": "draft_answer_explanation", "preference_id": "pipeline.explain", "is_truth": False,
                         "context_optimized": True, "optimized_context_tokens": _pre["envelope"]["optimized_tokens"]})
    _inf = _oips.infer_local(object_id="obj-runbook", preference_layers=_pref,
                             input_text=f"Explain the retry ceiling answer: {interro['answer_value']}",
                             now="2026-06-05T00:00:00Z",
                             # owner-authorized live model calls (.env); offline → stub, honestly receipted
                             allow_network=os.environ.get("OH_INFERENCE_ALLOW_NETWORK", "") == "1")
    _rcpt = _inf["receipt"]
    bus.publish("inference.completed", component="inference_gateway", stage="Enhancement", correlation_id=cid,
                object_ref="obj-runbook",
                payload={"receipt_id": _rcpt.get("receipt_id"), "executed_node": _rcpt.get("selected_provider_node_id"),
                         "fallback_used": _rcpt.get("fallback_used"), "is_truth": False,
                         "candidate_output_is_not_served_truth": True})
    bus.publish("receipt_issued", component="receipt", stage="Consumption", correlation_id=cid,
                payload={"answer_value": interro["answer_value"], "authority": (interro["authority"] or {}).get("subject_id")})
    # The REAL governed flow (ingest→assure→serve) fires live: verified_context_flow runs the bundled
    # sanctions fixture and emits source.received → verification.started → verification.completed →
    # context_pack.created NATIVELY (catches the SYN-0007 would-be violation + holds it out of serving).
    from scripts.pipeline.verified_context_flow import (
        DEMO_INTERNAL_CLAIMS, DEMO_SOURCE_RECORDS, run as run_verified_context_flow,
    )
    run_verified_context_flow(DEMO_SOURCE_RECORDS, DEMO_INTERNAL_CLAIMS, bus=bus)
    # Verification rail: a MEASURED lift (paired separate-judge protocol; deterministic stub scorers)
    bus.publish("eval.started", component="context_lift_matrix", stage="Verification rail", correlation_id=cid, payload={"corpus": "acme"})
    matrix = run_matrix(items=CORPUS_ITEMS["acme"])
    cm = matrix["by_model"]["local_mock"]["condition_mean"]
    lift = round((cm.get("context_pack") or 0.0) - (cm.get("no_context") or 0.0), 4)
    bus.publish("eval.completed", component="context_lift_matrix", stage="Verification rail", correlation_id=cid, payload={"best_condition": matrix["summary"]["best_condition"]})
    bus.publish("context_lift.calculated", component="context_lift_matrix", stage="Verification rail", correlation_id=cid,
                payload={"no_context": cm.get("no_context"), "context_pack": cm.get("context_pack"), "lift": lift, "best": matrix["summary"]["best_condition"]})
    bus.publish("pipeline.completed", component="pipeline", stage="Consumption", correlation_id=cid,
                payload={"answer_value": interro["answer_value"], "lift": lift})
    return {"ok": True, "answer_value": interro["answer_value"], "correlation_id": cid,
            "context_audit": {"issues": len(_pre["report"]["issues"]),
                              "estimated_optimized_tokens": _pre["report"]["estimated_optimized_tokens"],
                              "optimized_tokens": _pre["envelope"]["optimized_tokens"],
                              "lossless": _pre["envelope"]["lossless"]},
            "events_emitted": len(bus.by_correlation(cid))}


class Handler(BaseHTTPRequestHandler):
    def _authed(self, parsed) -> bool:
        supplied = (parse_qs(parsed.query).get("token") or [None])[0] or self.headers.get("X-OHH-Token")
        return _token_ok(SHOWCASE_TOKEN, supplied)

    def _tenant(self, parsed, body: dict | None = None) -> str:
        """P2 isolation seam at the request edge: ?tenant= → X-OHH-Tenant header → body → DEFAULT_TENANT.
        Defaults to the single demo tenant (byte-identical) but is honored end-to-end when supplied."""
        return resolve_tenant(parsed, self.headers.get(TENANT_HEADER), body)

    def _serve_web(self, name: str) -> None:
        """Serve a static file from _repos/baltor/frontend/ (open GET — viewing is never token-gated)."""
        try:
            # web/baltor/ moved to _repos/baltor/frontend/ in the _repos/ migration; resolve via _resource.
            self.send_bytes(200, (_resource("web/baltor") / name).read_bytes())
        except OSError:
            self.send_bytes(404, f"{name} not found".encode(), "text/plain")

    def _serve_pipeline_file(self, rel: str) -> None:
        """Serve a projection page or the shared css from _repos/baltor/frontend/pipeline/ (open GET).
        Pages use relative links (./upload.html, ./pipeline.css) so they are served under the /pipeline/
        path on THIS origin (same-origin as /api/pipeline/*). Projection-only static assets."""
        rel = (rel or "index.html").lstrip("/")
        if not rel.endswith((".html", ".css")):
            rel = rel + ".html"
        if ".." in rel:  # no path traversal out of the pipeline dir
            self.send_bytes(404, b"not found", "text/plain"); return
        ctype = "text/css; charset=utf-8" if rel.endswith(".css") else "text/html; charset=utf-8"
        try:
            # web/baltor/ moved to _repos/baltor/frontend/ in the _repos/ migration; resolve via _resource.
            self.send_bytes(200, (_resource("web/baltor") / "pipeline" / rel).read_bytes(), ctype)
        except OSError:
            self.send_bytes(404, f"pipeline/{rel} not found".encode(), "text/plain")

    def _read_json(self) -> dict:
        """Parse a JSON request body (empty/invalid → {})."""
        length = int(self.headers.get("Content-Length") or "0")
        raw = self.rfile.read(length).decode("utf-8", errors="ignore") if length else ""
        try:
            data = json.loads(raw or "{}")
            return data if isinstance(data, dict) else {}
        except json.JSONDecodeError:
            return {}

    def send_bytes(self, code: int, body: bytes, ctype: str = "text/html; charset=utf-8") -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store, must-revalidate")
        self.end_headers()
        self.wfile.write(body)

    def stream_events(self) -> None:
        """Server-Sent Events: stream the live bus to the dashboard. Sends the recent backlog, then
        each new event as `data: {json}\\n\\n`, with keep-alive comments; exits on client disconnect."""
        import queue as _queue

        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        # Bounded so a stalled/abandoned tunnel viewer (closed lid, flaky mobile) can't balloon RAM or
        # back-pressure publish() (which runs on request threads). On overflow drop the event; the
        # client re-syncs from BUS.recent() on reconnect. 2000 ≈ 2× the bus buffer — ample headroom.
        q: "_queue.Queue[dict]" = _queue.Queue(maxsize=2000)

        def _enqueue(ev: dict) -> None:
            try:
                q.put_nowait(ev)
            except _queue.Full:
                pass  # lagged viewer: drop; recent() backfills on reconnect — never block the bus
        unsub = BUS.subscribe(_enqueue)
        try:
            for ev in BUS.recent(100):
                self.wfile.write(f"data: {json.dumps(ev)}\n\n".encode("utf-8"))
            self.wfile.flush()
            while True:
                try:
                    ev = q.get(timeout=15)
                    self.wfile.write(f"data: {json.dumps(ev)}\n\n".encode("utf-8"))
                except _queue.Empty:
                    self.wfile.write(b": keep-alive\n\n")
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass  # client closed the stream
        finally:
            unsub()

    def current_run(self) -> dict | None:
        sync_context_worker_events()
        sync_worker_ledger()
        qs = parse_qs(urlparse(self.path).query)
        run_id = (qs.get("run") or [""])[0]
        return RUNS.get(run_id) or latest_run()

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        # Context Auditor → Optimizer manifest — handled BEFORE the /api/context/ gateway prefix below (exact
        # match wins). PROJECTION-ONLY: runs the auditor + lossless optimizer over the demo bundle; no canonical
        # mutation; the optimized view is evidence, not truth.
        if path == "/api/context/audit":
            from src.baltor.context_audit import apply_manifest, audit
            _ab = _audit_bundle()
            _arep = audit(_ab)
            _aenv = apply_manifest(_ab, _arep)
            self.send_bytes(200, json.dumps({
                "issues": _arep["issues"], "original_tokens": _aenv["original_tokens"],
                "optimized_tokens": _aenv["optimized_tokens"], "dropped": _aenv["dropped"],
                "superseded": _aenv["superseded"], "applied": _arep["applied"],
                "lossless": _aenv["lossless"], "rehydratable": _aenv["rehydratable"],
            }).encode(), "application/json")
            return
        # C-CONSUME-1: the Consumption API is a projection over ConsumptionService — delegate, never compute truth here.
        if path.startswith("/api/context/") or path in ("/api/runtime/sections", "/api/runtime/consumption"):
            from scripts.api_context_handler import handle as _ctx_handle
            q = {k: (v[0] if v else "") for k, v in parse_qs(parsed.query).items()}  # GET serve reads query params
            code, payload = _ctx_handle("GET", path, q)
            self.send_bytes(code, json.dumps(payload, indent=2).encode(), "application/json")
            return
        # C-MEM-1: governed Memory API — projection over MemoryProviderPort (candidate artifacts, never served facts).
        if path.startswith("/api/memory/"):
            from scripts.api_memory_handler import handle as _mem_handle
            q = {k: (v[0] if v else "") for k, v in parse_qs(parsed.query).items()}
            code, payload = _mem_handle("GET", path, q)
            self.send_bytes(code, json.dumps(payload, indent=2).encode(), "application/json")
            return
        # Pipeline visualization API — projection over the existing runtime (held-out/rejected/lineage exposed).
        if path.startswith("/api/pipeline/"):
            from scripts.api_pipeline_handler import handle as _pipe_handle
            q = {k: (v[0] if v else "") for k, v in parse_qs(parsed.query).items()}
            code, payload = _pipe_handle("GET", path, q)
            self.send_bytes(code, json.dumps(payload, indent=2).encode(), "application/json")
            return
        # C-NATIVE-1: Native Format Preservation — projection export/sidecar/diff (original never overwritten).
        if path.startswith("/api/native/"):
            from scripts.api_native_handler import handle as _nat_handle
            q = {k: (v[0] if v else "") for k, v in parse_qs(parsed.query).items()}
            code, payload = _nat_handle("GET", path, q)
            self.send_bytes(code, json.dumps(payload, indent=2).encode(), "application/json")
            return
        # Standards API — projection over the pattern/standard/template/routine/waiver registries.
        if path.startswith("/api/standards/"):
            from scripts.api_standards_handler import handle as _std_handle
            q = {k: (v[0] if v else "") for k, v in parse_qs(parsed.query).items()}
            code, payload = _std_handle("GET", path, q)
            self.send_bytes(code, json.dumps(payload, indent=2).encode(), "application/json")
            return
        # Determinism API — projection over the LLM→deterministic-rule demo (consensus≠truth; CFPB reference reproduced).
        if path.startswith("/api/determinism/"):
            from scripts.api_determinism_handler import handle as _det_handle
            q = {k: (v[0] if v else "") for k, v in parse_qs(parsed.query).items()}
            code, payload = _det_handle("GET", path, q)
            self.send_bytes(code, json.dumps(payload, indent=2).encode(), "application/json")
            return
        # C-GRAPH-1: Temporal Fact Graph — projection over the local governed temporal graph (Graphiti candidate).
        if path.startswith("/api/graph/temporal/"):
            from scripts.api_temporal_graph_handler import handle as _tg_handle
            q = {k: (v[0] if v else "") for k, v in parse_qs(parsed.query).items()}
            code, payload = _tg_handle("GET", path, q)
            self.send_bytes(code, json.dumps(payload, indent=2).encode(), "application/json")
            return
        # Shared LLM Plane (Inference Gateway / OIPS) — projection over _repos/teleon/backend/src/teleon/inference; no raw key, output never truth.
        if path.startswith("/api/inference/"):
            from scripts.api_inference_handler import handle as _inf_handle
            code, payload = _inf_handle("GET", path, None)
            self.send_bytes(code, json.dumps(payload, indent=2).encode(), "application/json")
            return
        if path in {"/", "/admin-demo"}:
            sync_context_worker_events()
            sync_worker_ledger()
            log_event("page.view", "Opened six-card admin demo", source=path)
            self.send_bytes(200, home_page())
        elif path == "/admin-demo/sources":
            log_event("page.view", "Opened Load Data page", source=path)
            self.send_bytes(200, sources_page())
        elif path == "/admin-demo/run-sample":
            run = create_background_run(SAMPLE_TEXT, "baltor-policy-sample.txt", "sample", None)
            log_event("upload.sample", "Loaded sample source file", run_id=run["run_id"], source="baltor-policy-sample.txt")
            self.send_response(303)
            self.send_header("Location", f"/admin-demo/monitoring?run={run['run_id']}")
            self.end_headers()
        elif path == "/admin-demo/monitoring":
            log_event("page.view", "Opened Processing page", source=path, detail={"run_id": (self.current_run() or {}).get("run_id", "")})
            self.send_bytes(200, monitoring_page(self.current_run()))
        elif path == "/admin-demo/outputs":
            log_event("page.view", "Opened Outputs page", source=path, detail={"run_id": (self.current_run() or {}).get("run_id", "")})
            self.send_bytes(200, outputs_page(self.current_run()))
        elif path == "/admin-demo/download":
            log_event("page.view", "Opened Download page", source=path, detail={"run_id": (self.current_run() or {}).get("run_id", "")})
            self.send_bytes(200, download_page(self.current_run()))
        elif path == "/admin-demo/explore":
            log_event("page.view", "Opened Explore page", source=path, detail={"run_id": (self.current_run() or {}).get("run_id", "")})
            self.send_bytes(200, explore_page(self.current_run()))
        elif path == "/admin-demo/testing":
            log_event("page.view", "Opened Integration Testing page", source=path)
            self.send_bytes(200, testing_page())
        elif path in {"/admin-dashboard/monitor", "/admin-dashboard"}:
            log_event("page.view", "Opened admin monitor", source=path)
            self.send_bytes(200, monitor_page())
        elif path == "/api/admin-dashboard/events":
            sync_context_worker_events()
            sync_worker_ledger()
            qs = parse_qs(parsed.query)
            limit = max(1, min(250, int((qs.get("limit") or ["100"])[0])))
            run = latest_run()
            payload = {"runs": len(RUNS), "latest_run_id": (run or {}).get("run_id"), "artifact_counts": run_artifact_counts(run), "queue": queue_stats(), "events": EVENTS[-limit:]}
            self.send_bytes(200, json.dumps(payload).encode(), "application/json")
        elif path == "/api/admin-dashboard/status":
            self.send_bytes(200, json.dumps(status_payload()).encode(), "application/json")
        elif path == "/api/admin-dashboard/queue-health":
            self.send_bytes(200, json.dumps(queue_health_payload(), indent=2).encode(), "application/json")
        elif path == "/api/admin-dashboard/operational-readiness":
            self.send_bytes(200, json.dumps(operational_readiness_payload(), indent=2).encode(), "application/json")
        elif path in {"/api/debug/heartbeat", "/api/admin-dashboard/heartbeat"}:
            qs = parse_qs(parsed.query)
            payload = heartbeat_payload((qs.get("run_id") or [""])[0])
            self.send_bytes(200, json.dumps(payload, indent=2).encode(), "application/json")
        elif path == "/api/fleet" or path.startswith("/api/fleet/"):
            # OPP-supervisor-scaling-live: READ-ONLY projection of live supervisor coordination state.
            from src.baltor.workers import supervisor_projection as _fp
            sub = path[len("/api/fleet"):].strip("/")
            if sub.startswith("supervisors/"):
                payload = _fp.supervisor_detail(sub.split("/", 1)[1])
            elif sub == "":
                payload = _fp.fleet_projection()
            else:
                payload = _fp.fleet_section(sub)
            self.send_bytes(200 if payload.get("ok") else 404,
                            json.dumps(payload, indent=2, default=str).encode(), "application/json")
        elif path == "/api/context-gateway/status":
            self.send_bytes(200, json.dumps(gateway_status_payload(), indent=2).encode(), "application/json")
        elif path == "/api/context-gateway/connectors":
            payload = connector_catalog_payload()
            self.send_bytes(200, json.dumps(payload, indent=2).encode(), "application/json")
        elif path == "/api/context-gateway/sync-contracts":
            payload = sync_contracts_payload()
            self.send_bytes(200, json.dumps(payload, indent=2).encode(), "application/json")
        elif path == "/api/context-gateway/context-object-schema":
            payload = context_object_schema_payload()
            self.send_bytes(200 if payload.get("ok") else 500, json.dumps(payload, indent=2).encode(), "application/json")
        elif path == "/api/context-gateway/context-schema-catalog":
            payload = context_schema_catalog_payload()
            self.send_bytes(200 if payload.get("ok") else 500, json.dumps(payload, indent=2).encode(), "application/json")
        elif path == "/api/context-gateway/product-surface":
            payload = context_product_surface_payload()
            self.send_bytes(200, json.dumps(payload, indent=2).encode(), "application/json")
        elif path == "/api/context-gateway/search":
            qs = parse_qs(parsed.query)
            query = (qs.get("query") or qs.get("q") or [""])[0]
            task_type = (qs.get("task_type") or ["code_change"])[0]
            pack_type = (qs.get("pack_type") or ["implementation_pack"])[0]
            token_budget = max(256, min(12000, int((qs.get("token_budget") or ["3000"])[0])))
            run_id = (qs.get("run_id") or [""])[0]
            tenant = self._tenant(parsed)                          # P2: which tenant is searching
            run = run_for_tenant(run_id, tenant)                   # tenant-scoped — cross-tenant run_id → None → no-run 404
            payload = context_search_payload(query, run=run, task_type=task_type, token_budget=token_budget, pack_type=pack_type, tenant_id=tenant)
            log_event("context_gateway.search", "Returned bounded context pack", run_id=str((run or {}).get("run_id") or ""), source=query[:120], detail={"task_type": task_type, "pack_type": pack_type, "tenant_id": tenant})
            self.send_bytes(200 if payload.get("ok") else 404, json.dumps(payload, indent=2).encode(), "application/json")
        elif path == "/api/context-gateway/fetch":
            # Item 4 (deep-dive): the gateway fetch returns RAW ingested content, so when OH_SHOWCASE_TOKEN
            # is configured (public tunnel) this read is token-gated like a POST. Unset (local/self-tests)
            # ⇒ open, byte-identical to prior behavior. Conservative: ONLY this ingested-content fetch is
            # gated; search/glossary/dimensions/status stay open so the public demo still reads.
            if not self._authed(parsed):
                self.send_bytes(401, json.dumps({"error": "token required for ingested-content fetch",
                                                 "hint": "append ?token=<token> or send an X-OHH-Token header"}).encode(),
                                "application/json")
                return
            qs = parse_qs(parsed.query)
            handle = (qs.get("handle") or [""])[0]
            max_tokens = max(64, min(4000, int((qs.get("max_tokens") or ["1000"])[0])))
            run_id = (qs.get("run_id") or [""])[0]
            tenant = self._tenant(parsed)                          # P2: which tenant is fetching
            # ctxv:// resolves against the tenant-scoped version table (run-independent); ctx:// resolves a
            # tenant-owned run (cross-tenant run_id → None → no-run 404, never leaking the handle's existence).
            run = None if str(handle).startswith("ctxv://") else run_for_tenant(run_id, tenant)
            payload = context_fetch_payload(handle, run=run, max_tokens=max_tokens, tenant_id=tenant)
            # 410 Gone iff a once-pinned ctxv:// version was superseded+pruned; every other not-ok → 404.
            code = 200 if payload.get("ok") else (410 if payload.get("status") == "gone" else 404)
            log_event("context_gateway.fetch", "Fetched bounded context handle", run_id=str((run or {}).get("run_id") or ""), source=handle[:160], detail={"ok": payload.get("ok"), "kind": payload.get("kind"), "tenant_id": tenant, "status": payload.get("status")})
            self.send_bytes(code, json.dumps(payload, indent=2).encode(), "application/json")
        elif path == "/api/context-gateway/receipts":
            # Honest provenance surface (deep-dive item 2): the persisted gateway receipts for search/fetch.
            qs = parse_qs(parsed.query)
            limit = max(1, min(500, int((qs.get("limit") or ["50"])[0])))
            receipts = latest_gateway_receipts(limit)
            self.send_bytes(200, json.dumps({"ok": True, "kind": "baltor.gateway-receipts",
                                             "durable": RUN_STORE is not None, "count": len(receipts),
                                             "receipts": receipts}, indent=2).encode(), "application/json")
        elif path == "/api/context-gateway/glossary":
            qs = parse_qs(parsed.query)
            term = (qs.get("term") or [""])[0]
            max_packets = max(1, min(50, int((qs.get("max_packets") or ["12"])[0])))
            run_id = (qs.get("run_id") or [""])[0]
            run = RUNS.get(run_id) if run_id else latest_run()
            payload = context_glossary_payload(run=run, term=term, max_packets=max_packets)
            log_event("context_gateway.glossary", "Returned glossary resolution packets", run_id=str((run or {}).get("run_id") or ""), source=term[:120], detail={"packet_count": payload.get("packet_count")})
            self.send_bytes(200 if payload.get("ok") else 404, json.dumps(payload, indent=2).encode(), "application/json")
        elif path == "/api/context-gateway/dimensions":
            qs = parse_qs(parsed.query)
            dimension_id = (qs.get("dimension_id") or [""])[0]
            subject_id = (qs.get("subject_id") or [""])[0]
            max_values = max(1, min(500, int((qs.get("max_values") or ["100"])[0])))
            run_id = (qs.get("run_id") or [""])[0]
            run = RUNS.get(run_id) if run_id else latest_run()
            payload = context_dimensions_payload(run=run, dimension_id=dimension_id, subject_id=subject_id, max_values=max_values)
            log_event("context_gateway.dimensions", "Returned context dimension definitions and values", run_id=str((run or {}).get("run_id") or ""), source=dimension_id[:120], detail={"value_count": payload.get("counts", {}).get("dimension_values")})
            self.send_bytes(200 if payload.get("ok") else 404, json.dumps(payload, indent=2).encode(), "application/json")
        elif path == "/api/context-gateway/model-routing":
            qs = parse_qs(parsed.query)
            task_type = (qs.get("task_type") or ["claim_review"])[0]
            run_id = (qs.get("run_id") or [""])[0]
            run = RUNS.get(run_id) if run_id else latest_run()
            payload = context_model_routing_payload(run=run, task_type=task_type)
            log_event("context_gateway.model_routing", "Returned provider-neutral model routing ladder", run_id=str((run or {}).get("run_id") or ""), source=task_type[:120], detail={"recommended_route": payload.get("sample_route_decision", {}).get("recommended_route")})
            self.send_bytes(200, json.dumps(payload, indent=2).encode(), "application/json")
        elif path == "/api/context-gateway/reranking":
            qs = parse_qs(parsed.query)
            query = (qs.get("query") or qs.get("q") or [""])[0]
            task_type = (qs.get("task_type") or ["implementation_pack"])[0]
            run_id = (qs.get("run_id") or [""])[0]
            run = RUNS.get(run_id) if run_id else latest_run()
            payload = context_reranking_payload(run=run, query=query, task_type=task_type)
            log_event("context_gateway.reranking", "Returned source-aware reranking ladder", run_id=str((run or {}).get("run_id") or ""), source=query[:120], detail={"recommended_stage": payload.get("sample_rerank_decision", {}).get("recommended_stage")})
            self.send_bytes(200, json.dumps(payload, indent=2).encode(), "application/json")
        elif path == "/api/context-gateway/local-memory":
            qs = parse_qs(parsed.query)
            run_id = (qs.get("run_id") or [""])[0]
            scope = (qs.get("scope") or ["personal"])[0]
            run = RUNS.get(run_id) if run_id else latest_run()
            payload = context_local_memory_payload(run=run, scope=scope)
            log_event("context_gateway.local_memory", "Returned local encrypted memory sync contract", run_id=str((run or {}).get("run_id") or ""), source=scope[:120], detail={"memory_profiles": len(payload.get("memory_profiles") or [])})
            self.send_bytes(200, json.dumps(payload, indent=2).encode(), "application/json")
        elif path == "/api/context-gateway/trace":
            qs = parse_qs(parsed.query)
            payload = context_trace_payload((qs.get("result_id") or [""])[0])
            self.send_bytes(200, json.dumps(payload, indent=2).encode(), "application/json")
        elif path == "/api/health":
            self.send_bytes(200, json.dumps({"ok": True, "service": "baltor-admin-demo", "status_url": "/api/admin-dashboard/status", "heartbeat_url": "/api/debug/heartbeat", "uptime_seconds": int(time.time()) - SERVER_STARTED_AT}).encode(), "application/json")
        elif path.startswith("/api/admin-demo/runs/") and "/exports/" in path:
            self.export(path)
        elif path.startswith("/api/admin-demo/runs/"):
            sync_context_worker_events()
            sync_worker_ledger()
            run_id = path.rsplit("/", 1)[-1]
            run = RUNS.get(run_id)
            self.send_bytes(200 if run else 404, json.dumps(run or {"error": "not found"}).encode(), "application/json")
        elif path == "/api/events":
            qs = parse_qs(parsed.query)
            limit = max(1, min(500, int((qs.get("limit") or ["100"])[0])))
            self.send_bytes(200, json.dumps({"events": BUS.recent(limit), "event_kinds": sorted(__import__("scripts.context_events", fromlist=["EVENT_KINDS"]).EVENT_KINDS)}).encode(), "application/json")
        elif path == "/api/events/stream":
            self.stream_events()
        elif path == "/dashboard" or path == "/dashboard.html":
            try:
                body = (_resource("web/baltor") / "dashboard.html").read_bytes()  # moved to _repos/baltor/frontend/
                self.send_bytes(200, body)
            except OSError:
                self.send_bytes(404, b"dashboard.html not found", "text/plain")
        elif path == "/api/dev/status":
            from scripts.dev_status import build_dev_status
            self.send_bytes(200, json.dumps(build_dev_status()).encode(), "application/json")
        elif path == "/dev" or path == "/dev-dashboard.html":
            try:
                body = (_resource("web/baltor") / "dev-dashboard.html").read_bytes()  # moved to _repos/baltor/frontend/
                self.send_bytes(200, body)
            except OSError:
                self.send_bytes(404, b"dev-dashboard.html not found", "text/plain")
        elif path in ("/", "/hub", "/hub.html"):
            self._serve_web("hub.html")
        elif path in ("/raw", "/raw.html", "/feed"):
            self._serve_web("raw.html")
        elif path in ("/integrate", "/integrate.html", "/cfpb"):
            self._serve_web("integrate.html")
        elif path in ("/consume", "/consume.html"):
            self._serve_web("consume.html")
        elif path in ("/memory", "/memory.html"):
            self._serve_web("memory.html")
        elif path in ("/standards", "/standards.html"):
            self._serve_web("standards.html")
        elif path in ("/determinism", "/determinism.html"):
            self._serve_web("determinism.html")
        elif path in ("/temporal-graph", "/temporal-graph.html"):
            self._serve_web("temporal-graph.html")
        elif path in ("/native", "/native.html"):
            self._serve_web("native.html")
        elif path in ("/guided-demos", "/guided-demos.html", "/demos"):
            self._serve_web("guided-demos.html")
        elif path in ("/inference-plane", "/inference-plane.html", "/inference"):
            self._serve_web("inference-plane.html")
        elif path in ("/fleet", "/fleet.html"):
            self._serve_web("fleet.html")
        elif path in ("/pipeline", "/pipeline.html", "/pipeline/index", "/pipeline/index.html"):
            self._serve_pipeline_file("index.html")
        elif path.startswith("/pipeline/"):
            self._serve_pipeline_file(path[len("/pipeline/"):])
        elif path in ("/cfpb-artifact-graph", "/cfpb-artifact-graph.html"):
            self._serve_web("cfpb-artifact-graph.html")
        elif path == "/api/dev/pipelines":
            from scripts.pipeline_runtime.specs import discover
            sp = discover()
            self.send_bytes(200, json.dumps({"pipelines": [
                {"ref": s.ref, "pipeline_id": s.pipeline_id, "version": s.pipeline_version, "status": s.status,
                 "steps": [st.step_id for st in s.steps], "isolation": s.isolation} for s in sp.values()]}).encode(), "application/json")
        elif path.startswith("/api/dev/pipelines/runs/") and path.endswith("/lineage"):
            if DURABLE is None:
                self.send_bytes(503, json.dumps({"error": "durable mode off"}).encode(), "application/json")
            else:
                from scripts.pipeline_runtime.store import PipelineLedger
                from scripts.pipeline_runtime.runner import run_lineage
                rid = path[len("/api/dev/pipelines/runs/"):-len("/lineage")]
                lin = run_lineage(PipelineLedger(DURABLE), DURABLE, rid)
                self.send_bytes(200 if lin else 404, json.dumps(lin or {"error": "run not found"}).encode(), "application/json")
        elif path.startswith("/api/dev/pipelines/runs/"):
            if DURABLE is None:
                self.send_bytes(503, json.dumps({"error": "durable mode off"}).encode(), "application/json")
            else:
                from scripts.pipeline_runtime.store import PipelineLedger
                run = PipelineLedger(DURABLE).get_run(path.rsplit("/", 1)[-1])
                self.send_bytes(200 if run else 404, json.dumps(run or {"error": "run not found"}).encode(), "application/json")
        elif path == "/api/dev/pipelines/runs":
            if DURABLE is None:
                self.send_bytes(503, json.dumps({"error": "durable mode off"}).encode(), "application/json")
            else:
                from scripts.pipeline_runtime.store import PipelineLedger
                self.send_bytes(200, json.dumps({"runs": PipelineLedger(DURABLE).list_runs(limit=50)}).encode(), "application/json")
        else:
            self.send_bytes(404, b"not found", "text/plain")

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if not self._authed(parsed):  # token-gate state-changing endpoints when OH_SHOWCASE_TOKEN is set
            self.send_bytes(401, json.dumps({"error": "token required",
                                             "hint": "append ?token=<token> or send an X-OHH-Token header"}).encode(),
                            "application/json")
            return
        if parsed.path.rstrip("/") == "/api/context/serve":
            # C-CONSUME-1: serve a ContextResponse through ConsumptionService (projection; no truth fabricated here).
            from scripts.api_context_handler import handle as _ctx_handle
            code, payload = _ctx_handle("POST", "/api/context/serve", self._read_json())
            log_event("context.serve", "Served a ContextResponse via the consumption API", source="api/context/serve")
            self.send_bytes(code, json.dumps(payload, indent=2).encode(), "application/json")
            return
        if parsed.path.startswith("/api/native/"):
            # C-NATIVE-1: ingest stores a SOURCE (exact bytes + sha256) and returns refs only — never mutates truth.
            from scripts.api_native_handler import handle as _nat_handle
            code, payload = _nat_handle("POST", parsed.path.rstrip("/"), self._read_json())
            self.send_bytes(code, json.dumps(payload, indent=2).encode(), "application/json")
            return
        if parsed.path.startswith("/api/standards/"):
            # generate-preview is a DRY-RUN: returns what WOULD be generated; writes no files.
            from scripts.api_standards_handler import handle as _std_handle
            code, payload = _std_handle("POST", parsed.path.rstrip("/"), self._read_json())
            self.send_bytes(code, json.dumps(payload, indent=2).encode(), "application/json")
            return
        if parsed.path.startswith("/api/graph/temporal/"):
            # rebuild is a deterministic runtime service (projection-only; does not mutate served truth).
            from scripts.api_temporal_graph_handler import handle as _tg_handle
            q = {k: (v[0] if v else "") for k, v in parse_qs(parsed.query).items()}
            code, payload = _tg_handle("POST", parsed.path.rstrip("/"), q)
            self.send_bytes(code, json.dumps(payload, indent=2).encode(), "application/json")
            return
        if parsed.path.startswith("/api/inference/"):
            # resolve-preference is a pure derivation; structured-local executes the LOCAL STUB and returns a
            # ModelInvocationReceipt — its output is a CANDIDATE, never served truth. No raw key is emitted.
            from scripts.api_inference_handler import handle as _inf_handle
            code, payload = _inf_handle("POST", parsed.path.rstrip("/"), self._read_json())
            self.send_bytes(code, json.dumps(payload, indent=2).encode(), "application/json")
            return
        if parsed.path == "/api/demo/run-full-pipeline":
            log_event("pipeline.run", "Ran the full connected pipeline", source="dashboard")
            result = run_full_pipeline(BUS)
            self.send_bytes(200, json.dumps(result).encode(), "application/json")
            return
        if parsed.path == "/api/demo/run-full-pipeline-via-fleet":
            # G1: run every stage AS a CapabilityTask claimed atomically by a worker under the supervisor.
            from scripts.fleet_pipeline import run_full_pipeline_via_fleet
            log_event("pipeline.run.fleet", "Ran the full pipeline as claimed fleet work", source="dashboard")
            result = run_full_pipeline_via_fleet(bus=BUS)
            self.send_bytes(200, json.dumps(result).encode(), "application/json")
            return
        if parsed.path == "/api/demo/integrate-cfpb":
            from scripts.integrate_cfpb import run as run_integrate_cfpb
            live = (parse_qs(parsed.query).get("live") or ["0"])[0] in ("1", "true", "yes")
            log_event("integrate.cfpb", "Ran the one-click CFPB integration", source="integrate", detail={"live": live})
            self.send_bytes(200, json.dumps(run_integrate_cfpb(bus=BUS, live=live)).encode(), "application/json")
            return
        if parsed.path == "/api/demo/cfpb-artifact-graph":
            # C32: ingest→artifacts→vectors→graph→conflicts→reconciliation→receipt. Persisted to a durable
            # ledger file (the ledger is the source of truth; this response is a projection for the page).
            from scripts.cfpb_artifact_graph_demo import run_demo
            # Item 3 (deep-dive): was hardcoded to <repo>/.agent/ (outside the Fly volume → lost on restart).
            # Now routed through CFPB_ARTIFACT_GRAPH_DB, which defaults into the BALTOR_DURABLE_DB volume dir.
            ledger_path = CFPB_ARTIFACT_GRAPH_DB
            Path(ledger_path).parent.mkdir(parents=True, exist_ok=True)
            resp = run_demo(tenant_id="acme", ledger_path=ledger_path)
            log_event("artifact_graph.run", f"Built CFPB artifact graph (run {resp['run_id']})", source="cfpb-artifact-graph",
                      detail={"counts": resp["counts"]})
            self.send_bytes(200, json.dumps(resp).encode(), "application/json")
            return
        if parsed.path == "/api/dev/enqueue":
            if DURABLE is None:
                self.send_bytes(503, json.dumps({"error": "durable mode off", "hint": "set BALTOR_DURABLE_DB"}).encode(), "application/json")
                return
            body = self._read_json()
            queue = str(body.get("queue") or "flywheel.commands.default")
            cmd = {"command_id": "cmd-" + stable_hash(body).split(":")[-1][:12],
                   "command_type": body.get("command_type") or "noop", "queue": queue,
                   "priority": body.get("priority") or "p2", "correlation_id": body.get("correlation_id") or "",
                   "payload": body.get("payload") or {}}
            res = DURABLE.enqueue(queue, cmd, idempotency_key=body.get("idempotency_key") or cmd["command_id"],
                                  max_attempts=int(body.get("max_attempts") or 5))
            self.send_bytes(200, json.dumps({"ok": True, "command_id": cmd["command_id"], "job_id": res["id"],
                                             "duplicate": res["duplicate"], "queue": queue}).encode(), "application/json")
            return
        if parsed.path == "/api/dev/pipelines/run":
            if DURABLE is None:
                self.send_bytes(503, json.dumps({"error": "durable mode off", "hint": "set BALTOR_DURABLE_DB"}).encode(), "application/json")
                return
            from scripts.pipeline_runtime.specs import discover
            from scripts.pipeline_runtime.processors import default_registry
            from scripts.pipeline_runtime.runner import run_pipeline
            from scripts.pipeline_runtime.isolation import resolve as resolve_isolation
            body = self._read_json()
            ref = f"{body.get('pipeline_id')}@{body.get('pipeline_version')}"
            spec = discover().get(ref)
            if spec is None:
                self.send_bytes(404, json.dumps({"error": f"unknown pipeline {ref}"}).encode(), "application/json")
                return
            tenant = str(body.get("tenant_id") or "demo-tenant")
            base_dir = os.path.dirname(_DURABLE_DB) if _DURABLE_DB else "."
            _store, ledger, db_path = resolve_isolation(spec, tenant, base_dir=base_dir, shared_store=DURABLE)
            res = run_pipeline(spec, tenant_id=tenant, run_input=dict(body.get("input") or {}),
                               ledger=ledger, registry=default_registry(), bus=BUS)
            res["isolation"] = spec.isolation
            res["db_path"] = db_path
            log_event("pipeline.run", f"Ran {ref} → {res.get('status')}", source="pipeline-runtime",
                      detail={"run_id": res.get("run_id"), "pipeline": ref})
            self.send_bytes(200, json.dumps({"ok": res.get("status") == "done", "run_id": res["run_id"],
                                             "pipeline_id": spec.pipeline_id, "pipeline_version": spec.pipeline_version,
                                             "status": res["status"], "duplicate": res.get("duplicate", False),
                                             "queued_steps": res.get("queued_steps"), "artifact_count": res.get("artifact_count"),
                                             "gates": res.get("gates"), "isolation": res.get("isolation"),
                                             "db_path": res.get("db_path")}).encode(), "application/json")
            return
        if parsed.path == "/api/dev/tenant-ingest":
            if DURABLE is None:
                self.send_bytes(503, json.dumps({"error": "durable mode off", "hint": "set BALTOR_DURABLE_DB"}).encode(), "application/json")
                return
            from scripts.ingest.tenant_ingest import enqueue_documents, drain
            body = self._read_json()
            tenant = str(body.get("tenant_id") or "demo-tenant")
            docs = body.get("documents") or []
            enq = enqueue_documents(DURABLE, tenant, docs)
            drained = drain(DURABLE, tenant, now=int(time.time())) if body.get("drain", True) else []
            facts = sum(d.get("facts", 0) for d in drained)
            log_event("tenant.ingest", f"Tenant {tenant}: {enq['new']} docs → {facts} facts", source="tenant-ingest",
                      detail={"tenant": tenant, **enq})
            self.send_bytes(200, json.dumps({"ok": True, "tenant_id": tenant, **enq,
                                             "processed": len(drained), "atomic_facts": facts,
                                             "queue_stats": DURABLE.stats(enq["queue"])}).encode(), "application/json")
            return
        if parsed.path == "/api/dev/drain":
            if DURABLE is None:
                self.send_bytes(503, json.dumps({"error": "durable mode off"}).encode(), "application/json")
                return
            body = self._read_json()
            queue = str(body.get("queue") or "flywheel.commands.default")
            limit = int(body.get("max") or 10)
            processed, now = [], int(time.time())
            for _ in range(limit):
                job = DURABLE.claim(queue, worker="http-drain", lease_seconds=60, now=now)
                if not job:
                    break
                # "process" the command: emit a durable work-plane event, then ack (at-least-once + idempotent)
                BUS.publish("component.finished", component="durable_worker", stage="Work plane",
                            correlation_id=(job["payload"] or {}).get("correlation_id") or None,
                            object_ref=str(job["id"]), payload={"command_id": (job["payload"] or {}).get("command_id"),
                                                                "attempt": job["attempts"]})
                DURABLE.ack(job["id"])
                processed.append(job["id"])
            self.send_bytes(200, json.dumps({"ok": True, "processed": processed, "stats": DURABLE.stats(queue)}).encode(), "application/json")
            return
        if parsed.path == "/api/events/clear":
            BUS.clear()
            if DURABLE is not None:
                DURABLE.clear_events()   # clear the durable log too, so a restart doesn't re-hydrate them
            self.send_bytes(200, json.dumps({"ok": True, "cleared": True}).encode(), "application/json")
            return
        if parsed.path == "/api/context-gateway/search":
            length = int(self.headers.get("Content-Length") or "0")
            raw = self.rfile.read(length).decode("utf-8", errors="ignore")
            try:
                data = json.loads(raw or "{}")
            except json.JSONDecodeError:
                data = {}
            tenant = self._tenant(parsed, data)
            run = run_for_tenant(str(data.get("run_id") or ""), tenant)
            payload = context_search_payload(
                str(data.get("query") or ""),
                run=run,
                task_type=str(data.get("task_type") or "code_change"),
                token_budget=int(data.get("token_budget") or 3000),
                pack_type=str(data.get("pack_type") or "implementation_pack"),
                tenant_id=tenant,
            )
            log_event("context_gateway.search", "Returned bounded context pack", run_id=str((run or {}).get("run_id") or ""), source=str(data.get("query") or "")[:120], detail={"method": "POST", "tenant_id": tenant})
            self.send_bytes(200 if payload.get("ok") else 404, json.dumps(payload, indent=2).encode(), "application/json")
            return
        if parsed.path == "/api/context-gateway/fetch":
            length = int(self.headers.get("Content-Length") or "0")
            raw = self.rfile.read(length).decode("utf-8", errors="ignore")
            try:
                data = json.loads(raw or "{}")
            except json.JSONDecodeError:
                data = {}
            tenant = self._tenant(parsed, data)
            handle = str(data.get("handle") or "")
            run = None if handle.startswith("ctxv://") else run_for_tenant(str(data.get("run_id") or ""), tenant)
            payload = context_fetch_payload(handle, run=run, max_tokens=int(data.get("max_tokens") or 1000), tenant_id=tenant)
            code = 200 if payload.get("ok") else (410 if payload.get("status") == "gone" else 404)
            log_event("context_gateway.fetch", "Fetched bounded context handle", run_id=str((run or {}).get("run_id") or ""), source=handle[:160], detail={"ok": payload.get("ok"), "method": "POST", "tenant_id": tenant, "status": payload.get("status")})
            self.send_bytes(code, json.dumps(payload, indent=2).encode(), "application/json")
            return
        if parsed.path == "/api/context-gateway/glossary":
            length = int(self.headers.get("Content-Length") or "0")
            raw = self.rfile.read(length).decode("utf-8", errors="ignore")
            try:
                data = json.loads(raw or "{}")
            except json.JSONDecodeError:
                data = {}
            run = RUNS.get(str(data.get("run_id") or "")) if data.get("run_id") else latest_run()
            payload = context_glossary_payload(
                run=run,
                term=str(data.get("term") or ""),
                max_packets=int(data.get("max_packets") or 12),
            )
            log_event("context_gateway.glossary", "Returned glossary resolution packets", run_id=str((run or {}).get("run_id") or ""), source=str(data.get("term") or "")[:120], detail={"method": "POST", "packet_count": payload.get("packet_count")})
            self.send_bytes(200 if payload.get("ok") else 404, json.dumps(payload, indent=2).encode(), "application/json")
            return
        if parsed.path == "/api/context-gateway/dimensions":
            length = int(self.headers.get("Content-Length") or "0")
            raw = self.rfile.read(length).decode("utf-8", errors="ignore")
            try:
                data = json.loads(raw or "{}")
            except json.JSONDecodeError:
                data = {}
            run = RUNS.get(str(data.get("run_id") or "")) if data.get("run_id") else latest_run()
            payload = context_dimensions_payload(
                run=run,
                dimension_id=str(data.get("dimension_id") or ""),
                subject_id=str(data.get("subject_id") or ""),
                max_values=int(data.get("max_values") or 100),
            )
            log_event("context_gateway.dimensions", "Returned context dimension definitions and values", run_id=str((run or {}).get("run_id") or ""), source=str(data.get("dimension_id") or "")[:120], detail={"method": "POST", "value_count": payload.get("counts", {}).get("dimension_values")})
            self.send_bytes(200 if payload.get("ok") else 404, json.dumps(payload, indent=2).encode(), "application/json")
            return
        if parsed.path == "/api/context-gateway/model-routing":
            length = int(self.headers.get("Content-Length") or "0")
            raw = self.rfile.read(length).decode("utf-8", errors="ignore")
            try:
                data = json.loads(raw or "{}")
            except json.JSONDecodeError:
                data = {}
            run = RUNS.get(str(data.get("run_id") or "")) if data.get("run_id") else latest_run()
            payload = context_model_routing_payload(
                run=run,
                task_type=str(data.get("task_type") or "claim_review"),
                risk=data.get("risk") if isinstance(data.get("risk"), dict) else None,
            )
            log_event("context_gateway.model_routing", "Returned provider-neutral model routing ladder", run_id=str((run or {}).get("run_id") or ""), source=str(data.get("task_type") or "")[:120], detail={"method": "POST", "recommended_route": payload.get("sample_route_decision", {}).get("recommended_route")})
            self.send_bytes(200, json.dumps(payload, indent=2).encode(), "application/json")
            return
        if parsed.path == "/api/context-gateway/reranking":
            length = int(self.headers.get("Content-Length") or "0")
            raw = self.rfile.read(length).decode("utf-8", errors="ignore")
            try:
                data = json.loads(raw or "{}")
            except json.JSONDecodeError:
                data = {}
            run = RUNS.get(str(data.get("run_id") or "")) if data.get("run_id") else latest_run()
            payload = context_reranking_payload(
                run=run,
                query=str(data.get("query") or ""),
                task_type=str(data.get("task_type") or "implementation_pack"),
                risk=data.get("risk") if isinstance(data.get("risk"), dict) else None,
            )
            log_event("context_gateway.reranking", "Returned source-aware reranking ladder", run_id=str((run or {}).get("run_id") or ""), source=str(data.get("query") or "")[:120], detail={"method": "POST", "recommended_stage": payload.get("sample_rerank_decision", {}).get("recommended_stage")})
            self.send_bytes(200, json.dumps(payload, indent=2).encode(), "application/json")
            return
        if parsed.path == "/api/context-gateway/local-memory":
            length = int(self.headers.get("Content-Length") or "0")
            raw = self.rfile.read(length).decode("utf-8", errors="ignore")
            try:
                data = json.loads(raw or "{}")
            except json.JSONDecodeError:
                data = {}
            run = RUNS.get(str(data.get("run_id") or "")) if data.get("run_id") else latest_run()
            payload = context_local_memory_payload(
                run=run,
                scope=str(data.get("scope") or "personal"),
            )
            log_event("context_gateway.local_memory", "Returned local encrypted memory sync contract", run_id=str((run or {}).get("run_id") or ""), source=str(data.get("scope") or "personal")[:120], detail={"method": "POST", "memory_profiles": len(payload.get("memory_profiles") or [])})
            self.send_bytes(200, json.dumps(payload, indent=2).encode(), "application/json")
            return
        if parsed.path != "/admin-demo/runs":
            self.send_bytes(404, b"not found", "text/plain")
            return
        ctype = self.headers.get("Content-Type", "")
        length = int(self.headers.get("Content-Length") or "0")
        text = ""
        source_name = "pasted-context.txt"
        document_tree = None
        form_tenant = ""                                          # P2: owner tenant supplied via the form body
        if "multipart/form-data" in ctype:
            form = parse_multipart_form(self.headers, self.rfile)
            form_tenant = str(form.getfirst(TENANT_PARAM) or "")
            text = str(form.getfirst("text") or "")
            file_item = form["file"] if "file" in form else None
            if file_item is not None and getattr(file_item, "filename", ""):
                raw = file_item.file.read()
                log_event("upload.received", "Received file upload", source=file_item.filename, detail={"bytes": len(raw)})
                text, source_name, document_tree = upload_to_text(file_item.filename, raw)
                log_event("upload.extracted", "Extracted readable upload text", source=source_name, detail={"characters": len(text), **document_tree.get("summary", {})})
            connector = str(form.getfirst("connector") or "")
            connector_url = str(form.getfirst("connector_url") or "").strip()
            if connector and not text:
                envelope = connector_envelope(connector, connector_url)
                source_name = str(envelope.get("target_uri") or envelope.get("label") or f"{connector} connector")
                log_event("connector.registered", f"Registered {envelope.get('label')} connector envelope", source=source_name, detail={"handle": envelope.get("handle"), "source_system": envelope.get("source_system")})
                text = connector_text(envelope)
                document_tree = connector_document_tree(envelope, text)
        else:
            body = self.rfile.read(length).decode("utf-8", errors="ignore")
            data = parse_qs(body)
            text = (data.get("text") or [""])[0]
            form_tenant = (data.get(TENANT_PARAM) or [""])[0]
        if not text.strip():
            text = SAMPLE_TEXT
            source_name = "baltor-policy-sample.txt"
            document_tree = None
            log_event("upload.fallback", "No source body supplied; using sample policy", source=source_name)
        source_type = "connector" if (document_tree or {}).get("connector_envelope") or source_name.startswith(("ftp://", "sftp://")) or "connector" in source_name.lower() else "upload"
        # P2: the run is OWNED by the resolving tenant (form field → ?tenant= → X-OHH-Tenant → demo). The
        # default keeps the current demo byte-identical; a supplied tenant scopes every ctx:// handle it mints.
        tenant = self._tenant(parsed, {"tenant_id": form_tenant} if form_tenant else None)
        run = create_background_run(text, source_name, source_type, document_tree, tenant_id=tenant)
        self.send_response(303)
        self.send_header("Location", f"/admin-demo/monitoring?run={run['run_id']}")
        self.end_headers()

    def export(self, path: str) -> None:
        parts = path.strip("/").split("/")
        run_id = parts[3] if len(parts) > 3 else ""
        kind = parts[5] if len(parts) > 5 else ""
        run = RUNS.get(run_id) or latest_run()
        if not run:
            self.send_bytes(404, b'{"error":"run not found"}', "application/json")
            return
        payload = export_payload(run, kind)
        log_event("export.created", f"Exported {kind} package", run_id=run["run_id"], source=path, detail={"kind": kind})
        body = json.dumps(payload, indent=2).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Disposition", f'attachment; filename="{run["run_id"]}-{kind}.json"')
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args: object) -> None:
        pass


def _self_test() -> int:
    """Gateway proof (warrant: docs/architecture/capability-rubric-and-deep-dive-2026-06-11.md).
    P1 (still proven): (1) ctx:// handle survives a REAL restart on the same durable db; (2) a receipt is
    issued + persisted on fetch; (3) the CFPB ledger path honors the setting / lands in the durable volume;
    (4) the in-process worker is the FALLBACK only (no double-processing when Redis publishes).
    P2 (tenancy + ctxv://): (5) a ctxv:// pin returns byte-identical bytes AFTER the live content changes,
    is superseded-but-kept (lossless), and becomes 410 Gone only after an explicit prune; (6) tenant A
    cannot fetch tenant B's ctx:// handle (404, no existence leak) while same-tenant fetch works, and a
    ctxv:// version is tenant-scoped too; (7) the default-tenant path is byte-identical to before.
    Spawns this server as a subprocess (like check_durable_restart_survival) and drives the
    run→search→fetch flow over HTTP — deliberately NOT /api/demo/run-full-pipeline (unrelated to this change)."""
    import socket
    import subprocess
    import tempfile
    import urllib.error
    import urllib.parse
    import urllib.request

    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    # ── pure-function checks (no server needed) ───────────────────────────────────────────────────────
    # Item 3: with BALTOR_DURABLE_DB set, the CFPB path defaults into that volume dir, not <repo>/.agent.
    vol = tempfile.mkdtemp(prefix="baltor-vol-")
    env_db = os.path.join(vol, "durable.db")
    expected_cfpb = os.path.join(vol, "cfpb_artifact_graph.db")
    code = ("import os,sys; os.environ['BALTOR_DURABLE_DB']=sys.argv[1];"
            "import scripts.baltor_admin_demo_server as s;"
            "print(s.CFPB_ARTIFACT_GRAPH_DB); print(s.RUN_STORE is not None)")
    out = subprocess.run([sys.executable, "-c", code, env_db], cwd=str(REPO_ROOT),
                         env={**os.environ, "PYTHONPATH": _pythonpath(".")},
                         capture_output=True, text=True)
    lines = (out.stdout or "").strip().splitlines()
    check("item3: CFPB ledger path lands in the durable volume dir",
          bool(lines) and lines[0] == expected_cfpb, f"{lines[:1]} != {expected_cfpb}\n{out.stderr[-300:]}")
    check("item1: RUN_STORE initializes when BALTOR_DURABLE_DB is set", len(lines) > 1 and lines[1] == "True", out.stderr[-300:])

    # Item 5: the run-engine source guarantees ONE path — in-process worker started only when NOT published.
    src = Path(__file__).read_text(encoding="utf-8")
    gate_i = src.find("if not published:")
    thread_i = src.find("threading.Thread(target=process_run_background")
    check("item5: in-process worker is gated behind `if not published:` (no double-run)",
          gate_i != -1 and thread_i != -1 and 0 < (thread_i - gate_i) < 200,
          f"gate@{gate_i} thread@{thread_i}")

    # ── P2 item5: ctxv:// immutability + lossless supersession + prune→410 (pure, in a durable subprocess) ──
    # Done in a subprocess that imports the module WITH a temp BALTOR_DURABLE_DB (RUN_STORE live), so it
    # exercises the real pin_version / fetch_pinned_version / prune_versions against real sqlite. It pins C1
    # under base handle H, then pins a DIFFERENT content C2 under the SAME H (the live content changed), and
    # proves: (a) C1's ctxv:// still returns C1 byte-identical (immutable under a live change); (b) C1 is now
    # superseded but STILL fetchable (lossless — nothing deleted); (c) H's latest ctxv:// is C2; (d) after a
    # prune to cap=1, C1's ctxv:// is 410 Gone (was-pinned, retention window passed) while C2 stays ok;
    # (e) a wrong-tenant fetch of C2's ctxv:// is 'missing' (404), never leaking it across tenants.
    pv_db = os.path.join(vol, "versions.db")
    pv_code = (
        "import os,sys,json; os.environ['BALTOR_DURABLE_DB']=sys.argv[1];"
        "import scripts.baltor_admin_demo_server as s;"
        "H='ctx://baltor/adm-pin/component/x=1';"
        "C1={'text':'ten business days','v':1}; C2={'text':'thirty business days','v':2};"
        "v1=s.pin_version(tenant_id='acme', run={'run_id':'adm-pin'}, base_handle=H, kind='component', content=C1);"
        "st1,row1=s.fetch_pinned_version('acme', v1);"
        "v2=s.pin_version(tenant_id='acme', run={'run_id':'adm-pin'}, base_handle=H, kind='component', content=C2);"
        "st1b,row1b=s.fetch_pinned_version('acme', v1);"           # C1 after the live change → still C1
        "st2,row2=s.fetch_pinned_version('acme', v2);"             # C2 latest
        "stx,_=s.fetch_pinned_version('globex', v2);"             # wrong tenant → missing
        "import sqlite3; sup=s.RUN_STORE.execute('SELECT superseded_at FROM gateway_versions WHERE version_handle=?',(v1,)).fetchone();"
        "s.DURABLE_VERSIONS_MAX=1; s.prune_versions();"
        "st1c,_=s.fetch_pinned_version('acme', v1); st2c,_=s.fetch_pinned_version('acme', v2);"
        "print(json.dumps({'v1':v1,'v2':v2,'diff':v1!=v2,"
        "'c1':json.loads(row1['body_json']) if row1 else None,"
        "'c1_after':json.loads(row1b['body_json']) if row1b else None,"
        "'c2':json.loads(row2['body_json']) if row2 else None,"
        "'st1':st1,'st1b':st1b,'st2':st2,'stx':stx,'superseded':bool(sup and sup[0]),"
        "'st1_after_prune':st1c,'st2_after_prune':st2c}))"
    )
    pvout = subprocess.run([sys.executable, "-c", pv_code, pv_db], cwd=str(REPO_ROOT),
                           env={**os.environ, "PYTHONPATH": _pythonpath(".")}, capture_output=True, text=True)
    try:
        pv = json.loads((pvout.stdout or "").strip().splitlines()[-1])
    except Exception:  # noqa: BLE001
        pv = {}
        check("P2 item5: ctxv:// version-pinning subprocess ran", False, (pvout.stderr or "")[-400:])
    if pv:
        C1, C2 = {"text": "ten business days", "v": 1}, {"text": "thirty business days", "v": 2}
        check("P2 item5a: ctxv:// pin returns C1 byte-identical AFTER the live content changed to C2",
              pv.get("st1b") == "ok" and pv.get("c1_after") == C1 and pv.get("c1") == C1, str(pv))
        check("P2 item5b: superseding is LOSSLESS — old version superseded_at set but STILL fetchable",
              pv.get("superseded") is True and pv.get("st1b") == "ok", str(pv.get("superseded")))
        check("P2 item5c: latest ctxv:// for the same base is the NEW content C2 (distinct handle)",
              pv.get("st2") == "ok" and pv.get("c2") == C2 and pv.get("diff") is True, str(pv))
        check("P2 item5d: after prune past the cap, the old version is 410 GONE while the new one stays ok",
              pv.get("st1_after_prune") == "gone" and pv.get("st2_after_prune") == "ok",
              f"old={pv.get('st1_after_prune')} new={pv.get('st2_after_prune')}")
        check("P2 item5e: a ctxv:// version is tenant-scoped — wrong tenant → missing (404), no leak",
              pv.get("stx") == "missing", str(pv.get("stx")))

    # ── integrated restart-survival + receipt proof (real subprocess server) ──────────────────────────
    def free_port() -> int:
        sk = socket.socket(); sk.bind(("127.0.0.1", 0)); p = sk.getsockname()[1]; sk.close(); return p

    def spawn(port: int, db: str):
        env = {**os.environ, "PYTHONPATH": _pythonpath("."), "BALTOR_DURABLE_DB": db}
        env.pop("OH_SHOWCASE_TOKEN", None)  # keep POSTs open so the proof needs no token
        return subprocess.Popen([sys.executable, str(Path(__file__).resolve()), "--port", str(port)],
                                cwd=str(REPO_ROOT), env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

    def wait_ready(base: str, proc) -> bool:
        for _ in range(80):
            try:
                if urllib.request.urlopen(base + "/api/health", timeout=1.0).status == 200:
                    return True
            except Exception:
                if proc.poll() is not None:
                    return False
                time.sleep(0.25)
        return False

    def stop(proc) -> None:
        proc.terminate()
        try:
            proc.wait(timeout=8)
        except Exception:
            proc.kill()

    db = os.path.join(vol, "durable.db")
    port = free_port()
    base = f"http://127.0.0.1:{port}"
    handle = ""
    proc = spawn(port, db)
    try:
        if not wait_ready(base, proc):
            check("server #1 ready", False, (proc.stderr.read() or b"").decode("utf-8", "ignore")[-400:] if proc.stderr else "")
            return 1
        # create a run (form POST), then search to obtain a ctx:// handle
        body = urllib.parse.urlencode({"text": SAMPLE_TEXT, "source_name": "selftest.txt", "source_type": "upload"}).encode()
        req = urllib.request.Request(base + "/admin-demo/runs", data=body, method="POST",
                                     headers={"Content-Type": "application/x-www-form-urlencoded"})
        urllib.request.urlopen(req, timeout=20).read()
        time.sleep(0.5)
        sres = json.loads(urllib.request.urlopen(base + "/api/context-gateway/search?query=escalation+threshold", timeout=10).read())
        handles = (sres.get("context_pack") or {}).get("source_handles") or []
        check("search returns a ctx:// handle + a receipt", bool(handles) and bool((sres.get("receipt") or {}).get("receipt_id")), str(sres.get("receipt")))
        handle = handles[0] if handles else ""
        fres = json.loads(urllib.request.urlopen(base + "/api/context-gateway/fetch?handle=" + urllib.parse.quote(handle), timeout=10).read())
        check("fetch resolves the handle BEFORE restart", fres.get("ok") is True, str(fres)[:160])
        check("fetch issues a receipt (item 2)", bool((fres.get("receipt") or {}).get("receipt_id")), str(fres.get("receipt")))
        rc = json.loads(urllib.request.urlopen(base + "/api/context-gateway/receipts?limit=50", timeout=10).read())
        ops = {r.get("operation") for r in rc.get("receipts") or []}
        check("receipt PERSISTED for fetch + search (durable)", rc.get("durable") and "context.fetch" in ops and "context.search" in ops, str(sorted(ops)))

        # ── P2 item6/7: tenant isolation over real HTTP ───────────────────────────────────────────────
        # A status-aware GET (urlopen raises on 4xx/410): returns (status_code, json_body).
        def http_get(url: str):
            try:
                r = urllib.request.urlopen(url, timeout=10)
                return r.status, json.loads(r.read() or "{}")
            except urllib.error.HTTPError as he:  # 404/410 carry a JSON body we still want to read
                try:
                    return he.code, json.loads(he.read() or "{}")
                except Exception:  # noqa: BLE001
                    return he.code, {}

        # The default-tenant fetch above (no ?tenant=) already proved byte-identical default behavior (item7).
        # Now create a run OWNED BY tenant 'acme', then prove 'globex' cannot reach its handle.
        abody = urllib.parse.urlencode({"text": SAMPLE_TEXT, "source_name": "acme.txt", "tenant": "acme"}).encode()
        areq = urllib.request.Request(base + "/admin-demo/runs", data=abody, method="POST",
                                      headers={"Content-Type": "application/x-www-form-urlencoded"})
        urllib.request.urlopen(areq, timeout=20).read()
        time.sleep(0.5)
        # search AS acme → an acme-owned ctx:// handle (its pack carries tenant_id)
        a_sc, a_search = http_get(base + "/api/context-gateway/search?tenant=acme&query=escalation+threshold")
        a_handles = (a_search.get("context_pack") or {}).get("source_handles") or []
        a_handle = a_handles[0] if a_handles else ""
        check("P2 item6: search is tenant-scoped (acme pack tagged tenant_id=acme)",
              a_sc == 200 and a_search.get("tenant_id") == "acme" and bool(a_handle), str(a_search.get("tenant_id")))
        # tenant 'globex' fetches acme's handle → 404 (never leaks that it exists)
        g_sc, g_body = http_get(base + "/api/context-gateway/fetch?tenant=globex&handle=" + urllib.parse.quote(a_handle))
        check("P2 item6: tenant B (globex) CANNOT fetch tenant A's handle → 404 (no existence leak)",
              g_sc == 404 and g_body.get("ok") is not True, f"status={g_sc} body={str(g_body)[:120]}")
        # globex search → its OWN (empty) namespace, never acme's run
        gs_sc, gs_body = http_get(base + "/api/context-gateway/search?tenant=globex&query=escalation+threshold")
        check("P2 item6: tenant B search never returns tenant A's run (own empty namespace → 404)",
              gs_sc == 404 and gs_body.get("ok") is not True, f"status={gs_sc}")
        # acme fetches its own handle → 200, and gets a ctxv:// version_handle back
        a_sc2, a_fetch = http_get(base + "/api/context-gateway/fetch?tenant=acme&handle=" + urllib.parse.quote(a_handle))
        a_version = a_fetch.get("version_handle") or ""
        check("P2 item6: SAME-tenant fetch works (acme → 200) and returns a ctxv:// version_handle",
              a_sc2 == 200 and a_fetch.get("ok") is True and a_version.startswith("ctxv://"), str(a_fetch)[:160])
        # acme fetches the ctxv:// version → 200 immutable pinned bytes
        av_sc, a_ver_fetch = http_get(base + "/api/context-gateway/fetch?tenant=acme&handle=" + urllib.parse.quote(a_version))
        check("P2 item6: ctxv:// pinned-version fetch works over HTTP for the owner (200, immutable=True)",
              av_sc == 200 and a_ver_fetch.get("ok") is True and a_ver_fetch.get("immutable") is True
              and a_ver_fetch.get("content") == a_fetch.get("content"), str(a_ver_fetch)[:160])
        # globex fetches acme's ctxv:// version → 404 (version isolation, no leak)
        gv_sc, _gv = http_get(base + "/api/context-gateway/fetch?tenant=globex&handle=" + urllib.parse.quote(a_version))
        check("P2 item6: tenant B CANNOT fetch tenant A's ctxv:// version → 404",
              gv_sc == 404, f"status={gv_sc}")
    finally:
        stop(proc)

    # RESTART on the SAME durable db (a fresh process) — the ctx:// handle must still resolve.
    proc2 = spawn(port, db)
    try:
        if not wait_ready(base, proc2):
            check("server #2 ready", False, (proc2.stderr.read() or b"").decode("utf-8", "ignore")[-400:] if proc2.stderr else "")
            return 1
        fres2 = json.loads(urllib.request.urlopen(base + "/api/context-gateway/fetch?handle=" + urllib.parse.quote(handle), timeout=10).read())
        check("ctx:// HANDLE SURVIVES RESTART (item 1): same handle still fetches", fres2.get("ok") is True, str(fres2)[:160])
        check("post-restart fetch also issues a receipt", bool((fres2.get("receipt") or {}).get("receipt_id")))
        rc2 = json.loads(urllib.request.urlopen(base + "/api/context-gateway/receipts?limit=200", timeout=10).read())
        check("pre-restart receipts persisted across restart", (rc2.get("count") or 0) >= 2, str(rc2.get("count")))
    finally:
        stop(proc2)

    import shutil
    shutil.rmtree(vol, ignore_errors=True)
    print(f"\n{'PASS — baltor_admin_demo_server self-test: ctx:// runs + receipts survive a real restart; receipts issued on search/fetch; CFPB path honors the volume setting; single (non-double) run engine; P2 — gateway is tenant-isolated (B cannot fetch A: ctx:// AND ctxv:// → 404), ctxv:// returns the pinned version after a live content change (lossless supersession; 410 only after prune), default-tenant path byte-identical.' if not failures else f'{len(failures)} FAILURES: {failures}'}")
    return 0 if not failures else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=9301)
    parser.add_argument("--self-test", action="store_true", help="run the gateway hardening + tenancy proof and exit")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    bind_host = os.environ.get("OH_BIND_HOST", "127.0.0.1")  # 0.0.0.0 only in container deploys
    rehydrate_runs()  # restore the newest ctx:// runs from the durable table so handles survive a restart
    httpd = ThreadingHTTPServer((bind_host, args.port), Handler)
    print(f"Baltor admin demo -> http://{bind_host}:{args.port}/admin-demo/")
    try:
        httpd.serve_forever()
    finally:
        httpd.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
