#!/usr/bin/env python3
"""Emit Hugging Face Dataset Cards from every `dataset/*` and
`knowledge-pack/*` manifest.

Spec: https://github.com/huggingface/hub-docs/blob/main/datasetcard.md
Output: dist/hf/dataset_cards/<slug>/README.md
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from scripts.emit._lib import DIST, by_type, load_catalog, slug_only  # noqa: E402


def task_categories(manifest: dict) -> list[str]:
    cap = set(manifest.get("capability", []) or [])
    out: list[str] = []
    if "classification" in cap:    out.append("text-classification")
    if "retrieval" in cap:         out.append("text-retrieval")
    if "extraction" in cap:        out.append("token-classification")
    if "summarization" in cap:     out.append("summarization")
    if "verification" in cap:      out.append("text-classification")
    if "evaluation" in cap:        out.append("text-classification")
    if "embedding" in cap:         out.append("sentence-similarity")
    if "translation" in cap:       out.append("translation")
    if "image_synthesis" in cap:   out.append("text-to-image")
    return sorted(set(out))


def size_category(file_count_lines: int) -> str:
    if file_count_lines < 1_000:     return "n<1K"
    if file_count_lines < 10_000:    return "1K<n<10K"
    if file_count_lines < 100_000:   return "10K<n<100K"
    if file_count_lines < 1_000_000: return "100K<n<1M"
    return "n>1M"


def estimate_size(manifest_path: Path, files: list[dict]) -> int:
    total = 0
    for f in files or []:
        p = manifest_path.parent / f["path"]
        if not p.exists():
            continue
        if p.suffix.lower() == ".jsonl":
            total += sum(1 for _ in p.read_text(errors="ignore").splitlines() if _.strip())
        else:
            total += 1
    return total


def render(manifest: dict, manifest_path: Path) -> str:
    slug = slug_only(manifest["id"])
    files = manifest.get("files", []) or []
    nrows = estimate_size(manifest_path, files)

    front: dict = {
        "license":          manifest.get("license", "MIT"),
        "tags":             sorted(set(
            (manifest.get("tags") or [])
            + (manifest.get("industry") or [])
            + (manifest.get("capability") or [])
            + ["open-harness-hub"]
            + [manifest.get("lifecycle", "experimental")]
        )),
        "task_categories":  task_categories(manifest),
        "size_categories":  [size_category(nrows)],
        "language":         ["en"],
        "pretty_name":      manifest.get("name", slug),
    }

    front_yaml = yaml.safe_dump(front, sort_keys=False, allow_unicode=True).strip()

    body: list[str] = [
        f"---\n{front_yaml}\n---",
        "",
        f"# {manifest.get('name', slug)}",
        "",
        f"<!-- Generated from Open Harness Hub manifest `{manifest['id']}` v{manifest.get('version','0.0.0')}. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->",
        "",
        "## Dataset description",
        "",
        manifest.get("description", "").strip(),
        "",
        "**Industries**: " + ", ".join(manifest.get("industry") or ["cross_industry"]),
        "**Capabilities**: " + ", ".join(manifest.get("capability") or []),
        "**Modalities**: " + ", ".join(manifest.get("modality") or []),
        "**Freshness**: " + (manifest.get("freshness") or "—"),
        "**Trust boundary**: " + (manifest.get("trust_boundary") or "—"),
        "",
    ]

    if manifest.get("content_types"):
        body.append("## Content types (leaf vocabulary)")
        body.append("")
        for ct in manifest["content_types"]:
            body.append(f"- `{ct}`")
        body.append("")

    if files:
        body.append("## Files")
        body.append("")
        body.append("| path | format | schema |")
        body.append("|---|---|---|")
        for f in files:
            body.append(f"| `{f['path']}` | {f.get('format', '—')} | {f.get('schema', '—')} |")
        body.append("")

    prov = manifest.get("provenance") or {}
    if prov:
        body.append("## Provenance")
        body.append("")
        for k, v in prov.items():
            if isinstance(v, list):
                v = ", ".join(str(x) for x in v)
            body.append(f"- **{k}**: {v}")
        body.append("")

    body.append("## Croissant")
    body.append("")
    body.append(
        f"A Croissant 1.0 JSON-LD record is emitted at "
        f"`dist/croissant/{slug}.croissant.json`. HF, Kaggle, and "
        "Google Dataset Search index this format automatically."
    )
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
    out_root = DIST / "hf" / "dataset_cards"
    if out_root.exists():
        shutil.rmtree(out_root)
    out_root.mkdir(parents=True)
    n = 0
    for path, m in list(by_type(catalog, "dataset")) + list(by_type(catalog, "knowledge-pack")):
        slug = slug_only(m["id"])
        card_dir = out_root / slug
        card_dir.mkdir(parents=True, exist_ok=True)
        (card_dir / "README.md").write_text(render(m, path))
        n += 1
    print(f"wrote {n} HF dataset cards to dist/hf/dataset_cards/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
