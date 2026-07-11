# Model-/tool-agnostic adapters — the universal scaling pattern (2026-06-21)

**Owner principle:** more LLMs and more browsers (and tools, models, runtimes) will keep arriving. So **every component
depends on an agnostic adapter/port, never a concrete provider** — and the selectable options are **populated from our
registries**. A future LLM/browser/tool drops in behind a port (or just a registry entry) with **zero component change**.
This is the future-proof property; it is made executable by a **drop-in test** (register a brand-new adapter → an
unchanged component uses it).

## The two built (the pattern to copy)
| Layer | Port | Populated from | Future-proof hook |
|---|---|---|---|
| **LLM** | `_repos/teleon/backend/src/teleon/llm_port.py` — `LLMPort`, `select_llm`, `as_callable` | model index (`_repos/shared-backend-components/architecture/model_index.json`) + lanes (`_repos/shared-backend-components/scripts/_llm_client.PROVIDERS`) | `register_llm_adapter(name, factory)`; a new model_id/lane is auto-selectable |
| **Browser** | `_repos/teleon/backend/src/teleon/research/browser_port.py` — `BrowserPort`, `select_browser` | browsing registry (`_repos/shared-backend-components/architecture/web_browsing_stack_registry.json`) | `register_browser_adapter(name, factory, engine=?)`; a chromium browser reuses Playwright automatically |

- A `model_id` selects its **provider lane**; a registry browser maps to its **engine** adapter; a declared-but-unwired
  engine returns an **honest** `NotWired` error (never a fabricated page). Routing reuses the existing inference plane
  (`_repos/teleon/backend/src/teleon/inference`) — the port never re-implements it. `serves_truth=false` throughout.
- Components consume the port, not a provider: `llm_driven_browser` and the hub engine's model port both route through
  `llm_port`/`browser_port` (no hardcoded `resolve_provider`/engine).

## Enforcement
`_repos/shared-backend-components/scripts/check_agnostic_adapters.py` (registered in the proof suite) proves: ports populate from the registries; a
model_id → its lane; a registry browser → its engine; an unwired engine is honest; and **the drop-in test** — a future
LLM + future browser register in one line and an **unchanged** `LLMBrowserDriver` drives them end-to-end.

## Extending to ALL components (the standing pattern)
Any component that depends on a swappable resource (a model, a tool, a runtime, a storage/compute backend, a search
provider) should: (1) define/consume a **port** (a small Protocol + a `select_*` factory), (2) **populate** the
selectable options from the relevant registry (the model index, the browsing/research catalogs, the tool repository,
the execution-provider factory), (3) provide a `register_*_adapter` hook, and (4) ship a **drop-in test** proving a new
adapter needs no component edit. Existing port-backed surfaces (the research catalog descent, the execution-provider
factory, the inference lanes) already follow this; the LLM + browser ports are the canonical examples to copy.
