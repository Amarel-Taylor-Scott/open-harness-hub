"""knowledge.product_distance — the Product Distance Metric (the owner's Registry #93 / §4).

Measures how close a REQUESTED system is to products that already exist, in latent (embedding) space rather than by
keyword: 'Build an AI coding assistant' -> {cursor: 0.91, claude_code: 0.88, continue_dev: 0.86}. This is much
stronger than keyword matching and is the differentiated 'you are rebuilding a product that exists' signal.

Grounded in _repos/shared-backend-components/architecture/product_similarity_registry.json + the embedder PLANE (best_embedder runtime; lexical floor
in proofs). The verdict (high_overlap) is a governed CANDIDATE a human triages, never an assertion. serves_truth=false.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import json
from pathlib import Path

from ._vec import (
    py_function_src_teleon_knowledge__vec__cosine,
    py_function_src_teleon_knowledge__vec__embed,
    py_function_src_teleon_knowledge__vec__lexical_embed_fn,
)

py_var_src_teleon_knowledge_product_distance___REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[3])
py_var_src_teleon_knowledge_product_distance___REGISTRY = _resource("architecture") / "product_similarity_registry.json"

py_var_src_teleon_knowledge_product_distance___HIGH_OVERLAP = 0.6  # nearest-product cosine above this -> flag likely reinvention of an existing product (tunable)
py_var_src_teleon_knowledge_product_distance___TOP = 5


def py_function_src_teleon_knowledge_product_distance__load_products() -> list[dict]:
    return json.loads(py_var_src_teleon_knowledge_product_distance___REGISTRY.read_text())["products"]


def py_function_src_teleon_knowledge_product_distance__build_product_space(py_arg_src_teleon_knowledge_product_distance__py_function_src_teleon_knowledge_product_distance__build_product_space__products: list[dict] | None = None, embed_fn=None) -> list[dict]:
    """Embed each product's description -> the latent product space (computed, not stored as truth)."""
    py_local_src_teleon_knowledge_product_distance__build_product_space__prods = py_arg_src_teleon_knowledge_product_distance__py_function_src_teleon_knowledge_product_distance__build_product_space__products if py_arg_src_teleon_knowledge_product_distance__py_function_src_teleon_knowledge_product_distance__build_product_space__products is not None else py_function_src_teleon_knowledge_product_distance__load_products()
    return [{**p, "vector": py_function_src_teleon_knowledge__vec__embed(p["description"], embed_fn)} for p in py_local_src_teleon_knowledge_product_distance__build_product_space__prods]


def py_function_src_teleon_knowledge_product_distance__distance_to_products(py_arg_src_teleon_knowledge_product_distance__py_function_src_teleon_knowledge_product_distance__distance_to_products__request_text: str, py_arg_src_teleon_knowledge_product_distance__py_function_src_teleon_knowledge_product_distance__distance_to_products__space: list[dict] | None = None, embed_fn=None) -> dict:
    """Rank existing products by semantic closeness to the request; flag high overlap (likely product reinvention)."""
    py_local_src_teleon_knowledge_product_distance__distance_to_products__sp = py_arg_src_teleon_knowledge_product_distance__py_function_src_teleon_knowledge_product_distance__distance_to_products__space if py_arg_src_teleon_knowledge_product_distance__py_function_src_teleon_knowledge_product_distance__distance_to_products__space is not None else py_function_src_teleon_knowledge_product_distance__build_product_space(embed_fn=embed_fn)
    py_local_src_teleon_knowledge_product_distance__distance_to_products__qv = py_function_src_teleon_knowledge__vec__embed(py_arg_src_teleon_knowledge_product_distance__py_function_src_teleon_knowledge_product_distance__distance_to_products__request_text, embed_fn)
    py_local_src_teleon_knowledge_product_distance__distance_to_products__ranked = sorted(
        ({"product": p["id"], "cluster": p.get("cluster"), "similarity": round(py_function_src_teleon_knowledge__vec__cosine(py_local_src_teleon_knowledge_product_distance__distance_to_products__qv, p["vector"]), 4)} for p in py_local_src_teleon_knowledge_product_distance__distance_to_products__sp),
        key=lambda py_arg_src_teleon_knowledge_product_distance__py_function_src_teleon_knowledge_product_distance__distance_to_products__r: py_arg_src_teleon_knowledge_product_distance__py_function_src_teleon_knowledge_product_distance__distance_to_products__r["similarity"], reverse=True)
    py_local_src_teleon_knowledge_product_distance__distance_to_products__nearest = py_local_src_teleon_knowledge_product_distance__distance_to_products__ranked[:py_var_src_teleon_knowledge_product_distance___TOP]
    py_local_src_teleon_knowledge_product_distance__distance_to_products__top = py_local_src_teleon_knowledge_product_distance__distance_to_products__nearest[0]["similarity"] if py_local_src_teleon_knowledge_product_distance__distance_to_products__nearest else 0.0
    return {
        "request": py_arg_src_teleon_knowledge_product_distance__py_function_src_teleon_knowledge_product_distance__distance_to_products__request_text[:120],
        "nearest_products": py_local_src_teleon_knowledge_product_distance__distance_to_products__nearest,
        "reinvention_probability": py_local_src_teleon_knowledge_product_distance__distance_to_products__top,  # closeness to the single nearest existing product
        "high_overlap": py_local_src_teleon_knowledge_product_distance__distance_to_products__top >= py_var_src_teleon_knowledge_product_distance___HIGH_OVERLAP,
        "nearest_cluster": py_local_src_teleon_knowledge_product_distance__distance_to_products__nearest[0]["cluster"] if py_local_src_teleon_knowledge_product_distance__distance_to_products__nearest else None,
        "verdict": (f"overlaps heavily with existing products (nearest {py_local_src_teleon_knowledge_product_distance__distance_to_products__top:.2f}) — consider reuse/comparison"
                    if py_local_src_teleon_knowledge_product_distance__distance_to_products__top >= py_var_src_teleon_knowledge_product_distance___HIGH_OVERLAP else "no strong overlap with a known product"),
        "serves_truth": False, "candidate": True,
    }


