#!/usr/bin/env python3
"""Emit Croissant 1.0 JSON-LD for every `dataset` and `knowledge-pack`.

Croissant is MLCommons + Google's JSON-LD format for ML-ready datasets,
extended from schema.org. It's indexed automatically by Hugging Face,
Kaggle, and Google Dataset Search.

Output: dist/croissant/<slug>.croissant.json (one per manifest).

Spec: https://docs.mlcommons.org/croissant/docs/croissant-spec.html
conformsTo: http://mlcommons.org/croissant/1.0
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

# Allow `python scripts/emit/croissant.py` and `python -m scripts.emit.croissant`.
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from scripts.emit._lib import (  # noqa: E402
    CATALOG, DIST, by_type, iter_jsonl, load_catalog,
    sha256_file, slug_only, spdx_license_url, write_json,
)

CONTEXT = {
    "@language":    "en",
    "@vocab":       "https://schema.org/",
    "sc":           "https://schema.org/",
    "cr":           "http://mlcommons.org/croissant/",
    "rai":          "http://mlcommons.org/croissant/RAI/",
    "dct":          "http://purl.org/dc/terms/",
    "citeAs":       "cr:citeAs",
    "column":       "cr:column",
    "conformsTo":   "dct:conformsTo",
    "data":         {"@id": "cr:data", "@type": "@json"},
    "dataType":     {"@id": "cr:dataType", "@type": "@vocab"},
    "examples":     {"@id": "cr:examples", "@type": "@json"},
    "extract":      "cr:extract",
    "field":        "cr:field",
    "fileObject":   "cr:fileObject",
    "fileSet":      "cr:fileSet",
    "format":       "cr:format",
    "includes":     "cr:includes",
    "isLiveDataset":"cr:isLiveDataset",
    "key":          "cr:key",
    "md5":          "cr:md5",
    "parentField":  "cr:parentField",
    "path":         "cr:path",
    "recordSet":    "cr:recordSet",
    "references":   "cr:references",
    "regex":        "cr:regex",
    "repeated":     "cr:repeated",
    "replace":      "cr:replace",
    "separator":    "cr:separator",
    "source":       "cr:source",
    "subField":     "cr:subField",
    "transform":    "cr:transform",
}

CONFORMS_TO = "http://mlcommons.org/croissant/1.0"

ENCODING_BY_EXT = {
    ".jsonl":   "application/jsonlines",
    ".json":    "application/json",
    ".csv":     "text/csv",
    ".tsv":     "text/tab-separated-values",
    ".yaml":    "application/yaml",
    ".yml":     "application/yaml",
    ".md":      "text/markdown",
    ".txt":     "text/plain",
    ".parquet": "application/vnd.apache.parquet",
}


def detect_data_type(values: list) -> str:
    """Heuristic per-field data type from sample values."""
    seen_bool = seen_int = seen_float = seen_str = seen_url = seen_list = False
    for v in values:
        if isinstance(v, bool):
            seen_bool = True
        elif isinstance(v, int):
            seen_int = True
        elif isinstance(v, float):
            seen_float = True
        elif isinstance(v, str):
            if v.startswith(("http://", "https://")):
                seen_url = True
            seen_str = True
        elif isinstance(v, list):
            seen_list = True
    if seen_str or seen_url or seen_list:
        return "sc:URL" if seen_url and not (seen_str and not seen_url) else "sc:Text"
    if seen_float:
        return "sc:Float"
    if seen_int:
        return "sc:Integer"
    if seen_bool:
        return "sc:Boolean"
    return "sc:Text"


def derive_fields(sample_rows: list[dict]) -> dict[str, str]:
    """Return field_name -> dataType from a sample of JSONL rows."""
    out: dict[str, list] = {}
    for row in sample_rows:
        for k, v in row.items():
            out.setdefault(k, []).append(v)
    return {k: detect_data_type(vs) for k, vs in out.items()}


def file_object(manifest_path: Path, file_decl: dict, parent_slug: str) -> tuple[dict, list[dict]]:
    """Build one FileObject + (one RecordSet for jsonl) given a file declaration."""
    rel = file_decl["path"]
    abs_path = manifest_path.parent / rel
    if not abs_path.exists():
        return {}, []

    fmt = file_decl.get("format") or abs_path.suffix.lstrip(".")
    encoding = ENCODING_BY_EXT.get(abs_path.suffix.lower(), "application/octet-stream")

    file_id = f"{parent_slug}__{abs_path.stem}"
    size = abs_path.stat().st_size
    sha = sha256_file(abs_path)

    fileobj = {
        "@type":          "cr:FileObject",
        "@id":            file_id,
        "name":           abs_path.name,
        "description":    f"Data file backing knowledge pack {parent_slug}.",
        "contentUrl":     str(abs_path.relative_to(abs_path.parent.parent.parent)),
        "encodingFormat": encoding,
        "contentSize":    f"{size} B",
        "sha256":         sha,
    }

    record_sets: list[dict] = []
    if fmt == "jsonl" or abs_path.suffix.lower() == ".jsonl":
        sample = list(iter_jsonl(abs_path))[:200]
        if sample:
            fields = derive_fields(sample)
            rs_id = f"{parent_slug}__records"
            record_sets.append({
                "@type": "cr:RecordSet",
                "@id":   rs_id,
                "name":  rs_id,
                "description": f"Records parsed from {abs_path.name}.",
                "field": [
                    {
                        "@type":    "cr:Field",
                        "@id":      f"{rs_id}/{fname}",
                        "name":     fname,
                        "dataType": dtype,
                        "source": {
                            "fileObject": {"@id": file_id},
                            "extract":    {"column": fname},
                        },
                    }
                    for fname, dtype in fields.items()
                ],
            })

    return fileobj, record_sets


def render_one(manifest_path: Path, manifest: dict) -> dict[str, Any]:
    slug = slug_only(manifest["id"])

    creators = []
    for a in manifest.get("authors", []) or []:
        c = {"@type": "sc:Person", "name": a.get("name", "Unknown")}
        if a.get("url"):
            c["url"] = a["url"]
        if a.get("email"):
            c["email"] = a["email"]
        creators.append(c)
    if not creators:
        creators = [{"@type": "sc:Person", "name": "Open Harness Hub contributors"}]

    out: dict[str, Any] = {
        "@context":     CONTEXT,
        "@type":        "sc:Dataset",
        "@id":          f"https://open-harness-hub.dev/{manifest['type']}/{slug}",
        "conformsTo":   CONFORMS_TO,
        "name":         manifest.get("name", slug),
        "description":  manifest.get("description", "").strip(),
        "version":      manifest.get("version", "0.1.0"),
        "license":      spdx_license_url(manifest.get("license")),
        "url":          f"https://open-harness-hub.dev/{manifest['type']}/{slug}",
        "creator":      creators,
        "datePublished": manifest.get("created") or manifest.get("updated") or "1970-01-01",
        "keywords":     manifest.get("tags", []) or manifest.get("capability", []) or [],
        "isLiveDataset": False,
    }

    if manifest.get("updated"):
        out["dateModified"] = manifest["updated"]

    prov = manifest.get("provenance") or {}
    if prov.get("sources"):
        out["citation"] = "; ".join(prov["sources"])

    distribution: list[dict] = []
    record_sets: list[dict] = []
    for f in manifest.get("files", []) or []:
        fobj, rs = file_object(manifest_path, f, slug)
        if fobj:
            distribution.append(fobj)
            record_sets.extend(rs)
    if distribution:
        out["distribution"] = distribution
    if record_sets:
        out["recordSet"] = record_sets

    return out


def main() -> int:
    catalog = load_catalog()
    targets = list(by_type(catalog, "dataset")) + list(by_type(catalog, "knowledge-pack"))
    out_dir = DIST / "croissant"
    out_dir.mkdir(parents=True, exist_ok=True)

    written = 0
    for path, manifest in targets:
        doc = render_one(path, manifest)
        slug = slug_only(manifest["id"])
        out_path = out_dir / f"{slug}.croissant.json"
        write_json(out_path, doc)
        files_count = len(doc.get("distribution", []) or [])
        rs_count    = len(doc.get("recordSet",   []) or [])
        print(f"  {out_path.relative_to(ROOT)}  ({files_count} files, {rs_count} record sets)")
        written += 1

    print(f"\nwrote {written} Croissant manifests to dist/croissant/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
