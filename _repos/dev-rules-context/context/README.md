<!--
HOW TO USE THIS FILE
====================
This README explains the per-component context structure. Copy this whole `context/`
tree into a new project, fill in `_shared/` (the common truth) and one
`<component>/` folder per component (copied from `_component-template/`), then edit the
tables/paths below to match your project. Delete guidance comments as you fill it in.

Reference implementation (a filled-in version): `context/README.md` in the AI Done
Right monorepo, which splits its hand-written context across six components + `_shared`.
-->

# `context/` — per-component context, organized to be managed separately

This tree splits a project's hand-written context by **component**, so each component
can be managed on its own (for example in a separate agent workspace against its own
repository) while the cross-component **compatibility contracts stay explicit**. It
mirrors how a single primitive is modeled: every component is a **blackbox** (what it
internally owns) plus **edges** (how it connects to the others).

When context is moved into this tree from elsewhere, move it losslessly (`git mv` so
history is preserved) and record each move so any file is one `git mv` from its origin
(the reference project records moves in a `_manifest.jsonl`; see the archival law).

## Layout

```
context/
  _shared/          the truth EVERY component depends on — read this first
    OVERARCHING-GOAL.md      the mission / north star / the governing filters
    PRODUCT-MARKET-FIT.md    the wedge, moat stack, market, admission bar, monetization
    STANDARDS.md             the engineering + governance laws (points at ../standards/)
    ARCHITECTURE-MAP.md      the components + the dependency law + the seams
    GLOSSARY.md              shared vocabulary (canonical spellings + sources)
  _component-template/       COPY this per component (do not edit in place)
    blackbox.md       what a component internally owns / is / does  (start here)
    edges.md          its interfaces + compatibility contracts with the others
  <component>/        one folder per component (copied from _component-template/)
    blackbox.md
    edges.md
    <topic docs…>     the component's detailed context (structure preserved on move)
```

## The components

<!-- One row per component: the name + a one-line "what it is". Keep this in sync with
     _shared/ARCHITECTURE-MAP.md (that file is the authority; this table is the index). -->

| Component | What it is |
|---|---|
| **<component-a>** | <one-line role>. |
| **<component-b>** | <one-line role>. |
| **<component-c>** | <one-line role>. |

## The compatibility law (do not break when managing components separately)

<!-- Restate the ONE dependency/ordering law + the seams, and point at the machine
     source + the shared map. This is the sentence a separate-management owner must
     internalize before touching any edge. -->

Dependency direction is **<THE-LAW, e.g. A → B → C, never the reverse>**, enforced by
`<check>` over `<path/to/law.json>`. The runtime seams are same-origin: `/api/<x>/...`,
`/<y>/...`, … See [`_shared/ARCHITECTURE-MAP.md`](_shared/ARCHITECTURE-MAP.md) for the
full map and [`_shared/STANDARDS.md`](_shared/STANDARDS.md) for the laws every component
must uphold.

## How to add a component

1. `cp -r _component-template/ <component>/` (never edit `_component-template/` in place).
2. Fill in `<component>/blackbox.md` (what it owns) then `<component>/edges.md` (its
   contracts with the rest).
3. Move the component's detailed docs under `<component>/` losslessly and record the move.
4. Add a row to the components table above and, if needed, to
   `_shared/ARCHITECTURE-MAP.md`.

## How to manage one component

1. Read `_shared/` (goal · PMF · standards · architecture-map · glossary) — the shared frame.
2. Open `context/<component>/blackbox.md` (what it owns) then `edges.md` (its contracts).
3. Work within that component's docs; when you touch an **edge**, honor the contract in
   `edges.md` so the other components stay compatible.

## What is deliberately NOT here (still at its original path)

<!-- List the categories of docs you deliberately leave at their original path so live
     references (from CLAUDE.md / AGENTS.md / build configs / code) do not break. -->

- **Operating-layer anchors** referenced by `<CLAUDE.md / AGENTS.md / build config>` or
  code stay at their original path so live references do not break. Moving them later
  requires a coordinated reference update.
- **Operational / meta** docs (runbooks, index files, archive READMEs) stay in place.
- **Generated** pages stay at their source (regenerated from live data, never moved).
- Already-archived context lives under `archive/legacy/` (see the archival law).
