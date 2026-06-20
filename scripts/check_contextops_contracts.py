#!/usr/bin/env python3
"""scripts.check_contextops_contracts — proof (CONTEXTOPS CONTRACTS MODE): the 14 ContextOps Verification
Foundry contract schemas exist, validate via the stdlib schema validator (no `jsonschema`, Python 3.14),
each ships a valid example that PASSES and at least one invalid example that FAILS, and the NON-NEGOTIABLE
ContextOps invariant is enforced AT THE CONTRACT LAYER.

THE INVARIANT made checkable: **Agents DISCOVER and PROPOSE; Baltor STORES, VERIFIES, RECONCILES, PROVES,
CONSUMES.** Concretely the contracts pin:
  - ContextTriageResult.lane ∈ the 12 triage lanes + a needs_action bool + serves_truth pinned false (a
    triage is a routing signal, never a served fact).
  - ResearchTask.produces pinned [source_discovery_report] + agent_may_serve_truth pinned [false] +
    bounds.secrets_allowed pinned [false] (an agent is bounded and never serves/promotes truth).
  - SourceDiscoveryReport.discovered_by (an attributable agent) + serves_truth pinned [false]; every
    candidate it carries REQUIRES a source_handle (red-team: serves_truth=true is REJECTED).
  - SourceCandidate REQUIRES source_handle + authority_rank (a candidate without a handle is inadmissible;
    authority is comparable so a FAQ can never outrank a regulation).
  - ExtractorSnippet.produces pinned [fact_assertion_candidate] + claim_status pinned [candidate] +
    has_unit_test pinned [true] + sandbox_required pinned [true] + REQUIRES source_handle (red-team: an
    extractor claiming produces='canonical_fact' / dropping its source_handle / lacking a unit test is
    REJECTED — extractor output is ALWAYS a candidate, never served/canonical truth).
  - GeneratedWorkerSpec REQUIRES proof_scripts + idempotency_key_template + retry_policy(retry/DLQ),
    rides_existing_worker_framework pinned [true], registration_status pinned [proposed] (red-team: an
    'active'/'registered' worker, or one that spins a 2nd runtime, is REJECTED — nothing auto-executes).
  - VerifierProofResult REQUIRES sandbox_passed + proof_passed + a gate_decision; the sandbox carries no
    secrets (secrets_present pinned false).
  - SourceRecipe / VerificationRecipe REQUIRE authority + a cross_source policy + watch triggers; a
    VerificationRecipe.produces is pinned [fact_verification_run] and its winning_source_type can never be
    a FAQ; FactVerificationRun.promoted_to_canonical is pinned [false] and it carries the cost-ladder moat
    metrics (llm_calls_avoided / deterministic_verifications / cached_fact_hits / cost_reduction_estimate /
    token_cost_before / token_cost_after).

Deterministic, stdlib-only, offline (no network, no RNG, no wall-clock).
CLI: PYTHONPATH=. python3 scripts/check_contextops_contracts.py --self-test
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from scripts.runtime.schema_validator import validate as _validate  # noqa: E402

_SCHEMA_DIR = _REPO / "schemas" / "contextops"
_EX_DIR = _SCHEMA_DIR / "examples"

#: the 14 ContextOps contracts this lane owns (filename stem under schemas/contextops).
_SCHEMAS = [
    "ContextTriageResult", "ResearchTask", "ResearchPlan", "SourceDiscoveryReport", "SourceCandidate",
    "SourceReliabilityScore", "SourceRecipe", "VerificationRecipe", "ExtractorSnippet", "GeneratedWorkerSpec",
    "VerifierProofResult", "FactRefreshPlan", "FactVerificationRun", "FactReliabilityScore",
]

#: the stdlib validator's enforced keyword set — schemas must use ONLY these (no silently-ignored
#: pattern/minimum/maximum/anyOf that would give a false sense of validation). 'minimum' IS enforced? No —
#: the stdlib validator ignores it; so we forbid it to avoid a false sense of validation.
_ALLOWED_KEYWORDS = {"type", "required", "properties", "enum", "additionalProperties", "items",
                     "$id", "title", "description"}

#: the 12 canonical ContextTriage lanes (single source — must match ContextTriageResult.lane.enum exactly).
_TRIAGE_LANES = {
    "needs_reconciliation", "needs_verification", "needs_enrichment", "is_fragile", "is_stale",
    "is_low_authority", "is_under_supported", "is_conflict_candidate", "is_missing_source",
    "is_customer_private_override", "is_model_interpretation", "is_high_value_reusable_fact",
}

#: the cost-ladder moat metrics FactVerificationRun.cost_tracking must require (the visible economic moat).
_COST_METRICS = {
    "llm_calls_avoided", "deterministic_verifications", "cached_fact_hits", "cost_reduction_estimate",
    "token_cost_before", "token_cost_after",
}


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


def _nested_enum(schema: dict, parent: str, field: str) -> list:
    return schema.get("properties", {}).get(parent, {}).get("properties", {}).get(field, {}).get("enum", [])


def _req(schema: dict) -> set:
    return set(schema.get("required", []))


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    schemas: dict[str, dict] = {}
    examples: dict[str, dict] = {}
    for stem in _SCHEMAS:
        sp = _SCHEMA_DIR / f"{stem}.v1.schema.json"
        ep = _EX_DIR / f"{stem}.v1.example.json"
        check(f"{stem}.v1 schema file exists", sp.is_file(), str(sp))
        check(f"{stem}.v1 example file exists", ep.is_file(), str(ep))
        if sp.is_file():
            schemas[stem] = json.loads(sp.read_text())
        if ep.is_file():
            examples[stem] = json.loads(ep.read_text())

    check("all 14 ContextOps contracts are present", len(schemas) == 14, f"got {len(schemas)}")

    # ── every schema parses, declares $id contextops/<Stem>.v1, is an object with additionalProperties:false,
    #    declares required+properties, uses ONLY stdlib-validator keywords, defines a property for every
    #    required field, and requires an injected-time *_at field (deterministic, no wall-clock). ──
    for stem, sc in schemas.items():
        check(f"{stem}.v1 $id is contextops/{stem}.v1",
              sc.get("$id") == f"contextops/{stem}.v1", str(sc.get("$id")))
        check(f"{stem}.v1 is an object with additionalProperties:false",
              sc.get("type") == "object" and sc.get("additionalProperties") is False)
        check(f"{stem}.v1 declares required + properties", bool(sc.get("required")) and bool(sc.get("properties")))
        check(f"{stem}.v1 uses only stdlib-validator keywords (no false-sense pattern/minimum/anyOf)", _keys_ok(sc))
        props = set(sc.get("properties", {}))
        missing_props = [r for r in sc.get("required", []) if r not in props]
        check(f"{stem}.v1 declares a property for every required field", missing_props == [], str(missing_props))
        time_fields = [k for k in sc.get("required", []) if k.endswith("_at")]
        check(f"{stem}.v1 requires an injected time field (deterministic, no wall-clock)", len(time_fields) >= 1)

    # ── valid example PASSES; every invalid_* example FAILS schema validation. ──
    for stem, ex in examples.items():
        sc = schemas[stem]
        valids = {k: v for k, v in ex.items() if k == "valid" or k.startswith("valid_")}
        check(f"{stem}.v1 has a 'valid' example", "valid" in valids)
        for k, v in valids.items():
            errs = _validate(v, sc)
            check(f"{stem}.v1 {k} example validates clean", errs == [], str(errs[:4]))
        invalids = {k: v for k, v in ex.items() if k.startswith("invalid")}
        check(f"{stem}.v1 ships at least one invalid example", len(invalids) >= 1)
        for k, v in invalids.items():
            errs = _validate(v, sc)
            check(f"{stem}.v1 {k} is correctly REJECTED by the schema", errs != [])

    # ── ContextTriageResult.v1: the 12 lanes + needs_action + a triage never serves truth. ──
    tr_sc = schemas.get("ContextTriageResult", {})
    check("ContextTriageResult.v1 lane enum is EXACTLY the 12 canonical triage lanes",
          set(_enum_of(tr_sc, "lane")) == _TRIAGE_LANES,
          str(sorted(_TRIAGE_LANES ^ set(_enum_of(tr_sc, "lane")))))
    check("ContextTriageResult.v1 requires needs_action + lane + fact_key",
          {"needs_action", "lane", "fact_key"} <= _req(tr_sc))
    check("ContextTriageResult.v1 pins serves_truth == [false] (a triage is a routing signal, never a fact)",
          _enum_of(tr_sc, "serves_truth") == [False])
    tr_valid = examples.get("ContextTriageResult", {}).get("valid", {})
    if tr_valid and tr_sc:
        bad_lane = dict(tr_valid); bad_lane["lane"] = "looks_fine"
        check("ContextTriageResult.v1 rejects an out-of-enum lane", _validate(bad_lane, tr_sc) != [])
        serves = dict(tr_valid); serves["serves_truth"] = True
        check("ContextTriageResult.v1 rejects serves_truth=true (red-team: a triage cannot be served as truth)",
              _validate(serves, tr_sc) != [])

    # ── ResearchTask.v1: agent is bounded, produces only a discovery report, never serves truth, no secrets. ──
    rt_sc = schemas.get("ResearchTask", {})
    check("ResearchTask.v1 produces pinned [source_discovery_report] (research yields candidate sources, NEVER a fact)",
          _enum_of(rt_sc, "produces") == ["source_discovery_report"])
    check("ResearchTask.v1 pins agent_may_serve_truth == [false] (THE INVARIANT — agents discover/propose, never serve)",
          _enum_of(rt_sc, "agent_may_serve_truth") == [False])
    check("ResearchTask.v1 requires bounds + question + authority_bar (a bounded research assignment)",
          {"bounds", "question", "authority_bar"} <= _req(rt_sc))
    check("ResearchTask.v1 bounds.secrets_allowed pinned [false] (a task never grants secrets)",
          _nested_enum(rt_sc, "bounds", "secrets_allowed") == [False])
    rt_valid = examples.get("ResearchTask", {}).get("valid", {})
    if rt_valid and rt_sc:
        serves = json.loads(json.dumps(rt_valid)); serves["agent_may_serve_truth"] = True
        check("ResearchTask.v1 rejects agent_may_serve_truth=true (red-team: agent cannot be told to serve truth)",
              _validate(serves, rt_sc) != [])
        prod = json.loads(json.dumps(rt_valid)); prod["produces"] = "canonical_fact"
        check("ResearchTask.v1 rejects produces='canonical_fact' (research never produces a fact)",
              _validate(prod, rt_sc) != [])
        sec = json.loads(json.dumps(rt_valid)); sec["bounds"]["secrets_allowed"] = True
        check("ResearchTask.v1 rejects bounds.secrets_allowed=true", _validate(sec, rt_sc) != [])

    # ── ResearchPlan.v1: a plan's execution yields a discovery report, its steps never serve a fact. ──
    rp_sc = schemas.get("ResearchPlan", {})
    check("ResearchPlan.v1 produces pinned [source_discovery_report]",
          _enum_of(rp_sc, "produces") == ["source_discovery_report"])
    check("ResearchPlan.v1 requires steps + step_budget + stop_conditions",
          {"steps", "step_budget", "stop_conditions"} <= _req(rp_sc))
    step_actions = set(rp_sc.get("properties", {}).get("steps", {}).get("items", {})
                       .get("properties", {}).get("action", {}).get("enum", []))
    check("ResearchPlan.v1 step actions are discovery-only (no 'serve_fact'/'promote')",
          step_actions and "serve_fact" not in step_actions and "promote" not in step_actions, str(sorted(step_actions)))

    # ── SourceDiscoveryReport.v1: attributable discoverer, never serves truth, every candidate has a handle. ──
    sdr_sc = schemas.get("SourceDiscoveryReport", {})
    check("SourceDiscoveryReport.v1 requires discovered_by (an attributable, non-serving agent)",
          "discovered_by" in _req(sdr_sc))
    check("SourceDiscoveryReport.v1 pins serves_truth == [false] (a discovery report can NEVER be served as truth)",
          _enum_of(sdr_sc, "serves_truth") == [False])
    cand_item = sdr_sc.get("properties", {}).get("candidates", {}).get("items", {})
    check("SourceDiscoveryReport.v1 every candidate REQUIRES a source_handle",
          "source_handle" in set(cand_item.get("required", [])))
    sdr_valid = examples.get("SourceDiscoveryReport", {}).get("valid", {})
    if sdr_valid and sdr_sc:
        serves = json.loads(json.dumps(sdr_valid)); serves["serves_truth"] = True
        check("SourceDiscoveryReport.v1 rejects serves_truth=true (red-team)", _validate(serves, sdr_sc) != [])
        nohandle = json.loads(json.dumps(sdr_valid))
        nohandle["candidates"] = [{"candidate_id": "c1", "authority_note": "no handle"}]
        check("SourceDiscoveryReport.v1 rejects a candidate that dropped its source_handle",
              _validate(nohandle, sdr_sc) != [])

    # ── SourceCandidate.v1: requires source_handle + authority_rank (handle inadmissible-without; authority comparable). ──
    sc_sc = schemas.get("SourceCandidate", {})
    check("SourceCandidate.v1 requires source_handle + authority_rank (no handle => inadmissible; authority comparable)",
          {"source_handle", "authority_rank"} <= _req(sc_sc))
    sc_valid = examples.get("SourceCandidate", {}).get("valid", {})
    if sc_valid and sc_sc:
        nohandle = {k: v for k, v in sc_valid.items() if k != "source_handle"}
        check("SourceCandidate.v1 rejects a candidate missing source_handle", _validate(nohandle, sc_sc) != [])
        norank = {k: v for k, v in sc_valid.items() if k != "authority_rank"}
        check("SourceCandidate.v1 rejects a candidate missing authority_rank", _validate(norank, sc_sc) != [])

    # ── SourceReliabilityScore.v1 / FactReliabilityScore.v1: a score ranks, it never serves truth. ──
    for stem, key in (("SourceReliabilityScore", "candidate"), ("FactReliabilityScore", "fact")):
        rs_sc = schemas.get(stem, {})
        check(f"{stem}.v1 requires authority_rank and an enumerated factors block",
              ("authority_rank" in _req(rs_sc) or "winning_authority_rank" in _req(rs_sc)) and "factors" in _req(rs_sc))
        check(f"{stem}.v1 pins served_as_truth == [false] (a reliability score is never itself a served fact)",
              _enum_of(rs_sc, "served_as_truth") == [False])
        # the factors block is closed (additionalProperties:false) so the factor set can't silently drift.
        check(f"{stem}.v1 factors block is closed (additionalProperties:false)",
              rs_sc.get("properties", {}).get("factors", {}).get("additionalProperties") is False)

    # ── SourceRecipe.v1: authority + cross_source policy + watch triggers (M2 rung is encoded, not re-derived). ──
    sr_sc = schemas.get("SourceRecipe", {})
    check("SourceRecipe.v1 requires authority + cross_source + watch_triggers",
          {"authority", "cross_source", "watch_triggers"} <= _req(sr_sc))
    check("SourceRecipe.v1 authority block requires authority_rank + source_type (reconciliation precedence encoded)",
          {"authority_rank", "source_type"} <= set(sr_sc.get("properties", {}).get("authority", {}).get("required", [])))
    check("SourceRecipe.v1 cross_source policy enum includes the official/two-source/tenant-signoff policies",
          {"single_official_source_ok", "two_independent_sources_required", "tenant_private_requires_human_signoff"}
          <= set(_nested_enum(sr_sc, "cross_source", "policy")))
    sr_valid = examples.get("SourceRecipe", {}).get("valid", {})
    if sr_valid and sr_sc:
        for f in ("cross_source", "watch_triggers", "authority"):
            broken = {k: v for k, v in sr_valid.items() if k != f}
            check(f"SourceRecipe.v1 rejects a recipe missing '{f}'", _validate(broken, sr_sc) != [])

    # ── VerificationRecipe.v1: authority + cross_source + freshness + tenant_scope; produces a run, not a fact;
    #    a FAQ can never be the winning source. ──
    vr_sc = schemas.get("VerificationRecipe", {})
    check("VerificationRecipe.v1 requires authority + cross_source + freshness + tenant_scope + validators",
          {"authority", "cross_source", "freshness", "tenant_scope", "validators"} <= _req(vr_sc))
    check("VerificationRecipe.v1 produces pinned [fact_verification_run] (a recipe verifies; it never promotes a fact)",
          _enum_of(vr_sc, "produces") == ["fact_verification_run"])
    winning = set(_nested_enum(vr_sc, "authority", "winning_source_type"))
    check("VerificationRecipe.v1 winning_source_type can NEVER be a FAQ/secondary (only high-authority sources win)",
          winning and "agency_faq" not in winning and "secondary_summary" not in winning and "blog" not in winning,
          str(sorted(winning)))
    vr_valid = examples.get("VerificationRecipe", {}).get("valid", {})
    if vr_valid and vr_sc:
        prod = json.loads(json.dumps(vr_valid)); prod["produces"] = "canonical_fact"
        check("VerificationRecipe.v1 rejects produces='canonical_fact'", _validate(prod, vr_sc) != [])
        faq = json.loads(json.dumps(vr_valid)); faq["authority"]["winning_source_type"] = "agency_faq"
        check("VerificationRecipe.v1 rejects winning_source_type='agency_faq' (red-team: FAQ cannot win)",
              _validate(faq, vr_sc) != [])

    # ── ExtractorSnippet.v1: THE load-bearing invariant — output is ALWAYS a candidate, sandboxed + unit-tested. ──
    es_sc = schemas.get("ExtractorSnippet", {})
    check("ExtractorSnippet.v1 produces pinned [fact_assertion_candidate] (NEVER served/canonical truth)",
          _enum_of(es_sc, "produces") == ["fact_assertion_candidate"])
    check("ExtractorSnippet.v1 claim_status pinned [candidate]", _enum_of(es_sc, "claim_status") == ["candidate"])
    check("ExtractorSnippet.v1 has_unit_test pinned [true] (no untested extractor)",
          _enum_of(es_sc, "has_unit_test") == [True])
    check("ExtractorSnippet.v1 sandbox_required pinned [true] (runs in a sandbox before any use)",
          _enum_of(es_sc, "sandbox_required") == [True])
    check("ExtractorSnippet.v1 requires source_handle (the candidate is traceable to a source)",
          "source_handle" in _req(es_sc))
    es_valid = examples.get("ExtractorSnippet", {}).get("valid", {})
    if es_valid and es_sc:
        canon = dict(es_valid); canon["produces"] = "canonical_fact"
        check("ExtractorSnippet.v1 REJECTS produces='canonical_fact' (red-team: extractor can't claim canonical truth)",
              _validate(canon, es_sc) != [])
        served = dict(es_valid); served["produces"] = "served_fact"
        check("ExtractorSnippet.v1 REJECTS produces='served_fact'", _validate(served, es_sc) != [])
        notest = dict(es_valid); notest["has_unit_test"] = False
        check("ExtractorSnippet.v1 REJECTS has_unit_test=false (red-team: untested extractor)", _validate(notest, es_sc) != [])
        nohandle = {k: v for k, v in es_valid.items() if k != "source_handle"}
        check("ExtractorSnippet.v1 REJECTS an extractor that dropped its source_handle", _validate(nohandle, es_sc) != [])
        nosandbox = dict(es_valid); nosandbox["sandbox_required"] = False
        check("ExtractorSnippet.v1 REJECTS sandbox_required=false", _validate(nosandbox, es_sc) != [])

    # ── GeneratedWorkerSpec.v1: proofs + idempotency + retry/DLQ; rides existing framework; never auto-active. ──
    gw_sc = schemas.get("GeneratedWorkerSpec", {})
    check("GeneratedWorkerSpec.v1 requires proof_scripts + idempotency_key_template + retry_policy",
          {"proof_scripts", "idempotency_key_template", "retry_policy"} <= _req(gw_sc))
    check("GeneratedWorkerSpec.v1 retry_policy requires max_attempts + backoff + dlq (retry/DLQ discipline)",
          {"max_attempts", "backoff", "dlq"} <= set(gw_sc.get("properties", {}).get("retry_policy", {}).get("required", [])))
    check("GeneratedWorkerSpec.v1 rides_existing_worker_framework pinned [true] (no 2nd runtime/worker framework)",
          _enum_of(gw_sc, "rides_existing_worker_framework") == [True])
    check("GeneratedWorkerSpec.v1 registration_status pinned [proposed] (nothing auto-registers/executes this pass)",
          _enum_of(gw_sc, "registration_status") == ["proposed"])
    gw_valid = examples.get("GeneratedWorkerSpec", {}).get("valid", {})
    if gw_valid and gw_sc:
        active = json.loads(json.dumps(gw_valid)); active["registration_status"] = "active"
        check("GeneratedWorkerSpec.v1 REJECTS registration_status='active' (red-team: unverified worker auto-registered)",
              _validate(active, gw_sc) != [])
        runtime = json.loads(json.dumps(gw_valid)); runtime["rides_existing_worker_framework"] = False
        check("GeneratedWorkerSpec.v1 REJECTS rides_existing_worker_framework=false (red-team: 2nd runtime)",
              _validate(runtime, gw_sc) != [])
        noretry = {k: v for k, v in gw_valid.items() if k != "retry_policy"}
        check("GeneratedWorkerSpec.v1 REJECTS a worker spec missing retry_policy", _validate(noretry, gw_sc) != [])

    # ── VerifierProofResult.v1: sandbox_passed + proof_passed + gate_decision; no secrets in the sandbox. ──
    vp_sc = schemas.get("VerifierProofResult", {})
    check("VerifierProofResult.v1 requires sandbox_passed + proof_passed + gate_decision",
          {"sandbox_passed", "proof_passed", "gate_decision"} <= _req(vp_sc))
    check("VerifierProofResult.v1 gate_decision enum ⊆ {approved, rejected, needs_human_approval}",
          set(_enum_of(vp_sc, "gate_decision")) == {"approved", "rejected", "needs_human_approval"})
    check("VerifierProofResult.v1 sandbox_report.secrets_present pinned [false] (a sandbox run carries no secrets)",
          vp_sc.get("properties", {}).get("sandbox_report", {}).get("properties", {})
          .get("secrets_present", {}).get("enum") == [False])

    # ── FactRefreshPlan.v1: watch mode + injected last_verified_at + computed next_check_at; refresh != fact. ──
    fr_sc = schemas.get("FactRefreshPlan", {})
    check("FactRefreshPlan.v1 requires watch_mode + last_verified_at + next_check_at + refresh_interval_seconds",
          {"watch_mode", "last_verified_at", "next_check_at", "refresh_interval_seconds"} <= _req(fr_sc))
    check("FactRefreshPlan.v1 produces pinned [fact_verification_run] (a refresh runs verification, not a publish)",
          _enum_of(fr_sc, "produces") == ["fact_verification_run"])
    check("FactRefreshPlan.v1 last_verified_at is an integer (injected epoch seconds — no wall-clock)",
          fr_sc.get("properties", {}).get("last_verified_at", {}).get("type") == "integer")
    fr_valid = examples.get("FactRefreshPlan", {}).get("valid", {})
    if fr_valid and fr_sc:
        # the next_check_at in the valid example IS last_verified_at + refresh_interval_seconds (deterministic).
        check("FactRefreshPlan.v1 valid example next_check_at == last_verified_at + refresh_interval_seconds (deterministic)",
              fr_valid.get("next_check_at") == fr_valid.get("last_verified_at") + fr_valid.get("refresh_interval_seconds"))

    # ── FactVerificationRun.v1: a run is a candidate + receipt, never canonical; carries the cost-ladder moat. ──
    fv_sc = schemas.get("FactVerificationRun", {})
    check("FactVerificationRun.v1 claim_status pinned [candidate] (a run yields a candidate, not canonical truth)",
          _enum_of(fv_sc, "claim_status") == ["candidate"])
    check("FactVerificationRun.v1 promoted_to_canonical pinned [false] (a run never self-promotes; reconciliation decides)",
          _enum_of(fv_sc, "promoted_to_canonical") == [False])
    check("FactVerificationRun.v1 requires source_handles + receipt_ref + cost_tracking",
          {"source_handles", "receipt_ref", "cost_tracking"} <= _req(fv_sc))
    ct_req = set(fv_sc.get("properties", {}).get("cost_tracking", {}).get("required", []))
    check("FactVerificationRun.v1 cost_tracking requires the 6 cost-ladder moat metrics",
          _COST_METRICS <= ct_req, str(sorted(_COST_METRICS - ct_req)))
    check("FactVerificationRun.v1 cost_tracking block is closed (additionalProperties:false — the metric set can't drift)",
          fv_sc.get("properties", {}).get("cost_tracking", {}).get("additionalProperties") is False)
    fv_valid = examples.get("FactVerificationRun", {}).get("valid", {})
    if fv_valid and fv_sc:
        promo = json.loads(json.dumps(fv_valid)); promo["promoted_to_canonical"] = True
        check("FactVerificationRun.v1 REJECTS promoted_to_canonical=true (red-team: a run can't self-promote)",
              _validate(promo, fv_sc) != [])
        served = json.loads(json.dumps(fv_valid)); served["claim_status"] = "served"
        check("FactVerificationRun.v1 REJECTS claim_status='served' (red-team: run output served as truth)",
              _validate(served, fv_sc) != [])
        for m in sorted(_COST_METRICS):
            broken = json.loads(json.dumps(fv_valid)); broken["cost_tracking"].pop(m, None)
            check(f"FactVerificationRun.v1 REJECTS a run missing cost metric '{m}'", _validate(broken, fv_sc) != [])

    ok = not fails
    print(
        f"\n{'PASS — check_contextops_contracts: 14 ContextOps contracts exist + validate (stdlib keywords only); each ships a passing valid example and a rejected invalid example; ContextTriageResult pins the 12 lanes + needs_action + serves_truth=false; ResearchTask/Plan produce ONLY a discovery report, agent_may_serve_truth pinned false, bounds carry no secrets; SourceDiscoveryReport names an attributable discoverer, serves_truth pinned false, every candidate carries a source_handle; SourceCandidate requires source_handle + authority_rank; ExtractorSnippet produces ONLY fact_assertion_candidate (canonical/served REJECTED), claim_status=candidate, has_unit_test + sandbox_required pinned true, source_handle required; GeneratedWorkerSpec requires proof_scripts + idempotency + retry/DLQ, rides the existing framework, registration_status pinned proposed (active/2nd-runtime REJECTED); VerifierProofResult requires sandbox_passed + proof_passed (no secrets in sandbox); SourceRecipe/VerificationRecipe require authority + cross_source + watch/freshness, a FAQ can never win; FactVerificationRun is a candidate + receipt, promoted_to_canonical pinned false, and carries the 6 cost-ladder moat metrics — THE INVARIANT (agents discover/propose; Baltor stores/verifies/reconciles/proves/consumes) is enforced at the contract layer.' if ok else f'{len(fails)} FAILURES: {fails}'}"
    )
    return 0 if ok else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: ContextOps Verification Foundry contract schemas enforce the invariant.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
