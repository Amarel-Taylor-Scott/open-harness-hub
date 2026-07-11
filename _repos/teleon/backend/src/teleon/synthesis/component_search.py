"""src.teleon.synthesis.component_search — label every component with text+keywords+vector + SEARCH/COMPOSE over them.

So the synthesizer can FIND components by meaning (not just exact id/plane) and COMPOSE them: search(query) ranks
components by a deterministic lexical VECTOR (char-trigram hash, offline) + keyword overlap; compose(capability) returns
candidate components per ladder rung (feeding the descent/DAG). The index (data/dev-intel/component_search_index.jsonl,
the operational component_search_index stream) is built from ALL registries by _repos/shared-backend-components/scripts/build_component_index.py. The
vector here is a deterministic LEXICAL embedding (real + offline); the learned embedding/vector_store plane swaps in
semantic vectors via the port (the stream is pgvector-ready). serves_truth=false; Teleon layer.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import hashlib
import json
import math
import re
from functools import lru_cache
from pathlib import Path

py_var_src_teleon_synthesis_component_search___REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[3])
py_const_src_teleon_synthesis_component_search__INDEX_PATH = _resource("data") / "dev-intel" / "component_search_index.jsonl"
py_const_src_teleon_synthesis_component_search__INDEX_DIM = 256                       # the search-index's OWN lexical dim (not a learned model's; the port re-embeds for semantic)
py_var_src_teleon_synthesis_component_search___TOK = re.compile(r"[a-z0-9]+")


def py_function_src_teleon_synthesis_component_search__embed(py_arg_src_teleon_synthesis_component_search__embed__text: str) -> list[float]:
    """Deterministic, offline LEXICAL embedding: char-trigrams + tokens hashed into a fixed dim, L2-normalized."""
    py_local_src_teleon_synthesis_component_search__embed__v = [0.0] * py_const_src_teleon_synthesis_component_search__INDEX_DIM
    py_local_src_teleon_synthesis_component_search__embed__t = (py_arg_src_teleon_synthesis_component_search__embed__text or "").lower()
    py_local_src_teleon_synthesis_component_search__embed__grams = [py_local_src_teleon_synthesis_component_search__embed__t[i:i + 3] for i in range(max(0, len(py_local_src_teleon_synthesis_component_search__embed__t) - 2))] + py_var_src_teleon_synthesis_component_search___TOK.findall(py_local_src_teleon_synthesis_component_search__embed__t)
    for py_local_src_teleon_synthesis_component_search__embed__g in py_local_src_teleon_synthesis_component_search__embed__grams:
        py_local_src_teleon_synthesis_component_search__embed__h = int(hashlib.md5(py_local_src_teleon_synthesis_component_search__embed__g.encode()).hexdigest(), 16)
        py_local_src_teleon_synthesis_component_search__embed__v[py_local_src_teleon_synthesis_component_search__embed__h % py_const_src_teleon_synthesis_component_search__INDEX_DIM] += 1.0 if (py_local_src_teleon_synthesis_component_search__embed__h >> 8) & 1 else -1.0      # signed hashing (reduces collisions)
    py_local_src_teleon_synthesis_component_search__embed__norm = math.sqrt(sum(x * x for x in py_local_src_teleon_synthesis_component_search__embed__v)) or 1.0
    return [x / py_local_src_teleon_synthesis_component_search__embed__norm for x in py_local_src_teleon_synthesis_component_search__embed__v]


def py_function_src_teleon_synthesis_component_search__index_entry(py_arg_src_teleon_synthesis_component_search__index_entry__id: str, py_arg_src_teleon_synthesis_component_search__index_entry__kind: str, py_arg_src_teleon_synthesis_component_search__index_entry__text: str, py_arg_src_teleon_synthesis_component_search__index_entry__keywords: list[str]) -> dict:
    py_local_src_teleon_synthesis_component_search__index_entry__kw = sorted({k for k in py_arg_src_teleon_synthesis_component_search__index_entry__keywords if k})
    return {"id": py_arg_src_teleon_synthesis_component_search__index_entry__id, "kind": py_arg_src_teleon_synthesis_component_search__index_entry__kind, "text": py_arg_src_teleon_synthesis_component_search__index_entry__text, "keywords": py_local_src_teleon_synthesis_component_search__index_entry__kw,
            "vector": py_function_src_teleon_synthesis_component_search__embed(py_arg_src_teleon_synthesis_component_search__index_entry__text + " " + " ".join(py_local_src_teleon_synthesis_component_search__index_entry__kw)), "serves_truth": False}


def py_function_src_teleon_synthesis_component_search___cos(py_arg_src_teleon_synthesis_component_search__cos__a: list[float], py_arg_src_teleon_synthesis_component_search__cos__b: list[float]) -> float:
    return sum(x * y for x, y in zip(py_arg_src_teleon_synthesis_component_search__cos__a, py_arg_src_teleon_synthesis_component_search__cos__b))            # both are unit vectors


@lru_cache(maxsize=1)
def py_function_src_teleon_synthesis_component_search__load_index() -> tuple:
    if not py_const_src_teleon_synthesis_component_search__INDEX_PATH.exists():
        return ()
    py_local_src_teleon_synthesis_component_search__load_index__rows = []
    for py_local_src_teleon_synthesis_component_search__load_index__line in py_const_src_teleon_synthesis_component_search__INDEX_PATH.read_text(encoding="utf-8").splitlines():
        if not py_local_src_teleon_synthesis_component_search__load_index__line.strip():
            continue
        try:
            py_local_src_teleon_synthesis_component_search__load_index__rows.append(json.loads(py_local_src_teleon_synthesis_component_search__load_index__line))
        except ValueError:
            continue  # tolerate a torn index line — one bad row must never break ALL component search
    return tuple(py_local_src_teleon_synthesis_component_search__load_index__rows)


def py_function_src_teleon_synthesis_component_search__search(py_arg_src_teleon_synthesis_component_search__search__query: str, *, k: int = 10, index=None, kind: str | None = None) -> list[dict]:
    """Rank components by lexical-vector cosine + a keyword-overlap boost. Returns top-k {id, kind, score, keywords}."""
    py_local_src_teleon_synthesis_component_search__search__idx = index if index is not None else py_function_src_teleon_synthesis_component_search__load_index()
    py_local_src_teleon_synthesis_component_search__search__qv, py_local_src_teleon_synthesis_component_search__search__qtok = py_function_src_teleon_synthesis_component_search__embed(py_arg_src_teleon_synthesis_component_search__search__query), set(py_var_src_teleon_synthesis_component_search___TOK.findall(py_arg_src_teleon_synthesis_component_search__search__query.lower()))
    py_local_src_teleon_synthesis_component_search__search__out = []
    for py_local_src_teleon_synthesis_component_search__search__e in py_local_src_teleon_synthesis_component_search__search__idx:
        if kind and py_local_src_teleon_synthesis_component_search__search__e["kind"] != kind:
            continue
        py_local_src_teleon_synthesis_component_search__search__boost = 0.15 * len(py_local_src_teleon_synthesis_component_search__search__qtok & set(" ".join(py_local_src_teleon_synthesis_component_search__search__e["keywords"]).lower().split()))
        py_local_src_teleon_synthesis_component_search__search__out.append({"id": py_local_src_teleon_synthesis_component_search__search__e["id"], "kind": py_local_src_teleon_synthesis_component_search__search__e["kind"], "score": round(py_function_src_teleon_synthesis_component_search___cos(py_local_src_teleon_synthesis_component_search__search__qv, py_local_src_teleon_synthesis_component_search__search__e["vector"]) + py_local_src_teleon_synthesis_component_search__search__boost, 4), "keywords": py_local_src_teleon_synthesis_component_search__search__e["keywords"]})
    return sorted(py_local_src_teleon_synthesis_component_search__search__out, key=lambda py_arg_src_teleon_synthesis_component_search__search__r: py_arg_src_teleon_synthesis_component_search__search__r["score"], reverse=True)[:k]


def py_function_src_teleon_synthesis_component_search__compose(py_arg_src_teleon_synthesis_component_search__compose__capability: str, *, k: int = 5, index=None) -> dict:
    """COMPOSE: for a capability's ladder rungs, search the index for candidate components per rung (by the rung's plane +
    its method text). Returns {rung_tier: [candidate component ids]} — the search-driven option set the synthesizer branches over."""
    py_local_src_teleon_synthesis_component_search__compose__lad = next((l for l in json.loads((_resource("architecture") / "capability_ladders.json").read_text())["ladders"]
                if l["capability"] == py_arg_src_teleon_synthesis_component_search__compose__capability), None)
    if not py_local_src_teleon_synthesis_component_search__compose__lad:
        return {}
    py_local_src_teleon_synthesis_component_search__compose__idx = index if index is not None else py_function_src_teleon_synthesis_component_search__load_index()
    py_local_src_teleon_synthesis_component_search__compose__out = {}
    for py_arg_src_teleon_synthesis_component_search__compose__r in sorted(py_local_src_teleon_synthesis_component_search__compose__lad["rungs"], key=lambda py_arg_src_teleon_synthesis_component_search__compose__r: py_arg_src_teleon_synthesis_component_search__compose__r["cost_rank"]):
        py_local_src_teleon_synthesis_component_search__compose__plane = (py_arg_src_teleon_synthesis_component_search__compose__r.get("planes") or [""])[0]
        py_local_src_teleon_synthesis_component_search__compose__hits = py_function_src_teleon_synthesis_component_search__search(f"{py_arg_src_teleon_synthesis_component_search__compose__r['tier']} {py_arg_src_teleon_synthesis_component_search__compose__r['method']} {py_local_src_teleon_synthesis_component_search__compose__plane}", k=k, index=py_local_src_teleon_synthesis_component_search__compose__idx)
        py_local_src_teleon_synthesis_component_search__compose__out[py_arg_src_teleon_synthesis_component_search__compose__r["tier"]] = [h["id"] for h in py_local_src_teleon_synthesis_component_search__compose__hits]
    return py_local_src_teleon_synthesis_component_search__compose__out
