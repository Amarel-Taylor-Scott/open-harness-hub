#!/usr/bin/env python3
"""src/baltor/native/native_format_preserver — detect the native SHAPE of a customer source and freeze it.

The first step of native preservation: take raw input bytes, detect its shape (json | csv | markdown), and
produce a ``NativeShapeContract`` that records exactly how to reproduce the same format on the way out —
keys + nesting for JSON, columns + order + delimiter + newline for CSV, the original document for Markdown.

LOSSLESS DISTILLATION: this module NEVER mutates the original. It keeps the original bytes + their sha256 so
every downstream projection can be proven byte-identical (passthrough) or reproduced. The contract is the
rollback target — a projection can always rehydrate to ``original_bytes``.

Deterministic + offline + stdlib only: ids are content-addressed (sha256), no RNG, no network.
"""
from __future__ import annotations

import csv as _csv
import hashlib
import io
import json
from dataclasses import dataclass, field

#: the native shapes Baltor can preserve same-shape today (Lane B owns json/csv/markdown).
FORMAT_JSON = "json"
FORMAT_CSV = "csv"
FORMAT_MARKDOWN = "markdown"
SUPPORTED_FORMATS = (FORMAT_JSON, FORMAT_CSV, FORMAT_MARKDOWN)


def _sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _as_bytes(source) -> bytes:
    if isinstance(source, bytes):
        return source
    if isinstance(source, str):
        return source.encode("utf-8")
    # a parsed object (dict/list) — canonicalize deterministically so the same object always hashes the same
    return json.dumps(source, sort_keys=True, ensure_ascii=False).encode("utf-8")


def _detect_newline(text: str) -> str:
    if "\r\n" in text:
        return "\r\n"
    if "\r" in text:
        return "\r"
    return "\n"


