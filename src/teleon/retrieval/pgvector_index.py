#!/usr/bin/env python3
"""src.teleon.retrieval.pgvector_index — HYBRID vector index: a pgvector (Postgres) backend with an HONEST in-memory fallback.

Upgrade #16. Each doc is stored with a LEARNED semantic vector (learned_vectors.LearnedVectorPort) PLUS explicit
`use_cases` and `labels` columns, and ranked by a HYBRID score = lexical(name/text) + vector(semantic) + use_cases +
labels. The column model + weights are REUSED from scripts/hybrid_search.py (single source — no magic weights), and the
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

_REPO = Path(__file__).resolve().parents[3]
if str(_REPO) not in sys.path:                       # sys.path insert so a direct `python3 .../pgvector_index.py` run works
    sys.path.insert(0, str(_REPO))

from scripts._config import DEFAULT_DATABASE_URL_ENV, DEFAULT_VECTOR_SIMILARITY, pgvector_type
from scripts.hybrid_search import WEIGHTS, _toks            # match the column model + weights (single source, no magic values)
from src.teleon.retrieval.learned_vectors import LearnedVectorPort

SERVES_TRUTH = False
PG_BACKEND = "postgres_pgvector"
MEM_BACKEND = "in_memory"
_TABLE = "retrieval_hybrid_doc"
#: the VECTOR signal's weight — reuse a canonical column weight rather than invent a new magic number.
VECTOR_WEIGHT = WEIGHTS["tags"]
#: pgvector distance operators by similarity name (cosine is the repo default DEFAULT_VECTOR_SIMILARITY).
_SIM_OP = {"cosine": "<=>", "l2": "<->", "inner_product": "<#>"}
_PG_CONNECT_TIMEOUT_S = 3
_RECALL_FACTOR = 5                                          # over-fetch factor for vector recall before the hybrid re-rank


def _as_text(v) -> str:
    return " ".join(str(x) for x in v) if isinstance(v, (list, tuple)) else str(v or "")


def _cosine(a, b) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


def _overlap(q_toks: set, text: str) -> float:
    return (len(q_toks & set(_toks(text))) / len(q_toks)) if q_toks else 0.0


@dataclass
class Doc:
    id: str
    text: str = ""
    use_cases: str = ""
    labels: str = ""
    vector: list = field(default_factory=list)


def _score(query: str, qv: list, doc: Doc) -> tuple:
    """HYBRID: weighted sum of vector cosine + per-column lexical overlap (name/text, use_cases, labels)."""
    qt = set(_toks(query))
    parts = {
        "vector": VECTOR_WEIGHT * max(0.0, _cosine(qv, doc.vector)),     # semantic (learned, or lexical floor honestly)
        "name": WEIGHTS["name"] * _overlap(qt, doc.text),
        "use_cases": WEIGHTS["use_cases"] * _overlap(qt, doc.use_cases),  # explicit use_cases column, weighted
        "labels": WEIGHTS["labels"] * _overlap(qt, doc.labels),          # explicit labels column, weighted
    }
    total = sum(parts.values())
    return total, {k: round(v, 4) for k, v in parts.items() if v > 0}


class _MemBackend:
    """Always-available in-memory cosine index — the HONEST offline fallback when pgvector isn't reachable."""
    backend = MEM_BACKEND

    def __init__(self, dim: int):
        self.dim = dim
        self._docs: dict[str, Doc] = {}

    def upsert(self, doc: Doc) -> None:
        self._docs[doc.id] = doc

    def candidates(self, qv, k):
        return list(self._docs.values())               # small index: hybrid-rank them all

    def count(self) -> int:
        return len(self._docs)

    def close(self) -> None:
        self._docs.clear()


class _PgBackend:
    """Postgres+pgvector store. Real, but engaged only when psycopg + the pgvector adapter + a reachable DSN exist; any
    failure in __init__ propagates so the resolver HONESTLY falls back to the in-memory index. Vector recall in SQL
    (ANN by the cosine operator), then the SAME Python hybrid re-rank over the over-fetched candidates."""
    backend = PG_BACKEND

    def __init__(self, dsn: str, dim: int):
        import psycopg
        from pgvector.psycopg import register_vector
        self.dim = dim
        self._conn = psycopg.connect(dsn, connect_timeout=_PG_CONNECT_TIMEOUT_S, autocommit=True)
        self._conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
        register_vector(self._conn)
        self._conn.execute(
            f"CREATE TABLE IF NOT EXISTS {_TABLE} (id text PRIMARY KEY, text text, use_cases text, labels text, "
            f"embedding {pgvector_type(dim)})")            # column type from _config.pgvector_type — never a literal dim

    def upsert(self, doc: Doc) -> None:
        self._conn.execute(
            f"INSERT INTO {_TABLE} (id, text, use_cases, labels, embedding) VALUES (%s, %s, %s, %s, %s) "
            f"ON CONFLICT (id) DO UPDATE SET text=EXCLUDED.text, use_cases=EXCLUDED.use_cases, "
            f"labels=EXCLUDED.labels, embedding=EXCLUDED.embedding",
            (doc.id, doc.text, doc.use_cases, doc.labels, doc.vector))

    def candidates(self, qv, k):
        op = _SIM_OP.get(DEFAULT_VECTOR_SIMILARITY, "<=>")
        rows = self._conn.execute(
            f"SELECT id, text, use_cases, labels, embedding FROM {_TABLE} ORDER BY embedding {op} %s LIMIT %s",
            (qv, max(k * _RECALL_FACTOR, k))).fetchall()
        return [Doc(id=r[0], text=r[1] or "", use_cases=r[2] or "", labels=r[3] or "", vector=list(r[4])) for r in rows]

    def count(self) -> int:
        return self._conn.execute(f"SELECT COUNT(*) FROM {_TABLE}").fetchone()[0]

    def close(self) -> None:
        try:
            self._conn.close()
        except Exception:  # noqa: BLE001
            pass


