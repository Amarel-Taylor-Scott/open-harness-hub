# The context layer — the analyst's desk (canonical explainer)

The product story in one image. **The model is an analyst at a desk. The context window is the
desk — small, expensive, easily buried under paper.** A good system keeps only the few distilled
pages that matter on the desk at any moment. Open Harness Hub is the system that decides *which
pages, governed, at minimum token cost* — and proves the result lifts capability over the bare model.

Each layer of the context-layer stack maps to the library:

- **Raw documentation** → the *archive stacks*: authoritative, far too much to pile on the desk.
- **Contextualized docs** → the *card catalog*: points to the few right pages, not the whole shelf.
- **Compressed docs** → *briefing notes*: more signal per inch of desk (summaries, distilled memory, cached prefixes).
- **Sync** → the *re-shelving crew*: keeps the catalog matched to the stacks as documents change.
- **Adversarial** → the *gate guard*: checks no forged note was slipped onto a shelf (prompt injection).
- **Verification** → *footnotes + a fact-checker*: every claim traces to a source; nobody grades their own work.
- **Tool clusters** → the *building + the runners* you dispatch (and whether you rent it, managed, or own it, self-host).

**Rigorous version (for engineers):** it is an **OS memory hierarchy** — context window = RAM,
distilled memory/cache = swap, raw docs = disk, retrieval = the page-fault that pulls disk→RAM,
MCP = the bus. (This is literally how MemGPT/Letta is designed.) OHH's *freezable* components are
the parts you keep resident cheaply; the one model call is the expensive RAM access you minimize.

## The 7 layers → OHH's real component buckets

Three phases: **document pipeline (1–3) · cross-cutting (4–6) · runtime (7).**

| # · Layer | What it does | OHH coverage (real components / surfaces) |
|---|---|---|
| **1 · Raw documentation** | where canonical docs live (verbose, rarely fed raw) | `connectors/` MCP — Confluence · GitLab · Postgres; source registry + scrapers |
| **2 · Contextualized docs** | chunk / embed / graph so an agent fetches the right slice | `retrieval/` — recursive/page chunkers · BM25 · dense · hybrid · exact-id · **graphrag** |
| **3 · Compressed docs** | the token-reduced form that enters the window | `retrieval/` extractive + **llmlingua-compress** · `memory/` distilled · `cache/` prompt/semantic/exact/KV |
| **4 · Sync** | the freshness contract (live vs indexed vs CDC) | freshness scrapers + CDC (`scripts/foundry/scrapers.py`, `/freshness`) |
| **5 · Adversarial** | defend against poisoned / injected content | `processor/prompt-injection-screen` · trust boundaries · read-only scoping |
| **6 · Verification** | traceable + measurably correct | `citation-span-checker` · `cross-encoder-reranker` · rubrics · eval (SkillsBench) |
| **7 · Tool clusters** | where retrieval + inference run | the governed recipe + foundry · `adapter/*` · `deliver/` + `platform/` buckets |

OHH covers all seven with real catalog components — it is the **governed assembler** of the stack,
not a single layer (see [[../strategy/context-layer-pmf.md]]).

## Best practices OHH is built on (field-sourced)

These principles (12-factor-agents, 12-factor-agentops, awesome-context-engineering) are the same
ones OHH enforces by construction — cited so the product's choices are defensible:

- **Everything is context engineering** — better inputs > bigger prompts. → the model-query template + R0–R6.
- **No agent grades its own work, ever** — use a separate reviewer/human. → eval/rubric stage + human-approval gate; lift measured paired, not self-asserted.
- **If it's not in git, it didn't happen** — version CLAUDE.md, `.mcp.json`, manifests. → the whole catalog is git-versioned + content-hashed.
- **Cache first, compress only at a measured breakeven** — provider prompt cache is free. → `cache/` family + the honest "measure the breakeven" note on `llmlingua-compress`.
- **Store what was learned, not raw history** — distilled facts carry more signal/token. → `memory/` distilled + reflect + confidence.
- **Treat all retrieved content as untrusted** — prompt injection is the core threat. → `prompt-injection-screen` + sandboxed trust boundaries + ACL-aware connectors.
- **Keep critical rules out of compaction** — they belong where they survive. → governed Conditionals + the system-prompt contract, not lossy summary.

## Honest caveats (carried from the research)

Agent-memory benchmark numbers (LongMemEval/LoCoMo, Hindsight's 91.4%, Mem0/Zep token footprints)
are **directional** — several don't hold up under scrutiny. OHH's answer is structural: lift is
measured **paired, on the user's data, by a separate evaluator** — never a vendor number, never
self-graded. That is the verification layer doing its job.
