# Benchmark vs Harness — the OpenBenchmarkHub / OpenHarnessHub boundary

The crux distinction behind adding **OpenBenchmarkHub.io** as a hub separate from OpenHarnessHub.

| | OpenBenchmarkHub.io | OpenHarnessHub.io |
|---|---|---|
| **Question** | *What* should we measure? What datasets/tasks/metrics define success? What results were observed? | *How* do we run the measurement safely, repeatably, with conformance proof? |
| **Owns** | benchmark definitions · benchmark cards · datasets/tasks · metric definitions · result records · leaderboards · suitability reports · contamination/risk · benchmark→capability maps | harnesses · runners · rubrics · fixtures · eval packs · templates · conformance packs |
| **Object** | `BenchmarkArtifact` / `BenchmarkResult` | `HarnessArtifact` |
| **Is not** | a runner, a runtime, a truth authority | a benchmark catalog, a runtime, a truth authority |

Relationship (encoded in `architecture/open_hubs_bridge_graph.json`): `BenchmarkArtifact RUN_BY HarnessArtifact`;
`BenchmarkResult SUPPORTS PromotionDecision`.

## The governing law (proof-enforced)

> **A benchmark is evidence, not authority.** A benchmark result **cannot by itself** promote a Teleon candidate
> or become Baltor truth. Promotion still requires policy gates + receipts + source handles + task-specific
> scorecards + redteam + (for boundary expansion) a HumanApprovalReceipt.

`benchmark_result_cannot_promote: true` is asserted by `scripts/check_open_hubs_bridge_graph.py`.

## Where it sits in the ecosystem

`OpenContextHub` context → `OpenSkillsHub` how → `OpenToolsHub` execution → `OpenMCPHub` connects tools →
`OpenCompressionHub` makes context cheap → **`OpenBenchmarkHub` defines what good means** → `OpenHarnessHub`
proves it → `Teleon` runs/evolves → `Baltor` governs truth → `AI Done Right` coordinates (founding thesis: ContextIsEverything).

## Benchmark families (registry taxonomy, queued build)

model_general · model_coding · model_reasoning · agent_tool_use · agent_memory · software_engineering ·
context_governance · rag_grounding · compression_fidelity · mcp_conformance · tool_safety · skill_effectiveness ·
runtime_selection · sandbox_security · chatbot_guardrail · regulated_context · domain_specific.

External references to catalog as **owner-provided, unverified** until confirmed against their official sources:
SWE-bench / SWE-bench Verified, AgentBench, HELM, OpenCompass, lm-evaluation-harness, LiveBench, Open LLM
Leaderboard, STATE-Bench. First-party benchmarks to author: **Baltor CFPB Context Governance** (reuse the existing
demo: serve "10 business days", hold out FAQ "30 days", preserve source handles/receipts), **Teleon CapabilityTask
Runtime Selection**, **OpenCompression Fidelity**, **OpenMCP Conformance**.

Status: the hub + boundary are LOCKED in the portfolio map (`company_portfolio_map.json` /
`open_hubs_bridge_graph.json`). The contracts (`schemas/benchmarks/*`), registry, website, API, and rubrics are
QUEUED — see `prompts/portfolio-add-openbenchmarkhub.md`.
