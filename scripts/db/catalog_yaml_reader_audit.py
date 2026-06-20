#!/usr/bin/env python3
"""Audit scripts that still read catalog YAML directly.

The database-backed catalog migration does not require every YAML reader to
disappear. Some scripts are seed/export utilities by design. This audit makes
that distinction explicit so operational consumers can be moved to
`catalog_row_source.py` while seed/export tooling remains file-based.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re
import time
from typing import Any


REPO = Path(__file__).resolve().parent.parent.parent
DEFAULT_OUTPUT = REPO / "dist" / "catalog-migration-smoke" / "catalog-yaml-reader-audit.json"

PATTERNS = {
    "catalog_rglob_yaml": re.compile(r"\b(?:CATALOG|CATALOG_DIR|KP_DIR|root|repo / \"catalog\")\.rglob\([\"']\*\.ya?ml[\"']\)"),
    "safe_load": re.compile(r"\byaml\.safe_load\b"),
    "catalog_literal": re.compile(r"[\"']catalog/"),
    "catalog_inbox": re.compile(r"catalog/_inbox|CATALOG / \"_inbox\""),
}

CLASSIFICATION_OVERRIDES = {
    "scripts/validate.py": "seed_export_validation",
    "scripts/build_component_id_index.py": "seed_export_validation",
    "scripts/db/catalog_manifest_bridge.py": "seed_export_bridge",
    "scripts/db/catalog_manifest_export_plan.py": "seed_export_bridge",
    "scripts/db/catalog_database_migration_smoke.py": "migration_infrastructure",
    "scripts/db/catalog_row_integrity.py": "migration_infrastructure",
    "scripts/db/catalog_row_source.py": "migration_infrastructure",
    "scripts/processors/catalog_search.py": "row_backed_consumer",
    "scripts/build_catalog_db.py": "row_backed_consumer",
    "scripts/build_catalog_pages.py": "row_backed_consumer",
    "scripts/build_catalog_index.py": "row_backed_consumer",
    "scripts/oh_hub.py": "row_backed_consumer",
    "scripts/run_pipeline.py": "row_backed_consumer",
    "scripts/emit/_lib.py": "row_backed_consumer",
    "scripts/db/build_vector_index.py": "row_backed_consumer",
    "scripts/db/build_vector_store.py": "row_backed_consumer",
    "scripts/scaffold_pipeline_from_task.py": "row_backed_consumer",
    "scripts/processors/semantic_dedup.py": "row_backed_consumer",
    "scripts/processors/draft_quality_gate.py": "row_backed_consumer",
    "scripts/factory/processor_loader.py": "row_backed_consumer",
    "scripts/factory/capability_lift_gate.py": "row_backed_consumer",
    "scripts/factory/capability_gap_scout.py": "row_backed_consumer",
    "scripts/audit_context_storage.py": "row_backed_consumer",
    "scripts/baltor_admin_demo_server.py": "operational_migration_candidate",
    "scripts/foundry/standardize.py": "row_backed_consumer",
    "scripts/emit/openlineage.py": "documentation_or_example",
    "scripts/factory/knowledge_pack_factory.py": "draft_generation",
    "scripts/foundry/skillsbench.py": "seed_export_validation",
    "scripts/run_esg_grep.py": "documentation_or_example",
    "scripts/seed/action_bucket_components.py": "draft_generation",
    "scripts/seed/baltor_components.py": "draft_generation",
    "scripts/seed/context_layer_components.py": "draft_generation",
    "scripts/showcase/verify_tunnels.py": "documentation_or_example",
}

CLASSIFICATION_NOTES = {
    "seed_export_validation": "Expected to read catalog YAML because it validates seed/export manifests.",
    "seed_export_bridge": "Expected to read or write manifest-shaped files as migration bridge/export tooling.",
    "migration_infrastructure": "Database migration support script; YAML references here are examples or migration metadata.",
    "row_backed_consumer": "Already has a database-row path; keep YAML mode as static/local fallback.",
    "operational_migration_candidate": "Likely runtime or product-facing consumer; migrate to catalog_row_source.py or document as seed/export-only.",
    "draft_generation": "Writes or checks drafts in catalog/_inbox; keep separate from operational truth.",
    "data_jsonl_utility": "Uses catalog data JSONL or fixed source data rather than component manifests.",
    "documentation_or_example": "References catalog paths in prose/examples.",
    "unknown_yaml_reader": "Needs manual classification.",
}


def utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return ""


def relative(path: Path) -> str:
    return str(path.relative_to(REPO))


def classify(rel_path: str, matched: dict[str, int], text: str) -> str:
    if rel_path in CLASSIFICATION_OVERRIDES:
        return CLASSIFICATION_OVERRIDES[rel_path]
    if "catalog/_inbox" in text or "_inbox" in rel_path:
        return "draft_generation"
    if "catalog/knowledge-packs/data/" in text and not matched.get("catalog_rglob_yaml"):
        return "data_jsonl_utility"
    if rel_path.startswith("docs/"):
        return "documentation_or_example"
    if matched.get("catalog_rglob_yaml") or "CATALOG.rglob" in text:
        return "operational_migration_candidate"
    if matched.get("safe_load") or matched.get("catalog_literal"):
        return "unknown_yaml_reader"
    return "documentation_or_example"


def line_samples(text: str, limit: int = 8) -> list[dict[str, Any]]:
    samples: list[dict[str, Any]] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        if any(pattern.search(line) for pattern in PATTERNS.values()):
            samples.append({"line": line_no, "text": line.strip()[:220]})
        if len(samples) >= limit:
            break
    return samples


def audit_paths(paths: list[Path]) -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    for path in sorted(paths):
        if "__pycache__" in path.parts:
            continue
        text = read_text(path)
        if not text:
            continue
        matched = {name: len(pattern.findall(text)) for name, pattern in PATTERNS.items()}
        if not any(matched.values()):
            continue
        rel = relative(path)
        classification = classify(rel, matched, text)
        entries.append({
            "path": rel,
            "classification": classification,
            "note": CLASSIFICATION_NOTES.get(classification, ""),
            "matches": matched,
            "samples": line_samples(text),
        })

    by_class = Counter(entry["classification"] for entry in entries)
    migration_candidates = [
        entry["path"]
        for entry in entries
        if entry["classification"] == "operational_migration_candidate"
    ]
    report = {
        "ok": True,
        "generated_at": utc_now(),
        "entry_count": len(entries),
        "by_classification": dict(sorted(by_class.items())),
        "operational_migration_candidate_count": len(migration_candidates),
        "operational_migration_candidates": migration_candidates,
        "entries": entries,
        "notes": [
            "This audit does not mutate files.",
            "Not every YAML reader is wrong; seed/export and draft-generation utilities may remain file-backed.",
            "Operational migration candidates should either gain a database-row path or be explicitly reclassified.",
        ],
    }
    return report


def default_paths() -> list[Path]:
    return [
        *list((REPO / "scripts").rglob("*.py")),
        *list((REPO / "docs" / "architecture").rglob("*.md")),
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit direct catalog YAML readers and classify migration status.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--path", action="append", type=Path, help="Optional path to audit; repeatable.")
    args = parser.parse_args(argv)
    paths = [path if path.is_absolute() else REPO / path for path in args.path] if args.path else default_paths()
    report = audit_paths(paths)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "ok": report["ok"],
        "entry_count": report["entry_count"],
        "by_classification": report["by_classification"],
        "operational_migration_candidate_count": report["operational_migration_candidate_count"],
        "output": str(args.output),
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
