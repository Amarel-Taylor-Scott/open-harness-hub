"""Shared, standardized component-seed builder.

ONE builder so every taxonomy-seeded component has a consistent shape AND consistent
ATTRIBUTION (the source taxonomy/spec it was generated from, the generator, the license) — and
validates against schemas/processor.schema.json. Per-bucket seed scripts (retrieval · clinical ·
deliver · platform) define specs and call `processor()` + `write_batch()`.

Attribution is recorded in the schema's standard `attribution` block (source_kind="manual" — these
are spec-level components authored in-repo from a taxonomy, not mined externally) + a `links.source`
pointer to the spec doc, so each component is traceable to where it came from. Honest lifecycle:
"experimental" — these are validated DEFINITIONS; implementing + lift-measuring promotes them.
"""
from __future__ import annotations

from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
STD_AUTHOR = "OpenHubForAI contributors"
STD_DATE = "2026-05-29"


def processor(slug: str, name: str, process_kind: str, capability: list[str], deterministic: bool,
              side_effects: str, inputs: list[str], outputs: list[str], description: str, *,
              industry: tuple = ("cross_industry",), modality: tuple = ("text", "structured"),
              tags: tuple = (), source_doc: str | None = None, source_label: str | None = None,
              impl_prefix: str = "scripts.processors", lifecycle: str = "experimental") -> dict:
    """Build one schema-valid `processor` component with standardized attribution."""
    comp = {
        "id": f"processor/{slug}",
        "type": "processor",
        "version": "0.1.0",
        "name": name,
        "description": description,
        "authors": [{"name": STD_AUTHOR}],
        "license": "MIT",
        "industry": list(industry),
        "capability": list(capability),
        "modality": list(modality),
        "lifecycle": lifecycle,
        "trust_boundary": "local",
        "tags": list(tags),
        "created": STD_DATE,
        "updated": STD_DATE,
        # standardized provenance: spec-level, authored in-repo from a named taxonomy/spec
        "attribution": {"source_kind": "manual", "author": source_label or "OpenHubForAI taxonomy", "license": "MIT"},
        "process_kind": process_kind,
        "deterministic": deterministic,
        "idempotent": True,
        "streaming": False,
        "inputs": [{"name": n, "type": "object"} for n in inputs],
        "outputs": [{"name": n, "type": "object"} for n in outputs],
        "side_effects": side_effects,
        "on_error": "raise",
        "implementations": [{"kind": "callable", "path": f"{impl_prefix}.{slug.replace('-', '_')}.run", "language": "python"}],
    }
    if source_doc:
        comp["links"] = {"source": source_doc}
    return comp


def write_batch(out_dir: str, comps: list[dict]) -> list[str]:
    """Write each component YAML under `out_dir` (repo-relative). Returns the written paths."""
    out = REPO / out_dir
    out.mkdir(parents=True, exist_ok=True)
    paths = []
    for c in comps:
        dest = out / (c["id"].split("/")[-1] + ".yaml")
        dest.write_text(yaml.safe_dump(c, sort_keys=False, allow_unicode=True, width=100), encoding="utf-8")
        paths.append(str(dest.relative_to(REPO)))
    return paths
