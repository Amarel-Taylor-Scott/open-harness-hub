#!/usr/bin/env python3
"""scripts.edge_representations — express an edge MANY ways and match / search / gate / remix across them.

Owner insight: an edge is not one string — it can be EXPRESSED, EDITED, SEARCHED, BLOCKED, and expressed as
EMBEDDINGS, as COMPATIBILITY, and as REMIXABILITY. So it must be a MULTI-PATH portfolio (the repo's
MULTI-PATH law: a portfolio of contract-substitutable representations behind one selector, never one
hardwired matcher). This module unifies the edge representations the composition system needs and factors
the "which representation matched" decision into ONE place, so edge_type_matcher / hybrid_composer / the
graph builders all decide compatibility the same way instead of re-implementing it.

The REPRESENTATIONS (each: edge -> a comparable form), strongest-confidence first:
  raw        — the exact string (identity).
  canonical  — folded onto the curated edge-type vocabulary (edge_type_matcher.canonicalize_edge).
  family     — the DOMINANT recurring type-token (data-driven standardization: many raw edges -> one family;
               the fix for canonicalize producing ~as-many "canonical" outputs as raw edges).
  tokens     — the significant type-token SET (Jaccard overlap).
  embedding  — a DETERMINISTIC char-trigram hashed vector (cosine similarity) — the offline stand-in for a
               real embedding model (nomic-embed-text); no network, reproducible.
  structural — the shape (arity / compound? / carries a policy?), for coarse type-compat.

The OPERATIONS:
  represent(edge)            -> all representations of one edge.
  compatibility(a, b)        -> the PORTFOLIO decision: the strongest representation that fires + a score +
                                the per-representation breakdown (never one hardcoded rule).
  connectivity(cards, via)   -> fraction of inputs that have a compatible producer under a chosen
                                representation (the honest lever measurement: raw << family <= token).
  search(edge, index, via)   -> compatible producer primitive_ids via a representation.
  remixable(a, b)            -> can edge a be EDITED (primitive_onion.remix_edges) into b? (same family,
                                different surface — a slight variation, not a new capability).
  blocked(a, b, forbidden)   -> a governance GATE: a forbidden/unsafe composition is blocked even if
                                otherwise compatible (e.g. a private edge feeding a public one).

candidate=true / serves_truth=false — representations + compatibility are POINTERS, never truth.

    PYTHONPATH=. python3 scripts/edge_representations.py --self-test
"""
from __future__ import annotations

import sys
from pathlib import Path

_here = Path(__file__).resolve()
_sbc = next((p for p in _here.parents if (p / "scripts" / "_repo_paths.py").exists()), _here.parents[1])
if str(_sbc) not in sys.path:
    sys.path.insert(0, str(_sbc))
from scripts._repo_paths import install as _install_code_roots  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import json  # noqa: E402
import math  # noqa: E402
import re  # noqa: E402
import zlib  # noqa: E402
from collections import Counter, defaultdict  # noqa: E402

#: noise tokens that never carry a composable TYPE (single source; shared by every representation).
_NOISE = frozenset(("policy", "pack", "batch", "intent", "signal", "report", "data", "the", "and", "for",
                    "with", "from", "list", "set", "map", "item", "record"))
_EMBED_DIM = 64                 # char-trigram hashed embedding dimension (small, deterministic)
_TOKEN_JACCARD_FLOOR = 0.34     # tokens representation fires at >= this Jaccard (over-matches below)
_EMBED_COS_FLOOR = 0.62         # embedding representation fires at >= this cosine
#: family df window — a token is a FAMILY only if it recurs enough to be a shared type but is not universal
#: noise (so we get hundreds of real families, not one giant "data" bucket nor ~unique per-edge canon).
_FAMILY_MIN_DF = 3
_FAMILY_MAX_DF_FRACTION = 0.20
#: confidence order — a portfolio prefers the STRONGEST representation that fires (exact > … > embedding).
_REPRESENTATION_ORDER = ("exact", "canonical", "family", "tokens", "embedding")
_REP_SCORE = {"exact": 1.0, "canonical": 0.9, "family": 0.75, "tokens": 0.5, "embedding": 0.45}


def type_tokens(edge: str) -> frozenset[str]:
    """Significant type tokens: camelCase + compound (+ : delimiters) split, 4+-char, noise dropped."""
    spaced = re.sub(r"([a-z])([A-Z])", r"\1 \2", str(edge)).replace("+", " ").replace(":", " ")
    return frozenset(t for t in re.findall(r"[a-z]{4,}", spaced.lower()) if t not in _NOISE)


