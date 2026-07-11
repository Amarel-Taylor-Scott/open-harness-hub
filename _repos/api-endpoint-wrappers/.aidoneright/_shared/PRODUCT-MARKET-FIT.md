<!--
HOW TO USE THIS FILE
====================
This is a FILL-IN TEMPLATE. Copy it to `<your-project>/_repos/_shared/PRODUCT-MARKET-FIT.md`
and replace every <PLACEHOLDER>. Delete guidance comments once each section is filled.

Purpose: a SINGLE lossless consolidation of the product-market-fit thesis — the
wedge, the moat stack, the market, the admission bar, the target segment, and
monetization. It invents no facts and fabricates no numbers.

THE ONE DISCIPLINE THAT MAKES THIS FILE HONEST:
  Mark every empirical claim as **PROVEN** (a dated artifact or implemented code
  exists — cite it) or **THESIS** (a stated hypothesis not yet demonstrated). A PMF
  doc that reads as all-PROVEN is selling, not reporting. Keep a "proven vs thesis"
  ledger table at the end.

  Every claim cites its source path. When two strategy docs disagree, name the ONE
  reconciling doc that governs and say what it supersedes.

Reference implementation (a filled-in version): `_repos/_shared/PRODUCT-MARKET-FIT.md`
in the AI Done Right monorepo, reconciled by
`docs/strategy/portfolio-pmf-solidification-2026-07-01.md`.
-->

# Product–Market Fit — consolidated thesis

> **What this file is.** A single lossless consolidation of the PMF thesis for
> <PROJECT_NAME>. It summarizes and links the detailed strategy documents; it
> invents no facts. The reconciling source when documents disagree is `<path>`,
> which names every claim it supersedes. Each section marks **PROVEN** (a dated
> artifact/code exists) vs **THESIS** (a hypothesis not yet demonstrated).

---

## 1. The wedge — <ONE LINE: the sharp first thing you sell, to whom, first>

<!-- The single entry point into the market. What is the ONE product/message that
     goes first, to which buyer, with which secondary lens deliberately held back?
     Resolve any contradiction where different docs led with different products. -->

**<THE-CENTER-OF-GRAVITY>** (source: `<path>`). The lead message is
<THE-ONE-SENTENCE-PITCH>; <SECONDARY-LENS> is secondary, never the lead. First
buyer: <NAMED-FIRST-BUYER-ROLE> (source: `<path>`).

- **PROVEN (<what>):** <the dated/implemented fact + the number's source> (source: `<path>`).
- **THESIS (<what>):** <the stated-but-unproven claim> (source: `<path>`).

## 2. The moat stack — <ranked, most-durable first>

<!-- The defensibility, as a RANKED stack (not a flat list). Which layer is the
     external pitch (what you sell), which is the internal selection criterion (what
     you admit), which is the compounding engine. Rank them; say which wins. -->

The reconciled hierarchy, ranked (source: `<path>`):

1. **External moat (what we sell): <e.g. governed data / distribution / data network>** —
   <one line; why it is orthogonal to competitor progress> (source: `<path>`).
2. **Internal bar (what we admit): <the selection criterion>** — <one line; a
   selection criterion, not the pitch> (see §4). (source: `<path>`).
3. **Supporting engine (how it compounds): <the flywheel>** — <one line> (source: `<path>`).

- **PROVEN:** <a moat mechanic that is actually built/demonstrated, with its receipt path> (source: `<path>`).
- **THESIS:** <the compounding-at-scale claim not yet demonstrated> (source: `<path>`).

## 3. Total addressable market — <ONE LINE: the market shape>

<!-- The market read: the shape of demand and why now. Ground public/market claims
     in a source; if it is a read rather than a fact, mark it THESIS. Name the gap
     incumbents leave that you fill. -->

