#!/usr/bin/env python3
"""scripts.domain_cloud_gcp — WORKABLE (proven + TYPED) deterministic SHAPE leaves for Google Cloud Platform shapes.

ADD-ONLY parallel path (its OWN shard file). It IMPORTS the shared machinery, never edits it:
  * `run_primitive_proof` / `MUTATOR_REGISTRY` / `_receipt` from `scripts.mutator_registry` — the proof-runner EXECUTES
    each pure mutator against a synthetic fixture and flips serves_truth false->true ONLY on a PASSING executed proof;
  * `canonicalize_edge` from `scripts.build_edge_type_retrofit` — folds each leaf's logical edge labels to canonical
    type_ids so every proven leaf is also TYPED (input_edge_type_id + output_edge_type_id) and can chain.

Covers parse / build / extract / validate / emit SHAPES (SYNTHETIC fixtures only, NO real secrets/PII/credentials) for:
  GCS URI (gs://bucket/object) parse+build · BigQuery table reference + parametrized SELECT builder (deterministic
  string, named @params — never a live query) · GCP resource name (projects/*/locations/* collection path) parse+build
  · Pub/Sub message envelope (deterministic base64 wrap/unwrap) + topic reference · GCP IAM binding / member / role
  shapes · Terraform google_* HCL resource block + address. All work is pure string/dict transformation on the SHAPE.

DOMAIN LAWS honored: NO insurance primitives (any domain); synthetic/public shapes only (bucket names, example.com
emails, fake project ids — NO real credentials, PAN, SSN, tokens). The actual GCS/BigQuery/Pub/Sub/IAM/Resource-Manager
API CALLS and any Vertex/Gemini model call are NETWORK / EFFECTFUL: they are NEVER run through the proof runner and
NEVER serve_truth — they are declared as GATED EFFECT candidates (candidate=true, serves_truth=false, effect,
proof_obligation) in a SEPARATE section of the shard, with SEPARATE honest counts.

Deterministic + offline: no network, no LLM, no wall-clock, no RNG (fixed literal manifest timestamp; stable string
seeds only). CLI: --self-test | --write.

Register tuple for the shared proof suite (REPORT ONLY — this module does NOT self-register):
    ("_repos/shared-backend-components/scripts/domain_cloud_gcp.py", "domain_cloud_gcp")
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import base64
import json
import re
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

# IMPORT the shared machinery — never edit it (ADD-ONLY / flexible-multi-path).
from scripts.mutator_registry import (  # noqa: E402
    MUTATOR_REGISTRY,
    _receipt,
    run_primitive_proof,
)
from scripts.build_edge_type_retrofit import canonicalize_edge  # noqa: E402

DOMAIN = "cloud_gcp"
_FIXED_UTC = "2026-07-03"  # fixed literal timestamp — NO wall-clock (repo law: deterministic + offline)

OUT_DIR = _resource("data") / "dev-intel" / "domain_primitives"
OUT_JSONL = OUT_DIR / "domain_cloud_gcp.jsonl"
OUT_MANIFEST = OUT_DIR / "manifest_cloud_gcp.json"


# ── PURE deterministic mutators, contract (payload, **kwargs) -> (output, receipt). Domain-prefixed (`dcg_`) so they
#    never collide with existing registry entries; registered via setdefault (idempotent, never overwrites). ──

# ── Google Cloud Storage URI: gs://<bucket>/<object-path> ──
def dcg_gcs_uri_parse(uri: str, **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    if not uri.startswith("gs://"):
        raise ValueError("not a gs:// URI")
    rest = uri[len("gs://"):]
    bucket, _, obj = rest.partition("/")
    out = {"bucket": bucket, "object": obj}
    return out, _receipt("dcg_gcs_uri_parse", before=uri, after=out, lossless=True, note="gs:// URI -> {bucket, object}; dcg_gcs_uri_build restores")


def dcg_gcs_uri_build(parsed: dict[str, Any], **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = f"gs://{parsed['bucket']}/{parsed['object']}"
    return out, _receipt("dcg_gcs_uri_build", before=parsed, after=out, lossless=True, note="{bucket, object} -> gs:// URI string")


def dcg_gcs_bucket_name(uri: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = uri[len("gs://"):].partition("/")[0]
    return out, _receipt("dcg_gcs_bucket_name", before=uri, after=out, lossless=False, note="extract GCS bucket name from gs:// URI")


def dcg_gcs_object_path(uri: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = uri[len("gs://"):].partition("/")[2]
    return out, _receipt("dcg_gcs_object_path", before=uri, after=out, lossless=False, note="extract GCS object path from gs:// URI")


def dcg_gcs_object_basename(uri: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    obj = uri[len("gs://"):].partition("/")[2]
    out = obj.rsplit("/", 1)[-1]
    return out, _receipt("dcg_gcs_object_basename", before=uri, after=out, lossless=False, note="basename of GCS object path (last '/' segment)")


def dcg_gcs_uri_validate(uri: str, **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    ok = isinstance(uri, str) and uri.startswith("gs://") and "/" in uri[len("gs://"):]
    bucket = uri[len("gs://"):].partition("/")[0] if ok else None
    out = {"valid": ok, "bucket": bucket if ok else None}
    return out, _receipt("dcg_gcs_uri_validate", before=uri, after=out, lossless=False, note="validate gs:// URI shape (scheme + bucket + object)")


# ── BigQuery: table reference project.dataset.table + a DETERMINISTIC parametrized SELECT builder (never a live query) ──
def dcg_bq_table_ref_parse(ref: str, **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    parts = ref.split(".")
    if len(parts) != 3:
        raise ValueError("expected project.dataset.table")
    out = {"project": parts[0], "dataset": parts[1], "table": parts[2]}
    return out, _receipt("dcg_bq_table_ref_parse", before=ref, after=out, lossless=True, note="project.dataset.table -> parts; dcg_bq_table_ref_build restores")


def dcg_bq_table_ref_build(parsed: dict[str, Any], **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = f"{parsed['project']}.{parsed['dataset']}.{parsed['table']}"
    return out, _receipt("dcg_bq_table_ref_build", before=parsed, after=out, lossless=True, note="{project, dataset, table} -> table reference string")


def dcg_bq_backtick_ref(ref: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = f"`{ref}`"
    return out, _receipt("dcg_bq_backtick_ref", before=ref, after=out, lossless=False, note="wrap a BigQuery table reference in backticks")


def dcg_bq_select_builder(spec: dict[str, Any], **_kw: Any) -> tuple[str, dict[str, Any]]:
    cols = spec.get("columns") or []
    select_list = ", ".join(cols) if cols else "*"
    sql = f"SELECT {select_list} FROM `{spec['table_ref']}`"
    filters = spec.get("filters") or []
    if filters:
        conds = " AND ".join(f"{c} = @{c}" for c in filters)
        sql += f" WHERE {conds}"
    limit = spec.get("limit")
    if limit is not None:
        sql += f" LIMIT {int(limit)}"
    return sql, _receipt("dcg_bq_select_builder", before=spec, after=sql, lossless=False, note="build a DETERMINISTIC parametrized SELECT (named @params; never executed)")


def dcg_bq_param_placeholder_count(sql: str, **_kw: Any) -> tuple[int, dict[str, Any]]:
    out = len(set(re.findall(r"@(\w+)", sql)))
    return out, _receipt("dcg_bq_param_placeholder_count", before=sql, after=out, lossless=False, note="count DISTINCT named @params in a BigQuery SQL string")


# ── GCP resource name: ordered collection/id path, e.g. projects/{p}/locations/{l}/services/{s} ──
def dcg_resource_name_parse(name: str, **_kw: Any) -> tuple[dict[str, str], dict[str, Any]]:
    parts = name.split("/")
    if len(parts) % 2 != 0:
        raise ValueError("resource name must have even segment count (collection/id pairs)")
    out = {parts[i]: parts[i + 1] for i in range(0, len(parts), 2)}
    return out, _receipt("dcg_resource_name_parse", before=name, after=out, lossless=True, note="collection/id resource name -> {collection: id}; dcg_resource_name_build restores")


def dcg_resource_name_build(parsed: dict[str, str], **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = "/".join(f"{k}/{v}" for k, v in parsed.items())
    return out, _receipt("dcg_resource_name_build", before=parsed, after=out, lossless=True, note="{collection: id} -> collection/id resource name string")


def dcg_resource_name_project(name: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    parts = name.split("/")
    out = ""
    for i in range(0, len(parts) - 1, 2):
        if parts[i] == "projects":
            out = parts[i + 1]
            break
    return out, _receipt("dcg_resource_name_project", before=name, after=out, lossless=False, note="extract the projects/{id} project id from a resource name")


def dcg_resource_name_collection_id(name: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    parts = name.split("/")
    out = parts[-2] if len(parts) >= 2 else ""
    return out, _receipt("dcg_resource_name_collection_id", before=name, after=out, lossless=False, note="last collection id of a resource name (second-to-last segment)")


def dcg_resource_name_leaf_id(name: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = name.split("/")[-1]
    return out, _receipt("dcg_resource_name_leaf_id", before=name, after=out, lossless=False, note="leaf id of a resource name (last segment)")


# ── Pub/Sub: message envelope (deterministic base64 wrap/unwrap) + topic reference ──
def dcg_pubsub_envelope_wrap(data: str, attributes: dict[str, str] | None = None, **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    encoded = base64.b64encode(data.encode("utf-8")).decode("ascii")
    out = {"message": {"data": encoded, "attributes": attributes or {}}}
    return out, _receipt("dcg_pubsub_envelope_wrap", before=data, after=out, lossless=True, note="text -> Pub/Sub envelope (base64 data); dcg_pubsub_envelope_unwrap restores the text")


def dcg_pubsub_envelope_unwrap(envelope: dict[str, Any], **_kw: Any) -> tuple[str, dict[str, Any]]:
    encoded = envelope["message"]["data"]
    out = base64.b64decode(encoded.encode("ascii")).decode("utf-8")
    return out, _receipt("dcg_pubsub_envelope_unwrap", before=envelope, after=out, lossless=True, note="Pub/Sub envelope -> decoded text payload")


def dcg_pubsub_topic_ref_parse(ref: str, **_kw: Any) -> tuple[dict[str, str], dict[str, Any]]:
    m = re.match(r"^projects/(?P<project>[^/]+)/topics/(?P<topic>[^/]+)$", ref)
    if not m:
        raise ValueError("expected projects/{p}/topics/{t}")
    out = {"project": m.group("project"), "topic": m.group("topic")}
    return out, _receipt("dcg_pubsub_topic_ref_parse", before=ref, after=out, lossless=True, note="Pub/Sub topic ref -> {project, topic}; dcg_pubsub_topic_ref_build restores")


def dcg_pubsub_topic_ref_build(parsed: dict[str, str], **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = f"projects/{parsed['project']}/topics/{parsed['topic']}"
    return out, _receipt("dcg_pubsub_topic_ref_build", before=parsed, after=out, lossless=True, note="{project, topic} -> Pub/Sub topic reference string")


def dcg_pubsub_attributes_extract(envelope: dict[str, Any], **_kw: Any) -> tuple[dict[str, str], dict[str, Any]]:
    out = dict(envelope.get("message", {}).get("attributes", {}))
    return out, _receipt("dcg_pubsub_attributes_extract", before=envelope, after=out, lossless=False, note="extract the attributes map from a Pub/Sub envelope")


# ── GCP IAM: binding / member / role shapes (synthetic example.com principals — no real identities) ──
def dcg_iam_binding_build(spec: dict[str, Any], **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    out = {"role": spec["role"], "members": sorted(set(spec.get("members") or []))}
    return out, _receipt("dcg_iam_binding_build", before=spec, after=out, lossless=False, note="build an IAM binding: role + deduped sorted members (deterministic)")


def dcg_iam_member_parse(member: str, **_kw: Any) -> tuple[dict[str, str], dict[str, Any]]:
    typ, sep, ident = member.partition(":")
    if not sep:
        raise ValueError("expected <type>:<identifier>")
    out = {"type": typ, "identifier": ident}
    return out, _receipt("dcg_iam_member_parse", before=member, after=out, lossless=True, note="IAM member -> {type, identifier}; dcg_iam_member_build restores")


def dcg_iam_member_build(parsed: dict[str, str], **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = f"{parsed['type']}:{parsed['identifier']}"
    return out, _receipt("dcg_iam_member_build", before=parsed, after=out, lossless=True, note="{type, identifier} -> IAM member string")


def dcg_iam_role_short_name(role: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = role[len("roles/"):] if role.startswith("roles/") else role
    return out, _receipt("dcg_iam_role_short_name", before=role, after=out, lossless=False, note="strip the 'roles/' prefix from a predefined IAM role id")


def dcg_iam_policy_add_member(spec: dict[str, Any], **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    role, member = spec["role"], spec["member"]
    bindings = [{"role": b["role"], "members": list(b.get("members") or [])} for b in spec.get("bindings") or []]
    found = False
    for b in bindings:
        if b["role"] == role:
            b["members"] = sorted(set(b["members"]) | {member})
            found = True
    if not found:
        bindings.append({"role": role, "members": [member]})
    bindings.sort(key=lambda b: b["role"])
    out = {"bindings": bindings}
    return out, _receipt("dcg_iam_policy_add_member", before=spec, after=out, lossless=False, note="add a member to an IAM policy binding (deterministic: deduped, sorted)")


# ── Terraform google_* HCL resource block + address ──
def dcg_tf_google_block_build(spec: dict[str, Any], **_kw: Any) -> tuple[str, dict[str, Any]]:
    rtype, name = spec["resource_type"], spec["name"]
    args = spec.get("args") or {}
    lines = [f'resource "{rtype}" "{name}" {{']
    for k in sorted(args):
        v = args[k]
        if isinstance(v, bool):
            rendered = "true" if v else "false"
        elif isinstance(v, str):
            rendered = f'"{v}"'
        else:
            rendered = str(v)
        lines.append(f"  {k} = {rendered}")
    lines.append("}")
    out = "\n".join(lines)
    return out, _receipt("dcg_tf_google_block_build", before=spec, after=out, lossless=False, note="build a Terraform google_* HCL resource block (deterministic: keys sorted)")


def dcg_tf_resource_address(spec: dict[str, str], **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = f"{spec['resource_type']}.{spec['name']}"
    return out, _receipt("dcg_tf_resource_address", before=spec, after=out, lossless=True, note="{resource_type, name} -> Terraform resource address; dcg_tf_address_parse restores")


def dcg_tf_address_parse(address: str, **_kw: Any) -> tuple[dict[str, str], dict[str, Any]]:
    rtype, sep, name = address.partition(".")
    if not sep:
        raise ValueError("expected <resource_type>.<name>")
    out = {"resource_type": rtype, "name": name}
    return out, _receipt("dcg_tf_address_parse", before=address, after=out, lossless=True, note="Terraform resource address -> {resource_type, name}")


def dcg_tf_block_arg_count(spec: dict[str, Any], **_kw: Any) -> tuple[int, dict[str, Any]]:
    out = len(spec.get("args") or {})
    return out, _receipt("dcg_tf_block_arg_count", before=spec, after=out, lossless=False, note="count arguments in a Terraform block spec")


#: new pure mutators to plug into the shared registry (idempotent setdefault — never overwrites an existing entry)
_NEW_MUTATORS = {
    "dcg_gcs_uri_parse": dcg_gcs_uri_parse, "dcg_gcs_uri_build": dcg_gcs_uri_build,
    "dcg_gcs_bucket_name": dcg_gcs_bucket_name, "dcg_gcs_object_path": dcg_gcs_object_path,
    "dcg_gcs_object_basename": dcg_gcs_object_basename, "dcg_gcs_uri_validate": dcg_gcs_uri_validate,
    "dcg_bq_table_ref_parse": dcg_bq_table_ref_parse, "dcg_bq_table_ref_build": dcg_bq_table_ref_build,
    "dcg_bq_backtick_ref": dcg_bq_backtick_ref, "dcg_bq_select_builder": dcg_bq_select_builder,
    "dcg_bq_param_placeholder_count": dcg_bq_param_placeholder_count,
    "dcg_resource_name_parse": dcg_resource_name_parse, "dcg_resource_name_build": dcg_resource_name_build,
    "dcg_resource_name_project": dcg_resource_name_project,
    "dcg_resource_name_collection_id": dcg_resource_name_collection_id,
    "dcg_resource_name_leaf_id": dcg_resource_name_leaf_id,
    "dcg_pubsub_envelope_wrap": dcg_pubsub_envelope_wrap, "dcg_pubsub_envelope_unwrap": dcg_pubsub_envelope_unwrap,
    "dcg_pubsub_topic_ref_parse": dcg_pubsub_topic_ref_parse, "dcg_pubsub_topic_ref_build": dcg_pubsub_topic_ref_build,
    "dcg_pubsub_attributes_extract": dcg_pubsub_attributes_extract,
    "dcg_iam_binding_build": dcg_iam_binding_build, "dcg_iam_member_parse": dcg_iam_member_parse,
    "dcg_iam_member_build": dcg_iam_member_build, "dcg_iam_role_short_name": dcg_iam_role_short_name,
    "dcg_iam_policy_add_member": dcg_iam_policy_add_member,
    "dcg_tf_google_block_build": dcg_tf_google_block_build, "dcg_tf_resource_address": dcg_tf_resource_address,
    "dcg_tf_address_parse": dcg_tf_address_parse, "dcg_tf_block_arg_count": dcg_tf_block_arg_count,
}


def register_new_mutators() -> None:
    """Plug the domain's pure mutators into the shared MUTATOR_REGISTRY (registration, not a rewrite). Idempotent."""
    for name, fn in _NEW_MUTATORS.items():
        MUTATOR_REGISTRY.setdefault(name, fn)


