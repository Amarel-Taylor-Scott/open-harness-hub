# Powering the Open\*Hubs Backends — Governed OSS Candidate Catalog

**Question:** which open-source repos could power the BACKEND COMPONENTS of the Open\*Hubs websites
(OpenContextHub, OpenSkillsHub, OpenToolsHub, OpenMCPHub, OpenCompressionHub, OpenBenchmarkHub,
OpenHarnessHub)?

**Status:** research / CANDIDATE catalog. Nothing here is installed, run, containerized, or wired into a
live backend. Structured companion: [`architecture/openhubs_backend_candidate_registry.json`](../../architecture/openhubs_backend_candidate_registry.json).
Proof: `scripts/check_openhubs_backend_registry.py --self-test`.

## Governance law (encoded in the registry + enforced by the proof)

- **discovery != trust** — appearing in a discovery aggregator (Glama / Smithery / mcp.so), or scoring high
  there, is discovery signal, never trust. An item clears governance before it powers a backend.
- **candidate != active** — every external repo is cataloged behind a **port** with a **local_equivalent**
  and a **proof_to_promote** ladder. It is **never auto-active**; promotion needs the ladder + owner
  authorization (especially for Docker / network / cloud).
- **benchmark result = EVIDENCE, never promotion authority** — an eval/benchmark score feeds a scorecard; it
  cannot by itself promote a candidate.
- **output != truth** — LLM / agent / eval-judge output is never truth.
- **the Open\*Hubs are REGISTRIES, NOT truth authorities** — they index/serve metadata. Per
  [`open_hubs_bridge_graph.json`](../../architecture/open_hubs_bridge_graph.json), **Baltor governs truth,
  Teleon runs capabilities**; the hubs do neither.
- **local-first** — every gated (Docker/network) candidate carries a local_equivalent so each backend has an
  offline golden path before any external dependency is wired.

---

## Lead insight: OpenMCPHub can WRAP the open-source official MCP registry

