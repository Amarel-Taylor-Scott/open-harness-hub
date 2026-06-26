#!/usr/bin/env python3
"""src/baltor/native/native_projection_builder — build a SAME-SHAPE native output per output_mode.

This is where "Baltor returns your format, not ours" happens. Given the frozen NativeShapeContract + an optional
set of VERIFIED value changes, it produces output in the customer's own shape:
  JSON  — same keys + nesting (changes addressed by JSON-pointer); passthrough is byte-identical.
  CSV   — same columns/order/delimiter/newline; changes addressed by (row, column).
  Markdown — default: original document, byte-unchanged (the governance rides in the sidecar). Optional
             annotated mode adds an HTML-comment block / frontmatter WITHOUT removing any original content.

LOSSLESS DISTILLATION: passthrough returns the exact original bytes. ``schema_preserving`` may change a value
ONLY when a verified change is supplied, and EVERY applied change emits a NativeDiff entry (path/old/new/
decision/receipt_id). The shape (keys/columns/structure) is never altered — a change without a receipt is
refused, never silently applied. The original bytes + hash are always retained on the contract for rollback.

Deterministic + offline + stdlib only: ids content-addressed, no RNG, no network.
"""
from __future__ import annotations

import csv as _csv
import hashlib
import io
import json
from dataclasses import dataclass, field

from src.baltor.native.native_format_preserver import (FORMAT_CSV, FORMAT_JSON, FORMAT_MARKDOWN,
                                                       NativeShapeContract)


def _hid(prefix: str, body: dict) -> str:
    return prefix + "-" + hashlib.sha256(json.dumps(body, sort_keys=True, default=str).encode()).hexdigest()[:16]


def _sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


@dataclass
class NativeDiff:
    """The ledger of every value change applied to a same-shape projection. Empty == no change made."""
    source_hash: str
    output_mode: str
    changed_fields: list = field(default_factory=list)   # {path, old, new, decision, receipt_id}
    diff_id: str = ""
    schema_version: str = "NativeDiff"

    def to_dict(self) -> dict:
        return {"schema_version": self.schema_version, "diff_id": self.diff_id, "source_hash": self.source_hash,
                "output_mode": self.output_mode, "changed_fields": list(self.changed_fields)}


@dataclass
class NativeProjection:
    """The same-shape output bytes + the diff that produced them. ``output_bytes`` fits the customer's system."""
    format: str
    output_mode: str
    output_bytes: bytes
    output_hash: str
    diff: NativeDiff
    byte_identical_to_source: bool
    annotations_added: int = 0
    schema_version: str = "NativeProjection"

    def output_text(self) -> str:
        return self.output_bytes.decode("utf-8", "replace")

    def to_dict(self) -> dict:
        return {"schema_version": self.schema_version, "format": self.format, "output_mode": self.output_mode,
                "output_hash": self.output_hash, "byte_identical_to_source": self.byte_identical_to_source,
                "annotations_added": self.annotations_added, "output_byte_size": len(self.output_bytes),
                "diff": self.diff.to_dict()}


def _pointer_get(obj, pointer: str):
    cur = obj
    for tok in [t for t in pointer.split("/") if t != ""]:
        tok = tok.replace("~1", "/").replace("~0", "~")
        cur = cur[int(tok)] if isinstance(cur, list) else cur[tok]
    return cur


def _pointer_set(obj, pointer: str, value) -> None:
    toks = [t for t in pointer.split("/") if t != ""]
    cur = obj
    for tok in toks[:-1]:
        tok = tok.replace("~1", "/").replace("~0", "~")
        cur = cur[int(tok)] if isinstance(cur, list) else cur[tok]
    last = toks[-1].replace("~1", "/").replace("~0", "~")
    if isinstance(cur, list):
        cur[int(last)] = value
    else:
        cur[last] = value


