#!/usr/bin/env python3
"""scripts.check_routine_library — proof: _repos/shared-backend-components/architecture/routine_library.json is well-formed. Every routine
carries the required keys, every routine's pattern_id is one of the canonical 25 patterns, every routine's
category is a declared category, and every NON-EMPTY example/proof path points at a file that actually
exists in this repo (a routine library that names files that no longer exist is a stale claim). Empty
example lists are allowed only when the routine carries a 'note' explaining it is declared-but-not-yet-built.

CLI: python3 _repos/shared-backend-components/scripts/check_routine_library.py --self-test
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
_LIB = _resource("architecture") / "routine_library.json"

#: the canonical 25 pattern ids — the single shared vocabulary used across the standards lane.
CANONICAL_PATTERN_IDS = {
    "source_adapter_pattern", "parser_provider_pattern", "ingestion_sync_pattern", "source_artifact_pattern",
    "durable_command_pattern", "worker_claim_loop_pattern", "processor_harness_pattern",
    "artifact_envelope_pattern", "provider_adapter_pattern", "api_projection_route_pattern",
    "ui_projection_page_pattern", "proof_script_pattern", "documentation_page_pattern",
    "contract_schema_pattern", "capability_catalog_entry_pattern", "optimization_candidate_pattern",
    "reconciliation_decision_pattern", "held_out_warning_pattern", "watchtower_verification_task_pattern",
    "tenant_isolation_pattern", "structured_logging_pattern", "review_pack_pattern",
    "section_maturity_entry_pattern", "dependency_emulator_pattern", "multi_source_fixture_pattern",
}
_REQUIRED_KEYS = ("routine_id", "pattern_id", "template_id", "inputs", "outputs", "commands", "proofs",
                  "anti_patterns", "examples")


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    data = json.loads(_LIB.read_text(encoding="utf-8"))
    check("routine_library.json parses + has version/categories/routines",
          all(k in data for k in ("version", "categories", "routines")))

    routines = data.get("routines", [])
    check("at least one routine declared", len(routines) > 0, str(len(routines)))

    declared_categories = set(data.get("categories", []))

    missing_keys, bad_pattern, bad_category, missing_paths, dup_ids = [], [], [], [], []
    empty_examples_no_note = []
    seen_ids: set[str] = set()
    for r in routines:
        rid = r.get("routine_id", "<no-id>")
        miss = [k for k in _REQUIRED_KEYS if k not in r]
        if miss:
            missing_keys.append(f"{rid}:{miss}")
        if rid in seen_ids:
            dup_ids.append(rid)
        seen_ids.add(rid)
        if r.get("pattern_id") not in CANONICAL_PATTERN_IDS:
            bad_pattern.append(f"{rid}:{r.get('pattern_id')}")
        if r.get("category") not in declared_categories:
            bad_category.append(f"{rid}:{r.get('category')}")
        for p in r.get("proofs", []) + r.get("examples", []):
            if p and not (_resource(p)).exists():
                missing_paths.append(f"{rid}:{p}")
        if not r.get("examples") and not r.get("note"):
            empty_examples_no_note.append(rid)

    check("every routine has all required keys", missing_keys == [], str(missing_keys[:8]))
    check("no duplicate routine_id", dup_ids == [], str(dup_ids))
    check("every routine's pattern_id is one of the canonical 25", bad_pattern == [], str(bad_pattern[:8]))
    check("every routine's category is declared in categories[]", bad_category == [], str(bad_category[:8]))
    check("every non-empty example/proof path exists in the repo", missing_paths == [], str(missing_paths[:8]))
    check("empty-examples routines carry a 'note' explaining declared-but-not-built",
          empty_examples_no_note == [], str(empty_examples_no_note))

    print(f"\n{'PASS — check_routine_library: routine library is well-formed; every routine names a canonical pattern, a declared category, and only files that exist. Stale routine claims fail.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: routine library is well-formed and references only real files.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
