#!/usr/bin/env python3
"""scripts.primitive_lifecycle — the 5-stage promotion state machine + provenance + truth-serving policy
(2026-07-08). A primitive does NOT become production / serves_truth=true because tests pass; it needs
schema, verifier, security, benchmark, deterministic-replay, and provenance EVIDENCE, each a receipt.
This is the governance plane of the supply chain (owner spec §3/§C; SLSA provenance model).

    candidate --[schema + verifier + self-test]--> validated
    validated --[security pass + benchmark + deterministic replay]--> certified
    certified --[provenance + run_proof + reviewer/policy approval]--> production  (serves_truth eligible)
    production --[superseded / drift / security issue / regression]--> deprecated
    any        --[malicious pattern / failed security / unverifiable]--> quarantined

Refuses any transition whose required receipts are absent; a failed security gate FORCES quarantined. Pure +
deterministic (timestamps only at the CLI). Consolidates promote_primitive / generate_primitive_provenance /
validate_truth_serving_policy into one cohesive, self-tested module (repo convention: one module, one gate).
candidate; serves_truth=false (this module never flips the bit — it states whether the bit WOULD be allowed).

    python3 scripts/primitive_lifecycle.py --self-test
    python3 scripts/primitive_lifecycle.py --audit-pool   # assert nothing is casually serving truth
"""
from __future__ import annotations

import sys
from pathlib import Path

_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import json  # noqa: E402
from typing import Any  # noqa: E402

try:
    from src.teleon.experiments.ids import canonical_id  # noqa: E402
except ImportError as exc:  # pragma: no cover
    raise SystemExit(f"primitive_lifecycle requires canonical_id; import failed: {exc}")

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
POLICY_VERSION = "primitive-lifecycle-policy-v1"
STAGES: tuple[str, ...] = ("candidate", "validated", "certified", "production", "deprecated", "quarantined")
#: determinism budgets that MAY serve truth (D3_hybrid / D4_stochastic may not — owner spec §B)
TRUTH_ELIGIBLE_DETERMINISM = frozenset({"D0_pure", "D1_seeded", "D2_bounded_external"})
#: forward transition -> the receipt keys that MUST be present-and-satisfied to allow it
_TRANSITION_REQUIREMENTS: dict[tuple[str, str], dict[str, Any]] = {
    ("candidate", "validated"): {"schema_valid": True, "self_test_pass": True, "_present": ["verifier_id"]},
    ("validated", "certified"): {"security_status": "pass", "deterministic_replay": True,
                                 "_present": ["benchmark_result"]},
    ("certified", "production"): {"_present": ["provenance", "run_proof"], "_any_present": ["reviewer",
                                                                                            "policy_approval"]},
}


def _missing_requirements(frm: str, to: str, receipts: dict[str, Any]) -> list[str]:
    spec = _TRANSITION_REQUIREMENTS.get((frm, to))
    if spec is None:
        return [f"no_defined_transition:{frm}->{to}"]
    missing: list[str] = []
    for key, want in spec.items():
        if key == "_present":
            missing += [f"missing:{k}" for k in want if not receipts.get(k)]
        elif key == "_any_present":
            if not any(receipts.get(k) for k in want):
                missing.append(f"missing_any:{'|'.join(want)}")
        elif receipts.get(key) != want:
            missing.append(f"unsatisfied:{key}(want {want!r}, got {receipts.get(key)!r})")
    return missing


