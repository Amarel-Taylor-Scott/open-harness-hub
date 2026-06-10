# App-tooling research — verified June 2026

Scope: the tools behind the whole-app tracks (HITL, version control, graph interrogation, lift
testing, swarms, free/local LLM, deterministic compression). **Verify-first**: every tool here was
web-checked for currency; the loop must still pin a version + re-confirm license/fit before adopting.
Verified backend catalog of record is `data/backend-tools.yaml`; this complements it for the app layer.

## Corrections vs the initial brief (important)
- **OpenAI Swarm is deprecated.** Its README redirects to the **OpenAI Agents SDK**
  (`openai-agents-python`, the production successor since Mar 2025, ~v0.17 by mid-2026). Treat Swarm
  as an *educational reference only* — do not cite it as production substrate.
- **DVC is now under lakeFS stewardship** (lakeFS acquired the DVC OSS project from Iterative). DVC
  stays OSS for individual/small-team data+model versioning; lakeFS for petabyte-scale lakes. They
  are complementary, same family — recommend them together, not as rivals.
- **AG-UI graduated from "candidate" to production-legitimized**: CopilotKit raised $27M and AWS
  Bedrock AgentCore added AG-UI support (Mar 2026). The 2026 protocol stack = **MCP** (tools) +
  **A2A** (agent↔agent) + **AG-UI** (agent↔user).

## Human-in-the-loop
- **LangGraph interrupts** — durable pause/resume of a graph mid-run waiting on human input; the
  standard durable-HITL pattern. LangChain HITL middleware can gate sensitive tool calls by policy.
- **AG-UI / CopilotKit** — agent↔user interaction protocol + frontend stack (TS/Python/Kotlin/Java/
  Go SDKs); supports approvals, shared state, generative UI. Production-grade as of 2026.
- **HumanLayer / CodeLayer** — human-approval supervision around agent/coding workflows (watch).
- Baltor fit: wire the **existing** `schemas/review-ticket` + `governance/steward-review-*` into a
  persisted queue; use interrupts or a DB queue for the pause. Don't add a new review schema.

## Full version control
- **Git** — code/docs/prompts/skills/workflows/schemas.
- **DVC (lakeFS)** — datasets, fixtures, model artifacts versioned alongside Git.
- **lakeFS** — Git-like branch/merge/commit over object storage (raw + parsed artifacts at scale).
- **Dolt / Doltgres** — Git-for-data SQL; **Dolt 2.0** (May 2026) version-controls **vectors** too;
  Doltgres (Postgres flavor) is Beta/production-ready. Use for versioned-SQL experiments.
- **W3C PROV / OpenLineage** — lineage models (entity→activity→agent; run/job/dataset facets). Already
  reflected in `context-object.schema.json` (`provenance`, `lineage`) and the new
  `lineage-manifest` / `source-locator` schemas.

## Graph interrogation (viz)
- **Cytoscape.js** — graph analysis + interactive exploration with built-in algorithms; best for the
  small demo graph. **Sigma.js + Graphology** — WebGL, best for large-scale rendering. vis-network for
  simple interactive diagrams; Neo4j Bloom as a polished reference over Neo4j.
- Baltor fit: `/graph` over `demo-data/acme-billing/seed-graph.json`; SVG/table fallback if no JS lib.

## Lift / regression testing
- **Inspect AI** (UK AISI + Meridian Labs) — 200+ prebuilt evals, multi-provider, safety-grade.
- **DeepEval v4** (May 2026) — pytest-native, G-Eval/DAG metrics, agentic eval harness.
- **Phoenix / Langfuse / Braintrust** — tracing + eval datasets from prod traces.
- Baltor fit: **extend** `scripts/eval/measured_lift_headtohead.py` (paired separate-judge protocol
  already exists) with condition×model arms; keep the no-self-grading + durability-class honesty.
  Treat external frameworks as optional integration stubs, not the core.

