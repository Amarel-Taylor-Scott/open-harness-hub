#!/usr/bin/env python3
"""Map catalog YAML manifests to database seed/import row sets.

This is a dry-run bridge. It does not connect to Postgres and it does not move
or delete catalog files. It reads validated manifests, emits JSONL rows for the
canonical database tables, and writes a reviewable psql load script.

The intent is to make repository manifests seed/export artifacts while Postgres
becomes the operational source of truth for hosted deployments.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
from datetime import date, datetime
import hashlib
import json
import re
import tempfile
import time
from pathlib import Path
from typing import Any, Iterable

import yaml


REPO = Path(__file__).resolve().parent.parent.parent
CATALOG = _resource("catalog")
DEFAULT_OUT = _resource("dist") / "catalog-manifest-bridge"
COMPONENT_REF_RE = re.compile(
    r"^(harness|pipeline|benchmark|rule-pack|knowledge-pack|logic-pack|tool|persona|adapter|rubric|dataset|schema|processor|pattern)/[a-z0-9]+(-[a-z0-9]+)*$"
)
LOAD_SQL_STAGE_NAMES = {
    "components": "stage_manifest_component",
    "component_versions": "stage_manifest_component_version",
    "component_industries": "stage_manifest_industry",
    "component_capabilities": "stage_manifest_capability",
    "component_modalities": "stage_manifest_modality",
    "component_tags": "stage_manifest_tag",
    "component_refs": "stage_manifest_ref",
    "rubric_dimensions": "stage_manifest_rubric_dimension",
    "context_objects": "stage_manifest_context_object",
    "component_context_objects": "stage_manifest_component_context_object",
    "context_mask_contracts": "stage_manifest_context_mask_contract",
    "context_transformer_contracts": "stage_manifest_context_transformer_contract",
    "manifest_import_batches": "stage_manifest_import_batch",
    "manifest_import_records": "stage_manifest_import_record",
}


def _utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _read_yaml(path: Path) -> dict[str, Any] | None:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or not value.get("id") or not value.get("type"):
        return None
    return value


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _manifest_hash(doc: dict[str, Any]) -> str:
    return _sha256_text(_canonical_json(doc))


def _write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    count = 0
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")
            count += 1
    return count


def _iter_manifest_paths(paths: list[Path] | None) -> Iterable[Path]:
    if paths:
        for path in paths:
            yield path if path.is_absolute() else (_resource(path))
        return
    for path in sorted(CATALOG.rglob("*.yaml")):
        if "_inbox" not in path.parts:
            yield path


def _walk_refs(node: Any, key_path: str = "") -> Iterable[tuple[str, str]]:
    if isinstance(node, dict):
        for key, value in node.items():
            if key in {"id", "examples", "example"}:
                continue
            yield from _walk_refs(value, f"{key_path}.{key}" if key_path else key)
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from _walk_refs(value, f"{key_path}[{index}]")
    elif isinstance(node, str) and COMPONENT_REF_RE.fullmatch(node):
        role = key_path.split(".")[-1].split("[")[0] if key_path else "ref"
        yield role, node


def _dimension_parent_path(path: str) -> str | None:
    if "." not in path:
        return None
    return path.rsplit(".", 1)[0]


def _dimension_level(path: str) -> int:
    if not path:
        return 0
    return path.count(".") + 1


def _slug_from_component_id(component_id: str) -> str:
    return component_id.split("/", 1)[1]


def _context_object_id(component_id: str) -> str:
    return "ctx://openhubforai/component/" + component_id


def _component_row_id(prefix: str, component_id: str) -> str:
    return prefix + "/" + component_id.replace("/", "/component/")


def _recommended_action(doc: dict[str, Any], flags: list[str]) -> str:
    if any(flag.startswith("duplicate_component_id") for flag in flags):
        return "hold"
    if doc.get("lifecycle") == "deprecated" or doc.get("superseded_by"):
        return "archive_seed"
    if flags:
        return "review"
    return "import"


def _rotted_flags(doc: dict[str, Any], *, dated_review_days: int) -> list[str]:
    flags: list[str] = []
    if doc.get("lifecycle") == "deprecated":
        flags.append("deprecated_lifecycle")
    if doc.get("superseded_by"):
        flags.append("superseded_component")
    if not doc.get("updated"):
        flags.append("missing_updated_date")
    if doc.get("freshness") in {"volatile", "dated"}:
        flags.append(f"{doc.get('freshness')}_freshness_requires_review")
    updated = str(doc.get("updated") or "")
    if updated and re.fullmatch(r"\d{4}-\d{2}-\d{2}", updated):
        updated_date = datetime.strptime(updated, "%Y-%m-%d").date()
        age_days = (date.today() - updated_date).days
        if age_days > dated_review_days:
            flags.append(f"updated_date_older_than_{dated_review_days}_days")
    slug = _slug_from_component_id(str(doc.get("id")))
    if re.search(r"(^|-)v[0-9]+($|-)", slug):
        flags.append("version_in_slug_migration_candidate")
    return flags


def _component_row(doc: dict[str, Any], path: Path, definition_hash: str) -> dict[str, Any]:
    return {
        "id": doc["id"],
        "type": doc["type"],
        "component_layer": doc.get("component_layer"),
        "control_flow_kind": doc.get("control_flow_kind"),
        "version": doc.get("version"),
        "name": doc.get("name"),
        "description": doc.get("description"),
        "license": doc.get("license"),
        "lifecycle": doc.get("lifecycle"),
        "trust_boundary": doc.get("trust_boundary"),
        "freshness": doc.get("freshness"),
        "created": doc.get("created"),
        "updated": doc.get("updated"),
        "superseded_by": doc.get("superseded_by"),
        "deprecated_on": doc.get("deprecated_on"),
        "attribution": doc.get("attribution"),
        "links": doc.get("links"),
        "body": doc,
        "seed": {
            "path": str(path.relative_to(REPO)),
            "definition_source": "repo_seed",
            "definition_hash": definition_hash,
        },
    }


def _component_version_row(doc: dict[str, Any], path: Path, definition_hash: str) -> dict[str, Any]:
    return {
        "component_version_id": f"ctxv://openhubforai/component/{doc['id']}@{definition_hash}",
        "component_id": doc["id"],
        "version": doc["version"],
        "version_status": "deprecated" if doc.get("lifecycle") == "deprecated" else "active",
        "change_summary": "Imported from repository seed manifest.",
        "definition_source": "repo_seed",
        "source_ref": str(path.relative_to(REPO)),
        "definition_hash": definition_hash,
        "body": doc,
    }


def _rubric_dimension_rows(doc: dict[str, Any]) -> Iterable[dict[str, Any]]:
    if doc.get("type") != "rubric":
        return
    for dimension in doc.get("dimensions", []) or []:
        path = str(dimension.get("id"))
        yield {
            "rubric_dimension_id": f"rubric-dimension/{doc['id']}/{path}",
            "rubric_id": doc["id"],
            "dimension_path": path,
            "parent_path": _dimension_parent_path(path),
            "dimension_level": _dimension_level(path),
            "label": dimension.get("label"),
            "weight": dimension.get("weight", 0),
            "scale": dimension.get("scale"),
            "evidence_required": dimension.get("evidence_required"),
            "gate": str(dimension.get("label", "")).lower().startswith("gate:"),
            "body": dimension,
        }


def _rubric_dimension_context_object_row(
    *,
    doc: dict[str, Any],
    dimension_row: dict[str, Any],
    path: Path,
    definition_hash: str,
) -> dict[str, Any]:
    dimension_path = dimension_row["dimension_path"]
    return {
        "context_object_id": (
            _context_object_id(doc["id"])
            + "/rubric-dimension/"
            + re.sub(r"[^a-zA-Z0-9._-]+", "-", str(dimension_path))
        ),
        "tenant_id": "openhubforai",
        "object_type": "catalog_rubric_dimension",
        "subkind": "rubric_dimension",
        "title": dimension_row.get("label"),
        "summary": dimension_row.get("evidence_required"),
        "source_system": "repo_catalog",
        "native_id": dimension_row["rubric_dimension_id"],
        "source_url": f"{path.relative_to(REPO)}#dimension-{dimension_path}",
        "classification": "public",
        "source_handles": [
            f"repo://{path.relative_to(REPO)}#dimension-{dimension_path}",
            f"db://rubric_dimension/{dimension_row['rubric_dimension_id']}",
        ],
        "facets": {
            "catalog": {
                "component_id": doc["id"],
                "component_type": doc["type"],
                "version": doc.get("version"),
                "definition_hash": definition_hash,
            },
            "rubric_dimension": {
                "rubric_id": dimension_row["rubric_id"],
                "dimension_path": dimension_path,
                "parent_path": dimension_row.get("parent_path"),
                "dimension_level": dimension_row.get("dimension_level"),
                "weight": dimension_row.get("weight"),
                "scale": dimension_row.get("scale"),
                "gate": dimension_row.get("gate"),
            },
        },
        "document": dimension_row["body"],
    }


def _transformer_kind_for_processor(doc: dict[str, Any]) -> str:
    process_kind = str(doc.get("process_kind") or "").lower()
    tags = {str(tag).lower() for tag in (doc.get("tags") or [])}
    capabilities = {str(capability).lower() for capability in (doc.get("capability") or [])}
    text = " ".join([process_kind, *tags, *capabilities, str(doc.get("name") or "").lower()])
    if "normalize" in text or "canonical" in text or "standardization" in text:
        return "raw_to_normalized"
    if "chunk" in text:
        return "normalized_to_chunk"
    if "claim" in text or "extract" in text:
        return "chunk_to_claim"
    if "embedding" in text or "embed" in text:
        return "artifact_to_embedding"
    if "rerank" in text:
        return "candidate_to_reranked_list"
    if "pack" in text and "context" in text:
        return "object_to_context_pack"
    if "mask" in text or "redact" in text or "redaction" in text or "pii" in text:
        return "mask_application"
    if "schema" in text and ("convert" in text or "conversion" in text):
        return "schema_conversion"
    return "custom"


def _processor_transformer_contract_rows(
    *,
    doc: dict[str, Any],
    context_object: dict[str, Any],
    path: Path,
    definition_hash: str,
) -> Iterable[dict[str, Any]]:
    if doc.get("type") != "processor":
        return
    yield {
        "transformer_contract_id": _component_row_id("transformer-contract", doc["id"]),
        "context_object_id": context_object["context_object_id"],
        "component_id": doc["id"],
        "transformer_kind": _transformer_kind_for_processor(doc),
        "input_contract": {
            "inputs": doc.get("inputs") or [],
            "source_ref": str(path.relative_to(REPO)),
        },
        "output_contract": {
            "outputs": doc.get("outputs") or [],
            "source_ref": str(path.relative_to(REPO)),
        },
        "deterministic": doc.get("deterministic"),
        "model_required": bool(doc.get("model_required") or False),
        "lossiness": doc.get("lossiness") or "unknown",
        "reversible": bool(doc.get("reversible") or False),
        "validation": {
            "idempotent": doc.get("idempotent"),
            "on_error": doc.get("on_error"),
            "latency_budget_ms": doc.get("latency_budget_ms"),
        },
        "lineage_policy": {
            "definition_source": "repo_seed",
            "definition_hash": definition_hash,
            "source_handle": f"repo://{path.relative_to(REPO)}",
            "required": True,
        },
        "contract": {
            "process_kind": doc.get("process_kind"),
            "side_effects": doc.get("side_effects"),
            "streaming": doc.get("streaming"),
            "implementations": doc.get("implementations") or [],
            "body": {
                "reason": (
                    "Processor manifests are imported as transformer contracts "
                    "because they consume structured inputs and emit transformed "
                    "outputs in runtime flows."
                )
            },
        },
    }


def _io_names(doc: dict[str, Any]) -> list[str]:
    names: list[str] = []
    for key in ("inputs", "outputs"):
        for item in doc.get(key) or []:
            if isinstance(item, dict) and item.get("name"):
                names.append(str(item["name"]))
    parameters = doc.get("parameters")
    if isinstance(parameters, dict):
        properties = parameters.get("properties")
        if isinstance(properties, dict):
            names.extend(str(name) for name in properties)
    returns = doc.get("returns")
    if isinstance(returns, dict):
        properties = returns.get("properties")
        if isinstance(properties, dict):
            names.extend(str(name) for name in properties)
    return names


def _has_redaction_semantics(doc: dict[str, Any]) -> bool:
    tags = {str(tag).lower() for tag in (doc.get("tags") or [])}
    capability = {str(item).lower() for item in (doc.get("capability") or [])}
    text = " ".join([
        str(doc.get("id") or "").lower(),
        str(doc.get("name") or "").lower(),
        str(doc.get("description") or "").lower(),
        str(doc.get("process_kind") or "").lower(),
        *tags,
        *capability,
        *_io_names(doc),
    ])
    direct_markers = {"redact", "redaction", "pii", "phi", "sensitive-data", "sensitive_data"}
    return any(marker in text for marker in direct_markers)


def _mask_contract_rows(
    *,
    doc: dict[str, Any],
    context_object: dict[str, Any],
    path: Path,
    definition_hash: str,
) -> Iterable[dict[str, Any]]:
    if doc.get("type") not in {"processor", "tool"} or not _has_redaction_semantics(doc):
        return
    config = doc.get("config") if isinstance(doc.get("config"), dict) else {}
    default_entity_types = config.get("default_entity_types") if isinstance(config, dict) else None
    target_names = [
        name
        for name in _io_names(doc)
        if re.search(r"text|markdown|object|candidate|source|packet|document", name, re.IGNORECASE)
    ]
    redact_paths = sorted(set(target_names or ["text"]))
    yield {
        "mask_contract_id": _component_row_id("mask-contract", doc["id"]),
        "context_object_id": context_object["context_object_id"],
        "component_id": doc["id"],
        "mask_kind": "redaction",
        "target_types": doc.get("modality") or [],
        "include_paths": [],
        "exclude_paths": [],
        "redact_paths": redact_paths,
        "policy_trigger": {
            "before_external_model": True,
            "before_publication": True,
            "source_ref": str(path.relative_to(REPO)),
        },
        "redaction_reason": "Manifest declares redaction, PII, PHI, or sensitive-data masking behavior.",
        "reversible": bool(doc.get("reversible") or False),
        "contract": {
            "process_kind": doc.get("process_kind"),
            "replacement_style": config.get("default_replacement_style") if isinstance(config, dict) else None,
            "default_entity_types": default_entity_types or [],
            "hipaa_safe_harbor_categories": (
                config.get("hipaa_safe_harbor_categories") if isinstance(config, dict) else []
            ) or [],
            "definition_source": "repo_seed",
            "definition_hash": definition_hash,
            "source_handle": f"repo://{path.relative_to(REPO)}",
            "body": {
                "reason": (
                    "Manifest has direct redaction/sensitive-data semantics and "
                    "therefore participates in model-destination and publication "
                    "masking policy."
                )
            },
        },
    }


def _axis_rows(component_id: str, axis: str, values: list[str]) -> Iterable[dict[str, str]]:
    for value in values or []:
        yield {"component_id": component_id, axis: value}


def _context_object_row(doc: dict[str, Any], path: Path, definition_hash: str) -> dict[str, Any]:
    return {
        "context_object_id": _context_object_id(doc["id"]),
        "tenant_id": "openhubforai",
        "object_type": f"catalog_{doc['type']}",
        "subkind": doc["type"],
        "title": doc.get("name"),
        "summary": doc.get("description"),
        "source_system": "repo_catalog",
        "native_id": doc["id"],
        "source_url": str(path.relative_to(REPO)),
        "classification": "public",
        "source_handles": [f"repo://{path.relative_to(REPO)}"],
        "facets": {
            "catalog": {
                "component_id": doc["id"],
                "component_type": doc["type"],
                "version": doc.get("version"),
                "definition_hash": definition_hash,
            }
        },
        "document": doc,
    }


def _load_sql(files: dict[str, str]) -> str:
    # COPY in text mode interprets backslash escapes before jsonb parsing. JSONL
    # rows can legitimately contain escaped newlines, tabs, and unicode escapes,
    # so use CSV with control characters that should not occur in generated JSON
    # as delimiter/quote. That preserves each physical JSONL line as one jsonb
    # value while avoiding pre-json unescaping.
    copy_options = "WITH (FORMAT csv, DELIMITER E'\\x02', QUOTE E'\\x01')"
    return f"""-- Review before applying. Generated by scripts/db/catalog_manifest_bridge.py.