register_new_mutators()


# ── proven-deterministic leaves: each a REAL SHAPE capability with a synthetic fixture + expected (+ inverse where a
#    roundtrip holds). spec fields: id, mutator, fixture, expected, args?, inverse?, format, input_edge, output_edge ──
LEAF_SPECS: list[dict[str, Any]] = [
    # GCS URI
    {"id": "prim:leaf:dcg_gcs_uri_parse", "mutator": "dcg_gcs_uri_parse", "format": "gcs_uri",
     "fixture": "gs://my-bucket/data/reports/q1.csv", "expected": {"bucket": "my-bucket", "object": "data/reports/q1.csv"},
     "inverse": "dcg_gcs_uri_build", "input_edge": "GcsUri", "output_edge": "GcsUriParts"},
    {"id": "prim:leaf:dcg_gcs_uri_build", "mutator": "dcg_gcs_uri_build", "format": "gcs_uri",
     "fixture": {"bucket": "my-bucket", "object": "a/b.txt"}, "expected": "gs://my-bucket/a/b.txt",
     "inverse": "dcg_gcs_uri_parse", "input_edge": "GcsUriParts", "output_edge": "GcsUri"},
    {"id": "prim:leaf:dcg_gcs_bucket_name", "mutator": "dcg_gcs_bucket_name", "format": "gcs_uri",
     "fixture": "gs://assets-prod/logo.png", "expected": "assets-prod", "input_edge": "GcsUri", "output_edge": "BucketName"},
    {"id": "prim:leaf:dcg_gcs_object_path", "mutator": "dcg_gcs_object_path", "format": "gcs_uri",
     "fixture": "gs://assets-prod/img/logo.png", "expected": "img/logo.png", "input_edge": "GcsUri", "output_edge": "ObjectPath"},
    {"id": "prim:leaf:dcg_gcs_object_basename", "mutator": "dcg_gcs_object_basename", "format": "gcs_uri",
     "fixture": "gs://assets-prod/img/deep/logo.png", "expected": "logo.png", "input_edge": "GcsUri", "output_edge": "ObjectBasename"},
    {"id": "prim:leaf:dcg_gcs_uri_validate", "mutator": "dcg_gcs_uri_validate", "format": "gcs_uri",
     "fixture": "gs://bucket-x/key", "expected": {"valid": True, "bucket": "bucket-x"},
     "input_edge": "GcsUri", "output_edge": "ValidationResult"},

    # BigQuery
    {"id": "prim:leaf:dcg_bq_table_ref_parse", "mutator": "dcg_bq_table_ref_parse", "format": "bigquery_ref",
     "fixture": "my-proj.analytics.events", "expected": {"project": "my-proj", "dataset": "analytics", "table": "events"},
     "inverse": "dcg_bq_table_ref_build", "input_edge": "BigQueryTableRef", "output_edge": "BigQueryTableRefParts"},
    {"id": "prim:leaf:dcg_bq_table_ref_build", "mutator": "dcg_bq_table_ref_build", "format": "bigquery_ref",
     "fixture": {"project": "my-proj", "dataset": "sales", "table": "orders"}, "expected": "my-proj.sales.orders",
     "inverse": "dcg_bq_table_ref_parse", "input_edge": "BigQueryTableRefParts", "output_edge": "BigQueryTableRef"},
    {"id": "prim:leaf:dcg_bq_backtick_ref", "mutator": "dcg_bq_backtick_ref", "format": "bigquery_ref",
     "fixture": "my-proj.analytics.events", "expected": "`my-proj.analytics.events`",
     "input_edge": "BigQueryTableRef", "output_edge": "BigQueryBacktickRef"},
    {"id": "prim:leaf:dcg_bq_select_builder", "mutator": "dcg_bq_select_builder", "format": "bigquery_sql",
     "fixture": {"table_ref": "my-proj.analytics.events", "columns": ["event_id", "name"], "filters": ["status"], "limit": 100},
     "expected": "SELECT event_id, name FROM `my-proj.analytics.events` WHERE status = @status LIMIT 100",
     "input_edge": "BigQuerySelectSpec", "output_edge": "BigQuerySql"},
    {"id": "prim:leaf:dcg_bq_param_placeholder_count", "mutator": "dcg_bq_param_placeholder_count", "format": "bigquery_sql",
     "fixture": "SELECT * FROM `p.d.t` WHERE a = @a AND b = @b AND c = @a", "expected": 2,
     "input_edge": "BigQuerySql", "output_edge": "Count"},

    # GCP resource name
    {"id": "prim:leaf:dcg_resource_name_parse", "mutator": "dcg_resource_name_parse", "format": "gcp_resource_name",
     "fixture": "projects/my-proj/locations/us-central1/services/api",
     "expected": {"projects": "my-proj", "locations": "us-central1", "services": "api"},
     "inverse": "dcg_resource_name_build", "input_edge": "GcpResourceName", "output_edge": "GcpResourceNameParts"},
    {"id": "prim:leaf:dcg_resource_name_build", "mutator": "dcg_resource_name_build", "format": "gcp_resource_name",
     "fixture": {"projects": "my-proj", "topics": "ingest"}, "expected": "projects/my-proj/topics/ingest",
     "inverse": "dcg_resource_name_parse", "input_edge": "GcpResourceNameParts", "output_edge": "GcpResourceName"},
    {"id": "prim:leaf:dcg_resource_name_project", "mutator": "dcg_resource_name_project", "format": "gcp_resource_name",
     "fixture": "projects/my-proj/locations/eu/functions/fn1", "expected": "my-proj",
     "input_edge": "GcpResourceName", "output_edge": "ProjectId"},
    {"id": "prim:leaf:dcg_resource_name_collection_id", "mutator": "dcg_resource_name_collection_id", "format": "gcp_resource_name",
     "fixture": "projects/my-proj/locations/eu/functions/fn1", "expected": "functions",
     "input_edge": "GcpResourceName", "output_edge": "CollectionId"},
    {"id": "prim:leaf:dcg_resource_name_leaf_id", "mutator": "dcg_resource_name_leaf_id", "format": "gcp_resource_name",
     "fixture": "projects/my-proj/locations/eu/functions/fn1", "expected": "fn1",
     "input_edge": "GcpResourceName", "output_edge": "LeafId"},

    # Pub/Sub
    {"id": "prim:leaf:dcg_pubsub_envelope_wrap", "mutator": "dcg_pubsub_envelope_wrap", "format": "pubsub_message",
     "fixture": "hello world", "args": {"attributes": {"origin": "test"}},
     "expected": {"message": {"data": base64.b64encode(b"hello world").decode("ascii"), "attributes": {"origin": "test"}}},
     "inverse": "dcg_pubsub_envelope_unwrap", "input_edge": "PubSubPayloadText", "output_edge": "PubSubEnvelope"},
    {"id": "prim:leaf:dcg_pubsub_envelope_unwrap", "mutator": "dcg_pubsub_envelope_unwrap", "format": "pubsub_message",
     "fixture": {"message": {"data": base64.b64encode(b"payload-42").decode("ascii"), "attributes": {}}},
     "expected": "payload-42", "input_edge": "PubSubEnvelope", "output_edge": "PubSubPayloadText"},
    {"id": "prim:leaf:dcg_pubsub_topic_ref_parse", "mutator": "dcg_pubsub_topic_ref_parse", "format": "pubsub_message",
     "fixture": "projects/my-proj/topics/ingest", "expected": {"project": "my-proj", "topic": "ingest"},
     "inverse": "dcg_pubsub_topic_ref_build", "input_edge": "PubSubTopicRef", "output_edge": "PubSubTopicRefParts"},
    {"id": "prim:leaf:dcg_pubsub_topic_ref_build", "mutator": "dcg_pubsub_topic_ref_build", "format": "pubsub_message",
     "fixture": {"project": "my-proj", "topic": "events"}, "expected": "projects/my-proj/topics/events",
     "inverse": "dcg_pubsub_topic_ref_parse", "input_edge": "PubSubTopicRefParts", "output_edge": "PubSubTopicRef"},
    {"id": "prim:leaf:dcg_pubsub_attributes_extract", "mutator": "dcg_pubsub_attributes_extract", "format": "pubsub_message",
     "fixture": {"message": {"data": "eA==", "attributes": {"k1": "v1", "k2": "v2"}}}, "expected": {"k1": "v1", "k2": "v2"},
     "input_edge": "PubSubEnvelope", "output_edge": "AttributesMap"},

    # GCP IAM
    {"id": "prim:leaf:dcg_iam_binding_build", "mutator": "dcg_iam_binding_build", "format": "gcp_iam_binding",
     "fixture": {"role": "roles/storage.objectViewer", "members": ["user:b@example.com", "user:a@example.com", "user:a@example.com"]},
     "expected": {"role": "roles/storage.objectViewer", "members": ["user:a@example.com", "user:b@example.com"]},
     "input_edge": "IamBindingSpec", "output_edge": "IamBinding"},
    {"id": "prim:leaf:dcg_iam_member_parse", "mutator": "dcg_iam_member_parse", "format": "gcp_iam_binding",
     "fixture": "serviceAccount:svc@my-proj.iam.gserviceaccount.com",
     "expected": {"type": "serviceAccount", "identifier": "svc@my-proj.iam.gserviceaccount.com"},
     "inverse": "dcg_iam_member_build", "input_edge": "IamMember", "output_edge": "IamMemberParts"},
    {"id": "prim:leaf:dcg_iam_member_build", "mutator": "dcg_iam_member_build", "format": "gcp_iam_binding",
     "fixture": {"type": "user", "identifier": "alice@example.com"}, "expected": "user:alice@example.com",
     "inverse": "dcg_iam_member_parse", "input_edge": "IamMemberParts", "output_edge": "IamMember"},
    {"id": "prim:leaf:dcg_iam_role_short_name", "mutator": "dcg_iam_role_short_name", "format": "gcp_iam_binding",
     "fixture": "roles/bigquery.dataViewer", "expected": "bigquery.dataViewer",
     "input_edge": "IamRoleId", "output_edge": "IamRoleShortName"},
    {"id": "prim:leaf:dcg_iam_policy_add_member", "mutator": "dcg_iam_policy_add_member", "format": "gcp_iam_binding",
     "fixture": {"bindings": [{"role": "roles/viewer", "members": ["user:a@example.com"]}],
                 "role": "roles/viewer", "member": "user:b@example.com"},
     "expected": {"bindings": [{"role": "roles/viewer", "members": ["user:a@example.com", "user:b@example.com"]}]},
     "input_edge": "IamPolicyAddSpec", "output_edge": "IamPolicy"},

    # Terraform google_*
    {"id": "prim:leaf:dcg_tf_google_block_build", "mutator": "dcg_tf_google_block_build", "format": "terraform_google_block",
     "fixture": {"resource_type": "google_storage_bucket", "name": "assets",
                 "args": {"name": "my-assets", "location": "US", "force_destroy": True}},
     "expected": 'resource "google_storage_bucket" "assets" {\n  force_destroy = true\n  location = "US"\n  name = "my-assets"\n}',
     "input_edge": "TerraformBlockSpec", "output_edge": "TerraformHcl"},
    {"id": "prim:leaf:dcg_tf_resource_address", "mutator": "dcg_tf_resource_address", "format": "terraform_google_block",
     "fixture": {"resource_type": "google_storage_bucket", "name": "assets"}, "expected": "google_storage_bucket.assets",
     "inverse": "dcg_tf_address_parse", "input_edge": "TerraformAddressSpec", "output_edge": "TerraformAddress"},
    {"id": "prim:leaf:dcg_tf_address_parse", "mutator": "dcg_tf_address_parse", "format": "terraform_google_block",
     "fixture": "google_pubsub_topic.ingest", "expected": {"resource_type": "google_pubsub_topic", "name": "ingest"},
     "input_edge": "TerraformAddress", "output_edge": "TerraformAddressSpec"},
    {"id": "prim:leaf:dcg_tf_block_arg_count", "mutator": "dcg_tf_block_arg_count", "format": "terraform_google_block",
     "fixture": {"resource_type": "google_bigquery_dataset", "name": "ds", "args": {"dataset_id": "ds", "location": "US"}},
     "expected": 2, "input_edge": "TerraformBlockSpec", "output_edge": "Count"},
]

