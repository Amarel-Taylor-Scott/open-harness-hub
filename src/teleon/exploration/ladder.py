"""src.teleon.exploration.ladder — the PURE, deterministic ESCALATION LADDER decision.

``escalation_decision(task, attempt_history, *, policy)`` looks at a task + the history of attempts already
made against it and decides the NEXT tier on the open-ended escalation ladder. It is the deterministic control
layer that detects when a task is open-ended / has no matching template / has exhausted the deterministic +
LLM first passes against the gate, and routes it to BOUNDED EXPLORATION (T3) as a CANDIDATE producer — or to a
HUMAN (T4) when even exploration fails or the task is forbidden-autonomous / an ENDS change.

THE TIERS (a task ascends only as cheaper rungs are exhausted — never skips down to a cheaper one):

  T0  TEMPLATE / KNOWN SOLUTION   a Shared-Template-Registry template (or a known-solution ref) matched →
                                  instantiate it. The cheapest rung; NO escalation, NO agent.
  T1  DETERMINISTIC PRIMITIVE     a deterministic primitive/capability covers it → run it through the gate.
  T2  LLM FIRST PASS              the runtime gate's model path (≤ max_llm_attempts) — the existing
                                  ``scripts/teleon_local_runtime`` gate with its train+holdout split.
  T3  OPEN-ENDED EXPLORATION      no template, no primitive, and the LLM passes FAILED the gate (or the task is
                                  itself an exploration/research/build-novel class) → dispatch a BOUNDED
                                  research/agent/swarm runtime (OpenClaw/Hermes-class) as a CANDIDATE. Its
                                  proposals RE-ENTER the gate. ``serves_truth=False`` always.
  T4  HUMAN ESCALATION            even exploration failed (exploration rounds exhausted), OR the task is
                                  forbidden-autonomous / an ENDS change (the explorer must never redraw the
                                  box). Always ``requires_human_boundary=True`` — never auto-dispatched.

THE DECISION IS DRIVEN BY (and ONLY by) deterministic, model-independent signals on ``task`` + ``attempt_history``:
  * did a template / known solution match? (``task.template_match`` / ``task.known_solution_ref``)
  * is a deterministic primitive available? (``task.deterministic_primitive``)
  * how many LLM attempts have been made, and did ANY pass the gate? (counted from ``attempt_history``)
  * how many exploration rounds have been spent? (counted from ``attempt_history``)
  * is the task class exploration/research/build-novel? (``task.task_class``)
  * is the change forbidden-autonomous / an ENDS change? (``task.change_type`` via the adaptation ladder)

Control logic branches on the numeric TIER + the named task-class/decision signals, never on free-text. All
thresholds are NAMED constants with a unit + rationale (no-magic-values). PURE + DETERMINISTIC: no clock, no
RNG, no I/O beyond reading the static adaptation-ladder JSON (cached) via the existing classifier.

ARCHITECTURAL LAW: Teleon-layer code — imports only stdlib + ``src.teleon`` siblings (the adaptation-ladder
classifier). Never ``src.baltor`` / ``src.openharnesshub``.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from src.teleon.experiments.ids import canonical_id
# the SINGLE SOURCE of the MEANS-vs-ENDS / forbidden-autonomous boundary (L0..L5) — we never re-encode it here.
from src.teleon.purpose_tasks.adaptation_ladder import is_ends_change, is_forbidden_autonomous

# ── tier identities (the numeric rung is what control logic branches on) ───────────────────────────────────────
#: the five rungs, lowest (cheapest) → highest (most expensive / human). The control rule branches on this
#: numeric tier, never on a tier name string — higher tier ⇒ more expensive escalation.
T0_TEMPLATE = 0          # a Shared-Template-Registry template / known-solution ref matched
T1_DETERMINISTIC = 1     # a deterministic primitive/capability covers the task
T2_LLM_FIRST_PASS = 2    # the runtime gate's LLM path (train+holdout split)
T3_EXPLORATION = 3       # OPEN-ENDED exploration: a bounded agent/research/swarm runtime as a CANDIDATE
T4_HUMAN = 4             # human escalation (exploration exhausted OR forbidden-autonomous / ENDS change)

#: the action a decision names (what the caller does next). Named so the CLI / wire-in can branch deterministically.
ACTION_INSTANTIATE_TEMPLATE = "instantiate_template"        # T0
ACTION_RUN_DETERMINISTIC = "run_deterministic_primitive"   # T1
ACTION_RUN_LLM_GATE = "run_llm_first_pass"                 # T2
ACTION_DISPATCH_EXPLORATION = "dispatch_bounded_exploration"  # T3
ACTION_ESCALATE_HUMAN = "escalate_to_human"               # T4

#: every tier's action, indexed by tier — one table so the action can never drift from its tier.
TIER_ACTIONS = {
    T0_TEMPLATE: ACTION_INSTANTIATE_TEMPLATE,
    T1_DETERMINISTIC: ACTION_RUN_DETERMINISTIC,
    T2_LLM_FIRST_PASS: ACTION_RUN_LLM_GATE,
    T3_EXPLORATION: ACTION_DISPATCH_EXPLORATION,
    T4_HUMAN: ACTION_ESCALATE_HUMAN,
}

# ── task classes (model-INDEPENDENT signal: what kind of work is this?) ────────────────────────────────────────
#: a routine task that a template / primitive / one-pass LLM is expected to cover.
TASK_CLASS_ROUTINE = "routine"
#: an open-ended class — exploration / research / build-something-novel — which has NO expected template and
#: should reach bounded exploration (T3) DIRECTLY once cheaper rungs are shown absent, not after pretending an
#: LLM first pass will close it. (It still tries T0/T1/T2 if those signals are present.)
TASK_CLASS_EXPLORATION = "exploration"
TASK_CLASS_RESEARCH = "research"
TASK_CLASS_BUILD_NOVEL = "build_novel"

#: every recognized task class (deny-by-default: an unknown class is treated as routine for tiering but flagged).
TASK_CLASSES = (TASK_CLASS_ROUTINE, TASK_CLASS_EXPLORATION, TASK_CLASS_RESEARCH, TASK_CLASS_BUILD_NOVEL)
#: the open-ended classes that, absent a template/primitive, head to T3 exploration rather than expecting an
#: LLM first pass to suffice. Single definition — the CLI + the doc read this, never a parallel literal.
EXPLORATION_TASK_CLASSES = (TASK_CLASS_EXPLORATION, TASK_CLASS_RESEARCH, TASK_CLASS_BUILD_NOVEL)

# ── named thresholds (no-magic-values: every literal carries a unit + rationale) ───────────────────────────────
#: how many LLM first-pass attempts may be spent against the gate BEFORE the task escalates to open-ended
#: exploration. Unit: attempts. Rationale: the runtime gate already runs ONE self-refine round internally per
#: run (scripts/teleon_local_runtime), so two whole gate runs (initial + one re-attempt) is a fair, bounded
#: budget before we conclude the LLM path won't close the gap and exploration is warranted. Not model-tuned.
DEFAULT_MAX_LLM_ATTEMPTS = 2
#: how many BOUNDED exploration rounds may be dispatched before the task escalates to a human. Unit: rounds.
#: Rationale: exploration is the most expensive autonomous rung; a small fixed budget (one initial + one
#: refined exploration) bounds cost and guarantees a human boundary is reached rather than an infinite loop.
DEFAULT_MAX_EXPLORATION_ROUNDS = 2

#: attempt-record ``kind`` values the ladder COUNTS (a single vocabulary — the gate/wire-in stamps these).
ATTEMPT_KIND_TEMPLATE = "template"
ATTEMPT_KIND_DETERMINISTIC = "deterministic"
ATTEMPT_KIND_LLM = "llm"
ATTEMPT_KIND_EXPLORATION = "exploration"
#: attempt-record ``outcome`` values. "passed" means the attempt CLEARED the gate; anything else did not.
OUTCOME_PASSED = "passed"


@dataclass(frozen=True)
class EscalationPolicy:
    """The deterministic knobs the ladder reads. Defaults are the named module constants; a caller may inject a
    policy to tighten/loosen the budgets (e.g. a tenant that forbids autonomous exploration entirely). PURE
    config — no behavior, no I/O."""
    max_llm_attempts: int = DEFAULT_MAX_LLM_ATTEMPTS
    max_exploration_rounds: int = DEFAULT_MAX_EXPLORATION_ROUNDS
    #: when False, a task that WOULD reach T3 is escalated to a human instead (exploration is never auto-run).
    #: Lets a cautious tenant keep the whole ladder but disable autonomous open-ended agents.
    allow_autonomous_exploration: bool = True


#: the single shared default policy instance (one definition; the CLI + callers read this, never re-build it).
DEFAULT_POLICY = EscalationPolicy()


@dataclass(frozen=True)
class TaskClass:
    """A minimal, Teleon-native view of the task the ladder needs to tier it — built ENTIRELY from
    model-independent signals so a model can never draw its own escalation map. A caller (the gate's failure
    path) projects its richer task object onto this shape; the ladder reads ONLY these fields.

    Mirrored (not imported) from the Baltor-side ResearchTask framing so Teleon never imports Baltor: the
    research/agent semantics live in ``task_class`` + ``bounds``; the dispatch step turns a T3 decision into the
    teleon-native AgentRuntimeRequest.
    """
    task_id: str
    #: free-text intent — passed through to the explorer; NEVER parsed for control decisions.
    intent: str = ""
    tenant_id: str = "unknown"
    #: the work class (routine | exploration | research | build_novel). Drives whether, absent template/primitive,
    #: the task heads to T3 directly. Unknown class → treated as routine for tiering (and ``known_class=False``).
    task_class: str = TASK_CLASS_ROUTINE
    #: True iff a Shared-Template-Registry template matched (the T0 short-circuit). The caller does the match.
    template_match: bool = False
    #: optional id of the matched template / a known-solution reference (provenance for the T0 decision).
    known_solution_ref: str | None = None
    #: True iff a deterministic primitive/capability is known to cover the task (the T1 rung).
    deterministic_primitive: bool = False
    #: the adaptation-ladder change_type this task would make, if any. An ENDS change / forbidden-autonomous
    #: change forces T4 (human) — the explorer must never redraw the box. None ⇒ a pure MEANS task.
    change_type: str | None = None
    #: caller-supplied bounds (time/steps/cost/sources) carried through to a T3 dispatch. Read-through only.
    bounds: dict = field(default_factory=dict)


@dataclass(frozen=True)
class EscalationDecision:
    """The pure decision the ladder returns: which tier, what to do, (for T3) which catalog runtime to dispatch,
    why, whether a human boundary is required, and the bounds to carry into a dispatch. ``serves_truth`` is
    pinned False — a routing decision is never truth; and any work it leads to is a CANDIDATE, never a fact."""
    decision_id: str
    task_id: str
    tier: int
    action: str
    rationale: str
    requires_human_boundary: bool
    #: for a T3 decision: the catalog runtime_id the dispatch step should request (the default exploration
    #: runtime). None for non-T3 tiers. NAMES a catalog entry — never an imported runtime.
    runtime_ref: str | None = None
    #: the bounds to carry into a T3 dispatch (merged caller bounds + the ladder's defaults). {} off T3.
    bounds: dict = field(default_factory=dict)
    #: the named task-class / signal that drove the decision (for audit + deterministic downstream branching).
    signals: dict = field(default_factory=dict)
    serves_truth: bool = False


# ── attempt-history reading (deterministic counts; the gate/wire-in stamps these records) ──────────────────────
def _count_attempts(attempt_history: list[dict] | None, kind: str) -> int:
    """How many attempts of ``kind`` have been made. Deterministic count over the caller-supplied history."""
    return sum(1 for a in (attempt_history or []) if a.get("kind") == kind)


def _any_passed(attempt_history: list[dict] | None) -> bool:
    """True iff ANY recorded attempt CLEARED the gate (outcome == passed). A passed attempt means the task is
    already solved — the ladder reports T0/T1/T2 'solved' rather than escalating."""
    return any(a.get("outcome") == OUTCOME_PASSED for a in (attempt_history or []))


def _last_passing_kind(attempt_history: list[dict] | None) -> str | None:
    """The kind of the LAST passing attempt (so a 'solved' decision reports the rung that solved it)."""
    for a in reversed(attempt_history or []):
        if a.get("outcome") == OUTCOME_PASSED:
            return a.get("kind")
    return None


def _as_task(task: "TaskClass | dict") -> TaskClass:
    """Accept a TaskClass or a plain dict (the gate's failure path may hand a dict). Deny-by-default: missing
    fields take the safe defaults (routine class, no template, no primitive)."""
    if isinstance(task, TaskClass):
        return task
    t = dict(task or {})
    return TaskClass(
        task_id=str(t.get("task_id") or t.get("id") or "unknown-task"),
        intent=str(t.get("intent") or ""),
        tenant_id=str(t.get("tenant_id") or "unknown"),
        task_class=str(t.get("task_class") or TASK_CLASS_ROUTINE),
        template_match=bool(t.get("template_match")),
        known_solution_ref=t.get("known_solution_ref"),
        deterministic_primitive=bool(t.get("deterministic_primitive")),
        change_type=t.get("change_type"),
        bounds=dict(t.get("bounds") or {}),
    )


def _decision(task: TaskClass, tier: int, rationale: str, *, requires_human: bool,
              runtime_ref: str | None, bounds: dict, signals: dict) -> EscalationDecision:
    """Build the frozen decision with a content-addressed id (deterministic: same inputs → same id)."""
    decision_id = canonical_id(
        "escal", task.task_id, str(tier), TIER_ACTIONS[tier], task.task_class,
        str(task.change_type), str(requires_human))
    return EscalationDecision(
        decision_id=decision_id, task_id=task.task_id, tier=tier, action=TIER_ACTIONS[tier],
        rationale=rationale, requires_human_boundary=requires_human, runtime_ref=runtime_ref,
        bounds=bounds, signals=signals, serves_truth=False)


def escalation_decision(
    task: "TaskClass | dict",
    attempt_history: list[dict] | None = None,
    *,
    policy: EscalationPolicy = DEFAULT_POLICY,
    exploration_runtime_id: str | None = None,
) -> EscalationDecision:
    """Decide the NEXT tier for ``task`` given ``attempt_history``. PURE + DETERMINISTIC.

    Order of evaluation (a task ascends only as cheaper signals are shown absent / exhausted):

      1. FORBIDDEN / ENDS first — a forbidden-autonomous change or an ENDS change is T4 (human), regardless of
         everything else: the open-ended explorer must NEVER redraw the box. (deny-by-default safety.)
      2. ALREADY SOLVED — if any recorded attempt PASSED the gate, report the solving rung (T0/T1/T2), no escalation.
      3. T0 — a template / known-solution matched and hasn't been tried → instantiate it.
      4. T1 — a deterministic primitive is available and hasn't been tried → run it.
      5. T2 — LLM attempts remain under the budget AND (the task is routine OR no template/primitive existed) → run
         the LLM gate path. An exploration-class task SKIPS T2 (its first pass isn't expected to close the gap).
      6. T3 — no template, no primitive, LLM budget exhausted (or the task is an exploration class) AND exploration
         rounds remain → dispatch a BOUNDED exploration runtime as a CANDIDATE. (Gated to T4 if the policy forbids
         autonomous exploration.)
      7. T4 — exploration rounds exhausted (or autonomous exploration disabled) → human escalation.

    ``exploration_runtime_id`` names the catalog runtime a T3 decision should dispatch (default: the dispatch
    module's ``DEFAULT_EXPLORATION_RUNTIME_ID`` — resolved lazily to avoid an import cycle). It NAMES a catalog
    entry; nothing is imported/executed here.
    """
    t = _as_task(task)
    history = attempt_history or []
    # resolve the default exploration runtime lazily (dispatch imports ladder; avoid a cycle at module load).
    if exploration_runtime_id is None:
        from src.teleon.exploration.dispatch import DEFAULT_EXPLORATION_RUNTIME_ID
        exploration_runtime_id = DEFAULT_EXPLORATION_RUNTIME_ID

    llm_attempts = _count_attempts(history, ATTEMPT_KIND_LLM)
    exploration_rounds = _count_attempts(history, ATTEMPT_KIND_EXPLORATION)
    known_class = t.task_class in TASK_CLASSES
    is_exploration_class = t.task_class in EXPLORATION_TASK_CLASSES
    base_signals = {
        "task_class": t.task_class, "known_class": known_class,
        "template_match": t.template_match, "deterministic_primitive": t.deterministic_primitive,
        "change_type": t.change_type, "llm_attempts": llm_attempts,
        "exploration_rounds": exploration_rounds,
    }

    # 1. FORBIDDEN / ENDS — always human, never an autonomous explorer. (Read the single-source classifier.)
    if t.change_type is not None and (is_forbidden_autonomous(t.change_type) or is_ends_change(t.change_type)):
        why = ("forbidden_autonomous" if is_forbidden_autonomous(t.change_type) else "ends_change")
        return _decision(
            t, T4_HUMAN,
            f"change_type {t.change_type!r} is {why}: an ENDS/forbidden change must be human-approved "
            f"(L5 boundary) — an open-ended explorer must never redraw the box.",
            requires_human=True, runtime_ref=None, bounds={},
            signals={**base_signals, "boundary": why})

    # 2. ALREADY SOLVED — a passing attempt means the task is done; report the rung that solved it.
    if _any_passed(history):
        kind = _last_passing_kind(history)
        solved_tier = {ATTEMPT_KIND_TEMPLATE: T0_TEMPLATE, ATTEMPT_KIND_DETERMINISTIC: T1_DETERMINISTIC,
                       ATTEMPT_KIND_LLM: T2_LLM_FIRST_PASS, ATTEMPT_KIND_EXPLORATION: T3_EXPLORATION}.get(
                           kind, T2_LLM_FIRST_PASS)
        return _decision(
            t, solved_tier,
            f"a prior {kind!r} attempt already PASSED the gate — no escalation; the task is solved at this rung.",
            requires_human=False, runtime_ref=None, bounds={},
            signals={**base_signals, "solved_by": kind})

    # 3. T0 — a template / known solution matched and hasn't been tried yet.
    template_tried = _count_attempts(history, ATTEMPT_KIND_TEMPLATE) > 0
    if t.template_match and not template_tried:
        return _decision(
            t, T0_TEMPLATE,
            f"a known template/solution matched ({t.known_solution_ref or 'template'}) — instantiate it "
            f"(cheapest rung); no agent, no escalation.",
            requires_human=False, runtime_ref=None, bounds={},
            signals={**base_signals, "known_solution_ref": t.known_solution_ref})

    # 4. T1 — a deterministic primitive is available and hasn't been tried yet.
    deterministic_tried = _count_attempts(history, ATTEMPT_KIND_DETERMINISTIC) > 0
    if t.deterministic_primitive and not deterministic_tried:
        return _decision(
            t, T1_DETERMINISTIC,
            "a deterministic primitive covers this task — run it through the gate before any model/agent.",
            requires_human=False, runtime_ref=None, bounds={}, signals=base_signals)

    # 5. T2 — the LLM gate path, IF the task is routine (an exploration class skips straight past T2) and the
    #    LLM attempt budget has room. A routine task earns its model passes before exploration is considered.
    if not is_exploration_class and llm_attempts < policy.max_llm_attempts:
        return _decision(
            t, T2_LLM_FIRST_PASS,
            f"no template/primitive solved it and {llm_attempts}/{policy.max_llm_attempts} LLM attempts used — "
            f"run the runtime gate's LLM first pass (train+holdout split) before escalating to exploration.",
            requires_human=False, runtime_ref=None, bounds={}, signals=base_signals)

    # 6. T3 — OPEN-ENDED EXPLORATION. We reach here when: the task is an exploration class with no
    #    template/primitive, OR a routine task exhausted its LLM budget without passing. Dispatch a BOUNDED
    #    exploration runtime as a CANDIDATE — unless the policy forbids autonomous exploration (→ T4).
    if exploration_rounds < policy.max_exploration_rounds:
        reached_by = ("exploration-class task with no template/primitive" if is_exploration_class
                      else f"routine task failed the gate after {llm_attempts} LLM attempt(s)")
        if not policy.allow_autonomous_exploration:
            return _decision(
                t, T4_HUMAN,
                f"{reached_by}: open-ended exploration is warranted but the policy disables autonomous "
                f"exploration — escalate to a human to authorize (or run) it.",
                requires_human=True, runtime_ref=None, bounds={},
                signals={**base_signals, "exploration_blocked_by_policy": True})
        merged_bounds = _merged_bounds(t.bounds, policy)
        return _decision(
            t, T3_EXPLORATION,
            f"{reached_by} — dispatch a BOUNDED exploration runtime ({exploration_runtime_id}) as a CANDIDATE "
            f"producer (round {exploration_rounds + 1}/{policy.max_exploration_rounds}); its proposal re-enters "
            f"the gate (serves_truth=False), never publishes.",
            requires_human=False, runtime_ref=exploration_runtime_id, bounds=merged_bounds,
            signals={**base_signals, "exploration_round": exploration_rounds + 1})

    # 7. T4 — exploration exhausted → human. Even open-ended exploration could not close the gap.
    return _decision(
        t, T4_HUMAN,
        f"open-ended exploration is exhausted ({exploration_rounds}/{policy.max_exploration_rounds} rounds spent) "
        f"without clearing the gate — escalate to a human (the autonomous ladder is done).",
        requires_human=True, runtime_ref=None, bounds={},
        signals={**base_signals, "exploration_exhausted": True})


# ── bounds (the caps a T3 dispatch carries; merged from the caller's bounds + the ladder's named defaults) ─────
#: the ladder's default exploration bounds — a small, named cap so an open-ended run can never be unbounded.
#: Unit/rationale on each. These are the LADDER's policy view; the dispatch module owns the request-shape caps.
LADDER_DEFAULT_BOUNDS = {
    "max_steps": 8,        # steps: the local emulator already caps to 8; one shared ceiling, never unbounded.
    "max_seconds": 300,    # seconds (5 min): a bounded wall-clock for one exploration round.
    "max_cost_usd": 1.0,   # USD: a per-round cost ceiling so an open-ended run can't run away on spend.
    "sandbox_required": True,  # an open-ended agent always runs sandboxed (never a generic cloud function).
}


def _merged_bounds(caller_bounds: dict, policy: EscalationPolicy) -> dict:
    """Merge the caller's bounds over the ladder defaults (caller may TIGHTEN; defaults fill the gaps). The
    result is what a T3 decision carries into the dispatch step. ``sandbox_required`` can never be turned off
    here — an open-ended explorer is always sandboxed."""
    merged = dict(LADDER_DEFAULT_BOUNDS)
    merged.update({k: v for k, v in (caller_bounds or {}).items() if v is not None})
    merged["sandbox_required"] = True  # invariant: never relax the sandbox from the ladder
    return merged


__all__ = [
    "escalation_decision", "EscalationDecision", "EscalationPolicy", "TaskClass",
    "DEFAULT_POLICY", "TASK_CLASSES", "EXPLORATION_TASK_CLASSES",
    "DEFAULT_MAX_LLM_ATTEMPTS", "DEFAULT_MAX_EXPLORATION_ROUNDS",
    "T0_TEMPLATE", "T1_DETERMINISTIC", "T2_LLM_FIRST_PASS", "T3_EXPLORATION", "T4_HUMAN", "Tier",
    "TIER_ACTIONS", "LADDER_DEFAULT_BOUNDS",
    "TASK_CLASS_ROUTINE", "TASK_CLASS_EXPLORATION", "TASK_CLASS_RESEARCH", "TASK_CLASS_BUILD_NOVEL",
    "ATTEMPT_KIND_TEMPLATE", "ATTEMPT_KIND_DETERMINISTIC", "ATTEMPT_KIND_LLM", "ATTEMPT_KIND_EXPLORATION",
    "OUTCOME_PASSED",
]

# ``Tier`` is exported as a readable alias for the integer tier (the contract uses a plain int; this name lets
# callers/docs refer to "a Tier" without a second enum that could drift from the T*_ constants above).
Tier = int
