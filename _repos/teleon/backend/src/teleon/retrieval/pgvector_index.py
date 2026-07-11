#!/usr/bin/env python3
"""src.teleon.retrieval.pgvector_index — HYBRID vector index: a pgvector (Postgres) backend with an HONEST in-memory fallback.

Upgrade #16. Each doc is stored with a LEARNED semantic vector (learned_vectors.LearnedVectorPort) PLUS explicit
`use_cases` and `labels` columns, and ranked by a HYBRID score = lexical(name/text) + vector(semantic) + use_cases +
labels. The column model + weights are REUSED from _repos/shared-backend-components/scripts/hybrid_search.py (single source — no magic weights), and the
vector column type comes from scripts._config.pgvector_type(dim) (never a literal dim). The store is Postgres+pgvector
when psycopg + the pgvector adapter + a DSN (scripts._config.DEFAULT_DATABASE_URL_ENV) are present; otherwise it
HONESTLY falls back to an in-memory cosine index so it always runs offline. Sits BEHIND the existing ports; modifies no
existing file. serves_truth=false (it RANKS candidates, it does not verify them); Teleon layer.

  --self-test
"""
from __future__ import annotations

import importlib.util
import math
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

py_var_src_teleon_retrieval_pgvector_index___REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[3])
if str(py_var_src_teleon_retrieval_pgvector_index___REPO) not in sys.path:                       # sys.path insert so a direct `python3 .../pgvector_index.py` run works
    sys.path.insert(0, str(py_var_src_teleon_retrieval_pgvector_index___REPO))

from scripts._config import DEFAULT_DATABASE_URL_ENV, DEFAULT_VECTOR_SIMILARITY, pgvector_type
from scripts.hybrid_search import WEIGHTS, _toks            # match the column model + weights (single source, no magic values)
from src.teleon.retrieval.learned_vectors import py_class_src_teleon_retrieval_learned_vectors__LearnedVectorPort

py_const_src_teleon_retrieval_pgvector_index__SERVES_TRUTH = False
py_const_src_teleon_retrieval_pgvector_index__PG_BACKEND = "postgres_pgvector"
py_const_src_teleon_retrieval_pgvector_index__MEM_BACKEND = "in_memory"
py_var_src_teleon_retrieval_pgvector_index___TABLE = "retrieval_hybrid_doc"
#: the VECTOR signal's weight — reuse a canonical column weight rather than invent a new magic number.
py_const_src_teleon_retrieval_pgvector_index__VECTOR_WEIGHT = WEIGHTS["tags"]
#: pgvector distance operators by similarity name (cosine is the repo default DEFAULT_VECTOR_SIMILARITY).
py_var_src_teleon_retrieval_pgvector_index___SIM_OP = {"cosine": "<=>", "l2": "<->", "inner_product": "<#>"}
py_var_src_teleon_retrieval_pgvector_index___PG_CONNECT_TIMEOUT_S = 3
py_var_src_teleon_retrieval_pgvector_index___RECALL_FACTOR = 5                                          # over-fetch factor for vector recall before the hybrid re-rank


def py_function_src_teleon_retrieval_pgvector_index___as_text(py_arg_src_teleon_retrieval_pgvector_index__py_function_src_teleon_retrieval_pgvector_index__as_text__v) -> str:
    return " ".join(str(x) for x in py_arg_src_teleon_retrieval_pgvector_index__py_function_src_teleon_retrieval_pgvector_index__as_text__v) if isinstance(py_arg_src_teleon_retrieval_pgvector_index__py_function_src_teleon_retrieval_pgvector_index__as_text__v, (list, tuple)) else str(py_arg_src_teleon_retrieval_pgvector_index__py_function_src_teleon_retrieval_pgvector_index__as_text__v or "")