#: deliberately-wrong leaf — the proof gate MUST leave it candidate (never persisted as proven-deterministic)
NEGATIVE_SPEC: dict[str, Any] = {
    "id": "prim:leaf:dcg_WRONG_expected", "mutator": "dcg_gcs_bucket_name", "format": "gcs_uri",
    "fixture": "gs://real-bucket/x", "expected": "WRONG", "input_edge": "GcsUri", "output_edge": "BucketName"}


# ── GATED-EFFECT candidates: NETWORK / EFFECTFUL GCP capabilities. NEVER run through the proof runner, NEVER
#    serve_truth. Each declares effect + proof_obligation (a live integration test with a credential) + typed edges. ──
GATED_EFFECT_SPECS: list[dict[str, Any]] = [
    {"id": "prim:gated:dcg_gcs_object_download", "capability": "download a GCS object (GET storage.objects.get) into bytes",
     "effect": "network_read", "proof_obligation": "live integration test against a GCS bucket with a service-account credential",
     "input_edge": "GcsUri", "output_edge": "ObjectBytes", "format": "gcs_uri"},
    {"id": "prim:gated:dcg_gcs_object_upload", "capability": "upload bytes to a GCS object (storage.objects.insert)",
     "effect": "network_write", "proof_obligation": "live integration test writing to a GCS bucket with a service-account credential",
     "input_edge": "ObjectBytes", "output_edge": "GcsUri", "format": "gcs_uri"},
    {"id": "prim:gated:dcg_bq_query_job_run", "capability": "run a BigQuery query job (jobs.insert) and wait for completion",
     "effect": "network_write", "proof_obligation": "live integration test against a BigQuery dataset with a credential (billable)",
     "input_edge": "BigQuerySql", "output_edge": "BigQueryJobRef", "format": "bigquery_sql"},
    {"id": "prim:gated:dcg_bq_results_fetch", "capability": "fetch rows of a completed BigQuery job (jobs.getQueryResults)",
     "effect": "network_read", "proof_obligation": "live integration test fetching results for a job with a credential",
     "input_edge": "BigQueryJobRef", "output_edge": "RowSet", "format": "bigquery_sql"},
    {"id": "prim:gated:dcg_pubsub_publish", "capability": "publish a message to a Pub/Sub topic (topics.publish)",
     "effect": "network_write", "proof_obligation": "live integration test publishing to a Pub/Sub topic with a credential",
     "input_edge": "PubSubEnvelope", "output_edge": "PubSubMessageId", "format": "pubsub_message"},
    {"id": "prim:gated:dcg_iam_set_policy", "capability": "set an IAM policy on a resource (setIamPolicy)",
     "effect": "network_write", "proof_obligation": "live integration test against a GCP resource with an owner credential",
     "input_edge": "IamPolicy", "output_edge": "IamPolicy", "format": "gcp_iam_binding"},
    {"id": "prim:gated:dcg_resourcemanager_get_project", "capability": "read project metadata (projects.get) from Resource Manager",
     "effect": "network_read", "proof_obligation": "live integration test against Resource Manager with a credential",
     "input_edge": "GcpResourceName", "output_edge": "ProjectMetadata", "format": "gcp_resource_name"},
    {"id": "prim:gated:dcg_vertex_gemini_generate", "capability": "Vertex AI Gemini text generation call",
     "effect": "model_call", "proof_obligation": "live model call with a Vertex AI credential; output is candidate advice, never truth",
     "input_edge": "PromptText", "output_edge": "GeneratedText", "format": "cloud_gcp"},
]


