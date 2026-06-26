# Acquisition Positioning — why a frontier lab buys Open Harness Hub

> The deliberate end-state: a clean, focused company whose assets **compound as base
> models improve** — the opposite of most AI app startups, which decay as models absorb
> their feature. This brief states the thesis, the PMF, the moat, and what specifically a
> GitHub / Meta / OpenAI / Anthropic / Google would be acquiring. Companion:
> `competitive-positioning-deep-dive.md`, `competitive-swot.md`, `product-market-monetization-brief.md`.

## Thesis (one sentence)

The registry that admits a component **only if it measurably lifts capability beyond a
bare LLM**, keeps it **governed and fresh**, and composes it into a **costed,
model-portable, deployable** flow — i.e. the **operating layer for what models still
can't do reliably.**

## Why it's anti-fragile to model progress (the crux)

Most AI products get *worse* relative to the frontier as models improve. This one gets
**more valuable**, by construction:

- The **capability-lift gate** prunes anything a better model absorbs, so the registry
  stays parked on the *moving frontier* of unmet capability.
- The **moat is orthogonal to model quality:** provenance, signed/verified facts,
  citations, review trails, **freshness/CDC/revocation**, privacy boundaries, and
  measured lift. A bigger model supplies none of these.
- The **experience database** (which compositions work, at what cost, on which model,
  with what measured delta) compounds with every run and every user query.

"Won't a better model just do this?" — by design, the better the model, the *tighter*
the registry focuses on what it still can't do. That's the whole strategy.

## Product-market fit

- **Wedge:** compliance / risk / audit teams in regulated, esoteric domains (ESG·CSDDD,
  GxP, customs, sanctions·AML, food/water safety) — where the lift is largest and most
  provable, buyers pay, and they need exactly what we uniquely offer (proof, citations,
  review trails, revocation) rather than "ask the model."
- **Two front doors:** *paste a task → costed, governed flow* (the headline interaction),
  and **Import & Improve** — upload an existing pipeline, get it critiqued, costed, and
  rebuilt with a **measured** before/after. The second is a land motion that proves the
  moat on the buyer's own system.
- **Proof, not pitch:** a live measurement showed a **+1.0 capability lift** when a fresh,
  dated, provenance'd fact replaced the bare model's stale answer. Lift is measured, not
  asserted.

## The acquirable assets (what a lab actually gets)

1. **The measurement dataset** — `bare_vs_pipeline` deltas across thousands of real
   tasks: a scarce, model-improving **eval/training signal** mapping exactly where
   grounded pipelines beat bare models. Uniquely valuable to a lab; licensable on its own.
2. **The governed fresh-fact flywheel** — scrapers + CDC + provenance + signed publishers
   producing dated, verifiable, continuously-refreshed knowledge. Decays the moment a
   user disconnects — which is why it's recurring revenue *and* a durable asset.
3. **The open standard + community** — an open protocol/engine for describing, validating,
   running, and composing components; distribution and ecosystem lock-in at the *format*
   layer (the Hub is the canonical index).
4. **The foundry** — a self-tested, modular engine (19 modules) that generates
   evidence-gated components with human approval and a measured-lift gate; queue/worker +
   K8s-ready (BYO-cloud / air-gap deployable).
5. **The demand graph** — privacy-redacted user interactions → unmet-need signal →
   prioritized build queue: a real, model-independent map of what the market needs next.

## Why each acquirer specifically

| Acquirer | What they get |
|---|---|
| **Anthropic** | a governance-/safety-native registry (human oversight, provenance, review gates) + the measurement dataset; Claude as the builder/judge; the "what models can't do reliably" discipline matches the house ethos. |
| **OpenAI** | the registry + builder + marketplace layer above GPTs/Assistants; the experience DB + demand graph; managed governance for enterprise. |
| **Google** | enterprise governance + regulated-vertical PMF on top of Vertex / Agent Builder; BYO-cloud/air-gap fit. |
| **Meta** | an open standard + community around an open registry/engine — distribution for the open-weights ecosystem. |
| **GitHub / Microsoft** | a governed component registry adjacent to the dev workflow; the "Docker-Hub-for-pipelines" framing, with evals + costed deploys. |

## Metrics that matter (and that we report)

**Useful-promoted/day** (gate-cleared, never "generated"), **measured lift** distribution,
**governance coverage** (% sourced/verified/fresh), **freshness SLA** (CDC latency),
**demand→build conversion**, and **decay watch** (lifts re-benchmarked as models ship).
The honest funnel — `probed → confirmed → sourced → built → novel → measured → promoted` —
is the operating dashboard.

## Honest risks → mitigations

| Risk | Mitigation |
|---|---|
| "A better model erases the value" | the lift gate *is* the hedge — it prunes absorbed components and refocuses on the frontier |
| Cost of measurement at scale | amortize lift per family; mine rich sources deterministically; per-job model budgets |
| Provenance/licensing of ingested sources | source-governance spine: license filter, attribution, review routing, public/synthetic only |
| Over-building before the buyer is validated | wedge-first; Phase-1 infra (~$40–90/mo); hold K8s/billion-tier until the wedge pays |

## The path

Validate the wedge (a few dozen capability-lift blueprints that visibly beat a bare model)
→ land compliance/agency buyers → expand to the agencies serving them → grow the fresh-fact
flywheel + the measurement dataset → the assets that make the acquisition obvious are the
same ones that run the business.

---

*Grounds: `scripts/foundry/` (the engine + the measurement that produces asset #1),
`docs/strategy/{product-market-monetization-brief,open-core-model,monetization-mechanisms}.md`,
`docs/architecture/{evidence-driven-component-factory,cloud-architecture}.md`,
`docs/codex/master-goal.md`.*
