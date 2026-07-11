# AIDevObserver — the edges view (how it connects to the other five + `_shared`)

**What this file is.** The compatibility contract for AIDevObserver as it moves toward being managed
separately: its inbound/outbound interfaces, its seam, its concrete dependencies (what it imports/
consumes from others, what it exposes to others), and the invariants that must hold so the other five
components keep working. Every claim links to an existing repo source; the source wins on conflict.
Companion file: `blackbox.md` (what this component internally is/does).

The six components (canonical map: `_repos/_shared/ARCHITECTURE-MAP.md`): AI Done Right (parent),
Teleon (runtime SaaS — efficiency), Baltor (applied product — truth), OpenHubForAI (open ecosystem +
spec), **AIDevObserver (this — the AI-usage layer)**, Backend (registry/primitives/service-plane).

---

## The dependency law (honor it — enforced, not prose)

The portfolio law (machine source `_repos/shared-backend-components/architecture/portfolio_dependency_law.json`, proof
`_repos/shared-backend-components/scripts/check_portfolio_dependency_law.py`) governs the three **package** layers:

```
Baltor ──▶ Teleon ──▶ OpenHubForAI (OpenHarnessHub)      never the reverse
```

- Baltor depends on Teleon (tenant `baltor-internal`) and may depend on OpenHubForAI.
- Teleon may consume OpenHubForAI. **Teleon must NEVER import Baltor.**
- OpenHubForAI depends on neither (must never import Teleon or Baltor).

**Where AIDevObserver sits in that law — the load-bearing subtlety.** AIDevObserver is not (yet) its
own package layer in the law; its engine code physically lives **inside `src/teleon/`**
(`src/teleon/observer/`, `src/teleon/knowledge/`, `src/teleon/economics/`). Therefore, for the import
checker, AIDevObserver's engine **IS Teleon** and inherits Teleon's constraints:

- **The engine must NEVER import Baltor** (it is `src/teleon/` code → the forbidden `teleon → baltor`
  edge). AIDevObserver observes AI-coding sessions generically; it must stay reusable infrastructure,
  not a Baltor feature. Source: `_repos/shared-backend-components/architecture/portfolio_dependency_law.json` → `forbidden_edges`.
- The engine **may consume OpenHubForAI** artifacts (catalog components, primitive/task templates, skills, evals) —
  that direction is allowed. AIDevObserver also has its own cross-repo surface contract allowing it to consume
  `openhubforai` plus the shared Backend registry substrate. Source: same file → `layers.teleon.may_depend_on =
  ["openhubforai"]`; `_repos/dev-rules-context/contracts/surface-registry.json` → `surfaces.aidevobserver.may_depend_on`.
- `_repos/shared-backend-components/scripts/observer_local_service.py`, `_repos/shared-backend-components/scripts/aidevobserver_mcp_server.py`, and
  `editor/aidevobserver-vscode/` are **tooling**, not a brand package — the same convention noted in
  the law's migration lessons ("scripts is tooling, not a brand layer"). They may reach the engine but
  must not create a `teleon → baltor` import edge either.
  Source: `_repos/shared-backend-components/architecture/portfolio_dependency_law.json` (`migration_status.extracted_so_far` notes on
  `scripts.runtime` being tooling, not a brand edge).

**Consequence for separate management.** If AIDevObserver is ever extracted to its own package
(`src/aidevobserver/`), it would sit as a **peer/consumer of Teleon**, and the law would need a new
row; until then, treat its code as Teleon for the dependency proof. Do not add a Baltor import to any
`src/teleon/observer/**` file.

---

## The seam (the standardized frontend ↔ backend contract)

The AIDevObserver web frontend never hardcodes a host. It calls the same-origin seam
**`/api/observer/...`**; the showcase rewrites it to the real backend.

| Frontend calls (same origin) | Backend service | Local registry id | Cloud override env |
|---|---|---|---|
| `/api/observer/...` | AIDevObserver session-review backend | `observer_runtime` | `OH_SEAM_OBSERVER_BASE` |

