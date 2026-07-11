"""Gradio playground for the OpenHubForAI.

Loads pipelines from `catalog/` and runs them step-by-step on user
input. Without a model adapter configured, runs in simulate mode so
every step returns a meaningful stub output.

Deploy this directory to a Hugging Face Space with sdk: gradio, or
run locally with `python app.py`.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

import gradio as gr
import yaml

# Add the repo root to sys.path so we can import scripts.run_pipeline.
py_const_hf_space_app__HERE = Path(__file__).resolve().parent
py_const_hf_space_app__ROOT = py_const_hf_space_app__HERE.parent
sys.path.insert(0, str(py_const_hf_space_app__ROOT))

from scripts.run_pipeline import load_catalog, run_pipeline  # noqa: E402


py_const_hf_space_app__CATALOG = load_catalog()
py_const_hf_space_app__PIPELINES = sorted(
    [(a["id"], a.get("name", a["id"])) for a in py_const_hf_space_app__CATALOG.values() if a.get("type") == "pipeline"]
)


def py_function_hf_space_app__render_pipeline_card(py_arg_hf_space_app__py_function_hf_space_app__render_pipeline_card__pipeline_id: str) -> str:
    py_local_hf_space_app__py_function_hf_space_app__render_pipeline_card__p = py_const_hf_space_app__CATALOG.get(py_arg_hf_space_app__py_function_hf_space_app__render_pipeline_card__pipeline_id) or {}
    py_local_hf_space_app__py_function_hf_space_app__render_pipeline_card__lines = [
        f"### {py_local_hf_space_app__py_function_hf_space_app__render_pipeline_card__p.get('name', py_arg_hf_space_app__py_function_hf_space_app__render_pipeline_card__pipeline_id)}",
        "",
        py_local_hf_space_app__py_function_hf_space_app__render_pipeline_card__p.get("description", "").strip(),
        "",
        f"- **id**: `{py_local_hf_space_app__py_function_hf_space_app__render_pipeline_card__p.get('id','')}`",
        f"- **pipeline_kind**: `{py_local_hf_space_app__py_function_hf_space_app__render_pipeline_card__p.get('pipeline_kind','—')}`",
        f"- **industry**: {', '.join(py_local_hf_space_app__py_function_hf_space_app__render_pipeline_card__p.get('industry', [])) or '—'}",
        f"- **capability**: {', '.join(py_local_hf_space_app__py_function_hf_space_app__render_pipeline_card__p.get('capability', [])) or '—'}",
        f"- **modality**: {', '.join(py_local_hf_space_app__py_function_hf_space_app__render_pipeline_card__p.get('modality', [])) or '—'}",
        f"- **lifecycle**: {py_local_hf_space_app__py_function_hf_space_app__render_pipeline_card__p.get('lifecycle','—')}",
        f"- **trust_boundary**: {py_local_hf_space_app__py_function_hf_space_app__render_pipeline_card__p.get('trust_boundary','—')}",
        "",
        "**Task**",
        "",
        (py_local_hf_space_app__py_function_hf_space_app__render_pipeline_card__p.get("task") or "").strip(),
    ]
    py_local_hf_space_app__py_function_hf_space_app__render_pipeline_card__steps = py_local_hf_space_app__py_function_hf_space_app__render_pipeline_card__p.get("steps") or []
    if py_local_hf_space_app__py_function_hf_space_app__render_pipeline_card__steps:
        py_local_hf_space_app__py_function_hf_space_app__render_pipeline_card__lines += ["", "**Steps**", ""]
        py_local_hf_space_app__py_function_hf_space_app__render_pipeline_card__lines += [
            f"{i+1}. `{s['id']}` — *{s['kind']}* → `{s['ref']}`"
            for i, s in enumerate(py_local_hf_space_app__py_function_hf_space_app__render_pipeline_card__steps)
        ]
    return "\n".join(py_local_hf_space_app__py_function_hf_space_app__render_pipeline_card__lines)


def py_function_hf_space_app__sample_inputs_text(py_arg_hf_space_app__py_function_hf_space_app__sample_inputs_text__pipeline_id: str) -> str:
    """Pre-fill with a sensible sample so visitors can click run immediately."""
    py_local_hf_space_app__py_function_hf_space_app__sample_inputs_text__samples = {
        "pipeline/research-entity": {
            "entity_name": "Acme Corp",
            "entity_kind": "company",
            "country": "US",
            "freshness_window_days": 30,
        },
        "pipeline/verify-claim-against-corpus": {
            "claim": "ILO Convention 29 prohibits forced labor.",
            "corpus": "knowledge-pack/style-references-cinematic",  # placeholder
        },
        "pipeline/brand-safe-product-photo": {
            "brief": {
                "name": "Ceramic mug",
                "category": "tabletop",
                "brand_tone": "moody noir",
                "shot_type": "portrait-85mm",
                "description": "studio shot of a navy ceramic mug, no logos",
            }
        },
    }
    return json.dumps(py_local_hf_space_app__py_function_hf_space_app__sample_inputs_text__samples.get(py_arg_hf_space_app__py_function_hf_space_app__sample_inputs_text__pipeline_id, {}), indent=2)


def py_function_hf_space_app__run_handler(py_arg_hf_space_app__py_function_hf_space_app__run_handler__pipeline_id: str, py_arg_hf_space_app__py_function_hf_space_app__run_handler__inputs_text: str, py_arg_hf_space_app__py_function_hf_space_app__run_handler__simulate: bool) -> tuple[str, str]:
    try:
        py_local_hf_space_app__py_function_hf_space_app__run_handler__inputs = json.loads(py_arg_hf_space_app__py_function_hf_space_app__run_handler__inputs_text) if py_arg_hf_space_app__py_function_hf_space_app__run_handler__inputs_text.strip() else {}
    except json.JSONDecodeError as py_local_hf_space_app__py_function_hf_space_app__run_handler__e:
        return f"**Input JSON parse error:** {py_local_hf_space_app__py_function_hf_space_app__run_handler__e}", ""
    py_local_hf_space_app__py_function_hf_space_app__run_handler__pipeline = py_const_hf_space_app__CATALOG.get(py_arg_hf_space_app__py_function_hf_space_app__run_handler__pipeline_id)
    if not py_local_hf_space_app__py_function_hf_space_app__run_handler__pipeline or py_local_hf_space_app__py_function_hf_space_app__run_handler__pipeline.get("type") != "pipeline":
        return f"**Unknown pipeline:** {py_arg_hf_space_app__py_function_hf_space_app__run_handler__pipeline_id}", ""
    py_local_hf_space_app__py_function_hf_space_app__run_handler__result = run_pipeline(py_local_hf_space_app__py_function_hf_space_app__run_handler__pipeline, py_local_hf_space_app__py_function_hf_space_app__run_handler__inputs, simulate=py_arg_hf_space_app__py_function_hf_space_app__run_handler__simulate)

    py_local_hf_space_app__py_function_hf_space_app__run_handler__md_parts: list[str] = ["## Trace", ""]
    for py_local_hf_space_app__py_function_hf_space_app__run_handler__step in py_local_hf_space_app__py_function_hf_space_app__run_handler__result["trace"]:
        py_local_hf_space_app__py_function_hf_space_app__run_handler__sim = " *(simulated)*" if py_local_hf_space_app__py_function_hf_space_app__run_handler__step.get("simulated") else ""
        py_local_hf_space_app__py_function_hf_space_app__run_handler__md_parts.append(f"### {py_local_hf_space_app__py_function_hf_space_app__run_handler__step['step_id']} — `{py_local_hf_space_app__py_function_hf_space_app__run_handler__step['kind']}` → `{py_local_hf_space_app__py_function_hf_space_app__run_handler__step['ref']}`{py_local_hf_space_app__py_function_hf_space_app__run_handler__sim}")
        py_local_hf_space_app__py_function_hf_space_app__run_handler__md_parts.append(f"- ms: {py_local_hf_space_app__py_function_hf_space_app__run_handler__step['ms']}")
        py_local_hf_space_app__py_function_hf_space_app__run_handler__md_parts.append("**input**")
        py_local_hf_space_app__py_function_hf_space_app__run_handler__md_parts.append("```json")
        py_local_hf_space_app__py_function_hf_space_app__run_handler__md_parts.append(json.dumps(py_local_hf_space_app__py_function_hf_space_app__run_handler__step["input"], indent=2))
        py_local_hf_space_app__py_function_hf_space_app__run_handler__md_parts.append("```")
        py_local_hf_space_app__py_function_hf_space_app__run_handler__md_parts.append("**output**")
        py_local_hf_space_app__py_function_hf_space_app__run_handler__md_parts.append("```json")
        py_local_hf_space_app__py_function_hf_space_app__run_handler__md_parts.append(json.dumps(py_local_hf_space_app__py_function_hf_space_app__run_handler__step["output"], indent=2))
        py_local_hf_space_app__py_function_hf_space_app__run_handler__md_parts.append("```")
    return "\n".join(py_local_hf_space_app__py_function_hf_space_app__run_handler__md_parts), json.dumps(py_local_hf_space_app__py_function_hf_space_app__run_handler__result, indent=2)


def py_function_hf_space_app__build_app() -> gr.Blocks:
    with gr.Blocks(title="OpenHubForAI — Playground", theme=gr.themes.Soft()) as py_local_hf_space_app__py_function_hf_space_app__build_app__app:
        gr.Markdown("# OpenHubForAI — Playground")
        gr.Markdown(
            "Pick a pipeline, edit the sample inputs, and run. Without a model "
            "configured (set `OH_MODEL` env var), this runs in **simulate mode** — "
            "every step returns a meaningful stub so you can see the shape of the "
            "trace."
        )

        with gr.Row():
            with gr.Column(scale=1):
                py_local_hf_space_app__py_function_hf_space_app__build_app__pipeline_dd = gr.Dropdown(
                    choices=[py_arg_hf_space_app__py_function_hf_space_app__build_app__pid for py_arg_hf_space_app__py_function_hf_space_app__build_app__pid, _ in py_const_hf_space_app__PIPELINES],
                    value=py_const_hf_space_app__PIPELINES[0][0] if py_const_hf_space_app__PIPELINES else None,
                    label="Pipeline",
                )
                py_local_hf_space_app__py_function_hf_space_app__build_app__simulate = gr.Checkbox(value=True, label="Simulate (no model calls)")
                py_local_hf_space_app__py_function_hf_space_app__build_app__run_btn = gr.Button("Run", variant="primary")
                py_local_hf_space_app__py_function_hf_space_app__build_app__card = gr.Markdown(py_function_hf_space_app__render_pipeline_card(py_const_hf_space_app__PIPELINES[0][0] if py_const_hf_space_app__PIPELINES else ""))

            with gr.Column(scale=2):
                py_local_hf_space_app__py_function_hf_space_app__build_app__inputs_tb = gr.Code(
                    value=py_function_hf_space_app__sample_inputs_text(py_const_hf_space_app__PIPELINES[0][0] if py_const_hf_space_app__PIPELINES else ""),
                    language="json",
                    label="Inputs (JSON)",
                )

        py_local_hf_space_app__py_function_hf_space_app__build_app__trace_md = gr.Markdown()
        py_local_hf_space_app__py_function_hf_space_app__build_app__raw_json = gr.Code(language="json", label="Full sample-run JSON")

        py_local_hf_space_app__py_function_hf_space_app__build_app__pipeline_dd.change(
            fn=lambda py_arg_hf_space_app__py_function_hf_space_app__build_app__pid: (py_function_hf_space_app__render_pipeline_card(py_arg_hf_space_app__py_function_hf_space_app__build_app__pid), py_function_hf_space_app__sample_inputs_text(py_arg_hf_space_app__py_function_hf_space_app__build_app__pid)),
            inputs=[py_local_hf_space_app__py_function_hf_space_app__build_app__pipeline_dd],
            outputs=[py_local_hf_space_app__py_function_hf_space_app__build_app__card, py_local_hf_space_app__py_function_hf_space_app__build_app__inputs_tb],
        )
        py_local_hf_space_app__py_function_hf_space_app__build_app__run_btn.click(
            fn=py_function_hf_space_app__run_handler,
            inputs=[py_local_hf_space_app__py_function_hf_space_app__build_app__pipeline_dd, py_local_hf_space_app__py_function_hf_space_app__build_app__inputs_tb, py_local_hf_space_app__py_function_hf_space_app__build_app__simulate],
            outputs=[py_local_hf_space_app__py_function_hf_space_app__build_app__trace_md, py_local_hf_space_app__py_function_hf_space_app__build_app__raw_json],
        )

    return py_var_hf_space_app__app


if __name__ == "__main__":
    py_var_hf_space_app__app = py_function_hf_space_app__build_app()
    py_var_hf_space_app__app.launch(server_name=os.environ.get("HOST", "127.0.0.1"), server_port=int(os.environ.get("PORT", "7860")))
