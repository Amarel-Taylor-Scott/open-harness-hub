#!/usr/bin/env python3
"""scripts.loop_prompt_builder — GENERATE the next north-star loop cycle's prompt FROM repo state.

The loop is SELF-PROMPTING: each cycle the running agent records what to do next in .agent/next-action.json
(``next_target`` + ``then`` + ``resume``) and the live flywheel status in .agent/north-star-loop-state.json.
This builder turns that evolving state into the next cycle's ``/loop`` prompt — so the human no longer hand-writes
the giant prompt; the repo's own state (which the agent itself updates every cycle) does. That is "Claude Code
creating the prompts to accomplish the loop": the agent writes next_action this cycle → the builder emits it as
next cycle's prompt.

Pure + deterministic + offline (reads only .agent/*.json; no network, no LLM, no clock). The standing constraints,
the STOP contract, the flywheel/watchdog discipline, and the hard-won shim-extraction lessons are fixed invariants
carried in EVERY emitted prompt so a cycle can never drift off the rails — only the variable target comes from state.

CLI:
  python3 _repos/shared-backend-components/scripts/loop_prompt_builder.py --emit        # print the next-cycle prompt (what the runner/hook feeds)
  python3 _repos/shared-backend-components/scripts/loop_prompt_builder.py --self-test    # prove the emitted prompt carries every invariant
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import json
import os
import sys
from pathlib import Path

_REPO = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_NEXT_ACTION = (_REPO / ".agent") / "next-action.json"
_NS_STATE = (_REPO / ".agent") / "north-star-loop-state.json"
_HC_STATE = (_REPO / ".agent") / "hardcore-loop-state.json"

#: the loop's slash entrypoint — re-entering it continues the loop.
LOOP_COMMAND = "/loop /claude-code-max-north-star-execution-loop"

#: standing constraints carried in EVERY cycle (single source — edit here, not in each pasted prompt).
STANDING_CONSTRAINTS = (
    "Honor standing constraints: NO commit/push/pip/npm/containers/cloud/network-LLM; exact-pid process "
    "management (never pkill); no raw secret values in artifacts (secrets are refs only); no vendor/company "
    "NAMED in any public surface (public-claim policy) — system TYPES only; LLM/benchmark/sandbox/eval output "
    "stays candidate-not-truth; benchmark/eval/LLM is never a source or promotion authority; candidate!=active; "
    "no dashboard truth; lossless distillation (preserve raw+lineage; re-export shims, never delete or fork the "
    "runtime); architectural law Baltor->Teleon->OpenHubForAI never reverse (Teleon must NEVER import Baltor); "
    "HELD items (3 .io hub sites; Teleon Control Tower greenfield; live LLM adapter call = allow_network+real key "
    "owner-gated; live cloud/K8s exec = backend+creds owner-gated; DurableFleetLedger extraction = owner-area "
    "decision) stay held with a ledger entry. External/billable actions need explicit owner 'do X'. Classify "
    "every blocker (FIXED_NOW / LOCAL_EQUIVALENT_BUILT / CANDIDATE_DEFERRED_WITH_PROOF / QUARANTINED / OWNER_HELD "
    "/ SPLIT_INTO_NEXT_INCREMENT / REPRODUCED_AND_ISOLATED)."
)

#: hard-won extraction/shim lessons — carried so the loop never re-learns them the hard way.
LESSONS = (
    "Lessons (apply every cycle): (1) PRE-GREP a module before moving it — proofs that read_text its SOURCE or "
    "access module._private OR module.<name> (names it imports, e.g. canonical_id from .ids) must be repointed in "
    "the SAME cycle; a re-export shim reproduces the module's FULL accessed-attribute surface. (2) Include RELATIVE "
    "`from .` imports in the dependency pre-grep, not just absolute `from src.baltor`. (3) A re-export shim "
    "preserves imports but NOT source-content scans — repoint those to the Teleon home. (4) RUN THE FLYWHEEL before "
    "declaring a cycle done; it catches a missed re-export. If a target is blocked, switch to a clean leaf and "
    "record the blocker — never break the law."
)

#: the anti-slop / anti-fake-progress gate (stop-slop spirit, applied to autonomous PROGRESS not prose):
#: a cycle must do REAL proof-backed work, never claim done without a passing proof, never soft-stop.
ANTI_SLOP = (
    "Do REAL proof-backed work this cycle: ship ONE concrete proven increment (a passing --self-test + flywheel "
    "GREEN), or mark a target VERIFIED_DONE only with evidence. NO fake completion, NO 'queued / next tick / will "
    "continue / standing by' soft-stop language, NO claiming done without a green proof. If the work is GENUINELY "
    "exhausted, create .agent/STOP_REQUESTED with a one-line reason instead of looping idle."
)


def _read_json(p: Path) -> dict:
    try:
        return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {}
    except Exception:
        return {}


def build_prompt(next_action: dict, *, ns_state: dict | None = None, hc_state: dict | None = None) -> str:
    """Build the next cycle's /loop prompt from state. Pure: (next_action, ns_state, hc_state) -> str."""
    ns_state = ns_state or {}
    hc_state = hc_state or {}
    flywheel = ns_state.get("flywheel") or "GREEN (verify with: env -u PYTHONPATH python3 scripts/baltor_flywheel.py --once)"
    cycle_id = hc_state.get("cycle_id", "?")
    target = next_action.get("next_target") or ns_state.get("next_command") or "Pick the highest-leverage unfinished north-star target from the loop log + state, and ship one proven increment."
    then = next_action.get("then") or []
    resume = next_action.get("resume") or ""
    then_block = "".join(f"\n  - {t}" for t in then)

    return (
        f"{LOOP_COMMAND}\n\n"
        "Resume the AI Done Right/Teleon/Baltor MAX north-star execution loop (self-prompted from "
        f".agent/next-action.json; last cycle id: {cycle_id}). "
        "FIRST verify reality: repair sweep (json-parse + py-compile changed files; "
        "env -u PYTHONPATH python3 scripts/baltor_flywheel.py --once, expect GREEN; confirm the flywheel watchdog "
        "is alive — latest pid in .agent/hardcore-loop-state.json `watchdog_action` — restart by EXACT pid ONLY if "
        "dead or PROOF_MODULES changes, never pkill). Mark already-done targets VERIFIED_DONE; do NOT redo done "
        f"work or duplicate proofs. Last recorded flywheel: {flywheel}.\n\n"
        f"THIS CYCLE'S TARGET (from .agent/next-action.json):\n{target}\n"
        f"{('Then (subsequent cycles):' + then_block) if then_block else ''}\n\n"
        f"{ANTI_SLOP}\n\n"
        f"How to run a cycle: {resume}\n\n"
        f"{LESSONS}\n\n"
        f"{STANDING_CONSTRAINTS} Append a receipt to .agent/baltor-goal-loop-log.md + refresh "
        ".agent/{north-star-loop-state,hardcore-loop-state,blocker-ledger,next-action}.json (set next_target to the "
        "NEXT increment so the following cycle is self-prompted). Stop ONLY if .agent/STOP_REQUESTED exists."
    )


