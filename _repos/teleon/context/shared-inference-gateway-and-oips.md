> **EDITOR'S NOTE (captured 2026-06-06 from the owner).** Canonical spec for the shared **Inference Gateway** +
> **Open Inference Preference Specification (OIPS)**. Executed INCREMENTALLY. **DONE + proven (flywheel 338):**
> the core — `_repos/teleon/backend/src/teleon/inference/oips.py` (preference inheritance · numeric provider selection · governed
> fallback · ModelInvocationReceipt · local deterministic stub); contracts
> `_repos/shared-backend-components/schemas/inference/{InferencePreference,ResolvedInferencePreference,ModelInvocationReceipt}.v1` (registered);
> numeric graph `_repos/shared-backend-components/architecture/model_{quality_tier,specialization,provider_status,provider_edge_type}_codes.json`
> + `model_provider_graph.json`; proof `_repos/shared-backend-components/scripts/check_inference_gateway.py`; docs
> `_repos/_shared/archive/legacy/docs/inference/open-inference-preference-spec.md`. Placed in **Teleon** (model routing = runtime), consumed by
> Baltor + hubs via Baltor→Teleon; sits ABOVE the existing `_repos/shared-backend-components/scripts/llm_gateway` (reused, not reinvented).
> **QUEUED:** remaining contracts (Request/Response/ProviderNode/Edge/RouteDecision/Health/Cost/FallbackPolicy/
> DataPolicy); candidate adapter FILES (openai/anthropic/gemini/bedrock/azure/litellm/openrouter/local-openai-
> compat/customer-private — offline seams, each with local_equivalent, no SDK import without secret_ref);
> preference inheritance config files + `ResolvedInferencePreference` everywhere; object-integration
> (`model_preference_ref` on CapabilityTask/PurposeTask/Skill/Tool/Harness/Context/Decomposition/Reconciliation/
> Evaluator/Worker/Codegen/etc.); `/api/inference/*` projections + the `/inference` UI panel; the full inference
> **redteam** (`check_inference_gateway_redteam.py`: SDK-imported-directly · raw-key-in-config/log/receipt ·
> silent-fallback · lower-tier-promoted · regulated-uses-external · display-name-branch · receipt-missing-actual
> · output-as-CanonicalFact/served_fact · judge==candidate · cost/region ignored — all fail safe).

# /workflows /shared-inference-gateway-and-llm-preference-standard

Build a shared LLM/model routing module used by Teleon, Baltor, and the OpenHubForAI surfaces. **Preference
requests intent. Router decides execution. Receipt records reality.**

**Rules:** no separate LLM wrapper per product · workers never import provider SDKs directly · no raw API keys in
object configs (secret_ref only) · no hard-coded provider display names or "frontier/fallback/cheap" string
logic (numeric codes + node ids) · LLM output never becomes truth · a lower-tier fallback may not be promoted
beyond its allowed use · OpenAI/Anthropic/Gemini/Bedrock/Azure/LiteLLM/OpenRouter are adapters behind
`InferenceGatewayPort`, none canonical.

## SHARED INFERENCE GATEWAY CLAUSE (carry forward)
All model calls go through one Inference Gateway. Every object may declare an InferencePreference (tier +
specialization, allowed/disallowed provider nodes, data/budget/latency/fallback policy, provenance required).
The router resolves via inheritance, selects via the numeric graph, handles governed fallback, and writes a
ModelInvocationReceipt with the actual provider/model, rejected candidates, fallback reasons, cost, latency,
tokens, input/output hashes, policy checks, and the allowed downstream use. Raw keys live only behind secret
refs. LLM output is candidate/advisory unless downstream gates promote it; the gateway never emits "served".

*(Full PART 1–16 detail is in the owner's message + the proven core above; build the QUEUED items next.)*
