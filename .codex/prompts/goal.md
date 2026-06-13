# /goal: Build The Three-Site Context Platform For Hours

You are an autonomous Codex/Claude agent working in this repository. Run for
hours. There is no terminal state until the human interrupts you or a hard safety
issue blocks all safe work.

## Mission

Polish the full three-site system into a credible local-first, cloud-ready
business and technical platform:

- **Baltor**: the context-control backbone that verifies, reconciles, refreshes,
  packages, and serves trusted context into existing agents/RAG systems.
- **Open Harness Hub**: the public standards/catalog surface for modular
  harnesses, workers, schemas, capabilities, and reusable agent infrastructure.
- **AI Done Right**: the narrative/research surface that explains why
  verified, current, traceable context is the durable enterprise AI control
  layer.

The work is not limited to exactly what the human typed. Do adversarial research,
compare alternatives, improve copy/design/architecture, and implement the most
defensible next improvements across product, engineering, GTM, pricing,
fundraising, operations, and cloud economics.

## Design And Reference Inputs

Read first:

1. `AGENTS.md`, `CLAUDE.md`, and `docs/codex/no-magic-values.md`
2. `README.md` and `taxonomy/SPEC.md`
3. `docs/codex/baltor-clean-context.md`
4. `docs/codex/baltor-context-control-current-state.md`
5. `docs/codex/baltor-context-control-iteration-plan.md`
6. `docs/codex/baltor-context-control-test-plan.md`
7. `docs/codex/baltor-autonomous-goal.md`
8. `docs/architecture/baltor-codebase-cleanup-plan.md`
9. `docs/architecture/baltor-model-and-document-pipeline.md`
10. `docs/architecture/baltor-stateless-worker-standard.md`
11. `docs/architecture/baltor-queue-priority-orchestration.md`
12. `docs/architecture/baltor-source-trust-and-adoption-policy.md`
13. `docs/strategy/baltor-gtm-fundraising-plan.md`
14. `docs/strategy/gtm-launch-guide.md`
15. `docs/architecture/low-cost-hosting-plan.md`
16. `docs/research/baltor-worker-orchestration-research.md`
17. `OpenHarness.zip` design files, if present. Inspect safely in a temporary
    directory and incorporate useful design/layout/copy ideas without overwriting
    current work.

Older docs remain substrate/history. When they conflict with the clean current
context, add supersession notes or update stale references opportunistically.

## Loop

```text
ORIENT   Read ledger, git status, current files, canonical context, and current product surfaces.
RESEARCH Compare current best practices, competitors, costs, and deployment options when facts may have changed.
PLAN     Pick one high-value unblocked improvement with technical or business leverage.
BUILD    Make durable repo changes: code, schemas, docs, pages, demos, plans, or validation.
VALIDATE Run focused checks and sanity-test the affected surface.
RECORD   Append a ledger entry with files changed, checks, decisions, and next action.
BRANCH   If blocked, switch paths without asking.
REPEAT
```

## Product Priorities

1. Keep the product story centered on **verified, current, reconciled,
   traceable, token-efficient context served into existing agents**.
2. Make `/admin-demo` a simple four-card console first: Load Data, Processing,
   Outputs, Download. Move details into dedicated pages.
3. Improve source setup flows: upload, zip, drive/docs connectors, website sync,
   public authority feeds, scheduled refresh, versioning, diff, and "last sync"
   status.
4. Build worker lifecycle visibility: queued, running, delayed, retried, blocked,
   complete, ETA, lane, cost estimate, and rare manual confirmation.
5. Serve updated context as text packs, RAG records, graph/hybrid retrieval,
   provenance/audit packets, and optional history-preserving facts.
6. Treat manual review as an exception after deterministic, small-model,
   search/tool, Hermes/OpenClaw, and frontier-model attempts are exhausted.

## Worker And Orchestration Priorities

1. Standardize stateless Python workers with:
   - manifest and capability declaration;
   - preflight checks;
   - typed input/output envelope;
   - idempotency and dedupe keys;
   - retry/backoff policy;
   - structured logs/traces;
   - clean shutdown;
   - artifact upload/download;
   - cost and token accounting;
   - deterministic replay fixtures.
2. Support worker classes:
   - CPU document workers: OCR, parse, chunk, classify, extract, graph;
   - audit workers: source trust, injection/spam/hijack review, archive capture;
   - research workers: web search, website browse, price/address/statute lookup,
     corporate hierarchy, M&A/news, capability/docs lookup;
   - orchestration workers: queue routing, lifecycle scans, requeue policy,
     adoption policy;
   - GPU/model workers: embeddings, local small-model passes, graph enrichment;
   - Hermes/OpenClaw workers: open-ended discovery that compiles successful
     nondeterministic procedures into cheaper deterministic rules/templates.
3. Keep local/cloud parity:
   - local: Docker Compose, SQLite/Postgres, Redis-compatible queue, Ollama or
     OpenAI-compatible local endpoints;
   - cloud: Kubernetes/KEDA worker pools, Temporal durable workflows, Argo batch
     jobs, managed queues, managed Postgres/pgvector, object storage, CDN.
4. Use serverless/cloud functions where better than Kubernetes:
   - low-duty webhooks;
   - source-change callbacks;
   - scheduled lightweight sync;
   - archive submissions;
   - simple queue fanout;
   - email events.
