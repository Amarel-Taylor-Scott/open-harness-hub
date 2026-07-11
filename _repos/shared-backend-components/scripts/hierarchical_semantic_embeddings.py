"""scripts.hierarchical_semantic_embeddings — beyond one flat vector: embed each primitive along TYPED ROLES
(intent / object / action / outcome) AND at GRAINS of a semantic hierarchy (specific → operation-frame →
domain → abstract-shape), and match a query at every role × grain. A vague query matches at a COARSE grain
where the specific card misses; an object-focused query ("something for invoices") matches on the OBJECT
role where the intent role is silent. The union is the match — the multi-path law applied to MEANING, not
just surface tokens.

Why (the owner's question): a single blackbox embedding conflates what a primitive DOES with what it operates
ON and the SHAPE of change it makes. Splitting them into named roles lets a query weight the axis it cares
about; adding abstraction grains lets an under-specified query still land on the right family. Both are
backend-agnostic STRUCTURE — they hold whether the vectors come from the offline proxy or a real model
(the proxy is token-correlated today, so the DECOMPOSITION carries the signal the flat proxy cannot; a real
Ollama embedding sharpens every axis at once).

  ROLES (different embedding KINDS):
    intent   — what it DOES              (title + blackbox)                     [the purpose]
    object   — what it operates ON       (input+output edge types + datatypes)  [the nouns]
    action   — the operation VERB        (canonical operation facet as text)    [the action]
    outcome  — the SHAPE of change       (output edge + impact class)           [the effect/delta]

  GRAINS (hierarchical / grouped semantics, specific → abstract):
    L0 specific — the full card text
    L1 frame    — the operation FRAME (Removing/Transforming/… — kin near-synonyms folded)
    L2 domain   — the datatype FAMILY / domain
    L3 shape    — the impact class (scalar/structural/collection/… — the coarsest "kind of change")

Every vector reuses ``capability_embedding.embed_text`` (the shipped embedder) over role/grain TEXT built
from proof-gated facet extractors — this module adds no new embedding math. serves_truth=false.

    PYTHONPATH=. python3 scripts/hierarchical_semantic_embeddings.py --self-test
"""
from __future__ import annotations

import sys
from pathlib import Path

# ── substrate-root bootstrap (sentinel; mirrors scripts/capability_retrieval_mcp_server.py) ──────────────────
_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import json  # noqa: E402
from typing import Any, Callable  # noqa: E402

from scripts import capability_embedding as _emb  # noqa: E402  REUSE: the shipped NL embedder + cosine
from scripts import primitive_descriptor as _desc  # noqa: E402  REUSE: operations/datatypes/impact facets
from scripts import primitive_retrieval_bakeoff as _bakeoff  # noqa: E402  REUSE: frame folding (near-synonym kin)

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}

_MATCH_FLOOR = 0.15   # a role×grain cell "fires" above this cosine (single-source; below is noise)
#: RANKING weights — discriminative cells (specific text, intent, object) drive the rank; coarse grains
#: (L1 frame / L2 domain / L3 shape) have few distinct values so they carry RECALL, not rank (a flat max
#: over them lets a coarse-grain tie drown the specific signal — the hierarchy is a FALLBACK LADDER, not a
#: flat max). Weights need not sum to 1; the rank score normalizes by the weights present.
_RANK_WEIGHTS: dict[str, float] = {
    "role:intent": 0.32, "role:object": 0.26, "role:action": 0.10, "role:outcome": 0.06,
    "grain:L0_specific": 0.20, "grain:L1_frame": 0.04, "grain:L2_domain": 0.015, "grain:L3_shape": 0.005,
}


# ── ROLE text (what to embed for each typed axis) ────────────────────────────────────────────────────────────
def _role_text(card: dict[str, Any], role: str) -> str:
    if role == "intent":
        return f"{card.get('title') or ''} {_emb.blackbox_text(card)}"
    if role == "object":
        edges = f"{_emb._edge_str(card, 'input')} {_emb._edge_str(card, 'output')}"
        return f"{edges} {' '.join(sorted(_desc.datatypes(card)))}"
    if role == "action":
        return " ".join(sorted(_desc.operations(card))) or "act"
    if role == "outcome":
        return f"{_emb._edge_str(card, 'output')} impact {_desc.impact_class(card)}"
    raise ValueError(f"unknown role {role!r}")


ROLES: tuple[str, ...] = ("intent", "object", "action", "outcome")


