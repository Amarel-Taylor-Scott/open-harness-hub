<!--
HOW TO USE THIS FILE
====================
This is a FILL-IN TEMPLATE. Copy it to `<your-project>/_repos/_shared/OVERARCHING-GOAL.md`
and replace every <PLACEHOLDER> with your project's truth. Delete guidance comments
(the <!-- ... --> blocks) once each section is filled.

Purpose: the single mission a component owner reads FIRST. One consolidated north
star that summarizes and LINKS the detailed source docs — it does not replace them.

Two rules this file must obey (they are what make it trustworthy):
  1. NO HAND-TYPED NUMBERS. If a count/total/date would appear, cite the doc or
     manifest that COMPUTES it instead. A number typed here is a number that drifts.
  2. EVERY CLAIM CITES ITS SOURCE (an existing doc path or machine file). This file
     consolidates; it is never a new authority. Name the doc that wins on conflict.

Reference implementation (a filled-in version of this template):
  `_repos/_shared/OVERARCHING-GOAL.md` in the AI Done Right monorepo, which
  consolidates `docs/BIBLE.md`, `CLAUDE.md`, and `architecture/substrate_layers.json`.
-->

# The Overarching Goal — the single mission a component owner reads first

> This is the consolidated north star for <PROJECT_NAME>. It summarizes and links
> to the detailed source docs; it does not replace them. No count is hand-typed —
> where a number would appear, this doc cites the doc or manifest that computes it.
>
> **Canonical sources this doc consolidates (read them for depth):**
> <LIST THE 3–6 CANONICAL DOCS + MACHINE FILES, e.g. `<path/to/north-star.md>`,
> `<path/to/CLAUDE.md or AGENTS.md>`, `<path/to/architecture/<law>.json>`.>
> If this doc ever disagrees with <THE-ONE-DOC-THAT-WINS>, that source wins.

---

## 1. What we are building

<!-- One paragraph: the SINGLE thing being built, stated as a system/capability,
     not a list of features. Name the top-level components/roles and the ONE law
     that binds them. Cite each claim. -->

We are building <ONE-SENTENCE-MISSION> (source: `<path>`). <N> <roles/components>
operate over one <substrate/product>:

- **<Component A>** — <one-line role> (source: `<path>`).
- **<Component B>** — <one-line role> (source: `<path>`).
- **<Component C>** — <one-line role> (source: `<path>`).

<!-- If your project has a dependency/ordering law between components, state it here
     and NAME the check that enforces it. Consumption/dependency direction is the
     load-bearing fact. -->

They are bound by one rule: **<DEPENDENCY-OR-ORDERING-LAW>**, enforced by
`<path/to/check_script>` over `<path/to/machine-source>` (source: `<path>`).

Concretely, the thing being built is <THE-CONCRETE-ARTIFACT> (source: `<path>`).
Product vocabulary is fixed: <LIST-CANONICAL-TERMS>; <ONE-VOCABULARY-RULE, e.g.
"version lives in metadata, never in a name or id"> (source: `<path>`).

## 2. The core substrate / model

<!-- If the project reduces everything to a small fixed model (a set of primitives,
     a schema, a small type system), state it here with its single source. If not,
     describe the core data/object the whole project is organized around. -->

The substrate everything reduces to is <THE-MODEL> (single source:
`<path/to/base>`, contract `<signature>`). <ENUMERATE the fixed set if there is one:>

1. **<Element 1>** — <role>.
2. **<Element 2>** — <role>.
   <!-- … -->

<STATE the closure rule if there is one, e.g. "there is no eighth X; an unmet need
becomes a <capability-request/typed-empty-slot>, never a real component until proven"
(source: `<path>`).>

## 3. The filters that govern what we build

<!-- The decision gate: how the project decides what to build vs not build, and what
     is admitted vs rejected. State each filter as a QUESTION with a yes/no
     consequence, and cite the machine source. Keep it to the load-bearing few. -->

Single source: `<path/to/filters-machine-source>`.

1. **<Filter 1 name>** — *<the question it asks>?* If no, <consequence>. (`<path>`.)
2. **<Filter 2 name>** — *<the question>?* <consequence>. (`<path>`.)
3. **<Admission filter>** — a new <thing> is admitted only if <the bar>. (`<path>`.)
4. **<Binding constraint — the filter that OUTRANKS the others on conflict>** —
   <the one non-negotiable> (`<path>`).

**Before building any "new" layer, check it does not already exist.** Run
`<path/to/reuse-or-inventory-check>` first. *"This already exists, do not rebuild
it"* is the highest-ROI decision (source: `<path>`).

## 4. The binding constraint, made concrete

<!-- Expand the ONE filter that wins when filters conflict (usually a
     depth/focus/revenue constraint). Say what "depth before breadth" (or your
     project's equivalent) forbids, and list the corollary principles that make the
     focused bet defensible. Mark PROVEN vs THESIS where you make an empirical claim. -->

**<THE-BINDING-CONSTRAINT>** outranks the others when they conflict (source: `<path>`).
The corollary principles that make it defensible:

- **<Principle 1>** — <one line> (`<path>`).
- **<Principle 2>** — <one line> (`<path>`).

## 5. Non-negotiable rails a component owner works under

<!-- The short list of laws every owner obeys. Each is ONE line + the doc/check that
     enforces it. This mirrors STANDARDS.md; keep it a pointer-list, not a restatement. -->

- **<Rail 1, e.g. Warrant before change>** — <one line> (`<path>`).
- **<Rail 2, e.g. Distillation is never replacement>** — <one line> (`<path>`).
- **<Rail 3, e.g. Archived, never deleted>** — <one line> (`<path>`).
- **<Rail 4, e.g. No magic values>** — <one line> (`<path>`).
- **<Rail 5, e.g. Deterministic naming>** — <one line> (`<path>`).
- **<Rail 6, e.g. Safety and scope>** — <one line> (`<path>`).

## 6. Where to go next

<!-- The reading list: the 4–6 canonical docs an owner opens after this one, each
     with a one-line "what it gives you". Point at the doc that WINS on conflict first. -->

- The full vision + binding laws: **`<path>`** (wins on conflict).
- The operating layer (fast path, factory targets, audit protocol): **`<path>`**.
- The filters + layer-by-layer map of proposed-vs-existing: **`<path>`**.
- The strategy north stars: **`<path>`**.
- The core model / taxonomy: **`<path>`**.