def emit() -> str:
    return build_prompt(_read_json(_NEXT_ACTION), ns_state=_read_json(_NS_STATE), hc_state=_read_json(_HC_STATE))


#: invariants every emitted prompt MUST carry (the proof asserts these).
_REQUIRED = [
    LOOP_COMMAND, ".agent/STOP_REQUESTED", "flywheel", "EXACT pid", "Teleon must NEVER import Baltor",
    "lossless", "REAL proof-backed work", "PRE-GREP", "next_target", "watchdog",
]


def _self_test() -> int:
    fails: list[str] = []

    def check(n: str, ok: bool, d: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok:
            fails.append(n)

    prompt = emit()
    missing = [r for r in _REQUIRED if r not in prompt]
    check("A: emitted prompt carries every standing invariant (loop cmd, STOP, flywheel, exact-pid, law, lossless, anti-slop, lessons)",
          not missing, f"missing={missing}")
    check("B: prompt is substantial (full cycle brief, not a stub)", len(prompt) > 1500, f"len={len(prompt)}")

    # state-driven: a synthetic next_action flows into the prompt (the builder reads state, nothing hardcoded)
    synth = build_prompt({"next_target": "SENTINEL_TARGET_XYZ move foo->teleon", "then": ["SENTINEL_THEN_ABC"],
                          "resume": "SENTINEL_RESUME_123"})
    check("C: state-driven — next_action.{next_target,then,resume} flow verbatim into the prompt",
          "SENTINEL_TARGET_XYZ" in synth and "SENTINEL_THEN_ABC" in synth and "SENTINEL_RESUME_123" in synth)

    # deterministic: same state -> identical prompt (no clock/rng)
    a = build_prompt({"next_target": "t"}, ns_state={"flywheel": "GREEN 383/383"}, hc_state={"cycle_id": "hc-1"})
    b = build_prompt({"next_target": "t"}, ns_state={"flywheel": "GREEN 383/383"}, hc_state={"cycle_id": "hc-1"})
    check("D: deterministic (same state -> identical prompt; no clock/RNG)", a == b)

    # anti-slop gate present (stop-slop spirit): no fake completion, no soft-stop, STOP-or-real-work
    check("E: anti-slop / anti-fake-progress gate present (no soft-stop; STOP_REQUESTED is the only exit)",
          "NO fake completion" in prompt and "soft-stop" in prompt and ".agent/STOP_REQUESTED with a one-line reason" in prompt)

    print("\n" + ("PASS — loop_prompt_builder: the next-cycle /loop prompt is generated FROM .agent/next-action.json "
                  "(self-prompting), deterministic, substantial, and carries every standing invariant + the STOP "
                  "contract + the anti-slop gate." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--emit" in sys.argv:
        print(emit())
        raise SystemExit(0)
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/loop_prompt_builder.py [--emit | --self-test]")
    raise SystemExit(0)
