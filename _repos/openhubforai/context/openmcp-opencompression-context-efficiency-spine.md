# /workflows /openmcp-opencompression-context-efficiency-spine

> **STATUS (2026-06-07).** BOUNDARY LOCKED: OpenMCPHub.io (port 9505) + OpenCompressionHub.io (port 9506) added to
> the canonical portfolio map + bridge graph (edges `MCPServerArtifact PROVIDES ToolArtifact`, `CompressionCandidate
> OPTIMIZES ContextArtifact`/`EVALUATED_BY HarnessArtifact`; boundary laws `mcp_discovery_not_trust` +
> `compression_must_preserve_fidelity`), guarded by the updated portfolio proofs. The Context Efficiency Spine is
> recorded as a shared internal layer. CONTRACTS / PROVIDER CATALOGS / PORTS / BAKE-OFF / WEBSITES below are QUEUED.

You are Claude Code running the OPEN MCP HUB + OPEN COMPRESSION HUB + CONTEXT EFFICIENCY SPINE workflow.

**Goal:** research, classify, and integrate context-window-saving tools, MCP servers, compression tools, repo/code
context tools, doc→Markdown tools, usage meters, and Claude Code context-hygiene practices. Adds two surfaces
(OpenMCPHub.io, OpenCompressionHub.io) + one shared internal layer (Context Efficiency Spine).

**Do not:** install everything · trust social star counts · use external/cloud indexing for private code without
policy · let compression drop source handles / receipts / held-out warnings / answer-critical facts · bypass
provider ports · create another runtime · duplicate existing optimization/compression slots.

**Core rule:** Context savings are valid only if fidelity, provenance, source handles, policy, and downstream
correctness survive. **MCP discovery is not trust. Token savings are not success unless fidelity passes.**

## Tool research (OWNER-PROVIDED, UNVERIFIED — verify repo identity/owner/license/stars/last-commit at intake)
| Tool | What | Hub/slot | Rec |
|---|---|---|---|
| Serena | MCP semantic code retrieval/edit/refactor; symbol nav | OpenMCPHub/OpenTools/code-intel | high candidate |
| Context7 | MCP/CLI current docs/API refs | OpenMCPHub/OpenContext/docs | high candidate |
| claude-context (zilliztech) | MCP semantic code search over large repos | OpenMCPHub/OpenTools/code-search | candidate (check cloud dep) |
| token-savior | MCP symbol/call-graph index + Bash-output compaction | OpenMCPHub/OpenCompression | watch/eval |
| caveman | terse-output skill pack | OpenSkillsHub/output-style | useful-but-risky (not customer copy) |
| context-mode | MCP context-window optimization, tool-output sandbox | OpenCompression/OpenMCP | very high |
| token-optimizer | ghost-token finder + usage/cost dashboard | OpenCompression/diagnostic | high diagnostic |
| markitdown (microsoft) | files/docs → Markdown for LLM pipelines | OpenTools/OpenContext/ingestion | high (Baltor ingestion) |
| repomix | pack a repo into an AI-friendly file | OpenTools/OpenCompression/repo-pack | useful w/ guardrails (snapshots, not live dumps) |
| ccusage | local token/cost tracking across coding CLIs | shared observability / cost telemetry | very high internal |
| code-review-graph | local-first code intelligence graph (MCP/CLI) | OpenMCPHub/OpenTools/code-graph | high candidate |
Note: pasted star counts/owners may be stale (e.g. headroom: `chopratejas/headroom` vs `zereight/...`). Store as
owner_provided_unverified signal; verify at intake.

## OpenMCPHub.io — owns MCP server registry/metadata/risk/conformance/install-profiles/permissions/secret-policy/
provenance/sandbox-policy. NOT a runtime; discovery ≠ trust; MCP output ≠ truth; execution gated through
Teleon/OpenTools. First candidates: serena, context7, claude-context, token-savior, code-review-graph, repomix MCP,
GitHub MCP server, modelcontextprotocol/registry + /servers, Glama, Smithery, PulseMCP.

## OpenCompressionHub.io — owns context/tool-output/repo/prompt/RAG compression + token-cost diagnostics + fidelity
benchmarks. Compression is invalid unless fidelity + source handles survive. First candidates: context-mode,
headroom, LLMLingua/LongLLMLingua, token-optimizer, token-savior, repomix, ccusage, markitdown, code-review-graph.

## Context Efficiency Spine (shared internal layer)
Rule: **never load the whole thing if a pointer/symbol/summary/graph/receipt/compressed projection will do.**
Contracts (QUEUED): `schemas/context_efficiency/{ContextBudgetPolicy,ContextBudgetReceipt,ContextWasteReport,
CompressionCandidate,CompressionRun,CompressionScorecard,ToolOutputProjection,RepoContextProjection,
CodeSymbolProjection}.v1` + `schemas/mcp/{MCPServerArtifact,MCPToolArtifact,MCPConformanceReport,MCPRiskReport,
MCPInstallProfile,MCPVisibilityPolicy}.v1`. Ports (extend, don't duplicate): CodeContextProviderPort,
DocsContextProviderPort, MCPRegistryProviderPort, CompressionProviderPort, ToolOutputCompressorPort,
RepoPackProviderPort, UsageMeterProviderPort — each with a local stub. Bake-off harness
(`scripts/check_context_efficiency_bakeoff.py`) measures token/byte reduction + latency + answer-critical/
source-handle/held-out preservation + schema validity + cost; **no promotion if fidelity fails.** Redteam:
compressed pack drops Reg E answer / source handle / FAQ-30 warning · repo pack dumps private repo despite policy ·
dangerous MCP exposed publicly · external index on private code · tool-output compressor hides an error line ·
caveman on customer legal copy · usage tool reads secrets · token "savings" claimed without fidelity · provider
imported bypassing the port. Practical first stack: ccusage (measure) → context-mode/headroom (tool-output) →
Serena/code-review-graph (symbols) → Context7 (docs) → markitdown (ingestion) → token-optimizer (waste). Then a
baseline-vs-stack bake-off scored on tokens/tool-calls/wall-clock/proofs-passed/fidelity.

## CONTEXT EFFICIENCY CLAUSE
Do not waste active LLM context. Use symbol-level code access, docs retrieval, semantic search, tool-output
compression, repo projections, usage metering, and context-budget policies before reading whole files/repos/raw
logs/raw MCP outputs. OpenMCPHub owns MCP discovery/risk/conformance; OpenCompressionHub owns compression/token-cost
+ fidelity benchmarks. Compression is valid only when answer-critical facts, source handles, receipts, tenant
boundaries, and held-out warnings survive. MCP discovery is not trust; token savings are not success unless
fidelity passes.