def _prove_one(spec: dict[str, Any]) -> dict[str, Any]:
    return run_primitive_proof(
        spec["id"], spec["mutator"], spec["fixture"], spec["expected"],
        mutator_args=spec.get("args") or {}, has_inverse=spec.get("inverse"),
    )


def prove_all() -> list[tuple[dict[str, Any], dict[str, Any]]]:
    """Run every declared deterministic leaf through the imported executed-proof runner. Returns [(spec, receipt), ...]."""
    return [(s, _prove_one(s)) for s in LEAF_SPECS]


def build_proven_rows() -> list[dict[str, Any]]:
    """Persist-ready rows for leaves whose executed proof PASSED — TYPED via canonicalize_edge (workable == typed)."""
    rows: list[dict[str, Any]] = []
    for spec, receipt in prove_all():
        if receipt["serves_truth"] is not True:
            continue  # a failing / wrong-expected leaf stays candidate and is NOT persisted (the gate is the point)
        rows.append({
            "primitive_id": receipt["primitive_id"],
            "mutator": receipt["mutator"],
            "domain": DOMAIN,
            "format": spec["format"],
            "row_section": "proven_deterministic",
            "candidate": False,
            "serves_truth": True,
            "verification_level": "L7_executed_proof",
            "input_edge": spec["input_edge"],
            "output_edge": spec["output_edge"],
            "input_edge_type_id": canonicalize_edge(spec["input_edge"]),
            "output_edge_type_id": canonicalize_edge(spec["output_edge"]),
            "has_inverse": spec.get("inverse"),
            "proofs": [p["name"] for p in receipt["proofs"] if p["passed"]],
        })
    return rows


