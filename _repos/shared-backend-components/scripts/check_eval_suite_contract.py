#!/usr/bin/env python3
"""scripts.check_eval_suite_contract — PROOF: the EVAL/BENCHMARK is a first-class PurposeTask/CapabilityTask
contract field ("the benchmark IS the spec"; closes vision gap D-2, _repos/shared-backend-components/docs/architecture/eval-as-contract.md).

Asserts, deterministically + offline:
  A. Both schemas (PurposeTaskSpec + CapabilityTask) are valid Draft-2020-12 AND still validate a spec
     WITHOUT eval_suite (backward compatible) — via jsonschema AND the in-repo stdlib validator.
  B. A spec WITH a (raw and normalized) eval_suite validates; a MALFORMED eval_suite is REJECTED by the
     schema (example missing `expected`, missing suite_id, bad judge enum).
  C. eval_suite round-trips through PurposeTaskSpec losslessly (from_dict(d).to_dict() == d; eval_suite
     preserved; with_eval_suite produces a gate-readable spec) and eval_suite_for(spec) yields the normalized
     suite the runtime gate consumes (eval_pairs == the (input, expected) rows).
  D. No-magic-values: the gate_threshold default == scripts.teleon_local_runtime.PROMOTE_AT, gate_basis ==
     GATE_BASIS, and holdout_policy is DERIVED from TRAIN_PARITY — single-sourced, not re-typed here.
  E. Honest benchmark_ref: an unregistered ref raises BenchmarkNotRegisteredError (never a fabricated suite);
     a registered ref resolves.
  F. Validation rules: XOR(examples, benchmark_ref); a model-built capability needs >=1 inline example; judge
     enum + threshold range enforced; an invalid suite fails CLOSED (with_eval_suite raises ValueError).
  G. Projection redaction: the customer view summarizes the eval_suite (id/count/threshold/judge) but NEVER
     leaks an example's `expected` answer key; the clean-tripwire still passes.

CLI: python3 _repos/shared-backend-components/scripts/check_eval_suite_contract.py --self-test  → exit 0/1.
"""
from __future__ import annotations

import json
from src.teleon.runtime.tenancy import py_const_src_teleon_runtime_tenancy__INTERNAL_TENANT_ID
import sys
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from jsonschema import Draft202012Validator  # noqa: E402

from scripts.runtime import schema_validator as sv  # noqa: E402
from scripts.teleon_local_runtime import GATE_BASIS, PROMOTE_AT, TRAIN_PARITY  # canonical gate constants  # noqa: E402
from src.teleon.purpose_tasks import PurposeTaskSpec, eval_suite as es, eval_suite_for  # noqa: E402
from src.teleon.purpose_tasks.projections import customer_projection, customer_view_is_clean  # noqa: E402

_PT_REF = "purpose_tasks/PurposeTaskSpec"
_PT_PATH = _resource("schemas") / "purpose_tasks" / "PurposeTaskSpec.schema.json"
_CT_PATH = _resource("schemas") / "workers" / "CapabilityTask.schema.json"
_NOW = "2026-06-11T00:00:00Z"

_INLINE = {"suite_id": "suite.dates@v1#h7a2",
           "examples": [{"input": "Filed 3/14/2026.", "expected": "Filed 2026-03-14."},
                        {"input": "No dates here.", "expected": "No dates here."}]}
_REF_SUITE = {"suite_id": "suite.legal@v3#h9c1", "benchmark_ref": "registry://acme/legal-cites@v3"}


def _pt_base() -> dict:
    return {"schema_version": "PurposeTaskSpec", "task_id": "pt.eval_demo@v1#h001",
            "purpose": "Pull X from a source.", "capability_slot": "fetch_demo",
            "input_contract": "DemoQuery", "output_contract": "DemoRecord",
            "success_criteria": {"max_cost": 5.0, "min_source_handles": 1},
            "promotion_criteria": {"cost_tolerance": 0.0}, "connected_to": ["demo.consumer"],
            "defined_at": _NOW}


