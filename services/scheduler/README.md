# scheduler/ — scheduled tier

No code here: the scheduled-tier DAGs live in `infra/airflow/dags/` (Airflow/Cloud Composer), with
Celery-beat and cron as alternatives (see `services/worker/celery_app.py`, `services/registry.yaml`).
