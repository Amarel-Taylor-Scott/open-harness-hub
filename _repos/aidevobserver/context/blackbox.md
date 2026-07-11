# AIDevObserver — the blackbox view (the AI-usage layer)

**What this file is.** The standalone briefing a Claude Code web session managing ONLY the
AIDevObserver component needs: what this component is, what it internally owns and does, its
key surfaces and subsystems, its current state, and the pointers to its detailed docs. Every
claim links to an existing repo source; where a source and this summary disagree, the source
wins. Companion file: `edges.md` (how this component connects to the other five + `_shared`).

---

## One sentence

AIDevObserver is the **AI-usage layer**: it watches how intelligence is used in real AI coding
sessions and coaches on it — session **review** (not code review), AI-usage waste detection,
reinvention catching, and economics — by consuming the same registry substrate as the rest of the
portfolio and surfacing everything as governed **candidate** advice a human triages, never as served truth.
Source: `docs/codex/aidevobserver-systems-registries-surfaces-overview.md`;
`_repos/shared-backend-components/architecture/substrate_layers.json` → `layers[ai_waste_engine]` (the "AI Usage Waste Engine",
marked live); role summary in `_repos/_shared/ARCHITECTURE-MAP.md` §5.

## The one correction that frames everything

It reviews the AI **usage / session**, **NOT the code**. It is not a PR/diff/code-correctness
reviewer (that is a separate concern — `/code-review`, the codegraph change-audit). Two moments:
**POST** = a post-session review report (the lead adoption wedge), and **WHILE** = intra-session
pop-ups (reinvention / adversarial question / cheaper path / token waste) governed by a global
interruption budget and graduated modes, failing open to silence.
Source: memory `observer-is-session-review-not-code-review`; owner correction 2026-06-24.
Detailed docs (post-move, under `_repos/aidevobserver/context/`):
`docs/codex/aidevobserver-systems-registries-surfaces-overview.md`,
`docs/codex/aidevobserver-product-usage-and-copy-guide.md`.

---

## Where the code actually lives (important)

The engine is **inside the Teleon package** today — `src/teleon/observer/` and
`src/teleon/knowledge/` — not a separate `src/aidevobserver/` package. The thin HTTP backend and
the editor/MCP tooling live under `_repos/shared-backend-components/scripts/` and `editor/` (tooling, not a brand package). This is
a deliberate placement, not drift: AIDevObserver is "the operational form of the execution filter"
built on Teleon's observer subsystems, being grown toward a standalone product.
Source: `_repos/_shared/ARCHITECTURE-MAP.md` §5;
`docs/codex/aidevobserver-systems-registries-surfaces-overview.md` (Portfolio Split → code surface
`src/teleon/observer`). The dependency-law consequence of this placement is spelled out in `edges.md`.

---

## The core engine — `src/teleon/observer/`

A THIN set of subsystems around ONE router. The design principle throughout is **restraint** —
"the product is the threshold"; many modules each firing "occasionally" is a tool that won't shut
up, so a global interruption budget is the load-bearing build.
Source: memory `observer-spotter-router-and-taxonomy` (BUILT 2026-06-23, batches 1–4).

| Module | What it owns |
|---|---|
| `router.py` | The Spotter **router** over the intervention **taxonomy** — one funnel generalized: Tier-0 `plausible()` gate → wake typed modules → `ground()` → Decide, under a per-type floor + a **global interruption budget** and graduated **modes** (silent_record → review_only → advisory → active → enforcing). `route_session(events, mode)`. |
| `review.py` | The POST-SESSION reviewer, a thin front-end: **review == `route_session(mode="review_only")`** (same engine, live vs replay differ only by timeline). The non-invasive adoption wedge. |
| `capture.py` | Transcript intake — normalizes Claude Code / Codex JSONL into events (drops thinking + slash-command noise, summarizes tool_use). `from_transcript(path)`. |
| `session_store.py` | Session / event / intervention schema + the accept/reject **outcome** loop (append-only, latest-wins, content-addressed ids). The per-type `outcome_stats` = the tuning signal / moat. |
| `sessions.py` | Zero-install Claude session **discovery** (`~/.claude/projects/<encoded-cwd>/*.jsonl`; `OBSERVER_PROJECTS_DIR` override for tests). `discover_sessions(cwd)`. |
| `agentic.py` | Supervision of **autonomous agent loops** (not just human sessions): intra-run `monitor_step(...)` → alerts + a `recommend_halt` flag, and post-run `review_agentic_run(...)`. Adds loop-shape signals (stall / thrash / repeated-failure / budget / goal-drift) over the step sequence; **never kills a process** — `recommend_halt` is a recommendation. |
| `consent.py` | **Gate #0** for the consented-session corpus flywheel — default-deny, granular (per purpose × scope), revocable, time-bounded, redaction-always-required. Nothing downstream may retain a session unless this gate allows it. |
| `registry_search.py` | The shared reuse-card search adapter — HTTP/MCP/hooks all use it instead of rebuilding local-registry search / outcome-memory ranking / reuse-card shaping. It searches registry artifacts from primitives and primitive templates through task/pipeline templates, source/provenance rows, and reuse cards. Candidate-only responses. pgvector/global service can plug in behind it later. |
| `corpus.py`, `local_registry_connector.py`, `settings.py` | Corpus retention plumbing, the opt-in local repo symbol/doc/script connector, and mode/behavior settings. |

