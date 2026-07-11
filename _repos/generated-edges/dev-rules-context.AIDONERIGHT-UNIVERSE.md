# AIDONERIGHT-UNIVERSE — how `dev-rules-context` interfaces with the rest of the AI Done Right org

> Generated from `contracts/surface-registry.json` by the edge-graph-generator — **single source, do
> not hand-edit** (regenerate after any registry change). **Self-contained:** with only this repo open,
> it tells you every surface in the org, what each exposes, and HOW to reach it.

> _Consume a neighbor ONLY via its published interface listed here — never read/import its source._

## This repo — `dev-rules-context` (`aidoneright-dev-rules-context`)
- **Layer:** devkit · **Kind:** rules_and_context
- **Role:** the standards + gates + shared-context TEMPLATE repo (this template-repo). Inherited by every other repo; holds the naming law, multi-path methodology, verification laws, the surface registry, and the portable checkers.
- **How others interface with you:** Inherited standards + shared context — present in every repo, read as law; not a running service.

**What you expose** (your published interface — keep it stable):
- `standards/*` — The eight inherited org laws (multi-path, globally-unique naming, candidate/truth boundary, change-verification, verify-the-verifier, no-magic-values, lossless-distillation, archival).
- `contracts/surface-registry.json` — The single source of truth for every surface: its exposes, allowed may_depend_on edges, and forbidden edges.
- `tools/check_*.py` — Portable enforcement gates every repo runs (cross-repo dependency law, interface-manifest consistency).
- `_shared/*` — Common truth every repo references: the glossary, architecture map, single-source config constants, and the id-minting authority.

## What you may consume — and exactly how
- (nothing — this repo consumes no other surface)

## Who consumes you (keep your interface stable for them)
- `aidevobserver` (`aidoneright-aidevobserver`)
- `aidoneright` (`aidoneright-parent`)
- `api-endpoint-wrappers` (`aidoneright-api-endpoint-wrappers`)
- `baltor` (`aidoneright-baltor`)
- `business-context` (`aidoneright-business-context`)
- `context-injection` (`aidoneright-context-injection`)
- `edge-graph-generator` (`aidoneright-edge-graph-generator`)
- `fundraising` (`aidoneright-fundraising`)
- `openhubforai` (`aidoneright-openhubforai`)
- `pitch-decks` (`aidoneright-pitch-decks`)
- `scraping` (`aidoneright-scraping`)
- `shared-backend-components` (`aidoneright-shared-backend-components`)
- `teleon` (`aidoneright-teleon`)
- `yc-applications` (`aidoneright-yc-applications`)

## Forbidden edges (the boundary law — never do these)
- **→ shared-backend-components** — the rules/standards repo depends on nothing — it is inherited, not a consumer

## The whole universe (every surface — what it is, how to reach it)

| Surface | Repo | Layer | Interface | One-line role |
|---|---|---|---|---|
| `aidevobserver` | aidoneright-aidevobserver | product | seam `/api/observer/` | the AI-USAGE layer — session/AI-usage coaching (not code review); MCP + CLI + extension + app + local service. |
| `aidoneright` | aidoneright-parent | product | site | the PARENT BRAND / portfolio umbrella (aidoneright.dev). References every surface's PUBLIC interface for the portfolio… |
| `api-endpoint-wrappers` | aidoneright-api-endpoint-wrappers | library | port | DEV TOOL — reusable adapters that wrap third-party / local / cloud API endpoints behind stable PORTS (agnostic-adapter… |
| `baltor` | aidoneright-baltor | product | seam `/api/baltor/` | the applied, customer-facing CONTEXT product, powered by Teleon (a TENANT). Governance / provenance / signed facts /… |
| `business-context` | aidoneright-business-context | business | read | CONTEXT repo — business notes, decisions (with warrants), activity log, analytics, MCP server configs, meeting/strategy… |
| `context-injection` | aidoneright-context-injection | library | port | DEV TOOL — reusable context assembly / packing / memory / prompt-composition tooling (context packs, headroom… |
| `dev-rules-context` **← you** | aidoneright-dev-rules-context | devkit | inherit | the standards + gates + shared-context TEMPLATE repo (this template-repo). Inherited by every other repo; holds the… |
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

