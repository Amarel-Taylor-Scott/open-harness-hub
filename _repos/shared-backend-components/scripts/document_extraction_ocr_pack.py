#!/usr/bin/env python3
"""scripts.document_extraction_ocr_pack — register the open-source VLM OCR pipeline as a TYPED, composable
primitive GRAPH in the document-extraction wedge (candidate-only).

Source of the shape + the cost-descent receipt: the Blue Guardrails write-up "Open source OCR with Vision
Language Models: High throughput and low cost" (Mathis Lucka, 2026-07-07) — a single-GPU pipeline that OCRs
PDFs at ~20 pages/sec for ~$0.04 / 1,000 pages, ~100x cheaper than Mistral OCR 4 and ~250x cheaper than Azure
Document Intelligence. It is exactly (a) the pre-LLM OCR/layout component family this substrate lists and (b) a
worked "make-it-cheap descent" exemplar (Teleon thesis: make-it-work -> make-it-cheap -> deterministic
substitution), so it is registered as BOTH a primitive graph and a descent receipt.

The pipeline is a 5-node typed graph whose edges CHAIN end-to-end (each node's output_edge == the next node's
input_edge), so it composes through the same route machinery as every other pack:

    PdfPageInput
      -> pdf_page_to_image        -> RasterPageImage
      -> document_layout_detect   -> LayoutDetectedRasterPage      (PP-DocLayoutV3 / TensorRT backend)
      -> layout_region_crop       -> CroppedRegionImageBatch
      -> vlm_ocr_region           -> RegionTextFragmentBatch        (GLM-OCR 0.9B via vLLM)
      -> document_markdown_assemble -> ReconstructedMarkdownDocument (sink)

Everything emitted is candidate=true / serves_truth=false. The cost-descent numbers are a benchmark HOOK
(a cited external receipt), not our own executed measurement — reproducing them here is a follow-up.

    python3 scripts/document_extraction_ocr_pack.py --self-test
    python3 scripts/document_extraction_ocr_pack.py --emit
    python3 scripts/document_extraction_ocr_pack.py --show
"""
from __future__ import annotations

import sys
from pathlib import Path

# ── substrate-root bootstrap (sentinel; mirrors scripts/ml_lifecycle_primitive_minter.py) ────────────────────
_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots, resource  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import json  # noqa: E402
from typing import Any  # noqa: E402

try:
    from src.teleon.experiments.ids import canonical_id  # noqa: E402
except Exception as exc:  # noqa: BLE001
    raise SystemExit(f"document_extraction_ocr_pack requires canonical_id; import failed: {exc}")

# ── constants (single source; no magic values) ───────────────────────────────────────────────────────────────
BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
OCR_ID_PREFIX = "prim-dococr"
OCR_RECORD_TYPE = "document_extraction_ocr_primitive_candidate"
PACK_FILENAME = "document_extraction_ocr_primitive_cards.jsonl"
MANIFEST_FILENAME = "document_extraction_ocr_manifest.json"
PACKAGED_AT = "2026-07-08T00:00:00Z"
SOURCE_FAMILY = "open_source_vlm_ocr_pipeline"
SOURCE_REFS = [
    "blueguardrails.com — 'Open source OCR with Vision Language Models: High throughput and low cost'"
    " (Mathis Lucka, 2026-07-07)",
    "GLM-OCR (0.9B) — best on OmniDocBench; PP-DocLayoutV3 layout detection; vLLM serving.",
]
PACK_DIR_REL = "data/dev-intel/primitive_factory/specialized_packs"

