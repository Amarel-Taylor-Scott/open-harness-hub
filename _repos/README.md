# `_repos/` — the local mirror of the future multi-repo layout

Each folder here maps to one planned GitHub repo under the new **AI Done Right** org account. The point of
this layout: a Claude Code (web) session can open **one folder** (or a few), read that repo's own context
plus its small **`EDGES.md`** digest, and be fully aware of how it connects to the others **without reading
through any of their internals**. When ready, each folder becomes its own `git init` + push.

The repo list, folder names, dependency directions, and every `EDGES.md` are **generated from one source** —
`dev-rules-context/contracts/surface-registry.json` — by `edge-graph-generator`. Change the registry, rerun
the generator, and every repo's edges update. Nothing here is hand-maintained in two places.

## The repos

<!-- BEGIN GENERATED: repo-table (build_context_indexes.py — do not hand-edit) -->
_15 surfaces · 325 context docs indexed — computed from `dev-rules-context/contracts/surface-registry.json` + the on-disk `context/` trees, never hand-counted._

| Surface → GitHub repo | Role | Depends on | Docs |
|---|---|---|---|
| **aidevobserver** → `aidoneright-aidevobserver` | the AI-USAGE layer — session/AI-usage coaching (not code review); MCP + CLI + extension +… | dev-rules-context · shared-backend-components · openhubforai | 12 |
| **aidoneright** → `aidoneright-parent` | the PARENT BRAND / portfolio umbrella (aidoneright.dev). References every surface's PUBLI… | dev-rules-context · teleon · baltor · aidevobserver · openhubforai | 5 |
| **api-endpoint-wrappers** → `aidoneright-api-endpoint-wrappers` | DEV TOOL — reusable adapters that wrap third-party / local / cloud API endpoints behind s… | dev-rules-context · shared-backend-components | — |
| **baltor** → `aidoneright-baltor` | the applied, customer-facing CONTEXT product, powered by Teleon (a TENANT). Governance /… | dev-rules-context · shared-backend-components · openhubforai · teleon | 94 |
| **business-context** → `aidoneright-business-context` | CONTEXT repo — business notes, decisions (with warrants), activity log, analytics, MCP se… | dev-rules-context | — |
| **context-injection** → `aidoneright-context-injection` | DEV TOOL — reusable context assembly / packing / memory / prompt-composition tooling (con… | dev-rules-context · shared-backend-components | — |
| **dev-rules-context** → `aidoneright-dev-rules-context` | the standards + gates + shared-context TEMPLATE repo (this template-repo). Inherited by e… | — | 3 |
| **edge-graph-generator** → `aidoneright-edge-graph-generator` | META DEV TOOL — reads the surface-registry + every repo's published interface.json and GE… | dev-rules-context | — |
| **fundraising** → `aidoneright-fundraising` | CONTEXT repo — go-to-market + fundraising strategy, investor outreach, round planning, ma… | dev-rules-context · aidoneright | 3 |
| **openhubforai** → `aidoneright-openhubforai` | the OPEN ecosystem + the open CapabilityTask spec (CTS): primitives, primitive/task templ… | dev-rules-context · shared-backend-components | 13 |
| **pitch-decks** → `aidoneright-pitch-decks` | CONTEXT repo — investor pitch decks, investment narrative, one-pagers, traction/metrics e… | dev-rules-context · aidoneright | 4 |
| **scraping** → `aidoneright-scraping` | DEV TOOL — reusable scraping / browser-automation / stealth-fetch toolkit (the descent la… | dev-rules-context · shared-backend-components · api-endpoint-wrappers | — |
| **shared-backend-components** → `aidoneright-shared-backend-components` | the SUBSTRATE every product consumes — the primitive/component/template registry + factor… | dev-rules-context | 157 |
| **teleon** → `aidoneright-teleon` | the purpose-driven, eval-gated, self-adaptive compute RUNTIME SaaS. Owns PurposeTask/Capa… | dev-rules-context · shared-backend-components · openhubforai | 31 |
| **yc-applications** → `aidoneright-yc-applications` | CONTEXT repo — Y Combinator (and other accelerator) application drafts, answers, founder/… | dev-rules-context · aidoneright | 3 |
<!-- END GENERATED: repo-table -->

`_shared/` (org goal · PMF · architecture map · glossary) sits at the root because it is the common truth
every repo references; it moves into `dev-rules-context` (or its own tiny repo) at split time — owner choice.

## How to work in one repo

1. Read `dev-rules-context/standards/README.md` (the laws) + `dev-rules-context/CLAUDE.md` (the operating template).
2. Open `<repo>/EDGES.md` — the neighbours' **published edges** and who consumes you. That is the only
   cross-repo context you need.
3. Work inside `<repo>/context/` (its blackbox). Touching an edge? Honour the contract in `EDGES.md` so the
   other repos stay compatible — the boundary is enforced by `tools/check_cross_repo_dependency_law.py`.

## The whole-graph view

`dev-rules-context/generated-edges/GRAPH.md` renders the 12-surface dependency graph (mermaid). Regenerate
everything after a registry change with:

```
python3 dev-rules-context/tools/generate_repo_edges.py --write --propagate  # regen digests + refresh every <repo>/EDGES.md
python3 dev-rules-context/tools/check_cross_repo_dependency_law.py          # proves the boundary
```

Lineage for every moved file is in `_MANIFEST.jsonl` (this staging) and `_context-reorg-lineage.jsonl`
(the earlier per-component grouping). Move-never-delete — nothing was lost.
