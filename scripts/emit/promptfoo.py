#!/usr/bin/env python3
"""Emit promptfoo config (promptfooconfig.yaml) for every `benchmark/*`.

Spec: https://www.promptfoo.dev/docs/configuration/guide
Maps:
  benchmark.model_arms → providers[]
  benchmark.dataset    → tests[].vars (one test per dataset row)
  benchmark.rubric     → defaultTest.assert[]  (one per dimension)

Output: dist/promptfoo/<slug>.promptfooconfig.yaml
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from scripts.emit._lib import DIST, by_type, load_catalog, slug_only  # noqa: E402


PROVIDER_BY_TRANSPORT = {
    "ollama":               "ollama",
    "openai_compatible":    "openai:chat",
    "anthropic":            "anthropic:messages",
    "google_gemini":        "google",
    "hf_inference_endpoint":"huggingface",
    "transformers":         "huggingface",
    "callable":             "exec",
    "none":                 "echo",
}


def render(benchmark: dict, catalog: dict) -> str:
    slug = slug_only(benchmark["id"])
    rubric = catalog.get(benchmark.get("rubric", ""), (None, None))[1] if "rubric" in benchmark else None

    providers: list[dict] = []
    for arm in benchmark.get("model_arms", []) or []:
        adapter = catalog.get(arm.get("adapter_ref", ""), (None, None))[1]
        if adapter:
            transport = adapter.get("transport", "openai_compatible")
            provider_id = PROVIDER_BY_TRANSPORT.get(transport, "openai:chat")
            model = adapter.get("default_model") or arm["label"]
            providers.append({
                "id":    f"{provider_id}:{model}",
                "label": arm["label"],
                "config": {
                    "apiBaseUrl": adapter.get("endpoint"),
                },
            })
        else:
            providers.append({"id": f"openai:chat:{arm['label']}", "label": arm["label"]})

    asserts: list[dict] = []
    if rubric:
        for dim in rubric.get("dimensions", []) or []:
            # promptfoo built-ins: contains-json, javascript, llm-rubric, similar, etc.
            asserts.append({
                "type":   "llm-rubric",
                "value":  f"{dim['label']}. {dim.get('evidence_required', '')}".strip(),
                "metric": dim["id"],
                "weight": dim.get("weight", 1.0),
            })
    if not asserts:
        asserts.append({"type": "contains-json"})

    config: dict = {
        "description": benchmark.get("description", "").strip(),
        "prompts":     ["{{prompt}}"],
        "providers":   providers,
        "defaultTest": {"assert": asserts},
        "tests":       [
            {
                "description": f"Sample row 0 from {benchmark.get('dataset','dataset')}",
                "vars":        {"prompt": "TODO: replace with rows from dataset"},
            }
        ],
        "outputPath":  f"./reports/{slug}.json",
        "writeLatestResults": True,
        "metadata": {
            "open_harness_hub_id":  benchmark["id"],
            "version":              benchmark.get("version", "0.0.0"),
            "headline_metric":      benchmark.get("headline_metric"),
            "reproducibility":      benchmark.get("reproducibility", {}),
        },
    }

    yaml_out = yaml.safe_dump(config, sort_keys=False, allow_unicode=True, width=120)
    header = (
        f"# Auto-generated from Open Harness Hub `{benchmark['id']}` "
        f"v{benchmark.get('version','0.0.0')}.\n"
        f"# Re-run `python scripts/emit/promptfoo.py` after editing the source manifest.\n"
    )
    return header + yaml_out


def main() -> int:
    catalog = load_catalog()
    out_dir = DIST / "promptfoo"
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)

    benchmarks = list(by_type(catalog, "benchmark"))
    if not benchmarks:
        print("no `benchmark/*` manifests yet; emitting a placeholder.")
        (out_dir / ".gitkeep").write_text("")
    n = 0
    for _, m in benchmarks:
        slug = slug_only(m["id"])
        (out_dir / f"{slug}.promptfooconfig.yaml").write_text(render(m, catalog))
        n += 1
    print(f"wrote {n} promptfoo configs to dist/promptfoo/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
