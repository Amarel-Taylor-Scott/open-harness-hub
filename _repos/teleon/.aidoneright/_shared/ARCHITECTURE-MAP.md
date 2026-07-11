<!--
HOW TO USE THIS FILE
====================
This is a FILL-IN TEMPLATE. Copy it to `<your-project>/_repos/_shared/ARCHITECTURE-MAP.md`
and replace every <PLACEHOLDER>. Delete guidance comments once filled.

Purpose: the canonical map of the project's components, how they depend on each
other, and the interfaces (seams) between their frontends and backends. This is the
COMPATIBILITY CONTRACT for the components as they move toward separate management: it
states what each component is, which direction one may depend on another, and the
addressing convention that keeps a frontend identical locally and in the cloud.

TWO RULES:
  1. GROUNDING — every claim is a summary of, and a link to, an existing repo doc or
     machine source. Where a rule is enforced by a check, NAME the check. If this map
     and a cited source disagree, the source wins. This file is a consolidation, not
     a new authority.
  2. The DEPENDENCY DIRECTION is a LAW, not prose — it belongs in a machine file with
     a check that fails the build on a forbidden edge. Branch on the layer + edge,
     never on a display/brand name.

Reference implementation (a filled-in version): `_repos/_shared/ARCHITECTURE-MAP.md`
in the AI Done Right monorepo (six components; law in
`architecture/portfolio_dependency_law.json`, enforced by
`scripts/check_portfolio_dependency_law.py`; seams in `docs/INTEGRATION-BIBLE.md`).
-->

# Architecture Map — the components, their dependency law, and the seams between them

**Purpose.** The canonical map of the <N> components of <PROJECT_NAME> and how they
depend on each other. It is the compatibility contract as the components move toward
being managed separately: what each component is, which direction one may depend on
another, and the seams over which frontends talk to backends.

**Grounding.** Every claim is a summary of, and a link to, an existing repo doc or
machine source. Where a rule is enforced by a check, that check is named. If this map
and a cited source disagree, the cited source wins.

Primary sources synthesized here:

- `<path/to/dependency-law.json>` — the machine source of the dependency law (enforced by `<check>`).
- `<path/to/layer-map.json>` — the systems/layer map (enforced by `<check>`).
- `<path/to/portfolio-architecture-doc>` — the canonical component + dependency architecture.
- `<path/to/integration-doc>` — the seam table (source of truth: `<the code that owns the seam table>`).

---

## The components

<!-- One subsection per component. For each: WHAT it is, WHAT it owns, what it does
     NOT own, its package/web root, and the source. Keep the "owns / does not own"
     boundary explicit — it is what makes separate management safe. -->

### 1. <Component A> — <one-line role>

<WHAT-IT-IS, 2–3 sentences.> It **owns**: <list>. It **does not own**: <list — say
where those moved>. Package root: `<path>`. <Web surface: `<path>` if any.>
Source: `<path>`.

### 2. <Component B> — <one-line role>

<WHAT-IT-IS.> It **owns**: <list>. Package root: `<path>`.
Source: `<path>`.

<!-- … repeat per component … -->

---

## The architectural law (enforced, not prose)

<!-- State the dependency direction as an ASCII arrow diagram, then the ALLOWED edges
     and the FORBIDDEN edges, each pulled from the machine source. Name the check that
     fails the build. If a migration is in progress, point at the machine status field
     rather than typing the current state (it drifts). -->

The dependency direction is a **law**, encoded in `<path/to/law.json>` and enforced by
`<check>`, which fails the build on any forbidden import edge. Branch on the layer +
edge, never on a display name.

```
<Component A> ──────► <Component B> ──────► <Component C>
(<role>)              (<role>)              (<role>)
```

- **<A> depends on <B>** — <how; e.g. calls the B API as tenant `<id>`>.
- **<B> may consume <C>** — <what it consumes>.
- **<C> depends on neither** — <why it stays neutral>.

**Never the reverse.** Forbidden edges (from `<path/to/law.json>` → `forbidden_edges`):

- **<B> must NEVER import <A>** — <why>.
- **<C> must never import <A> or <B>** — <why>.

<!-- If concepts are being extracted from one component into another, point at the
     machine migration_status field for the authoritative current state. -->
<IF-MIGRATION: generic concepts are being extracted `<A>` → `<B>` incrementally and
losslessly (a module move + a re-export shim so callers and proofs stay green — never
big-bang). Consult `<path/to/law.json>` → `migration_status` for the authoritative
current state rather than trusting this sentence. Source: `<path>`.>

**Separability corollary (why the law matters for separate management).** The
components co-locate for <reason> but stay cleanly separable via: a stable versioned
API contract as the only coupling; **no shared database**; no shared code except via
<the published/open interface>; separate identity/billing/infra; and graceful local
fallback if a dependency is unreachable (<A> never hard-fails because <B> is down).
Source: `<path>`.

---

## The seams (the standardized frontend ↔ backend contract)

<!-- The addressing convention. A frontend NEVER hardcodes a backend host/port; it
     calls a same-origin SEAM PATH that the serving layer rewrites to the real
     backend (resolved locally by default, overridden by an env in the cloud). The
     frontend code is identical locally and in the cloud. Put the table's source of
     truth in code, not in this doc. -->

A frontend **never** hardcodes a backend host or port. It calls a same-origin **seam
path**; the serving layer rewrites that seam to the real backend, resolved from the
local service registry by default and overridden by an `<ENV_PREFIX>_*_BASE` env in
the cloud. The frontend code is identical locally and in the cloud. Source of truth
for the table: `<the code that owns the seam table>`.

| Frontend calls (same origin) | Backend service | Local registry id | Cloud override env |
|---|---|---|---|
| `/api/<x>/...` | <service> | `<local_id>` (<port>) | `<ENV_PREFIX>_X_BASE` |
| `/<y>/...` | <service> | `<local_id>` (<port>) | `<ENV_PREFIX>_Y_BASE` |
| <...> | <...> | <...> | <...> |

A new frontend↔backend integration is always a service-plane service **plus** a seam
**plus** a `fetch('/api/<x>/...')` — never a hardcoded host. Source: `<path>`.

---

## Related canonical reading

- `<path>` — <canonical component + dependency architecture>.
- `<path>` — <the systems/layer reframe + governing filters>.
- `<path/to/law.json>` — machine source of the law (proof: `<check>`).
- `<path/to/layer-map.json>` — machine source of the layer↔asset↔gap map (proof: `<check>`).
- `<path>` — the frontend↔backend seam contract.
