#!/usr/bin/env python3
"""scripts.check_determinism_contracts — proof (DETERMINISM CONTRACTS MODE): the 11 determinism-factory
contract schemas exist, validate via the stdlib schema validator (no `jsonschema`, Python 3.14), each ships
a valid example that PASSES and at least one invalid example that FAILS, the required fields the factory
depends on are ENFORCED by the contracts themselves, and the NON-NEGOTIABLE determinism semantics are
checkable at the contract layer.

The contract layer for "convert repeated VERIFIED LLM/multi-LLM/heuristic/human decisions into deterministic
rules" — made checkable:
  - WorkflowTrace REQUIRES tenant_id, source_scope, workflow_id, step_id, input/output artifact ids,
    prompt_hash, the three validation gates (schema/grounding/deterministic), final_decision, a `verified`
    flag (the miner consumes ONLY verified=true traces), source_handles, receipt_ids, created_at.
  - ConsensusRun carries agreement_score + per-model outputs but its final_label comes from
    label_source ∈ {deterministic_validator, adjudication, authority_policy} — NEVER 'consensus'/'majority';
    and consensus_only_is_not_truth is pinned true. Consensus alone can NEVER serve a fact.
  - AdjudicationRecord's adjudicated_by can NEVER be 'consensus' (truth comes from a validator/authority/
    human), and a verified label REQUIRES source_handles + a receipt_id.
  - RuleCandidate is born status='proposed' (NOT active), and REQUIRES examples, counterexamples,
    expected_failure_modes, a fallback_policy, and the lossless distilled_from_pattern_id +
    distilled_from_trace_ids back-link.
  - RulePromotionReceipt REQUIRES a replay_report_id AND a shadow_report_id AND a fallback_policy AND the
    traces_preserved (lossless) flag — no promotion without all of them.
  - LLMTrace.is_truth and the *_is_not_truth / non_authoritative / replayed_over_verified_only flags are
    enum-pinned so a single LLM proposal / consensus / shadow run can never structurally claim to be truth.

Deterministic, stdlib-only, offline (no network, no RNG, no wall-clock).
CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_determinism_contracts.py --self-test
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from scripts.runtime.schema_validator import validate as _validate  # noqa: E402

_SCHEMA_DIR = _resource("schemas") / "determinism"
_EX_DIR = _SCHEMA_DIR / "examples"

#: the 11 determinism contracts this lane owns (filename stem under schemas/determinism).
_SCHEMAS = [
    "WorkflowTrace", "LLMTrace", "ConsensusRun", "AdjudicationRecord", "PatternCandidate",
    "RuleCandidate", "RuleReplayReport", "ShadowRunReport", "DeterministicRule",
    "RulePromotionReceipt", "FallbackPolicy",
]

#: the keyword set the stdlib validator actually enforces — schemas must use only these (no silently-ignored
#: pattern/minimum/anyOf that would give a false sense of validation).
_ALLOWED_KEYWORDS = {"type", "required", "properties", "enum", "additionalProperties", "items",
                     "$id", "title", "description"}

#: WorkflowTrace MUST require these (the trace fields the whole factory keys on, per the lane spec).
_WORKFLOWTRACE_REQUIRED = {
    "tenant_id", "source_scope", "workflow_id", "step_id", "input_artifact_ids", "output_artifact_ids",
    "prompt_hash", "schema_validation", "grounding_validation", "deterministic_validation", "final_decision",
    "verified", "source_handles", "receipt_ids", "created_at",
}
#: RuleCandidate MUST require these (proposed-not-active + examples/counterexamples + fallback + lossless link).
_RULECANDIDATE_REQUIRED = {
    "scope", "examples", "counterexamples", "expected_failure_modes", "fallback_policy", "status",
    "distilled_from_pattern_id", "distilled_from_trace_ids",
}
#: RulePromotionReceipt MUST require these (no promotion without a replay + shadow report + fallback + lossless).
_PROMOTION_REQUIRED = {"replay_report_id", "shadow_report_id", "fallback_policy", "traces_preserved",
                       "distilled_from_trace_ids"}


def _keys_ok(node) -> bool:
    """True iff every schema keyword in the (recursive) node is one the stdlib validator enforces."""
    if not isinstance(node, dict):
        return True
    for k, v in node.items():
        if k == "properties" and isinstance(v, dict):
            if not all(_keys_ok(sub) for sub in v.values()):
                return False
            continue
        if k == "items" and isinstance(v, dict):
            if not _keys_ok(v):
                return False
            continue
        if k not in _ALLOWED_KEYWORDS:
            return False
    return True


def _enum_of(schema: dict, field: str) -> list:
    return schema.get("properties", {}).get(field, {}).get("enum", [])


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    schemas: dict[str, dict] = {}
    examples: dict[str, dict] = {}
    for stem in _SCHEMAS:
        sp = _SCHEMA_DIR / f"{stem}.schema.json"
        ep = _EX_DIR / f"{stem}.example.json"
        check(f"{stem} schema file exists", sp.is_file(), str(sp))
        check(f"{stem} example file exists", ep.is_file(), str(ep))
        if sp.is_file():
            schemas[stem] = json.loads(sp.read_text())
        if ep.is_file():
            examples[stem] = json.loads(ep.read_text())

    check("all 11 determinism contracts are present", len(schemas) == 11, f"got {len(schemas)}")

    # ── every schema parses, declares $id determinism/<Stem>, is an object with additionalProperties:false,
    #    declares required+properties, uses ONLY stdlib-validator keywords, and defines a property for every
    #    required field (no required-but-undefined field). ──
    for stem, sc in schemas.items():
        check(f"{stem} $id is determinism/{stem}",
              sc.get("$id") == f"determinism/{stem}", str(sc.get("$id")))
        check(f"{stem} is an object with additionalProperties:false",
              sc.get("type") == "object" and sc.get("additionalProperties") is False)
        check(f"{stem} declares required + properties", bool(sc.get("required")) and bool(sc.get("properties")))
        check(f"{stem} uses only stdlib-validator keywords", _keys_ok(sc))
        props = set(sc.get("properties", {}))
        missing_props = [r for r in sc.get("required", []) if r not in props]
        check(f"{stem} declares a property for every required field", missing_props == [], str(missing_props))
        # every contract carries an injected-time created_at OR a *_at field (deterministic, no wall-clock).
        time_fields = [k for k in sc.get("required", []) if k.endswith("_at")]
        check(f"{stem} requires an injected time field (deterministic, no wall-clock)", len(time_fields) >= 1)

    # ── valid example PASSES; every invalid_* example FAILS schema validation. ──
    for stem, ex in examples.items():
        sc = schemas[stem]
        valids = {k: v for k, v in ex.items() if k == "valid" or k.startswith("valid_")}
        check(f"{stem} has a 'valid' example", "valid" in valids)
        for k, v in valids.items():
            errs = _validate(v, sc)
            check(f"{stem} {k} example validates clean", errs == [], str(errs[:4]))
        invalids = {k: v for k, v in ex.items() if k.startswith("invalid")}
        check(f"{stem} ships at least one invalid example", len(invalids) >= 1)
        for k, v in invalids.items():
            errs = _validate(v, sc)
            check(f"{stem} {k} is correctly REJECTED by the schema", errs != [])

    # ── WorkflowTrace required-field enforcement (the trace fields the factory depends on). ──
    wt_sc = schemas.get("WorkflowTrace", {})
    wt_req = set(wt_sc.get("required", []))
    check("WorkflowTrace requires all the spec-mandated trace fields",
          _WORKFLOWTRACE_REQUIRED <= wt_req, str(sorted(_WORKFLOWTRACE_REQUIRED - wt_req)))
    wt_valid = examples.get("WorkflowTrace", {}).get("valid", {})
    if wt_valid and wt_sc:
        for f in sorted(_WORKFLOWTRACE_REQUIRED):
            broken = {k: v for k, v in wt_valid.items() if k != f}
            check(f"WorkflowTrace rejects a trace missing '{f}'", _validate(broken, wt_sc) != [])
        # source_scope is enum-bounded — a bogus scope is rejected (tenant isolation can't be smuggled).
        bad_scope = dict(wt_valid); bad_scope["source_scope"] = "everyone"
        check("WorkflowTrace rejects an out-of-enum source_scope", _validate(bad_scope, wt_sc) != [])
        # the three validation gates are enum-bounded.
        for gate in ("schema_validation", "grounding_validation", "deterministic_validation"):
            bad_gate = dict(wt_valid); bad_gate[gate] = "maybe"
            check(f"WorkflowTrace rejects an out-of-enum {gate}", _validate(bad_gate, wt_sc) != [])
        # the verified flag exists so the miner can distinguish a verified trace from a raw LLM trace.
        unver = examples.get("WorkflowTrace", {}).get("valid_llm_step_unverified", {})
        check("WorkflowTrace carries a 'verified' boolean (raw LLM step is verified=false)",
              wt_valid.get("verified") is True and unver.get("verified") is False)

    # ── ConsensusRun: consensus is EVIDENCE, not truth. ──
    cons_sc = schemas.get("ConsensusRun", {})
    cons_valid = examples.get("ConsensusRun", {}).get("valid", {})
    label_enum = _enum_of(cons_sc, "label_source")
    check("ConsensusRun has a final_label field", "final_label" in cons_sc.get("properties", {}))
    check("ConsensusRun final_label comes from label_source ∈ {validator, adjudication, authority} — NEVER consensus/majority",
          set(label_enum) == {"deterministic_validator", "adjudication", "authority_policy"}, str(label_enum))
    check("ConsensusRun 'consensus'/'majority' is NOT an allowed label_source (consensus alone never serves a fact)",
          "consensus" not in label_enum and "majority" not in label_enum)
    check("ConsensusRun carries an agreement_score + per_model_outputs (evidence) and a routed_to_review flag",
          {"agreement_score", "per_model_outputs", "routed_to_review"} <= set(cons_sc.get("required", [])))
    # the consensus_only_is_not_truth flag is pinned true (a downstream gate asserts it).
    check("ConsensusRun pins consensus_only_is_not_truth == [true]",
          _enum_of(cons_sc, "consensus_only_is_not_truth") == [True])
    if cons_valid and cons_sc:
        # a label_source of 'consensus' is flagged: it is REJECTED by the schema enum.
        consensus_only = examples.get("ConsensusRun", {}).get("invalid_label_source_consensus", {})
        check("ConsensusRun a 'consensus'-sourced label (consensus_only) is flagged/REJECTED, not served",
              consensus_only and _validate(consensus_only, cons_sc) != [])
        # even at full agreement the label still comes from the authority, not the votes.
        full = examples.get("ConsensusRun", {}).get("valid_full_agreement_still_not_truth", {})
        check("ConsensusRun full-agreement (1.0) example STILL takes its label from the authority, not the vote",
              full.get("agreement_score") == 1.0 and full.get("label_source") in {"deterministic_validator", "authority_policy"}
              and "reg-e" in full.get("final_label", ""))
        # consensus_only_is_not_truth=false is rejected.
        truthy = examples.get("ConsensusRun", {}).get("invalid_consensus_is_truth", {})
        check("ConsensusRun rejects consensus_only_is_not_truth=false", truthy and _validate(truthy, cons_sc) != [])

    # ── LLMTrace: a single LLM proposal is structurally NOT truth. ──
    llm_sc = schemas.get("LLMTrace", {})
    check("LLMTrace pins is_truth == [false] (a single LLM proposal is never truth)",
          _enum_of(llm_sc, "is_truth") == [False])
    check("LLMTrace requires a response_ref (raw response is NOT inlined — object/tenant store)",
          "response_ref" in set(llm_sc.get("required", [])))

    # ── AdjudicationRecord: truth comes from a human/policy/authority, NEVER consensus. ──
    adj_sc = schemas.get("AdjudicationRecord", {})
    adj_enum = _enum_of(adj_sc, "adjudicated_by")
    check("AdjudicationRecord adjudicated_by ∈ {human_reviewer, deterministic_policy, authority_ranking} — never consensus/llm",
          set(adj_enum) == {"human_reviewer", "deterministic_policy", "authority_ranking"}, str(adj_enum))
    check("AdjudicationRecord 'consensus' is NOT an allowed adjudicator",
          "consensus" not in adj_enum and "llm" not in adj_enum)
    check("AdjudicationRecord requires source_handles + receipt_id (verified label = grounded + receipt-backed)",
          {"source_handles", "receipt_id"} <= set(adj_sc.get("required", [])))
    adj_valid = examples.get("AdjudicationRecord", {}).get("valid", {})
    if adj_valid and adj_sc:
        for f in ("source_handles", "receipt_id"):
            broken = {k: v for k, v in adj_valid.items() if k != f}
            check(f"AdjudicationRecord rejects an adjudication missing '{f}'", _validate(broken, adj_sc) != [])
        consensus_adj = examples.get("AdjudicationRecord", {}).get("invalid_adjudicated_by_consensus", {})
        check("AdjudicationRecord rejects adjudicated_by='consensus'", consensus_adj and _validate(consensus_adj, adj_sc) != [])

    # ── PatternCandidate: only mined from verified traces. ──
    pat_sc = schemas.get("PatternCandidate", {})
    check("PatternCandidate pins all_traces_verified == [true] (mined only from verified traces)",
          _enum_of(pat_sc, "all_traces_verified") == [True])
    check("PatternCandidate requires supported_by_trace_ids + counterexample_trace_ids (lossless evidence link)",
          {"supported_by_trace_ids", "counterexample_trace_ids"} <= set(pat_sc.get("required", [])))

    # ── RuleCandidate: proposed-not-active + examples/counterexamples + fallback + lossless link. ──
    rc_sc = schemas.get("RuleCandidate", {})
    rc_req = set(rc_sc.get("required", []))
    check("RuleCandidate requires scope+examples+counterexamples+failure_modes+fallback+status+lossless link",
          _RULECANDIDATE_REQUIRED <= rc_req, str(sorted(_RULECANDIDATE_REQUIRED - rc_req)))
    status_enum = _enum_of(rc_sc, "status")
    check("RuleCandidate status enum has NO 'active' value (a candidate is never active by default)",
          "active" not in status_enum and "proposed" in status_enum, str(status_enum))
    rc_valid = examples.get("RuleCandidate", {}).get("valid", {})
    if rc_valid and rc_sc:
        check("RuleCandidate valid example is born status='proposed' (NOT active)", rc_valid.get("status") == "proposed")
        check("RuleCandidate valid example carries the lossless distilled_from_trace_ids back-link",
              len(rc_valid.get("distilled_from_trace_ids", [])) >= 1)
        for f in ("fallback_policy", "distilled_from_trace_ids", "distilled_from_pattern_id", "counterexamples"):
            broken = {k: v for k, v in rc_valid.items() if k != f}
            check(f"RuleCandidate rejects a candidate missing '{f}'", _validate(broken, rc_sc) != [])
        # an out-of-enum status (e.g. 'active') is rejected.
        active_cand = examples.get("RuleCandidate", {}).get("invalid_status_active", {})
        check("RuleCandidate rejects status='active'", active_cand and _validate(active_cand, rc_sc) != [])

    # ── DeterministicRule: an ACTIVE rule must carry a fallback, lossless link, and equivalence claim. ──
    dr_sc = schemas.get("DeterministicRule", {})
    check("DeterministicRule requires fallback_policy + promotion_receipt_id + replay+shadow report ids",
          {"fallback_policy", "promotion_receipt_id", "replay_report_id", "shadow_report_id"} <= set(dr_sc.get("required", [])))
    check("DeterministicRule requires distilled_from_trace_ids (lossless) + asserts_equivalence_to (reproduces reference, no 2nd authority)",
          {"distilled_from_trace_ids", "asserts_equivalence_to"} <= set(dr_sc.get("required", [])))
    check("DeterministicRule status enum is exactly {promoted, retired} (no 'proposed' active rule)",
          set(_enum_of(dr_sc, "status")) == {"promoted", "retired"})
    dr_valid = examples.get("DeterministicRule", {}).get("valid", {})
    if dr_valid and dr_sc:
        no_fb = {k: v for k, v in dr_valid.items() if k != "fallback_policy"}
        check("DeterministicRule rejects an active rule missing fallback_policy", _validate(no_fb, dr_sc) != [])
        check("DeterministicRule valid (reconciliation) rule asserts equivalence to the existing reference (reproduces, not replaces)",
              "reg-e" in dr_valid.get("asserts_equivalence_to", ""))

    # ── RulePromotionReceipt: no promotion without replay + shadow + fallback + lossless. ──
    pr_sc = schemas.get("RulePromotionReceipt", {})
    pr_req = set(pr_sc.get("required", []))
    check("RulePromotionReceipt requires replay_report_id + shadow_report_id + fallback_policy + traces_preserved + lossless link",
          _PROMOTION_REQUIRED <= pr_req, str(sorted(_PROMOTION_REQUIRED - pr_req)))
    pr_valid = examples.get("RulePromotionReceipt", {}).get("valid", {})
    if pr_valid and pr_sc:
        for f in sorted(_PROMOTION_REQUIRED):
            broken = {k: v for k, v in pr_valid.items() if k != f}
            check(f"RulePromotionReceipt rejects a promotion missing '{f}'", _validate(broken, pr_sc) != [])
        # a truth_serving first promotion carries an accountable human sign-off; the gate fields are all booleans.
        check("RulePromotionReceipt truth_serving valid example is human_review_signed + unsafe_fp_zero + traces_preserved",
              pr_valid.get("rule_class") == "truth_serving" and pr_valid.get("human_review_signed") is True
              and pr_valid.get("unsafe_fp_zero") is True and pr_valid.get("traces_preserved") is True)

    # ── RuleReplayReport / ShadowRunReport: verified-only + non-authoritative pins; safety counters present. ──
    rr_sc = schemas.get("RuleReplayReport", {})
    check("RuleReplayReport pins replayed_over_verified_only == [true] (never scores against unverified traces)",
          _enum_of(rr_sc, "replayed_over_verified_only") == [True])
    check("RuleReplayReport requires unsafe_false_positives + tenant_leak_count (the gate's safety counters)",
          {"unsafe_false_positives", "tenant_leak_count"} <= set(rr_sc.get("required", [])))
    sr_sc = schemas.get("ShadowRunReport", {})
    check("ShadowRunReport pins non_authoritative == [true] (shadow output recorded, never served)",
          _enum_of(sr_sc, "non_authoritative") == [True])
    check("ShadowRunReport requires unsafe_mismatch_count + tenant_leak_count (any unsafe mismatch blocks promotion)",
          {"unsafe_mismatch_count", "tenant_leak_count"} <= set(sr_sc.get("required", [])))

    # ── FallbackPolicy: every active rule has a real fallback that is recorded + feeds mining. ──
    fb_sc = schemas.get("FallbackPolicy", {})
    fb_target_enum = _enum_of(fb_sc, "default_fallback_target")
    check("FallbackPolicy default_fallback_target has NO 'never_fallback' value (every rule must have a real fallback)",
          "never_fallback" not in fb_target_enum and len(fb_target_enum) >= 3, str(fb_target_enum))
    check("FallbackPolicy pins fallback_recorded==[true] and feeds_future_mining==[true]",
          _enum_of(fb_sc, "fallback_recorded") == [True] and _enum_of(fb_sc, "feeds_future_mining") == [True])

    ok = not fails
    print(
        f"\n{'PASS — check_determinism_contracts: 11 determinism contracts exist + validate (stdlib keywords only); each ships a passing valid example and a rejected invalid example; WorkflowTrace requires tenant/scope/workflow/step/io-ids/prompt_hash/3-gates/final_decision/verified/source_handles/receipt_ids/created_at (each load-bearing); ConsensusRun final_label is validator/adjudication/authority-sourced (NEVER consensus/majority) and consensus_only_is_not_truth is pinned — consensus alone can never serve a fact; LLMTrace.is_truth pinned false; AdjudicationRecord never adjudicated_by consensus and needs source_handles+receipt; PatternCandidate mined only from verified traces; RuleCandidate is born proposed-not-active with examples+counterexamples+fallback+lossless back-link; RulePromotionReceipt needs replay+shadow+fallback+traces_preserved; DeterministicRule asserts-equivalence to the existing reference (no 2nd authority); replay is verified-only and shadow is non-authoritative.' if ok else f'{len(fails)} FAILURES: {fails}'}"
    )
    return 0 if ok else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: determinism-factory contract schemas enforce the non-negotiable semantics.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
