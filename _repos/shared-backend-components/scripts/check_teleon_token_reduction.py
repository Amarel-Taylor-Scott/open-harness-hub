#!/usr/bin/env python3
"""check_teleon_token_reduction — proof that TOKEN consumption (in/out) is a tracked dimension + a SKILL can be
token-reduced losslessly.

  * tokens_in and tokens_out are canonical descent axes (lower-is-better) — token consumption in AND out, tracked.
  * the RunLedger records tokens_in/tokens_out per run and reports the observed token usage (the metric to track).
  * compress_skill token-reduces a SKILL's prompt deterministically + losslessly (collapse whitespace, drop
    duplicate instructions, prune optional boilerplate) — answer-critical content survives, the raw is preserved,
    and a must_keep phrase that did NOT survive flags lossless=False (escalate, never ship a lossy compression).
  * prompt_compression is a registered descent strategy on the tokens_in axis (improves tokens_in + cost), so the
    generic descender builds a token_reduced fork; measure_descent counts token-axis improvements. Never serves truth.

CLI: python3 _repos/shared-backend-components/scripts/check_teleon_token_reduction.py --self-test
"""
from __future__ import annotations

import os
import sys

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _R not in sys.path:
        sys.path.insert(0, _R)

from src.teleon.evolution import DESCENT_AXES, compress_skill, descend, descent_strategies, measure_descent
from src.teleon.objectives import RunLedger, RunObservation

_BLOATED_SKILL = """You are a helpful assistant.

You are a helpful assistant.
Always cite the source: ecfr://12/1005.11 for the Reg E deadline.
[optional] Here is some background boilerplate that does not change the answer.
[optional] More boilerplate the model does not need.
Always cite the source: ecfr://12/1005.11 for the Reg E deadline.
Return the deadline in business days.



Return the deadline in business days.
"""


def _self_test() -> int:
    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    # tokens_in / tokens_out are canonical axes (lower is better).
    ck("token consumption IN and OUT are canonical descent axes (lower-is-better)",
       "tokens_in" in DESCENT_AXES and "tokens_out" in DESCENT_AXES
       and DESCENT_AXES["tokens_in"]["direction"] == "lower" and DESCENT_AXES["tokens_out"]["direction"] == "lower")

    # SKILL token reduction — lossless, with the answer-critical source handle preserved.
    c = compress_skill("reg-e-deadline-skill", _BLOATED_SKILL,
                       must_keep=("ecfr://12/1005.11", "business days"))
    ck("even a SKILL is token-reduced: fewer INPUT tokens after compression",
       c["tokens_in_after"] < c["tokens_in_before"] and c["tokens_saved"] > 0, str({k: c[k] for k in ("tokens_in_before", "tokens_in_after")}))
    ck("the compression is LOSSLESS: answer-critical content survives + the raw skill is preserved",
       c["must_keep_survived"] is True and c["lossless"] is True and c["raw_preserved"] is True
       and "ecfr://12/1005.11" in c["compressed"] and "business days" in c["compressed"])
    ck("duplicate instructions + optional boilerplate are pruned (the source of the savings)",
       c["compressed"].count("helpful assistant") == 1 and "[optional]" not in c["compressed"]
       and c["compressed"].count("business days") == 1)
    ck("a meaningful reduction is reported + never serves truth", c["reduction_pct"] > 0 and c["serves_truth"] is False)

    # the LOSSLESS GUARD: a must_keep phrase that does not survive flags lossless=False (escalate, never ship).
    bad = compress_skill("s", "just a short prompt", must_keep=("THIS_PHRASE_IS_ABSENT",))
    ck("a compression that would drop answer-critical content is flagged lossless=False (escalate)",
       bad["must_keep_survived"] is False and bad["lossless"] is False)

    # prompt_compression is a registered descent strategy on the tokens_in axis -> the generic descender builds a fork.
    strat = descent_strategies()["tokens_in"]
    ck("prompt_compression is the registered descent strategy for the tokens_in axis (improves tokens_in + cost)",
       strat["strategy_id"] == "prompt_compression" and {"tokens_in", "cost"} <= set(strat["improves"]))
    fork = descend("reg-e-deadline-skill", "tokens_in")
    ck("descend('tokens_in') builds a token_reduced fork that improves tokens_in + cost, lossless, never truth",
       fork["fork_kind"] == "token_reduced" and "tokens_in" in fork["record"]["improvement_axes"]
       and fork["record"]["lossless"] is True and fork["serves_truth"] is False)
    ck("the token-reduction fork is cheaper (fewer tokens -> lower cost)",
       fork["record"]["per_call_cost_after"] < fork["record"]["per_call_cost_before"])

    # TOKEN CONSUMPTION is TRACKED: the RunLedger records tokens in/out per run and reports the observed usage.
    led = RunLedger()
    for _ in range(3):
        led.record(RunObservation("skill@compressed", cost=0.01, latency_ms=300, llm_calls=1, passed=True,
                                  output_key="ok", tokens_in=180, tokens_out=40))
    usage = led.token_usage("skill@compressed")
    ck("the RunLedger TRACKS token consumption in + out per run (the metric to track)",
       usage["mean_tokens_in"] == 180 and usage["mean_tokens_out"] == 40 and usage["mean_tokens_total"] == 220)

    # measure_descent counts a tokens_in improvement (the axis flows into the measurement harness).
    m = measure_descent([fork["record"]])
    ck("measure_descent counts the tokens_in improvement on the token-reduction fork",
       m["improved_by_axis"].get("tokens_in", 0) >= 1 and "tokens_out" in m["improved_by_axis"])

    # deterministic
    ck("skill compression is deterministic (same skill -> same compressed output + token counts)",
       compress_skill("reg-e-deadline-skill", _BLOATED_SKILL, must_keep=("ecfr://12/1005.11", "business days")) == c)

    print("\n" + ("PASS - check_teleon_token_reduction: token consumption IN and OUT are tracked canonical axes; the "
                  "RunLedger records tokens-in/out per run; compress_skill token-reduces even a single SKILL "
                  "losslessly (duplicates + optional boilerplate pruned, answer-critical content + raw preserved, a "
                  "dropped must_keep flags lossless=False); prompt_compression is a registered tokens_in descent "
                  "strategy the generic descender + measurement harness pick up. Deterministic; never serves truth."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(_self_test() if "--self-test" in sys.argv else 0)
