<!--
HOW TO USE THIS FILE
====================
This is a FILL-IN TEMPLATE. Copy it to `<your-project>/_repos/_shared/STANDARDS.md`
and replace every <PLACEHOLDER>. Delete guidance comments once filled.

Purpose: the shared contract that keeps independently-managed components compatible.
This is the POINTER version — it lists the load-bearing laws as one-line entries and
sends the reader to the full normative standard for each. Keep the full standard docs
in a sibling `standards/` directory (see `_repos/dev-rules-context/standards/` for portable,
reusable versions of the common laws).

THE SHAPE OF EACH LAW (do not vary it — consistency is what makes the set scannable):
  - **Rule** — one line, imperative.
  - **Why** — the failure mode it prevents (ideally a real bug that already shipped).
  - **Enforced by** — the CHECK/script that turns drift red. A law with no check is a
    suggestion, not a standard. Name the check.
  - **Source** — the full standard doc + the operating-layer reference.

This file CONSOLIDATES and LINKS; it never restates a standard's detail. Read the
linked source before acting on a law.

Reference implementation (a filled-in version): `_repos/_shared/STANDARDS.md` in the
AI Done Right monorepo (eight laws), whose full standard docs are portably re-authored
in `_repos/dev-rules-context/standards/`.
-->

# Component Standards — the engineering + governance laws every component follows

This is the shared contract that keeps independently-managed components compatible.
Every component obeys the same laws below. Each is stated as **Rule** / **Why** /
**Enforced by** / **Source**. This file consolidates and links the canonical
standards; it never restates their detail — read the linked source before acting.

Full standard docs live in **[`../standards/`](../standards/)** (the portable,
reusable versions). Canonical operating-layer sources: `<path/to/CLAUDE.md or AGENTS.md>`,
`<path/to/north-star.md>`, `<path/to/standards-index>`.

---

<!-- List YOUR project's load-bearing laws. The set below is the portable default
     (the same laws re-authored in _repos/dev-rules-context/standards/). Keep, drop, or add per
     project — but every entry keeps the Rule/Why/Enforced-by/Source shape. -->

## 1. <e.g. No Magic Values — single source of truth>

- **Rule:** <one line>.
- **Why:** <the failure mode; cite the real bug if one shipped>.
- **Enforced by:** <the config module / vocabulary file / CI assertion that recomputes and fails on drift>.
- **Source:** [`../standards/NO-MAGIC-VALUES.md`](../standards/NO-MAGIC-VALUES.md); `<operating-layer path>`.

## 2. <e.g. Deterministic global naming — CODE plane>

- **Rule:** <one line>.
- **Why:** <one line>.
- **Enforced by:** `<engine>` + `<conformance check>` over `<migration manifest>`.
- **Source:** [`../standards/GLOBALLY-UNIQUE-NAMING.md`](../standards/GLOBALLY-UNIQUE-NAMING.md); `<path>`.

## 3. <e.g. ID / hash discipline — DATA plane>

- **Rule:** <one line — generated ids minted by ONE module; version in metadata, not names>.
- **Why:** <one line — collision-proof keys for millions of rows; formatting changes are non-events>.
- **Enforced by:** `<single-source check>` over `<migration manifest>` (the drift signal ratchets down).
- **Source:** [`../standards/GLOBALLY-UNIQUE-NAMING.md`](../standards/GLOBALLY-UNIQUE-NAMING.md); `<path>`.

## 4. <e.g. Change Verification — warrant before change>

- **Rule:** <one line — every change carries a warrant matched to blast radius>.
- **Why:** <"it's green" is necessary, not sufficient; cite the unwarranted change that got reversed>.
- **Enforced by:** <the verifier checks the warrant, not just green; the verifier is a different agent than the builder>.
- **Source:** [`../standards/CHANGE-VERIFICATION.md`](../standards/CHANGE-VERIFICATION.md); `<path>`.

## 5. <e.g. Change-impact audit — audit neighbors before AND after a code change>

- **Rule:** <one line — audit strong graph connections before and after an edit, fix load-bearing neighbors same-change>.
- **Why:** <a green suite says the code runs; the graph says what else can break>.
- **Enforced by:** `<the audit command>` + `<self-tested graph seam>` registered in `<proof entrypoint>`.
- **Source:** <path to the audit protocol>; `<path>`.

## 6. <e.g. Lossless Distillation — distillation is never replacement>

- **Rule:** <one line — any distillation/compression/promotion creates a NEW versioned layer, preserving raw + lineage + held-out + rejected + rollback>.
- **Why:** <omitted / held-out / rejected / superseded ≠ deleted>.
- **Enforced by:** <the promotability test + side-by-side + shadow mode + rehydration proof>.
- **Source:** [`../standards/LOSSLESS-DISTILLATION.md`](../standards/LOSSLESS-DISTILLATION.md); `<path>`.

## 7. <e.g. Archived / Legacy — move, never delete; never untrack>

- **Rule:** <one line — outdated context is MOVED under `archive/legacy/<original-path>` with a status label, never deleted or untracked>.
- **Why:** <superseded ≠ deleted; archived files drop out of model context but stay recoverable in git>.
- **Enforced by:** `<the mover script>` (conservative header-marker detection) + `<manifest>` + codemap exclusion of `archive/`.
- **Source:** [`../standards/ARCHIVAL-MOVE-NEVER-DELETE.md`](../standards/ARCHIVAL-MOVE-NEVER-DELETE.md); `<path>`.

## 8. <e.g. Promotion Boundary — load-ready is not publication-ready>

- **Rule:** <one line — a candidate can be load-ready yet MUST NOT be user-visible while it has open review / high-risk / placeholder / unresolved-source flags>.
- **Why:** <publishing an unverified candidate erodes the governance moat; report the stages separately, never raw generated lines as active>.
- **Enforced by:** [`../standards/CANDIDATE-TRUTH-BOUNDARY.md`](../standards/CANDIDATE-TRUTH-BOUNDARY.md); `<the readiness plan script>`; candidates carry `serves_truth=false` until proof.
- **Source:** `<path>`.

<!-- Add project-specific laws here (e.g. verify-the-verifier, multi-path development).
     Portable versions of both live in _repos/dev-rules-context/standards/. -->

---

## Per-pattern standards (the component-shape layer)

<!-- The laws above are CROSS-CUTTING. The *shape* of a specific component pattern
     (source adapter, command handler, projection route, provider adapter, proof
     script, docs page) is governed separately by normative standards + runnable
     templates. Point at that catalog here. -->

The laws above are cross-cutting. The *shape* of a specific component pattern is
governed separately by the normative standards + runnable templates in `<path/to/standards-index>`
→ `<path/to/standard_catalog.json>` / `<path/to/template_catalog.json>`, generated by
`<generator>` and proven by `<catalog checks>`. `enforced` standards are
non-negotiable for any new component. Use those to BUILD a conforming component; use
the laws here to keep it COMPATIBLE once components are managed independently.
