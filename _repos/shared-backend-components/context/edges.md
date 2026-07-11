# Backend — the substrate (EDGES view)

**What this file is.** How the **Backend / substrate** connects to the other five components
(AI Done Right, Teleon, Baltor, OpenHubForAI, AIDevObserver) and to `_shared`: its inbound and
outbound interfaces, the same-origin seams, and the **compatibility contracts** that must be preserved
when the substrate is managed as a separate component. It honors the portfolio dependency law and lists
concrete import/consume relationships.

**Grounding rule.** Every claim summarizes and links an existing repo doc or machine source; the cited
source wins on disagreement. No fabricated metrics — counts come from the named scripts.

---

## 1. The one structural fact that shapes every edge

The substrate is **not a fourth brand layer with its own package root.** Its Python is realized inside
the **Teleon** package (`src/teleon/{registry,storage,components,knowledge,...}`) plus the tooling tree
(`scripts/`, which the dependency law treats as tooling, not a brand), the config registries
(`architecture/*.json`), the seven-primitive shells (`scripts/primitives/`), and JSONL staging under
`data/`. Therefore, in the portfolio dependency law the substrate's Python sits at the **Teleon layer**,
and every cross-component edge inherits the law below.
Sources: `architecture/portfolio_dependency_law.json` → `layers.teleon`;
`_repos/shared-backend-components/context/blackbox.md` §1; directory listings under `src/teleon/`, `scripts/`, `architecture/`.

---

## 2. The dependency law (honored, enforced by a proof)

Machine source `architecture/portfolio_dependency_law.json`, enforced by
`scripts/check_portfolio_dependency_law.py` (fails the build on any forbidden import edge). Branch on
the layer + edge, never on a brand display name.

```
Baltor ─────► Teleon ─────► OpenHubForAI (OpenHarnessHub)
(applied)     (runtime SaaS + the substrate's Python)   (open ecosystem + spec)
```

- **Baltor depends on Teleon** — it calls the substrate/runtime as tenant `baltor-internal` through the
  versioned `src/baltor/teleon_client`; Baltor may also depend on OpenHubForAI.
- **Teleon may consume OpenHubForAI** artifacts (harnesses, templates, skills, the open CapabilityTask
  spec). Because the substrate's Python is Teleon-layer, the substrate may consume OpenHubForAI but
  **must never import Baltor.**
- **OpenHubForAI depends on neither** — the open ecosystem/spec stays neutral.

**Forbidden edges** (`forbidden_edges`): Teleon → Baltor (Teleon is reusable infrastructure, not a
Baltor feature); OpenHubForAI → Baltor; OpenHubForAI → Teleon. **Never the reverse of the arrow above.**

