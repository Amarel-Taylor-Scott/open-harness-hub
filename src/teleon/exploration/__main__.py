"""src.teleon.exploration.__main__ — CLI + self-test for the open-ended exploration escalation ladder.

Usage:
  python -m src.teleon.exploration --self-test    # prove the ladder + dispatch contract (offline, deterministic)
  python -m src.teleon.exploration --decide '<json task>' [--history '<json list>']  # one decision, as JSON

The self-test PROVES (offline, no network, no candidate import):
  * a template/known-solution match SHORT-CIRCUITS at T0 (no escalation, no agent);
  * a routine task with no template/primitive runs the T2 LLM gate first, then escalates to T3 after N failed
    LLM attempts (N = the named DEFAULT_MAX_LLM_ATTEMPTS budget);
  * an exploration/research/build-novel class reaches T3 DIRECTLY (skips the LLM first pass);
  * a T3 dispatch re-enters as a CANDIDATE (serves_truth=False, reenters_gate=True, carries a receipt) on the
    offline local_emulator@v1 — no candidate executed/imported;
  * a named candidate runtime (OpenClaw/Hermes) with no runtime/credential degrades HONESTLY to
    'unavailable' (its env:// ref named, never imported / never a fabricated result);
  * forbidden-autonomous / ENDS-change tasks go to T4 (human) and are NEVER auto-dispatched;
  * a policy that disables autonomous exploration routes a would-be-T3 task to T4 (human) instead;
  * the whole thing is DETERMINISTIC (same input → byte-identical decision + proposal ids).

Offline, stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict

from src.teleon.exploration.ladder import (
    escalation_decision,
    EscalationPolicy,
    TaskClass,
    DEFAULT_MAX_LLM_ATTEMPTS,
    DEFAULT_MAX_EXPLORATION_ROUNDS,
    T0_TEMPLATE,
    T1_DETERMINISTIC,
    T2_LLM_FIRST_PASS,
    T3_EXPLORATION,
    T4_HUMAN,
    TASK_CLASS_RESEARCH,
    ATTEMPT_KIND_LLM,
    ATTEMPT_KIND_DETERMINISTIC,
    ATTEMPT_KIND_EXPLORATION,
)
from src.teleon.exploration.dispatch import (
    dispatch_exploration,
    DEFAULT_EXPLORATION_RUNTIME_ID,
    EXPLORATION_WORKER_BUCKET,
    ExplorationProposal,
)

# a fixed, injected timestamp so the self-test is deterministic (the ladder/dispatch never read the clock).
_NOW = "2026-06-11T00:00:00Z"
# a couple of failed LLM attempt records (outcome != "passed") — the gate's failure path stamps these.
_FAILED_LLM = {"kind": ATTEMPT_KIND_LLM, "outcome": "rolled-back"}
_CANDIDATE_LLM = {"kind": ATTEMPT_KIND_LLM, "outcome": "candidate"}  # below-gate but workable; still not "passed"


def _self_test() -> int:
    fails: list[str] = []

    def ck(name: str, ok: bool) -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
        if not ok:
            fails.append(name)

    # ── T0: a template / known-solution match short-circuits — no escalation, no agent ────────────────────────
    d0 = escalation_decision(TaskClass("t-tmpl", template_match=True, known_solution_ref="tmpl:date_normalizer"))
    ck("T0: a template/known-solution match short-circuits to T0 (instantiate), no human boundary",
       d0.tier == T0_TEMPLATE and d0.action == "instantiate_template"
       and not d0.requires_human_boundary and d0.runtime_ref is None)
    ck("T0: a template match never dispatches an agent (runtime_ref is None, serves_truth False)",
       d0.runtime_ref is None and d0.serves_truth is False)

    # ── T1: a deterministic primitive is tried before any model/agent ─────────────────────────────────────────
    d1 = escalation_decision(TaskClass("t-prim", deterministic_primitive=True))
    ck("T1: a deterministic primitive runs before any model/agent (T1, no escalation)",
       d1.tier == T1_DETERMINISTIC and not d1.requires_human_boundary and d1.runtime_ref is None)

    # ── T2: a routine task with no template/primitive runs the LLM gate first ────────────────────────────────
    d2 = escalation_decision(TaskClass("t-routine"))
    ck("T2: a routine task with no template/primitive runs the LLM first pass (T2) before exploration",
       d2.tier == T2_LLM_FIRST_PASS and not d2.requires_human_boundary)
    # one failed LLM attempt: still under the budget → still T2 (earns its second pass).
    d2b = escalation_decision(TaskClass("t-routine"), [_FAILED_LLM])
    ck(f"T2: one failed LLM attempt stays at T2 while under the budget (N={DEFAULT_MAX_LLM_ATTEMPTS})",
       d2b.tier == T2_LLM_FIRST_PASS)

    # ── T3: after N failed LLM attempts a routine task ESCALATES to bounded exploration ───────────────────────
    exhausted_llm = [_FAILED_LLM] * DEFAULT_MAX_LLM_ATTEMPTS
    d3 = escalation_decision(TaskClass("t-routine", intent="normalize messy citations"), exhausted_llm)
    ck(f"T3: a routine task ESCALATES to exploration after {DEFAULT_MAX_LLM_ATTEMPTS} failed LLM attempts",
       d3.tier == T3_EXPLORATION and d3.action == "dispatch_bounded_exploration")
    ck("T3: the escalation names the DEFAULT exploration runtime (local_emulator@v1) and carries bounds",
       d3.runtime_ref == DEFAULT_EXPLORATION_RUNTIME_ID
       and d3.bounds.get("sandbox_required") is True and "max_steps" in d3.bounds
       and not d3.requires_human_boundary)

    # ── T3 (direct): an exploration/research/build-novel class skips the LLM first pass ──────────────────────
    de = escalation_decision(TaskClass("t-research", task_class=TASK_CLASS_RESEARCH))
    ck("T3-direct: a research/exploration class reaches T3 DIRECTLY (skips the LLM first pass)",
       de.tier == T3_EXPLORATION and de.signals.get("task_class") == TASK_CLASS_RESEARCH)

    # ── DISPATCH: a T3 decision re-enters as a CANDIDATE on the offline emulator (no candidate executed) ──────
    prop = dispatch_exploration(d3, intent="explore the negative space", now=_NOW, tenant_id="baltor-internal")
    ck("dispatch: a T3 decision produces a CANDIDATE proposal (serves_truth=False, reenters the gate)",
       isinstance(prop, ExplorationProposal) and prop.serves_truth is False and prop.reenters_gate is True)
    ck("dispatch: the offline default ran the local_emulator@v1 invariant (status produced)",
       prop.status == "produced" and prop.runtime_id == DEFAULT_EXPLORATION_RUNTIME_ID)
    ck("dispatch: the proposal carries a content-addressed RECEIPT + provenance + lineage to the decision",
       bool(prop.receipt.get("receipt_id")) and prop.receipt.get("serves_truth") is False
       and prop.provenance.get("from_decision_id") == d3.decision_id
       and prop.provenance.get("compiled_directly") is False)
    ck("dispatch: it rode the open_ended_agent bucket (hard-guarded off generic cloud functions) + a backend",
       prop.receipt.get("worker_bucket") == EXPLORATION_WORKER_BUCKET and prop.backend is not None)
    # the candidate proposal id(s) the explorer emitted exist (the emulator produced a proposal, never a fact).
    ck("dispatch: the candidate proposal carries result id(s) — a proposal, never a served fact",
       len(prop.result_ids) >= 1 and prop.produces == "exploration_candidate_proposal")

    # ── CANDIDATE runtime honesty: a named OpenClaw/Hermes with no runtime degrades to 'unavailable' ──────────
    for cand in ("hermes@candidate", "clawless_openclaw@candidate"):
        pc = dispatch_exploration(d3, intent="x", now=_NOW, runtime_id=cand)
        ck(f"candidate {cand}: honest UNAVAILABLE (env:// ref named, never imported, never a fake result)",
           pc.status == "unavailable" and pc.serves_truth is False
           and (pc.runtime_ref or "").startswith("env://") and pc.result_ids == ())
        ck(f"candidate {cand}: even unavailable, it still SHOWS the backend Teleon would provision (honest)",
           pc.backend is not None and pc.reenters_gate is True)

    # ── FORBIDDEN / ENDS: a boundary change goes to T4 (human) and is NEVER auto-dispatched ───────────────────
    for ct in ("purpose.change", "permission.expand", "success_criteria.weaken", "eval_suite.remove"):
        df = escalation_decision(TaskClass("t-ends", change_type=ct))
        ck(f"T4: change_type {ct!r} (ENDS/forbidden) escalates to a HUMAN, never an explorer",
           df.tier == T4_HUMAN and df.requires_human_boundary is True and df.runtime_ref is None)
    # PROOF a forbidden/ENDS task is never auto-dispatched: dispatch_exploration REFUSES a non-T3 decision.
    df = escalation_decision(TaskClass("t-ends", change_type="purpose.change"))
    refused = False
    try:
        dispatch_exploration(df, intent="should never run", now=_NOW)
    except ValueError:
        refused = True
    ck("T4: dispatch_exploration REFUSES a non-T3 (human) decision — a forbidden task can't be auto-dispatched",
       refused)

    # ── EXPLORATION EXHAUSTED → T4 (human) ────────────────────────────────────────────────────────────────────
    spent_exploration = exhausted_llm + [{"kind": ATTEMPT_KIND_EXPLORATION, "outcome": "candidate"}] * DEFAULT_MAX_EXPLORATION_ROUNDS
    d4 = escalation_decision(TaskClass("t-routine"), spent_exploration)
    ck(f"T4: after {DEFAULT_MAX_EXPLORATION_ROUNDS} exploration rounds without passing, escalate to a HUMAN",
       d4.tier == T4_HUMAN and d4.requires_human_boundary is True
       and d4.signals.get("exploration_exhausted") is True)

    # ── POLICY: disabling autonomous exploration routes a would-be-T3 to T4 (human) ──────────────────────────
    cautious = EscalationPolicy(allow_autonomous_exploration=False)
    dp = escalation_decision(TaskClass("t-research", task_class=TASK_CLASS_RESEARCH), policy=cautious)
    ck("policy: allow_autonomous_exploration=False routes a would-be-T3 task to T4 (human authorizes it)",
       dp.tier == T4_HUMAN and dp.requires_human_boundary is True
       and dp.signals.get("exploration_blocked_by_policy") is True)

    # ── ALREADY SOLVED: a passing attempt reports the solving rung, no escalation ─────────────────────────────
    solved = escalation_decision(TaskClass("t-routine"),
                                 [{"kind": ATTEMPT_KIND_DETERMINISTIC, "outcome": "passed"}])
    ck("solved: a passing attempt reports the solving rung (T1) with no escalation, no human",
       solved.tier == T1_DETERMINISTIC and not solved.requires_human_boundary
       and solved.signals.get("solved_by") == ATTEMPT_KIND_DETERMINISTIC)

    # ── DETERMINISM: same input → identical decision id AND identical proposal/receipt ids ────────────────────
    d3_again = escalation_decision(TaskClass("t-routine", intent="normalize messy citations"), exhausted_llm)
    prop_again = dispatch_exploration(d3_again, intent="explore the negative space", now=_NOW,
                                      tenant_id="baltor-internal")
    ck("determinism: same task+history → byte-identical escalation decision id",
       d3.decision_id == d3_again.decision_id and asdict(d3) == asdict(d3_again))
    ck("determinism: same decision + now → byte-identical proposal id AND receipt id",
       prop.proposal_id == prop_again.proposal_id
       and prop.receipt["receipt_id"] == prop_again.receipt["receipt_id"])

    # ── NO THIRD-PARTY IMPORT: prove this package imports no openclaw/hermes/agent SDK (source scan) ──────────
    import re
    from pathlib import Path
    pkg = Path(__file__).resolve().parent
    banned = re.compile(r"\b(import|from)\b.*\b(openclaw|clawless|hermes|openhands|open_swe|langchain|crewai|autogen)\b",
                        re.IGNORECASE)
    offenders: list[str] = []
    for py in sorted(pkg.glob("*.py")):
        for raw in py.read_text(encoding="utf-8").splitlines():
            s = raw.strip()
            if (s.startswith("import ") or s.startswith("from ")) and banned.search(s):
                offenders.append(f"{py.name}: {s}")
    ck("no-import: the package never imports OpenClaw/Hermes/OpenHands/Open SWE or any agent SDK (source scan)",
       not offenders)

    print("\n" + ("PASS — src.teleon.exploration: the open-ended escalation ladder is deterministic — a template "
                  "match short-circuits at T0, a routine task runs the LLM gate then escalates to bounded "
                  "exploration (T3) after the LLM budget, an exploration class reaches T3 directly, a T3 dispatch "
                  "re-enters the gate as a CANDIDATE (serves_truth=False, receipt-backed) on the offline emulator, "
                  "named OpenClaw/Hermes candidates degrade honestly (never imported/executed), forbidden/ENDS "
                  "tasks + exhausted exploration go to a human (T4, never auto-dispatched), and the whole decision "
                  "is reproducible."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def _decide(task_json: str, history_json: str | None) -> int:
    """One decision as JSON (for a wire-in / shell caller). Reads a task dict + optional history list."""
    task = json.loads(task_json)
    history = json.loads(history_json) if history_json else None
    decision = escalation_decision(task, history)
    out = asdict(decision)
    proposal = None
    if decision.tier == T3_EXPLORATION:
        # show what a dispatch WOULD produce (offline emulator default) — still a candidate, never published.
        prop = dispatch_exploration(decision, intent=task.get("intent", ""), now=_NOW,
                                    tenant_id=task.get("tenant_id", "unknown"))
        proposal = asdict(prop)
    print(json.dumps({"decision": out, "proposal": proposal}, indent=2, sort_keys=True))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m src.teleon.exploration",
                                     description="Open-ended exploration escalation ladder (Teleon).")
    parser.add_argument("--self-test", action="store_true", help="run the offline deterministic contract proof")
    parser.add_argument("--decide", metavar="TASK_JSON", help="emit one escalation decision for a task dict (JSON)")
    parser.add_argument("--history", metavar="HISTORY_JSON", default=None,
                        help="optional attempt-history list (JSON) accompanying --decide")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.decide:
        return _decide(args.decide, args.history)
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
