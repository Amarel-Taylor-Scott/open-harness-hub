# AIDONERIGHT-UNIVERSE — how `aidoneright` interfaces with the rest of the AI Done Right org

> Generated from `contracts/surface-registry.json` by the edge-graph-generator — **single source, do
> not hand-edit** (regenerate after any registry change). **Self-contained:** with only this repo open,
> it tells you every surface in the org, what each exposes, and HOW to reach it.

> _Consume a neighbor ONLY via its published interface listed here — never read/import its source._

## This repo — `aidoneright` (`aidoneright-parent`)
- **Layer:** product · **Kind:** parent_brand
- **Role:** the PARENT BRAND / portfolio umbrella (aidoneright.dev). References every surface's PUBLIC interface for the portfolio site; owns no product logic.
- **How others interface with you:** The portfolio site; it references other surfaces' PUBLIC interfaces for display/routing only.

**What you expose** (your published interface — keep it stable):
- `portfolio-site` — The parent brand site (aidoneright.dev) referencing every surface's public face.
- `brand` — The parent brand system ('AI, done right.') and design family.

## What you may consume — and exactly how

### `dev-rules-context` (`aidoneright-dev-rules-context`) — rules_and_context
- **How to interface:** Inherited standards + shared context — present in every repo, read as law; not a running service.
- **Its role:** the standards + gates + shared-context TEMPLATE repo (this template-repo). Inherited by every other repo; holds the naming law, multi-path methodology, verification laws, the surface registry, and the portable checkers.
- **You may use:**
    - `standards/*` — The eight inherited org laws (multi-path, globally-unique naming, candidate/truth boundary, change-verification, verify-the-verifier, no-magic-values, lossless-distillation, archival).
    - `contracts/surface-registry.json` — The single source of truth for every surface: its exposes, allowed may_depend_on edges, and forbidden edges.
    - `tools/check_*.py` — Portable enforcement gates every repo runs (cross-repo dependency law, interface-manifest consistency).
    - `_shared/*` — Common truth every repo references: the glossary, architecture map, single-source config constants, and the id-minting authority.

### `teleon` (`aidoneright-teleon`) — product_runtime
- **How to interface:** Call its HTTP seam same-origin (`/api/teleon/…`); cloud base `OH_SEAM_TELEON_BASE`, a local port in dev. Seam: `/api/teleon/`.
- **Its role:** the purpose-driven, eval-gated, self-adaptive compute RUNTIME SaaS. Owns PurposeTask/CapabilityTask, runtime selection, evidence ledger, promotion/policy gates, adapters, the assurance dashboard. Reference implementation of the open spec.
- **You may use:**
    - `/api/teleon` — The runtime SaaS API: PurposeTask submission, runtime selection, and receipts.
    - `PurposeTask` — The core runtime object (formal synonym CapabilityTask): a purpose + guardrails compiled to an optimized, verified execution graph.
    - `runtime-selector` — Cost-ordered, deterministic-first selection of the execution path, bounded by the org guardrail policy.
    - `evidence-ledger` — The append-only receipt store recording every run's cost, accuracy, and decisions.
    - `promotion-gate` — The proof-gated boundary that promotes a candidate to served truth — never self-promoted.
    - `assurance-portal` — The customer-facing Capability Assurance Portal (runtime health, receipts, policy).

### `baltor` (`aidoneright-baltor`) — product_applied
- **How to interface:** Call its HTTP seam same-origin (`/api/baltor/…`); cloud base `OH_SEAM_BALTOR_BASE`, a local port in dev. Seam: `/api/baltor/`.
- **Its role:** the applied, customer-facing CONTEXT product, powered by Teleon (a TENANT). Governance / provenance / signed facts / CDC is the moat.
- **You may use:**
    - `/api/baltor` — The applied context-product API: customer workflows over the governed context engine.
    - `context-engine` — The six-stage context pipeline + verification rail that wraps memory/RAG/observability providers.
    - `governance` — Provenance, signed facts, and CDC/revocation — the external moat; serves_truth=true only after review.
    - `customer-workflows` — Vertical, customer-facing capability workflows (e.g. sanctions screening, provider directory).
    - `receipts` — Per-answer provenance receipts: source handles, lineage, and verification status.

### `aidevobserver` (`aidoneright-aidevobserver`) — product_usage_layer
- **How to interface:** Call its HTTP seam same-origin (`/api/aidevobserver/…`); cloud base `OH_SEAM_AIDEVOBSERVER_BASE`, a local port in dev. Seam: `/api/observer/`.
- **Its role:** the AI-USAGE layer — session/AI-usage coaching (not code review); MCP + CLI + extension + app + local service.
- **You may use:**
    - `/api/observer` — The AI-usage layer API: session/AI-usage coaching (not code review).
    - `session-review` — Consented-session review that mines AI-coding sessions into tools, research-queue items, and registry candidates.
    - `mcp-server` — The Claude Code MCP connection that surfaces live reuse hints.
    - `cli` — The command-line client for session review and primitive refresh.
    - `extension` — The editor/browser extension client.

