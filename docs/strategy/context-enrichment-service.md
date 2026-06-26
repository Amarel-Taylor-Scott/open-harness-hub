# Baltor.ai — the Context Enrichment service (CEaaS) — product spec

> **Brand (2026-05-29, locked — [[brand-architecture.md]]):** this service is **Baltor.ai** (in prose:
> **Baltor**), modules **Verify · Corpus · Compress**, under the company **AI Done Right** (founding thesis: Context is Everything).
> "CEaaS / Context Enrichment" is the working/descriptive term used in this spec and in code; the brand is
> Baltor.

Baltor is a **content + corpus refinery**, not a pipeline builder (that's OpenHubForAI — see
[[two-services-shared-infrastructure.md]]). You give it content (or use our unique governed corpora);
it refines that content into **token-efficiency tiers**, hosts them (or hands them back), and feeds
the corpora + tools into whatever open-ended agent you already run (Claude Code, Cursor, any MCP
client). *OHH is a governed factory for pipelines; Baltor is a refinery-plus-CDN for agent fuel.* Both
burn the same crude (ingestion, compression, embedding, governance, clusters); they sell different
refined products.

## Scope: enrichment + management (lead with enrichment — it's the novel wedge)

Baltor spans **both faces of the context layer**, and they're not equally novel:

- **Context enrichment (the novel wedge — the headline):** making the content itself denser and
  trustworthy — the raw→compressed→hyper-efficient **tiers**, structural + learned **compression**,
  **distillation**, and the **measured-fidelity-per-tier** guarantee. This is the part nobody hosts as
  a governed service, so it leads the brand and the positioning.