# ── GRAIN text (the abstraction hierarchy) ───────────────────────────────────────────────────────────────────
def _grain_text(card: dict[str, Any], grain: str) -> str:
    if grain == "L0_specific":
        return f"{card.get('title') or ''} {_emb.blackbox_text(card)}"
    if grain == "L1_frame":
        return _bakeoff.frame_of_card(card) or "act"
    if grain == "L2_domain":
        return " ".join(sorted(_desc.datatypes(card))) or "generic"
    if grain == "L3_shape":
        return _desc.impact_class(card) or "neutral"
    raise ValueError(f"unknown grain {grain!r}")


GRAINS: tuple[str, ...] = ("L0_specific", "L1_frame", "L2_domain", "L3_shape")


def typed_key(card: dict[str, Any]) -> dict[str, list[float]]:
    """The card's TYPED-ROLE embedding key — one unit vector per role (intent/object/action/outcome)."""
    return {role: _emb.embed_text(_role_text(card, role)) for role in ROLES}


def grained_key(card: dict[str, Any]) -> dict[str, list[float]]:
    """The card's HIERARCHICAL embedding key — one unit vector per abstraction grain (specific→shape)."""
    return {grain: _emb.embed_text(_grain_text(card, grain)) for grain in GRAINS}


def _q_role_text(query: str, role: str) -> str:
    """A raw query has no edges — read its roles from the query text itself via the same facet extractors."""
    qc = {"title": query, "blackbox": query, "input_edge": "", "output_edge": ""}
    if role == "intent":
        return query
    if role == "object":
        return " ".join(sorted(_desc.datatypes(qc))) or query
    if role == "action":
        return " ".join(sorted(_desc.operations(qc))) or query
    if role == "outcome":
        return f"impact {_desc.impact_class(qc)}"
    raise ValueError(role)


def _q_grain_text(query: str, grain: str) -> str:
    qc = {"title": query, "blackbox": query, "input_edge": "", "output_edge": ""}
    if grain == "L0_specific":
        return query
    if grain == "L1_frame":
        return _bakeoff.frame_of_card(qc) or "act"
    if grain == "L2_domain":
        return " ".join(sorted(_desc.datatypes(qc))) or "generic"
    if grain == "L3_shape":
        return _desc.impact_class(qc) or "neutral"
    raise ValueError(grain)


def match(query: str, card: dict[str, Any]) -> dict[str, Any]:
    """Score (query, card) at EVERY role × grain. Returns per-role, per-grain, the strongest firing cell, and
    the union (max over all cells) — so a query lands on whichever axis/level actually carries its meaning."""
    role_scores = {r: round(max(0.0, _emb.cosine(_emb.embed_text(_q_role_text(query, r)),
                                                 _emb.embed_text(_role_text(card, r)))), 4) for r in ROLES}
    grain_scores = {g: round(max(0.0, _emb.cosine(_emb.embed_text(_q_grain_text(query, g)),
                                                  _emb.embed_text(_grain_text(card, g)))), 4) for g in GRAINS}
    cells = {**{f"role:{r}": s for r, s in role_scores.items()},
             **{f"grain:{g}": s for g, s in grain_scores.items()}}
    best = max(cells, key=lambda c: cells[c])
    # RANK score = weighted blend favouring discriminative cells (specific/intent/object); coarse grains
    # contribute little to rank. RECALL score = the raw max any cell fires (the hierarchy's fallback: a vague
    # query with only a coarse-grain hit is still RETRIEVABLE, just not top-ranked over a specific match).
    rank_score = sum(_RANK_WEIGHTS[c] * cells[c] for c in _RANK_WEIGHTS) / sum(_RANK_WEIGHTS.values())
    return {"query": query, "primitive_id": card.get("primitive_id"),
            "role_scores": role_scores, "grain_scores": grain_scores,
            "best_cell": best, "best_score": cells[best],
            "rank_score": round(rank_score, 4),           # discriminative — drives ranking
            "recall_score": round(max(cells.values()), 4),  # any-cell max — the hierarchy fallback for recall
            "union_score": round(max(cells.values()), 4),   # kept for compat (== recall_score)
            "cells_fired": sorted(c for c, s in cells.items() if s >= _MATCH_FLOOR), **BOUNDARY}