class NativeProjectionBuilder:
    """Render a same-shape native projection for a given output_mode. Applies only verified changes; emits diffs."""

    def build(self, contract: NativeShapeContract, *, output_mode: str, passthrough: bool,
              verified_changes=None, annotate: bool = False, sidecar_ref: str = "", now: str = "") -> NativeProjection:
        """verified_changes: list of {path, new_value, decision, receipt_id}. A change WITHOUT a receipt_id is
        refused (raises) — schema_preserving never changes a value that is not verified."""
        verified_changes = list(verified_changes or [])
        for ch in verified_changes:
            if not ch.get("receipt_id"):
                raise ValueError(f"refused unverified change at {ch.get('path')!r}: every value change in a "
                                 "schema-preserving projection requires a verification receipt (lossless law)")
        if contract.format == FORMAT_JSON:
            return self._json(contract, output_mode, passthrough, verified_changes, now)
        if contract.format == FORMAT_CSV:
            return self._csv(contract, output_mode, passthrough, verified_changes, now)
        return self._markdown(contract, output_mode, passthrough, annotate, sidecar_ref, verified_changes, now)

    # ── JSON: preserve keys + nesting; changes addressed by JSON-pointer ───────────────────────────────
    def _json(self, contract, output_mode, passthrough, changes, now) -> NativeProjection:
        if passthrough or not changes:
            out = contract.original_bytes
            return self._proj(contract, output_mode, out, NativeDiff(contract.source_hash, output_mode), now,
                              byte_identical=(out == contract.original_bytes))
        # rebuild a fresh parsed copy so we NEVER mutate the contract's reference
        doc = json.loads(contract.original_bytes.decode("utf-8"))
        changed: list[dict] = []
        for ch in changes:
            ptr = ch["path"]
            old = _pointer_get(doc, ptr)
            new = ch["new_value"]
            if old != new:
                _pointer_set(doc, ptr, new)
                changed.append({"path": ptr, "old": old, "new": new,
                                "decision": ch.get("decision", "verified_update"), "receipt_id": ch["receipt_id"]})
        # re-serialize preserving key order (json.dumps keeps dict insertion order == original key order)
        out = json.dumps(doc, ensure_ascii=False).encode("utf-8")
        diff = NativeDiff(contract.source_hash, output_mode, changed)
        diff.diff_id = _hid("ndiff", {"sh": contract.source_hash, "ch": changed})
        return self._proj(contract, output_mode, out, diff, now, byte_identical=(out == contract.original_bytes))

    # ── CSV: preserve columns/order/delimiter/newline; changes addressed by (row, column) ──────────────
    def _csv(self, contract, output_mode, passthrough, changes, now) -> NativeProjection:
        if passthrough or not changes:
            out = contract.original_bytes
            return self._proj(contract, output_mode, out, NativeDiff(contract.source_hash, output_mode), now,
                              byte_identical=True)
        text = contract.original_bytes.decode("utf-8")
        rows = list(_csv.reader(io.StringIO(text), delimiter=contract.delimiter))
        header = rows[0] if rows else []
        col_idx = {c: i for i, c in enumerate(header)}
        changed: list[dict] = []
        for ch in changes:
            # path form: "row.<n>.col.<name>" (n is the DATA row index, 0-based, excluding header)
            ptr = ch["path"]
            parts = ptr.split(".")
            rn = int(parts[1]); cn = parts[3]
            ridx = rn + (1 if contract.has_header else 0)
            cidx = col_idx[cn]
            old = rows[ridx][cidx]
            new = str(ch["new_value"])
            if old != new:
                rows[ridx][cidx] = new
                changed.append({"path": ptr, "old": old, "new": new,
                                "decision": ch.get("decision", "verified_update"), "receipt_id": ch["receipt_id"]})
        buf = io.StringIO()
        # preserve the exact delimiter + newline; QUOTE_MINIMAL matches the common case
        writer = _csv.writer(buf, delimiter=contract.delimiter, lineterminator=contract.newline,
                             quoting=_csv.QUOTE_MINIMAL)
        writer.writerows(rows)
        out = buf.getvalue().encode("utf-8")
        diff = NativeDiff(contract.source_hash, output_mode, changed)
        diff.diff_id = _hid("ndiff", {"sh": contract.source_hash, "ch": changed})
        return self._proj(contract, output_mode, out, diff, now, byte_identical=(out == contract.original_bytes))

    # ── Markdown: default original unchanged; optional annotated mode adds without removing ────────────
    def _markdown(self, contract, output_mode, passthrough, annotate, sidecar_ref, changes, now) -> NativeProjection:
        original = contract.original_bytes
        diff = NativeDiff(contract.source_hash, output_mode)
        if not annotate:
            # strict preservation: the note is NEVER edited; governance rides entirely in the sidecar.
            return self._proj(contract, output_mode, original, diff, now, byte_identical=True, annotations=0)
        # annotated mode: append a trailing HTML-comment block — original content is fully retained ABOVE it.
        note_lines = ["", "<!-- baltor:native-annotations",
                      f"baltor_source_hash: {contract.source_hash}"]
        if sidecar_ref:
            note_lines.append(f"baltor_sidecar: {sidecar_ref}")
        note_lines += [f"baltor_warning: {w}" for w in (c.get("note", "") for c in changes) if w]
        note_lines.append("-->")
        annotation = (contract.newline.join(note_lines)).encode("utf-8")
        out = original + contract.newline.encode("utf-8") + annotation
        # the original prefix is byte-preserved; only an appended block was added
        return self._proj(contract, output_mode, out, diff, now, byte_identical=False, annotations=1)

    def _proj(self, contract, output_mode, out: bytes, diff: NativeDiff, now, *, byte_identical: bool,
              annotations: int = 0) -> NativeProjection:
        if not diff.diff_id:
            diff.diff_id = _hid("ndiff", {"sh": contract.source_hash, "ch": diff.changed_fields})
        return NativeProjection(format=contract.format, output_mode=output_mode, output_bytes=out,
                                output_hash=_sha256(out), diff=diff, byte_identical_to_source=byte_identical,
                                annotations_added=annotations)
