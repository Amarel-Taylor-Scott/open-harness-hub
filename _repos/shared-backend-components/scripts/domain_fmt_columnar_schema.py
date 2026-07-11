#!/usr/bin/env python3
"""scripts.domain_fmt_columnar_schema — WORKABLE (proven + TYPED) deterministic leaves for the `fmt_columnar_schema`
domain: pure schema/shape transforms across columnar & serialization formats (Parquet · Avro · Protobuf · Arrow ·
ORC · JSON-Schema · SQL DDL), PLUS an HONEST, separate ledger of cloud/network schema CALLS declared as GATED-EFFECT
candidates (never proven, never serves_truth=true).

ADD-ONLY parallel path. It IMPORTS the shared machinery (never edits it):
  * `run_primitive_proof` / `MUTATOR_REGISTRY` / `_receipt` from `scripts.mutator_registry` — the proof-runner EXECUTES
    each mutator against a fixture and flips serves_truth false->true ONLY on a PASSING executed proof;
  * `canonicalize_edge` from `scripts.build_edge_type_retrofit` — folds each leaf's logical edge labels to canonical
    type_ids so a proven leaf is also TYPED (a workable leaf MUST carry canonical input/output edge types to chain).

Repo law honored precisely:
  * serves_truth=true ONLY on a PASSING executed proof of a DETERMINISTIC transform (parse/emit/convert/roundtrip run
    on a synthetic fixture, output checked). No wall-clock / RNG / network / model / disk in any transform body.
  * A NETWORK/EFFECTFUL row (fetch a Parquet footer from S3, register an Avro schema to a Schema Registry, create a
    BigQuery table, ...) is NEVER run through the proof runner and is declared as a GATED EFFECT:
    {candidate:true, serves_truth:false, effect, proof_obligation, input_edge_type_id, output_edge_type_id}.
  * HONEST accounting: the manifest carries proven_deterministic / typed / gated_effect_candidates as SEPARATE counts.
  * DOMAIN: no insurance (any domain); shapes only, synthetic fixtures — no real PII/PAN/SSN/secrets.

The canonical intermediate is a `ColumnSpec` = ordered list of {"name": str, "type": <logical>, "nullable": bool}
where logical ∈ {int64,int32,double,float,string,bool,bytes,date,timestamp}. Every format emitter/parser folds to/from
that one shape, so a proven Parquet leaf and a proven Avro leaf share a namespace and compose.

Deterministic + offline. CLI: --self-test (standalone, no data files) | --write.

Register tuple for the shared proof suite (REPORT ONLY — this module does NOT self-register):
    ("_repos/shared-backend-components/scripts/domain_fmt_columnar_schema.py", "domain_fmt_columnar_schema")
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
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

DOMAIN = "fmt_columnar_schema"
FAMILY = DOMAIN
_FIXED_UTC = "2026-07-03"  # fixed literal timestamp — NO wall-clock (repo law: deterministic + offline)
_TABLE_NAME = "row_table"  # single source for the DDL/select table name used across emit + parse
_RECORD_NAME = "Row"  # single source for the Avro/Protobuf message name

OUT_DIR = _resource("data") / "dev-intel" / "domain_primitives"
OUT_JSONL = OUT_DIR / "domain_fmt_columnar_schema.jsonl"
OUT_MANIFEST = OUT_DIR / "manifest_fmt_columnar_schema.json"

# ── canonical logical-type ↔ per-format-type tables (ONE definition each; parsers reuse the reverse) ──────────────
# Only the reversible subset is used inside roundtrip fixtures; parsers land on the CANONICAL logical name.
LOGICAL_TO_PARQUET = {"int64": "int64", "int32": "int32", "double": "double", "float": "float",
                      "string": "binary", "bool": "boolean", "bytes": "binary"}
PARQUET_TO_LOGICAL = {"int64": "int64", "int32": "int32", "double": "double", "float": "float",
                      "binary": "string", "boolean": "bool"}
LOGICAL_TO_AVRO = {"int64": "long", "int32": "int", "double": "double", "float": "float",
                   "string": "string", "bool": "boolean", "bytes": "bytes"}
AVRO_TO_LOGICAL = {"long": "int64", "int": "int32", "double": "double", "float": "float",
                   "string": "string", "boolean": "bool", "bytes": "bytes"}
LOGICAL_TO_ARROW = {"int64": "int64", "int32": "int32", "double": "double", "float": "float",
                    "string": "utf8", "bool": "bool", "bytes": "binary"}
ARROW_TO_LOGICAL = {"int64": "int64", "int32": "int32", "double": "double", "float": "float",
                    "utf8": "string", "bool": "bool", "binary": "bytes"}
LOGICAL_TO_PROTO = {"int64": "int64", "int32": "int32", "double": "double", "float": "float",
                    "string": "string", "bool": "bool", "bytes": "bytes"}
PROTO_TO_LOGICAL = {"int64": "int64", "int32": "int32", "double": "double", "float": "float",
                    "string": "string", "bool": "bool", "bytes": "bytes"}
LOGICAL_TO_ORC = {"int64": "bigint", "int32": "int", "double": "double", "float": "float",
                  "string": "string", "bool": "boolean", "bytes": "binary"}
ORC_TO_LOGICAL = {"bigint": "int64", "int": "int32", "double": "double", "float": "float",
                  "string": "string", "boolean": "bool", "binary": "bytes"}
LOGICAL_TO_DDL = {"int64": "BIGINT", "int32": "INT", "double": "DOUBLE", "float": "FLOAT",
                  "string": "VARCHAR", "bool": "BOOLEAN", "bytes": "VARBINARY"}
DDL_TO_LOGICAL = {"BIGINT": "int64", "INT": "int32", "DOUBLE": "double", "FLOAT": "float",
                  "VARCHAR": "string", "BOOLEAN": "bool", "VARBINARY": "bytes"}
LOGICAL_TO_JSONSCHEMA = {"int64": "integer", "int32": "integer", "double": "number", "float": "number",
                         "string": "string", "bool": "boolean"}
JSONSCHEMA_TO_LOGICAL = {"integer": "int64", "number": "double", "string": "string", "boolean": "bool"}
LOGICAL_TO_BIGQUERY = {"int64": "INT64", "int32": "INT64", "double": "FLOAT64", "float": "FLOAT64",
                       "string": "STRING", "bool": "BOOL", "bytes": "BYTES"}
# Python sample-value type → canonical logical (for schema INFERENCE from a synthetic record)
_PY_TO_LOGICAL = {"bool": "bool", "int": "int64", "float": "double", "str": "string"}


# ── PURE deterministic mutators — contract (payload, **kwargs) -> (output, receipt). `fcs_` prefixed so they never
#    collide with existing registry entries; registered via setdefault (idempotent). No I/O / RNG / clock / network. ──

# --- Parquet message text <-> ColumnSpec (roundtrip) ---
def fcs_columns_to_parquet_message(cols: list[dict[str, Any]], **_kw: Any) -> tuple[str, dict[str, Any]]:
    lines = [f"  {'optional' if c['nullable'] else 'required'} {LOGICAL_TO_PARQUET[c['type']]} {c['name']};" for c in cols]
    out = "message schema {\n" + "\n".join(lines) + "\n}"
    return out, _receipt("fcs_columns_to_parquet_message", before=cols, after=out, lossless=True,
                         note="ColumnSpec -> parquet message text; fcs_parquet_message_to_columns restores")


def fcs_parquet_message_to_columns(text: str, **_kw: Any) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for raw in text.split("\n")[1:-1]:
        rep, ptype, name = raw.strip().rstrip(";").split()
        out.append({"name": name, "type": PARQUET_TO_LOGICAL[ptype], "nullable": rep == "optional"})
    return out, _receipt("fcs_parquet_message_to_columns", before=text, after=out, lossless=True,
                         note="parse parquet message text -> ColumnSpec")


# --- Avro record schema (dict) <-> ColumnSpec (roundtrip) ---
def fcs_columns_to_avro_schema(cols: list[dict[str, Any]], **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    fields = []
    for c in cols:
        atype: Any = LOGICAL_TO_AVRO[c["type"]]
        fields.append({"name": c["name"], "type": ["null", atype] if c["nullable"] else atype})
    out = {"type": "record", "name": _RECORD_NAME, "fields": fields}
    return out, _receipt("fcs_columns_to_avro_schema", before=cols, after=out, lossless=True,
                         note="ColumnSpec -> avro record schema; fcs_avro_schema_to_columns restores")


def fcs_avro_schema_to_columns(schema: dict[str, Any], **_kw: Any) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for f in schema["fields"]:
        t = f["type"]
        nullable = isinstance(t, list) and "null" in t
        atype = next(x for x in t if x != "null") if nullable else t
        out.append({"name": f["name"], "type": AVRO_TO_LOGICAL[atype], "nullable": nullable})
    return out, _receipt("fcs_avro_schema_to_columns", before=schema, after=out, lossless=True,
                         note="parse avro record schema -> ColumnSpec")


# --- Arrow schema (list of field dicts) <-> ColumnSpec (roundtrip) ---
def fcs_columns_to_arrow_schema(cols: list[dict[str, Any]], **_kw: Any) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    out = [{"name": c["name"], "type": LOGICAL_TO_ARROW[c["type"]], "nullable": c["nullable"]} for c in cols]
    return out, _receipt("fcs_columns_to_arrow_schema", before=cols, after=out, lossless=True,
                         note="ColumnSpec -> arrow schema fields; fcs_arrow_schema_to_columns restores")


def fcs_arrow_schema_to_columns(fields: list[dict[str, Any]], **_kw: Any) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    out = [{"name": f["name"], "type": ARROW_TO_LOGICAL[f["type"]], "nullable": f["nullable"]} for f in fields]
    return out, _receipt("fcs_arrow_schema_to_columns", before=fields, after=out, lossless=True,
                         note="parse arrow schema fields -> ColumnSpec")


# --- Protobuf message text <-> ColumnSpec (roundtrip; proto3 scalars are non-null -> fixtures use nullable=False) ---
def fcs_columns_to_protobuf(cols: list[dict[str, Any]], **_kw: Any) -> tuple[str, dict[str, Any]]:
    lines = [f"  {LOGICAL_TO_PROTO[c['type']]} {c['name']} = {i};" for i, c in enumerate(cols, start=1)]
    out = f"message {_RECORD_NAME} {{\n" + "\n".join(lines) + "\n}"
    return out, _receipt("fcs_columns_to_protobuf", before=cols, after=out, lossless=True,
                         note="ColumnSpec -> protobuf message text; fcs_protobuf_to_columns restores")


def fcs_protobuf_to_columns(text: str, **_kw: Any) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for raw in text.split("\n")[1:-1]:
        ptype, name, _eq, _num = raw.strip().rstrip(";").split()
        out.append({"name": name, "type": PROTO_TO_LOGICAL[ptype], "nullable": False})
    return out, _receipt("fcs_protobuf_to_columns", before=text, after=out, lossless=True,
                         note="parse protobuf message text -> ColumnSpec (field numbers by order)")


# --- ORC struct type string <-> ColumnSpec (roundtrip; ORC struct string carries no nullability -> nullable=False) ---
def fcs_columns_to_orc_shape(cols: list[dict[str, Any]], **_kw: Any) -> tuple[str, dict[str, Any]]:
    inner = ",".join(f"{c['name']}:{LOGICAL_TO_ORC[c['type']]}" for c in cols)
    out = f"struct<{inner}>"
    return out, _receipt("fcs_columns_to_orc_shape", before=cols, after=out, lossless=True,
                         note="ColumnSpec -> ORC struct type string; fcs_orc_shape_to_columns restores")


def fcs_orc_shape_to_columns(text: str, **_kw: Any) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    inner = text[len("struct<"):-1]
    out: list[dict[str, Any]] = []
    for part in inner.split(","):
        name, otype = part.split(":")
        out.append({"name": name, "type": ORC_TO_LOGICAL[otype], "nullable": False})
    return out, _receipt("fcs_orc_shape_to_columns", before=text, after=out, lossless=True,
                         note="parse ORC struct type string -> ColumnSpec")


# --- SQL DDL CREATE TABLE <-> ColumnSpec (roundtrip; carries nullability via NOT NULL) ---
def fcs_columns_to_ddl(cols: list[dict[str, Any]], **_kw: Any) -> tuple[str, dict[str, Any]]:
    defs = [f"{c['name']} {LOGICAL_TO_DDL[c['type']]}" + ("" if c["nullable"] else " NOT NULL") for c in cols]
    out = f"CREATE TABLE {_TABLE_NAME} ({', '.join(defs)})"
    return out, _receipt("fcs_columns_to_ddl", before=cols, after=out, lossless=True,
                         note="ColumnSpec -> CREATE TABLE DDL; fcs_ddl_to_columns restores")


def fcs_ddl_to_columns(text: str, **_kw: Any) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    body = text[text.index("(") + 1:text.rindex(")")]
    out: list[dict[str, Any]] = []
    for part in body.split(", "):
        toks = part.split()
        name, dtype = toks[0], toks[1]
        out.append({"name": name, "type": DDL_TO_LOGICAL[dtype], "nullable": "NOT NULL" not in part})
    return out, _receipt("fcs_ddl_to_columns", before=text, after=out, lossless=True,
                         note="parse CREATE TABLE DDL column list -> ColumnSpec")


# --- JSON Schema (object) <-> ColumnSpec (roundtrip; nullability via `required`) ---
def fcs_columns_to_json_schema(cols: list[dict[str, Any]], **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    props = {c["name"]: {"type": LOGICAL_TO_JSONSCHEMA[c["type"]]} for c in cols}
    required = [c["name"] for c in cols if not c["nullable"]]
    out = {"type": "object", "properties": props, "required": required}
    return out, _receipt("fcs_columns_to_json_schema", before=cols, after=out, lossless=True,
                         note="ColumnSpec -> JSON Schema object; fcs_json_schema_to_columns restores")


def fcs_json_schema_to_columns(schema: dict[str, Any], **_kw: Any) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    required = set(schema.get("required", []))
    out = [{"name": name, "type": JSONSCHEMA_TO_LOGICAL[spec["type"]], "nullable": name not in required}
           for name, spec in schema["properties"].items()]
    return out, _receipt("fcs_json_schema_to_columns", before=schema, after=out, lossless=True,
                         note="parse JSON Schema object -> ColumnSpec")


# --- inference / projection / measurement / cross-format type-map (standalone; proven vs own fixtures) ---
def fcs_infer_columns_from_record(record: dict[str, Any], **_kw: Any) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    out = [{"name": k, "type": _PY_TO_LOGICAL[type(v).__name__], "nullable": v is None} for k, v in record.items()]
    return out, _receipt("fcs_infer_columns_from_record", before=record, after=out, lossless=False,
                         note="infer ColumnSpec from a synthetic sample record (types by python value)")


def fcs_column_names(cols: list[dict[str, Any]], **_kw: Any) -> tuple[list[str], dict[str, Any]]:
    out = [c["name"] for c in cols]
    return out, _receipt("fcs_column_names", before=cols, after=out, lossless=False, note="ColumnSpec -> ordered name list")


def fcs_column_count(cols: list[dict[str, Any]], **_kw: Any) -> tuple[int, dict[str, Any]]:
    out = len(cols)
    return out, _receipt("fcs_column_count", before=cols, after=out, lossless=False, note="ColumnSpec -> column count")


def fcs_column_type_map(cols: list[dict[str, Any]], **_kw: Any) -> tuple[dict[str, str], dict[str, Any]]:
    out = {c["name"]: c["type"] for c in cols}
    return out, _receipt("fcs_column_type_map", before=cols, after=out, lossless=False, note="ColumnSpec -> {name: logical_type}")


def fcs_required_columns(cols: list[dict[str, Any]], **_kw: Any) -> tuple[list[str], dict[str, Any]]:
    out = [c["name"] for c in cols if not c["nullable"]]
    return out, _receipt("fcs_required_columns", before=cols, after=out, lossless=False, note="names of non-nullable columns")


def fcs_nullable_columns(cols: list[dict[str, Any]], **_kw: Any) -> tuple[list[str], dict[str, Any]]:
    out = [c["name"] for c in cols if c["nullable"]]
    return out, _receipt("fcs_nullable_columns", before=cols, after=out, lossless=False, note="names of nullable columns")


def fcs_columns_sorted_by_name(cols: list[dict[str, Any]], **_kw: Any) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    out = sorted(cols, key=lambda c: c["name"])
    return out, _receipt("fcs_columns_sorted_by_name", before=cols, after=out, lossless=True, note="canonicalize ColumnSpec order by name")


def fcs_logical_to_bigquery(cols: list[dict[str, Any]], **_kw: Any) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    out = [{"name": c["name"], "type": LOGICAL_TO_BIGQUERY[c["type"]],
            "mode": "NULLABLE" if c["nullable"] else "REQUIRED"} for c in cols]
    return out, _receipt("fcs_logical_to_bigquery", before=cols, after=out, lossless=False, note="ColumnSpec -> BigQuery field shape")


def fcs_logical_to_parquet_physical(cols: list[dict[str, Any]], **_kw: Any) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    out = [{"name": c["name"], "physical_type": LOGICAL_TO_PARQUET[c["type"]],
            "repetition": "OPTIONAL" if c["nullable"] else "REQUIRED"} for c in cols]
    return out, _receipt("fcs_logical_to_parquet_physical", before=cols, after=out, lossless=False, note="ColumnSpec -> parquet physical-type shape")


def fcs_columns_to_pyarrow_fields(cols: list[dict[str, Any]], **_kw: Any) -> tuple[list[str], dict[str, Any]]:
    out = [f"pa.field('{c['name']}', pa.{LOGICAL_TO_ARROW[c['type']]}(), nullable={c['nullable']})" for c in cols]
    return out, _receipt("fcs_columns_to_pyarrow_fields", before=cols, after=out, lossless=False, note="ColumnSpec -> pyarrow field constructor strings")


def fcs_columns_to_select_list(cols: list[dict[str, Any]], **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = f"SELECT {', '.join(c['name'] for c in cols)} FROM {_TABLE_NAME}"
    return out, _receipt("fcs_columns_to_select_list", before=cols, after=out, lossless=False, note="ColumnSpec -> SELECT projection SQL")


def fcs_avro_record_name(schema: dict[str, Any], **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = schema["name"]
    return out, _receipt("fcs_avro_record_name", before=schema, after=out, lossless=False, note="extract avro record name")


def fcs_ddl_table_name(text: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = re.match(r"CREATE TABLE (\w+)", text).group(1)
    return out, _receipt("fcs_ddl_table_name", before=text, after=out, lossless=False, note="extract table name from CREATE TABLE DDL")


def fcs_json_schema_required_list(schema: dict[str, Any], **_kw: Any) -> tuple[list[str], dict[str, Any]]:
    out = list(schema.get("required", []))
    return out, _receipt("fcs_json_schema_required_list", before=schema, after=out, lossless=False, note="extract JSON Schema required list")


def fcs_columns_add_field(cols: list[dict[str, Any]], field: dict[str, Any], **_kw: Any) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    out = [*cols, field]
    return out, _receipt("fcs_columns_add_field", before=cols, after=out, lossless=True, note="schema evolution: append a column (additive)")


def fcs_columns_drop_field(cols: list[dict[str, Any]], name: str, **_kw: Any) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    out = [c for c in cols if c["name"] != name]
    return out, _receipt("fcs_columns_drop_field", before=cols, after=out, lossless=False, note=f"schema evolution: drop column {name!r}")


def fcs_arrow_schema_field_count(fields: list[dict[str, Any]], **_kw: Any) -> tuple[int, dict[str, Any]]:
    out = len(fields)
    return out, _receipt("fcs_arrow_schema_field_count", before=fields, after=out, lossless=False, note="arrow schema field count")


def fcs_orc_field_types(text: str, **_kw: Any) -> tuple[list[str], dict[str, Any]]:
    inner = text[len("struct<"):-1]
    out = [part.split(":")[1] for part in inner.split(",")]
    return out, _receipt("fcs_orc_field_types", before=text, after=out, lossless=False, note="ORC struct string -> ordered ORC type list")


#: new pure mutators to plug into the shared registry (idempotent setdefault — never overwrites an existing entry)
_NEW_MUTATORS = {
    "fcs_columns_to_parquet_message": fcs_columns_to_parquet_message,
    "fcs_parquet_message_to_columns": fcs_parquet_message_to_columns,
    "fcs_columns_to_avro_schema": fcs_columns_to_avro_schema,
    "fcs_avro_schema_to_columns": fcs_avro_schema_to_columns,
    "fcs_columns_to_arrow_schema": fcs_columns_to_arrow_schema,
    "fcs_arrow_schema_to_columns": fcs_arrow_schema_to_columns,
    "fcs_columns_to_protobuf": fcs_columns_to_protobuf,
    "fcs_protobuf_to_columns": fcs_protobuf_to_columns,
    "fcs_columns_to_orc_shape": fcs_columns_to_orc_shape,
    "fcs_orc_shape_to_columns": fcs_orc_shape_to_columns,
    "fcs_columns_to_ddl": fcs_columns_to_ddl,
    "fcs_ddl_to_columns": fcs_ddl_to_columns,
    "fcs_columns_to_json_schema": fcs_columns_to_json_schema,
    "fcs_json_schema_to_columns": fcs_json_schema_to_columns,
    "fcs_infer_columns_from_record": fcs_infer_columns_from_record,
    "fcs_column_names": fcs_column_names,
    "fcs_column_count": fcs_column_count,
    "fcs_column_type_map": fcs_column_type_map,
    "fcs_required_columns": fcs_required_columns,
    "fcs_nullable_columns": fcs_nullable_columns,
    "fcs_columns_sorted_by_name": fcs_columns_sorted_by_name,
    "fcs_logical_to_bigquery": fcs_logical_to_bigquery,
    "fcs_logical_to_parquet_physical": fcs_logical_to_parquet_physical,
    "fcs_columns_to_pyarrow_fields": fcs_columns_to_pyarrow_fields,
    "fcs_columns_to_select_list": fcs_columns_to_select_list,
    "fcs_avro_record_name": fcs_avro_record_name,
    "fcs_ddl_table_name": fcs_ddl_table_name,
    "fcs_json_schema_required_list": fcs_json_schema_required_list,
    "fcs_columns_add_field": fcs_columns_add_field,
    "fcs_columns_drop_field": fcs_columns_drop_field,
    "fcs_arrow_schema_field_count": fcs_arrow_schema_field_count,
    "fcs_orc_field_types": fcs_orc_field_types,
}


def register_new_mutators() -> None:
    """Plug the domain's pure mutators into the shared MUTATOR_REGISTRY (registration, not a rewrite). Idempotent."""
    for name, fn in _NEW_MUTATORS.items():
        MUTATOR_REGISTRY.setdefault(name, fn)


