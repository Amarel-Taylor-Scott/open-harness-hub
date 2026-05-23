#!/usr/bin/env python3
"""Emit OpenLineage v2 event templates for every pipeline.

Spec: https://openlineage.io/docs/spec/object-model
Each pipeline produces one COMPLETE event template with inputs/outputs
populated from the pipeline's dataset / knowledge-pack refs. The real
runtime emits START / COMPLETE / FAIL variants with concrete run_ids.

Output: dist/openlineage/<pipeline-slug>.event.json
"""
from __future__ import annotations

import datetime
import json
import shutil
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from scripts.emit._lib import DIST, by_type, load_catalog, slug_only  # noqa: E402

NAMESPACE = "open-harness-hub"


def dataset_facets(manifest: dict) -> dict:
    return {
        "schema": {
            "_producer":     "https://open-harness-hub.dev",
            "_schemaURL":    "https://openlineage.io/spec/facets/1-1-0/SchemaDatasetFacet.json",
            "fields": [{"name": ct, "type": "string"} for ct in (manifest.get("content_types") or [])],
        },
        "documentation": {
            "_producer":     "https://open-harness-hub.dev",
            "_schemaURL":    "https://openlineage.io/spec/facets/1-0-0/DocumentationDatasetFacet.json",
            "description":   manifest.get("description", "").strip(),
        },
        "dataSource": {
            "_producer":   "https://open-harness-hub.dev",
            "_schemaURL":  "https://openlineage.io/spec/facets/1-0-0/DatasourceDatasetFacet.json",
            "name":        NAMESPACE,
            "uri":         f"https://open-harness-hub.dev/{manifest['type']}/{slug_only(manifest['id'])}",
        },
    }


def render(pipeline: dict, catalog: dict) -> dict:
    slug = slug_only(pipeline["id"])

    inputs: list[dict] = []
    seen: set[str] = set()
    for step in pipeline.get("steps", []) or []:
        ref = step.get("ref")
        if not ref or ref.startswith("$.") or ref in seen:
            continue
        seen.add(ref)
        artifact = catalog.get(ref)
        if not artifact:
            continue
        _, m = artifact
        if m.get("type") in ("dataset", "knowledge-pack"):
            inputs.append({
                "namespace": NAMESPACE,
                "name":      m["id"],
                "facets":    dataset_facets(m),
            })

    outputs: list[dict] = []
    for out in pipeline.get("outputs", []) or []:
        outputs.append({
            "namespace": NAMESPACE,
            "name":      f"{pipeline['id']}/output/{out['name']}",
            "facets": {
                "documentation": {
                    "_producer":  "https://open-harness-hub.dev",
                    "_schemaURL": "https://openlineage.io/spec/facets/1-0-0/DocumentationDatasetFacet.json",
                    "description": f"{out['name']} ({out.get('type', 'object')})",
                },
            },
        })

    event = {
        "eventType":  "COMPLETE",
        "eventTime":  datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "producer":   "https://open-harness-hub.dev/emitter/openlineage@0.1.0",
        "schemaURL":  "https://openlineage.io/spec/2-0-2/OpenLineage.json#/$defs/RunEvent",
        "run": {
            "runId":   str(uuid.uuid4()),
            "facets": {
                "nominalTime": {
                    "_producer":   "https://open-harness-hub.dev",
                    "_schemaURL":  "https://openlineage.io/spec/facets/1-0-0/NominalTimeRunFacet.json",
                    "nominalStartTime": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                },
            },
        },
        "job": {
            "namespace": NAMESPACE,
            "name":      pipeline["id"],
            "facets": {
                "documentation": {
                    "_producer":  "https://open-harness-hub.dev",
                    "_schemaURL": "https://openlineage.io/spec/facets/1-0-0/DocumentationJobFacet.json",
                    "description": pipeline.get("description", "").strip(),
                },
                "ownership": {
                    "_producer":  "https://open-harness-hub.dev",
                    "_schemaURL": "https://openlineage.io/spec/facets/1-0-0/OwnershipJobFacet.json",
                    "owners":     [{"name": a["name"], "type": "MAINTAINER"} for a in (pipeline.get("authors") or [])],
                },
                "sourceCode": {
                    "_producer":  "https://open-harness-hub.dev",
                    "_schemaURL": "https://openlineage.io/spec/facets/1-0-0/SourceCodeJobFacet.json",
                    "language":   "yaml",
                    "source":     f"catalog/pipelines/.../{slug}.yaml",
                },
            },
        },
        "inputs":  inputs,
        "outputs": outputs,
    }
    return event


def main() -> int:
    catalog = load_catalog()
    out_dir = DIST / "openlineage"
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)
    n = 0
    for _, m in by_type(catalog, "pipeline"):
        slug = slug_only(m["id"])
        ev = render(m, catalog)
        (out_dir / f"{slug}.event.json").write_text(json.dumps(ev, indent=2) + "\n")
        n += 1
    print(f"wrote {n} OpenLineage event templates to dist/openlineage/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