Registration facts (grounded, not guessed):
- The seam is wired in `_repos/shared-backend-components/scripts/showcase/server.py` (line ~128–130): `observer = _local_service_port("observer_runtime")` → `("/api/observer/", "", _seam_base("OH_SEAM_OBSERVER_BASE", observer))`. The **strip is `""`** — the FULL path is forwarded, so the service answers both `/review` and `/api/observer/review`.
- The backend is registered as `observer_runtime` in `_repos/shared-backend-components/architecture/local_service_registry.json` (line ~1094), display "AIDevObserver session-review backend"; the SPA process is `aidevobserver_app` (line ~356). The **port is single-sourced from that registry** and drift-gated by the proof — never hardcode it.

Source: `_repos/_shared/ARCHITECTURE-MAP.md` (seam table); `docs/INTEGRATION-BIBLE.md` §2;
`_repos/shared-backend-components/scripts/showcase/server.py`; `_repos/shared-backend-components/architecture/local_service_registry.json`;
`_repos/shared-backend-components/scripts/observer_local_service.py` docstring.

**Seam contract to preserve.** Every `/api/observer/*` response carries `serves_truth=false`; the
backend is read-only for review and stores only optional metadata-only outcomes. A new
frontend↔backend integration = a service-plane service + a seam + `fetch('/api/observer/...')`, never
a hardcoded host. Source: `CLAUDE.md` (Surfaces / INTEGRATION-BIBLE §4);
`docs/codex/aidevobserver-systems-registries-surfaces-overview.md` (Operating Rules).

---

## Outbound edges — what AIDevObserver consumes from the other components

### → Backend (registry / primitives / service-plane) — heaviest dependency

- **Registry payload breadth.** AIDevObserver consumes the shared registry as a broad capability substrate,
  not a narrow component list: primitives, primitive templates/cards, component records, task/pipeline
  templates, source/provenance rows, embeddings, codegraph views, eval-harness pointers, storage tiers, and
  credential-plane affordances. These are the assets behind reuse search, primitive refresh, and candidate
  mining. Source: `_repos/dev-rules-context/contracts/surface-registry.json` → `capability_catalog.registry`;
  `_repos/shared-backend-components/architecture/primitive_registry_builder_contracts.json`.
- **Reinvention grounding.** The reinvention module wraps `src/teleon/registry/reinvention_guard.py`
  and searches the registry federation to answer "this already exists." The moat is that grounding.
  Source: memory `observer-spotter-router-and-taxonomy`; memory `reinvention-guard-product-2026-06-23`.
- **Reuse-card / candidate search.** `src/teleon/observer/registry_search.py` is the single adapter
  over local-registry search + outcome-memory ranking + reuse-card shaping; the pgvector/global
  primitive service plugs in behind it later without changing review/UI surfaces.
  Source: `src/teleon/observer/registry_search.py` docstring.
- **Knowledge-graph views** (`src/teleon/knowledge/`) read backend registries — global repository
  registry, package/dependency seed, product-similarity registry, `component_search` embeddings — as
  **views over existing assets**, not new stores. Source: memory `observer-spotter-router-and-taxonomy` (batch 2/3).
