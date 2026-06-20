#!/usr/bin/env python3
"""scripts.check_baltor_context_environment — PROOF (P3): the Baltor-style governed-context environment
``environment.baltor.cfpb_context_governance.local@v1`` measures a candidate answer correctly and never serves
truth (nor the held-out contradiction).

The task (synthetic, from demo-data/cfpb-sample): the Reg E §1005.11 EFT-error resolution deadline. The
authoritative answer is "10 business days"; a stale FAQ saying "30 days" is the HELD-OUT CONTRADICTION that must
NOT be served. This environment is Teleon INFRA modeling a Baltor-style task — it does NOT import src.baltor.

Asserts:
  A. ENVIRONMENT + SPEC SHAPE: the module defines ENVIRONMENT_ID / REWARD_SPEC_ID; the RewardSpec is a
     deterministic_check with an authoritative-value check, a held_out_absent check, and a source-handle check;
     describe() is a local-first card (no docker/network) with serves_truth False.
  B. GOOD ANSWER PASSES: a candidate answer that states "...10 business days..." WITH a source handle ->
     reward.passed True, the held_out_absent check passes, a receipt is present, and EnvironmentRunResult.
     serves_truth is False (the agent answer is measured, never served truth).
  C. BAD ANSWER FAILS (held-out leak): a candidate answer that says "30 days" -> reward.passed False BECAUSE the
     held_out_absent check fails (the stale contradiction was leaked) — the held-out value is never served as truth.
  D. OUTPUT != TRUTH: across runs, no LLM/agent output is marked truth (result.serves_truth False AND
     reward.is_truth False); the fixture loads offline (seed JSON or inline fallback); determinism holds.
  E. NO BALTOR IMPORT: the teleon module does not import src.baltor (it encodes / reads the fixture locally).

Deterministic + offline. stdlib only. Exit 0/1. _REPO = parents[1]; sys.path.insert. No raw keys/secrets.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.teleon.environments import baltor_cfpb_context_governance as cfpb  # noqa: E402

_NOW = "2026-01-01T00:00:00Z"
_TELEON_MODULE = _REPO / "src" / "teleon" / "environments" / "baltor_cfpb_context_governance.py"


def _self_test() -> int:
    fails: list[str] = []

    def check(n: str, ok: bool, d: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok:
            fails.append(n)

    # ---- A. environment + spec shape ---------------------------------------------------
    check("A: ENVIRONMENT_ID is the cfpb governed-context env id",
          cfpb.ENVIRONMENT_ID == "environment.baltor.cfpb_context_governance.local@v1")
    fixture = cfpb.load_fixture()
    check("A: fixture authoritative answer is '10 business days'",
          cfpb.AUTHORITATIVE_ANSWER == "10 business days"
          and fixture["authoritative_answer"] == "10 business days")
    check("A: fixture held-out contradiction is '30 days'",
          cfpb.HELD_OUT_CONTRADICTION == "30 days" and fixture["held_out_contradiction"] == "30 days")
    check("A: fixture carries a source handle", bool(fixture.get("source_handle")))

    spec = cfpb.build_reward_spec(fixture)
    check("A: RewardSpec kind is deterministic_check", spec["kind"] == "deterministic_check")
    types = {c.get("type") for c in spec["checks"]}
    check("A: RewardSpec has substring_present + held_out_absent + key_present checks",
          {"substring_present", "held_out_absent", "key_present"}.issubset(types), str(sorted(types)))
    held = next((c for c in spec["checks"] if c.get("type") == "held_out_absent"), {})
    check("A: held_out_absent check targets the '30 days' contradiction", held.get("needle") == "30 days")
    card = cfpb.describe()
    check("A: describe() is local-first (no docker/network) + serves_truth False",
          card.get("requires_docker") is False and card.get("requires_network") is False
          and card.get("serves_truth") is False)

    # ---- B. GOOD candidate answer passes -----------------------------------------------
    good_answer = ("Under Reg E §1005.11 the institution must investigate and resolve the error within "
                   "10 business days (extendable to 45 calendar days with provisional credit).")
    good = cfpb.run_candidate("run-cfpb-good", candidate_answer=good_answer, now=_NOW)
    g_result, g_reward, g_receipt = good["result"], good["reward"], good["receipt"]
    check("B: GOOD answer -> reward.passed True", g_reward["passed"] is True,
          f"score={g_reward['score']}/{g_reward['max_score']}, breakdown={g_reward['breakdown']}")
    g_held = next((b for b in g_reward["breakdown"] if b["check_id"] == "held_out_contradiction_absent"), {})
    check("B: GOOD answer -> held_out_absent check PASSES (no '30 days' leaked)", g_held.get("passed") is True)
    check("B: GOOD answer -> a receipt is present (input_hash/output_hash + timestamps)",
          bool(g_receipt.get("receipt_id")) and bool(g_receipt.get("input_hash"))
          and bool(g_receipt.get("output_hash")) and g_receipt.get("started_at") == _NOW)
    check("B: GOOD answer -> EnvironmentRunResult.serves_truth is False (answer measured, never served)",
          g_result["serves_truth"] is False)
    check("B: receipt is linked to the measurement (reward_result_id back-filled)",
          g_receipt.get("reward_result_id") == g_reward["reward_result_id"]
          and g_result.get("reward_result_id") == g_reward["reward_result_id"])

    # ---- C. BAD candidate answer (leaks the held-out '30 days') fails -------------------
    bad_answer = "Per our FAQ, the bank has 30 days to investigate and resolve a disputed electronic fund transfer."
    bad = cfpb.run_candidate("run-cfpb-bad", candidate_answer=bad_answer, now=_NOW)
    b_result, b_reward = bad["result"], bad["reward"]
    check("C: BAD answer (says '30 days') -> reward.passed False", b_reward["passed"] is False)
    b_held = next((x for x in b_reward["breakdown"] if x["check_id"] == "held_out_contradiction_absent"), {})
    check("C: BAD answer FAILS specifically on held_out_absent (the stale contradiction was leaked)",
          b_held.get("passed") is False, str(b_held))
    # the authoritative value is missing too, but the load-bearing failure is the held-out leak.
    b_val = next((x for x in b_reward["breakdown"] if x["check_id"] == "authoritative_value_present"), {})
    check("C: BAD answer also lacks the authoritative '10 business days' value", b_val.get("passed") is False)
    check("C: BAD answer output is still NOT marked truth (serves_truth False)", b_result["serves_truth"] is False)

    # ---- D. output != truth (no agent/LLM output is truth) + determinism ----------------
    check("D: no agent output is truth — result.serves_truth False AND reward.is_truth False (good + bad)",
          g_result["serves_truth"] is False and g_reward["is_truth"] is False
          and b_result["serves_truth"] is False and b_reward["is_truth"] is False)
    good_again = cfpb.run_candidate("run-cfpb-good", candidate_answer=good_answer, now=_NOW)
    check("D: deterministic — same (run_id, answer, now) -> identical reward_result_id + receipt_id",
          good_again["reward"]["reward_result_id"] == g_reward["reward_result_id"]
          and good_again["receipt"]["receipt_id"] == g_receipt["receipt_id"])
    # offline fixture fallback: an inline fixture (no seed file) yields the same authoritative answer.
    inline = cfpb.load_fixture(seed_path=Path("/nonexistent/seed-graph.json"))
    check("D: fixture loads offline even without the seed file (inline fallback)",
          inline["authoritative_answer"] == "10 business days" and inline["held_out_contradiction"] == "30 days")

    # negative control: a good answer that DROPS the source handle must fail the source-handle check.
    no_handle = cfpb.run_candidate("run-cfpb-nohandle", candidate_answer=good_answer, now=_NOW, source_handles=[])
    nh_src = next((x for x in no_handle["reward"]["breakdown"] if x["check_id"] == "source_handle_present"), {})
    check("D: negative control — dropping the source handle fails source_handle_present + the run",
          nh_src.get("passed") is False and no_handle["reward"]["passed"] is False)

    # ---- E. no baltor import -----------------------------------------------------------
    # Match a real IMPORT STATEMENT only (line-start, optional indent) — the module's docstring documents
    # the rule ("does NOT import src.baltor"), which is the invariant being stated, not a violation.
    text = _TELEON_MODULE.read_text()
    baltor_import = re.compile(r"^[ \t]*(?:import|from)[ \t]+src\.baltor\b", re.MULTILINE)
    check("E: the teleon cfpb module does not import src.baltor (encodes/reads the fixture locally)",
          not baltor_import.search(text))

    print("\n" + ("PASS — check_baltor_context_environment: environment.baltor.cfpb_context_governance.local@v1 "
                  "scores a GOOD '10 business days' answer (with a source handle) as passed=True and a BAD answer "
                  "that leaks the held-out '30 days' as passed=False (held_out_absent bites). No agent/LLM output "
                  "is marked truth (serves_truth / is_truth False); the fixture loads offline; the Teleon module "
                  "does not import src.baltor."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_baltor_context_environment.py --self-test")
    raise SystemExit(0)
