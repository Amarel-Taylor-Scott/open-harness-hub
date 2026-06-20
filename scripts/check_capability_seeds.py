#!/usr/bin/env python3
"""check_capability_seeds — proof that every reviewed GitHub-signal repo is IMPLEMENTED as a governed capability
seed (learn-from-them, clean-room): each seed runs real logic, records the lesson taken, emits a valid PurposeTask
candidate, and NEVER serves truth. Drop-in is allowed only for clean permissive licenses; copyleft/unstated/
proprietary sources are technique-only (clean-room). The deterministic seeds (court-deadline, inference routing)
are checked for actual correctness, not just that they run.

CLI: PYTHONPATH=. python3 scripts/check_capability_seeds.py --self-test
"""
from __future__ import annotations

import json
import os
import sys
from datetime import date, timedelta
from pathlib import Path

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _R not in sys.path:
        sys.path.insert(0, _R)

_REPO = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_FEED = _REPO / "data" / "capability-candidates" / "discovered-feed-github-signal-2026-06-20.json"

from src.teleon.purpose_tasks.purpose_task import PurposeTaskSpec
from src.teleon.seeds import all_seeds
from src.teleon.seeds.capability_seed import vendorable


def _token(repo: str) -> str:
    return repo.split("/")[-1].lower().replace(".ai", "").replace(".dev", "")


def _self_test() -> int:
    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    seeds = all_seeds()
    by_slot = {s.slot: s for s in seeds}

    # (1) coverage: every reviewed repo in the intake feed has >= 1 seed (learn-from-them is implemented for ALL)
    feed = json.loads(_FEED.read_text())
    intake_tokens = {_token(c["repo"]) for c in feed["candidates"]}
    seed_blob = " ".join(s.learned_from.lower() for s in seeds)
    missing = sorted(t for t in intake_tokens if t not in seed_blob)
    ck("every reviewed repo has >= 1 capability seed (all implemented, learn-from-them)", not missing, str(missing))
    ck("there are at least as many seeds as reviewed repos (BigLaw yields two)", len(seeds) >= len(intake_tokens))

    # (2) each seed runs real logic and NEVER serves truth; each records a lesson + emits a valid PurposeTask candidate
    bad_run = []
    for s in seeds:
        r = s.run({})
        cand = s.as_purpose_task_candidate()
        ok = (r["serves_truth"] is False and r["output"] is not None and bool(s.lesson.strip())
              and PurposeTaskSpec.from_dict(cand).to_dict() == cand and cand["serves_truth"] is False)
        if not ok:
            bad_run.append(s.slot)
    ck("every seed runs, records a lesson, emits a valid PurposeTask candidate, and never serves truth", not bad_run, str(bad_run))

    # (3) drop-in discipline: copyleft/unstated/proprietary sources are NEVER drop-in (clean-room only)
    leaky = [s.slot for s in seeds if not vendorable(s.source_license) and s.is_drop_in()]
    ck("no copyleft/unstated/proprietary seed is drop-in (clean-room only)", not leaky, str(leaky))
    drop_ins = [s.slot for s in seeds if s.is_drop_in()]
    ck("drop-in seeds are clean-permissive (the MIT pair: marketing + source-discovery)",
       set(drop_ins) == {"marketing-copy-brief", "web-source-discovery"}, str(drop_ins))

    # (4) determinism: every determinism_ceiling==1.0 seed is deterministic (run twice → identical)
    nondet = [s.slot for s in seeds if s.determinism_ceiling == 1.0 and s.run({"x": 1}) != s.run({"x": 1})]
    ck("deterministic seeds (ceiling==1.0) are actually deterministic", not nondet, str(nondet))

    # (5) court-deadline calculator is CORRECT: never lands on a weekend; never rolls backward
    cd = by_slot["court-deadline-calculator"]
    out = cd.run({"filing_date": "2026-06-19", "rule_days": 1})["output"]   # +1 from a Friday → must roll to Monday
    due = date.fromisoformat(out["deadline"])
    naive = date.fromisoformat(out["filing_date"]) + timedelta(days=out["rule_days"])
    ck("court-deadline never lands on a weekend and never rolls backward (deterministic If-Statement)",
       due.weekday() < 5 and due >= naive and out["rolled_off_weekend"] is True, str(out))

    # (6) inference routing is CORRECT: cheapest CAPABLE within budget; cache-preferred on ties
    rt = by_slot["inference-prefix-cache-routing"]
    pick1 = rt.run({"models": [{"id": "cheap-small", "cost": 0.001, "ctx": 1000},
                               {"id": "pricey-big", "cost": 0.01, "ctx": 9000}], "prompt_tokens": 2000})["output"]
    pick2 = rt.run({"models": [{"id": "a", "cost": 0.002, "ctx": 9000, "cache_hit": False},
                               {"id": "b", "cost": 0.002, "ctx": 9000, "cache_hit": True}], "prompt_tokens": 100})["output"]
    ck("routing picks the cheapest CAPABLE model within the token budget (small model excluded by ctx)",
       pick1["picked"] == "pricey-big", str(pick1))
    ck("routing prefers the warm prefix-cache on a cost tie (borrowed inferoa technique)",
       pick2["picked"] == "b", str(pick2))

    # (7) adoptable discipline: foils/commodity/out-of-scope/clean-room-blocked are governed honestly
    ck("the AVOID/foil/out-of-scope seeds are adoptable=False (honest)",
       all(not by_slot[s].adoptable for s in ("inference-prefix-cache-routing", "local-asr-transcription",
                                              "eng-management-out-of-scope")))
    ck("the on-thesis clean capabilities are adoptable (marketing, source-discovery, both legal seeds)",
       all(by_slot[s].adoptable for s in ("marketing-copy-brief", "web-source-discovery",
                                          "legal-source-registry", "court-deadline-calculator")))
    ck("deterministic registry (stable order)", [s.slot for s in all_seeds()] == [s.slot for s in seeds])

    print("\n" + (f"PASS - check_capability_seeds: {len(seeds)} governed capability seeds implement ALL "
                  f"{len(intake_tokens)} reviewed repos (learn-from-them, clean-room) — drop-in only for clean "
                  f"licenses, technique-only for copyleft/unstated; the court-deadline + routing seeds are "
                  f"deterministically correct; every seed records its lesson and never serves truth. Nothing promoted."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def _main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--self-test" in argv:
        return _self_test()
    print("usage: check_capability_seeds.py --self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
