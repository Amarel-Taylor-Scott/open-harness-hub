# Baltor Backend-Tool Verification — synthesis

> **Provenance:** produced by the verification workflow `wsxzk600t` (14 web-research lanes,
> adversarially flagged), 2026-06-04. Each candidate tool from the original (other-AI) lists
> was web-searched and only kept as "verified" with a real URL; the rest were flagged. Full
> per-tool JSON (license/hosting/interface/maturity per lane) is in the workflow output file
> under the session's `tasks/wsxzk600t.output`. **Rule:** domain code depends on the
> *capability layer*, not the vendor — adapters are swappable (see
> `docs/standards/adapter-contract.md` once created).

## 1. Recommended PRIMARY + FALLBACK per capability layer

| Layer | PRIMARY | FALLBACK | Why |
|---|---|---|---|
| **Parser Manager** | **Docling** (MIT, local) | **Unstructured** (Apache-2.0, hybrid) | Docling is fully OSS, broadest format coverage, AI layout/table models, no weight/revenue strings. Unstructured is the battle-tested ETL baseline. Avoid Marker/PyMuPDF4LLM as primary (restricted weights / AGPL-or-commercial); LlamaParse/Reducto are cloud-only. |
| **Repo Directory / CodeGraph** | **ast-grep** (MIT, local) + **aider repo map** (Apache-2.0) | **CodeGraphContext** (MIT, self-host graph) | ast-grep = fast multi-lang structural search w/ MCP; aider's tree-sitter+PageRank map is the proven compact-context builder. CodeGraphContext gives a persistent graph backend. Sourcegraph is proprietary; SCIP is a format, not an engine. |
| **Skills Manager** | **Anthropic Agent Skills** (open SKILL.md standard) | **HarnessKit** (Apache-2.0, multi-agent) | Build on the open standard, not one host; HarnessKit manages skills across 8 agents on native dirs (no shadow copies). |
| **Scraping Manager** | **Crawl4AI** (Apache-2.0, self-host) | **Scrapy** (BSD-3, local) | Crawl4AI emits RAG-ready markdown, lib or Docker, pure Apache. Scrapy = mature high-throughput non-LLM workhorse. Firecrawl core is AGPL; Apify/Bright Data are managed. |
| **API Manager (gateway)** | **LiteLLM** (MIT) for LLM routing; **Kong** (Apache-2.0) for generic L7 | **Portkey Gateway** (Apache-2.0) | LiteLLM = one OpenAI-format interface to 100+ providers w/ keys/cost/guardrails. Kong covers non-LLM API traffic. Portkey doubles as MCP gateway. |
| **API Repo / Catalog** | **Backstage** (Apache-2.0, self-host) | **Apicurio Registry** (Apache-2.0) | Backstage = CNCF-graduated open catalog standard. Apicurio adds versioned OpenAPI/AsyncAPI/schema storage. Port/Kong/Redocly/Stoplight are proprietary. |
| **MCP Gateway** | **IBM ContextForge** (Apache-2.0, hybrid) | **Docker MCP Gateway** (MIT) | ContextForge federates MCP+A2A+REST/gRPC behind one governed endpoint w/ guardrails — on-thesis. Docker MCP Gateway = container-isolated servers + 300+ verified catalog. (Portkey/Bifrost strong alternates.) |
| **Durable Workflow / Agent Engine** | **DBOS** (MIT, Postgres-backed) | **Temporal** (MIT, self-host) | DBOS checkpoints state in your *existing* Postgres — zero extra infra for a Postgres/pgvector stack. Temporal = proven heavyweight. Agent-framework layer: **Pydantic AI** primary, **LangGraph** fallback. |
| **Temporal Claim Graph / Memory** | **Graphiti** (Apache-2.0, self-host) | **Cognee** (Apache-2.0, hybrid) | Graphiti = only open engine with native bi-temporal (valid-time + ingestion-time) claim modeling — exact substrate for verified claims (it's the engine under Zep). |
| **Graph DB Substrate** | **HelixDB** (AGPL) or **Memgraph** (BSL) | **FalkorDB** (SSPL) | Purpose-built graph+vector; source-available w/ service-distribution caveats (fine internally). **Do NOT adopt original Kuzu — archived Oct 2025; use a maintained fork.** |
| **Hybrid Retrieval** | **Qdrant** (Apache-2.0, hybrid) | **pgvector** (PostgreSQL License) | Qdrant = pure-Apache Rust, native dense+sparse hybrid + filtering. pgvector keeps retrieval *in* Postgres for the demo/light path (combine w/ FTS). |
| **Observability + Evals** | **Langfuse** (MIT core, hybrid) | **Arize Phoenix** (ELv2) + **Ragas** (Apache-2.0) | Langfuse = mature OSS tracing+evals+prompts, OTel-GenAI compatible. Emit to the **OTel GenAI semantic conventions** for portability. |
| **Sandboxed Execution** | **E2B** (Apache-2.0, hybrid) | **microsandbox** (Apache-2.0, self-host) | E2B = mature Firecracker-microVM sandbox w/ clean SDKs, self-hostable. microsandbox = local-first libkrun. (Firecracker/gVisor/Kata are substrates, not turnkey.) |

## 2. Hallucination / unverified / untrustworthy-name report

These are entries from the original (other-AI) lists you should **not** trust verbatim:

| Tool / Name | Lane | Why flagged |
|---|---|---|
| **Synapse AI** | workflow_engines | **Likely hallucinated.** No canonical "Synapse AI" durable workflow/agent engine; name maps to several unrelated small projects. Disambiguate or drop. |
| **Microsoft Conductor** | workflow_engines | **Real but wrong-fit + name collision.** A CLI for deterministic multi-agent *dev* workflows — NOT a server-side durable engine. Bare "Conductor" usually means Netflix/Orkes conductor-oss. Verify before adopting. |
| **Kuzu** | graph_memory | **Real but dead upstream.** `kuzudb/kuzu` archived Oct 2025; survives only via forks (LadybugDB, Bighorn/Kineviz, Vela). Do not adopt the original. |
| **Neo4j GraphRAG** | graph_memory | **Real but mislabeled.** It's a *retrieval library*, not a graph-memory store — requires a separately-licensed Neo4j server (GPLv3 Community / commercial Enterprise) underneath. |
| **Marqo** | retrieval | **Real but pivoted/decayed.** Shifted to "AI-native ecommerce search"; standalone vector product no longer actively maintained. Not recommended as general hybrid-retrieval. |
| **GitHub `gh skill` / agent skills** | skills_managers | **Ambiguous (conflated).** Two real things: first-party `gh skill` in GitHub CLI v2.90.0, and third-party `nicholasspencer/gh-skill` (Gists). Disambiguate. |
| **LiteParse** | parsers | **Real — metadata correction.** LICENSE is **Apache-2.0** (a snippet wrongly said MIT). LiteParse = LOCAL parser; LlamaParse = separate CLOUD product (both real). |
| **SCIP** | repo_codegraph | **Real — slug/category correction.** Canonical repo is `sourcegraph/scip` (spec: scip-code.org). SCIP is a protocol/format, **not** a runnable engine. |
| **Envoy (as "API gateway")** | api_gateways | **Real — label imprecise.** Envoy is an L4/L7 proxy; the gateway products are **Envoy Gateway** / **Envoy AI Gateway**. |
| **Composio (license)** | api_gateways | **Real — data conflict.** One source said ELv2; actual LICENSE is **MIT** (Sampark Inc, 2025). Hosted platform is still commercial/freemium. |

**Net takeaway:** Only **"Synapse AI"** is plausibly fully invented. **"Microsoft Conductor"** and **"Marqo"** are real but the wrong/decayed thing for their lane. The rest are real but carry a correction the original list got wrong (dead upstream, mislabeled, conflated, license error, category error).

## 3. Free demo APIs — see `research/free-demo-apis.md`

The free public API shortlist (no-/low-auth, for the non-commercial demo) was extracted to its own file for the Phase-5 connectors.
