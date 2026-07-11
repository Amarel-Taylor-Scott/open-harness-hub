# Brand & messaging system — LOCKED — 2026-05-29

> **PARENT RENAME (2026-06-08, owner-locked) — read first.** The **parent / holding company** is now
> **AIDoneRight** (domain **aidoneright.dev**), parent tagline **"AI is Everything"**. This **supersedes**
> the parent/company name **"Context is Everything" / "ContextIsEverything Group"** used below. Canonical
> single source: `architecture/brand.json` (which preserves the prior name + tagline as the rollback target —
> lossless). **Scope of the rename = the parent identity ONLY.** Baltor and Teleon names are **unchanged**;
> the Open*Hubs are unchanged. The product *thesis* below — "a model is only as good as the context it acts
> on", the Baltor hooks, the Balto narrative — is **Baltor product copy and is retained as-is**; only the
> parent/company-name lines are superseded by AIDoneRight. Whether "Context is Everything" is kept as
> Baltor's product line / origin story is an open owner decision (see brand.json `owner_actions_outstanding`).
> Everything below this banner is preserved as the prior locked state (history / rollback context).

Canonical identity for the company and both products. **Supersedes** the earlier house-of-brands draft
(quiet-parent-holdco + wordmark-TBD + the *X Corpus / X Verify / X Proof / X Build / X Connect* SKU sketch),
which predated the Context-first and Baltor decisions. Competitive positioning lives in
[[positioning-v2.md]]; this doc is **identity + architecture + messaging**.

Status: **structure, names, and messaging LOCKED.** The only open items are trademark/domain clearance (bottom).

> **Naming map (read once):** the paid SaaS that working docs and code still call the **Context Enrichment
> service / CEaaS / "verified-context SaaS"** is now branded **Baltor.ai**. Those docs
> ([[two-services-shared-infrastructure.md]], [[context-enrichment-service.md]]) and the code paths
> (`services/products/context_enrichment/`, `scripts/enrichment/`, the `oh_ce` CLI, `web/context-enrichment/`)
> describe the same product — Baltor is its brand. A code/path rename is a tracked follow-up, not part of this
> brand lock.
>
> **Disambiguation:** Baltor's **Corpus** module (verified-context subscriptions) is a *product surface* and is
> distinct from the seven-primitive **Knowledge Corpus** component type (see
> `docs/concepts/component-taxonomy-and-stages.md`). Same word, two layers — don't conflate.

---

## Thesis
**Context is Everything.** A model is only as good as the context it acts on. The best model still fails on
stale, unverified, contradictory, or bloated context. The company exists to make the context AI agents use
trustworthy.

---

## Brand architecture

```
Context is Everything            ── company / mission · tagline: "Context is Everything"
│
├── Baltor.ai                    ── paid SaaS · "context assurance for AI agents"
│     hero: "Trust your context like Nome trusted Balto."
│     ├─ Verify      assure YOUR context — correctness · currency · anomalies/contradictions (HITL)
│     ├─ Corpus      verified context WE provide, by domain   (beachhead: sanctions / export controls)
│     └─ Compress    fewer tokens · measured fidelity
│        proof built into all three (provenance + metrics) — NOT a separate SKU
│        I/O:  Connect (your context in) · Deliver (verified context out, incl. push to other RAG/data platforms)
│        processing (parse / chunk / embed): backstage defaults; lineage surfaced as proof
│        measurement spine: lift · fidelity delta · anomaly scoring · drift monitoring (this emits the proof)
│
└── Open Harness Hub             ── open funnel (free) · build governed harnesses, consume Baltor
      Harness Builder · Catalog/Registry · Runtime · Consumption surface · Measured-lift gate
      (a component must beat the bare model to enter the catalog)
```

**The two products, one line each:**
- **Baltor.ai** — make the context trustworthy (verify · supply · compress · prove). The moat, paid.
- **Open Harness Hub** — build the governed workflow that uses it. The funnel, free/open.
- **The join:** a verified corpus, governed once, is consumed two ways — wired into an OHH harness, or served
  (via Deliver) straight into any agent (Claude Code, Codex) or platform.

---

## How context moves (two sources · processing · two exits)

```
SOURCE                              PROCESSING                         EXIT
your context  ──Connect──►   parse/chunk/embed (backstage)   ──►   Deliver → your agent
our context   ──Subscribe─►        │                                 (Claude Code, Codex,
(Corpus)                            ├─ Verify  (correct? current? HITL)    any RAG / data platform)
                                    └─ Compress (fewer tokens, fidelity)
                                       proof on everything
```

- Nobody "builds" a corpus: customers **Connect** theirs or **Subscribe** to ours. A domain we don't carry is
  **requested** → we build + verify it → it enters the Corpus catalog. ("Build a corpus" = our supply engine;
  "build a harness" = Open Harness Hub — different objects.)
