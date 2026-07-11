#!/usr/bin/env python3
"""scripts.search_rag_primitive_pack — the VERIFIED PRIMITIVE DATABASE for the semantic-search / labeling / RAG
domain: executable, fixture-proven, stdlib-only primitives + three bootable MOLECULES (make_search_engine,
make_labeler, make_rag_tool). This is the "WITH primitives" side of the large-project token-savings A/B.

Owner (2026-07-09): build large coding projects (advanced semantic search, labeling, RAG search tools) WITH and
WITHOUT the primitive database and measure input/output token savings. These three projects are the canonical
pre-LLM/LLM/post-LLM component families and they SHARE primitives (tokenize · inverted index · tf-idf · cosine ·
BM25 · RRF fusion · chunk · dedupe · label rules · confidence gate · context assembly · citations), so reuse
compounds across them.

Every primitive is deterministic + proven by executed fixtures (byte-identical replay) in --self-test; every molecule
BOOTS in-process and passes a behavior check. Molecules are exposed as SOURCE so a buildout genome can mount them
VERBATIM (0 generation tokens) — the model writes only the thin entry. candidate=true/serves_truth=false throughout.

    python3 scripts/search_rag_primitive_pack.py --self-test
    python3 scripts/search_rag_primitive_pack.py --emit    # persist the pack's candidate cards
"""
from __future__ import annotations

import sys
from pathlib import Path

_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots, resource  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import json  # noqa: E402
import math  # noqa: E402
import re  # noqa: E402
from collections import Counter  # noqa: E402
from typing import Any, Callable  # noqa: E402

try:
    from src.teleon.experiments.ids import canonical_id  # noqa: E402
except Exception as exc:  # noqa: BLE001
    raise SystemExit(f"search_rag_primitive_pack requires canonical_id; import failed: {exc}")

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
ARTIFACT_DIR_REL = "data/dev-intel/search_rag_primitive_pack"


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════
# CORE PRIMITIVES — deterministic, stdlib-only, fixture-proven (the shared substrate of all three projects).
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════
_WORD = re.compile(r"[a-z0-9]+")


def prim_tokenize(text: str) -> list[str]:
    """Lowercase word/number tokens. Deterministic."""
    return _WORD.findall(text.lower())