- **Behavioral heuristics** are single-sourced in `_repos/shared-backend-components/architecture/behavioral_heuristics.json` (owner
  Registry #94); the modules read them (no magic values). Source: same memory;
  `_repos/shared-backend-components/architecture/behavioral_heuristics.json`.
- **Local service registry** — the backend port for `observer_runtime` comes from
  `_repos/shared-backend-components/architecture/local_service_registry.json`. Source: `_repos/shared-backend-components/scripts/observer_local_service.py` docstring.

### → OpenHubForAI (allowed by the law)

AIDevObserver searches the OpenHubForAI catalog families (primitive/task templates, harnesses, pipelines,
rule packs / **If Statements**, knowledge packs / **Knowledge Corpus**, tools, personas, adapters, rubrics) to find
existing reusable components before new code is written, and it distills accepted patterns into
candidate OpenHubForAI artifacts (benchmark case / component definition / template / harness).
Source: `docs/codex/aidevobserver-systems-registries-surfaces-overview.md` (Registry Families;
AIDevObserver → OpenHubForAI Bridge).

### → Teleon (the engine's home + the compiler it explains)

Because the engine lives in `src/teleon/`, this is an internal edge, but conceptually AIDevObserver is
the **adoption wedge / front-end for the Teleon engine** (descent + reinvention guardrail + registry
federation + economics). It explains Teleon routes using Teleon's artifact vocabulary
(PrimitiveRecord → CandidateBundle → PlanDelta → RemixSurface → PlanLock → Ledger → ProofBundle →
PromotionRecord) and turns accepted findings into Teleon registry candidates that improve future route
search. Source: memory `observer-is-session-review-not-code-review`;
`docs/codex/aidevobserver-systems-registries-surfaces-overview.md` (Canonical Teleon Artifact Chain;
AIDevObserver → Teleon Bridge).

### → Backend session sources (read-only capture)

Session discovery reads Claude Code / Codex transcripts from `~/.claude/projects/<encoded-cwd>/*.jsonl`
(`OBSERVER_PROJECTS_DIR` override for tests) — read-only, never republished.
Source: `src/teleon/observer/sessions.py`; memory `observer-spotter-router-and-taxonomy` (batch 4).

---

## Inbound edges — what AIDevObserver exposes to the other components

### The `/api/observer/*` HTTP surface (consumed by any frontend / agent)

`GET /sessions`, `POST /review`, `POST /live`, `POST /agentic`, `POST /outcome`, `GET /outcomes`,
`GET /registry/search`, `GET/POST /config`, `POST /ide/plan`, `POST/GET /ide/session[s]`, `GET /health`.
All read-only for review; `serves_truth=false` on every response.
Source: `_repos/shared-backend-components/scripts/observer_local_service.py` docstring.

### The CLI + MCP + editor contracts (consumed by terminals / agents / editors)

- CLI: `python3 -m src.teleon.observer.cli list|review|live` (the terminal/editor contract).
- MCP: `_repos/shared-backend-components/scripts/aidevobserver_mcp_server.py` tools `list_sessions` / `review_session` / `live_review`
  (stdlib-only JSON-RPC over stdio; `claude mcp add aidevobserver -- python3 .../aidevobserver_mcp_server.py`).
- Editor: `editor/aidevobserver-vscode/` VSIX (runs in VS Code and Cursor) shells to the CLI.
Source: `src/teleon/observer/cli.py`, `_repos/shared-backend-components/scripts/aidevobserver_mcp_server.py` docstrings; memory
`observer-spotter-router-and-taxonomy` (batch 4).

### → Teleon (the bridge, candidate-only)

AIDevObserver emits, per accepted human outcome (accept / reuse / dismiss / defer), candidate bridge
objects for Teleon: PrimitiveCandidate, TemplateCandidate, NegativeMemoryEdge, KnownGoodChain,
CompositePrimitiveCandidate, BenchmarkCase, ProofRequirement, TokenSavingsObservation. These are
**candidates**, never promoted truth. Source:
`docs/codex/aidevobserver-systems-registries-surfaces-overview.md` (AIDevObserver → Teleon Bridge).

### → Baltor (indirect ONLY — never direct)

**Baltor must consume only governed outputs.** AIDevObserver findings must NOT become Baltor served
truth directly. The only allowed path is:

```
AIDevObserver observation → Teleon proof/promotion → Baltor-governed truth decision
```

This is consistent with the law (Baltor → Teleon, never AIDevObserver-engine → Baltor). AIDevObserver
never imports Baltor and never writes Baltor truth. Source:
`docs/codex/aidevobserver-systems-registries-surfaces-overview.md` (AIDevObserver → Baltor Bridge);
`_repos/shared-backend-components/architecture/portfolio_dependency_law.json`.

### → The consented-corpus flywheel (feeds the whole factory, behind gate #0)

With explicit/granular/revocable consent (`src/teleon/observer/consent.py`, gate #0), retained sessions
are mined → standardized (losslessly, 7-primitive model) → scanned (SkillScannerPort) → governed/
promoted as `serves_truth=false` candidates into the Backend registries and the research queue
(`data/research-queue/areas.jsonl`). Tenant-private patterns never become global; only consented +
anonymized + generalizable patterns promote. Status: consent gate built; miner/standardizer designed,
not fully built. Source: memory `consented-session-corpus-flywheel`;
`docs/strategy/consented-session-corpus-flywheel.md`; `src/teleon/observer/consent.py` docstring.

---

## Compatibility contracts that MUST be preserved (when managed separately)

1. **Seam stability.** Keep the `/api/observer/` seam with strip `""` (full-path forward) and the
   `observer_runtime` registry id + `OH_SEAM_OBSERVER_BASE` override; keep the port single-sourced from
   `_repos/shared-backend-components/architecture/local_service_registry.json`. Source: `_repos/shared-backend-components/scripts/showcase/server.py`; that registry.
2. **Candidate-only invariant.** Every finding and every seam/CLI/MCP response carries
   `serves_truth=false`. AIDevObserver proposes; Baltor/Teleon promotion disposes. Do not emit truth.
   Source: engine + service docstrings.
3. **Read-only + privacy invariant.** Never store/republish raw transcripts, absolute local paths, or
   evidence snippets; footgun evidence is redacted; consent gate #0 governs any retention;
   revoke-and-delete propagates. Source: `consent.py`, service docstrings; consent flywheel doc.
4. **Dependency-law invariant.** No `src/teleon/observer/**` (or knowledge/economics) file may import
   Baltor; tooling under `_repos/shared-backend-components/scripts/`/`editor/` must not create that edge either. OpenHubForAI/Teleon
   consumption is the allowed direction. Source: `_repos/shared-backend-components/architecture/portfolio_dependency_law.json` + proof.
5. **Serve the built-out app.** The web surface is `_repos/aidevobserver/frontend/` served by the showcase over the
   seam — never a skinny replacement server; a page that renders but 501s on `/api/observer/*` is not
   done. Source: `CLAUDE.md` (Surfaces); memory `surfaces-served-by-showcase-not-basic-replacements`.
6. **Restraint invariant.** The global interruption budget + graduated modes + per-type floors are
   load-bearing (the product is the threshold); do not add modules that erode it. Source: memory
   `observer-spotter-router-and-taxonomy`.

---

## Source index

- `_repos/shared-backend-components/architecture/portfolio_dependency_law.json` (+ proof `_repos/shared-backend-components/scripts/check_portfolio_dependency_law.py`) — the law.
- `_repos/_shared/ARCHITECTURE-MAP.md` — six-component map, seam table.
- `docs/INTEGRATION-BIBLE.md` — the seam contract.
- `docs/codex/aidevobserver-systems-registries-surfaces-overview.md` — surfaces, routes, seam, bridges, registry families.
- `_repos/shared-backend-components/scripts/showcase/server.py` — seam wiring; `_repos/shared-backend-components/architecture/local_service_registry.json` — `observer_runtime` registration.
- `_repos/shared-backend-components/scripts/observer_local_service.py`, `src/teleon/observer/{cli,registry_search,consent,sessions,router,review,capture,agentic,session_store}.py`, `_repos/shared-backend-components/scripts/aidevobserver_mcp_server.py`, `editor/aidevobserver-vscode/` — the surfaces + engine.
- `_repos/shared-backend-components/architecture/behavioral_heuristics.json` — Registry #94 (single-sourced patterns).
- `docs/strategy/consented-session-corpus-flywheel.md` — gate #0 flywheel.
- Memories: `observer-spotter-router-and-taxonomy`, `observer-is-session-review-not-code-review`, `consented-session-corpus-flywheel`, `reinvention-guard-product-2026-06-23`.
