"""Runtime I/O primitives shared by context workers.

These helpers keep operational state out of individual worker implementations:
artifacts, idempotency markers, heartbeats, and atomic JSON writes all use one
layout that works locally, in Docker, and when mounted into cloud workers.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from scripts._config import CONTEXT_WORKER_RUNTIME_SETTINGS
from scripts.db.runtime_settings import runtime_setting


CONTEXT_WORKER_RUNTIME_NAMESPACE = "baltor.context_worker.runtime"


def _worker_setting(name: str) -> str:
    return runtime_setting(
        namespace=CONTEXT_WORKER_RUNTIME_NAMESPACE,
        definitions=CONTEXT_WORKER_RUNTIME_SETTINGS,
        name=name,
    )


DEFAULT_RUNTIME_DIR = Path(_worker_setting("runtime_dir"))
DEFAULT_ARTIFACT_DIR = Path(_worker_setting("artifact_dir"))


def safe_token(value: object, *, fallback: str = "unknown") -> str:
    text = str(value or "").strip().lower()
    clean = "".join(ch if ch.isalnum() or ch in {"-", "_", "."} else "-" for ch in text)
    clean = "-".join(part for part in clean.split("-") if part)
    return clean[:96] or fallback


def stable_json_hash(value: Any) -> str:
    body = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(body.encode("utf-8", errors="ignore")).hexdigest()


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + f".tmp-{os.getpid()}")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


@dataclass(frozen=True)
class RuntimePaths:
    runtime_dir: Path = DEFAULT_RUNTIME_DIR
    artifact_dir: Path = DEFAULT_ARTIFACT_DIR

    @classmethod
    def from_env(cls) -> "RuntimePaths":
        return cls(
            runtime_dir=Path(_worker_setting("runtime_dir")),
            artifact_dir=Path(_worker_setting("artifact_dir")),
        )

    @property
    def heartbeat_dir(self) -> Path:
        return self.runtime_dir / "heartbeats"

    @property
    def idempotency_dir(self) -> Path:
        return self.runtime_dir / "idempotency"

    @property
    def status_dir(self) -> Path:
        return self.runtime_dir / "status"


class ArtifactStore:
    def __init__(self, paths: RuntimePaths | None = None) -> None:
        self.paths = paths or RuntimePaths.from_env()

    def job_dir(self, *, run_id: object, job_id: object) -> Path:
        return self.paths.artifact_dir / safe_token(run_id, fallback="run") / safe_token(job_id, fallback="job")

    def write_job_artifacts(self, record: dict[str, Any]) -> dict[str, Any]:
        job_id = record.get("job_id") or "job"
        run_id = record.get("run_id") or "run"
        base = self.job_dir(run_id=run_id, job_id=job_id)
        refs: dict[str, str] = {}
        for key in ("output", "warnings", "lifecycle", "runtime"):
            if key in record:
                target = base / f"{key}.json"
                atomic_write_json(target, {"kind": f"context_worker.{key}", key: record[key]})
                refs[key] = str(target)
        manifest = {
            "kind": "context_worker.artifact_manifest",
            "job_id": job_id,
            "run_id": run_id,
            "task": record.get("task"),
            "ok": record.get("ok"),
            "error": record.get("error", ""),
            "created_at": int(time.time()),
            "refs": refs,
        }
        manifest_path = base / "manifest.json"
        atomic_write_json(manifest_path, manifest)
        refs["manifest"] = str(manifest_path)
        return refs


class HeartbeatStore:
    def __init__(self, paths: RuntimePaths | None = None) -> None:
        self.paths = paths or RuntimePaths.from_env()

    def path_for(self, job_id: object) -> Path:
        return self.paths.heartbeat_dir / f"{safe_token(job_id, fallback='job')}.json"

    def write(self, *, job: dict[str, Any], runtime: object, stage: str, status: str, detail: dict[str, Any] | None = None) -> None:
        payload = {
            "kind": "context_worker.heartbeat",
            "ts": int(time.time()),
            "job_id": job.get("job_id"),
            "run_id": job.get("run_id"),
            "task": job.get("task"),
            "tenant_id": job.get("tenant_id"),
            "stage": stage,
            "status": status,
            "runtime": asdict(runtime) if hasattr(runtime, "__dataclass_fields__") else runtime,
            "detail": detail or {},
        }
        atomic_write_json(self.path_for(job.get("job_id")), payload)

    def list_recent(self, *, limit: int = 50) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for path in sorted(self.paths.heartbeat_dir.glob("*.json"), key=lambda item: item.stat().st_mtime, reverse=True)[:limit]:
            try:
                rows.append(json.loads(path.read_text(encoding="utf-8")))
            except (OSError, json.JSONDecodeError):
                continue
        return rows


class IdempotencyStore:
    def __init__(self, paths: RuntimePaths | None = None) -> None:
        self.paths = paths or RuntimePaths.from_env()

    def key_for(self, job: dict[str, Any]) -> str:
        explicit = str(job.get("idempotency_key") or "").strip()
        if explicit:
            return safe_token(explicit)
        basis = {
            "task": job.get("task"),
            "run_id": job.get("run_id"),
            "tenant_id": job.get("tenant_id"),
            "pass_index": job.get("pass_index"),
            "payload": job.get("payload"),
        }
        return stable_json_hash(basis)[:32]

    def path_for_key(self, key: str) -> Path:
        return self.paths.idempotency_dir / f"{safe_token(key, fallback='key')}.json"

    def acquire(self, job: dict[str, Any], *, runtime: object) -> dict[str, Any]:
        key = self.key_for(job)
        path = self.path_for_key(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        marker = {
            "kind": "context_worker.idempotency",
            "key": key,
            "status": "processing",
            "job_id": job.get("job_id"),
            "run_id": job.get("run_id"),
            "task": job.get("task"),
            "tenant_id": job.get("tenant_id"),
            "started_at": int(time.time()),
            "runtime": asdict(runtime) if hasattr(runtime, "__dataclass_fields__") else runtime,
        }
        try:
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
        except FileExistsError:
            try:
                existing = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                existing = {"kind": "context_worker.idempotency", "key": key, "status": "unknown"}
            if existing.get("status") != "complete":
                marker["resumed_from"] = existing
                atomic_write_json(path, marker)
                return {"acquired": True, "key": key, "path": str(path), "existing": existing, "resumed": True}
            return {"acquired": False, "key": key, "path": str(path), "existing": existing}
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(marker, indent=2, sort_keys=True) + "\n")
        return {"acquired": True, "key": key, "path": str(path), "existing": None}

    def close(self, key: str, *, status: str, record: dict[str, Any]) -> None:
        path = self.path_for_key(key)
        payload = {
            "kind": "context_worker.idempotency",
            "key": key,
            "status": status,
            "job_id": record.get("job_id"),
            "run_id": record.get("run_id"),
            "task": record.get("task"),
            "ok": record.get("ok"),
            "error": record.get("error", ""),
            "finished_at": int(time.time()),
            "artifact_refs": record.get("artifact_refs", {}),
        }
        atomic_write_json(path, payload)


def runtime_health(paths: RuntimePaths | None = None) -> dict[str, Any]:
    paths = paths or RuntimePaths.from_env()
    for directory in (paths.runtime_dir, paths.artifact_dir, paths.heartbeat_dir, paths.idempotency_dir, paths.status_dir):
        directory.mkdir(parents=True, exist_ok=True)
    probe = paths.status_dir / f"write-probe-{os.getpid()}.json"
    atomic_write_json(probe, {"ok": True, "ts": int(time.time())})
    try:
        probe.unlink()
    except OSError:
        pass
    return {
        "ok": True,
        "runtime_dir": str(paths.runtime_dir),
        "artifact_dir": str(paths.artifact_dir),
        "heartbeat_dir": str(paths.heartbeat_dir),
        "idempotency_dir": str(paths.idempotency_dir),
        "status_dir": str(paths.status_dir),
    }