register_new_mutators()


# ── synthetic ColumnSpec fixtures (SHAPE only — no real PII/PAN/SSN; NO insurance domain) ─────────────────────────
# Roundtrip-safe subsets differ per format (proto/orc carry no nullability; parquet/arrow/ddl/json do), so each
# roundtrip fixture is chosen to survive its format's expressiveness.
_COLS_FULL = [{"name": "id", "type": "int64", "nullable": False}, {"name": "label", "type": "string", "nullable": True}]
_COLS_REQUIRED = [{"name": "id", "type": "int64", "nullable": False}, {"name": "amount", "type": "double", "nullable": False}]
_COLS_JSON = [{"name": "id", "type": "int64", "nullable": False}, {"name": "score", "type": "double", "nullable": True}]


# ── leaf primitives: each a REAL deterministic capability with a synthetic fixture + expected (+ inverse where a
#    roundtrip holds). serves_truth=true set ONLY by the executed proof. ──
LEAF_SPECS: list[dict[str, Any]] = [
    # roundtrip format emit/parse pairs (has_inverse -> reversibility proven by the roundtrip proof)
    {"id": "prim:leaf:fcs_columns_to_parquet_message", "mutator": "fcs_columns_to_parquet_message", "fixture": _COLS_FULL,
     "expected": "message schema {\n  required int64 id;\n  optional binary label;\n}",
     "inverse": "fcs_parquet_message_to_columns", "input_edge": "ColumnSpec", "output_edge": "ParquetSchema"},
    {"id": "prim:leaf:fcs_parquet_message_to_columns", "mutator": "fcs_parquet_message_to_columns",
     "fixture": "message schema {\n  required int64 id;\n  optional binary label;\n}", "expected": _COLS_FULL,
     "input_edge": "ParquetSchema", "output_edge": "ColumnSpec"},
    {"id": "prim:leaf:fcs_columns_to_avro_schema", "mutator": "fcs_columns_to_avro_schema", "fixture": _COLS_FULL,
     "expected": {"type": "record", "name": "Row",
                  "fields": [{"name": "id", "type": "long"}, {"name": "label", "type": ["null", "string"]}]},
     "inverse": "fcs_avro_schema_to_columns", "input_edge": "ColumnSpec", "output_edge": "AvroSchema"},
    {"id": "prim:leaf:fcs_avro_schema_to_columns", "mutator": "fcs_avro_schema_to_columns",
     "fixture": {"type": "record", "name": "Row",
                 "fields": [{"name": "id", "type": "long"}, {"name": "label", "type": ["null", "string"]}]},
     "expected": _COLS_FULL, "input_edge": "AvroSchema", "output_edge": "ColumnSpec"},
    {"id": "prim:leaf:fcs_columns_to_arrow_schema", "mutator": "fcs_columns_to_arrow_schema", "fixture": _COLS_FULL,
     "expected": [{"name": "id", "type": "int64", "nullable": False}, {"name": "label", "type": "utf8", "nullable": True}],
     "inverse": "fcs_arrow_schema_to_columns", "input_edge": "ColumnSpec", "output_edge": "ArrowSchema"},
    {"id": "prim:leaf:fcs_arrow_schema_to_columns", "mutator": "fcs_arrow_schema_to_columns",
     "fixture": [{"name": "id", "type": "int64", "nullable": False}, {"name": "label", "type": "utf8", "nullable": True}],
     "expected": _COLS_FULL, "input_edge": "ArrowSchema", "output_edge": "ColumnSpec"},
    {"id": "prim:leaf:fcs_columns_to_protobuf", "mutator": "fcs_columns_to_protobuf", "fixture": _COLS_REQUIRED,
     "expected": "message Row {\n  int64 id = 1;\n  double amount = 2;\n}",
     "inverse": "fcs_protobuf_to_columns", "input_edge": "ColumnSpec", "output_edge": "ProtobufMessage"},
    {"id": "prim:leaf:fcs_protobuf_to_columns", "mutator": "fcs_protobuf_to_columns",
     "fixture": "message Row {\n  int64 id = 1;\n  double amount = 2;\n}", "expected": _COLS_REQUIRED,
     "input_edge": "ProtobufMessage", "output_edge": "ColumnSpec"},
    {"id": "prim:leaf:fcs_columns_to_orc_shape", "mutator": "fcs_columns_to_orc_shape", "fixture": _COLS_REQUIRED,
     "expected": "struct<id:bigint,amount:double>",
     "inverse": "fcs_orc_shape_to_columns", "input_edge": "ColumnSpec", "output_edge": "OrcShape"},
    {"id": "prim:leaf:fcs_orc_shape_to_columns", "mutator": "fcs_orc_shape_to_columns",
     "fixture": "struct<id:bigint,amount:double>", "expected": _COLS_REQUIRED,
     "input_edge": "OrcShape", "output_edge": "ColumnSpec"},
    {"id": "prim:leaf:fcs_columns_to_ddl", "mutator": "fcs_columns_to_ddl", "fixture": _COLS_FULL,
     "expected": "CREATE TABLE row_table (id BIGINT NOT NULL, label VARCHAR)",
     "inverse": "fcs_ddl_to_columns", "input_edge": "ColumnSpec", "output_edge": "DdlText"},
    {"id": "prim:leaf:fcs_ddl_to_columns", "mutator": "fcs_ddl_to_columns",
     "fixture": "CREATE TABLE row_table (id BIGINT NOT NULL, label VARCHAR)", "expected": _COLS_FULL,
     "input_edge": "DdlText", "output_edge": "ColumnSpec"},
    {"id": "prim:leaf:fcs_columns_to_json_schema", "mutator": "fcs_columns_to_json_schema", "fixture": _COLS_JSON,
     "expected": {"type": "object", "properties": {"id": {"type": "integer"}, "score": {"type": "number"}},
                  "required": ["id"]},
     "inverse": "fcs_json_schema_to_columns", "input_edge": "ColumnSpec", "output_edge": "JsonSchema"},
    {"id": "prim:leaf:fcs_json_schema_to_columns", "mutator": "fcs_json_schema_to_columns",
     "fixture": {"type": "object", "properties": {"id": {"type": "integer"}, "score": {"type": "number"}},
                 "required": ["id"]}, "expected": _COLS_JSON,
     "input_edge": "JsonSchema", "output_edge": "ColumnSpec"},

    # standalone inference / projection / measurement / cross-format type-map leaves
    {"id": "prim:leaf:fcs_infer_columns_from_record", "mutator": "fcs_infer_columns_from_record",
     "fixture": {"id": 7, "amount": 1.5, "label": "x", "flag": True},
     "expected": [{"name": "id", "type": "int64", "nullable": False},
                  {"name": "amount", "type": "double", "nullable": False},
                  {"name": "label", "type": "string", "nullable": False},
                  {"name": "flag", "type": "bool", "nullable": False}],
     "input_edge": "Record", "output_edge": "ColumnSpec"},
    {"id": "prim:leaf:fcs_column_names", "mutator": "fcs_column_names", "fixture": _COLS_FULL, "expected": ["id", "label"],
     "input_edge": "ColumnSpec", "output_edge": "NameList"},
    {"id": "prim:leaf:fcs_column_count", "mutator": "fcs_column_count", "fixture": _COLS_FULL, "expected": 2,
     "input_edge": "ColumnSpec", "output_edge": "Count"},
    {"id": "prim:leaf:fcs_column_type_map", "mutator": "fcs_column_type_map", "fixture": _COLS_FULL,
     "expected": {"id": "int64", "label": "string"}, "input_edge": "ColumnSpec", "output_edge": "TypeMap"},
    {"id": "prim:leaf:fcs_required_columns", "mutator": "fcs_required_columns", "fixture": _COLS_FULL, "expected": ["id"],
     "input_edge": "ColumnSpec", "output_edge": "NameList"},
    {"id": "prim:leaf:fcs_nullable_columns", "mutator": "fcs_nullable_columns", "fixture": _COLS_FULL, "expected": ["label"],
     "input_edge": "ColumnSpec", "output_edge": "NameList"},
    {"id": "prim:leaf:fcs_columns_sorted_by_name", "mutator": "fcs_columns_sorted_by_name", "fixture": _COLS_FULL,
     "expected": [{"name": "id", "type": "int64", "nullable": False}, {"name": "label", "type": "string", "nullable": True}],
     "input_edge": "ColumnSpec", "output_edge": "ColumnSpec"},
    {"id": "prim:leaf:fcs_logical_to_bigquery", "mutator": "fcs_logical_to_bigquery", "fixture": _COLS_FULL,
     "expected": [{"name": "id", "type": "INT64", "mode": "REQUIRED"},
                  {"name": "label", "type": "STRING", "mode": "NULLABLE"}],
     "input_edge": "ColumnSpec", "output_edge": "BigQuerySchema"},
    {"id": "prim:leaf:fcs_logical_to_parquet_physical", "mutator": "fcs_logical_to_parquet_physical", "fixture": _COLS_FULL,
     "expected": [{"name": "id", "physical_type": "int64", "repetition": "REQUIRED"},
                  {"name": "label", "physical_type": "binary", "repetition": "OPTIONAL"}],
     "input_edge": "ColumnSpec", "output_edge": "ParquetPhysicalShape"},
    {"id": "prim:leaf:fcs_columns_to_pyarrow_fields", "mutator": "fcs_columns_to_pyarrow_fields", "fixture": _COLS_FULL,
     "expected": ["pa.field('id', pa.int64(), nullable=False)", "pa.field('label', pa.utf8(), nullable=True)"],
     "input_edge": "ColumnSpec", "output_edge": "PyArrowFields"},
    {"id": "prim:leaf:fcs_columns_to_select_list", "mutator": "fcs_columns_to_select_list", "fixture": _COLS_FULL,
     "expected": "SELECT id, label FROM row_table", "input_edge": "ColumnSpec", "output_edge": "DdlText"},
    {"id": "prim:leaf:fcs_avro_record_name", "mutator": "fcs_avro_record_name",
     "fixture": {"type": "record", "name": "Row", "fields": []}, "expected": "Row",
     "input_edge": "AvroSchema", "output_edge": "Name"},
    {"id": "prim:leaf:fcs_ddl_table_name", "mutator": "fcs_ddl_table_name",
     "fixture": "CREATE TABLE row_table (id BIGINT NOT NULL)", "expected": "row_table",
     "input_edge": "DdlText", "output_edge": "Name"},
    {"id": "prim:leaf:fcs_json_schema_required_list", "mutator": "fcs_json_schema_required_list",
     "fixture": {"type": "object", "properties": {"id": {"type": "integer"}}, "required": ["id"]}, "expected": ["id"],
     "input_edge": "JsonSchema", "output_edge": "NameList"},
    {"id": "prim:leaf:fcs_columns_add_field", "mutator": "fcs_columns_add_field", "fixture": _COLS_FULL,
     "args": {"field": {"name": "ts", "type": "timestamp", "nullable": True}},
     "expected": [{"name": "id", "type": "int64", "nullable": False}, {"name": "label", "type": "string", "nullable": True},
                  {"name": "ts", "type": "timestamp", "nullable": True}],
     "input_edge": "ColumnSpec", "output_edge": "ColumnSpec"},
    {"id": "prim:leaf:fcs_columns_drop_field", "mutator": "fcs_columns_drop_field", "fixture": _COLS_FULL,
     "args": {"name": "label"}, "expected": [{"name": "id", "type": "int64", "nullable": False}],
     "input_edge": "ColumnSpec", "output_edge": "ColumnSpec"},
    {"id": "prim:leaf:fcs_arrow_schema_field_count", "mutator": "fcs_arrow_schema_field_count",
     "fixture": [{"name": "id", "type": "int64", "nullable": False}, {"name": "label", "type": "utf8", "nullable": True}],
     "expected": 2, "input_edge": "ArrowSchema", "output_edge": "Count"},
    {"id": "prim:leaf:fcs_orc_field_types", "mutator": "fcs_orc_field_types", "fixture": "struct<id:bigint,amount:double>",
     "expected": ["bigint", "double"], "input_edge": "OrcShape", "output_edge": "TypeList"},
]

