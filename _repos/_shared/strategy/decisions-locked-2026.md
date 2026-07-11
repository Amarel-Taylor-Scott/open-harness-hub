# Decisions Locked — 2026 (AI Done Right · Baltor · Teleon)

**Status:** honest lock-state tracker. **Date:** 2026-06-25.
**Purpose:** satisfy the YC "decisions locked" criterion by separating what is **actually decided**
(Section A — cite the source, do not re-open) from what is **recommended but still owner-gated**
(Section B — `⟦DECISION⟧`, pending ratification). This doc does **not** override anything; where it
references a decision, the named source is the source of truth. It companions
`docs/strategy/yc-master-current-state-business-plan-and-pitch.md` (the master) and never contradicts it.

> **Honesty preamble.** We are **pre-revenue, design-partner stage**. Nothing here invents traction.
> Repo counts (proofs, catalog, family surfaces) are **computed and dated**, never hardcoded magic
> numbers — each carries its recompute command. Pricing numbers and raise size are **NOT locked** here;
> they are recommendations flagged `⟦DECISION⟧`. Scope rails hold: **avoid insurance**, synthetic/public
> data only, never republish `_reference/`.

---

## A · LOCKED — decided (cite as settled; do not re-open unilaterally)

| # | Decision | What it means (one line) | Locked where |
|---|---|---|---|
| A1 | **Parent brand = AI Done Right** | Display brand "AI Done Right", domain `aidoneright.dev`, tagline **"AI, done right."** (parent = efficiency + appropriate + easy, *not* context). | `architecture/brand.json` (`status: locked-2026-06-08`, owner: "I went with AIDoneRight.dev"); `CLAUDE.md` Portfolio |
| A2 | **The one-liner + pillars (verbatim)** | Hook: **"Models don't fail. Their context does."** Functional: **"Verified, current, and provable context for the agents you already run."** Pillars: **Verified · Current · Efficient · Provable.** | archived `brand-architecture.md` (messaging system, owner-locked); master §0 uses it verbatim |
| A3 | **Three product layers** | **Teleon** (`teleon.dev`) = runtime SaaS engine (efficiency/descent); **Baltor** (`baltor.ai`) = customer-facing governed context, *powered by Teleon* (a tenant); **OpenHubForAI registries** = the open registries/funnel both consume. | `CLAUDE.md` Portfolio; `docs/strategy/teleon-baltor-openhubforai-portfolio.md`; `brand.json` `positioning` |
| A4 | **AIDevObserver = AI-usage coaching** | `aidevobserver.io` watches AI **usage** — post-session review + intra-session coaching (renamed from *Teleon Observer*, 2026-06-25). It reviews the *session*, not code/PR correctness. | `docs/BIBLE.md`; `docs/NORTHSTAR.md`; memory "Observer = session review" |
| A5 | **Architectural dependency law** | **Baltor → Teleon → OpenHubForAI, never the reverse.** Teleon must not import Baltor; OpenHubForAI imports neither. Enforced, not aspirational. | `architecture/portfolio_dependency_law.json`, enforced by `scripts/check_portfolio_dependency_law.py` |
| A6 | **One-site consolidation** | All OpenHubForAI registries live under **ONE site, `OpenHubForAI.io`** (records are the unit; hubs/registries are facets). The OpenHubForAI registries are the open funnel/commons, not the parent identity. | owner 2026-06-25, `docs/BIBLE.md` ("UI/UX CONSOLIDATION"); `brand.json` `scope.open_hubs` |
| A7 | **Economic unit = usage meters, not seats** | Bill on `source monitored → facts verified → context package served → agent risk reduced` (monitored sources, pages, facts under management, verification jobs, served packages, premium feeds, frontier overage). **Never price by seat.** | master §4.1; `_repos/baltor/context/strategy/baltor-cloud-cost-pricing-pro-forma.md` |
| A8 | **Open-core monetization boundary** | **Free** = a *freezable* verified snapshot pulled into an OpenHubForAI harness. **Paid (Baltor)** = the *live, kept-fresh, governed* serving layer against a dynamic corpus. One governed object, two doors. | master §4.3; archived `brand-architecture.md` (monetization boundary) |
| A9 | **Beachhead = regulated context** | Land first where context change = legal/financial risk: sanctions / export-controls / vendor-compliance / regulated procurement / legal ops. Wedge demos: CFPB correctness invariant + OFAC sanctions catch. | master §1.1, §5 (demo), §11 (GTM) |
| A10 | **No-insurance scope rail** | Do not build or expand insurance pipelines. Target the *claims-shape* in adjacent regulated verticals instead. Synthetic/public data only; no real PII/secrets. | `CLAUDE.md` "Safety And Scope"; enforced by `scripts/check_adjacent_verticals.py` |
| A11 | **Assurance-brand discipline** | Claim only what the proofs support. Never "100% accurate" / "perfect" / "guaranteed." Output ≠ truth; candidates ≠ active; discovery ≠ trust; receipts make work inspectable. | `brand.json` `brand_laws`; archived `brand-architecture.md` (Voice); master §7 (risks) |

**Dated proof-state (computed, not hardcoded).** The deterministic proof gate stands at **713 green** as a
dated **2026-06-25** snapshot. Recompute before quoting in any deck:

```bash
PYTHONPATH=. python3 scripts/run_proofs.py            # exit code = number of reds
python3 scripts/check_ai_done_right_surface_family.py --self-test   # family surface count
```

