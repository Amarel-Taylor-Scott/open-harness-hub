# /workflows /free-limited-llm-endpoint-intelligence

> **STATUS (2026-06-06).** Slice 1 BUILT + proven (`_repos/shared-backend-components/scripts/check_free_limited_endpoint_intel.py`, flywheel-
> registered): class taxonomy + policy + seeded registry + gateway-repo watchlist (single sources of truth);
> the deterministic classifier + risk scorer + due-diligence engine
> (`_repos/teleon/backend/src/teleon/inference/free_endpoint_intel.py`, composing the Inference Gateway); 3 contracts
> (`FreeLimitedEndpoint`, `EndpointDueDiligenceReport`, `GatewayRepoAssessment`); OpenHubForAI metadata
> projection; provider-node **proposals** (not graph writes); embedded redteam. Docs:
> `_repos/_shared/archive/legacy/docs/inference/free-limited-llm-endpoints.md` + `clawless-assessment.md`.
>
> **QUEUED (this prompt drives the remainder):** the per-class schema split (Conformance/Quota/RiskReport/Policy
> as separate contracts); the live conformance harness (`--live` + secret_ref + synthetic prompts + receipt
> capture + quota headers); OpenHubForAI `ToolArtifact` composition via the canonical shell; the dedicated
> redteam script + full-stack proof; the 7-doc split; live provider-node adoption into `model_provider_graph`.

You are Claude Code running the FREE / LIMITED LLM ENDPOINT INTELLIGENCE workflow.

**Goal:** Build a governed registry and due-diligence pipeline for official free/limited LLM endpoints, free-tier
discovery repos, and LLM gateway repos. Feeds: Shared Inference Gateway · OpenHubForAI.io ·
Teleon.dev · Baltor.

**Do not:** treat free endpoints as production infrastructure · use shared/free leaked keys · import gateway
repos directly · put raw provider keys in config · let LLM output become truth · route customer-sensitive data
through free tiers unless the data policy explicitly allows it · trust third-party free-tier claims without
official docs.

**Core rule:** Free endpoint discovery is metadata. Official provider docs decide eligibility. Inference Gateway
decides routing. ModelInvocationReceipt records reality. Baltor never treats model output as truth.

## PART 1 — Discovery  *(seeded; extend)*
Search the repo for: LLM gateway, provider graph, model preferences, OpenHubForAI, free LLM
endpoint notes, ClawLess/ClawContainer, provider adapters. Output `.agent/free-limited-llm-endpoint-discovery.json`.

## PART 2 — Contracts  *(3 of 7 built)*
Built: `FreeLimitedEndpoint`, `EndpointDueDiligenceReport`, `GatewayRepoAssessment`. Queued:
`EndpointConformanceRun`, `EndpointRiskReport`, `EndpointQuotaSnapshot`, `FreeEndpointPolicy`.
Register all in `_repos/shared-backend-components/architecture/contract_registry.json`.

## PART 3 — Registry  *(built; extend rows)*
`_repos/shared-backend-components/architecture/free_limited_llm_endpoint_registry.json` + `..._policy.json` + `gateway_repo_watchlist.json`
(+ `free_endpoint_class_codes.json` as the numeric taxonomy). Seeded official candidates: GitHub Models, Google
Gemini, Groq, Mistral, Cerebras, Cloudflare Workers AI, OpenRouter `:free`, Hugging Face Inference Providers,
NVIDIA NIM, Together AI (paid). Gateway/discovery + ClawLess runtime + quarantine examples seeded.

## PART 4 — Classification  *(built)*
Classes: official_free_limited_provider · official_trial_credit_provider · official_paid_required_provider ·
inference_aggregator · self_hosted_gateway · discovery_list · browser_agent_runtime · shared_key_repo_quarantine
· reverse_engineered_quarantine · unknown_quarantine. Rules: ClawLess = browser_agent_runtime; Together AI =
paid_required; shared-key repos = quarantine; discovery lists = metadata only; gateway repos = lab candidate only.

## PART 5 — Risk scoring  *(built; 10 dimensions)*
official_docs_confidence · ToS risk · data retention risk · free-tier stability · rate-limit clarity · key custody
risk · secret handling risk · prompt logging risk · proxy/intermediary risk · production suitability (+ OpenAI /
structured-output / tool-call compatibility as future dimensions).

## PART 6 — Conformance tests  *(QUEUED)*
Local stub tests first. Live: explicit env flag + secret_ref + no customer data + synthetic prompts + hard
timeout + ModelInvocationReceipt + quota/rate-limit headers. Test: chat completion · structured output ·
tool calling · embeddings · rate-limit behavior · fallback behavior.

## PART 7 — OpenHubForAI outputs  *(metadata projection built; ToolArtifact composition QUEUED)*
Every endpoint → `ToolArtifact` metadata (provider, endpoint type, API style, base URL, free/limited policy,
visibility, execution gating, secret policy, allowed data class, conformance status, risk score). Executable use
is gated through Teleon/Inference Gateway, not public OpenHubForAI.

## PART 8 — Inference Gateway integration  *(proposal built; live adoption QUEUED)*
Provider-node **proposals** declare: provider_node_id · endpoint registry ref · allowed data classes · secret_ref
required · free/prototype status · fallback behavior · ModelInvocationReceipt requirement · local stub equivalent.
No direct calls outside the gateway. Adoption into `model_provider_graph.json` requires a proof-to-promote.

## PART 9 — Redteam  *(embedded subset built; standalone QUEUED)*
`_repos/shared-backend-components/scripts/check_free_limited_endpoint_redteam.py`. Attacks (all must fail safely): shared-key repo added as
approved provider · ClawLess as free LLM endpoint · gateway repo handles prod keys without warning · free-tier +
customer-sensitive data · silent fallback model/provider change · raw key in logs · no-official-docs marked
approved · Together AI marked free · public OpenHubForAI exposes executable credentialed endpoint · Baltor
consumes free endpoint output as fact.

## PART 10 — Docs  *(2 of 7 built)*
Built: `free-limited-llm-endpoints.md`, `clawless-assessment.md`. Queued: `free-endpoint-risk-policy.md`,
`gateway-repo-watchlist.md`, `approved-prototype-providers.md`, `quarantined-free-key-repos.md`,
`live-endpoint-test-policy.md`.

## PART 11 — Proofs  *(slice-1 proof built)*
Built: `_repos/shared-backend-components/scripts/check_free_limited_endpoint_intel.py` (A–N + redteam M1–M5). Queued: the per-concern split
(`..._contracts`, `..._registry`, `..._gateway_repo_watchlist`, `..._clawless_classification`,
`..._risk_policy`, `..._conformance_local`, `..._opentools_outputs`, `..._inference_gateway_integration`,
`..._redteam`, `..._full_stack`). Regression each pass: `demo_offline_full_baltor`,
`check_no_direct_provider_bypass`, `baltor_flywheel --once`.

## Acceptance
A. ClawLess = browser/WebContainer runtime, not LLM endpoint ✓  B. official free/limited endpoints registered ✓
C. discovery repos metadata-only ✓  D. gateway repos lab candidates only ✓  E. shared-key/bypass quarantined ✓
F. risk policy exists ✓  G. OpenHubForAI metadata projection ✓  H. Inference Gateway provider nodes (proposals) ✓
I. local conformance tests pass *(queued)*  J. redteam passes (embedded ✓; standalone queued)  K. Baltor demo
green ✓  L. flywheel green ✓.
