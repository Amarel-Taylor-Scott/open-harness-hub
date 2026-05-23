#!/usr/bin/env python3
"""Emit a CycloneDX-ML 1.6 AIBOM (AI Bill of Materials) for the catalog.

Spec: https://cyclonedx.org/docs/1.6/json/
ML extension: components[].modelCard.{modelParameters, quantitativeAnalysis, considerations}

Output: dist/aibom/cyclonedx-ml.cdx.json

This is a release-level artifact summarising every harness, adapter,
dataset, and knowledge-pack in the catalog as CycloneDX components.
"""
from __future__ import annotations

import datetime
import json
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from scripts.emit._lib import DIST, load_catalog, slug_only, spdx_license_url  # noqa: E402


def component(manifest: dict) -> dict:
    slug = slug_only(manifest["id"])
    t = manifest["type"]
    c: dict = {
        "type":      "machine-learning-model" if t == "harness" or t == "adapter" else
                     "data" if t in ("dataset", "knowledge-pack") else
                     "library",
        "bom-ref":   f"ohh:{manifest['id']}@{manifest.get('version','0.0.0')}",
        "name":      manifest.get("name", slug),
        "version":   manifest.get("version", "0.0.0"),
        "description": manifest.get("description", "").strip(),
        "licenses":  [{"license": {"id": manifest.get("license", "MIT")}}],
        "purl":      f"pkg:open-harness-hub/{manifest['id']}@{manifest.get('version','0.0.0')}",
        "externalReferences": [
            {"type": "documentation",
             "url":  f"https://open-harness-hub.dev/{manifest['type']}/{slug}"},
        ],
        "tags":      sorted(set(
            (manifest.get("tags") or [])
            + (manifest.get("industry") or [])
            + (manifest.get("capability") or [])
        )),
    }

    if t in ("harness", "adapter"):
        c["modelCard"] = {
            "bom-ref": f"ohh:{manifest['id']}:modelcard",
            "modelParameters": {
                "approach":  {"type": "supervised"},
                "task":      manifest.get("capability", []),
                "datasets":  [],
                "inputs":    [{"format": "text"}],
                "outputs":   [{"format": "text"}],
            },
            "considerations": {
                "users":            ["developers", "researchers"],
                "useCases":         manifest.get("capability", []),
                "technicalLimitations": manifest.get("output_verification", []) or [],
                "ethicalConsiderations": [
                    {"name": "trust_boundary", "description": manifest.get("trust_boundary") or "unspecified"},
                ],
                "fairnessAssessments": [],
            },
            "properties": [
                {"name": "ohh:lifecycle",          "value": manifest.get("lifecycle", "experimental")},
                {"name": "ohh:lifecycle_position", "value": manifest.get("lifecycle_position", "")},
                {"name": "ohh:eu_ai_act_risk",    "value": manifest.get("eu_ai_act_risk", "")},
            ],
        }

    properties: list[dict] = [
        {"name": "ohh:type",            "value": t},
        {"name": "ohh:industry",         "value": ",".join(manifest.get("industry", []) or [])},
        {"name": "ohh:capability",       "value": ",".join(manifest.get("capability", []) or [])},
        {"name": "ohh:modality",         "value": ",".join(manifest.get("modality", []) or [])},
        {"name": "ohh:trust_boundary",  "value": manifest.get("trust_boundary", "")},
        {"name": "ohh:lifecycle",       "value": manifest.get("lifecycle", "")},
        {"name": "ohh:license_url",     "value": spdx_license_url(manifest.get("license"))},
    ]
    if manifest.get("eu_ai_act_risk"):
        properties.append({"name": "ohh:eu_ai_act_risk", "value": manifest["eu_ai_act_risk"]})
    c["properties"] = properties

    return c


def main() -> int:
    catalog = load_catalog()

    components: list[dict] = []
    dependencies: list[dict] = []

    for path, m in catalog.values():
        components.append(component(m))

        # Build a dependency edge for pipelines → step refs
        if m.get("type") == "pipeline":
            deps = []
            for step in m.get("steps", []) or []:
                ref = step.get("ref")
                if ref and not ref.startswith("$.") and ref in catalog:
                    deps.append(f"ohh:{ref}@{catalog[ref][1].get('version','0.0.0')}")
            if deps:
                dependencies.append({
                    "ref":       f"ohh:{m['id']}@{m.get('version','0.0.0')}",
                    "dependsOn": deps,
                })

    bom = {
        "bomFormat":    "CycloneDX",
        "specVersion":  "1.6",
        "version":      1,
        "serialNumber": f"urn:uuid:{uuid.uuid4()}",
        "metadata": {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "tools": {"components": [{
                "type":     "application",
                "name":     "open-harness-hub-emitter",
                "version":  "0.1.0",
            }]},
            "component": {
                "type":    "application",
                "bom-ref": "ohh:catalog",
                "name":    "Open Harness Hub catalog",
                "version": "0.1.0",
            },
            "properties": [
                {"name": "ohh:spec_version", "value": "0.1.0"},
                {"name": "ohh:catalog_size", "value": str(len(components))},
            ],
        },
        "components":   components,
        "dependencies": dependencies,
    }

    out = DIST / "aibom" / "cyclonedx-ml.cdx.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(bom, indent=2) + "\n")
    print(f"wrote {out.relative_to(ROOT)}  ({len(components)} components, {len(dependencies)} pipeline deps)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
