#!/usr/bin/env python3
"""scripts.check_parallel_path_contracts — proof (PARALLEL-PATH CONTRACTS MODE): the 6 parallel-path
experiment contract schemas exist, validate via the stdlib schema validator (no `jsonschema`, Python 3.14),
each ships a passing valid example and a rejected invalid example, the contract registry covers every schema,
and the NON-NEGOTIABLE parallel-path semantics are enforceable at the contract layer.

The contract layer for "run a baseline path + candidate paths on the SAME input, compare, and promote a
candidate ONLY through a passing decision — never serve a candidate as truth" — made checkable:
  - PathDefinition REQUIRES a rollback_target (a candidate without it is not promotable/reversible) and
    its mode is enum-bounded to {baseline,candidate,shadow,canary,fallback,deprecated} — no ad-hoc 'champion'.
  - ParallelPathRun REQUIRES input_snapshot_hash (proof baseline + candidates saw identical input),
    pins candidate_served == [false] (a candidate's output is NEVER served as truth — a true value is
    structurally rejected), and the baseline_result.mode is bounded to {baseline,fallback} (the served
    result can never be a candidate/shadow/canary).
  - PathComparisonReport's per-candidate verdict REQUIRES all the gates (same_output_contract,
    output_equivalent, source_handles_preserved, held_out_not_leaked, safety_ok, cost_delta) and a
    recommended_action enum-bounded so there is no 'serve_candidate' action.
  - PathPromotionDecision REQUIRES all six gates + a rollback_target, and decision is enum-bounded to
    {promote,keep_baseline} — the only object that can authorize a promotion, never a 'serve_candidate'.
  - PathRollbackPlan pins deletes_paths == [false] and deletes_prior_runs == [false] (rollback is a
    pointer move, never a delete) and REQUIRES a rollback_target_path_id.
  - PathCostReport carries the pricebook-derived relative cost with currency pinned to 'relative-unit'
    and confidence enum-bounded to {high,low} (a 'low' placeholder never silently becomes high).

Deterministic, stdlib-only, offline (no network, no RNG, no wall-clock).
CLI: PYTHONPATH=. python3 scripts/check_parallel_path_contracts.py --self-test
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

_SCHEMA_DIR = _REPO / "schemas" / "experiments"
_EX_DIR = _SCHEMA_DIR / "examples"
_REGISTRY = _REPO / "architecture" / "contract_registry.json"

#: the 6 parallel-path contracts this lane owns (filename stem under schemas/experiments).
_SCHEMAS = [
    "PathDefinition", "ParallelPathRun", "PathComparisonReport",
    "PathPromotionDecision", "PathRollbackPlan", "PathCostReport",
]

#: the keyword set the stdlib validator actually enforces — schemas must use only these (no silently-ignored
#: pattern/minimum/anyOf that would give a false sense of validation). const/allOf/if/then/else are the
#: cross-field set the validator now honors (used to bind a decision's label to its own gate booleans).
_ALLOWED_KEYWORDS = {"type", "required", "properties", "enum", "additionalProperties", "items",
                     "const", "allOf", "if", "then", "else",
                     "$id", "title", "description"}

#: the promotion gates the decision MUST require (per the ENGINE DESIGN). same_input is the input-attestation
#: gate added to reject a different-input comparison on the INPUT (not inferred from output divergence).
_DECISION_GATES = {
    "same_input", "same_output_contract", "output_equivalent", "source_handles_preserved",
    "held_out_not_leaked", "safety_ok", "cost_acceptable",
}
#: the gates each PathComparisonReport candidate verdict MUST carry.
_VERDICT_GATES = {
    "same_input", "same_output_contract", "output_equivalent", "source_handles_preserved",
    "held_out_not_leaked", "safety_ok", "cost_delta", "recommended_action",
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
        if k in ("items", "if", "then", "else") and isinstance(v, dict):
            if not _keys_ok(v):
                return False
            continue
        if k == "allOf" and isinstance(v, list):
            if not all(_keys_ok(sub) for sub in v):
                return False
            continue
        if k not in _ALLOWED_KEYWORDS:
            return False
    return True


def _enum_of(schema: dict, field: str) -> list:
    return schema.get("properties", {}).get(field, {}).get("enum", [])


def _verdict_item_schema(report_sc: dict) -> dict:
    return report_sc.get("properties", {}).get("candidate_verdicts", {}).get("items", {})


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

    check("all 6 parallel-path contracts are present", len(schemas) == 6, f"got {len(schemas)}")

    # ── every schema parses, declares $id experiments/<Stem>, is an object with additionalProperties:false,
    #    declares required+properties, uses ONLY stdlib-validator keywords, defines a property for every
    #    required field, and requires an injected time field. ──
    for stem, sc in schemas.items():
        check(f"{stem} $id is experiments/{stem}",
              sc.get("$id") == f"experiments/{stem}", str(sc.get("$id")))
        check(f"{stem} is an object with additionalProperties:false",
              sc.get("type") == "object" and sc.get("additionalProperties") is False)
        check(f"{stem} declares required + properties", bool(sc.get("required")) and bool(sc.get("properties")))
        check(f"{stem} uses only stdlib-validator keywords", _keys_ok(sc))
        props = set(sc.get("properties", {}))
        missing_props = [r for r in sc.get("required", []) if r not in props]
        check(f"{stem} declares a property for every required field", missing_props == [], str(missing_props))
        time_fields = [k for k in sc.get("required", []) if k.endswith("_at")]
        check(f"{stem} requires an injected time field (deterministic, no wall-clock)", len(time_fields) >= 1)
        check(f"{stem} schema_version enum pins {stem}",
              _enum_of(sc, "schema_version") == [f"{stem}"], str(_enum_of(sc, "schema_version")))

    # ── valid example(s) PASS; every invalid_* example FAILS schema validation. ──
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

    # ── PathDefinition: rollback_target REQUIRED (reversible/promotable); mode enum-bounded. ──
    pd_sc = schemas.get("PathDefinition", {})
    check("PathDefinition REQUIRES rollback_target (no reversible promotion without it)",
          "rollback_target" in set(pd_sc.get("required", [])))
    check("PathDefinition mode enum is exactly {baseline,candidate,shadow,canary,fallback,deprecated}",
          set(_enum_of(pd_sc, "mode")) == {"baseline", "candidate", "shadow", "canary", "fallback", "deprecated"},
          str(_enum_of(pd_sc, "mode")))
    check("PathDefinition REQUIRES input_contract + output_contract (apples-to-apples paths)",
          {"input_contract", "output_contract"} <= set(pd_sc.get("required", [])))
    pd_valid = examples.get("PathDefinition", {}).get("valid", {})
    if pd_valid and pd_sc:
        no_rb = {k: v for k, v in pd_valid.items() if k != "rollback_target"}
        check("PathDefinition rejects a path missing rollback_target", _validate(no_rb, pd_sc) != [])
        bad_mode = dict(pd_valid); bad_mode["mode"] = "champion"
        check("PathDefinition rejects an out-of-enum mode ('champion')", _validate(bad_mode, pd_sc) != [])

    # ── ParallelPathRun: SAME input (snapshot hash), candidate NEVER served. ──
    ppr_sc = schemas.get("ParallelPathRun", {})
    ppr_req = set(ppr_sc.get("required", []))
    check("ParallelPathRun REQUIRES input_snapshot_hash (baseline + candidates saw identical input)",
          "input_snapshot_hash" in ppr_req)
    check("ParallelPathRun pins candidate_served == [false] (a candidate output is NEVER served as truth)",
          _enum_of(ppr_sc, "candidate_served") == [False])
    check("ParallelPathRun REQUIRES baseline_result + candidate_results + served_path_id + candidate_served",
          {"baseline_result", "candidate_results", "served_path_id", "candidate_served"} <= ppr_req)
    base_mode_enum = set(ppr_sc.get("properties", {}).get("baseline_result", {})
                         .get("properties", {}).get("mode", {}).get("enum", []))
    check("ParallelPathRun baseline_result.mode is bounded to {baseline,fallback} (served result is never a candidate)",
          base_mode_enum == {"baseline", "fallback"}, str(base_mode_enum))
    ppr_valid = examples.get("ParallelPathRun", {}).get("valid", {})
    if ppr_valid and ppr_sc:
        served = dict(ppr_valid); served["candidate_served"] = True
        check("ParallelPathRun rejects candidate_served=true (cannot smuggle a candidate to the consumer)",
              _validate(served, ppr_sc) != [])
        no_hash = {k: v for k, v in ppr_valid.items() if k != "input_snapshot_hash"}
        check("ParallelPathRun rejects a run missing input_snapshot_hash", _validate(no_hash, ppr_sc) != [])
        check("ParallelPathRun valid example served the BASELINE path (served_path_id == baseline_result.path_id)",
              ppr_valid.get("served_path_id") == ppr_valid.get("baseline_result", {}).get("path_id"))

    # ── PathComparisonReport: every gate present per verdict; no 'serve_candidate' action. ──
    pcr_sc = schemas.get("PathComparisonReport", {})
    verdict_item = _verdict_item_schema(pcr_sc)
    verdict_req = set(verdict_item.get("required", []))
    check("PathComparisonReport verdict REQUIRES every gate (same_output_contract/output_equivalent/handles/held_out/safety/cost_delta/action)",
          _VERDICT_GATES <= verdict_req, str(sorted(_VERDICT_GATES - verdict_req)))
    action_enum = verdict_item.get("properties", {}).get("recommended_action", {}).get("enum", [])
    check("PathComparisonReport recommended_action enum is exactly {promote,keep_baseline,investigate} (no 'serve_candidate')",
          set(action_enum) == {"promote", "keep_baseline", "investigate"}, str(action_enum))
    leak_keep = examples.get("PathComparisonReport", {}).get("valid_keep_baseline_on_leak", {})
    if leak_keep:
        v0 = (leak_keep.get("candidate_verdicts") or [{}])[0]
        check("PathComparisonReport a held-out LEAK verdict (held_out_not_leaked=false) recommends keep_baseline, not promote",
              v0.get("held_out_not_leaked") is False and v0.get("recommended_action") == "keep_baseline")

    # ── PathPromotionDecision: ALL gates + rollback_target REQUIRED; only object that promotes. ──
    ppd_sc = schemas.get("PathPromotionDecision", {})
    ppd_req = set(ppd_sc.get("required", []))
    check("PathPromotionDecision REQUIRES all six gates",
          _DECISION_GATES <= ppd_req, str(sorted(_DECISION_GATES - ppd_req)))
    check("PathPromotionDecision REQUIRES rollback_target (a promotion is always reversible)",
          "rollback_target" in ppd_req)
    check("PathPromotionDecision decision enum is exactly {promote,keep_baseline} (no 'serve_candidate')",
          set(_enum_of(ppd_sc, "decision")) == {"promote", "keep_baseline"}, str(_enum_of(ppd_sc, "decision")))
    ppd_valid = examples.get("PathPromotionDecision", {}).get("valid", {})
    if ppd_valid and ppd_sc:
        no_rb = {k: v for k, v in ppd_valid.items() if k != "rollback_target"}
        check("PathPromotionDecision rejects a decision missing rollback_target", _validate(no_rb, ppd_sc) != [])
        for g in sorted(_DECISION_GATES):
            broken = {k: v for k, v in ppd_valid.items() if k != g}
            check(f"PathPromotionDecision rejects a decision missing gate '{g}'", _validate(broken, ppd_sc) != [])
        check("PathPromotionDecision valid 'promote' example has all six gates true and rollback_target == baseline_path_id",
              all(ppd_valid.get(g) is True for g in _DECISION_GATES)
              and ppd_valid.get("rollback_target") == ppd_valid.get("baseline_path_id"))
    ppd_keep = examples.get("PathPromotionDecision", {}).get("valid_keep_baseline", {})
    if ppd_keep:
        check("PathPromotionDecision a failing-gate decision is keep_baseline with promoted_path_id == null",
              ppd_keep.get("decision") == "keep_baseline" and ppd_keep.get("promoted_path_id") is None
              and ppd_keep.get("rollback_target") == ppd_keep.get("baseline_path_id"))

    # ── PathRollbackPlan: pointer move only (deletes pinned false), target required. ──
    prp_sc = schemas.get("PathRollbackPlan", {})
    check("PathRollbackPlan pins deletes_paths == [false] (rollback never deletes a path definition)",
          _enum_of(prp_sc, "deletes_paths") == [False])
    check("PathRollbackPlan pins deletes_prior_runs == [false] (prior ParallelPathRuns stay readable)",
          _enum_of(prp_sc, "deletes_prior_runs") == [False])
    check("PathRollbackPlan REQUIRES rollback_target_path_id + from_path_id + promotion_decision_id",
          {"rollback_target_path_id", "from_path_id", "promotion_decision_id"} <= set(prp_sc.get("required", [])))
    prp_valid = examples.get("PathRollbackPlan", {}).get("valid", {})
    if prp_valid and prp_sc:
        del_true = dict(prp_valid); del_true["deletes_paths"] = True
        check("PathRollbackPlan rejects deletes_paths=true", _validate(del_true, prp_sc) != [])
        no_tgt = {k: v for k, v in prp_valid.items() if k != "rollback_target_path_id"}
        check("PathRollbackPlan rejects a plan missing rollback_target_path_id", _validate(no_tgt, prp_sc) != [])

    # ── PathCostReport: pricebook-relative cost; currency + confidence enum-pinned. ──
    pcost_sc = schemas.get("PathCostReport", {})
    check("PathCostReport currency enum is exactly {relative-unit} (offline ranking units, not real money)",
          _enum_of(pcost_sc, "currency") == ["relative-unit"], str(_enum_of(pcost_sc, "currency")))
    check("PathCostReport confidence enum is exactly {high,low} (a 'low' placeholder never becomes 'medium'/'high' silently)",
          set(_enum_of(pcost_sc, "confidence")) == {"high", "low"}, str(_enum_of(pcost_sc, "confidence")))
    check("PathCostReport REQUIRES backend_id + pricebook_version + estimated_cost + confidence",
          {"backend_id", "pricebook_version", "estimated_cost", "confidence"} <= set(pcost_sc.get("required", [])))
    pcost_valid = examples.get("PathCostReport", {}).get("valid", {})
    if pcost_valid and pcost_sc:
        bad_conf = dict(pcost_valid); bad_conf["confidence"] = "medium"
        check("PathCostReport rejects confidence='medium'", _validate(bad_conf, pcost_sc) != [])
        bad_cur = dict(pcost_valid); bad_cur["currency"] = "USD"
        check("PathCostReport rejects currency='USD'", _validate(bad_cur, pcost_sc) != [])
        # the valid example's estimated_cost equals request + duration*dur_s + idle*idle_s (the documented formula).
        expected = (pcost_valid["request_cost"]
                    + pcost_valid["duration_cost_per_s"] * pcost_valid["estimated_duration_s"]
                    + pcost_valid["idle_cost_per_s"] * pcost_valid["estimated_idle_s"])
        check("PathCostReport valid example estimated_cost matches request + duration*s + idle*s",
              abs(pcost_valid["estimated_cost"] - expected) < 1e-9, f"{pcost_valid['estimated_cost']} vs {expected}")
        # the backend_id names a real pricebook entry (config is the single source of cost).
        pb = json.loads((_REPO / "architecture" / "execution_backend_pricebook.json").read_text())
        check("PathCostReport valid example backend_id exists in the execution-backend pricebook",
              pcost_valid["backend_id"] in pb.get("backends", {}), pcost_valid["backend_id"])
        check("PathCostReport valid example pricebook_version matches the pricebook version",
              pcost_valid["pricebook_version"] == pb.get("version"))

    # ── contract registry covers each schema (no contract sprawl). ──
    reg = json.loads(_REGISTRY.read_text())
    reg_schemas = {item.get("schema") for item in reg.get("artifact_types", [])}
    reg_names = {item.get("name") for item in reg.get("artifact_types", [])}
    for stem in _SCHEMAS:
        rel = f"schemas/experiments/{stem}.schema.json"
        check(f"contract registry covers {stem} (schema path registered)", rel in reg_schemas, rel)
        check(f"contract registry has a {stem} entry by name", stem in reg_names)
    # every registered experiments schema points at a file that exists.
    missing = [item["schema"] for item in reg.get("artifact_types", [])
               if str(item.get("schema", "")).startswith("schemas/experiments/")
               and not (_REPO / item["schema"]).exists()]
    check("every registered experiments schema file exists", missing == [], str(missing))

    ok = not fails
    print(
        f"\n{'PASS — check_parallel_path_contracts: 6 parallel-path contracts exist + validate (stdlib keywords only); each ships a passing valid example and a rejected invalid example; PathDefinition requires rollback_target and a bounded mode; ParallelPathRun requires input_snapshot_hash and pins candidate_served=false (a candidate is never served) with the served result bounded to baseline/fallback; PathComparisonReport requires all gates per verdict and has no serve_candidate action; PathPromotionDecision requires all six gates + a rollback_target and only {promote,keep_baseline}; PathRollbackPlan is a pointer move (deletes pinned false); PathCostReport carries pricebook-relative cost with currency+confidence pinned; the contract registry covers every schema.' if ok else f'{len(fails)} FAILURES: {fails}'}"
    )
    return 0 if ok else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: parallel-path experiment contract schemas enforce the non-negotiable semantics.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
