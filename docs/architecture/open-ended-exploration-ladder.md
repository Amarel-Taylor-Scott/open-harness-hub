# Open-Ended Exploration — the escalation ladder (gate failure → bounded exploration → gate re-entry)

**Date:** 2026-06-11. **Status:** built + self-tested (the decision layer + governed dispatch; the wire-in into
the runtime gate is DESIGNED-not-applied — see "Built vs designed"). **Code:** `src/teleon/exploration/` ·
**CLI:** `python -m src.teleon.exploration --self-test` (and `--decide '<json>'`).

**Owner intent (the question this answers):** *"tasks and tools that are open ended at first — do we have a
layer for OpenClaw and Hermes type systems to pick these up? For exploration, research, or building initiatives
that don't fit any current templates or known solutions, or when an LLM first pass fails."*

The governed **ports** already existed (an agent runtime port, a bounded-research-agent port, a stateful-swarm
port, the agent-runtime catalog with OpenClaw/Hermes as candidates). What was missing was the **connective
tissue**: the deterministic DECISION layer that *detects* "this is open-ended / nothing matched / the first
passes failed the gate" and *routes* it to one of those bounded exploration runtimes — as a **candidate
producer** whose proposals re-enter the same gate. This package is that layer, and only that layer.

## The ladder (T0 → T4)

A task climbs the ladder one rung at a time; it never skips *down* to a cheaper rung it already exhausted. The
control logic branches on the **numeric tier** + named signals, never on free text.

| Tier | Name | What runs | Escalates? | Human? |
|---|---|---|---|---|
| **T0** | Template / known solution | instantiate a Shared-Template-Registry template / known-solution ref | no | no |
| **T1** | Deterministic primitive | run the deterministic primitive/capability through the gate | no | no |
| **T2** | LLM first pass | the runtime gate's model path (train+holdout split), ≤ `max_llm_attempts` | no | no |
| **T3** | **Open-ended exploration** | dispatch a **bounded** research/agent/swarm runtime (OpenClaw/Hermes-class) as a **candidate** | from T2 | no |
| **T4** | Human escalation | stop — a human decides | from T3 | **yes** |

`escalation_decision(task, attempt_history, *, policy) -> EscalationDecision` returns
`{decision_id, task_id, tier, action, rationale, requires_human_boundary, runtime_ref, bounds, signals,
serves_truth=False}`. It is **pure + deterministic** (no clock, no RNG; content-addressed ids), and reads only
model-independent signals so a model can never draw its own escalation map.

## The escalation triggers (what moves a task up a rung)

Evaluated in this order (deny-by-default safety first):

1. **Forbidden / ENDS change → T4 (human), always.** If `task.change_type` is an ENDS change or a
   `forbidden_autonomous` change (read from the single-source adaptation-ladder classifier
   `src/teleon/purpose_tasks/adaptation_ladder.py`, L0–L5), the task goes straight to a human. An open-ended
   explorer must **never** redraw the box (change purpose/permissions/criteria, remove evals/observability).
2. **Already solved → report the solving rung, no escalation.** If any `attempt_history` record has
   `outcome="passed"`, the task is done at that rung (T0/T1/T2/T3).
3. **T0** — a template/known-solution matched (`template_match`) and hasn't been tried.
4. **T1** — a deterministic primitive is available (`deterministic_primitive`) and hasn't been tried.
5. **T2** — a *routine* task with LLM-attempt budget remaining (`llm_attempts < max_llm_attempts`,
   default **2**). An *exploration/research/build-novel* class **skips T2** — its first pass is not expected to
   close the gap, so it heads to T3 directly.
6. **T3** — no template, no primitive, and either the task is an exploration class **or** a routine task
   exhausted its LLM budget without passing, with exploration rounds remaining
   (`exploration_rounds < max_exploration_rounds`, default **2**). (If the policy sets
   `allow_autonomous_exploration=False`, a would-be-T3 task is routed to T4 so a human authorizes it.)
7. **T4** — exploration rounds exhausted → a human.

Named thresholds live in `ladder.py` with a unit + rationale (`DEFAULT_MAX_LLM_ATTEMPTS=2`,
`DEFAULT_MAX_EXPLORATION_ROUNDS=2`) — no magic values. The gate's failure path stamps `attempt_history` records
`{kind: template|deterministic|llm|exploration, outcome: passed|<anything-else>}`; the ladder only *counts*
them.

