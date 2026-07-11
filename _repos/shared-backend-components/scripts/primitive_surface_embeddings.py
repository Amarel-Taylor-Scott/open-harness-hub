#!/usr/bin/env python3
"""primitive_surface_embeddings — embed MANY SURFACES per primitive (code + descriptions + components) with
SPECIALIZED models, kept in separate named spaces.

Owner (2026-07-10): "embed the code and the descriptions, and description components, inputs and outputs, code
portions, etc" + "other specialized embedding models". A primitive is not one text — it has many SURFACES, and each
is best embedded by a DIFFERENT model: CODE surfaces by a code-specialized encoder (jina-code / CodeBERT / GraphCode
BERT), TEXT surfaces by strong text encoders (BGE-large / EmbeddingGemma / GTE / nomic). This module defines the
surface registry + routes each surface to its model kind, producing a multi-surface × multi-model representation you
can search by CODE-similarity OR input-similarity OR problem-similarity independently, then fuse.

This is §2A×§2B of docs/FABLE-5-SEMANTIC-LINKER-100M-HANDOFF.md made runnable. Surfaces + model routing are zoos
(add a surface / a model = one row). Reuses `embedder_zoo` for the model portfolio (incl. the advanced models added
2026-07-10). serves_truth=false — a candidate representation, raced by receipt to decide what to serve.

    PYTHONPATH=. python3 scripts/primitive_surface_embeddings.py --self-test
    PYTHONPATH=. python3 scripts/primitive_surface_embeddings.py --surfaces   # the surface x model-kind registry
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Callable, Optional

_HERE = Path(__file__).resolve()
_REPO = _HERE.parent.parent
for _p in (str(_REPO), str(_REPO / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)


def _words(s: object) -> str:
    s = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", str(s or ""))
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def _code_of(card: dict[str, Any]) -> str:
    return str(card.get("code") or card.get("source_code") or card.get("body") or "")


def _code_signature(card: dict[str, Any]) -> str:
    code = _code_of(card)
    for line in code.splitlines():
        if line.strip().startswith("def "):
            return line.strip()
    return ""


def _code_portions(card: dict[str, Any]) -> str:
    """The identifier/keyword skeleton of the body (calls + names) — a coarse code-structure surface."""
    code = _code_of(card)
    ids = re.findall(r"[A-Za-z_][A-Za-z0-9_]*", code)
    kw = {"def", "return", "for", "if", "in", "self", "x", "np", "import"}
    return " ".join(i for i in ids if i not in kw)[:400]


#: SURFACES — name -> {extract(card)->str, kind}. kind routes to a model portfolio ('code' vs 'text'). Add-a-row.
SURFACES: dict[str, dict[str, Any]] = {
    "code": {"extract": _code_of, "kind": "code"},
    "code_signature": {"extract": _code_signature, "kind": "code"},
    "code_portions": {"extract": _code_portions, "kind": "code"},
    "title": {"extract": lambda c: str(c.get("title") or ""), "kind": "text"},
    "blackbox": {"extract": lambda c: str(c.get("blackbox") or ""), "kind": "text"},
    "input": {"extract": lambda c: _words(c.get("input_edge")), "kind": "text"},
    "output": {"extract": lambda c: _words(c.get("output_edge")), "kind": "text"},
    "input_output_combined": {"extract": lambda c: f"{_words(c.get('input_edge'))} to {_words(c.get('output_edge'))}", "kind": "text"},
    "problem": {"extract": lambda c: f"how to {_words(c.get('title'))} producing {_words(c.get('output_edge'))}", "kind": "text"},
    "keywords": {"extract": lambda c: " ".join(str(t) for t in (c.get("capability_tags") or [])), "kind": "text"},
}

#: default MODEL per kind (the SPECIALIZED routing). Overridable — the point is code!=text models. The self-test
#: uses the always-available proxy so it runs offline; real serving uses jina-code for code + BGE/Gemma for text.
DEFAULT_MODELS: dict[str, str] = {"code": "fastembed_jina_code", "text": "fastembed_bge_large"}
#: candidate advanced models per kind (the portfolio to RACE — 5+ per surface, kept in separate spaces).
MODEL_PORTFOLIO: dict[str, list[str]] = {
    "code": ["fastembed_jina_code", "model2vec_potion_8m", "proxy_crc32"],
    "text": ["fastembed_bge_large", "fastembed_gte_large", "fastembed_mxbai_large",
             "ollama_embeddinggemma", "ollama_nomic", "model2vec_potion_8m", "proxy_crc32"],
}


def extract_surfaces(card: dict[str, Any]) -> dict[str, str]:
    """Every non-empty surface text for a primitive."""
    out: dict[str, str] = {}
    for name, spec in SURFACES.items():
        try:
            t = str(spec["extract"](card) or "").strip()
        except Exception:  # noqa: BLE001
            t = ""
        if t:
            out[name] = t
    return out


def embed_surfaces(card: dict[str, Any], *, models: Optional[dict[str, str]] = None,
                   embed: Optional[Callable[[str, str], list[float]]] = None) -> dict[str, dict[str, Any]]:
    """Embed each surface with its KIND's model. Returns {surface: {model, kind, vector}}. `embed(text, backend)`
    defaults to embedder_zoo.embed; inject a stub for offline tests."""
    models = models or DEFAULT_MODELS
    if embed is None:
        from scripts import embedder_zoo as _z  # noqa: PLC0415
        embed = _z.embed
    out: dict[str, dict[str, Any]] = {}
    for name, text in extract_surfaces(card).items():
        kind = SURFACES[name]["kind"]
        model = models.get(kind, "proxy_crc32")
        try:
            vec = embed(text, model)
        except Exception:  # noqa: BLE001 — a model fault degrades that surface, never the whole primitive
            vec = None
        out[name] = {"model": model, "kind": kind, "vector": vec, "dim": len(vec) if vec else 0}
    return out


def summary() -> dict[str, Any]:
    kinds = {s["kind"] for s in SURFACES.values()}
    return {"surfaces": len(SURFACES), "surface_names": list(SURFACES),
            "kinds": sorted(kinds), "code_surfaces": [n for n, s in SURFACES.items() if s["kind"] == "code"],
            "text_surfaces": [n for n, s in SURFACES.items() if s["kind"] == "text"],
            "model_portfolio": MODEL_PORTFOLIO}


# ================================================================================================================
# Surface x model RACE (which surface + which model retrieves best — the receipt that decides what to serve)
# ================================================================================================================
def race_surface_model(cards, labelled, *, embed, models_by_kind) -> dict[str, Any]:
    """For each (surface, model), embed that surface for every card + each query, rank by cosine, report MRR. Shows
    which surface+model pairs carry retrieval signal (e.g. code-model on the code surface for a code query)."""
    import numpy as np  # noqa: PLC0415

    def _emb(t, m):
        v = embed(t, m)
        a = np.asarray(v, float)
        n = np.linalg.norm(a) or 1.0
        return a / n

    grid: dict[str, dict[str, float]] = {}
    for sname, spec in SURFACES.items():
        for model in models_by_kind.get(spec["kind"], []):
            texts, ids = [], []
            for c in cards:
                t = str(spec["extract"](c) or "").strip()
                if t:
                    texts.append(t)
                    ids.append(c.get("primitive_id"))
            if not texts:
                continue
            M = np.stack([_emb(t, model) for t in texts])
            mrr = 0.0
            for q, rel in labelled:
                qv = _emb(q, model)
                order = np.argsort(-(M @ qv))
                ranked = [ids[int(i)] for i in order[:10]]
                hit = next((r for r, pid in enumerate(ranked) if pid in rel), None)
                mrr += 1.0 / (hit + 1) if hit is not None else 0.0
            grid.setdefault(sname, {})[model] = round(mrr / len(labelled), 4) if labelled else 0.0
    # best (surface, model)
    best = None
    for s, mm in grid.items():
        for m, v in mm.items():
            if best is None or v > best["mrr"]:
                best = {"surface": s, "model": m, "mrr": v}
    return {"grid": grid, "best": best, "candidate": True, "serves_truth": False}


# ================================================================================================================
# Self-test (offline — proxy embedder for both kinds so no model download)
# ================================================================================================================
def _fixture():
    return [
        {"primitive_id": "p:count", "title": "Count Items", "blackbox": "Counts the items in a list.",
         "input_edge": "ItemList", "output_edge": "ItemCount", "capability_tags": ["count"],
         "code": "def run(x):\n    return len(x)\n"},
        {"primitive_id": "p:sort", "title": "Sort Numbers", "blackbox": "Sorts numbers ascending.",
         "input_edge": "NumberList", "output_edge": "SortedNumberList", "capability_tags": ["sort"],
         "code": "def run(x):\n    return sorted(x)\n"},
        {"primitive_id": "p:unique", "title": "Unique Values", "blackbox": "Returns distinct values preserving order.",
         "input_edge": "ValueList", "output_edge": "UniqueValueList", "capability_tags": ["unique"],
         "code": "def run(x):\n    seen=set()\n    return [v for v in x if not (v in seen or seen.add(v))]\n"},
    ]


def _self_test() -> int:
    checks: list[tuple[str, bool, str]] = []
    cards = _fixture()

    # (1) surfaces extract, including CODE surfaces distinct from TEXT surfaces.
    surf = extract_surfaces(cards[0])
    s = summary()
    checks.append((f"extracts {len(surf)} surfaces incl. code ({s['code_surfaces']})",
                   "code" in surf and "code_signature" in surf and "input" in surf and "problem" in surf
                   and len(s["code_surfaces"]) >= 2, json.dumps(sorted(surf))))

    # (2) each surface routes to its KIND's model (code->code model, text->text model).
    stub = lambda t, m: [float(len(t) % 7), float(hash((t, m)) % 5), 1.0]  # deterministic-ish offline stub
    embs = embed_surfaces(cards[0], models={"code": "CODEMODEL", "text": "TEXTMODEL"}, embed=stub)
    checks.append(("code surface embedded by CODE model, text surface by TEXT model",
                   embs["code"]["model"] == "CODEMODEL" and embs["input"]["model"] == "TEXTMODEL"
                   and embs["code"]["kind"] == "code", f"code->{embs['code']['model']} input->{embs['input']['model']}"))

    # (3) RACE runs over surface x model and yields a best (surface, model). Use the proxy embedder (offline).
    from scripts import embedder_zoo as _z
    labelled = [("count the items in a list", {"p:count"}), ("sort the numbers", {"p:sort"}),
                ("distinct values", {"p:unique"})]
    rec = race_surface_model(cards, labelled, embed=lambda t, m: _z.embed(t, "proxy_crc32"),
                             models_by_kind={"code": ["proxy_crc32"], "text": ["proxy_crc32"]})
    checks.append((f"surface x model race yields a best pair ({rec['best']})",
                   rec["best"] is not None and rec["best"]["mrr"] > 0
                   and "title" in rec["grid"], json.dumps(rec["best"])))

    # (4) FLEXIBILITY: add a surface row -> extraction grows.
    SURFACES["_probe"] = {"extract": lambda c: "probe", "kind": "text"}
    try:
        grew = "_probe" in extract_surfaces(cards[0])
    finally:
        del SURFACES["_probe"]
    checks.append(("flexibility: add-a-surface grows extraction", grew, ""))

    # (5) DETERMINISM.
    checks.append(("extraction deterministic", extract_surfaces(cards[0]) == surf, ""))

    ok = all(c[1] for c in checks)
    print(f"{'PASS' if ok else 'FAIL'} - primitive_surface_embeddings: {len(SURFACES)} surfaces "
          f"({len(s['code_surfaces'])} code + {len(s['text_surfaces'])} text) x specialized model portfolio "
          f"(code!=text models), surface x model race. serves_truth=false")
    for name, passed, detail in checks:
        print(f"  [{'ok' if passed else 'XX'}] {name}" + (f"  ({detail})" if not passed else ""))
    return 0 if ok else 1


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Embed many surfaces (code + descriptions + components) with specialized models.")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--surfaces", action="store_true", help="print the surface x model-kind registry")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.surfaces:
        print(json.dumps(summary(), indent=2))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