## Swarm / multi-agent
- **LangGraph** (multi-agent + handoffs, durable) · **CrewAI** (crews/flows, guardrails, memory) ·
  **AutoGen** (multi-agent + HITL reference) · **OpenAI Agents SDK** (handoffs/guardrails/tracing;
  the production successor to deprecated Swarm).
- Baltor fit: Track-3 swarm is **deterministic-first** (stub agents over graph neighborhood + source
  handles), live-model via `model_gateway`; a framework is an optional executor behind a seam. High-
  risk findings → steward-review; never auto-overwrite canonical objects.

## Free / local LLM (for the demo)
- **Ollama** (`http://localhost:11434`, OpenAI-compatible) · **llama.cpp** OpenAI-compatible server ·
  **OpenRouter** free-model router (rate-limited/variable — not for production) · **Groq** (fast,
  rate-limited, optional). All already supported by `scripts/model_gateway.py` lanes.
- Rule: no paid provider required; deterministic **mock** fallback so the demo runs with zero models.

## Deterministic / non-LLM context compression (answer: yes, and it should be the default)
Run the cheap deterministic ladder before any LLM; LLM is a recorded escalation only.
| Step | Stdlib offline default (shipped in `context_compress.py`) | Stronger tool behind a seam |
|---|---|---|
| token budget | char-ratio estimate | **tiktoken** / model tokenizer |
| boilerplate removal | regex line filter | **trafilatura**, jusText, readability-lxml |
| structural extraction | (input already structured) | **Docling**, tree-sitter, SCIP, ctags, LSP |
| dedupe near-dups | `difflib.SequenceMatcher` | **datasketch** MinHash, SimHash, **RapidFuzz** |
| entity/pattern extraction | regex | **spaCy** Matcher/EntityRuler, dateparser |
| keyphrases | TF top-k | **YAKE**, RAKE, **pke**, PyTextRank |
| query-focused ranking | BM25-lite term overlap | **rank-bm25**, bm25s, scikit-learn TF-IDF |
| extractive selection | budget-greedy lead sentences | **sumy** (LexRank/TextRank/Luhn/LSA) |
| graph-path compression | (use `context_graph` paths) | personalized PageRank, community detection |
**Invariant:** every retained unit keeps a `ctx://` handle; dropped near-dups collapse INTO the
canonical item's handles (reversible). Emit a `CompressionRun`; reference it from pack + LineageManifest.

## Sources
- OpenAI Agents SDK vs Swarm (deprecation/migration): https://www.respan.ai/articles/openai-agents-sdk-vs-swarm · https://github.com/openai/openai-agents-python
- AG-UI / CopilotKit: https://github.com/ag-ui-protocol/ag-ui · https://www.copilotkit.ai/ag-ui · https://learn.microsoft.com/en-us/agent-framework/integrations/ag-ui/
- Dolt 2.0 / Doltgres: https://github.com/dolthub/dolt · https://www.dolthub.com/blog/2026-05-11-dolt-2-dot-0/ · https://github.com/dolthub/doltgresql
- DVC↔lakeFS: https://dvc.org/blog/dvc-joins-lakefs-your-questions-answered/ · https://lakefs.io/blog/dvc-vs-git-vs-dolt-vs-lakefs/
- Inspect AI: https://github.com/UKGovernmentBEIS/inspect_ai · https://inspect.aisi.org.uk/ · DeepEval: https://github.com/confident-ai/deepeval
- Graph viz comparison: https://www.pkgpulse.com/blog/cytoscape-vs-vis-network-vs-sigma-graph-visualization-javascript-2026
- W3C PROV: https://www.w3.org/TR/prov-overview/ · OpenLineage: https://openlineage.io/ · Web Annotation: https://www.w3.org/TR/annotation-model/
- Compression libs: tiktoken, trafilatura, jusText, sumy, rank-bm25, datasketch, RapidFuzz, YAKE, spaCy, tree-sitter (all current, OSS; pin versions on adoption).
