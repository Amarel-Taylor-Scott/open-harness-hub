#!/usr/bin/env python3
"""Export component pipeline templates as CSV plus a psql load script."""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import csv
import json
import tempfile
import time
from pathlib import Path
from typing import Any


def _utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def _json(value: Any, default: Any) -> str:
    return json.dumps(value if value is not None else default, sort_keys=True, ensure_ascii=False)


def _str(value: Any) -> str:
    return "" if value is None else str(value)


def _sql_path(path: Path) -> str:
    return str(path).replace("'", "''")


TEMPLATE_COLUMNS = [
    "template_id",
    "name",
    "task_family",
    "cost_profile",
    "modality",
    "industry",
    "body",
]
STEP_COLUMNS = [
    "template_step_id",
    "template_id",
    "step_order",
    "component_layer",
    "control_flow_kind",
    "component_ref",
    "component_id",
    "component_candidate_id",
    "required",
    "inputs",
    "outputs",
    "body",
]


def _template_row(template: dict[str, Any]) -> dict[str, str]:
    return {
        "template_id": _str(template.get("template_id")),
        "name": _str(template.get("name") or template.get("task") or template.get("template_id")),
        "task_family": _str(template.get("task_family") or "general_llm_pipeline"),
        "cost_profile": _str(template.get("cost_profile") or "cheap"),
        "modality": _json(template.get("modality"), []),
        "industry": _json(template.get("industry"), []),
        "body": _json(template, {}),
    }


def _component_id(ref: str) -> str:
    if ref.startswith("component-candidate/"):
        return ""
    return ref if "/" in ref else ""


def _component_candidate_id(ref: str) -> str:
    return ref if ref.startswith("component-candidate/") else ""


def _step_rows(template: dict[str, Any]) -> list[dict[str, str]]:
    template_id = _str(template.get("template_id"))
    rows: list[dict[str, str]] = []
    for index, step in enumerate(template.get("steps") or [], 1):
        if not isinstance(step, dict):
            continue
        step_id = _str(step.get("id") or f"step-{index:03d}")
        ref = _str(step.get("ref"))
        rows.append({
            "template_step_id": f"{template_id}/step/{index:03d}-{step_id}",
            "template_id": template_id,
            "step_order": str(index),
            "component_layer": _str(step.get("component_layer")),
            "control_flow_kind": _str(step.get("control_flow_kind")),
            "component_ref": ref,
            "component_id": _component_id(ref),
            "component_candidate_id": _component_candidate_id(ref),
            "required": "true" if step.get("required", True) else "false",
            "inputs": _json(step.get("inputs"), {}),
            "outputs": _json(step.get("outputs"), {}),
            "body": _json(step, {}),
        })
    return rows


