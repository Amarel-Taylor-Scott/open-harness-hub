# GTM / Positioning One-Pager — June 2026

> **Status:** synthesis of the June 2026 external market review + the locked brand
> architecture. Internal/private (see launch-blocker C2 — keep `docs/strategy/` out of
> the public site). Brand names here are **locked** (`brand-architecture.md`); this doc
> changes *messaging and sequencing*, not identity.

## The one-line pitch (lead with the tool, not the category)

**Baltor catches the stale and contradicted facts your AI agent would otherwise cite —
verified against the live regulatory source, with a provenance receipt — for the agent
you already run.**

Do **not** lead external copy with "context layer," "capability valleys," or "structural
lift." Those are internal vocabulary. "Context layer" is analyst-blessed (a16z, Mar 2026)
but is **not yet a buyer's budget line** — sell into RAG / agent-infra / AI-governance
budgets with a concrete job.

## The moat — reframed (the one correction the research forces)

The durable moat is **NOT "models can't do this" (capability valleys).** The RAG-vs-long-context
literature (LaRA, ICML 2025) shows retrieval survives on **cost, freshness, and data access**,
not on permanent capability gaps — every frontier release would erase a "valley" moat.

State the moat as: **proprietary/governed corpus + continuous verification against external
authority + freshness/CDC + measured fidelity-per-tier + portable audit artifact — cheaper and
more current than stuffing it into a long context window.**

Keep the two-axis lift gate (`scripts/eval/reason_codes.py`) as an **internal selection
criterion** — it's good discipline for what to admit. It is not the customer-facing story.

## Brands — one leads each surface (no rebrand; this is messaging hygiene)

- **Baltor.ai** leads every *paid / sales / outbound* surface. The product. The wedge above.
- **Open Harness Hub** is "the open project behind Baltor" — credibility, standard-setting,
  developer adoption, SEO. **Not** a near-term revenue engine (OSS free→paid converts ~0.5–3%,
  often <1%; even Confluent monetized <1% — via enterprise value, not volume).
- **AI Done Right** (founding thesis: Context is Everything) → corporate footer / legal entity only. Don't make a prospect
  parse three identities to understand one product.

## Beachhead & expansion

- **Beachhead:** sanctions / export controls (OFAC, BIS, EU) — rules that change faster than
  anyone re-indexes, where stale is a *legal* event, and the source is public + machine-readable.
  Then **ESG / CSDDD** (assets already live-tested: 12 jurisdictions, regression benchmark).
- **Buyer:** compliance / risk / audit / AI-governance lead. Pain: "our agents cite stale policy,"
  "our docs disagree," "we need an audit trail."
- **Expansion later:** GxP/pharma, AML, customs. **Engineering/code context (repo/API/skills) is a
  *different product* in a more crowded market (Sourcegraph, Glean, Cursor) — treat as a deliberate
  Phase 2, not a drift.** (See `substrate-vs-product-two-theses` in agent memory.)

## Competitive read (updated)

- **Contextual AI is no longer "the competitor."** Google DeepMind acqui-hired 20+ of its
  researchers incl. Douwe Kiela + a non-exclusive license for ~$80–100M (Bloomberg / The
  Information / Reuters, May 19–20 2026); it reportedly had ~$10M ARR. **Lesson:** the closest
  standalone grounded-context play couldn't stay independent → don't bet the moat on being a
  better engine; bet it on governed/fresh data. **Opportunity:** their product attention is
  disrupted — a window to land the verified-corpus wedge.
- **Real long-term gravity:** data-gravity incumbents — **Snowflake Cortex, Databricks Genie**
  (a16z names them as the likely owners of the context layer). Compete by being **agent/model-neutral
  and open**, serving into the agent the customer already runs, where those platforms lock to their own.
- **Distribution template to copy:** Mem0 became the exclusive memory provider for the AWS Agent
  SDK. Win a distribution/integration partner, don't out-build the field.

## GTM motion (open-core → design partners → cloud)

1. **Proof first (the gate to everything else):** one end-to-end thread in sanctions/ESG —
   scrape live source → parse → verify a corpus against it → catch a stale/wrong fact → emit the
   audit receipt → serve via MCP to a real agent. Capture it as a 90-second screen recording.
   "Baltor caught N stale clauses your agent would have cited, with provenance, in 48 hours."
2. **3–5 design partners** in the beachhead, hand-sold against that recording. Land on the
   narrow job; expand to adjacent corpora.
3. **OSS funnel (OHH)** runs in parallel for credibility + developer mindshare + inbound — measured
   on adoption/stars/contributors, **not** on direct conversion.
4. **Distribution partner** (the Mem0→AWS move) once the proof point and 1–2 references exist.

## What to stop / avoid

- Stop benchmarking RAG quality and building a grounded model — that race is lost and now Google's.
- Stop expanding component *count* as a headline metric (and remove count claims from prose — the
  `4,241` drift was the canonical bug). Volume is not the wedge; one proven outcome is.
- Don't build six substrate managers before the proof point. Only **Parser (one)** + **Scraping
  (one)** are on the beachhead critical path; the freshness/scrape thread *is* the "current ≠
  correct" demo.

## The single metric that unblocks fundraising / partners / acqui-hire optionality

**One named design partner with a measured outcome** ("Baltor found 7 stale clauses, saved 12
person-days, here's the receipt"). Worth more than the architecture, the vector search, or the
next 1,000 candidates.
