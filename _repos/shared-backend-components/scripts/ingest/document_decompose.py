#!/usr/bin/env python3
"""scripts.ingest.document_decompose — the Bronze decomposition contract (proven).

The six visible stages hide a sub-pipeline inside *Source Systems*: a raw artifact (a
1,000-page PDF, a DOCX, a deck, a scan) must become a **tree of addressable, typed context
objects** BEFORE reconciliation — not one giant text blob. This module implements and proves
the part **Baltor owns**: the recursive object model, coordinate-precise source handles,
per-node lineage + content hash, claim-attaches-to-leaf, source-handle expansion, and the
re-decompose→diff that drives document-specific context rot.

Product boundary (kept clean):
  * **Baltor owns** the ``ContextObject`` tree + ``ctx://`` fragment handles + lineage +
    the normalization of any parser's output into this tree (implemented + self-tested here).
  * **Swappable infra (the SEAM):** the actual byte-level parse/layout/OCR is a
    ``ParserProvider`` (Docling primary / LiteParse / Unstructured — see
    ``research/backend-tool-verification.md``). Here a ``CannedParser`` stands in so the
    contract is proven offline + deterministically; a real adapter slots behind the same
    interface in a dep/network-permitted environment. NOTHING here touches the network, a
    clock, or RNG — re-decomposing identical parser output is byte-identical.

Spec: ``docs/backend/raw-document-processing.md``. Stdlib only.

CLI / self-test (proves the whole contract, incl. a 1,000-page fan-out, offline):
    python3 _repos/shared-backend-components/scripts/ingest/document_decompose.py --self-test
"""
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Protocol, runtime_checkable

# ── Vocabulary (single source of truth; No-Magic-Values) ─────────────────────

#: Open-vocab node kinds. The closed set here is the seed; extend per source.
KIND_DOCUMENT = "document"
KIND_PAGE = "page"
KIND_BLOCK = "block"            # a layout region
KIND_PARAGRAPH = "paragraph"
KIND_HEADING = "heading"
KIND_TABLE = "table"
KIND_TABLE_CELL = "table_cell"
KIND_FIGURE = "figure"
KIND_DIAGRAM = "diagram"
KIND_EQUATION = "equation"
KIND_OCR_SPAN = "ocr_span"

#: Text-bearing leaf kinds (carry ``text``); others carry an ``artifact_uri`` pointer.
TEXT_KINDS = frozenset({KIND_PARAGRAPH, KIND_HEADING, KIND_TABLE_CELL, KIND_EQUATION, KIND_OCR_SPAN})
ARTIFACT_KINDS = frozenset({KIND_FIGURE, KIND_DIAGRAM})

#: Document-specific context-rot signal types (a superset of the generic ones).
ROT_SOURCE_HASH_CHANGED = "source_hash_changed"
ROT_PAGE_COUNT_CHANGED = "page_count_changed"
ROT_NODE_CHANGED = "node_changed"
ROT_NODE_ADDED = "node_added"
ROT_NODE_REMOVED = "node_removed"
ROT_HANDLE_UNRESOLVABLE = "source_handle_unresolvable"
ROT_OCR_CONFIDENCE_LOW = "ocr_confidence_low"

#: Below this parser/OCR confidence, a node is fragile → route to steward review.
LOW_CONFIDENCE_FLOOR = 0.60


# ── The ParserProvider SEAM ───────────────────────────────────────────────────


@runtime_checkable
class ParserProvider(Protocol):
    """The swappable byte-parse. A real adapter (Docling/LiteParse/Unstructured) returns the
    same shape; ``CannedParser`` provides it offline for the proof.

    ``parse(raw)`` returns ``{"pages": [PAGE, ...]}`` where each PAGE is
    ``{"page_no": int, "blocks": [BLOCK, ...]}`` and each BLOCK is
    ``{"kind": str, "ordinal": int, "bbox": {...}|None, "confidence": float,
       "text": str | None, "artifact_uri": str | None, "cells": [CELL,...]|None}``
    (CELL = ``{"row": int, "col": int, "text": str, "bbox": {...}|None}``).
    """

    def parse(self, raw: Any) -> dict: ...