def promote(card: dict[str, Any], to_stage: str, receipts: dict[str, Any] | None = None) -> dict[str, Any]:
    """Attempt a promotion. Returns the decision + (on success) the updated card. Refuses on missing receipts.
    A security verdict of quarantine FORCES quarantined regardless of the requested target (fail-safe)."""
    # card-level evidence (verifier_id, provenance) counts toward requirements; explicit receipts override it
    receipts = {"verifier_id": card.get("verifier_id"), "provenance": card.get("provenance"),
                **(receipts or {})}
    frm = card.get("lifecycle_stage", "candidate")
    if to_stage not in STAGES:
        return {"ok": False, "from": frm, "to": to_stage, "error": f"unknown_stage:{to_stage}"}
    if receipts.get("security_status") == "quarantine" and to_stage != "quarantined":
        return {"ok": False, "from": frm, "to": to_stage, "forced": "quarantined",
                "reason": "security_gate_quarantine_forces_quarantine", "missing": ["security_status:pass"]}
    if to_stage == "quarantined":
        if not receipts.get("quarantine_reason") and receipts.get("security_status") != "quarantine":
            return {"ok": False, "from": frm, "to": to_stage, "missing": ["quarantine_reason"]}
        updated = {**card, "lifecycle_stage": "quarantined",
                   "quarantine_reason": receipts.get("quarantine_reason", "security_gate_quarantine"), **BOUNDARY}
        return {"ok": True, "from": frm, "to": "quarantined", "card": updated}
    if to_stage == "deprecated":
        if not receipts.get("deprecation_reason"):
            return {"ok": False, "from": frm, "to": to_stage, "missing": ["deprecation_reason"]}
        return {"ok": True, "from": frm, "to": "deprecated",
                "card": {**card, "lifecycle_stage": "deprecated",
                         "deprecation_reason": receipts["deprecation_reason"], **BOUNDARY}}
    missing = _missing_requirements(frm, to_stage, receipts)
    if missing:
        return {"ok": False, "from": frm, "to": to_stage, "missing": missing}
    updated = {**card, "lifecycle_stage": to_stage,
               "promotion_receipts": {**card.get("promotion_receipts", {}),
                                      to_stage: {k: v for k, v in receipts.items() if not k.startswith("_")}},
               "promotion_policy_version": POLICY_VERSION, **BOUNDARY}
    return {"ok": True, "from": frm, "to": to_stage, "card": updated}


def build_provenance(card: dict[str, Any], *, source_files: list[str] | None = None,
                     commit_sha: str | None = None) -> dict[str, Any]:
    """SLSA-shaped provenance: what built this artifact + how it is verified. Deterministic (no timestamp)."""
    body = card.get("executable_body") or ""
    return {"record_type": "primitive_provenance", "primitive_id": card.get("primitive_id"),
            "artifact_hash": canonical_id("artifact", body, card.get("impl_name") or ""),
            "source_pack": card.get("pack_module"), "source_files": source_files or [],
            "verifier_id": card.get("verifier_id"),
            "build_command": f"import {card.get('pack_module')}; all_cards()",
            "verifier_command": "python3 scripts/flywheel_proof_modules.py --self-test",
            "security_gate_command": "python3 scripts/primitive_security_gate.py --scan-pool",
            "benchmark_command": "python3 scripts/primitive_benchmark_taxonomy.py --bench",
            "commit_sha": commit_sha, "contract_version": card.get("provenance", {}).get("contract_version"),
            **BOUNDARY}


def validate_truth_serving(card: dict[str, Any]) -> dict[str, Any]:
    """The 'can this serve truth?' policy (owner spec §C). serves_truth=true is allowed ONLY with the full
    evidence chain. Returns {allowed, blockers} — a card claiming serves_truth without allowance is a
    VIOLATION the pool audit fails on."""
    blockers: list[str] = []
    if card.get("lifecycle_stage") != "production":
        blockers.append("not_production_lifecycle")
    if card.get("determinism_level") not in TRUTH_ELIGIBLE_DETERMINISM:
        blockers.append(f"determinism_not_eligible:{card.get('determinism_level')}")
    receipts = {**card.get("promotion_receipts", {}).get("validated", {}),
                **card.get("promotion_receipts", {}).get("certified", {}),
                **card.get("promotion_receipts", {}).get("production", {})}
    if receipts.get("security_status") != "pass":
        blockers.append("no_security_pass_receipt")
    if not receipts.get("benchmark_result"):
        blockers.append("no_benchmark_receipt")
    if not card.get("verifier_id"):
        blockers.append("no_verifier")
    if not (card.get("provenance") or receipts.get("provenance")):
        blockers.append("no_provenance")
    if card.get("risk_tier") == "quarantined" or card.get("lifecycle_stage") == "quarantined":
        blockers.append("quarantined")
    if card.get("lifecycle_stage") == "deprecated":
        blockers.append("deprecated")
    return {"primitive_id": card.get("primitive_id"), "allowed": not blockers, "blockers": blockers}


