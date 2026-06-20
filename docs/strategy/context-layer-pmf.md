# Context-layer PMF — Open Harness Hub on the consumption thesis

**The market the public tape just validated is exactly ours.** In the SNOW (Q1 FY27 product
rev $1.33B, +34%), MDB (Q1 FY27 $687.6M, +25% re-accel, Atlas +29% with a record $117M net-new),
DDOG (+32%), and NET (+34% on agentic) prints, the common story is a **consumption-priced
"context layer"**: AI doesn't replace the data platform, it feeds it more work — retrieval,
memory, real-time signals, governance, billed per query / per GB / per inference. Altman's
"AI augments, not replaces" walk-back is the bull case: every augmented workflow needs trustworthy
data underneath it. **Open Harness Hub sits in that market — but at the seam the raw infra leaves open.**

## Where OHH sits (and the wedge)

The named winners sell *infrastructure* (a data platform, a vector DB, an observability pipe). The
open-source memory/RAG frameworks (Mem0, Zep, Letta, LlamaIndex, LLMLingua, GPTCache) give you the
*plumbing*. **Both leave the same gap** — and the builder-side research says so explicitly: *"these
frameworks generally lack enterprise governance — no glossary, lineage, or entity resolution, which
is precisely the seam the commercial context-layer vendors are selling into."*

**That seam is Open Harness Hub.** OHH is not another vector DB or memory lib. It is the **open,
governed *assembler*** of the context layer: a network of components — each admitted only on
**measured lift**, carrying **provenance**, and **composable** under the seven-primitive grammar —
that you wire (and swap) into a governed pipeline. The infra is the substrate; OHH is the lift +
governance + composability layer on top. You don't rip out Qdrant/Mem0/LLMLingua — OHH **wraps them
as governed, measured-lift components** you compose under one provenance/eval contract.

The deeper product loop is context control: **adversarially validate context, find fragile context,
keep volatile context fresh, reconcile internal inconsistencies, and strengthen weak dependencies with
better components/tools or verified global context feeds**. The catalog is valuable because it gives
the runtime modular upgrade paths when a context block, rule pack, tool schema, memory, or harness
becomes stale, low-lift, unsafe, or hard to verify. See [[../architecture/context-control-loop.md]].

## The 7-layer context stack → OHH's taxonomy (what we have / the gaps)

| Layer (builder map) | OHH today | Gap to fill |
|---|---|---|
| **Standardization (MCP)** | MCP bridge (`/connect`), provider-neutral routes | MCP-connector components (Confluence/GitLab/Postgres) |
| **Retrieval (vector·lexical·graph·hybrid)** | R0–R6 taxonomy + 20 `processors/retrieval/*` (BM25, dense, fuzzy/regex, exact-id, hybrid, RRF, rerank…) | **graph-RAG**, SPLADE/ColBERT as real components |
| **Memory (Mem0·Hindsight·Zep·Letta)** | only `platform/memory-write` | **a real memory family** (distilled · temporal-graph · agentic · working) ← biggest gap |
| **Compression (LLMLingua)** | `extractive-span-selector`, token-reduction step | **LLMLingua-style** compressor component |
| **Caching (prompt · semantic · KV)** | `platform/cache-write` | **a caching family** (provider-prompt · semantic/GPTCache · KV) |
| **Sync (live·indexed·CDC)** | freshness scrapers + CDC (`scripts/foundry/scrapers.py`, `/freshness`) | — (strength) |
| **Adversarial** | `prompt-injection-screen`, sandbox/trust boundaries, read-only | — |
| **Verification** | `citation-span-checker`, cross-encoder rerank, rubrics, eval (SkillsBench) | — (strength) |
| **Tool clusters / runtime** | the governed recipe + foundry + `adapter/*` | — |

**OHH already covers most of the stack; the build gaps are memory + caching (+ graph-RAG, MCP
connectors).** Those are the families to seed next so the catalog matches the market's spend.

## Why the model fits the consumption thesis

OHH's billing axes are *already* consumption-shaped (see `docs/strategy/monetization-mechanisms.md`):
**build-on-demand** (per assembled flow), **live_subscription** (per governed-corpus refresh, CDC),
**hosted_endpoint** (per metered, scoped retrieval call). That is the per-query / per-GB / per-inference
motion SNOW/MDB are rewarded for — but applied to the *governed component layer*, not raw storage.
The open spec/SDK/export is the free funnel; the governed corpora + measured-lift components + the
live layer are the metered product.

## Builder-side reality (the team's own stack)

The team runs **Claude Code (hub) + Confluence (prose) + GitLab (technical) + custom clusters**, and
weighs **regex/grep vs vector vs hybrid** retrieval, **LLMLingua** compression, **Hindsight/Vectorize**
memory. OHH should: (a) ship **MCP-connector components** for Confluence/GitLab so those docs become
governed corpora; (b) ship the **memory + caching + graph-RAG** components above; (c) keep the
**regex/hybrid** retrieval choice first-class (we already do — R1 options); (d) target **self-hostable /
air-gapped** delivery (the Onyx / UC-San-Diego pattern) as a governed alternative.

## Acquisition read

The context layer is the hottest, most public-market-validated AI-infra thesis of 2026, and the one
thing every player lacks is the **governance + measured-lift + composability** layer. An acquirer
(data-platform, hyperscaler, or model lab) buying into "trustworthy context for agents" is buying
exactly OHH's moat — the open protocol + the governed component network + the lift-measurement harness
(externally validated by SkillsBench). See [[../strategy/acquihire-roadmap.md]],
[[../strategy/skillsbench-alignment.md]], `docs/concepts/retrieval-and-prompt-taxonomy.md`.
