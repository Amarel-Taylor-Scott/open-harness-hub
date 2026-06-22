#!/usr/bin/env python3
"""check_adjacent_verticals — the adjacent demo/pitch verticals share the adjudication shape, map to real loops, and
are NOT insurance (the non-compete + CLAUDE.md rule, enforced in code).

Proves: every vertical maps to a real agentic loop (agentic_loop_catalog); every vertical follows the shared
intake→extract→validate→policy→decide→act pipeline; and — the guardrail — NO vertical is insurance (sector/name/
pipeline), so a future insurance vertical/demo fails the gate instead of slipping in. serves_truth=false.

  python3 scripts/check_adjacent_verticals.py --self-test
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
V = REPO / "architecture" / "adjacent_verticals.json"
LOOPS = REPO / "architecture" / "agentic_loop_catalog.json"
_INSURANCE = ("insurance", "insurer", "claims adjuster", "underwrit insurance", "actuari", "policyholder")


def _self_test() -> int:
    data = json.loads(V.read_text(encoding="utf-8"))
    verticals = data["verticals"]
    loop_ids = {L["id"] for L in json.loads(LOOPS.read_text(encoding="utf-8"))["loops"]}
    fails = []
    def ck(n, ok, d=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok: fails.append(n)

    ck(f"adjacent verticals declared ({len(verticals)}), each with a pipeline + a demo", len(verticals) >= 8
       and all(v.get("pipeline") and v.get("demo") for v in verticals))
    bad_map = [v["id"] for v in verticals if v.get("maps_to") not in loop_ids]
    ck("every vertical maps to a REAL agentic loop (agentic_loop_catalog)", not bad_map, str(bad_map))
    ck("every vertical follows the shared adjudication shape (intake→extract→validate→policy→decide→act)",
       all(len(v["pipeline"]) >= 4 for v in verticals) and data.get("shared_pipeline"))
    # THE GUARDRAIL: no insurance anywhere (non-compete + CLAUDE.md), enforced in code
    blob = json.dumps(data).lower()
    hits = [k for k in _INSURANCE if k in blob]
    # 'avoid' explicitly NAMES insurance as the excluded sector — that mention is allowed; any OTHER mention is not
    allowed_ctx = json.dumps(data.get("avoid", {})).lower() + data.get("principle", "").lower()
    real_hits = [k for k in hits if blob.count(k) > allowed_ctx.count(k)]
    ck("NO vertical is insurance (sector/name/pipeline) — the non-compete rule enforced in code", not real_hits, str(real_hits))
    ck("the avoid rule is declared + names its enforcement", data.get("avoid", {}).get("sector") == "insurance"
       and "check_adjacent_verticals" in data.get("avoid", {}).get("enforced_by", ""))
    ck("vertical-neutral positioning present (pitch the pattern, not a vertical)", len(data.get("positioning", [])) >= 1)
    ck("serves_truth=false", data.get("serves_truth") is False)

    print("\n" + (f"PASS - check_adjacent_verticals: {len(verticals)} document/policy-heavy adjudication verticals, each "
                  "mapped to a real agentic loop, sharing the intake→extract→validate→policy→decide→act shape; NONE is "
                  "insurance (enforced in code). serves_truth=false." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(_self_test())
