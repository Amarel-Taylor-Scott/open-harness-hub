<!--
HOW TO USE THIS FILE
====================
This is the per-component EDGES template — the companion to `blackbox.md`. Fill it in
when you add a component (copy `_component-template/` to `context/<your-component>/`).
Delete guidance comments as you fill each section.

WHAT "EDGES" MEANS HERE: the COMPATIBILITY CONTRACT for managing this component
separately. It states the component's inbound/outbound interfaces, the seams it calls,
its concrete dependencies on the other components, and the invariants that must be
preserved so a clean cut stays cheap. It mirrors the `input_edge`/`output_edge` framing
of a single primitive: agents compose by reading a component's edges, not its body. The
companion `blackbox.md` covers what this component internally is/owns/does.

THE ORGANIZING QUESTION for every section: "if someone manages this component in
isolation, what MUST they not break?" An edge that has no enforcing check is a wish;
NAME the check that turns a broken edge red.

Reference implementation (a filled-in version): `_repos/baltor/context/edges.md` in the AI
Done Right monorepo.
-->

# <Component> — edges view (how <Component> connects to the other components)

**Purpose of this file.** The compatibility contract for managing <Component>
separately. It states <Component>'s inbound/outbound interfaces, the same-origin seams,
its concrete dependencies on the other components, and the invariants that must be
preserved so a clean cut stays cheap. The companion `blackbox.md` covers what
<Component> internally is/owns/does.

**Grounding.** Every rule here summarizes and links a machine source or doc (cited
inline). Where a rule is enforced by a check, that check is named — the check, not this
prose, is the authority.

Primary sources synthesized here:

- `<path/to/dependency-law.json>` — the machine source of the dependency law (+ any migration status), enforced by `<check>`.
- `<path/to/api-surface-doc>` — the API surface this component calls / exposes.
- `<path/to/integration-doc>` and `../_shared/ARCHITECTURE-MAP.md` — the seam table.
- `<path/to/state-report>` — the guardrail proofs.

---

## The dependency law (LAW — enforced, honor it exactly)

<!-- Restate the project's dependency direction as it constrains THIS component. Pull
     the allowed/forbidden edges from the machine source; name the check. Add any
     migration gotchas that can silently reintroduce a forbidden edge (lazy imports,
     private-name imports) if your project extracts code between components. -->

```
<A> ──────► <B> ──────► <C>
```

- **<Component> MAY depend on <X>** (<how — e.g. calls the X API as tenant `<id>`>).
- **<Y> MUST NEVER import <Component>** — <why>.

Any forbidden import edge fails the build via `<check>` over `<path/to/law.json>`.
Branch on the **layer + edge**, never on a display name. Source: `<path>`.

<IF-EXTRACTION-IN-PROGRESS: a move between components must pre-grep for lazy
inside-function absolute imports and explicit private-name imports (`from <mod> import
_NAME`) — a top-level import grep misses both and they reintroduce a forbidden edge.
Source: `<path/to/law.json>` → `migration_status.lessons`.>

---

## Outbound: what <Component> consumes from the others

<!-- Every concrete consumption point: the client module, the id/hash single source,
     the API surface it calls. State the ONE sanctioned coupling and forbid parallel
     implementations. Include the failure-isolation contract (what happens when a
     dependency is down). -->

- **`<the client module>`** — <the versioned client; offline-first + graceful fallback
  + per-call receipt>. This is <Component>'s ONLY sanctioned coupling to <X>.
  Source: `<path>`.
- **<shared id/hash single source>** — <Component> mints via `<the single module>`;
  `<the local shim>` is a re-export shim over it (do not add a parallel
  implementation; `<the drift signal>` is forbidden). Source: `<path>`.
- **The <X> API surface** (the boundary <Component> calls): `<endpoint>`, `<endpoint>`, …
  Source: `<path>`.

**Failure isolation contract:** if <X> is unreachable, <Component> **degrades to a
local fallback** behind a circuit breaker and NEVER hard-fails; the per-call receipt
records the fallback. Source: `<path>`.

<!-- Repeat an "Outbound" subsection per dependency (e.g. what it consumes from the
     open store / registry). If a boundary is LOCKED (e.g. specs-only, no
     implementation crosses), state it. -->

---

## The seams (same-origin frontend ↔ backend contract)

<!-- The seam paths THIS component's frontend calls. Same convention as the shared map:
     never hardcode a host; call a same-origin seam the serving layer rewrites. Give
     the source of truth (the code that owns the seam table). -->

A <Component> frontend never hardcodes a backend host; it calls a same-origin **seam
path** that the serving layer rewrites to the real backend (local registry by default;
`<ENV_PREFIX>_*_BASE` in the cloud). Source of truth: `<the code that owns the seam table>`.

| <Component> frontend calls (same origin) | Backend service | Cloud override env |
|---|---|---|
| `/api/<x>/...` | <service> | `<ENV_PREFIX>_X_BASE` |
| `/<y>/...` | <service> | `<ENV_PREFIX>_Y_BASE` |

Source: `../_shared/ARCHITECTURE-MAP.md` ("The seams"); `<path>`.

---

## Inbound: what <Component> exposes to others

<!-- The interfaces OTHER components (or agents/tools) consume from this one: its
     serving surface, its projection/admin APIs, and who observes/consumes its output.
     State the direction explicitly (who depends on whom) to avoid an accidental
     reverse edge. -->

- **<The primary serving surface>** — <the response type / HTTP form>. Source: `<path>`.
- **<Admin / projection APIs>** served by `<the service>`: <list> — all
  **projection-only** (no truth, no secrets). Source: `<path>`.
- **<Who observes / consumes its usage>** — <e.g. downstream of usage, not a dependency
  it imports>. Source: `<path>`.

---

## Compatibility contracts to preserve (invariants for separate management)

<!-- The numbered checklist a separate-management owner must not break. Each item: the
     invariant + the CHECK that enforces it. This is the most reused section — keep it
     a tight, checkable list. -->

1. **Dependency direction** — never import <Component> from <the layers above it>
   (`<check>`).
2. **No shared database** — integrate via the API + events, never a cross-DB join
   (source: `<path>`).
3. **<Id / hash single source>** — mint via `<the module>`; keep `<the shim>` a shim
   (`<the drift signal>` forbidden).
4. **<Domain safety invariant, e.g. agents propose, the component disposes>** —
   (`<check>`).
5. **<Projection-only dashboards / no truth leakage>** — (`<check>`).
6. **<Tenant isolation>** — <private never trains/updates global> (`<check>`).
7. **<Lossless>** — every distillation/promotion preserves raw + held-out + lineage;
   the original is never overwritten (source: `<path>`).
8. **<Graceful degrade>** — <Component> never hard-fails because a dependency is down.
Source (proof names): `<path>`.

---

## Related canonical reading

- `<path/to/law.json>` — the law + migration status (machine source).
- `<path/to/api-surface-doc>` — roles, API surface, hosting/separability.
- `../_shared/ARCHITECTURE-MAP.md` — the full component map + seam table.
- `<path/to/integration-doc>` — the frontend↔backend seam contract.
- `blackbox.md` — the internal view of this component.
