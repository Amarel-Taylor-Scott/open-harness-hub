# Stateful Swarms (Irys) and the persistent-blackboard / agent-memory landscape

**Verified via web research, June 2026.** Is this relevant, and how does it fit our portfolio? **Yes — strongly
relevant, as a research_candidate and a thesis-validator, not a dependency.** Irys "Stateful Swarms" is the
cleanest public proof point that *cheaper models + better shared state + decomposition + verification beats
frontier brute force* — exactly [[teleon-serves-ai-agents]]. We catalog it, govern its open problems as Baltor
product areas, and never wire it as a runtime.

Companion machine-readable catalogs (the enforcement of everything below):
- `_repos/shared-backend-components/architecture/stateful_swarm_provider_catalog.json` — the swarm-runner catalog (Irys @ research_candidate + the offline local stub @ active).
- `_repos/shared-backend-components/architecture/blackboard_provider_catalog.json` — the BlackboardProviderPort candidates (local SQLite @ active + Graphiti/Letta/LangGraph-checkpoint/AutoGen-Mem0/seekdb @ candidate).
- `_repos/shared-backend-components/scripts/check_stateful_swarm_provider_catalog.py --self-test` — deterministic, offline, stdlib proof of the governance boundary (60 checks, exit 0).

## What Irys Stateful Swarms is

A **blackboard architecture for multi-agent analytical work.** Many worker agents read from and write to a
single, shared, **append-only, provenance-tracked knowledge base** (the "blackboard") instead of passing
context through prompts. Because the state is durable and structured, agents **don't reread the source
documents, don't lose context at handoffs, and don't recompute** what a peer already derived.

