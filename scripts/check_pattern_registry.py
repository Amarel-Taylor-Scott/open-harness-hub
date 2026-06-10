#!/usr/bin/env python3
"""scripts.check_pattern_registry — proof: the pattern registry holds its contract.

Asserts architecture/pattern_registry.json parses; all 25 canonical pattern ids are present exactly
once; every pattern carries the required keys; every detected_examples path EXISTS on disk (this is the
no-fake enforcement — a fabricated example fails the proof); maturity is in the enum; and the compact
pattern_maturity_matrix.json agrees with the registry (no drift between the two single sources).

CLI: python3 scripts/check_pattern_registry.py --self-test
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_REGISTRY = _REPO / "architecture" / "pattern_registry.json"
_MATRIX = _REPO / "architecture" / "pattern_maturity_matrix.json"

# The canonical 25 pattern ids (single source for this proof; must match the lane spec exactly).
CANONICAL_IDS = (
    "source_adapter_pattern", "parser_provider_pattern", "ingestion_sync_pattern", "source_artifact_pattern",
    "durable_command_pattern", "worker_claim_loop_pattern", "processor_harness_pattern",
    "artifact_envelope_pattern", "provider_adapter_pattern", "api_projection_route_pattern",
    "ui_projection_page_pattern", "proof_script_pattern", "documentation_page_pattern",
    "contract_schema_pattern", "capability_catalog_entry_pattern", "optimization_candidate_pattern",
    "reconciliation_decision_pattern", "held_out_warning_pattern", "watchtower_verification_task_pattern",
    "tenant_isolation_pattern", "structured_logging_pattern", "review_pack_pattern",
    "section_maturity_entry_pattern", "dependency_emulator_pattern", "multi_source_fixture_pattern",
)

REQUIRED_KEYS = (
    "pattern_id", "category", "name", "description", "detected_examples", "owner_folder",
    "required_contracts", "required_ports", "required_adapters", "required_registries",
    "required_proofs", "required_docs", "template_ids", "anti_patterns", "maturity",
    "waiver_allowed", "done_when",
)

VALID_MATURITY = {"candidate", "standard", "enforced", "deprecated"}


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    # --- parse ---
    try:
        reg = json.loads(_REGISTRY.read_text(encoding="utf-8"))
        check("pattern_registry.json parses", True)
    except (OSError, json.JSONDecodeError) as e:
        check("pattern_registry.json parses", False, str(e))
        print(f"\n1 FAILURES: ['parse']")
        return 1

    check("registry has maturity_enum matching the contract",
          set(reg.get("maturity_enum", [])) == VALID_MATURITY, str(reg.get("maturity_enum")))

    patterns = reg.get("patterns", [])
    ids = [p.get("pattern_id") for p in patterns]
    check("all 25 canonical pattern ids present", set(CANONICAL_IDS) <= set(ids),
          str(sorted(set(CANONICAL_IDS) - set(ids))))
    check("no unexpected pattern ids", set(ids) <= set(CANONICAL_IDS),
          str(sorted(set(ids) - set(CANONICAL_IDS))))
    check("no duplicate pattern ids", len(ids) == len(set(ids)),
          str([i for i in ids if ids.count(i) > 1]))

    # --- per-pattern required keys + maturity enum ---
    missing_keys, bad_maturity = [], []
    for p in patterns:
        pid = p.get("pattern_id", "?")
        for k in REQUIRED_KEYS:
            if k not in p:
                missing_keys.append(f"{pid}:{k}")
        if p.get("maturity") not in VALID_MATURITY:
            bad_maturity.append(f"{pid}={p.get('maturity')}")
    check("every pattern has all required keys", missing_keys == [], str(missing_keys[:8]))
    check("every maturity ∈ candidate|standard|enforced|deprecated", bad_maturity == [], str(bad_maturity))

    # --- NO-FAKE: every detected_examples path EXISTS on disk ---
    missing_paths, empty_examples = [], []
    for p in patterns:
        ex = p.get("detected_examples", [])
        if not ex:
            empty_examples.append(p.get("pattern_id"))
        for path in ex:
            if not (_REPO / path).exists():
                missing_paths.append(f"{p.get('pattern_id')}:{path}")
    check("every pattern has at least one detected example", empty_examples == [], str(empty_examples))
    check("EVERY detected_examples path exists on disk (no-fake)", missing_paths == [], str(missing_paths[:8]))

    # --- honesty: a 'standard'/'enforced' pattern has at least one real example AND a real proof ---
    bad_grade = []
    for p in patterns:
        if p.get("maturity") in ("standard", "enforced"):
            has_example = any((_REPO / e).exists() for e in p.get("detected_examples", []))
            has_real_proof = any((_REPO / pr.split("#")[0]).exists() for pr in p.get("required_proofs", []))
            if not (has_example and has_real_proof):
                bad_grade.append(f"{p.get('pattern_id')} (example={has_example}, proof={has_real_proof})")
    check("every standard/enforced pattern has a real example + a real proof file", bad_grade == [], str(bad_grade))

    # --- matrix agrees with registry (no drift between the two single sources) ---
    try:
        matrix = json.loads(_MATRIX.read_text(encoding="utf-8"))
        mids = set(matrix.get("patterns", {}).keys())
        check("maturity matrix covers exactly the 25 ids", mids == set(CANONICAL_IDS),
              str(sorted(mids ^ set(CANONICAL_IDS))))
        drift = []
        for p in patterns:
            pid = p["pattern_id"]
            mrow = matrix["patterns"].get(pid, {})
            if mrow.get("maturity") != p.get("maturity"):
                drift.append(f"{pid}: registry={p.get('maturity')} matrix={mrow.get('maturity')}")
            if mrow.get("examples_count") != len(p.get("detected_examples", [])):
                drift.append(f"{pid}: examples_count drift")
        check("matrix maturity + examples_count match the registry (no drift)", drift == [], str(drift[:6]))
    except (OSError, json.JSONDecodeError) as e:
        check("pattern_maturity_matrix.json parses", False, str(e))

    print(f"\n{'PASS — check_pattern_registry: 25 canonical patterns present + keyed; every detected example exists (no-fake); maturity honest; matrix in sync.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: pattern registry contract.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
