"""knowledge.product_distance — the Product Distance Metric (the owner's Registry #93 / §4).

Measures how close a REQUESTED system is to products that already exist, in latent (embedding) space rather than by
keyword: 'Build an AI coding assistant' -> {cursor: 0.91, claude_code: 0.88, continue_dev: 0.86}. This is much
stronger than keyword matching and is the differentiated 'you are rebuilding a product that exists' signal.

Grounded in architecture/product_similarity_registry.json + the embedder PLANE (best_embedder runtime; lexical floor
in proofs). The verdict (high_overlap) is a governed CANDIDATE a human triages, never an assertion. serves_truth=false.
"""
from __future__ import annotations

import json
from pathlib import Path

from ._vec import cosine, embed

_REPO = Path(__file__).resolve().parents[3]
_REGISTRY = _REPO / "architecture" / "product_similarity_registry.json"

_HIGH_OVERLAP = 0.6  # nearest-product cosine above this -> flag likely reinvention of an existing product (tunable)
_TOP = 5


def load_products() -> list[dict]:
    return json.loads(_REGISTRY.read_text())["products"]


def build_product_space(products: list[dict] | None = None, embed_fn=None) -> list[dict]:
    """Embed each product's description -> the latent product space (computed, not stored as truth)."""
    prods = products if products is not None else load_products()
    return [{**p, "vector": embed(p["description"], embed_fn)} for p in prods]


def distance_to_products(request_text: str, space: list[dict] | None = None, embed_fn=None) -> dict:
    """Rank existing products by semantic closeness to the request; flag high overlap (likely product reinvention)."""
    sp = space if space is not None else build_product_space(embed_fn=embed_fn)
    qv = embed(request_text, embed_fn)
    ranked = sorted(
        ({"product": p["id"], "cluster": p.get("cluster"), "similarity": round(cosine(qv, p["vector"]), 4)} for p in sp),
        key=lambda r: r["similarity"], reverse=True)
    nearest = ranked[:_TOP]
    top = nearest[0]["similarity"] if nearest else 0.0
    return {
        "request": request_text[:120],
        "nearest_products": nearest,
        "reinvention_probability": top,  # closeness to the single nearest existing product
        "high_overlap": top >= _HIGH_OVERLAP,
        "nearest_cluster": nearest[0]["cluster"] if nearest else None,
        "verdict": (f"overlaps heavily with existing products (nearest {top:.2f}) — consider reuse/comparison"
                    if top >= _HIGH_OVERLAP else "no strong overlap with a known product"),
        "serves_truth": False, "candidate": True,
    }


def _self_test() -> list[str]:
    fails = []

    def ck(name, ok):
        if not ok:
            fails.append(f"product_distance: {name}")
            print(f"  [XX] product_distance: {name}")

    lex = __import__("src.teleon.knowledge._vec", fromlist=["lexical_embed_fn"]).lexical_embed_fn()
    space = build_product_space(embed_fn=lex)
    ck("product space embeds every product", len(space) == len(load_products()) and all(p["vector"] for p in space))

    coding = distance_to_products("Build an AI coding assistant that edits my repository", space, embed_fn=lex)
    ck("coding request ranks a coding-assistant product nearest",
       coding["nearest_products"][0]["cluster"] == "ai_coding_assistant")

    vdb = distance_to_products("I want to build a vector database for embeddings", space, embed_fn=lex)
    ck("vector-db request ranks a vector_database product nearest",
       vdb["nearest_products"][0]["cluster"] == "vector_database")

    # high_overlap flag (embedder-agnostic): an exact product description -> cosine ~1.0 -> flagged, that product nearest
    exact = distance_to_products(next(p["description"] for p in load_products() if p["id"] == "cursor"), space,
                                 embed_fn=lex)
    ck("exact product description flags high overlap", exact["high_overlap"])
    ck("exact product description ranks that product nearest", exact["nearest_products"][0]["product"] == "cursor")

    # cluster separation (embedder-agnostic): coding request is closer to coding products than to a resilience lib
    sims = {r["product"]: r["similarity"] for r in coding["nearest_products"]}
    resilience_sim = next((r["similarity"] for r in distance_to_products(
        "Build an AI coding assistant that edits my repository", space, embed_fn=lex)["nearest_products"]
        if r["cluster"] == "resilience_library"), 0.0)
    ck("coding request separates clusters (coding > resilience)", coding["nearest_products"][0]["similarity"] > resilience_sim)
    ck("nearest-first ordering is monotonic", all(
        coding["nearest_products"][i]["similarity"] >= coding["nearest_products"][i + 1]["similarity"]
        for i in range(len(coding["nearest_products"]) - 1)))
    ck("verdict is a governed candidate", coding["serves_truth"] is False and coding["candidate"])
    return fails