BEGIN;

CREATE TEMP TABLE stage_manifest_component_raw (line text);
CREATE TEMP TABLE stage_manifest_component_version_raw (line text);
CREATE TEMP TABLE stage_manifest_industry_raw (line text);
CREATE TEMP TABLE stage_manifest_capability_raw (line text);
CREATE TEMP TABLE stage_manifest_modality_raw (line text);
CREATE TEMP TABLE stage_manifest_tag_raw (line text);
CREATE TEMP TABLE stage_manifest_ref_raw (line text);
CREATE TEMP TABLE stage_manifest_rubric_dimension_raw (line text);
CREATE TEMP TABLE stage_manifest_context_object_raw (line text);
CREATE TEMP TABLE stage_manifest_component_context_object_raw (line text);
CREATE TEMP TABLE stage_manifest_context_mask_contract_raw (line text);
CREATE TEMP TABLE stage_manifest_context_transformer_contract_raw (line text);
CREATE TEMP TABLE stage_manifest_import_batch_raw (line text);
CREATE TEMP TABLE stage_manifest_import_record_raw (line text);

\\copy stage_manifest_component_raw FROM '{files["components"]}' {copy_options}
\\copy stage_manifest_component_version_raw FROM '{files["component_versions"]}' {copy_options}
\\copy stage_manifest_industry_raw FROM '{files["component_industries"]}' {copy_options}
\\copy stage_manifest_capability_raw FROM '{files["component_capabilities"]}' {copy_options}
\\copy stage_manifest_modality_raw FROM '{files["component_modalities"]}' {copy_options}
\\copy stage_manifest_tag_raw FROM '{files["component_tags"]}' {copy_options}
\\copy stage_manifest_ref_raw FROM '{files["component_refs"]}' {copy_options}
\\copy stage_manifest_rubric_dimension_raw FROM '{files["rubric_dimensions"]}' {copy_options}
\\copy stage_manifest_context_object_raw FROM '{files["context_objects"]}' {copy_options}
\\copy stage_manifest_component_context_object_raw FROM '{files["component_context_objects"]}' {copy_options}
\\copy stage_manifest_context_mask_contract_raw FROM '{files["context_mask_contracts"]}' {copy_options}
\\copy stage_manifest_context_transformer_contract_raw FROM '{files["context_transformer_contracts"]}' {copy_options}
\\copy stage_manifest_import_batch_raw FROM '{files["manifest_import_batches"]}' {copy_options}
\\copy stage_manifest_import_record_raw FROM '{files["manifest_import_records"]}' {copy_options}

