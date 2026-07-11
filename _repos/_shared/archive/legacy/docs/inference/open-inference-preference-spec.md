# Open Inference Preference Specification (OIPS) + the shared Inference Gateway

**Status:** core built + proven (`scripts/check_inference_gateway.py`, flywheel-registered). Code:
`src/teleon/inference/` (lives in **Teleon** — model routing is a runtime concern; Baltor + the open hubs
consume it via the allowed `Baltor → Teleon` direction, honoring `architecture/portfolio_dependency_law.json`).
It is the standard layer **above** the existing LLM gateway (`scripts/llm_gateway/`, `scripts/model_gateway.py`),
which becomes the primary provider adapter — not reinvented.

> **SHARED INFERENCE GATEWAY CLAUSE.** All LLM/model calls across Teleon, Baltor, and any Open*Hub surface go
> through one **Inference Gateway**. Every object may declare an **InferencePreference** (desired tier +
> specialization, allowed/disallowed provider **nodes**, data/budget/latency/fallback policy, provenance
> required). The gateway resolves preferences through inheritance, selects a provider via a **numeric** model
> graph, applies **governed fallback**, and writes a **ModelInvocationReceipt** recording the **actual** model
> used, the rejected candidates, the fallback reasons, hashes, cost/latency/tokens, and the **allowed
> downstream use**. Raw API keys live only behind `secret_ref`s. **LLM output is candidate/advisory — never
> served truth** (Baltor governs serving).

## The three asks, answered
1. **Shared router** — `src/teleon/inference/oips.py` (`select_provider`, `infer_local`) over the numeric
   `architecture/model_provider_graph.json`. One plane, not a wrapper per product.
2. **Object-level preferences (the standard)** — `InferencePreference.v1`: *the object declares intent.* Resolved
   via inheritance (`global → product → tenant → environment → object-type → instance → call`) with a
   `resolved_from` trail + a deterministic `effective_policy_hash`.
3. **Unavailable preferred model + provenance** — when the preferred provider is missing-secret / unhealthy /
   policy-blocked, it is **rejected with a reason code** and a **governed fallback** is chosen (never silent);
   `ModelInvocationReceipt.v1` records the actual node/model + the rejected candidates + the fallback trail.

## Numeric, not brittle strings
Runtime branches on numeric **codes** + node ids, never provider display names (the display-name-breaks-a-proof
trap). `model_quality_tier_codes` (100 local_stub … 500 frontier … 700 customer_private) ·
`model_specialization_codes` (classification…structured_output) · `model_provider_status_codes` ·
`model_provider_edge_type_codes` (CAN_FALLBACK_TO, REQUIRES_SECRET_REF, REQUIRES_LOCAL_EQUIVALENT, …). A new
model slots between others by number with no code change.

## Governed fallback → allowed use (not binary)
A fallback is not pass/fail — it changes what the output may be used for. `allowed_use` ∈
`draft · non_serving_explanation · candidate · promotable · served`. A lower-tier fallback yields a **candidate**
or **draft**, not a **promotable** output; the local stub yields **draft**. The gateway **never** emits
`served` — Baltor governs serving. Downstream gates read `allowed_use` to decide.

## Secrets + truth
- Preferences and the graph carry `secret_ref` (e.g. `secret://provider/openai`), **never raw keys**; nothing
  raw appears in routes, receipts, or logs (proven). Every external node also declares a `local_equivalent`
  (cloud-defer-after-local).
- `receipt.policy_checks.llm_output_is_truth == False` — model output is advisory; Baltor's verification /
  reconciliation / consumption gates remain the authority.

## Built vs queued
**Built + proven:** the 3 OIPS contracts, the numeric provider graph, preference inheritance, provider selection
+ governed fallback, the receipt, the local deterministic stub, and the proof. **Queued**
(`prompts/shared-inference-gateway-and-oips.md`): the remaining contracts (Request/Response/ProviderNode/Edge/
RouteDecision/Health/Cost), candidate adapter **files** (OpenAI/Anthropic/Gemini/Bedrock/Azure/LiteLLM/
OpenRouter/local-OpenAI-compat/customer-private — offline seams), `/api/inference/*` + the `/inference` UI panel,
object-integration across every object type, and the full inference redteam suite.
