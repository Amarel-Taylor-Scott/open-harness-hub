#!/usr/bin/env python3
"""Expand technical theory seeds into database-backed component candidate rows."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from scripts._config import LOCAL_POSTGRES_PGVECTOR_BACKEND
from scripts.factory.use_case_seed_rows import export_seed_rows


DEFAULT_THEORY_SEEDS = "catalog/knowledge-packs/data/theory-to-component-patterns/theory-seeds.jsonl"

DEFAULT_COMPONENT_STAGES = [
    "source_governance",
    "theory_claim_normalization",
    "component_boundary_extraction",
    "entity_linking",
    "fuzzy_dedupe",
    "index_record_emission",
    "review_ticket_routing",
]

COMPONENT_ROLES = [
    ("pre_llm_detector", "Detect or normalize input before a model is called", ["source_record", "raw_input"], ["normalized_input", "risk_signal"]),
    ("llm_router", "Choose the model, runtime, or escalation path", ["normalized_input", "risk_signal"], ["model_route", "cost_estimate"]),
    ("post_llm_verifier", "Check or transform model output after generation", ["model_output", "evidence_packet"], ["verification_result", "audit_event"]),
    ("evaluation_rubric", "Score the pipeline behavior against expected evidence", ["run_trace", "expected_behavior"], ["rubric_score", "failure_reason"]),
    ("deployment_blueprint", "Describe infrastructure and runtime choices", ["component_graph", "runtime_constraints"], ["deployment_plan", "terraform_hint"]),
    ("audit_trace", "Capture replayable evidence without storing sensitive content", ["decision", "evidence_hashes"], ["audit_record", "review_packet"]),
    ("cost_guard", "Estimate and constrain marginal model or worker cost", ["route_plan", "pricing_profile"], ["cost_decision", "fallback_route"]),
    ("human_review_gate", "Route uncertain or high-risk cases to qualified review", ["risk_signal", "uncertainty"], ["review_ticket", "decision_hold"]),
]

DEPLOYMENT_TARGETS = [
    LOCAL_POSTGRES_PGVECTOR_BACKEND,
    "render_worker_postgres",
    "cloud_run_container",
    "browser_local_model",
    "mobile_edge_runtime",
    "bigquery_analytics_tier",
]

RISK_ROUTES = [
    "low_risk_auto",
    "medium_risk_review",
    "high_risk_human_review",
    "regulated_signed_source",
]


def _read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            value = json.loads(line)
            if isinstance(value, dict):
                rows.append(value)
    return rows


def _slug(value: str) -> str:
    chars: list[str] = []
    for char in value.lower():
        if char.isalnum():
            chars.append(char)
        elif chars and chars[-1] != "-":
            chars.append("-")
    return "".join(chars).strip("-")[:80] or "theory"


def _stage_list(seed: dict[str, Any], role: str) -> list[str]:
    stages = list(DEFAULT_COMPONENT_STAGES)
    extra = [str(item) for item in seed.get("extra_stages", []) or []]
    if role not in stages:
        stages.insert(3, role)
    for item in extra:
        if item not in stages:
            stages.append(item)
    return stages


def build_theory_component_seeds(
    *,
    theory_seeds: list[dict[str, Any]],
    target_count: int = 1000,
    run_id: str = "theory-components",
) -> list[dict[str, Any]]:
    """Build cross-product candidate seeds from theory/postmortem inputs."""
    if not theory_seeds:
        raise ValueError("at least one theory seed is required")
    seeds: list[dict[str, Any]] = []
    ordinal = 1
    while len(seeds) < target_count:
        for theory in theory_seeds:
            theory_id = str(theory.get("id") or theory.get("name") or "theory")
            theory_slug = _slug(theory_id)
            domain = str(theory.get("domain") or "cross_domain")
            risk_tier = str(theory.get("risk_tier") or "medium")
            capability_gap = str(theory.get("capability_gap") or "not_solved_by_out_of_box_llm")
            source_kind = str(theory.get("source_kind") or "user_supplied_theory")
            base_labels = [str(item) for item in theory.get("label_paths", []) or []]
            axes = [str(item) for item in theory.get("expansion_axes", []) or []] or ["default_axis"]
            constraints = [str(item) for item in theory.get("constraints", []) or []] or ["review_before_publish"]
            for role, role_description, default_inputs, default_outputs in COMPONENT_ROLES:
                for deployment in DEPLOYMENT_TARGETS:
                    for route in RISK_ROUTES:
                        for axis in axes:
                            if len(seeds) >= target_count:
                                break
                            seed_id = f"{run_id}-{ordinal:05d}-{theory_slug}-{role}-{deployment}-{route}-{_slug(axis)}"
                            labels = [
                                f"theory.{theory_slug}",
                                f"component_role.{role}",
                                f"deployment.{deployment}",
                                f"risk_route.{route}",
                                f"capability_gap.{_slug(capability_gap).replace('-', '_')}",
                                f"source_kind.{source_kind}",
                            ] + base_labels
                            seeds.append(
                                {
                                    "id": seed_id,
                                    "title": f"{role.replace('_', ' ').title()} for {theory.get('name', theory_id)}",
                                    "domain": domain.replace(".", "_"),
                                    "task": (
                                        f"Turn the theory '{theory.get('name', theory_id)}' into a reusable {role} component. "
                                        f"{role_description}. Preserve provenance, constraints, review gates, deployment target {deployment}, "
                                        f"risk route {route}, and expansion axis {axis}."
                                    ),
                                    "inputs": list(default_inputs) + [source_kind, "theory_claim", "constraint_set"],
                                    "outputs": list(default_outputs) + ["subcomponent", "index_record", "review_ticket"],
                                    "required_stages": _stage_list(theory, role),
                                    "label_paths": labels,
                                    "risk_tier": risk_tier if route not in {"high_risk_human_review", "regulated_signed_source"} else "high",
                                    "excluded_scope": ["insurance"],
                                    "theory_context": {
                                        "theory_id": theory_id,
                                        "axis": axis,
                                        "constraints": constraints,
                                        "capability_gap": capability_gap,
                                    },
                                }
                            )
                            ordinal += 1
    return seeds


def run_theory_component_batch(
    *,
    theory_seeds_path: str | Path = DEFAULT_THEORY_SEEDS,
    output_dir: str | Path = "dist/theory-component-batch",
    target_count: int = 1000,
    run_id: str = "theory-components",
) -> dict[str, Any]:
    theory_seeds = _read_jsonl(theory_seeds_path)
    out = Path(output_dir)
    seeds = build_theory_component_seeds(theory_seeds=theory_seeds, target_count=target_count, run_id=run_id)
    seed_path = out / "theory-component-seeds.jsonl"
    seed_path.parent.mkdir(parents=True, exist_ok=True)
    seed_path.write_text("".join(json.dumps(seed, sort_keys=True, ensure_ascii=True) + "\n" for seed in seeds), encoding="utf-8")
    rows = export_seed_rows(seeds, output_dir=out / "rows", excluded_scopes=["insurance"])
    high_risk_count = sum(1 for seed in seeds if seed.get("risk_tier") == "high")
    summary = {
        "ok": True,
        "run_id": run_id,
        "theory_seed_count": len(theory_seeds),
        "target_count": target_count,
        "seed_count": len(seeds),
        "high_risk_seed_count": high_risk_count,
        "seed_path": str(seed_path),
        "row_counts": rows["row_counts"],
        "row_family_paths": rows["row_family_paths"],
        "source_path": str(theory_seeds_path),
        "strategy": "theory_to_database_backed_component_candidates",
        "notes": [
            "Generated candidates stay staged until dedupe, review, approval, promotion, CDC, and database load gates pass.",
            "The generator stores defensive summaries and component boundaries, not reusable harmful prompt payloads.",
            "Use this for technical postmortems, architecture critiques, research notes, and user-supplied theories.",
        ],
    }
    (out / "theory-component-batch-summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def _self_test() -> int:
    import tempfile

    sample = [
        {
            "id": "edge-semantic-gap",
            "name": "Edge semantic gap guardrails",
            "domain": "security.defensive",
            "risk_tier": "high",
            "source_kind": "defensive_postmortem",
            "capability_gap": "encoded_payloads_evade_syntactic_filters",
            "expansion_axes": ["base64", "url_encoding"],
            "constraints": ["no_harmful_payload_storage"],
        }
    ]
    with tempfile.TemporaryDirectory() as tmp:
        sample_path = Path(tmp) / "theories.jsonl"
        sample_path.write_text("".join(json.dumps(row) + "\n" for row in sample), encoding="utf-8")
        result = run_theory_component_batch(
            theory_seeds_path=sample_path,
            output_dir=Path(tmp) / "out",
            target_count=48,
            run_id="self-test",
        )
        assert result["ok"] is True
        assert result["seed_count"] == 48
        assert result["row_counts"]["normalized_object"] == 48
        assert result["row_counts"]["object_embedding"] == 48
        assert result["row_counts"]["index_record"] == 240
        assert result["row_counts"]["review_ticket"] >= 1
    print("ok")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--theory-seeds", default=DEFAULT_THEORY_SEEDS)
    parser.add_argument("--output-dir", default="dist/theory-component-batch")
    parser.add_argument("--target-count", type=int, default=1000)
    parser.add_argument("--run-id", default="theory-components")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    result = run_theory_component_batch(
        theory_seeds_path=args.theory_seeds,
        output_dir=args.output_dir,
        target_count=args.target_count,
        run_id=args.run_id,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
