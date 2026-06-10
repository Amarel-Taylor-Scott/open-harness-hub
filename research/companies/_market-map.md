# Vertical-AI + AI-infra market map (competitive intelligence)

> **Source confidence:** every funding/valuation/traction figure below is **owner_provided_unverified** (from the
> owner's cited company pages) — verify against primary sources before any external use. **No public accusations;
> regulated (legal/clinical/finance) framing carries a review caveat** (reuse `src/baltor/sales/claim_guard`). This
> is internal market intelligence, not product truth and not outward outreach.

## The market splits into four layers (not all "vertical SaaS")
1. **Trusted vertical AI apps** — Harvey (legal), OpenEvidence (clinical)
2. **Human-intelligence / expert-labor infra** — Mercor
3. **AI compute + inference infra** — Crusoe, Nscale, Fireworks
4. **Agentic software/app creation** — Cursor/Anysphere, Cognition/Devin, Lovable

## Where our portfolio sits — between and underneath
- **Baltor** = governed-context + trust layer for regulated AI (what Harvey/OpenEvidence-class systems *need under
  them*: source handles, claim decomposition, conflict detection, freshness/fragile-fact watch, held-out warnings,
  evidence receipts, safe consumption, audit/review packs). We do **not** become Harvey/OpenEvidence.
- **Teleon** = purpose-defined runtime / CapabilityTask control plane over any capability (not just code); routes
  across compute/inference backends; evidence-gated promotion; human approval for boundary expansion.
- **Open\*Hubs** = lead-gen registries + benchmarks + proof surfaces.

## Company → category → our implication (facts unverified)
| Company | Layer | Implication for us |
|---|---|---|
| **Harvey** (legal AI; ~$200M @ $11B, Mar 2026) | 1 trusted vertical | Validates Baltor's regulated-context thesis → build the governance layer such systems need. Compete: low. Learn: high. |
| **OpenEvidence** (clinical search; ~$250M Series D @ $12B; cited 40%+ US physicians) | 1 trusted vertical | Cleanest Baltor analogy in regulated knowledge: source-licensed grounding + evidence-backed answers. **Caution: no medical-advice claims.** |
| **Mercor** (expert-labor infra; ~$350M Series C @ $10B) | 2 expert infra | Validates expert pods / human-in-loop / skill extraction → OpenSkillsHub + OpenBenchmarkHub + Baltor review packs. |
| **Crusoe** ("AI factory"; ~$1.375B Series E @ $10B) | 3 compute | Candidate **ExecutionBackendProvider** for Teleon (not a competitor). Reinforces cloud-agnostic backend selection. |
| **Nscale** (sovereign GPU cloud; Rubin GPUs for MS; $790M Norway) | 3 compute | Candidate **sovereign ExecutionBackendProvider** → region/residency/cost/capacity as runtime-decision inputs. |
| **Fireworks AI** (inference platform; ~$250M Series C) | 3 inference | Candidate node in the **Shared Inference Gateway provider graph** — never a direct dependency. |
| **Cursor/Anysphere** (AI coding agent; Automations = event/schedule-triggered cloud agents) | 4 agentic | Validates Teleon's event-triggered worker thesis — but Teleon generalizes beyond code. |
| **Cognition/Devin** (autonomous SWE agents; >10x enterprise growth, ~$492M run-rate) | 4 agentic | Validates agent-worker teams → Teleon runtime + Baltor governance/receipts for agent output. |
| **Lovable** (NL app builder; ~$330M Series B @ $6.6B) | 4 agentic | NL creation → governance gap (security/runtime policy/provenance/evals/promotion) = Teleon + OpenHarnessHub + Baltor. |

## Provider-node mappings (candidates only — wrap behind ports, never direct imports)
- Crusoe / Nscale → `ExecutionBackendProvider` candidates (Nscale = sovereign).
- Fireworks → Inference Gateway provider-graph candidate (alongside Groq/OpenRouter/Bedrock/Azure/Cloudflare/local).
- Cursor / Cognition → `CodegenAgentProvider` candidates (bounded agents, behind a port).
- Lovable → generated-app target / app-builder connector candidate.
- Mercor → expert-evaluation / human-in-loop candidate.
- Harvey / OpenEvidence → regulated-context **benchmark analogs** (see below), not providers.

## Benchmark opportunities → now live in OpenBenchmarkHub (as candidates)
`benchmark.legal_context_governance` (Harvey-class) · `benchmark.clinical_evidence_grounding` (OpenEvidence-class,
regulated caveat) · `benchmark.consumer_finance_chatbot_guardrail` · `benchmark.agentic_code_runtime_safety`
(Cursor/Cognition-class) · `benchmark.generated_app_productionization` (Lovable-class) ·
`benchmark.inference_backend_routing` (Crusoe/Nscale/Fireworks-class) · `benchmark.expert_workflow_skill_extraction`
(Mercor-class) — all seeded `status 200` (candidate) in `architecture/open_benchmark_registry.json`.

## Compete / partner / sell / learn
We are **not** trying to beat these — we build the governance/runtime/evidence layer their customers increasingly
need. Compete: low across the board (partial conceptual overlap only with Cursor/Cognition/Lovable on agent
workflows). Partner: Crusoe/Nscale (execution), Fireworks (inference), Cursor/Cognition (code-agent providers),
Lovable (app-hardening). Sell-to: governance/eval/runtime layers for all four layers' customers. Learn: very high
from Harvey/OpenEvidence (source-grounded trust adoption).

**Key sentence:** *Harvey & OpenEvidence prove trusted vertical AI is valuable; Cursor/Cognition/Lovable prove
agentic creation is mainstream; Crusoe/Nscale/Fireworks prove runtime/inference choices are strategic; Mercor
proves human expertise is infrastructure — Teleon and Baltor provide the purpose-runtime and governed-context
layers these systems increasingly need.*

QUEUED (full CI registry): `prompts/competitive-intelligence-vertical-ai-and-infra-map.md` — CompanyArtifact/
SalesWedge/ProviderNodeMapping schemas, the competitive_company_registry, per-company `research/companies/*.md`,
and the lead-funnel target maps. The **lead-funnel + outreach** parts stay under the HELD sales authorization
(see [[portfolio-sales-machine-and-safety-gate]]); diagnostics run only on authorized/provided inputs.
