#!/usr/bin/env python3
"""scripts.domain_fmt_markup_config — breadth primitives for the `fmt_markup_config` domain.

Deterministic parse / emit / validate / convert leaves for config + markup text formats: XML, YAML, TOML, INI,
dotenv, HCL, .properties, CSV-dialect, NDJSON. ADD-ONLY parallel path — it IMPORTS the shared machinery and never
edits it:
  * `run_primitive_proof` / `MUTATOR_REGISTRY` / `_receipt` from `scripts.mutator_registry` — the proof-runner
    EXECUTES each mutator against a fixture and flips serves_truth false->true ONLY on a PASSING executed proof
    (fixture-behavior + determinism, plus a roundtrip when the leaf declares an inverse);
  * `canonicalize_edge` from `scripts.build_edge_type_retrofit` — folds each leaf's logical edge labels to canonical
    type_ids so a proven leaf is also TYPED (input_edge_type_id + output_edge_type_id) and can chain.

Repo law honored HONESTLY: serves_truth=true is set ONLY by an executed passing proof of a DETERMINISTIC transform.
NETWORK/EFFECTFUL operations (fetching a remote config over HTTP, uploading to object storage, a config-lint model
call, writing to a cloud KV / secrets store) are NEVER run through the proof runner and NEVER serve truth — they are
declared as GATED-EFFECT candidates {candidate:true, serves_truth:false, effect, proof_obligation, edge type ids}.
The manifest reports proven_deterministic, typed, and gated_effect_candidates as SEPARATE counts.

Deterministic + offline: no network, no LLM, no wall-clock, no RNG (fixed literal manifest timestamp; stdlib only).
CLI: --self-test | --write.

Register tuple for the shared proof suite (REPORT ONLY — this module does NOT self-register):
    ("_repos/shared-backend-components/scripts/domain_fmt_markup_config.py", "domain_fmt_markup_config")
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import configparser
import csv
import io
import json
import re
import sys
import tomllib
import xml.etree.ElementTree as ET
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

DOMAIN = "fmt_markup_config"
FAMILY = "fmt_markup_config"
_FIXED_UTC = "2026-07-03"  # fixed literal timestamp — NO wall-clock (repo law: deterministic + offline)

OUT_DIR = _resource("data") / "dev-intel" / "domain_primitives"
OUT_JSONL = OUT_DIR / "domain_fmt_markup_config.jsonl"
OUT_MANIFEST = OUT_DIR / "manifest_fmt_markup_config.json"


# ── scalar helpers (shared by TOML + HCL emit/parse) ─────────────────────────────────────────────────────────
def _quote_scalar(value: Any) -> str:
    """Emit a scalar in `"str"` / bare-int / lowercase-bool form (TOML + HCL attribute syntax). bool before int."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    return '"' + str(value) + '"'


def _unquote_scalar(token: str) -> Any:
    token = token.strip()
    if len(token) >= 2 and token[0] == '"' and token[-1] == '"':
        return token[1:-1]
    if token in ("true", "false"):
        return token == "true"
    if token.lstrip("-").isdigit():
        return int(token)
    return token


# ── PURE deterministic mutators, contract (payload, **kwargs) -> (output, receipt). Family-prefixed `fmc_` so they
#    never collide with existing registry entries; registered via setdefault (idempotent, never overwrites). ──

