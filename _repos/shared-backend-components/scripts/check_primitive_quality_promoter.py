#!/usr/bin/env python3
"""Proof: primitive quality promoter separates real reusable candidates from noisy symbols."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path


REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts import primitive_quality_promoter
from scripts._config import (
    PRIMITIVE_QUALITY_ARTIFACT_FILES,
    PRIMITIVE_QUALITY_CLASS_NEEDS_CONTRACT,
    PRIMITIVE_QUALITY_CLASS_NOISE,
    PRIMITIVE_QUALITY_CLASS_SURFACEABLE,
    PRIMITIVE_QUALITY_DIRNAME,
)


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    check("promoter fixture self-test passes", primitive_quality_promoter.self_test() == 0)

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        records_dir = root / ".agent" / "primitive-registry"
        operational_dir = records_dir / "operational"
        code_dir = root / "src"
        code_dir.mkdir(parents=True)
        (code_dir / "utils.py").write_text(
            '"""Utility functions for common import workflows."""\n\n'
            "def parse_csv(inputs: dict) -> dict:\n"
            "    \"\"\"Parse CSV text into deterministic row records.\"\"\"\n"
            "    text = inputs.get('text', '')\n"
            "    delimiter = inputs.get('delimiter', ',')\n"
            "    return {'rows': text.splitlines(), 'delimiter': delimiter}\n\n"
            "def test_parse_csv():\n"
            "    assert parse_csv({'text': 'a'})['rows'] == ['a']\n",
            encoding="utf-8",
        )
        records = [
            {
                "id": "primitive.repo.src_utils_py.function.parse_csv",
                "name": "parse_csv",
                "purpose": "Candidate primitive generated from real repo symbol `parse_csv`.",
                "input_contract": {"shape": "callable_signature_candidate", "parameters": [{"name": "inputs"}]},
                "output_contract": {"shape": "unknown_candidate"},
                "license_provenance": {
                    "generated_from_real_artifact": True,
                    "license": "MIT",
                    "line": 3,
                    "path": "src/utils.py",
                    "symbol_kind": "function",
                    "symbol_name": "parse_csv",
                    "synthetic": False,
                },
                "execution_surface": "python_callable_candidate",
                "candidate": True,
                "serves_truth": False,
            },
            {
                "id": "primitive.repo.src_utils_py.function.test_parse_csv",
                "name": "test_parse_csv",
                "purpose": "Candidate primitive generated from real repo symbol `test_parse_csv`.",
                "input_contract": {"shape": "callable_signature_candidate"},
                "output_contract": {"shape": "unknown_candidate"},
                "license_provenance": {
                    "generated_from_real_artifact": True,
                    "license": "MIT",
                    "line": 8,
                    "path": "src/utils.py",
                    "symbol_kind": "function",
                    "symbol_name": "test_parse_csv",
                    "synthetic": False,
                },
                "execution_surface": "python_callable_candidate",
                "candidate": True,
                "serves_truth": False,
            },
            {
                "id": "primitive.repo.src_utils_py.const.MAX_ROWS",
                "name": "MAX_ROWS",
                "purpose": "Candidate primitive generated from real repo symbol `MAX_ROWS`.",
                "input_contract": {"shape": "source_symbol_candidate"},
                "output_contract": {"shape": "python_value_candidate"},
                "license_provenance": {
                    "generated_from_real_artifact": True,
                    "license": "MIT",
                    "line": 1,
                    "path": "src/utils.py",
                    "symbol_kind": "const",
                    "symbol_name": "MAX_ROWS",
                    "synthetic": False,
                },
                "execution_surface": "python_source_symbol_candidate",
                "candidate": True,
                "serves_truth": False,
            },
        ]
        operational_dir.mkdir(parents=True)
        primitive_quality_promoter.write_jsonl(records_dir / "primitive_candidate_records.jsonl", records)
        primitive_quality_promoter.write_jsonl(operational_dir / "registry_records.jsonl", [
            {
                "registry_record_id": record["id"],
                "readiness_level": "R3_contract_known",
                "trust_status": "candidate",
                "title": record["name"],
                "blackbox_description": record["purpose"],
            }
            for record in records
        ])
        primitive_quality_promoter.write_jsonl(operational_dir / "primitive_edges.jsonl", [])
        primitive_quality_promoter.write_jsonl(operational_dir / "primitive_mutation_options.jsonl", [])
        primitive_quality_promoter.write_jsonl(operational_dir / "primitive_effects.jsonl", [
            {"registry_record_id": record["id"], "effect_kind": "pure"}
            for record in records
        ])

        old_repo = primitive_quality_promoter.REPO
        primitive_quality_promoter.REPO = root
        try:
            manifest = primitive_quality_promoter.build(records_dir, write=True)
        finally:
            primitive_quality_promoter.REPO = old_repo

        quality_dir = records_dir / PRIMITIVE_QUALITY_DIRNAME
        assessments = load_jsonl(quality_dir / PRIMITIVE_QUALITY_ARTIFACT_FILES["assessments"])
        surfaceable = load_jsonl(quality_dir / PRIMITIVE_QUALITY_ARTIFACT_FILES["surfaceable"])
        class_by_id = {row["registry_record_id"]: row["quality_class"] for row in assessments}
        check("fixture emits all required quality artifacts", all((quality_dir / filename).exists() for filename in PRIMITIVE_QUALITY_ARTIFACT_FILES.values()))
        check("parse_csv becomes surfaceable", class_by_id.get("primitive.repo.src_utils_py.function.parse_csv") == PRIMITIVE_QUALITY_CLASS_SURFACEABLE)
        check("test helper is hidden as noise", class_by_id.get("primitive.repo.src_utils_py.function.test_parse_csv") == PRIMITIVE_QUALITY_CLASS_NOISE)
        check("constant does not become a default surfaceable primitive", class_by_id.get("primitive.repo.src_utils_py.const.MAX_ROWS") in {PRIMITIVE_QUALITY_CLASS_NOISE, PRIMITIVE_QUALITY_CLASS_NEEDS_CONTRACT})
        check("surfaceable cards never serve truth", surfaceable and all(row["serves_truth"] is False and row["candidate"] is True for row in surfaceable))
        check("manifest counts match artifacts", manifest["assessments"] == len(assessments) and manifest["aidevobserver_surfaceable_primitives"] == len(surfaceable))

    if failures:
        print(f"\nFAIL - check_primitive_quality_promoter: {len(failures)} failure(s)")
        return 1
    print("\nPASS - check_primitive_quality_promoter: quality promoter gates surfaceable primitive candidates")
    return 0


if __name__ == "__main__":
    raise SystemExit(self_test())