5. Research and document tradeoffs among Celery, Temporal, Argo, KEDA, managed
   queues, Cloud Run/Lambda/Fargate, GPU nodes, batch jobs, and always-on
   orchestrators.

## Business And GTM Priorities

Create and continuously refine a practical operating plan that includes:

1. Competitor analysis:
   - agent platforms;
   - RAG platforms;
   - knowledge graph vendors;
   - governance/GRC tools;
   - data catalog/lineage tools;
   - compliance monitoring tools;
   - web-monitoring and source-intelligence tools;
   - internal AI platform teams as the real competitor.
2. Pricing:
   - design partner pilot pricing;
   - startup/midmarket/enterprise tiers;
   - usage meters for documents, sources, workers, verification jobs, served
     context packs, and frontier model calls;
   - gross margin model by workload;
   - overage and committed-use pricing.
3. Cost modeling:
   - local dev and demo costs;
   - staging/prod hosting;
   - managed database/object storage/CDN/email/domain costs;
   - queue/orchestration costs;
   - CPU K8s worker costs;
   - GPU K8s worker costs;
   - serverless alternatives;
   - frontier model API costs;
   - observability/security/compliance costs.
4. Pro forma financials:
   - 12, 24, and 36-month revenue scenarios;
   - COGS by customer/workload;
   - cloud/model spend assumptions;
   - support and implementation labor;
   - runway and hiring plan;
   - gross margin, burn, ARR, ACV, CAC, payback, and expansion assumptions.
5. Marketing and sales budget:
   - founder-led outbound;
   - design partner program;
   - compliance/procurement/legal ops content;
   - demos, webinars, and technical deep dives;
   - conferences and targeted sponsorships;
   - case studies and benchmark reports;
   - website conversion paths and transactional email.
6. Fundraising:
   - seed narrative;
   - milestone plan;
   - investor target list categories;
   - use of funds;
   - defensibility;
   - risk register;
   - diligence packet;
   - demo script;
   - metrics to prove before raising.

## Website And Ops Priorities

Build or improve clear pages/guides for:

1. Git/dev/staging/prod setup.
2. Cloud account setup and IaC path.
3. Domain/DNS/CDN/SSL setup.
4. Transactional email setup.
5. Auth, billing, analytics, telemetry, and support inbox.
6. Local development with cheap models and optional frontier-model APIs.
7. Deployment cost estimates and scaling inflection points.
8. GTM launch checklist and weekly operating cadence.
9. Demo scripts for Baltor, Open Harness Hub, and AI Done Right.

## Engineering Priority Menu

1. Split monoliths:
   - `scripts/showcase/server.py`
   - `web/harness-hub/styles/admin-demo.css`
   - `scripts/context_workers/tasks.py`
2. Improve the admin demo, source sync pages, processing pages, output pages,
   and downloadable package flows.
3. Add or harden export APIs:
   - text pack;
   - RAG records;
   - graph package;
   - audit/provenance package;
   - hybrid serving bundle.
4. Add Postgres/source/version/diff records while keeping local JSON fallback.
5. Improve document processing, graph construction, source trust, and worker
   outputs.
6. Improve local model routing for Gemma/Ollama and hosted OpenAI-compatible APIs.
7. Add multi-source fact adoption, archive queueing, injection defense, and
   lifecycle requeue scanning.
8. Add deterministic fixtures for adversarial cases and queue-priority policy.
9. Keep schemas/components consistent across lifecycle fields and state history.
10. Clean stale context by supersession and consolidation, not broad deletion.

## Model And Worker Rules

- Run cheapest-first: deterministic -> small local model -> medium model ->
  Hermes/OpenClaw/frontier.
- Model routes go through `scripts/model_routes.py`.
- Embeddings go through `scripts/embeddings.py`.
- Local default should work with Ollama/Gemma-style OpenAI-compatible endpoints.
- Hosted routes must use env vars only.
- Hash embeddings are staging-only and never promotable.
- Expensive workers must write deterministic rules/templates/checks when possible.
- New facts should require configured multi-source/adoption policy before serving
  as current; preserve provenance/history when serving updated facts.
- Queue priority should be driven by source risk, freshness, customer impact,
  agent usage, failed attempts, adoption state, and availability of authoritative
  sources.

## Validation Menu

Use the smallest meaningful check set:

```bash
node --check web/harness-hub/admin-demo.js
node --check web/harness-hub/admin-demo-assets/app.js
node --check web/harness-hub/admin-demo-assets/renderers.js
python3 -m py_compile scripts/showcase/server.py
python3 -m py_compile scripts/context_workers/*.py
python3 -m scripts.context_workers.runner --self-test
python3 scripts/validate.py
.venv/bin/python -m mkdocs build
```

For catalog/schema changes, follow `AGENTS.md`.

## Standing Rules

- Do not ask the human to decide reasonable implementation details.
- Do research when current facts, competitor claims, hosting prices, model prices,
  or best practices may have changed.
- Do not stop because a provider, scraper, dependency, or cloud service is
  unavailable.
- Do not store secrets, real PII, or proprietary customer data.
- Do not republish `_reference/`.
- Preserve user changes and ignore dirty-worktree noise.
- Avoid product-facing terms that create unnecessary concern: "fragile facts",
  "conflict-aware", "cache-shaped", and "replacement". Prefer verified,
  current, reconciled, traceable, modular, token-efficient, lifecycle-managed,
  and serving-ready.

After each cycle, record the ledger entry and immediately continue.
