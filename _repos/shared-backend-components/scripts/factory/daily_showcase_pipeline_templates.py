#!/usr/bin/env python3
"""Generate daily off-the-shelf showcase pipeline templates."""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from scripts.db.component_template_load_plan import create_component_template_load_plan
from scripts._config import POSTGRES_PGVECTOR_RENDER_WORKER_TARGET


DEFAULT_SCENARIOS = _resource("catalog/knowledge-packs/data/daily-showcase-pipeline-patterns/showcase-scenarios.jsonl")

COMMON_STEPS = {
    "source_governance": {
        "id": "source-governance",
        "component_layer": "pre_llm",
        "ref": "tool/source-record-governance-router",
        "inputs": {"records": "$.inputs.source_records"},
        "outputs": {"governed_records": "$.state.governed_records"},
    },
    "sensitive_gate": {
        "id": "sensitive-data-gate",
        "component_layer": "pre_llm",
        "ref": "tool/sensitive-data-object-gate",
        "inputs": {"candidate": "$.state.governed_records"},
        "outputs": {"safe_candidate": "$.state.safe_candidate", "review_route": "$.state.privacy_review"},
    },
    "entity_linking": {
        "id": "entity-linking",
        "component_layer": "pre_llm",
        "ref": "tool/entity-recognition-linker",
        "inputs": {"text": "$.state.safe_candidate"},
        "outputs": {"entities": "$.state.entities"},
    },
    "retrieval": {
        "id": "hybrid-retrieval",
        "component_layer": "pre_llm",
        "ref": "tool/embedding-index-search",
        "inputs": {"query": "$.inputs.user_goal", "filters": "$.state.entities"},
        "outputs": {"evidence": "$.state.evidence"},
    },
    "model_route": {
        "id": "model-route",
        "component_layer": "llm",
        "ref": "tool/model-capability-router",
        "inputs": {"task": "$.inputs.user_goal", "cost_profile": "$.template.cost_profile"},
        "outputs": {"model_route": "$.state.model_route"},
    },
    "cost_check": {
        "id": "cost-check",
        "component_layer": "post_llm",
        "ref": "tool/blueprint-ab-cost-quality-planner",
        "inputs": {"route": "$.state.model_route", "traffic": "$.inputs.expected_volume"},
        "outputs": {"cost_estimate": "$.outputs.cost_estimate"},
    },
    "review_gate": {
        "id": "human-review-gate",
        "component_layer": "control_flow",
        "control_flow_kind": "human_review",
        "ref": "tool/content-approval-planner",
        "inputs": {"risk": "$.template.risk_tier", "evidence": "$.state.evidence"},
        "outputs": {"review_ticket": "$.outputs.review_ticket"},
    },
    "blueprint_emit": {
        "id": "blueprint-output",
        "component_layer": "post_llm",
        "ref": "tool/blueprint-output-record-emitter",
        "inputs": {"result": "$.state.result", "cost_estimate": "$.outputs.cost_estimate"},
        "outputs": {"blueprint": "$.outputs.blueprint"},
    },
}


def _safe_slug(value: str) -> str:
    chars: list[str] = []
    for char in value.lower():
        if char.isalnum():
            chars.append(char)
        elif chars and chars[-1] != "-":
            chars.append("-")
    return "".join(chars).strip("-")[:80] or "showcase"


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


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


