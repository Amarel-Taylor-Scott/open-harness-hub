#!/usr/bin/env python3
"""Build a single hierarchical, faceted index of every artifact and write
it to docs/catalog/index.json so the static catalog browser can load it.

Each row in the output is:

  {
    "id": "harness/text-safety-review",
    "type": "harness",
    "name": "Text Safety Review",
    "description": "...",
    "industry":  [...],
    "capability":[...],
    "modality":  [...],
    "lifecycle": "beta",
    "lifecycle_position": "api.model_call",   # derived if not declared
    "trust_boundary": "local",
    "tags":      [...],
    "applied_layers": [...],     # for harnesses
    "family": "...",             # for rule-packs
    "consumes": [...],
    "emits":    [...],
    "step_refs":[...],           # for pipelines
    "links": {...},
    "path": "catalog/harnesses/text-safety-review.yaml"
  }

Output also includes:
  - `_meta`: counts grouped by lifecycle stage, by type, by industry.
  - `_tree`: hierarchical lifecycle → type → industry → artifact ids.
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    sys.stderr.write("pyyaml is required: pip install pyyaml\n")
    sys.exit(2)

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "catalog"
OUT = ROOT / "docs" / "catalog" / "index.json"


def derive_position(manifest: dict) -> str:
    """Derive lifecycle_position from type + family + name when not declared."""
    type_ = manifest.get("type", "")
    name = manifest.get("id", "").split("/", 1)[-1].lower()

    if type_ == "pipeline":
        return "cross_cutting.composition"
    if type_ == "benchmark":
        return "cross_cutting.evaluation"
    if type_ in ("dataset", "schema"):
        return "cross_cutting.data"
    if type_ == "adapter":
        return "api.model_call"
    if type_ == "tool":
        return "api.tool_call"
    if type_ == "persona":
        return "pre_api.context_assembly"
    if type_ == "rubric":
        return "post_api.evaluation"
    if type_ in ("knowledge-pack", "logic-pack"):
        return "pre_api.context_assembly"
    if type_ == "rule-pack":
        family = manifest.get("family", "")
        if family in ("privacy", "schema"):
            return "pre_api.input_gating"
        if family == "grep":
            return "post_api.output_safety" if "output" in name else "pre_api.input_gating"
        if family == "glob":
            return "pre_api.input_gating"
        if family == "classifier":
            return "pre_api.classification"
        if family == "heuristic":
            return "post_api.output_safety" if "output" in name else "pre_api.input_gating"
        if family in ("rag", "citation"):
            return "pre_api.context_assembly"
        if family == "online_search":
            return "pre_api.query_sanitization"
        if family == "routing":
            return "pre_api.classification"
        return "pre_api.input_gating"
    if type_ == "harness":
        kind = manifest.get("kind", "model_harness")
        if kind == "safety_gate":
            return "post_api.output_safety" if "output" in name else "pre_api.input_gating"
        if kind == "utility_surface":
            return "cross_cutting.composition"
        return "api.model_call"
    return "cross_cutting"


def step_refs(manifest: dict) -> list[str]:
    refs = []
    for step in manifest.get("steps", []) or []:
        ref = step.get("ref")
        if ref and not ref.startswith("$."):
            refs.append(ref)
    return refs


def main() -> int:
    rows: list[dict[str, Any]] = []
    for path in CATALOG.rglob("*.yaml"):
        if "_inbox" in path.parts or any(p == "data" for p in path.parts):
            continue
        try:
            m = yaml.safe_load(path.read_text())
        except yaml.YAMLError:
            continue
        if not isinstance(m, dict) or "type" not in m or "id" not in m:
            continue

        position = m.get("lifecycle_position") or derive_position(m)
        stage = position.split(".", 1)[0]

        rows.append({
            "id":          m["id"],
            "type":        m["type"],
            "name":        m.get("name", m["id"]),
            "description": (m.get("description") or "").strip(),
            "version":     m.get("version", ""),
            "industry":    m.get("industry", []) or [],
            "capability":  m.get("capability", []) or [],
            "modality":    m.get("modality", []) or [],
            "lifecycle":   m.get("lifecycle", "experimental"),
            "lifecycle_position": position,
            "lifecycle_stage":    stage,
            "trust_boundary":     m.get("trust_boundary"),
            "tags":               m.get("tags", []) or [],
            "applied_layers":     m.get("applied_layers", []) or [],
            "family":             m.get("family"),
            "pipeline_kind":      m.get("pipeline_kind"),
            "consumes":           m.get("consumes", []) or [],
            "emits":              m.get("emits", []) or [],
            "step_refs":          step_refs(m),
            "links":              m.get("links", {}) or {},
            "path":               str(path.relative_to(ROOT)),
        })

    rows.sort(key=lambda r: (r["lifecycle_stage"], r["type"], r["id"]))

    # Build aggregates.
    by_stage: dict[str, int]      = defaultdict(int)
    by_position: dict[str, int]   = defaultdict(int)
    by_type: dict[str, int]       = defaultdict(int)
    by_industry: dict[str, int]   = defaultdict(int)
    by_capability: dict[str, int] = defaultdict(int)
    by_modality: dict[str, int]   = defaultdict(int)
    by_lifecycle: dict[str, int]  = defaultdict(int)
    for r in rows:
        by_stage[r["lifecycle_stage"]] += 1
        by_position[r["lifecycle_position"]] += 1
        by_type[r["type"]] += 1
        for ind in r["industry"]:
            by_industry[ind] += 1
        for cap in r["capability"]:
            by_capability[cap] += 1
        for mod in r["modality"]:
            by_modality[mod] += 1
        by_lifecycle[r["lifecycle"]] += 1

    # Build hierarchical tree: stage → position → type → industry → [ids]
    tree: dict[str, Any] = {}
    for r in rows:
        stage = r["lifecycle_stage"]
        position = r["lifecycle_position"]
        type_ = r["type"]
        inds = r["industry"] or ["cross_industry"]
        for ind in inds:
            tree.setdefault(stage, {}) \
                .setdefault(position, {}) \
                .setdefault(type_, {}) \
                .setdefault(ind, []) \
                .append(r["id"])

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "_version": "0.1.0",
        "_meta": {
            "by_stage":      dict(sorted(by_stage.items())),
            "by_position":   dict(sorted(by_position.items())),
            "by_type":       dict(sorted(by_type.items())),
            "by_industry":   dict(sorted(by_industry.items())),
            "by_capability": dict(sorted(by_capability.items())),
            "by_modality":   dict(sorted(by_modality.items())),
            "by_lifecycle":  dict(sorted(by_lifecycle.items())),
            "total":         len(rows),
        },
        "_tree": tree,
        "rows":  rows,
    }, indent=2))
    print(f"wrote {OUT.relative_to(ROOT)} — {len(rows)} artifacts")
    print(f"  by stage:     {dict(sorted(by_stage.items()))}")
    print(f"  by type:      {dict(sorted(by_type.items()))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
