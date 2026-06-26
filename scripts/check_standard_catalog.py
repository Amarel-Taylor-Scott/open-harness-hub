#!/usr/bin/env python3
"""scripts.check_standard_catalog — proof: architecture/standard_catalog.json is well-formed + grounded.

Asserts: it parses; every standard.status is in status_enum; every standard.pattern_id is one of the canonical
25 pattern ids; every standard's `examples` paths EXIST in this repo (no fabricated paths); every template_id
a standard references exists in template_catalog.json; required structural keys are present; and the 17
required standard_ids from the lane spec are all defined. Deterministic + offline.

CLI: python3 scripts/check_standard_catalog.py --self-test
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_STD = _REPO / "architecture" / "standard_catalog.json"
_TMPL = _REPO / "architecture" / "template_catalog.json"

#: the canonical 25 component pattern ids (single source for the whole lane).
CANONICAL_PATTERNS = {
    "source_adapter_pattern", "parser_provider_pattern", "ingestion_sync_pattern", "source_artifact_pattern",
    "durable_command_pattern", "worker_claim_loop_pattern", "processor_harness_pattern",
    "artifact_envelope_pattern", "provider_adapter_pattern", "api_projection_route_pattern",
    "ui_projection_page_pattern", "proof_script_pattern", "documentation_page_pattern",
    "contract_schema_pattern", "capability_catalog_entry_pattern", "optimization_candidate_pattern",
    "reconciliation_decision_pattern", "held_out_warning_pattern", "watchtower_verification_task_pattern",
    "tenant_isolation_pattern", "structured_logging_pattern", "review_pack_pattern",
    "section_maturity_entry_pattern", "dependency_emulator_pattern", "multi_source_fixture_pattern",
}

#: the standard_ids the lane spec requires to be authored.
REQUIRED_STANDARD_IDS = {
    "standard.source_adapter", "standard.ingestion_sync", "standard.durable_command",
    "standard.worker_claim_loop", "standard.processor", "standard.provider_adapter",
    "standard.api_projection", "standard.ui_projection", "standard.proof_script",
    "standard.docs_page", "standard.contract_schema", "standard.artifact_object",
    "standard.optimization_candidate", "standard.reconciliation_decision", "standard.watchtower_task",
    "standard.tenant_isolation", "standard.review_pack",
}

_REQUIRED_KEYS = {
    "standard_id", "pattern_id", "title", "status", "applies_to", "must_have", "must_not_have",
    "naming_rules", "file_location_rules", "contract_rules", "proof_rules", "doc_rules", "registry_rules",
    "security_rules", "observability_rules", "examples", "template_ids", "enforcement_proofs",
}


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    cat = json.loads(_STD.read_text())
    check("standard_catalog parses + has standards", bool(cat.get("standards")))
    status_enum = set(cat.get("status_enum", []))
    check("status_enum present", bool(status_enum), str(status_enum))

    tmpl = json.loads(_TMPL.read_text())
    tmpl_ids = {t["template_id"] for t in tmpl.get("templates", [])}

    seen_std_ids: set[str] = set()
    for s in cat.get("standards", []):
        sid = s.get("standard_id", "<?>")
        seen_std_ids.add(sid)
        missing_keys = _REQUIRED_KEYS - set(s)
        check(f"{sid}: has all required keys", not missing_keys, str(sorted(missing_keys)))
        check(f"{sid}: status in enum", s.get("status") in status_enum, s.get("status"))
        check(f"{sid}: pattern_id is one of the canonical 25", s.get("pattern_id") in CANONICAL_PATTERNS,
              s.get("pattern_id"))
        # examples must be REAL repo paths (no fabricated paths)
        for ex in s.get("examples", []):
            check(f"{sid}: example path exists -> {ex}", (_REPO / ex).exists())
        # referenced template_ids must exist in the template catalog
        for tid in s.get("template_ids", []):
            check(f"{sid}: template_id {tid} exists in template_catalog", tid in tmpl_ids)

    missing_required = REQUIRED_STANDARD_IDS - seen_std_ids
    check("all required standard_ids are defined", not missing_required, str(sorted(missing_required)))

    print(f"{'PASS' if not fails else 'FAIL'} check_standard_catalog ({len(fails)} failing)")
    return 0 if not fails else 1


def _main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Proof: standard_catalog.json is well-formed + grounded.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