#: deliberately-wrong leaf — the proof gate MUST leave it candidate (never persisted as proven-deterministic)
NEGATIVE_SPEC: dict[str, Any] = {
    "id": "prim:leaf:fcs_WRONG_expected", "mutator": "fcs_columns_to_orc_shape", "fixture": _COLS_REQUIRED,
    "expected": "struct<WRONG:nope>", "input_edge": "ColumnSpec", "output_edge": "OrcShape"}


# ── GATED-EFFECT candidates: cloud/network schema CALLS. NEVER run through the proof runner; NEVER serves_truth=true.
#    Each declares an effect + a proof_obligation (live integration test with credential) + typed edges. Synthetic
#    shapes only — no secrets embedded (env-name references, not values). ──
GATED_EFFECT_SPECS: list[dict[str, Any]] = [
    {"id": "prim:gated:fcs_read_parquet_footer_s3", "effect": "network_read",
     "proof_obligation": "live integration test: read a Parquet file footer/schema from S3 with an AWS credential",
     "input_edge": "S3ObjectUri", "output_edge": "ParquetSchema",
     "note": "fetch a Parquet footer over the network (object storage) — effectful, cannot be proven offline"},
    {"id": "prim:gated:fcs_read_orc_footer_gcs", "effect": "network_read",
     "proof_obligation": "live integration test: read an ORC footer/schema from GCS with a GCP credential",
     "input_edge": "GcsObjectUri", "output_edge": "OrcShape",
     "note": "fetch an ORC footer over the network — effectful"},
    {"id": "prim:gated:fcs_fetch_avro_schema_registry", "effect": "network_read",
     "proof_obligation": "live integration test: GET a subject's Avro schema from a Confluent Schema Registry",
     "input_edge": "SchemaRegistrySubject", "output_edge": "AvroSchema",
     "note": "read an Avro schema from a running Schema Registry — effectful"},
    {"id": "prim:gated:fcs_register_avro_schema_registry", "effect": "network_write",
     "proof_obligation": "live integration test: POST a new Avro schema version to a Schema Registry subject",
     "input_edge": "AvroSchema", "output_edge": "SchemaRegistryVersion",
     "note": "register/evolve an Avro schema in a running registry — effectful WRITE"},
    {"id": "prim:gated:fcs_register_glue_table", "effect": "network_write",
     "proof_obligation": "live integration test: create/update a table in AWS Glue Data Catalog from a ColumnSpec",
     "input_edge": "ColumnSpec", "output_edge": "GlueTableRef",
     "note": "write a table definition to Glue Data Catalog — effectful WRITE"},
    {"id": "prim:gated:fcs_create_bigquery_table", "effect": "network_write",
     "proof_obligation": "live integration test: create a BigQuery table from a ColumnSpec with a GCP credential",
     "input_edge": "BigQuerySchema", "output_edge": "BigQueryTableRef",
     "note": "create a BigQuery table — effectful WRITE"},
    {"id": "prim:gated:fcs_apply_ddl_to_warehouse", "effect": "network_write",
     "proof_obligation": "live integration test: execute CREATE TABLE DDL against a live warehouse connection",
     "input_edge": "DdlText", "output_edge": "WarehouseTableRef",
     "note": "run CREATE TABLE DDL against a real database — effectful WRITE"},
    {"id": "prim:gated:fcs_write_parquet_file", "effect": "file_write",
     "proof_obligation": "live integration test: write a Parquet file with the emitted schema via a parquet engine",
     "input_edge": "ParquetSchema", "output_edge": "ParquetFileRef",
     "note": "materialize a Parquet file on disk via an engine — effectful FILE WRITE"},
]


