# /workflows /competitive-intelligence-vertical-ai-and-infra-map

> **STATUS (2026-06-07).** Market map captured (`research/companies/_market-map.md`): 4-layer classification of the
> 9 companies + portfolio implications + provider-node mappings + compete/partner stance, all facts
> owner_provided_unverified, no accusations. **PART 5 (benchmark opportunities) BUILT** into OpenBenchmarkHub
> (`architecture/open_benchmark_registry.json` opportunities; proof `check_openbenchmarkhub_core`). The rest below
> is QUEUED; the lead-funnel + outreach parts stay under the HELD sales authorization.

You are Claude Code running the COMPETITIVE INTELLIGENCE — VERTICAL AI + AI INFRA MAP workflow. Research + structure
the market around Harvey, OpenEvidence, Mercor, Crusoe, Nscale, Fireworks, Cursor/Anysphere, Cognition/Devin,
Lovable. Structured artifacts, not prose-only. Classify into 4 layers (regulated vertical AI · expert/human-intel
infra · AI compute/inference infra · coding/app-building agent platforms). **Core rule:** use competitors to define
**proof-driven sales wedges**, not vague inspiration.

**Governance (enforced by the redteam + reusing `src/baltor/sales/claim_guard`):** company facts need a source;
funding from a weak source is NOT "verified"; never copy Harvey/OpenEvidence as direct product strategy; clinical/
legal claims carry a caveat; an AI-infra provider is never "active" without a provider wrapper/port; a sales wedge
makes NO public accusation; competitor research never updates product truth.

PART 1 — Contracts (QUEUED): `schemas/market/{CompanyArtifact,ProductArtifact,MarketCategory,BuyerPersona,
PainHypothesis,SalesWedge,IntegrationOpportunity,BenchmarkOpportunity,ProviderNodeMapping,CompetitiveRisk}.v1`.
PART 2 — Registries (QUEUED): `architecture/{market_category_registry,competitive_company_registry,
competitive_sales_wedge_registry,competitive_integration_opportunities,competitive_benchmark_opportunities}.json`.
Seed the 9 companies (4-layer classification per the market map).
PART 3 — Research docs (QUEUED): `research/companies/{harvey,openevidence,mercor,crusoe,nscale,fireworks,cursor,
cognition,lovable}.md` — category · product · buyer · use cases · funding/traction (source confidence) ·
architecture/Baltor/Teleon/OpenHub implications · sales wedge · risks · monitor-next. (Master map already at
`research/companies/_market-map.md`.)
PART 4 — Lead-funnel maps (QUEUED, HELD sales): `docs/sales/{vertical-ai,ai-infra,agentic-dev,regulated-chatbot}-
target-map.md` with the diagnostic offers (Baltor Guardrail/Source-Handle Audit, Teleon CapabilityTask/Task-Sprawl
Audit, OpenBenchmarkHub Benchmark-Fit Audit, OpenCompressionHub Context-Cost Audit, OpenTools/MCP Exposure Audit).
PART 5 — Benchmark opportunities (**BUILT**): seeded as candidates in OpenBenchmarkHub —
`benchmark.{legal_context_governance, clinical_evidence_grounding, consumer_finance_chatbot_guardrail,
agentic_code_runtime_safety, generated_app_productionization, inference_backend_routing,
expert_workflow_skill_extraction}`.
PART 6 — Provider mappings (QUEUED): Crusoe/Nscale → ExecutionBackendProvider candidates; Fireworks → Inference
Gateway provider node; Cursor/Cognition → CodegenAgentProvider candidates; Lovable → generated-app target; Mercor →
expert/human-in-loop candidate; Harvey/OpenEvidence → regulated-context benchmark analogs. Seed into the existing
`model_provider_graph` / execution-backend catalog as CANDIDATES behind ports (never direct imports).
PART 7 — Redteam (QUEUED): `scripts/check_competitive_intelligence_redteam.py` — category misclassified · fact
lacks source · weak-source funding marked verified · Harvey/OpenEvidence copied as product · healthcare/legal claim
w/o caveat · infra provider active w/o wrapper · sales wedge public accusation · competitor research updates truth.
All fail safely.
PART 8 — Proofs (QUEUED): check_competitive_{company_registry,research_docs,sales_wedges,provider_mappings,
benchmark_opportunities,intelligence_redteam,intelligence_full_stack}. Regression: demo_offline_full_baltor,
check_no_direct_provider_bypass, baltor_flywheel --once.

## Conclusion (captured)
Teleon = purpose-defined runtime + backend routing + self-adaptive capability execution. Baltor = governed context
+ source handles + reconciliation + freshness + safe consumption. Open\*Hubs = public lead-gen registries. We sit
between and underneath the four layers — the governance/runtime/evidence layer their customers increasingly need.
