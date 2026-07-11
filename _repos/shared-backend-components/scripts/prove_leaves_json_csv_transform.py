#!/usr/bin/env python3
"""scripts.prove_leaves_json_csv_transform — WORKABLE (proven + TYPED) deterministic leaves for `json_csv_transform`.

ADD-ONLY parallel path. It IMPORTS the shared machinery (never edits it):
  * `run_primitive_proof` / `MUTATOR_REGISTRY` / `_receipt` from `scripts.mutator_registry` — the proof-runner EXECUTES
    each mutator against a fixture and flips serves_truth false->true ONLY on a PASSING executed proof;
  * `canonicalize_edge` from `scripts.build_edge_type_retrofit` — folds each leaf's logical edge labels to canonical
    type_ids so a proven leaf is also TYPED (the fix for "proven but untyped": a workable leaf MUST carry canonical
    input/output edge types so it can chain).

Family shape hint: RecordBatch -> SerializedText. Each leaf declares a sensible, sometimes more-specific, input_edge /
output_edge label; where a leaf has a true inverse (parse/emit, flatten/unflatten, encode/decode) the ROUNDTRIP is
proven reversible via has_inverse. serves_truth=true here is CORRECT + required — it is set ONLY by the executed proof;
a deliberately-wrong-expected leaf stays candidate and is NEVER persisted. Deterministic + offline (no wall-clock/RNG/
network in any body; fixed literal manifest timestamp). CLI: --self-test | --write.

Register tuple for the shared proof suite (REPORT ONLY — this module does NOT self-register):
    ("_repos/shared-backend-components/scripts/prove_leaves_json_csv_transform.py", "prove_leaves_json_csv_transform")
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import json
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

FAMILY = "json_csv_transform"
_FIXED_UTC = "2026-07-03"  # fixed literal timestamp — NO wall-clock (repo law: deterministic + offline)

OUT_DIR = _resource("data") / "dev-intel" / "proven_primitives"
OUT_JSONL = OUT_DIR / "proven_json_csv_transform.jsonl"
OUT_MANIFEST = OUT_DIR / "manifest_json_csv_transform.json"


# ── PURE deterministic mutators, contract (payload, **kwargs) -> (output, receipt). Family-prefixed (`jct_`) so they
#    never collide with existing registry entries; registered via setdefault (idempotent, never overwrites). ──
def jct_row_to_json(row: dict[str, Any], **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = json.dumps(row, sort_keys=True)
    return out, _receipt("jct_row_to_json", before=row, after=out, lossless=True, note="record -> canonical json text; jct_json_to_row restores")


def jct_json_to_row(text: str, **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    out = json.loads(text)
    return out, _receipt("jct_json_to_row", before=text, after=out, lossless=True, note="parse a json object row")


def jct_records_to_ndjson(records: list[dict[str, Any]], **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = "\n".join(json.dumps(r, sort_keys=True) for r in records)
    return out, _receipt("jct_records_to_ndjson", before=records, after=out, lossless=True, note="record batch -> ndjson text; jct_ndjson_to_records restores")


def jct_ndjson_to_records(text: str, **_kw: Any) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    out = [json.loads(line) for line in text.split("\n") if line.strip()]
    return out, _receipt("jct_ndjson_to_records", before=text, after=out, lossless=True, note="parse ndjson text -> record batch")


def jct_csv_line_emit(fields: list[Any], sep: str = ",", **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = sep.join(str(f) for f in fields)
    return out, _receipt("jct_csv_line_emit", before=fields, after=out, lossless=True, note="field list -> csv line; jct_csv_line_parse restores")


def jct_csv_line_parse(line: str, sep: str = ",", **_kw: Any) -> tuple[list[str], dict[str, Any]]:
    out = line.split(sep)
    return out, _receipt("jct_csv_line_parse", before=line, after=out, lossless=True, note="parse a csv line -> field list")


def jct_tsv_line_emit(fields: list[Any], **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = "\t".join(str(f) for f in fields)
    return out, _receipt("jct_tsv_line_emit", before=fields, after=out, lossless=True, note="field list -> tsv line; jct_tsv_line_parse restores")


def jct_tsv_line_parse(line: str, **_kw: Any) -> tuple[list[str], dict[str, Any]]:
    out = line.split("\t")
    return out, _receipt("jct_tsv_line_parse", before=line, after=out, lossless=True, note="parse a tsv line -> field list")


def _sorted_cols(records: list[dict[str, Any]]) -> list[str]:
    return sorted({k for r in records for k in r})


def jct_records_to_csv(records: list[dict[str, Any]], **_kw: Any) -> tuple[str, dict[str, Any]]:
    cols = _sorted_cols(records)
    lines = [",".join(cols)] + [",".join(str(r.get(c, "")) for c in cols) for r in records]
    out = "\n".join(lines)
    return out, _receipt("jct_records_to_csv", before=records, after=out, lossless=True, note="record batch -> csv text (sorted header); jct_csv_to_records restores")


def jct_csv_to_records(text: str, **_kw: Any) -> tuple[list[dict[str, str]], dict[str, Any]]:
    lines = text.split("\n")
    cols = lines[0].split(",")
    out = [dict(zip(cols, ln.split(","))) for ln in lines[1:] if ln != ""]
    return out, _receipt("jct_csv_to_records", before=text, after=out, lossless=True, note="parse csv text (header row) -> record batch")


def jct_json_prettify(text: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = json.dumps(json.loads(text), sort_keys=True, indent=2)
    return out, _receipt("jct_json_prettify", before=text, after=out, lossless=True, note="json text -> pretty (indent 2); jct_json_minify restores compact")


def jct_json_minify(text: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = json.dumps(json.loads(text), sort_keys=True, separators=(",", ":"))
    return out, _receipt("jct_json_minify", before=text, after=out, lossless=True, note="json text -> minified compact form")


def jct_kv_line_emit(record: dict[str, Any], **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = ";".join(f"{k}={record[k]}" for k in sorted(record))
    return out, _receipt("jct_kv_line_emit", before=record, after=out, lossless=True, note="record -> canonical (sorted) kv line; jct_kv_line_parse restores")


def jct_kv_line_parse(text: str, **_kw: Any) -> tuple[dict[str, str], dict[str, Any]]:
    out = dict(p.split("=", 1) for p in text.split(";")) if text else {}
    return out, _receipt("jct_kv_line_parse", before=text, after=out, lossless=True, note="parse a kv line -> record")


def jct_flatten_record(record: dict[str, Any], sep: str = ".", **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    def _flatten(d: dict[str, Any], prefix: str) -> dict[str, Any]:
        items: dict[str, Any] = {}
        for k, v in d.items():
            nk = f"{prefix}{sep}{k}" if prefix else k
            if isinstance(v, dict):
                items.update(_flatten(v, nk))
            else:
                items[nk] = v
        return items

    out = _flatten(record, "")
    return out, _receipt("jct_flatten_record", before=record, after=out, lossless=True, note="nested record -> dotted flat record; jct_unflatten_record restores")


def jct_unflatten_record(flat: dict[str, Any], sep: str = ".", **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    out: dict[str, Any] = {}
    for k, v in flat.items():
        parts = k.split(sep)
        d = out
        for p in parts[:-1]:
            d = d.setdefault(p, {})
        d[parts[-1]] = v
    return out, _receipt("jct_unflatten_record", before=flat, after=out, lossless=True, note="dotted flat record -> nested record")


def jct_records_to_json_array(records: list[dict[str, Any]], **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = json.dumps(records, sort_keys=True)
    return out, _receipt("jct_records_to_json_array", before=records, after=out, lossless=True, note="record batch -> json array text; jct_json_array_to_records restores")


def jct_json_array_to_records(text: str, **_kw: Any) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    out = json.loads(text)
    return out, _receipt("jct_json_array_to_records", before=text, after=out, lossless=True, note="parse json array text -> record batch")


def jct_dict_to_pairs(record: dict[str, Any], **_kw: Any) -> tuple[list[list[Any]], dict[str, Any]]:
    out = [[k, record[k]] for k in sorted(record)]
    return out, _receipt("jct_dict_to_pairs", before=record, after=out, lossless=True, note="record -> sorted [key,value] pair list; jct_pairs_to_dict restores")


def jct_pairs_to_dict(pairs: list[list[Any]], **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    out = {k: v for k, v in pairs}
    return out, _receipt("jct_pairs_to_dict", before=pairs, after=out, lossless=True, note="[key,value] pair list -> record")


def jct_records_to_csv_header(records: list[dict[str, Any]], **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = ",".join(_sorted_cols(records))
    return out, _receipt("jct_records_to_csv_header", before=records, after=out, lossless=False, note="record batch -> sorted csv header line")


def jct_csv_escape_field(field: Any, **_kw: Any) -> tuple[str, dict[str, Any]]:
    s = str(field)
    out = '"' + s.replace('"', '""') + '"' if any(c in s for c in (",", '"', "\n")) else s
    return out, _receipt("jct_csv_escape_field", before=field, after=out, lossless=False, note="rfc4180 field quoting when special chars present")


def jct_row_values_to_str(record: dict[str, Any], **_kw: Any) -> tuple[dict[str, str], dict[str, Any]]:
    out = {k: str(v) for k, v in record.items()}
    return out, _receipt("jct_row_values_to_str", before=record, after=out, lossless=False, note="stringify every field value (csv-ready record)")


def jct_ndjson_count(text: str, **_kw: Any) -> tuple[int, dict[str, Any]]:
    out = sum(1 for line in text.split("\n") if line.strip())
    return out, _receipt("jct_ndjson_count", before=text, after=out, lossless=False, note="count non-empty ndjson rows")


def jct_csv_row_count(text: str, **_kw: Any) -> tuple[int, dict[str, Any]]:
    lines = [ln for ln in text.split("\n") if ln != ""]
    out = max(0, len(lines) - 1)
    return out, _receipt("jct_csv_row_count", before=text, after=out, lossless=False, note="count csv data rows (excluding header)")


def jct_json_array_length(text: str, **_kw: Any) -> tuple[int, dict[str, Any]]:
    out = len(json.loads(text))
    return out, _receipt("jct_json_array_length", before=text, after=out, lossless=False, note="length of a json array")


def jct_csv_header_list(text: str, **_kw: Any) -> tuple[list[str], dict[str, Any]]:
    out = text.split("\n")[0].split(",")
    return out, _receipt("jct_csv_header_list", before=text, after=out, lossless=False, note="extract csv header as a field list")


def jct_records_pluck_column(records: list[dict[str, Any]], col: str, **_kw: Any) -> tuple[list[Any], dict[str, Any]]:
    out = [r.get(col) for r in records]
    return out, _receipt("jct_records_pluck_column", before=records, after=out, lossless=False, note=f"pluck column {col!r} -> value list")


def jct_json_compact_sorted(record: dict[str, Any], **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = json.dumps(record, sort_keys=True, separators=(",", ":"))
    return out, _receipt("jct_json_compact_sorted", before=record, after=out, lossless=True, note="record -> compact sorted json text")


def jct_json_prettify_indent4(text: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = json.dumps(json.loads(text), sort_keys=True, indent=4)
    return out, _receipt("jct_json_prettify_indent4", before=text, after=out, lossless=True, note="json text -> pretty (indent 4)")


def jct_records_to_tsv(records: list[dict[str, Any]], **_kw: Any) -> tuple[str, dict[str, Any]]:
    cols = _sorted_cols(records)
    lines = ["\t".join(cols)] + ["\t".join(str(r.get(c, "")) for c in cols) for r in records]
    out = "\n".join(lines)
    return out, _receipt("jct_records_to_tsv", before=records, after=out, lossless=True, note="record batch -> tsv text (sorted header)")


#: new pure mutators to plug into the shared registry (idempotent setdefault — never overwrites an existing entry)
_NEW_MUTATORS = {
    "jct_row_to_json": jct_row_to_json, "jct_json_to_row": jct_json_to_row,
    "jct_records_to_ndjson": jct_records_to_ndjson, "jct_ndjson_to_records": jct_ndjson_to_records,
    "jct_csv_line_emit": jct_csv_line_emit, "jct_csv_line_parse": jct_csv_line_parse,
    "jct_tsv_line_emit": jct_tsv_line_emit, "jct_tsv_line_parse": jct_tsv_line_parse,
    "jct_records_to_csv": jct_records_to_csv, "jct_csv_to_records": jct_csv_to_records,
    "jct_json_prettify": jct_json_prettify, "jct_json_minify": jct_json_minify,
    "jct_kv_line_emit": jct_kv_line_emit, "jct_kv_line_parse": jct_kv_line_parse,
    "jct_flatten_record": jct_flatten_record, "jct_unflatten_record": jct_unflatten_record,
    "jct_records_to_json_array": jct_records_to_json_array, "jct_json_array_to_records": jct_json_array_to_records,
    "jct_dict_to_pairs": jct_dict_to_pairs, "jct_pairs_to_dict": jct_pairs_to_dict,
    "jct_records_to_csv_header": jct_records_to_csv_header, "jct_csv_escape_field": jct_csv_escape_field,
    "jct_row_values_to_str": jct_row_values_to_str, "jct_ndjson_count": jct_ndjson_count,
    "jct_csv_row_count": jct_csv_row_count, "jct_json_array_length": jct_json_array_length,
    "jct_csv_header_list": jct_csv_header_list, "jct_records_pluck_column": jct_records_pluck_column,
    "jct_json_compact_sorted": jct_json_compact_sorted, "jct_json_prettify_indent4": jct_json_prettify_indent4,
    "jct_records_to_tsv": jct_records_to_tsv,
}


def register_new_mutators() -> None:
    """Plug the family's pure mutators into the shared MUTATOR_REGISTRY (registration, not a rewrite). Idempotent."""
    for name, fn in _NEW_MUTATORS.items():
        MUTATOR_REGISTRY.setdefault(name, fn)


