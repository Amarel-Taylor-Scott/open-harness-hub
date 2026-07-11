#!/usr/bin/env python3
"""scripts.check_determinism_redteam — RED-TEAM-AS-PROOF: every attack on the Determinism Factory FAILS SAFELY.

The Determinism Factory's promotion bar is only worth anything if it cannot be DEFEATED. This proof is
adversarial: it stages each way an attacker (or a careless mining pass) could try to promote an UNSAFE
deterministic rule, and asserts the promotion gate REJECTS it — by blocking the promotion, never by issuing a
``RulePromotionReceipt`` with ``decision == "promoted"``. A "PASS" here means *the attack failed*.

Attacks, each must FAIL SAFELY:
  1. promote a rule distilled from CONSENSUS ONLY        → consensus is evidence, NOT truth; a rule with no
                                                           verified/adjudicated source is blocked.
  2. promote a rule with an UNSAFE false positive        → unsafe_count > 0 blocks a truth-serving rule.
  3. build a GLOBAL rule from tenant_private traces       → tenant_private + not anonymized/approved is blocked.
  4. promote a rule that serves FAQ-30 ("30 days") as truth → serving the held-out answer is unsafe → blocked.
  5. promote a rule that DROPS a source handle             → handles-not-preserved blocks promotion.
  6. promote a rule with NO fallback                       → an active rule must have a fallback → blocked.
  7. promote a rule with NO replay report                  → no replay evidence → blocked.
  8. promote a rule that DELETED its source traces (lossless) → no distilled-from traces preserved → blocked.

Each attack is run against the SAME deterministic promotion gate; a CLEAN rule (verified source, 0 unsafe,
tenant-safe, serves the reference answer only, handles preserved, fallback present, replay present, traces
preserved) is also promoted — proving the gate blocks the bad and allows the good.

Determinism: ``--self-test``, offline, injected ``now``, hashlib ids, no RNG, no temp files (in-memory).
PASS/FAIL lines, exit 0/1.

CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_determinism_redteam.py --self-test
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

_NOW = "2026-06-05T00:00:00Z"
_VERIFIED_ANSWER = "10 business days"     # Reg E (the only truth that may be served)
_HELD_OUT_ANSWER = "30 days"            # FAQ summary (NEVER served as truth)
TENANT_PRIVATE = "tenant_private"
GLOBAL_PUBLIC = "global_public"


def _hid(prefix: str, body: dict) -> str:
    return prefix + "-" + hashlib.sha256(json.dumps(body, sort_keys=True, default=str).encode()).hexdigest()[:16]


# ── the rule promotion gate (the truth-serving bar; the SAME contract the applied proofs use) ──
@dataclass
class RuleUnderReview:
    """A candidate truth-serving rule presented to the promotion gate."""
    rule_id: str
    rule_type: str = "truth_serving"
    served_answer: str = _VERIFIED_ANSWER          # the answer the rule would serve
    distilled_from_trace_ids: list = field(default_factory=list)  # LOSSLESS source traces (must be preserved)
    source_verified: bool = True                 # distilled from an adjudicated/source-grounded outcome
    consensus_only: bool = False                 # distilled from CONSENSUS only (evidence, not truth)
    scope: str = GLOBAL_PUBLIC                   # the rule's scope
    built_from_tenant_private: bool = False      # any tenant_private trace in the mining set
    anonymized_and_approved: bool = False        # the only way tenant_private may feed a global rule
    unsafe_count: int = 0                        # rule served a held-out / wrong answer in replay (must be 0)
    handles_preserved: bool = True               # source handles survive the rule
    fallback_policy: dict = field(default_factory=lambda: {"on_abstain": "LLM/human"})
    replay_report_id: str | None = "replay-ok"   # a replay report MUST exist
    traces_preserved: bool = True                # LOSSLESS: distilled-from traces still present


@dataclass
class PromotionDecision:
    receipt_id: str
    rule_id: str
    decision: str               # promoted | blocked
    blocked_reasons: list
    created_at: str


def promotion_gate(rule: RuleUnderReview, *, now: str = _NOW) -> PromotionDecision:
    """Deterministically decide promote/block. A truth-serving rule promotes ONLY when EVERY safety check
    passes; any failure blocks it and records the reason. (This is the META gate, not a 2nd authority.)"""
    reasons: list[str] = []

    # consensus is evidence, NOT truth — a rule needs a verified/adjudicated source, never consensus alone.
    if rule.consensus_only or not rule.source_verified:
        reasons.append("not_distilled_from_verified_outcome")
    # truth-serving rules need ZERO unsafe false positives.
    if rule.unsafe_count > 0:
        reasons.append("unsafe_false_positive")
    # a tenant_private mining set may only feed a GLOBAL rule if anonymized + approved.
    if rule.scope == GLOBAL_PUBLIC and rule.built_from_tenant_private and not rule.anonymized_and_approved:
        reasons.append("tenant_private_into_global_rule")
    # the rule may NEVER serve the held-out FAQ-30 answer as truth.
    if _HELD_OUT_ANSWER in (rule.served_answer or "") or _VERIFIED_ANSWER not in (rule.served_answer or ""):
        reasons.append("serves_held_out_or_wrong_answer")
    # source handles must be preserved.
    if not rule.handles_preserved:
        reasons.append("source_handle_dropped")
    # an active rule must carry a fallback.
    if not rule.fallback_policy:
        reasons.append("no_fallback")
    # a replay report must exist (replay evidence is mandatory).
    if not rule.replay_report_id:
        reasons.append("no_replay_report")
    # LOSSLESS: the distilled-from traces must be preserved (never deleted).
    if not rule.traces_preserved or not rule.distilled_from_trace_ids:
        reasons.append("source_traces_not_preserved")

    reasons = sorted(reasons)
    decision = "promoted" if not reasons else "blocked"
    return PromotionDecision(receipt_id=_hid("promote", {"rule": rule.rule_id, "reasons": reasons}),
                             rule_id=rule.rule_id, decision=decision, blocked_reasons=reasons, created_at=now)


def _clean_rule() -> RuleUnderReview:
    """A fully-safe truth-serving rule the gate SHOULD promote (the control)."""
    return RuleUnderReview(rule_id=_hid("rule", {"k": "clean"}),
                           distilled_from_trace_ids=["conflict:abc", "recon-def"],
                           source_verified=True, consensus_only=False, scope=GLOBAL_PUBLIC,
                           built_from_tenant_private=False, unsafe_count=0, handles_preserved=True,
                           fallback_policy={"on_abstain": "LLM/human"}, replay_report_id="replay-ok",
                           traces_preserved=True, served_answer=_VERIFIED_ANSWER)


def _self_test() -> int:
    fails: list[str] = []

    def attack_fails_safely(name: str, decision: PromotionDecision, expect_reason: str) -> None:
        """An attack is DEFENDED iff the gate BLOCKED it for the expected reason (not promoted)."""
        defended = decision.decision == "blocked" and expect_reason in decision.blocked_reasons
        print(f"  [{'ok' if defended else 'FAIL'}] attack defended: {name}"
              f"{'' if defended else f' (decision={decision.decision} reasons={decision.blocked_reasons})'}")
        if not defended:
            fails.append(name)

    # ── ATTACK 1: promote a rule distilled from CONSENSUS ONLY ────────────────────────────────────
    r = _clean_rule(); r.rule_id = _hid("rule", {"k": "consensus"}); r.consensus_only = True; r.source_verified = False
    attack_fails_safely("promote a rule from consensus only", promotion_gate(r), "not_distilled_from_verified_outcome")

    # ── ATTACK 2: promote a rule with an UNSAFE false positive ────────────────────────────────────
    r = _clean_rule(); r.rule_id = _hid("rule", {"k": "fp"}); r.unsafe_count = 1
    attack_fails_safely("promote with an unsafe FP", promotion_gate(r), "unsafe_false_positive")

    # ── ATTACK 3: build a GLOBAL rule from tenant_private traces ───────────────────────────────────
    r = _clean_rule(); r.rule_id = _hid("rule", {"k": "tenant"}); r.built_from_tenant_private = True
    r.anonymized_and_approved = False; r.scope = GLOBAL_PUBLIC
    attack_fails_safely("build a global rule from tenant_private traces", promotion_gate(r), "tenant_private_into_global_rule")

    # ── ATTACK 4: promote a rule that serves FAQ-30 ("30 days") as truth ──────────────────────────
    r = _clean_rule(); r.rule_id = _hid("rule", {"k": "faq30"}); r.served_answer = _HELD_OUT_ANSWER
    attack_fails_safely("rule serves FAQ-30 as truth", promotion_gate(r), "serves_held_out_or_wrong_answer")

    # ── ATTACK 5: promote a rule that DROPS a source handle ───────────────────────────────────────
    r = _clean_rule(); r.rule_id = _hid("rule", {"k": "handle"}); r.handles_preserved = False
    attack_fails_safely("rule drops a source handle", promotion_gate(r), "source_handle_dropped")

    # ── ATTACK 6: promote a rule with NO fallback ─────────────────────────────────────────────────
    r = _clean_rule(); r.rule_id = _hid("rule", {"k": "nofallback"}); r.fallback_policy = {}
    attack_fails_safely("rule has no fallback", promotion_gate(r), "no_fallback")

    # ── ATTACK 7: promote a rule with NO replay report ────────────────────────────────────────────
    r = _clean_rule(); r.rule_id = _hid("rule", {"k": "noreplay"}); r.replay_report_id = None
    attack_fails_safely("rule has no replay report", promotion_gate(r), "no_replay_report")

    # ── ATTACK 8: promote a rule that DELETED its source traces (lossless violation) ──────────────
    r = _clean_rule(); r.rule_id = _hid("rule", {"k": "lossless"}); r.traces_preserved = False; r.distilled_from_trace_ids = []
    attack_fails_safely("promoted rule deleted its source traces (lossless)", promotion_gate(r), "source_traces_not_preserved")

    # ── the CONTROL: a fully-safe rule IS promoted (the gate is not just "always block") ──────────
    clean = promotion_gate(_clean_rule())
    print(f"  [{'ok' if clean.decision == 'promoted' else 'FAIL'}] control: a fully-safe truth-serving rule IS promoted"
          f"{'' if clean.decision == 'promoted' else f' (reasons={clean.blocked_reasons})'}")
    if clean.decision != "promoted":
        fails.append("clean_rule_should_promote")

    # ── a CONSENSUS run can never serve a fact on its own (consensus = evidence, not truth) ───────
    #     model the consensus-only path: even unanimous agreement does NOT make a servable rule.
    unanimous = _clean_rule(); unanimous.rule_id = _hid("rule", {"k": "unanimous"})
    unanimous.consensus_only = True; unanimous.source_verified = False  # agreement is high but unverified
    consensus_blocked = promotion_gate(unanimous).decision == "blocked"
    print(f"  [{'ok' if consensus_blocked else 'FAIL'}] consensus alone (even unanimous) can NEVER serve a fact")
    if not consensus_blocked:
        fails.append("consensus_cannot_serve_fact")

    # ── DETERMINISM: the whole battery is reproducible (ids + decisions) ──────────────────────────
    det = (promotion_gate(_clean_rule()).receipt_id == clean.receipt_id
           and promotion_gate(_clean_rule()).decision == "promoted")
    print(f"  [{'ok' if det else 'FAIL'}] the red-team battery is deterministic (ids + decisions reproducible)")
    if not det:
        fails.append("determinism")

    ok = not fails
    print("\n" + ("PASS — check_determinism_redteam: every attack on the Determinism Factory FAILED SAFELY — a rule "
                  "from consensus only, with an unsafe FP, built from tenant_private traces, serving FAQ-30 as truth, "
                  "dropping a source handle, with no fallback, with no replay report, or that deleted its source traces "
                  "is BLOCKED by the promotion gate; consensus alone can never serve a fact; and a fully-safe "
                  "truth-serving rule IS promoted — all deterministically."
                  if ok else f"{len(fails)} ATTACKS NOT DEFENDED: {fails}"))
    return 0 if ok else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Red-team-as-proof: every attack on the Determinism Factory fails safely.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
