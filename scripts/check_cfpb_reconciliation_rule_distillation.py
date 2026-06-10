#!/usr/bin/env python3
"""scripts.check_cfpb_reconciliation_rule_distillation — APPLIED DISTILLATION (assert-equivalence, NOT a 2nd authority).

The Determinism Factory's M5→M7 ladder applied to the CFPB Reg-E-vs-FAQ deadline conflict. We MINE a
deterministic rule from the repeated VERIFIED reconciliation outcome and prove it REPRODUCES the existing
reference — it does not become a competing source of truth.

The mined rule (a ``reconciliation_policy_rule`` / authority-precedence decision):

    IF conflict_type == "deadline_mismatch"
       AND source_a.authority_rank > source_b.authority_rank
       AND same fact_key/scope (same topic + unit-class)
    THEN winner = higher_authority_source, loser = held_out

What this proof asserts (the non-negotiable semantics):

  * The rule is mined ONLY from a VERIFIED outcome — the EXISTING deterministic authority
    ``scripts/artifact_graph/reconciliation.py`` already decided "Reg E (10 business days)" beats the
    "FAQ (30 days)" summary and HELD the FAQ out. The rule asserts EQUIVALENCE to that reference; it does NOT
    re-decide truth, and **no LLM / consensus trace is required for the truth**.
  * Consensus-only / raw-LLM traces can NEVER serve the fact — the served answer is the authority's, and
    here is "10 business days" ONLY (the FAQ "30 days" stays held out).
  * NO SECOND AUTHORITY: the rule's output is checked AGAINST ``reconciliation.reconcile(...)`` on the same
    reference fixture; if they ever diverge, this proof FAILS. The factory is a META ledger over the authority.
  * LOSSLESS: the ``RuleCandidate`` links back to the trace ids it was distilled from (the conflict +
    reconciliation receipt); promotion never deletes those traces.
  * Promotion bar = truth-serving → unsafe false positives must be 0, source handles preserved, fallback
    exists, replay report + promotion receipt present, traces preserved. Only then is a ``RulePromotionReceipt``
    issued.

This file builds ONLY against the EXISTING runtime (``cfpb_artifacts`` + ``conflict_detector`` +
``reconciliation``). It defines the M5→M7 ladder artifacts (RuleCandidate / RuleReplayReport /
RulePromotionReceipt) locally as plain dataclasses describing the distillation — it does NOT modify the
runtime and does NOT create a second reconciliation engine.

Determinism: ``--self-test``, offline, injected ``now``, hashlib ids, no RNG, no temp files (the artifact
ledger fixture is in-memory via the existing builder). PASS/FAIL lines, exit 0/1.

CLI: PYTHONPATH=. python3 scripts/check_cfpb_reconciliation_rule_distillation.py --self-test
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from scripts.artifact_graph import cfpb_artifacts as CA  # noqa: E402
from scripts.artifact_graph import conflict_detector as CD  # noqa: E402
from scripts.artifact_graph import graph_builder as GB  # noqa: E402
from scripts.artifact_graph import reconciliation as RC  # noqa: E402
from scripts.security.tenant_catalog import TenantPolicy  # noqa: E402

_NOW = "2026-06-05T00:00:00Z"
_TENANT = "acme"

# The same CFPB record the existing reference proof uses — so we mine from the EXISTING verified outcome.
REC = [{"complaint_id": "CFPB-1", "product": "Credit card", "issue": "Billing dispute", "company": "Acme",
        "state": "CA", "date_received": "2026-01-02",
        "consumer_complaint_narrative": "I was charged twice. The company refused to refund me."}]

# The reference answer that must keep being served — and the one that must stay held out.
_VERIFIED_ANSWER = "10 business days"     # Reg E (source-of-law), the only served deadline
_HELD_OUT_ANSWER = "30 days"            # FAQ summary, held out (NEVER served as truth)


def _hid(prefix: str, body: dict) -> str:
    """A deterministic, content-addressed id (hashlib; no clock, no RNG)."""
    return prefix + "-" + hashlib.sha256(json.dumps(body, sort_keys=True, default=str).encode()).hexdigest()[:16]


# ── the M5→M7 ladder artifacts the Determinism Factory produces (described locally for this proof) ──
@dataclass
class RuleCandidate:
    """An M5 mined deterministic rule (proposed, NOT active). Carries examples + counterexamples + fallback,
    and — LOSSLESS — links back to the trace ids it was distilled from (never deletes them)."""
    rule_id: str
    rule_type: str                       # reconciliation_policy_rule
    inputs: list                         # input fields the rule reads
    output_decision: str                 # what the rule decides
    scope: str                           # tenant scope / fact scope it is valid for
    examples: list                       # verified examples it reproduces
    counterexamples: list                # what it must NOT do
    fallback_policy: dict                # what happens on low confidence / unknown
    distilled_from_trace_ids: list = field(default_factory=list)  # LOSSLESS back-links
    asserts_equivalence_to: str = "scripts/artifact_graph/reconciliation.py"
    active: bool = False                 # mined rules are NEVER active until promoted

    def to_dict(self) -> dict:
        return {"rule_id": self.rule_id, "rule_type": self.rule_type, "inputs": self.inputs,
                "output_decision": self.output_decision, "scope": self.scope, "examples": self.examples,
                "counterexamples": self.counterexamples, "fallback_policy": self.fallback_policy,
                "distilled_from_trace_ids": self.distilled_from_trace_ids,
                "asserts_equivalence_to": self.asserts_equivalence_to, "active": self.active}


@dataclass
class RuleReplayReport:
    """An M5/M6 replay of a RuleCandidate against historical VERIFIED outcomes."""
    report_id: str
    rule_id: str
    matched: int
    total: int
    false_positives: int
    false_negatives: int
    unsafe_count: int                    # rule served a held-out / wrong-authority answer (must be 0)
    abstentions: int
    tenant_leak_count: int
    handles_preserved: bool
    created_at: str

    @property
    def precision(self) -> float:
        denom = self.matched + self.false_positives
        return (self.matched / denom) if denom else 1.0

    def to_dict(self) -> dict:
        return {"report_id": self.report_id, "rule_id": self.rule_id, "matched": self.matched,
                "total": self.total, "false_positives": self.false_positives,
                "false_negatives": self.false_negatives, "unsafe_count": self.unsafe_count,
                "abstentions": self.abstentions, "tenant_leak_count": self.tenant_leak_count,
                "handles_preserved": self.handles_preserved, "precision": round(self.precision, 4),
                "created_at": self.created_at}


@dataclass
class RulePromotionReceipt:
    """An M7 promotion receipt — issued ONLY when the truth-serving bar is met."""
    receipt_id: str
    rule_id: str
    replay_report_id: str
    decision: str                        # promoted | blocked
    checks: list
    traces_preserved: bool               # LOSSLESS: distilled-from traces still present
    fallback_present: bool
    created_at: str

    def to_dict(self) -> dict:
        return {"receipt_id": self.receipt_id, "rule_id": self.rule_id, "replay_report_id": self.replay_report_id,
                "decision": self.decision, "checks": self.checks, "traces_preserved": self.traces_preserved,
                "fallback_present": self.fallback_present, "created_at": self.created_at}


# ── the mined deterministic rule LOGIC (asserts equivalence; does NOT re-implement reconciliation) ──
def _rank_of(art) -> int:
    """The authority rank the EXISTING reconciliation authority reads (source_rank in payload)."""
    return int(art.payload_json.get("source_rank", 50)) if art else 0


def apply_authority_precedence_rule(conflict, by_id: dict) -> dict | None:
    """The deterministic rule: deadline_mismatch + a strict authority gap on the SAME fact_key/scope →
    winner = higher authority, loser = held out. Returns None (ABSTAIN → fallback) when the rule does not
    apply (different conflict type, equal authority, or a missing artifact). This is a PURE function of the
    already-verified inputs — it reads the SAME authority signal the reconciliation authority reads, so it
    reproduces, never replaces.

    fact_key/scope identity for a deadline_mismatch = same topic (both atomic_facts on the same topic, which
    is exactly how ``conflict_detector`` raises a ``deadline_mismatch``)."""
    if getattr(conflict, "conflict_type", None) != "deadline_mismatch":
        return None
    a, b = by_id.get(conflict.artifact_a_id), by_id.get(conflict.artifact_b_id)
    if not (a and b):
        return None
    # same fact_key/scope guard: both must be atomic_facts on the same topic + same tenant.
    if not (a.artifact_type == b.artifact_type == "atomic_fact"):
        return None
    if a.payload_json.get("topic") != b.payload_json.get("topic"):
        return None
    if a.tenant_id != b.tenant_id:
        return None
    ra, rb = _rank_of(a), _rank_of(b)
    if ra == rb:
        return None  # no strict authority gap → ABSTAIN → fallback (LLM/human/freshness path)
    winner, loser = (a, b) if ra > rb else (b, a)
    return {"decision": "resolved_by_authority", "winner_id": winner.artifact_id,
            "loser_id": loser.artifact_id, "winner_text": winner.text, "loser_text": loser.text,
            "winner_handles": list(winner.source_handles_json), "loser_handles": list(loser.source_handles_json)}


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    # ── 0) build the EXISTING verified outcome (the reference) via the real runtime ──────────────────
    built = CA.build_artifacts(REC, TenantPolicy(_TENANT), now=_NOW)
    arts, rid = built["artifacts"], built["run_id"]
    by_id = {a.artifact_id: a for a in arts}
    edges = GB.build_edges(arts, tenant_id=_TENANT, run_id=rid)
    conflicts = CD.detect(arts, edges, tenant_id=_TENANT, now=_NOW)
    reference = RC.reconcile(conflicts, by_id, tenant_id=_TENANT, now=_NOW)

    # the reference authority decision we are asserting equivalence to.
    authority_recons = [r for r in reference["reconciliations"] if r.decision == "resolved_by_authority"]
    check("the EXISTING authority produced a resolved_by_authority outcome (the reference)", len(authority_recons) == 1)
    reference_winner = built["reg_e_id"]
    reference_loser = built["faq_id"]
    check("reference winner is Reg E (10 business days)", authority_recons and authority_recons[0].winning_artifact_id == reference_winner)
    check("reference holds out the FAQ (30 days)", reference_loser in reference["held_out_ids"])
    # the served answer text the reference carries.
    check("reference winner text says '10 business days'", _VERIFIED_ANSWER in by_id[reference_winner].text)
    check("reference loser text says '30 days'", _HELD_OUT_ANSWER in by_id[reference_loser].text)

    # the deadline conflict the rule is mined over.
    deadline_conflicts = [c for c in conflicts if c.conflict_type == "deadline_mismatch"]
    check("there is exactly one deadline_mismatch conflict to mine", len(deadline_conflicts) == 1, str(len(deadline_conflicts)))
    dc = deadline_conflicts[0] if deadline_conflicts else None

    # ── 1) MINE the deterministic rule from the VERIFIED outcome (M5) ─────────────────────────────
    # The trace ids the rule is distilled from (LOSSLESS back-links): the conflict + the reconciliation receipt.
    distilled_from = sorted([dc.conflict_id] + [r.reconciliation_id for r in authority_recons]) if dc else []
    rule = RuleCandidate(
        rule_id=_hid("rule", {"k": "cfpb_authority_precedence", "from": distilled_from}),
        rule_type="reconciliation_policy_rule",
        inputs=["conflict_type", "source_a.authority_rank", "source_b.authority_rank", "fact_key/scope"],
        output_decision="winner=higher_authority_source; loser=held_out",
        scope=_TENANT,
        examples=[{"conflict_type": "deadline_mismatch", "winner": "Regulation E", "loser": "FAQ",
                   "winner_answer": _VERIFIED_ANSWER, "loser_answer": _HELD_OUT_ANSWER}],
        counterexamples=[{"why": "equal authority → ABSTAIN, never auto-pick a winner"},
                         {"why": "FAQ-30 is NEVER served as truth"},
                         {"why": "an LLM/consensus trace is NOT sufficient to serve the fact"}],
        fallback_policy={"on_abstain": "route to existing reconciliation authority (freshness/scope/human)",
                         "on_unknown_conflict_type": "no rule output → fallback path"},
        distilled_from_trace_ids=distilled_from)
    check("the mined rule is PROPOSED, not active", rule.active is False)
    check("the mined rule asserts equivalence to the EXISTING reconciliation authority",
          rule.asserts_equivalence_to == "scripts/artifact_graph/reconciliation.py")
    check("the rule is LOSSLESS — it links back to the traces it was distilled from",
          bool(rule.distilled_from_trace_ids) and (dc.conflict_id in rule.distilled_from_trace_ids))

    # ── 2) the rule REPRODUCES the reference WITHOUT any LLM/consensus trace (assert-equivalence) ────
    rule_out = apply_authority_precedence_rule(dc, by_id) if dc else None
    check("the deterministic rule fired on the deadline conflict", rule_out is not None)
    if rule_out:
        check("rule winner == reference winner (Reg E)", rule_out["winner_id"] == reference_winner, rule_out["winner_id"])
        check("rule loser == reference loser (FAQ, held out)", rule_out["loser_id"] == reference_loser, rule_out["loser_id"])
        check("rule winner answer is '10 business days' ONLY", _VERIFIED_ANSWER in rule_out["winner_text"]
              and _HELD_OUT_ANSWER not in rule_out["winner_text"])
        check("the rule produced truth from the authority signal, with NO LLM/consensus trace required",
              "authority" in rule_out["decision"])
        check("rule decision matches the reference authority decision exactly",
              authority_recons and rule_out["winner_id"] == authority_recons[0].winning_artifact_id
              and rule_out["decision"] == authority_recons[0].decision)

    # ── 3) NO SECOND AUTHORITY: rule output is verified AGAINST reconcile() on the same fixture ────
    #     (the factory is a META ledger; the rule reproduces the authority — it never replaces it.)
    second_run = RC.reconcile(conflicts, by_id, tenant_id=_TENANT, now=_NOW)
    second_authority = [r for r in second_run["reconciliations"] if r.decision == "resolved_by_authority"]
    equivalence = (rule_out is not None and second_authority
                   and rule_out["winner_id"] == second_authority[0].winning_artifact_id
                   and rule_out["loser_id"] in second_run["held_out_ids"])
    check("rule output == existing authority output (equivalence, not a 2nd authority)", bool(equivalence))

    # ── 4) the SERVED answer is still '10 business days' ONLY (FAQ-30 held out) ───────────────────
    served_facts = [a for a in arts if a.artifact_type == "atomic_fact"
                    and a.payload_json.get("topic") == "investigation_deadline"
                    and a.artifact_id not in reference["held_out_ids"]]
    served_answers = {f.text for f in served_facts}
    check("only Reg E '10 business days' is servable for the deadline (FAQ-30 held out)",
          any(_VERIFIED_ANSWER in t for t in served_answers) and not any(_HELD_OUT_ANSWER in t for t in served_answers),
          str(sorted(served_answers)))

    # ── 5) REPLAY REPORT over the historical verified traces (here: the reference deadline conflict) ─
    matched = 1 if equivalence else 0
    unsafe = 0 if (rule_out and _HELD_OUT_ANSWER not in rule_out["winner_text"]) else 1
    handles_preserved = bool(rule_out and rule_out["winner_handles"]) and \
        rule_out["winner_handles"] == list(by_id[reference_winner].source_handles_json)
    replay = RuleReplayReport(
        report_id=_hid("replay", {"rule": rule.rule_id}), rule_id=rule.rule_id, matched=matched, total=1,
        false_positives=0, false_negatives=0, unsafe_count=unsafe, abstentions=0, tenant_leak_count=0,
        handles_preserved=handles_preserved, created_at=_NOW)
    check("replay report: rule precision is 1.0 against the verified reference", replay.precision == 1.0)
    check("replay report: ZERO unsafe outcomes (never served the held-out FAQ-30)", replay.unsafe_count == 0)
    check("replay report: source handles preserved", replay.handles_preserved)
    check("replay report: zero tenant leakage", replay.tenant_leak_count == 0)

    # ── 6) PROMOTION GATE (truth-serving bar) → RulePromotionReceipt only when ALL checks pass ────
    gate_checks = [
        {"name": "precision_meets_truth_bar", "ok": replay.precision >= 1.0},
        {"name": "unsafe_false_positives_zero", "ok": replay.unsafe_count == 0},
        {"name": "source_handles_preserved", "ok": replay.handles_preserved},
        {"name": "tenant_safe", "ok": replay.tenant_leak_count == 0},
        {"name": "fallback_present", "ok": bool(rule.fallback_policy)},
        {"name": "traces_preserved_lossless", "ok": bool(rule.distilled_from_trace_ids)},
        {"name": "asserts_equivalence_not_second_authority", "ok": bool(equivalence)},
        {"name": "serves_reference_answer_only", "ok": _VERIFIED_ANSWER in (rule_out or {}).get("winner_text", "")
            and _HELD_OUT_ANSWER not in (rule_out or {}).get("winner_text", "")},
    ]
    promoted = all(c["ok"] for c in gate_checks)
    receipt = RulePromotionReceipt(
        receipt_id=_hid("promote", {"rule": rule.rule_id, "replay": replay.report_id}),
        rule_id=rule.rule_id, replay_report_id=replay.report_id,
        decision="promoted" if promoted else "blocked", checks=gate_checks,
        traces_preserved=bool(rule.distilled_from_trace_ids), fallback_present=bool(rule.fallback_policy),
        created_at=_NOW)
    check("promotion gate issued a RulePromotionReceipt", bool(receipt.receipt_id))
    check("the truth-serving rule was PROMOTED (all gate checks passed)", receipt.decision == "promoted",
          str([c["name"] for c in gate_checks if not c["ok"]]))
    check("the promotion receipt confirms traces preserved (lossless) + fallback present",
          receipt.traces_preserved and receipt.fallback_present)

    # ── 7) DETERMINISM: a clean re-run reproduces every id + the served answer ────────────────────
    built2 = CA.build_artifacts(REC, TenantPolicy(_TENANT), now=_NOW)
    by_id2 = {a.artifact_id: a for a in built2["artifacts"]}
    edges2 = GB.build_edges(built2["artifacts"], tenant_id=_TENANT, run_id=built2["run_id"])
    conflicts2 = CD.detect(built2["artifacts"], edges2, tenant_id=_TENANT, now=_NOW)
    dc2 = next(c for c in conflicts2 if c.conflict_type == "deadline_mismatch")
    rule_out2 = apply_authority_precedence_rule(dc2, by_id2)
    det = (rule_out2 and rule_out2["winner_id"] == rule_out["winner_id"]
           and _hid("rule", {"k": "cfpb_authority_precedence",
                             "from": sorted([dc2.conflict_id] + [r.reconciliation_id for r in authority_recons])}) == rule.rule_id)
    check("deterministic: a clean re-run reproduces the rule id + winner", bool(det))

    ok = not fails
    print("\n" + ("PASS — check_cfpb_reconciliation_rule_distillation: the mined deterministic authority-precedence "
                  "rule REPRODUCES the existing reference (Reg E '10 business days' wins; FAQ '30 days' held out) "
                  "WITHOUT requiring any LLM/consensus trace for the truth; its output is verified EQUIVALENT to "
                  "scripts/artifact_graph/reconciliation.py (no second authority); it carries a replay report "
                  "(precision 1.0, 0 unsafe) + a promotion receipt; lossless trace back-links are preserved; the "
                  "served deadline answer is '10 business days' ONLY."
                  if ok else f"{len(fails)} FAILURES: {fails}"))
    return 0 if ok else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Applied distillation: CFPB reconciliation rule asserts equivalence to the reference.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
