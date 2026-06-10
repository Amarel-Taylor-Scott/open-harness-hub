# Context control loop

The core product is a governed control loop for AI context. It does not merely
store prompts, retrieve documents, or assemble pipelines. It continuously tests
whether the context an agent depends on is trustworthy, current, internally
consistent, and modular enough to strengthen when a dependency becomes fragile.

## Core thesis

Open Harness Hub and Baltor create value by doing five things together:

1. **Adversarially validate context.** Treat retrieved documents, memory,
   prompt blocks, tool outputs, and generated intermediate state as untrusted
   until they pass injection, provenance, citation, and policy checks.
2. **Find fragile context.** Detect stale facts, unsupported claims, inconsistent
   sources, ambiguous prompt instructions, brittle regex/routing rules, weak
   citations, low-fidelity compression, and components that only work under
   narrow examples.
3. **Keep context current.** Bind volatile facts to tools, CDC feeds, freshness
   checks, signed publishers, and verified search surfaces instead of freezing
   them into personas or static prompts.
4. **Reconcile internal inconsistencies.** Compare source authority, timestamps,
   provenance chains, policy scope, jurisdiction, component version, benchmark
   evidence, and human review state before deciding which context wins.
5. **Strengthen fragile components.** Promote stronger rule packs, tools,
   knowledge packs, processors, harnesses, or verified global context feeds when
   a dependency is stale, low-lift, unsafe, or too expensive.

The operating loop is:

```text
observe context dependency
-> adversarially test it
-> score fragility, freshness, reconciliation status, and lift
-> route to stronger components, human review, or verified global context
-> publish updated component/context pack
-> monitor drift and reuse events
```

## What counts as fragile

Fragility is broader than factual inaccuracy. A component or context block is
fragile when small changes in the world, prompt, model, user, or corpus can
cause a large drop in reliability.

Common signals:

- source is stale, revoked, superseded, or no longer authoritative;
- two trusted sources disagree and no reconciliation policy decides precedence;
- a prompt block mixes stable policy with volatile facts;
- a context pack has poor compression-fidelity scores;
- citations do not support the generated claim;
- a tool schema is ambiguous or changes without a version/hash update;
- a rule pack fires on examples but fails adversarial variants;
- a harness depends on one model behavior with no fallback path;
- cache reuse would cross a privacy or tenant boundary;
- benchmark lift is narrow, decays over time, or disappears under a stronger
  baseline model.

## Component strengthening policy

The platform should prefer modular strengthening when a better primitive exists.
Strengthening candidates can be:

- deterministic tools for facts that should not live in prompts;
- signed or registry-verified knowledge objects for public facts;
- fresher CDC-backed context packs for volatile domains;
- stricter schemas or output contracts for brittle model outputs;
- higher-lift rule packs, processors, or harnesses from the catalog;
- verified global context retrieved through governed search/tool surfaces;
- human-reviewed components when automated evidence is insufficient.

The strengthening decision should preserve the trust boundary of the original
component unless the user explicitly approves a boundary change.

## Reconciliation

When sources disagree, the runtime should not flatten the mismatch into a single
summary. It should emit a reconciliation object with:

- competing or overlapping claims;
- source ids and provenance;
- effective dates and collection dates;
- jurisdiction or scope;
- authority ranking;
- freshness state;
- citation support;
- recommended active claim or escalation reason.

Resolvable mismatches update the active context pack. Unresolved mismatches
become review tickets, abstentions, or user-visible caveats depending on the
pipeline risk tier.

## Relationship to Prompt ABI

Prompt ABI makes stable, verified context cheap to reuse. The context control
loop decides what is allowed to become stable and reusable in the first place.

That means token-efficient reusable context must pass:

- adversarial validation;
- freshness checks;
- reconciliation checks;
- privacy/cache-scope checks;
- compression-fidelity checks when compressed;
- benchmark or task-lift evidence when it claims to improve a workflow.

Only then should it become a public, org, tenant, or user-scoped prefix/cache
entry.

## Product boundary

The point is not to promise perfect truth. The product promise is narrower and
more defensible:

```text
find fragile context earlier,
keep volatile context fresh,
resolve or expose conflicts,
strengthen weak dependencies with better primitives,
and prove the resulting pipeline lifts over a bare model.
```

That is the shared core of Open Harness Hub and Baltor: governed context that is
verified, current, reconciled, modular, token-efficient, and measurable.