The single strongest finding. The **official MCP registry**,
[`modelcontextprotocol/registry`](https://github.com/modelcontextprotocol/registry), is **open source (MIT)**
and **explicitly designed so anyone can build a COMPATIBLE SUB-REGISTRY**. OpenMCPHub therefore does **not**
reinvent a registry service — it **forks/wraps** the reference implementation behind an `McpRegistryProviderPort`,
namespaces an OpenMCPHub sub-registry, and seeds it from local fixture data for the offline golden path.

This same project is also the **reference implementation of the generic `registry_service` pattern** every
hub needs: a metadata service that points at packages (npm / PyPI / Docker). So OpenSkillsHub, OpenToolsHub,
and OpenBenchmarkHub can reuse the **same** wrap-the-reference-implementation play for their `SkillArtifact` /
`ToolArtifact` / `BenchmarkArtifact` metadata. **Governance:** a registry **lists** servers/skills/tools as
**candidates** — listing is never trust, never active.

---

## Per-hub backend breakdown

### OpenMCPHub

| Backend component | Candidate repos | Recommended | Posture |
|---|---|---|---|
| MCP registry (core) | [Official MCP registry](https://github.com/modelcontextprotocol/registry) (MIT) | **Official MCP registry — fork/wrap as a compatible sub-registry** | Wrap; local Postgres + seed fixtures; offline golden path |
| Discovery feeds | [Glama](https://glama.ai/mcp/servers) (10k+, scored), [Smithery](https://smithery.ai) (7k+), [mcp.so](https://mcp.so) (~20k) | snapshot-ingest, not live crawl | Candidate; discovery != trust; cached snapshots behind a `DiscoveryFeedPort` |
| Gateway / serving (optional) | [microsoft/mcp-gateway](https://github.com/microsoft/mcp-gateway) (K8s), [Docker MCP Gateway](https://github.com/docker/mcp-gateway), [IBM ContextForge](https://github.com/IBM/mcp-context-forge) | in-process stub for the golden path | **Container/K8s-gated → owner-gated**; candidate only |

**Caveats:** all three gateways need **Docker/K8s** (Docker MCP Gateway is explicitly owner-gated per repo
guardrails). Discovery aggregators have **unverified licenses/ToS** — redistribution needs a license check;
ingest cached snapshots, not a live crawl, until the owner authorizes it. Confidence: registry = **verified**
(MIT); discovery sources = **unverified**.

### OpenContextHub

| Backend component | Candidate repos | Recommended | Posture |
|---|---|---|---|
| Vector search | [pgvector](https://github.com/pgvector/pgvector), [Qdrant](https://github.com/qdrant/qdrant), [LanceDB](https://github.com/lancedb/lancedb), [Milvus](https://github.com/milvus-io/milvus) | **pgvector** (simplest — a Postgres extension); **LanceDB** for embedded/in-process | pgvector + LanceDB are local-first (no container); Qdrant/Milvus container-typical → candidate |
| Hybrid / keyword search | [Weaviate](https://github.com/weaviate/weaviate) (relativeScoreFusion), [OpenSearch](https://github.com/opensearch-project/OpenSearch), [Meilisearch](https://github.com/meilisearch/meilisearch), [Typesense](https://github.com/typesense/typesense) | **Meilisearch** (MIT, single binary) for the public read surface; Weaviate for native hybrid at scale | Meilisearch/Typesense run as a local binary (no Docker); OpenSearch/Weaviate are JVM/container-heavy |

**Caveats:** **pgvector** aligns with the repo's existing Postgres/pgvector load plans → lowest friction,
**verified** PostgreSQL license. **Typesense is GPL-3.0** (copyleft) — license review required before backend
adoption; **Meilisearch (MIT)** is the lower-risk default. Qdrant/Milvus/OpenSearch/Weaviate are container/JVM
deployments → **Docker-gated, candidate**. Single source of truth: embedding dimension/config must come from
one config module, not parallel literals (repo no-magic-values law).

### OpenHarnessHub

| Backend component | Candidate repos | Recommended | Posture |
|---|---|---|---|
| Eval harness | [Inspect AI](https://github.com/UKGovernmentBEIS/inspect_ai) (UK AISI, MIT), [promptfoo](https://github.com/promptfoo/promptfoo), [DeepEval](https://github.com/confident-ai/deepeval), [Ragas](https://github.com/explodinggradients/ragas) | **Inspect AI** — task + tool-use native, framework-grade, MIT | Candidate behind an `EvalHarnessPort`; run against a local/mock model for the offline path |

**Caveats:** **promptfoo** was reportedly **acquired into OpenAI (Mar 2026)** — re-verify project
governance/independence before backend reliance (flagged in the registry). DeepEval/Ragas use **LLM-as-judge**
metrics → judge output is **evidence, not truth**. Eval/agent environments (Repo2RLEnv, Harbor, OpenEnv) are
cataloged in [`agent_environment_research_registry.json`](../../architecture/agent_environment_research_registry.json)
— **cross-ref, not duplicated here.** Confidence: Inspect AI & promptfoo licenses **verified** (MIT);
DeepEval/Ragas **unverified** (likely Apache-2.0 — confirm).

### OpenBenchmarkHub

| Backend component | Candidate repos | Recommended | Posture |
|---|---|---|---|
| Benchmark runner | [lm-evaluation-harness](https://github.com/EleutherAI/lm-evaluation-harness) (MIT) + the eval frameworks above | **lm-evaluation-harness** as the academic-yardstick **reference** | Reference (compared against, not run as live infra) |
| Registry service | [Official MCP registry](https://github.com/modelcontextprotocol/registry) pattern for `BenchmarkArtifact` metadata | wrap the registry pattern | Candidate; local seed data offline |
| Benchmark environments | Repo2RLEnv / Harbor / OpenEnv — **see [`agent_environment_research_registry.json`](../../architecture/agent_environment_research_registry.json)** | (cataloged there) | **Cross-ref, do not duplicate** |

**Caveats:** a benchmark **result is EVIDENCE, never a promotion authority** — the hub stores results, it does
not promote anything from them. The environment backends are Docker/network/LLM-gated and already governed in
the environment registry.

### OpenCompressionHub

| Backend component | Candidate repos | Recommended | Posture |
|---|---|---|---|
| Context compression | [Microsoft LLMLingua](https://github.com/microsoft/LLMLingua) + LLMLingua-2 (MIT) | **LLMLingua / LLMLingua-2** | Candidate behind a `ContextCompressionPort`; runs locally with a small compressor model |

**Caveats:** compression here is governed by the repo's **Lossless Distillation law** — distillation is never
replacement. Compression may shrink the text surface **only if** answer-critical facts + source handles +
held-out warnings survive, the **original context is preserved**, and **rehydration is provable**. Reported
ratios up to ~20x (4–10x in production). License **verified** (MIT). Deeper notes:
[`context-compression-tools.md`](context-compression-tools.md).

### OpenSkillsHub

| Backend component | Candidate repos | Recommended | Posture |
|---|---|---|---|
| Skill format | [SKILL.md open format / agentskills spec](https://github.com/agentskills/agentskills) | **conform to SKILL.md** (reference standard) | Reference; parse/validate locally |
| Registry service | [Official MCP registry](https://github.com/modelcontextprotocol/registry) pattern for `SkillArtifact` metadata | wrap the registry pattern | Candidate; local seed data offline |

**Caveats:** **~13%+ of marketplace skills reportedly carry critical vulnerabilities** → a **security/scan
gate is mandatory**, and provenance / signed-publisher checks apply. A listed skill is a **candidate, never
auto-active**. SKILL.md license is **unverified** (open standard — confirm).

### OpenToolsHub

| Backend component | Candidate repos | Recommended | Posture |
|---|---|---|---|
| Tool registry | [Official MCP registry](https://github.com/modelcontextprotocol/registry) pattern for `ToolArtifact` metadata | wrap the registry pattern | Candidate; local seed data offline |
| Tool discovery | overlaps OpenMCPHub discovery (Glama / Smithery / mcp.so) | snapshot-ingest | Candidate; **discovery != trust** |

**Caveats:** OpenToolsHub's catalog **overlaps OpenMCPHub** discovery sources (MCP tools are tools) — reuse the
same `DiscoveryFeedPort` snapshots rather than building a parallel crawler. Discovered tools are candidates.

---

## Generic site-backend pattern (original tracked backend candidates)

Every Open*Hub is, at its core, a **registry SERVICE + a public read surface**.
This research note originally scoped the seven backend candidates listed in
`architecture/openhubs_backend_candidate_registry.json`; the same pattern should
be extended to the newer OpenSkillToTool, OpenReviewHub, private-bench hubs, and
Baltor method hubs only after their backend candidate records are added:

1. **Registry service** — metadata records pointing at packages (npm / PyPI / Docker). The OSS
   [official MCP registry](https://github.com/modelcontextprotocol/registry) (MIT) is the **reference
   implementation**; fork/wrap it per hub behind a `*RegistryPort`. Local Postgres + seed fixtures = offline
   golden path.
2. **Public read surface** — a static site fronted by **search**. **Meilisearch (MIT, single binary)** is the
   recommended low-friction default; Typesense is an alternative but **GPL-3.0** (license review first).
3. **Governance plane (everywhere)** — listing/scoring is discovery, not trust; every external item is a
   candidate behind a port; benchmark/eval output is evidence, not promotion authority; the hub is a registry,
   not a truth authority.

## Honest confidence summary

- **Verified licenses (MIT/permissive):** official MCP registry, pgvector (PostgreSQL), LanceDB, Qdrant,
  Milvus, OpenSearch, Meilisearch, Inspect AI, promptfoo, lm-evaluation-harness, LLMLingua (all Apache-2.0/MIT
  per source repos — confirmed permissive).
- **Unverified / needs a license check before adoption:** Glama / Smithery / mcp.so (discovery ToS),
  microsoft/mcp-gateway, Docker MCP Gateway, IBM ContextForge, Weaviate (BSD-3 likely), **Typesense (GPL-3.0 —
  copyleft, review required)**, DeepEval / Ragas (Apache-2.0 likely), SKILL.md spec.
- **Container/cloud-gated (owner-gated, candidate only):** all three MCP gateways, Qdrant, Milvus, OpenSearch,
  Weaviate.
- **Watch flags:** promptfoo OpenAI acquisition (governance/independence); skill-marketplace vuln rate
  (security scan mandatory).

## See also

- [`architecture/openhubs_backend_candidate_registry.json`](../../architecture/openhubs_backend_candidate_registry.json) — structured entries + governance law.
- [`architecture/open_hubs_bridge_graph.json`](../../architecture/open_hubs_bridge_graph.json) — hub relationship chain; "hubs are not truth authorities."
- [`architecture/agent_environment_research_registry.json`](../../architecture/agent_environment_research_registry.json) — Repo2RLEnv / Harbor / OpenEnv benchmark+harness environments (not duplicated here).
- [`docs/research/context-compression-tools.md`](context-compression-tools.md) — LLMLingua compression notes.
