#!/usr/bin/env python3
"""scripts.ingest.decompose_to_context_objects — bridge the decomposition tree → canonical schema.

`document_decompose` proves the recursive object tree; `schemas/context-object.schema.json` is the
canonical, standards-aligned context-object profile the rest of Baltor consumes. This module wires
them together (no new schema — reuse the existing one): it maps each decomposed `Node` into a
`baltor.context-object` record and **validates every record against the real schema** with the
same `Draft202012Validator` `scripts/validate.py` uses.

Why this matters: it proves a decomposed paragraph / table-cell / figure is emittable as a
governed context object — carrying its `ctx://…#page=…` source handle, a Web-Annotation-style
FragmentSelector for its bbox, `provenance.wasDerivedFrom` = its parent (the tree relationship,
kept as a first-class link rather than a nested blob), its content hash, and a policy stamp
(derived context; low-confidence nodes are not promotion-eligible). The recursion lives in the
handle + the parent link, matching the storage rule (relationships are first-class records).

Deterministic + offline (the self-test decomposes a fixture and validates against the real schema;
`created_at` is passed in, not read from a clock). Stdlib + jsonschema (already a repo dep).

CLI:
    python3 scripts/ingest/decompose_to_context_objects.py --self-test
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    import os
    import sys

    _REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if _REPO_ROOT not in sys.path:
        sys.path.insert(0, _REPO_ROOT)

from scripts.ingest.document_decompose import (
    KIND_DOCUMENT, KIND_PAGE, KIND_BLOCK, KIND_TABLE, LOW_CONFIDENCE_FLOOR,
    CannedParser, DocumentTree, Node, decompose,
)

_REPO = Path(__file__).resolve().parents[2]
CONTEXT_OBJECT_SCHEMA = _REPO / "schemas" / "context-object.schema.json"

#: Decomposition node kind → context-object schema `object_type` enum value (single source).
#: page/block are structural sections; document is the root; tables are tables; every text/figure
#: leaf is a source_excerpt (an addressable excerpt of the source).
_OBJECT_TYPE_BY_KIND: dict[str, str] = {
    KIND_DOCUMENT: "document",
    KIND_PAGE: "document_section",
    KIND_BLOCK: "document_section",
    KIND_TABLE: "table",
}
_DEFAULT_OBJECT_TYPE = "source_excerpt"  # paragraph/heading/table_cell/figure/diagram/equation/ocr_span


def node_to_context_object(node: Node, tree: DocumentTree, *, created_at: str) -> dict[str, Any]:
    """Render one decomposed Node as a `baltor.context-object` record (schema-valid)."""
    obj: dict[str, Any] = {
        "kind": "baltor.context-object",
        "context_object_id": node.object_id,
        "object_type": _OBJECT_TYPE_BY_KIND.get(node.kind, _DEFAULT_OBJECT_TYPE),
        "source_handles": [node.source_handle],
        "created_at": created_at,
        "policy": {
            "derived_context": True,           # decomposed objects are derived from the raw doc
            "raw_source_dump_allowed": False,  # never serve the raw blob; serve the addressable node
            # a low-confidence node (bad OCR / ambiguous table) is not promotion-eligible until reviewed
            "promotion_allowed": float(node.lineage.get("confidence", 1.0)) >= LOW_CONFIDENCE_FLOOR,
            "prompt_injection_checked": False,
        },
        "provenance": {
            "content_hash": node.content_hash,
            "wasGeneratedBy": node.lineage.get("parser"),
            # the tree relationship, kept as a first-class link (parent's handle), not a nested blob
            "wasDerivedFrom": ([tree.nodes[node.parent_ref].source_handle] if node.parent_ref else []),
        },
    }
    if node.text is not None:
        obj["body"] = {"text": node.text}
    # A bbox becomes a Web-Annotation-style FragmentSelector so the visual region is addressable.
    if node.bbox is not None:
        obj["evidence"] = [{
            "source_handle": node.source_handle,
            "selector_type": "FragmentSelector",
            "selector": {"type": "pdf-bbox", "page": node.page_no, "bbox": node.bbox},
            "supports_claim": False,
        }]
    return obj


def tree_to_context_objects(tree: DocumentTree, *, created_at: str) -> list[dict[str, Any]]:
    """Map every node in a decomposition tree to a schema-valid context-object (reading order)."""
    return [node_to_context_object(tree.nodes[oid], tree, created_at=created_at) for oid in tree.order]


def _validator():
    from jsonschema import Draft202012Validator
    schema = json.loads(CONTEXT_OBJECT_SCHEMA.read_text(encoding="utf-8"))
    return Draft202012Validator(schema)


def _self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    check("canonical schema exists", CONTEXT_OBJECT_SCHEMA.exists(), str(CONTEXT_OBJECT_SCHEMA))

    parsed = {"pages": [
        {"page_no": 1, "blocks": [
            {"kind": "heading", "ordinal": 0, "text": "Screening Policy", "confidence": 0.99},
            {"kind": "paragraph", "ordinal": 1, "text": "Screen all counterparties.",
             "bbox": {"x": 112.4, "y": 204.8, "width": 392.1, "height": 44.6, "unit": "pt"}, "confidence": 0.97},
        ]},
        {"page_no": 2, "blocks": [
            {"kind": "table", "ordinal": 0, "confidence": 0.88, "cells": [
                {"row": 1, "col": 1, "text": "Program"}, {"row": 1, "col": 2, "text": "Threshold"}]},
            {"kind": "ocr_span", "ordinal": 1, "text": "scanned clause", "confidence": 0.41},  # low-conf
        ]},
    ]}
    tree = decompose("acme", "policy", CannedParser(parsed, version="1").parse(None), parser="canned", parser_version="1")
    objs = tree_to_context_objects(tree, created_at="2026-06-04T00:00:00Z")

    # ── EVERY emitted object validates against the REAL canonical schema ──
    v = _validator()
    errors: list[str] = []
    for o in objs:
        for e in v.iter_errors(o):
            errors.append(f"{o.get('context_object_id')}: {e.message}")
    check("every decomposed node validates against context-object.schema.json",
          not errors, "; ".join(errors[:3]))
    check("object count == node count", len(objs) == len(tree.nodes), f"{len(objs)} vs {len(tree.nodes)}")

    by_handle = {o["source_handles"][0]: o for o in objs}
    para = by_handle.get("ctx://acme/doc/policy#page=0001&block=02")
    check("paragraph → source_excerpt with body text", para and para["object_type"] == "source_excerpt"
          and para["body"]["text"] == "Screen all counterparties.", str(para and para.get("object_type")))
    check("paragraph carries FragmentSelector bbox evidence",
          para and para["evidence"][0]["selector"]["bbox"]["unit"] == "pt")
    check("paragraph provenance.wasDerivedFrom = its page",
          para and para["provenance"]["wasDerivedFrom"] == ["ctx://acme/doc/policy#page=0001"])
    table = by_handle.get("ctx://acme/doc/policy#page=0002&table=01")
    check("table node → object_type 'table'", table and table["object_type"] == "table")
    ocr = by_handle.get("ctx://acme/doc/policy#page=0002&block=01")
    check("low-confidence OCR span is NOT promotion-eligible",
          ocr and ocr["policy"]["promotion_allowed"] is False, str(ocr and ocr["policy"]))
    doc = by_handle.get("ctx://acme/doc/policy")
    check("root → object_type 'document', no parent", doc and doc["object_type"] == "document"
          and doc["provenance"]["wasDerivedFrom"] == [])

    # ── determinism ──
    objs2 = tree_to_context_objects(tree, created_at="2026-06-04T00:00:00Z")
    check("bridge is deterministic", objs2 == objs)

    print(f"\n{'all decompose_to_context_objects self-tests passed.' if not failures else f'{len(failures)} FAILURES: {failures}'}")
    return 0 if not failures else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Bridge document decomposition → canonical context-object records (schema-validated).")
    p.add_argument("--self-test", action="store_true", help="offline, deterministic; validates against the real schema")
    p.add_argument("--demo", action="store_true", help="print the context-objects for the bundled fixture")
    args = p.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.demo:
        parsed = {"pages": [{"page_no": 1, "blocks": [{"kind": "paragraph", "ordinal": 0, "text": "Example.", "confidence": 0.95}]}]}
        tree = decompose("acme", "demo", CannedParser(parsed).parse(None))
        print(json.dumps(tree_to_context_objects(tree, created_at="2026-06-04T00:00:00Z"), indent=2))
        return 0
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
