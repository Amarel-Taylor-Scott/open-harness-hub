# Local demo — no paid services, runs on the dev box

Baltor's local demo proves the contracts end-to-end with **only local/free components**. Two modes:

## Mode 0 — zero services (fastest)
The proof modules are pure Python and need no infra. Run any of:
```bash
python3 scripts/demo_context_engine_proof.py        # decompose → verify → keep-fresh (offline)
python3 scripts/demo_context_engine_proof.py --live # + a real OFAC SDN fetch
python3 scripts/baltor_flywheel.py --once           # green-check every proof module
python3 scripts/ingest/document_decompose.py --self-test
```
The foundry/connectors fall back to SQLite + offline fixtures (the connectors expose a `--live` flag
when you want a real fetch). This is the "prove the model" path — no Docker required.

## Mode 1 — local stack (cloud-equivalent)
Use the **existing** compose (do not add a new one): it mirrors the cloud topology 1:1.
```bash
docker compose -f infra/docker-compose.yml up --build   # Postgres+pgvector + Redis + web + worker
```
Other stacks already present: `infra/docker-compose.context.yml`, `infra/docker-compose.platform.yml`,
`infra/postgres/docker-compose.pgvector.yml`. Env contract: copy `.env.example` → `.env`. **No paid
APIs**; model/provider integration is local-first + OpenAI-compatible (point at a local Ollama if
present; degrade gracefully if no model is installed — the offline self-tests still pass).

Recommended additions for the full context-engine demo (local, free): **Qdrant** (hybrid retrieval),
**MinIO** (object store for raw/parsed artifacts), **OpenFGA + OPA** (policy), **Ollama** (local LLM).
Per the verified catalog (`data/backend-tools.yaml`): primary Qdrant→pgvector, Graphiti for the claim
graph, DBOS for durable workflows.

## The end-to-end demo flow (what to show)
1. **Ingest** a fixture doc → `document_decompose` → a recursive tree of `ctx://…#page=…` objects.
2. **Verify** against a live source → `sanctions_feed_live` → `verified_context_flow` (a would-be
   violation is held out of the served corpus with provenance).
3. **Keep fresh** → `context_rot` / `source_handle_resolver` (TTL/CDC/ACL).
4. **Pack + receipt** → build a context pack, enforce the **Gold-Pack Contract**
   (`scripts/check_gold_pack_contract.py`), issue a render receipt.
5. **Serve** → MCP descriptor / llms.txt (the M3 serving surface).

## Guard
`python3 scripts/validate_compose.py` keeps the compose files honest (stateful services must pin
their image — no `:latest`). It runs in the flywheel watchdog. Do NOT start real containers in CI.

## Runtime planes
See `docs/architecture/runtime-planes.md` — local = Docker Compose; K8s is only for the enterprise
worker plane, and durable workflows are not K8s Jobs.
