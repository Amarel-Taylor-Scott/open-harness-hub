# MASFactory — verified research + Baltor positioning (2026-06-04)

## Verified (web-confirmed — verify-first; this is NOT another hallucinated tool)
- **Repo:** https://github.com/BUPT-GAMMA/MASFactory (BUPT GAMMA Lab — a known graph-ML group).
- **Paper:** arXiv **2603.06007**, "MASFactory: A Graph-centric Framework for Orchestrating LLM-Based
  Multi-Agent Systems with Vibe Graphing," submitted **2026-03-06**, ACL 2026 Demo Track; evaluated
  on 7 public benchmarks (reproduction consistency + Vibe-Graphing effectiveness).
- **What it is (confirmed):** a graph-centric MAS orchestration framework. **Vibe Graphing** =
  natural-language intent → editable workflow spec → executable graph, human-in-the-loop. **Graph
  composition** = explicit Node/Edge with subgraphs, loops, branches, composite components. **Visualizer**
  = topology preview + runtime tracing + HITL. **ContextBlock** = Memory/RAG/MCP context organized,
  auto-injected + on-demand retrieval.
- **Caveats (per the owner's analysis — CONFIRM during a bakeoff, not yet independently verified):**
  no built-in checkpointing for resume-after-crash; Visualizer appears VS Code-centric; young repo.

## Positioning for Baltor (the load-bearing decision)
**MASFactory is an authoring / Vibe-Graphing / prototyping layer. Baltor is the governed context
engine those workflows call.** Keep Baltor's canonical state (ContextObject, SourceHandle,
ContextClaim, ContextPack, ContextReceipt, FlywheelSpec, DecisionContext, ReviewRequest) the source
of truth. MASFactory helps *generate, visualize, refine, and run* workflow graphs — it is NOT the
canonical context store, the durable execution engine, the policy authority, or the queue backbone.
Durable execution stays a seam (DBOS/Temporal/Restate); MASFactory designs/prototypes the graph.

## Concept mapping (MASFactory ↔ Baltor — what already exists here)
| MASFactory | Baltor (already in this repo) |
|---|---|
| natural-language intent | a flywheel/workflow design request |
| graph design artifact | `schemas/workflow/flywheel-workflow` + `schemas/pipeline/pipeline-object` (versioned) |
| Node | a worker / agent / deterministic step (our `scripts/*` engines) |
| Edge | `schemas/queue/queue-message` dependency |
| ContextBlock | a Baltor **ContextPack** wrapped with provenance (source_handles + receipt + policy) |
| Context Adapter | the Baltor Context Gateway (`/api/context-gateway/*` on the admin server) |
| Visualizer / runtime trace | **our live event bus + `/api/events/stream` + `web/baltor/dashboard.html`** (shipped C2) |
| runtime hooks (node/edge lifecycle) | **`scripts/context_events.py` EVENT_KINDS** → publish onto the same bus |
| human request | `schemas/governance/steward-review-request` (+ our review queue) |
| final output | ContextArtifact / SwarmConsensus / ContextPackPatch (our `context_swarm` already emits these) |

The integration is unusually clean because we just built the substrate: a MASFactory node hook
(`Node.Hook.EXECUTE.BEFORE` → `component.started`, `Edge.Hook.SEND_MESSAGE` → a message event, etc.)
maps 1:1 onto `EventBus.publish(...)` → the live dashboard. ContextBlock ← `context_for_task` pack,
wrapped with source_handles + receipt_id + freshness + policy_decision.

## First bakeoff (when prioritized) — the context-object swarm graph
We already have the exact agents (`scripts/context_swarm.py`: SourceHandleValidator,
InternalEvidenceFinder, ContradictionHunter, FreshnessChecker, PolicyChecker, PackImprover,
HumanReviewRouter, SwarmConsensus). The bakeoff: author a MASFactory graph for
`context_object_swarm(object_id, purpose="verify")`, feed Baltor packs as ContextBlocks, emit node
hooks onto our EventBus (so it shows on `/dashboard`), return a SwarmConsensus + ReviewRequest +
receipt. **Pass criteria:** graph generated from NL intent; design is readable/editable JSON;
runs headless/locally; each node emits a trace event; consensus links real source handles; no raw
context dumped into memory; versionable graph artifact. **Fail:** can't run headless; artifacts not
versionable; ContextBlock can't preserve source handles; can't be wrapped by a durable engine.
**Dependency reality here:** Python 3.14, NO pip — MASFactory would need vendoring onto PYTHONPATH
(check its deps; if it needs compiled extensions it may not be installable offline → then this stays
a docs+adapter-stub track with the exact `pip install masfactory` next-command recorded, not faked).

## Comparison (verified alternatives, for the same need)
- **MASFactory** — NL→graph authoring + visualizer. → Vibe-Flywheel/Context-Wizard prototyping.
- **LangGraph (+ Studio)** — durable/stateful agent graphs, visual debug. → production-ish workflows.
- **Flowise / Langflow** — visual low-code agent builders (Langflow exposes MCP). → demos / MCP tools.
- **React Flow (xyflow) / Rete.js** — node-editor UI libs. → if Baltor builds its OWN graph editor.
- **ELK.js** — auto-layout for large graphs / runtime traces.
Recommendation: MASFactory for research/prototyping; if Baltor needs a durable, product-grade editor,
build on React Flow/Rete + ELK over our event bus, with DBOS/Temporal for durability.

## Sources
- https://github.com/BUPT-GAMMA/MASFactory
- https://arxiv.org/abs/2603.06007 · https://arxiv.org/html/2603.06007v1
- LangGraph, Flowise, Langflow, React Flow (xyflow), Rete.js, ELK.js (verified, current — pin versions on adoption).
