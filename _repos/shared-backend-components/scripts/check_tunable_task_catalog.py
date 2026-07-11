#!/usr/bin/env python3
"""check_tunable_task_catalog — proof that the document-extraction idea GENERALIZES: a catalog of agentic tasks
that each fit automated setup tuning (tiered method grid, cheapest-first, escalate only as far as the requirement
forces). Validates the tiers are cheapest-first with a deterministic floor, the document-extraction task is the
reference instance, and the auto-tuner produces a cheapest-first escalation plan that key-gates LLM tiers and lets
deterministic-possible tasks complete without an LLM. serves_truth=false.

CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_tunable_task_catalog.py --self-test
"""
from __future__ import annotations

import os
import sys

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _R not in sys.path:
        sys.path.insert(0, _R)

from src.teleon.evolution.auto_tuning import auto_tune_setup, get_task, load_catalog, tuning_ladder


def _self_test() -> int:
    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    cat = load_catalog()
    tasks = cat["tasks"]
    ck("catalog generalizes to MANY agentic tasks (>= 10)", len(tasks) >= 10, str(len(tasks)))
    ck("every task has >= 2 method tiers + a requirement metric + objective",
       all(len(t["tiers"]) >= 2 and t.get("requirement_metric") and t.get("objective") for t in tasks))
    # tiers are cheapest-first and start at a deterministic/cheap floor (the whole point)
    ck("every task's tiers are cheapest-first (ascending cost) with a deterministic cheap floor",
       all([x["cost_rank"] for x in tuning_ladder(t)] == sorted(x["cost_rank"] for x in tuning_ladder(t))
           and tuning_ladder(t)[0]["deterministic"] for t in tasks))
    ck("the document-extraction task is present as the reference instance",
       get_task("document-schema-extraction") is not None)

    # auto-tuner: cheapest-first escalation; LLM tiers key-gated; deterministic-possible tasks need no LLM
    plan = auto_tune_setup("document-schema-extraction", available_keys=("LLM_API_KEY",))
    ck("auto-tuner emits a cheapest-first escalation order with the LLM tier LAST",
       plan["escalation_order"] and plan["escalation_order"][-1] == "llm" and plan["cheapest_tier"] != "llm")
    nokey = auto_tune_setup("document-schema-extraction", available_keys=())
    ck("without an LLM key the LLM tier is excluded (deterministic tiers still reachable)",
       "llm" in nokey["excluded_for_missing_keys"] and "llm" not in nokey["escalation_order"]
       and nokey["deterministic_floor"] is not None)
    # a deterministic-possible task completes WITHOUT an LLM at all
    dedup = auto_tune_setup("dedup-near-duplicate", available_keys=())
    ck("a deterministic-possible task (dedup) completes with NO LLM (can_complete_deterministically)",
       dedup["can_complete_deterministically"] is True and dedup["cheapest_tier"] is not None)
    asr = auto_tune_setup("transcription-asr", available_keys=())
    ck("transcription-asr runs its local deterministic tier with no cloud key", asr["cheapest_tier"] is not None
       and asr["can_complete_deterministically"] is True)

    # the named real tasks span domains (extraction, entity-res, classification, moderation, sql, translation, ...)
    ids = {t["task_id"] for t in tasks}
    ck("the catalog spans diverse domains (entity-res, classification, grounded-answer, moderation, sql, translation)",
       {"entity-resolution", "text-classification", "grounded-answer", "content-moderation",
        "sql-generation", "translation"} <= ids)
    ck("nothing serves truth (outputs are candidates for the verification rail)",
       cat["serves_truth"] is False and plan["serves_truth"] is False)
    ck("deterministic", auto_tune_setup("document-schema-extraction", available_keys=("LLM_API_KEY",)) == plan)

    print("\n" + (f"PASS - check_tunable_task_catalog: {len(tasks)} agentic tasks generalize the document-extraction "
                  f"pattern — each a tiered method grid (deterministic floor → small model → frontier LLM), "
                  f"cheapest-first, escalate-only-as-needed; the auto-tuner key-gates LLM tiers and lets "
                  f"deterministic-possible tasks finish with no LLM. Automated setup tuning, generalized. Never "
                  f"serves truth." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def _main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--self-test" in argv:
        return _self_test()
    print("usage: check_tunable_task_catalog.py --self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
