#!/usr/bin/env python3
"""scripts.check_watchtower_minimum_freshness — proof (FACT-1..7): the Fragile Fact Watchtower MINIMUM.

A fact that perishes must be CAUGHT. This proves the watchtower's minimum slice end-to-end, all deterministic
and offline (time injected; ids content-addressed; no clock/RNG/network):

  * the Reg E '10 business days' fact gets FragilityMetadata carrying last_verified_at + next_verify_at +
    watch_policy_id (a real freshness horizon);
  * a FAQ-30 fact is classified conflict-prone at medium-or-higher volatility (the perishable summary case);
  * an immutable / demo source uses a no_refresh policy and NEVER goes stale;
  * a STALE fact (now past its horizon) yields a DURABLE-shaped VerificationTask (id stable across reruns);
  * the task's refresh STORES an EVIDENCE artifact (an evidence record, not a fabricated answer);
  * a tenant_private refresh CANNOT update a global_public canonical fact (scope isolation — refused);
  * the same inputs produce identical ids on rerun (determinism);
  * a sample of EACH of the 6 contract schemas validates via scripts.runtime.schema_validator.validate_ref;
  * GATE-COMPATIBILITY: a stale fragile fact handed to scripts.runtime.verification_gate.VerificationGate is
    held_out, and a fresh one is allow (when otherwise promotable).

CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_watchtower_minimum_freshness.py --self-test
"""
from __future__ import annotations

import argparse

from scripts.runtime.schema_validator import validate_ref
from scripts.runtime.verification_gate import VerificationGate
from src.baltor.contracts.artifacts.canonical_fact import CanonicalFact
from src.baltor.contracts.artifacts.fact_assertion import FactAssertion
from src.baltor.facts.classifier import classify, classify_volatility
from src.baltor.facts.refresh_planner import FactRefreshPlanner

NOW = 1_000_000          # injected clock (epoch seconds) — no wall-clock anywhere
GLOBAL = "global_public"

# the reference Reg E (source-of-law, 10 business days) vs FAQ (summary, 30 days) pair.
REGE_TEXT = "Regulation E requires the institution to resolve billing errors within 10 business days deadline."
FAQ_TEXT = "An FAQ summary says 30 days deadline."
DEMO_TEXT = "Demo fixture constant used only in the offline showcase."