### `openhubforai` (`aidoneright-openhubforai`) — open_spec
- **How to interface:** Consume the open CapabilityTask spec + conformance tests; its backend also answers a same-origin seam.
- **Its role:** the OPEN ecosystem + the open CapabilityTask spec (CTS). The neutral home of the standard; stays product-neutral.
- **You may use:**
    - `capabilitytask-spec` — The open CapabilityTask Spec (CTS): the neutral, portable definition of an executable capability.
    - `eval-harnesses` — Open evaluation harnesses for scoring capability lift in the ecosystem.
    - `task-templates` — Reusable open task/pipeline templates.
    - `conformance-tests` — Conformance suites that prove an implementation meets the CTS.
    - `skills` — The open library of composable skills/Actions.

## Who consumes you (keep your interface stable for them)
- `fundraising` (`aidoneright-fundraising`)
- `pitch-decks` (`aidoneright-pitch-decks`)
- `yc-applications` (`aidoneright-yc-applications`)

## The whole universe (every surface — what it is, how to reach it)

| Surface | Repo | Layer | Interface | One-line role |
|---|---|---|---|---|
| `aidevobserver` | aidoneright-aidevobserver | product | seam `/api/observer/` | the AI-USAGE layer — session/AI-usage coaching (not code review); MCP + CLI + extension + app + local service. |
| `aidoneright` **← you** | aidoneright-parent | product | site | the PARENT BRAND / portfolio umbrella (aidoneright.dev). References every surface's PUBLIC interface for the portfolio… |
| `api-endpoint-wrappers` | aidoneright-api-endpoint-wrappers | library | port | DEV TOOL — reusable adapters that wrap third-party / local / cloud API endpoints behind stable PORTS (agnostic-adapter… |
| `baltor` | aidoneright-baltor | product | seam `/api/baltor/` | the applied, customer-facing CONTEXT product, powered by Teleon (a TENANT). Governance / provenance / signed facts /… |
| `business-context` | aidoneright-business-context | business | read | CONTEXT repo — business notes, decisions (with warrants), activity log, analytics, MCP server configs, meeting/strategy… |
| `context-injection` | aidoneright-context-injection | library | port | DEV TOOL — reusable context assembly / packing / memory / prompt-composition tooling (context packs, headroom… |
| `dev-rules-context` | aidoneright-dev-rules-context | devkit | inherit | the standards + gates + shared-context TEMPLATE repo (this template-repo). Inherited by every other repo; holds the… |
| `edge-graph-generator` | aidoneright-edge-graph-generator | library | generate | META DEV TOOL — reads the surface-registry + every repo's published interface.json and GENERATES the repo-to-repo edge… |
| `fundraising` | aidoneright-fundraising | business | read | CONTEXT repo — go-to-market + fundraising strategy, investor outreach, round planning, market sizing. The money/market… |
| `openhubforai` | aidoneright-openhubforai | product | spec | the OPEN ecosystem + the open CapabilityTask spec (CTS). The neutral home of the standard; stays product-neutral. |
| `pitch-decks` | aidoneright-pitch-decks | business | read | CONTEXT repo — investor pitch decks, investment narrative, one-pagers, traction/metrics evidence. The outward-facing… |
| `scraping` | aidoneright-scraping | library | port | DEV TOOL — reusable scraping / browser-automation / stealth-fetch toolkit (the descent ladder: API -> browser ->… |
| `shared-backend-components` | aidoneright-shared-backend-components | substrate | seam `/registry/` | the SUBSTRATE every product consumes — the primitive/component registry + factory + catalog, codegraph, naming planes… |
| `teleon` | aidoneright-teleon | product | seam `/api/teleon/` | the purpose-driven, eval-gated, self-adaptive compute RUNTIME SaaS. Owns PurposeTask/CapabilityTask, runtime selection… |
| `yc-applications` | aidoneright-yc-applications | business | read | CONTEXT repo — Y Combinator (and other accelerator) application drafts, answers, founder/video scripts, readiness… |

## How interfacing works (the rules that keep it safe)
- **Consumption rule:** surface A may reference surface B's capabilities ONLY through B's interface.json (name + version + exposes). Importing B's source from A is a forbidden cross-repo edge, caught by the checker.
- **Dependency law:** Dependency direction is preserved across repos: Baltor -> Teleon -> OpenHubForAI, never the reverse. Every product surface may consume SharedBackendComponents (the substrate) and the OpenHubForAI open spec. A surface consumes another ONLY via its published interface.json (a versioned contract), never its internals. dev-rules-context is inherited by every repo (standards + gates) and depends on nothing.
- **Seams are same-origin:** call `/api/<surface>/…` (or `/registry/` for the substrate), never a
  hardcoded host; the cloud base is `OH_SEAM_<SURFACE>_BASE`, a local port in dev.
- **Libraries and context are not seams:** a `dev_tool` is invoked behind a port; a `context` repo is
  read as grounding — neither is called over HTTP nor imported as source.

