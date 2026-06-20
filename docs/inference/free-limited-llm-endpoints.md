# Free / Limited LLM Endpoint Intelligence

A governed due-diligence layer that distinguishes **safe official/free-tier inference options** from **risky
shared-key or bypass projects**, and routes each into the right portfolio surface. It feeds the **Inference
Gateway** (routing), **OpenToolsHub** (metadata), **OpenHarnessHub** (conformance/redteam — queued), and
**Teleon/Baltor** (governed use).

> Engine: `src/teleon/inference/free_endpoint_intel.py` · Proof: `scripts/check_free_limited_endpoint_intel.py`
> Single sources of truth: `architecture/free_endpoint_class_codes.json`,
> `architecture/free_limited_llm_endpoint_policy.json`, `architecture/free_limited_llm_endpoint_registry.json`,
> `architecture/gateway_repo_watchlist.json`.

## Core law

- **Free endpoint discovery is metadata.** Official provider docs decide eligibility.
- **Third-party free-tier claims are unverified** until confirmed against official docs (every `rate_limit_claim`
  is stored `source: owner_provided_unverified, confidence: unverified`).
- **The Inference Gateway decides routing; the `ModelInvocationReceipt` records reality** (which model actually
  ran + fallback trail).
- **A browser/WebContainer runtime (ClawLess) is NOT an LLM endpoint** — it is a sandbox/runtime candidate.
- **Shared-key / bypass / reverse-engineered repos are quarantine** — never an approved provider.
- **Raw keys are never stored** (secret_ref only). **LLM output is never truth** — Baltor governs serving.

## Class taxonomy (numeric codes — the engine branches on these, never display strings)

| Code | Class | What it is | Posture |
|---|---|---|---|
| 100 | official_free_limited_provider | Official provider with a documented free/limited tier | Candidate (non-serving), phase ≤ 3 |
| 200 | official_trial_credit_provider | Time/credit-limited trial, not a durable free tier | Candidate, phase ≤ 2 |
| 300 | official_paid_required_provider | Payment required; **not free** (e.g. Together AI) | Candidate→prod with paid terms, phase ≤ 5 |
| 400 | inference_aggregator | One endpoint, many providers, free variants (OpenRouter `:free`, HF) | Candidate; verify intermediary + upstream data handling |
| 500 | self_hosted_gateway | Self-hostable OpenAI-compatible proxy repo | **Lab candidate only**, never imported |
| 600 | discovery_list | awesome-list of free APIs | **Metadata only**, phase 0 |
| 700 | browser_agent_runtime | WebContainer/browser agent runtime (ClawLess) | **Sandbox/runtime candidate — NOT an LLM endpoint** |
| 900 | shared_key_repo_quarantine | Shared/free/leaked keys, "unlimited"/"bypass" | **Quarantine** |
| 910 | reverse_engineered_quarantine | Reverse-engineered/unofficial access | **Quarantine** |
| 990 | unknown_quarantine | Claims free but no official docs / unclear retention | **Quarantine** until officially documented |

Codes ≥ `quarantine_floor` (900) are rejected. Classification is driven by **signal booleans** and an explicit
`markers_text` (the repo's own marketing language) — never by scanning field names or descriptive notes, so a
discovery list that says it *excludes* reverse-engineered services is not itself quarantined.

## Promotion phases (the ladder; recommended phase = min(policy cap, risk-derived))

`-1 rejected` · `0 discovery_only` (metadata, no keys) · `1 local_conformance` (local stub) ·
`2 dev_only_live_key` (dev key, spend caps, no private data, receipts) · `3 candidate_teleon_provider`
(shadow/candidate, not serving) · `4 approved_non_sensitive` (public/synthetic only) · `5 production_with_policy`
(official paid/prod terms + security + privacy + observability + fallback). Free tiers cap at phase 3; an
official claim without official docs cannot exceed -1; raw key forces quarantine.

## Seeded official candidates (all `candidate`/`watch`, none production)

GitHub Models · Google Gemini API (watch free-tier data-use) · Groq · Mistral La Plateforme · Cerebras (verify
limits) · Cloudflare Workers AI · OpenRouter `:free` (aggregator) · Hugging Face Inference Providers (aggregator,
tiny budget) · NVIDIA NIM API Catalog · **Together AI = paid_required (not free)**.

## Watchlist (metadata only — nothing imported or executed)

- Discovery lists (600): `cheahjs/free-llm-api-resources` (excludes illegitimate, warns on abuse),
  `mnfst/awesome-free-llm-apis`, `amardeeplakshkar/awesome-free-llm-apis`.
- Self-hosted gateways (500, lab only): `tashfeenahmed/freellmapi` (author: not production),
  `MrFadiAi/free-llm-gateway` (review code/key handling first).
- Browser runtime (700): `open-gitagent/clawless` — see [clawless-assessment.md](./clawless-assessment.md).
- Quarantine examples (900/910): synthetic shared-key + reverse-engineered patterns (exercise the classifier).

## Integration

- **OpenToolsHub** ← `to_opentools_metadata(report)`: provider metadata, risk score, free/limited flag,
  `executable: false`, `executable_use_gated_through: teleon_inference_gateway`, secret policy, allowed data class.
- **Inference Gateway** ← `provider_node_proposal`: a *proposed* `model_provider_graph` node (status candidate)
  requiring `secret_ref` + `local_equivalent` (the offline stub) + receipt. **A proposal, not a write** — agents
  propose, Baltor disposes; the node is never added to the graph by this layer.
- **Baltor** consumes model-assisted output only as candidate/evidence — never as truth.

## Queued (the rest of the 11-part spec — see `prompts/free-limited-llm-endpoint-intelligence.md`)

Per-class schema split (conformance/quota/risk-report/policy as separate contracts); live conformance harness
(`--live`, secret_ref, synthetic prompts only, receipt capture, quota headers); OpenToolsHub `ToolArtifact`
composition via the canonical shell; a dedicated redteam script; the 7-doc split; live provider-node adoption.