def _psycopg_available() -> bool:
    """Network-free: are BOTH psycopg and the pgvector adapter importable?"""
    return (importlib.util.find_spec("psycopg") is not None
            and importlib.util.find_spec("pgvector") is not None)


def _resolve_backend(dsn, allow_pg: bool, dim: int):
    if allow_pg and dsn and _psycopg_available():
        try:
            return _PgBackend(dsn, dim)
        except Exception:  # noqa: BLE001 — honest fallback: no extension / can't connect → in-memory cosine index
            pass
    return _MemBackend(dim)


class HybridVectorIndex:
    """Hybrid (lexical + learned-vector + use_cases + labels) index over a pgvector OR in-memory backend (auto, honest)."""

    def __init__(self, *, embedder=None, dsn: str | None = None, allow_pg: bool = True):
        self.embedder = embedder or LearnedVectorPort()
        self.dim = self.embedder.dim
        if dsn is None:
            dsn = os.environ.get(DEFAULT_DATABASE_URL_ENV) or None
        self._backend = _resolve_backend(dsn, allow_pg, self.dim)
        self.backend = self._backend.backend
        self.serves_truth = False

    def _doc_vector(self, text: str, use_cases: str) -> list:
        return self.embedder.embed(f"{text} {use_cases}".strip())      # vectorize the meaning-bearing columns

    def add(self, id: str, *, text="", use_cases="", labels="", vector=None) -> None:
        text, use_cases, labels = _as_text(text), _as_text(use_cases), _as_text(labels)
        vec = list(vector) if vector is not None else self._doc_vector(text, use_cases)
        self._backend.upsert(Doc(id=id, text=text, use_cases=use_cases, labels=labels, vector=vec))

    def add_many(self, docs) -> None:
        for d in docs:
            self.add(d["id"], text=d.get("text", ""), use_cases=d.get("use_cases", ""),
                     labels=d.get("labels", ""), vector=d.get("vector"))

    def search(self, query: str, *, k: int = 10, explain: bool = False) -> list[dict]:
        qv = self.embedder.embed(query or "")
        out = []
        for doc in self._backend.candidates(qv, k):
            total, parts = _score(query, qv, doc)
            if total > 0:
                row = {"id": doc.id, "score": round(total, 4), "use_cases": doc.use_cases, "labels": doc.labels}
                if explain:
                    row["by_signal"] = dict(sorted(parts.items(), key=lambda kv: -kv[1]))
                out.append(row)
        return sorted(out, key=lambda r: (-r["score"], r["id"]))[:k]

    def count(self) -> int:
        return self._backend.count()

    def info(self) -> dict:
        emb = self.embedder.info() if hasattr(self.embedder, "info") else getattr(self.embedder, "name", "?")
        return {"backend": self.backend, "dim": self.dim, "vector_type": pgvector_type(self.dim),
                "similarity": DEFAULT_VECTOR_SIMILARITY, "embedder": emb, "serves_truth": False}

    def close(self) -> None:
        self._backend.close()


def build_hybrid_index(docs, *, embedder=None, dsn=None, allow_pg=True) -> HybridVectorIndex:
    idx = HybridVectorIndex(embedder=embedder, dsn=dsn, allow_pg=allow_pg)
    idx.add_many(docs)
    return idx


def self_test() -> int:
    from src.teleon.synthesis.component_search import embed as _lex, INDEX_DIM

    # 1) LEARNED vectors HONEST-fallback: model forced unavailable → deterministic lexical floor (never a fake model).
    port = LearnedVectorPort(allow_model=False)
    assert port.is_learned is False and port.backend_name == "lexical", port.info()
    assert port.dim == INDEX_DIM and port.embed("agent") == _lex("agent"), "fallback == repo lexical embed"

    # 2) pgvector backend HONEST-fallback: no DSN → in-memory cosine index; vector type built from the LIVE dim.
    idx = HybridVectorIndex(embedder=port, dsn=None, allow_pg=True)
    assert idx.backend == MEM_BACKEND, idx.info()
    if not _psycopg_available():                            # even WITH a DSN, absent psycopg/pgvector → in-memory (honest)
        assert HybridVectorIndex(embedder=port, dsn="postgresql://nope/x", allow_pg=True).backend == MEM_BACKEND
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
    top = idx.search("multi-agent orchestration", k=3, explain=True)
    assert top and top[0]["id"] == "agent", f"use_cases+labels rank the agent doc first: {top[:2]}"
    assert any(s in top[0]["by_signal"] for s in ("use_cases", "labels")), f"use_cases/labels contributed: {top[0]}"
    assert idx.search("regular expression syntax", k=1)[0]["id"] == "email", "use_cases-only match wins (weighted use_cases)"
    assert idx.search("capture", k=1)[0]["id"] == "ocr", "labels-only match wins (weighted labels)"
    assert isinstance(_psycopg_available(), bool)
    idx.close()
    print(f"pgvector_index self-test: OK (learned->lexical honest-fallback dim={port.dim}; pgvector->in_memory "
          f"honest-fallback; hybrid lexical+vector+use_cases+labels ranks correctly; vector_type={pgvector_type(port.dim)}) "
          f"serves_truth={SERVES_TRUTH}")
    return 0


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        return self_test()
    print("usage: pgvector_index.py --self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
