# API Interface Primitives — endpoints are a primitive factory

> An API endpoint is **source material**, not a primitive. A production primitive is an endpoint wrapped with
> schema validation, auth policy, side-effect metadata, idempotency/retry policy, error normalization, a mock,
> contract tests, provenance, and telemetry. Importer: `scripts/import_openapi_as_api_primitives.py`. Schema:
> `schemas/api_interface_primitive.schema.json`. This is the **fourth primitive class** — after pure
> functions, external-tool enrichment, and standard specs — and it flows the identical governance.

## What the importer does (offline, deterministic)

`import_openapi(spec, provider=, service=)` parses an OpenAPI dict/file (it **never** calls the network) and
emits, per operation:

1. one **interface primitive** — the governed wrapper, carrying the §15 contract: `semantic_action`
   (read/search/classify/standardize/create/update/delete/submit/reconcile inferred from method+path+opId),
   input/output/error schema, auth + scopes, side-effect level, idempotency, pagination, reliability policy,
   cost model, compilation targets, and `provenance.spec_hash`;
2. its **sub-primitive bundle** — `request_builder · request_schema_validator · response_normalizer ·
   error_mapper · side_effect_gate` (a small pack, not one giant wrapper).

## Safety inferred from the method (not guessed)

| Method | semantic_action | side-effect | safe_to_retry | risk_tier |
|---|---|---|---|---|
| GET/HEAD | read / search | none | yes | low risk / safe |
| POST | create | write_external | **no** (unless Idempotency-Key present) | review required |
| PUT | update | write_external | yes | review required |
| PATCH | update | write_external | no | review required |
| DELETE | delete | delete | yes | review required |
| any on a `payment/charge/payout/transfer/refund/ledger` path | — | **money_movement** | — | **high risk**, `never_final_adverse_decision` |

Every interface primitive is `execution_model=external_tool`, `determinism_level=D2_bounded_external`,
`permission_class=network egress`, `lifecycle_stage=candidate`, `needs_executor=true`, `serves_truth=false`.
A write endpoint with no idempotency key gets `max_retries=0` — we never auto-retry a non-idempotent write.

## Ingestion order (endpoints, tests, and examples are the value)

OpenAPI specs → operations/schemas/auth/errors. Postman collections → real request/response **fixtures** +
test scripts (often higher-value than prose docs). Google Discovery / GitHub OpenAPI / AsyncAPI / GraphQL
introspection / MCP manifests → the same interface-primitive shape. **Rule: examples and tests are more
valuable than documentation prose.** MCP is the export plug; the registry is the trust breaker-box — imported
MCP tools enter quarantined, never certified.

## Compilation targets

Each interface primitive declares its targets: `python_client · typescript_client · mcp_tool ·
openai_tool_schema · mock_server · contract_test`. The candidate spec becomes a validated primitive only after
the executor + verifier + mock + contract tests are generated and the security/benchmark/lifecycle gates pass.

## LLM endpoints are their own family (next)

LLM endpoints (OpenRouter/LiteLLM/Portkey/Bedrock routing) need extra fields — model_id, context_window,
modalities, supports_tools/structured_output/streaming/batch/prompt_caching, cost-per-token, data-retention
and region policy, quality-benchmark refs, fallback compatibility. The **router** should be *deterministic*
even though the model is stochastic: task-family → policy filter → provider route → response verifier → cost
receipt (the best route is often **no model call** — a compiled primitive). Queued as an `llm_endpoint`
extension of this schema.

## Run it

```bash
python3 scripts/import_openapi_as_api_primitives.py --self-test
python3 scripts/import_openapi_as_api_primitives.py --spec openapi.json --provider stripe --service billing \
  --out artifacts/api_primitives/billing.jsonl
```