def build_gated_rows() -> list[dict[str, Any]]:
    """Gated-effect candidate rows — NEVER proven, NEVER serves_truth; typed so they still declare their edges."""
    rows: list[dict[str, Any]] = []
    for spec in GATED_EFFECT_SPECS:
        rows.append({
            "primitive_id": spec["id"],
            "domain": DOMAIN,
            "format": spec["format"],
            "row_section": "gated_effect_candidate",
            "capability": spec["capability"],
            "candidate": True,
            "serves_truth": False,
            "effect": spec["effect"],
            "proof_obligation": spec["proof_obligation"],
            "input_edge": spec["input_edge"],
            "output_edge": spec["output_edge"],
            "input_edge_type_id": canonicalize_edge(spec["input_edge"]),
            "output_edge_type_id": canonicalize_edge(spec["output_edge"]),
        })
    return rows


def build_manifest(proven: list[dict[str, Any]], gated: list[dict[str, Any]]) -> dict[str, Any]:
    typed = [r for r in proven if r["input_edge_type_id"] and r["output_edge_type_id"]]
    return {
        "record_type": "domain_primitive_shard_manifest",
        "domain": DOMAIN,
        "generator": "scripts/domain_cloud_gcp.py",
        "generated_utc": _FIXED_UTC,
        "formats_covered": sorted({s["format"] for s in LEAF_SPECS}),
        # SEPARATE, honest counts (proven-deterministic vs gated-effect candidate).
        "defined_deterministic_count": len(LEAF_SPECS),
        "proven_deterministic": len(proven),
        "typed": len(typed),
        "gated_effect_candidates": len(gated),
        "gated_effect_by_effect": {e: sum(1 for r in gated if r["effect"] == e)
                                   for e in sorted({r["effect"] for r in gated})},
        "verification_level": "L7_executed_proof",
        "proven_primitive_ids": sorted(r["primitive_id"] for r in proven),
        "gated_effect_primitive_ids": sorted(r["primitive_id"] for r in gated),
        "note": "proven_deterministic rows: serves_truth=true set ONLY by an executed passing proof (run_primitive_proof, "
                "imported from scripts/mutator_registry.py); every row TYPED via canonicalize_edge (imported from "
                "scripts/build_edge_type_retrofit.py). gated_effect_candidate rows: the actual GCS/BigQuery/Pub/Sub/IAM/"
                "Resource-Manager API calls + any Vertex/Gemini model call are NEVER proven and stay candidate/"
                "serves_truth=false with an effect + proof_obligation. Synthetic/public shapes only; NO insurance. "
                "Counts are separate and honest.",
    }