class CannedParser:
    """Offline parser for the proof/replay: returns a fixed ``{"pages": [...]}`` structure."""

    def __init__(self, parsed: Mapping[str, Any], *, name: str = "canned", version: str = "0") -> None:
        self._parsed = dict(parsed)
        self.name = name
        self.version = version

    def parse(self, raw: Any) -> dict:  # raw ignored — the fixture IS the parse
        return self._parsed


# ── Node model ────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Node:
    object_id: str
    kind: str
    source_handle: str
    parent_ref: str | None
    ordinal: int
    page_no: int | None
    bbox: dict | None
    text: str | None
    artifact_uri: str | None
    content_hash: str
    lineage: dict = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "object_id": self.object_id, "kind": self.kind, "source_handle": self.source_handle,
            "parent_ref": self.parent_ref, "ordinal": self.ordinal, "page_no": self.page_no,
            "bbox": self.bbox, "text": self.text, "artifact_uri": self.artifact_uri,
            "content_hash": self.content_hash, "lineage": self.lineage,
        }


@dataclass
class DocumentTree:
    doc_id: str
    source: str
    root: str
    nodes: dict[str, Node]          # object_id -> Node
    order: list[str]                # deterministic reading order (all nodes)

    @property
    def page_count(self) -> int:
        return sum(1 for n in self.nodes.values() if n.kind == KIND_PAGE)

    def leaves(self) -> list[Node]:
        parents = {n.parent_ref for n in self.nodes.values() if n.parent_ref}
        return [self.nodes[oid] for oid in self.order if oid not in parents]

    def low_confidence(self) -> list[Node]:
        return [n for n in self.nodes.values()
                if float(n.lineage.get("confidence", 1.0)) < LOW_CONFIDENCE_FLOOR]


# ── Handles + hashing ─────────────────────────────────────────────────────────


def _hash(*parts: Any) -> str:
    h = hashlib.sha256()
    for p in parts:
        h.update(repr(p).encode("utf-8"))
    return h.hexdigest()


def doc_handle(source: str, doc_id: str) -> str:
    return f"ctx://{source}/doc/{doc_id}"


def _frag(base: str, **kv: Any) -> str:
    """Append an ordered query fragment to a base doc handle (coordinate-precise addressing)."""
    frag = "&".join(f"{k}={v}" for k, v in kv.items())
    return f"{base}#{frag}"


# ── Decomposition ──────────────────────────────────────────────────────────────


