# Context-Engineering Tool Landscape (governed CANDIDATES)

> **Status: research candidates, never adopted runtime.** The tools below are a *due-diligence
> landscape* the owner researched. **candidate ≠ active · discovery ≠ trust · output ≠ truth.** Nothing
> here is pip-installed, executed, or wired into a runtime. Stars / recency / a README claim are
> discovery signals, not proof of fit. Every "finds redundant / finds conflicting / N% savings" below is
> a **claim to verify on our own traces**, not an endorsement.
>
> Machine-readable catalog: `architecture/context_engineering_tool_catalog.json`
> · proof: `scripts/check_context_engineering_tool_catalog.py --self-test`
> · governing laws: `docs/codex/lossless-distillation.md`, the change-verification contract.
> · **Distinct from** `architecture/context_compression_provider_catalog.json` (the PROXY-level /
> code-context compression *providers* from the TokenTamer research) — this is the **broader** landscape
> across five layers. Cross-reference; do not duplicate.

## 1. The failure modes (why context engineering exists)

LangChain's context-engineering writeups name four ways a long, unmanaged context window *degrades* a
capable model — the problem is rarely the model, it is the context handed to it:

- **Context poisoning** — a hallucination or stale/incorrect fact gets written into the context (a
  memory, a summary, a tool output) and is then repeatedly referenced as if true.
- **Context distraction** — the window grows so large that the model over-weights the accumulated
  history and under-weights its own competence / the actual task.
- **Context confusion** — superfluous or irrelevant content (unused tool descriptions, tangential docs)
  is present and influences the response.
- **Context clash** — different parts of the context **disagree** (an old instruction vs a new one, two
  retrieved docs that contradict, a memory that conflicts with the system prompt).

Two of these — **poisoning** and **clash** — are *contradiction* problems (the same thing this repo's
Reconciliation stage exists for). **Distraction** and **confusion** are *redundancy / selection*
problems (the Optimization/compression stage). The landscape below is organized by which lever a tool
pulls.

## 2. The five-layer landscape

| Tool (repo) | Layer | Redundant? | Conflicting? | One-line note (a CLAIM — verify) |
|---|---|:---:|:---:|---|
| token-optimizer (alexgreensh/token-optimizer) | token-waste observability | partial | partial | "Ghost-token" diagnosis + CLAUDE.md/MEMORY.md health + drift. License unverified. |
| squeez (claudioemmanuel/squeez) | token-waste observability | yes | no | Hook-based token compressor across 5 AI CLIs; MinHash dedup; signature mode. |
| openwolf (cytostack/openwolf) | token-waste observability | yes | partial | Claude Code `.wolf/` project map, token ledger, repeated-read warnings (do-not-repeat memory). |
| lean-ctx (yvgude/lean-ctx) | context compression | yes | partial | Broad "context OS": read modes, AST signatures, budgets, verification. *Ambitious all-in-one — verify the claims.* |
| headroom (chopratejas/headroom) | context compression | yes | no | Compress tool outputs/logs/RAG/files; library / proxy / MCP; reversible retrieval. |
| claw-compactor (open-compress/claw-compactor) | context compression | yes | no | 14-stage **reversible** compression, AST-aware, simhash dedup, rewind retrieval. (MIT) |
| context-chef (MyPrototypeWhat/context-chef) | context compression | yes | partial | JS/TS agent context **compiler**: history compression, tool pruning, VFS offload, provider adapters. |
| LLMLingua (microsoft/LLMLingua) | context compression | yes | no | Research-grade **learned** prompt compression. Lossy + model-based → scrutinize vs lossless law. |
| Selective Context (research) | context compression | yes | no | Prunes low-information content to fit more. Lossy + model-scored → verify facts survive. |
| context-mode (mksglu/context-mode) | tool-output isolation | yes | no | Sandboxes large tool outputs; FTS5/BM25 index; folds compact summaries back. **License badge = ELv2 — verify.** |
| rtk (rtk-ai/rtk) | tool-output isolation | yes | no | Rust CLI proxy compresses dev-command output (pytest/cargo/git diff/docker). |
| repomix (yamadashy/repomix) | code-context selection | partial | no | Packs a repo into one LLM-friendly file; tree-sitter compression; MCP tools. |
| code-hud (Tidemarks-AI/Code-HUD) | code-context selection | partial | no | Tree-sitter skeletons/signatures, structural search, symbol-aware editing. *Overlaps CodeGraph.* |
| claude-context (zilliztech/claude-context) | code-context selection | yes | no | Semantic code-retrieval MCP. **Needs embeddings + vector DB** (data-egress concern). |
| code-review-graph (tirth8205/code-review-graph) | code-context selection | yes | no | Tree-sitter structural map, incremental, MCP review context. *Overlaps CodeGraph.* |
| codegraphcontext (CodeGraphContext/CodeGraphContext) | code-context selection | yes | no | MCP+CLI indexes code into a graph DB (callers/callees/chains). *Overlaps CodeGraph.* |
| distill (Siddhant-K-code/distill) | memory / RAG dedupe+conflict | **yes** | **yes** | Write-time dedup, semantic clustering, **conflict detection**, supersession, decay — **no LLM calls.** (MIT) **Strongest find-redundant + find-conflicting match.** |
| memory-guardian (rishipratap10/memory-guardian) | memory / RAG dedupe+conflict | **yes** | **yes** | Exact+vector dedupe, decay, pinned, explainable retrieval, **3 conflict providers** (heuristic/NLI/LLM), `/api/v1/conflicts`. |
| mem0 (mem0ai/mem0) | memory / RAG dedupe+conflict | partial | partial | Popular memory layer; ADD-only extraction, entity linking, temporal reasoning. *Pair with distill/memory-guardian for strict conflict resolution.* |
| aegis-memory (quantifylabs/aegis-memory) | memory / RAG dedupe+conflict | partial | partial | Secure context engineering, integrity verification, trust hierarchy. (Apache-2.0) |