Treat the number as a *snapshot with a recompute command*, exactly as the master doc and `CLAUDE.md`
require — do not transcribe it into prose as a fixed figure that can drift.

---

## B · RECOMMENDED — PENDING OWNER RATIFICATION `⟦DECISION⟧`

These are **not decided.** Each gives the recommended default, the rationale, and exactly what the owner
must confirm. None may be treated as locked until the owner signs off (design/brand/strategy/pricing
decisions are never a unilateral single-agent call).

### B1 · Raise size + use of funds `⟦DECISION⟧`
- **Recommended default:** a **pre-seed round of ~$1.0M–$2.0M** (≈18-month runway to the seed-readiness
  gates), *additive to* the standard YC SAFE — **stated here as a recommendation, not a decision.**
- **Rationale:** pre-revenue, design-partner stage with a *working governed engine* (not vaporware) and a
  locked brand justifies a defensible pre-seed, not a priced seed. The range funds the milestones in master
  §8 without over-raising against zero revenue. Use-of-funds buckets (from master §15, keep verbatim):
  **connectors / source monitoring · worker orchestration · verified public context feeds · local+cloud
  deployment hardening · security / compliance baseline · design-partner success + founder-led GTM.**
- **Owner must confirm:** the exact figure and the per-bucket split, the instrument (SAFE cap/discount),
  and whether to frame it pre-seed vs seed in the deck's "Ask" slide.

### B2 · Final pricing numbers `⟦DECISION⟧`
- **Recommended default:** **keep the master §4.2 tier *structure*** — Design-partner pilot ($5k–$25k fixed)
  · Team ($1.5k–$3k/mo) · Business ($6k–$15k/mo) · Enterprise ($40k+/yr, often $75k–$250k ACV) — as
  **drafts**, and let the owner set the exact numbers against `baltor-cloud-cost-pricing-pro-forma.md`.
- **Rationale:** the four-tier shape (pilot → Team → Business → Enterprise) maps cleanly to the
  consumption-meter model (A7) and the open-core boundary (A8); it is the *ranges*, not the structure, that
  need owner judgement against real COGS and design-partner signal.
- **Owner must confirm:** the exact dollar figures per tier, what each meter costs, and overage/floor
  policy. Until then the deck cites ranges labeled "draft."

### B3 · Public fidelity-tier names `⟦DECISION⟧`
- **Recommended default:** **retire "Gold context" / Bronze-Silver-Gold medallion** as the headline tier
  (owner direction: "gold doesn't mean anything") and name the public fidelity dial with the pillars —
  **Verified · Provable**. "Medallion" may survive only as an industry *reference* to Databricks' model,
  never as our product noun.
- **Rationale:** the locked pillars (A2) already carry the meaning "Gold" was standing in for; aligning the
  fidelity-tier names to *Verified · Provable* removes a borrowed metaphor and keeps one vocabulary. Repo
  code/proofs are already free of "golden"; the cleanup is in the GTM/positioning prose (master §6.1).
- **Owner must confirm:** the final public tier labels (e.g. *Verified* vs *Provable* vs a deterministic-only
  entry tier), and supersede `baltor-gtm-fundraising-plan.md` + `baltor-medallion-context-positioning.md` in
  the **same change** so no stale "Gold context" headline remains.

### B4 · TAM math `⟦DECISION⟧`
- **Recommended default:** present TAM **comparable-anchored and explicitly labeled an estimate** — position
  in the consumption-priced "context layer" the public tape validates (SNOW / MDB / DDOG / NET), wedge
  bottom-up from regulated-context buyers, and expand along the consumption axis. **No invented
  top-down number presented as fact.**
- **Rationale:** a pre-revenue company cannot defend a precise TAM; an honest comparable-anchored estimate is
  credible to YC and consistent with the assurance brand (A11). The story is "open, governed assembler at the
  governance seam" — wrap incumbents (Qdrant/Mem0/LLMLingua/Langfuse), don't out-RAG them.
- **Owner must confirm:** the chosen comparables, the wedge SAM figure (if any), and the estimate disclaimer
  wording on the Market slide.

---

## Open follow-ups (tracked, not decisions to make here)
- Trademark search + registration for "AI Done Right" / BALTOR; register/fence remaining domains
  (`brand.json` `owner_actions_outstanding`). "AI Done Right" is a common phrase — keep the *product* marks
  (Baltor, Teleon, the hubs) as the ownable moat, not the parent phrase.
- Confirm whether **"Context is Everything"** stays as Baltor's origin/founding-thesis line or fully retires
  (`brand.json` `superseded.note`).
- Execute the master §6 consolidation (bounded-agent naming, CEaaS → Baltor code-path rename, competitive-doc
  merge) so deck + docs + code tell one story.

---

*Warrant: built on **clear owner intent** for the YC push (this request) and on the already-locked sources
cited inline — `architecture/brand.json` (parent brand, owner-locked 2026-06-08), the archived
`brand-architecture.md` (one-liner + pillars), `architecture/portfolio_dependency_law.json` (dependency law),
`docs/BIBLE.md` (OpenHubForAI.io consolidation + AIDevObserver, owner 2026-06-25), and the YC master doc.
Section A items each name where they were decided. **Section B — pricing numbers and raise size — remains
owner-gated and is marked `⟦DECISION⟧`; nothing in B is locked by this doc.** Pre-revenue; counts are
computed/dated with recompute commands; no insurance; no `_reference/` republished.*