def _ct_base() -> dict:
    return {"task_id": "ct.eval_demo@v1#h002", "tenant_id": py_const_src_teleon_runtime_tenancy__INTERNAL_TENANT_ID, "capability_id": "cap-dates",
            "status": "queued", "idempotency_key": "k-001", "max_attempts": 3, "attempt": 0,
            "created_at": _NOW}


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    pt_schema = json.loads(_PT_PATH.read_text(encoding="utf-8"))
    ct_schema = json.loads(_CT_PATH.read_text(encoding="utf-8"))
    pt_v = Draft202012Validator(pt_schema)
    ct_v = Draft202012Validator(ct_schema)

    # A. valid Draft-2020-12 + backward compatible (no eval_suite)
    for nm, sc in (("PurposeTaskSpec", pt_schema), ("CapabilityTask", ct_schema)):
        try:
            Draft202012Validator.check_schema(sc)
            check(f"A: {nm} is valid Draft-2020-12", True)
        except Exception as e:  # pragma: no cover
            check(f"A: {nm} is valid Draft-2020-12", False, str(e))
    check("A: PurposeTask WITHOUT eval_suite validates (jsonschema)", pt_v.is_valid(_pt_base()))
    check("A: PurposeTask WITHOUT eval_suite validates (stdlib sv)", sv.validate(_pt_base(), pt_schema) == [])
    check("A: CapabilityTask WITHOUT eval_suite validates (jsonschema)", ct_v.is_valid(_ct_base()))

    # B. WITH eval_suite validates (raw + normalized); malformed rejected
    spec_pt = PurposeTaskSpec.from_dict(_pt_base()).with_eval_suite(_INLINE).to_dict()
    spec_ct = {**_ct_base(), "eval_suite": es.normalize_eval_suite(_INLINE)}
    check("B: PurposeTask WITH normalized eval_suite validates (jsonschema)", pt_v.is_valid(spec_pt))
    check("B: PurposeTask WITH normalized eval_suite validates (stdlib sv)", sv.validate(spec_pt, pt_schema) == [])
    check("B: PurposeTask WITH RAW eval_suite validates (jsonschema)",
          pt_v.is_valid({**_pt_base(), "eval_suite": _INLINE}))
    check("B: CapabilityTask WITH eval_suite validates (jsonschema)", ct_v.is_valid(spec_ct))
    check("B: CapabilityTask WITH eval_suite validates (stdlib sv)", sv.validate(spec_ct, ct_schema) == [])
    check("B: schema REJECTS an example missing `expected`",
          not pt_v.is_valid({**_pt_base(), "eval_suite": {"suite_id": "x", "examples": [{"input": "a"}]}}))
    check("B: schema REJECTS eval_suite missing suite_id",
          not pt_v.is_valid({**_pt_base(), "eval_suite": {"examples": [{"input": "a", "expected": "b"}]}}))
    check("B: schema REJECTS a bad judge enum",
          not pt_v.is_valid({**_pt_base(),
                             "eval_suite": {**_INLINE, "judge": "vibes"}}))

    # C. round-trip + the runtime-gate seam
    rt = PurposeTaskSpec.from_dict(spec_pt)
    check("C: round-trip from_dict(d).to_dict() == d", rt.to_dict() == spec_pt)
    check("C: round-trip preserves eval_suite", rt.to_dict().get("eval_suite") == spec_pt["eval_suite"])
    check("C: PurposeTaskSpec == its dict", rt == spec_pt)
    norm = eval_suite_for(spec_pt)
    check("C: eval_suite_for(spec) == the normalized stored suite", norm == spec_pt["eval_suite"])
    check("C: eval_pairs(suite) == the (input, expected) rows the gate executes",
          es.eval_pairs(norm) == [("Filed 3/14/2026.", "Filed 2026-03-14."), ("No dates here.", "No dates here.")])
    check("C: a spec without eval_suite → eval_suite_for is None (backward compatible)",
          eval_suite_for(_pt_base()) is None)

    # D. no-magic-values: single-sourced from the live gate constants
    check("D: gate_threshold default == teleon_local_runtime.PROMOTE_AT (single source)",
          norm["gate_threshold"] == float(PROMOTE_AT))
    check("D: gate_basis == teleon_local_runtime.GATE_BASIS (single source)", norm["gate_basis"] == GATE_BASIS)
    expect_side = "even=train" if TRAIN_PARITY == 0 else "odd=train"
    check("D: holdout_policy derived from TRAIN_PARITY (not re-typed)",
          norm["holdout_policy"] == es.default_holdout_policy() and expect_side in norm["holdout_policy"])

    # E. honest benchmark_ref
    check("E: benchmark_ref suite validates (jsonschema)", pt_v.is_valid({**_pt_base(), "eval_suite": _REF_SUITE}))
    raised = False
    try:
        es.resolve_benchmark_ref(_REF_SUITE["benchmark_ref"], registry={})
    except es.BenchmarkNotRegisteredError as e:
        raised = "not registered" in str(e) and "fabricated" in str(e)
    check("E: unregistered benchmark_ref raises honestly (no fabricated suite)", raised)
    check("E: a registered benchmark_ref resolves",
          es.resolve_benchmark_ref("rk", registry={"rk": _INLINE}) == _INLINE)

    # F. validation rules + fail-closed
    check("F: XOR — examples AND benchmark_ref together is rejected",
          any("not both" in e for e in es.validate_eval_suite(
              {"suite_id": "x", "examples": [{"input": 1, "expected": 2}], "benchmark_ref": "r"})))
    check("F: XOR — neither carrier is rejected", any("one of" in e for e in es.validate_eval_suite({"suite_id": "x"})))
    check("F: a model-built capability needs >=1 inline example",
          any("model-built" in e for e in es.validate_eval_suite({"suite_id": "x", "examples": []}, model_built=True)))
    check("F: a model-built capability MAY use a benchmark_ref (registry carries the examples)",
          es.validate_eval_suite(_REF_SUITE, model_built=True) == [])
    check("F: bad judge / out-of-range threshold rejected",
          any("judge" in e for e in es.validate_eval_suite({**_INLINE, "judge": "x"}))
          and any("gate_threshold" in e for e in es.validate_eval_suite({**_INLINE, "gate_threshold": 2.0})))
    fc = False
    try:
        PurposeTaskSpec.from_dict(_pt_base()).with_eval_suite({"suite_id": "x"})  # neither carrier → invalid
    except ValueError:
        fc = True
    check("F: with_eval_suite fails CLOSED on an invalid suite (ValueError)", fc)

    # F2. a model-built spec (mode=model) round-trips with a non-empty suite and is gate-readable
    mb_spec = PurposeTaskSpec.from_dict({**_pt_base(), "build_mode": "model"}).with_eval_suite(_INLINE).to_dict()
    check("F2: model-built spec with inline suite validates + is gate-readable",
          pt_v.is_valid(mb_spec) and eval_suite_for(mb_spec)["example_count"] == 2)
    mb_fail = False
    try:
        PurposeTaskSpec.from_dict({**_pt_base(), "build_mode": "model"}).with_eval_suite({"suite_id": "x", "examples": []})
    except ValueError:
        mb_fail = True
    check("F2: model-built spec REJECTS an empty inline suite (fail-closed)", mb_fail)

    # G. projection redaction — the answer key never leaks to a customer
    view = customer_projection(spec_pt)
    ec = view["spec"].get("eval_contract")
    check("G: customer view summarizes the eval_suite (id + count + threshold + judge)",
          isinstance(ec, dict) and ec.get("suite_id") == _INLINE["suite_id"]
          and ec.get("example_count") == 2 and ec.get("gate_threshold") == float(PROMOTE_AT)
          and ec.get("judge") == es.DEFAULT_JUDGE)
    check("G: customer eval_contract carries NO `examples` (the answer key stays staff-only)",
          "examples" not in ec)
    leaked = "Filed 2026-03-14." in json.dumps(view)  # an expected answer-key value
    check("G: no example `expected` value appears anywhere in the customer view", not leaked)
    check("G: customer_view_is_clean() still passes with an eval_suite present", customer_view_is_clean(view))

    print("\n" + ("PASS — check_eval_suite_contract: eval_suite is a real, schema-constrained, round-tripping "
                  "first-class field of PurposeTaskSpec + CapabilityTask; the gate threshold/holdout "
                  "policy are single-sourced from the live runtime constants; benchmark_ref fails honestly; "
                  "the runtime-gate seam (eval_suite_for/eval_pairs) is real; and the answer key never leaks "
                  "to a customer. The benchmark IS the spec."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_eval_suite_contract.py --self-test")
    raise SystemExit(0)