def decompose(
    source: str,
    doc_id: str,
    parsed: Mapping[str, Any],
    *,
    parser: str = "canned",
    parser_version: str = "0",
) -> DocumentTree:
    """Normalize a ParserProvider's output into the recursive ContextObject tree.

    Deterministic + pure: same parser output → byte-identical tree (sorted ordering, no clock).
    Every node carries a coordinate-precise source handle, a content hash (the rot identity),
    and lineage (parser + per-node confidence). Raises ``ValueError`` on malformed input.
    """
    if "pages" not in parsed or not isinstance(parsed["pages"], list):
        raise ValueError("parser output must carry a 'pages' list")

    base = doc_handle(source, doc_id)
    nodes: dict[str, Node] = {}
    order: list[str] = []

    def add(kind, handle, parent, ordinal, page_no, bbox, text, artifact_uri, confidence) -> str:
        oid = _hash("oid", handle)[:16]
        chash = _hash(kind, text, artifact_uri, bbox)  # rot identity: content, not position-of-mention
        nodes[oid] = Node(
            object_id=oid, kind=kind, source_handle=handle, parent_ref=parent, ordinal=ordinal,
            page_no=page_no, bbox=bbox, text=text, artifact_uri=artifact_uri, content_hash=chash,
            lineage={"parser": parser, "parser_version": parser_version, "confidence": round(float(confidence), 4)},
        )
        order.append(oid)
        return oid

    doc_id_node = add(KIND_DOCUMENT, base, None, 0, None, None, None, None, 1.0)

    for page in sorted(parsed["pages"], key=lambda p: int(p["page_no"])):
        pno = int(page["page_no"])
        ph = _frag(base, page=f"{pno:04d}")
        page_oid = add(KIND_PAGE, ph, doc_id_node, pno, pno, None, None, None, 1.0)

        # Per-page, per-kind occurrence counters: a figure handle is "the Nth figure on the
        # page" (figure=01), not "the Nth layout block" — stable across re-parses even if an
        # unrelated block is inserted above it. Text blocks number within their own sequence.
        seq: dict[str, int] = {}
        for bi, block in enumerate(sorted(page.get("blocks", []), key=lambda b: int(b.get("ordinal", 0)))):
            kind = block["kind"]
            bbox = block.get("bbox")
            conf = block.get("confidence", 1.0)
            if kind == KIND_TABLE:
                seq[KIND_TABLE] = seq.get(KIND_TABLE, 0) + 1
                tnum = f"{seq[KIND_TABLE]:02d}"
                th = _frag(base, page=f"{pno:04d}", table=tnum)
                table_oid = add(KIND_TABLE, th, page_oid, bi, pno, bbox, None, None, conf)
                for cell in block.get("cells", []):
                    r, c = int(cell["row"]), int(cell["col"])
                    ch = _frag(base, page=f"{pno:04d}", table=tnum, cell=f"r{r:02d}c{c:02d}")
                    add(KIND_TABLE_CELL, ch, table_oid, r * 1000 + c, pno, cell.get("bbox"),
                        str(cell.get("text", "")), None, conf)
            elif kind in ARTIFACT_KINDS:
                seq[kind] = seq.get(kind, 0) + 1
                fh = _frag(base, page=f"{pno:04d}", **{kind: f"{seq[kind]:02d}"})
                add(kind, fh, page_oid, bi, pno, bbox, None, block.get("artifact_uri"), conf)
            else:  # text-bearing block (paragraph/heading/equation/ocr_span/…)
                seq[KIND_BLOCK] = seq.get(KIND_BLOCK, 0) + 1
                bh = _frag(base, page=f"{pno:04d}", block=f"{seq[KIND_BLOCK]:02d}")
                add(kind, bh, page_oid, bi, pno, bbox, str(block.get("text", "")), None, conf)

    return DocumentTree(doc_id=doc_id, source=source, root=doc_id_node, nodes=nodes, order=order)


# ── Resolve / expand (the consumption-side contract) ─────────────────────────


def resolve(tree: DocumentTree, handle: str) -> Node | None:
    for n in tree.nodes.values():
        if n.source_handle == handle:
            return n
    return None


def expand(tree: DocumentTree, handle: str, *, with_parent: bool = False, with_children: bool = False) -> dict:
    """Return EXACTLY the node for ``handle`` (+ optionally its parent / direct children).

    This is why decomposition matters: a pack carries a leaf handle; expansion pulls the
    minimal node(s) on demand — the whole document never enters a context window.
    Raises ``KeyError`` if the handle does not resolve (a ``source_handle_unresolvable`` rot).
    """
    node = resolve(tree, handle)
    if node is None:
        raise KeyError(f"{ROT_HANDLE_UNRESOLVABLE}: {handle}")
    out: dict[str, Any] = {"node": node.as_dict()}
    if with_parent and node.parent_ref:
        out["parent"] = tree.nodes[node.parent_ref].as_dict()
    if with_children:
        out["children"] = [n.as_dict() for n in tree.nodes.values() if n.parent_ref == node.object_id]
    return out


# ── Re-decompose → diff (document context rot) ───────────────────────────────