def write_shard() -> dict[str, Any]:
    proven = build_proven_rows()
    gated = build_gated_rows()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    # Both sections written to the SAME shard, each row self-labels via row_section.
    all_rows = proven + gated
    OUT_JSONL.write_text(
        "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in all_rows), encoding="utf-8")
    manifest = build_manifest(proven, gated)
    OUT_MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def self_test() -> int:
    proven = prove_all()
    rows = build_proven_rows()
    gated = build_gated_rows()
    ids = [r["primitive_id"] for r in rows]
    typed = [r for r in rows if r["input_edge_type_id"] and r["output_edge_type_id"]]
    roundtrip_specs = [s for s in LEAF_SPECS if s.get("inverse")]
    proven_by_id = {r["primitive_id"]: r for (s, r) in proven}

    # deliberately-wrong leaf must stay candidate (proof gate is real) — and never enter the proven section
    wrong = _prove_one(NEGATIVE_SPEC)
    # a second wrong path: an un-runnable fixture -> execution error -> not promoted
    err = run_primitive_proof("prim:leaf:dcg_EXEC_ERROR", "dcg_gcs_uri_parse", object(), "irrelevant")

    manifest = build_manifest(rows, gated)
    valid_effects = {"network_read", "network_write", "model_call", "file_write"}
    target_formats = {"gcs_uri", "bigquery_ref", "bigquery_sql", "gcp_resource_name", "pubsub_message",
                      "gcp_iam_binding", "terraform_google_block"}

    checks: list[tuple[str, bool]] = [
        (">=25 deterministic leaves declared", len(LEAF_SPECS) >= 25),
        ("unique proven primitive ids", len(set(ids)) == len(ids)),
        (">=25 leaves PROVE serves_truth=true via an executed proof", len(rows) >= 25),
        ("every proven receipt is L7_executed_proof with all sub-proofs passing",
         all(r["verification_level"] == "L7_executed_proof" and all(p["passed"] for p in r["proofs"])
             for (_s, r) in proven if r["serves_truth"] is True)),
        ("all declared leaves proved (none silently dropped)", len(rows) == len(LEAF_SPECS)),
        ("EVERY proven row carries non-null input+output edge type ids", len(typed) == len(rows)),
        ("manifest typed == proven_deterministic", manifest["typed"] == manifest["proven_deterministic"]),
        ("all 7 target GCP formats are covered", set(manifest["formats_covered"]) == target_formats),
        ("roundtrip-inverse pairs actually ran + PASSED a roundtrip proof", all(
            any(p["name"] == "roundtrip_test" and p["passed"] for p in proven_by_id[s["id"]]["proofs"])
            for s in roundtrip_specs)),
        ("domain stamped on every proven row", all(r["domain"] == DOMAIN for r in rows)),
        ("deterministic: re-running yields identical proven rows",
         [json.dumps(r, sort_keys=True) for r in build_proven_rows()] == [json.dumps(r, sort_keys=True) for r in rows]),
        # gated-effect law: EVERY gated row is candidate / serves_truth=false with a valid effect + proof_obligation
        (">=1 gated-effect candidate declared", len(gated) >= 1),
        ("EVERY gated-effect row is candidate + serves_truth=false",
         all(r["candidate"] is True and r["serves_truth"] is False for r in gated)),
        ("EVERY gated-effect row has a valid effect + non-empty proof_obligation",
         all(r["effect"] in valid_effects and isinstance(r["proof_obligation"], str) and r["proof_obligation"]
             for r in gated)),
        ("EVERY gated-effect row is TYPED (input+output edge type ids)",
         all(r["input_edge_type_id"] and r["output_edge_type_id"] for r in gated)),
        ("no gated-effect id leaked into the proven section", not (set(r["primitive_id"] for r in gated) & set(ids))),
        # the proof gate is real
        ("a deliberately-wrong leaf stays CANDIDATE (never promoted)",
         wrong["serves_truth"] is False and wrong["promoted"] is False),
        ("the wrong leaf is NOT persisted as proven", NEGATIVE_SPEC["id"] not in set(ids)),
        ("an un-runnable fixture fails the proof, does not promote",
         err["serves_truth"] is False and err["promoted"] is False),
        ("new mutators registered into the shared registry (add-only seam)",
         all(m in MUTATOR_REGISTRY for m in _NEW_MUTATORS)),
    ]
    failed = [n for n, ok in checks if not ok]
    if failed:
        print("FAIL - domain_cloud_gcp:\n  " + "\n  ".join(failed))
        return 1
    print(f"PASS - domain_cloud_gcp: {len(rows)} WORKABLE (proven + TYPED) deterministic SHAPE leaves for "
          f"'{DOMAIN}' (serves_truth=true, L7_executed_proof; typed=={len(rows)}) across {len(target_formats)} GCP "
          f"shape formats; {len(roundtrip_specs)} inverse pairs proven reversible via roundtrip; {len(gated)} GCP "
          "API / model capabilities declared as GATED-EFFECT candidates (serves_truth=false, effect + proof_obligation). "
          "A deliberately-wrong leaf and an un-runnable fixture correctly stay candidate. Synthetic shapes; no insurance.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    if args.write:
        manifest = write_shard()
        print(json.dumps(manifest, indent=2, sort_keys=True))
        return self_test()
    return self_test()


if __name__ == "__main__":
    raise SystemExit(main())
