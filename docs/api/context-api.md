# Context API (C-CONSUME-1) — serving ContextResponse over HTTP

**Purpose.** Expose the proven `ConsumptionService` over read/projection-safe HTTP so an agent can fetch a
served `ContextResponse.v1` (verified + promoted + receipted facts, held-out warnings separate). The API never
computes truth — it delegates to `ConsumptionService` (`run_cfpb_to_consumption`).

**Owner.** `scripts/api_context_handler.py` (pure handler) + dispatch hooks in `scripts/baltor_admin_demo_server.py`.
**Contract.** `ContextResponse.v1` (`schemas/consumption/`). **Registry.** `architecture/contract_registry.json#api_routes`.

## Routes (all projection-only)

| Route | Returns |
|---|---|
| `POST /api/context/serve` | `ContextResponse.v1` from ConsumptionService (token-gated like all POSTs) |
| `GET /api/context/responses/<id>` | a previously served `ContextResponse.v1` |
| `GET /api/context/receipts/<id>` | the verification / optimization / consumption receipt |
| `GET /api/runtime/sections` | the section maturity matrix summary (the honest scoreboard) |
| `GET /api/runtime/consumption` | the latest served response summary |

## Request / response

```
POST /api/context/serve
{"tenant_id": "demo", "corpus": "cfpb", "require_optimized": true}
→ 200 ContextResponse.v1: answer "10 business days"; served_facts[] (each with source_handle +
   verification_receipt_id + optimization_receipt_id); held_out_warnings[] (FAQ-30, allegations);
   receipts{verification_receipt_id, optimization_receipt_id, consumption_receipt_id}; lineage; freshness.
```

Unknown corpus → `400`. Missing response/receipt id → `404` JSON. No secrets or private memory are ever emitted.

## Guarantees (proven)

- Only `ConsumptionService` output is served; the server fabricates nothing (`check_no_api_consumption_bypass`).
- No route bypasses the Verification / Optimization-promotion / Consumption-readiness gates.
- The handler imports no provider SDK / admin server / raw sqlite / global bus.
- The UI/dashboard consume **this** projection; they do not compute truth.

## Commands

```
PYTHONPATH=. python3 scripts/check_consumption_api.py --self-test
PYTHONPATH=. python3 scripts/check_context_response_retrieval_api.py --self-test
PYTHONPATH=. python3 scripts/check_runtime_sections_api.py --self-test
PYTHONPATH=. python3 scripts/check_no_api_consumption_bypass.py --self-test
```

Live smoke (server up):
```
curl -s -X POST "http://127.0.0.1:9307/api/context/serve?token=$(cat dist/baltor-admin-token.txt)" \
  -H "Content-Type: application/json" -d '{"tenant_id":"demo","corpus":"cfpb","require_optimized":true}' | python3 -m json.tool
```

## Known limitations / opportunities

- Retrieval is a process-level projection of deterministic responses; a durable response/receipt store is the
  next depth (OPP — not required because responses are deterministic + content-addressed).
- Only the `cfpb` corpus is wired; new corpora plug in behind the same handler.
- Adding routes here grows the admin-server monolith (split target — OPP-admin-monolith-split).