## How OpenClaw / Hermes / a swarm plug in (governed candidates, never imported)

`dispatch.py::dispatch_exploration(decision, *, intent, now, …)` takes a **T3** decision and:

- builds a **bounded** `AgentRuntimeRequest` (caps: `max_steps`, `max_seconds`, `max_cost_usd`,
  `sandbox_required=True`, `allowlisted_sources`) on the **`open_ended_agent`** worker bucket;
- **delegates** to the existing `src/teleon/agents/agent_runtime_provider.dispatch_agent_request`, which selects
  the execution backend via `execution_backend_selector.select_backend → ExecutionProviderPort` and rides the
  **FleetLedger** — so this is **not** a second worker/agent framework. The `open_ended_agent` bucket is
  hard-guarded **off generic cloud functions** by the selector (it provisions onto a sandbox worker / k8s job
  unless a proof override says otherwise);
- **defaults the runtime to the offline `local_emulator@v1` invariant.** A caller may instead name a catalog
  candidate (`clawless_openclaw@candidate`, `hermes@candidate` in `architecture/agent_runtime_catalog.json`),
  but those are **catalog references only** — never imported, pip-installed, or executed here. An unprovisioned
  candidate degrades **honestly** to `status="unavailable"`, naming the `env://…` runtime ref it would need and
  the backend Teleon *would* have provisioned — **never a fabricated result**.

OpenClaw is a browser/WebContainer agent lab; Hermes is a container-sandbox open-ended agent. The
bounded-research framing (a discovery report, never a fact) is the **Baltor-side** re-entry contract in
`src/baltor/ports/research_agent_provider.py`; the Teleon-side dispatch produces the runtime-native
`AgentRuntimeRequest` and an `ExplorationProposal`. (Teleon must not import Baltor — dependency law — so the
research/agent semantics are mirrored into `TaskClass.task_class` + `bounds`, not imported.) A stateful **swarm**
(`src/teleon/ports/stateful_swarm_provider.py`) is the same story behind the same bucket: bounded workers on a
shared blackboard, output never truth.

## The re-entry: propose → gate → compile (a candidate, never a publish)

Every exploration output is an `ExplorationProposal` with `serves_truth=False`, `reenters_gate=True`, a
content-addressed **receipt**, and **provenance** (runtime + bounds + the originating `decision_id`). The
contract is: **it re-enters the same governance gate** (lift + durability + receipts), exactly like any other
candidate. It never publishes a fact.

```
open-ended task ──escalation_decision──▶ T3 ──dispatch_exploration──▶ ExplorationProposal
   (serves_truth=False, receipt, provenance)
        │
        └──re-enters──▶ runtime gate (scripts/teleon_local_runtime: train+holdout, receipts)
                                   │  promoted?
                                   ├─ yes ─▶ src/teleon/compiler.compile_capability  ──▶ CompiledRuntimeUnit
                                   │          (REFUSES a non-promoted capability — NotPromotedError)
                                   └─ no  ─▶ stays a candidate (or climbs to T3 again, then T4/human)
```

This composes cleanly with the **compiler**: the compiler `compile_capability` raises `NotPromotedError` for any
capability whose status is not `"promoted"`. So an exploration proposal can only ever become a runtime by going
*through* the gate to promotion first — the ladder's output is a candidate, the gate is the admission boundary,
and the compiler enforces it structurally. Exploration → gate → (promoted) → compiled runtime is the only path.

## Human-boundary rules

- **ENDS / forbidden changes are always T4** (`requires_human_boundary=True`) and are **never** auto-dispatched.
  `dispatch_exploration` **refuses** any non-T3 decision (`ValueError`) — a forbidden/human task physically
  cannot be turned into an agent run.
- **Exhausted exploration is T4** — when even bounded exploration can't clear the gate, a human decides.
- **A tenant may disable autonomous exploration** (`EscalationPolicy(allow_autonomous_exploration=False)`),
  which converts every would-be-T3 into a T4 human authorization while keeping the rest of the ladder.

## Built vs designed (honest)

