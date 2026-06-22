"""src.teleon.synthesis.component_search — label every component with text+keywords+vector + SEARCH/COMPOSE over them.

So the synthesizer can FIND components by meaning (not just exact id/plane) and COMPOSE them: search(query) ranks
components by a deterministic lexical VECTOR (char-trigram hash, offline) + keyword overlap; compose(capability) returns
candidate components per ladder rung (feeding the descent/DAG). The index (data/dev-intel/component_search_index.jsonl,
the operational component_search_index stream) is built from ALL registries by scripts/build_component_index.py. The
vector here is a deterministic LEXICAL embedding (real + offline); the learned embedding/vector_store plane swaps in
semantic vectors via the port (the stream is pgvector-ready). serves_truth=false; Teleon layer.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from functools import lru_cache
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
INDEX_PATH = _REPO / "data" / "dev-intel" / "component_search_index.jsonl"
INDEX_DIM = 256                       # the search-index's OWN lexical dim (not a learned model's; the port re-embeds for semantic)
_TOK = re.compile(r"[a-z0-9]+")


def embed(text: str) -> list[float]:
    """Deterministic, offline LEXICAL embedding: char-trigrams + tokens hashed into a fixed dim, L2-normalized."""
    v = [0.0] * INDEX_DIM
    t = (text or "").lower()
    grams = [t[i:i + 3] for i in range(max(0, len(t) - 2))] + _TOK.findall(t)
    for g in grams:
        h = int(hashlib.md5(g.encode()).hexdigest(), 16)
        v[h % INDEX_DIM] += 1.0 if (h >> 8) & 1 else -1.0      # signed hashing (reduces collisions)
    norm = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / norm for x in v]


def index_entry(id: str, kind: str, text: str, keywords: list[str]) -> dict:
    kw = sorted({k for k in keywords if k})
    return {"id": id, "kind": kind, "text": text, "keywords": kw,
            "vector": embed(text + " " + " ".join(kw)), "serves_truth": False}


def _cos(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))            # both are unit vectors


@lru_cache(maxsize=1)
def load_index() -> tuple:
    if not INDEX_PATH.exists():
        return ()
    return tuple(json.loads(l) for l in INDEX_PATH.read_text(encoding="utf-8").splitlines() if l.strip())


def search(query: str, *, k: int = 10, index=None, kind: str | None = None) -> list[dict]:
    """Rank components by lexical-vector cosine + a keyword-overlap boost. Returns top-k {id, kind, score, keywords}."""
    idx = index if index is not None else load_index()
    qv, qtok = embed(query), set(_TOK.findall(query.lower()))
    out = []
    for e in idx:
        if kind and e["kind"] != kind:
            continue
        boost = 0.15 * len(qtok & set(" ".join(e["keywords"]).lower().split()))
        out.append({"id": e["id"], "kind": e["kind"], "score": round(_cos(qv, e["vector"]) + boost, 4), "keywords": e["keywords"]})
    return sorted(out, key=lambda r: r["score"], reverse=True)[:k]


def compose(capability: str, *, k: int = 5, index=None) -> dict:
    """COMPOSE: for a capability's ladder rungs, search the index for candidate components per rung (by the rung's plane +
    its method text). Returns {rung_tier: [candidate component ids]} — the search-driven option set the synthesizer branches over."""
    lad = next((l for l in json.loads((_REPO / "architecture" / "capability_ladders.json").read_text())["ladders"]
                if l["capability"] == capability), None)
    if not lad:
        return {}
    idx = index if index is not None else load_index()
    out = {}
    for r in sorted(lad["rungs"], key=lambda r: r["cost_rank"]):
        plane = (r.get("planes") or [""])[0]
        hits = search(f"{r['tier']} {r['method']} {plane}", k=k, index=idx)
        out[r["tier"]] = [h["id"] for h in hits]
    return out
