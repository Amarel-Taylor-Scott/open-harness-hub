"""Readiness checks for the Baltor admin demo local/cloud path."""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]


def _file_check(label: str, path: str) -> dict[str, Any]:
    target = ROOT / path
    return {
        "id": label,
        "status": "ready" if target.exists() else "missing",
        "detail": path,
        "required_for": "local_and_cloud",
    }


def _module_check(label: str, module: str, *, required_for: str = "local_and_cloud") -> dict[str, Any]:
    return {
        "id": label,
        "status": "ready" if importlib.util.find_spec(module) is not None else "missing",
        "detail": module,
        "required_for": required_for,
    }


def _env_check(label: str, key: str, *, local_default: str = "") -> dict[str, Any]:
    value = os.environ.get(key)
    return {
        "id": label,
        "status": "configured" if value else "local_default",
        "detail": key if value else f"{key} not set; using {local_default or 'demo default'}",
        "required_for": "cloud",
    }


def _worker_count() -> int:
    from scripts.context_workers.tasks import ensure_registered
    from scripts.context_workers.registry import registry

    ensure_registered()
    return len(registry.manifest())


def admin_demo_readiness() -> dict[str, Any]:
    """Return local and cloud readiness state for the six-tile demo."""
    worker_count = _worker_count()
    checks = [
        _file_check("six_tile_ui", "web/harness-hub/admin-demo.html"),
        _file_check("admin_demo_assets", "web/harness-hub/admin-demo-assets/app.js"),
        _file_check("admin_demo_styles", "web/harness-hub/styles/admin-demo/base.css"),
        _module_check("admin_demo_api", "scripts.showcase.admin_demo.routes"),
        _module_check("export_packages", "scripts.showcase.admin_demo.exports"),
        _module_check("source_sync", "scripts.showcase.admin_demo.source_sync"),
        _module_check("worker_registry", "scripts.context_workers.registry"),
        _module_check("worker_runner", "scripts.context_workers.runner"),
        _module_check("queue_backend", "scripts.foundry.queues"),
        _module_check("model_gateway", "scripts.model_gateway"),
        _file_check("local_compose", "infra/docker-compose.context.yml"),
        _file_check("k8s_worker", "infra/k8s/context-worker.yaml"),
        _file_check("k8s_web", "infra/k8s/web.yaml"),
        _file_check("argo_batch", "infra/k8s/argo-context-pipeline.yaml"),
        _file_check("observability", "infra/observability/otel-collector.yaml"),
        _env_check("database_url", "DATABASE_URL", local_default="filesystem run store"),
        _env_check("redis_url", "REDIS_URL", local_default="in-process demo runner"),
        _env_check("showcase_token", "OH_SHOWCASE_TOKEN", local_default="open local demo"),
    ]
    ready = sum(1 for check in checks if check["status"] in {"ready", "configured", "local_default"})
    missing = [check for check in checks if check["status"] == "missing"]
    cloud_required = [check for check in checks if check["required_for"] == "cloud"]
    cloud_configured = sum(1 for check in cloud_required if check["status"] == "configured")
    return {
        "status": "ready" if not missing else "partial",
        "local": {
            "status": "ready" if not missing else "partial",
            "checks_ready": ready,
            "checks_total": len(checks),
            "worker_count": worker_count,
        },
        "cloud": {
            "status": "configured" if cloud_configured == len(cloud_required) else "needs_configuration",
            "configured": cloud_configured,
            "required": len(cloud_required),
            "missing_env": [check["id"] for check in cloud_required if check["status"] != "configured"],
        },
        "api_endpoints": [
            "POST /api/admin-demo/runs",
            "GET /api/admin-demo/runs/{run_id}",
            "GET /api/admin-demo/runs/{run_id}/exports/manifest",
            "GET /api/admin-demo/runs/{run_id}/exports/text",
            "GET /api/admin-demo/runs/{run_id}/exports/rag",
            "GET /api/admin-demo/runs/{run_id}/exports/graph",
            "GET /api/admin-demo/runs/{run_id}/exports/audit",
            "GET /api/admin-demo/readiness",
        ],
        "deployment_paths": [
            "Local stdlib showcase server for the six-tile demo.",
            "Docker Compose with Postgres/pgvector, Redis, and context worker.",
            "Kubernetes web and context-worker manifests with KEDA-ready queue scaling.",
            "Argo workflow templates for bounded batch processing.",
        ],
        "checks": checks,
    }


__all__ = ["admin_demo_readiness"]
