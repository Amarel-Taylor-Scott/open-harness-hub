"""Gradio playground for the Open Harness Hub.

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
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))

from scripts.run_pipeline import load_catalog, run_pipeline  # noqa: E402


CATALOG = load_catalog()
PIPELINES = sorted(
    [(a["id"], a.get("name", a["id"])) for a in CATALOG.values() if a.get("type") == "pipeline"]
)


def render_pipeline_card(pipeline_id: str) -> str:
    p = CATALOG.get(pipeline_id) or {}
    lines = [
        f"### {p.get('name', pipeline_id)}",
        "",
        p.get("description", "").strip(),
        "",
        f"- **id**: `{p.get('id','')}`",
        f"- **pipeline_kind**: `{p.get('pipeline_kind','—')}`",
        f"- **industry**: {', '.join(p.get('industry', [])) or '—'}",
        f"- **capability**: {', '.join(p.get('capability', [])) or '—'}",
        f"- **modality**: {', '.join(p.get('modality', [])) or '—'}",
        f"- **lifecycle**: {p.get('lifecycle','—')}",
        f"- **trust_boundary**: {p.get('trust_boundary','—')}",
        "",
        "**Task**",
        "",
        (p.get("task") or "").strip(),
    ]
    steps = p.get("steps") or []
    if steps:
        lines += ["", "**Steps**", ""]
        lines += [
            f"{i+1}. `{s['id']}` — *{s['kind']}* → `{s['ref']}`"
            for i, s in enumerate(steps)
        ]
    return "\n".join(lines)


def sample_inputs_text(pipeline_id: str) -> str:
    """Pre-fill with a sensible sample so visitors can click run immediately."""
    samples = {
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
    return json.dumps(samples.get(pipeline_id, {}), indent=2)


def run_handler(pipeline_id: str, inputs_text: str, simulate: bool) -> tuple[str, str]:
    try:
        inputs = json.loads(inputs_text) if inputs_text.strip() else {}
    except json.JSONDecodeError as e:
        return f"**Input JSON parse error:** {e}", ""
    pipeline = CATALOG.get(pipeline_id)
    if not pipeline or pipeline.get("type") != "pipeline":
        return f"**Unknown pipeline:** {pipeline_id}", ""
    result = run_pipeline(pipeline, inputs, simulate=simulate)

    md_parts: list[str] = ["## Trace", ""]
    for step in result["trace"]:
        sim = " *(simulated)*" if step.get("simulated") else ""
        md_parts.append(f"### {step['step_id']} — `{step['kind']}` → `{step['ref']}`{sim}")
        md_parts.append(f"- ms: {step['ms']}")
        md_parts.append("**input**")
        md_parts.append("```json")
        md_parts.append(json.dumps(step["input"], indent=2))
        md_parts.append("```")
        md_parts.append("**output**")
        md_parts.append("```json")
        md_parts.append(json.dumps(step["output"], indent=2))
        md_parts.append("```")
    return "\n".join(md_parts), json.dumps(result, indent=2)


def build_app() -> gr.Blocks:
    with gr.Blocks(title="Open Harness Hub — Playground", theme=gr.themes.Soft()) as app:
        gr.Markdown("# Open Harness Hub — Playground")
        gr.Markdown(
            "Pick a pipeline, edit the sample inputs, and run. Without a model "
            "configured (set `OH_MODEL` env var), this runs in **simulate mode** — "
            "every step returns a meaningful stub so you can see the shape of the "
            "trace."
        )

        with gr.Row():
            with gr.Column(scale=1):
                pipeline_dd = gr.Dropdown(
                    choices=[pid for pid, _ in PIPELINES],
                    value=PIPELINES[0][0] if PIPELINES else None,
                    label="Pipeline",
                )
                simulate = gr.Checkbox(value=True, label="Simulate (no model calls)")
                run_btn = gr.Button("Run", variant="primary")
                card = gr.Markdown(render_pipeline_card(PIPELINES[0][0] if PIPELINES else ""))

            with gr.Column(scale=2):
                inputs_tb = gr.Code(
                    value=sample_inputs_text(PIPELINES[0][0] if PIPELINES else ""),
                    language="json",
                    label="Inputs (JSON)",
                )

        trace_md = gr.Markdown()
        raw_json = gr.Code(language="json", label="Full sample-run JSON")

        pipeline_dd.change(
            fn=lambda pid: (render_pipeline_card(pid), sample_inputs_text(pid)),
            inputs=[pipeline_dd],
            outputs=[card, inputs_tb],
        )
        run_btn.click(
            fn=run_handler,
            inputs=[pipeline_dd, inputs_tb, simulate],
            outputs=[trace_md, raw_json],
        )

    return app


if __name__ == "__main__":
    app = build_app()
    app.launch(server_name=os.environ.get("HOST", "127.0.0.1"), server_port=int(os.environ.get("PORT", "7860")))
