# Monetization Mechanisms — what an export can't freeze

> **The principle.** The export is the commodity — a technical user *should* be able
> to export a flow and self-host it; that's the funnel, not the business. Recurring
> revenue is **everything an export can't freeze**: freshness, gated verified data,
> and hosted processing. We don't fight the export; we monetize what decays.
>
> **Proof it's worth paying for (measured live, 2026-05-28, via Ollama):** on a 2026
> regulatory change, the **bare model answered the stale value (PHP 500k)** and the
> **grounded pipeline answered correctly (PHP 1M)** — a **measured +1.0 lift**. That
> delta is exactly what a frozen export loses the moment the fact moves. Freshness is
> not a nicety; it's measurable capability.

## Two orthogonal axes (both implemented)

A component carries two independent billing properties, each computed automatically
and stamped on its `index_record`:

| Axis | Question | Module | Values |
|---|---|---|---|
| **Openness** | Is the *content* free or commercial? | `scripts/foundry/openness.py` | `open` (free) · `commercial` |
| **Delivery** | How is it *delivered & billed*? | `scripts/foundry/access.py` | `frozen_export` · `live_subscription` · `credentialed_data` · `hosted_endpoint` |

They're orthogonal: a **gov-published fact is `open` (free) but `live_subscription`**
(the snapshot is free; the auto-updated feed is the subscription). A **verified RAG
corpus is `commercial` + `credentialed_data`** (the data is gated and metered).

## The delivery / billing model (your three ideas, implemented)

| Delivery | What you get / what's metered | Billable event | Applies to |
|---|---|---|---|
| **frozen_export** | Fully bundled; free; offline forever (a static snapshot) | — | open static content + logic/scaffolding |
| **live_subscription** *(idea #1)* | Export = a **dated snapshot**; staying current (re-scrape + CDC + revocation, full date + provenance) = subscription | `refresh` | any **dynamic** corpus — incl. *free* gov facts (snapshot free, freshness paid) |
| **credentialed_data** *(idea #3)* | Flow + schema export, but **querying the verified data** needs a billed credential to the hosted corpus | `data_query` | commercial **verified RAG databases / curated corpora** |
| **hosted_endpoint** *(idea #2)* | Runs on **our servers** (managed processing / API proxy), metered per call; or self-host with your keys | `hosted_call` | code-executing (custom tools, harnesses, pipelines) |

## The freshness engine (your scraper point)

The recurring value needs a supply of fresh, verified facts. Even without external
publishers on the platform, **government / standards-body scrapers** are a
first-class **source surface** (a `sources.SourceScout` impl, e.g. `GovScraperScout`):
fetch → capture **full date + provenance + source_url** → emit a **dynamic Knowledge
Corpus** with `freshness: volatile` + CDC. That corpus is `open` (gov-published = free
content) but `live_subscription` (the maintained feed is the paid value). When a fact
changes, CDC + revocation propagate to subscribers — and an alert fires (below).

## The full mechanism catalog (the "what else is there")

**Already designed (subscription + usage):**
1. **Tiers** — Free / Pro / Team / Enterprise (see the monetization brief).
2. **Live knowledge subscription** — the freshness feed (`live_subscription` / `refresh`). *(#1)*
3. **Credentialed data access** — exported flow + billed credential to the hosted corpus (`credentialed_data` / `data_query`). *(#3)*
4. **Hosted processing endpoint** — managed run / model-API proxy (`hosted_endpoint` / `hosted_call`). *(#2)*
5. **Usage metering** — embeddings, eval runs, source scans, media gen.
6. **Build-on-demand** — premium agent builds a capability-request (community builds earn credits).
7. **Marketplace revenue share** — premium / community components.
8. **Managed ingestion** — ingest a customer's procedures / OSS ecosystem into governed components.
9. **Verified-publisher accounts** — gov/standards bodies publish **free**; commercial publishers pay for verification + a `🛡 verified` badge + distribution.

**New additions to consider:**
10. **Freshness SLA tiers** — pay for higher refresh cadence + faster revocation propagation on `live_subscription` corpora.
11. **Audit / compliance packs** — signed attestations + full provenance + review-trail bundles for regulated buyers (one-shot or per-audit).
12. **Alerting / webhooks** — "your cited fact changed / was revoked / a lift decayed" notifications (per-channel, per-volume).
13. **Private tenant registry hosting** — host the customer's own governed components + corpora.
14. **Bulk corpus / data licensing** — license the verified, dated corpus to an enterprise or **AI lab** (bulk, non-metered).
15. **Eval / benchmark-as-a-service** — run the lift benchmark on a customer's pipeline (Import & Improve, paid).
16. **Priority build queue** — pay to jump the capability-request build queue.
17. **Embeddings / vector hosting** — managed pgvector index for a tenant's components.
18. **White-label / OEM + API access** — embed the registry/search/recommend/pricing APIs in a partner product.
19. **Measurement-dataset licensing** — the `bare_vs_pipeline` deltas across thousands of tasks (where pipelines beat bare models) are a unique **training/eval signal** — licensable to a lab (and a core acquisition asset).
20. **Royalty / usage-share** — on the highest-value verified facts or premium components.

## Why "export is free" is a feature, not a leak

A technical user who exports a `frozen_export` flow gets a *static snapshot* — and the
moment the world moves, it silently rots (the +1.0 demo, in reverse). The product's
pitch isn't "you can't leave"; it's **"the value you'd lose by leaving is the freshness,
the verified data, and the managed processing — all measurable."** That keeps the open
funnel wide *and* the recurring layer honest.

## Acquisition angle

For a big AI lab, the durable assets compound on exactly this layer: (a) the
**governed fresh-fact flywheel** (scrapers + CDC + provenance) that stays valuable as
models improve, (b) the **open standard + community** (distribution), and (c) the
**measurement dataset** (#19) — a benchmark of where grounded pipelines beat bare
models, which is scarce, model-improving training signal. The monetization mechanisms
and the moat are the same thing: *what models still can't do reliably, kept fresh and
governed.*

---

*Implemented: `scripts/foundry/openness.py` (free vs commercial), `scripts/foundry/access.py`
(delivery + billable events), both stamped on `stage_load`'s `index_record`. Grounds:
`_repos/_shared/strategy/product-market-monetization-brief.md`, `_repos/_shared/strategy/open-core-model.md`,
`docs/concepts/component-taxonomy-and-stages.md` (execution classes + the pricing boundary).*