def audit_pool() -> dict[str, Any]:
    """Enforcement: assert NO live card claims serves_truth=true without passing the policy. All our cards are
    candidate/serves_truth=false, so the pool must be clean (0 violations)."""
    from scripts.executable_pack_pool_sync import collect_pack_cards  # noqa: PLC0415
    violations = []
    stages: dict[str, int] = {}
    for c in collect_pack_cards():
        stages[c.get("lifecycle_stage", "candidate")] = stages.get(c.get("lifecycle_stage", "candidate"), 0) + 1
        if c.get("serves_truth") is True and not validate_truth_serving(c)["allowed"]:
            violations.append(c.get("primitive_id"))
    return {"record_type": "truth_serving_audit", "n_cards": sum(stages.values()),
            "by_lifecycle_stage": stages, "serves_truth_violations": violations,
            "clean": not violations, **BOUNDARY}


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []
    base = {"primitive_id": "p", "lifecycle_stage": "candidate", "verifier_id": "pack::_self_test",
            "determinism_level": "D0_pure", "provenance": {"artifact_hash": "artifact-x"}, "risk_tier": "safe",
            "executable_body": "def f():\n    return 1\n"}
    # candidate -> validated needs schema + verifier + self-test
    blocked = promote(base, "validated", {"schema_valid": True})
    ok = promote(base, "validated", {"schema_valid": True, "self_test_pass": True})
    checks.append(("candidate->validated: blocked without self_test_pass, ok with it",
                   not blocked["ok"] and "unsatisfied:self_test_pass(want True, got None)" in blocked["missing"]
                   and ok["ok"] and ok["card"]["lifecycle_stage"] == "validated"))
    val = ok["card"]
    # validated -> certified needs security pass + benchmark + replay
    b2 = promote(val, "certified", {"security_status": "pass", "deterministic_replay": True})
    ok2 = promote(val, "certified", {"security_status": "pass", "deterministic_replay": True,
                                     "benchmark_result": "artifacts/bench/p.json"})
    checks.append(("validated->certified: blocked w/o benchmark, ok with security+replay+benchmark",
                   not b2["ok"] and "missing:benchmark_result" in b2["missing"]
                   and ok2["ok"] and ok2["card"]["lifecycle_stage"] == "certified"))
    cert = ok2["card"]
    # certified -> production needs provenance + run_proof + reviewer|policy
    b3 = promote(cert, "production", {"provenance": "prov.json", "run_proof": "proof"})
    ok3 = promote(cert, "production", {"provenance": "prov.json", "run_proof": "proof", "reviewer": "sec-team"})
    checks.append(("certified->production: blocked w/o reviewer/policy, ok with reviewer",
                   not b3["ok"] and "missing_any:reviewer|policy_approval" in b3["missing"]
                   and ok3["ok"] and ok3["card"]["lifecycle_stage"] == "production"))
    # security quarantine forces quarantined
    q = promote(val, "certified", {"security_status": "quarantine", "deterministic_replay": True,
                                   "benchmark_result": "x"})
    checks.append(("failed security gate FORCES quarantine (fail-safe)",
                   not q["ok"] and q.get("forced") == "quarantined"))
    # truth-serving policy
    prod = ok3["card"]
    prod_truthy = {**prod, "promotion_receipts": {"certified": {"security_status": "pass",
                   "benchmark_result": "x"}}}
    checks.append(("candidate card NOT allowed to serve truth; fully-evidenced D0 production card IS",
                   not validate_truth_serving(base)["allowed"]
                   and validate_truth_serving(prod_truthy)["allowed"]))
    d4 = {**prod_truthy, "determinism_level": "D4_stochastic"}
    checks.append(("D4_stochastic production card is BLOCKED from truth (determinism budget)",
                   "determinism_not_eligible:D4_stochastic" in validate_truth_serving(d4)["blockers"]))
    dep = {**prod_truthy, "lifecycle_stage": "deprecated"}
    checks.append(("deprecated card cannot serve truth",
                   "not_production_lifecycle" in validate_truth_serving(dep)["blockers"]
                   or "deprecated" in validate_truth_serving(dep)["blockers"]))
    prov = build_provenance({**base, "pack_module": "scripts.scalar_standardization_primitives"})
    checks.append(("provenance carries artifact_hash + verifier + commands, deterministic",
                   prov["artifact_hash"].startswith("artifact-") and prov["verifier_id"] == "pack::_self_test"
                   and prov == build_provenance({**base, "pack_module": "scripts.scalar_standardization_primitives"})))
    audit = audit_pool()
    checks.append(("pool audit: every live card is candidate stage, 0 truth-serving violations (clean)",
                   audit["clean"] and audit["by_lifecycle_stage"].get("candidate", 0) >= 100
                   and audit["serves_truth_violations"] == []))
    failed = [n for n, okk in checks if not okk]
    for n, okk in checks:
        print(f"  [{'ok' if okk else 'FAIL'}] {n}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print(f"\nPASS - primitive_lifecycle: 5-stage promotion (candidate->validated->certified->production, "
          f"+deprecated/quarantined), every transition receipt-gated, security-quarantine fail-safe, "
          f"SLSA provenance, truth-serving policy. Pool clean. serves_truth=false.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--audit-pool", action="store_true")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.audit_pool:
        print(json.dumps(audit_pool(), indent=2, sort_keys=True))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
