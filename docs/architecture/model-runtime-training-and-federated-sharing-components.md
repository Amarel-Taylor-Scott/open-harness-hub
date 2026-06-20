# Model Runtime, Training, and Federated Sharing Components

Open Harness Hub should treat model operations as composable components, not as hidden deployment details. A user should be able to ask for a cheap local pipeline, a Kubernetes-hosted inference service, a fine-tuning job, or a federated reviewed-knowledge network and receive searchable building blocks with cost, risk, runtime, and review metadata.

## Component Families

Model/runtime components should cover:

- local model adapters such as Ollama, llama.cpp, local Gemma nodes, and offline edge runtimes;
- hosted inference runtimes such as vLLM, TGI, OpenAI-compatible gateways, and Kubernetes services;
- training jobs such as LoRA, QLoRA, distillation, data curation, benchmark building, and evaluation gates;
- model governance components such as model-card cost profilers, license checks, PII gates, prompt and output safety gates, and rollback plans;
- sharing components such as signed knowledge-object publishers, receivers, revocation records, hash receipts, and trust scoring.

These components are pre-LLM, LLM, and post-LLM pieces. A training data sensitive-content gate is pre-training. A local Gemma route is a model/runtime piece. A signed reviewed-object publisher is post-LLM governance and distribution.

## Federated Reviewed-Learning Pattern

The DueCare/Gemma pattern generalizes beyond one domain:

1. raw files, private case notes, personal narratives, IDs, and sensitive documents stay inside the local node;
2. local models extract candidate facts, graph edges, benchmark rows, evaluation failures, and rubric updates;
3. deterministic gates check provenance, redaction, signatures, licenses, consent, and privacy boundaries;
4. a human reviewer approves only the shareable object;
5. the shared layer receives signed, versioned, revocable knowledge objects, not raw cases.

The model weights do not need to change for the network to get smarter. The deterministic harness around the models improves as reviewed objects, benchmark rows, failure modes, and runtime metadata accumulate.

## Why This Belongs In The Registry

Training and runtime choices affect cost, accuracy, latency, privacy, and deployment management. If they are searchable components, the platform can recommend:

- cheap local-first pipelines for sensitive contexts;
- Kubernetes inference services when throughput matters;
- fine-tuning only when RAG, prompts, routing, and post-processing are insufficient;
- reviewed-object sharing when organizations need cross-node learning without pooling raw data;
- model swaps when pricing, context windows, or deployment constraints change.

## Data Shape

The first seed pack is `knowledge-pack/model-runtime-training-component-patterns`. It emits staged row families through `tool/model-runtime-training-seed-exporter`:

- normalized component candidates;
- canonical entities and object-entity references;
- labels and dimensions for runtime, training, deployment, cost, and privacy;
- embedding work rows;
- index records;
- review tickets for high-risk training and sharing components.

The rows remain staged candidates until reviewed, deduped, loaded, embedded, and promoted. The exporter does not download models, train weights, mutate Kubernetes, or apply SQL.

For daily expansion, `tool/model-ops-daily-runner` expands the curated seed patterns across model families, runtime targets, cost profiles, and privacy boundaries. It then writes the standard row families and runs the staged partition load audit.

```bash
python3 -m scripts.factory.model_ops_daily_run \
  --run-date YYYY-MM-DD \
  --output-dir dist/model-ops-daily-runs/YYYY-MM-DD \
  --target-count 1000
```

The daily runner is still side-effect free. It emits candidate rows and load SQL, but it does not execute the SQL, contact Kubernetes, download weights, or train a model.

After candidate generation, the vector-readiness path is:

```bash
python3 -m scripts.db.embedding_execution_plan \
  --object-embeddings-jsonl dist/model-ops-daily-runs/YYYY-MM-DD/rows/object-embeddings.jsonl \
  --output-dir dist/model-ops-daily-runs/YYYY-MM-DD/embedding-plan \
  --run-id model-ops-daily-YYYY-MM-DD-embedding-plan

python3 -m scripts.db.local_hash_embedding_worker \
  --embedding-plan dist/model-ops-daily-runs/YYYY-MM-DD/embedding-plan/embedding-execution-plan.json \
  --output-dir dist/model-ops-daily-runs/YYYY-MM-DD/local-hash-embedding-worker \
  --limit 1000

python3 -m scripts.db.pgvector_embedding_load_plan \
  --stored-vectors-jsonl dist/model-ops-daily-runs/YYYY-MM-DD/local-hash-embedding-worker/stored-vector-rows.jsonl \
  --source-embedding-rows-jsonl dist/model-ops-daily-runs/YYYY-MM-DD/rows/object-embeddings.jsonl \
  --output-dir dist/model-ops-daily-runs/YYYY-MM-DD/pgvector-load-plan

python3 -m scripts.db.embedding_committed_load_audit \
  --embedding-execution-plan dist/model-ops-daily-runs/YYYY-MM-DD/embedding-plan/embedding-execution-plan.json \
  --vector-readiness-summary dist/model-ops-daily-runs/YYYY-MM-DD/local-hash-embedding-worker/vector-readiness/vector-readiness-summary.json \
  --pgvector-load-plan-summary dist/model-ops-daily-runs/YYYY-MM-DD/pgvector-load-plan/pgvector-embedding-load-plan-summary.json \
  --output dist/model-ops-daily-runs/YYYY-MM-DD/embedding-committed-load-audit.json
```

