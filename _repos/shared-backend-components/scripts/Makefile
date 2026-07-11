# OpenHubForAI — dev shortcuts. Local runs need ZERO services (sqlite); the same
# commands run in cloud against Postgres+Redis purely by env (see .env.example).
.PHONY: help bootstrap test e2e foundry worker demand scrape ingest freshness ingest-health ingest-promote ingest-loop dev-up dev-down refresh check-org add-component split-plan

help:
	@echo "bootstrap  - pip install runtime deps"
	@echo "test       - run the full foundry self-test suite (offline, zero cost)"
	@echo "e2e        - end-to-end foundry pipeline proof"
	@echo "foundry    - run one daily factory batch (seeds --run; uses OLLAMA_API_KEY if set)"
	@echo "worker     - run the queue worker (--serve; sqlite queue local, redis in cloud)"
	@echo "demand     - mine logged user interactions -> capability-requests + research areas"
	@echo "scrape     - refresh registered sources (live; needs network + data/source-registry.jsonl)"
	@echo "ingest        - feed EVERY registered official source into the governed corpus (live)"
	@echo "freshness     - poll sources for changes (CDC) + enqueue reingest jobs (live)"
	@echo "ingest-health - reachability + parseability check of all source URLs (live)"
	@echo "ingest-loop   - run the freshness->feed loop forever (sidecar; sqlite local, postgres+redis cloud)"
	@echo "dev-up     - full local stack mirroring cloud (postgres+pgvector + redis + web + worker)"
	@echo "--- multi-repo org (derived from _repos/dev-rules-context/contracts/surface-registry.json) ---"
	@echo "refresh       - regenerate every derived artifact (edges/graph/interfaces/migration-plan) from the source"
	@echo "check-org     - drift gate: prove derived artifacts are in sync (run before a release / in CI)"
	@echo "add-component - onboard a new surface/project/repo the right way (registry first, then refresh)"
	@echo "split-plan    - build the history-preserving git-subtree split plan + per-project manifests"

bootstrap:
	pip install -r requirements.txt

test:
	@for m in contracts novelty standardize gate measure eval_scorers gaps sources construction openness \
	          access benchmark_synth interactions model_route queues store scrapers stage_load; do \
	  python -m scripts.foundry.$$m >/dev/null 2>&1 && echo "  ok $$m" || python -m scripts.foundry.$$m --self-test ; \
	done
	python -m scripts.foundry.pipeline --self-test >/dev/null && echo "  ok pipeline"
	python -m scripts.foundry.worker --self-test >/dev/null && echo "  ok worker"

e2e:
	python -m scripts.foundry.pipeline --self-test

foundry:
	python -m scripts.foundry.seeds --run

worker:
	python -m scripts.foundry.worker --serve

demand:
	python -m scripts.foundry.interactions --mine $${OH_STORE_PATH:-dist/interactions.jsonl}

scrape:
	python -m scripts.foundry.scrapers --refresh

ingest:
	python3 -m scripts.ingest.feed --all

freshness:
	python3 -m scripts.ingest.freshness --check --enqueue

ingest-health:
	python3 -m scripts.ingest.health --check

ingest-promote:
	python3 -m scripts.ingest.promote_staged --self-test

ingest-loop:
	python3 -m scripts.ingest.run --loop

dev-up:
	docker compose -f infra/docker-compose.yml up --build

dev-down:
	docker compose -f infra/docker-compose.yml down -v

# --- multi-repo org maintenance (single source: surface-registry.json; never hand-edit a derived file) ---
refresh:
	python3 scripts/refresh_all.py --write

check-org:
	python3 scripts/check_org_freshness.py
	python3 scripts/refresh_all.py --check

# usage: make add-component NAME=<name> KIND=<kind> ARGS="--may-depend-on a b --exposes cap"
add-component:
	python3 scripts/scaffold_component.py --name "$(NAME)" --kind "$(KIND)" $(ARGS) --write

split-plan:
	python3 scripts/build_migration_plan.py --write
