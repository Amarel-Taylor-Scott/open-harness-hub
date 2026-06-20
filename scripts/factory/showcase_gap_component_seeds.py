#!/usr/bin/env python3
"""Convert showcase coverage gaps into targeted component candidate rows."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from scripts._config import POSTGRES_PGVECTOR_BACKEND
from scripts.factory.use_case_seed_rows import export_seed_rows


ROLE_STAGE_MAP = {
    "sensitive_gate": ["source_governance", "sensitive_data_screening", "review_ticket_routing", "index_record_emission"],
    "retrieval": ["source_governance", "entity_linking", "embedding_retrieval", "index_record_emission"],
    "cost_check": ["source_governance", "model_route_costing", "cost_estimation", "review_ticket_routing"],
    "blueprint_emit": ["source_governance", "blueprint_emission", "template_step_mapping", "index_record_emission"],
}

ROLE_INPUTS = {
    "sensitive_gate": ["source_record", "candidate_payload", "privacy_boundary"],
    "retrieval": ["query", "entity_refs", "index_record"],
    "cost_check": ["model_route", "expected_volume", "deployment_target"],
    "blueprint_emit": ["template_step", "coverage_result", "cost_estimate"],
}


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        if not isinstance(row, dict):
            raise ValueError(f"{path}:{line_no}: expected JSON object")
        rows.append(row)
    return rows


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


def _safe_slug(value: str) -> str:
    chars: list[str] = []
    for char in value.lower():
        if char.isalnum():
            chars.append(char)
        elif chars and chars[-1] != "-":
            chars.append("-")
    return "".join(chars).strip("-")[:88] or "gap"


def _short_hash(value: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()[:10]


def _seed_from_gap(gap: dict[str, Any]) -> dict[str, Any]:
    role = str(gap.get("showcase_role") or "pipeline_step")
    domain = str(gap.get("needed_domain") or "cross_domain")
    risk_tier = str(gap.get("needed_risk_tier") or "medium")
    cost_profile = str(gap.get("needed_cost_profile") or "balanced")
    deployment_target = str(gap.get("needed_deployment_target") or POSTGRES_PGVECTOR_BACKEND)
    template_name = str(gap.get("template_name") or gap.get("template_id") or "showcase template")
    seed_id = f"showcase-gap-{_short_hash(gap)}-{_safe_slug(str(gap.get('request_id') or template_name + '-' + role))}"
    suggested_labels = [str(item) for item in gap.get("suggested_label_paths", []) or []]
    outputs = list(dict.fromkeys([str(item) for item in gap.get("suggested_outputs", []) or []] + [role, "pipeline_step", "review_ticket"]))
    return {
        "id": seed_id,
        "title": f"{role.replace('_', ' ').title()} component for {template_name}",
        "domain": domain.replace(".", "_").replace("-", "_"),
        "task": (
            f"Create a targeted {role} component candidate for the showcase template {template_name}. "
            f"The component should improve partial coverage for domain {domain}, cost profile {cost_profile}, "
            f"deployment target {deployment_target}, and risk tier {risk_tier}. Preserve source governance, "
            "entity links, dedupe keys, index records, review routing, and model-swap metadata."
        ),
        "inputs": ROLE_INPUTS.get(role, ["source_record", "normalized_object", "template_step"]),
        "outputs": outputs,
        "required_stages": ROLE_STAGE_MAP.get(role, ["source_governance", "entity_linking", "index_record_emission", "review_ticket_routing"]),
        "label_paths": list(dict.fromkeys([
            *suggested_labels,
            f"showcase.template.{_safe_slug(str(gap.get('template_id') or template_name))}",
            f"showcase.role.{role}",
            f"cost_profile.{cost_profile}",
            f"deployment.{deployment_target}",
            "customization.pipeline_step",
            "source.showcase_gap_request",
        ])),
        "risk_tier": risk_tier,
        "excluded_scope": ["insurance"],
        "source_gap_request": gap,
    }


def generate_gap_component_rows(
    *,
    missing_requests: str | Path,
    output_dir: str | Path,
) -> dict[str, Any]:
    gaps = _read_jsonl(Path(missing_requests))
    seeds = [_seed_from_gap(gap) for gap in gaps]
    out = Path(output_dir)
    seed_path = out / "showcase-gap-component-seeds.jsonl"
    _write_jsonl(seed_path, seeds)
    rows = export_seed_rows(seeds, output_dir=out / "rows", excluded_scopes=["insurance"])
    summary = {
        "ok": True,
        "missing_request_count": len(gaps),
        "seed_count": len(seeds),
        "seed_path": str(seed_path),
        "row_counts": rows["row_counts"],
        "row_family_paths": rows["row_family_paths"],
        "strategy": "showcase_gap_to_component_candidates",
        "notes": [
            "These rows target partial or missing showcase template coverage.",
            "They are database-backed component candidates, not public component definitions.",
            "High-risk gap-derived candidates remain review-gated before promotion.",
        ],
    }
    (out / "showcase-gap-component-summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def _self_test() -> int:
    result = generate_gap_component_rows(
        missing_requests="dist/showcase-candidate-coverage/2026-05-28/missing-component-requests.jsonl",
        output_dir="dist/showcase-gap-components/self-test",
    )
    assert result["seed_count"] >= 1
    assert result["row_counts"]["normalized_object"] == result["seed_count"]
    assert result["row_counts"]["index_record"] == result["seed_count"] * 5
    print("ok")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--missing-requests")
    parser.add_argument("--output-dir", default="dist/showcase-gap-components")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    if not args.missing_requests:
        parser.error("--missing-requests is required unless --self-test is used")
    result = generate_gap_component_rows(missing_requests=args.missing_requests, output_dir=args.output_dir)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
