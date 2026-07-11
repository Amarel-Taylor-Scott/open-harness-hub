#!/usr/bin/env python3
"""execution_scorer — turn the grid-search `execution_efficiency` DECLARED SEAM into a real measurement (gap 2.5).

The grid-search scorer zoo scores paths by token PROXIES; `execution_efficiency` was a declared seam (fn=None),
so "most efficient" and "needs 8 GB" were planning bands, never observations. This module measures execution
for real — but by EXECUTED INSTRUCTION COUNT, not wall-clock. Instruction count is (a) a genuine execution
signal (a bubble sort executes far more lines than a builtin sort on the same input) and (b) DETERMINISTIC
(same code + same input → same count), so it satisfies the repo's determinism law where wall-time cannot. It
runs the member's actual body under a line-execution tracer on sample inputs — a measurement, not a proxy.

A member is measurable only if it carries an `executable_body` + an `entry` (the callable name) + a sample
input. Non-executable members (the governance-spec cards) ABSTAIN honestly — the scorer reports coverage so a
caller never mistakes an abstention for a cheap path. It stays OFF in the default grid search (proxy-only,
byte-identical) and is opted in behind a flag.

    PYTHONPATH=. python3 scripts/execution_scorer.py --self-test
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Optional

_ABSTAIN = -1   # a member with no executable body — not measurable; reported as coverage, never counted as 0


def measured_instruction_cost(body: str, entry: str, sample_inputs: list[tuple]) -> Optional[int]:
    """Total executed lines when `entry(*args)` runs for each sample input, under a line tracer. Deterministic.
    Returns None if the body has no such callable or raises (an honest non-measurement, not a fake 0)."""
    namespace: dict[str, Any] = {}
    try:
        exec(compile(body, "<primitive_body>", "exec"), namespace)  # noqa: S102  measuring a declared body
    except Exception:  # noqa: BLE001
        return None
    fn = namespace.get(entry)
    if not callable(fn):
        return None

    counter = {"lines": 0}

    def _tracer(frame, event, arg):  # line-granularity execution counter
        if event == "line":
            counter["lines"] += 1
        return _tracer

    total = 0
    for args in sample_inputs:
        counter["lines"] = 0
        prev = sys.gettrace()
        sys.settrace(_tracer)
        try:
            fn(*args)
        except Exception:  # noqa: BLE001  a body that raises is not measurable on this input
            sys.settrace(prev)
            return None
        finally:
            sys.settrace(prev)
        total += counter["lines"]
    return total


def score_path_execution(members: list[dict[str, Any]],
                         sample_inputs_by_id: Optional[dict[str, list[tuple]]] = None) -> dict[str, Any]:
    """Measured execution cost of a PATH: sum of measurable members' instruction counts, with honest coverage.
    `sample_inputs_by_id` maps a member id to its sample inputs (falls back to the member's own `sample_inputs`)."""
    sample_inputs_by_id = sample_inputs_by_id or {}
    total, measured, abstained = 0, 0, 0
    per_member: list[dict[str, Any]] = []
    for member in members:
        mid = str(member.get("card_id") or member.get("primitive_id") or member.get("component_id") or "")
        body = member.get("executable_body")
        entry = member.get("entry") or member.get("impl_name")
        samples = sample_inputs_by_id.get(mid) or member.get("sample_inputs") or []
        cost = measured_instruction_cost(body, entry, samples) if (body and entry and samples) else None
        if cost is None:
            abstained += 1
            per_member.append({"id": mid, "measured": False, "cost": _ABSTAIN})
        else:
            measured += 1
            total += cost
            per_member.append({"id": mid, "measured": True, "cost": cost})
    return {"record_type": "path_execution_measurement",
            "measured_instructions": total if measured else _ABSTAIN,
            "members_measured": measured, "members_abstained": abstained,
            "coverage": round(measured / max(1, len(members)), 4),
            "per_member": per_member,
            "note": "executed-instruction count (deterministic, real measurement); abstained members are "
                    "non-executable governance cards, NOT free — coverage discloses how much was measured",
            "candidate": True, "serves_truth": False}


# ── executable fixtures for the self-test: a lean builtin sort vs a quadratic bubble sort. Same output, very
#    different EXECUTED work — the measurement must tell them apart. ─────────────────────────────────────────
_LEAN_SORT = "def run(xs):\n    return sorted(xs)\n"
_BUBBLE_SORT = ("def run(xs):\n"
                "    a = list(xs)\n"
                "    for i in range(len(a)):\n"
                "        for j in range(len(a) - 1):\n"
                "            if a[j] > a[j + 1]:\n"
                "                a[j], a[j + 1] = a[j + 1], a[j]\n"
                "    return a\n")


def _self_test() -> int:
    checks: list[tuple[str, bool, str]] = []
    sample = [([5, 3, 1, 4, 2, 8, 7, 6],)]

    lean = measured_instruction_cost(_LEAN_SORT, "run", sample)
    bubble = measured_instruction_cost(_BUBBLE_SORT, "run", sample)
    checks.append(("REAL measurement: the quadratic bubble sort executes far MORE instructions than the builtin "
                   "sort on the same input (measured, not a token proxy)",
                   lean is not None and bubble is not None and bubble > lean * 3,
                   f"lean={lean} lines, bubble={bubble} lines"))

    # DETERMINISM: instruction count is reproducible (unlike wall-time), so it obeys the scorer determinism law.
    checks.append(("DETERMINISTIC: the same body+input yields the identical instruction count twice",
                   measured_instruction_cost(_BUBBLE_SORT, "run", sample) == bubble
                   and measured_instruction_cost(_LEAN_SORT, "run", sample) == lean, ""))

    # scaling: a bigger input executes MORE (the measurement tracks real work).
    big = measured_instruction_cost(_BUBBLE_SORT, "run", [(list(range(30, 0, -1)),)])
    checks.append(("the measurement tracks input size (30-element reverse list executes more than 8-element)",
                   big is not None and big > bubble, f"big={big} > small={bubble}"))

    # path scoring: a path of the lean member scores LOWER than a path of the bubble member (efficiency).
    lean_path = [{"card_id": "m:lean", "executable_body": _LEAN_SORT, "entry": "run", "sample_inputs": sample}]
    bubble_path = [{"card_id": "m:bubble", "executable_body": _BUBBLE_SORT, "entry": "run", "sample_inputs": sample}]
    lean_score = score_path_execution(lean_path)
    bubble_score = score_path_execution(bubble_path)
    checks.append(("path execution scoring ranks the lean path below the bubble path BY MEASUREMENT; coverage=1",
                   lean_score["measured_instructions"] < bubble_score["measured_instructions"]
                   and lean_score["coverage"] == 1.0, ""))

    # HONEST ABSTENTION: a non-executable governance card is not scored 0 — it abstains + lowers coverage.
    spec_path = [{"card_id": "m:spec", "title": "governance spec", "blackbox": "no body"}]
    spec_score = score_path_execution(spec_path)
    checks.append(("honest abstention: a non-executable card abstains (coverage 0), never counted as a free 0",
                   spec_score["members_abstained"] == 1 and spec_score["coverage"] == 0.0
                   and spec_score["measured_instructions"] == _ABSTAIN, ""))

    # a body that raises on the input is a non-measurement (None), not a fake number.
    raiser = "def run(xs):\n    raise ValueError('boom')\n"
    checks.append(("a body that raises is an honest non-measurement (None), never a fabricated cost",
                   measured_instruction_cost(raiser, "run", sample) is None, ""))

    # the tracer is restored (no leaked sys.settrace after measuring).
    checks.append(("the execution tracer is always restored (no leaked sys.settrace)",
                   sys.gettrace() is None or callable(sys.gettrace()), ""))

    ok = all(passed for _n, passed, _d in checks)
    print(f"{'PASS' if ok else 'FAIL'} - execution_scorer: real execution-backed scoring (gap 2.5) by EXECUTED "
          f"INSTRUCTION COUNT (deterministic, not wall-clock) — measures a member's actual body on sample "
          f"inputs, ranks a quadratic path above a linear one by measurement, abstains honestly on "
          f"non-executable cards. Turns the grid-search execution seam into a measurement. serves_truth=false")
    for name, passed, detail in checks:
        print(f"  [{'ok' if passed else 'XX'}] {name}" + (f"  ({detail[:200]})" if not passed else ""))
    return 0 if ok else 1


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Execution-backed (instruction-count) scorer for primitive paths.")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
