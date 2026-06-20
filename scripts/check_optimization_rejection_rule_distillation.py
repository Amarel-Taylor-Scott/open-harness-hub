#!/usr/bin/env python3
"""scripts.check_optimization_rejection_rule_distillation — APPLIED DISTILLATION: deterministic optimization-reject rules.

The Determinism Factory applied to the repeated VERIFIED optimization-rejection decision. The optimizer keeps
REJECTING candidate context packs for the SAME reasons (dropped a source handle, dropped an answer-critical
fact, served a held-out conflict, promoted a narrative allegation, crossed a tenant boundary, lacks a
promotion/verification receipt). That repeated verified verdict can become a deterministic reject rule. This
proof DEFINES the rule and proves each reject row MATCHES the EXISTING optimizer/consumption authority.

ASSERT-EQUIVALENCE (no second optimizer): every rejection the rule fires is checked AGAINST the EXISTING
``scripts/runtime/optimization.py`` authority on the same fixture:
  * "drops an answer-critical fact" / "drops a source handle" / "promotes a held-out or allegation" /
    "crosses a tenant boundary"  → checked against ``OptimizationHarness.regressions(...)`` (the regression
    gate that makes the harness ``decision == "reject"``).
  * "lacks a promotion/verification receipt"  → checked against ``ConsumptionReadinessGate.assess(...)``
    (a pack is NOT consumable without receipts).
If the rule's verdict ever disagrees with the existing authority, this proof FAILS. The rule reproduces the
optimizer's rejections — it never replaces the optimizer.

Determinism: ``--self-test``, offline, injected ``now``, hashlib ids, no RNG, in-memory fixtures (no temp files).
PASS/FAIL lines, exit 0/1.

CLI: PYTHONPATH=. python3 scripts/check_optimization_rejection_rule_distillation.py --self-test
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from scripts.runtime.optimization import (  # noqa: E402
    ConsumptionReadinessGate,
    OptimizationHarness,
    _handles,
)

_NOW = "2026-06-05T00:00:00Z"
_TENANT = "acme"
_OTHER = "globex"
_HANDLE = "ctx://reg-e/1005.11#deadline"


def _hid(prefix: str, body: dict) -> str:
    return prefix + "-" + hashlib.sha256(json.dumps(body, sort_keys=True, default=str).encode()).hexdigest()[:16]


# ── the mined deterministic optimization-reject rule (PURE; reads the same signals the harness reads) ──
def optimization_reject_reasons(*, baseline_artifacts: list, candidate_artifacts: list, answer_fact_ids: list,
                                excluded_ids: list, tenant_id: str,
                                verification_receipt: dict | None = None,
                                promotion_receipt: dict | None = None) -> list[str]:
    """Return the SORTED list of deterministic reject reasons for a candidate pack (empty list = no reason to
    reject). Mirrors the EXISTING optimizer's regression gate + the consumption gate's receipt requirement."""
    excluded = set(excluded_ids or ())
    cand_ids = {a.get("artifact_id") for a in candidate_artifacts}
    base_handles = {a.get("artifact_id"): set(_handles(a)) for a in baseline_artifacts}
    reasons: list[str] = []

    # 1) drops an answer-critical fact
    if not set(answer_fact_ids) <= cand_ids:
        reasons.append("drops_answer_critical_fact")
    # 2) drops a source handle (an artifact that HAD a handle in the baseline now has none)
    if any(base_handles.get(a.get("artifact_id")) and not set(_handles(a)) for a in candidate_artifacts):
        reasons.append("drops_source_handle")
    # 3) includes a held-out conflict as a served fact, or promotes a narrative allegation
    if any(a.get("artifact_id") in excluded for a in candidate_artifacts):
        reasons.append("serves_held_out_conflict")
    if any(a.get("claim_type") == "narrative_allegation" for a in candidate_artifacts):
        reasons.append("promotes_narrative_allegation")
    # 4) crosses a tenant boundary (a tenant_private artifact from another tenant)
    if any(a.get("tenant_id") and a.get("tenant_id") != tenant_id and a.get("scope") == "tenant_private"
           for a in candidate_artifacts):
        reasons.append("crosses_tenant_boundary")
    # 5) lacks a promotion / verification receipt
    if not (verification_receipt and verification_receipt.get("receipt_id")
            and promotion_receipt and promotion_receipt.get("receipt_id")):
        reasons.append("lacks_promotion_receipt")
    return sorted(reasons)


@dataclass
class RuleCandidate:
    rule_id: str
    rule_type: str                       # optimization_reject_rule
    reject_reasons: list                 # the deterministic reject rows
    fallback_policy: dict
    asserts_equivalence_to: str = "scripts/runtime/optimization.py"
    active: bool = False


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    harness = OptimizationHarness()
    gate = ConsumptionReadinessGate()

    # ── a clean, promotable baseline pack (one answer-critical fact carrying a handle) ────────────
    good_fact = {"artifact_id": "f1", "artifact_type": "atomic_fact", "subject": "regE", "predicate": "deadline",
                 "object": "10 business days", "source_handle": _HANDLE, "tenant_id": _TENANT, "scope": "global_public"}
    extra_fact = {"artifact_id": "f2", "artifact_type": "atomic_fact", "subject": "regE", "predicate": "scope",
                  "object": "consumer", "source_handle": _HANDLE, "tenant_id": _TENANT, "scope": "global_public"}
    baseline = {"pack_id": "pk1", "tenant_id": _TENANT, "artifacts": [good_fact, extra_fact]}
    answer_ids = ["f1"]

    def harness_rejects(candidate_arts, *, excluded=()):
        """Truth from the EXISTING authority: run the harness regression gate over a candidate (identity opt)."""
        cand_pack = {"pack_id": "pk1", "tenant_id": _TENANT, "artifacts": candidate_arts}

        class _Identity:
            name = "identity"
            def optimize(self, pack, *, signals):
                return cand_pack
        out = harness.run(baseline, _Identity(), answer_fact_ids=answer_ids,
                          signals={"excluded_ids": list(excluded)}, now=_NOW)
        return out["decision"] == "reject", {r.name: r.ok for r in out["regressions"]}

    # ── case-by-case: the rule reason fires AND the existing authority also rejects ───────────────
    # (A) drops an answer-critical fact (f1 removed)
    cand_a = [extra_fact]
    reasons_a = optimization_reject_reasons(baseline_artifacts=baseline["artifacts"], candidate_artifacts=cand_a,
                                            answer_fact_ids=answer_ids, excluded_ids=[], tenant_id=_TENANT,
                                            verification_receipt={"receipt_id": "vr"}, promotion_receipt={"receipt_id": "pr"})
    auth_a, _ = harness_rejects(cand_a)
    check("drops_answer_critical_fact: rule fires", "drops_answer_critical_fact" in reasons_a)
    check("drops_answer_critical_fact: existing optimizer also REJECTS (equivalence)", auth_a)

    # (B) drops a source handle (f1 keeps id but loses its handle)
    f1_no_handle = {k: v for k, v in good_fact.items() if k != "source_handle"}
    cand_b = [f1_no_handle, extra_fact]
    reasons_b = optimization_reject_reasons(baseline_artifacts=baseline["artifacts"], candidate_artifacts=cand_b,
                                            answer_fact_ids=answer_ids, excluded_ids=[], tenant_id=_TENANT,
                                            verification_receipt={"receipt_id": "vr"}, promotion_receipt={"receipt_id": "pr"})
    auth_b, _ = harness_rejects(cand_b)
    check("drops_source_handle: rule fires", "drops_source_handle" in reasons_b)
    check("drops_source_handle: existing optimizer also REJECTS (equivalence)", auth_b)

    # (C) serves a held-out conflict (excluded id stays in the served pack)
    held = {"artifact_id": "faq30", "artifact_type": "atomic_fact", "subject": "faq", "predicate": "deadline",
            "object": "30 days", "source_handle": "ctx://faq/30", "tenant_id": _TENANT, "scope": "global_public"}
    baseline_with_held = {"pack_id": "pk1", "tenant_id": _TENANT, "artifacts": [good_fact, extra_fact, held]}
    cand_c = [good_fact, extra_fact, held]

    class _IdC:
        name = "identity"
        def optimize(self, pack, *, signals):
            return {"pack_id": "pk1", "tenant_id": _TENANT, "artifacts": cand_c}
    out_c = harness.run(baseline_with_held, _IdC(), answer_fact_ids=answer_ids,
                        signals={"excluded_ids": ["faq30"]}, now=_NOW)
    reasons_c = optimization_reject_reasons(baseline_artifacts=baseline_with_held["artifacts"], candidate_artifacts=cand_c,
                                            answer_fact_ids=answer_ids, excluded_ids=["faq30"], tenant_id=_TENANT,
                                            verification_receipt={"receipt_id": "vr"}, promotion_receipt={"receipt_id": "pr"})
    check("serves_held_out_conflict: rule fires", "serves_held_out_conflict" in reasons_c)
    check("serves_held_out_conflict: existing optimizer also REJECTS (equivalence)", out_c["decision"] == "reject")

    # (D) promotes a narrative allegation
    allegation = {"artifact_id": "alg1", "artifact_type": "narrative_allegation", "claim_type": "narrative_allegation",
                  "subject": "x", "predicate": "y", "object": "z", "source_handle": _HANDLE, "tenant_id": _TENANT}
    cand_d = [good_fact, extra_fact, allegation]
    baseline_with_alg = {"pack_id": "pk1", "tenant_id": _TENANT, "artifacts": [good_fact, extra_fact, allegation]}

    class _IdD:
        name = "identity"
        def optimize(self, pack, *, signals):
            return {"pack_id": "pk1", "tenant_id": _TENANT, "artifacts": cand_d}
    out_d = harness.run(baseline_with_alg, _IdD(), answer_fact_ids=answer_ids, signals={"excluded_ids": []}, now=_NOW)
    reasons_d = optimization_reject_reasons(baseline_artifacts=baseline_with_alg["artifacts"], candidate_artifacts=cand_d,
                                            answer_fact_ids=answer_ids, excluded_ids=[], tenant_id=_TENANT,
                                            verification_receipt={"receipt_id": "vr"}, promotion_receipt={"receipt_id": "pr"})
    check("promotes_narrative_allegation: rule fires", "promotes_narrative_allegation" in reasons_d)
    check("promotes_narrative_allegation: existing optimizer also REJECTS (equivalence)", out_d["decision"] == "reject")

    # (E) crosses a tenant boundary (a tenant_private artifact from another tenant)
    foreign = {"artifact_id": "ff1", "artifact_type": "atomic_fact", "subject": "x", "predicate": "y", "object": "z",
               "source_handle": _HANDLE, "tenant_id": _OTHER, "scope": "tenant_private"}
    cand_e = [good_fact, extra_fact, foreign]
    baseline_with_foreign = {"pack_id": "pk1", "tenant_id": _TENANT, "artifacts": [good_fact, extra_fact, foreign]}

    class _IdE:
        name = "identity"
        def optimize(self, pack, *, signals):
            return {"pack_id": "pk1", "tenant_id": _TENANT, "artifacts": cand_e}
    out_e = harness.run(baseline_with_foreign, _IdE(), answer_fact_ids=answer_ids, signals={"excluded_ids": []}, now=_NOW)
    reasons_e = optimization_reject_reasons(baseline_artifacts=baseline_with_foreign["artifacts"], candidate_artifacts=cand_e,
                                            answer_fact_ids=answer_ids, excluded_ids=[], tenant_id=_TENANT,
                                            verification_receipt={"receipt_id": "vr"}, promotion_receipt={"receipt_id": "pr"})
    check("crosses_tenant_boundary: rule fires", "crosses_tenant_boundary" in reasons_e)
    check("crosses_tenant_boundary: existing optimizer also REJECTS (equivalence)", out_e["decision"] == "reject")

    # (F) lacks a promotion/verification receipt → consumption authority refuses to make it consumable
    clean_pack = {"pack_id": "pk1", "tenant_id": _TENANT, "artifacts": [good_fact, extra_fact]}
    reasons_f = optimization_reject_reasons(baseline_artifacts=baseline["artifacts"], candidate_artifacts=clean_pack["artifacts"],
                                            answer_fact_ids=answer_ids, excluded_ids=[], tenant_id=_TENANT,
                                            verification_receipt={}, promotion_receipt={})  # no receipts
    rpt_no_receipt = gate.assess(clean_pack, verification_receipt={"decision": "allow"},
                                 optimization_receipt={"decision": "promote"}, now=_NOW)  # no receipt_ids
    check("lacks_promotion_receipt: rule fires", "lacks_promotion_receipt" in reasons_f)
    check("lacks_promotion_receipt: existing consumption gate also refuses (not consumable)",
          rpt_no_receipt.consumable is False)

    # ── the converse: a clean candidate has NO reject reason AND the authority PROMOTES it ─────────
    # (use the dedupe optimizer over a baseline with a duplicate so there is measurable lift to promote.)
    from scripts.runtime.optimization import DedupeOptimizer
    dup = dict(extra_fact)
    base_dup = {"pack_id": "pk1", "tenant_id": _TENANT, "artifacts": [good_fact, extra_fact, dup]}
    out_clean = harness.run(base_dup, DedupeOptimizer(), answer_fact_ids=answer_ids, signals={"excluded_ids": []}, now=_NOW)
    reasons_clean = optimization_reject_reasons(baseline_artifacts=base_dup["artifacts"],
                                                candidate_artifacts=out_clean["candidate_pack"]["artifacts"],
                                                answer_fact_ids=answer_ids, excluded_ids=[], tenant_id=_TENANT,
                                                verification_receipt={"receipt_id": "vr"}, promotion_receipt={"receipt_id": "pr"})
    check("clean candidate: rule finds NO reject reason", reasons_clean == [], str(reasons_clean))
    check("clean candidate: existing optimizer PROMOTES it (equivalence on the accept path)",
          out_clean["decision"] == "promote")

    # ── build the M5 RuleCandidate (proposed, equivalence-asserting, with a fallback) ─────────────
    reject_rows = ["drops_answer_critical_fact", "drops_source_handle", "serves_held_out_conflict",
                   "promotes_narrative_allegation", "crosses_tenant_boundary", "lacks_promotion_receipt"]
    rule = RuleCandidate(rule_id=_hid("rule", {"k": "optimization_reject", "rows": reject_rows}),
                         rule_type="optimization_reject_rule", reject_reasons=reject_rows,
                         fallback_policy={"on_no_reason": "defer to the harness lift measurement + receipts"})
    check("the optimization-reject rule is PROPOSED, not active", rule.active is False)
    check("the rule asserts equivalence to the existing optimizer",
          rule.asserts_equivalence_to == "scripts/runtime/optimization.py")

    # ── DETERMINISM: a clean re-run reproduces the reasons + the rule id ──────────────────────────
    reasons_a2 = optimization_reject_reasons(baseline_artifacts=baseline["artifacts"], candidate_artifacts=[extra_fact],
                                             answer_fact_ids=answer_ids, excluded_ids=[], tenant_id=_TENANT,
                                             verification_receipt={"receipt_id": "vr"}, promotion_receipt={"receipt_id": "pr"})
    det = (reasons_a2 == reasons_a and _hid("rule", {"k": "optimization_reject", "rows": reject_rows}) == rule.rule_id)
    check("deterministic: reject reasons + rule id are reproducible", det)

    ok = not fails
    print("\n" + ("PASS — check_optimization_rejection_rule_distillation: the mined deterministic optimization-reject "
                  "rule fires on each unsafe candidate (drops an answer-critical fact / drops a source handle / serves "
                  "a held-out conflict / promotes a narrative allegation / crosses a tenant boundary / lacks a promotion "
                  "receipt) and each rejection is verified EQUIVALENT to the EXISTING OptimizationHarness regression gate "
                  "+ ConsumptionReadinessGate; a clean candidate yields NO reject reason and the existing optimizer "
                  "promotes it — the rule reproduces the optimizer's verdict, never replaces it."
                  if ok else f"{len(fails)} FAILURES: {fails}"))
    return 0 if ok else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Applied distillation: deterministic optimization-reject rules (asserts equivalence).")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