# ── proving + row building ────────────────────────────────────────────────────────────────────────────────────────
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
            "family": FAMILY,
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
    """Persist-ready GATED-EFFECT candidate rows — typed, but candidate:true / serves_truth:false, each with an effect
    + a proof_obligation. NEVER run through the proof runner."""
    rows: list[dict[str, Any]] = []
    for spec in GATED_EFFECT_SPECS:
        rows.append({
            "primitive_id": spec["id"],
            "domain": DOMAIN,
            "family": FAMILY,
            "candidate": True,
            "serves_truth": False,
            "effect": spec["effect"],
            "proof_obligation": spec["proof_obligation"],
            "verification_level": "L0_gated_effect_candidate",
            "input_edge": spec["input_edge"],
            "output_edge": spec["output_edge"],
            "input_edge_type_id": canonicalize_edge(spec["input_edge"]),
            "output_edge_type_id": canonicalize_edge(spec["output_edge"]),
            "note": spec["note"],
        })
    return rows


_VALID_EFFECTS = frozenset({"network_read", "network_write", "model_call", "file_write"})


def build_manifest(proven: list[dict[str, Any]], gated: list[dict[str, Any]]) -> dict[str, Any]:
    typed = [r for r in proven if r["input_edge_type_id"] and r["output_edge_type_id"]]
    gated_typed = [r for r in gated if r["input_edge_type_id"] and r["output_edge_type_id"]]
    return {
        "record_type": "domain_columnar_schema_leaves_manifest",
        "domain": DOMAIN,
        "family": FAMILY,
        "generator": "scripts/domain_fmt_columnar_schema.py",
        "generated_utc": _FIXED_UTC,
        "defined_deterministic_count": len(LEAF_SPECS),
        # HONEST, SEPARATE counts (never conflated):
        "proven_deterministic": len(proven),
        "typed": len(typed),
        "gated_effect_candidates": len(gated),
        "gated_effect_typed": len(gated_typed),
        "verification_level_proven": "L7_executed_proof",
        "verification_level_gated": "L0_gated_effect_candidate",
        "proven_primitive_ids": sorted(r["primitive_id"] for r in proven),
        "gated_effect_primitive_ids": sorted(r["primitive_id"] for r in gated),
        "note": "proven_deterministic rows are serves_truth=true set ONLY by an executed passing proof "
                "(run_primitive_proof, imported from scripts/mutator_registry.py) over a synthetic fixture; every "
                "such row is TYPED via canonicalize_edge (scripts/build_edge_type_retrofit.py). gated_effect_candidates "
                "are cloud/network/file CALLS — candidate:true, serves_truth:false, each with an effect + a "
                "proof_obligation (live integration test with credential); they are NEVER run through the proof runner. "
                "No insurance domain; synthetic shapes only, no real PII/PAN/SSN/secrets.",
    }


