# OpenHubForAI — ONE image, two+ roles (web tier vs. foundry worker vs. cron).
# The web/API tier is request/response; the worker pulls partition jobs off the queue and
# runs the evidence-driven foundry; cron fires the daily factory. Override the command per service.
#
# BUILD CONTEXT = _repos/ (the parent of the product repos), so the image can include BOTH the
# substrate (shared-backend-components) AND the cross-repo product backends (teleon/openhubforai/
# baltor) that services import as `src.<x>`. This replicates scripts/_repo_paths.install(), which
# adds every _repos/<x>/backend to sys.path. Without the backends, identity/registry/etc. crash with
# `ModuleNotFoundError: No module named 'src'` at container start. See deploy/docker-compose.deploy.yml
# (context: ../..) — the .dockerignore lives at _repos/ (the context root).
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

WORKDIR /app

# Core deps always; local deterministic context extras by default; scale platform
# extras (Celery, Prometheus, OTel) only when INSTALL_PLATFORM=1. Deps first for layer caching.
ARG INSTALL_PLATFORM=0
ARG INSTALL_CONTEXT_LOCAL=1
COPY shared-backend-components/requirements.txt shared-backend-components/requirements-platform.txt shared-backend-components/requirements-context-local.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
 && if [ "$INSTALL_CONTEXT_LOCAL" = "1" ]; then pip install --no-cache-dir -r requirements-context-local.txt; fi \
 && if [ "$INSTALL_PLATFORM" = "1" ]; then pip install --no-cache-dir -r requirements-platform.txt; fi

# The substrate (scripts/, catalog/, architecture/, config) -> /app.
COPY shared-backend-components/ /app/
# The .aidoneright-root marker lives only at the monorepo root (outside the build context), so create it
# here: repo_root()/_repo_paths.py resolve /app as the root explicitly, not by a fragile parents[] fallback.
RUN : > /app/.aidoneright-root
# The cross-repo product backends so `import src.<x>` resolves (PYTHONPATH=/app -> /app/src/<x>).
# Mirrors _repo_paths.install(): every _repos/<x>/backend/src/<x> becomes /app/src/<x>.
COPY teleon/backend/src/teleon /app/src/teleon
COPY openhubforai/backend/src/openhubforai /app/src/openhubforai
COPY baltor/backend/src/baltor /app/src/baltor
# The per-brand frontends, at the exact path the showcase's web/<brand> resolver maps to in-container
# (repo_root()=/app -> /app/_repos/<repo>/frontend). Without these the web tier serves the skinny stub.
COPY openhubforai/frontend /app/_repos/openhubforai/frontend
COPY teleon/frontend /app/_repos/teleon/frontend
COPY baltor/frontend /app/_repos/baltor/frontend
COPY aidevobserver/frontend /app/_repos/aidevobserver/frontend
COPY aidoneright/frontend /app/_repos/aidoneright/frontend
COPY aidevobserver/frontend /app/_repos/aidevobserver/frontend

# Prebuild the catalog vector store (hash backend, offline, deterministic) INTO the image so the web
# tier boots instantly instead of rebuilding it on the first request. Non-fatal.
RUN python -m scripts.db.build_vector_store build >/dev/null 2>&1 || true

# Health: the foundry self-tests run offline with zero cost — a cheap liveness/readiness probe.
HEALTHCHECK --interval=5m --timeout=60s --start-period=20s \
    CMD python -m scripts.foundry.pipeline --self-test >/dev/null 2>&1 || exit 1

# Default role = the async queue worker. Web/cron override the command (see the compose file).
CMD ["python", "-m", "scripts.foundry.worker", "--serve"]
