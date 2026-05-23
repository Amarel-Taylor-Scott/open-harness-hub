#!/usr/bin/env python3
"""Generate docs/catalog/*.md pages from every manifest in catalog/.

Each artifact gets one page with:
  - title + description
  - cross-cutting axes (industry, capability, modality, etc.)
  - artifact-type-specific fields
  - graph of refs (consumes / emits / steps / model targets)
  - inline sample-run output if one is committed under catalog/<type>/<slug>/samples/

Usage:
  python scripts/build_catalog_pages.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from textwrap import dedent
from typing import Any

try:
    import yaml
except ImportError:
    sys.stderr.write("pyyaml is required: pip install pyyaml\n")
    sys.exit(2)

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "catalog"
DOCS = ROOT / "docs" / "catalog"


def slug_from_id(artifact_id: str) -> str:
    return artifact_id.replace("/", "_")


def render_axes(manifest: dict) -> str:
    rows = []
    for key in ["industry", "capability", "modality", "lifecycle", "trust_boundary", "freshness", "license"]:
        v = manifest.get(key)
        if v is None:
            continue
        if isinstance(v, list):
            v = ", ".join(v) if v else "-"
        rows.append(f"| {key} | {v} |")
    if not rows:
        return ""
    return "| axis | value |\n|---|---|\n" + "\n".join(rows)


def render_refs(manifest: dict) -> str:
    lines: list[str] = []
    for key, label in [("consumes", "Consumes"), ("emits", "Emits"), ("contributes_to", "Contributes to")]:
        vals = manifest.get(key)
        if vals:
            lines.append(f"**{label}:** " + ", ".join(f"`{v}`" for v in vals))
    return "\n\n".join(lines)


def render_steps(manifest: dict) -> str:
    steps = manifest.get("steps")
    if not steps:
        return ""
    out = ["| # | id | kind | ref | when |", "|---|---|---|---|---|"]
    for i, step in enumerate(steps, 1):
        when = step.get("when", "-")
        out.append(f"| {i} | `{step['id']}` | {step['kind']} | `{step['ref']}` | {when} |")
    return "\n".join(out)


def render_logic_paths(manifest: dict) -> str:
    paths = manifest.get("logic_paths")
    if not paths:
        return ""
    parts: list[str] = []
    for path in paths:
        parts.append(f"### {path['label']}  \n*model_call: `{path.get('model_call', 'n/a')}`*")
        if path.get("steps"):
            parts.append("\n".join(f"1. {s}" for s in path["steps"]))
        if path.get("consumes"):
            parts.append("**consumes:** " + ", ".join(f"`{t}`" for t in path["consumes"]))
        if path.get("emits"):
            parts.append("**emits:** " + ", ".join(f"`{t}`" for t in path["emits"]))
        if path.get("verification"):
            parts.append("**verification:** " + ", ".join(path["verification"]))
        parts.append("")
    return "\n\n".join(parts)


def render_model_targets(manifest: dict) -> str:
    mts = manifest.get("model_targets")
    if not mts:
        return ""
    out = ["| id | transport | trust | required | default |", "|---|---|---|---|---|"]
    for m in mts:
        out.append(
            f"| `{m['id']}` | `{m['transport']}` | {m.get('trust_boundary', '-')} | "
            f"{m.get('required', False)} | {m.get('default', False)} |"
        )
    return "\n".join(out)


def render_rules(manifest: dict) -> str:
    rules = manifest.get("rules")
    if not rules:
        return ""
    out = ["| id | severity | category | pattern/condition |", "|---|---|---|---|"]
    for r in rules:
        pat = r.get("pattern") or r.get("condition") or ""
        if len(pat) > 80:
            pat = pat[:77] + "..."
        out.append(f"| `{r['id']}` | {r.get('severity','-')} | {r.get('category','-')} | `{pat}` |")
    return "\n".join(out)


def render_sample_runs(manifest: dict, path: Path) -> str:
    """Look for sample-run JSON next to the manifest."""
    samples_dir = path.parent / "samples"
    if not samples_dir.exists():
        return ""
    out: list[str] = ["## Sample runs", ""]
    for sample in sorted(samples_dir.glob("*.json")):
        out.append(f"### {sample.stem}")
        data = json.loads(sample.read_text())
        out.append("```json")
        out.append(json.dumps(data, indent=2))
        out.append("```")
    if len(out) == 2:
        return ""
    return "\n".join(out)


def page_body(manifest: dict, path: Path) -> str:
    parts = [
        f"# {manifest['name']}",
        "",
        f"*{manifest['type']}* · `{manifest['id']}` · v{manifest['version']} · {manifest['lifecycle']}",
        "",
        manifest["description"].strip(),
        "",
        render_axes(manifest),
        "",
        render_refs(manifest),
    ]

    if manifest["type"] == "harness":
        if (mt := render_model_targets(manifest)):
            parts.extend(["", "## Model targets", "", mt])
        if (lp := render_logic_paths(manifest)):
            parts.extend(["", "## Logic paths", "", lp])
        pb = manifest.get("privacy_boundaries")
        if pb:
            parts.extend(["", "## Privacy boundaries", "",
                          "\n".join(f"- **{k}**: {v}" for k, v in pb.items())])

    if manifest["type"] == "pipeline":
        parts.extend(["", "## Task", "", manifest["task"].strip()])
        parts.extend(["", f"**pipeline_kind:** `{manifest.get('pipeline_kind','-')}`"])
        if (steps := render_steps(manifest)):
            parts.extend(["", "## Steps", "", steps])

    if manifest["type"] == "rule-pack":
        parts.extend(["", f"**family:** `{manifest.get('family')}`"])
        if (rules := render_rules(manifest)):
            parts.extend(["", "## Rules", "", rules])

    parts.append("")
    parts.append(render_sample_runs(manifest, path))
    return "\n".join(parts)


def main() -> int:
    DOCS.mkdir(parents=True, exist_ok=True)

    pages: list[tuple[str, str]] = []
    for path in CATALOG.rglob("*.yaml"):
        if "_inbox" in path.parts:
            continue
        if any(p == "data" for p in path.parts):
            continue
        data = yaml.safe_load(path.read_text())
        if not isinstance(data, dict) or "type" not in data or "id" not in data:
            continue
        slug = slug_from_id(data["id"])
        out = DOCS / f"{slug}.md"
        out.write_text(page_body(data, path))
        pages.append((data["type"], data["id"]))

    # Build an index page grouped by type.
    by_type: dict[str, list[str]] = {}
    for t, i in pages:
        by_type.setdefault(t, []).append(i)
    lines = ["# Catalog index", ""]
    for t in sorted(by_type):
        lines.append(f"## {t}")
        for i in sorted(by_type[t]):
            slug = slug_from_id(i)
            lines.append(f"- [`{i}`]({slug}.md)")
        lines.append("")
    (DOCS / "index.md").write_text("\n".join(lines))

    print(f"wrote {len(pages)} catalog pages + index to docs/catalog/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
