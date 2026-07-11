#!/usr/bin/env python3
"""Generate _repos/shared-backend-components/docs/catalog/*.md pages from catalog rows or seed manifests.

Each component gets one page with:
  - title + description
  - cross-cutting axes (industry, capability, modality, etc.)
  - component-type-specific fields
  - graph of refs (consumes / emits / steps / model targets)
  - inline sample-run output if one is committed under _repos/shared-backend-components/catalog/<type>/<slug>/samples/

Usage:
  python _repos/shared-backend-components/scripts/build_catalog_pages.py
  python _repos/shared-backend-components/scripts/build_catalog_pages.py --row-dir dist/catalog-db-export-rows
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
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
CATALOG = _resource("catalog")
DOCS = _resource("docs") / "catalog"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.db.catalog_row_source import iter_components_from_rows, row_source_status


def slug_from_id(component_id: str) -> str:
    return component_id.replace("/", "_")


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


def render_sample_runs(manifest: dict, path: Path | str) -> str:
    """Look for sample-run JSON next to the manifest."""
    if not isinstance(path, Path):
        return ""
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


def render_database_refs(manifest: dict) -> str:
    refs = manifest.get("_database_refs")
    if not isinstance(refs, list) or not refs:
        return ""
    lines = ["| role | target |", "|---|---|"]
    for ref in refs:
        if not isinstance(ref, dict):
            continue
        role = ref.get("role") or ref.get("relation") or "-"
        target = ref.get("target_id") or ref.get("dst_id") or "-"
        lines.append(f"| `{role}` | `{target}` |")
    if len(lines) == 2:
        return ""
    return "\n".join(lines)


def page_body(manifest: dict, path: Path | str) -> str:
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

    if (database_refs := render_database_refs(manifest)):
        parts.extend(["", "## Database references", "", database_refs])

    parts.append("")
    parts.append(render_sample_runs(manifest, path))
    return "\n".join(parts)


def _manifest_paths(paths: list[str]) -> list[Path]:
    if not paths:
        return list(CATALOG.rglob("*.yaml"))
    out: list[Path] = []
    for value in paths:
        path = Path(value)
        if not path.is_absolute():
            path = _resource(path)
        out.append(path)
    return out


def _load_page_manifests(paths: list[Path]) -> list[tuple[Path, dict]]:
    manifests: list[tuple[Path, dict]] = []
    for path in paths:
        if not path.exists():
            raise FileNotFoundError(path)
        if "_inbox" in path.parts:
            continue
        if any(p == "data" for p in path.parts):
            continue
        data = yaml.safe_load(path.read_text())
        if not isinstance(data, dict) or "type" not in data or "id" not in data:
            continue
        manifests.append((path, data))
    return manifests


def _load_page_manifests_from_rows(row_dir: Path) -> list[tuple[str, dict]]:
    manifests: list[tuple[str, dict]] = []
    for component in iter_components_from_rows(row_dir):
        manifest = dict(component.manifest)
        manifest["_database_refs"] = component.database_refs
        manifests.append((component.source_path, manifest))
    return manifests


def _write_pages(manifests: list[tuple[Path | str, dict]]) -> list[tuple[str, str]]:
    pages: list[tuple[str, str]] = []
    for path, data in manifests:
        slug = slug_from_id(data["id"])
        out = DOCS / f"{slug}.md"
        out.write_text(page_body(data, path))
        pages.append((data["type"], data["id"]))
    return pages


def _render_row_source_status(status: dict[str, Any] | None) -> list[str]:
    if not status:
        return []
    fields = [
        ("kind", "Kind"),
        ("promotion_status", "Promotion status"),
        ("promotion_ready", "Promotion ready"),
        ("staleness_status", "Staleness status"),
        ("staleness_would_pass", "Staleness gate would pass"),
        ("integrity_ok", "Integrity ok"),
        ("integrity_warning_count", "Integrity warnings"),
    ]
    lines = [
        "## Row source status",
        "",
        "This generated index was built from database-shaped catalog rows.",
        "",
        "| field | value |",
        "|---|---|",
    ]
    for key, label in fields:
        value = status.get(key)
        lines.append(f"| {label} | `{value}` |")
    row_dir = status.get("row_dir")
    if row_dir:
        lines.append(f"| Row directory | `{row_dir}` |")
    return lines + [""]


def _write_index(pages: list[tuple[str, str]], *, row_status: dict[str, Any] | None = None) -> None:
    by_type: dict[str, list[str]] = {}
    for t, i in pages:
        by_type.setdefault(t, []).append(i)
    _write_index_from_map(by_type, row_status=row_status)


def _write_index_from_map(by_type: dict[str, list[str]], *, row_status: dict[str, Any] | None = None) -> None:
    lines = ["# Catalog index", ""]
    lines.extend(_render_row_source_status(row_status))
    for t in sorted(by_type):
        lines.append(f"## {t}")
        for i in sorted(set(by_type[t])):
            slug = slug_from_id(i)
            lines.append(f"- [`{i}`]({slug}.md)")
        lines.append("")
    (DOCS / "index.md").write_text("\n".join(lines))


def _display_output_dir() -> str:
    try:
        return str(DOCS.relative_to(ROOT))
    except ValueError:
        return str(DOCS)


def _read_index_map() -> dict[str, list[str]]:
    index_path = DOCS / "index.md"
    if not index_path.exists():
        return {}

    by_type: dict[str, list[str]] = {}
    current_type: str | None = None
    for raw_line in index_path.read_text().splitlines():
        line = raw_line.strip()
        if line.startswith("## "):
            current_type = line.removeprefix("## ").strip()
            by_type.setdefault(current_type, [])
            continue
        if current_type is None or not line.startswith("- [`"):
            continue
        try:
            component_id = line.split("`", 2)[1]
        except IndexError:
            continue
        by_type.setdefault(current_type, []).append(component_id)
    return by_type


def _update_index(pages: list[tuple[str, str]]) -> None:
    by_type = _read_index_map()
    for component_type, component_id in pages:
        by_type.setdefault(component_type, []).append(component_id)
    _write_index_from_map(by_type)


def main(argv: list[str] | None = None) -> int:
    global DOCS
    parser = argparse.ArgumentParser(description="Generate docs/catalog/*.md pages from database rows or catalog manifests.")
    parser.add_argument(
        "--paths",
        nargs="*",
        default=[],
        help="Optional manifest paths to render. Defaults to every manifest under catalog/.",
    )
    parser.add_argument(
        "--skip-index",
        action="store_true",
        help="Only render selected pages and leave docs/catalog/index.md unchanged.",
    )
    parser.add_argument(
        "--update-index",
        action="store_true",
        help="Merge selected pages into docs/catalog/index.md without scanning the whole catalog.",
    )
    parser.add_argument(
        "--row-dir",
        help="Read database-shaped JSONL row sets from this directory instead of walking catalog YAML.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DOCS,
        help="Directory for generated catalog pages. Defaults to docs/catalog.",
    )
    args = parser.parse_args(argv)

    if args.skip_index and args.update_index:
        parser.error("--skip-index and --update-index cannot be used together")
    if args.update_index and not args.paths:
        parser.error("--update-index requires --paths")
    if args.row_dir and args.paths:
        parser.error("--row-dir cannot be combined with --paths")

    DOCS = args.output_dir if args.output_dir.is_absolute() else _resource(args.output_dir)
    DOCS.mkdir(parents=True, exist_ok=True)

    if args.row_dir:
        row_dir = Path(args.row_dir)
        manifests = _load_page_manifests_from_rows(row_dir)
        row_status = row_source_status(row_dir)
    else:
        paths = _manifest_paths(args.paths)
        manifests = _load_page_manifests(paths)
        row_status = None
    pages = _write_pages(manifests)
    output_dir = _display_output_dir()
    if args.paths and args.skip_index:
        print(f"wrote {len(pages)} selected catalog pages to {output_dir}/ (index unchanged)")
    elif args.paths and args.update_index:
        _update_index(pages)
        print(f"wrote {len(pages)} selected catalog pages to {output_dir}/ (index updated incrementally)")
    else:
        if args.paths:
            all_manifests = _load_page_manifests(_manifest_paths([]))
            _write_index([(data["type"], data["id"]) for _, data in all_manifests])
        else:
            _write_index(pages, row_status=row_status)
        print(f"wrote {len(pages)} catalog pages + index to {output_dir}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
