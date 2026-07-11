# aidevobserver — `aidoneright-aidevobserver`

The **AI-usage layer** of the AI Done Right portfolio. Staged folder for the future
`aidoneright-aidevobserver` repo.

**North star (one line):** watch how intelligence is used in real AI coding sessions and coach on it
(session **review**, not code review), surfacing every finding as governed **candidate** advice a human
triages — never as served truth.

## What this repo is

AIDevObserver reviews the AI **usage / session**, **NOT the code** — it is not a PR / diff / code-correctness
reviewer. It works in two moments:

- **POST** — a post-session review report (the lead adoption wedge, non-invasive).
- **WHILE** — intra-session pop-ups (reinvention · adversarial question · cheaper path · token waste)
  governed by a global interruption budget and graduated modes, failing open to silence.

The engine is a thin set of subsystems around **one router** over a typed intervention taxonomy. Its detection
families ground against a knowledge graph (dependency / product-distance / repo-similarity / code-genome) and
the shared Backend registry substrate (primitives, primitive templates, task/pipeline templates, reuse cards,
source/provenance rows), so "this already exists" is answered from real assets. Everything it emits carries
`serves_truth=false`; it proposes, and Teleon promotion + Baltor governance dispose. The core detail — modules,
surfaces, current honest state — lives in `context/blackbox.md`.

## Layout

```
_repos/aidevobserver/
├── README.md            ← you are here: what this repo is + how to work in it
├── CLAUDE.md            ← the agent operating manual (fill-in of the dev-rules-context template)
├── EDGES.md             ← generated cross-repo edge contract (the only cross-repo context needed)
└── context/
    ├── blackbox.md      ← what this component internally is / owns / does (the standalone briefing)
    ├── edges.md         ← how it connects to the other five components + _shared (compat contract)
    ├── codex/           ← the AIDevObserver docex set (surfaces overview, product/copy guide,
    │                       trigger + primitive-search architecture, launch/alpha plans, roadmap, …)
    └── design/          ← the surface design context (aidoneright-claude-design)
```

## How to work in this repo

1. Read [`CLAUDE.md`](CLAUDE.md) — the operating manual: identity, the inherited laws (linked into the
   sibling `dev-rules-context` repo), and the AIDevObserver-specific invariants + seam.
2. Read [`context/blackbox.md`](context/blackbox.md) first (what this component is), then
   [`context/edges.md`](context/edges.md) (how it connects). Go deeper via `context/codex/` and
   `context/design/`.
3. Read [`EDGES.md`](EDGES.md) for the cross-repo contract before touching anything that crosses a boundary.
4. The **laws** are not copied here — they live in
   [`../dev-rules-context/standards/`](../dev-rules-context/standards/README.md) and the common truth in
   [`../dev-rules-context/_shared/`](../dev-rules-context/_shared/). Link to them; never fork them.

A Claude Code session opening ONLY this folder can work it fully from `CLAUDE.md` + `context/` + `EDGES.md`.

### The invariants you must not break

- Reviews AI **usage / the session**, never the code.
- **Candidate-only:** every finding / seam / CLI / MCP response carries `serves_truth=false`.
- **Read-only + privacy:** never store or republish raw transcripts, absolute local paths, or evidence
  snippets; footgun evidence stays redacted; `consent.py` gate #0 governs retention.
- **Dependency law:** the engine lives in `src/teleon/` → it IS Teleon for the import checker and must
  **never import Baltor**; it may consume OpenHubForAI + the Backend registry.
- **Restraint:** the global interruption budget + graduated modes + per-type floors are load-bearing — the
  product is the threshold.
- **Serve the built-out app** (`web/aidevobserver/`) via the showcase over the seam; never a skinny
  replacement server.

## Edges (from `EDGES.md`)

- **This repo's role:** the AI-usage layer — session / AI-usage coaching (not code review); MCP + CLI +
  extension + app + local service.
- **This repo exposes:** `/api/observer`, session-review, mcp-server, cli, extension. **Seam:**
  same-origin `/api/observer/...`; registry id `observer_runtime`; cloud override `OH_SEAM_OBSERVER_BASE`;
  strip `""` (full-path forward); port single-sourced from `architecture/local_service_registry.json`.
- **You may consume (published interface only):**
  - `dev-rules-context` (`aidoneright-dev-rules-context`) → `standards/*`,
    `contracts/surface-registry.json`, `tools/check_*.py`, `_shared/*`.
  - `shared-backend-components` (`aidoneright-shared-backend-components`) → registry, primitives, primitive
    templates, codegraph, eval-harness, storage-tiers, credential-plane (the reinvention-grounding + reuse-card source).
  - `openhubforai` (`aidoneright-openhubforai`) → CapabilityTask spec, task/pipeline templates,
    eval harnesses, conformance tests, and skills.
- **Who consumes you (keep stable):** `aidoneright` (the parent).

Consume a neighbor ONLY via its exposed interface listed in `EDGES.md` — never read or import its source.
