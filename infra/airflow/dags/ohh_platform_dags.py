"""Airflow / Cloud Composer DAGs for the SCHEDULED tier (opt-in orchestrator above the queue —
docs/architecture/backend-services-and-platform.md). Each task runs the SAME real module a cron job
or Celery-beat would; Airflow adds per-task retries + visibility + backfill for the multi-step DAGs.

Drop this file in the Airflow `dags/` folder (or point Composer at infra/airflow/dags/). Import-safe
outside Airflow: if `airflow` isn't installed it defines nothing rather than crashing a syntax check.

    pip install -r requirements-platform.txt     # includes apache-airflow
"""
from __future__ import annotations

try:
    import pendulum
    from airflow import DAG
    from airflow.operators.bash import BashOperator
    _AIRFLOW = True
except Exception:  # pragma: no cover - only present inside an Airflow/Composer environment
    _AIRFLOW = False

PY = "python -m"
DEFAULT_ARGS = {"retries": 2, "retry_delay_seconds": 300}


def _module_task(dag, task_id: str, module: str, args: str = "") -> "BashOperator":
    return BashOperator(task_id=task_id, bash_command=f"{PY} {module} {args}".strip(), dag=dag)


if _AIRFLOW:
    _start = pendulum.datetime(2026, 1, 1, tz="UTC")

    # CDC / freshness sweep — poll registered sources, enqueue reingest. Every 30 min.
    with DAG("ohh_freshness", schedule="*/30 * * * *", start_date=_start, catchup=False,
             default_args=DEFAULT_ARGS, tags=["platform", "ingestion"]) as ohh_freshness:
        _module_task(ohh_freshness, "freshness_check", "scripts.ingest.freshness", "--check --enqueue")

    # Daily factory → promotion readiness — the multi-step pipeline (sequential, per-task retries).
    with DAG("ohh_daily_factory", schedule="0 7 * * *", start_date=_start, catchup=False,
             default_args=DEFAULT_ARGS, tags=["platform", "foundry", "governance"]) as ohh_daily_factory:
        seed = _module_task(ohh_daily_factory, "foundry_seed", "scripts.foundry.seeds", "--run")
        embed = _module_task(ohh_daily_factory, "embedding_execution", "scripts.db.embedding_execution_plan")
        readiness = _module_task(ohh_daily_factory, "promotion_readiness", "scripts.db.daily_promotion_readiness_plan")
        seed >> embed >> readiness

    # Feed every registered source into the governed corpus. Daily, off-peak.
    with DAG("ohh_corpus_ingest", schedule="0 3 * * *", start_date=_start, catchup=False,
             default_args=DEFAULT_ARGS, tags=["platform", "ingestion"]) as ohh_corpus_ingest:
        _module_task(ohh_corpus_ingest, "ingest_feed", "scripts.ingest.feed", "--all")


if __name__ == "__main__":
    print("OHH Airflow DAGs:", "loaded" if _AIRFLOW else "airflow not installed (opt-in: requirements-platform.txt)")
