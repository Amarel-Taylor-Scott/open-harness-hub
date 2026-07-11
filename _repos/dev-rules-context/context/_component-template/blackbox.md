<!--
HOW TO USE THIS FILE
====================
This is the per-component BLACKBOX template. To add a component:
  1. Copy the whole `_component-template/` directory to `context/<your-component>/`.
  2. Fill in this `blackbox.md` (what the component IS / OWNS / DOES) and its sibling
     `edges.md` (how it CONNECTS to the others).
  3. Delete guidance comments (the <!-- ... --> blocks) as you fill each section.

WHAT "BLACKBOX" MEANS HERE: the standalone briefing for a session managing ONLY this
component. It says what this component internally owns, is, and does — its contract,
surfaces, subsystems, and current state — WITHOUT the implementation detail. It is the
disclosure a reader (human or agent) reads BEFORE opening any source. It mirrors the
"blackbox" contract of a single primitive: does-what, in→out, key side effect. The
companion `edges.md` covers how this component connects to the others.

TWO RULES (they are what make this file trustworthy):
  1. GROUNDING — every claim summarizes and LINKS an existing repo doc or machine
     source (cited inline). This file is a consolidation, not a new authority: if it
     and a cited source disagree, the source wins.
  2. NO INVENTED NUMBERS — where a count/total appears, QUOTE it with the generator or
     doc it comes from, and tell the reader to re-run the generator for the current
     figure rather than trusting the sentence.

Reference implementation (a filled-in version): `_repos/baltor/context/blackbox.md` in the
AI Done Right monorepo.
-->

# <Component> — blackbox view (what this component is, owns, and does)

**Purpose of this file.** The standalone briefing for a session managing *only*
<Component>. It says what <Component> internally owns, is, and does; its key surfaces
and subsystems; its current state; and where the detailed docs live. The companion
`edges.md` covers how <Component> connects to the other components and the `_shared`
layer.

**Grounding.** Every claim below summarizes and links to an existing repo doc or
machine source (cited inline). This file is a consolidation, not a new authority — if
it and a cited source disagree, the source wins. No numbers are invented; where a
count appears it is quoted with the generator/doc it comes from.

Primary sources synthesized here:

- `<path>` — <what it gives you: role / product definition>.
- `<path>` — <current state report + its generator>.
- `<path/to/machine-source>` → `<the field>` — the machine role definition.

---

## What <Component> is

<!-- 2–4 sentences: the one-line identity, its own buyer/user if it is a standalone
     product, and what it complements rather than replaces. Cite each claim. -->

<Component> is <THE-ONE-LINE-IDENTITY> (source: `<path>`). It <what it does for its
user>, and **complements rather than replaces** <the systems it sits alongside>
(source: `<path>`).

<THE-DURABLE-ADVANTAGE-SENTENCE — what makes this component defensible, and what is
NOT the moat.> Source: `<path>`.

Package root: **`<path>`**. <Web surface: **`<path>`** if any — say how it is served.>

## What <Component> owns (and what it explicitly does NOT)

<!-- The ownership boundary is the load-bearing part of a blackbox — it is what makes
     separate management safe. List what it owns; then list what it does NOT own and
     say WHERE those responsibilities live (this feeds edges.md). -->

**Owns:** <list the responsibilities this component internally owns>.

**Does NOT own** (these live in <other component(s)> — see `edges.md`): <list>.
Source: `<path>`; `../_shared/ARCHITECTURE-MAP.md`.

## The core invariant / contract (the spine)

<!-- If the component has ONE correctness invariant or end-to-end motion it must
     always satisfy, state it here — ideally as a pipeline/step diagram — and name the
     proof(s) that hold it. A blackbox that names its invariant + proof is far more
     useful than one that only lists features. -->

<Component>'s correctness invariant runs <the end-to-end motion> and is proven, not
asserted:

```
<STEP 1> → <STEP 2> → <STEP 3> → <served output>
```

The **reference result** is <THE-CONCRETE-EXPECTED-ANSWER>, proven by `<check>` /
`<check>`. Source: `<path>`.

## Key subsystems (grounded, with proofs where they exist)

<!-- The load-bearing internal parts a session touches. For each: one line + the
     module path + the proof if one exists. Group them if the component is large. -->

- **<Subsystem>** — <one line> (`<path>`; proof `<check>`).
- **<Subsystem>** — <one line> (`<path>`).
- **<The governance/safety machinery, if any>** — <one line + why it matters>
  (`<path>`).
  Source for all of the above: `<path>` (matching section rows).

## Surfaces (what a session touches)

<!-- The concrete surfaces: the built-out app, the backend/admin routes, the
     projection/dashboard endpoints. Say what is projection-only vs truth-serving. -->

- **`<web path>`** — <the built-out app + what it shows>. <How it is served.>
- **<Admin / backend routes>** — `<path>`, served by `<the service>`.
- **<Live projection surfaces>** — <list>, each over its `/api/*` projection
  (projection-only — no truth/secret leakage). Source: `<path>`.

## Current state (as of the generated report — do not hand-edit these numbers)

<!-- Point at the DETERMINISTIC state report and its generator. Quote figures WITH
     their source and tell the reader to re-run the generator. Flag honestly what is
     candidate/pending vs complete. Include the verify commands. -->

The state report is **deterministic**, generated by `<generator>` from `<inputs>`. As
of that doc: <quote the figures with their generator>. Non-reference surfaces are
honestly flagged candidate/pending. Re-run the report for current figures rather than
trusting this sentence. Source: `<path>`.

Verify commands: `<cmd>`, `<cmd --self-test>`.

## Detailed docs

<!-- The reading list for a deep session on this component, grouped by topic. -->

- Product: `<path>`, `<path>`.
- State + opportunities + risks: `<path>`.
- Governance / trust: `<path>`.
- Role + dependency law: `<path>`, `<path/to/law.json>`.