**THESIS (market read).** <THE-MARKET-SHAPE-AND-WHY-NOW> (source: `<path>`). The
incumbents <what they sell> and leave <THE-GAP>; that seam is <YOUR-PROJECT>
(source: `<path>`).

## 4. The admission bar — <the ONE test a component/feature must pass>

<!-- The gate that decides what earns a place in the product. State it as a testable
     condition (ideally with a code single-source for the taxonomy). Distinguish
     durable/structural value from transient value. -->

A <thing> earns a place only if <THE-TESTABLE-CONDITION> AND <THE-DURABILITY-CONDITION>.
Transient <value> is revenue today but depreciating inventory, never a defensibility
claim. The taxonomy has a single source in code: `<path>`; never re-defined in prose.
(source: `<path>`).

- **PROVEN:** <the gate demonstrably culling / a measured delta + its source> (source: `<path>`).
- **THESIS:** <the systematic instrumentation not yet run> (source: `<path>`).

## 5. Target segment — <the named ICP + scope rails>

<!-- WHO pays first and WHY the pain is acute for them. Name the accountable person,
     not a category. State any LOCKED scope rails (domains you will NOT touch) and
     the check that enforces them. If there is a starter vertical, describe the
     concrete first win. Mark pre-revenue honestly. -->

**Where the value is largest and most provable: <SEGMENT>** (source: `<path>`).
**The named ICP:** <THE-ACCOUNTABLE-PERSON> — not <the wrong buyer> (source: `<path>`).

**Scope rail (LOCKED): <WHAT-YOU-WILL-NOT-BUILD>.** Enforced by `<path/to/check>`
(source: `<path>`).

**Starter vertical (depth before breadth):** <THE-ONE-CONCRETE-FIRST-WIN>. Code:
`<path>` (source: `<path>`).

- **PROVEN:** <what is implemented, with the proof command> (source: `<path>`).
- **THESIS:** <pre-revenue / design-partner stage; no traction claimed> (source: `<path>`).

## 6. Monetization — <ONE LINE: the open/free vs paid line>

<!-- The business model, stated as a LINE: what is free (the funnel) vs what is paid
     (the recurring revenue). If open-core, say exactly what an export can freeze
     (free) vs what it structurally cannot (paid). List the billing axes if
     implemented. Mark billing/pricing as THESIS if not live. -->

**The line:** <OPEN-THE-X, COMMERCIALIZE-THE-Y> (source: `<path>`).

**OPEN (free funnel):** <list> (source: `<path>`).
**COMMERCIAL (recurring):** <list — everything an export cannot freeze> (source: `<path>`).

- **PROVEN:** <the classifiers/axes actually implemented + stamped, with paths> (source: `<path>`).
- **THESIS / not built:** <billing live? production domains? pricing validated?> (source: `<path>`).

## 7. Proven vs thesis — the honest ledger

<!-- The single scannable table. One row per load-bearing claim: Status = PROVEN
     (dated) or THESIS, and the source path. This is the section a skeptic reads first. -->

| Claim | Status | Source |
|---|---|---|
| <claim 1> | **PROVEN** (dated <date>) | `<path>` |
| <claim 2> | **PROVEN** | `<path>` |
| <claim 3> | **THESIS** (not yet <run/built>) | `<path>` |
| <claim 4> | **THESIS / open gap** | `<path>` |

## Sources (detailed docs — read these for depth)

<!-- The reading list: every strategy doc this file consolidates, one line each. -->

- `<path>` — <the reconciling PMF synthesis; authoritative on conflicts>.
- `<path>` — <market/TAM read>.
- `<path>` — <north stars / admission bar>.
- `<path>` — <GTM / beachhead / buyer>.
- `<path>` — <monetization / open-core line>.

*Consolidation warrant: add-only file under `context/`, grounded in the docs cited
above; no facts invented, no numbers fabricated (each metric cites its doc); PROVEN
vs THESIS marked throughout; where docs conflicted, `<the-reconciling-doc>` governs.*