def py_function_src_teleon_retrieval_pgvector_index___cosine(py_arg_src_teleon_retrieval_pgvector_index__py_function_src_teleon_retrieval_pgvector_index__cosine__a, py_arg_src_teleon_retrieval_pgvector_index__py_function_src_teleon_retrieval_pgvector_index__cosine__b) -> float:
    if not py_arg_src_teleon_retrieval_pgvector_index__py_function_src_teleon_retrieval_pgvector_index__cosine__a or not py_arg_src_teleon_retrieval_pgvector_index__py_function_src_teleon_retrieval_pgvector_index__cosine__b or len(py_arg_src_teleon_retrieval_pgvector_index__py_function_src_teleon_retrieval_pgvector_index__cosine__a) != len(py_arg_src_teleon_retrieval_pgvector_index__py_function_src_teleon_retrieval_pgvector_index__cosine__b):
        return 0.0
    py_local_src_teleon_retrieval_pgvector_index__cosine__dot = sum(x * y for x, y in zip(py_arg_src_teleon_retrieval_pgvector_index__py_function_src_teleon_retrieval_pgvector_index__cosine__a, py_arg_src_teleon_retrieval_pgvector_index__py_function_src_teleon_retrieval_pgvector_index__cosine__b))
    py_local_src_teleon_retrieval_pgvector_index__cosine__na = math.sqrt(sum(x * x for x in py_arg_src_teleon_retrieval_pgvector_index__py_function_src_teleon_retrieval_pgvector_index__cosine__a))
    py_local_src_teleon_retrieval_pgvector_index__cosine__nb = math.sqrt(sum(y * y for y in py_arg_src_teleon_retrieval_pgvector_index__py_function_src_teleon_retrieval_pgvector_index__cosine__b))
    return py_local_src_teleon_retrieval_pgvector_index__cosine__dot / (py_local_src_teleon_retrieval_pgvector_index__cosine__na * py_local_src_teleon_retrieval_pgvector_index__cosine__nb) if py_local_src_teleon_retrieval_pgvector_index__cosine__na and py_local_src_teleon_retrieval_pgvector_index__cosine__nb else 0.0


def py_function_src_teleon_retrieval_pgvector_index___overlap(py_arg_src_teleon_retrieval_pgvector_index__py_function_src_teleon_retrieval_pgvector_index__overlap__q_toks: set, py_arg_src_teleon_retrieval_pgvector_index__py_function_src_teleon_retrieval_pgvector_index__overlap__text: str) -> float:
    return (len(py_arg_src_teleon_retrieval_pgvector_index__py_function_src_teleon_retrieval_pgvector_index__overlap__q_toks & set(_toks(py_arg_src_teleon_retrieval_pgvector_index__py_function_src_teleon_retrieval_pgvector_index__overlap__text))) / len(py_arg_src_teleon_retrieval_pgvector_index__py_function_src_teleon_retrieval_pgvector_index__overlap__q_toks)) if py_arg_src_teleon_retrieval_pgvector_index__py_function_src_teleon_retrieval_pgvector_index__overlap__q_toks else 0.0


@dataclass
class py_class_src_teleon_retrieval_pgvector_index__Doc:
    id: str
    text: str = ""
    use_cases: str = ""
    labels: str = ""
    vector: list = field(default_factory=list)