Only **distill** and **memory-guardian** claim to do *both* redundancy **and** conflict detection at the
memory layer — the rest are mostly compression / selection (the distraction & confusion levers). No tool
in the landscape audits redundancy **and** contradiction across *all* context sources at once. That is
the gap.

## 3. The gap: a Context Auditor (Baltor-owned, build in progress)

**Thesis.** No single mature repo audits redundancy **and** contradiction across **all** context
sources — system prompt, `CLAUDE.md`, `AGENTS.md`, MCP tool descriptions, retrieved docs, memories, tool
outputs, code comments — assigns **authority/recency**, and emits an **auditable optimization manifest
before each LLM call**. The tools above each cover one slice (token waste, or compression, or code
selection, or memory dedup); none unifies all sources behind one governed, deterministic pre-call audit.

**Realization in this repo — CONNECT, don't recreate.** The Context Auditor MVP
(`src/baltor/context_audit`) is *not* a new engine. It **composes the deterministic engines this repo
already has** into one pre-LLM-call manifest:

| Failure mode it addresses | Existing Baltor/Teleon subsystem the Auditor calls (do not re-build) |
|---|---|
| Context **clash** / poisoning (contradiction) | **Reconciliation stage** → `context_graph.find_contradictions` |
| Context **distraction / confusion** (redundancy, budget) | **Optimization stage** → `context_compress` |
| Stale / decaying context (freshness, repeated reads) | **Anti-Fragility** → `context_rot` |
| On-demand source discovery + deterministic verification | **ContextOps Verification Foundry** (agents PROPOSE, Baltor DISPOSES) |
| Pre-call assembly for the actual model invocation | **Teleon Inference Gateway / LLM router** (the manifest is what feeds the call) |

The Auditor **PROPOSES** an optimization manifest (what is redundant, what conflicts and which side has
authority, what to drop/compress); Baltor **disposes**. It never silently rewrites context, and its
output is **never** promoted to truth.

## 4. Layered architecture: Auditor → Optimizer → Router

The owner's framing is a three-stage spine sitting in front of every model call. Each stage maps to
something this repo already runs:

```
   raw context sources (kept intact — lossless)
   ┌──────────────────────────────────────────────────────────────────────┐
   │ system prompt · CLAUDE.md · AGENTS.md · MCP tool descriptions ·        │
   │ retrieved docs · memories · tool outputs · code comments              │
   └──────────────────────────────────────────────────────────────────────┘
                                   │   (nothing deleted; raw + lineage retained)
                                   ▼
        ┌───────────────────────────────────────────────────────────┐
        │  1) CONTEXT AUDITOR        (src/baltor/context_audit, MVP)  │
        │     • find redundancy   → Optimization / context_compress   │
        │     • find contradiction→ Reconciliation /                  │
        │                            context_graph.find_contradictions │
        │     • freshness / decay → Anti-Fragility / context_rot       │
        │     • assign authority + recency to each source             │
        │     ⇒ emits an AUDITABLE optimization manifest (PROPOSES)    │
        └───────────────────────────────────────────────────────────┘
                                   │   manifest (proposal, not truth)
                                   ▼
        ┌───────────────────────────────────────────────────────────┐
        │  2) OPTIMIZER              (Optimization stage)             │
        │     • applies the manifest: compress / drop / keep          │
        │     • LOSSLESS: supersede ≠ delete; raw + lineage + held-out │
        │       survive; a rehydration target always exists           │
        └───────────────────────────────────────────────────────────┘
                                   │   optimized, governed context payload
                                   ▼
        ┌───────────────────────────────────────────────────────────┐
        │  3) ROUTER         (Teleon Inference Gateway / LLM router)  │
        │     • selects model via the numeric provider graph          │
        │     • records a ModelInvocationReceipt (actual model +       │
        │       fallback trail); model OUTPUT is never truth          │
        └───────────────────────────────────────────────────────────┘
```

The landscape tools are *inputs* to stages 1–2 (ideas, techniques, benchmarks), never the runtime of any
stage.

## 5. Governance caveats (non-negotiable)

- **candidate ≠ active.** Every tool in the catalog is `status: "candidate"` with
  `do_not_adopt_as_runtime: true`. The proof asserts 0 active. Adoption of any tool — even its code
  ideas — is a separate, warranted decision.
- **never adopt as runtime / never pip-install.** These are studied for their *ideas* and to map the
  landscape, not vendored. Proxy / MITM modes (headroom proxy, rtk, context-chef provider adapters) are
  network-path concerns — verify no off-machine sends before *any* local evaluation; never in a shared
  deployment.
- **LOSSLESS dedupe / supersession.** Any tool whose value is "dedup / supersede / decay / compress"
  (distill, memory-guardian, claw-compactor, the compression tools) is governed by
  `docs/codex/lossless-distillation.md` *if we adopt its ideas*: **supersede ≠ delete.** The raw layer,
  lineage to the superseded/losing items, and held-out warnings always survive. No destructive overwrite
  of a truth-bearing fact; a smaller payload that drops an answer-critical fact or a source handle is a
  **failed** compression, not a cheaper one.
- **output ≠ truth.** Conflict detectors that use an NLI or LLM provider (memory-guardian's
  NLI/LLM modes, any learned compressor) produce *proposals*. Their output is never auto-served and never
  promoted to truth — Baltor disposes.
- **current ≠ verified.** A tool being recently active / trending says nothing about its fit, license, or
  security. Licenses recorded "unverified" must be confirmed before use; the ELv2 badge on context-mode
  (managed-service restrictions) matters for a hosted product; embedding/vector-DB/graph-DB dependencies
  (claude-context, codegraphcontext) are data-egress questions to answer first.

## 6. Recommended evaluation shortlist

If/when an evaluation is warranted (owner decision — this is a research artifact, not a green light), the
highest-signal, lowest-risk slice to study **first**, one per lever:

1. **token-optimizer** — *observability first.* Cheap diagnosis of where the budget actually goes
   (ghost tokens, CLAUDE.md/MEMORY.md health) before changing anything. (Verify license.)
2. **distill** — *the conflict + dedup workhorse.* The strongest find-redundant **and** find-conflicting
   match, **MIT**, and explicitly **no LLM calls** (deterministic, aligns with our deterministic-tool
   requirement). Adopt ideas **losslessly**: supersede ≠ delete.
3. **memory-guardian** — *the explainable-retrieval + conflict-API comparator.* Evaluate its **heuristic**
   conflict provider (deterministic) against distill; treat the NLI/LLM providers as proposals only.
4. **context-mode** *or* **headroom** — *tool-output isolation.* Sandbox/compress the largest single
   source of bloat (tool outputs). Prefer context-mode's BM25-index pattern; **verify ELv2** before any
   use. headroom is the library/MCP alternative (verify reversible retrieval truly rehydrates).
5. **a code-graph tool** — *code-context selection*, but note **all of these overlap our existing
   CodeGraph** (codegraphcontext / code-review-graph / code-hud). Evaluate against what we already run
   before adding a second graph DB; repomix is the "pack, don't select" baseline to beat, not adopt.

Every item above is studied for its **technique and as a benchmark target**, behind the governance in §5.
The deliverable of any evaluation is a *measured* comparison on our own traces (tokens saved, fidelity
retained, conflict precision/recall, false-compression rate, rehydration rate), never a "we adopted X."