# ── the 5-node typed pipeline: (node, blackbox, input_edge, output_edge, mutators, backend_notes) ────────────
# Edges are declared so output_edge[i] == input_edge[i+1] (a real chainable route). Source = PdfPageInput,
# sink = ReconstructedMarkdownDocument. Keep edge names CamelCase to match the pack edge convention.
_PIPELINE: list[dict[str, Any]] = [
    {
        "node": "pdf_page_to_image",
        "blackbox": "Rasterize one PDF page to an image at a configurable DPI. DPI is a first-class cost lever: "
                    "the source pipeline dropped 200->100 DPI with no OCR-quality loss on its corpus for a large "
                    "throughput gain. Pure/deterministic given (pdf_bytes, page_index, dpi).",
        "input_edge": "PdfPageInput",
        "output_edge": "RasterPageImage",
        "mutators": ["dpi_select", "page_index_bind", "colorspace_normalize"],
        "backend": "pypdfium2 / pdf2image render; deterministic given DPI.",
    },
    {
        "node": "document_layout_detect",
        "blackbox": "Detect layout bounding boxes (headings, paragraphs, tables, figures) on the rasterized page "
                    "so regions are OCR'd individually instead of feeding a whole page to the VLM. Backend is a "
                    "swappable zoo row (PaddlePaddle PP-DocLayoutV3 default; a TensorRT backend cut layout "
                    "wall-time from 46.8% -> 7.1% of the pipeline in the source).",
        "input_edge": "RasterPageImage",
        "output_edge": "LayoutDetectedRasterPage",
        "mutators": ["layout_model_select", "tensorrt_backend_toggle", "box_confidence_filter"],
        "backend": "PP-DocLayoutV3 (paddle) | TensorRT — selector row, race by receipt.",
    },
    {
        "node": "layout_region_crop",
        "blackbox": "Crop the page image into one image per detected region using the layout boxes, preserving "
                    "region metadata (kind, order, bbox) for reassembly. Pure/deterministic given (image, boxes).",
        "input_edge": "LayoutDetectedRasterPage",
        "output_edge": "CroppedRegionImageBatch",
        "mutators": ["bbox_crop", "region_order_preserve", "region_meta_attach"],
        "backend": "PIL/numpy crop; deterministic.",
    },
    {
        "node": "vlm_ocr_region",
        "blackbox": "Recognize text in each region crop with a small open OCR VLM (GLM-OCR 0.9B) served by vLLM. "
                    "The OCR stage is the throughput bottleneck once layout is fast; speculative decoding "
                    "(draft-3) and scaling vLLM API servers are the documented cost levers. Model + decode params "
                    "are zoo rows.",
        "input_edge": "CroppedRegionImageBatch",
        "output_edge": "RegionTextFragmentBatch",
        "mutators": ["ocr_model_select", "speculative_decode_toggle", "api_server_scale", "batch_stream"],
        "backend": "GLM-OCR 0.9B via vLLM (open weights) — model/decoder selector row.",
    },
    {
        "node": "document_markdown_assemble",
        "blackbox": "Reassemble region text fragments + region metadata into a full Markdown (or HTML) "
                    "reconstruction of the original document, in reading order. Pure/deterministic given "
                    "(fragments, region_meta). This is the sink of the route.",
        "input_edge": "RegionTextFragmentBatch",
        "output_edge": "ReconstructedMarkdownDocument",
        "mutators": ["reading_order_sort", "markdown_render", "html_render_alt"],
        "backend": "deterministic template render (markdown|html).",
    },
]

# ── the cost-descent receipt (cited external benchmark HOOK, not our own executed measurement) ────────────────
# throughput pages/sec and cost USD / 1,000 pages, in the order the source applied each optimization.
_DESCENT_RECEIPT: dict[str, Any] = {
    "record_type": "make_it_cheap_descent_receipt",
    "measured_by": "external_source",  # NOT executed here; reproduce = follow-up
    "source": SOURCE_REFS[0],
    "hardware": "single A100 40GB (steps 1-5) / L40S (star) on Modal",
    "unit_throughput": "pages_per_second",
    "unit_cost": "usd_per_1000_pages",
    "steps": [
        {"step": 1, "change": "reassembled_sdk_baseline", "pages_per_sec": 4.5, "usd_per_1000": 0.129},
        {"step": 2, "change": "4x_vllm_api_servers", "pages_per_sec": 5.6, "usd_per_1000": 0.105},
        {"step": 3, "change": "speculative_decoding_draft3", "pages_per_sec": 7.1, "usd_per_1000": 0.082},
        {"step": 4, "change": "100_dpi_page_images", "pages_per_sec": 11.6, "usd_per_1000": 0.050},
        {"step": 5, "change": "streaming_page_batches", "pages_per_sec": 14.3, "usd_per_1000": 0.041},
    ],
    "production_run": {"pages": 116000, "docs": 2000, "pages_per_sec": 20.0, "total_usd": 4.64,
                       "usd_per_1000": 0.04},
    "commercial_baselines_usd_per_1000": {"azure_document_intelligence": 10.0, "mistral_ocr_4": 4.0},
    "descent_thesis": "make_it_work -> make_it_cheap -> deterministic_substitution: a deterministic layout/crop/"
                      "assemble harness around a small open OCR model beats a big hosted OCR API on $/page by 100-250x.",
}


