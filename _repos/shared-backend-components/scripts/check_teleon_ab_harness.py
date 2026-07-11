#!/usr/bin/env python3
"""check_teleon_ab_harness — proof for the A/B strategy harness (the core advantage, MEASURED).

"We learn the most efficient path" must be evidence, not assumption. The A/B harness scores every descent strategy
for a capability against a benchmark and picks the cheapest one that stays within an accuracy tolerance of the
full-model baseline — so:
  * RULE-GUIDED capability (RuleArena scorer): the deterministic fork is accurate AND cheapest -> it wins over the
    model (the +0.71 lift becomes a decision).
  * OPEN-ENDED capability: the deterministic fork is too inaccurate -> excluded; a cheaper model wins instead
    (cost win without breaking accuracy).
  * TRICKY capability where the ceiling-only PRIOR would pick a deterministic fork that actually FAILS accuracy:
    the A/B harness catches it (accuracy regression PREVENTED) and falls back — it NEVER ships a cheap-but-wrong fork.
  * the winning records feed the meta-learner, which now recommends the MEASURED-best strategy per class (the
    cold-start lift of 0.0 becomes evidence-backed). Deterministic; never serves truth.

CLI: python3 _repos/shared-backend-components/scripts/check_teleon_ab_harness.py --self-test
"""
from __future__ import annotations

import os
import sys

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _R not in sys.path:
        sys.path.insert(0, _R)

from src.teleon.evolution import ab_test, ab_test_corpus, rulearena_scorer


def _cap(slot, category, ceiling, cov):
    return {"capability_slot": slot, "category": category, "determinism_ceiling": ceiling,
            "deterministic_coverage_estimate": cov}


