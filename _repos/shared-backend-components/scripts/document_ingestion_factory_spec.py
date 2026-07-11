#!/usr/bin/env python3
"""scripts.document_ingestion_factory_spec — the DURABLE BACKBONE for turning document corpora into
source-grounded, typed, candidate-only primitives (the OCR pipeline is the middle; this is layers 0-35).

Owner blueprint (2026-07-08, verified against `blue-guardrails/cheap-ocr` + GLM-OCR): the Blue Guardrails OCR
pipeline (`document_extraction_ocr_pack.py`) covers only layers 7-17 (render -> layout -> crop -> VLM OCR ->
assemble). The primitive factory needs the full supply chain around it — source discovery/trust/acquisition,
raw preservation, **two-stage metadata classification (cheap pre-OCR routing + semantic post-OCR)**, triage,
forensics, structural + semantic extraction, question/interrogation, candidate + anti-primitive generation,
dedupe, security, quality, verifier + benchmark generation, GATED promotion, route composition, telemetry,
drift, and gap feedback.

This module encodes that backbone as DATA (single source): the ordered layer stack, the three provenance
receipt schemas (OcrArtifactReceipt / OcrRegionReceipt / DocumentUnit), the primitive FAMILIES to fill, and the
OCR-specific promotion gates. It is a spec, not the 200 executors — those get minted into the families over
time. The load-bearing law: **OCR output is candidate EVIDENCE, never truth** — an OCR-derived primitive stays
candidate=true/serves_truth=false until a source-span-grounded verifier or human review promotes it, and
NEVER promotes from OCR alone. The $0.04/1000pp figure is a reproduce-TARGET (workload/GPU-specific), not a price.

    python3 scripts/document_ingestion_factory_spec.py --self-test
    python3 scripts/document_ingestion_factory_spec.py --emit
    python3 scripts/document_ingestion_factory_spec.py --show
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
    raise SystemExit(f"document_ingestion_factory_spec requires canonical_id; import failed: {exc}")

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
SPEC_ID_PREFIX = "spec-docingest"
PACK_DIR_REL = "data/dev-intel/primitive_factory/specialized_packs"
SCHEMA_DIR_REL = "schemas/document_ingestion"
SPEC_FILENAME = "document_ingestion_factory_spec.json"
PACKAGED_AT = "2026-07-08T00:00:00Z"
SOURCE_REFS = [
    "blueguardrails.com/en/blog/high-throughput-vlm-ocr (Mathis Lucka, 2026-07-07)",
    "github.com/blue-guardrails/cheap-ocr (Apache-2.0)",
    "github.com/zai-org/GLM-OCR ; huggingface.co/zai-org/GLM-OCR",
    "owner document-ingestion layered blueprint (2026-07-08, verified)",
]

# ── the ordered layer stack (0..35). `pack` marks which are already shipped here. ─────────────────────────────
# Each entry: (index, layer_name, one_line, shipped_by | None). The OCR pack covers layers 7-17.
_OCR_PACK = "document_extraction_ocr_pack"
LAYER_STACK: list[dict[str, Any]] = [
    {"i": 0, "layer": "source_discovery", "desc": "find candidate documents; why ingest; expected primitives"},
    {"i": 1, "layer": "source_trust_classification", "desc": "authority tier T0..T5, domain, risk"},
    {"i": 2, "layer": "acquisition_policy", "desc": "crawl/legal guardrails; license; robots; ToS-respecting"},
    {"i": 3, "layer": "raw_artifact_preservation", "desc": "store raw PDF + hash FIRST (root of lineage)"},
    {"i": 4, "layer": "pre_ocr_metadata_classification", "desc": "cheap route on filename/URL/headers/PDF meta"},
    {"i": 5, "layer": "document_triage", "desc": "text-first vs scanned-OCR vs hybrid vs table-heavy vs skip"},
    {"i": 6, "layer": "pdf_forensics", "desc": "encryption, embedded text, fonts, rotation, forms, signatures"},
    {"i": 7, "layer": "page_rendering", "desc": "render pages to images at DPI (cost lever)", "pack": _OCR_PACK},
    {"i": 8, "layer": "page_visual_classification", "desc": "text/table/form/scan/handwriting/multi-column"},
    {"i": 9, "layer": "adaptive_dpi_preprocess", "desc": "DPI by complexity + deskew/contrast (quality-gated)"},
    {"i": 10, "layer": "layout_detection", "desc": "PP-DocLayoutV3 region boxes + region graph", "pack": _OCR_PACK},
    {"i": 11, "layer": "region_classification", "desc": "heading/paragraph/table/figure/formula/code labels"},
    {"i": 12, "layer": "region_routing", "desc": "per-region OCR prompt/backend (table_to_markdown, etc.)"},
    {"i": 13, "layer": "region_crop_normalize", "desc": "crop/pad/deskew/encode + crop hash", "pack": _OCR_PACK},
    {"i": 14, "layer": "ocr_recognition", "desc": "GLM-OCR via vLLM (speculative decode)", "pack": _OCR_PACK},
    {"i": 15, "layer": "ocr_text_postprocess", "desc": "dehyphenate, de-dupe headers, normalize; keep raw+norm"},
    {"i": 16, "layer": "region_to_page_reconstruct", "desc": "reading-order assemble page md/html/json"},
    {"i": 17, "layer": "page_to_document_assembly", "desc": "merge pages/tables; PRESERVE source spans", "pack": _OCR_PACK},
    {"i": 18, "layer": "document_structure_classification", "desc": "type/sections/toc/refs/code-lists/endpoints"},
    {"i": 19, "layer": "semantic_metadata_classification", "desc": "industry/standard/datatype/operation/risk"},
    {"i": 20, "layer": "structural_extraction", "desc": "tables/kv/code-blocks/endpoints/enums/rules -> objects"},
    {"i": 21, "layer": "question_interrogation", "desc": "deconstruction-plane questions answered w/ source spans"},
    {"i": 22, "layer": "primitive_candidate_generation", "desc": "parser/validator/lookup/workflow/ruleset/tool"},
    {"i": 23, "layer": "anti_primitive_generation", "desc": "negative knowledge from warnings/exceptions/errors"},
    {"i": 24, "layer": "dedupe_canonicalization", "desc": "MinHash-LSH + behavior-sig + canonical id"},
    {"i": 25, "layer": "security_privacy_compliance", "desc": "PHI/PII/PCI/secret detect + redact + sandbox"},
    {"i": 26, "layer": "quality_confidence_scoring", "desc": "layout/ocr/table-fidelity/coverage/needs-review"},
    {"i": 27, "layer": "verifier_generation", "desc": "positive/negative/edge/mutation fixtures + verifiers"},
    {"i": 28, "layer": "benchmark_generation", "desc": "ocr-quality + downstream-primitive-yield benchmarks"},
    {"i": 29, "layer": "promotion_lifecycle", "desc": "ocr_evidence->candidate->validated->certified->production"},
    {"i": 30, "layer": "search_indexing", "desc": "index by source/type/industry/standard/schema/quality"},
    {"i": 31, "layer": "route_composition_ports", "desc": "emit normalized typed input/output ports immediately"},
    {"i": 32, "layer": "runtime_serving", "desc": "deterministic execution of promoted primitives"},
    {"i": 33, "layer": "telemetry_token_ledger", "desc": "pages/regions/candidates/verified-yield/route-delta"},
    {"i": 34, "layer": "drift_detection", "desc": "source/hash/schema/standard-version change -> re-OCR"},
    {"i": 35, "layer": "gap_feedback", "desc": "misses -> new source-discovery targets (close the loop)"},
]

# ── two-stage metadata classification (the owner's most-important added layer) ────────────────────────────────
TWO_STAGE_CLASSIFICATION: dict[str, Any] = {
    "pre_ocr": {"layer": 4, "inputs": ["filename", "url_path", "http_headers", "pdf_metadata", "page_count",
                                       "embedded_text_ratio"],
                "decides": ["skip_ocr_use_embedded_text", "scanned_needs_ocr", "table_heavy_pipeline",
                            "route_to_domain_interrogator", "quarantine_low_trust"],
                "why": "cheap; prevents wasting GPU time before expensive OCR"},
    "post_ocr": {"layer": 19, "inputs": ["recognized_sections", "tables", "examples", "workflows", "standards"],
                 "decides": ["industry", "standards", "datatypes", "operations", "risk", "human_review_required"],
                 "why": "content-grounded; makes OCR output useful for the multi-axis atlas"},
}

# ── OCR-derived promotion gates (EXTRA gates on top of the standard lifecycle) ───────────────────────────────
OCR_PROMOTION_GATES: list[str] = [
    "source_span_exists", "source_span_hash_valid", "raw_pdf_sha256_recorded",
    "region_or_page_reference_exists", "ocr_model_version_recorded", "layout_model_version_recorded",
    "dpi_recorded", "quality_score_above_threshold", "table_fidelity_passed_if_table_derived",
    "human_review_if_low_confidence", "no_promotion_from_ocr_alone",
]

# ── primitive families to fill (representative members; the taxonomy is the source of truth, not the count) ──
PRIMITIVE_FAMILIES: dict[str, list[str]] = {
    "atomic": ["pdf_count_pages", "pdf_render_page_to_image", "page_image_downsample", "layout_detect_regions",
               "layout_region_sort_reading_order", "layout_region_crop", "ocr_region_with_glm_ocr",
               "assemble_markdown_from_regions", "hash_raw_pdf", "hash_region_crop", "emit_ocr_stage_receipt"],
    "pipeline": ["ocr_pdf_to_markdown", "ocr_pdf_to_json_layout", "ocr_cloud_folder_to_markdown",
                 "ocr_resume_incomplete_documents", "ocr_skip_completed_outputs"],
    "performance": ["benchmark_pages_per_second", "measure_layout_wall_time", "measure_ocr_wall_time",
                    "tune_pdf_dpi", "tune_vllm_api_server_count", "tune_speculative_tokens",
                    "tune_page_batch_streaming"],
    "quality": ["ocr_compare_markdown_to_gold", "ocr_table_structure_score", "ocr_layout_order_score",
                "ocr_missing_region_detector", "ocr_hallucinated_text_detector", "ocr_low_confidence_page_router",
                "ocr_diff_against_commercial_provider"],
    "registry": ["ocr_artifact_to_document_units", "ocr_markdown_to_chunks", "ocr_layout_json_to_region_graph",
                 "ocr_document_to_candidate_primitives", "ocr_table_to_crosswalk_candidate",
                 "ocr_code_block_to_primitive_candidate", "ocr_page_region_to_source_span",
                 "ocr_source_span_to_provenance_ref"],
    "anti": ["anti_ocr.full_page_vlm_without_layout_for_complex_pdfs", "anti_ocr.lower_dpi_without_quality_gate",
             "anti_ocr.promote_ocr_text_to_truth_without_verifier", "anti_ocr.ignore_region_source_spans",
             "anti_ocr.benchmark_throughput_without_quality",
             "anti_ocr.compare_marginal_gpu_cost_to_managed_api_without_ops_overhead"],
}

# ── the three provenance receipt schemas (required-field contracts; JSON-schema-ish) ─────────────────────────
RECEIPT_SCHEMAS: dict[str, dict[str, Any]] = {
    "OcrArtifactReceipt": {
        "required": ["artifact_id", "source_document_id", "raw_pdf_sha256", "pipeline", "pipeline_version",
                     "layout_model", "ocr_model", "ocr_backend", "pdf_dpi", "pages", "regions", "output_formats",
                     "created_at", "candidate_only", "serves_truth"],
        "invariants": {"candidate_only": True, "serves_truth": False},
    },
    "OcrRegionReceipt": {
        "required": ["region_id", "page", "bbox", "layout_label", "crop_hash", "ocr_text_hash", "reading_order",
                     "source_span_ref"],
        "invariants": {},
    },
    "DocumentUnit": {
        "required": ["document_unit_id", "source_span_ref", "unit_type", "text", "candidate_primitives",
                     "needs_human_review", "candidate", "serves_truth"],
        "invariants": {"serves_truth": False},
        "unit_types": ["section", "paragraph", "table", "code_block", "form_field", "figure_caption"],
    },
}


def build_spec() -> dict[str, Any]:
    """The whole backbone as one candidate spec record."""
    spec_id = canonical_id(SPEC_ID_PREFIX, "layers", str(len(LAYER_STACK)), "v1")
    shipped = [ly for ly in LAYER_STACK if ly.get("pack")]
    return {
        "record_type": "document_ingestion_factory_spec",
        "spec_id": spec_id,
        "title": "Document-ingestion primitive factory — source corpora -> typed candidate primitives",
        "framing": "OCR is a SOURCE-ACQUISITION ACCELERATOR: convert corpora into source-grounded, typed, "
                   "benchmarkable primitive candidates. OCR output is candidate EVIDENCE, never truth.",
        "layer_stack": LAYER_STACK,
        "n_layers": len(LAYER_STACK),
        "layers_shipped_by_ocr_pack": [ly["i"] for ly in shipped],
        "two_stage_classification": TWO_STAGE_CLASSIFICATION,
        "ocr_promotion_gates": OCR_PROMOTION_GATES,
        "primitive_families": {k: {"members": v, "n": len(v),
                                   "note": "representative; taxonomy is source of truth, mint to fill"}
                               for k, v in PRIMITIVE_FAMILIES.items()},
        "receipt_schemas": RECEIPT_SCHEMAS,
        "cost_note": "$0.04/1000pp is a workload/GPU-specific reproduce-TARGET, not a universal OCR price; "
                     "benchmark quality + downstream-primitive-yield, not just throughput.",
        "source_refs": SOURCE_REFS,
        "packaged_at": PACKAGED_AT,
        **BOUNDARY,
    }


def _emit_schema_files() -> list[str]:
    out_dir = resource(SCHEMA_DIR_REL)
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for name, schema in RECEIPT_SCHEMAS.items():
        doc = {"$schema": "https://json-schema.org/draft/2020-12/schema", "title": name, "type": "object",
               "required": schema["required"],
               "properties": {f: {} for f in schema["required"]},
               "x_invariants": schema.get("invariants", {}), "x_candidate_only": True}
        p = out_dir / f"{name}.schema.json"
        p.write_text(json.dumps(doc, indent=2, sort_keys=True), encoding="utf-8")
        written.append(str(p))
    return written


def emit() -> dict[str, Any]:
    spec = build_spec()
    out_dir = resource(PACK_DIR_REL)
    out_dir.mkdir(parents=True, exist_ok=True)
    spec_path = out_dir / SPEC_FILENAME
    spec_path.write_text(json.dumps(spec, indent=2, sort_keys=True), encoding="utf-8")
    schemas = _emit_schema_files()
    return {"spec_path": str(spec_path), "n_layers": spec["n_layers"],
            "schema_files": schemas, "families": {k: len(v) for k, v in PRIMITIVE_FAMILIES.items()}}


def self_test() -> bool:
    """Mutation-gated: broken layer order, a receipt missing provenance, or a missing 'no_promotion_from_ocr_alone'
    gate goes RED."""
    # (1) layer stack is contiguous 0..N-1 and ordered.
    idx = [ly["i"] for ly in LAYER_STACK]
    assert idx == list(range(len(LAYER_STACK))), f"layer stack not contiguous/ordered: {idx[:5]}..."
    assert len(LAYER_STACK) >= 36, "expected the full 0-35 layer stack"

    # (2) the OCR pack maps into the render->assemble band (layers 7..17).
    shipped = [ly["i"] for ly in LAYER_STACK if ly.get("pack")]
    assert shipped and all(7 <= i <= 17 for i in shipped), f"OCR-pack layers out of band: {shipped}"

    # (3) two-stage classification present and cheap-before-expensive (pre < post layer index).
    assert TWO_STAGE_CLASSIFICATION["pre_ocr"]["layer"] < TWO_STAGE_CLASSIFICATION["post_ocr"]["layer"]

    # (4) the load-bearing gate: OCR alone can NEVER promote to truth.
    assert "no_promotion_from_ocr_alone" in OCR_PROMOTION_GATES
    assert "source_span_exists" in OCR_PROMOTION_GATES

    # (5) receipts carry provenance + the candidate/truth boundary.
    art = RECEIPT_SCHEMAS["OcrArtifactReceipt"]
    for f in ("raw_pdf_sha256", "ocr_model", "layout_model", "pdf_dpi", "candidate_only", "serves_truth"):
        assert f in art["required"], f"OcrArtifactReceipt missing provenance field {f}"
    assert art["invariants"]["serves_truth"] is False and art["invariants"]["candidate_only"] is True
    assert "source_span_ref" in RECEIPT_SCHEMAS["OcrRegionReceipt"]["required"]
    assert RECEIPT_SCHEMAS["DocumentUnit"]["invariants"]["serves_truth"] is False

    # (6) spec is candidate-only, families non-empty, id deterministic.
    spec = build_spec()
    assert spec["candidate"] is True and spec["serves_truth"] is False
    assert all(PRIMITIVE_FAMILIES.values()), "a primitive family is empty"
    assert build_spec()["spec_id"] == spec["spec_id"], "spec id not deterministic"

    n_members = sum(len(v) for v in PRIMITIVE_FAMILIES.values())
    print(f"OK document_ingestion_factory_spec self-test: {len(LAYER_STACK)} layers "
          f"(OCR pack covers {shipped}), {len(PRIMITIVE_FAMILIES)} families / {n_members} members, "
          f"{len(RECEIPT_SCHEMAS)} receipt schemas, no_promotion_from_ocr_alone gate present, serves_truth=false")
    return True


def main() -> None:
    ap = argparse.ArgumentParser(description="Document-ingestion primitive factory backbone (layers 0-35).")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--emit", action="store_true")
    ap.add_argument("--show", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return
    if args.emit:
        print(json.dumps(emit(), indent=2))
        return
    if args.show:
        print(json.dumps(build_spec(), indent=2, sort_keys=True))
        return
    self_test()


if __name__ == "__main__":
    main()