def py_function_src_teleon_retrieval_pgvector_index___score(py_arg_src_teleon_retrieval_pgvector_index__py_function_src_teleon_retrieval_pgvector_index__score__query: str, py_arg_src_teleon_retrieval_pgvector_index__py_function_src_teleon_retrieval_pgvector_index__score__qv: list, py_arg_src_teleon_retrieval_pgvector_index__py_function_src_teleon_retrieval_pgvector_index__score__doc: py_class_src_teleon_retrieval_pgvector_index__Doc) -> tuple:
    """HYBRID: weighted sum of vector cosine + per-column lexical overlap (name/text, use_cases, labels)."""
    py_local_src_teleon_retrieval_pgvector_index__score__qt = set(_toks(py_arg_src_teleon_retrieval_pgvector_index__py_function_src_teleon_retrieval_pgvector_index__score__query))
    py_local_src_teleon_retrieval_pgvector_index__score__parts = {
        "vector": py_const_src_teleon_retrieval_pgvector_index__VECTOR_WEIGHT * max(0.0, py_function_src_teleon_retrieval_pgvector_index___cosine(py_arg_src_teleon_retrieval_pgvector_index__py_function_src_teleon_retrieval_pgvector_index__score__qv, py_arg_src_teleon_retrieval_pgvector_index__py_function_src_teleon_retrieval_pgvector_index__score__doc.vector)),     # semantic (learned, or lexical floor honestly)
        "name": WEIGHTS["name"] * py_function_src_teleon_retrieval_pgvector_index___overlap(py_local_src_teleon_retrieval_pgvector_index__score__qt, py_arg_src_teleon_retrieval_pgvector_index__py_function_src_teleon_retrieval_pgvector_index__score__doc.text),
        "use_cases": WEIGHTS["use_cases"] * py_function_src_teleon_retrieval_pgvector_index___overlap(py_local_src_teleon_retrieval_pgvector_index__score__qt, py_arg_src_teleon_retrieval_pgvector_index__py_function_src_teleon_retrieval_pgvector_index__score__doc.use_cases),  # explicit use_cases column, weighted
        "labels": WEIGHTS["labels"] * py_function_src_teleon_retrieval_pgvector_index___overlap(py_local_src_teleon_retrieval_pgvector_index__score__qt, py_arg_src_teleon_retrieval_pgvector_index__py_function_src_teleon_retrieval_pgvector_index__score__doc.labels),          # explicit labels column, weighted
    }
    py_local_src_teleon_retrieval_pgvector_index__score__total = sum(py_local_src_teleon_retrieval_pgvector_index__score__parts.values())
    return py_local_src_teleon_retrieval_pgvector_index__score__total, {k: round(v, 4) for k, v in py_local_src_teleon_retrieval_pgvector_index__score__parts.items() if v > 0}


class py_class_src_teleon_retrieval_pgvector_index___MemBackend:
    """Always-available in-memory cosine index — the HONEST offline fallback when pgvector isn't reachable."""
    backend = py_const_src_teleon_retrieval_pgvector_index__MEM_BACKEND

    def __init__(self, dim: int):
        self.dim = dim
        self._docs: dict[str, py_class_src_teleon_retrieval_pgvector_index__Doc] = {}

    def upsert(self, py_arg_src_teleon_retrieval_pgvector_index__py_class_src_teleon_retrieval_pgvector_index__MemBackend_upsert__doc: py_class_src_teleon_retrieval_pgvector_index__Doc) -> None:
        self._docs[py_arg_src_teleon_retrieval_pgvector_index__py_class_src_teleon_retrieval_pgvector_index__MemBackend_upsert__doc.id] = py_arg_src_teleon_retrieval_pgvector_index__py_class_src_teleon_retrieval_pgvector_index__MemBackend_upsert__doc

    def candidates(self, py_arg_src_teleon_retrieval_pgvector_index__py_class_src_teleon_retrieval_pgvector_index__MemBackend_candidates__qv, py_arg_src_teleon_retrieval_pgvector_index__py_class_src_teleon_retrieval_pgvector_index__MemBackend_candidates__k):
        return list(self._docs.values())               # small index: hybrid-rank them all

    def count(self) -> int:
        return len(self._docs)

    def close(self) -> None:
        self._docs.clear()