CREATE TEMP VIEW stage_manifest_component AS SELECT line::jsonb AS line FROM stage_manifest_component_raw;
CREATE TEMP VIEW stage_manifest_component_version AS SELECT line::jsonb AS line FROM stage_manifest_component_version_raw;
CREATE TEMP VIEW stage_manifest_industry AS SELECT line::jsonb AS line FROM stage_manifest_industry_raw;
CREATE TEMP VIEW stage_manifest_capability AS SELECT line::jsonb AS line FROM stage_manifest_capability_raw;
CREATE TEMP VIEW stage_manifest_modality AS SELECT line::jsonb AS line FROM stage_manifest_modality_raw;
CREATE TEMP VIEW stage_manifest_tag AS SELECT line::jsonb AS line FROM stage_manifest_tag_raw;
CREATE TEMP VIEW stage_manifest_ref AS SELECT line::jsonb AS line FROM stage_manifest_ref_raw;
CREATE TEMP VIEW stage_manifest_rubric_dimension AS SELECT line::jsonb AS line FROM stage_manifest_rubric_dimension_raw;
CREATE TEMP VIEW stage_manifest_context_object AS SELECT line::jsonb AS line FROM stage_manifest_context_object_raw;
CREATE TEMP VIEW stage_manifest_component_context_object AS SELECT line::jsonb AS line FROM stage_manifest_component_context_object_raw;
CREATE TEMP VIEW stage_manifest_context_mask_contract AS SELECT line::jsonb AS line FROM stage_manifest_context_mask_contract_raw;
CREATE TEMP VIEW stage_manifest_context_transformer_contract AS SELECT line::jsonb AS line FROM stage_manifest_context_transformer_contract_raw;
CREATE TEMP VIEW stage_manifest_import_batch AS SELECT line::jsonb AS line FROM stage_manifest_import_batch_raw;
CREATE TEMP VIEW stage_manifest_import_record AS SELECT line::jsonb AS line FROM stage_manifest_import_record_raw;

