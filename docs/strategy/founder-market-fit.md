# Founder–Market Fit — AI Done Right · Baltor.ai (the YC FMF answer)

**Status:** best-effort DRAFT for owner edit (additive). **Date:** 2026-06-25.
**Purpose:** the Y Combinator **founder–market-fit** answer in one place. It expands slide 14 (Team) and
slide 3 (Why now) of `docs/strategy/yc-master-current-state-business-plan-and-pitch.md` — that master doc is
the source of truth and **wins on any conflict**. Every personal / biographical claim is marked
**[OWNER TO FILL]**: the prose around it is a scaffold so you *edit* rather than write from scratch, not a
set of facts I asserted on your behalf.

> **Honesty rail (hard).** This doc invents no biography. The only founder signal taken as given is the master
> doc's slide 14 — *technical founder with a training-free / frozen-model + legal-AI background* — and even
> that is treated as a hint to confirm, not gospel. We are **pre-revenue**. All counts are dated, recomputed
> snapshots (commands inline), never hand-typed magic numbers. Personal specifics are owner-gated; see the
> closing note.

---

## 1 · Why this founder knows this problem better than anyone

The whole company is a bet that **context, not raw model capability, is the durable bottleneck**. The founder
did not arrive at that bet from a slide — it is the lesson two prior careers teach by force.

**The training-free / frozen-model grain.** Whoever builds useful AI on a *frozen* model — no fine-tuning, no
weight access, no training budget — learns the bottleneck viscerally: the only levers left are **what you feed
the model and how you constrain and check what comes back**. You spend your days on retrieval, grounding,
decomposition, verification, and held-out facts, because that is the *only* surface you control. That is
exactly Baltor's product surface. A founder from this grain reaches for **structural, deterministic,
governance-first** methods by reflex — the same instinct that makes the Determinism Factory (expensive
resolution distilled into cheap deterministic rules) feel obvious rather than clever.

- [OWNER TO FILL: the specific work — *which* frozen / training-free systems you built, the years, the
  employer or lab, what shipped, and the scale (users, documents, domains). One concrete sentence beats a
  paragraph of adjectives.]
- [OWNER TO CONFIRM: `docs/strategy/yc-readiness-and-prep-2026.md` (§3) hints at a *few-shot segmentation* /
  PhD research background. If accurate, name the degree, field, and institution; if not, delete this line.]

**The legal-AI grain.** Legal AI is the one domain where an unprovenanced answer is worthless no matter how
fluent it is. The deliverable *is* the citation, the authority hierarchy, the audit trail, the defensibility
under challenge. A founder who built there does not treat provenance, lineage, and receipts as enterprise
garnish — they treat them as the product. That is why Baltor's spine is "every served fact carries source
handles + a portable receipt + lineage," and why "agents PROPOSE, Baltor DISPOSES" reads as common sense
instead of ideology.

- [OWNER TO FILL: the legal-AI chapter — company / role / years, what you shipped, who used it, and the
  hardest provenance or correctness problem you owned. If there is a regulated-domain anecdote (a wrong-but-
  confident answer that had real consequences), it belongs here — it is the emotional core of the pitch.]

**The overlap is the fit.** Most people who *see* the context-governance seam have never shipped the machinery
for it; most people who *can* ship deterministic governance machinery are chasing model capability instead.
This founder sits in the rare intersection: trained by a frozen model to obsess over context, trained by law
to obsess over provenance — and has already built the governed engine that fuses both.

## 2 · The hardest thing you've built

Two answers: the citable one that is true *today*, and the personal one only you can write.

**The citable one (real, reproducible, unusual for pre-seed).** A **governed context engine that runs
end-to-end, fully offline, deterministically** — stdlib-only, no pip, no cloud, no network model — and still
enforces its moat mechanics. The hard part was never a single feature; it was making *correctness a property
the machine proves about itself*:

- A **deterministic proof gate — 713 green** (dated snapshot, 2026-06-25; recompute with
  `PYTHONPATH=. python3 scripts/run_proofs.py`). Every governance invariant is a `--self-test` that fails the
  build on regression — correctness is continuously *demonstrated*, not asserted in prose.
- The **CFPB correctness invariant**, always-on: when authorities disagree, Reg-E's "10 business days" wins by
  authority; the 30-day FAQ and the narrative allegation are **held out**; only the reconciled winner is
  served, with its source and a receipt (`scripts/demo_offline_full_baltor.py --self-test`).
- A **live OFAC sanctions catch**: a dated 2026-06-14 `--live` run against the real OFAC SDN list caught a
  *planted* would-be violation that had been held out of the served corpus
  (`docs/strategy/evidence/ofac-live-run-2026-06-14.json`) — alongside an always-green synthetic conformance
  proof.
- The **Determinism Factory**: expensive LLM/agent resolution is distilled **losslessly** into a cheap
  deterministic rule (measured RuleArena lift **+0.71**, per `docs/strategy/yc-readiness-and-prep-2026.md`
  §4) — the mechanism that turns a services-heavy early margin into reusable infrastructure.

For a pre-seed company the signal is not the feature list — it is the **rigor**: a one-person-scale system
where every governance claim is backed by a test that runs on a laptop with the network off.