class py_class_src_teleon_retrieval_pgvector_index___PgBackend:
    """Postgres+pgvector store. Real, but engaged only when psycopg + the pgvector adapter + a reachable DSN exist; any
    failure in __init__ propagates so the resolver HONESTLY falls back to the in-memory index. Vector recall in SQL
    (ANN by the cosine operator), then the SAME Python hybrid re-rank over the over-fetched candidates."""
    backend = py_const_src_teleon_retrieval_pgvector_index__PG_BACKEND

    def __init__(self, dsn: str, dim: int):
        import psycopg
        from pgvector.psycopg import register_vector
        self.dim = dim
        self._conn = psycopg.connect(dsn, connect_timeout=py_var_src_teleon_retrieval_pgvector_index___PG_CONNECT_TIMEOUT_S, autocommit=True)
        self._conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
        register_vector(self._conn)
        self._conn.execute(
            f"CREATE TABLE IF NOT EXISTS {py_var_src_teleon_retrieval_pgvector_index___TABLE} (id text PRIMARY KEY, text text, use_cases text, labels text, "
            f"embedding {pgvector_type(dim)})")            # column type from _config.pgvector_type — never a literal dim

    def upsert(self, py_arg_src_teleon_retrieval_pgvector_index__py_class_src_teleon_retrieval_pgvector_index__PgBackend_upsert__doc: py_class_src_teleon_retrieval_pgvector_index__Doc) -> None:
        self._conn.execute(
            f"INSERT INTO {py_var_src_teleon_retrieval_pgvector_index___TABLE} (id, text, use_cases, labels, embedding) VALUES (%s, %s, %s, %s, %s) "
            f"ON CONFLICT (id) DO UPDATE SET text=EXCLUDED.text, use_cases=EXCLUDED.use_cases, "
            f"labels=EXCLUDED.labels, embedding=EXCLUDED.embedding",
            (py_arg_src_teleon_retrieval_pgvector_index__py_class_src_teleon_retrieval_pgvector_index__PgBackend_upsert__doc.id, py_arg_src_teleon_retrieval_pgvector_index__py_class_src_teleon_retrieval_pgvector_index__PgBackend_upsert__doc.text, py_arg_src_teleon_retrieval_pgvector_index__py_class_src_teleon_retrieval_pgvector_index__PgBackend_upsert__doc.use_cases, py_arg_src_teleon_retrieval_pgvector_index__py_class_src_teleon_retrieval_pgvector_index__PgBackend_upsert__doc.labels, py_arg_src_teleon_retrieval_pgvector_index__py_class_src_teleon_retrieval_pgvector_index__PgBackend_upsert__doc.vector))

    def candidates(self, py_arg_src_teleon_retrieval_pgvector_index__py_class_src_teleon_retrieval_pgvector_index__PgBackend_candidates__qv, py_arg_src_teleon_retrieval_pgvector_index__py_class_src_teleon_retrieval_pgvector_index__PgBackend_candidates__k):
        py_local_src_teleon_retrieval_pgvector_index__PgBackend_candidates__op = py_var_src_teleon_retrieval_pgvector_index___SIM_OP.get(DEFAULT_VECTOR_SIMILARITY, "<=>")
        py_local_src_teleon_retrieval_pgvector_index__PgBackend_candidates__rows = self._conn.execute(
            f"SELECT id, text, use_cases, labels, embedding FROM {py_var_src_teleon_retrieval_pgvector_index___TABLE} ORDER BY embedding {py_local_src_teleon_retrieval_pgvector_index__PgBackend_candidates__op} %s LIMIT %s",
            (py_arg_src_teleon_retrieval_pgvector_index__py_class_src_teleon_retrieval_pgvector_index__PgBackend_candidates__qv, max(py_arg_src_teleon_retrieval_pgvector_index__py_class_src_teleon_retrieval_pgvector_index__PgBackend_candidates__k * py_var_src_teleon_retrieval_pgvector_index___RECALL_FACTOR, py_arg_src_teleon_retrieval_pgvector_index__py_class_src_teleon_retrieval_pgvector_index__PgBackend_candidates__k))).fetchall()
        return [py_class_src_teleon_retrieval_pgvector_index__Doc(id=r[0], text=r[1] or "", use_cases=r[2] or "", labels=r[3] or "", vector=list(r[4])) for r in py_local_src_teleon_retrieval_pgvector_index__PgBackend_candidates__rows]

    def count(self) -> int:
        return self._conn.execute(f"SELECT COUNT(*) FROM {py_var_src_teleon_retrieval_pgvector_index___TABLE}").fetchone()[0]

    def close(self) -> None:
        try:
            self._conn.close()
        except Exception:  # noqa: BLE001
            pass


