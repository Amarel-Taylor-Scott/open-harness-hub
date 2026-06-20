# Open Harness Hub — ONE image, two+ roles (web tier vs. foundry worker vs. cron).
# The web/API tier is request/response; the worker pulls partition jobs off the queue and
# runs the evidence-driven foundry; cron fires the daily factory. See
# docs/architecture/cloud-architecture.md. Override the command per service (render.yaml / K8s).
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

WORKDIR /app

# Core deps always; local deterministic context extras by default; scale platform
# extras (Celery, Prometheus, OTel) only when INSTALL_PLATFORM=1.
ARG INSTALL_PLATFORM=0
ARG INSTALL_CONTEXT_LOCAL=1
COPY requirements.txt requirements-platform.txt requirements-context-local.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
 && if [ "$INSTALL_CONTEXT_LOCAL" = "1" ]; then pip install --no-cache-dir -r requirements-context-local.txt; fi \
 && if [ "$INSTALL_PLATFORM" = "1" ]; then pip install --no-cache-dir -r requirements-platform.txt; fi

COPY . .

# Prebuild the catalog vector store (hash backend, offline, deterministic) INTO the image so the web
# tier boots instantly instead of rebuilding it on the first request. A real-embedder deploy
# (OH_EMBED_BACKEND + keys) transparently rebuilds for its own model on first boot. Non-fatal.
RUN python -m scripts.db.build_vector_store build >/dev/null 2>&1 || true

# Health: the foundry self-tests run offline with zero cost — a cheap liveness/readiness probe.
HEALTHCHECK --interval=5m --timeout=60s --start-period=20s \
    CMD python -m scripts.foundry.pipeline --self-test >/dev/null 2>&1 || exit 1

# Default role = the async queue worker. Web/cron override the command (see render.yaml).
CMD ["python", "-m", "scripts.foundry.worker", "--serve"]
