"""Celery adapter for the async + scheduled tiers — OPT-IN.

The default broker is the light `RedisQueue` + built-in worker loop (scripts/foundry/queues.py,
worker.py) — see docs/architecture/backend-services-and-platform.md. This module is the Celery option
the existing design explicitly allows ("Celery / RQ / SQS all satisfy the same protocol"): pick it
when you want Celery's per-queue routing, beat scheduler, and Flower monitoring at scale.

Tasks invoke the SAME real module entrypoints cron/Airflow would (no logic forked here — honest
adapter). Queues mirror the service concerns. Celery is a scale extra (requirements-platform.txt);
this module imports safely without it so the repo's self-tests still pass.

    pip install -r requirements-platform.txt
    celery -A services.worker.celery_app worker -Q foundry,ingest,enrich,measure -l info
    celery -A services.worker.celery_app beat -l info        # the scheduled tier
"""
from __future__ import annotations

import os
import subprocess
import sys

from services.platform._shared import telemetry

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

try:
    from celery import Celery  # type: ignore
    from celery.schedules import crontab  # type: ignore
    _CELERY = True
except Exception:  # pragma: no cover - opt-in extra
    _CELERY = False


def _run_module(module: str, *args: str) -> int:
    """Run a real platform entrypoint as a subprocess (exactly what cron/Airflow trigger)."""
    telemetry.configure("worker")
    with telemetry.span("task.run_module", module=module, args=list(args)):
        proc = subprocess.run([sys.executable, "-m", module, *args])
        telemetry.counter("ohh_task_runs_total", "platform module task runs", ("module",)).labels(module=module).inc()
        return proc.returncode


if _CELERY:
    app = Celery("ohh", broker=REDIS_URL, backend=os.environ.get("CELERY_RESULT_BACKEND") or None)
    app.conf.update(
        task_default_queue="foundry",
        task_routes={
            "ohh.foundry.*": {"queue": "foundry"},
            "ohh.ingest.*": {"queue": "ingest"},
            "ohh.enrich.*": {"queue": "enrich"},
            "ohh.measure.*": {"queue": "measure"},
        },
        task_acks_late=True,            # ack after success — pairs with the foundry's idempotent re-runs
        worker_prefetch_multiplier=1,   # long, cost-gated jobs — don't hoard
    )

    @app.task(name="ohh.foundry.seed")
    def foundry_seed():                 # one daily factory batch
        return _run_module("scripts.foundry.seeds", "--run")

    @app.task(name="ohh.ingest.feed")
    def ingest_feed():                  # feed every registered source into the governed corpus
        return _run_module("scripts.ingest.feed", "--all")

    @app.task(name="ohh.ingest.freshness")
    def freshness_check():              # CDC: poll sources, enqueue reingest
        return _run_module("scripts.ingest.freshness", "--check", "--enqueue")

    @app.task(name="ohh.measure.promotion_readiness")
    def promotion_readiness():          # governance: who is load-ready vs blocked
        return _run_module("scripts.db.daily_promotion_readiness_plan")

    # the scheduled tier (Celery beat) — the same DAGs Airflow/Composer would run
    app.conf.beat_schedule = {
        "freshness-every-30m": {"task": "ohh.ingest.freshness", "schedule": 1800.0, "options": {"queue": "ingest"}},
        "daily-factory": {"task": "ohh.foundry.seed", "schedule": crontab(hour=7, minute=0), "options": {"queue": "foundry"}},
        "daily-promotion-readiness": {"task": "ohh.measure.promotion_readiness", "schedule": crontab(hour=8, minute=0), "options": {"queue": "measure"}},
    }
else:                                   # import-safe stub when celery isn't installed
    app = None


def self_test() -> int:
    if not _CELERY:
        print("celery adapter: NOT installed (opt-in scale extra — pip install -r requirements-platform.txt)")
        return 0
    tasks = sorted(t for t in app.tasks if t.startswith("ohh."))
    print(f"celery adapter ok · broker={REDIS_URL} · queues=foundry,ingest,enrich,measure · tasks={tasks}")
    return 0


if __name__ == "__main__":
    raise SystemExit(self_test())