def py_function_src_teleon_retrieval_pgvector_index___psycopg_available() -> bool:
    """Network-free: are BOTH psycopg and the pgvector adapter importable?"""
    return (importlib.util.find_spec("psycopg") is not None
            and importlib.util.find_spec("pgvector") is not None)


def py_function_src_teleon_retrieval_pgvector_index___resolve_backend(py_arg_src_teleon_retrieval_pgvector_index__py_function_src_teleon_retrieval_pgvector_index__resolve_backend__dsn, py_arg_src_teleon_retrieval_pgvector_index__py_function_src_teleon_retrieval_pgvector_index__resolve_backend__allow_pg: bool, py_arg_src_teleon_retrieval_pgvector_index__py_function_src_teleon_retrieval_pgvector_index__resolve_backend__dim: int):
    if py_arg_src_teleon_retrieval_pgvector_index__py_function_src_teleon_retrieval_pgvector_index__resolve_backend__allow_pg and py_arg_src_teleon_retrieval_pgvector_index__py_function_src_teleon_retrieval_pgvector_index__resolve_backend__dsn and py_function_src_teleon_retrieval_pgvector_index___psycopg_available():
        try:
            return py_class_src_teleon_retrieval_pgvector_index___PgBackend(py_arg_src_teleon_retrieval_pgvector_index__py_function_src_teleon_retrieval_pgvector_index__resolve_backend__dsn, py_arg_src_teleon_retrieval_pgvector_index__py_function_src_teleon_retrieval_pgvector_index__resolve_backend__dim)
        except Exception:  # noqa: BLE001 — honest fallback: no extension / can't connect → in-memory cosine index
            pass
    return py_class_src_teleon_retrieval_pgvector_index___MemBackend(py_arg_src_teleon_retrieval_pgvector_index__py_function_src_teleon_retrieval_pgvector_index__resolve_backend__dim)


