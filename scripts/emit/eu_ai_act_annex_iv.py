#!/usr/bin/env python3
"""Emit an EU AI Act Annex IV technical-documentation dossier for any
harness or pipeline tagged `eu_ai_act_risk: high_risk`.

Source: Regulation (EU) 2024/1689, Annex IV.
Output: dist/eu-ai-act/<slug>/annex-iv.md
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from scripts.emit._lib import DIST, load_catalog, slug_only  # noqa: E402


def render(manifest: dict, catalog: dict) -> str:
    slug = slug_only(manifest["id"])
    name = manifest.get("name", slug)

    sections: list[str] = []
    sections.append(f"# Annex IV technical documentation — {name}")
    sections.append("")
    sections.append(f"> Generated from Open Harness Hub manifest `{manifest['id']}` v{manifest.get('version','0.0.0')}. EU AI Act Regulation 2024/1689, Annex IV.")
    sections.append("")

    sections.append("## 1. General description of the AI system")
    sections.append("")
    sections.append(f"- **Name**: {name}")
    sections.append(f"- **Provider**: {(manifest.get('authors') or [{'name':'Open Harness Hub contributors'}])[0]['name']}")
    sections.append(f"- **Intended purpose**: {manifest.get('description','').strip()}")
    sections.append(f"- **Version**: {manifest.get('version','0.0.0')}")
    sections.append(f"- **EU AI Act risk classification**: `{manifest.get('eu_ai_act_risk', 'high_risk')}`")
    sections.append("")

    sections.append("## 2. Detailed description of the elements")
    sections.append("")
    sections.append("### 2.1 Methods and steps used to develop the system")
    sections.append("")
    if manifest.get("type") == "harness":
        sections.append("Workflow harness wrapping a model call. Applied layers:")
        sections.append("")
        for layer in manifest.get("applied_layers", []) or []:
            sections.append(f"- `{layer}`")
    elif manifest.get("type") == "pipeline":
        sections.append("Pipeline composed of:")
        sections.append("")
        for i, step in enumerate(manifest.get("steps", []) or [], 1):
            sections.append(f"{i}. **{step['id']}** ({step['kind']}) → `{step['ref']}`")
    sections.append("")

    sections.append("### 2.2 Design specifications")
    sections.append("")
    sections.append(f"- Lifecycle position: `{manifest.get('lifecycle_position','—')}`")
    sections.append(f"- Trust boundary: `{manifest.get('trust_boundary','—')}`")
    sections.append(f"- Industry tags: {', '.join(manifest.get('industry', []) or [])}")
    sections.append(f"- Modality: {', '.join(manifest.get('modality', []) or [])}")
    sections.append("")

    sections.append("### 2.3 Computational resources and architecture")
    sections.append("")
    if manifest.get("model_targets"):
        sections.append("Compatible model transports (provider-neutral):")
        sections.append("")
        for m in manifest["model_targets"]:
            sections.append(f"- `{m['id']}` — `{m['transport']}` (trust: {m.get('trust_boundary','—')})")
    sections.append("")

    sections.append("## 3. Information about the data and data governance")
    sections.append("")
    dp = manifest.get("data_protection") or {}
    if dp:
        for k, v in dp.items():
            if isinstance(v, list):
                v = ", ".join(str(x) for x in v) or "—"
            sections.append(f"- **{k}**: {v}")
    else:
        sections.append("Data protection metadata not declared on the source manifest. Add a `data_protection:` block with DPV-aligned categories.")
    sections.append("")

    sections.append("## 4. Risk management system")
    sections.append("")
    sections.append(f"- NIST AI RMF controls referenced: {', '.join(manifest.get('nist_ai_rmf_controls', []) or []) or '—'}")
    sections.append(f"- ISO/IEC 42001 controls: {', '.join(manifest.get('iso_42001_controls', []) or []) or '—'}")
    sections.append("")
    if manifest.get("input_verification"):
        sections.append("### 4.1 Input verification")
        sections.append("")
        for v in manifest["input_verification"]:
            sections.append(f"- {v}")
        sections.append("")
    if manifest.get("output_verification"):
        sections.append("### 4.2 Output verification")
        sections.append("")
        for v in manifest["output_verification"]:
            sections.append(f"- {v}")
        sections.append("")

    sections.append("## 5. Monitoring, functioning and control of the AI system")
    sections.append("")
    sections.append("Logging and audit trail: emit OpenLineage events per pipeline run (see `dist/openlineage/`) and `processor/audit-trace-emitter` outputs.")
    sections.append("")

    sections.append("## 6. Description of changes")
    sections.append("")
    sections.append("Version-controlled in git; see commit history. Hub manifests use semver; `superseded_by` and `deprecated_on` fields document changes.")
    sections.append("")

    sections.append("## 7. Compliance instruments")
    sections.append("")
    sections.append("- CycloneDX-ML 1.6 AIBOM: `dist/aibom/cyclonedx-ml.cdx.json`")
    sections.append("- Hugging Face Model Card: `dist/hf/model_cards/.../README.md`")
    sections.append("- Croissant 1.0 (for any backing datasets): `dist/croissant/`")
    sections.append("")

    sections.append("## 8. Reference documentation")
    sections.append("")
    sections.append("- Source manifest: in the hub catalog repo, search for the id above.")
    sections.append("- JSON-LD `@context`: `/ns/context.jsonld`")
    sections.append("- Hub specification: `taxonomy/SPEC.md`")
    sections.append("")

    return "\n".join(sections)


def main() -> int:
    catalog = load_catalog()
    out_root = DIST / "eu-ai-act"
    if out_root.exists():
        shutil.rmtree(out_root)
    out_root.mkdir(parents=True)
    n = 0
    for _, m in catalog.values():
        if m.get("eu_ai_act_risk") != "high_risk":
            continue
        slug = slug_only(m["id"])
        (out_root / slug).mkdir(parents=True, exist_ok=True)
        (out_root / slug / "annex-iv.md").write_text(render(m, catalog))
        n += 1
    print(f"wrote {n} Annex IV dossiers to dist/eu-ai-act/")
    if n == 0:
        print("  (no `eu_ai_act_risk: high_risk` artifacts in the catalog — emitter is a no-op until one is added)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
