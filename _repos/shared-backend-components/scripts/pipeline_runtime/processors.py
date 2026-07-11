#!/usr/bin/env python3
"""scripts.pipeline_runtime.processors — the swappable processor plugins (registry).

A processor is a pure-ish function ``fn(inputs, *, config, run) -> {artifact_type: payload}``. It takes
upstream artifacts + config and returns declared output artifacts — it never knows about the whole app.
Swapping ``decompose.structured_atomic@v1`` for ``@v2`` or ``parser.docling@v0`` is a MANIFEST change,
not a runner change. The runner resolves processors ONLY through this registry.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from scripts.foundry.scrapers import content_hash
from scripts.ingest.decompose_structured import decompose_cfpb_complaint, decompose_multigrain

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[2])
from scripts._repo_paths import resource as _resource
CFPB_FIXTURE = _resource("data") / "cfpb-demo" / "complaints-fixture.json"

ProcessorFn = Callable[[dict, ], dict]


@dataclass
class ProcessorSpec:
    processor_id: str
    processor_version: str
    kind: str
    input_schema: str
    output_schema: str
    deterministic: bool = True
    side_effects: str = "none"
    idempotent: bool = True
    supports_batch: bool = True
    owner: str = "baltor"
    available: bool = True
    unavailable_reason: str = ""

    @property
    def ref(self) -> str:
        return f"{self.processor_id}@{self.processor_version}"


class ProcessorRegistry:
    def __init__(self) -> None:
        self._fns: dict[str, ProcessorFn] = {}
        self._specs: dict[str, ProcessorSpec] = {}

    def register(self, spec: ProcessorSpec, fn: ProcessorFn) -> None:
        self._fns[spec.ref] = fn
        self._specs[spec.ref] = spec

    def has(self, ref: str) -> bool:
        return ref in self._fns

    def spec(self, ref: str) -> ProcessorSpec | None:
        return self._specs.get(ref)

    def get(self, ref: str) -> ProcessorFn:
        if ref not in self._fns:
            raise KeyError(f"unregistered processor {ref!r}")
        return self._fns[ref]

    def refs(self) -> list[str]:
        return sorted(self._fns)


# ── processor implementations (adapters over proven, deterministic code) ──────
def _p_source_fixture(inputs: dict, *, config: dict, run: dict) -> dict:
    records = json.loads(CFPB_FIXTURE.read_text(encoding="utf-8"))
    if isinstance(config.get("records"), list):
        records = config["records"]                      # allow injected records (tests/live)
    limit = int(config.get("limit", 5) or 5)
    records = records[:limit]
    norm = []
    for i, r in enumerate(records):
        norm.append({"native_id": str(r.get("complaint_id") or r.get("native_id") or f"demo-{i}"), "record": r})
    return {"SourceRecordBatch": {"records": norm, "count": len(norm)}}


def _p_decompose_atomic(inputs: dict, *, config: dict, run: dict) -> dict:
    batch = inputs["SourceRecordBatch"]["records"]
    facts, allegations = [], []
    for item in batch:
        d = decompose_cfpb_complaint(item["record"], native_id=item["native_id"])
        for c in d["components"]:
            (facts if c["claim_status"] == "fact" else allegations).append(c)
    return {"AtomicFactSet": {"facts": facts, "count": len(facts)},
            "HeldOutAllegationSet": {"allegations": allegations, "count": len(allegations)}}


def _p_decompose_multigrain(inputs: dict, *, config: dict, run: dict) -> dict:
    """v2 decomposer — same atomic facts/allegations PLUS extra grains (paragraphs/conclusion/sentiment)."""
    batch = inputs["SourceRecordBatch"]["records"]
    facts, allegations, per_record = [], [], []
    for item in batch:
        mg = decompose_multigrain(item["record"], native_id=item["native_id"])
        for c in mg["components"]:
            if c.get("claim_status") == "fact":
                facts.append(c)
            elif c.get("grain") in ("sentence", "paragraph"):
                allegations.append(c)
        per_record.append({"native_id": mg["native_id"], "grains": mg["grains"], "sentiment": mg["sentiment"]})
    return {"AtomicFactSet": {"facts": facts, "count": len(facts)},
            "HeldOutAllegationSet": {"allegations": allegations, "count": len(allegations)},
            "MultiGrainSet": {"per_record": per_record, "count": len(per_record)}}


def _p_verify_governance(inputs: dict, *, config: dict, run: dict) -> dict:
    facts = inputs["AtomicFactSet"]["facts"]
    all_handled = all("#" in f.get("source_handle", "") for f in facts)
    return {"VerifiedFactSet": {"facts": facts, "count": len(facts),
                                   "checks": {"all_facts_source_handled": all_handled,
                                              "all_facts_promotion_eligible": all(f.get("promotion_eligible") for f in facts)}}}


def _p_package_v1(inputs: dict, *, config: dict, run: dict) -> dict:
    facts = inputs["VerifiedFactSet"]["facts"]
    held = inputs.get("HeldOutAllegationSet", {}).get("allegations", [])
    fact_ids = [f["fact_id"] for f in facts]
    pack = {"kind": "baltor.context-pack", "pipeline": run.get("pipeline_ref"),
            "grain": {"atomic_facts": len(facts), "held_out_allegations": len(held)},
            "fact_object_ids": fact_ids, "source_handles": sorted({f["source_handle"] for f in facts})}
    pack["context_pack_id"] = "context-pack/" + content_hash(json.dumps(pack, sort_keys=True))[:12]
    receipt = {"kind": "baltor.context-receipt", "pack_id": pack["context_pack_id"],
               "facts_served": len(facts), "facts_held_out": len(held)}
    return {"ContextPack": pack, "Receipt": receipt}


def _p_package_v2(inputs: dict, *, config: dict, run: dict) -> dict:
    """v2 packager — same governed facts, adds a normalized fact_index (distinct output ⇒ distinct hash)."""
    out = _p_package_v1(inputs, config=config, run=run)
    pack = out["ContextPack"]
    pack["kind"] = "baltor.context-pack"
    pack["fact_index"] = {f.split("#")[-1]: f for f in pack["source_handles"]}  # the v2 addition
    pack["context_pack_id"] = "context-pack/" + content_hash(json.dumps(pack, sort_keys=True))[:12]
    out["Receipt"]["pack_id"] = pack["context_pack_id"]
    out["Receipt"]["packager"] = "v2"
    return out


def _p_source_canned_document(inputs: dict, *, config: dict, run: dict) -> dict:
    """A raw-document source (the unstructured path). A CannedParser fixture stands in for real bytes;
    a real fetch/parse (Docling/PyMuPDF) is the vendored swap that produces the same `parsed` shape."""
    from scripts.ingest.document_decompose import _fixture_v1
    doc_id = str(config.get("doc_id") or "policy-001")
    source = str(config.get("source") or "acme")
    return {"RawDocument": {"doc_id": doc_id, "source": source, "parsed": config.get("parsed") or _fixture_v1()}}


def _p_parser_document_tree(inputs: dict, *, config: dict, run: dict) -> dict:
    """ParserProvider SEAM: normalize a parser's output into the recursive ContextObject tree
    (coordinate-precise `ctx://…#` leaf handles, per-node lineage, low-confidence flags). Offline via the
    CannedParser fixture; real Docling/PyMuPDF/Unstructured slot behind the SAME contract."""
    from scripts.ingest.document_decompose import decompose
    raw = inputs["RawDocument"]
    tree = decompose(raw["source"], raw["doc_id"], raw["parsed"], parser="canned", parser_version="1")
    nodes = [tree.nodes[oid].as_dict() for oid in tree.order]
    return {"DocumentTree": {
        "doc_id": tree.doc_id, "source": tree.source, "root": tree.root, "page_count": tree.page_count,
        "node_count": len(nodes), "nodes": nodes,
        "leaf_handles": [n.source_handle for n in tree.leaves()],
        "low_confidence_handles": [n.source_handle for n in tree.low_confidence()]}}


def _p_docling_unavailable(inputs: dict, *, config: dict, run: dict) -> dict:
    """Experimental seam — Docling is not vendored; raise a CLEAR unavailable error (caught → run failed)."""
    raise RuntimeError("unavailable_processor: parser.docling@v0 — Docling not vendored in this environment (SEAM only)")


def default_registry() -> ProcessorRegistry:
    r = ProcessorRegistry()
    r.register(ProcessorSpec("source.cfpb_fixture", "v1", "source", "SourceBatch", "SourceRecordBatch"), _p_source_fixture)
    r.register(ProcessorSpec("decompose.structured_atomic", "v1", "decomposer", "SourceRecordBatch", "AtomicFactSet"), _p_decompose_atomic)
    r.register(ProcessorSpec("decompose.multigrain", "v2", "decomposer", "SourceRecordBatch", "MultiGrainSet"), _p_decompose_multigrain)
    r.register(ProcessorSpec("verify.governance", "v1", "verifier", "AtomicFactSet", "VerifiedFactSet"), _p_verify_governance)
    r.register(ProcessorSpec("package.context_pack", "v1", "packager", "VerifiedFactSet", "ContextPack"), _p_package_v1)
    r.register(ProcessorSpec("package.context_pack", "v2", "packager", "VerifiedFactSet", "ContextPack"), _p_package_v2)
    r.register(ProcessorSpec("source.canned_document", "v1", "source", "RawDocument", "RawDocument"), _p_source_canned_document)
    r.register(ProcessorSpec("parser.document_tree", "v1", "parser", "RawDocument", "DocumentTree"), _p_parser_document_tree)
    # experimental, unavailable (no dep) — registered so it's DISCOVERABLE but flagged + fails clearly if run
    r.register(ProcessorSpec("parser.docling", "v0", "parser", "RawDocument", "DocumentTree",
                             available=False, unavailable_reason="Docling not vendored (no-pip env)"), _p_docling_unavailable)
    return r
