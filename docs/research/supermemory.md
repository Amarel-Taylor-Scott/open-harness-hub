# Supermemory — positioning vs Baltor (verified 2026-06-05)

Source: `_reference/supermemory` (cloned full history, HEAD ad5734cd 2026-06-05; MIT). Repo:
github.com/supermemoryai/supermemory — 25.7k★, Turbo/TS monorepo (TS 63.7%, MDX 29.2%, Py 6.2%),
Postgres + Cloudflare Workers/KV/Pages + Drizzle. **Verify-first: read the actual code/docs, not the
list.** Do NOT npm/pip-install or execute it; keep as `_reference/` + a cataloged *candidate*.

## What it is
"The memory and context layer for AI." Consumer app (Nova agent) + developer API. **#1 on
LongMemEval (81.6%), LoCoMo, ConvoMem.** Surfaces:
- **Memory engine** — extracts facts from conversations, tracks temporal change, resolves
  contradictions, "intelligent forgetting" of expired info.
- **User Profiles** — `profile.static` (long-term facts) + `profile.dynamic` (recent activity); one
  call, ~50ms; inject into system prompt.
- **Hybrid search** — RAG + memory in one query (`searchMode: hybrid|memories|documents`).
- **Connectors** — Google Drive · Gmail · Notion · OneDrive · GitHub · Web Crawler, real-time webhooks.
- **SuperRAG** — managed extract→chunk→embed→index→relationships; multimodal (PDF/OCR/video/code AST).
- **Graph memory** — facts-on-facts with relationship types **Updates** (`isLatest`, history preserved),
  **Extends** (both stay valid), **Derives** (infers new facts from patterns).
- **Distribution** — open MCP server (`mcp.supermemory.ai/mcp`), plugins (Claude Code, OpenCode,
  OpenClaw, Hermes), framework wrappers (Vercel AI SDK, LangChain, LangGraph, OpenAI Agents, Mastra,
  Agno), browser/Raycast extensions. **MemoryBench** — open benchmark harness + an Agent skill
  (`npx skills add supermemoryai/memorybench` → `/benchmark-context`).

## The relationship to Baltor: adjacent, overlapping, differently optimized
Supermemory occupies Baltor's "context layer" TAM ([[context-layer-pmf]]) and the same ingest→consume
arc. Its own concept docs draw the distinction Baltor already lives by:
- **Documents (stateless/unversioned/universal) vs Memories (stateful/temporal/personal/relational)**
  ≈ Baltor's corpus / `global_public` vs tracked facts / `tenant_private`+`tenant_override`.
- **SuperRAG pipeline** (detect type→extract→chunk→embed→relationships) ≈ Baltor
  ingestion→decomposition→vectorize→graph. Validates Baltor's pipeline shape.
- **Graph Updates/Extends/Derives + `isLatest`** ≈ Baltor supersession / reconciliation / CDC / freshness.

### Where supermemory is genuinely stronger (respect it)
Distribution + DX (single API, no vector config), benchmark leadership, connector breadth, plugin/MCP
ecosystem, consumer app, and MemoryBench as a credibility flywheel. Baltor will not out-distribute or
out-recall them; do not try.

### Where Baltor is differentiated — the wedge to protect and sharpen
Supermemory optimizes **frictionless personal recall**; Baltor optimizes **provable, governed,
auditable context** for regulated/high-stakes use. The gap is exactly Baltor's moat
([[moat-reframe-data-not-capability-gap]], [[governance-is-the-product]]):
- **"Intelligent forgetting"** is a *liability* in compliance. Baltor's just-adopted
  **[[lossless-distillation-law]]**: omitted/held-out ≠ deleted; raw + lineage + held-out + rejected +
  rollback always preserved. **This is the cleanest contrast in the whole space — lean on it.**
- **Automatic contradiction resolution by recency (`isLatest`)** vs Baltor **deterministic
  reconciliation by AUTHORITY + receipt** (Reg E 10 days beats a newer FAQ's 30 days; the loser is
  *held out*, not forgotten). Recency ≠ correctness; authority + freshness + provenance do.
- **"Derives" (serving inferred facts)** is precisely what Baltor *holds out* — an inference without a
  source handle is never served as truth.
- **Source handles + portable receipts + accountable signer + tenant-isolation proofs + verification
  gate** — supermemory's pitch is recall quality, not portable provability.

One-liner: **supermemory remembers you; Baltor can prove what it served, why, from where, and how to
roll it back.**