INSERT INTO manifest_import_batch (
  manifest_import_batch_id, source_kind, source_ref, importer, import_mode, policy, summary
)
SELECT
  line->>'manifest_import_batch_id',
  line->>'source_kind',
  line->>'source_ref',
  line->>'importer',
  line->>'import_mode',
  COALESCE(line->'policy', '{{}}'::jsonb),
  COALESCE(line->'summary', '{{}}'::jsonb)
FROM stage_manifest_import_batch
ON CONFLICT (manifest_import_batch_id) DO UPDATE SET
  source_kind=EXCLUDED.source_kind,
  source_ref=EXCLUDED.source_ref,
  importer=EXCLUDED.importer,
  import_mode=EXCLUDED.import_mode,
  policy=EXCLUDED.policy,
  summary=EXCLUDED.summary;

INSERT INTO component (
  id, type, component_layer, control_flow_kind, version, name, description,
  license, lifecycle, trust_boundary, freshness, created, updated,
  superseded_by, deprecated_on, attribution, links, body
)
SELECT
  line->>'id',
  line->>'type',
  line->>'component_layer',
  line->>'control_flow_kind',
  line->>'version',
  line->>'name',
  line->>'description',
  line->>'license',
  line->>'lifecycle',
  line->>'trust_boundary',
  line->>'freshness',
  NULLIF(line->>'created', '')::date,
  NULLIF(line->>'updated', '')::date,
  line->>'superseded_by',
  NULLIF(line->>'deprecated_on', '')::date,
  line->'attribution',
  line->'links',
  line->'body'
