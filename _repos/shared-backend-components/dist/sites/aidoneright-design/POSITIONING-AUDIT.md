# Positioning & Language Audit — Baltor / ContextIsEverything

A grounded read on (1) category-language alignment with the 2026 market, (2) marketing
language vs backend/architecture language, and (3) product–market-fit signal. Companion to
`MARKETING.md` (the canonical messaging) and `products.js` (the identity source of truth).

_Researched June 2026 against the current market. Treat external numbers as directional._

---

## 1. The category has a name now: **context engineering**

The market converged in late 2025–2026 on **"context engineering"** as the umbrella term —
Anthropic formalized it (Sept 2025) as curating the optimal set of tokens during inference;
by 2026 trade press calls it "the defining AI skill of 2026," and vendors (Atlan, Salesforce,
Google) build it into their language. Prompt engineering and RAG are now framed as *subsets* of
it.

**Implication for Baltor.** Baltor should not *fight* this term — it should claim the
**governance / assurance layer of context engineering**. The market explicitly says the
*hard, under-served, valuable* part is governance, not retrieval:
- Atlan's thesis: teams "don't win at the retrieval layer — they win at the context layer
  underneath," ensuring data is classified, permissioned and trustworthy *before the first
  query is served*. That is almost verbatim Baltor's "before any agent reads it."
- NStarX frames RAG's 2026–2030 arc as moving "from a retrieval pipeline bolted onto LLMs to
  an autonomous knowledge runtime that orchestrates retrieval, reasoning, verification, and
  governance."

→ **Baltor's "Not retrieval. A governed-context engine" is exactly the market's direction.**
Keep it. The one wording caution we already enforce (never plain "context engine" → reads as
RAG) is well-judged; "governed context" / "context governance" / "context hardening" are the
differentiated terms and they're consistent with where buyers are looking.

### Language tweaks worth A/B-testing
- Add a hook that bridges to the category term buyers now search for, e.g.
  *"Context engineering decides what your agent sees. Baltor decides what it can trust."*
- "Context layer" is becoming a recognized noun (Atlan: "the Context Layer for AI"). Baltor can
  use **"the governed context layer"** as a category descriptor in the subhead without diluting
  the four-stage engine story.

---

## 2. Marketing language ↔ backend language map

The strongest surfaces are the ones where the **buyer word and the architecture word are the
same concrete object.** Where they diverge, keep the buyer word on the surface and the
architecture word in docs/handoff.

| Concept | Backend / architecture term | Marketing / surface term | Verdict |
|---|---|---|---|
| Pin a fact to its origin | `source handle` | **source handle** | ✅ shared — concrete, keep everywhere |
| Signed record of a served fact | `ModelInvocationReceipt`, verification/optimization receipt | **receipt** | ✅ shared — "receipt" is the buyer-friendly form; keep |
| Contradiction not served | held-out item | **held out** | ✅ shared — strong, distinctive |
| Conflict resolution | reconciliation / source precedence | **Reconcile** (stage 01) | ✅ aligned |
| Volatile value → live object | refreshable object | **Anti-Fragility / Harden** (stage 02) | ⚠ see below |
| Add citations/relationships | enhancement | **Enhance** (stage 03) | ✅ aligned |
| Token-lean cited pack | optimization / tiers | **Optimize** (stage 04) | ✅ aligned |
| Checked + signed | verification rail | **Verify** (stage 05) | ✅ aligned |
| Output ≠ truth | `llm_output_is_truth=false`, projection-only | "the model never decides truth" | ✅ translated well |
| Capability object (Teleon) | `CapabilityTask` / `PurposeTask` | "capability" / "outcome" | ✅ kept technical term only where devs see it |
| How Baltor calls Teleon | `PurposeTaskProviderPort` | (not surfaced — correct) | ✅ internal-only |

**The one term to watch: "Anti-Fragility."** It's a real engine stage and a good *internal*
name, but it's borrowed jargon (Taleb) that a compliance/ops buyer won't parse. The surfaces
already lead with **"Harden"** / **"hardening"** as the buyer word — keep doing that, and treat
"Anti-Fragility" as the internal/architecture label (like `ObjectShell` or `ExecutionProviderPort`,
which correctly never appear on marketing surfaces). Recommend: on buyer-facing surfaces use
**Hardening** as the primary, "(anti-fragility)" at most as a parenthetical.

