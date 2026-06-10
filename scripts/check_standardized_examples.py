#!/usr/bin/env python3
"""scripts.check_standardized_examples — proof: docs/examples/standardized-patterns.md is grounded.

The standardized-patterns page is the field guide: for 10 recurring shapes it names the ONE existing
Baltor implementation as the canonical example, plus its pattern_id, standard/template (if any), and a
proof command. This proof enforces that the page never drifts into fiction:

  * the doc exists and parses into 10 example sections (## 1 .. ## 10);
  * every **Canonical example** path it cites EXISTS on disk (the no-fake rule);
  * every **proof command** it cites names a REAL scripts/check_*.py that exists on disk;
  * every **pattern_id** it cites is one of the canonical 25;
  * the cross-referenced single-source files (pattern_registry / standard_catalog / template_catalog /
    routine_library / pattern_maturity_matrix) all exist.

Deterministic + offline (reads files only; no wall-clock, no RNG, no network).

CLI: python3 scripts/check_standardized_examples.py --self-test
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_DOC = _REPO / "docs" / "examples" / "standardized-patterns.md"

#: the canonical 25 component pattern ids (single source for this lane; matches the spec exactly).
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

#: single-source files the doc points into; all must exist.
_CROSS_REF_FILES = (
    "architecture/pattern_registry.json",
    "architecture/standard_catalog.json",
    "architecture/template_catalog.json",
    "architecture/routine_library.json",
    "architecture/pattern_maturity_matrix.json",
)

#: a path-like token (e.g. scripts/foo.py, web/baltor/x.html, architecture/y.json) inside backticks.
_PATH_RE = re.compile(r"`([A-Za-z0-9_][A-Za-z0-9_./@-]+\.(?:py|html|json|md))`")
#: a proof command line: python3 scripts/check_<thing>.py --self-test
_PROOF_RE = re.compile(r"python3\s+(scripts/check_[A-Za-z0-9_]+\.py)\s+--self-test")
#: a pattern_id token (snake_case ending in _pattern) inside backticks.
_PATTERN_RE = re.compile(r"`([a-z_]+_pattern)`")
#: an "## N." numbered example section header.
_SECTION_RE = re.compile(r"^##\s+\d+\.\s", re.MULTILINE)
#: the canonical-example bullet line, so we can extract example paths specifically.
_EXAMPLE_LINE_RE = re.compile(r"\*\*Canonical example:\*\*\s+(.*)")


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    # --- doc exists + parses ---
    if not _DOC.exists():
        check("docs/examples/standardized-patterns.md exists", False, str(_DOC))
        print("\n1 FAILURES: ['doc missing']")
        return 1
    check("docs/examples/standardized-patterns.md exists", True)
    text = _DOC.read_text(encoding="utf-8")

    sections = _SECTION_RE.findall(text)
    check("doc documents exactly 10 numbered example shapes", len(sections) == 10, str(len(sections)))

    # --- every Canonical example path exists on disk (no-fake) ---
    example_paths: list[str] = []
    for line in _EXAMPLE_LINE_RE.findall(text):
        example_paths.extend(_PATH_RE.findall(line))
    check("doc names at least 10 canonical example paths", len(example_paths) >= 10, str(len(example_paths)))
    missing_examples = [p for p in example_paths if not (_REPO / p).exists()]
    check("EVERY canonical example path exists on disk (no-fake)", missing_examples == [],
          str(missing_examples))

    # --- every cited proof command names a real scripts/check_*.py ---
    proof_paths = _PROOF_RE.findall(text)
    check("doc cites at least 10 proof commands", len(proof_paths) >= 10, str(len(proof_paths)))
    missing_proofs = [p for p in proof_paths if not (_REPO / p).exists()]
    check("EVERY cited proof command names a real scripts/check_*.py", missing_proofs == [],
          str(missing_proofs))
    # each example section should carry a proof command (10 distinct example shapes -> 10 proofs)
    check("at least 10 distinct proof scripts cited", len(set(proof_paths)) >= 10,
          str(sorted(set(proof_paths))))

    # --- every cited pattern_id is canonical ---
    cited_patterns = set(_PATTERN_RE.findall(text))
    unknown_patterns = sorted(cited_patterns - CANONICAL_PATTERNS)
    check("doc cites at least 10 distinct canonical pattern ids", len(cited_patterns) >= 10,
          str(sorted(cited_patterns)))
    check("EVERY cited pattern_id is one of the canonical 25", unknown_patterns == [],
          str(unknown_patterns))

    # --- cross-referenced single-source files all exist ---
    missing_refs = [f for f in _CROSS_REF_FILES if not (_REPO / f).exists()]
    check("all cross-referenced single-source files exist", missing_refs == [], str(missing_refs))
    for f in _CROSS_REF_FILES:
        check(f"doc references single source -> {f}", f in text)

    print(f"\n{'PASS — check_standardized_examples: 10 canonical example shapes; every example path + proof + pattern_id is REAL.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: standardized-patterns.md cites only real examples + proofs.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