class py_class_src_teleon_retrieval_pgvector_index__HybridVectorIndex:
    """Hybrid (lexical + learned-vector + use_cases + labels) index over a pgvector OR in-memory backend (auto, honest)."""

    def __init__(self, *, embedder=None, dsn: str | None = None, allow_pg: bool = True):
        self.embedder = embedder or py_class_src_teleon_retrieval_learned_vectors__LearnedVectorPort()
        self.dim = self.embedder.dim
        if dsn is None:
            dsn = os.environ.get(DEFAULT_DATABASE_URL_ENV) or None
        self._backend = py_function_src_teleon_retrieval_pgvector_index___resolve_backend(dsn, allow_pg, self.dim)
        self.backend = self._backend.backend
        self.serves_truth = False

    def _doc_vector(self, py_arg_src_teleon_retrieval_pgvector_index__py_class_src_teleon_retrieval_pgvector_index__HybridVectorIndex__doc_vector__text: str, py_arg_src_teleon_retrieval_pgvector_index__py_class_src_teleon_retrieval_pgvector_index__HybridVectorIndex__doc_vector__use_cases: str) -> list:
        return self.embedder.embed(f"{py_arg_src_teleon_retrieval_pgvector_index__py_class_src_teleon_retrieval_pgvector_index__HybridVectorIndex__doc_vector__text} {py_arg_src_teleon_retrieval_pgvector_index__py_class_src_teleon_retrieval_pgvector_index__HybridVectorIndex__doc_vector__use_cases}".strip())      # vectorize the meaning-bearing columns

    def add(self, py_arg_src_teleon_retrieval_pgvector_index__py_class_src_teleon_retrieval_pgvector_index__HybridVectorIndex_add__id: str, *, text="", use_cases="", labels="", vector=None) -> None:
        text, use_cases, labels = py_function_src_teleon_retrieval_pgvector_index___as_text(text), py_function_src_teleon_retrieval_pgvector_index___as_text(use_cases), py_function_src_teleon_retrieval_pgvector_index___as_text(labels)
        py_local_src_teleon_retrieval_pgvector_index__HybridVectorIndex_add__vec = list(vector) if vector is not None else self._doc_vector(text, use_cases)
        self._backend.upsert(py_class_src_teleon_retrieval_pgvector_index__Doc(id=py_arg_src_teleon_retrieval_pgvector_index__py_class_src_teleon_retrieval_pgvector_index__HybridVectorIndex_add__id, text=text, use_cases=use_cases, labels=labels, vector=py_local_src_teleon_retrieval_pgvector_index__HybridVectorIndex_add__vec))

    def add_many(self, py_arg_src_teleon_retrieval_pgvector_index__py_class_src_teleon_retrieval_pgvector_index__HybridVectorIndex_add_many__docs) -> None:
        for py_local_src_teleon_retrieval_pgvector_index__HybridVectorIndex_add_many__d in py_arg_src_teleon_retrieval_pgvector_index__py_class_src_teleon_retrieval_pgvector_index__HybridVectorIndex_add_many__docs:
            self.add(py_local_src_teleon_retrieval_pgvector_index__HybridVectorIndex_add_many__d["id"], text=py_local_src_teleon_retrieval_pgvector_index__HybridVectorIndex_add_many__d.get("text", ""), use_cases=py_local_src_teleon_retrieval_pgvector_index__HybridVectorIndex_add_many__d.get("use_cases", ""),
                     labels=py_local_src_teleon_retrieval_pgvector_index__HybridVectorIndex_add_many__d.get("labels", ""), vector=py_local_src_teleon_retrieval_pgvector_index__HybridVectorIndex_add_many__d.get("vector"))

    def search(self, py_arg_src_teleon_retrieval_pgvector_index__py_class_src_teleon_retrieval_pgvector_index__HybridVectorIndex_search__query: str, *, k: int = 10, explain: bool = False) -> list[dict]:
        py_local_src_teleon_retrieval_pgvector_index__HybridVectorIndex_search__qv = self.embedder.embed(py_arg_src_teleon_retrieval_pgvector_index__py_class_src_teleon_retrieval_pgvector_index__HybridVectorIndex_search__query or "")
        py_local_src_teleon_retrieval_pgvector_index__HybridVectorIndex_search__out = []
        for py_local_src_teleon_retrieval_pgvector_index__HybridVectorIndex_search__doc in self._backend.candidates(py_local_src_teleon_retrieval_pgvector_index__HybridVectorIndex_search__qv, k):
            py_local_src_teleon_retrieval_pgvector_index__HybridVectorIndex_search__total, py_local_src_teleon_retrieval_pgvector_index__HybridVectorIndex_search__parts = py_function_src_teleon_retrieval_pgvector_index___score(py_arg_src_teleon_retrieval_pgvector_index__py_class_src_teleon_retrieval_pgvector_index__HybridVectorIndex_search__query, py_local_src_teleon_retrieval_pgvector_index__HybridVectorIndex_search__qv, py_local_src_teleon_retrieval_pgvector_index__HybridVectorIndex_search__doc)
            if py_local_src_teleon_retrieval_pgvector_index__HybridVectorIndex_search__total > 0:
                py_local_src_teleon_retrieval_pgvector_index__HybridVectorIndex_search__row = {"id": py_local_src_teleon_retrieval_pgvector_index__HybridVectorIndex_search__doc.id, "score": round(py_local_src_teleon_retrieval_pgvector_index__HybridVectorIndex_search__total, 4), "use_cases": py_local_src_teleon_retrieval_pgvector_index__HybridVectorIndex_search__doc.use_cases, "labels": py_local_src_teleon_retrieval_pgvector_index__HybridVectorIndex_search__doc.labels}
                if explain:
                    py_local_src_teleon_retrieval_pgvector_index__HybridVectorIndex_search__row["by_signal"] = dict(sorted(py_local_src_teleon_retrieval_pgvector_index__HybridVectorIndex_search__parts.items(), key=lambda py_arg_src_teleon_retrieval_pgvector_index__py_class_src_teleon_retrieval_pgvector_index__HybridVectorIndex_search__kv: -py_arg_src_teleon_retrieval_pgvector_index__py_class_src_teleon_retrieval_pgvector_index__HybridVectorIndex_search__kv[1]))
                py_local_src_teleon_retrieval_pgvector_index__HybridVectorIndex_search__out.append(py_local_src_teleon_retrieval_pgvector_index__HybridVectorIndex_search__row)
        return sorted(py_local_src_teleon_retrieval_pgvector_index__HybridVectorIndex_search__out, key=lambda py_arg_src_teleon_retrieval_pgvector_index__py_class_src_teleon_retrieval_pgvector_index__HybridVectorIndex_search__r: (-py_arg_src_teleon_retrieval_pgvector_index__py_class_src_teleon_retrieval_pgvector_index__HybridVectorIndex_search__r["score"], py_arg_src_teleon_retrieval_pgvector_index__py_class_src_teleon_retrieval_pgvector_index__HybridVectorIndex_search__r["id"]))[:k]

    def count(self) -> int:
        return self._backend.count()

    def info(self) -> dict:
        py_local_src_teleon_retrieval_pgvector_index__HybridVectorIndex_info__emb = self.embedder.info() if hasattr(self.embedder, "info") else getattr(self.embedder, "name", "?")
        return {"backend": self.backend, "dim": self.dim, "vector_type": pgvector_type(self.dim),
                "similarity": DEFAULT_VECTOR_SIMILARITY, "embedder": py_local_src_teleon_retrieval_pgvector_index__HybridVectorIndex_info__emb, "serves_truth": False}

    def close(self) -> None:
        self._backend.close()


