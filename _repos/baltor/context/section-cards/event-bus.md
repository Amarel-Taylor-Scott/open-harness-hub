# Event Bus — section card

Section: `event_bus` (category: runtime) · critical-path.

## Purpose

The event bus is the ONE in-process channel every Baltor component emits lifecycle events onto — the substrate
for the realtime dashboard. Components publish; the admin server's SSE route (`/api/events/stream`) and
`log_event(...)` drain from the SAME bus, so a user can watch the system fire live. Events carry a MONOTONIC
`seq` (NOT wall-clock), so an offline replay is byte-for-byte deterministic and there is no second event
channel to drift out of sync.

## Owner module

`_repos/shared-backend-components/scripts/context_events.py` — `EventBus` (`publish`, `subscribe`, `recent`, `clear`, `restore`,
`by_correlation`) and the `emit(...)` helper. Registered runtime owner `EventBus`
(`_repos/shared-backend-components/architecture/runtime_ownership.json#EventBus`).

## Contracts

Input: `EventEnvelope`. Output: `event` (carrying a monotonic `seq` + correlation fields).

## Proof scripts

`_repos/shared-backend-components/scripts/context_events.py` (own `--self-test`), `_repos/shared-backend-components/scripts/check_event_integration.py`,
`_repos/shared-backend-components/scripts/check_event_envelope.py` — all registered in the flywheel.

## Commands

```bash
PYTHONPATH=. python3 _repos/shared-backend-components/scripts/context_events.py --self-test
PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_event_integration.py --self-test
PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_event_envelope.py --self-test
```

## Limitations

The bus is in-process (single runtime) by design — it is the demo/ops substrate, not a distributed broker.
Subscribers run in the same process; cross-process fan-out would need a real broker behind the same
`EventBusPort`.

## Opportunities

Back the same `EventBusPort` with a durable/cross-process broker for multi-worker deployments without changing
emitters.