def diff_trees(old: DocumentTree, new: DocumentTree) -> list[dict]:
    """Emit per-node rot signals between two decompositions of the same doc.

    Keyed by source handle (stable across re-parses): changed content_hash → node_changed;
    handle only in new → node_added; only in old → node_removed; page-count delta →
    page_count_changed. This is freshness at paragraph/figure/cell precision, not "the doc
    is stale". Deterministic (sorted by handle).
    """
    signals: list[dict] = []
    old_by_h = {n.source_handle: n for n in old.nodes.values()}
    new_by_h = {n.source_handle: n for n in new.nodes.values()}

    if old.page_count != new.page_count:
        signals.append({"type": ROT_PAGE_COUNT_CHANGED, "from": old.page_count, "to": new.page_count})

    for h in sorted(set(old_by_h) | set(new_by_h)):
        o, n = old_by_h.get(h), new_by_h.get(h)
        if o and n and o.content_hash != n.content_hash:
            signals.append({"type": ROT_NODE_CHANGED, "handle": h, "kind": n.kind})
        elif n and not o:
            signals.append({"type": ROT_NODE_ADDED, "handle": h, "kind": n.kind})
        elif o and not n:
            signals.append({"type": ROT_NODE_REMOVED, "handle": h, "kind": o.kind})
    return signals


# ── Fixtures + self-test ──────────────────────────────────────────────────────


def _fixture_v1() -> dict:
    return {"pages": [
        {"page_no": 1, "blocks": [
            {"kind": KIND_HEADING, "ordinal": 0, "text": "Sanctions Screening Policy", "confidence": 0.99},
            {"kind": KIND_PARAGRAPH, "ordinal": 1, "text": "All counterparties must be screened against the current list.",
             "bbox": {"x": 112.4, "y": 204.8, "width": 392.1, "height": 44.6, "unit": "pt"}, "confidence": 0.97},
        ]},
        {"page_no": 2, "blocks": [
            {"kind": KIND_TABLE, "ordinal": 0, "confidence": 0.88, "cells": [
                {"row": 1, "col": 1, "text": "Program"}, {"row": 1, "col": 2, "text": "Threshold"},
                {"row": 2, "col": 1, "text": "OFAC"}, {"row": 2, "col": 2, "text": "0 USD"},
            ]},
            {"kind": KIND_FIGURE, "ordinal": 1, "artifact_uri": "s3://baltor-artifacts/doc/policy/pages/0002-fig-01.png",
             "bbox": {"x": 60, "y": 400, "width": 300, "height": 200, "unit": "pt"}, "confidence": 0.9},
        ]},
        {"page_no": 3, "blocks": [
            {"kind": KIND_OCR_SPAN, "ordinal": 0, "text": "scanned addendum clause 4.2", "confidence": 0.41},  # low-conf
        ]},
    ]}