This produces pgvector load SQL and a committed-load audit. Vector search remains marked not product-ready until an operator applies the SQL and provides committed Postgres counts.

For a local end-to-end database smoke plan that includes both staged component rows and embedding vectors:

```bash
python3 -m scripts.db.component_local_postgres_smoke_plan \
  --component-run-summary dist/model-ops-daily-runs/YYYY-MM-DD/model-ops-daily-run-summary.json \
  --load-audit-summary dist/model-ops-daily-runs/YYYY-MM-DD/load-audit/summary.json \
  --pgvector-load-plan-summary dist/model-ops-daily-runs/YYYY-MM-DD/pgvector-load-plan/pgvector-embedding-load-plan-summary.json \
  --embedding-execution-plan dist/model-ops-daily-runs/YYYY-MM-DD/embedding-plan/embedding-execution-plan.json \
  --vector-readiness-summary dist/model-ops-daily-runs/YYYY-MM-DD/local-hash-embedding-worker/vector-readiness/vector-readiness-summary.json \
  --output-dir dist/model-ops-daily-runs/YYYY-MM-DD/local-postgres-smoke
```

The plan emits Docker, `psql`, count-export, staged-load audit, and embedding-load audit commands. It does not run those commands automatically.

Before any local smoke commands are run, gate the plan:

```bash
python3 -m scripts.db.local_smoke_command_gate \
  --smoke-plan dist/model-ops-daily-runs/YYYY-MM-DD/local-postgres-smoke/component-local-postgres-smoke-plan.json \
  --output dist/model-ops-daily-runs/YYYY-MM-DD/local-postgres-smoke/command-gate.json
```

The gate classifies Docker, `psql`, and audit commands, writes a dry-run execution ledger, and lists approval items. It also does not execute commands.

The next layer can prepare an execution ledger for only policy-approved commands:

```bash
python3 -m scripts.db.local_smoke_approved_command_runner \
  --command-gate dist/model-ops-daily-runs/YYYY-MM-DD/local-postgres-smoke/command-gate.json \
  --output dist/model-ops-daily-runs/YYYY-MM-DD/local-postgres-smoke/approved-command-runner.json
```

By default this is also plan-only. `--execute-approved` runs only commands marked `allowed_by_default=true` and `requires_approval=false`, unless a run-scoped approval record is supplied. Docker and `psql` mutation commands remain blocked without matching approved command hashes.

For commands that require approval, create a run-scoped approval template:

```bash
python3 -m scripts.db.local_smoke_command_approval \
  --mode template \
  --command-gate dist/model-ops-daily-runs/YYYY-MM-DD/local-postgres-smoke/command-gate.json \
  --output dist/model-ops-daily-runs/YYYY-MM-DD/local-postgres-smoke/approval-template.json
```

The approval record is tied to command hashes and the single smoke-plan run. Verification is also side-effect free and must happen immediately before any future executor uses those approvals.

For the safest execution tests, require an approval record for every command that may run:

```bash
python3 -m scripts.db.local_smoke_approved_command_runner \
  --command-gate dist/model-ops-daily-runs/YYYY-MM-DD/local-postgres-smoke/command-gate.json \
  --approval-record dist/model-ops-daily-runs/YYYY-MM-DD/local-postgres-smoke/audit-only-approval.json \
  --require-approval-record \
  --execute-approved \
  --output dist/model-ops-daily-runs/YYYY-MM-DD/local-postgres-smoke/audit-only-execution.json
```

To merge an approval record into the runner ledger without executing anything:

```bash
python3 -m scripts.db.local_smoke_approved_command_runner \
  --command-gate dist/model-ops-daily-runs/YYYY-MM-DD/local-postgres-smoke/command-gate.json \
  --approval-record dist/model-ops-daily-runs/YYYY-MM-DD/local-postgres-smoke/approval-template.json \
  --output dist/model-ops-daily-runs/YYYY-MM-DD/local-postgres-smoke/approved-command-runner-with-approvals.json
```

## Guardrails

- Do not share raw case files or personal context across nodes.
- Do not train on private or licensed data without explicit approval and provenance.
- Treat fine-tuning as a governed pipeline, not a shortcut around retrieval, evaluation, or review.
- Every model/runtime component needs cost, deployment target, privacy boundary, and model-swap metadata.
- Every federated sharing component needs signatures, revocation, publisher identity, trust scoring, and review status.
