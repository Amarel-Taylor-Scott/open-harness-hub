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

#: The emitted config lives at dist/promptfoo/<slug>.promptfooconfig.yaml; the dataset split paths
#: are repo-relative (e.g. data/<x>/samples/). promptfoo resolves file:// against the config's own
#: directory, so reach the repo root with two ".." hops. Single constant, not a literal per call.
_CONFIG_TO_REPO = "../../"


def _resolve_dataset(benchmark: dict, catalog: dict) -> dict | None:
    """The dataset manifest a benchmark binds, if any (mirrors how rubric is resolved)."""
    ref = benchmark.get("dataset")
    if not isinstance(ref, str) or not ref:
        return None
    entry = catalog.get(ref)
    return entry[1] if entry else None


def _dataset_split(dataset: dict) -> tuple[str | None, int, str | None]:
    """Pick the eval split (prefer `test`) → (path, declared_row_count, split_name)."""
    splits = dataset.get("splits", {}) or {}
    name = "test" if "test" in splits else next(iter(splits), None)
    if not name:
        return None, 0, None
    split = splits.get(name) or {}
    return split.get("path"), int(split.get("rows", 0) or 0), name


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

    # Bind tests to the dataset's eval split via promptfoo's native file loader — one test per real
    # row, never a fabricated placeholder. If no dataset is bound (or it declares no split), emit an
    # HONEST single schema smoke test, clearly labelled as not-a-benchmark-run.
    dataset = _resolve_dataset(benchmark, catalog)
    ds_path, ds_rows, ds_split = _dataset_split(dataset) if dataset else (None, 0, None)
    if ds_path:
        tests: object = f"file://{_CONFIG_TO_REPO}{ds_path.rstrip('/')}/*.json"
    else:
        tests = [{
            "description": "No dataset bound — schema smoke test only (not a scored benchmark run).",
            "vars": {"prompt": "Return a JSON object that satisfies the benchmark output schema."},
        }]

    config: dict = {
        "description": benchmark.get("description", "").strip(),
        "prompts":     ["{{prompt}}"],
        "providers":   providers,
        "defaultTest": {"assert": asserts},
        "tests":       tests,
        "outputPath":  f"./reports/{slug}.json",
        "writeLatestResults": True,
        "metadata": {
            "open_harness_hub_id":  benchmark["id"],
            "version":              benchmark.get("version", "0.0.0"),
            "headline_metric":      benchmark.get("headline_metric"),
            "reproducibility":      benchmark.get("reproducibility", {}),
            "dataset":              dataset["id"] if dataset else None,
            "dataset_split":        ds_split,
            "dataset_rows":         ds_rows,
        },
    }

    yaml_out = yaml.safe_dump(config, sort_keys=False, allow_unicode=True, width=120)
    header = (
        f"# Auto-generated from Open Harness Hub `{benchmark['id']}` "
        f"v{benchmark.get('version','0.0.0')}.\n"
        f"# Re-run `python scripts/emit/promptfoo.py` after editing the source manifest.\n"
    )
    return header + yaml_out


def _self_test() -> int:
    # A benchmark that binds a dataset → tests load from the split path (real rows, no placeholder).
    cat = {
        "dataset/demo-samples": (None, {"id": "dataset/demo-samples", "type": "dataset",
                                        "splits": {"test": {"rows": 12, "path": "data/demo/samples/"}}}),
    }
    bench = {"id": "benchmark/demo", "version": "1.0.0", "dataset": "dataset/demo-samples",
             "description": "demo", "model_arms": [{"label": "bare"}]}
    out = render(bench, cat)
    assert "TODO" not in out, "placeholder row leaked into the emitted config"
    assert "file://../../data/demo/samples/*.json" in out, out
    assert "dataset_rows: 12" in out and "dataset_split: test" in out, out
    # A benchmark with NO dataset → an honest smoke test, still no TODO.
    nods = render({"id": "benchmark/x", "version": "1.0.0", "model_arms": [{"label": "bare"}]}, {})
    assert "TODO" not in nods and "schema smoke test only" in nods, nods
    assert "dataset: null" in nods
    # Deterministic.
    assert render(bench, cat) == render(bench, cat)
    print("PASS — emit/promptfoo: benchmark.dataset → promptfoo tests bound to the split path via "
          "file:// (real rows, never a TODO placeholder); unbound benchmark → honest schema smoke "
          "test; dataset id/split/rows in metadata; deterministic")
    return 0


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    if "--self-test" in argv:
        return _self_test()
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