def _self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    parser = CannedParser(_fixture_v1(), name="canned", version="1")
    tree = decompose("acme", "policy-manual", parser.parse(None), parser="canned", parser_version="1")

    # ── recursive tree shape ──
    check("1 document + 3 pages", tree.page_count == 3 and sum(1 for n in tree.nodes.values() if n.kind == KIND_DOCUMENT) == 1)
    # doc=1, pages=3, p1: heading+para=2, p2: table+4cells+figure=6, p3: ocr=1 → 13 nodes
    check("node count = 13 (recursion incl. table cells)", len(tree.nodes) == 13, str(len(tree.nodes)))
    para = resolve(tree, "ctx://acme/doc/policy-manual#page=0001&block=02")
    check("paragraph addressable by fragment handle", para is not None and "screened" in (para.text or ""), str(para))
    check("paragraph carries bbox (coordinate-precise)", para is not None and para.bbox and para.bbox["unit"] == "pt")
    cell = resolve(tree, "ctx://acme/doc/policy-manual#page=0002&table=01&cell=r02c02")
    check("table cell addressable", cell is not None and cell.text == "0 USD", str(cell))
    fig = resolve(tree, "ctx://acme/doc/policy-manual#page=0002&figure=01")
    check("figure carries artifact pointer (not text)", fig is not None and fig.artifact_uri and fig.text is None)

    # ── lineage + quality: low-confidence OCR span flagged fragile ──
    low = tree.low_confidence()
    check("low-confidence OCR span flagged for review", len(low) == 1 and low[0].kind == KIND_OCR_SPAN, str(low))

    # ── claim attaches to a LEAF; expansion returns exactly that node ──
    claim = {"claim_text": "Screening is mandatory for all counterparties.",
             "source_handle": "ctx://acme/doc/policy-manual#page=0001&block=02"}
    ex = expand(tree, claim["source_handle"], with_parent=True)
    check("expansion returns exactly the cited leaf", ex["node"]["source_handle"] == claim["source_handle"])
    check("expansion can pull the parent page only on request", ex["parent"]["kind"] == KIND_PAGE)
    check("whole-doc text is NOT in the leaf payload (pack stays minimal)",
          "Sanctions Screening Policy" not in (ex["node"]["text"] or ""))
    raised = False
    try:
        expand(tree, "ctx://acme/doc/policy-manual#page=0099&block=99")
    except KeyError as e:
        raised = ROT_HANDLE_UNRESOLVABLE in str(e)
    check("unresolvable handle raises source_handle_unresolvable", raised)

    # ── determinism: re-decompose identical parse → byte-identical tree ──
    tree2 = decompose("acme", "policy-manual", parser.parse(None), parser="canned", parser_version="1")
    check("decompose is deterministic", {k: v.as_dict() for k, v in tree.nodes.items()} ==
          {k: v.as_dict() for k, v in tree2.nodes.items()})

    # ── re-decompose → diff = paragraph/cell-precise context rot ──
    v2 = _fixture_v1()
    v2["pages"][1]["blocks"][0]["cells"][3]["text"] = "10000 USD"   # the OFAC threshold cell changed
    tree_v2 = decompose("acme", "policy-manual", v2, parser="canned", parser_version="1")
    sigs = diff_trees(tree, tree_v2)
    changed = [s for s in sigs if s["type"] == ROT_NODE_CHANGED]
    check("diff isolates exactly the changed table cell", len(changed) == 1 and changed[0]["handle"].endswith("cell=r02c02"), str(changed))
    check("no spurious page_count_changed on an edit", not any(s["type"] == ROT_PAGE_COUNT_CHANGED for s in sigs))
    # remove page 3 → its node(s) removed + page_count_changed
    v3 = _fixture_v1(); v3["pages"] = v3["pages"][:2]
    sigs3 = diff_trees(tree, decompose("acme", "policy-manual", v3, parser="canned", parser_version="1"))
    check("removing a page emits page_count_changed + node_removed",
          any(s["type"] == ROT_PAGE_COUNT_CHANGED for s in sigs3) and any(s["type"] == ROT_NODE_REMOVED for s in sigs3))

    # ── the 1,000-page case: thousands of source-linked micro-objects, NOT one blob ──
    big = {"pages": [{"page_no": i, "blocks": [{"kind": KIND_PARAGRAPH, "ordinal": 0,
                      "text": f"Clause for page {i}.", "confidence": 0.95}]} for i in range(1, 1001)]}
    big_tree = decompose("acme", "policy-manual-1k", big, parser="canned", parser_version="1")
    check("1,000-page doc → 1,000 page nodes", big_tree.page_count == 1000, str(big_tree.page_count))
    check("1,000-page doc → >2,000 addressable micro-objects (not one blob)", len(big_tree.nodes) == 2001, str(len(big_tree.nodes)))
    check("each page-1000 paragraph independently addressable",
          resolve(big_tree, "ctx://acme/doc/policy-manual-1k#page=1000&block=01") is not None)

    print(f"\n{'all document_decompose self-tests passed.' if not failures else f'{len(failures)} FAILURES: {failures}'}")
    return 0 if not failures else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Bronze document decomposition (the contract Baltor owns).")
    p.add_argument("--self-test", action="store_true", help="offline, deterministic")
    p.add_argument("--demo", action="store_true", help="print the decomposed tree for the bundled fixture")
    args = p.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.demo:
        tree = decompose("acme", "policy-manual", _fixture_v1())
        print(json.dumps({"doc_id": tree.doc_id, "page_count": tree.page_count,
                          "node_count": len(tree.nodes),
                          "nodes": [tree.nodes[o].as_dict() for o in tree.order]}, indent=2))
        return 0
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