FROM stage_manifest_component
ON CONFLICT (id) DO UPDATE SET
  version=EXCLUDED.version,
  name=EXCLUDED.name,
  description=EXCLUDED.description,
  license=EXCLUDED.license,
  lifecycle=EXCLUDED.lifecycle,
  trust_boundary=EXCLUDED.trust_boundary,
  freshness=EXCLUDED.freshness,
  updated=EXCLUDED.updated,
  superseded_by=EXCLUDED.superseded_by,
  deprecated_on=EXCLUDED.deprecated_on,
  attribution=EXCLUDED.attribution,
  links=EXCLUDED.links,
  body=EXCLUDED.body;

INSERT INTO component_version (
  component_version_id, component_id, version, version_status, change_summary,
  definition_source, source_ref, definition_hash, body, activated_at
)
SELECT
  line->>'component_version_id',
  line->>'component_id',
  line->>'version',
  line->>'version_status',
  line->>'change_summary',
  line->>'definition_source',
  line->>'source_ref',
  line->>'definition_hash',
  line->'body',
  now()
FROM stage_manifest_component_version
ON CONFLICT (component_id, version) DO UPDATE SET
  version_status=EXCLUDED.version_status,
  definition_source=EXCLUDED.definition_source,
  source_ref=EXCLUDED.source_ref,
  definition_hash=EXCLUDED.definition_hash,
  body=EXCLUDED.body;

INSERT INTO component_industry (component_id, industry)
SELECT line->>'component_id', line->>'industry' FROM stage_manifest_industry
ON CONFLICT DO NOTHING;
INSERT INTO component_capability (component_id, capability)
SELECT line->>'component_id', line->>'capability' FROM stage_manifest_capability
ON CONFLICT DO NOTHING;
INSERT INTO component_modality (component_id, modality)
SELECT line->>'component_id', line->>'modality' FROM stage_manifest_modality
ON CONFLICT DO NOTHING;
INSERT INTO component_tag (component_id, tag)
SELECT line->>'component_id', line->>'tag' FROM stage_manifest_tag
ON CONFLICT DO NOTHING;
INSERT INTO component_ref (src_id, dst_id, role)
SELECT line->>'src_id', line->>'dst_id', line->>'role' FROM stage_manifest_ref
ON CONFLICT DO NOTHING;

INSERT INTO rubric_dimension (
  rubric_dimension_id, rubric_id, dimension_path, parent_path, dimension_level,
  label, weight, scale, evidence_required, gate, body
)
SELECT
  line->>'rubric_dimension_id',
  line->>'rubric_id',
  line->>'dimension_path',
  line->>'parent_path',
  (line->>'dimension_level')::integer,
  line->>'label',
  (line->>'weight')::numeric,
  line->>'scale',
  line->>'evidence_required',
  COALESCE((line->>'gate')::boolean, false),
  COALESCE(line->'body', '{{}}'::jsonb)
FROM stage_manifest_rubric_dimension
ON CONFLICT (rubric_id, dimension_path) DO UPDATE SET
  parent_path=EXCLUDED.parent_path,
  dimension_level=EXCLUDED.dimension_level,
  label=EXCLUDED.label,
  weight=EXCLUDED.weight,
  scale=EXCLUDED.scale,
  evidence_required=EXCLUDED.evidence_required,
  gate=EXCLUDED.gate,
  body=EXCLUDED.body,
  updated_at=now();

INSERT INTO context_object (
  context_object_id, tenant_id, object_type, subkind, title, summary,
  source_system, native_id, source_url, classification, source_handles,
  facets, document
)
SELECT
  line->>'context_object_id',
  line->>'tenant_id',
  line->>'object_type',
  line->>'subkind',
  line->>'title',
  line->>'summary',
  line->>'source_system',
  line->>'native_id',
  line->>'source_url',
  line->>'classification',
  COALESCE(line->'source_handles', '[]'::jsonb),
  COALESCE(line->'facets', '{{}}'::jsonb),
  COALESCE(line->'document', '{{}}'::jsonb)
FROM stage_manifest_context_object
ON CONFLICT (context_object_id) DO UPDATE SET
  title=EXCLUDED.title,
  summary=EXCLUDED.summary,
  source_url=EXCLUDED.source_url,
  source_handles=EXCLUDED.source_handles,
  facets=EXCLUDED.facets,
  document=EXCLUDED.document,
  updated_at=now();

INSERT INTO component_context_object (
  component_id, context_object_id, role, binding_status, source_ref, binding_hash, body
)
SELECT
  line->>'component_id',
  line->>'context_object_id',
  line->>'role',
  line->>'binding_status',
  line->>'source_ref',
  line->>'binding_hash',
  COALESCE(line->'body', '{{}}'::jsonb)
FROM stage_manifest_component_context_object
ON CONFLICT (component_id, context_object_id, role) DO UPDATE SET
  binding_status=EXCLUDED.binding_status,
  source_ref=EXCLUDED.source_ref,
  binding_hash=EXCLUDED.binding_hash,
  body=EXCLUDED.body,
  updated_at=now();

INSERT INTO context_mask_contract (
  mask_contract_id, context_object_id, component_id, mask_kind, target_types,
  include_paths, exclude_paths, redact_paths, policy_trigger,
  redaction_reason, reversible, contract
)
SELECT
  line->>'mask_contract_id',
  line->>'context_object_id',
  line->>'component_id',
  line->>'mask_kind',
  COALESCE(line->'target_types', '[]'::jsonb),
  COALESCE(line->'include_paths', '[]'::jsonb),
  COALESCE(line->'exclude_paths', '[]'::jsonb),
  COALESCE(line->'redact_paths', '[]'::jsonb),
  COALESCE(line->'policy_trigger', '{{}}'::jsonb),
  line->>'redaction_reason',
  COALESCE((line->>'reversible')::boolean, false),
  COALESCE(line->'contract', '{{}}'::jsonb)
