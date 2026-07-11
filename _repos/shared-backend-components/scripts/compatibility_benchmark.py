"""compatibility_benchmark — a labeled, ADVERSARIAL held-out set that scores the compatibility system (review §6.1).

The external review's methodology point: raw similarity accuracy is the wrong metric. A compatibility system
should retrieve many plausible neighbors, PROVE a narrow safe subset, explicitly bridge another, and ABSTAIN on
the rest — and it must never AUTO-AUTHORIZE an unsafe join. This benchmark makes that measurable with the
adversarial cases the review enumerates (same name/different unit, same shape/different type, different
names/equivalent, optional vs required, semantically-related-not-executable, input-contract vs payload, …).

The load-bearing result it proves: **name equality alone is unsafe** — the name-only lattice AUTO-AUTHORIZES a
same-name/different-unit pair (a false authorize), while the CONTRACT-AWARE classifier (structural width
subtyping when contracts are present, the graded lattice otherwise) has ZERO false auto-authorizes on the whole
adversarial set. That is exactly the review's thesis — names retrieve, contracts authorize — as a number.

    PYTHONPATH=. python3 scripts/compatibility_benchmark.py --self-test
    PYTHONPATH=. python3 scripts/compatibility_benchmark.py --run
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Optional

_HERE = Path(__file__).resolve()
_SBC = _HERE.parent.parent
_ROOT = _SBC.parent.parent
for _p in (str(_SBC), str(_SBC / "scripts"), str(_ROOT), str(_ROOT / "_repos" / "teleon" / "backend")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

#: the labeled adversarial held-out set. `authorize` = should a deterministic composer be allowed to auto-chain
#: this producer->consumer join? Contracts (when present) are field maps {name: {type, unit?, required?}}.
_ALIGNMENTS = {"OfficerDirectorRowBatch": "OfficerRowBatch", "NonprofitOfficerRowBatch": "OfficerRowBatch"}
BENCHMARK: list[dict[str, Any]] = [
    {"id": "direct_identical", "producer": "OfficerRowBatch", "consumer": "OfficerRowBatch",
     "label": "direct_compatible", "authorize": True},
    {"id": "curated_alignment", "producer": "OfficerDirectorRowBatch", "consumer": "OfficerRowBatch",
     "label": "family_compatible", "authorize": True},
    {"id": "semantic_not_executable", "producer": "VendorOfficerRowBatch", "consumer": "OfficerRowBatch",
     "label": "semantically_related_not_executable", "authorize": False},   # token-similar, no alignment
    {"id": "input_contract_to_payload", "producer": "StateStatusNormalizeRequest", "consumer": "SourceEntityRecordBatch",
     "label": "incompatible", "authorize": False},
    {"id": "unknown_role", "producer": "weird_lowercase", "consumer": "OfficerRowBatch",
     "label": "unknown", "authorize": False},
    # ── contract-level adversarial cases (the traps a NAME cannot catch) ──
    {"id": "width_subtype", "label": "direct_compatible", "authorize": True,
     "producer_contract": {"fields": {"name": {"type": "str"}, "age": {"type": "int"}, "extra": {"type": "str"}}},
     "consumer_contract": {"fields": {"name": {"type": "str", "required": True}, "age": {"type": "int", "required": True}}}},
    {"id": "missing_required", "label": "incompatible", "authorize": False,
     "producer_contract": {"fields": {"name": {"type": "str"}}},
     "consumer_contract": {"fields": {"name": {"type": "str", "required": True}, "age": {"type": "int", "required": True}}}},
    {"id": "same_shape_wrong_type", "label": "incompatible", "authorize": False,
     "producer_contract": {"fields": {"x": {"type": "float"}}},
     "consumer_contract": {"fields": {"x": {"type": "int", "required": True}}}},
    # THE KILLER: identical edge NAME, but the contracts differ in UNIT. Name says IDENTICAL (would authorize);
    # the contract says INCOMPATIBLE. This is why names must never authorize.
    {"id": "same_name_different_unit", "producer": "DistanceBatch", "consumer": "DistanceBatch",
     "label": "incompatible", "authorize": False,
     "producer_contract": {"fields": {"d": {"type": "float", "unit": "miles"}}},
     "consumer_contract": {"fields": {"d": {"type": "float", "unit": "km", "required": True}}}},
    {"id": "optional_vs_required", "label": "direct_compatible", "authorize": True,
     "producer_contract": {"fields": {"name": {"type": "str"}}},
     "consumer_contract": {"fields": {"name": {"type": "str", "required": True}, "nickname": {"type": "str", "required": False}}}},
]


def _name_only_authorizes(pair: dict[str, Any]) -> bool:
    """The NAIVE classifier: edge-name lattice only (ignores contracts). Used to prove names are unsafe alone."""
    from scripts.compatibility_lattice import classify_compatibility  # noqa: PLC0415
    if not pair.get("producer") or not pair.get("consumer"):
        # no edge names -> the name-only lattice can't judge; treat identical-shape as its (wrong) 'authorize'.
        return True if pair.get("producer_contract") == pair.get("consumer_contract") else False
    verdict = classify_compatibility(pair["producer"], pair["consumer"], alignments=_ALIGNMENTS)
    return verdict["authorizes_execution"]


def _contract_aware_authorizes(pair: dict[str, Any]) -> bool:
    """The SOUND classifier: structural width subtyping when contracts are present (contracts WIN over names),
    else the graded edge-name lattice."""
    if pair.get("producer_contract") is not None and pair.get("consumer_contract") is not None:
        from scripts.edge_contract_and_adapters import structural_compatible  # noqa: PLC0415
        return structural_compatible(pair["producer_contract"], pair["consumer_contract"])["compatible"]
    from scripts.compatibility_lattice import classify_compatibility  # noqa: PLC0415
    return classify_compatibility(pair["producer"], pair["consumer"], alignments=_ALIGNMENTS)["authorizes_execution"]


def run_benchmark() -> dict[str, Any]:
    rows = []
    name_false, contract_false = 0, 0
    contract_tp = contract_tn = contract_fp = contract_fn = 0
    for pair in BENCHMARK:
        expected = pair["authorize"]
        name_auth = _name_only_authorizes(pair)
        contract_auth = _contract_aware_authorizes(pair)
        if name_auth and not expected:
            name_false += 1
        if contract_auth and not expected:
            contract_false += 1
        # confusion for the contract-aware classifier (positive = "authorize")
        if contract_auth and expected:
            contract_tp += 1
        elif not contract_auth and not expected:
            contract_tn += 1
        elif contract_auth and not expected:
            contract_fp += 1
        else:
            contract_fn += 1
        rows.append({"id": pair["id"], "label": pair["label"], "expected_authorize": expected,
                     "name_only_authorize": name_auth, "contract_aware_authorize": contract_auth})
    n = len(BENCHMARK)
    precision = contract_tp / max(1, contract_tp + contract_fp)
    recall = contract_tp / max(1, contract_tp + contract_fn)
    return {"record_type": "compatibility_benchmark_result", "n_cases": n,
            "name_only_false_authorizes": name_false, "contract_aware_false_authorizes": contract_false,
            "contract_aware_precision": round(precision, 4), "contract_aware_recall": round(recall, 4),
            "rows": rows,
            "note": "false_authorizes = auto-authorized an unsafe join. The contract-aware classifier must be 0 "
                    "(the safety invariant); the name-only classifier is >0, proving names cannot authorize.",
            "candidate": True, "serves_truth": False}


def _self_test() -> int:
    checks: list[tuple[str, bool, str]] = []
    result = run_benchmark()

    # (1) THE SAFETY INVARIANT: the contract-aware classifier NEVER auto-authorizes an unsafe join on the whole
    #     adversarial set (0 false authorizes).
    checks.append(("SAFETY INVARIANT: the contract-aware classifier has ZERO false auto-authorizes across the "
                   "adversarial set (never authorizes an incompatible/semantic/unit-mismatch join)",
                   result["contract_aware_false_authorizes"] == 0, str(result["contract_aware_false_authorizes"])))

    # (2) THE REVIEW'S THESIS, MEASURED: the NAME-ONLY classifier DOES make a false auto-authorize (the
    #     same-name/different-unit case), proving names cannot authorize execution.
    checks.append(("names cannot authorize: the name-only classifier makes >=1 false auto-authorize (the "
                   "same-name/different-unit trap) that the contract-aware one catches",
                   result["name_only_false_authorizes"] >= 1
                   and result["name_only_false_authorizes"] > result["contract_aware_false_authorizes"],
                   f"name_only={result['name_only_false_authorizes']}"))

    # (3) the same-name/different-unit case specifically: name authorizes, contract refuses.
    unit_row = next(r for r in result["rows"] if r["id"] == "same_name_different_unit")
    checks.append(("the same-name/different-unit case: name-only AUTHORIZES (wrong), contract-aware REFUSES",
                   unit_row["name_only_authorize"] is True and unit_row["contract_aware_authorize"] is False, ""))

    # (4) the semantically-related-not-executable case ABSTAINS (not authorized) — retrieval, not authorization.
    sem_row = next(r for r in result["rows"] if r["id"] == "semantic_not_executable")
    checks.append(("semantically-related-not-executable ABSTAINS (contract-aware does not authorize) — "
                   "retrieval candidate, not an execution authorization",
                   sem_row["contract_aware_authorize"] is False, ""))

    # (5) the genuinely-compatible cases (identical, curated alignment, width subtype, optional-vs-required) ARE
    #     authorized — the system is not merely conservative; it admits the safe subset.
    good = [r for r in result["rows"] if r["expected_authorize"]]
    checks.append(("the safe subset IS admitted: every genuinely-compatible case is authorized (recall) — not "
                   "merely conservative refusal",
                   all(r["contract_aware_authorize"] for r in good) and result["contract_aware_recall"] == 1.0,
                   f"recall={result['contract_aware_recall']}"))

    # (6) precision is perfect on this set (no false authorize) + determinism.
    checks.append(("contract-aware precision == 1.0 on the adversarial set; deterministic re-run",
                   result["contract_aware_precision"] == 1.0
                   and run_benchmark()["rows"] == result["rows"], ""))

    ok = all(passed for _n, passed, _d in checks)
    print(f"{'PASS' if ok else 'FAIL'} - compatibility_benchmark: a labeled ADVERSARIAL held-out set (review "
          f"§6.1) scoring the compatibility system — the contract-aware classifier has {result['contract_aware_false_authorizes']} "
          f"false auto-authorizes (the safety invariant) vs the name-only classifier's "
          f"{result['name_only_false_authorizes']} (proving names retrieve but cannot authorize); recall "
          f"{result['contract_aware_recall']} on the safe subset. serves_truth=false")
    for name, passed, detail in checks:
        print(f"  [{'ok' if passed else 'XX'}] {name}" + (f"  ({detail[:200]})" if not passed else ""))
    return 0 if ok else 1


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Adversarial held-out compatibility benchmark.")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.run:
        result = run_benchmark()
        print(json.dumps({k: result[k] for k in ("n_cases", "name_only_false_authorizes",
                                                 "contract_aware_false_authorizes", "contract_aware_precision",
                                                 "contract_aware_recall")}, indent=2, sort_keys=True))
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