- **Context management (the established surround — table stakes):** managing the *lifecycle* of what
  reaches the window — **memory** (recall/reflect/confidence), **retrieval** (vector/lexical/hybrid/
  graph), **freshness/CDC**, **caching**, and window-budget paging (the OS-memory / "what stays on the
  desk" model — [[../concepts/context-layer-and-the-desk.md]]). Mem0/Letta/Hindsight/MemGPT already
  occupy this; we cover it because an agent needs both, but we don't claim novelty here.

Both are already in the catalog (`scripts/seed/context_layer_components.py` = management: memory ·
cache · retrieval · connectors; `scripts/seed/baltor_components.py` = enrichment: tiers · surfaces ·
fidelity). **Sell the enrichment; deliver the management.** The wedge is "governed, measured-fidelity
enrichment"; management is what makes it usable end-to-end.

## The whitespace (why this is a category, not a feature)

The tooling exists — but only as **scattered, single-shot, local CLIs**. **Repomix** is the clearest
proof of the raw→compressed tier: Tree-sitter compression strips function bodies while preserving
signatures for **~70% token reduction**, with per-file token counts, Secretlint scanning, and an MCP
server (`pack_codebase` / `pack_remote_repository`) — it already ships an official Claude Code plugin.
Its neighbors — **gitingest** (Python), **code2prompt** (power CLI), **yek** (speed), **Repo Prompt**
(GUI) — all converge on **MCP**, and **llms.txt / llms-full.txt** is the emerging doc-tier standard
for the same job. **Nobody hosts the tiers as governed, downloadable, freshness-tracked artifacts and
serves them to open agents.** That is Baltor's opening — the governed, hosted, measured version of what
the CLIs do once, locally, ungoverned.

## Three tiers = three distinct techniques = three SKUs

Each tier is a *different mechanism*, which is exactly why they productize as separate SKUs:

| Tier | Technique | Mechanism (shared-backend component) | Numbers |
|---|---|---|---|
| **Raw** | hosted full fidelity | object store + source registry + connectors | source of truth; freezable export |
| **Compressed — structural** | strip bodies, keep signatures | `compress.structural` (Repomix/Tree-sitter) | ~70% on code, structure lossless |
| **Compressed — learned** | token-classification compression | `summarize.llmlingua` (LLMLingua-2) | 2–5× (general 5–20×, up to ~95%); 3–6× faster than v1 |
| **Hyper-efficient** | distilled facts + token-efficient packaging | `memory/*` (Mem0/Hindsight) + `cache/*` | provider cache ~90% + context engine 40–60%; prefix reuse compounds |

The hyper-efficient tier is where value compounds: extracted facts/observations **packaged onto a
cacheable prefix**, so the provider prompt cache (~90% off input at a high hit rate) does the rest —
worth far more than raw compression alone. (There's even an autonomous "active context compression"
result: 22.7% reduction, up to 57% on individual tasks, at identical accuracy.)

## The four consumption surfaces (this is the product design)

The mistake would be shipping Baltor as "an API." To put corpora + tools into open-ended agents, you
meet them **where they actually ingest context** — the four-surface pattern Repomix already proves:

1. **MCP server** (`deliver.mcp_serve`) — live-serve the corpus/tool to Claude Code, Cursor, any MCP
   client. The default surface (MCP is the convergence point); tier-negotiated, CDC-fresh, metered.
2. **Packed file / llms.txt** (`deliver.llms_txt`) — download or paste the tier directly. Works with
   any subscription, **no integration**. The freezable surface.
3. **Claude Code skill / plugin** (`deliver.skill_package`) — distribute the corpus + tools as one
   installable governed unit (Repomix ships exactly this).
4. **CLAUDE.md fragment** (`deliver.claudemd`) — the always-loaded, **near-zero-token** distilled tier
   for stable knowledge that must survive compaction (conventions, glossary).

**Baltor's output isn't an answer — it's a governed corpus rendered into whichever of those four shapes
the user's agent consumes, at whichever efficiency tier they pay for.**

## Pricing logic (falls out of freezable-vs-recurring)

- **Raw + Compressed** are downloadable → **freezable**: one-time or storage-priced. A static download
  is yours forever.
- **Hyper-efficient, live-served and kept fresh against a dynamic corpus** → **recurring**, because a
  static download *can't stay current*. That CDC/freshness obligation is the recurring-revenue moat.

This is the same freezable-vs-recurring boundary as the rest of the product
([[monetization-mechanisms.md]]): you only pay-forever for what must stay live.

## Measured fidelity per tier (the moat — and the honest caution)

Compress too aggressively and you **destroy the model's ability to reason** — the failure mode every
context-optimization guide flags. Baltor lives or dies on **measured fidelity per tier**: every
artifact ships a **published quality delta** (raw → compressed → hyper-efficient) from
`verify.compression_fidelity` — "did this tier preserve enough?" — scored by a *separate* evaluator,
never self-graded. That guarantee is what turns "we compressed your docs" into a trustworthy service
rather than a gamble. It is the **same engine and the same moat as OHH's lift gate** — the shared
measurement engine extended from "does the pipeline lift?" to "did the tier preserve?".

## Built on the shared backend (reuse, not rebuild)

Baltor adds **no new engine** — a surface + a meter + the four emitters over the same substrate OHH
uses (compression/memory/cache components, governed corpora, connectors, the lift/fidelity harness,
the vector store, the workers). A better compressor or a fresher corpus shipped for OHH is instantly a
better Baltor tier. This is why the data plane is attribute-level
([[../codex/schema-extensibility.md]]): a new tier metric (e.g. `token_savings_ratio`,
`fidelity_delta`) is a `dimension-record` both services read, never a per-service column.

## The join (one object, two doors)

A **Knowledge Corpus or tool, produced and governed once**, is consumed two ways: wire it into a
bounded OHH pipeline, **or** serve it via Baltor into an open-ended agent. Same object, same provenance
trail, same lift + compression-fidelity scores — two consumption models, two GTM motions, one backend.
OHH monetizes governed *pipelines*; Baltor monetizes governed *fuel*. The foundry and measurement
engine feed both, so **every component we mint is sellable through either door.**

## Status (honest)

Spec-level. The tier/surface/fidelity **components are seeded as governed definitions** (this turn —
`scripts/seed/baltor_components.py`; lifecycle experimental). Implementation to make Baltor real: the
tier pipeline (raw→compressed→hyper-efficient, hosted + downloadable) on the shared workers, the MCP
serving endpoint, the four emitters, and the token-efficiency + fidelity meter. None of it forks the
backend.