**Built + self-tested (`python -m src.teleon.exploration --self-test`, 28 checks, deterministic across runs):**
- `ladder.escalation_decision` — the full T0–T4 pure decision (template short-circuit, LLM budget, direct-T3
  for exploration classes, forbidden/ENDS→T4, exhausted-exploration→T4, policy gate, already-solved, content-
  addressed deterministic ids).
- `dispatch.dispatch_exploration` — the governed bounded dispatch riding the agent-runtime port (so it rides
  `select_backend`/`ExecutionProviderPort`/FleetLedger), the offline-emulator default, the honest-unavailable
  candidate path, and the `ExplorationProposal` (serves_truth=False, receipt, provenance, reenters_gate).
- Proof that the package imports **no** OpenClaw/Hermes/OpenHands/Open SWE/agent SDK (source scan) and obeys the
  portfolio dependency law (`scripts/check_portfolio_dependency_law.py --self-test` passes with this package
  present).

**Designed, NOT applied (the wire-in gaps — owner-gated, single-source decisions):**
- **The runtime-gate failure-path wire-in is documented, not applied** (see next section). It is a one-call
  hook; applying it edits `scripts/teleon_local_runtime.py`, which other agents are live-editing, so it is left
  to the owner / a focused change.
- **Real candidate runtimes stay catalog-only.** Provisioning OpenClaw/Hermes for real is owner-gated (dev-only
  keys behind a gate); until then `local_emulator@v1` is the correctness invariant and candidates report
  `unavailable`. The emulator's "exploration" is a bounded deterministic placeholder — a real explorer's
  *proposals* would still re-enter the same gate unchanged.
- **The proposal does not yet auto-feed the gate's intake.** Re-entry is the contract (`reenters_gate=True` +
  receipt + provenance); an actual "submit this proposal as a candidate capability run" call is the natural
  next increment (it belongs on the Baltor governance rail / the gate's candidate intake, not in this Teleon
  decision layer).

## The one-line wire-in (documented, NOT applied)

The natural integration point is the runtime gate's **failure path** — where a run's `decision` is `candidate`
or `rolled-back` (not `promoted`) in `scripts/teleon_local_runtime.py::Runtime._run_to_completion`, right after
the `decision` is computed (around the `decision = ("promoted" if … else "candidate" if … else "rolled-back")`
line). After a failed gate run, ask the ladder what to do next:

```python
# at the gate's failure path (decision != "promoted"), build the attempt history from this run + priors,
# then ask the ladder for the next rung. Pure + offline; it dispatches nothing by itself.
from src.teleon.exploration import escalation_decision, TaskClass, dispatch_exploration
next_step = escalation_decision(
    TaskClass(task_id=cap_id, intent=spec["purpose"], task_class="routine"),
    attempt_history=[{"kind": "llm", "outcome": decision}],  # decision == "candidate"/"rolled-back"
)
# next_step.tier == T3 ⇒ a caller MAY dispatch a bounded exploration candidate (owner-gated runtime);
# next_step.requires_human_boundary ⇒ stop and route to a human. The proposal re-enters THIS gate.
```

This is a **read-only decision** call — it never runs an agent on its own; `dispatch_exploration` is a separate,
explicit step that a caller invokes only for a T3 decision (and it defaults to the offline emulator). Applying
the hook is deferred so it lands as one clean, owner-reviewed edit to the live gate file.

## Laws honored

- **propose-never-dispose / serves_truth=false** — every decision and every proposal is `serves_truth=False`;
  exploration output is a candidate that re-enters the gate, never a fact.
- **discovery ≠ trust; catalog refs only** — OpenClaw/Hermes/swarm runtimes are never imported, pip-installed,
  or executed; they are catalog entries, and an unprovisioned candidate degrades honestly.
- **ride FleetLedger, no second framework** — dispatch delegates to the existing agent-runtime port +
  execution-backend selector + ExecutionProviderPort.
- **lossless** — proposals carry a receipt + full provenance + lineage to the originating decision; nothing is
  discarded; the held-out/rejected story lives downstream on the gate's lossless layer.
- **no magic values** — every threshold/bucket/runtime id is a named constant or read from the single source
  (the agent-runtime catalog, the adaptation ladder).
- **dependency law** — Teleon-layer code; imports only stdlib + `src.teleon`; never `src.baltor` /
  `src.openhubforai`.
```
