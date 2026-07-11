#!/usr/bin/env python3
"""Validate the high-priority primitive opportunity rankings seed pack."""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import json
import re
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
PACK_DIR = _resource("catalog/knowledge-packs/data/high-priority-primitive-opportunity-rankings")
MANIFEST_PATH = PACK_DIR / "manifest.json"
FORBIDDEN_ID_PATTERN = re.compile(
    r"(@|(?:^|[:._-])v\d+(?:$|[:._-])|(?:^|[:._-])latest(?:$|[:._-])|20\d{2}[-_]\d{2})",
    re.IGNORECASE,
)


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"{path}: expected JSON object")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise AssertionError(f"{path}:{line_number}: invalid JSONL: {exc}") from exc
        if not isinstance(value, dict):
            raise AssertionError(f"{path}:{line_number}: expected JSON object")
        rows.append(value)
    if not rows:
        raise AssertionError(f"{path}: expected at least one row")
    return rows


def _require_candidate_boundary(row: dict[str, Any], row_id: str) -> None:
    if row.get("candidate") is not True:
        raise AssertionError(f"{row_id} must keep candidate=true")
    if row.get("serves_truth") is not False:
        raise AssertionError(f"{row_id} must keep serves_truth=false")


def _require_list(row: dict[str, Any], field: str, row_id: str, *, min_len: int = 1) -> list[Any]:
    value = row.get(field)
    if not isinstance(value, list) or len(value) < min_len:
        raise AssertionError(f"{row_id} must declare {field} with at least {min_len} item(s)")
    return value


def _check_id(value: str, row_id: str, field: str) -> None:
    if FORBIDDEN_ID_PATTERN.search(value):
        raise AssertionError(f"{row_id} field {field} must be version-free: {value!r}")


def self_test() -> dict[str, Any]:
    manifest = _read_json(MANIFEST_PATH)
    _require_candidate_boundary(manifest, "manifest")
    files = manifest.get("files")
    if not isinstance(files, dict):
        raise AssertionError("manifest must declare files")
    opportunities = _read_jsonl(PACK_DIR / str(files["primitive_opportunities"]))
    modules = _read_jsonl(PACK_DIR / str(files["module_specialties"]))
    industries = _read_jsonl(PACK_DIR / str(files["industry_priority_matrix"]))
    variants = _read_jsonl(PACK_DIR / str(files["route_variants"]))
    scoring_model = _read_json(PACK_DIR / str(files["scoring_model"]))
    _require_candidate_boundary(scoring_model, "scoring_model")

    if len(modules) != 20:
        raise AssertionError(f"expected 20 module specialties; got {len(modules)}")
    if len(industries) != 25:
        raise AssertionError(f"expected 25 industries; got {len(industries)}")
    if len(variants) != 2:
        raise AssertionError(f"expected 2 variants; got {len(variants)}")
    if len(opportunities) != 1000:
        raise AssertionError(f"expected 1000 opportunities; got {len(opportunities)}")
    if manifest.get("opportunity_count") != len(opportunities):
        raise AssertionError("manifest opportunity_count must match rows")

    module_ids = {str(row.get("module_id") or "") for row in modules}
    industry_ids = {str(row.get("industry_id") or "") for row in industries}
    variant_ids = {str(row.get("variant_id") or "") for row in variants}
    required_modules = {
        "module:entity_resolution",
        "module:entity_enrichment",
        "module:data_verification",
        "module:related_data_search",
        "module:fragile_context_monitoring",
        "module:geography_specific_search",
        "module:legal_information_search",
        "module:source_ref_resolution",
        "module:privacy_boundary_classification",
        "module:proof_receipt_generation",
    }
    if required_modules - module_ids:
        raise AssertionError(f"missing required modules: {sorted(required_modules - module_ids)}")

    for row in modules + industries + variants:
        row_id = str(row.get("module_id") or row.get("industry_id") or row.get("variant_id") or "")
        _require_candidate_boundary(row, row_id)
        _check_id(row_id, row_id, "id")
    if any(not _require_list(row, "proof_requirements", str(row["module_id"]), min_len=3) for row in modules):
        raise AssertionError("module proof requirements should be present")

    opportunity_ids: set[str] = set()
    combos: set[tuple[str, str, str]] = set()
    ranks: list[int] = []
    scores: list[float] = []
    for row in opportunities:
        row_id = str(row.get("opportunity_id") or "")
        if not row_id:
            raise AssertionError("opportunity rows must declare opportunity_id")
        _require_candidate_boundary(row, row_id)
        _check_id(row_id, row_id, "opportunity_id")
        opportunity_ids.add(row_id)
        module_id = str(row.get("module_id") or "")
        industry_id = str(row.get("industry_id") or "")
        variant_id = str(row.get("variant_id") or "")
        if module_id not in module_ids:
            raise AssertionError(f"{row_id} references unknown module {module_id!r}")
        if industry_id not in industry_ids:
            raise AssertionError(f"{row_id} references unknown industry {industry_id!r}")
        if variant_id not in variant_ids:
            raise AssertionError(f"{row_id} references unknown variant {variant_id!r}")
        combos.add((module_id, industry_id, variant_id))
        ranks.append(int(row.get("rank") or 0))
        scores.append(float(row.get("priority_score") or 0))
        if not str(row.get("input_edge") or "") or not str(row.get("output_edge") or ""):
            raise AssertionError(f"{row_id} must declare input_edge and output_edge")
        _require_list(row, "transformations", row_id, min_len=4)
        _require_list(row, "runtime_targets", row_id, min_len=3)
        _require_list(row, "source_surface_hints", row_id, min_len=3)
        _require_list(row, "proof_requirements", row_id, min_len=4)
        _require_list(row, "negative_memory_queries", row_id, min_len=3)
        if row.get("source_refs") != []:
            raise AssertionError(f"{row_id} source_refs should stay empty until verified")

    if len(opportunity_ids) != len(opportunities):
        raise AssertionError("opportunity ids must be unique")
    if len(combos) != len(modules) * len(industries) * len(variants):
        raise AssertionError("expected every module x industry x variant combination")
    if ranks != list(range(1, len(opportunities) + 1)):
        raise AssertionError("ranks must be contiguous starting at 1")
    if scores != sorted(scores, reverse=True):
        raise AssertionError("opportunities must be sorted by descending score")

    top_50_modules = {row["module_id"] for row in opportunities[:50]}
    if "module:entity_resolution" not in top_50_modules or "module:data_verification" not in top_50_modules:
        raise AssertionError("top 50 should include entity resolution and data verification")

    return {
        "opportunities": len(opportunities),
        "modules": len(modules),
        "industries": len(industries),
        "variants": len(variants),
        "candidate": True,
        "serves_truth": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true", help="run validation checks")
    args = parser.parse_args()
    if not args.self_test:
        parser.error("expected --self-test")
    print(json.dumps(self_test(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