## What to fold in (learn from — behind ports, verify-first, NEVER import as runtime)
1. **Governed User-Profile projection** — adopt `profile.static`/`profile.dynamic` as a *Baltor
   consumption projection*: static = promoted canonical facts (each with source_handle + verification/
   optimization/consumption receipt), dynamic = recent governed context. One call. Strong UX primitive;
   fits ConsumptionService. **Highest-value borrow.**
2. **memory-vs-RAG narrative → "assurance-vs-recall"** — reuse the Documents-vs-Memories framing as
   Baltor's "governed-context (provable) vs RAG (stateless recall)" story in product copy.
3. **GovernedContextBench** — a MemoryBench analog that measures **assurance**, not recall:
   source-handle coverage, held-out-leak rate, stale-fact-served rate, reconciliation-authority
   correctness, tenant-leak rate, portable-receipt verifiability, rehydration success. Open + an Agent
   skill, like theirs. Credibility flywheel that competes on Baltor's axis, not supermemory's.
4. **Connector breadth** — GDrive/Gmail/Notion/OneDrive/GitHub + webhooks validate + extend the new
   `SourceAdapterPort` ingestion roadmap; catalog each as a *candidate* connector behind the port.
5. **MCP + plugin distribution** — expose a governed-context MCP server / Claude-Code plugin so Baltor
   is consumable where supermemory is (we already have `catalog/adapters/gateway/mcp-server-bridge`).
6. **Relationship vocabulary (Updates/Extends/Derives)** — Baltor already has supersession/
   reconciliation; if adopted, **Derives must map to held_out/candidate, never served fact**.

## What NOT to copy (governance lines)
Auto-forgetting; recency-only contradiction resolution without authority/receipt; serving derived/
inferred facts as truth; storing facts without source handles; the TS/Cloudflare runtime (Baltor is a
stdlib-Python governed runtime). Per [[swarm-orchestration-foil-positioning]] + the no-uncataloged-repos
guard: never import or execute it; `_reference/` + catalog candidate only.

## Suggested next actions (not auto-applied — owner warrant for product/strategy)
- Add a `governed_user_profile` consumption projection (port-level design first).
- Stand up GovernedContextBench as the assurance-axis benchmark (sibling to the measured-lift harness).
- Catalog GDrive/Gmail/Notion/GitHub connectors as candidates behind `SourceAdapterPort`.

## Self-host + cost + API surface (owner research 2026-06-05)
- **Openness:** repo MIT + substantial, BUT full production self-host is **enterprise-gated** — the official
  self-hosting guide ships an enterprise deployment package (unique host id + compiled JS bundle + deploy
  script) on Cloudflare Workers + Postgres/pgvector + LLM keys + email + connector OAuth. So: study/borrow
  freely; do NOT assume free self-host of the whole API.
- **Pricing (public):** Free $0 ($5/mo usage) · Pro $19 · Max $100 · Scale $399 (self-host option, SOC2/HIPAA
  BAA) · Enterprise custom (air-gapped). Usage ~ $0.005/1K SM tokens (text) memory, SuperRAG $0.001/1K, search
  $0.005/1K. Self-host infra rough: dev ~$10–50/mo; small prod ~$50–300+/mo; enterprise custom.
- **API surface → Baltor contract mapping** (for the supermemory_api@candidate adapter, behind MemoryProviderPort):
  POST /v3/documents (+ /batch) → MemoryWriteRequest · /v3/search → MemorySearchRequest ·
  POST /v3/documents/list → MemoryDocumentList · GET /v3/documents/{id}/chunks → MemoryChunkSet ·
  profile endpoint → MemoryProfile · /v3/connections/* (list/create/sync/fetch) → ConnectorSyncRequest ·
  mcp.supermemory.ai/mcp (OAuth or Bearer header; x-sm-project scope) → MCPToolRequest.
- **Integration modes:** A no-dep local-only (current/strict gov) · B hosted candidate provider · C MCP for
  coding-agent memory · D enterprise self-host · E Baltor-native memory w/ supermemory-compatible adapter.
- **Memory Router** (api.supermemory.ai/v3/<provider-base-url>): do NOT make it the default model path — it
  couples model calls + memory; only ever an LLMGateway candidate.
- **Tenant-private evidence (e.g. complaint/email/screenshot artifacts):** never default to hosted supermemory
  without consent; route as tenant_private source_document → OCR/parse candidate → narrative allegations →
  entities/deadlines → verification tasks → tenant-scoped response only; if supermemory is used, tenant-scoped
  provider + redaction, output = candidate memory not canonical fact.
