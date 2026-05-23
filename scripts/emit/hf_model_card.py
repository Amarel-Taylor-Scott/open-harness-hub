#!/usr/bin/env python3
"""Emit Hugging Face Model Cards from every `harness/*` manifest.

HF Model Cards are README.md files with YAML frontmatter following the
spec at https://github.com/huggingface/hub-docs/blob/main/modelcard.md.

Output: dist/hf/model_cards/<slug>/README.md
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from scripts.emit._lib import DIST, by_type, load_catalog, slug_only  # noqa: E402


def hf_pipeline_tag(manifest: dict) -> str | None:
    cap = set(manifest.get("capability", []) or [])
    mod = set(manifest.get("modality", []) or [])
    if "image_synthesis" in cap or ("image" in mod and "generation" in cap):
        return "text-to-image"
    if "audio_synthesis" in cap:
        return "text-to-speech"
    if "translation" in cap:
        return "translation"
    if "summarization" in cap:
        return "summarization"
    if "classification" in cap:
        return "text-classification"
    if "extraction" in cap:
        return "token-classification"
    if "embedding" in cap:
        return "sentence-similarity"
    if "dialogue" in cap or "reasoning" in cap or "generation" in cap:
        return "text-generation"
    return None


def hf_tags(manifest: dict) -> list[str]:
    tags: set[str] = set()
    tags.update(manifest.get("tags", []) or [])
    tags.update(manifest.get("industry", []) or [])
    tags.update(manifest.get("capability", []) or [])
    tags.update(manifest.get("modality", []) or [])
    tags.add("open-harness-hub")
    tags.add(manifest.get("lifecycle", "experimental"))
    return sorted(t for t in tags if t)


def render(manifest: dict) -> str:
    slug = slug_only(manifest["id"])

    front: dict = {
        "license":  manifest.get("license", "MIT"),
        "tags":     hf_tags(manifest),
        "library_name": "open-harness-hub",
    }
    pt = hf_pipeline_tag(manifest)
    if pt:
        front["pipeline_tag"] = pt
    if manifest.get("industry"):
        front["language"] = ["en"]  # default; manifests can override later
        front["region"] = manifest["industry"]

    front_yaml = yaml.safe_dump(front, sort_keys=False, allow_unicode=True).strip()

    body: list[str] = [
        f"---\n{front_yaml}\n---",
        "",
        f"# {manifest.get('name', slug)}",
        "",
        f"<!-- Generated from Open Harness Hub manifest `{manifest['id']}` v{manifest.get('version','0.0.0')}. Do not edit by hand; edit the source manifest and re-run `python scripts/emit/hf_model_card.py`. -->",
        "",
        "## Model description",
        "",
        manifest.get("description", "").strip(),
        "",
    ]

    body.append("## Intended use")
    body.append("")
    body.append("Use this harness as a **wrapping workflow around a model call**. It composes:")
    body.append("")
    for layer in manifest.get("applied_layers", []) or []:
        body.append(f"- `{layer}` layer")
    body.append("")
    body.append("**Industries**: " + ", ".join(manifest.get("industry", []) or ["cross_industry"]))
    body.append("**Capabilities**: " + ", ".join(manifest.get("capability", []) or []))
    body.append("**Modalities**: " + ", ".join(manifest.get("modality", []) or []))
    body.append("**Trust boundary**: " + (manifest.get("trust_boundary") or "—"))

    if manifest.get("logic_paths"):
        body.append("")
        body.append("## How the harness runs")
        body.append("")
        for path in manifest["logic_paths"]:
            body.append(f"### {path.get('label', path['id'])}")
            body.append("")
            for i, step in enumerate(path.get("steps", []) or [], 1):
                body.append(f"{i}. {step}")
            body.append("")

    pb = manifest.get("privacy_boundaries") or {}
    if pb:
        body.append("## Privacy boundaries")
        body.append("")
        for k, v in pb.items():
            body.append(f"- **{k}**: {v}")
        body.append("")

    if manifest.get("model_targets"):
        body.append("## Compatible model targets (provider-neutral)")
        body.append("")
        body.append("| id | transport | trust |")
        body.append("|---|---|---|")
        for m in manifest["model_targets"]:
            body.append(f"| `{m['id']}` | `{m['transport']}` | {m.get('trust_boundary','—')} |")
        body.append("")

    body.append("## Evaluation")
    body.append("")
    body.append(
        "Bench against a hub `benchmark/*` manifest with "
        "`python scripts/emit/lm_eval_harness.py` (emits lm-eval-harness "
        "YAML) or `python scripts/emit/promptfoo.py` (emits promptfoo "
        "config). Both reference the same `rubric/*` and `dataset/*` "
        "manifests."
    )
    body.append("")

    body.append("## Risks & limitations")
    body.append("")
    body.append("This is a workflow harness, not a trained model. Risk profile depends on the model wired in via the configured `model_target`. See the source manifest for `input_verification` and `output_verification` checks.")
    body.append("")

    body.append("## Citation")
    body.append("")
    body.append("```bibtex")
    body.append(f"@misc{{{slug}_open_harness_hub,")
    body.append(f"  title  = {{{manifest.get('name', slug)}}},")
    body.append(f"  author = {{Open Harness Hub contributors}},")
    body.append(f"  url    = {{https://open-harness-hub.dev/{manifest['type']}/{slug}}},")
    body.append(f"  version= {{{manifest.get('version', '0.1.0')}}},")
    body.append(f"  year   = {{2026}}")
    body.append("}")
    body.append("```")
    body.append("")
    body.append(f"License: `{manifest.get('license', 'MIT')}`. Hub artifact: `{manifest['id']}`.")

    return "\n".join(body) + "\n"


def main() -> int:
    catalog = load_catalog()
    out_root = DIST / "hf" / "model_cards"
    if out_root.exists():
        import shutil
        shutil.rmtree(out_root)
    out_root.mkdir(parents=True)
    n = 0
    for _, m in by_type(catalog, "harness"):
        slug = slug_only(m["id"])
        card_dir = out_root / slug
        card_dir.mkdir(parents=True, exist_ok=True)
        (card_dir / "README.md").write_text(render(m))
        n += 1
    print(f"wrote {n} HF model cards to dist/hf/model_cards/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
