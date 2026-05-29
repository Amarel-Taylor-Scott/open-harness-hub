# Open Harness Hub — ONE image, two+ roles (web tier vs. foundry worker vs. cron).
# The web/API tier is request/response; the worker pulls partition jobs off the queue and
# runs the evidence-driven foundry; cron fires the daily factory. See
# docs/architecture/cloud-architecture.md. Override the command per service (render.yaml / K8s).
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Health: the foundry self-tests run offline with zero cost — a cheap liveness/readiness probe.
HEALTHCHECK --interval=5m --timeout=60s --start-period=20s \
    CMD python -m scripts.foundry.pipeline --self-test >/dev/null 2>&1 || exit 1

# Default role = the async queue worker. Web/cron override the command (see render.yaml).
CMD ["python", "-m", "scripts.foundry.worker", "--serve"]