def _gate_artifact(fact_id: str, fragility: dict, **over) -> dict:
    """A verified, source-grounded fact shaped for the C40 VerificationGate, carrying a fragility dict."""
    art = {"artifact_id": fact_id, "artifact_type": "atomic_fact",
           "source_handle": "ctx://cfpb/reg-e#error_resolution.deadline", "content_hash": "h-rege-10",
           "claim_status": "fact", "promotion_eligible": True, "scope": GLOBAL, "fragility": fragility}
    art.update(over)
    return art


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    planner = FactRefreshPlanner()

    # 1) the Reg E fact gets FragilityMetadata: last_verified_at + next_verify_at + watch_policy_id
    rege_frag, rege_pol = classify(fact_id="cf-rege-10", claim_type="atomic_fact",
                                   source_authority="source-of-law", claim_text=REGE_TEXT, last_verified_at=NOW)
    check("Reg E fact gets FragilityMetadata with last_verified_at",
          rege_frag.last_verified_at == NOW, str(rege_frag.last_verified_at))
    check("Reg E FragilityMetadata carries a next_verify_at horizon",
          isinstance(rege_frag.next_verify_at, int) and rege_frag.next_verify_at > NOW, str(rege_frag.next_verify_at))
    check("Reg E FragilityMetadata carries a watch_policy_id matching its policy",
          rege_frag.watch_policy_id == rege_pol.watch_policy_id and bool(rege_frag.watch_policy_id))

    # 2) a FAQ-30 fact is conflict-prone and medium-or-higher volatility
    faq_frag, _ = classify(fact_id="cf-faq-30", claim_type="atomic_fact", source_authority="agency-faq",
                           claim_text=FAQ_TEXT, last_verified_at=NOW)
    check("FAQ-30 fact is conflict-prone", faq_frag.conflict_prone is True)
    check("FAQ-30 fact is medium-or-higher volatility",
          faq_frag.volatility_class in ("medium", "high", "realtime"), faq_frag.volatility_class)

    # 3) an immutable / demo source uses a no_refresh policy and never goes stale
    demo_frag, demo_pol = classify(fact_id="cf-demo", claim_type="atomic_fact", source_authority="demo-fixture",
                                   claim_text=DEMO_TEXT, last_verified_at=NOW)
    check("immutable/demo source gets a no_refresh policy",
          demo_pol.no_refresh is True and demo_frag.no_refresh is True)
    check("a no_refresh fact NEVER goes stale (even far in the future)",
          demo_frag.is_stale(NOW + 10**9) is False and demo_frag.horizon() is None)
    check("plan_task returns None for a no_refresh fact (nothing to do)",
          planner.plan_task(demo_frag, source_handle="ctx://demo#x", scope=GLOBAL, now=NOW + 10**9) is None)

    # 4) a STALE fact creates a durable-shaped VerificationTask
    now_late = rege_frag.next_verify_at + 1  # one second past the Reg E horizon
    check("the Reg E fact is stale once now passes its horizon", rege_frag.is_stale(now_late) is True)
    task = planner.plan_task(rege_frag, source_handle="ctx://cfpb/reg-e#error_resolution.deadline",
                             scope=GLOBAL, now=now_late)
    check("a stale fact yields a VerificationTask", task is not None and task.status == "queued")
    check("the VerificationTask is durable-shaped (content-addressed id, missed horizon, policy)",
          task is not None and task.task_id.startswith("vtask-") and task.due_at == rege_frag.next_verify_at
          and task.watch_policy_id == rege_frag.watch_policy_id)
    # durability: re-planning the SAME missed horizon coalesces to the SAME task id (created_at differs)
    task_rerun = planner.plan_task(rege_frag, source_handle="ctx://cfpb/reg-e#error_resolution.deadline",
                                   scope=GLOBAL, now=now_late + 5000)
    check("re-planning the same missed horizon coalesces to the SAME durable task id",
          task is not None and task_rerun is not None and task.task_id == task_rerun.task_id)

    # 5) the verification task's refresh STORES an EVIDENCE artifact (not an answer)
    result = planner.refresh(task, rege_pol, fact_scope=GLOBAL, now=now_late)
    check("refresh stores an EVIDENCE artifact (evidence record, not a fabricated answer)",
          bool(result.evidence) and result.evidence.get("artifact_type") == "source_record"
          and "value" not in result.evidence and "answer" not in result.evidence
          and result.evidence.get("method") == "stubbed_offline_recheck")
    check("a clean refresh marks the fact verified_current and sets a NEW horizon",
          result.applied is True and result.new_status == "verified_current"
          and isinstance(result.next_verify_at, int) and result.next_verify_at > now_late)

    # 6) a tenant_private assertion/refresh CANNOT update a global_public canonical fact (scope isolation)
    tenant_task = planner.plan_task(rege_frag, source_handle="ctx://acme/policy#deadline",
                                    scope="tenant_private", now=now_late)
    tenant_result = planner.refresh(tenant_task, rege_pol, fact_scope=GLOBAL, now=now_late)
    check("a tenant_private refresh CANNOT update a global_public fact (refused, applied=False)",
          tenant_result.applied is False and tenant_result.new_status == "held_out"
          and "scope isolation" in tenant_result.reason)
    # and a FactAssertion in tenant_private scope feeding a global fact is recognizably cross-scope
    tpriv_assert = FactAssertion(claim_text="tenant says 5 days", claim_type="atomic_fact",
                                 source_handle="ctx://acme/policy#deadline", scope="tenant_private",
                                 asserted_at=now_late, subject="Reg E error resolution",
                                 predicate="deadline_business_days", object="5", tenant_id="acme")
    global_fact = CanonicalFact(subject="Reg E error resolution", predicate="deadline_business_days",
                                object="10", scope=GLOBAL, status="verified_current",
                                source_handle="ctx://cfpb/reg-e#error_resolution.deadline", content_hash="h-rege-10",
                                fragility_id=rege_frag.fragility_id)
    check("a tenant_private assertion's scope differs from the global_public canonical fact's scope",
          tpriv_assert.scope == "tenant_private" and global_fact.scope == GLOBAL)
    # applying the refused result does NOT make the fact servable as verified truth
    after = planner.apply_result(global_fact, tenant_result)
    check("applying a refused (scope-leak) result does NOT leave the fact verified_current/servable",
          after.status == "held_out" and after.servable is False and after.fact_id == global_fact.fact_id)

    # 7) determinism: identical inputs → identical ids on rerun (no clock/rng)
    frag_a, pol_a = classify(fact_id="cf-rege-10", claim_type="atomic_fact", source_authority="source-of-law",
                             claim_text=REGE_TEXT, last_verified_at=NOW)
    frag_b, pol_b = classify(fact_id="cf-rege-10", claim_type="atomic_fact", source_authority="source-of-law",
                             claim_text=REGE_TEXT, last_verified_at=NOW)
    res_a = planner.refresh(task, rege_pol, fact_scope=GLOBAL, now=now_late)
    check("classifier is deterministic (same fragility_id + watch_policy_id across reruns)",
          frag_a.fragility_id == frag_b.fragility_id and pol_a.watch_policy_id == pol_b.watch_policy_id)
    check("refresh is deterministic (same result_id + evidence_id across reruns)",
          res_a.result_id == result.result_id and res_a.evidence["evidence_id"] == result.evidence["evidence_id"])

    # 8) a sample of EACH of the 6 contract schemas validates via validate_ref(artifacts/<Name>)
    samples = {
        "FactAssertion": tpriv_assert.to_dict(),
        "CanonicalFact": global_fact.to_dict(),
        "FragilityMetadata": rege_frag.to_dict(),
        "WatchPolicy": rege_pol.to_dict(),
        "VerificationTask": task.to_dict(),
        "VerificationResult": result.to_dict(),
    }
    for name, sample in samples.items():
        errs = validate_ref(sample, f"artifacts/{name}")
        check(f"sample {name} validates against its schema", errs == [], str(errs[:2]))
    # also validate the immutable (no_refresh, null horizon) fragility + policy variant
    check("no_refresh FragilityMetadata (null horizon) validates",
          validate_ref(demo_frag.to_dict(), "artifacts/FragilityMetadata") == [])
    check("no_refresh WatchPolicy validates",
          validate_ref(demo_pol.to_dict(), "artifacts/WatchPolicy") == [])

    # 9) GATE-COMPATIBILITY: the fragility dict drives the C40 VerificationGate as designed.
    gate = VerificationGate()
    fresh_art = _gate_artifact("cf-rege-10", rege_frag.to_dict())   # now < horizon
    fresh_eval = gate.evaluate(fresh_art, context={"now": NOW, "requested_scope": GLOBAL},
                               now="2026-06-05T00:00:00Z")
    check("a FRESH fragile fact is ALLOWED by the C40 gate (otherwise promotable)",
          fresh_eval["decision"].decision == "allow", str(fresh_eval["decision"].reasons))
    stale_art = _gate_artifact("cf-rege-10", rege_frag.to_dict())
    stale_eval = gate.evaluate(stale_art, context={"now": now_late, "requested_scope": GLOBAL},
                               now="2026-06-05T00:00:00Z")
    check("a STALE fragile fact is HELD OUT by the C40 gate (no queued task)",
          stale_eval["decision"].decision == "hold_out"
          and any(c.name == "fragile_fact_current_or_queued" and not c.passed for c in stale_eval["report"].checks))
    # and a stale fact WITH a queued task (our planner emitted one) is allowed again
    queued_eval = gate.evaluate(stale_art, context={"now": now_late, "requested_scope": GLOBAL,
                                                    "pending_verification_ids": {"cf-rege-10"}},
                                now="2026-06-05T00:00:00Z")
    check("a STALE fragile fact with a QUEUED verification task is allowed by the C40 gate",
          queued_eval["decision"].decision == "allow", str(queued_eval["decision"].reasons))
    # the no_refresh fact is never stale to the gate either
    demo_gate = gate.evaluate(_gate_artifact("cf-demo", demo_frag.to_dict()),
                              context={"now": NOW + 10**9, "requested_scope": GLOBAL}, now="2026-06-05T00:00:00Z")
    check("a no_refresh fact is never held out for staleness by the C40 gate",
          demo_gate["decision"].decision == "allow"
          and all(c.passed for c in demo_gate["report"].checks if c.name == "fragile_fact_current_or_queued"))

    summary = ("PASS — check_watchtower_minimum_freshness: the Fragile Fact Watchtower minimum — Reg E gets a "
               "freshness horizon (last_verified+next_verify+policy); FAQ-30 is conflict-prone medium+; demo is "
               "no_refresh; a stale fact yields a durable VerificationTask whose refresh stores EVIDENCE (not an "
               "answer); tenant_private cannot update global_public; deterministic; all 6 schemas validate; and a "
               "stale fragile fact is held_out / a fresh one allowed by the C40 gate.")
    print(f"\n{summary if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: Fragile Fact Watchtower MINIMUM (FACT-1..7).")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