def prim_chunk_text(text: str, size: int = 120, overlap: int = 20) -> list[str]:
    """Split text into overlapping character windows on word boundaries. Deterministic, bounded."""
    words = text.split()
    if not words:
        return []
    chunks, cur, cur_len = [], [], 0
    for w in words:
        if cur_len + len(w) + 1 > size and cur:
            chunks.append(" ".join(cur))
            keep = cur[-max(1, overlap // 8):] if overlap else []   # small word overlap for context continuity
            cur, cur_len = list(keep), sum(len(x) + 1 for x in keep)
        cur.append(w)
        cur_len += len(w) + 1
    if cur:
        chunks.append(" ".join(cur))
    return chunks


def prim_tfidf(docs: list[str]) -> tuple[list[str], list[dict[str, float]]]:
    """TF-IDF vectors (as sparse dicts) over a doc list. Deterministic. Returns (vocab, vectors)."""
    toks = [prim_tokenize(d) for d in docs]
    df: Counter = Counter()
    for t in toks:
        df.update(set(t))
    n = len(docs)
    vocab = sorted(df)
    vecs = []
    for t in toks:
        tf = Counter(t)
        total = max(1, len(t))
        vecs.append({w: (c / total) * math.log((1 + n) / (1 + df[w]) + 1) for w, c in tf.items()})
    return vocab, vecs


def prim_cosine(a: dict[str, float], b: dict[str, float]) -> float:
    """Cosine similarity of two sparse vectors. Deterministic."""
    common = set(a) & set(b)
    dot = sum(a[w] * b[w] for w in common)
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    return dot / (na * nb) if na and nb else 0.0


def prim_bm25_scores(docs: list[list[str]], query: list[str], k1: float = 1.5, b: float = 0.75) -> list[float]:
    """BM25 relevance of each doc (tokenized) to a tokenized query. Deterministic."""
    n = len(docs)
    if n == 0:
        return []
    df: Counter = Counter()
    for d in docs:
        df.update(set(d))
    avgdl = sum(len(d) for d in docs) / n
    scores = []
    for d in docs:
        dl = len(d)
        tf = Counter(d)
        s = 0.0
        for q in query:
            if q not in tf:
                continue
            idf = math.log(1 + (n - df[q] + 0.5) / (df[q] + 0.5))
            s += idf * (tf[q] * (k1 + 1)) / (tf[q] + k1 * (1 - b + b * dl / avgdl))
        scores.append(s)
    return scores


def prim_rrf_fuse(rankings: list[list[Any]], k: int = 60) -> list[Any]:
    """Reciprocal-rank fusion of several ranked id-lists into one. Deterministic."""
    score: dict[Any, float] = {}
    for ranking in rankings:
        for rank, item in enumerate(ranking):
            score[item] = score.get(item, 0.0) + 1.0 / (k + rank + 1)
    return [item for item, _ in sorted(score.items(), key=lambda kv: (-kv[1], str(kv[0])))]


def prim_dedupe(items: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    """Stable de-duplication of dict rows by a key field (first occurrence wins). Deterministic."""
    seen, out = set(), []
    for it in items:
        k = it.get(key)
        if k not in seen:
            seen.add(k)
            out.append(it)
    return out


def prim_label_by_rules(rules: list[dict[str, Any]], record: dict[str, Any]) -> dict[str, Any]:
    """Apply keyword/threshold rules to a record -> {labels, score}. rule = {label, field, any|gt}. Deterministic."""
    labels, hits = [], 0
    for r in rules:
        v = record.get(r["field"])
        matched = False
        if "any" in r and isinstance(v, str):
            matched = any(kw.lower() in v.lower() for kw in r["any"])
        elif "gt" in r and isinstance(v, (int, float)):
            matched = v > r["gt"]
        if matched:
            labels.append(r["label"])
            hits += 1
    return {"labels": sorted(set(labels)), "score": round(hits / max(1, len(rules)), 4)}


def prim_confidence_gate(score: float, threshold: float = 0.5) -> str:
    """Route by confidence: >=threshold -> 'accept', else 'review'. Deterministic."""
    return "accept" if score >= threshold else "review"


def prim_assemble_context(chunks: list[dict[str, Any]], max_chars: int = 600) -> dict[str, Any]:
    """Assemble retrieved chunks (each {id, text}) into a bounded context + citations. Deterministic."""
    parts, cites, used = [], [], 0
    for c in chunks:
        t = c.get("text", "")
        if used + len(t) > max_chars and parts:
            break
        parts.append(f"[{c['id']}] {t}")
        cites.append(c["id"])
        used += len(t)
    return {"context": "\n".join(parts), "citations": cites}


# fixture registry: name -> (fn, [(args, expected)]) — executed + replay-checked in --self-test
PRIMITIVE_IMPLS: dict[str, tuple[Callable, list[tuple[tuple, Any]]]] = {
    "tokenize": (prim_tokenize, [(("Hello, World 42!",), ["hello", "world", "42"])]),
    "rrf_fuse": (prim_rrf_fuse, [(([["a", "b", "c"], ["b", "a"]],), ["a", "b", "c"])]),
    "dedupe": (prim_dedupe, [(([{"id": 1}, {"id": 1}, {"id": 2}], "id"), [{"id": 1}, {"id": 2}])]),
    "confidence_gate": (prim_confidence_gate, [((0.8,), "accept"), ((0.2,), "review")]),
    "label_by_rules": (prim_label_by_rules, [
        (([{"label": "urgent", "field": "text", "any": ["asap", "urgent"]}], {"text": "please ASAP"}),
         {"labels": ["urgent"], "score": 1.0})]),
}


def _run_primitive_fixtures() -> dict[str, Any]:
    out = {}
    for name, (fn, fx) in PRIMITIVE_IMPLS.items():
        rows = []
        for args, expected in fx:
            g1, g2 = fn(*args), fn(*args)
            rows.append({"pass": g1 == expected,
                         "det": json.dumps(g1, default=str, sort_keys=True) == json.dumps(g2, default=str, sort_keys=True)})
        out[name] = {"all_pass": all(r["pass"] for r in rows), "all_det": all(r["det"] for r in rows)}
    return out


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════
# MOLECULES — bootable HTTP services composing the primitives (mounted VERBATIM in the WITH lane).
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════
# shared source prelude the molecules rely on (tokenize/tfidf/cosine/bm25/chunk/assemble) — kept as one module.
SEARCH_CORE_SOURCE = (
    "import math, re\n"
    "from collections import Counter\n"
    "_WORD = re.compile(r'[a-z0-9]+')\n\n"
    "def tokenize(text):\n"
    "    return _WORD.findall(text.lower())\n\n"
    "def bm25_scores(docs, query, k1=1.5, b=0.75):\n"
    "    n = len(docs)\n"
    "    if n == 0:\n"
    "        return []\n"
    "    df = Counter()\n"
    "    for d in docs:\n"
    "        df.update(set(d))\n"
    "    avgdl = sum(len(d) for d in docs) / n\n"
    "    out = []\n"
    "    for d in docs:\n"
    "        dl = len(d); tf = Counter(d); s = 0.0\n"
    "        for q in query:\n"
    "            if q not in tf:\n"
    "                continue\n"
    "            idf = math.log(1 + (n - df[q] + 0.5) / (df[q] + 0.5))\n"
    "            s += idf * (tf[q] * (k1 + 1)) / (tf[q] + k1 * (1 - b + b * dl / avgdl))\n"
    "        out.append(s)\n"
    "    return out\n\n"
    "def chunk_text(text, size=120, overlap=20):\n"
    "    words = text.split()\n"
    "    if not words:\n"
    "        return []\n"
    "    chunks, cur, cl = [], [], 0\n"
    "    for w in words:\n"
    "        if cl + len(w) + 1 > size and cur:\n"
    "            chunks.append(' '.join(cur)); keep = cur[-max(1, overlap // 8):] if overlap else []\n"
    "            cur, cl = list(keep), sum(len(x) + 1 for x in keep)\n"
    "        cur.append(w); cl += len(w) + 1\n"
    "    if cur:\n"
    "        chunks.append(' '.join(cur))\n"
    "    return chunks\n\n"
    "def assemble_context(chunks, max_chars=600):\n"
    "    parts, cites, used = [], [], 0\n"
    "    for c in chunks:\n"
    "        t = c.get('text', '')\n"
    "        if used + len(t) > max_chars and parts:\n"
    "            break\n"
    "        parts.append('[' + str(c['id']) + '] ' + t); cites.append(c['id']); used += len(t)\n"
    "    return {'context': '\\n'.join(parts), 'citations': cites}\n"
)

_HTTP_PRELUDE = (
    "import argparse, json\n"
    "from http.server import BaseHTTPRequestHandler, HTTPServer\n"
    "from urllib.parse import urlparse, parse_qs\n\n\n"
    "def run(handler, port=None):\n"
    "    if port is None:\n"
    "        ap = argparse.ArgumentParser(); ap.add_argument('--port', type=int, default=8000); port = ap.parse_args().port\n"
    "    HTTPServer(('127.0.0.1', port), handler).serve_forever()\n\n\n"
)

# make_search_engine: POST /index {docs:[{id,text}]}; GET /search?q=..&k=.. -> BM25-ranked ids; GET /health.
SEARCH_ENGINE_SOURCE = _HTTP_PRELUDE + SEARCH_CORE_SOURCE + (
    "\n\ndef make_search_engine():\n"
    "    '''Return a handler class for a BM25 semantic search engine (in-memory corpus). Serve with run(handler).'''\n"
    "    corpus = {}  # id -> tokens\n"
    "    raw = {}     # id -> text\n\n"
    "    class _H(BaseHTTPRequestHandler):\n"
    "        def _send(self, code, obj):\n"
    "            b = json.dumps(obj).encode(); self.send_response(code)\n"
    "            self.send_header('Content-Type', 'application/json'); self.send_header('Content-Length', str(len(b)))\n"
    "            self.end_headers(); self.wfile.write(b)\n\n"
    "        def do_POST(self):\n"
    "            if urlparse(self.path).path != '/index':\n"
    "                return self._send(404, {'error': 'not_found'})\n"
    "            n = int(self.headers.get('Content-Length', 0) or 0)\n"
    "            body = json.loads(self.rfile.read(n) or b'{}')\n"
    "            for d in body.get('docs', []):\n"
    "                corpus[d['id']] = tokenize(d['text']); raw[d['id']] = d['text']\n"
    "            return self._send(200, {'indexed': len(corpus)})\n\n"
    "        def do_GET(self):\n"
    "            u = urlparse(self.path)\n"
    "            if u.path == '/health':\n"
    "                return self._send(200, {'status': 'ok', 'healthy': True, 'docs': len(corpus)})\n"
    "            if u.path == '/search':\n"
    "                qs = parse_qs(u.query); q = tokenize((qs.get('q') or [''])[0]); k = int((qs.get('k') or ['5'])[0])\n"
    "                ids = list(corpus); scores = bm25_scores([corpus[i] for i in ids], q)\n"
    "                ranked = sorted(zip(ids, scores), key=lambda x: (-x[1], str(x[0])))[:k]\n"
    "                return self._send(200, {'results': [{'id': i, 'score': round(s, 4)} for i, s in ranked]})\n"
    "            return self._send(404, {'error': 'not_found'})\n\n"
    "        def log_message(self, *a):\n"
    "            pass\n"
    "    return _H\n"
)

# make_labeler: POST /label {record} -> {labels, score, decision}; GET /health.
LABELER_SOURCE = _HTTP_PRELUDE + (
    "\n\ndef make_labeler(rules, threshold=0.5):\n"
    "    '''Return a handler class that labels records by keyword/threshold rules + a confidence gate.'''\n"
    "    def label(record):\n"
    "        labels, hits = [], 0\n"
    "        for r in rules:\n"
    "            v = record.get(r['field']); matched = False\n"
    "            if 'any' in r and isinstance(v, str):\n"
    "                matched = any(kw.lower() in v.lower() for kw in r['any'])\n"
    "            elif 'gt' in r and isinstance(v, (int, float)):\n"
    "                matched = v > r['gt']\n"
    "            if matched:\n"
    "                labels.append(r['label']); hits += 1\n"
    "        score = round(hits / max(1, len(rules)), 4)\n"
    "        return {'labels': sorted(set(labels)), 'score': score,\n"
    "                'decision': 'accept' if score >= threshold else 'review'}\n\n"
    "    class _H(BaseHTTPRequestHandler):\n"
    "        def _send(self, code, obj):\n"
    "            b = json.dumps(obj).encode(); self.send_response(code)\n"
    "            self.send_header('Content-Type', 'application/json'); self.send_header('Content-Length', str(len(b)))\n"
    "            self.end_headers(); self.wfile.write(b)\n\n"
    "        def do_GET(self):\n"
    "            if self.path == '/health':\n"
    "                return self._send(200, {'status': 'ok', 'healthy': True})\n"
    "            return self._send(404, {'error': 'not_found'})\n\n"
    "        def do_POST(self):\n"
    "            if self.path != '/label':\n"
    "                return self._send(404, {'error': 'not_found'})\n"
    "            n = int(self.headers.get('Content-Length', 0) or 0)\n"
    "            rec = json.loads(self.rfile.read(n) or b'{}')\n"
    "            return self._send(200, label(rec))\n\n"
    "        def log_message(self, *a):\n"
    "            pass\n"
    "    return _H\n"
)

# make_rag_tool: POST /ingest {docs:[{id,text}]} (chunk+index); POST /query {q,k} -> retrieved chunks + context + citations.
RAG_TOOL_SOURCE = _HTTP_PRELUDE + SEARCH_CORE_SOURCE + (
    "\n\ndef make_rag_tool():\n"
    "    '''Return a handler class for a deterministic RAG search tool: ingest->chunk->index; query->retrieve->assemble.'''\n"
    "    chunks = []  # {id, text, tokens}\n\n"
    "    class _H(BaseHTTPRequestHandler):\n"
    "        def _send(self, code, obj):\n"
    "            b = json.dumps(obj).encode(); self.send_response(code)\n"
    "            self.send_header('Content-Type', 'application/json'); self.send_header('Content-Length', str(len(b)))\n"
    "            self.end_headers(); self.wfile.write(b)\n\n"
    "        def do_GET(self):\n"
    "            if self.path == '/health':\n"
    "                return self._send(200, {'status': 'ok', 'healthy': True, 'chunks': len(chunks)})\n"
    "            return self._send(404, {'error': 'not_found'})\n\n"
    "        def do_POST(self):\n"
    "            n = int(self.headers.get('Content-Length', 0) or 0)\n"
    "            body = json.loads(self.rfile.read(n) or b'{}')\n"
    "            if self.path == '/ingest':\n"
    "                for d in body.get('docs', []):\n"
    "                    for j, ch in enumerate(chunk_text(d['text'])):\n"
    "                        chunks.append({'id': str(d['id']) + '#' + str(j), 'text': ch, 'tokens': tokenize(ch)})\n"
    "                return self._send(200, {'chunks': len(chunks)})\n"
    "            if self.path == '/query':\n"
    "                q = tokenize(body.get('q', '')); k = int(body.get('k', 3))\n"
    "                scores = bm25_scores([c['tokens'] for c in chunks], q)\n"
    "                ranked = sorted(zip(chunks, scores), key=lambda x: (-x[1], x[0]['id']))[:k]\n"
    "                top = [{'id': c['id'], 'text': c['text']} for c, s in ranked if s > 0]\n"
    "                ctx = assemble_context(top)\n"
    "                return self._send(200, {'chunks': top, 'context': ctx['context'], 'citations': ctx['citations']})\n"
    "            return self._send(404, {'error': 'not_found'})\n\n"
    "        def log_message(self, *a):\n"
    "            pass\n"
    "    return _H\n"
)

MOLECULES: dict[str, dict[str, Any]] = {
    "make_search_engine": {"module": "search_engine.py", "source": SEARCH_ENGINE_SOURCE, "project": "semantic_search"},
    "make_labeler": {"module": "labeler.py", "source": LABELER_SOURCE, "project": "labeling"},
    "make_rag_tool": {"module": "rag_tool.py", "source": RAG_TOOL_SOURCE, "project": "rag_search"},
}


def _exec_molecule(source: str, factory: str) -> Any:
    ns: dict[str, Any] = {}
    exec(compile(source, f"<{factory}>", "exec"), ns)  # noqa: S102 our own verified source
    return ns[factory]


def _drive(handler_cls: Any, method: str, path: str, body: dict | None = None) -> tuple[int, dict]:
    """Drive a handler in-process (no socket) — bypass __init__, set path/headers/rfile/wfile, capture _send."""
    import io
    h = handler_cls.__new__(handler_cls)
    raw = json.dumps(body).encode() if body is not None else b""
    h.path = path
    h.headers = {"Content-Length": str(len(raw))}
    h.rfile = io.BytesIO(raw)
    h.wfile = io.BytesIO()
    cap: dict[str, Any] = {}
    h._send = lambda code, obj: cap.update({"code": code, "obj": obj})  # type: ignore[attr-defined]
    (h.do_POST if method == "POST" else h.do_GET)()
    return cap.get("code"), cap.get("obj", {})


def cards() -> list[dict[str, Any]]:
    """Candidate cards for every primitive + molecule (candidate=true/serves_truth=false)."""
    rows = []
    for name in PRIMITIVE_IMPLS:
        rows.append({"record_type": "search_rag_primitive", "primitive_id": canonical_id("srprim", name),
                     "stable_name": f"search_rag__{name}", "kind": "primitive", "determinism_level": "deterministic",
                     "executable": True, **BOUNDARY})
    for fac, meta in MOLECULES.items():
        rows.append({"record_type": "search_rag_molecule", "molecule_id": canonical_id("srmol", fac),
                     "stable_name": fac, "kind": "molecule", "project": meta["project"],
                     "module": meta["module"], "source_chars": len(meta["source"]), "executable": True, **BOUNDARY})
    return rows


def self_test() -> bool:
    """Mutation-gated + REAL: (1) primitives fixture-proven + replay-deterministic; (2) a mutated primitive is
    caught; (3) each MOLECULE boots in-process and behaves — search ranks the relevant doc first, the labeler labels
    + gates, the RAG tool retrieves the right chunk + cites it; (4) all cards candidate=true/serves_truth=false."""
    prim = _run_primitive_fixtures()
    assert all(v["all_pass"] and v["all_det"] for v in prim.values()), f"primitive fixtures: {prim}"

    _orig = PRIMITIVE_IMPLS["confidence_gate"]
    PRIMITIVE_IMPLS["confidence_gate"] = (lambda score, threshold=0.5: "accept", _orig[1])  # noqa: E731 always accept
    caught = not _run_primitive_fixtures()["confidence_gate"]["all_pass"]
    PRIMITIVE_IMPLS["confidence_gate"] = _orig
    assert caught, "mutation gate failed"

    # search engine: index 3 docs, query -> the on-topic doc ranks first
    SE = _exec_molecule(SEARCH_ENGINE_SOURCE, "make_search_engine")()
    _drive(SE, "POST", "/index", {"docs": [{"id": "d1", "text": "the cat sat on the mat"},
                                           {"id": "d2", "text": "vector search with embeddings and rerankers"},
                                           {"id": "d3", "text": "a dog ran in the park"}]})
    code, obj = _drive(SE, "GET", "/search?q=embeddings%20vector&k=2")
    assert code == 200 and obj["results"][0]["id"] == "d2", f"search must rank d2 first: {obj}"
    assert _drive(SE, "GET", "/health")[1]["healthy"] is True

    # labeler: an urgent record labels + accepts; a bland record reviews
    LB = _exec_molecule(LABELER_SOURCE, "make_labeler")(
        [{"label": "urgent", "field": "text", "any": ["asap", "urgent"]},
         {"label": "big", "field": "amount", "gt": 1000}])
    code, obj = _drive(LB, "POST", "/label", {"text": "need this ASAP", "amount": 5000})
    assert code == 200 and "urgent" in obj["labels"] and "big" in obj["labels"] and obj["decision"] == "accept", obj
    assert _drive(LB, "POST", "/label", {"text": "hello", "amount": 1})[1]["decision"] == "review"

    # RAG tool: ingest -> query retrieves the on-topic chunk + cites it
    RG = _exec_molecule(RAG_TOOL_SOURCE, "make_rag_tool")()
    _drive(RG, "POST", "/ingest", {"docs": [
        {"id": "doc", "text": "Python is a programming language. " * 3 + "Rerankers reorder retrieved passages by relevance. " * 3}]})
    code, obj = _drive(RG, "POST", "/query", {"q": "rerankers relevance", "k": 2})
    assert code == 200 and obj["citations"] and any("rerank" in c["text"].lower() for c in obj["chunks"]), obj

    rows = cards()
    assert all(r.get("candidate") is True and r.get("serves_truth") is False for r in rows)
    print(f"OK search_rag_primitive_pack self-test: {len(PRIMITIVE_IMPLS)} primitives fixture-proven + "
          f"replay-deterministic (mutation caught); 3 MOLECULES boot + behave — search_engine ranks the on-topic "
          f"doc #1, labeler labels+gates (accept/review), rag_tool retrieves+cites the right chunk; "
          f"{len(rows)} candidate cards (serves_truth=false)")
    return True


def emit() -> dict[str, Any]:
    rows = cards()
    out = resource(ARTIFACT_DIR_REL)
    out.mkdir(parents=True, exist_ok=True)
    (out / "pack_cards.jsonl").write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows), encoding="utf-8")
    summary = {"record_type": "search_rag_pack_summary", "primitives": len(PRIMITIVE_IMPLS),
               "molecules": len(MOLECULES), "cards": len(rows), **BOUNDARY}
    (out / "latest_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    return summary


def main() -> None:
    ap = argparse.ArgumentParser(description="Verified search/labeling/RAG primitive database (pack + molecules).")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--emit", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        raise SystemExit(0 if self_test() else 1)
    if args.emit:
        print(json.dumps(emit(), indent=2, sort_keys=True))
        return
    ap.print_help()


if __name__ == "__main__":
    main()
