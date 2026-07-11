from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from scripts.factory.use_case_seed_rows import export_seed_rows


DEFAULT_REQUIRED_STAGES = [
    "source_governance",
    "entity_linking",
    "fuzzy_dedupe",
    "index_record_emission",
    "review_ticket_routing",
]


def _read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            value = json.loads(line)
            if isinstance(value, dict):
                rows.append(value)
    return rows


def _primitive_title(value: str) -> str:
    return value.replace("_", " ").replace("-", " ").strip().title()


def source_surface_to_use_case_seeds(surface: dict[str, Any]) -> list[dict[str, Any]]:
    primitives = surface.get("candidate_primitives", []) or ["candidate_primitive"]
    vertical = str(surface.get("vertical") or surface.get("domain") or "cross_domain")
    label_paths = list(surface.get("label_paths", []) or [])
    if vertical:
        label_paths.append(f"vertical.{vertical}")
    seeds = []
    for primitive in primitives:
        primitive_name = str(primitive)
        seed_id = f"{surface.get('id', 'source-surface')}-{primitive_name}".replace("_", "-")
        seeds.append(
            {
                "id": seed_id,
                "type": "use_case_seed",
                "title": f"{_primitive_title(primitive_name)} for {surface.get('title', vertical)}",
                "domain": vertical.replace(".", "_"),
                "task": " ".join(
                    str(item)
                    for item in [
                        surface.get("capability_gap_reason", ""),
                        f"Build primitive {primitive_name} from governed source surfaces.",
                    ]
                    if item
                ),
                "inputs": sorted(set(str(item) for item in surface.get("source_surfaces", []) or [])),
                "outputs": [primitive_name, "review_ticket", "index_record"],
                "required_stages": list(surface.get("required_stages", []) or DEFAULT_REQUIRED_STAGES),
                "label_paths": sorted(set(label_paths + [f"primitive.{primitive_name}"])),
                "risk_tier": surface.get("risk_tier", "medium"),
                "excluded_scope": sorted(set(str(item) for item in surface.get("excluded_scope", []) or [])),
            }
        )
    return seeds


def export_source_surface_rows(
    source_surfaces: list[dict[str, Any]],
    *,
    output_dir: str | Path | None = None,
    excluded_scopes: list[str] | None = None,
) -> dict[str, Any]:
    seeds: list[dict[str, Any]] = []
    for surface in source_surfaces:
        seeds.extend(source_surface_to_use_case_seeds(surface))
    result = export_seed_rows(seeds, output_dir=output_dir, excluded_scopes=excluded_scopes)
    result["source_surface_count"] = len(source_surfaces)
    result["candidate_seed_count"] = len(seeds)
    return result


def _sample_surfaces() -> list[dict[str, Any]]:
    return [
        {
            "id": "plumbing-hvac-permit-system-surface",
            "title": "Plumbing and HVAC permit system surface",
            "vertical": "trades.mechanical.plumbing_hvac",
            "capability_gap_reason": "Permit rules and inspection checkpoints are fragmented.",
            "source_surfaces": ["municipal permit checklists", "public inspection forms"],
            "candidate_primitives": ["permit_requirement_fact", "inspection_checklist_item"],
            "label_paths": ["vertical.trades.plumbing.inspection"],
            "risk_tier": "high",
            "excluded_scope": ["insurance"],
        }
    ]


def _self_test() -> None:
    result = export_source_surface_rows(_sample_surfaces(), excluded_scopes=["insurance"])
    assert result["source_surface_count"] == 1
    assert result["candidate_seed_count"] == 2
    assert result["row_counts"]["normalized_object"] == 2
    assert result["row_counts"]["object_embedding"] == 2
    assert result["row_counts"]["review_ticket"] == 2


def main() -> int:
    parser = argparse.ArgumentParser(description="Export esoteric source-surface seeds into canonical factory JSONL rows.")
    parser.add_argument("--source-surfaces-jsonl")
    parser.add_argument("--output-dir")
    parser.add_argument("--excluded-scopes", nargs="*", default=["insurance"])
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        _self_test()
        print("ok")
        return 0
    if not args.source_surfaces_jsonl:
        parser.error("--source-surfaces-jsonl is required unless --self-test is used")
    print(
        json.dumps(
            export_source_surface_rows(
                _read_jsonl(args.source_surfaces_jsonl),
                output_dir=args.output_dir,
                excluded_scopes=args.excluded_scopes,
            ),
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
