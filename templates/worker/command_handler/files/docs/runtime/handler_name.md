# {{title}} command handler

> GENERATED STUB (standard.docs_page) — fill every section before promotion.

## Purpose
Durable, idempotent processing of `{{command_type}}` jobs on the one durable store.

## Owner
{{owner}} — `scripts/handlers/{{handler_name}}.py`.

## Inputs
A CommandEnvelope payload with `command_type: {{command_type}}` enqueued onto `{{queue_name}}`.

## Outputs
A handler result dict + a durable Work-plane event (no second bus).

## Contracts
`command_type` `{{command_type}}`; idempotency_key content-addressed; verdict drives ack/nack.

## Ports
Reuses `scripts/durable_store.py` (DurableStore) — claim/ack/lease/DLQ; no new framework.

## Adapters
n/a (handler routes via the existing flywheel_worker default handler).

## Registry entries
- `architecture/contract_registry.json#command_types += {{command_type}}`
- `architecture/contract_registry.json#queue_names += {{queue_name}}`

## Proofs
`scripts/check_{{handler_name}}_handler.py --self-test`

## Commands
```
python3 scripts/check_{{handler_name}}_handler.py --self-test
```

## Limitations
Stub: `handle` raises NotImplementedError until implemented; permanent vs retryable failure split is wired.

## Opportunities
Route `{{command_type}}` from the worker fleet once the handler passes.

## Next steps
Implement the effect, emit the durable event, make the proof pass, register command_type + queue_name.
