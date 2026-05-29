# The free-vs-paid line + learn-from-Contextual (funnel → moat)

The explicit open-core boundary so the **funnel-to-moat handoff is concrete and we never accidentally
give away the defensible part**. Builds on [[../strategy/two-services-shared-infrastructure.md]],
[[beat-contextual-positioning.md]], the open-core model, and the freezable-vs-recurring boundary
([[monetization-mechanisms.md]]).

## The one rule
**FREE = freezable** (you can download it and it's yours forever). **PAID = anything that must stay
LIVE** — verified, current, provenanced, HITL'd, hosted — *because a static download structurally can't
replicate it.* The defensible part is the *live verification layer*; it is **never** free.

## The line (OHH free/OSS tier vs CEaaS paywall)
| FREE — OHH OSS tier (funnel + low-end wedge) | PAID — CEaaS / governed layer (moat, recurring) |
|---|---|
| Harness + seven-primitive grammar + components + basic flows/pipelines | **Verified / current corpora** — cross-checked vs authoritative truth + cross-corpus |
| SDK/CLI + export emitters (SPDX · C2PA · CycloneDX/AIBOM) | **Freshness / CDC / regulatory-diff** (the live layer — can't be frozen) |
| **Raw + compressed** corpora you can **download** | **Provenance + C2PA signing + attestation registry + oracle-publisher corpora** |
| The build experience (describe→flow), local/offline path | **HITL verification + adversarial corpus-integrity** |
| MCP / open-standards integration; works with the agent you already run | **Hosted hyper-efficient** corpora (live-served — can't freeze) |
| Public-good carve-outs (anti-trafficking etc. — free even as RAG) | **Compliance artifacts as a service** (EU-AI-Act / AIBOM, regulator-facing); build-on-demand; private tenant registries |

## The low-end wedge — NOT price (price is the door, not the room)
Contextual already has a free funnel ("get started free" → enterprise sales), so **"cheaper" is table
stakes, not a wedge** — and solo-dev is low-WTP / high-support, easy to get stuck at the bottom. The real
low-end wedge is **open + portable + governed + works with the agent you already run (Claude Code/Codex)**
— the three things Contextual structurally **won't** do because each undercuts "build on us + our GLM."
Free tools/flows/components are the funnel, the community, **and the data exhaust** that reveals which
verified corpora people actually need (which feeds CEaaS).

## Three non-overlapping channels (they don't cannibalize)
1. **Low-end devs** (OHH free/OSS) — funnel + community + demand signal.
2. **CEaaS verification SaaS** — the recurring moat, fed by what OHH usage reveals.
3. **Upstream supplier** — feeding verified corpora into Contextual/Snowflake/Databricks/Claude Code
   ([[beat-contextual-positioning.md]] "sit upstream"). Distinct buyers, distinct motions.

## Acquisition: design for OPTIONALITY, not dependence
Build something **independently valuable** — "build to flip to Contextual" is fragile (if they pass
you're stranded; it warps the roadmap; acquirers pay for momentum, not eagerness). The complement thesis
that makes an acquirer want us: **oracle/verified corpora + the corpus-verification layer + a PLG/dev
funnel & community they lack + compliance/provenance emitters + downmarket reach** — a tuck-in that
extends them *and* adds assurance.
- **Probable buyers = the data clouds (Snowflake, Databricks)** — actively building corpus-for-agents
  marketplaces, acquire aggressively — a hyperscaler, or a GRC/compliance incumbent. **Not** primarily
  Contextual (early: ~$100M / ~100 ppl / ~2.5 yr, no known acquisition track record — verify).
- **Stay-optionable moves:** clean cap table + standard docs; build on **open standards (MCP, C2PA,
  CycloneDX/AIBOM)** so we're snap-in; clean IP/licensing (no copyleft in the core, a clear contributor
  license); instrument the metrics acquirers price on (active devs, corpora consumed, retention,
  regulated-vertical logos); no single-cloud lock-in.
- **The useful irony:** the upstream/complement positioning that's most *defensible* is also the most
  *acquirable* — **one design serves both.** Don't contort toward "acquisition signals" at users'
  expense; the users + the oracle-publisher relationships **are** the asset.

## Learn from Contextual — adopt the rigor, extend one layer up
Their work is mostly public; study it, then extend where their incentives stop.
| Their release | ADOPT (align → integrable + acquirable) | EXTEND (our wedge) |
|---|---|---|
| **RAG 2.0** (end-to-end optimized; benchmarked on faithfulness HaluEvalQA/TruthfulQA + freshness FreshQA) | the eval rigor + the two axes | an **"is-the-corpus-correct"** eval (source-of-truth), not just answer-faithfulness |
| **Grounded LM (GLM)** (faithful to sources, inline attributions, SOTA FACTS) | groundedness + attribution **conventions** | their GLM is faithful **even when the corpus is wrong** → we verify the corpus IS right |
| **Instruction-following reranker** (recency/doc-type/source/metadata; conflict handling) | the instruction-following pattern | turn conflict-handling into **cross-corpus reconciliation + HITL** |
| **LMUnit** (NL unit-testing for RAG eval; open weights) | **adopt the pattern wholesale** in our measurement layer | an **LMUnit-analog for source-of-truth / corpus-correctness** |

**The one thing to internalize (= our wedge):** their "freshness" means *generalizing to world knowledge
via web search* — **not** keeping a *regulated corpus current against its authoritative source*. That gap
is the whole business. Use their open releases (OLMoE, GRIT, KTO, LENS, LMUnit) per license; aligning to
their eval/attribution conventions also makes us more integrable — and more acquirable.

---
*warrant: user-intent — "draw the explicit free-vs-paid line" + "bundle the Contextual learn-from list";
corroboration — owner's cited research (Contextual's published RAG 2.0/GLM/reranker/LMUnit, FACTS/FreshQA,
Snowflake/Databricks marketplace moves) + the open-core/monetization decision records.*