def _scenario_hash(scenario: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(scenario, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()[:16]


def _template_from_scenario(scenario: dict[str, Any], run_id: str) -> dict[str, Any]:
    slug = _safe_slug(str(scenario["id"]).split("/")[-1])
    template_id = f"template/showcase/{run_id}/{slug}"
    selected_steps = scenario.get("step_profile") or [
        "source_governance",
        "sensitive_gate",
        "entity_linking",
        "retrieval",
        "model_route",
        "cost_check",
        "review_gate",
        "blueprint_emit",
    ]
    steps: list[dict[str, Any]] = []
    for name in selected_steps:
        step = dict(COMMON_STEPS[name])
        step["body"] = {
            "showcase_role": name,
            "domain": scenario.get("domain"),
            "risk_tier": scenario.get("risk_tier"),
            "deployment_target": scenario.get("deployment_target"),
        }
        steps.append(step)
    return {
        "template_id": template_id,
        "name": scenario["name"],
        "task_family": scenario.get("task_family", scenario.get("domain", "cross_industry")),
        "cost_profile": scenario.get("cost_profile", "cheap"),
        "modality": scenario.get("modality", ["text"]),
        "industry": scenario.get("industry", ["cross_industry"]),
        "user_sentence": scenario["user_sentence"],
        "domain": scenario.get("domain"),
        "risk_tier": scenario.get("risk_tier", "medium"),
        "deployment_target": scenario.get("deployment_target", POSTGRES_PGVECTOR_RENDER_WORKER_TARGET),
        "expected_inputs": scenario.get("expected_inputs", []),
        "expected_outputs": scenario.get("expected_outputs", []),
        "review_gates": scenario.get("review_gates", []),
        "source_scenario_id": scenario["id"],
        "source_scenario_hash": _scenario_hash(scenario),
        "publication_status": "review_ready_template",
        "steps": steps,
    }


def generate_showcase_templates(
    *,
    scenario_path: str | Path = DEFAULT_SCENARIOS,
    output_dir: str | Path,
    count: int = 10,
    run_id: str = "daily-showcase",
) -> dict[str, Any]:
    if count < 5 or count > 25:
        raise ValueError("daily showcase template count must be between 5 and 25")
    scenarios = _read_jsonl(Path(scenario_path))
    if len(scenarios) < count:
        raise ValueError(f"scenario file has {len(scenarios)} rows but {count} requested")

    out = Path(output_dir)
    template_dir = out / "templates"
    selected = scenarios[:count]
    templates = [_template_from_scenario(scenario, run_id=run_id) for scenario in selected]
    template_paths: list[str] = []
    for template in templates:
        path = template_dir / f"{_safe_slug(template['template_id'])}.json"
        _write_json(path, template)
        template_paths.append(str(path))

    _write_jsonl(out / "selected-showcase-scenarios.jsonl", selected)
    load_plan = create_component_template_load_plan(
        template_paths=template_paths,
        output_dir=out / "load-plan",
    )
    summary = {
        "ok": True,
        "run_id": run_id,
        "scenario_path": str(scenario_path),
        "output_dir": str(out),
        "showcase_template_count": len(templates),
        "template_step_count": load_plan["template_step_count"],
        "template_paths": template_paths,
        "load_plan": load_plan,
        "counts": {
            "showcase_templates": len(templates),
            "template_steps": load_plan["template_step_count"],
            "selected_scenarios": len(selected),
        },
        "notes": [
            "These are database-backed component pipeline templates, not one YAML file per showcase.",
            "Templates are review-ready and should be loaded into Postgres only after operator approval.",
            "Each template includes pre-LLM, LLM, post-LLM, control-flow, cost, review, and deployment metadata.",
        ],
    }
    _write_json(out / "daily-showcase-pipeline-summary.json", summary)
    return summary


def _self_test() -> int:
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        result = generate_showcase_templates(output_dir=tmp, count=5, run_id="self-test")
        assert result["showcase_template_count"] == 5
        assert result["template_step_count"] >= 35
        assert Path(result["load_plan"]["files"]["load_sql"]).exists()
    print("ok")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--scenario-path", default=str(DEFAULT_SCENARIOS))
    parser.add_argument("--output-dir", default="dist/daily-showcase-pipelines")
    parser.add_argument("--count", type=int, default=10)
    parser.add_argument("--run-id", default="daily-showcase")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    result = generate_showcase_templates(
        scenario_path=args.scenario_path,
        output_dir=args.output_dir,
        count=args.count,
        run_id=args.run_id,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