Consequence for the substrate specifically: registry/factory/service-plane/codegraph/naming code under
`src/teleon` and `scripts` may be consumed by Baltor and may read OpenHubForAI packages, but may not
`import src.baltor.*`. Lazy (inside-function) absolute imports count — a `from src.baltor...` inside a
method is still a forbidden Teleon→Baltor edge (recorded lesson in the law's `migration_status.lessons`).
Sources: `architecture/portfolio_dependency_law.json` (`law`, `forbidden_edges`, `migration_status`);
`_repos/_shared/ARCHITECTURE-MAP.md` §"The architectural law".

**Internal import direction is also strict + downward** (a finer-grained law within the substrate):
`architecture/import_boundaries.json` — `contracts → ports → adapters → runtime → processors → workers`,
each with `may_import` / `must_not_import` sets (e.g. `contracts` may import only stdlib; `runtime` must
not import processors/web/demos/`scripts.baltor_admin_demo_server`). Enforced by
`check_import_boundaries_manifest.py`.
Source: `architecture/import_boundaries.json`.

---

## 3. Outbound — what the substrate EXPOSES (who consumes it, and how)

### 3a. → Teleon (the compiler/runtime, same package)
The Teleon **descent/compiler** consumes the registries as its ingredient buffet: a capability statement
is compiled into the cheapest bounded, verified DAG — **retrieve → compose → bound & verify → descend →
execute** — where *retrieve* reads the curated core registries via the registry port. The registry
returns pointers/shapes only (`serves_truth=false`); the type system + descent dispose.
Sources: `docs/concepts/system-overview.md` §§2–3;
`docs/concepts/compiling-capabilities-into-bounded-dags.md`; `src/teleon/registry/port.py`.

### 3b. → Baltor (the applied product, a tenant)
Baltor consumes the substrate as tenant `baltor-internal` through `src/baltor/teleon_client`
(offline-first local + graceful fallback from a remote seam + per-call receipt). Baltor governs **truth**
on top (provenance, verify, CDC) but does not re-own the generic registry/runtime — the Baltor→Teleon
extraction of fleet/experiments/purpose_tasks/client is recorded **COMPLETE** in the law's
`migration_status`. Baltor imports the canonical-id single source via the
`src/baltor/experiments/ids.py` shim (never a re-implemented hash).
Sources: `architecture/portfolio_dependency_law.json` → `migration_status`;
`_repos/_shared/ARCHITECTURE-MAP.md` §"3. Baltor"; `CLAUDE.md` §"Deterministic Global Object Naming".

### 3c. → OpenHubForAI (the open ecosystem exposes the registries)
`architecture/registry_ontology.json` maps each load-bearing registry to the **Open\*Hub that exposes
it** (a hub can expose several registries; finer layer beneath `architecture/hub_profiles.json`). The
open CapabilityTask spec is stewarded by OpenHubForAI; the substrate provides the reference registries
that back the hubs. The public/free funnel is export of pure text-operation / static-information
components; the recurring-value layer is the code-executing + dynamic-corpus components.
Sources: `architecture/registry_ontology.json`; `architecture/hub_profiles.json`;
`docs/concepts/component-taxonomy-and-stages.md` (pricing boundary).

### 3d. → AIDevObserver (the AI-usage layer, `ai_waste_engine` is `live`)
AIDevObserver's reinvention/reuse coaching is **grounded by the substrate**: the reinvention guard
(`src/teleon/registry/reinvention_guard.py`) queries the registry federation to answer "this already
exists, don't rebuild it" — the moat is grounding, and federation + search is that grounding. The
`ai_waste_engine` substrate layer IS AIDevObserver + economics + inefficient-pipeline archetypes.
Sources: `architecture/substrate_layers.json` → `layers[ai_waste_engine]` / `existing_systems_registry`;
`src/teleon/registry/reinvention_guard.py`; `_repos/aidevobserver/context/` (peer component).

### 3e. → all frontends (over the `/registry/...` seam)
The catalog projection the frontends read is `local_openhubforai_projection_api` (port 9423) behind the
same-origin `/registry/...` seam, served by the showcase. Frontends never hardcode a host.
Sources: `architecture/local_service_registry.json`; `docs/INTEGRATION-BIBLE.md` §§1–2.

---

## 4. Inbound — what the substrate CONSUMES

- **From `_shared` (the standards + naming laws):** the eight component laws in
  `_repos/_shared/STANDARDS.md` (No Magic Values, both naming planes, change verification, codegraph
  audit, lossless distillation, archive-don't-delete, promotion boundary), canonical in
  `docs/codex/*` and `CLAUDE.md`. The substrate is the primary enforcer of the two naming planes
  (`scripts/pyprefix.py`, `src.teleon.experiments.ids`).
- **From external sources (candidate-only intake):** the harvester `scripts/harvest_tools.py` and
  `scripts/acquisition/*` scrape tools/repos into `data/dev-intel/*.jsonl` staging (discovery ≠ trust;
  license + plane classified; deduped by content hash). Nothing in staging is read by the descent until
  promoted.
- **From OpenHubForAI:** the open CapabilityTask spec + published packages (allowed by the law).
- **From the config registries themselves:** `architecture/*.json` are the config storage tier the
  registry port wraps.
Sources: `architecture/registry_layers.json`; `_repos/_shared/STANDARDS.md`;
`architecture/portfolio_dependency_law.json`.

---

## 5. The seams (the standardized frontend ↔ backend contract)

A frontend calls a same-origin **seam path**; the showcase rewrites it to the real backend, resolved
from `architecture/local_service_registry.json` locally and overridden by `OH_SEAM_*_BASE` in the cloud.
The frontend code is identical locally and in the cloud. Source of truth: the seam table in
`scripts/showcase/server.py` (mirrored in `docs/INTEGRATION-BIBLE.md` §2).

| Frontend calls (same origin) | Backend service | Local registry id (port) | Cloud override env |
|---|---|---|---|
| `/registry/...` | **registry / catalog projection (this component)** | `local_openhubforai_projection_api` (9423) | `OH_SEAM_REGISTRY_BASE` |
| `/api/identity/...` | auth / identity | `local_auth_service` (9410) | `OH_SEAM_IDENTITY_BASE` |
| `/analytics/...` | event tracking | `local_event_tracking_service` (9420) | `OH_SEAM_ANALYTICS_BASE` |
| `/api/mailbox/...` | mailbox | `mailbox_local_service` (9428) | `OH_SEAM_MAILBOX_BASE` |
| `/api/teleon/...` | Teleon runtime | `teleon_local_runtime` (9430) | `OH_SEAM_TELEON_RUNTIME_BASE` |
| `/api/observer/...` | AIDevObserver session review | `observer_runtime` (9431) | `OH_SEAM_OBSERVER_BASE` |
| live-ops | Baltor admin / live-ops | `baltor_admin_demo_server` | `OH_SEAM_LIVEOPS_BASE` |

A new frontend↔backend integration is always a service-plane service **plus** a seam **plus** a
`fetch('/api/<x>/...')` — never a hardcoded host.
Sources: `_repos/_shared/ARCHITECTURE-MAP.md` §"The seams"; `docs/INTEGRATION-BIBLE.md` §§1–2;
`architecture/local_service_registry.json`.

---

## 6. Compatibility contracts to PRESERVE (when managed separately)

These are the invariants other components rely on; breaking one breaks a consumer silently. Change a
seam/contract/count and update its check in the **same** change.

1. **The registry port verbs.** Every source catalog is reachable through the uniform
   `list / lookup / search / explain` menu on `src/teleon/registry/port.py`. The lexical scorer may be
   swapped for a learned one **behind the same port** without changing a call site (agnostic-adapter
   pattern). Adding a catalog = a `CATALOGS` entry keyed by its `registry_ontology` id, not a bespoke
   accessor. Source: `src/teleon/registry/port.py`.
2. **`serves_truth = false` at this layer.** A registry/index/code-graph returns pointers/shapes/static
   derivations, never a truth claim. Consumers (Baltor) add truth on top; the substrate must not start
   asserting it. Sources: `src/teleon/registry/port.py`, `architecture/registry_layers.json`,
   `scripts/codegraph.py`.
3. **The promotion boundary.** staged → core requires license-clean/vendorable or a service/technique
   tag, a real source URL, dedupe-clean, a vetting pass; the descent reads only the promoted core.
   Load-ready ≠ publication-ready; report the six stages separately. Sources:
   `architecture/registry_layers.json`, `_repos/_shared/STANDARDS.md` §8, `CLAUDE.md`
   §"Promotion Boundary".
4. **The row families.** A factory batch preserves `source_record`, `normalized_object`,
   `canonical_entity`, `object_entity_ref`, `dedupe_cluster`, `label_assignment`, `dimension_value`,
   `object_embedding`, `index_record` (+ `review_ticket` on risk). Downstream load plans key on these
   names. Sources: `CLAUDE.md` §"Required Row Families",
   `docs/architecture/database-backed-component-store.md`.
5. **Canonical id single source (DATA plane).** Generated ids come only from `src.teleon.experiments.ids`
   (`"{prefix}-{sha256(canonical_bytes)[:16]}"`); Baltor via the shim; version lives in `schema_version`
   metadata (no `.vN`/`@N`). A NEW `import hashlib` in `src/**` fails the gate. Sources: `CLAUDE.md`
   §"ID And Hash Discipline"; `scripts/check_canonical_id_single_source.py`;
   `architecture/canonical_id_migration.json`.
6. **Pyprefix naming (CODE plane).** New/generated substrate code follows
   `py_<kind>__<file>__<scope>__<name>` from the first draft; a migrated path stays 100% conformant.
   Sources: `scripts/pyprefix.py`, `architecture/pyprefix_migration.json`,
   `architecture/teleon_codegen_contracts.json`.
7. **The `record_store` port + storage tiers.** Config (JSON in git) / operational (SQLite → Postgres +
   pgvector) / history (warehouse), all behind `src/teleon/storage/record_store.py`. Per-registry
   embedding column manifests + table shapes are single-sourced in
   `architecture/primitive_data_plane.json` — import dimensions/column-names/paths, never re-type them.
   Sources: `architecture/storage_tier_policy.json`, `architecture/primitive_data_plane.json`.
8. **The seam contract (§5).** Frontends address the substrate only through `/registry/...` (and the
   other seams), resolved by the local service registry / `OH_SEAM_*_BASE`. Source of truth is
   `scripts/showcase/server.py`. Source: `docs/INTEGRATION-BIBLE.md`.
9. **Lossless distillation.** Any distillation/dedupe/promotion/LLM→rule conversion in the factory
   creates a new versioned derived layer and PRESERVES the raw layer + lineage + held-out + rejected +
   rollback. Distillation is never replacement. Sources: `docs/codex/lossless-distillation.md`,
   `_repos/_shared/STANDARDS.md` §6.
10. **Separability corollary.** No shared database across products; the only cross-product coupling is a
    stable versioned API + the open spec / published OpenHubForAI packages; Baltor never hard-fails
    because Teleon is unreachable (graceful local fallback). Source:
    `docs/strategy/teleon-baltor-openhubforai-portfolio.md` (hosting topology);
    `_repos/_shared/ARCHITECTURE-MAP.md` §"Separability corollary".

---

## 7. Concrete dependency list (imports/consumes ↔ exposes)

**Substrate imports / consumes:**
- stdlib only for the deepest layers (`contracts`, and `src/teleon/registry/port.py` is deterministic,
  stdlib-only). Source: `architecture/import_boundaries.json`, `src/teleon/registry/port.py`.
- the config registries `architecture/*.json` (read through the port).
- the naming-plane engines `scripts/pyprefix.py`, `src.teleon.experiments.ids`.
- OpenHubForAI packages + the open spec (allowed by the law).
- external candidate rows via `scripts/harvest_tools.py` / `scripts/acquisition/*` into `data/` staging.

**Substrate exposes / is imported by:**
- Teleon compiler/descent (`retrieve` stage) — reads the registry port.
- Baltor via `src/baltor/teleon_client` + the `ids.py` shim (tenant `baltor-internal`).
- OpenHubForAI hubs via `architecture/registry_ontology.json` → `hub_profiles.json`.
- AIDevObserver reinvention guard (`src/teleon/registry/reinvention_guard.py`) grounds reuse coaching.
- all frontends via the `/registry/...` seam (`local_openhubforai_projection_api`, 9423).

**Substrate must NOT import:** `src.baltor.*` (Teleon→Baltor is forbidden), and within itself must obey
`architecture/import_boundaries.json` (no upward imports: `runtime`/`processors` must not import
`web`/`demos`/`scripts.baltor_admin_demo_server`).
Sources: `architecture/portfolio_dependency_law.json`, `architecture/import_boundaries.json`.

---

## 8. Related reading

- `_repos/shared-backend-components/context/blackbox.md` — the internal view of this component.
- `_repos/_shared/ARCHITECTURE-MAP.md` — the six components + the seam table.
- `_repos/_shared/STANDARDS.md` — the eight cross-component laws.
- `architecture/portfolio_dependency_law.json` (proof `scripts/check_portfolio_dependency_law.py`),
  `architecture/import_boundaries.json` (proof `check_import_boundaries_manifest.py`).
- `docs/INTEGRATION-BIBLE.md` — the seam contract; `docs/strategy/teleon-baltor-openhubforai-portfolio.md`
  — the brand + dependency architecture + hosting topology.
