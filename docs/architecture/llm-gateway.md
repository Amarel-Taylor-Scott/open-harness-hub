# LLM Gateway v1

The rest of Baltor never calls OpenAI / Anthropic / Gemini / Ollama / vLLM directly. It builds an
`LLMRequest` and calls **`gateway.complete(request, policy)`**. The gateway is the only legal way to call a
model — so every model interaction is governed, validated, traced, and secret-safe.

Modules: `scripts/llm_gateway/{types,secrets,providers,validation,router}.py`. Secrets:
`scripts/security/tenant_store_resolver.py` (tenant) + `scripts/llm_gateway/secrets.py` (keys).

## Contracts (`types.py`)

`LLMRequest` (request_id, tenant_id, task_type, prompt_id/version, schema_id, data_classification,
input_artifact_ids, routing_policy, idempotency_key) → `LLMResponse` (provider, model, status, output_json,
`raw_response_ref` to object store, usage, validation, trace). `RoutingPolicy` carries preferred/fallback
providers, max_attempts, max_cost_usd, latency_slo_ms. `cache_key = hash(input_hash + prompt_hash +
model_config_hash)`.

## Providers (`providers.py`) — replaceable adapters

- `stub.local@v1` — deterministic, offline, no key; the default that proves the gateway end-to-end.
- `openai.responses@v1` — OpenAI Responses API; loads its key **only** from `api_key_ref` (`env://OPENAI_API_KEY`).
- `openai_compatible.http@v1` — any OpenAI-compatible `base_url` (Azure / vLLM / Ollama / custom).

Network is **off** unless `BALTOR_LLM_ALLOW_NETWORK=1`, so a self-test never makes a network call — a
configured-but-network-disabled provider raises a *retryable* error and the router falls back. The same
seam later admits Anthropic / Gemini / managed endpoints.

## Secrets (`secrets.py`) — refs only, never values

Provider config carries `api_key_ref="env://OPENAI_API_KEY"`, never a raw key. `SecretsResolver.get(ref)`
reads at runtime only and never logs the value; a missing secret raises `UnavailableSecret` naming the
*variable* (not a value), the provider is simply unavailable, and the system stays green. Proven by
`check_llm_secret_hygiene` (no raw `sk-` keys or inline `api_key` anywhere in source — with a precise
allowlist for synthetic redaction-test fixtures so a real key still fails).

## Router (`router.py`) — policy-aware selection, fallback on bad output

Selection order = routing_policy preferred + fallback. Before any call, each provider is **policy-gated**:
a tenant with `allow_external_api=false`, or data classified `restricted`, can never select an external
provider — this is an *exclusion* (`policy_blocked`), never retried as transport. Allowed providers are
attempted up to `max_attempts`; the router falls back to the next provider on a **retryable** failure
**or** a **validation** failure (not merely a transport error). Every attempt is recorded in `LLMTrace`
(provider, model, prompt_hash, model_config_hash, status, validation). A per-(input,prompt,model) cache
returns a prior good result without re-calling. If nothing validates → `status="needs_human"`.

## Validation (`validation.py`) — accept only good output

`transport · schema (declared JSON schema adherence) · grounding (claims cite KNOWN input artifact ids) ·
policy · cost · no-unknown-artifact-ids · no-promoted-claim-without-source`. A response is accepted only
when all pass. (Where a provider supports schema-constrained output, that is preferred over plain JSON.)

## Proofs

`check_llm_secret_hygiene` · `check_llm_gateway_stub` · `check_llm_gateway_openai_config` ·
`check_llm_router_policy` (all registered in the flywheel). Acceptance: LLM calls go only through the
gateway; configs use secret refs; OpenAI is optional and self-tests pass with no key and no network;
routing is policy-aware with retry/fallback/validation/tracing.

## Status / next

Built + proven: the gateway, providers (stub + OpenAI config-only + compat), secrets, validation, router,
and the hybrid storage pieces (`scripts/runtime/object_store.py` content-addressed blobs +
`projections.py` rebuildable projections). **Deferred to the next pass** (overlaps the existing
`scripts/pipeline_runtime/` runtime): routing the CFPB artifact-graph processors *through* the generic
`pipeline_runner` end-to-end, the `/runtime-demo` page, and the proofs `check_pipeline_manifest_generic`,
`check_cfpb_runtime_end_to_end`, `check_runtime_demo_api`. The existing `pipeline_runtime` already provides
versioned manifests, a processor registry, a durable runner, per-tenant isolation, and the
`unstructured_pdf_docling@v0` experimental manifest — so the remaining work is wiring, not new substrate.
