# {{title}} API ({{area}})

> GENERATED STUB (standard.docs_page) — fill every section before promotion.

## Purpose
Expose {{title}} over HTTP as a projection-only route ({{route_path}}).

## Owner
{{owner}} — `scripts/api_{{area}}_handler.py`.

## Inputs
Request body to `{{route_path}}` (the handler is socket-free: `handle(method, path, body)`).

## Outputs
A `{{returns_contract}}` object; no secret markers.

## Contracts
Returns `{{returns_contract}}` (registered). Route registered with `projection_only: true`.

## Ports
n/a (delegates to the proven engine; the admin server delegates to this handler).

## Adapters
n/a.

## Registry entries
- `architecture/contract_registry.json#api_routes += GET {{route_path}}` (owner `scripts/api_{{area}}_handler.py`, projection_only)

## Proofs
`scripts/check_{{area}}_api.py --self-test`

## Commands
```
python3 scripts/check_{{area}}_api.py --self-test
```

## Limitations
Stub: `serve` raises NotImplementedError until wired to the engine; secret-marker guard is in place.

## Opportunities
Add a projection UI page that renders {{route_path}}.

## Next steps
Wire `serve` to the engine, make the proof pass, register the route, have MAIN delegate from the admin server.