def _write_csv(path: Path, columns: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _load_sql(template_csv: Path, step_csv: Path) -> str:
    return f"""BEGIN;

CREATE TEMP TABLE stage_component_pipeline_template (
  template_id text,
  name text,
  task_family text,
  cost_profile text,
  modality jsonb,
  industry jsonb,
  body jsonb
);

CREATE TEMP TABLE stage_component_pipeline_template_step (
  template_step_id text,
  template_id text,
  step_order integer,
  component_layer text,
  control_flow_kind text,
  component_ref text,
  component_id text,
  component_candidate_id text,
  required boolean,
  inputs jsonb,
  outputs jsonb,
  body jsonb
);

\\copy stage_component_pipeline_template FROM '{_sql_path(template_csv)}' WITH (FORMAT csv, HEADER true)
\\copy stage_component_pipeline_template_step FROM '{_sql_path(step_csv)}' WITH (FORMAT csv, HEADER true)

INSERT INTO component_pipeline_template (
  template_id, name, task_family, cost_profile, modality, industry, body
)
SELECT
  template_id,
  name,
  task_family,
  NULLIF(cost_profile, ''),
  ARRAY(SELECT jsonb_array_elements_text(COALESCE(modality, '[]'::jsonb))),
  ARRAY(SELECT jsonb_array_elements_text(COALESCE(industry, '[]'::jsonb))),
  COALESCE(body, '{{}}'::jsonb)
FROM stage_component_pipeline_template
WHERE template_id <> ''
ON CONFLICT (template_id) DO UPDATE SET
  name=EXCLUDED.name,
  task_family=EXCLUDED.task_family,
  cost_profile=EXCLUDED.cost_profile,
  modality=EXCLUDED.modality,
  industry=EXCLUDED.industry,
  body=EXCLUDED.body,
  updated_at=now();

INSERT INTO component_pipeline_template_step (
  template_step_id, template_id, step_order, component_id,
  component_candidate_id, component_layer, control_flow_kind,
  required, inputs, outputs, body
)
SELECT
  template_step_id,
  template_id,
  step_order,
  CASE
    WHEN component_id <> '' AND EXISTS (SELECT 1 FROM component WHERE id = component_id) THEN component_id
    ELSE NULL
  END,
  CASE
    WHEN component_candidate_id <> '' AND EXISTS (
      SELECT 1 FROM component_candidate cc WHERE cc.component_candidate_id = stage_component_pipeline_template_step.component_candidate_id
    ) THEN component_candidate_id
    ELSE NULL
  END,
  component_layer,
  NULLIF(control_flow_kind, ''),
  COALESCE(required, true),
  COALESCE(inputs, '{{}}'::jsonb),
  COALESCE(outputs, '{{}}'::jsonb),
  COALESCE(body, '{{}}'::jsonb) || jsonb_build_object('component_ref', component_ref)
FROM stage_component_pipeline_template_step
WHERE template_step_id <> '' AND template_id <> ''
ON CONFLICT (template_step_id) DO UPDATE SET
  template_id=EXCLUDED.template_id,
  step_order=EXCLUDED.step_order,
  component_id=EXCLUDED.component_id,
  component_candidate_id=EXCLUDED.component_candidate_id,
  component_layer=EXCLUDED.component_layer,
  control_flow_kind=EXCLUDED.control_flow_kind,
  required=EXCLUDED.required,
  inputs=EXCLUDED.inputs,
  outputs=EXCLUDED.outputs,
  body=EXCLUDED.body;

COMMIT;
"""


def create_component_template_load_plan(
    *,
    template_paths: list[str | Path],
    output_dir: str | Path | None = None,
    load_sql_name: str = "load-component-pipeline-templates.sql",
) -> dict[str, Any]:
    if not template_paths:
        raise ValueError("at least one template path is required")
    out = Path(output_dir) if output_dir else Path(tempfile.mkdtemp(prefix="ohh-component-template-load-"))
    templates = [_read_json(Path(path)) for path in template_paths]
    template_rows = [_template_row(template) for template in templates]
    step_rows = [row for template in templates for row in _step_rows(template)]

    template_csv = out / "component-pipeline-templates.csv"
    step_csv = out / "component-pipeline-template-steps.csv"
    load_sql = out / load_sql_name
    _write_csv(template_csv, TEMPLATE_COLUMNS, template_rows)
    _write_csv(step_csv, STEP_COLUMNS, step_rows)
    load_sql.write_text(_load_sql(template_csv, step_csv), encoding="utf-8")

    report = {
        "ok": True,
        "generated_at": _utc_now(),
        "template_count": len(template_rows),
        "template_step_count": len(step_rows),
        "output_dir": str(out),
        "input_templates": [str(path) for path in template_paths],
        "files": {
            "templates_csv": str(template_csv),
            "template_steps_csv": str(step_csv),
            "load_sql": str(load_sql),
            "summary": str(out / "component-template-load-plan.json"),
        },
        "safety_notes": [
            "This planner writes CSV and SQL only; it does not connect to Postgres.",
            "Component references are preserved in step bodies even when the active component row is not present yet.",
            "Templates should be reviewed before tenant-visible publication.",
        ],
    }
    _write_json(out / "component-template-load-plan.json", report)
    return report


def _self_test() -> int:
    path = _resource("dist/source-surface-scan-partitions/seed/component-pipeline-templates/human-exploitation-photo-description-cheap.json")
    if not path.exists():
        raise FileNotFoundError(f"{path} is required; run the component pipeline template expander first")
    with tempfile.TemporaryDirectory() as tmp:
        report = create_component_template_load_plan(template_paths=[path], output_dir=tmp)
        assert report["template_count"] == 1
        assert report["template_step_count"] >= 4
        assert Path(report["files"]["load_sql"]).exists()
    print(json.dumps({
        "ok": True,
        "template_count": report["template_count"],
        "template_step_count": report["template_step_count"],
    }, indent=2, sort_keys=True))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create CSV and psql load script for component pipeline templates.")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--template-path", action="append", default=[])
    parser.add_argument("--output-dir")
    parser.add_argument("--load-sql-name", default="load-component-pipeline-templates.sql")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    if not args.template_path:
        parser.error("--template-path is required unless --self-test is used")
    result = create_component_template_load_plan(
        template_paths=args.template_path,
        output_dir=args.output_dir,
        load_sql_name=args.load_sql_name,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