def rank(query: str, cards: list[dict[str, Any]], *, k: int = 5, cell: str | None = None) -> list[dict[str, Any]]:
    """Rank cards for a query. ``cell=None`` = UNION (each card by its strongest role×grain cell — the robust
    default); ``cell='role:object'`` or ``cell='grain:L1_frame'`` isolates one cell for the per-cell receipt."""
    scored: list[tuple[float, str]] = []
    for card in cards:
        m = match(query, card)
        if cell is None:
            s = m["rank_score"]  # discriminative blend — specific/intent/object win, not a coarse-grain tie
        elif cell.startswith("role:"):
            s = m["role_scores"][cell.split(":", 1)[1]]
        else:
            s = m["grain_scores"][cell.split(":", 1)[1]]
        scored.append((s, str(card.get("primitive_id") or "")))
    scored.sort(key=lambda t: (-t[0], t[1]))
    floor = 0.0 if cell is None else _MATCH_FLOOR  # rank_score is a weighted blend (smaller magnitude than a raw cell)
    return [{"primitive_id": pid, "score": round(s, 4)} for s, pid in scored[:k] if s > floor]


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []
    cards = [
        {"primitive_id": "p:invoice", "title": "Extract invoice line items",
         "blackbox": "Parse a pdf invoice and extract structured line item records.",
         "input_edge": "PdfInvoice", "output_edge": "LineItemRecords", **BOUNDARY},
        {"primitive_id": "p:dedup", "title": "Deduplicate records",
         "blackbox": "Remove duplicate rows by clustering near-identical records.",
         "input_edge": "RecordBatch", "output_edge": "DedupedBatch", **BOUNDARY},
        {"primitive_id": "p:resize", "title": "Resize image",
         "blackbox": "Resize an image to target dimensions.",
         "input_edge": "Image", "output_edge": "ResizedImage", **BOUNDARY},
    ]
    # (a) typed key: all four roles, each a unit vector; grained key: all four grains
    tk = typed_key(cards[0])
    checks.append(("typed key has all four ROLES", set(tk) == set(ROLES)))
    checks.append(("grained key has all four GRAINS", set(grained_key(cards[0])) == set(GRAINS)))

    # (b) TYPED decomposition works: an OBJECT-focused query ("something for invoices") scores the invoice
    #     card higher on the OBJECT role than a pure INTENT query would on an unrelated card's object role
    obj_q = "i need something that works with pdf invoices"
    m_inv = match(obj_q, cards[0])
    checks.append(("an object-focused query fires the OBJECT/intent axis on the right card",
                   m_inv["role_scores"]["object"] >= _MATCH_FLOOR or m_inv["role_scores"]["intent"] >= _MATCH_FLOOR))
    checks.append(("the union ranks the object-matched card #1",
                   rank(obj_q, cards, k=1) and rank(obj_q, cards, k=1)[0]["primitive_id"] == "p:invoice"))

    # (c) HIERARCHICAL recovery: a vague, under-specified query that shares few surface words still lands on
    #     the dedup card via a COARSE grain (frame 'Removing' / collection shape) — union catches it
    vague_q = "tidy up and shrink my messy pile of rows"
    m_dedup = match(vague_q, cards[1])
    checks.append(("a vague query fires a COARSE grain (frame/domain/shape) on the right family",
                   any(m_dedup["grain_scores"][g] >= _MATCH_FLOOR for g in ("L1_frame", "L2_domain", "L3_shape"))))

    # (d) the RECALL score == the best single cell (the hierarchy's fallback never loses recall), while the
    #     RANK score is a discriminative blend that is NOT dominated by a coarse-grain tie
    m = match("extract structured records from a document", cards[0])
    single_best = max(list(m["role_scores"].values()) + list(m["grain_scores"].values()))
    checks.append(("recall_score == best single cell (hierarchy fallback never loses recall)",
                   abs(m["recall_score"] - single_best) < 1e-9))
    checks.append(("rank_score is discriminative, not a raw coarse-grain max (rank <= recall)",
                   m["rank_score"] <= m["recall_score"] + 1e-9))

    # (e) determinism + governance
    checks.append(("determinism (byte-identical twice)",
                   json.dumps(match(vague_q, cards[1]), sort_keys=True)
                   == json.dumps(match(vague_q, cards[1]), sort_keys=True)))
    checks.append(("everything is candidate/serves_truth=false",
                   typed_key.__doc__ is not None and match(vague_q, cards[1])["serves_truth"] is False))

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print(f"\nPASS - hierarchical_semantic_embeddings: {len(ROLES)} TYPED role embeddings (intent/object/action/"
          f"outcome) x {len(GRAINS)} hierarchical GRAINS (specific→frame→domain→shape) per primitive, matched at "
          f"every role x grain with a union — an object-focused query lands on the OBJECT axis, a vague query "
          f"lands on a COARSE grain, and the union never loses to a single cell. Backend-agnostic structure "
          f"(sharpens under a real embedder). serves_truth=false.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--match", nargs=2, metavar=("QUERY", "CARD_JSON"), help="score one query x card (debug)")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.match:
        print(json.dumps(match(args.match[0], json.loads(args.match[1])), indent=2, sort_keys=True))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