def _camel(edge: str) -> bool:
    return bool(edge) and edge[0].isupper() and edge.replace("+", "").isalnum()


def build_cards() -> list[dict[str, Any]]:
    """Deterministic candidate cards for the 5 pipeline nodes; edges chain end-to-end."""
    cards: list[dict[str, Any]] = []
    for i, step in enumerate(_PIPELINE):
        node = step["node"]
        in_edge, out_edge = step["input_edge"], step["output_edge"]
        cid = canonical_id(OCR_ID_PREFIX, node, in_edge, out_edge)
        route_sig = f"{in_edge} -> {out_edge}"
        blocking = sorted({t.lower() for t in (
            "document extraction", "ocr", "vlm ocr", "pdf parsing", "layout detection", node,
            in_edge.lower(), out_edge.lower(),
        ) if t})
        cards.append({
            "record_type": OCR_RECORD_TYPE,
            "kind": "document_extraction_ocr_node",
            "card_id": cid,
            "primitive_id": cid,
            "title": f"{node} — document-extraction OCR pipeline node ({i + 1}/{len(_PIPELINE)})",
            "blackbox": step["blackbox"] + f" Backend zoo: {step['backend']}",
            "blocking_keys": blocking,
            "domains": ["document_extraction", "ocr", "pre_llm_intake", "vlm_ocr_pipeline"],
            "candidate": True,
            "serves_truth": False,
            "source_family": SOURCE_FAMILY,
            "source_refs": SOURCE_REFS,
            "visible_edge": route_sig,
            "edge_contract": {
                "candidate": True,
                "input_edge": in_edge,
                "output_edge": out_edge,
                "input_contract": {"Edge": in_edge},
                "output_contract": {"Edge": out_edge},
            },
            "composition_hints": {
                "candidate_only": True,
                "serves_truth": False,
                "consumes_edge": in_edge,
                "produces_edge": out_edge,
                "route_signature": route_sig,
                "adapter_mutators": step["mutators"],
                "pipeline_position": i,
                "pipeline_prev": _PIPELINE[i - 1]["node"] if i > 0 else None,
                "pipeline_next": _PIPELINE[i + 1]["node"] if i + 1 < len(_PIPELINE) else None,
                "proofs_to_run_before_linking": [
                    "candidate_boundary_gate", "edge_chain_check", "backend_license_check",
                ],
            },
            "benchmark_hooks": {
                "cost_descent_receipt": _DESCENT_RECEIPT if node == "vlm_ocr_region" else
                {"see": "vlm_ocr_region node carries the full descent receipt"},
                "reproduce": "run the open pipeline on a held-out PDF set; record pages/sec + $/1000pp per step.",
            },
            "token_saving_usage": {
                "mechanism": "deterministic layout/crop/assemble around a small open OCR model",
                "vs": "hosted OCR API ($/page) or a large VLM reading whole pages",
                "candidate_only": True,
            },
            "packaged_at": PACKAGED_AT,
        })
    return cards


def graph_route() -> dict[str, Any]:
    """The full chained route as one record (source -> sink), edges proven to chain."""
    nodes = [s["node"] for s in _PIPELINE]
    src, sink = _PIPELINE[0]["input_edge"], _PIPELINE[-1]["output_edge"]
    return {
        "record_type": "document_extraction_ocr_route",
        "route_id": canonical_id(OCR_ID_PREFIX + "-route", src, sink, *nodes),
        "source_edge": src,
        "sink_edge": sink,
        "route_signature": f"{src} -> {sink}",
        "nodes": nodes,
        "edge_chain": [(s["input_edge"], s["output_edge"]) for s in _PIPELINE],
        "candidate": True,
        "serves_truth": False,
        "source_refs": SOURCE_REFS,
    }


def _pack_dir() -> Path:
    return resource(PACK_DIR_REL)