def py_function_src_teleon_retrieval_pgvector_index__build_hybrid_index(py_arg_src_teleon_retrieval_pgvector_index__py_function_src_teleon_retrieval_pgvector_index__build_hybrid_index__docs, *, py_arg_src_teleon_retrieval_pgvector_index__py_function_src_teleon_retrieval_pgvector_index__build_hybrid_index__embedder=None, py_arg_src_teleon_retrieval_pgvector_index__py_function_src_teleon_retrieval_pgvector_index__build_hybrid_index__dsn=None, py_arg_src_teleon_retrieval_pgvector_index__py_function_src_teleon_retrieval_pgvector_index__build_hybrid_index__allow_pg=True) -> py_class_src_teleon_retrieval_pgvector_index__HybridVectorIndex:
    idx = py_class_src_teleon_retrieval_pgvector_index__HybridVectorIndex(embedder=py_arg_src_teleon_retrieval_pgvector_index__py_function_src_teleon_retrieval_pgvector_index__build_hybrid_index__embedder, dsn=py_arg_src_teleon_retrieval_pgvector_index__py_function_src_teleon_retrieval_pgvector_index__build_hybrid_index__dsn, allow_pg=py_arg_src_teleon_retrieval_pgvector_index__py_function_src_teleon_retrieval_pgvector_index__build_hybrid_index__allow_pg)
    idx.add_many(py_arg_src_teleon_retrieval_pgvector_index__py_function_src_teleon_retrieval_pgvector_index__build_hybrid_index__docs)
    return idx


