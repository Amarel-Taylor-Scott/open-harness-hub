#!/usr/bin/env python3
"""Expand a plain-language task into a reusable component pipeline template."""
from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path
from typing import Any

from scripts._config import POSTGRES_PGVECTOR_BACKEND


def _utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _slug(value: str) -> str:
    text = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return text[:72].strip("-") or "component-pipeline"


def _task_family(task: str) -> str:
    t = task.lower()
    if any(word in t for word in ("moderate", "flag", "abuse", "exploitation", "content")):
        return "content_moderation"
    if any(word in t for word in ("law", "rule", "regulation", "compliance", "fee", "overcharging")):
        return "regulated_fact_check"
    if any(word in t for word in ("image", "photo", "video", "audio", "music")):
        return "multimodal_review"
    if any(word in t for word in ("search", "research", "competitive", "market")):
        return "research_synthesis"
    return "general_llm_pipeline"


def _modalities(task: str) -> list[str]:
    t = task.lower()
    out = ["text"]
    for key, value in (("image", "image"), ("photo", "image"), ("video", "video"), ("audio", "audio"), ("music", "audio")):
        if key in t and value not in out:
            out.append(value)
    return out


def expand_component_pipeline_template(
    *,
    task: str,
    cost_profile: str = "cheap",
    output_path: str | Path | None = None,
) -> dict[str, Any]:
    family = _task_family(task)
    modalities = _modalities(task)
    cheap = cost_profile in {"cheap", "local_first"}
    model_ref = "adapter/ollama-default" if cost_profile == "local_first" else "adapter/openai-compatible-reviewer"

    steps = [
        {
            "id": "normalize-input",
            "component_layer": "pre_llm",
            "component_type": "tool",
            "ref": "tool/page-to-markdown-converter" if modalities == ["text"] else "tool/multimodal-evidence-router",
            "purpose": "Normalize raw user input and media references into structured evidence records.",
        },
        {
            "id": "privacy-and-source-gate",
            "component_layer": "pre_llm",
            "component_type": "tool",
            "ref": "tool/sensitive-data-object-gate",
            "purpose": "Detect sensitive fields, apply privacy boundaries, and route high-risk inputs to review.",
        },
        {
            "id": "retrieve-relevant-components",
            "component_layer": "pre_llm",
            "component_type": "tool",
            "ref": "tool/embedding-index-search",
            "purpose": "Use hybrid keyword, label, and vector search to select relevant components and subcomponents.",
        },
        {
            "id": "cheap-first-model-pass",
            "component_layer": "llm",
            "component_type": "adapter",
            "ref": model_ref,
            "purpose": "Run the lowest-cost model that satisfies the routing, modality, and risk constraints.",
            "cost_policy": "prefer cached prompts and small/local models before larger hosted models" if cheap else "prefer higher accuracy model calls for ambiguous cases",
        },
        {
            "id": "threshold-check",
            "component_layer": "post_llm",
            "component_type": "tool",
            "ref": "tool/scale-policy-threshold-check-003",
            "purpose": "Convert model output into deterministic labels, confidence scores, and review routes.",
        },
        {
            "id": "verify-critical-claims",
            "component_layer": "post_llm",
            "component_type": "tool",
            "ref": "tool/grounded-multimodel-verification-gate",
            "purpose": "Escalate high-risk or low-confidence decisions to grounded search, multiple models, or human review.",
        },
        {
            "id": "iterate-until-decision",
            "component_layer": "control_flow",
            "control_flow_kind": "iterate",
            "component_type": "pipeline",
            "ref": "pipeline/component-pipeline-template-expansion",
            "purpose": "Repeat retrieval, model pass, and verification until stop criteria or budget limits are reached.",
        },
        {
            "id": "human-review-loop",
            "component_layer": "control_flow",
            "control_flow_kind": "human_review",
            "component_type": "tool",
            "ref": "tool/expert-email-review-campaign-manager",
            "purpose": "Route important or risky outputs to vetted reviewers and ingest their responses as knowledge updates.",
        },
    ]
    result = {
        "ok": True,
        "generated_at": _utc_now(),
        "template_id": f"component-pipeline-template/{_slug(task)}",
        "task": task,
        "task_family": family,
        "cost_profile": cost_profile,
        "modality": modalities,
        "storage_target": "postgres_component_pipeline_template",
        "vector_search": POSTGRES_PGVECTOR_BACKEND,
        "steps": steps,
        "scale_notes": [
            "Store reusable templates in Postgres and embed step text for pgvector retrieval.",
            "Keep raw scraped material in object storage; store normalized rows, labels, vectors, and provenance in Postgres.",
            "Promote generated candidates only after review and source-governance checks.",
        ],
    }
    if output_path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def _self_test() -> int:
    result = expand_component_pipeline_template(
        task="Build a cheap pipeline to flag social media content related to worker exploitation from a photo and description.",
        cost_profile="cheap",
    )
    assert result["ok"]
    assert any(step["component_layer"] == "pre_llm" for step in result["steps"])
    assert any(step["component_layer"] == "llm" for step in result["steps"])
    assert any(step["component_layer"] == "post_llm" for step in result["steps"])
    assert any(step.get("control_flow_kind") == "iterate" for step in result["steps"])
    print(json.dumps({"ok": True, "step_count": len(result["steps"]), "task_family": result["task_family"]}, indent=2, sort_keys=True))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Expand a task into a reusable component pipeline template.")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--task")
    parser.add_argument("--cost-profile", default="cheap", choices=["cheap", "balanced", "quality", "local_first"])
    parser.add_argument("--output-path")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    if not args.task:
        parser.error("--task is required unless --self-test is used")
    result = expand_component_pipeline_template(task=args.task, cost_profile=args.cost_profile, output_path=args.output_path)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