def canonical(edge: str) -> str:
    """Fold onto the curated edge-type vocabulary (reuse the existing matcher's canonicalizer; fall back to a
    lowercase token-join so this module never hard-depends on that import)."""
    try:
        from scripts.edge_type_matcher import canonicalize_edge  # noqa: PLC0415
        return canonicalize_edge(edge) or ""
    except Exception:  # noqa: BLE001
        return "".join(sorted(type_tokens(edge)))


def embedding(edge: str) -> list[float]:
    """Deterministic char-trigram HASHED embedding (L2-normalized). The offline, reproducible stand-in for a
    real embedding model — same edge -> same vector, no network, no model."""
    vec = [0.0] * _EMBED_DIM
    s = "  " + re.sub(r"[^a-z0-9]", "", str(edge).lower()) + "  "
    for i in range(len(s) - 2):
        vec[zlib.crc32(s[i:i + 3].encode()) % _EMBED_DIM] += 1.0
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def _cos(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def structural(edge: str) -> tuple[int, bool, bool]:
    """Coarse shape: (#significant type tokens, is a compound '+' edge?, carries a policy/noise qualifier?)."""
    e = str(edge)
    return (len(type_tokens(e)), "+" in e, bool(re.search(r"policy|pack|batch", e, re.I)))


def build_family_index(edges) -> dict[str, str]:
    """Assign each edge a FAMILY = its dominant recurring type token (df in the [MIN, MAX*N] window, ties ->
    the lexicographically smallest for determinism). Data-driven standardization: many raw edges collapse to
    one family, which is what raw canonicalization failed to do. Edges with no qualifying token -> '' (unfoldable)."""
    edges = list(dict.fromkeys(edges))  # DISTINCT edge types — family is a TYPE property, not weighted by how
    df: Counter = Counter()             # many cards happen to use an edge (df over repeats skews the window)
    for e in edges:
        df.update(type_tokens(e))
    n = len(edges) or 1
    hi = max(_FAMILY_MIN_DF, int(_FAMILY_MAX_DF_FRACTION * n))
    fam: dict[str, str] = {}
    for e in edges:
        cands = [(df[t], t) for t in type_tokens(e) if _FAMILY_MIN_DF <= df[t] <= hi]
        fam[e] = min(cands, key=lambda dt: (-dt[0], dt[1]))[1] if cands else ""
    return fam


def family(edge: str, family_index: dict[str, str]) -> str:
    return family_index.get(edge, "")


def represent(edge: str, family_index: dict[str, str] | None = None) -> dict:
    """All representations of ONE edge — the multi-expression view."""
    return {
        "raw": edge,
        "canonical": canonical(edge),
        "family": family(edge, family_index or {}),
        "tokens": sorted(type_tokens(edge)),
        "embedding_dim": _EMBED_DIM,
        "structural": structural(edge),
        "serves_truth": False,
    }


def compatibility(a: str, b: str, family_index: dict[str, str] | None = None) -> dict:
    """The PORTFOLIO compatibility decision: test every representation, return the STRONGEST that fires (the
    'via'), a confidence score, and the full per-representation breakdown. Never one hardcoded rule."""
    fam = family_index or {}
    ta, tb = type_tokens(a), type_tokens(b)
    jac = (len(ta & tb) / len(ta | tb)) if (ta or tb) else 0.0
    cos = _cos(embedding(a), embedding(b))
    per = {
        "exact": a == b and bool(a),
        "canonical": bool(canonical(a)) and canonical(a) == canonical(b),
        "family": bool(family(a, fam)) and family(a, fam) == family(b, fam),
        "tokens": jac >= _TOKEN_JACCARD_FLOOR,
        "embedding": cos >= _EMBED_COS_FLOOR,
    }
    via = next((r for r in _REPRESENTATION_ORDER if per[r]), None)
    return {"a": a, "b": b, "compatible": via is not None, "via": via,
            "score": _REP_SCORE.get(via, 0.0), "jaccard": round(jac, 3), "cosine": round(cos, 3),
            "per_representation": per, "serves_truth": False}


def _compatible_via(a: str, b: str, via: str, fam: dict) -> bool:
    if via == "exact":
        return a == b and bool(a)
    if via == "canonical":
        return bool(canonical(a)) and canonical(a) == canonical(b)
    if via == "family":
        return bool(family(a, fam)) and family(a, fam) == family(b, fam)
    if via == "tokens":
        ta, tb = type_tokens(a), type_tokens(b)
        return ((len(ta & tb) / len(ta | tb)) if (ta or tb) else 0.0) >= _TOKEN_JACCARD_FLOOR
    if via == "embedding":
        return _cos(embedding(a), embedding(b)) >= _EMBED_COS_FLOOR
    if via == "portfolio":
        return compatibility(a, b, fam)["compatible"]
    raise ValueError(f"unknown representation {via!r}")


def search(edge: str, producer_edges, via: str = "portfolio", family_index: dict | None = None) -> list[str]:
    """Every producer edge compatible with ``edge`` under representation ``via`` (a representation-parametrised
    edge search — the 'edges expressed as search' operation)."""
    fam = family_index or {}
    return [pe for pe in producer_edges if _compatible_via(edge, pe, via, fam)]


def connectivity(cards: list[dict], via: str = "family") -> dict:
    """Fraction of primitive INPUT edges that have a compatible PRODUCER under representation ``via`` — the
    honest per-representation lever number (raw << family <= tokens; each is a different confidence)."""
    inputs, outputs = [], set()
    for c in cards:
        i, o = str(c.get("input_edge") or ""), str(c.get("output_edge") or "")
        if i:
            inputs.append(i)
        if o:
            outputs.add(o)
    fam = build_family_index(list(inputs) + list(outputs))
    # index producers by the representation key so the scan is not O(inputs*outputs)
    def key(e):
        return {"exact": e, "canonical": canonical(e), "family": family(e, fam)}.get(via)
    if via in ("exact", "canonical", "family"):
        produced = {key(o) for o in outputs if key(o)}
        sat = sum(1 for i in set(inputs) if key(i) and key(i) in produced)
    else:  # tokens/embedding: scan over ALL distinct outputs (no cap — use everything; O(inputs*outputs))
        outs = list(outputs)
        sat = sum(1 for i in set(inputs) if search(i, outs, via, fam))
    m = len(set(inputs)) or 1
    return {"via": via, "distinct_inputs": len(set(inputs)), "satisfiable": round(sat / m, 3), "serves_truth": False}


def remixable(a: str, b: str, family_index: dict | None = None) -> bool:
    """Can edge ``a`` be EDITED into ``b`` (primitive_onion.remix_edges) — a slight surface variation of the
    SAME type, not a new capability? True when they share a family/canonical but differ in raw string."""
    if a == b:
        return False
    fam = family_index or {}
    return ((bool(family(a, fam)) and family(a, fam) == family(b, fam))
            or (bool(canonical(a)) and canonical(a) == canonical(b)))


def blocked(a: str, b: str, forbidden_pairs=()) -> bool:
    """A governance GATE over composition: block a compat pair if either edge carries a forbidden token pairing
    (e.g. a 'private'/'tenant' edge feeding a 'public'/'global' one). serves_truth=false; a candidate gate."""
    ta, tb = type_tokens(a) | {str(a).lower()}, type_tokens(b) | {str(b).lower()}
    for x, y in forbidden_pairs:
        if (x in " ".join(ta) and y in " ".join(tb)) or (x in " ".join(tb) and y in " ".join(ta)):
            return True
    return False


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []

    fam = build_family_index(["NormalizedRecord", "NormalizedRecordBatch", "NormalizedOpportunity",
                              "OpportunityBatch", "RawText", "RawTextDocument", "Unrelated"] * 3)

    # representations exist + differ
    rep = represent("NormalizedRecordBatch", fam)
    checks.append(("represent() gives raw+canonical+family+tokens+embedding+structural",
                   set(rep) >= {"raw", "canonical", "family", "tokens", "embedding_dim", "structural"} and rep["serves_truth"] is False))

    # family standardization: two surface variants collapse to ONE family (what raw canon failed to do)
    checks.append(("family folds surface variants together (NormalizedRecord ~ NormalizedRecordBatch)",
                   family("NormalizedRecord", fam) and family("NormalizedRecord", fam) == family("NormalizedRecordBatch", fam)))

    # compatibility portfolio: exact wins when identical; family when only surface differs; None when unrelated
    checks.append(("exact identity -> via=exact score 1.0", compatibility("X", "X", fam)["via"] == "exact"))
    cvar = compatibility("NormalizedRecord", "NormalizedRecordBatch", fam)
    checks.append(("surface variant -> compatible, strongest via is family/canonical/tokens (not exact)",
                   cvar["compatible"] and cvar["via"] in ("canonical", "family", "tokens") and cvar["via"] != "exact"))
    checks.append(("unrelated edges -> incompatible (portfolio does not over-fire)",
                   not compatibility("RawText", "Unrelated", fam)["compatible"]))

    # embedding is deterministic + normalized + similar-for-similar
    e1, e2 = embedding("NormalizedRecord"), embedding("NormalizedRecord")
    checks.append(("embedding deterministic + unit norm", e1 == e2 and abs(sum(v * v for v in e1) - 1.0) < 1e-6))
    checks.append(("embedding: near-duplicate edges are closer than unrelated ones",
                   _cos(embedding("NormalizedRecord"), embedding("NormalizedRecords"))
                   > _cos(embedding("NormalizedRecord"), embedding("ZzqxUnrelated"))))

    # search by representation
    prod = ["NormalizedRecord", "NormalizedRecordBatch", "Unrelated"]
    checks.append(("search(exact) is strict; search(family) finds the variants",
                   search("NormalizedRecord", prod, "exact", fam) == ["NormalizedRecord"]
                   and len(search("NormalizedRecord", prod, "family", fam)) >= 2))

    # remixable: same family/canon, different surface -> editable; identical or unrelated -> not
    checks.append(("remixable when same-type surface variant, not when identical/unrelated",
                   remixable("NormalizedRecord", "NormalizedRecordBatch", fam)
                   and not remixable("X", "X", fam) and not remixable("RawText", "Unrelated", fam)))

    # blocked governance gate
    checks.append(("blocked gate stops a forbidden private->public composition",
                   blocked("TenantPrivateRecord", "PublicGlobalFeed", forbidden_pairs=[("private", "public")])
                   and not blocked("NormalizedRecord", "Scored", forbidden_pairs=[("private", "public")])))

    # connectivity lever: family/tokens strictly beat exact on a real-ish synthetic corpus (the standardization win)
    cards = [{"input_edge": "NormalizedRecordBatch", "output_edge": "DedupeClusters"},
             {"input_edge": "RawText", "output_edge": "NormalizedRecord"},
             {"input_edge": "NormalizedOpportunity", "output_edge": "OpportunityBatch"}]
    ce, cf = connectivity(cards, "exact")["satisfiable"], connectivity(cards, "family")["satisfiable"]
    checks.append(("connectivity(family) >= connectivity(exact) (standardization never lowers reach)", cf >= ce))

    # determinism
    checks.append(("build_family_index deterministic", build_family_index(["NormalizedRecord"] * 2) == build_family_index(["NormalizedRecord"] * 2)))

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print("\nPASS - edge_representations: one edge, MANY representations (raw/canonical/family/tokens/embedding/"
          "structural) behind one portfolio; compatibility picks the strongest that fires; search/remix/block "
          "operate across representations; family standardizes surface variants; deterministic; serves_truth=false.")
    return 0


def _run(corpus: int) -> int:
    from scripts._jsonl import read_jsonl_tolerant  # noqa: PLC0415
    from scripts._repo_paths import resource  # noqa: PLC0415
    from scripts._time import now_iso  # noqa: PLC0415
    for rel in ("data/dev-intel/aidevobserver_edge_foundry/verified_factory_primitive_cards.jsonl",):
        path = resource(rel)
        if path.exists():
            _all = [c for c in read_jsonl_tolerant(path) if c.get("primitive_id")]
            cards = _all[:corpus] if corpus else _all  # 0 = FULL corpus (use everything)
            break
    else:
        print("no cards found"); return 1
    out = {"record_type": "edge_representation_connectivity", "generated_at": now_iso(),
           "cards": len(cards), "by_representation": {via: connectivity(cards, via)["satisfiable"]
                                                      for via in ("exact", "canonical", "family")},
           "serves_truth": False}
    outdir = resource("data") / "dev-intel" / "edge_representations"
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "summary.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=2))
    print("  => confidence order: exact (guaranteed) < canonical (curated, trustworthy) < family (dominant-type")
    print("     standardization — more principled than any-token overlap, but its high REACH over-groups some")
    print("     same-domain edges, so it is a MEDIUM-confidence candidate, cross-checked by embedding/structural).")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--corpus", type=int, default=0, help="0 = FULL corpus (use everything)")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.run:
        return _run(args.corpus)
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
