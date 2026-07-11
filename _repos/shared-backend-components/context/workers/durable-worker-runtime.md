# Durable Worker Runtime (+ context.consume)

**Purpose.** Run governed work durably: claim → process → ack/nack, with idempotency, retry→DLQ, restart
survival, and exactly-once across parallel worker processes. The same loop now also runs **consumption as
durable work** via the `context.consume` command.

**Owner.** `scripts/flywheel_worker.py` (`default_handler`, `work_once`, `run_worker`, `PermanentJobError`).
**Queue/store.** `scripts/durable_store.py` (`DurableStore`). **No second worker framework / bus / store.**

## Command types handled (registered in `contract_registry.json#command_types`)

| command_type | does |
|---|---|
| `pipeline.run_step` | a CommandEnvelope through the ProcessorHarness (registry-only) |
| `pipeline.run` / `pipeline.step` | a versioned pipeline via the Pipeline Runtime |
| `tenant.doc` | decompose a tenant doc into atomic facts |
| **`context.consume`** | run the governed ingestion→consumption path through ConsumptionService, recording a ContextResponse durably |

## `context.consume` contract

```
{"command_type":"context.consume","tenant_id":"demo","corpus":"cfpb","source_snapshot_hash":"…","require_optimized":true}
```

Behavior (proven): claim → `run_cfpb_to_consumption` → append a durable `context.response.created` event carrying
the response_id, answer, served/held-out counts, and the verification+optimization+consumption receipt ids →
ack. **Idempotent** by `source_snapshot_hash` (`mark_processed("consumption", …)`): a duplicate snapshot is
skipped, never re-served. An **invalid** command (unknown corpus / missing fields) raises `PermanentJobError`
→ dead-letters immediately (no worker crash, no retry-budget burn). **Two worker processes serve a snapshot
exactly once.** Deterministic (injected clock `EPOCH_CONSUME`, no wall-clock).

## Durable guarantees (proven)

idempotency · retry→DLQ · restart survival · outbox · two-process exactly-once.

## Commands

```
PYTHONPATH=. python3 scripts/check_consumption_worker_command.py --self-test
PYTHONPATH=. python3 scripts/check_durable_worker_parallel.py --self-test
PYTHONPATH=. python3 scripts/check_durable_restart_survival.py --self-test
PYTHONPATH=. python3 scripts/check_invalid_command_envelope_safe_failure.py --self-test
```

## Known limitations / opportunities

- Queue backend is the local SQLite `DurableStore`; broker/KEDA/Postgres (DBOS/Temporal) are cataloged swap
  candidates behind the same claim/ack/lease/DLQ contract (no contract rewrite when swapped).
- `context.consume` is wired for `corpus=cfpb`; new corpora plug in behind the same command + ConsumptionService.