def emit() -> dict[str, Any]:
    cards = build_cards()
    route = graph_route()
    out_dir = _pack_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    pack_path = out_dir / PACK_FILENAME
    with pack_path.open("w", encoding="utf-8") as fh:
        for c in cards:
            fh.write(json.dumps(c, sort_keys=True) + "\n")
    manifest = {
        "record_type": "document_extraction_ocr_manifest",
        "pack_file": PACK_FILENAME,
        "n_cards": len(cards),
        "nodes": [s["node"] for s in _PIPELINE],
        "route": route,
        "descent_receipt": _DESCENT_RECEIPT,
        "source_family": SOURCE_FAMILY,
        "source_refs": SOURCE_REFS,
        "packaged_at": PACKAGED_AT,
        "candidate": True,
        "serves_truth": False,
    }
    (out_dir / MANIFEST_FILENAME).write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return {"pack_path": str(pack_path), "n_cards": len(cards), "route_nodes": manifest["nodes"]}


def self_test() -> bool:
    """Mutation-gated: a broken edge chain, a lost boundary bit, or a non-monotonic descent goes RED."""
    cards = build_cards()
    assert len(cards) == len(_PIPELINE) == 5, "expected 5 pipeline nodes"

    # (1) every card is candidate-only, never truth-serving.
    for c in cards:
        assert c["candidate"] is True and c["serves_truth"] is False, f"boundary broken: {c['card_id']}"
        assert c["edge_contract"]["candidate"] is True

    # (2) edges CHAIN end-to-end: output_edge[i] == input_edge[i+1]; all CamelCase.
    for i in range(len(cards) - 1):
        out_i = cards[i]["composition_hints"]["produces_edge"]
        in_next = cards[i + 1]["composition_hints"]["consumes_edge"]
        assert out_i == in_next, f"edge chain broken at node {i}: {out_i} != {in_next}"
    for s in _PIPELINE:
        assert _camel(s["input_edge"]) and _camel(s["output_edge"]), f"non-camel edge on {s['node']}"

    # (3) route source/sink are the pipeline endpoints.
    route = graph_route()
    assert route["source_edge"] == _PIPELINE[0]["input_edge"]
    assert route["sink_edge"] == _PIPELINE[-1]["output_edge"]
    assert route["nodes"] == [s["node"] for s in _PIPELINE]

    # (4) canonical ids: deterministic + unique.
    ids = [c["card_id"] for c in cards]
    assert len(set(ids)) == len(ids), "duplicate card ids"
    assert build_cards()[0]["card_id"] == cards[0]["card_id"], "ids not deterministic"

    # (5) the cited descent receipt is MONOTONE-improving (throughput up, cost down) — the make-it-cheap claim.
    steps = _DESCENT_RECEIPT["steps"]
    for a, b in zip(steps, steps[1:]):
        assert b["pages_per_sec"] >= a["pages_per_sec"], "throughput regressed in descent receipt"
        assert b["usd_per_1000"] <= a["usd_per_1000"], "cost regressed in descent receipt"
    # production run beats both commercial baselines on $/1000pp.
    prod = _DESCENT_RECEIPT["production_run"]["usd_per_1000"]
    for base in _DESCENT_RECEIPT["commercial_baselines_usd_per_1000"].values():
        assert prod < base, "production cost not below a commercial baseline"

    print(f"OK document_extraction_ocr_pack self-test: {len(cards)} chained candidate nodes, "
          f"route {route['route_signature']}, descent {steps[0]['pages_per_sec']}->{steps[-1]['pages_per_sec']} pg/s "
          f"(${steps[0]['usd_per_1000']}->${steps[-1]['usd_per_1000']}/1000pp), serves_truth=false")
    return True


def main() -> None:
    ap = argparse.ArgumentParser(description="Register the open VLM OCR pipeline as a candidate primitive graph.")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--emit", action="store_true", help="write the candidate pack + manifest")
    ap.add_argument("--show", action="store_true", help="print the route + cards")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return
    if args.emit:
        print(json.dumps(emit(), indent=2))
        return
    if args.show:
        print(json.dumps({"route": graph_route(), "cards": build_cards()}, indent=2, sort_keys=True))
        return
    self_test()


if __name__ == "__main__":
    main()