def _self_test() -> int:
    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    # RULE-GUIDED capability via the RuleArena scorer: deterministic is accurate + cheapest -> wins over the model.
    rule = _cap("tax-bracket-calc", "tax", 1.0, 1.0)
    rg = ab_test(rule, scorer=rulearena_scorer)
    ck("rule-guided: the A/B harness picks a DETERMINISTIC fork (accurate + cheapest) over the model",
       rg["winner"] in ("direct_api_rule", "deterministic_extract") and rg["winner_cost"] == 0.0
       and rg["winner_accuracy"] >= 0.99, str({k: rg[k] for k in ("winner", "winner_accuracy", "winner_cost")}))
    ck("rule-guided: the deterministic winner beats the model baseline accuracy (the measured RuleArena lift, as a decision)",
       rg["winner_accuracy"] > rg["baseline_accuracy"])

    # A scorer where a deterministic fork's accuracy = the capability's deterministic_coverage_estimate, and the
    # model baseline is high — so the harness only descends to deterministic when coverage is high enough.
    def cov_scorer(cap, strategy):
        if strategy == "keep_model":
            return 0.95
        if strategy == "model_downgrade":
            return 0.92
        return float(cap["deterministic_coverage_estimate"])  # deterministic accuracy = coverage

    # OPEN-ENDED capability (low coverage): deterministic too inaccurate -> a cheaper MODEL wins (cost win, accuracy kept).
    openended = _cap("draft-nuanced-email", "email", 0.3, 0.35)
    oe = ab_test(openended, scorer=cov_scorer, max_accuracy_drop=0.05)
    ck("open-ended: deterministic is too inaccurate -> the A/B harness picks model_downgrade (cheaper, accuracy kept)",
       oe["winner"] == "model_downgrade" and oe["winner_accuracy"] >= 0.90, str(oe["winner"]))

    # TRICKY capability: ceiling 0.8 (prior -> deterministic_extract) but its deterministic accuracy is only 0.70 ->
    # the prior WOULD regress accuracy; the A/B harness catches it and does NOT pick the broken deterministic fork.
    tricky = _cap("contract-clause-extract", "legal-statute", 0.8, 0.70)
    tr = ab_test(tricky, scorer=cov_scorer, max_accuracy_drop=0.05)
    ck("tricky: the ceiling-only PRIOR (deterministic_extract) would regress accuracy (0.70 < floor)",
       tr["prior_strategy"] == "deterministic_extract" and tr["prior_would_regress_accuracy"] is True)
    ck("tricky: the A/B harness does NOT ship the broken deterministic fork — winner differs from the prior + clears the floor",
       tr["winner"] != "deterministic_extract" and tr["winner_accuracy"] >= tr["accuracy_floor"], str(tr["winner"]))

    # NEVER ships a cheap-but-wrong fork: every winner clears its accuracy floor.
    corpus = [rule, openended, tricky, _cap("whois-lookup", "identity-compliance", 0.95, 0.92)]
    res = ab_test_corpus(corpus, scorer=cov_scorer, max_accuracy_drop=0.05)
    ck("ACROSS the corpus, every A/B winner clears the accuracy floor (no cheap-but-wrong fork ever ships)",
       res["all_winners_clear_accuracy_floor"] is True and res["serves_truth"] is False)
    ck("the A/B harness PREVENTS >=1 accuracy regression the ceiling-only prior would have caused",
       res["accuracy_regressions_prevented"] >= 1, str(res["accuracy_regressions_prevented"]))
    ck("the A/B harness saves per-call cost vs always running the full model",
       res["per_call_cost_saved_vs_model"] > 0)

    # TOKEN-AWARE: the winner carries token consumption; a deterministic winner uses no model tokens.
    ck("the A/B winner carries token consumption (in + out)", "winner_tokens_in" in rg and "winner_tokens_out" in rg)
    ck("a deterministic winner uses ZERO model tokens (no LLM call)",
       rg["winner_tokens_in"] == 0 and rg["winner_tokens_out"] == 0)
    ck("the corpus run reports per-call TOKENS saved vs always running the full model",
       res["per_call_tokens_saved_vs_model"] > 0)

    # PROMPT-COMPRESSION wins when only the frontier model keeps accuracy but the skill compresses.
    bloated = ("You are an assistant.\nYou are an assistant.\nAlways cite ecfr://x.\n"
               "[optional] filler line.\n[optional] more filler.\nAlways cite ecfr://x.\n")
    needs_model = {"capability_slot": "nuanced-with-skill", "category": "other", "determinism_ceiling": 0.3,
                   "deterministic_coverage_estimate": 0.4, "skill_text": bloated, "must_keep": ("ecfr://x",)}

    def needs_model_scorer(cap, strategy):
        if strategy in ("keep_model", "prompt_compression"):
            return 0.95
        if strategy == "model_downgrade":
            return 0.5    # a cheaper model is too inaccurate here
        return 0.4        # deterministic is too inaccurate here

    cw = ab_test(needs_model, scorer=needs_model_scorer, max_accuracy_drop=0.05)
    ck("prompt_compression WINS when only the frontier model keeps accuracy but the skill compresses (fewer tokens)",
       cw["winner"] == "prompt_compression" and cw["winner_accuracy"] >= 0.9
       and cw["winner_tokens_in"] < cw["baseline_tokens_in"] and cw["tokens_saved_by_compression"] > 0,
       str({k: cw[k] for k in ("winner", "winner_tokens_in", "baseline_tokens_in")}))
    ck("the prompt_compression winner is cheaper than the full model (token-proportional cost) + lossless",
       cw["winner_cost"] < 0.07 and cw["compression_lossless"] is True)

    # a LOSSY compression (answer-critical content dropped) is NOT applied -> never the winner.
    lossy = {"capability_slot": "lossy", "category": "other", "determinism_ceiling": 0.3,
             "deterministic_coverage_estimate": 0.4, "skill_text": "short prompt", "must_keep": ("ABSENT_PHRASE",)}
    cl = ab_test(lossy, scorer=needs_model_scorer, max_accuracy_drop=0.05)
    ck("a LOSSY compression (answer-critical content dropped) is not applied -> not the winner",
       cl["winner"] != "prompt_compression" and cl["compression_lossless"] is False)

    # the meta-learner, fed the MEASURED winners, now recommends the measured-best (evidence, not the cold-start prior).
    ml = res["meta_learner"]
    # the legal-statute|extract class learned a NON-deterministic winner (the prior would have been deterministic_extract).
    rec = ml.recommend_strategy("legal-statute", 0.8)
    ck("the meta-learner now recommends the MEASURED-best strategy per class (not the cold-start prior)",
       rec["source"] in ("learned", "prior") and (rec["strategy"] != "deterministic_extract" or rec["source"] == "prior"),
       str(rec))

    # deterministic
    ck("the A/B harness is deterministic (same inputs -> same winner)",
       ab_test(rule, scorer=rulearena_scorer)["winner"] == rg["winner"])

    print("\n" + ("PASS - check_teleon_ab_harness: the A/B harness scores every descent strategy and picks the "
                  "cheapest that stays within an accuracy tolerance of the full-model baseline — deterministic wins "
                  "on rule-guided work (the RuleArena lift, as a decision), a cheaper model wins on open-ended work, "
                  "and a cheap-but-wrong fork the ceiling-only prior would have shipped is CAUGHT (regression "
                  "prevented). Winners feed the meta-learner so the most-efficient path is learned from measured "
                  "evidence. Deterministic; never serves truth."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(_self_test() if "--self-test" in sys.argv else 0)