- [OWNER TO FILL: the personal hardest-thing — the prior project where you shipped something genuinely hard
  (the frozen-model or legal-AI system above is the natural candidate). What broke, what you owned, what the
  constraint was, and why finishing it was hard. YC weights *shipped-it-against-odds* over *designed-it*.]

## 3 · The earned, unfair insight

> **Context, not capability, is the durable bottleneck — and governance is the seam frontier models will not
> fill.**

The better the model gets, the more its remaining failures are **context** failures: it cites stale policy,
reconciles contradictions silently, and asserts unverified facts *fluently*. Capability rises; trustworthiness
of the underlying data does not come with it. Frontier labs optimize **weights**; nobody owns the
**governed-context seam across models** — provenance, freshness/CDC, authority reconciliation, held-out
unverified facts, and a portable receipt. That seam is a *data + process + liability* problem, structurally
orthogonal to model training, so it does not close when the next model ships. It is the negative space the
capability race leaves behind — and it widens as capability climbs.

This is the insight the founder grain *earns* rather than guesses: a frozen model teaches that the leverage
lives outside the weights; legal AI teaches that an answer without provenance is not an answer. Put together,
they predict the exact moat the master doc names — **Verified · Current · Efficient · Provable** — and they
predict it would be invisible to anyone who believes the model is the product.

## 4 · Why you + why now

**Why now — three forcing functions converging:**

1. **Regulation turns receipts into a legal deadline.** The **EU AI Act** moves toward full enforcement
   (per `docs/strategy/yc-readiness-and-prep-2026.md` §3: **Aug 2, 2026**; Art. 73 incident reconstruction on
   a 72-hour clock). Provenance, lineage, and a portable receipt stop being a nice-to-have and become a
   compliance artifact regulated buyers must produce on a deadline — which is precisely Baltor's native
   output. *[OWNER/COUNSEL TO VERIFY the exact article + date before this goes in an application — it is
   outward-facing and legal; cite the regulation directly, not this doc.]*
2. **The market just repriced the context layer by consumption.** SNOW / MDB / DDOG / NET are all growing on
   the consumption-priced data/agent infrastructure tape (master doc §4.5). The named winners sell plumbing
   and storage; **none sell enterprise governance — glossary, lineage, entity resolution — at the seam.** A
   consumption-shaped, governed context layer fits that tape exactly, and the slot is open.
3. **Frontier models make context the moat.** As capability commoditizes (slide 3), the durable differentiator
   moves *under* the model to the trustworthiness of what it consumes. We do not race the model; we **wrap**
   the infra incumbents (Qdrant / Mem0 / LLMLingua / Langfuse) as governed, measured-lift components under one
   provenance contract.

**Why you:** the forcing functions reward the one founder who both *sees* the governance seam and has *already
built* the deterministic machinery for it. The engine, the proof gate, the Determinism Factory, and the
CFPB/OFAC flagships exist **today** — so "founder–market fit" here is not a story about pedigree, it is a
story about a person whose two prior careers point at this exact seam and who has already shipped the
hardest, least-glamorous 80% of it.

- [OWNER TO FILL: the personal "why me, why now" sentence — what you saw in your prior work that convinced you
  this was the company to build *now*, in your own voice.]

## 5 · Answer block — draft for the YC application prompts

> A tight, paste-ready draft for YC's founder/insight prompts (e.g. *"Please tell us about the time you most
> successfully hacked some (non-computer) system to your advantage,"* and *"Why did you pick this idea? What do
> you understand that others don't?"*). ~150 words; swap the **[OWNER TO FILL]** anchors for specifics in your
> own voice.

**Draft (~150 words):**

> The system I hacked was a *frozen model*. At [OWNER TO FILL: company / lab, years], I had no training budget
> and no access to the weights — so I got [OWNER TO FILL: the result, e.g. "near-frontier accuracy on
> [domain]"] purely by engineering the **context**: retrieval, decomposition, held-out unverified facts, and a
> verification pass that the model wasn't allowed to overrule. Working in **legal AI** taught me the other
> half — an answer without provenance is worthless, however fluent. Those two lessons are the same lesson:
> **capability isn't the bottleneck; trustworthy, governed context is.** Frontier labs optimize the model;
> nobody owns the seam *underneath* it — provenance, freshness, reconciliation, a portable receipt. So I built
> Baltor: a governed context engine that already runs end-to-end, offline, deterministically, with **713 green
> proofs** (`scripts/run_proofs.py`, 2026-06-25). Models don't fail. Their context does.

- [OWNER TO FILL: replace the bracketed anchors with the real company, years, result, and domain — keep it
  matter-of-fact and specific; YC rewards a concrete, verifiable story over adjectives.]

---

*Warrant: written on clear owner intent (this request) as a best-effort scaffold. Positioning is anchored to
the LOCKED brand and to `docs/strategy/yc-master-current-state-business-plan-and-pitch.md` (slides 3 + 14) and
`docs/strategy/yc-readiness-and-prep-2026.md`; this doc adds no strategy decision and contradicts neither.
**All personal specifics (biography, employers, dates, degrees, prior projects, the EU AI Act legal citation)
are owner-gated and marked [OWNER TO FILL] / [OWNER TO CONFIRM] / [VERIFY] — none were invented.***
