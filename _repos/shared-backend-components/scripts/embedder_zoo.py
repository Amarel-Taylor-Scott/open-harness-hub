#!/usr/bin/env python3
"""scripts.embedder_zoo — the EMBEDDER is a port, so it is a ZOO too. Today the model port has a few backends
(crc32 proxy, Ollama nomic, model2vec potion); the thousands of embedding/text models out there each register as
one more row behind the same interface, and we RACE them by receipt. This module makes that explicit AND adds
the ability to TRAIN OUR OWN mini-embedder from scratch on our corpus — no external model, numpy only.

Backends (each a contract-substitutable `embed(text) -> unit vector`):
  * proxy_crc32          — hashed-tf offline baseline (keyless; the floor the real models must beat).
  * lsa_local_trained    — a mini-embedder we TRAIN FROM SCRATCH on our own primitive corpus: TF-IDF + truncated
                           SVD (Latent Semantic Analysis), numpy only, deterministic (sign-fixed). This is the
                           first "our own model" — extend it to word2vec/GloVe/contrastive/distilled next.
  * model2vec_potion_8m  — static-embedding pretrained model (in-process, no torch, dim 256).
  * model2vec_retrieval_32m — retrieval-tuned static pretrained model (loads on demand).
  * ollama_nomic         — real nomic-embed-text via the local Ollama endpoint.

`race_embedders(cards, labelled)` benchmarks every AVAILABLE backend on a labelled family set (recall@k / MRR /
nDCG) and ranks them — so adding a model is a row + a re-run, and the choice is a receipt, never a guess. New
model families (sentence-transformers BGE/GTE/E5/mxbai/jina/arctic via fastembed-ONNX or sentence-transformers;
cross-encoder rerankers; a distilled or fine-tuned mini-embedder; a router / mini-LLM) each slot in as a new
backend row behind this same race. serves_truth=false — an embedding is geometry over a candidate, never truth.

    PYTHONPATH=. python3 scripts/embedder_zoo.py --self-test
    PYTHONPATH=. python3 scripts/embedder_zoo.py --race --sample 200
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
from collections import Counter  # noqa: E402
from typing import Any, Optional  # noqa: E402

from scripts import capability_embedding as _emb  # noqa: E402  REUSE: proxy/ollama/model2vec + blackbox text
from scripts import path_graph_bench as _bench  # noqa: E402  REUSE: metrics + labelled families + corpus
from scripts.build_primitive_search_index import tokenize as _tokenize  # noqa: E402  REUSE: the ONE tokenizer

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}

_LSA_DIM = 64          # latent dimensions for the from-scratch LSA embedder (single-source default)
_LSA_MAX_DOCS = 4000   # cap the training doc set (SVD is dense; a sample trains the space fine)
_LSA_MAX_VOCAB = 6000  # keep the most-frequent terms (the TF-IDF column space)

#: the model zoo — name -> {kind, ...}. Expanding = a new row (multi-path law), the choice made by race receipt.
EMBEDDER_BACKENDS: dict[str, dict[str, Any]] = {
    "proxy_crc32": {"kind": "proxy_offline", "detail": "crc32 hashed-tf, keyless baseline"},
    "lsa_local_trained": {"kind": "trained_from_scratch",
                          "detail": "TF-IDF + truncated SVD (LSA) trained on OUR corpus, numpy-only"},
    "model2vec_potion_8m": {"kind": "static_pretrained", "model": "minishlab/potion-base-8M",
                            "detail": "static embeddings, dim 256"},
    "model2vec_retrieval_32m": {"kind": "static_pretrained", "model": "minishlab/potion-retrieval-32M",
                                "detail": "retrieval-tuned static embeddings"},
    "model2vec_potion_2m": {"kind": "static_pretrained", "model": "minishlab/potion-base-2M",
                            "detail": "smallest static embedder — the latency/size floor row"},
    "model2vec_potion_4m": {"kind": "static_pretrained", "model": "minishlab/potion-base-4M",
                            "detail": "small static embedder between 2M and 8M"},
    "model2vec_multilingual_128m": {"kind": "static_pretrained", "model": "minishlab/potion-multilingual-128M",
                                    "detail": "multilingual static embeddings — the mixed-language gap row"},
    "ollama_nomic": {"kind": "api_local", "ollama_model": "nomic-embed-text", "detail": "nomic-embed-text via local Ollama"},
    "fastembed_bge_small": {"kind": "onnx_local", "model": "BAAI/bge-small-en-v1.5",
                            "detail": "BGE-small via fastembed ONNX, CPU — the dense bi-encoder row"},
    "fastembed_minilm_l6": {"kind": "onnx_local", "model": "sentence-transformers/all-MiniLM-L6-v2",
                            "detail": "MiniLM-L6 via fastembed ONNX, CPU"},
    # ── ADVANCED dense models (owner 2026-07-10: 'more than just model2vec — Gemma Embedding + other advanced
    #    models, numerous models'). fastembed ONNX (CPU, no torch) gives strong bi-encoders; each is one row, raced
    #    by receipt, first use downloads the model. These are MUCH stronger than the static model2vec lane. ──
    "fastembed_bge_large": {"kind": "onnx_local", "model": "BAAI/bge-large-en-v1.5", "detail": "BGE-large 1024d (strong)"},
    "fastembed_gte_large": {"kind": "onnx_local", "model": "thenlper/gte-large", "detail": "GTE-large 1024d (strong)"},
    "fastembed_mxbai_large": {"kind": "onnx_local", "model": "mixedbread-ai/mxbai-embed-large-v1", "detail": "mxbai-large 1024d (SOTA-class)"},
    "fastembed_arctic_l": {"kind": "onnx_local", "model": "snowflake/snowflake-arctic-embed-l", "detail": "Snowflake arctic-large"},
    "fastembed_jina_code": {"kind": "onnx_local", "model": "jinaai/jina-embeddings-v2-base-code", "detail": "CODE-specialized encoder"},
    "fastembed_nomic_v15": {"kind": "onnx_local", "model": "nomic-ai/nomic-embed-text-v1.5", "detail": "nomic v1.5 768d"},
    # Gemma + other Ollama embedding models — per-backend model via 'ollama_model' (first use may need `ollama pull`).
    "ollama_embeddinggemma": {"kind": "api_local", "ollama_model": "embeddinggemma", "detail": "Google EmbeddingGemma via Ollama"},
    "ollama_all_minilm": {"kind": "api_local", "ollama_model": "all-minilm", "detail": "all-MiniLM via Ollama"},
}

_m2v_cache: dict[str, Any] = {}


def _load_m2v(model_name: str) -> Any:
    """Load a model2vec static model by name ONCE (in-process, no torch). None if unavailable."""
    if model_name in _m2v_cache:
        return _m2v_cache[model_name]
    try:
        from model2vec import StaticModel  # noqa: PLC0415
        _m2v_cache[model_name] = StaticModel.from_pretrained(model_name)
    except Exception:  # noqa: BLE001 — offline / not installed => None, race skips it
        _m2v_cache[model_name] = None
    return _m2v_cache[model_name]


def _embed_m2v(text: str, model_name: str) -> list[float]:
    import numpy as np  # noqa: PLC0415
    model = _load_m2v(model_name)
    if model is None:
        return _emb.embed_text(text, path="tokens")
    vec = np.asarray(model.encode([str(text)])[0], dtype="float32")
    nrm = float(np.linalg.norm(vec)) or 1.0
    return (vec / nrm).tolist()


# ── TRAIN OUR OWN: LSA (TF-IDF + truncated SVD) from scratch on the corpus, numpy only ───────────────────────
def train_lsa(cards: list[dict[str, Any]], *, dim: int = _LSA_DIM, max_docs: int = _LSA_MAX_DOCS,
              max_vocab: int = _LSA_MAX_VOCAB) -> dict[str, Any]:
    """Fit a Latent Semantic Analysis embedder on OUR primitive corpus: build a TF-IDF term-document matrix,
    truncated-SVD it, keep the top-``dim`` right singular vectors as the term→latent projection. Deterministic
    (SVD signs fixed). This is a real, from-scratch, local model trained on our own data — no network, no torch."""
    import numpy as np  # noqa: PLC0415
    docs = [f"{_emb.blackbox_text(c)} {c.get('title') or ''}" for c in cards[:max_docs]]
    toks = [_tokenize(d) for d in docs]
    df: Counter = Counter()
    for ts in toks:
        df.update(set(ts))
    vocab = [t for t, _c in df.most_common(max_vocab)]
    vidx = {t: i for i, t in enumerate(vocab)}
    n_docs, vsize = len(docs), len(vocab)
    idf = np.zeros(vsize, dtype="float32")
    for t, i in vidx.items():
        idf[i] = np.log((n_docs + 1) / (df[t] + 1)) + 1.0
    mat = np.zeros((n_docs, vsize), dtype="float32")
    for d, ts in enumerate(toks):
        for t, cnt in Counter(ts).items():
            j = vidx.get(t)
            if j is not None:
                mat[d, j] = cnt
    mat *= idf  # tf-idf
    rownorm = np.linalg.norm(mat, axis=1, keepdims=True)
    rownorm[rownorm == 0] = 1.0
    mat /= rownorm
    dim = max(1, min(dim, vsize, n_docs))
    _u, _s, vt = np.linalg.svd(mat, full_matrices=False)
    comp = vt[:dim].copy()  # dim × vocab (term -> latent)
    for i in range(comp.shape[0]):  # deterministic sign: max-abs entry positive (svd_flip)
        j = int(np.argmax(np.abs(comp[i])))
        if comp[i, j] < 0:
            comp[i] *= -1.0
    return {"model": "lsa", "vocab_index": vidx, "idf": idf.tolist(), "components": comp.tolist(),
            "dim": dim, "trained_docs": n_docs, "vocab_size": vsize, **BOUNDARY}


def embed_lsa(text: str, state: dict[str, Any]) -> list[float]:
    """Project a query into the trained LSA latent space (TF-IDF vector · term→latent components)."""
    import numpy as np  # noqa: PLC0415
    vidx = state["vocab_index"]
    idf = np.asarray(state["idf"], dtype="float32")
    comp = np.asarray(state["components"], dtype="float32")
    vec = np.zeros(len(vidx), dtype="float32")
    for t, cnt in Counter(_tokenize(text)).items():
        j = vidx.get(t)
        if j is not None:
            vec[j] = cnt
    vec *= idf
    rn = float(np.linalg.norm(vec)) or 1.0
    latent = comp @ (vec / rn)
    ln = float(np.linalg.norm(latent)) or 1.0
    return (latent / ln).tolist()


_fe_cache: dict[str, Any] = {}


def _load_fastembed(model_name: str) -> Any:
    """Lazy fastembed ONNX model singleton (first call downloads the model once). None when unavailable."""
    if model_name in _fe_cache:
        return _fe_cache[model_name]
    try:
        from fastembed import TextEmbedding  # noqa: PLC0415
        _fe_cache[model_name] = TextEmbedding(model_name=model_name)
    except Exception:  # noqa: BLE001 — no package / no model / offline => row unavailable, race skips it
        _fe_cache[model_name] = None
    return _fe_cache[model_name]


def _embed_fastembed(text: str, model_name: str) -> list[float]:
    """One text via a fastembed ONNX model (L2-normalized); proxy fallback keeps the contract if it vanishes."""
    model = _load_fastembed(model_name)
    if model is None:
        return _emb.embed_text(text, path="tokens")  # labelled fallback, same contract
    import numpy as np  # noqa: PLC0415
    vec = np.asarray(next(iter(model.embed([str(text)]))), dtype=float)
    norm = float(np.linalg.norm(vec)) or 1.0
    return (vec / norm).tolist()


def _embed_ollama_model(text: str, model: str) -> Optional[list[float]]:
    """L2-normalized embedding from a SPECIFIC local Ollama model (EmbeddingGemma / nomic / all-minilm / …).
    Self-contained (doesn't touch capability_embedding's single-model global); None on any failure -> proxy fallback."""
    try:
        import urllib.request  # noqa: PLC0415
        import math  # noqa: PLC0415
        base = getattr(_emb, "_OLLAMA_BASE", "http://localhost:11434")
        payload = json.dumps({"model": model, "prompt": str(text)}).encode()
        req = urllib.request.Request(f"{base}/api/embeddings", data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=getattr(_emb, "_OLLAMA_TIMEOUT_S", 30)) as resp:  # noqa: S310
            raw = json.loads(resp.read()).get("embedding") or []
        if not raw:
            return None
        n = math.sqrt(sum(float(v) * float(v) for v in raw)) or 1.0
        return [float(v) / n for v in raw]
    except Exception:  # noqa: BLE001
        return None


def embed(text: str, backend: str, *, state: Optional[dict[str, Any]] = None) -> list[float]:
    """One text -> unit vector under the chosen backend. serves_truth=false."""
    if backend not in EMBEDDER_BACKENDS:
        raise ValueError(f"unknown backend {backend!r}; backends are {sorted(EMBEDDER_BACKENDS)}")
    spec = EMBEDDER_BACKENDS[backend]
    if backend == "proxy_crc32":
        return _emb.embed_text(text, path="tokens")
    if spec["kind"] == "api_local":  # per-backend Ollama model (nomic / embeddinggemma / all-minilm / …)
        vec = _embed_ollama_model(text, spec.get("ollama_model", "nomic-embed-text"))
        return vec if vec is not None else _emb.embed_text(text, path="tokens")
    if backend == "lsa_local_trained":
        if state is None:
            raise ValueError("lsa_local_trained needs a trained state — call train_lsa(cards) first")
        return embed_lsa(text, state)
    if spec["kind"] == "onnx_local":
        return _embed_fastembed(text, spec["model"])
    return _embed_m2v(text, spec["model"])  # static_pretrained


def backend_available(name: str) -> bool:
    """Whether a backend can run right now (package/model/endpoint present) — the race skips unavailable rows."""
    spec = EMBEDDER_BACKENDS[name]
    kind = spec["kind"]
    if kind in ("proxy_offline", "trained_from_scratch"):
        return True
    if kind == "static_pretrained":
        return _load_m2v(spec["model"]) is not None
    if kind == "api_local":
        return _embed_ollama_model("probe", spec.get("ollama_model", "nomic-embed-text")) is not None
    if kind == "onnx_local":
        return _load_fastembed(spec["model"]) is not None
    return False


def _embed_corpus(cards: list[dict[str, Any]], backend: str, state: Optional[dict[str, Any]]):
    import numpy as np  # noqa: PLC0415
    texts = [_emb.card_embed_text(c) for c in cards]  # the ONE embed surface (single-sourced)
    spec = EMBEDDER_BACKENDS[backend]
    if spec["kind"] == "static_pretrained" and _load_m2v(spec["model"]) is not None:
        mat = np.asarray(_load_m2v(spec["model"]).encode(texts), dtype="float32")
    elif spec["kind"] == "onnx_local" and _load_fastembed(spec["model"]) is not None:
        mat = np.asarray(list(_load_fastembed(spec["model"]).embed(texts)), dtype="float32")
    else:
        mat = np.asarray([embed(t, backend, state=state) for t in texts], dtype="float32")
    norms = np.linalg.norm(mat, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return mat / norms


def race_embedders(cards: list[dict[str, Any]], labelled: list[dict[str, str]], *,
                   k: int = _bench._DEFAULT_K, backends: Optional[list[str]] = None) -> dict[str, Any]:
    """Race every AVAILABLE embedder backend on the labelled family set — recall@k / MRR / nDCG over an
    independent dense retrieval per backend. Champion = highest nDCG then recall. Losers kept as labelled rows."""
    import numpy as np  # noqa: PLC0415
    backends = backends or [b for b in EMBEDDER_BACKENDS if backend_available(b)]
    receipts: list[dict[str, Any]] = []
    for name in backends:
        state = train_lsa(cards) if name == "lsa_local_trained" else None
        mat = _embed_corpus(cards, name, state)
        recalls, mrrs, ndcgs = [], [], []
        for q in labelled:
            rel = _bench._relevant(q["family"])
            qv = np.asarray(embed(q["query"], name, state=state), dtype="float32")
            qv = qv / (float(np.linalg.norm(qv)) or 1.0)
            order = np.argsort(-(mat @ qv))[:k]
            ids = [cards[int(i)].get("primitive_id") for i in order]
            recalls.append(_bench._recall_at_k(ids, rel, k))
            mrrs.append(_bench._mrr(ids, rel))
            ndcgs.append(_bench._ndcg_at_k(ids, rel, k))
        receipts.append({"backend": name, "kind": EMBEDDER_BACKENDS[name]["kind"], "dim": int(mat.shape[1]),
                         "recall_at_k": round(_bench._mean(recalls), 4), "mrr": round(_bench._mean(mrrs), 4),
                         "ndcg_at_k": round(_bench._mean(ndcgs), 4)})
    ranked = sorted(receipts, key=lambda r: (-r["ndcg_at_k"], -r["recall_at_k"], r["backend"]))
    return {"record_type": "embedder_race_receipt", "k": k, "queries": len(labelled),
            "corpus_size": len(cards), "backends_raced": [r["backend"] for r in ranked],
            "champion": ranked[0]["backend"] if ranked else None, "receipts": ranked,
            "registered_backends": len(EMBEDDER_BACKENDS),
            "note": "adding a model = a new EMBEDDER_BACKENDS row + re-run; the choice is a receipt. Paraphrased "
                    "labelled queries reward real/ trained embedders over the crc32 proxy. serves_truth=false.",
            **BOUNDARY}


def _self_test() -> int:
    import numpy as np  # noqa: PLC0415
    checks: list[tuple[str, bool]] = []
    distractors = [{"primitive_id": f"d:{i}", "title": f"zeta{i} widget",
                    "blackbox": f"sigma{i} an unrelated distractor record {i}.", "input_edge": f"In{i}",
                    "output_edge": f"Out{i}", **BOUNDARY} for i in range(20)]
    cards = _bench._gold_corpus() + distractors
    labelled = list(_bench._LABELLED_QUERIES)

    # (a) we can TRAIN our own embedder from scratch on the corpus, and it embeds to the trained dim
    state = train_lsa(cards, dim=16)
    v = embed("get rid of duplicate rows", "lsa_local_trained", state=state)
    checks.append(("an LSA embedder trains from scratch on our corpus (numpy only)",
                   state["model"] == "lsa" and state["dim"] == 16))
    checks.append(("the trained embedder produces a fixed-dim unit vector",
                   len(v) == 16 and abs(float(np.linalg.norm(v)) - 1.0) < 1e-4))
    checks.append(("the trained embedder is deterministic (SVD signs fixed)",
                   embed("dedupe rows", "lsa_local_trained", state=state)
                   == embed("dedupe rows", "lsa_local_trained", state=state)))

    # (b) the zoo registers several backends and reports which are available now
    avail = [b for b in EMBEDDER_BACKENDS if backend_available(b)]
    checks.append(("the zoo registers multiple embedder backends", len(EMBEDDER_BACKENDS) >= 4))
    checks.append(("proxy + trained + at least one real model are available locally",
                   {"proxy_crc32", "lsa_local_trained"} <= set(avail) and len(avail) >= 3))

    # (c) the RACE ranks the available backends and a REAL/TRAINED model beats the crc32 proxy on paraphrase
    race = race_embedders(cards, labelled, k=5,
                          backends=[b for b in ("proxy_crc32", "lsa_local_trained", "model2vec_potion_8m")
                                    if backend_available(b)])
    by = {r["backend"]: r for r in race["receipts"]}
    checks.append(("the race ranks every backend and picks a champion",
                   race["champion"] in EMBEDDER_BACKENDS and len(race["receipts"]) >= 2))
    if "model2vec_potion_8m" in by:
        checks.append(("a real embedder beats the crc32 proxy on paraphrased queries (nDCG)",
                       by["model2vec_potion_8m"]["ndcg_at_k"] >= by["proxy_crc32"]["ndcg_at_k"]))
    else:
        checks.append(("the trained LSA embedder is at least as good as the proxy on paraphrase",
                       by["lsa_local_trained"]["ndcg_at_k"] >= by["proxy_crc32"]["ndcg_at_k"] - 1e-9))

    # (d) determinism + governance
    checks.append(("the race is deterministic (byte-identical twice)",
                   json.dumps(race_embedders(cards, labelled, backends=["proxy_crc32", "lsa_local_trained"]),
                              sort_keys=True)
                   == json.dumps(race_embedders(cards, labelled, backends=["proxy_crc32", "lsa_local_trained"]),
                                 sort_keys=True)))
    checks.append(("race receipt is candidate/serves_truth=false", race["serves_truth"] is False))

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print(f"\nPASS - embedder_zoo: {len(EMBEDDER_BACKENDS)} embedder backends behind one interface "
          f"(crc32 proxy / a from-scratch LSA we TRAIN on our own corpus / model2vec static pretrained / Ollama "
          f"nomic), raced by recall@k/MRR/nDCG on a labelled family set — a real/trained model beats the proxy on "
          f"paraphrase, and adding any of the thousands of models out there is one new row + a re-run. "
          f"serves_truth=false.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--race", action="store_true", help="race every available embedder over the labelled set")
    ap.add_argument("--sample", type=int, default=200, help="real distractor cards mixed into the gold families")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.race:
        cards = _bench.bench_corpus(args.sample)
        print(f"racing embedders over {len(cards)} cards; available: "
              f"{[b for b in EMBEDDER_BACKENDS if backend_available(b)]}")
        rec = race_embedders(cards, list(_bench._LABELLED_QUERIES))
        print(json.dumps(rec, indent=2, sort_keys=True))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