FROM stage_manifest_context_mask_contract
ON CONFLICT (mask_contract_id) DO UPDATE SET
  context_object_id=EXCLUDED.context_object_id,
  component_id=EXCLUDED.component_id,
  mask_kind=EXCLUDED.mask_kind,
  target_types=EXCLUDED.target_types,
  include_paths=EXCLUDED.include_paths,
  exclude_paths=EXCLUDED.exclude_paths,
  redact_paths=EXCLUDED.redact_paths,
  policy_trigger=EXCLUDED.policy_trigger,
  redaction_reason=EXCLUDED.redaction_reason,
  reversible=EXCLUDED.reversible,
  contract=EXCLUDED.contract,
  updated_at=now();

INSERT INTO context_transformer_contract (
  transformer_contract_id, context_object_id, component_id, transformer_kind,
  input_contract, output_contract, deterministic, model_required, lossiness,
  reversible, validation, lineage_policy, contract
)
SELECT
  line->>'transformer_contract_id',
  line->>'context_object_id',
  line->>'component_id',
  line->>'transformer_kind',
  COALESCE(line->'input_contract', '{{}}'::jsonb),
  COALESCE(line->'output_contract', '{{}}'::jsonb),
  CASE WHEN line ? 'deterministic' THEN (line->>'deterministic')::boolean ELSE NULL END,
  COALESCE((line->>'model_required')::boolean, false),
  line->>'lossiness',
  COALESCE((line->>'reversible')::boolean, false),
  COALESCE(line->'validation', '{{}}'::jsonb),
  COALESCE(line->'lineage_policy', '{{}}'::jsonb),
  COALESCE(line->'contract', '{{}}'::jsonb)
FROM stage_manifest_context_transformer_contract
ON CONFLICT (transformer_contract_id) DO UPDATE SET
  context_object_id=EXCLUDED.context_object_id,
  component_id=EXCLUDED.component_id,
  transformer_kind=EXCLUDED.transformer_kind,
  input_contract=EXCLUDED.input_contract,
  output_contract=EXCLUDED.output_contract,
  deterministic=EXCLUDED.deterministic,
  model_required=EXCLUDED.model_required,
  lossiness=EXCLUDED.lossiness,
  reversible=EXCLUDED.reversible,
  validation=EXCLUDED.validation,
  lineage_policy=EXCLUDED.lineage_policy,
  contract=EXCLUDED.contract,
  updated_at=now();

INSERT INTO manifest_import_record (
  manifest_import_record_id, manifest_import_batch_id, component_id,
  component_type, manifest_path, manifest_hash, manifest_updated,
  manifest_lifecycle, manifest_freshness, definition_source, import_status,
  recommended_action, rotted_context_flags, row_counts, source_ref, error_message
)
SELECT
  line->>'manifest_import_record_id',
  line->>'manifest_import_batch_id',
  line->>'component_id',
  line->>'component_type',
  line->>'manifest_path',
  line->>'manifest_hash',
  NULLIF(line->>'manifest_updated', '')::date,
  line->>'manifest_lifecycle',
  line->>'manifest_freshness',
  line->>'definition_source',
  line->>'import_status',
  line->>'recommended_action',
  COALESCE(line->'rotted_context_flags', '[]'::jsonb),
  COALESCE(line->'row_counts', '{{}}'::jsonb),
  line->>'source_ref',
  line->>'error_message'
FROM stage_manifest_import_record
ON CONFLICT (manifest_import_batch_id, manifest_path) DO UPDATE SET
  component_id=EXCLUDED.component_id,
  manifest_hash=EXCLUDED.manifest_hash,
  import_status=EXCLUDED.import_status,
  recommended_action=EXCLUDED.recommended_action,
  rotted_context_flags=EXCLUDED.rotted_context_flags,
  row_counts=EXCLUDED.row_counts,
  error_message=EXCLUDED.error_message;

