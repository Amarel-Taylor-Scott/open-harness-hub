<!--
HOW TO USE THIS FILE
====================
This is a FILL-IN TEMPLATE. Copy it to `<your-project>/_repos/_shared/GLOSSARY.md`
and replace every <PLACEHOLDER>. Delete guidance comments once filled.

Purpose: the shared vocabulary so separately-managed components stay consistent. Each
term gives ONE canonical spelling, one crisp definition, and a link to the detailed
source doc (the source wins on conflict).

THREE RULES:
  1. NOTHING IS INVENTED — every entry cites where it comes from. If you cannot cite
     a term, it is not canonical yet.
  2. ONE CANONICAL SPELLING per concept. Where a term REPLACES an old word, say so
     ("write X, not Y") — a glossary's job is to kill the synonym drift.
  3. GOVERNING VOCABULARY RULES (which words to use, which never to) live in the
     operating layer; this file points at them, it does not re-legislate them.

Reference implementation (a filled-in version): `_repos/_shared/GLOSSARY.md` in the
AI Done Right monorepo (seven primitives, edges, blackbox, serves_truth vs candidate,
the two naming planes).
-->

# Shared Glossary

The shared vocabulary so separately-managed components stay consistent. Each term
below gives the **canonical spelling** and one crisp definition, then links to the
detailed source doc — the source wins on any conflict. Nothing here is invented:
every entry cites where it comes from.

Governing vocabulary rules (spellings, what NOT to say) live in `<operating-layer path>`.
<The core model / taxonomy doc> is `<path>`. The naming law is `<path>`.

---

## <Core-model section — e.g. "The core primitives / objects">

<!-- If your project reduces everything to a small fixed set (primitives, object
     types, a schema), define the set here with its single source. Number them, give
     each a one-line role, and state the canonical spelling. Add a closure rule if
     there is one (e.g. "there is no eighth X"). -->

Everything reduces to <THE-FIXED-SET>, all extending one shell (`<path>`, contract
`<signature>`). Canonical spellings + one-line roles (source: `<path>`):

1. **<Term 1>** — <role>.
2. **<Term 2>** — <role>. (Product term; NOT "<the banned synonym>".)
3. **<Term 3>** — <role>. (NOT "<banned synonym>" in prose.)
   <!-- … -->

<CLOSURE-RULE if any: there is no <N+1>th <thing>; an unmet need becomes a
<capability-request / typed-empty-slot>, never user-visible as a real one (source: `<path>`).>

### <Term-that-needs-its-own-paragraph, e.g. a product term that replaces a legacy schema key>

<Definition. If a schema `type` key differs from the user-facing word, say the storage
key stays for back-compat and is NEVER shown to users; in prose write <CANONICAL>.>
Source: `<path>`.

---

## <Distinction section — e.g. "Component vs subcomponent">

<!-- Define pairs of terms readers confuse. Use vs. sparingly; prefer a one-line
     definition of each + one line on how they relate. Cite the operating-layer rule
     that mandates the usage. -->

Use **<Term A>** and **<Term B>** in new prose; avoid new uses of "<banned word>"
unless quoting an existing schema/filename/legacy phrase (source: `<path>`). A
**<Term A>** is <definition>; a **<Term B>** is <definition>.

---

## <Interface vocabulary — e.g. "Edges / input_edge / output_edge">

<!-- If components compose by reading INTERFACES rather than bodies, define the
     interface terms here — the connection-point names, the identity/dedupe key, the
     "compose by reading names + edges, not bodies" rule. This ties directly to the
     per-component edges.md template. -->

<A component's typed connection points: `<input_edge>` (what it consumes) and
`<output_edge>` (what it emits), each with a compact typed value plus a description.
Agents compose by reading names + edges, not bodies.> Source: `<path>`.

## <Contract vocabulary — e.g. "blackbox">

<The one-sentence contract of a component: does-what, in→out, key side effect —
without implementation detail. The shallow disclosure a composing agent reads before
opening the source.> Source: `<path>`.

---

## <Truth/state flags — e.g. "serves_truth vs candidate">

<!-- If your project separates asserted truth from unverified work, define the flags
     here. State the DEFAULT (usually: everything is born unverified) and the ONE
     condition under which something becomes truth. This is load-bearing for the
     promotion boundary. -->

Two flags that separate asserted truth from unverified work:

- **`<candidate flag> = true` / `<truth flag> = false`** — the default on every
  generated row / output / mined component. Candidate advice, not asserted truth,
  until a promotion gate passes (sources: `<path>`).
- **`<truth flag> = true`** — reserved for <THE-ONE-KIND-OF-GOVERNED-OUTPUT> that has
  passed verification. Everything else is `<truth flag> = false` (source: `<path>`).

## <Disclosure/proof ladder — if any>

<!-- If proof/verification is tiered, name the ladder and the top tier. Be honest
     about what is a live runtime vs a scorecard scheme (cite a red-team doc if one
     flagged the gap). -->

<Components disclose progressively: `<L1> → … → <Ln>`; a row's `<level field>` records
how far its proof reached; a row is only proven once executed proof at the top passes.
Until then it stays `<candidate>=true`. NOTE: <flag honestly if the full escalation
engine is a scheme, not yet a live runtime>. Source: `<path>`.>

---

## <Naming planes — the code + data uniqueness law>

<!-- If the project mandates globally-unique location-derived names, summarize both
     planes (code-object naming scheme + data-object id scheme) with the engine and
     the gate for each. State the "version lives in metadata, never in a name/id"
     rule and WHY it matters (grep-as-graph exactness). -->

Every defined thing gets a globally-unique, location-derived, meaning-bearing name;
no name is reused; version lives in metadata, never in a name or id. Full law: `<path>`.

- **<code-plane name> — the CODE-object plane.** Definitions follow `<the scheme>`;
  engine `<path>`; gate `<path>`. Example: `<example name>`.
- **<data-plane name> — the DATA-object plane.** Generated ids minted ONLY by
  `<the single module>` (`<the id formula>`). Version lives in `<metadata field>`,
  never in a name/id. Gate: `<path>` (the drift signal is `<x>`, ratcheting down).

Why it matters: globally-unique names make grep-as-graph exact — the code graph,
component edges, and cross-codebase search resolve by NAME with zero ambiguity
(source: `<path>`).

---

## Terms defined + sources

<!-- The scannable index: every canonical term + its source doc, one row each. -->

| Term (canonical spelling) | Source doc |
|---|---|
| <term> | `<path>` |
| <term> (not "<banned synonym>") | `<path>` |
| <term> | `<path>` |
