#!/usr/bin/env python3
"""Emit C2PA v2.x manifest templates for image/audio/video generation pipelines.

Spec: https://c2pa.org/specifications/specifications/2.1/specs/C2PA_Specification.html
The manifest asserts AI-generated content via `c2pa.actions` +
`c2pa.training-mining`. Real signing requires a code-signing certificate
(out of scope for this emitter); this script emits the JSON shape.

Output: dist/c2pa/<pipeline-slug>.manifest.json
"""
from __future__ import annotations

import datetime
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from scripts.emit._lib import DIST, by_type, load_catalog, slug_only  # noqa: E402


GENERATIVE_PIPELINE_KINDS = {
    "generate_image", "generate_audio", "generate_video",
    "multimodal_image", "multimodal_audio", "multimodal_video",
}


def render(pipeline: dict, catalog: dict) -> dict:
    slug = slug_only(pipeline["id"])
    now  = datetime.datetime.now(datetime.timezone.utc).isoformat()

    # Find the tool that does the synthesis (the txt2img/txt2video/etc.)
    synth_tool = None
    for step in pipeline.get("steps", []) or []:
        if step.get("kind") == "tool":
            t = catalog.get(step.get("ref", ""), (None, None))[1]
            if t:
                synth_tool = t
                break

    return {
        "claim_generator":      f"open_harness_hub/{slug}@{pipeline.get('version','0.0.0')}",
        "claim_generator_info": [
            {"name":    "Open Harness Hub",
             "version": "0.1.0"}
        ],
        "title":      pipeline.get("name", slug),
        "format":     "image/png",
        "instance_id": "urn:uuid:00000000-0000-0000-0000-000000000000",
        "thumbnail":  {"format": "image/jpeg", "identifier": "thumb.jpg"},
        "assertions": [
            {
                "label":     "c2pa.actions",
                "data": {
                    "actions": [
                        {
                            "action":         "c2pa.created",
                            "when":           now,
                            "softwareAgent":  {
                                "name":    pipeline.get("name", slug),
                                "version": pipeline.get("version", "0.0.0"),
                            },
                            "digitalSourceType": "http://cv.iptc.org/newscodes/digitalsourcetype/trainedAlgorithmicMedia",
                        }
                    ]
                }
            },
            {
                "label": "c2pa.training-mining",
                "data": {
                    "entries": {
                        "c2pa.ai_generative_training": {
                            "use":    "allowed",
                            "notice": f"Pipeline `{pipeline['id']}` uses tool `{synth_tool['id'] if synth_tool else 'unknown'}` and obeys the hub's output_safety_packs.",
                        },
                        "c2pa.ai_inference": {
                            "use": "allowed",
                        },
                    }
                }
            },
            {
                "label": "ohh.pipeline_provenance",
                "data": {
                    "pipeline_id":      pipeline["id"],
                    "pipeline_version": pipeline.get("version", "0.0.0"),
                    "synth_tool":       synth_tool.get("id") if synth_tool else None,
                    "output_safety_packs": pipeline.get("output_safety_packs", []),
                    "style_packs":         pipeline.get("style_packs", []),
                    "physics_packs":       pipeline.get("physics_packs", []),
                    "license":          pipeline.get("license", "MIT"),
                    "trust_boundary":   pipeline.get("trust_boundary", "mixed"),
                },
            },
        ],
    }


def main() -> int:
    catalog = load_catalog()
    out_dir = DIST / "c2pa"
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)
    n = 0
    for _, m in by_type(catalog, "pipeline"):
        if m.get("pipeline_kind") not in GENERATIVE_PIPELINE_KINDS:
            continue
        slug = slug_only(m["id"])
        manifest = render(m, catalog)
        (out_dir / f"{slug}.manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        n += 1
    print(f"wrote {n} C2PA manifest templates to dist/c2pa/")
    if n == 0:
        print("  (no generative pipelines in catalog — emitter is a no-op)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