COMMIT;
"""


def _load_sql_coverage(sql: str, row_files: dict[str, str]) -> dict[str, Any]:
    """Report whether every emitted row file is staged and inserted by load SQL."""
    row_families: list[dict[str, Any]] = []
    issues: list[dict[str, Any]] = []
    copy_count = sql.count("\\copy")
    insert_count = len(re.findall(r"\bINSERT INTO\b", sql))
    expected_row_family_count = len(row_files)

    if copy_count != expected_row_family_count:
        issues.append({
            "severity": "error",
            "code": "copy_statement_count_mismatch",
            "expected": expected_row_family_count,
            "actual": copy_count,
        })

    for row_family, file_path in sorted(row_files.items()):
        stage_name = LOAD_SQL_STAGE_NAMES.get(row_family)
        file_name = Path(file_path).name
        file_referenced = file_name in sql
        path_referenced = file_path in sql
        stage_referenced = bool(stage_name and stage_name in sql)
        entry = {
            "row_family": row_family,
            "file": file_name,
            "path": file_path,
            "stage_name": stage_name,
            "file_referenced": file_referenced,
            "path_referenced": path_referenced,
            "stage_referenced": stage_referenced,
        }
        row_families.append(entry)
        if not file_referenced:
            issues.append({
                "severity": "error",
                "code": "load_sql_missing_file_reference",
                "row_family": row_family,
                "file": file_name,
            })
        if not path_referenced:
            issues.append({
                "severity": "error",
                "code": "load_sql_missing_path_reference",
                "row_family": row_family,
                "path": file_path,
            })
        if not stage_referenced:
            issues.append({
                "severity": "error",
                "code": "load_sql_missing_stage_reference",
                "row_family": row_family,
                "stage_name": stage_name,
            })
    for row_family in sorted(set(row_files) - set(LOAD_SQL_STAGE_NAMES)):
        issues.append({
            "severity": "error",
            "code": "missing_load_sql_stage_mapping",
            "row_family": row_family,
        })

    return {
        "ok": not any(issue["severity"] == "error" for issue in issues),
        "copy_statement_count": copy_count,
        "insert_statement_count": insert_count,
        "expected_row_family_count": expected_row_family_count,
        "row_families": row_families,
        "issues": issues,
    }


def build_bridge_plan(
    *,
    paths: list[Path] | None = None,
    output_dir: Path | None = None,
    dated_review_days: int = 90,
    batch_id: str | None = None,
) -> dict[str, Any]:
    out = output_dir or DEFAULT_OUT
    out.mkdir(parents=True, exist_ok=True)

    batch_id = batch_id or "manifest-import-batch/" + _sha256_text(_utc_now())[7:23]
    components: list[dict[str, Any]] = []
    versions: list[dict[str, Any]] = []
    industries: list[dict[str, str]] = []
    capabilities: list[dict[str, str]] = []
    modalities: list[dict[str, str]] = []
    tags: list[dict[str, str]] = []
    refs: list[dict[str, str]] = []
    rubric_dimensions: list[dict[str, Any]] = []
    context_objects: list[dict[str, Any]] = []
    component_context_objects: list[dict[str, Any]] = []
    context_mask_contracts: list[dict[str, Any]] = []
    context_transformer_contracts: list[dict[str, Any]] = []
    import_records: list[dict[str, Any]] = []
    seen_component_paths: dict[str, str] = {}

    for path in _iter_manifest_paths(paths):
        if not path.exists() or path.suffix not in {".yaml", ".yml"}:
            continue
        doc = _read_yaml(path)
        if doc is None:
            continue
        definition_hash = _manifest_hash(doc)
        flags = _rotted_flags(doc, dated_review_days=dated_review_days)
        component_id = str(doc["id"])
        rel_path = str(path.relative_to(REPO))
        duplicate_of = seen_component_paths.get(component_id)
        if duplicate_of is not None:
            duplicate_flags = flags + [f"duplicate_component_id:{component_id}", f"duplicate_of:{duplicate_of}"]
            import_records.append({
                "manifest_import_record_id": f"manifest-import-record/{definition_hash}",
                "manifest_import_batch_id": batch_id,
                "component_id": component_id,
                "component_type": doc["type"],
                "manifest_path": rel_path,
                "manifest_hash": definition_hash,
                "manifest_updated": doc.get("updated"),
                "manifest_lifecycle": doc.get("lifecycle"),
                "manifest_freshness": doc.get("freshness"),
                "definition_source": "repo_seed",
                "import_status": "skipped",
                "recommended_action": _recommended_action(doc, duplicate_flags),
                "rotted_context_flags": duplicate_flags,
                "row_counts": {
                    "rubric_dimensions": 0,
                    "component_refs": 0,
                    "reason": "duplicate component id skipped before database row emission",
                },
                "source_ref": rel_path,
                "error_message": f"Duplicate component id already mapped from {duplicate_of}",
            })
            continue
        seen_component_paths[component_id] = rel_path
        components.append(_component_row(doc, path, definition_hash))
        versions.append(_component_version_row(doc, path, definition_hash))
        industries.extend(_axis_rows(component_id, "industry", doc.get("industry") or []))
        capabilities.extend(_axis_rows(component_id, "capability", doc.get("capability") or []))
        modalities.extend(_axis_rows(component_id, "modality", doc.get("modality") or []))
        tags.extend(_axis_rows(component_id, "tag", doc.get("tags") or []))
        doc_refs = [
            {"src_id": component_id, "role": role, "dst_id": target}
            for role, target in sorted(set(_walk_refs(doc)))
        ]
        refs.extend(doc_refs)
        dims = list(_rubric_dimension_rows(doc) or [])
        rubric_dimensions.extend(dims)
        context_object = _context_object_row(doc, path, definition_hash)
        context_objects.append(context_object)
        component_context_objects.append({
            "component_id": component_id,
            "context_object_id": context_object["context_object_id"],
            "role": "is_context_object",
            "binding_status": "active",
            "source_ref": rel_path,
            "binding_hash": definition_hash,
            "body": {
                "reason": "Catalog component participates in retrieval, policy, lineage, or evaluation.",
                "seed_path": rel_path,
            },
        })
        transformer_rows = list(
            _processor_transformer_contract_rows(
                doc=doc,
                context_object=context_object,
                path=path,
                definition_hash=definition_hash,
            ) or []
        )
        context_transformer_contracts.extend(transformer_rows)
        mask_rows = list(
            _mask_contract_rows(
                doc=doc,
                context_object=context_object,
                path=path,
                definition_hash=definition_hash,
            ) or []
        )
        context_mask_contracts.extend(mask_rows)
        dimension_context_count = 0
        for dimension_row in dims:
            dimension_context_object = _rubric_dimension_context_object_row(
                doc=doc,
                dimension_row=dimension_row,
                path=path,
                definition_hash=definition_hash,
            )
            context_objects.append(dimension_context_object)
            component_context_objects.append({
                "component_id": component_id,
                "context_object_id": dimension_context_object["context_object_id"],
                "role": "has_rubric_dimension_context",
                "binding_status": "active",
                "source_ref": dimension_context_object["source_url"],
                "binding_hash": definition_hash,
                "body": {
                    "reason": (
                        "Rubric dimensions are context objects so they can be "
                        "retrieved, evaluated, masked, transformed, and audited "
                        "independently of the parent rubric manifest."
                    ),
                    "rubric_dimension_id": dimension_row["rubric_dimension_id"],
                    "dimension_path": dimension_row["dimension_path"],
                },
            })
            dimension_context_count += 1
        import_records.append({
            "manifest_import_record_id": f"manifest-import-record/{definition_hash}",
            "manifest_import_batch_id": batch_id,
            "component_id": component_id,
            "component_type": doc["type"],
            "manifest_path": str(path.relative_to(REPO)),
            "manifest_hash": definition_hash,
            "manifest_updated": doc.get("updated"),
            "manifest_lifecycle": doc.get("lifecycle"),
            "manifest_freshness": doc.get("freshness"),
            "definition_source": "repo_seed",
            "import_status": "mapped",
            "recommended_action": _recommended_action(doc, flags),
            "rotted_context_flags": flags,
            "row_counts": {
                "rubric_dimensions": len(dims),
                "rubric_dimension_context_objects": dimension_context_count,
                "context_mask_contracts": len(mask_rows),
                "context_transformer_contracts": len(transformer_rows),
                "component_refs": len(doc_refs),
            },
            "source_ref": rel_path,
        })

    import_batches = [{
        "manifest_import_batch_id": batch_id,
        "source_kind": "repo_catalog",
        "source_ref": str(CATALOG.relative_to(REPO)),
        "importer": "scripts/db/catalog_manifest_bridge.py",
        "import_mode": "dry_run",
        "policy": {
            "files_are": "seed_export_artifacts",
            "database_is": "operational_truth",
            "dated_review_days": dated_review_days,
            "do_not_delete_catalog_files": True,
        },
        "summary": {
            "component_count": len(components),
            "rubric_dimension_count": len(rubric_dimensions),
            "context_object_count": len(context_objects),
            "context_mask_contract_count": len(context_mask_contracts),
            "context_transformer_contract_count": len(context_transformer_contracts),
            "archive_seed_recommendation_count": sum(1 for row in import_records if row["recommended_action"] == "archive_seed"),
            "review_recommendation_count": sum(1 for row in import_records if row["recommended_action"] == "review"),
        },
    }]

    row_sets: dict[str, list[dict[str, Any]]] = {
        "components": components,
        "component_versions": versions,
        "component_industries": industries,
        "component_capabilities": capabilities,
        "component_modalities": modalities,
        "component_tags": tags,
        "component_refs": refs,
        "rubric_dimensions": rubric_dimensions,
        "context_objects": context_objects,
        "component_context_objects": component_context_objects,
        "context_mask_contracts": context_mask_contracts,
        "context_transformer_contracts": context_transformer_contracts,
        "manifest_import_batches": import_batches,
        "manifest_import_records": import_records,
    }
    files: dict[str, str] = {}
    counts: dict[str, int] = {}
    for name, rows in row_sets.items():
        path = out / f"{name}.jsonl"
        counts[name] = _write_jsonl(path, rows)
        files[name] = str(path)

    row_files = dict(files)
    load_sql_text = _load_sql(row_files)
    load_sql_coverage = _load_sql_coverage(load_sql_text, row_files)
    load_sql = out / "load-catalog-manifests.sql"
    load_sql.write_text(load_sql_text, encoding="utf-8")
    files["load_sql"] = str(load_sql)

    report = {
        "ok": load_sql_coverage["ok"],
        "generated_at": _utc_now(),
        "output_dir": str(out),
        "counts": counts,
        "files": files,
        "load_sql_coverage": load_sql_coverage,
        "safety_notes": [
            "This script does not connect to Postgres.",
            "It does not move, delete, or rewrite catalog manifests.",
            "Generated SQL should be reviewed before use.",
            "Repository manifests remain seed/export artifacts; database rows are operational truth for hosted deployments.",
        ],
    }
    report_path = out / "manifest-import-plan.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    return report


def _self_test() -> int:
    sample = _resource("catalog") / "rubrics" / "baltor-business-object-governance-quality.yaml"
    processor_sample = _resource("catalog") / "processors" / "standardization" / "tabular-schema-canonicalizer.yaml"
    mask_processor_sample = _resource("catalog") / "processors" / "redact" / "pii-text.yaml"
    if not sample.exists():
        raise FileNotFoundError(sample)
    if not processor_sample.exists():
        raise FileNotFoundError(processor_sample)
    if not mask_processor_sample.exists():
        raise FileNotFoundError(mask_processor_sample)
    with tempfile.TemporaryDirectory(prefix="ohh-manifest-bridge-") as tmp:
        report = build_bridge_plan(paths=[sample, processor_sample, mask_processor_sample], output_dir=Path(tmp))
        assert report["counts"]["components"] == 3
        assert report["counts"]["component_versions"] == 3
        assert report["counts"]["rubric_dimensions"] > 0
        expected_context_objects = 1 + report["counts"]["rubric_dimensions"]
        expected_context_objects += 2
        assert report["counts"]["context_objects"] == expected_context_objects
        assert report["counts"]["component_context_objects"] == expected_context_objects
        assert "context_mask_contracts" in report["counts"]
        assert "context_transformer_contracts" in report["counts"]
        assert report["counts"]["context_mask_contracts"] == 1
        assert report["counts"]["context_transformer_contracts"] == 2
        assert Path(report["files"]["load_sql"]).exists()
        assert report["load_sql_coverage"]["ok"]
        assert report["load_sql_coverage"]["copy_statement_count"] == len(report["counts"])
        assert not report["load_sql_coverage"]["issues"]
    print(json.dumps({"ok": True, "self_test": "catalog_manifest_bridge"}, indent=2, sort_keys=True))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Map catalog YAML manifests to Postgres seed/import row sets.")
    parser.add_argument("paths", nargs="*", type=Path, help="Optional manifest paths. Defaults to all catalog manifests.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--dated-review-days", type=int, default=90)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    report = build_bridge_plan(paths=args.paths or None, output_dir=args.output_dir, dated_review_days=args.dated_review_days)
    print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