def _flatten_pointers(obj, prefix: str = "") -> list[str]:
    """Every leaf JSON-pointer path, in document order. Lists index by position. The set of pointers IS the
    JSON schema-shape we must preserve."""
    out: list[str] = []
    if isinstance(obj, dict):
        for k in obj:
            out += _flatten_pointers(obj[k], f"{prefix}/{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            out += _flatten_pointers(v, f"{prefix}/{i}")
    else:
        out.append(prefix or "")
    return out


@dataclass
class NativeShapeContract:
    """How to reproduce the customer's native format on the way out. The frozen, never-mutated source-of-shape."""
    format: str                              # one of SUPPORTED_FORMATS
    schema_hash: str                         # hash of the SHAPE (keys/columns/structure), not the values
    original_bytes: bytes                    # the exact input bytes — NEVER overwritten; the rollback target
    source_hash: str                         # sha256 of original_bytes
    encoding: str = "utf-8"
    mime_type: str = ""
    # JSON
    field_order: list = field(default_factory=list)   # leaf JSON-pointers in document order
    parsed: object = None                              # the parsed JSON object (read-only reference)
    # CSV
    columns: list = field(default_factory=list)        # header columns in order
    delimiter: str = ","
    newline: str = "\n"
    quoting: str = "minimal"
    has_header: bool = True
    row_count: int = 0
    schema_version: str = "NativeShapeContract"

    def shape_signature(self) -> dict:
        """The shape-only fingerprint (no values) used to compare input-schema == output-schema."""
        if self.format == FORMAT_JSON:
            return {"format": self.format, "field_order": list(self.field_order)}
        if self.format == FORMAT_CSV:
            return {"format": self.format, "columns": list(self.columns), "delimiter": self.delimiter,
                    "newline": self.newline, "has_header": self.has_header}
        return {"format": self.format}

    def to_dict(self) -> dict:
        return {"schema_version": self.schema_version, "format": self.format, "schema_hash": self.schema_hash,
                "source_hash": self.source_hash, "encoding": self.encoding, "mime_type": self.mime_type,
                "field_order": list(self.field_order), "columns": list(self.columns), "delimiter": self.delimiter,
                "newline": self.newline, "quoting": self.quoting, "has_header": self.has_header,
                "row_count": self.row_count, "original_byte_size": len(self.original_bytes)}


class NativeFormatPreserver:
    """Detect a source's native shape and freeze it into a NativeShapeContract. Never mutates the original."""

    def detect_format(self, source, *, hint: str = "") -> str:
        if hint in SUPPORTED_FORMATS:
            return hint
        if isinstance(source, (dict, list)):
            return FORMAT_JSON
        text = source.decode("utf-8", "replace") if isinstance(source, bytes) else str(source)
        stripped = text.lstrip()
        if stripped[:1] in ("{", "["):
            try:
                json.loads(text)
                return FORMAT_JSON
            except (json.JSONDecodeError, ValueError):
                pass
        # CSV heuristic: a header line with a delimiter and >1 consistent column across lines, no markdown markers
        if "," in text or "\t" in text:
            if not any(text.lstrip().startswith(m) for m in ("#", "-", "*", ">")):
                delim = "\t" if (text.count("\t") > text.count(",")) else ","
                lines = [ln for ln in text.splitlines() if ln.strip()]
                if len(lines) >= 1 and delim in lines[0]:
                    cols0 = len(lines[0].split(delim))
                    if cols0 >= 2 and all(delim in ln for ln in lines[1:2]):
                        return FORMAT_CSV
        return FORMAT_MARKDOWN

    def preserve(self, source, *, hint: str = "", mime_type: str = "") -> NativeShapeContract:
        """Freeze the source shape. ``original_bytes`` is the exact input; never overwritten downstream."""
        fmt = self.detect_format(source, hint=hint)
        original_bytes = _as_bytes(source)
        source_hash = _sha256(original_bytes)
        if fmt == FORMAT_JSON:
            return self._json_contract(source, original_bytes, source_hash, mime_type)
        if fmt == FORMAT_CSV:
            return self._csv_contract(original_bytes, source_hash, mime_type)
        return self._markdown_contract(original_bytes, source_hash, mime_type)

    def _json_contract(self, source, original_bytes: bytes, source_hash: str, mime_type: str) -> NativeShapeContract:
        parsed = source if isinstance(source, (dict, list)) else json.loads(
            original_bytes.decode("utf-8"))
        field_order = _flatten_pointers(parsed)
        schema_hash = _sha256(json.dumps(field_order, sort_keys=False).encode())[:16]
        return NativeShapeContract(format=FORMAT_JSON, schema_hash=schema_hash, original_bytes=original_bytes,
                                   source_hash=source_hash, mime_type=mime_type or "application/json",
                                   field_order=field_order, parsed=parsed)

    def _csv_contract(self, original_bytes: bytes, source_hash: str, mime_type: str) -> NativeShapeContract:
        text = original_bytes.decode("utf-8")
        newline = _detect_newline(text)
        delimiter = "\t" if (text.count("\t") > text.count(",")) else ","
        reader = _csv.reader(io.StringIO(text), delimiter=delimiter)
        rows = list(reader)
        columns = list(rows[0]) if rows else []
        return NativeShapeContract(format=FORMAT_CSV, schema_hash=_sha256(json.dumps(columns).encode())[:16],
                                   original_bytes=original_bytes, source_hash=source_hash,
                                   mime_type=mime_type or "text/csv", columns=columns, delimiter=delimiter,
                                   newline=newline, has_header=bool(columns), row_count=max(0, len(rows) - 1))

    def _markdown_contract(self, original_bytes: bytes, source_hash: str, mime_type: str) -> NativeShapeContract:
        text = original_bytes.decode("utf-8", "replace")
        return NativeShapeContract(format=FORMAT_MARKDOWN, schema_hash=source_hash[:16],
                                   original_bytes=original_bytes, source_hash=source_hash,
                                   mime_type=mime_type or "text/markdown", newline=_detect_newline(text))
