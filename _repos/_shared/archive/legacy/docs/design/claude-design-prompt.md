# Claude Design Prompt — Open Harness Hub UI (explore multiple directions)

> **How to use.** Paste this whole file into Claude with design/artifact generation.
> Optionally attach the companion **`product-ui-and-design-system.md`** (full page
> inventory + exhaustive tokens + the seven-primitive legend). This prompt asks
> Claude to **propose and compare several visual directions** against a best-practice
> rubric — not to settle on one prematurely. Tune the knobs in §5 (how many options,
> which directions, your own references) before running.

---

## 1. The brief, in six lines

- **Product:** Open Harness Hub — a database-backed **registry of reusable AI-pipeline components** + a **conversational builder**. Admission rule: a component earns a place only if it **measurably lifts capability over a bare LLM** and the lift is *structural*.
- **The one sacred interaction:** *paste a task → get a working, **costed**, deployable flow built from existing components.* The landing page is essentially this single entry box.
- **Primary buyer:** compliance / risk / audit teams in regulated, esoteric domains (ESG·CSDDD, GxP, customs, sanctions·AML, food/water safety). Secondary: AI consultants/agencies, SaaS teams adding AI.
- **Must always be legible on screen:** ① **lift** (why it beats a bare model), ② **governance** (provenance, license, verified, review, freshness), ③ **cost & portability** (what it costs, on which model, deployable in your own env).
- **Aesthetic target:** *instrument-grade trust* — closer to a lab instrument / financial terminal / premium dev console than a consumer app. It should survive a screenshot placed next to Anthropic, Linear, Vercel, Stripe, and Perplexity.
- **What we're moving away from:** the currently-shipped GitHub-dark + loud-orange look (`scripts/showcase/pages.py`). It reads "generic dev tool" and undersells the governance moat. Treat it as the *baseline to beat*, not a constraint.

---

## 2. Design best practices — the rubric (satisfy these in EVERY direction)

Distilled from the AI/dev tools that set the bar (and got acquired/iconic on the strength of their craft). Each direction you propose is **scored against this list** in §6.