- **Monetization boundary:** a **freezable** verified snapshot pulled into an OHH harness is free; **live,
  kept-fresh** serving against a dynamic corpus is Baltor (paid). See [[open-core-line-and-learn-from-contextual.md]].

---

## The Balto narrative
Balto led the 1925 serum run — the sled dog who ran lead on the final leg, found the trail through a whiteout,
and got the critical antitoxin to Nome when it mattered most. **Baltor leads agents to context they can trust,
across messy terrain.** Two brand threads, both from the story:
- **Leading the way** → what Baltor *does* (goes first, finds the trail to good context).
- **Trust** → why it *matters* ("like Nome trusted Balto").

**IP note:** the brand draws on the **1925 historical event** (public domain, free to use). Keep visual
branding (logo, art) clear of Universal's 1995 *Balto* film — the inspiration is the history, not the movie.
The protectable mark is **BALTOR** ("." + "ai" is styling, not part of the mark).

---

## Messaging system
Four layers, each with a role. **Default: hook-first** — the thesis grabs cold traffic; the Balto line is the
soul beneath it and leads in brand moments.

```
THESIS HOOK (lead):     Models don't fail. Their context does.
FUNCTIONAL (subhead):   Verified, current, and provable context for the agents you already run.
BRAND / SOUL:           Trust your context like Nome trusted Balto.
PILLARS (everywhere):   Verified · Current · Efficient · Provable
```

**Backup hero lines (same registers, interchangeable):**
- Thesis: "Your agent is only as good as its context." / "The model isn't the bottleneck. The context is."
- Trust + proof hybrid: "Context you can trust. Proof you can show."

### Three audience doors (same product, framed per reader)
| Audience | Line |
|---|---|
| **Developers** | Plug verified, token-lean context into Claude Code, Codex, or any agent. No stale RAG, no re-platforming. |
| **Enterprise / regulated** | Prove your AI acts on current, correct, source-linked context — with an audit trail that holds up. |
| **Investors / partners** | AI is only as good as its context. Baltor is the assurance layer for the agent era. |

### Lexicon
- **Own and repeat:** context · trust / trusted · verified · current / fresh · provable / proof · source of
  truth · lead / leading · assurance
- **Never say:** "perfect" / "100% accurate" (overclaim + legal exposure) · "AI-powered" (generic) ·
  "revolutionary / magic" · "compression" as a headline → say **lean** / **efficient context** instead

### Voice (3 rules)
1. Confident, concrete, no fluff — developers smell marketing.
2. Claim only what you can prove. It's an *assurance* brand; overclaiming is fatal. Not "guaranteed accurate"
   → "verified, and here's the proof."
3. Story-aware, not story-dependent — the Balto myth gives warmth; every page still states the concrete
   benefit beside it.

---

## Names & domains
| Asset | Status |
|---|---|
| Company / mission | **Context is Everything** |
| Paid SaaS | **Baltor.ai** — wordmark "Baltor.ai"; in running prose write "Baltor" |
| Open product | **Open Harness Hub** |
| Modules (in-product, bare) | Verify · Corpus · Compress |
| SEO landing pages (→ funnel into Baltor) | ContextVerify · ContextCompress · ContextGov |
| Category owned via content/SEO | "context assurance" · "verified context" |
| baltor.ai | owned ✓ |
| openharnesshub.com | owned ✓ |
| contextfidelity.ai | secured ✓ → point at the ContextVerify landing page, redirect into Baltor |
| contextgov.com | to grab (compliance / audit landing) |
| baltor.com / getbaltor.com / baltor.dev | fence (defensive, redirect to baltor.ai) |

---

## Open items (the only things not yet final)
1. Clear **BALTOR** as a trademark in the software class (USPTO / EUIPO).
2. Grab **contextgov.com**; fence **baltor.com** (+ getbaltor.com / baltor.dev) and redirect to baltor.ai.
3. Tagline backups remain refinable; hero-line order (**hook-first**) is the default unless flipped to soul-first.

---
*warrant: locked with the owner across this session (2026-05-29). Decisions — "Context is Everything" as
parent; "Baltor.ai" as the paid SaaS (from Balto: leading the way / the 1925 serum run); "Open Harness Hub"
kept as the open funnel; modules Verify / Corpus / Compress with proof built in (no standalone Proof SKU);
Connect / Deliver as I/O; two sources (Connect yours · Subscribe to Corpus); hook-first messaging led by
"Models don't fail. Their context does." with "Trust your context like Nome trusted Balto." as the soul line.
Names, structure, and messaging locked by the owner; trademark + domain clearance are the only open items.
Supersedes the earlier house-of-brands draft (wordmark-TBD + the X-SKU sketch).*