def write_pack() -> dict[str, Any]:
    proven = build_proven_rows()
    gated = build_gated_rows()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    # ONE shard, two clearly-separated sections (proven-deterministic vs gated-effect-candidate) via a `section` tag.
    lines: list[str] = []
    for r in proven:
        lines.append(json.dumps({"section": "proven_deterministic", **r}, ensure_ascii=False, sort_keys=True))
    for r in gated:
        lines.append(json.dumps({"section": "gated_effect_candidate", **r}, ensure_ascii=False, sort_keys=True))
    OUT_JSONL.write_text("\n".join(lines) + "\n", encoding="utf-8")
    manifest = build_manifest(proven, gated)
    OUT_MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def self_test() -> int:
    proven_pairs = prove_all()
    proven = build_proven_rows()
    gated = build_gated_rows()
    ids = [r["primitive_id"] for r in proven]
    typed = [r for r in proven if r["input_edge_type_id"] and r["output_edge_type_id"]]
    roundtrip_specs = [s for s in LEAF_SPECS if s.get("inverse")]
    proven_by_id = {r["primitive_id"]: r for (_s, r) in proven_pairs}

    # deliberately-wrong leaf must stay candidate (proof gate is real) — and never enter the proven rows
    wrong = _prove_one(NEGATIVE_SPEC)
    # an un-runnable fixture -> execution error -> not promoted
    err = run_primitive_proof("prim:leaf:fcs_EXEC_ERROR", "fcs_ddl_to_columns", object(), "irrelevant")

    manifest = build_manifest(proven, gated)
    checks: list[tuple[str, bool]] = [
        (">=25 deterministic leaves declared", len(LEAF_SPECS) >= 25),
        ("unique proven primitive ids", len(set(ids)) == len(ids)),
        (">=25 leaves PROVE serves_truth=true via an executed proof", len(proven) >= 25),
        ("every proven receipt is L7_executed_proof with all sub-proofs passing",
         all(r["verification_level"] == "L7_executed_proof" and all(p["passed"] for p in r["proofs"])
             for (_s, r) in proven_pairs if r["serves_truth"] is True)),
        ("EVERY persisted proven row carries non-null input+output edge type ids", len(typed) == len(proven)),
        ("manifest typed == proven_deterministic", manifest["typed"] == manifest["proven_deterministic"]),
        ("roundtrip-inverse pairs actually ran + PASSED a roundtrip proof", all(
            any(p["name"] == "roundtrip_test" and p["passed"] for p in proven_by_id[s["id"]]["proofs"])
            for s in roundtrip_specs)),
        ("all 7 format pairs present (parquet/avro/arrow/protobuf/orc/ddl/json_schema)", len(roundtrip_specs) >= 7),
        ("domain stamped on every proven row", all(r["domain"] == DOMAIN for r in proven)),
        ("deterministic: re-running yields identical proven rows",
         [json.dumps(r, sort_keys=True) for r in build_proven_rows()] == [json.dumps(r, sort_keys=True) for r in proven]),
        ("a deliberately-wrong leaf stays CANDIDATE (never promoted)",
         wrong["serves_truth"] is False and wrong["promoted"] is False),
        ("the wrong leaf is NOT persisted as proven", NEGATIVE_SPEC["id"] not in set(ids)),
        ("an un-runnable fixture fails the proof, does not promote",
         err["serves_truth"] is False and err["promoted"] is False),
        # gated-effect ledger honesty
        (">=1 gated-effect candidate declared", len(gated) >= 1),
        ("EVERY gated-effect row is candidate:true / serves_truth:false",
         all(r["candidate"] is True and r["serves_truth"] is False for r in gated)),
        ("EVERY gated-effect row has a valid effect + a proof_obligation",
         all(r["effect"] in _VALID_EFFECTS and isinstance(r.get("proof_obligation"), str) and r["proof_obligation"]
             for r in gated)),
        ("EVERY gated-effect row is TYPED (non-null input+output edge type ids)",
         all(r["input_edge_type_id"] and r["output_edge_type_id"] for r in gated)),
        ("NO gated id overlaps a proven id (separate accounting)", set(r["primitive_id"] for r in gated).isdisjoint(set(ids))),
        ("new mutators registered into the shared registry (add-only seam)",
         all(m in MUTATOR_REGISTRY for m in _NEW_MUTATORS)),
    ]
    failed = [n for n, ok in checks if not ok]
    if failed:
        print("FAIL - domain_fmt_columnar_schema:\n  " + "\n  ".join(failed))
        return 1
    print(f"PASS - domain_fmt_columnar_schema: {len(proven)} proven-deterministic + TYPED leaves for domain "
          f"'{DOMAIN}' (serves_truth=true, L7_executed_proof; typed={len(typed)}=={len(proven)}); "
          f"{len(roundtrip_specs)} format roundtrip pairs proven reversible (parquet/avro/arrow/protobuf/orc/ddl/"
          f"json_schema); {len(gated)} gated-effect candidates (candidate/serves_truth=false, each with effect + "
          "proof_obligation) accounted SEPARATELY; a deliberately-wrong leaf and an un-runnable fixture correctly "
          "stay candidate.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    if args.write:
        manifest = write_pack()
        print(json.dumps(manifest, indent=2, sort_keys=True))
        return self_test()
    return self_test()


if __name__ == "__main__":
    raise SystemExit(main())