Source for the above: module docstring headers in `src/teleon/observer/*.py` (read directly);
memory `observer-spotter-router-and-taxonomy`; memory `consented-session-corpus-flywheel`.

### Registry consumption boundary

AIDevObserver consumes two registry-facing surfaces. From `shared-backend-components` it consumes the
federated Backend registry substrate: primitive records, primitive templates/cards, component records,
task/pipeline template rows, source links, provenance, embeddings, codegraph views, eval harness pointers,
and storage/credential-plane affordances. From `openhubforai` it consumes the open CapabilityTask spec,
task templates, eval harnesses, conformance tests, and skills. It uses those artifacts to answer
"this already exists," suggest cheaper/reusable paths, mine candidate primitives from sessions, and refresh
candidate search artifacts. It does **not** promote truth; every emitted observation remains
`serves_truth=false` until Teleon proof/promotion and, where relevant, Baltor governance dispose.
Source: `_repos/dev-rules-context/contracts/surface-registry.json`; `context/edges.md`.

### The intervention taxonomy (the typed modules the router wakes)

The taxonomy is now ~11 modules / 8+ types that can fire in one session — reinvention (wraps the
registry reinvention guard, federation-grounded, can ASK), footgun (regex secret/destructive, with
**redacted** evidence `<redacted match>`, can BLOCK), adversarial (question templates, notice-only),
reinvention-cluster (session-level signal sequence), oversized/duplicate-context (waste),
stack-reinvention (dependency-graph-grounded), guidance / alternative / shortcut, and
product-reinvention (latent-space distance, defaults to a deterministic lexical floor).
Patterns are single-sourced in `_repos/shared-backend-components/architecture/behavioral_heuristics.json` (owner Registry #94, no
magic values — modules read them).
Source: memory `observer-spotter-router-and-taxonomy` (batches 1–4);
`_repos/shared-backend-components/architecture/behavioral_heuristics.json`.

## The knowledge graph — `src/teleon/knowledge/`

The "computational cognition mapping" the reinvention/stack modules ground against: `dependency_graph.py`
(transitive closure / cycle / `stack_exists`), `product_distance.py` (latent-space cosine to existing
products — "overlaps 0.88 with X"), `repo_similarity.py` (semantic equivalents of an intent),
`code_genome.py` (decompose → architectural-primitive fingerprint → software similarity; a stdlib-`ast`
fork reads real symbols, tree-sitter is the higher-fidelity fork). Embedding proofs inject a
deterministic lexical floor and assert relative ordering (embedder-agnostic).
Source: memory `observer-spotter-router-and-taxonomy` (batch 2/3); `src/teleon/knowledge/*.py`.

## Economics — `src/teleon/economics/`

The cost/waste side of the AI-usage layer: `cost_model.py`, `routing_engine.py`, `provider_arbitrage.py`,
`provider_intel.py`, `economic_graph.py`, `observation_store.py`, `simulator.py`, `vertical_proof.py`.
This is what turns "you used a frontier model where a small one sufficed" into a token/cost estimate.
Source: `_repos/_shared/ARCHITECTURE-MAP.md` §5 (cites `src/teleon/economics/`); `src/teleon/economics/`.

---