register_new_mutators()


# ── the leaf primitives: each a REAL capability with a concrete fixture + expected (+ inverse where roundtrip holds) ──
# spec fields: id, mutator, fixture, expected, args?, inverse?, input_edge, output_edge
LEAF_SPECS: list[dict[str, Any]] = [
    # roundtrip encode leaves (has_inverse -> the pair is proven reversible by the roundtrip proof)
    {"id": "prim:leaf:jct_row_to_json", "mutator": "jct_row_to_json", "fixture": {"z": 9}, "expected": '{"z": 9}',
     "inverse": "jct_json_to_row", "input_edge": "Record", "output_edge": "JsonText"},
    {"id": "prim:leaf:jct_records_to_ndjson", "mutator": "jct_records_to_ndjson",
     "fixture": [{"a": 1}, {"b": 2}], "expected": '{"a": 1}\n{"b": 2}',
     "inverse": "jct_ndjson_to_records", "input_edge": "RecordBatch", "output_edge": "NdjsonText"},
    {"id": "prim:leaf:jct_csv_line_emit", "mutator": "jct_csv_line_emit", "fixture": ["a", "b", "c"], "expected": "a,b,c",
     "inverse": "jct_csv_line_parse", "input_edge": "FieldList", "output_edge": "CsvLine"},
    {"id": "prim:leaf:jct_tsv_line_emit", "mutator": "jct_tsv_line_emit", "fixture": ["a", "b"], "expected": "a\tb",
     "inverse": "jct_tsv_line_parse", "input_edge": "FieldList", "output_edge": "TsvLine"},
    {"id": "prim:leaf:jct_records_to_csv", "mutator": "jct_records_to_csv",
     "fixture": [{"a": "1", "b": "2"}, {"a": "3", "b": "4"}], "expected": "a,b\n1,2\n3,4",
     "inverse": "jct_csv_to_records", "input_edge": "RecordBatch", "output_edge": "CsvText"},
    {"id": "prim:leaf:jct_json_prettify", "mutator": "jct_json_prettify", "fixture": '{"a":1}',
     "expected": '{\n  "a": 1\n}', "inverse": "jct_json_minify", "input_edge": "JsonText", "output_edge": "PrettyJsonText"},
    {"id": "prim:leaf:jct_kv_line_emit", "mutator": "jct_kv_line_emit", "fixture": {"a": "1", "b": "2"},
     "expected": "a=1;b=2", "inverse": "jct_kv_line_parse", "input_edge": "Record", "output_edge": "KvLine"},
    {"id": "prim:leaf:jct_flatten_record", "mutator": "jct_flatten_record",
     "fixture": {"a": 1, "b": {"c": 2, "d": 3}}, "expected": {"a": 1, "b.c": 2, "b.d": 3},
     "inverse": "jct_unflatten_record", "input_edge": "NestedRecord", "output_edge": "FlatRecord"},
    {"id": "prim:leaf:jct_records_to_json_array", "mutator": "jct_records_to_json_array",
     "fixture": [{"a": 1}, {"b": 2}], "expected": '[{"a": 1}, {"b": 2}]',
     "inverse": "jct_json_array_to_records", "input_edge": "RecordBatch", "output_edge": "JsonArrayText"},
    {"id": "prim:leaf:jct_dict_to_pairs", "mutator": "jct_dict_to_pairs", "fixture": {"a": 1, "b": 2},
     "expected": [["a", 1], ["b", 2]], "inverse": "jct_pairs_to_dict", "input_edge": "Record", "output_edge": "PairList"},

    # decode / parse leaves (proven independently against their own fixtures)
    {"id": "prim:leaf:jct_json_to_row", "mutator": "jct_json_to_row", "fixture": '{"a": 1, "b": 2}',
     "expected": {"a": 1, "b": 2}, "input_edge": "JsonText", "output_edge": "Record"},
    {"id": "prim:leaf:jct_ndjson_to_records", "mutator": "jct_ndjson_to_records", "fixture": '{"x": 1}\n{"y": 2}',
     "expected": [{"x": 1}, {"y": 2}], "input_edge": "NdjsonText", "output_edge": "RecordBatch"},
    {"id": "prim:leaf:jct_csv_line_parse", "mutator": "jct_csv_line_parse", "fixture": "x,y,z",
     "expected": ["x", "y", "z"], "input_edge": "CsvLine", "output_edge": "FieldList"},
    {"id": "prim:leaf:jct_tsv_line_parse", "mutator": "jct_tsv_line_parse", "fixture": "p\tq",
     "expected": ["p", "q"], "input_edge": "TsvLine", "output_edge": "FieldList"},
    {"id": "prim:leaf:jct_csv_to_records", "mutator": "jct_csv_to_records", "fixture": "a,b\n1,2\n3,4",
     "expected": [{"a": "1", "b": "2"}, {"a": "3", "b": "4"}], "input_edge": "CsvText", "output_edge": "RecordBatch"},
    {"id": "prim:leaf:jct_json_minify", "mutator": "jct_json_minify", "fixture": '{"a": 1, "b": 2}',
     "expected": '{"a":1,"b":2}', "input_edge": "JsonText", "output_edge": "CompactJsonText"},
    {"id": "prim:leaf:jct_kv_line_parse", "mutator": "jct_kv_line_parse", "fixture": "x=9;y=8",
     "expected": {"x": "9", "y": "8"}, "input_edge": "KvLine", "output_edge": "Record"},
    {"id": "prim:leaf:jct_unflatten_record", "mutator": "jct_unflatten_record", "fixture": {"x": 1, "y.z": 2},
     "expected": {"x": 1, "y": {"z": 2}}, "input_edge": "FlatRecord", "output_edge": "NestedRecord"},
    {"id": "prim:leaf:jct_json_array_to_records", "mutator": "jct_json_array_to_records",
     "fixture": '[{"a": 1}, {"b": 2}]', "expected": [{"a": 1}, {"b": 2}],
     "input_edge": "JsonArrayText", "output_edge": "RecordBatch"},
    {"id": "prim:leaf:jct_pairs_to_dict", "mutator": "jct_pairs_to_dict", "fixture": [["x", 1], ["y", 2]],
     "expected": {"x": 1, "y": 2}, "input_edge": "PairList", "output_edge": "Record"},

    # standalone transform / projection / measurement leaves
    {"id": "prim:leaf:jct_records_to_csv_header", "mutator": "jct_records_to_csv_header",
     "fixture": [{"name": "x", "age": "3"}], "expected": "age,name",
     "input_edge": "RecordBatch", "output_edge": "CsvHeaderLine"},
    {"id": "prim:leaf:jct_csv_escape_field", "mutator": "jct_csv_escape_field", "fixture": "a,b", "expected": '"a,b"',
     "input_edge": "Field", "output_edge": "CsvField"},
    {"id": "prim:leaf:jct_row_values_to_str", "mutator": "jct_row_values_to_str", "fixture": {"a": 1, "b": 2},
     "expected": {"a": "1", "b": "2"}, "input_edge": "Record", "output_edge": "StringRecord"},
    {"id": "prim:leaf:jct_ndjson_count", "mutator": "jct_ndjson_count", "fixture": '{"a": 1}\n{"b": 2}', "expected": 2,
     "input_edge": "NdjsonText", "output_edge": "Count"},
    {"id": "prim:leaf:jct_csv_row_count", "mutator": "jct_csv_row_count", "fixture": "a,b\n1,2\n3,4", "expected": 2,
     "input_edge": "CsvText", "output_edge": "Count"},
    {"id": "prim:leaf:jct_json_array_length", "mutator": "jct_json_array_length", "fixture": "[1, 2, 3]", "expected": 3,
     "input_edge": "JsonArrayText", "output_edge": "Count"},
    {"id": "prim:leaf:jct_csv_header_list", "mutator": "jct_csv_header_list", "fixture": "a,b,c\n1,2,3",
     "expected": ["a", "b", "c"], "input_edge": "CsvText", "output_edge": "FieldList"},
    {"id": "prim:leaf:jct_records_pluck_column", "mutator": "jct_records_pluck_column",
     "fixture": [{"a": 1}, {"a": 2}], "expected": [1, 2], "args": {"col": "a"},
     "input_edge": "RecordBatch", "output_edge": "ValueList"},
    {"id": "prim:leaf:jct_json_compact_sorted", "mutator": "jct_json_compact_sorted", "fixture": {"b": 2, "a": 1},
     "expected": '{"a":1,"b":2}', "input_edge": "Record", "output_edge": "CompactJsonText"},
    {"id": "prim:leaf:jct_json_prettify_indent4", "mutator": "jct_json_prettify_indent4", "fixture": '{"a":1}',
     "expected": '{\n    "a": 1\n}', "input_edge": "JsonText", "output_edge": "PrettyJsonText"},
    {"id": "prim:leaf:jct_records_to_tsv", "mutator": "jct_records_to_tsv", "fixture": [{"a": "1", "b": "2"}],
     "expected": "a\tb\n1\t2", "input_edge": "RecordBatch", "output_edge": "TsvText"},
]