def _self_test() -> list[str]:
    py_local_src_teleon_knowledge_product_distance__self_test__fails = []

    def ck(py_arg_src_teleon_knowledge_product_distance__self_test_ck__name, py_arg_src_teleon_knowledge_product_distance__self_test_ck__ok):
        if not py_arg_src_teleon_knowledge_product_distance__self_test_ck__ok:
            py_local_src_teleon_knowledge_product_distance__self_test__fails.append(f"product_distance: {py_arg_src_teleon_knowledge_product_distance__self_test_ck__name}")
            print(f"  [XX] product_distance: {py_arg_src_teleon_knowledge_product_distance__self_test_ck__name}")

    py_local_src_teleon_knowledge_product_distance__self_test__lex = py_function_src_teleon_knowledge__vec__lexical_embed_fn()
    py_local_src_teleon_knowledge_product_distance__self_test__space = py_function_src_teleon_knowledge_product_distance__build_product_space(embed_fn=py_local_src_teleon_knowledge_product_distance__self_test__lex)
    ck("product space embeds every product", len(py_local_src_teleon_knowledge_product_distance__self_test__space) == len(py_function_src_teleon_knowledge_product_distance__load_products()) and all(p["vector"] for p in py_local_src_teleon_knowledge_product_distance__self_test__space))

    py_local_src_teleon_knowledge_product_distance__self_test__coding = py_function_src_teleon_knowledge_product_distance__distance_to_products("Build an AI coding assistant that edits my repository", py_local_src_teleon_knowledge_product_distance__self_test__space, embed_fn=py_local_src_teleon_knowledge_product_distance__self_test__lex)
    ck("coding request ranks a coding-assistant product nearest",
       py_local_src_teleon_knowledge_product_distance__self_test__coding["nearest_products"][0]["cluster"] == "ai_coding_assistant")

    py_local_src_teleon_knowledge_product_distance__self_test__vdb = py_function_src_teleon_knowledge_product_distance__distance_to_products("I want to build a vector database for embeddings", py_local_src_teleon_knowledge_product_distance__self_test__space, embed_fn=py_local_src_teleon_knowledge_product_distance__self_test__lex)
    ck("vector-db request ranks a vector_database product nearest",
       py_local_src_teleon_knowledge_product_distance__self_test__vdb["nearest_products"][0]["cluster"] == "vector_database")

    # high_overlap flag (embedder-agnostic): an exact product description -> cosine ~1.0 -> flagged, that product nearest
    py_local_src_teleon_knowledge_product_distance__self_test__exact = py_function_src_teleon_knowledge_product_distance__distance_to_products(next(p["description"] for p in py_function_src_teleon_knowledge_product_distance__load_products() if p["id"] == "cursor"), py_local_src_teleon_knowledge_product_distance__self_test__space,
                                 embed_fn=py_local_src_teleon_knowledge_product_distance__self_test__lex)
    ck("exact product description flags high overlap", py_local_src_teleon_knowledge_product_distance__self_test__exact["high_overlap"])
    ck("exact product description ranks that product nearest", py_local_src_teleon_knowledge_product_distance__self_test__exact["nearest_products"][0]["product"] == "cursor")

    # cluster separation (embedder-agnostic): coding request is closer to coding products than to a resilience lib
    py_local_src_teleon_knowledge_product_distance__self_test__sims = {r["product"]: r["similarity"] for r in py_local_src_teleon_knowledge_product_distance__self_test__coding["nearest_products"]}
    py_local_src_teleon_knowledge_product_distance__self_test__resilience_sim = next((r["similarity"] for r in py_function_src_teleon_knowledge_product_distance__distance_to_products(
        "Build an AI coding assistant that edits my repository", py_local_src_teleon_knowledge_product_distance__self_test__space, embed_fn=py_local_src_teleon_knowledge_product_distance__self_test__lex)["nearest_products"]
        if r["cluster"] == "resilience_library"), 0.0)
    ck("coding request separates clusters (coding > resilience)", py_local_src_teleon_knowledge_product_distance__self_test__coding["nearest_products"][0]["similarity"] > py_local_src_teleon_knowledge_product_distance__self_test__resilience_sim)
    ck("nearest-first ordering is monotonic", all(
        py_local_src_teleon_knowledge_product_distance__self_test__coding["nearest_products"][i]["similarity"] >= py_local_src_teleon_knowledge_product_distance__self_test__coding["nearest_products"][i + 1]["similarity"]
        for i in range(len(py_local_src_teleon_knowledge_product_distance__self_test__coding["nearest_products"]) - 1)))
    ck("verdict is a governed candidate", py_local_src_teleon_knowledge_product_distance__self_test__coding["serves_truth"] is False and py_local_src_teleon_knowledge_product_distance__self_test__coding["candidate"])
    return py_local_src_teleon_knowledge_product_distance__self_test__fails
