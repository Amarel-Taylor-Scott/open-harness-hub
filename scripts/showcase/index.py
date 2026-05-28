"""In-memory hybrid index over the vector store (keyword + label + vector)."""
from __future__ import annotations

import json
import re
import sqlite3

from scripts.db import build_vector_store as vs
from scripts.embeddings import resolve_backend

_TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9_.+-]{1,40}")
# Stopwords: matching on these ("and/for/the/risk") produced nonsense selections.
STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "into", "your", "you", "are",
    "use", "using", "get", "via", "per", "out", "all", "any", "can", "has", "have",
    "of", "to", "in", "on", "is", "it", "as", "by", "or", "be", "at", "we", "an", "a",
    "task", "build", "make", "create", "run", "then", "when", "each", "its", "their",
    "based", "given", "following", "appropriate", "most", "more", "less",
}


def tokens(text: str) -> set[str]:
    return {t for t in _TOKEN_RE.findall(text.lower()) if len(t) >= 3 and t not in STOPWORDS}


class Index:
    """In-memory hybrid index loaded once from the vector store."""

    def __init__(self) -> None:
        self.backend = resolve_backend()
        store = vs.DEFAULT_STORE
        if not store.exists():
            vs.build(store=store, model=self.backend.model_id)
        con = sqlite3.connect(store)
        rows = con.execute(
            "SELECT subject_id, subject_type, text, embedding FROM object_embedding WHERE embedding_model=?",
            (self.backend.model_id,),
        ).fetchall()
        if not rows:  # store built with a different model — (re)build for this one
            con.close()
            vs.build(store=store, model=self.backend.model_id)
            con = sqlite3.connect(store)
            rows = con.execute(
                "SELECT subject_id, subject_type, text, embedding FROM object_embedding WHERE embedding_model=?",
                (self.backend.model_id,),
            ).fetchall()
        self.labels: dict[str, list[str]] = {}
        for sid, label in con.execute("SELECT subject_id, label FROM label_assignment"):
            self.labels.setdefault(sid, []).append(label)
        con.close()
        self.items = []
        for sid, stype, text, emb in rows:
            name, desc = (text.split(" · ", 2) + ["", ""])[:2]
            self.items.append({
                "id": sid, "type": stype, "name": name.strip() or sid,
                "desc": desc.strip(), "text": text, "tokens": tokens(text),
                "vec": json.loads(emb), "labels": self.labels.get(sid, []),
            })

    def search(self, task: str, k: int = 24) -> list[dict]:
        qtok = tokens(task)
        qvec = self.backend.embed_one(task)
        semantic = self.backend.promotable  # real embeddings → trust the vector
        out = []
        for it in self.items:
            lex = len(qtok & it["tokens"]) / (len(qtok) + 1)            # stopword-filtered overlap
            vec = max(0.0, sum(a * b for a, b in zip(qvec, it["vec"])))  # cosine (both L2)
            lab = 0.04 * len(set(it["labels"]) & qtok)                  # label boost
            # With real embeddings the vector leads; offline (hash) lean on keywords.
            score = (0.72 * vec + 0.24 * lex + lab) if semantic else (0.30 * vec + 0.65 * lex + lab)
            shared = sorted(qtok & it["tokens"])[:6]
            out.append({**{x: it[x] for x in ("id", "type", "name", "desc", "labels")},
                        "score": round(score, 4), "vec": round(vec, 4), "matched": shared})
        out.sort(key=lambda r: r["score"], reverse=True)
        return out[:k]
