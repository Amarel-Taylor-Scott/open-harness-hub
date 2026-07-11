# GEV Adversarial Interrogatories

This is the adversarial layer for the Graphable, Enrichable, Verifiable system. It gives deterministic
tools, LLM reviewers, and humans repeatable question sets so reviews do not miss blast radius, dynamic
references, public contracts, data-shape problems, or product impact.

The intent is not to slow work down. It is to make confusion harder.

## Corner-Case Families

1. **Dynamic Python:** `getattr`, `setattr`, `globals`, `locals`, `eval`, `exec`, dynamic imports, string
   dispatch, monkey-patching.
2. **Framework entrypoints:** CLI `main`, pytest/unittest hooks, web route handlers, Click/Typer commands,
   template `run(inputs)`, Celery tasks, decorators.
3. **Schema and serialization:** JSON/YAML fields, dataclass fields, TypedDict keys, Pydantic models, CSV
   columns, database columns, OpenAPI contracts.
4. **Data-shape scalability:** numbered scalars, repeated calls, scalar-only functions that should accept
   sequences, rule tables, dispatch maps.
5. **Control-flow fragility:** branch ladders, unbounded loops, broad exception swallowing, retry without
   budgets, implicit fallthrough.
6. **State and side effects:** mutable defaults, global state, cache invalidation, file/network/DB/queue
   effects, time/random dependence.
7. **Blast radius and re-exports:** `__all__`, facades, star imports, aliases, package `__init__`, public
   exports, downstream callers, UI/backend seams.
8. **Security/privacy/tenant:** secret-like values, PII/PHI, auth/session, tenant boundary, egress, prompt
   injection, unsafe deserialization.
9. **Temporal/freshness:** timezone, relative dates, TTL, CDC, stale facts, scheduled jobs, injected clock.
10. **Long-name failure modes:** token bloat, line length, external API name limits, path limits, public
    aliases, case-insensitive filesystem collisions.
11. **Multi-language surface:** JSX handlers, HTML forms, CSS/data attributes, frontend routes, fetch calls,
    templates.
12. **Generated-code quality:** model-authored snippets, placeholders, missing purpose, unbounded loops,
    strict typing before shape stability.

## Core Interrogatories

Every review packet should answer these before a fix is accepted:

### Graphability

- What node(s) does this artifact create or modify?
- What edge types should exist?
- What dynamic or unresolved edge could hide from static parsing?
- Can this be found by exact grep using the long source name?

### Blast Radius

- Who calls this, imports this, re-exports this, or serializes this?
- Which UI/backend paths reach it?
- Which proofs fail if this changes?
- What is the smallest bounded slice that can be safely migrated?

### Enrichment

- What purpose does this object serve?
- What problem does it solve?
- What inputs and outputs does it expect today?
- What UI/UX or product behavior depends on it?
- What would confuse an LLM or engineer reading only this packet?

### Verification

- Which deterministic check proves the finding exists?
- Which proof or test accepts a fix?
- What nondeterministic enrichment is merely candidate-only?
- What human/owner review is required before promotion?

## Specialized Interrogatories

### Data Shape

Used for scalar series, repeated calls, rigid branch chains, and magic literals.

- Is this scalar actually one element of a repeated set?
- Should input be `scalar_or_sequence`?
- Can a table, array, map, or dispatch row replace the branch/repetition?
- What Teleon primitive block makes it scalable?

### Dynamic Reference

Used for `getattr`, `**kwargs`, dynamic imports, and string dispatch.

- What name/field/method/module is resolved dynamically?
- Can the possible targets be enumerated into a dispatch table?
- Does this block rename or data-flow confidence?
- What fixture proves each dynamic target remains reachable?

### Security/Privacy

Used for secret-like patterns and sensitive surfaces.

- Is this real, synthetic, or a detector fixture?
- Is it marked synthetic clearly enough?
- Can it leak into docs, logs, prompts, or deployed artifacts?
- Which redaction or fixture-marker proof guards it?

### External Contract

Used for entrypoints, decorators, framework callbacks, and pyprefix drift on public names.

- Is this name called by a framework, CLI, template, or external user?
- Should it remain as a shim while the implementation gets the long name?
- Which callers use keyword names, string names, route names, or serialized keys?
- What compatibility proof prevents breaking public behavior?

## Reviewer Skill Templates

These are lightweight roles an LLM or human can apply to the same packet. They are not truth sources.

- **graph_cartographer:** map nodes, edges, unresolved references, and blast radius before proposing fixes.
- **contract_skeptic:** assume the change breaks a public/API/schema/framework contract and demand the shim.
- **data_shape_normalizer:** find scalar-to-array, loop, dispatch, and rule-table opportunities.
- **verification_prosecutor:** require deterministic evidence, proof command, and fixture before acceptance.
- **adversarial_breaker:** test malformed, repeated, stale, dynamic, concurrent, and cross-tenant cases.
- **ux_product_mapper:** map code risk to user workflow, UI/UX, and product behavior.

## How Packets Use This

`scripts/hybrid_repo_review_pipeline.py` adds `interrogatory_template_ids` to every packet. All packets get
the core graphability, blast-radius, enrichment, and verification interrogatories. Specialized templates
are added by finding kind.

This gives LLM review a bounded, repeatable frame:

1. deterministic evidence first;
2. graph and blast radius visible;
3. interrogatories selected by kind;
4. LLM output candidate-only;
5. proof gate promotes.
