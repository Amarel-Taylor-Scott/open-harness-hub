#!/usr/bin/env python3
"""Emit an SPDX 3.0 (JSON-LD) document for the whole catalog release.

Spec: https://spdx.github.io/spdx-3-model/
This is the SPDX side of the AIBOM picture (CycloneDX-ML is in
cyclonedx_ml.py); ship both and downstream consumers pick.

Output: dist/spdx/open-harness-hub.spdx.json
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


NS = "https://open-harness-hub.dev/spdx/"


def spdx_element(manifest: dict) -> dict:
    t = manifest["type"]
    spdx_type = (
        "spdx:software_Package"   if t in ("harness", "adapter", "tool", "processor") else
        "spdx:dataset_DatasetPackage" if t in ("dataset", "knowledge-pack") else
        "spdx:ai_AIPackage"            if t == "harness" else
        "spdx:software_Package"
    )
    return {
        "@type":       spdx_type,
        "spdxId":      f"{NS}{manifest['id']}",
        "name":        manifest.get("name", slug_only(manifest["id"])),
        "summary":     manifest.get("description", "").strip()[:240],
        "description": manifest.get("description", "").strip(),
        "packageVersion": manifest.get("version", "0.0.0"),
        "primaryPurpose": {
            "harness":          "application",
            "pipeline":         "application",
            "benchmark":        "test",
            "rule-pack":        "data",
            "knowledge-pack":   "data",
            "logic-pack":       "data",
            "tool":             "library",
            "persona":          "data",
            "adapter":          "library",
            "rubric":           "test",
            "dataset":          "data",
            "schema":           "specification",
            "processor":        "library",
        }.get(t, "other"),
        "homepage":   f"https://open-harness-hub.dev/{manifest['type']}/{slug_only(manifest['id'])}",
        "supplier":   "Open Harness Hub contributors",
        "license_declared": spdx_license_url(manifest.get("license")),
        "extension": [{
            "@type":  "spdx:extension_ExtensionElement",
            "name":   "ohh:metadata",
            "value": {
                "industry":         manifest.get("industry", []) or [],
                "capability":       manifest.get("capability", []) or [],
                "modality":         manifest.get("modality", []) or [],
                "trust_boundary":   manifest.get("trust_boundary"),
                "lifecycle":        manifest.get("lifecycle"),
                "lifecycle_position": manifest.get("lifecycle_position"),
                "eu_ai_act_risk":   manifest.get("eu_ai_act_risk"),
            },
        }],
    }


def main() -> int:
    catalog = load_catalog()
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()

    creation_info = {
        "@type": "spdx:core_CreationInfo",
        "specVersion": "SPDX-3.0.1",
        "createdBy":  [f"{NS}emitter"],
        "createdUsing": [f"{NS}tool/open-harness-hub-emitter"],
        "created":     now,
        "profile":     ["software", "ai", "dataset"],
        "dataLicense": "CC0-1.0",
    }

    elements = [spdx_element(m) for _, m in catalog.values()]
    doc = {
        "@context": "https://spdx.github.io/spdx-3-model/spdx-context.jsonld",
        "@graph": [
            {
                "@type":  "spdx:core_SpdxDocument",
                "spdxId": f"{NS}document/{uuid.uuid4()}",
                "name":   "Open Harness Hub catalog",
                "comment": f"SPDX 3.0 catalog release. Element count: {len(elements)}.",
                "creationInfo": creation_info,
                "element":      [e["spdxId"] for e in elements],
                "rootElement":  [e["spdxId"] for e in elements],
            },
            *elements,
        ],
    }

    out = DIST / "spdx" / "open-harness-hub.spdx.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, indent=2) + "\n")
    print(f"wrote {out.relative_to(ROOT)}  ({len(elements)} elements)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
