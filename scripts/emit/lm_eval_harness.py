#!/usr/bin/env python3
"""Emit EleutherAI lm-evaluation-harness task YAML for every `benchmark/*`.

Spec: https://github.com/EleutherAI/lm-evaluation-harness/blob/main/docs/task_guide.md

Maps:
  hub `benchmark.dataset`  → lm-eval `dataset_path` (+ dataset_name)
  hub `benchmark.rubric`   → lm-eval `metric_list`
  hub `benchmark.pipeline` → lm-eval `doc_to_text` / `doc_to_target`
                             (composed from the pipeline's defaults)

Output: dist/lm-eval-harness/tasks/<slug>.yaml
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from scripts.emit._lib import DIST, by_type, load_catalog, slug_only  # noqa: E402


def map_rubric_to_metrics(rubric: dict | None) -> list[dict]:
    """Turn a hub `rubric/*` manifest into lm-eval metric_list entries."""
    if not rubric:
        return [{"metric": "exact_match", "aggregation": "mean", "higher_is_better": True}]
    out: list[dict] = []
    for dim in rubric.get("dimensions", []) or []:
        out.append({
            "metric":           dim["id"],
            "aggregation":      "mean",
            "higher_is_better": True,
        })
    if rubric.get("scoring_method") == "weighted_sum":
        out.append({"metric": "weighted_rubric_score", "aggregation": "mean", "higher_is_better": True})
    return out or [{"metric": "exact_match", "aggregation": "mean", "higher_is_better": True}]


def render(benchmark: dict, catalog: dict) -> str:
    slug = slug_only(benchmark["id"])
    pipeline = catalog.get(benchmark.get("pipeline", ""), (None, None))[1] if "pipeline" in benchmark else None
    rubric   = catalog.get(benchmark.get("rubric",   ""), (None, None))[1] if "rubric"   in benchmark else None
    dataset  = catalog.get(benchmark.get("dataset",  ""), (None, None))[1] if "dataset"  in benchmark else None

    task: dict = {
        "task":           slug,
        "tag":            sorted(set((benchmark.get("tags") or []) + (benchmark.get("capability") or []))),
        "description":    benchmark.get("description", "").strip(),
        "dataset_path":   f"open-harness-hub/{slug_only(benchmark['dataset'])}" if "dataset" in benchmark else "TODO",
        "dataset_name":   None,
        "output_type":    "generate_until",
        "training_split": "train",
        "validation_split": "val",
        "test_split":     "test",
        "doc_to_text":    "{{prompt}}",            # placeholder; consumer fills in from dataset record schema
        "doc_to_target":  "{{ideal}}",
        "generation_kwargs": {
            "max_gen_toks":  512,
            "temperature":   0.0,
            "top_p":         1.0,
            "until":         ["\n\n"],
        },
        "metric_list":    map_rubric_to_metrics(rubric),
        "num_fewshot":    0,
        "metadata": {
            "version":           benchmark.get("version", "0.0.0"),
            "open_harness_hub_id": benchmark["id"],
            "rubric":            benchmark.get("rubric"),
            "pipeline":          benchmark.get("pipeline"),
            "reproducibility":   benchmark.get("reproducibility", {}),
        },
    }

    if pipeline and pipeline.get("defaults", {}).get("persona"):
        task["doc_to_text"] = f"# Persona: {pipeline['defaults']['persona']}\n\n{{{{prompt}}}}"

    yaml_out = yaml.safe_dump(task, sort_keys=False, allow_unicode=True, width=120)
    header = (
        f"# Auto-generated from Open Harness Hub manifest `{benchmark['id']}` v{benchmark.get('version','0.0.0')}.\n"
        f"# Edit the source manifest at catalog/benchmarks/{slug}.yaml and re-run\n"
        f"# `python scripts/emit/lm_eval_harness.py`.\n"
    )
    return header + yaml_out


def main() -> int:
    catalog = load_catalog()
    out_root = DIST / "lm-eval-harness" / "tasks"
    if out_root.exists():
        shutil.rmtree(out_root)
    out_root.mkdir(parents=True)

    benchmarks = list(by_type(catalog, "benchmark"))
    if not benchmarks:
        print("no `benchmark/*` manifests in the catalog yet; emitting a placeholder.")
        (out_root / ".gitkeep").write_text("")
    n = 0
    for _, m in benchmarks:
        slug = slug_only(m["id"])
        (out_root / f"{slug}.yaml").write_text(render(m, catalog))
        n += 1
    print(f"wrote {n} lm-eval-harness task YAML files to dist/lm-eval-harness/tasks/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
