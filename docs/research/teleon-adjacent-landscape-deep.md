# Teleon-adjacent landscape — deep dive (capability-slot + validation-risk, 2026-06)

**Companion to** [`architecture/teleon_runtime_landscape.json`](../../architecture/teleon_runtime_landscape.json)
(ARK / kagent / AgentScope / agent-sandbox / Temporal / DBOS / Dapr / Hatchet / Inngest / Trigger.dev /
Ouroboros / agentregistry). This file covers a **second wave** of Teleon-adjacent platforms and adds a
**VALIDATION-RISK** lens on top of the capability-slot classification. Machine-readable twin:
[`architecture/teleon_adjacent_extended.json`](../../architecture/teleon_adjacent_extended.json)
(proof: `scripts/check_teleon_adjacent_extended.py --self-test`).

> **Positioning law.** Teleon is the capability **CONTROL PLANE ABOVE** execution substrates and managed
> agent runtimes: the **CapabilityTask/PurposeTask stays stable** while implementation/runtime evolve;
> **evidence decides**; **policy gates promotion**; predecessors are kept as a **reversible rollback**
> target; **humans approve boundary expansion**; a **truth boundary** keeps runtime/agent/LLM output from
> being served as truth. Teleon is **NOT** another agent framework, **NOT** another workflow / durable-
> execution engine, **NOT** another managed agent runtime. We never compete on *"we run agents"* — we win
> on the **capability contract + eval-gated promotion + rollback + truth boundary** that sit above whatever
> runs the agent. (Reinforces [[teleon-portfolio-architecture]], [[execution-backend-flexibility]],
> [[numeric-config-and-wrapped-redundancy]], [[cloud-task-self-adapting-execution]].)

## Validation-risk legend

| risk | meaning | Teleon move |
|---|---|---|
| `thesis_strengthening` | the market is converging on control-plane-above-substrate | cite as external proof; generalize the top layer |
| `safe_to_wrap` | a swappable execution/compute/memory substrate | wrap behind `ExecutionProviderPort` (or a memory port); carries `do_not_adopt_as_primary` |
| `positioning_threat` | marketed as "agent runtime / durable agents" — closest to Teleon's surface | differentiate on contract + eval-gated promotion + rollback + truth boundary, NOT on running agents |
| `quarantine` | license / trust / safety blocker | none in this wave |

**None of these is `quarantine`.** Honest `license_confidence` (`verified`/`unverified`) is recorded per entry.

---

## THE thesis signal — the 2-layer production stack (`thesis_strengthening`)

