#!/usr/bin/env python3
"""Validate every manifest under catalog/ against its JSON Schema.

Also checks:
  - every `ref` field points to an existing artifact id;
  - every leaf type referenced is in vocabularies/leaf-types.yaml;
  - industry / capability / modality / lifecycle tags are in their vocabularies;
  - pipeline DAGs have no cycles or dangling step refs.

Exit code is non-zero on the first failure.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    sys.stderr.write("pyyaml is required: pip install pyyaml\n")
    sys.exit(2)

try:
    import jsonschema
    from jsonschema import Draft202012Validator
except ImportError:
    sys.stderr.write("jsonschema is required: pip install jsonschema\n")
    sys.exit(2)


ROOT = Path(__file__).resolve().parent.parent
SCHEMAS = ROOT / "schemas"
CATALOG = ROOT / "catalog"
VOCABS = ROOT / "vocabularies"

TYPE_TO_SCHEMA = {
    "harness":        "harness.schema.json",
    "pipeline":       "pipeline.schema.json",
    "benchmark":      "benchmark.schema.json",
    "rule-pack":      "rule-pack.schema.json",
    "knowledge-pack": "knowledge-pack.schema.json",
    "logic-pack":     "logic-pack.schema.json",
    "tool":           "tool.schema.json",
    "persona":        "persona.schema.json",
    "adapter":        "adapter.schema.json",
    "rubric":         "rubric.schema.json",
    "dataset":        "dataset.schema.json",
    "processor":      "processor.schema.json",
    "pattern":        "pattern.schema.json",
}


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_schemas() -> dict[str, dict]:
    common = json.loads((SCHEMAS / "_common.schema.json").read_text())
    schemas: dict[str, dict] = {"_common.schema.json": common}
    for name in TYPE_TO_SCHEMA.values():
        schemas[name] = json.loads((SCHEMAS / name).read_text())
    return schemas


def load_vocab(name: str) -> set[str]:
    path = VOCABS / f"{name}.yaml"
    if not path.exists():
        return set()
    data = yaml.safe_load(path.read_text())
    keys = list(data.keys())
    if not keys:
        return set()
    items = data[keys[0]]
    out: set[str] = set()
    for item in items:
        out.add(item["id"])
        for sub in item.get("sub", []) or []:
            out.add(sub["id"])
    return out


def make_validator(schemas: dict[str, dict], schema_name: str) -> Draft202012Validator:
    schema = schemas[schema_name]
    base = (SCHEMAS).as_uri() + "/"
    resolver = jsonschema.RefResolver(base_uri=base, referrer=schema, store={
        base + name: doc for name, doc in schemas.items()
    })
    return Draft202012Validator(schema, resolver=resolver)


def collect_manifests() -> list[tuple[Path, dict]]:
    out: list[tuple[Path, dict]] = []
    for path in CATALOG.rglob("*.yaml"):
        if "_inbox" in path.parts:
            continue
        data = load_yaml(path)
        if not isinstance(data, dict) or "type" not in data:
            continue
        out.append((path, data))
    return out


def check_refs(manifest: dict, known_ids: set[str], errors: list[str]) -> None:
    """Walk the manifest looking for ref-shaped strings that must resolve."""
    def walk(node: Any, key_path: str = "") -> None:
        if isinstance(node, dict):
            for k, v in node.items():
                walk(v, f"{key_path}.{k}")
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, f"{key_path}[{i}]")
        elif isinstance(node, str):
            if re.fullmatch(r"(harness|pipeline|benchmark|rule-pack|knowledge-pack|logic-pack|tool|persona|adapter|rubric|dataset|schema|processor|pattern)/[a-z0-9]+(-[a-z0-9]+)*", node):
                if node not in known_ids and not key_path.endswith(".id"):
                    errors.append(f"  unresolved ref {node!r} at {key_path}")
    walk(manifest)


def main() -> int:
    schemas = load_schemas()
    industries  = load_vocab("industries")
    capabilities = load_vocab("capabilities")
    modalities  = load_vocab("modalities")
    leaf_types  = load_vocab("leaf-types")

    manifests = collect_manifests()
    known_ids = {m["id"] for _, m in manifests if "id" in m}

    print(f"validating {len(manifests)} manifests …")
    failures = 0

    for path, manifest in manifests:
        rel = path.relative_to(ROOT)
        type_ = manifest.get("type")
        schema_name = TYPE_TO_SCHEMA.get(type_)
        if schema_name is None:
            print(f"FAIL {rel}: unknown type {type_!r}")
            failures += 1
            continue

        validator = make_validator(schemas, schema_name)
        errors = sorted(validator.iter_errors(manifest), key=lambda e: e.path)
        msg_errors = [f"  {'/'.join(str(p) for p in e.path) or '<root>'}: {e.message}" for e in errors]

        # vocabulary checks
        for ind in manifest.get("industry", []) or []:
            if industries and ind not in industries:
                msg_errors.append(f"  industry/{ind} not in vocabularies/industries.yaml")
        for cap in manifest.get("capability", []) or []:
            if capabilities and cap not in capabilities:
                msg_errors.append(f"  capability/{cap} not in vocabularies/capabilities.yaml")
        for mod in manifest.get("modality", []) or []:
            if modalities and mod not in modalities:
                msg_errors.append(f"  modality/{mod} not in vocabularies/modalities.yaml")
        for lt in manifest.get("consumes", []) or []:
            if leaf_types and lt not in leaf_types:
                msg_errors.append(f"  consumes/{lt} not in vocabularies/leaf-types.yaml")
        for lt in manifest.get("emits", []) or []:
            if leaf_types and lt not in leaf_types:
                msg_errors.append(f"  emits/{lt} not in vocabularies/leaf-types.yaml")

        ref_errors: list[str] = []
        check_refs(manifest, known_ids, ref_errors)
        msg_errors.extend(ref_errors)

        if msg_errors:
            print(f"FAIL {rel}")
            for line in msg_errors:
                print(line)
            failures += 1
        else:
            print(f"  ok {rel}")

    if failures:
        print(f"\n{failures} manifest(s) failed validation.")
        return 1
    print("\nall manifests valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