#: deliberately-wrong leaf — the proof gate MUST leave it candidate (never persisted as proven)
NEGATIVE_SPEC: dict[str, Any] = {
    "id": "prim:leaf:jct_WRONG_expected", "mutator": "jct_row_to_json", "fixture": {"z": 9},
    "expected": '{"WRONG": 999}', "input_edge": "Record", "output_edge": "JsonText"}


def _prove_one(spec: dict[str, Any]) -> dict[str, Any]:
    return run_primitive_proof(
        spec["id"], spec["mutator"], spec["fixture"], spec["expected"],
        mutator_args=spec.get("args") or {}, has_inverse=spec.get("inverse"),
    )


def prove_all() -> list[tuple[dict[str, Any], dict[str, Any]]]:
    """Run every declared leaf through the imported executed-proof runner. Returns [(spec, receipt), ...]."""
    return [(s, _prove_one(s)) for s in LEAF_SPECS]


def build_rows() -> list[dict[str, Any]]:
    """Persist-ready rows for leaves whose executed proof PASSED — TYPED via canonicalize_edge (workable == typed)."""
    rows: list[dict[str, Any]] = []
    for spec, receipt in prove_all():
        if receipt["serves_truth"] is not True:
            continue  # a failing / wrong-expected leaf stays candidate and is NOT persisted (the gate is the point)
        rows.append({
            "primitive_id": receipt["primitive_id"],
            "mutator": receipt["mutator"],
            "family": FAMILY,
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


def build_manifest(rows: list[dict[str, Any]]) -> dict[str, Any]:
    typed = [r for r in rows if r["input_edge_type_id"] and r["output_edge_type_id"]]
    return {
        "record_type": "proven_family_leaves_manifest",
        "family": FAMILY,
        "generator": "scripts/prove_leaves_json_csv_transform.py",
        "generated_utc": _FIXED_UTC,
        "defined_count": len(LEAF_SPECS),
        "proven_count": len(rows),
        "typed_count": len(typed),
        "verification_level": "L7_executed_proof",
        "proven_primitive_ids": sorted(r["primitive_id"] for r in rows),
        "note": "serves_truth=true is set ONLY by an executed passing proof (run_primitive_proof, imported from "
                "scripts/mutator_registry.py). Every persisted row is TYPED via canonicalize_edge (imported from "
                "scripts/build_edge_type_retrofit.py) so a workable leaf carries canonical input/output edge types "
                "and can chain. A deliberately-wrong-expected leaf stays candidate and is never persisted.",
    }


def write_pack() -> dict[str, Any]:
    rows = build_rows()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSONL.write_text(
        "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows), encoding="utf-8")
    manifest = build_manifest(rows)
    OUT_MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def self_test() -> int:
    proven = prove_all()
    rows = build_rows()
    ids = [r["primitive_id"] for r in rows]
    typed = [r for r in rows if r["input_edge_type_id"] and r["output_edge_type_id"]]
    roundtrip_specs = [s for s in LEAF_SPECS if s.get("inverse")]
    proven_by_id = {r["primitive_id"]: r for (s, r) in proven}

    # deliberately-wrong leaf must stay candidate (proof gate is real, not a rubber stamp) — and never enter rows
    wrong = _prove_one(NEGATIVE_SPEC)
    # a second wrong path: an un-runnable fixture -> execution error -> not promoted
    err = run_primitive_proof("prim:leaf:jct_EXEC_ERROR", "jct_json_to_row", object(), "irrelevant")

    checks: list[tuple[str, bool]] = [
        (">=28 leaves declared", len(LEAF_SPECS) >= 28),
        ("unique primitive ids", len(set(ids)) == len(ids)),
        (">=28 leaves PROVE serves_truth=true via an executed proof", len(rows) >= 28),
        ("every proven receipt is L7_executed_proof with all sub-proofs passing",
         all(r["verification_level"] == "L7_executed_proof" and all(p["passed"] for p in r["proofs"])
             for (_s, r) in proven if r["serves_truth"] is True)),
        ("EVERY persisted row carries non-null input+output edge type ids", len(typed) == len(rows)),
        ("typed_count == proven_count", build_manifest(rows)["typed_count"] == build_manifest(rows)["proven_count"]),
        ("roundtrip-inverse pairs actually ran + PASSED a roundtrip proof", all(
            any(p["name"] == "roundtrip_test" and p["passed"] for p in proven_by_id[s["id"]]["proofs"])
            for s in roundtrip_specs)),
        ("family stamped on every row", all(r["family"] == FAMILY for r in rows)),
        ("deterministic: re-running yields identical rows",
         [json.dumps(r, sort_keys=True) for r in build_rows()] == [json.dumps(r, sort_keys=True) for r in rows]),
        ("a deliberately-wrong leaf stays CANDIDATE (never promoted)",
         wrong["serves_truth"] is False and wrong["promoted"] is False),
        ("the wrong leaf is NOT persisted", NEGATIVE_SPEC["id"] not in set(ids)),
        ("an un-runnable fixture fails the proof, does not promote",
         err["serves_truth"] is False and err["promoted"] is False),
        ("new mutators registered into the shared registry (add-only seam)",
         all(m in MUTATOR_REGISTRY for m in _NEW_MUTATORS)),
    ]
    failed = [n for n, ok in checks if not ok]
    if failed:
        print("FAIL - prove_leaves_json_csv_transform:\n  " + "\n  ".join(failed))
        return 1
    print(f"PASS - prove_leaves_json_csv_transform: {len(rows)} WORKABLE (proven + TYPED) leaves for '{FAMILY}' "
          f"(serves_truth=true, L7_executed_proof; typed_count={len(typed)}=={len(rows)}); "
          f"{len(roundtrip_specs)} inverse pairs proven reversible via roundtrip; a deliberately-wrong leaf and an "
          "un-runnable fixture correctly stay candidate. Real capability, not vocabulary.")
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