- Repo: [github.com/dl1683/irys-stateful-swarms](https://github.com/dl1683/irys-stateful-swarms) (company [irys.ai](https://irys.ai)).
- **License: MIT** — `license_confidence: verified` (license file read on the repo).
- **Requires Python 3.12+**, `pip install -e .`, and **at least one LLM key** (`GEMINI_API_KEY` primary; `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` optional; worker/synthesis/reviewer models overridable via env). → **research_candidate**, not active, not a dependency, never pip-installed or executed here.
- **Typed blackboard entries:** `observations` (source-grounded facts with document refs), `calculations`
  (derived numeric/logical results), `analyses` (cross-document reasoning), `gaps` (explicitly logged missing
  info), `synthesis`, plus `source`, `worker`, and `iteration` provenance. Entry metadata carries `created_by`
  (worker id, description, iteration), `source` (document, section, evidence), and a `confidence` score.
- **Self-defining swarms:** analysts write custom worker prompts per problem; shipped as an open-source CLI
  that accepts any document set + a task instruction.
- Background reading: [Stateful Swarms: How Persistent Memory Beats Traditional Agent Architectures](https://www.artificialintelligencemadesimple.com/p/stateful-swarms-how-persistent-memory) · [Stateful Swarms Will Revolutionize Agentic AI (Medium)](https://machine-learning-made-simple.medium.com/stateful-swarms-will-revolutionize-agentic-ai-3315f7ec2a5c) · [The Architecture of AI Agent Swarms (Codefinity)](https://codefinity.com/blog/The-Architecture-Of-AI-Agent-Swarms).

### The reported result — EVIDENCE, **unverified-until-reproduced**

On **Harvey's public Legal Agent Benchmark (LAB)** ([github.com/harveyai/harvey-labs](https://github.com/harveyai/harvey-labs);
announced [here](https://www.harvey.ai/blog/introducing-harveys-legal-agent-benchmark), initial results
[here](https://www.harvey.ai/blog/legal-agent-benchmark-initial-results)), Irys reports:

| Metric | Irys Stateful Swarms | Harvey published |
|---|---|---|
| Pooled-criteria pass | **~83.74%** | — |
| Strict all-pass (every criterion) | **~17.75%** | 10.4% |
| Cost / task | **~$1.30** | $50.90 |

> **`harvey_lab_claims_unverified: true`.** Irys ran the **PUBLIC** benchmark (the full ~1,251-task LAB set)
> with **no private holdout**, so leakage / overfit to the public set is not ruled out. These numbers are
> **EVIDENCE that the architecture lifts, NEVER a promotion authority** (see
> `open_hubs_bridge_graph.boundary_laws.benchmark_result_cannot_promote`). To move Irys off
> `research_candidate` we require reproduction via the public Harvey LAB scorer **plus** our own swarm
> harnesses green **plus** Baltor governance over the produced state **plus** the two-axis lift+durability
> gate. A score alone never promotes. See the LawSites/ArtificialLawyer commentary on LAB for the
> "public-benchmark" caveat: [LawSites](https://www.lawnext.com/2026/05/some-thoughts-on-harveys-launch-of-lab-an-open-source-long-horizon-benchmark-for-legal-ai-agents.html) · [Artificial Lawyer](https://www.artificiallawyer.com/2026/05/06/harvey-launches-legal-agent-bench/).

## The split: Irys runs analysis · Baltor governs the state · Teleon runs the swarm

The single most important framing: **the durable governed context object is worth more than the final answer.**
Irys produces an excellent *analytical* blackboard; it does not produce *served truth*. Those are different
objects, and the gap between them is Baltor.

| Layer | Role | What it owns |
|---|---|---|
| **Irys (research_candidate)** | the persistent **analytical** blackboard for agent work | typed, provenance-tracked entries; worker prompts; convergence-by-iteration; synthesis |
| **Baltor (governance)** | the **governance layer over that state** | adds `authority_rank`, `claim_status`, `verification_status`, `held_out_reason`, `freshness`, `temporal_validity`, `tenant_scope`, `promotion_eligibility`, `receipt_refs`, `source_handles` — turns "here is what agents found" into "here is what is **verified**, what **conflicts**, what is **stale**, what is **held out**, and what **may be served**" |
| **Teleon (runtime)** | the runtime that **runs a stateful swarm as a CapabilityTask** | `SwarmRunnerProviderPort` (runs the swarm) + `BlackboardProviderPort` (the state store), behind policy/cost/promotion gates; switchable backend; keeps the offline stub as fallback |

**Irys's own open problems ARE Baltor product areas** — this is the strongest fit signal in the whole space:

| Irys open problem | Baltor product area it lands in |
|---|---|
| **Cross-document entity resolution** ("Zenith Petrochem" vs "Zenith Petrochemical") | reconciliation / entity-linking / verification (`fragile_context_*`, the reconciliation stage) |
| **Convergence detection** (when has the blackboard stabilized?) | a governed stabilization signal — promotion-readiness over agent state, not a fixed iteration count |
| **Blackboard compression for synthesis** (rank/cluster entries for density) | OpenCompressionHub fidelity: compress the surface while preserving **source-handles + held-out + receipts** ([[lossless-distillation-law]]) |
| Multi-benchmark generalization (legal → medical/patents/insurance) | the negative-space / capability-valley grid (note: **stay away from insurance** per repo scope) |

This is why Irys *validates* us rather than competing: it independently arrives at "structured shared state +
decomposition + cheap models" as the win, and then hits exactly the governance/reconciliation/compression
walls Baltor is built to be.

## Per-hub fit (open ecosystem)

- **OpenBenchmarkHub** — catalogs **Harvey LAB** and **Irys's reported outputs** as **EVIDENCE, never
  authority** (alongside the existing `external_unverified` benchmark list; a Harvey-class
  `benchmark.legal_context_governance` opportunity already exists in `_repos/shared-backend-components/architecture/open_benchmark_registry.json`
  with a no-accusation / legal-review caveat). Pooled/strict/$-per-task are recorded as `owner_provided_unverified` until reproduced.
- **OpenHubForAI** — **owns the harnesses** that grade a swarm run (this is our lane, not Irys's):
  **blackboard schema validation**, **source-handle coverage**, **gap closure**, **entity reconciliation**,
  **held-out leakage** (must be 0), and **cost/task**. These are the gates a swarm runner must pass before any
  promotion conversation.
- **OpenHubForAI — stateful context-pack examples**: a governed blackboard snapshot is a context pack with
  source handles + held-out + receipts (a stateful sibling of the existing context-pack examples).
- **OpenHubForAI — worker skills**: the per-role analyst prompts a self-defining swarm uses, cataloged
  as `SkillArtifact`s — teaching *how*, never serving truth.
- **OpenCompressionHub** — **blackboard compression** that preserves **source-handles + held-out** (directly
  answers Irys's open compression problem; graded by `benchmark.opencompression.fidelity@v1`'s
  source_handle_preservation / held_out_warning_preservation / receipt_preservation metrics).

All of these obey the bridge-graph law: **none of the hubs is a truth authority — Baltor governs context,
Teleon runs capabilities** (`_repos/shared-backend-components/architecture/open_hubs_bridge_graph.json`).

## The landscape — persistent blackboard / agent memory / agent state

Honest `license_confidence` shown; **only Irys's MIT was confirmed by reading the license** — everything else
is `unverified` here and must be confirmed against the official repo before any adoption step. Every non-local
option is a **candidate behind the `BlackboardProviderPort` with a working local fallback and
`do_not_adopt_as_primary: true`**.

| Provider | What it is | License (confidence) | Our catalog status |
|---|---|---|---|
| **Irys Stateful Swarms** | append-only analytical blackboard for multi-agent work | MIT (**verified**) | `research_candidate` (swarm runner) |
| **Graphiti / Zep** ([getzep/graphiti](https://github.com/getzep/graphiti)) | real-time **temporal** knowledge graph for agents; tracks how facts change + provenance; runs on Neo4j/FalkorDB/Neptune | Apache-2.0 (unverified) | `candidate` (also cross-listed with our temporal-graph provider work) |
| **Letta (formerly MemGPT)** ([letta-ai/letta](https://github.com/letta-ai/letta)) | stateful-agent framework; memory blocks persisted to a DB; self-improving memory | unverified | `candidate` |
| **LangGraph checkpoint** ([langchain-ai/langgraph](https://github.com/langchain-ai/langgraph), [persistence docs](https://docs.langchain.com/oss/python/langgraph/persistence)) | per-step state snapshots / threads / time-travel — workflow checkpointing | MIT (unverified) | `candidate` |
| **AutoGen + Mem0** ([mem0ai/mem0](https://github.com/mem0ai/mem0), [AutoGen memory](https://microsoft.github.io/autogen/stable//user-guide/agentchat-user-guide/memory.html)) | universal self-improving memory layer (vector+KV+graph); AutoGen integration | Apache-2.0 (unverified) | `candidate` |
| **seekdb (OceanBase)** ([oceanbase/seekdb](https://github.com/oceanbase/seekdb)) | AI-native **write-heavy** state store; MySQL-compatible; hybrid vector+full-text; COW FORK/MERGE sandboxes | unverified | `candidate` |
| **kyegomez/swarms** ([kyegomez/swarms](https://github.com/kyegomez/swarms)) | multi-agent **orchestration** framework (uses the blackboard pattern) | unverified | foil/reference (orchestration, not our runtime) — per [[swarm-orchestration-foil-positioning]] |
| Local append-only **SQLite** stub | offline correctness invariant; source_refs+receipts+tenant required; **no truth writes** | stdlib (**verified**) | **`active`** (the one authority) |

How they differ (so we wrap the right one for the right job): **Irys** = ephemeral-run *analytical* blackboard
optimized for one decomposed task; **Graphiti/Zep** = durable *temporal* fact graph (good for "how did this
change over time" — overlaps our reconciliation/freshness story); **Letta** = agent-centric persistent memory
*runtime*; **LangGraph checkpoint** = workflow *plumbing* (resume/replay), not a knowledge store; **AutoGen/Mem0**
= a *recall* memory layer (self-improving, auto-forgetting — a governance hazard, see below); **seekdb** = the
*storage* substrate for write-heavy agent state. We never need to pick one — they sit side by side behind the
port, selected by policy, with the local SQLite store as the invariant.

Related prior research in-repo: [[context-layer-landscape]] (Mem0/Letta/Graphiti/Langfuse as candidate
providers Baltor wraps), [[temporal-graph-provider]] (Graphiti as a candidate, baltor-local as authority),
[[supermemory]] (memory/context layer; auto-forgetting vs lossless governance), and the agentic-tools landscape.

## What NOT to do (governance lines — these are the failure modes)

1. **Don't serve blackboard / agent output as truth.** Typed entries are *analytical agent output*. Servable
   only after Baltor governance: source_handle present, `verification_status=verified`, no open conflict, fresh
   within `temporal_validity`, `tenant_scope` honored, `promotion_eligibility` met, `receipt_refs` attached.
2. **Don't treat a benchmark number as a promotion.** Harvey LAB pooled/strict/$-per-task is EVIDENCE.
   Reproduction + our harnesses + governance + the two-axis gate promote; a score never does.
3. **Don't pip-install / execute / wire Irys (or any candidate) as a runtime.** Python 3.12+ + install + LLM
   keys ⇒ `research_candidate`. Study it; keep the offline local stub as the active authority.
4. **Don't let "intelligent forgetting" / self-improving memory delete truth-bearing facts.** Mem0/Letta-style
   auto-forget and derived facts map to `held_out` / `candidate`, **never served fact** — omitted ≠ deleted
   ([[lossless-distillation-law]]).
5. **Don't resolve conflicts by recency or by agent confidence.** Reconcile by **authority + receipt**; the
   loser is held out, not overwritten.
6. **Don't serve an inferred/derived entry without a source handle.** No source handle ⇒ not served truth.
7. **Don't pick a single backend or hard-code one.** Graphiti/Letta/LangGraph/Mem0/seekdb are interchangeable
   candidates behind the port with a working local fallback and `do_not_adopt_as_primary` ([[execution-backend-flexibility]]).
8. **Don't trust discovery / stars / a blog as fit.** discovery ≠ trust; candidate ≠ active. Confirm each
   license against the official repo before any adoption step (only Irys's MIT is `verified` here).
9. **Don't expand into insurance** while generalizing the legal result to other domains (repo scope rule).

## Verdict

Catalog Irys as a **research_candidate** swarm runner and a **thesis-validator**. Govern its three open
problems (entity resolution, convergence, compression) as Baltor product areas. Keep the offline local stub /
SQLite store as the single active authority. The durable, governed context object — not the swarm's final
answer — is the product.

---
*Sources cited inline as markdown links. Claims about Irys's Harvey LAB performance are
`unverified-until-reproduced` via the public Harvey LAB scorer. Enforced by
`_repos/shared-backend-components/scripts/check_stateful_swarm_provider_catalog.py`; cataloged in
`_repos/shared-backend-components/architecture/stateful_swarm_provider_catalog.json` + `_repos/shared-backend-components/architecture/blackboard_provider_catalog.json`.*