The strongest external validation in this wave is the **emerging 2-layer standard**: **Temporal-style macro
durable orchestration UNDER LangGraph-style micro agent logic**. A stable orchestration/contract layer above
a swappable execution layer is exactly the control-plane-above-substrate shape — production teams are
arriving at it independently ([AlphaBold](https://www.alphabold.com/langgraph-agents-in-production/),
[AI Workflow Lab](https://aiworkflowlab.dev/article/ai-workflow-orchestration-in-production-building-durable-agent-pipelines-with-langgraph-and-temporal)).

- **[LangGraph](https://github.com/langchain-ai/langgraph)** (OSS, MIT) — `agent_micro_orchestration`.
  LangGraph 1.2 (May 2026) treats an agent run as a **durable graph execution**: state persisted after every
  step via a checkpointer/`StateSnapshot`, replay-from-checkpoint, pause-for-human, streaming
  ([LangChain docs](https://docs.langchain.com/oss/python/langgraph/durable-execution)). It is the **bottom**
  layer of the stack.
  - *Lacks vs Teleon:* no runtime-neutral capability contract, no candidate-vs-baseline selection, no
    eval-gated promotion, no rollback-as-object, no boundary approval, no truth boundary.
  - *Differentiation move:* treat Temporal(macro)+LangGraph(micro) as **proof** of the thesis; Teleon
    generalizes the top layer from "orchestration" to a **runtime-neutral, eval-gated capability**, and can
    host a LangGraph graph as **one candidate implementation**.
  - **Caveat worth internalizing:** vendors argue "checkpoints are NOT durable execution"
    ([Diagrid](https://www.diagrid.io/blog/checkpoints-are-not-durable-execution-why-langgraph-crewai-google-adk-and-others-fall-short-for-production-agent-workflows)).
    That debate is exactly why Teleon must stay **substrate-neutral**: let evidence + policy pick the durable
    layer (Temporal/DBOS/Restate) under LangGraph micro-logic, rather than betting the thesis on one runtime.

---

## Safe to wrap — substrate adapters behind `ExecutionProviderPort`

Each is a **candidate node** in the numeric provider graph (local / function / job / K8s / browser / worker /
edge / managed-runtime), chosen by policy/telemetry/pricing with **governed, non-silent fallback**. Each
carries `do_not_adopt_as_primary`: adopting one must **not** create a second durable ledger / second worker
framework / second event bus. **The Baltor SQLite `FleetLedger` stays the local truth.**

| Provider | Slot | License (confidence) | What it lacks vs Teleon | Port mapping |
|---|---|---|---|---|
| **[Restate](https://github.com/restatedev/restate)** | `durable_workflow` | runtime **BSL**, SDKs MIT (verified) | durable-execution primitive only; no contract/candidates/promotion/rollback/boundary/truth | durable-workflow node; log never decides promotion |
| **[Prefect](https://github.com/PrefectHQ/prefect)** | `durable_workflow` | Apache 2.0 (verified) | orchestrates Python flows, not capabilities; no eval-gated promotion/rollback/boundary | work-pools as exec node; its orchestration/execution split = design confirmation |
| **[Kestra](https://github.com/kestra-io/kestra)** | `durable_workflow` | Apache 2.0 core, EE commercial (verified) | declarative DAGs; task-runner offload ≠ evidence-gated promotion | DAG + task-runner targets (Azure/Google Batch, Cloud Run) as exec nodes |
| **[Windmill](https://github.com/windmill-labs/windmill)** | `durable_workflow` | **AGPLv3** core (+ proprietary EE flags); clients Apache 2.0 (verified) | script/workflow platform, not a capability plane | script-execution node **across a service boundary only** (AGPL — never in-process import) |
| **[Flyte](https://github.com/flyteorg/flyte)** | `ml_pipeline` | Apache 2.0, LF AI & Data-governed (verified) | ML pipeline + lineage; lineage ≠ evidence-gated promotion | K8s ML-pipeline node; its lineage feeds Teleon evidence |
| **[Ray / Ray Serve](https://github.com/ray-project/ray)** | `compute_backend` | Apache 2.0 (verified) | raw scalable compute/serving; no contract/selection/promotion | compute node; Teleon picks which candidate Ray serves |
| **[Modal](https://modal.com/)** | `compute_backend` | proprietary cloud, OSS clients only (verified) | managed serverless compute; no governance layer; no local-equiv by itself | one serverless peer; Teleon keeps a local-equivalent fallback |
| **[Cloudflare Workflows](https://developers.cloudflare.com/workflows/)** | `edge_durable_runtime` | proprietary edge; "Dynamic Workflows" lib MIT (verified) | edge durable-execution substrate; no capability plane | edge node on Durable Objects for low-latency tasks |
| **[Letta](https://github.com/letta-ai/letta)** (MemGPT) | `agent_memory_runtime` | Apache 2.0 (verified) | single-agent memory/state; recall ≠ governed truth | memory port peer (mem0/supermemory); recall is candidate context, never auto-served truth |

**License flags worth carrying:** **Restate** runtime is **BSL** (not OSI-open) — watch terms before
production reliance. **Windmill** core is **AGPLv3** — wrap only across a process boundary, never link into
Teleon's code. **Modal** is **proprietary cloud** — one switchable peer with a governed local fallback, never
primary. The rest (Prefect/Kestra/Flyte/Ray/Letta) are Apache 2.0; Flyte's foundation governance makes it the
lowest single-vendor-capture risk.

---

## Positioning threats — the four closest to Teleon's surface

These market themselves as an **"agent runtime" / "durable agents"** — the language nearest to Teleon. They
**run** agents well; none owns the **stable capability contract + evidence-gated promotion + reversible
rollback + truth boundary** above the runtime. **Teleon's answer is identical for all four: we are the
cloud/runtime-neutral control plane ABOVE you, and you are one candidate runtime behind
`ExecutionProviderPort`.**

### 1. [LangGraph Platform](https://www.langchain.com/langgraph-platform) (managed) — `managed_agent_runtime`
Commercial managed runtime (tiered) for long-running stateful "durable agents" with autoscaling + SLA
(library is MIT; platform is the commercial layer). **Lacks:** runtime-neutral capability contract,
candidate-vs-baseline, eval-gated promotion, rollback-as-object, boundary approval, truth boundary; tied to
the LangGraph programming model. **Move:** Teleon sits above it; the contract + promotion + rollback + truth
boundary hold whether the agent runs on LangGraph Platform, Temporal, or a Cloud Function — LangGraph
Platform is one candidate runtime, Teleon decides if its output is promoted.

### 2. [Cloudflare Agents SDK](https://developers.cloudflare.com/agents/) — `managed_agent_runtime`
Persistent stateful agent environments on **Durable Objects** (each Agent *is* a Durable Object with its own
SQLite DB); Project Think (Apr 2026) adds durable-execution fibers/stash/recovery
([Agents Week](https://www.cloudflare.com/agents-week/updates/)). Explicitly "build stateful / durable
agents." **Lacks:** runtime-neutral contract, candidate comparison, evidence-gated promotion, rollback
object, boundary approval, truth boundary; bound to the Cloudflare runtime. **Move:** wrap as one **edge**
agent-runtime candidate; the stable CapabilityTask + evidence + promotion + rollback + truth boundary live in
Teleon, not in the Durable Object.

### 3. [Amazon Bedrock AgentCore](https://aws.amazon.com/bedrock/agentcore/) — `managed_agent_runtime`
Proprietary AWS managed runtime (**GA Oct 13 2025**) to deploy/operate agents at scale on any
framework/model/protocol: 8-hour execution windows, session isolation, A2A, and **durable managed session
storage** that resumes filesystem state by session id (Mar 2026
[AWS](https://aws.amazon.com/about-aws/whats-new/2026/03/bedrock-agentcore-runtime-session-storage/)).
**Lacks:** stable runtime-neutral capability contract, side-by-side candidates, evidence-gated promotion,
reversible rollback object, boundary approval, truth boundary; AWS-cloud-locked. **Move:** Teleon stays the
cloud-neutral control plane above it — AgentCore is one managed-runtime candidate; the contract + promotion +
rollback + truth boundary remain portable.

### 4. [Google Vertex Agent Engine](https://cloud.google.com/products/gemini-enterprise-agent-platform) — `managed_agent_runtime`
Proprietary GCP managed runtime. At **Cloud Next 2026, Vertex AI Agent Builder was rebranded into the
Gemini Enterprise Agent Platform**; **Agent Engine** is the managed runtime (compute-billed per vCPU-hour,
persistent memory, **tool governance**). **Lacks:** runtime-neutral capability contract, candidate-vs-baseline,
evidence-**gated** promotion, reversible rollback object, Baltor-style truth boundary; GCP-cloud-locked — and
note it even ships "tool governance", so Teleon must be precise that **its** governance is *eval-gated
promotion of candidate implementations + truth boundary*, not tool allow-lists. **Move:** wrap as one
managed-runtime candidate; differentiate on the portable capability contract + promotion + rollback + truth
boundary across GCP/AWS, never on "we run agents".

> **The one-line wedge against all four:** they answer *"can I run a durable agent here?"* Teleon answers
> *"is this capability meeting its purpose, is a better candidate implementation proven by EVIDENCE, can I
> promote it under policy, can I roll back, and is its output allowed to be served as truth?"* — and it
> answers that **across** all four runtimes at once.

---

## Sources

- [Restate — restatedev/restate](https://github.com/restatedev/restate) · [Restate 1.0 single Rust binary](https://x.com/restatedev/status/1800893180256321636)
- [Prefect — PrefectHQ/prefect](https://github.com/PrefectHQ/prefect)
- [Kestra](https://kestra.io/) · [kestra-io/kestra](https://github.com/kestra-io/kestra)
- [Windmill — windmill-labs/windmill](https://github.com/windmill-labs/windmill) · [Windmill LICENSE (AGPL)](https://github.com/windmill-labs/windmill/blob/main/LICENSE)
- [Flyte — flyteorg/flyte](https://github.com/flyteorg/flyte) · [State of OSS workflow orchestration 2025](https://www.pracdata.io/p/state-of-workflow-orchestration-ecosystem-2025)
- [Ray — ray-project/ray (Apache-2.0)](https://github.com/ray-project/ray) · [Ray Serve docs](https://docs.ray.io/en/latest/serve/index.html)
- [Modal](https://modal.com/) · [Modal $355M round (Jun 2026)](https://siliconangle.com/2026/05/21/serverless-ai-infrastructure-startup-modal-labs-seals-355m-funding-round/)
- [Cloudflare Workflows — Build a Durable AI Agent](https://developers.cloudflare.com/workflows/get-started/durable-agents/) · [Cloudflare Dynamic Workflows (MIT)](https://www.infoq.com/news/2026/05/cloudflare-dynamic-workflows/) · [Cloudflare Durable Objects](https://developers.cloudflare.com/durable-objects/)
- [LangGraph — langchain-ai/langgraph](https://github.com/langchain-ai/langgraph) · [LangGraph durable execution docs](https://docs.langchain.com/oss/python/langgraph/durable-execution) · [Checkpoints are not durable execution (Diagrid)](https://www.diagrid.io/blog/checkpoints-are-not-durable-execution-why-langgraph-crewai-google-adk-and-others-fall-short-for-production-agent-workflows)
- [LangGraph + Temporal 2-layer pattern](https://aiworkflowlab.dev/article/ai-workflow-orchestration-in-production-building-durable-agent-pipelines-with-langgraph-and-temporal) · [LangGraph in production (AlphaBold)](https://www.alphabold.com/langgraph-agents-in-production/)
- [Letta — letta-ai/letta (Apache-2.0, MemGPT lineage)](https://github.com/letta-ai/letta)
- [LangGraph Platform](https://www.langchain.com/langgraph-platform)
- [Cloudflare Agents](https://developers.cloudflare.com/agents/) · [cloudflare/agents](https://github.com/cloudflare/agents) · [Agents Week 2026](https://www.cloudflare.com/agents-week/updates/)
- [Amazon Bedrock AgentCore](https://aws.amazon.com/bedrock/agentcore/) · [AgentCore GA (Oct 2025)](https://aws.amazon.com/about-aws/whats-new/2025/10/amazon-bedrock-agentcore-available/) · [AgentCore session storage (Mar 2026)](https://aws.amazon.com/about-aws/whats-new/2026/03/bedrock-agentcore-runtime-session-storage/)
- [Google Gemini Enterprise Agent Platform (ex-Vertex Agent Engine)](https://cloud.google.com/products/gemini-enterprise-agent-platform) · [Vertex AI Agent Builder guide 2026](https://uibakery.io/blog/vertex-ai-agent-builder)