## The surfaces (how the layer is reached)

AIDevObserver deliberately has **five capture/consumption surfaces** over the same engine — the
engine already existed; the surfaces were built around it (reuse, not rebuild).

1. **Web app + backend** — the SPA `_repos/aidevobserver/frontend/` (`index.html`, `aidevobserver-main.jsx`,
   `aidevobserver.css`, `examples/`) served by the showcase, backed by
   `_repos/shared-backend-components/scripts/observer_local_service.py` (a THIN HTTP front-end over the engine — review =
   `review.review_session`, live = `router.route_session`, intake = `capture.from_transcript`,
   discovery = `sessions.discover_sessions`; rebuilds nothing). Routes: `#/review`, `#/sessions`,
   `#/findings`, `#/agentic`, `#/examples`, `#/reports`, `#/developer`, `#/settings`.
   Source: `docs/codex/aidevobserver-systems-registries-surfaces-overview.md` (Current Surface);
   `_repos/shared-backend-components/scripts/observer_local_service.py` docstring.
2. **CLI** — `python3 -m src.teleon.observer.cli list|review|live [--latest|--path] [--json]`, the
   terminal/editor contract (same data the MCP server exposes).
   Source: `src/teleon/observer/cli.py` docstring.
3. **MCP server** — `_repos/shared-backend-components/scripts/aidevobserver_mcp_server.py`, a **stdlib-only** JSON-RPC 2.0 / MCP
   stdio server (no `mcp` pip dep). Tools: `list_sessions`, `review_session`, `live_review`.
   Register: `claude mcp add aidevobserver -- python3 .../scripts/aidevobserver_mcp_server.py`.
   Source: `_repos/shared-backend-components/scripts/aidevobserver_mcp_server.py` docstring.
4. **Editor extension** — `editor/aidevobserver-vscode/` (a VS Code extension; the same VSIX runs
   in Cursor via standard `vscode.*` APIs) — review webview, live-check notifications, listSessions
   QuickPick, status bar; it shells to the CLI.
   Source: memory `observer-spotter-router-and-taxonomy` (batch 4); `editor/aidevobserver-vscode/`.
5. **Pre-tool hook** — a non-blocking PreToolUse warning adapter (advisory only). Status: the live
   event-driven hook is still open (the MCP `live_review` is prospective-on-demand, not yet
   event-driven).
   Source: memory `observer-spotter-router-and-taxonomy` (STILL open list);
   `hooks/pretooluse-aidevobserver.md` referenced in `CLAUDE.md`.

### The local backend HTTP surface (`_repos/shared-backend-components/scripts/observer_local_service.py`)

Read-only for demo review; synthetic/public session text by default; stores only optional
metadata-only triage outcomes; every response carries `serves_truth=false`.

```
GET  /health (/healthz /readyz)   → {"ok": true, "service": "observer"}
GET  /sessions[?cwd=PATH]         → discover_sessions(cwd)
POST /review  {messages | transcript_path, registry_cwd?}  → governed post-session report
POST /live    {messages, mode?:"advisory"}                 → route_session → {surfaced, summary}
POST /agentic {steps, goal?, budget?, monitor?}            → agent-loop supervision
POST /outcome {session_id, intervention_id, outcome}       → append Accept/Reuse/Dismiss/Ignored
GET  /outcomes?session_id=...                              → latest outcome memory
GET  /registry/search?q=...                                → opt-in local candidate source-ref search
GET/POST /config                                           → model/harness/MCP/toggle state
POST /ide/plan · POST/GET /ide/session[s]                  → supervised browser-IDE session plans
```
Source: `_repos/shared-backend-components/scripts/observer_local_service.py` docstring (verbatim surface list). The service reads its
port from `_repos/shared-backend-components/architecture/local_service_registry.json` (single source, drift-gated).

---

## Current state (honest read — do not overclaim)

- The **engine is BUILT and gated**: router / review / capture / session_store / agentic / consent,
  ~11 modules, registry-grounded, with the five surfaces (app + CLI + MCP + editor extension + hook)
  around it. In `_repos/shared-backend-components/architecture/substrate_layers.json` the AI-Usage-Waste-Engine layer is marked
  **live**. Source: memory `observer-spotter-router-and-taxonomy`; `_repos/shared-backend-components/architecture/substrate_layers.json`.
