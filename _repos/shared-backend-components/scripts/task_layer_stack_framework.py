#!/usr/bin/env python3
"""scripts.task_layer_stack_framework — the GENERIC "every task is a layered stack x options-per-layer" pattern
(candidate-only).

Owner directive (2026-07-08): "think about all of the possible ways and layers, and options per layer, that
simple tasks like document processing involve — we need to think about this for EVERYTHING." Document processing
is not one pipeline; it is a ~36-layer stack where each layer emits metadata, classifications, receipts, routing
decisions, primitive candidates, quality scores, and feedback. This is our MULTI-PATH LAW (zoo of zoos, standard
§1) made literal PER DOMAIN — and it recurs for every task the factory touches, not just OCR.

This module extracts the invariant: a set of CANONICAL LAYER ROLES that recur in every task domain, the fixed
set of things every layer can EMIT, the rule that every layer is itself a ZOO of interchangeable options
(extend by adding a row, never a rewrite), and a registry that MAPS each concrete domain (document ingestion,
app digestion, harness bakeoff, + the next domains to build) onto the canonical roles. New domain = one row.

Everything candidate=true / serves_truth=false.

    python3 scripts/task_layer_stack_framework.py --self-test
    python3 scripts/task_layer_stack_framework.py --show
    python3 scripts/task_layer_stack_framework.py --emit
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
    raise SystemExit(f"task_layer_stack_framework requires canonical_id; import failed: {exc}")

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
FRAMEWORK_ID_PREFIX = "spec-tasklayers"
PACK_DIR_REL = "data/dev-intel/primitive_factory/specialized_packs"
SPEC_FILENAME = "task_layer_stack_framework.json"
PACKAGED_AT = "2026-07-08T00:00:00Z"

# ── the fixed set of things ANY layer can emit (the owner's "each layer can emit ...") ───────────────────────
EMISSION_TYPES: list[str] = [
    "metadata", "classification", "receipt", "routing_decision", "primitive_candidates", "quality_score",
    "feedback",
]

# ── the canonical layer ROLES that recur in EVERY task domain (ordered). Each concrete domain's layers map onto
#    these; a domain need not fill every role, but the ORDER and the role semantics are invariant. Every layer is
#    a ZOO of options (multi-path law). ──────────────────────────────────────────────────────────────────────
CANONICAL_LAYER_ROLES: list[dict[str, Any]] = [
    {"role": "source_discovery", "purpose": "find candidate artifacts; why ingest; expected primitive yield"},
    {"role": "source_trust", "purpose": "authority tier, domain, license, risk"},
    {"role": "acquisition_policy", "purpose": "how to fetch; legal/ToS/robots guardrails"},
    {"role": "raw_preservation", "purpose": "store raw artifact + hash FIRST (root of lineage)"},
    {"role": "pre_transform_classification", "purpose": "cheap metadata route BEFORE expensive work"},
    {"role": "triage_routing", "purpose": "pick the ingestion/transform path (cost control)"},
    {"role": "forensics_probe", "purpose": "inspect structure before the core transform"},
    {"role": "core_transform", "purpose": "the visible pipeline (OCR / recon / inference / parse)"},
    {"role": "transform_postprocess", "purpose": "normalize + keep raw AND normalized"},
    {"role": "reconstruction", "purpose": "reassemble parts into structured output + source spans"},
    {"role": "structure_classification", "purpose": "classify the produced structure/objects"},
    {"role": "semantic_classification", "purpose": "content-grounded axes (industry/standard/operation/risk)"},
    {"role": "structural_extraction", "purpose": "extract machine-readable objects (tables/kv/rules/endpoints)"},
    {"role": "question_interrogation", "purpose": "deconstruction-plane questions answered w/ source spans"},
    {"role": "primitive_candidate_generation", "purpose": "typed candidate primitives per family + edges"},
    {"role": "anti_primitive_generation", "purpose": "negative knowledge from warnings/exceptions/errors"},
    {"role": "dedupe_canonicalization", "purpose": "MinHash-LSH + behavior-sig + canonical id"},
    {"role": "security_compliance", "purpose": "PHI/PII/PCI/secret detect + redact + sandbox"},
    {"role": "quality_confidence", "purpose": "per-part + per-artifact quality scores + needs-review"},
    {"role": "verifier_generation", "purpose": "positive/negative/edge/mutation fixtures + verifiers"},
    {"role": "benchmark_generation", "purpose": "quality + downstream-yield benchmarks"},
    {"role": "promotion_lifecycle", "purpose": "evidence->candidate->validated->certified->production (gated)"},
    {"role": "search_indexing", "purpose": "index by source/type/schema/quality/lifecycle"},
    {"role": "route_composition_ports", "purpose": "emit normalized typed input/output ports immediately"},
    {"role": "runtime_serving", "purpose": "deterministic execution of promoted primitives"},
    {"role": "telemetry_ledger", "purpose": "counts + yield + cost + route-delta + token ledger"},
    {"role": "drift_detection", "purpose": "source/hash/schema/version change -> re-run"},
    {"role": "gap_feedback", "purpose": "misses -> new source-discovery targets (close the loop)"},
]

# ── CROSS-CUTTING layers (owner §30 "additional layers beyond the obvious"): not a fixed position in the linear
#    stack — they wrap/observe MANY layers. Each is also a zoo of options. Every domain should consider them. ──
CROSS_CUTTING_LAYERS: list[dict[str, str]] = [
    {"layer": "cost_routing", "purpose": "before the expensive core: can a cheaper path solve it? select "
                                         "backend/DPI/page-subset/cloud-vs-local; estimate cost first"},
    {"layer": "primitive_yield_prediction", "purpose": "estimate expected primitive/standard/code-list/fixture "
                                                       "density BEFORE processing — is this artifact worth it?"},
    {"layer": "source_span_fidelity", "purpose": "every extracted claim links to id/page/region/bbox/span + raw "
                                                 "hash + output hash + model version (trust root)"},
    {"layer": "cross_document_merge", "purpose": "many primitives need several artifacts (spec + impl-guide + "
                                                 "examples + error-table + changelog) linked together"},
    {"layer": "human_review_ui", "purpose": "low-confidence parts + candidates create review tasks; "
                                            "approve/reject before promotion"},
    {"layer": "learned_routing", "purpose": "learn over time which artifact classes need which path/model, which "
                                            "sources yield good primitives, which candidates promote"},
    {"layer": "adversarial_stress", "purpose": "fuzz the pipeline (rotated/tiny-font/multi-column/handwriting/"
                                               "low-contrast/foreign-language) + a regression suite"},
]

# ── domain instantiations: map each concrete task domain onto the canonical roles. BUILT ones point at their
#    module; NEXT ones are stubs to fill (one row each). ────────────────────────────────────────────────────
DOMAIN_INSTANTIATIONS: dict[str, dict[str, Any]] = {
    "document_ingestion": {"module": "document_ingestion_factory_spec", "status": "built", "n_layers": 36,
                           "core_transform": "vlm_ocr (GLM-OCR/PP-DocLayout)",
                           "primitive_families": ["parser", "table_lookup", "ruleset", "workflow", "validator"]},
    "app_digestion": {"module": "app_digestion_primitive_generation_pack", "status": "built", "n_layers": 8,
                      "core_transform": "recon + component-spec extraction (getComputedStyle)",
                      "primitive_families": ["design_token", "component", "layout", "interaction_state", "a11y",
                                             "framework_idiom", "rebuild_plan"]},
    "harness_bakeoff": {"module": "harness_bakeoff_spec", "status": "built", "n_layers": 0,
                        "core_transform": "model x harness x runtime x task execution + metering",
                        "primitive_families": ["harness_run_receipt", "routing_policy"]},
    "esoteric_platform_formats": {"module": "esoteric_platform_primitive_pack", "status": "built", "n_layers": 0,
                                  "core_transform": "deterministic bit/byte/format parse",
                                  "primitive_families": ["parser", "decoder", "comparator", "checksum"]},
    "api_ingestion": {"module": None, "status": "next", "n_layers": 0,
                      "core_transform": "OpenAPI/GraphQL/proto spec -> request builder + response normalizer",
                      "primitive_families": ["api_tool", "schema_validator", "error_mapper", "pagination"]},
    "repo_mining": {"module": None, "status": "next", "n_layers": 0,
                    "core_transform": "AST/codegraph decompose of a repo",
                    "primitive_families": ["function", "adapter", "codemod", "test_fixture"]},
    "browser_automation": {"module": "primitive_browser_control_harness", "status": "partial", "n_layers": 0,
                           "core_transform": "browser trace -> tab_graph / form_map / safe_submit",
                           "primitive_families": ["tab_graph", "form_mapper", "safe_submit_gate"]},
    "kaggle_notebook": {"module": "kaggle_iterative_object_miner", "status": "partial", "n_layers": 0,
                        "core_transform": "notebook AST decompose",
                        "primitive_families": ["feature_transform", "model_step", "eval_metric"]},
    "data_pipeline": {"module": None, "status": "next", "n_layers": 0,
                      "core_transform": "ETL/warehouse job decompose",
                      "primitive_families": ["extractor", "transform", "loader", "quality_check"]},
}

MULTI_PATH_LAW = ("every layer is a ZOO of interchangeable options behind one selector (standard §1); extend a "
                  "layer by adding a row, never a rewrite; race options by receipt and keep the losers as "
                  "labelled fallbacks.")


def build_spec() -> dict[str, Any]:
    spec_id = canonical_id(FRAMEWORK_ID_PREFIX, "roles", str(len(CANONICAL_LAYER_ROLES)),
                           str(len(DOMAIN_INSTANTIATIONS)))
    built = {k: v for k, v in DOMAIN_INSTANTIATIONS.items() if v["status"] == "built"}
    return {
        "record_type": "task_layer_stack_framework",
        "spec_id": spec_id,
        "title": "Every task is a layered stack x options-per-layer (the multi-path law per domain)",
        "principle": "a 'simple' task (document processing, app cloning, harness selection, ...) is a deep "
                     "ordered stack of layers; each layer emits metadata/classification/receipt/routing/"
                     "candidates/quality/feedback and is itself a zoo of options.",
        "emission_types": EMISSION_TYPES,
        "canonical_layer_roles": CANONICAL_LAYER_ROLES,
        "n_canonical_roles": len(CANONICAL_LAYER_ROLES),
        "cross_cutting_layers": CROSS_CUTTING_LAYERS,
        "n_cross_cutting": len(CROSS_CUTTING_LAYERS),
        "domain_instantiations": DOMAIN_INSTANTIATIONS,
        "n_domains_built": len(built),
        "n_domains_next": sum(1 for v in DOMAIN_INSTANTIATIONS.values() if v["status"] == "next"),
        "multi_path_law": MULTI_PATH_LAW,
        "how_to_add_a_domain": "add one DOMAIN_INSTANTIATIONS row (module + core_transform + primitive_families), "
                               "then build the module mapping its layers onto the canonical roles.",
        "packaged_at": PACKAGED_AT,
        **BOUNDARY,
    }


def emit() -> dict[str, Any]:
    spec = build_spec()
    out_dir = resource(PACK_DIR_REL)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / SPEC_FILENAME).write_text(json.dumps(spec, indent=2, sort_keys=True), encoding="utf-8")
    return {"spec_path": str(out_dir / SPEC_FILENAME), "n_roles": spec["n_canonical_roles"],
            "n_domains": len(DOMAIN_INSTANTIATIONS), "built": spec["n_domains_built"]}


def self_test() -> bool:
    """Mutation-gated: a missing core role, a domain that maps to nothing, or a lost boundary bit goes RED."""
    roles = {r["role"] for r in CANONICAL_LAYER_ROLES}
    assert len(roles) == len(CANONICAL_LAYER_ROLES), "duplicate canonical role"

    # (1) the invariant spine must be present (these recur in EVERY domain).
    for must in ("source_discovery", "raw_preservation", "core_transform", "primitive_candidate_generation",
                 "promotion_lifecycle", "gap_feedback"):
        assert must in roles, f"canonical spine missing {must}"

    # (2) core_transform sits AFTER acquisition/preservation and BEFORE candidate generation (order invariant).
    order = [r["role"] for r in CANONICAL_LAYER_ROLES]
    assert order.index("raw_preservation") < order.index("core_transform") < \
        order.index("primitive_candidate_generation") < order.index("promotion_lifecycle"), "role order broken"

    # (3) emission types complete + include primitive_candidates + feedback (the loop).
    for e in ("primitive_candidates", "quality_score", "feedback"):
        assert e in EMISSION_TYPES, f"emission type missing {e}"

    # (4) every domain declares a core_transform + at least one primitive family; built ones name a real module.
    for name, dom in DOMAIN_INSTANTIATIONS.items():
        assert dom["core_transform"], f"domain {name} has no core_transform"
        assert dom["primitive_families"], f"domain {name} has no primitive families"
        if dom["status"] == "built":
            assert dom["module"], f"built domain {name} names no module"

    # (5) at least the four built domains are present (proof the pattern generalizes).
    built = [k for k, v in DOMAIN_INSTANTIATIONS.items() if v["status"] == "built"]
    assert len(built) >= 4, f"expected >=4 built domain instantiations, got {built}"

    # (5b) the owner's §30 cross-cutting layers are all named (thoroughness — the non-obvious layers).
    cc = {c["layer"] for c in CROSS_CUTTING_LAYERS}
    for must in ("cost_routing", "primitive_yield_prediction", "source_span_fidelity", "cross_document_merge",
                 "human_review_ui", "learned_routing", "adversarial_stress"):
        assert must in cc, f"cross-cutting layer missing {must}"

    # (6) candidate-only + deterministic id.
    spec = build_spec()
    assert spec["candidate"] is True and spec["serves_truth"] is False
    assert build_spec()["spec_id"] == spec["spec_id"]

    print(f"OK task_layer_stack_framework self-test: {len(CANONICAL_LAYER_ROLES)} canonical roles + "
          f"{len(CROSS_CUTTING_LAYERS)} cross-cutting, {len(EMISSION_TYPES)} emission types, "
          f"{len(DOMAIN_INSTANTIATIONS)} domains ({len(built)} built: {', '.join(built)}), serves_truth=false")
    return True


def main() -> None:
    ap = argparse.ArgumentParser(description="Generic 'every task is a layered stack x options' framework.")
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