1. **One sacred interaction.** Identify the single most important move (here: the entry box → costed flow) and make it the brightest, simplest thing on the page. Everything else recedes. *(Perplexity's box, Vercel's deploy, Linear's command bar.)*
2. **Restraint + one memorable accent.** Pick **one** accent and spend it deliberately — ideally reserved for the primary action and brand mark. Color carries *meaning* (type, state, execution class), never mood. *(Vercel near-monochrome; Stripe's single blue.)*
3. **Typographic confidence.** Use a real type system, not Inter-everywhere: a **display face with personality** (a serif reads "credible/editorial"; a sharp grotesk reads "frontier"), a **workhorse UI grotesk**, and a **mono** for IDs/data/code. Build a true modular scale; tighten tracking on large sizes; give body text generous line-height. *(Anthropic's serif; Vercel's Geist; Stripe's editorial type.)*
4. **Trust-coding matches the buyer.** Warm/editorial/light tends to read "considered, governed, human-in-the-loop" (fits compliance buyers); pure monochrome reads "frontier infrastructure"; refined dark reads "power-user craft." Choose the coding **on purpose**, not by default. *(Anthropic/Stripe vs OpenAI/Vercel vs Linear.)*
5. **A real spatial system.** Strict 4/8px grid, a consistent radius set, **hairline borders over heavy shadows** (flat & precise > drop-shadowed), minimal elevation tiers. Generous whitespace on marketing; dense-but-legible on data screens (catalog, trace, cost matrix).
6. **Motion with meaning.** Short (≤320ms), eased, purposeful — e.g. the flow "assembles" stage-by-stage to dramatize *built from components*. No decorative animation. Honor `prefers-reduced-motion`.
7. **Every state is designed.** Empty, loading (skeleton), partial, **blocked-by-gate**, error, success — all first-class. And **honest states**: never fake precision (costs are qualified bands until live pricing; a placeholder embedding shows a "staging/preview" chip, never "semantic").
8. **Accessibility as a constraint.** WCAG 2.1 AA contrast in *both* themes; **never rely on color alone** (type = color + glyph + label); full keyboard traversal; visible focus rings; a linear text alternative for the DAG.
9. **Theme parity.** If light and dark both exist, the system — especially the seven-primitive legend — must read **identically** in both. Don't bolt dark on; design the tokens for both from the start.
10. **Tokens + components are the single source.** Define color/type/space/radius/elevation as tokens; design each atom once (card, badge, button, input, node) and reuse everywhere. *(This mirrors the repo's "no magic values" rule — consistency is a feature.)*
11. **Show the substance.** The UI's job is to make truth legible, not to impress: surface the **lift delta**, the **provenance trail**, the **cost** — prominently, on every component and flow.
12. **Power-tool craft cues.** Instant feedback, optimistic UI, copy-to-clipboard on every ID, a **⌘K command palette**, keyboard-first navigation. These micro-details are what made Linear/Raycast/Vercel *feel* premium.
13. **The distinctiveness test.** For each direction, ask: *"Would this survive a screenshot next to Anthropic / Linear / Vercel / Perplexity — or does it look like generic Bootstrap / generic dev-dark?"* Reject the generic.

---

## 3. Non-negotiable product constraints (true across all directions)

- **Vocabulary:** use **Knowledge Corpus · Conditional · Action · Loop/Flow · Output · Component · Capability-request**. Never surface storage names (`manifest`, `artifact`, `rule-pack`, `knowledge-pack`) in UI copy. Version is metadata — never in a name/ID.
- **The seven-primitive legend must exist** (it's the spine of the catalog, the builder canvas, and the run trace). Re-tune its palette to each direction, but always: **7 distinct, color-blind-distinguishable hues, each with a glyph + label**, mapping to **Input · Knowledge Corpus · Conditional · Action · Loop/Flow · Stop·End · Output**, plus a distinct **Logical Operator** (OR/AND) node. Shipped baseline to evolve: Input gray `#8b949e` · Knowledge green `#3fb950` · Conditional amber `#d29922` · Action orange `#fb7714` · Loop purple `#a371f7` · Stop red `#f85149` · Output blue `#58a6ff` · Operator gold `#e3b341` (diamond).
- **Three signals on every component/flow surface:** lift · governance · cost (per §2.11).
- **Dynamic counts:** any catalog/result count is rendered from data — never hard-code a number into a mockup.
- **One accent** per direction (per §2.2). If the accent equals the Action hue, that coupling is fine and intentional.

---

## 4. Candidate directions to explore (starting points — improve or hybridize them)

These are seeds, not a menu to pick from blindly. Explore the ones selected in §5; you may also propose a defensible hybrid or a fifth direction **if** it beats these on the §2 rubric.

**A · Warm Editorial "Paper"** — *Anthropic · Notion · Stripe · Mintlify*
```
bg #FAF7F0  panel #FFFFFF  line #E7E0D2  ink #1C1B19  muted #6B675E
ACCENT #B8501F (refined clay — evolves the orange)   verify #0E7C86 (teal)
type: Newsreader/Tiempos serif + Inter UI + mono IDs   dark: warm charcoal #1B1A17
feels: considered, governed, human-in-the-loop. Strong trust-coding for the wedge.
```

**B · Clinical Monochrome** — *Vercel · OpenAI · Cursor · Resend*
```
bg #FFFFFF / #0A0A0A   ink #0A0A0A / #FAFAFA   gray #737373   line #EAEAEA / #1F1F1F
ACCENT #2563EB used ONLY on the primary action; otherwise pure B/W
type: Geist/Inter grotesk + heavy mono   feels: frontier, infrastructural, austere
risk: can blend into the AI-infra crowd — lean on type + the box to differentiate.
```

**C · Refined Product Dark** — *Linear · Raycast* (NOT GitHub-dark)
```
bg #0B0B0F  panel #16161D  line #26262E  ink #EDEDF2  muted #8A8A99
ACCENT #6E56CF -> #8B7CF6 (indigo/violet micro-gradient)   verify #2DD4BF
type: Inter/Geist crisp + mono   feels: craft, speed, power-user console.
```

**D · Answer-Engine Light + Teal** — *Perplexity · Glean · Neeva*
```
bg #FFFFFF  panel #FCFCFD  line #E6E8EB  ink #0F1419  muted #5B6470
ACCENT #0E7C86 (deep teal/peacock — doubles as the 'verified/governance' color)
type: clean grotesk + mono (slight rounding)   feels: answers + proof, search-grade.
Fits the paste-a-task move best; the entry box is the absolute hero.
```

---

## 5. The task — knobs + what to produce

**Knobs (edit these before running):**
- **Number of directions:** explore **3** (default) — suggested A, B, D — or change the set / count.
- **Theme:** for each direction, deliver the tokens for its natural primary theme **plus** its companion theme (light↔dark parity, §2.9). *(Open question we're deliberately leaving to you: is the builder/app better dark even when marketing is light? Make a recommendation.)*
- **Fidelity:** start with **HTML/CSS artifacts** (real, viewable) for the comparison screens; promise the full page set only after a direction is chosen.

**For EACH direction, produce a cohesive package:**
1. **Token set** — color (both themes), type (display + UI + mono with the scale), space/radius/elevation, motion. As CSS custom properties.
2. **The re-tuned seven-primitive legend** (per §3) shown as a legend bar.
3. **Four canonical, comparable artifacts** (same four for every direction, so they can be judged side-by-side):
   - **① Landing — the entry box** (the sacred interaction; bare, hero-scale input + a few example chips + quiet secondary links).
   - **② Builder results** — three costed options side-by-side (cheap / balanced / quality-first), each a mini-DAG + component count + est. cost band + lift badge.
   - **③ Component card + badge system** — one card showing primitive hue, type, **lift** badge, **provenance/verified** badge, **execution-class** dot, lifecycle, cost band, license.
   - **④ A DAG node + a Logical-Operator node** in context, with the legend.

Keep ①–④ identical in content across directions; only the design language changes — that's what makes the comparison fair.

---

## 6. Self-evaluate, then recommend

After generating the directions:
1. **Score each** against the §2 rubric (1–5 per principle) in a comparison table, with a one-line justification per row. Include the §2.13 distinctiveness test explicitly.
2. **Recommend one** direction for the product, given the buyer (compliance/regulated) and the sacred interaction (paste-a-task). Say *why* in 3–4 sentences.
3. **Graft the best of the runners-up** — name 2–3 specific elements from the non-winning directions worth importing into the winner.
4. **Flag risks** in the recommended direction and how to mitigate (e.g. "monochrome risks blandness → mitigate with type scale + the assembly motion").

---

## 7. Output format

For each direction, in order:
- `### Direction <X> — <name>` + one-line "feels like / who it's for."
- A fenced **CSS token block** (`:root` + `[data-theme]`).
- The **four artifacts** (①–④) as self-contained HTML/CSS you can render.
Then a final **`## Comparison & recommendation`** section with the scored table, the pick, the grafts, and the risks.

---

## 8. Pointers

- **Full page inventory & exhaustive tokens / legend / component anatomy:** companion file `docs/design/product-ui-and-design-system.md` (40 pages, the seven-primitive system, badges, states, accessibility, data-viz). Use it for the *content* of screens; this prompt governs the *visual direction exploration*.
- **Legacy baseline being replaced:** `scripts/showcase/pages.py` (GitHub-dark + `#fb7714` orange + the shipped legend). Beat it.
- **Source of product truth:** `docs/concepts/component-taxonomy-and-stages.md` (primitives, stages, execution classes), `docs/codex/master-goal.md` (the lift gate, headline interaction), `docs/strategy/product-market-monetization-brief.md` (buyer, wedge, moat, tiers).