def py_function_src_teleon_retrieval_pgvector_index__self_test() -> int:
    from src.teleon.synthesis.component_search import py_function_src_teleon_synthesis_component_search__embed as _lex, py_const_src_teleon_synthesis_component_search__INDEX_DIM

    # 1) LEARNED vectors HONEST-fallback: model forced unavailable → deterministic lexical floor (never a fake model).
    port = py_class_src_teleon_retrieval_learned_vectors__LearnedVectorPort(allow_model=False)
    assert port.is_learned is False and port.backend_name == "lexical", port.info()
    assert port.dim == py_const_src_teleon_synthesis_component_search__INDEX_DIM and port.embed("agent") == _lex("agent"), "fallback == repo lexical embed"

    # 2) pgvector backend HONEST-fallback: no DSN → in-memory cosine index; vector type built from the LIVE dim.
    idx = py_class_src_teleon_retrieval_pgvector_index__HybridVectorIndex(embedder=port, dsn=None, allow_pg=True)
    assert idx.backend == py_const_src_teleon_retrieval_pgvector_index__MEM_BACKEND, idx.info()
    if not py_function_src_teleon_retrieval_pgvector_index___psycopg_available():                            # even WITH a DSN, absent psycopg/pgvector → in-memory (honest)
        assert py_class_src_teleon_retrieval_pgvector_index__HybridVectorIndex(embedder=port, dsn="postgresql://nope/x", allow_pg=True).backend == py_const_src_teleon_retrieval_pgvector_index__MEM_BACKEND
    assert idx.info()["vector_type"] == pgvector_type(port.dim) and str(port.dim) in idx.info()["vector_type"]

    # 3) HYBRID search over use_cases/labels returns the right doc on the fallback.
    idx.add_many([
        {"id": "agent", "text": "workflow orchestrator",
         "use_cases": "orchestrate multi-agent workflows and route tool calls",
         "labels": ["tool", "agent", "orchestration"]},
        {"id": "email", "text": "contact validator",
         "use_cases": "validate email address syntax with a regular expression",
         "labels": ["component", "regex", "validation"]},
        {"id": "ocr", "text": "scanned page reader",
         "use_cases": "extract printed words from scanned document images",
         "labels": ["ocr", "document", "capture"]},
    ])
    assert idx.count() == 3
    py_local_src_teleon_retrieval_pgvector_index__self_test__top = idx.search("multi-agent orchestration", k=3, explain=True)
    assert py_local_src_teleon_retrieval_pgvector_index__self_test__top and py_local_src_teleon_retrieval_pgvector_index__self_test__top[0]["id"] == "agent", f"use_cases+labels rank the agent doc first: {py_local_src_teleon_retrieval_pgvector_index__self_test__top[:2]}"
    assert any(s in py_local_src_teleon_retrieval_pgvector_index__self_test__top[0]["by_signal"] for s in ("use_cases", "labels")), f"use_cases/labels contributed: {py_local_src_teleon_retrieval_pgvector_index__self_test__top[0]}"
    assert idx.search("regular expression syntax", k=1)[0]["id"] == "email", "use_cases-only match wins (weighted use_cases)"
    assert idx.search("capture", k=1)[0]["id"] == "ocr", "labels-only match wins (weighted labels)"
    assert isinstance(py_function_src_teleon_retrieval_pgvector_index___psycopg_available(), bool)
    idx.close()
    print(f"pgvector_index self-test: OK (learned->lexical honest-fallback dim={port.dim}; pgvector->in_memory "
          f"honest-fallback; hybrid lexical+vector+use_cases+labels ranks correctly; vector_type={pgvector_type(port.dim)}) "
          f"serves_truth={py_const_src_teleon_retrieval_pgvector_index__SERVES_TRUTH}")
    return 0


def main(py_arg_src_teleon_retrieval_pgvector_index__main__argv: list[str]) -> int:
    if "--self-test" in py_arg_src_teleon_retrieval_pgvector_index__main__argv:
        return py_function_src_teleon_retrieval_pgvector_index__self_test()
    print("usage: pgvector_index.py --self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