- **All output is candidate-only** (`serves_truth=false`), read-only against code and transcripts;
  triage writes append only outcome metadata (no raw transcript text stored). Source: engine + service
  docstrings; `docs/codex/aidevobserver-systems-registries-surfaces-overview.md` (Operating Rules).
- **Consent flywheel** (retain-and-learn mode → mine sessions into tools / research queue / registry
  components): the consent gate (`consent.py`) exists; the full miner/standardizer pipeline is
  **designed and warranted, not fully built**. Source: memory `consented-session-corpus-flywheel`;
  `docs/strategy/consented-session-corpus-flywheel.md`.
- **Known open items** (from the memory's STILL-open list): the live event-driven PreToolUse hook, and
  the `outcome` write-back from a live client (the tuning loop is built; live human accept/reject
  capture is not). `_repos/shared-backend-components/scripts/check_aidevobserver_vscode_ext.py` still asserts a legacy HTTP contract —
  the clean follow-up is migrating it to the CLI contract. Source: memory `observer-spotter-router-and-taxonomy`.
- **Demos are `/demo` pages on the surfaces**, not separate sites; the replayable example pack lives
  under `_repos/aidevobserver/frontend/examples/`. Source:
  `docs/codex/aidevobserver-systems-registries-surfaces-overview.md` (Replayable Demo Pack).

---

## What a Claude Code session managing ONLY this component must not do

- Do **not** reframe it as code/PR review. It reviews AI **usage**.
- Do **not** let any surface emit `serves_truth=true`; every finding is a candidate a human triages.
- Do **not** store or republish raw transcripts, absolute local paths, or evidence snippets; footgun
  evidence stays redacted (`<redacted match>`); consent gate #0 governs any retention.
- Do **not** rebuild search/review/route logic in a surface — go through the engine
  (`src/teleon/observer/`) and `registry_search.py`.
- Do **not** create a skinny replacement server for the web surface; serve the built-out
  `_repos/aidevobserver/frontend/` app via the showcase over the `/api/observer/` seam.
  Source: `CLAUDE.md` ("Surfaces: serve the BUILT-OUT apps"); memory `surfaces-served-by-showcase-not-basic-replacements`.

---

## Detailed docs (pointers)

- `docs/codex/aidevobserver-systems-registries-surfaces-overview.md` — operator-facing map (surfaces, routes, seam, detection families, demo pack, checks).
- `docs/codex/aidevobserver-product-usage-and-copy-guide.md` — product usage + copy guide.
- `docs/codex/aidevobserver-compiled-ai-evaluation-plan.md` — the compiled-AI evaluation plan.
- `docs/codex/aidevobserver-trigger-and-primitive-search-architecture.md` — trigger + primitive-search architecture.
- `docs/codex/aidevobserver-long-session-sources-and-ingestion-plan.md` — long-session sources + ingestion.
- `docs/codex/aidevobserver-launch-readiness-and-alpha-plan.md`, `-use-case-and-primitive-roadmap.md`, `-product-usage-and-copy-guide.md`, `-context-foundry-goal-command.md`, `-claude-project-integration-template.md` — the AIDevObserver docex set. (The global `-context-foundry-loop-runbook.md` moved to `_repos/shared-backend-components/context/codex/` and now inlines the former real-primitive-launch addendum; the feedback-response/v1 plan was merged into the copy guide and the external-feedback brief archived.)
- `docs/strategy/consented-session-corpus-flywheel.md` — the consent flywheel (gate #0) design.
- Companion project pack referenced in `CLAUDE.md`: `commands/find-reuse.md`, `commands/review-session.md`, `commands/refresh-primitives.md`, `mcp/aidevobserver.md`, `hooks/pretooluse-aidevobserver.md`.
- Proof/check scripts: `_repos/shared-backend-components/scripts/check_observer_router.py`, `check_observer_review.py`, `check_observer_agentic.py`, `check_observer_capture_store.py`, `check_observer_consent.py`, `check_observer_corpus.py`, `check_observer_local_service.py`, `check_aidevobserver_mcp.py`, `check_aidevobserver_vscode_ext.py`, `check_aidevobserver_example_sessions.py`, `check_aidevobserver_session_benchmark.py`, `check_aidevobserver_compiled_ai_evaluation.py`, `check_knowledge_graph.py`.