**Healthy discipline already in place:** backend nouns that would confuse buyers
(`ObjectShell`, `ExecutionProviderPort`, `RepoIntelClassifier`, `SandboxRunResult`) are absent
from every surface. That separation is correct — don't leak them onto marketing pages.

---

## 3. Product–market-fit signal

**Where the wedge is validated:**
- **Governance-before-retrieval is the consensus gap.** Multiple 2026 buyer guides say the
  failure mode isn't the platform — it's "sending ungoverned data into any platform." Baltor
  sells exactly that missing upstream layer.
- **Staleness / "context rot" is a named, feared problem.** Baltor's hardening + "Stale context
  is a silent outage" hook lands directly on it.
- **Regulated / high-stakes is where governed context is non-optional** (EU AI Act enforcement,
  auditability, "explain the answer to a regulator"). Baltor's demo library (CFPB, OFAC, EUDR,
  FDA, OSHA, tariffs) is precisely this surface — and it's a **sharper, deeper wedge** than the
  horizontal "enterprise search" plays (Glean, Atlan, Writer, Onyx) that dominate the category.

**Where Baltor is differentiated from the incumbents:**
- Incumbents govern *access + freshness of internal documents* (catalog/permissions/lineage).
  Baltor governs **correctness against an external authority** (the regulation/standard/contract
  in force), **holds out contradictions**, and **proves it with receipts** — agent- and
  model-neutral, served into the agent you already run. That verification-against-authority +
  held-out + receipt triad is not what the search/catalog vendors lead with.
- The **open-core** + **oracle-published Verified corpora** model is differentiated distribution.

**Honest gaps / risks to message around:**
- The category is crowded and the big terms ("context layer," "governed RAG") are being claimed
  by well-funded incumbents. Baltor wins on **depth in regulated facts**, not breadth — the
  positioning should stay narrow and concrete (the demos do this well; the horizontal pages
  should resist drifting into generic "enterprise knowledge" language).
- The market quantifies the value of governed context (industry claims of large accuracy lifts
  vs ungoverned). Baltor **deliberately avoids "100% accurate"** — correct. But it currently
  shows the win only qualitatively ("caught the stale value"). Consider a **measured, sourced**
  framing: per-demo it already has a "lift"/"caught" line; an aggregate, clearly-scoped metric
  (e.g. "in this corpus, N conflicts held out, 100% of served facts cited") would meet buyers'
  expectation for a number without overclaiming.

---

## 4. Concrete recommendations (prioritized)

1. ~~**Bridge to the category term.**~~ ✅ **Done** — added `baltor_hero` variant **I** “Context
   engineering picks it. Baltor governs it.” + `baltor_subhead` variant **E** “The governed
   context layer…” in `products.js`.
2. ~~**Standardize “Harden” over “Anti-Fragility” on buyer surfaces.**~~ ✅ **Done** — every
   buyer-facing stage name is now **Hardening** (landing, engine hub, deep-dive, dashboard,
   guided-demo timeline, pipeline). “Anti-fragility” kept only as the internal label + one
   parenthetical; internal keys (`'anti'`) and the filename are unchanged to preserve links.
3. **Add a scoped, sourced metric** to the governance report / engine hub — a number that's
   true-by-construction (citations %, conflicts held out, freshness) rather than an accuracy
   claim. Meets the buyer's "show me the lift" reflex without breaking the no-"100%" rule. *(open)*
4. **Keep the horizontal pages narrow.** Audit the parent + hub copy for generic "enterprise
   knowledge/search" drift; Baltor's edge is regulated-fact depth, not breadth. *(open)*
5. ~~**Adopt “the governed context layer” as the one-line category descriptor.**~~ ✅ **Done** —
   shipped as `baltor_subhead` variant E (above).

None of these require new product claims — they're language alignment + one optional measured
metric. All are A/B-testable through the existing experiments engine.

---

## 5. Open-source competitive landscape (June 2026 research)

**Finding: many adjacent repos, none that do Baltor's job.** The OSS "context stack" clusters
into categories that sit *beside* Baltor, not on top of it:

| Category | Representative OSS | What it does | Baltor's relation |
|---|---|---|---|
| Agent memory / knowledge graph | Graphiti (Zep), Cognee, TrustGraph, CocoIndex | relationships + durable memory, often graph + CDC | governs whether a remembered fact is still **true & authoritative** |
| Tracing / observability | Langfuse, LangSmith, OpenLIT | execution traces — latency, tokens, cost, prompt versions | receipts export as traces; adds the **"was it true?"** layer |
| RAG / answer eval | RAGAS, promptfoo, DeepEval | score faithfulness/relevance/groundedness | verification is **evidence, not authority** — composes, never gates alone |
| Catalog / lineage / governance | DataHub, OpenMetadata, OpenLineage, Marquez | catalog internal data, lineage, access control | governs **correctness vs an external authority** — orthogonal, stacks |
| PII / redaction | Microsoft Presidio | detect + redact sensitive fields | runs as a gate **inside** the pipeline — composes |
| Orchestration | LangChain, LlamaIndex, Haystack, DSPy | wire retrieval/tools/models | Baltor is **framework-neutral** — serves into whatever you run |

**The consensus gap (validated by the market, not just us):** every tool above *retrieves or
measures what it's given* — none decide whether a fact is **authoritative, current, and safe to
serve**. Industry guides say it directly: "every platform retrieves what it's given; none
determine which data is authoritative, who can access it, or whether it's still accurate."
Baltor's **verify-vs-authority · hold-out · receipt** triad is that missing layer.

**Implications:**
- **Position as compose-with, not replace.** Teams already run 3–5 of these. The buyer objection
  is "why not just use the OSS tool?" → answer: those tools are good and Baltor sits *above*
  them (the new `Baltor Where It Fits.html` surface handles this objection honestly).
- **Lean into interop as a moat-friendly story**, not a lock-in: emit lineage a catalog can
  ingest, export receipts a tracer can read, feed eval frameworks / OpenBenchmarkHub. This also
  reinforces the open-hub family narrative (ecosystem, not walled garden).
- **The hubs map cleanly onto OSS categories** — OpenContextHub ≈ memory/context, OpenBenchmarkHub
  ≈ eval, OpenToolsHub/OpenMCPHub ≈ tools — which makes the family's interop posture credible.
- **Honesty guardrail:** name these projects accurately and at category level; mark interop as
  *design intent* of the prototypes, not a shipped integration list (the new page does this).

---

## 6. Teleon competitive landscape (June 2026 research)

Same exercise for the runtime side. **Finding: Teleon's neighbors are agent frameworks,
durable-execution engines, optimizers and eval harnesses — none keep a stable capability
contract while the implementation self-improves under an evidence gate + human-approved bounds.**

| Category | Representative OSS | What it does | Teleon's relation |
|---|---|---|---|
| Orchestration frameworks | LangGraph, CrewAI, OpenAI Agents SDK, Pydantic AI, AutoGen | wire models/tools/state into agent graphs — you ship & own the impl | Teleon keeps the **contract stable** while the impl evolves; can run a graph as one *candidate* |
| Durable execution | Temporal, DBOS, Inngest, Restate, AWS AgentCore | crash-safe long-running workflows | composes as an **execution backend**; Teleon adds eval-gated promotion above it |
| Prompt / program optimization | DSPy, GEPA, TextGrad | optimize prompts/chains vs a metric | **closest neighbor** — but Teleon promotes a whole candidate w/ rollback + boundary approval, not just a tuned prompt |
| Eval / CI gating | LangSmith, Arize AX, promptfoo, RAGAS | score + gate changes; some open PRs a human merges | **evidence decides** — Teleon auto-promotes within bounds + auto-rolls-back; exports evidence to these |
| Sandboxes | E2B, Daytona, LangSmith Sandboxes | isolated execution envs | Teleon runs **candidates** inside them before promotion |
| Agent memory | Letta, Mem0, Zep/Graphiti | durable/temporal memory | adjacent — composes, doesn't replace |

**Teleon's triad (the gap):** stable capability contract · evidence-gated promotion with
auto-rollback · bounded self-adaptation under human-approved boundaries. **Positioning:** Teleon
is **not another agent framework** — it's the layer *above* them that turns a task into a stable,
self-proving capability. Shipped as `teleon/#/fits` (kit-based, violet), mirroring Baltor's
`Where It Fits` page. Same honesty guardrails (accurate at category level; interop = design
intent). This also reinforces the family interop story: Teleon runs **on** LangGraph/Temporal,
feeds LangSmith/Arize, and draws candidates from the open hubs.
