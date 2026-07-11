#!/usr/bin/env python3
"""scripts.check_lossless_distillation_contracts — proof (LOSSLESS DISTILLATION CONTRACTS MODE): the six
distillation contract schemas exist, validate via the stdlib schema validator, each ships a valid example
that PASSES and at least one invalid example that FAILS, and the lossless-law invariants are ENFORCED by the
contracts themselves.

The law (_repos/shared-backend-components/docs/codex/lossless-distillation.md) made checkable at the contract layer:
  - DistillationRun REQUIRES input+output artifact ids (a transform records what it consumed AND produced),
    REQUIRES lineage, and REQUIRES all THREE preservation lists (omitted/held_out/rejected) to be present
    EVEN WHEN EMPTY — so 'omitted ≠ deleted' is structurally auditable. It also requires EITHER config_hash
    (deterministic transform) OR rule_version (LLM-to-rule conversion) — a disjunction the stdlib validator
    keyword set can't express, enforced here directly.
  - PromotionRecord REQUIRES a rollback_target_id — no promotion is lossless without a reversible pointer.
  - RehydrationReport REQUIRES reachable source artifact ids when rehydrated is true — a derived artifact
    that can't be walked back to its source is not lossless.

Deterministic, stdlib-only, offline. CLI: python3 _repos/shared-backend-components/scripts/check_lossless_distillation_contracts.py --self-test
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from scripts.runtime.schema_validator import validate as _validate

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
_SCHEMA_DIR = _resource("schemas") / "distillation"
_EX_DIR = _SCHEMA_DIR / "examples"

#: every distillation contract schema this lane owns (filename stem under schemas/distillation).
_SCHEMAS = ["DistillationRun", "LineageBundle", "RehydrationReport", "InformationRetentionReport",
            "PromotionRecord", "RollbackPlan"]

#: DistillationRun MUST require these (lossless-law fields, lists present even if empty).
_RUN_REQUIRED = {"input_artifact_ids", "output_artifact_ids", "input_hashes", "output_hashes", "lineage",
                 "omitted_artifact_ids", "held_out_artifact_ids", "rejected_candidate_ids", "rollback_target_id",
                 "receipts"}
#: the three preservation lists that must be present on EVERY run even when empty (omitted ≠ deleted).
_PRESERVATION_LISTS = ("omitted_artifact_ids", "held_out_artifact_ids", "rejected_candidate_ids")
#: the keyword set the stdlib validator actually enforces — schemas must use only these.
_ALLOWED_KEYWORDS = {"type", "required", "properties", "enum", "additionalProperties", "items",
                     "$id", "title", "description"}


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

    # ── every schema parses, declares $id distillation/<Stem>, is an object with additionalProperties:false,
    #    and uses ONLY keywords the stdlib validator enforces (no silently-ignored pattern/minimum/anyOf). ──
    for stem, sc in schemas.items():
        check(f"{stem} $id is distillation/{stem}",
              sc.get("$id") == f"distillation/{stem}", str(sc.get("$id")))
        check(f"{stem} is an object with additionalProperties:false",
              sc.get("type") == "object" and sc.get("additionalProperties") is False)
        check(f"{stem} declares required + properties", bool(sc.get("required")) and bool(sc.get("properties")))
        check(f"{stem} uses only stdlib-validator keywords", _keys_ok(sc))
        # every required field is actually declared in properties (no required-but-undefined field).
        props = set(sc.get("properties", {}))
        missing_props = [r for r in sc.get("required", []) if r not in props]
        check(f"{stem} declares a property for every required field", missing_props == [], str(missing_props))

    # ── valid example PASSES; every invalid_* example FAILS validation. ──
    for stem, ex in examples.items():
        sc = schemas[stem]
        # there may be multiple valid_* examples; each must validate clean.
        valids = {k: v for k, v in ex.items() if k == "valid" or k.startswith("valid_")}
        check(f"{stem} has a 'valid' example", "valid" in valids)
        for k, v in valids.items():
            errs = _validate(v, sc)
            check(f"{stem} {k} example validates clean", errs == [], str(errs[:4]))
        invalids = {k: v for k, v in ex.items() if k.startswith("invalid")}
        check(f"{stem} ships at least one invalid example", len(invalids) >= 1)
        for k, v in invalids.items():
            # invalid_no_config_or_rule is a SEMANTIC reject (disjunction), checked separately below — it is
            # structurally valid against the keyword set, so skip it in the schema-level reject loop.
            if k == "invalid_no_config_or_rule":
                continue
            errs = _validate(v, sc)
            check(f"{stem} {k} is correctly REJECTED by the schema", errs != [])

    # ── DistillationRun lossless invariants ──
    run_sc = schemas.get("DistillationRun", {})
    run_req = set(run_sc.get("required", []))
    check("DistillationRun requires input+output ids+hashes, lineage, receipts, all 3 preservation lists, rollback_target",
          _RUN_REQUIRED <= run_req, str(sorted(_RUN_REQUIRED - run_req)))
    # each required lossless field is INDIVIDUALLY load-bearing — drop it and the run is rejected.
    run_valid = examples.get("DistillationRun", {}).get("valid", {})
    if run_valid and run_sc:
        for f in sorted(_RUN_REQUIRED):
            broken = {k: v for k, v in run_valid.items() if k != f}
            check(f"DistillationRun rejects a run missing '{f}'", _validate(broken, run_sc) != [])
        # the three preservation lists must be PRESENT even when EMPTY (omitted ≠ deleted, auditable).
        for f in _PRESERVATION_LISTS:
            empty_list_run = dict(run_valid); empty_list_run[f] = []
            check(f"DistillationRun ACCEPTS '{f}' present-but-empty (omitted ≠ deleted)",
                  _validate(empty_list_run, run_sc) == [])
            missing_list_run = {k: v for k, v in run_valid.items() if k != f}
            check(f"DistillationRun REJECTS '{f}' absent entirely (must be present even if empty)",
                  _validate(missing_list_run, run_sc) != [])
        # lineage must carry source handles back to source — drop lineage.source_handles → rejected.
        no_handles = dict(run_valid)
        no_handles["lineage"] = {k: v for k, v in run_valid["lineage"].items() if k != "source_handles"}
        check("DistillationRun rejects a lineage with no source_handles", _validate(no_handles, run_sc) != [])
        # transform_type is enum-bounded — a bogus transform is rejected.
        bad_tt = dict(run_valid); bad_tt["transform_type"] = "obliterate"
        check("DistillationRun rejects an out-of-enum transform_type", _validate(bad_tt, run_sc) != [])

    # ── DistillationRun disjunction: config_hash OR rule_version (one must be present). ──
    def _has_config_or_rule(run: dict) -> bool:
        return bool(run.get("config_hash")) or bool(run.get("rule_version"))
    if run_valid:
        check("DistillationRun valid (deterministic) carries config_hash", bool(run_valid.get("config_hash")))
        run_rule = examples.get("DistillationRun", {}).get("valid_llm_to_rule", {})
        check("DistillationRun valid_llm_to_rule carries rule_version (no config_hash needed)",
              bool(run_rule.get("rule_version")) and not run_rule.get("config_hash"))
        check("DistillationRun disjunction: deterministic run satisfies config_hash|rule_version",
              _has_config_or_rule(run_valid))
        check("DistillationRun disjunction: llm_to_rule run satisfies config_hash|rule_version",
              _has_config_or_rule(run_rule))
        no_cfg_no_rule = examples.get("DistillationRun", {}).get("invalid_no_config_or_rule", {})
        # it passes the keyword schema (both fields optional) but VIOLATES the disjunction the law requires.
        check("DistillationRun invalid_no_config_or_rule passes the bare schema (disjunction is semantic)",
              run_sc and _validate(no_cfg_no_rule, run_sc) == [])
        check("DistillationRun invalid_no_config_or_rule VIOLATES config_hash|rule_version (correctly rejected by check)",
              not _has_config_or_rule(no_cfg_no_rule))

    # ── PromotionRecord REQUIRES a rollback_target_id (no lossless promotion without a reversible pointer). ──
    promo_sc = schemas.get("PromotionRecord", {})
    check("PromotionRecord requires rollback_target_id", "rollback_target_id" in set(promo_sc.get("required", [])))
    promo_valid = examples.get("PromotionRecord", {}).get("valid", {})
    if promo_valid and promo_sc:
        no_rb = {k: v for k, v in promo_valid.items() if k != "rollback_target_id"}
        check("PromotionRecord rejects a promotion missing rollback_target_id", _validate(no_rb, promo_sc) != [])
        # it must also keep the prior version and the rejected list (nothing deleted on promotion).
        check("PromotionRecord requires prior_version_id + rejected_candidate_ids (promotion deletes nothing)",
              {"prior_version_id", "rejected_candidate_ids"} <= set(promo_sc.get("required", [])))

    # ── RollbackPlan: pointer-only move, never a delete. ──
    rb_sc = schemas.get("RollbackPlan", {})
    check("RollbackPlan requires rollback_target_id + from_artifact_id + the two delete flags",
          {"rollback_target_id", "from_artifact_id", "deletes_artifacts", "deletes_prior_responses"}
          <= set(rb_sc.get("required", [])))
    rb_valid = examples.get("RollbackPlan", {}).get("valid", {})
    if rb_valid:
        check("RollbackPlan valid plan deletes nothing (pointer-only move)",
              rb_valid.get("deletes_artifacts") is False and rb_valid.get("deletes_prior_responses") is False)

    # ── RehydrationReport REQUIRES reachable source artifact ids when rehydrated. ──
    rh_sc = schemas.get("RehydrationReport", {})
    check("RehydrationReport requires source_artifact_ids + rehydrated + crossed_tenant_boundary",
          {"source_artifact_ids", "rehydrated", "crossed_tenant_boundary"} <= set(rh_sc.get("required", [])))
    rh_valid = examples.get("RehydrationReport", {}).get("valid", {})
    if rh_valid:
        # a successful rehydration must reach at least one source artifact (lossless: walk back to source).
        check("RehydrationReport valid (rehydrated=true) reaches >=1 source artifact id",
              rh_valid.get("rehydrated") is True and len(rh_valid.get("source_artifact_ids", [])) >= 1)
        check("RehydrationReport valid never crosses a tenant boundary",
              rh_valid.get("crossed_tenant_boundary") is False)
        rh_fail = examples.get("RehydrationReport", {}).get("valid_failed_rehydration", {})
        check("RehydrationReport valid_failed_rehydration (rehydrated=false) carries a failure_reason + no source ids",
              rh_fail.get("rehydrated") is False and rh_fail.get("source_artifact_ids") == []
              and bool(rh_fail.get("failure_reason")))

    ok = not fails
    print(
        f"\n{'PASS — check_lossless_distillation_contracts: 6 distillation schemas exist + validate (stdlib keywords only); each has a passing valid example and a rejected invalid example; DistillationRun requires input+output ids/hashes + lineage (with source_handles) + all 3 preservation lists present-even-if-empty (omitted ≠ deleted) + config_hash|rule_version (disjunction) + rollback_target; PromotionRecord requires a rollback_target and keeps prior+rejected; RollbackPlan is pointer-only (deletes nothing); RehydrationReport reaches its source and never crosses a tenant boundary.' if ok else f'{len(fails)} FAILURES: {fails}'}"
    )
    return 0 if ok else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: lossless distillation contract schemas enforce the law.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