# NDJSON ------------------------------------------------------------------------------------------------------
def fmc_ndjson_emit(records: list[dict[str, Any]], **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = "\n".join(json.dumps(r, sort_keys=True) for r in records)
    return out, _receipt("fmc_ndjson_emit", before=records, after=out, lossless=True, note="record batch -> ndjson text; fmc_ndjson_parse restores")


def fmc_ndjson_parse(text: str, **_kw: Any) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    out = [json.loads(line) for line in text.split("\n") if line.strip()]
    return out, _receipt("fmc_ndjson_parse", before=text, after=out, lossless=True, note="parse ndjson text -> record batch")


def fmc_ndjson_count(text: str, **_kw: Any) -> tuple[int, dict[str, Any]]:
    out = sum(1 for line in text.split("\n") if line.strip())
    return out, _receipt("fmc_ndjson_count", before=text, after=out, lossless=False, note="count non-empty ndjson rows")


def fmc_ndjson_to_json_array(text: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    records = [json.loads(line) for line in text.split("\n") if line.strip()]
    out = json.dumps(records, sort_keys=True)
    return out, _receipt("fmc_ndjson_to_json_array", before=text, after=out, lossless=True, note="ndjson text -> json array text; fmc_json_array_to_ndjson restores")


def fmc_json_array_to_ndjson(text: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = "\n".join(json.dumps(r, sort_keys=True) for r in json.loads(text))
    return out, _receipt("fmc_json_array_to_ndjson", before=text, after=out, lossless=True, note="json array text -> ndjson text")


# dotenv ------------------------------------------------------------------------------------------------------
def fmc_dotenv_emit(record: dict[str, str], **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = "\n".join(f"{k}={record[k]}" for k in sorted(record))
    return out, _receipt("fmc_dotenv_emit", before=record, after=out, lossless=True, note="record -> sorted dotenv (KEY=VALUE); fmc_dotenv_parse restores")


def fmc_dotenv_parse(text: str, **_kw: Any) -> tuple[dict[str, str], dict[str, Any]]:
    out: dict[str, str] = {}
    for line in text.split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        k, _, v = line.partition("=")
        out[k.strip()] = v.strip()
    return out, _receipt("fmc_dotenv_parse", before=text, after=out, lossless=True, note="parse dotenv text -> record (skips blanks/comments)")


# .properties -------------------------------------------------------------------------------------------------
def fmc_properties_emit(record: dict[str, str], **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = "\n".join(f"{k}={record[k]}" for k in sorted(record))
    return out, _receipt("fmc_properties_emit", before=record, after=out, lossless=True, note="record -> sorted java .properties; fmc_properties_parse restores")


def fmc_properties_parse(text: str, **_kw: Any) -> tuple[dict[str, str], dict[str, Any]]:
    out: dict[str, str] = {}
    for line in text.split("\n"):
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("!"):
            continue
        # java .properties accepts '=' or ':' as the separator — take the first occurrence
        idx_eq, idx_colon = line.find("="), line.find(":")
        cands = [i for i in (idx_eq, idx_colon) if i != -1]
        sep = min(cands)
        out[line[:sep].strip()] = line[sep + 1:].strip()
    return out, _receipt("fmc_properties_parse", before=text, after=out, lossless=True, note="parse .properties text -> record")


# INI ---------------------------------------------------------------------------------------------------------
def fmc_ini_emit(sections: dict[str, dict[str, str]], **_kw: Any) -> tuple[str, dict[str, Any]]:
    blocks: list[str] = []
    for section in sorted(sections):
        body = "\n".join(f"{k} = {sections[section][k]}" for k in sorted(sections[section]))
        blocks.append(f"[{section}]\n{body}" if body else f"[{section}]")
    out = "\n\n".join(blocks)
    return out, _receipt("fmc_ini_emit", before=sections, after=out, lossless=True, note="section map -> ini text; fmc_ini_parse restores")


def fmc_ini_parse(text: str, **_kw: Any) -> tuple[dict[str, dict[str, str]], dict[str, Any]]:
    cp = configparser.ConfigParser(interpolation=None)
    cp.optionxform = str  # preserve key case (default lowercases) — lossless roundtrip
    cp.read_string(text)
    out = {s: dict(cp[s]) for s in cp.sections()}
    return out, _receipt("fmc_ini_parse", before=text, after=out, lossless=True, note="parse ini text -> section map (case-preserving)")


def fmc_ini_section_names(text: str, **_kw: Any) -> tuple[list[str], dict[str, Any]]:
    cp = configparser.ConfigParser(interpolation=None)
    cp.optionxform = str
    cp.read_string(text)
    out = sorted(cp.sections())
    return out, _receipt("fmc_ini_section_names", before=text, after=out, lossless=False, note="ini text -> sorted section-name list")


# CSV-dialect -------------------------------------------------------------------------------------------------
def _csv_emit(records: list[dict[str, str]], delimiter: str) -> str:
    cols = sorted({k for r in records for k in r})
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=cols, delimiter=delimiter, lineterminator="\n")
    writer.writeheader()
    writer.writerows(records)
    return buf.getvalue().rstrip("\n")


def _csv_parse(text: str, delimiter: str) -> list[dict[str, str]]:
    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
    return [dict(row) for row in reader]


def fmc_csv_comma_emit(records: list[dict[str, str]], **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = _csv_emit(records, ",")
    return out, _receipt("fmc_csv_comma_emit", before=records, after=out, lossless=True, note="record batch -> comma csv text (sorted header); fmc_csv_comma_parse restores")


def fmc_csv_comma_parse(text: str, **_kw: Any) -> tuple[list[dict[str, str]], dict[str, Any]]:
    out = _csv_parse(text, ",")
    return out, _receipt("fmc_csv_comma_parse", before=text, after=out, lossless=True, note="parse comma csv text -> record batch")


def fmc_csv_semicolon_emit(records: list[dict[str, str]], **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = _csv_emit(records, ";")
    return out, _receipt("fmc_csv_semicolon_emit", before=records, after=out, lossless=True, note="record batch -> semicolon-dialect csv text; fmc_csv_semicolon_parse restores")


def fmc_csv_semicolon_parse(text: str, **_kw: Any) -> tuple[list[dict[str, str]], dict[str, Any]]:
    out = _csv_parse(text, ";")
    return out, _receipt("fmc_csv_semicolon_parse", before=text, after=out, lossless=True, note="parse semicolon-dialect csv text -> record batch")


def fmc_csv_delimiter_convert(text: str, from_delim: str = ",", to_delim: str = ";", **_kw: Any) -> tuple[str, dict[str, Any]]:
    rows = list(csv.reader(io.StringIO(text), delimiter=from_delim))
    buf = io.StringIO()
    csv.writer(buf, delimiter=to_delim, lineterminator="\n").writerows(rows)
    out = buf.getvalue().rstrip("\n")
    return out, _receipt("fmc_csv_delimiter_convert", before=text, after=out, lossless=True, note=f"csv dialect convert {from_delim!r} -> {to_delim!r}")


# XML ---------------------------------------------------------------------------------------------------------
def fmc_xml_emit(record: dict[str, str], **_kw: Any) -> tuple[str, dict[str, Any]]:
    root = ET.Element("root")
    for k in sorted(record):
        child = ET.SubElement(root, k)
        child.text = str(record[k])
    out = ET.tostring(root, encoding="unicode")
    return out, _receipt("fmc_xml_emit", before=record, after=out, lossless=True, note="flat record -> xml (sorted <root> children); fmc_xml_parse restores")


def fmc_xml_parse(text: str, **_kw: Any) -> tuple[dict[str, str], dict[str, Any]]:
    root = ET.fromstring(text)
    out = {child.tag: child.text for child in root}
    return out, _receipt("fmc_xml_parse", before=text, after=out, lossless=True, note="parse flat xml -> record")


def fmc_xml_validate_wellformed(text: str, **_kw: Any) -> tuple[bool, dict[str, Any]]:
    try:
        ET.fromstring(text)
        out = True
    except ET.ParseError:
        out = False
    return out, _receipt("fmc_xml_validate_wellformed", before=text, after=out, lossless=False, note="xml well-formedness check -> bool")


# YAML (deterministic flat/scalar + list subset; stdlib has no yaml) ------------------------------------------
def fmc_yaml_emit(record: dict[str, str], **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = "\n".join(f"{k}: {record[k]}" for k in sorted(record))
    return out, _receipt("fmc_yaml_emit", before=record, after=out, lossless=True, note="flat record -> sorted yaml mapping (scalar subset); fmc_yaml_parse restores")


def fmc_yaml_parse(text: str, **_kw: Any) -> tuple[dict[str, str], dict[str, Any]]:
    out: dict[str, str] = {}
    for line in text.split("\n"):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        k, _, v = line.partition(": ")
        out[k.strip()] = v
    return out, _receipt("fmc_yaml_parse", before=text, after=out, lossless=True, note="parse yaml mapping (scalar subset) -> record")


def fmc_yaml_list_emit(items: list[str], **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = "\n".join(f"- {i}" for i in items)
    return out, _receipt("fmc_yaml_list_emit", before=items, after=out, lossless=True, note="value list -> yaml block sequence; fmc_yaml_list_parse restores")


def fmc_yaml_list_parse(text: str, **_kw: Any) -> tuple[list[str], dict[str, Any]]:
    out = [line[2:] for line in text.split("\n") if line.startswith("- ")]
    return out, _receipt("fmc_yaml_list_parse", before=text, after=out, lossless=True, note="parse yaml block sequence -> value list")


# TOML (emit hand-rolled; parse via stdlib tomllib) ----------------------------------------------------------
def fmc_toml_emit(record: dict[str, Any], **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = "\n".join(f"{k} = {_quote_scalar(record[k])}" for k in sorted(record))
    return out, _receipt("fmc_toml_emit", before=record, after=out, lossless=True, note="flat record -> toml key/value (scalar subset); fmc_toml_parse restores")


def fmc_toml_parse(text: str, **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    out = tomllib.loads(text)
    return out, _receipt("fmc_toml_parse", before=text, after=out, lossless=True, note="parse toml text -> record (stdlib tomllib)")


def fmc_toml_table_emit(tables: dict[str, dict[str, Any]], **_kw: Any) -> tuple[str, dict[str, Any]]:
    blocks: list[str] = []
    for section in sorted(tables):
        body = "\n".join(f"{k} = {_quote_scalar(tables[section][k])}" for k in sorted(tables[section]))
        blocks.append(f"[{section}]\n{body}" if body else f"[{section}]")
    out = "\n".join(blocks)
    return out, _receipt("fmc_toml_table_emit", before=tables, after=out, lossless=True, note="table map -> toml [section] blocks; fmc_toml_table_parse restores")


def fmc_toml_table_parse(text: str, **_kw: Any) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    out = tomllib.loads(text)
    return out, _receipt("fmc_toml_table_parse", before=text, after=out, lossless=True, note="parse toml table blocks -> table map")


# HCL (deterministic attribute + block subset; stdlib has no hcl) --------------------------------------------
def fmc_hcl_attrs_emit(record: dict[str, Any], **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = "\n".join(f"{k} = {_quote_scalar(record[k])}" for k in sorted(record))
    return out, _receipt("fmc_hcl_attrs_emit", before=record, after=out, lossless=True, note="record -> hcl attribute block (scalar subset); fmc_hcl_attrs_parse restores")


def fmc_hcl_attrs_parse(text: str, **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    out: dict[str, Any] = {}
    for line in text.split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        k, _, rest = line.partition("=")
        out[k.strip()] = _unquote_scalar(rest)
    return out, _receipt("fmc_hcl_attrs_parse", before=text, after=out, lossless=True, note="parse hcl attribute block -> record")


def fmc_hcl_block_emit(block: dict[str, Any], **_kw: Any) -> tuple[str, dict[str, Any]]:
    label_str = " ".join(f'"{lbl}"' for lbl in block["labels"])
    header = f'{block["block_type"]} {label_str} {{'.replace("  {", " {")
    body_lines = [f"  {k} = {_quote_scalar(block['body'][k])}" for k in sorted(block["body"])]
    out = "\n".join([header] + body_lines + ["}"])
    return out, _receipt("fmc_hcl_block_emit", before=block, after=out, lossless=True, note="labelled hcl block -> text; fmc_hcl_block_parse restores")


def fmc_hcl_block_parse(text: str, **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    lines = text.split("\n")
    first = lines[0].strip().rstrip("{").strip()
    tokens = re.findall(r'"[^"]*"|\S+', first)
    block_type = tokens[0]
    labels = [t[1:-1] for t in tokens[1:]]
    body: dict[str, Any] = {}
    for line in lines[1:]:
        line = line.strip()
        if not line or line == "}":
            continue
        k, _, rest = line.partition("=")
        body[k.strip()] = _unquote_scalar(rest)
    out = {"block_type": block_type, "labels": labels, "body": body}
    return out, _receipt("fmc_hcl_block_parse", before=text, after=out, lossless=True, note="parse labelled hcl block -> {block_type,labels,body}")


#: new pure mutators to plug into the shared registry (idempotent setdefault — never overwrites an existing entry)
_NEW_MUTATORS = {
    "fmc_ndjson_emit": fmc_ndjson_emit, "fmc_ndjson_parse": fmc_ndjson_parse, "fmc_ndjson_count": fmc_ndjson_count,
    "fmc_ndjson_to_json_array": fmc_ndjson_to_json_array, "fmc_json_array_to_ndjson": fmc_json_array_to_ndjson,
    "fmc_dotenv_emit": fmc_dotenv_emit, "fmc_dotenv_parse": fmc_dotenv_parse,
    "fmc_properties_emit": fmc_properties_emit, "fmc_properties_parse": fmc_properties_parse,
    "fmc_ini_emit": fmc_ini_emit, "fmc_ini_parse": fmc_ini_parse, "fmc_ini_section_names": fmc_ini_section_names,
    "fmc_csv_comma_emit": fmc_csv_comma_emit, "fmc_csv_comma_parse": fmc_csv_comma_parse,
    "fmc_csv_semicolon_emit": fmc_csv_semicolon_emit, "fmc_csv_semicolon_parse": fmc_csv_semicolon_parse,
    "fmc_csv_delimiter_convert": fmc_csv_delimiter_convert,
    "fmc_xml_emit": fmc_xml_emit, "fmc_xml_parse": fmc_xml_parse, "fmc_xml_validate_wellformed": fmc_xml_validate_wellformed,
    "fmc_yaml_emit": fmc_yaml_emit, "fmc_yaml_parse": fmc_yaml_parse,
    "fmc_yaml_list_emit": fmc_yaml_list_emit, "fmc_yaml_list_parse": fmc_yaml_list_parse,
    "fmc_toml_emit": fmc_toml_emit, "fmc_toml_parse": fmc_toml_parse,
    "fmc_toml_table_emit": fmc_toml_table_emit, "fmc_toml_table_parse": fmc_toml_table_parse,
    "fmc_hcl_attrs_emit": fmc_hcl_attrs_emit, "fmc_hcl_attrs_parse": fmc_hcl_attrs_parse,
    "fmc_hcl_block_emit": fmc_hcl_block_emit, "fmc_hcl_block_parse": fmc_hcl_block_parse,
}


def register_new_mutators() -> None:
    """Plug the domain's pure mutators into the shared MUTATOR_REGISTRY (registration, not a rewrite). Idempotent."""
    for name, fn in _NEW_MUTATORS.items():
        MUTATOR_REGISTRY.setdefault(name, fn)


register_new_mutators()


# ── the leaf primitives: each a REAL capability with a concrete fixture + expected (+ inverse where roundtrip holds).
# spec fields: id, mutator, fixture, expected, args?, inverse?, capability, input_edge, output_edge ──
LEAF_SPECS: list[dict[str, Any]] = [
    # NDJSON
    {"id": "prim:fmc:ndjson_emit", "mutator": "fmc_ndjson_emit", "fixture": [{"a": 1}, {"b": 2}],
     "expected": '{"a": 1}\n{"b": 2}', "inverse": "fmc_ndjson_parse", "capability": "emit",
     "input_edge": "RecordBatch", "output_edge": "NdjsonText"},
    {"id": "prim:fmc:ndjson_parse", "mutator": "fmc_ndjson_parse", "fixture": '{"x": 1}\n{"y": 2}',
     "expected": [{"x": 1}, {"y": 2}], "capability": "parse",
     "input_edge": "NdjsonText", "output_edge": "RecordBatch"},
    {"id": "prim:fmc:ndjson_count", "mutator": "fmc_ndjson_count", "fixture": '{"a": 1}\n{"b": 2}\n', "expected": 2,
     "capability": "validate", "input_edge": "NdjsonText", "output_edge": "Count"},
    {"id": "prim:fmc:ndjson_to_json_array", "mutator": "fmc_ndjson_to_json_array", "fixture": '{"a": 1}\n{"b": 2}',
     "expected": '[{"a": 1}, {"b": 2}]', "inverse": "fmc_json_array_to_ndjson", "capability": "convert",
     "input_edge": "NdjsonText", "output_edge": "JsonArrayText"},
    {"id": "prim:fmc:json_array_to_ndjson", "mutator": "fmc_json_array_to_ndjson", "fixture": '[{"a": 1}, {"b": 2}]',
     "expected": '{"a": 1}\n{"b": 2}', "capability": "convert",
     "input_edge": "JsonArrayText", "output_edge": "NdjsonText"},

    # dotenv
    {"id": "prim:fmc:dotenv_emit", "mutator": "fmc_dotenv_emit", "fixture": {"HOST": "localhost", "PORT": "8080"},
     "expected": "HOST=localhost\nPORT=8080", "inverse": "fmc_dotenv_parse", "capability": "emit",
     "input_edge": "Record", "output_edge": "DotenvText"},
    {"id": "prim:fmc:dotenv_parse", "mutator": "fmc_dotenv_parse", "fixture": "# comment\nHOST=localhost\nPORT=8080\n",
     "expected": {"HOST": "localhost", "PORT": "8080"}, "capability": "parse",
     "input_edge": "DotenvText", "output_edge": "Record"},

    # .properties
    {"id": "prim:fmc:properties_emit", "mutator": "fmc_properties_emit", "fixture": {"db.host": "localhost", "db.port": "5432"},
     "expected": "db.host=localhost\ndb.port=5432", "inverse": "fmc_properties_parse", "capability": "emit",
     "input_edge": "Record", "output_edge": "PropertiesText"},
    {"id": "prim:fmc:properties_parse", "mutator": "fmc_properties_parse", "fixture": "db.host=localhost\ndb.port : 5432",
     "expected": {"db.host": "localhost", "db.port": "5432"}, "capability": "parse",
     "input_edge": "PropertiesText", "output_edge": "Record"},

    # INI
    {"id": "prim:fmc:ini_emit", "mutator": "fmc_ini_emit",
     "fixture": {"server": {"host": "localhost", "port": "8080"}}, "expected": "[server]\nhost = localhost\nport = 8080",
     "inverse": "fmc_ini_parse", "capability": "emit", "input_edge": "SectionMap", "output_edge": "IniText"},
    {"id": "prim:fmc:ini_parse", "mutator": "fmc_ini_parse", "fixture": "[server]\nhost = localhost\nport = 8080",
     "expected": {"server": {"host": "localhost", "port": "8080"}}, "capability": "parse",
     "input_edge": "IniText", "output_edge": "SectionMap"},
    {"id": "prim:fmc:ini_section_names", "mutator": "fmc_ini_section_names",
     "fixture": "[b]\nx = 1\n\n[a]\ny = 2", "expected": ["a", "b"], "capability": "validate",
     "input_edge": "IniText", "output_edge": "FieldList"},

    # CSV-dialect
    {"id": "prim:fmc:csv_comma_emit", "mutator": "fmc_csv_comma_emit",
     "fixture": [{"a": "1", "b": "2"}, {"a": "3", "b": "4"}], "expected": "a,b\n1,2\n3,4",
     "inverse": "fmc_csv_comma_parse", "capability": "emit", "input_edge": "RecordBatch", "output_edge": "CsvText"},
    {"id": "prim:fmc:csv_comma_parse", "mutator": "fmc_csv_comma_parse", "fixture": "a,b\n1,2\n3,4",
     "expected": [{"a": "1", "b": "2"}, {"a": "3", "b": "4"}], "capability": "parse",
     "input_edge": "CsvText", "output_edge": "RecordBatch"},
    {"id": "prim:fmc:csv_semicolon_emit", "mutator": "fmc_csv_semicolon_emit",
     "fixture": [{"a": "1", "b": "2"}], "expected": "a;b\n1;2", "inverse": "fmc_csv_semicolon_parse",
     "capability": "emit", "input_edge": "RecordBatch", "output_edge": "CsvText"},
    {"id": "prim:fmc:csv_semicolon_parse", "mutator": "fmc_csv_semicolon_parse", "fixture": "a;b\n1;2",
     "expected": [{"a": "1", "b": "2"}], "capability": "parse",
     "input_edge": "CsvText", "output_edge": "RecordBatch"},
    {"id": "prim:fmc:csv_delimiter_convert", "mutator": "fmc_csv_delimiter_convert", "fixture": "a,b\n1,2",
     "expected": "a;b\n1;2", "args": {"from_delim": ",", "to_delim": ";"}, "capability": "convert",
     "input_edge": "CsvText", "output_edge": "CsvText"},

    # XML
    {"id": "prim:fmc:xml_emit", "mutator": "fmc_xml_emit", "fixture": {"a": "1", "b": "2"},
     "expected": "<root><a>1</a><b>2</b></root>", "inverse": "fmc_xml_parse", "capability": "emit",
     "input_edge": "Record", "output_edge": "XmlText"},
    {"id": "prim:fmc:xml_parse", "mutator": "fmc_xml_parse", "fixture": "<root><a>1</a><b>2</b></root>",
     "expected": {"a": "1", "b": "2"}, "capability": "parse", "input_edge": "XmlText", "output_edge": "Record"},
    {"id": "prim:fmc:xml_validate_wellformed", "mutator": "fmc_xml_validate_wellformed",
     "fixture": "<root><a>1</a></root>", "expected": True, "capability": "validate",
     "input_edge": "XmlText", "output_edge": "Bool"},

    # YAML
    {"id": "prim:fmc:yaml_emit", "mutator": "fmc_yaml_emit", "fixture": {"city": "paris", "name": "alice"},
     "expected": "city: paris\nname: alice", "inverse": "fmc_yaml_parse", "capability": "emit",
     "input_edge": "Record", "output_edge": "YamlText"},
    {"id": "prim:fmc:yaml_parse", "mutator": "fmc_yaml_parse", "fixture": "# hdr\ncity: paris\nname: alice",
     "expected": {"city": "paris", "name": "alice"}, "capability": "parse",
     "input_edge": "YamlText", "output_edge": "Record"},
    {"id": "prim:fmc:yaml_list_emit", "mutator": "fmc_yaml_list_emit", "fixture": ["alpha", "beta"],
     "expected": "- alpha\n- beta", "inverse": "fmc_yaml_list_parse", "capability": "emit",
     "input_edge": "ValueList", "output_edge": "YamlText"},
    {"id": "prim:fmc:yaml_list_parse", "mutator": "fmc_yaml_list_parse", "fixture": "- alpha\n- beta",
     "expected": ["alpha", "beta"], "capability": "parse", "input_edge": "YamlText", "output_edge": "ValueList"},

    # TOML
    {"id": "prim:fmc:toml_emit", "mutator": "fmc_toml_emit", "fixture": {"name": "alice", "port": 8080},
     "expected": 'name = "alice"\nport = 8080', "inverse": "fmc_toml_parse", "capability": "emit",
     "input_edge": "Record", "output_edge": "TomlText"},
    {"id": "prim:fmc:toml_parse", "mutator": "fmc_toml_parse", "fixture": 'name = "alice"\nport = 8080',
     "expected": {"name": "alice", "port": 8080}, "capability": "parse",
     "input_edge": "TomlText", "output_edge": "Record"},
    {"id": "prim:fmc:toml_table_emit", "mutator": "fmc_toml_table_emit",
     "fixture": {"server": {"host": "localhost", "port": 8080}},
     "expected": '[server]\nhost = "localhost"\nport = 8080', "inverse": "fmc_toml_table_parse", "capability": "emit",
     "input_edge": "TableMap", "output_edge": "TomlText"},
    {"id": "prim:fmc:toml_table_parse", "mutator": "fmc_toml_table_parse",
     "fixture": '[server]\nhost = "localhost"\nport = 8080',
     "expected": {"server": {"host": "localhost", "port": 8080}}, "capability": "parse",
     "input_edge": "TomlText", "output_edge": "TableMap"},

    # HCL
    {"id": "prim:fmc:hcl_attrs_emit", "mutator": "fmc_hcl_attrs_emit", "fixture": {"count": 3, "region": "us-east"},
     "expected": 'count = 3\nregion = "us-east"', "inverse": "fmc_hcl_attrs_parse", "capability": "emit",
     "input_edge": "Record", "output_edge": "HclText"},
    {"id": "prim:fmc:hcl_attrs_parse", "mutator": "fmc_hcl_attrs_parse", "fixture": 'count = 3\nregion = "us-east"',
     "expected": {"count": 3, "region": "us-east"}, "capability": "parse",
     "input_edge": "HclText", "output_edge": "Record"},
    {"id": "prim:fmc:hcl_block_emit", "mutator": "fmc_hcl_block_emit",
     "fixture": {"block_type": "resource", "labels": ["aws_instance", "web"], "body": {"ami": "abc-123", "count": 2}},
     "expected": 'resource "aws_instance" "web" {\n  ami = "abc-123"\n  count = 2\n}',
     "inverse": "fmc_hcl_block_parse", "capability": "emit", "input_edge": "HclBlock", "output_edge": "HclText"},
    {"id": "prim:fmc:hcl_block_parse", "mutator": "fmc_hcl_block_parse",
     "fixture": 'resource "aws_instance" "web" {\n  ami = "abc-123"\n  count = 2\n}',
     "expected": {"block_type": "resource", "labels": ["aws_instance", "web"], "body": {"ami": "abc-123", "count": 2}},
     "capability": "parse", "input_edge": "HclText", "output_edge": "HclBlock"},
]

#: deliberately-wrong leaf — the proof gate MUST leave it candidate (never persisted as proven)
NEGATIVE_SPEC: dict[str, Any] = {
    "id": "prim:fmc:WRONG_expected", "mutator": "fmc_xml_emit", "fixture": {"a": "1"},
    "expected": "<root><WRONG>999</WRONG></root>", "input_edge": "Record", "output_edge": "XmlText"}


# ── GATED-EFFECT candidates: network / cloud / model operations. NEVER proven, NEVER serves_truth=true. ──
# Each declares {candidate, serves_truth:false, effect, proof_obligation, edge type ids} per repo law.
GATED_EFFECT_SPECS: list[dict[str, Any]] = [
    {"id": "prim:fmc:fetch_remote_config", "capability": "fetch", "effect": "network_read",
     "description": "GET a config/markup file over HTTP(S) and return its text body.",
     "input_edge": "ConfigUri", "output_edge": "ConfigText"},
    {"id": "prim:fmc:load_config_from_secrets_manager", "capability": "fetch", "effect": "network_read",
     "description": "Read a config document from a cloud secrets manager by name.",
     "input_edge": "SecretRef", "output_edge": "ConfigText"},
    {"id": "prim:fmc:put_config_to_object_storage", "capability": "publish", "effect": "network_write",
     "description": "Upload rendered config text to cloud object storage (S3/GCS-shape).",
     "input_edge": "ConfigText", "output_edge": "ObjectStorageUri"},
    {"id": "prim:fmc:publish_config_to_kv_store", "capability": "publish", "effect": "network_write",
     "description": "Write config key/values into a cloud KV / parameter store.",
     "input_edge": "Record", "output_edge": "WriteReceipt"},
    {"id": "prim:fmc:lint_config_via_model", "capability": "validate", "effect": "model_call",
     "description": "Ask an LLM to lint/explain a config document (advisory, never truth).",
     "input_edge": "ConfigText", "output_edge": "LintReport"},
    {"id": "prim:fmc:write_config_to_local_file", "capability": "publish", "effect": "file_write",
     "description": "Persist rendered config text to a local file path (effectful side write).",
     "input_edge": "ConfigText", "output_edge": "FilePath"},
]


def _prove_one(spec: dict[str, Any]) -> dict[str, Any]:
    return run_primitive_proof(
        spec["id"], spec["mutator"], spec["fixture"], spec["expected"],
        mutator_args=spec.get("args") or {}, has_inverse=spec.get("inverse"),
    )


def prove_all() -> list[tuple[dict[str, Any], dict[str, Any]]]:
    """Run every declared leaf through the imported executed-proof runner. Returns [(spec, receipt), ...]."""
    return [(s, _prove_one(s)) for s in LEAF_SPECS]


def build_proven_rows() -> list[dict[str, Any]]:
    """Persist-ready rows for leaves whose executed proof PASSED — TYPED via canonicalize_edge (workable == typed)."""
    rows: list[dict[str, Any]] = []
    for spec, receipt in prove_all():
        if receipt["serves_truth"] is not True:
            continue  # a failing / wrong-expected leaf stays candidate and is NOT persisted (the gate is the point)
        rows.append({
            "record_type": "proven_deterministic_primitive",
            "primitive_id": receipt["primitive_id"],
            "mutator": receipt["mutator"],
            "domain": DOMAIN,
            "family": FAMILY,
            "capability": spec["capability"],
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
    """Gated-effect candidates — NEVER proven, serves_truth=false, each carries effect + proof_obligation + edges."""
    rows: list[dict[str, Any]] = []
    for spec in GATED_EFFECT_SPECS:
        rows.append({
            "record_type": "gated_effect_candidate",
            "primitive_id": spec["id"],
            "domain": DOMAIN,
            "family": FAMILY,
            "capability": spec["capability"],
            "description": spec["description"],
            "candidate": True,
            "serves_truth": False,
            "effect": spec["effect"],
            "proof_obligation": "live integration test with credential",
            "input_edge": spec["input_edge"],
            "output_edge": spec["output_edge"],
            "input_edge_type_id": canonicalize_edge(spec["input_edge"]),
            "output_edge_type_id": canonicalize_edge(spec["output_edge"]),
        })
    return rows


def build_manifest(proven: list[dict[str, Any]], gated: list[dict[str, Any]]) -> dict[str, Any]:
    typed = [r for r in proven if r["input_edge_type_id"] and r["output_edge_type_id"]]
    return {
        "record_type": "domain_primitive_manifest",
        "domain": DOMAIN,
        "family": FAMILY,
        "generator": "scripts/domain_fmt_markup_config.py",
        "generated_utc": _FIXED_UTC,
        "formats_covered": ["XML", "YAML", "TOML", "INI", "dotenv", "HCL", ".properties", "CSV-dialect", "NDJSON"],
        "defined_leaf_count": len(LEAF_SPECS),
        # SEPARATE, honest counts (repo law):
        "proven_deterministic": len(proven),
        "typed": len(typed),
        "gated_effect_candidates": len(gated),
        "verification_level": "L7_executed_proof",
        "proven_primitive_ids": sorted(r["primitive_id"] for r in proven),
        "gated_effect_primitive_ids": sorted(r["primitive_id"] for r in gated),
        "note": "serves_truth=true is set ONLY by an executed passing proof (run_primitive_proof, imported from "
                "scripts/mutator_registry.py). Every proven row is TYPED via canonicalize_edge (imported from "
                "scripts/build_edge_type_retrofit.py). NETWORK/EFFECTFUL ops are declared as gated-effect candidates "
                "(serves_truth=false, effect + proof_obligation) and are NEVER run through the proof runner.",
    }


def write_pack() -> dict[str, Any]:
    proven = build_proven_rows()
    gated = build_gated_rows()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    # Separate sections of the shard: a section marker line, then proven rows, then gated-effect candidate rows.
    lines: list[str] = []
    lines.append(json.dumps({"record_type": "shard_section", "section": "proven_deterministic",
                             "count": len(proven)}, sort_keys=True))
    lines += [json.dumps(r, ensure_ascii=False, sort_keys=True) for r in proven]
    lines.append(json.dumps({"record_type": "shard_section", "section": "gated_effect_candidates",
                             "count": len(gated)}, sort_keys=True))
    lines += [json.dumps(r, ensure_ascii=False, sort_keys=True) for r in gated]
    OUT_JSONL.write_text("".join(ln + "\n" for ln in lines), encoding="utf-8")
    manifest = build_manifest(proven, gated)
    OUT_MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def self_test() -> int:
    proven_receipts = prove_all()
    proven = build_proven_rows()
    gated = build_gated_rows()
    ids = [r["primitive_id"] for r in proven]
    typed = [r for r in proven if r["input_edge_type_id"] and r["output_edge_type_id"]]
    roundtrip_specs = [s for s in LEAF_SPECS if s.get("inverse")]
    proven_by_id = {r["primitive_id"]: r for (_s, r) in proven_receipts}

    # deliberately-wrong leaf must stay candidate (proof gate is real, not a rubber stamp) — and never enter rows
    wrong = _prove_one(NEGATIVE_SPEC)
    # a second wrong path: an un-runnable fixture -> execution error -> not promoted
    err = run_primitive_proof("prim:fmc:EXEC_ERROR", "fmc_xml_parse", object(), "irrelevant")

    manifest = build_manifest(proven, gated)
    checks: list[tuple[str, bool]] = [
        (">=25 leaves declared", len(LEAF_SPECS) >= 25),
        ("unique primitive ids across proven+gated",
         len(set(ids) | {r["primitive_id"] for r in gated}) == len(proven) + len(gated)),
        (">=25 leaves PROVE serves_truth=true via an executed proof", len(proven) >= 25),
        ("every proven receipt is L7_executed_proof with all sub-proofs passing",
         all(r["verification_level"] == "L7_executed_proof" and all(p["passed"] for p in r["proofs"])
             for (_s, r) in proven_receipts if r["serves_truth"] is True)),
        ("EVERY proven row carries non-null input+output edge type ids", len(typed) == len(proven)),
        ("manifest typed == proven_deterministic", manifest["typed"] == manifest["proven_deterministic"]),
        ("roundtrip-inverse pairs actually ran + PASSED a roundtrip proof", all(
            any(p["name"] == "roundtrip_test" and p["passed"] for p in proven_by_id[s["id"]]["proofs"])
            for s in roundtrip_specs)),
        ("every format family present in proven mutators", all(
            any(tok in r["mutator"] for r in proven)
            for tok in ("xml", "yaml", "toml", "ini", "dotenv", "hcl", "properties", "csv", "ndjson"))),
        ("domain+family stamped on every proven row",
         all(r["domain"] == DOMAIN and r["family"] == FAMILY for r in proven)),
        ("deterministic: re-running yields identical proven rows",
         [json.dumps(r, sort_keys=True) for r in build_proven_rows()] == [json.dumps(r, sort_keys=True) for r in proven]),
        ("a deliberately-wrong leaf stays CANDIDATE (never promoted)",
         wrong["serves_truth"] is False and wrong["promoted"] is False),
        ("the wrong leaf is NOT persisted", NEGATIVE_SPEC["id"] not in set(ids)),
        ("an un-runnable fixture fails the proof, does not promote",
         err["serves_truth"] is False and err["promoted"] is False),
        # gated-effect law: every gated row is candidate/serves_truth=false with an effect + proof_obligation + edges
        (">=1 gated-effect candidate declared", len(gated) >= 1),
        ("EVERY gated row is candidate=true, serves_truth=false",
         all(r["candidate"] is True and r["serves_truth"] is False for r in gated)),
        ("EVERY gated row carries a known effect + a proof_obligation",
         all(r["effect"] in ("network_read", "network_write", "model_call", "file_write")
             and r["proof_obligation"] == "live integration test with credential" for r in gated)),
        ("EVERY gated row is TYPED (non-null input+output edge type ids)",
         all(r["input_edge_type_id"] and r["output_edge_type_id"] for r in gated)),
        ("no gated id ever appears in the proven set", set(r["primitive_id"] for r in gated).isdisjoint(set(ids))),
        ("new mutators registered into the shared registry (add-only seam)",
         all(m in MUTATOR_REGISTRY for m in _NEW_MUTATORS)),
    ]
    failed = [n for n, ok in checks if not ok]
    if failed:
        print("FAIL - domain_fmt_markup_config:\n  " + "\n  ".join(failed))
        return 1
    print(f"PASS - domain_fmt_markup_config: {len(proven)} proven-deterministic + TYPED leaves "
          f"(serves_truth=true, L7_executed_proof; typed={len(typed)}=={len(proven)}) across XML/YAML/TOML/INI/"
          f"dotenv/HCL/.properties/CSV-dialect/NDJSON; {len(roundtrip_specs)} inverse pairs proven reversible via "
          f"roundtrip; {len(gated)} gated-effect candidates (serves_truth=false, effect+proof_obligation, honestly "
          "NOT proven); a deliberately-wrong leaf and an un-runnable fixture correctly stay candidate.")
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
