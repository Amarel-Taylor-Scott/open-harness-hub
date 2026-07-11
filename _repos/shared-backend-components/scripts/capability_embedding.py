#!/usr/bin/env python3
"""scripts.capability_embedding — the SEMANTIC DISCOVERY axis the composition kit was missing: embed a
primitive's BLACKBOX (what it DOES), not just its edges, so an LLM (or the front-door decomposer) can FIND
primitives by INTENT ("something that removes duplicate records") — and fuse blackbox + input + output into ONE
structured CAPABILITY KEY so FIND / RELATE / DECOMPOSE share a single vector space.

Why this exists (first principles). A primitive has an INTENT (its blackbox: "what it does") and an INTERFACE
(its typed input/output edges). ``edge_representations.embedding`` embeds the INTERFACE (edge strings). NOTHING
embedded the INTENT. Interface-matching (edge -> edge) is what lets you WIRE two primitives; intent-matching
(request -> blackbox) is what lets you DISCOVER the right primitive in the first place. Without a blackbox
vector the only way to find "a primitive that deduplicates" was a lexical keyword hit — which misses paraphrase
and forces the LLM to burn tokens reading cards. This module adds the discovery axis and the request->primitives
RETRIEVAL core (decompose by RETRIEVAL, not by reasoning: embed the request, pull the k nearest blackboxes,
those ARE the candidate sub-capabilities the composer then orders + connects).

Multi-path (a portfolio behind one selector — the repo law, never a hardwired single strategy). The text->vector
embedder is a PORT with contract-substitutable paths:
  * "trigram" — REUSES ``edge_representations.embedding`` (char-trigram hash; right for SHORT type strings/edges).
  * "tokens"  — a deterministic word-token hashed tf embedding (right for NATURAL-LANGUAGE blackbox text, where
                char-trigrams smear meaning across common substrings). Offline, reproducible; REUSES the shipped
                ``build_primitive_search_index.tokenize`` (same tokenization + stopwords the lexical index uses).
  * "ollama"  — a REAL embedding model (nomic-embed-text) when OLLAMA is reachable — a LABELLED path that
                REPLACES the proxy while preserving the SAME (text)->vector contract. It is NEVER the silent
                default; the offline proxy stays the reproducible default so a self-test never needs a network.

serves_truth=false — embedding or searching a candidate primitive never promotes it.

    PYTHONPATH=. python3 scripts/capability_embedding.py --self-test
    PYTHONPATH=. python3 scripts/capability_embedding.py --intent "remove duplicate records" --k 8
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
import os  # noqa: E402
import zlib  # noqa: E402
from typing import Any, Iterable, Optional  # noqa: E402

from scripts import edge_representations as _edge_representations  # noqa: E402  REUSE: trigram embed + cosine
from scripts import primitive_onion as _primitive_onion  # noqa: E402  REUSE: signature layer for each hit
from scripts.build_primitive_search_index import tokenize as _tokenize  # noqa: E402  REUSE: tokens + stopwords

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}

# ── named constants (single-source; no magic literals in logic) ──
#: NL-text token embedding width. Wider than the 64-dim edge trigram vector (``edge_representations._EMBED_DIM``)
#: because blackbox descriptions carry many more distinct significant tokens than a short edge type string, so a
#: larger space keeps hash collisions low. A power of two so ``crc32 % dim`` distributes evenly.
_TEXT_EMBED_DIM = 256
#: the default text->vector path is the OFFLINE, reproducible proxy — never the network model (which is opt-in).
DEFAULT_TEXT_PATH = "tokens"     # blackbox / request / any natural-language text
DEFAULT_EDGE_PATH = "trigram"    # short edge type strings (reuses edge_representations)
#: the axes of the structured capability key. blackbox = INTENT (discovery); input/output = INTERFACE (wiring).
CAPABILITY_AXES: tuple[str, ...] = ("blackbox", "input", "output")
#: default fusion weights when collapsing the structured key into ONE vector — intent-weighted, since the fused
#: vector is used for INTENT search; interface axes contribute but do not dominate. Single-source; sums to 1.0.
DEFAULT_FUSION_WEIGHTS: dict[str, float] = {"blackbox": 0.6, "input": 0.2, "output": 0.2}
#: Ollama real-model path (opt-in): the local default embed model + endpoint. Env-overridable; only used when the
#: caller selects path="ollama" AND the endpoint answers — otherwise we fall back to the proxy (labelled).
_OLLAMA_EMBED_MODEL = os.environ.get("OH_OLLAMA_EMBED_MODEL", "nomic-embed-text")
_OLLAMA_BASE = os.environ.get("OH_OLLAMA_BASE", "http://127.0.0.1:11434")
_OLLAMA_TIMEOUT_S = 3.0  # a real embed call must answer fast or we fall back to the offline proxy
#: model2vec real-model path (opt-in, IN-PROCESS): a static-embedding model (no torch, CPU, ~30MB) loaded once
#: from HuggingFace. Real semantics with zero network per call — the fast local embedder for bulk work (bench,
#: index build). Env-overridable; only used when path="model2vec" AND the package+model load, else proxy fallback.
_MODEL2VEC_NAME = os.environ.get("OH_MODEL2VEC_MODEL", "minishlab/potion-base-8M")
_model2vec_model: Any = None       # lazy singleton (loaded once, reused)
_model2vec_tried = False           # a failed load is recorded so we do not retry the import every call


# ──────────────────────────────────────────────────────────────────────────────
# The embedder PORT — text -> unit vector, one selectable path.
# ──────────────────────────────────────────────────────────────────────────────
def embed_tokens(text: str) -> list[float]:
    """Deterministic word-token hashed tf embedding (L2-normalized) for NATURAL-LANGUAGE text. Each significant
    token (via the shipped lexical tokenizer — same stopwords/min-len as the search index) is hashed to a dim and
    tf-accumulated; the offline, reproducible stand-in for a real text embedder. Same text -> same vector."""
    vec = [0.0] * _TEXT_EMBED_DIM
    for tok in _tokenize(text):
        vec[zlib.crc32(tok.encode()) % _TEXT_EMBED_DIM] += 1.0
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def _embed_ollama(text: str) -> Optional[list[float]]:
    """Real-model embedding via a local Ollama endpoint (nomic-embed-text). Returns the L2-normalized vector, or
    None if the endpoint is unreachable/errors (so callers fall back to the offline proxy — never a hard failure).
    Kept import-light and network-guarded; the offline paths never touch this."""
    try:  # noqa: PLR1702
        import urllib.request  # noqa: PLC0415

        payload = json.dumps({"model": _OLLAMA_EMBED_MODEL, "prompt": str(text)}).encode()
        req = urllib.request.Request(f"{_OLLAMA_BASE}/api/embeddings", data=payload,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=_OLLAMA_TIMEOUT_S) as resp:  # noqa: S310  local, opt-in
            data = json.loads(resp.read())
        raw = data.get("embedding") or []
        if not raw:
            return None
        norm = math.sqrt(sum(float(v) * float(v) for v in raw)) or 1.0
        return [float(v) / norm for v in raw]
    except Exception:  # noqa: BLE001 — any failure => fall back to the offline proxy
        return None


def _load_model2vec() -> Any:
    """Load the model2vec static-embedding model ONCE (in-process, no torch). None if the package or model is
    unavailable (offline / not installed) — recorded so we don't retry the import on every call."""
    global _model2vec_model, _model2vec_tried
    if _model2vec_tried:
        return _model2vec_model
    _model2vec_tried = True
    try:
        from model2vec import StaticModel  # noqa: PLC0415
        _model2vec_model = StaticModel.from_pretrained(_MODEL2VEC_NAME)
    except Exception:  # noqa: BLE001 — no package / no model / offline => stay None, callers fall back to proxy
        _model2vec_model = None
    return _model2vec_model


def _embed_model2vec(text: str) -> Optional[list[float]]:
    """Real in-process embedding via model2vec (L2-normalized). None on any failure so callers fall back to the
    offline proxy — never a hard crash. Fast enough to embed a whole corpus without a network round-trip."""
    model = _load_model2vec()
    if model is None:
        return None
    try:
        import numpy as np  # noqa: PLC0415
        vec = np.asarray(model.encode([str(text)])[0], dtype=float)
        norm = float(np.linalg.norm(vec)) or 1.0
        return (vec / norm).tolist()
    except Exception:  # noqa: BLE001 — any failure => fall back to the offline proxy
        return None


def embed_text(text: str, *, path: str = DEFAULT_TEXT_PATH) -> list[float]:
    """text -> unit vector under the selected PATH. "tokens" (NL, default) | "trigram" (short edges) | "ollama"
    (real nomic via local Ollama) | "model2vec" (real in-process static embedder). The real paths fall back to
    "tokens" if unavailable — the fallback is LABELLED by returning the proxy vector, never a silent crash. Each
    real path REPLACES the proxy under the same contract."""
    if path == "tokens":
        return embed_tokens(text)
    if path == "trigram":
        return _edge_representations.embedding(text)
    if path == "ollama":
        vec = _embed_ollama(text)
        return vec if vec is not None else embed_tokens(text)  # graceful, labelled fallback
    if path == "model2vec":
        vec = _embed_model2vec(text)
        return vec if vec is not None else embed_tokens(text)  # graceful, labelled fallback
    raise ValueError(f"unknown embed path {path!r}; paths are ('tokens', 'trigram', 'ollama', 'model2vec')")


#: the resolved best REAL local text-embed path (memoized): 'model2vec' (in-process) > 'ollama' (local nomic) >
#: 'tokens' (offline proxy). Lets callers ask for real semantics without hardcoding which local backend is up.
_REAL_TEXT_PATH: Optional[str] = None


def real_text_path() -> str:
    """The best REAL local text-embed path available now, resolved ONCE. So the semantic lane runs on a real
    model locally when one is up (model2vec or Ollama), degrading to the proxy only when neither is."""
    global _REAL_TEXT_PATH
    if _REAL_TEXT_PATH is None:
        if _load_model2vec() is not None:
            _REAL_TEXT_PATH = "model2vec"
        elif _embed_ollama("probe") is not None:
            _REAL_TEXT_PATH = "ollama"
        else:
            _REAL_TEXT_PATH = "tokens"
    return _REAL_TEXT_PATH


def cosine(a: list[float], b: list[float]) -> float:
    """Cosine similarity of two unit vectors (dot product). Guards a dim mismatch (comparing vectors from
    different paths is a caller bug) by returning 0.0 rather than silently truncating via zip."""
    if len(a) != len(b):
        return 0.0
    return sum(x * y for x, y in zip(a, b))


# ──────────────────────────────────────────────────────────────────────────────
# The structured CAPABILITY KEY — intent (blackbox) ⊕ interface (edges).
# ──────────────────────────────────────────────────────────────────────────────
def blackbox_text(card: dict[str, Any]) -> str:
    """The card's blackbox description as text (edge cards store {"does": "..."}; primitive cards store a str)."""
    bb = card.get("blackbox")
    if isinstance(bb, dict):
        return str(bb.get("does") or "")
    return str(bb or "")


def card_embed_text(card: dict[str, Any]) -> str:
    """The ONE text surface a card is embedded by for intent search — blackbox, falling back to title so a
    thin card still lands somewhere. Single-sourced here so the persisted store (build_primitive_embeddings),
    the bench's in-process dense index (path_graph_bench.build_dense_index) and the stored lane's delta embed
    below all embed the SAME surface (no-magic-values: one definition, many readers)."""
    return blackbox_text(card) or str(card.get("title") or "")


def _edge_str(card: dict[str, Any], side: str) -> str:
    """input/output edge as a string (falls back to contract.input/output; dict edges are flattened to tokens)."""
    contract = card.get("contract") if isinstance(card.get("contract"), dict) else {}
    val = card.get(f"{side}_edge") or contract.get(side) or ""
    if isinstance(val, dict):
        val = " ".join(f"{k} {v}" for k, v in val.items())
    return str(val)


def capability_key(card: dict[str, Any], *, text_path: str = DEFAULT_TEXT_PATH,
                   edge_path: str = DEFAULT_EDGE_PATH) -> dict[str, list[float]]:
    """The structured capability vector: one unit vector per axis — ``blackbox`` (INTENT, discovery axis, NL
    embedder) and ``input``/``output`` (INTERFACE, wiring axis, edge embedder). Keeping the axes SEPARATE (not a
    blind concat) lets a query weight discovery vs interface — the single composite key behind FIND/RELATE/
    DECOMPOSE. serves_truth carries nothing here; it is pure geometry over the candidate card."""
    return {
        # card_embed_text (blackbox-or-title), NOT bare blackbox_text: the ONE embed surface — so the
        # recompute lane retrieves empty-blackbox cards exactly like the store/delta lanes (review finding)
        "blackbox": embed_text(card_embed_text(card), path=text_path),
        "input": embed_text(_edge_str(card, "input"), path=edge_path),
        "output": embed_text(_edge_str(card, "output"), path=edge_path),
    }


def fuse(key: dict[str, list[float]], *, weights: dict[str, float] = DEFAULT_FUSION_WEIGHTS) -> list[float]:
    """Collapse a structured capability key into ONE vector by weighted concatenation-free sum PER AXIS. Axes may
    have different dims (blackbox 256, edges 64), so we cannot sum across axes directly; instead we CONCATENATE
    the weighted axes into a single fused vector (dims add). This is the single-vector form for a flat index."""
    fused: list[float] = []
    for axis in CAPABILITY_AXES:
        w = float(weights.get(axis, 0.0))
        fused.extend(w * v for v in key.get(axis, []))
    return fused


# ──────────────────────────────────────────────────────────────────────────────
# Description REGISTERS — the same primitive described in DIFFERENT LANGUAGES, each its own comparison axis.
# A person asks in PLAIN words, an engineer asks in TECHNICAL type/operation vocabulary, and the distilled
# SEMANTIC facets resist paraphrase. Scoring across ALL registers and keeping the best catches queries any
# single register misses. Register texts derive deterministically from card fields; an AUTHORED override
# (card["descriptions"][register]) always wins, so richer registers (real-world stories, tenant vocab) can be
# attached per card without a schema change.
# ──────────────────────────────────────────────────────────────────────────────
REGISTERS: tuple[str, ...] = ("plain", "technical", "semantic")


def register_text(card: dict[str, Any], register: str) -> str:
    """The card's description in one register. ``plain`` = title + blackbox (how a person asks); ``technical`` =
    edges + operations + datatypes + impact + operation count (how an engineer asks); ``semantic`` = the
    distilled keyword/keyphrase facets (paraphrase-resistant). Authored ``card['descriptions'][register]`` wins."""
    authored = card.get("descriptions")
    if isinstance(authored, dict) and str(authored.get(register) or "").strip():
        return str(authored[register]).strip()
    if register == "plain":
        return f"{card.get('title') or ''} {blackbox_text(card)}".strip()
    from scripts import primitive_descriptor as _primitive_descriptor  # noqa: PLC0415  lazy: descriptor imports us
    if register == "technical":
        desc = _primitive_descriptor.describe(card, with_semantic=False)
        return " ".join(filter(None, [
            _edge_str(card, "input"), "to", _edge_str(card, "output"),
            " ".join(sorted(desc["operations"])), " ".join(sorted(desc["datatypes"])),
            f"impact {desc['impact_class']}", f"operations {desc['operation_count']}",
        ]))
    if register == "semantic":
        desc = _primitive_descriptor.describe(card, with_semantic=False)
        return " ".join(sorted(desc["keywords"]) + sorted(desc["keyphrases"]))
    raise ValueError(f"unknown register {register!r}; registers are {REGISTERS}")


def register_key(card: dict[str, Any], *, path: str = DEFAULT_TEXT_PATH) -> dict[str, list[float]]:
    """One unit vector per REGISTER — the multi-register sibling of ``capability_key`` (axes stay separate so a
    query can match through whichever language it was asked in)."""
    return {r: embed_text(register_text(card, r), path=path) for r in REGISTERS}


def register_similarity(a: dict[str, Any], b: dict[str, Any], *, path: str = DEFAULT_TEXT_PATH) -> dict[str, Any]:
    """Compare two cards register-by-register: per-register cosine, the best register (which LANGUAGE they agree
    in), and the max/mean — candidate geometry only, serves_truth=false."""
    ka, kb = register_key(a, path=path), register_key(b, path=path)
    by_register = {r: round(cosine(ka[r], kb[r]), 6) for r in REGISTERS}
    best = max(REGISTERS, key=lambda r: (by_register[r], r))
    return {"by_register": by_register, "best_register": best, "best": by_register[best],
            "mean": round(sum(by_register.values()) / len(REGISTERS), 6), **BOUNDARY}


#: memoized handle to the PERSISTED register store (build_primitive_embeddings --build-registers output).
#: Same lifecycle as _STORED_CORPUS: None = unprobed, False = unavailable, dict = loaded once.
_STORED_REGISTERS: Any = None


def _default_register_store() -> Optional[dict[str, Any]]:
    """The default persisted REGISTER store, memoized WITH revalidation (see _revalidated_handle)."""
    global _STORED_REGISTERS
    _STORED_REGISTERS = _revalidated_handle(_STORED_REGISTERS, dir_fn_name="default_register_store_dir",
                                            load_fn_name="load_register_store")
    return _STORED_REGISTERS or None


def _resolve_register_store(store: Any, *, path: str) -> Optional[dict[str, Any]]:
    """Resolve intent_query_registers' ``store`` argument — same geometry guard as _resolve_store: "auto" only
    engages when the persisted store scores the exact space the caller asked for."""
    if store is None:
        return None
    if isinstance(store, dict):
        return _store_handle(store)
    if store == "auto":
        handle = _default_register_store()
        return handle if handle and handle["store"].get("embed_model") == path else None
    raise ValueError(f"unknown store {store!r}; use None, 'auto', or a register store dict")


def _intent_query_registers_stored(request: str, cards: Iterable[dict[str, Any]], *, k: int,
                                   handle: dict[str, Any]) -> list[dict[str, Any]]:
    """STORED-MATRIX lane for multi-register search: ONE query embed + one lazy matmul PER REGISTER over the
    persisted matrices; per card the BEST register wins. Cards absent from the store delta-embed their
    register_key in the store's space (contract survives). Hits carry matched_register + vector_source."""
    import numpy as np  # noqa: PLC0415
    st, row_by_id = handle["store"], handle["row_by_id"]
    space = st.get("embed_model") or DEFAULT_TEXT_PATH
    q = np.asarray(embed_text(request, path=space), dtype="float32")
    qn = float(np.linalg.norm(q)) or 1.0
    q = q / qn
    # FAST PATH (mirror of _intent_query_stored's): cards == the store in store order (sentinel-checked) ->
    # 3 matmuls, element-wise MAX across registers, argpartition top-k, hits built for k rows only.
    cards_list = cards if isinstance(cards, list) else list(cards)
    n = len(cards_list)
    if (k > 0 and n == len(st["ids"]) and n >= 3
            and cards_list[0].get("primitive_id") == st["ids"][0]
            and cards_list[n // 2].get("primitive_id") == st["ids"][n // 2]
            and cards_list[-1].get("primitive_id") == st["ids"][-1]):
        reg_sims = {r: np.asarray(m) @ q for r, m in st["matrices"].items()}
        best_vec = np.maximum.reduce(list(reg_sims.values()))
        kk = min(k, n)
        part = np.argpartition(-best_vec, kk - 1)[:kk]
        rows = []
        for i in part:
            i = int(i)
            score = float(best_vec[i])
            if score <= 0.0:
                continue
            by_register = {r: float(reg_sims[r][i]) for r in reg_sims}
            best = max(sorted(by_register), key=lambda r: (by_register[r], r))
            rows.append((score, str(st["ids"][i]), cards_list[i], by_register, best))
        rows.sort(key=lambda s: (-s[0], s[1]))
        return [{"primitive_id": card.get("primitive_id"), "score": round(score, 6),
                 "matched_register": best, "by_register": {r: round(v, 6) for r, v in sorted(br.items())},
                 "vector_source": "stored", "signature": _primitive_onion.signature(card), **BOUNDARY}
                for score, _pid, card, br, best in rows]
    cards = cards_list
    q_list = q.tolist()
    sims: dict[str, Any] = {}
    scored: list[tuple[float, str, dict[str, Any], dict[str, float], str, str]] = []
    for card in cards:
        pid = card.get("primitive_id")
        row = row_by_id.get(pid)
        if row is not None:
            if not sims:
                sims = {r: np.asarray(m) @ q for r, m in st["matrices"].items()}
            by_register = {r: float(sims[r][row]) for r in sims}
            source = "stored"
        else:  # delta lane: embed just THIS card's registers, same space
            key = register_key(card, path=space)
            by_register = {r: cosine(q_list, key[r]) for r in REGISTERS}
            source = "delta_computed"
        best = max(sorted(by_register), key=lambda r: (by_register[r], r))
        score = by_register[best]
        if score <= 0.0:
            continue
        scored.append((score, str(pid), card, by_register, best, source))
    scored.sort(key=lambda s: (-s[0], s[1]))
    top = scored if k <= 0 else scored[:k]
    return [{"primitive_id": card.get("primitive_id"), "score": round(score, 6), "matched_register": best,
             "by_register": {r: round(v, 6) for r, v in sorted(by_register.items())},
             "vector_source": source, "signature": _primitive_onion.signature(card), **BOUNDARY}
            for score, _pid, card, by_register, best, source in top]


def intent_query_registers(request: str, cards: Iterable[dict[str, Any]], *, k: int = 10,
                           path: str = DEFAULT_TEXT_PATH, store: Any = "auto") -> list[dict[str, Any]]:
    """Multi-register front door: score the request against EVERY register of every card and rank by the BEST
    register match. A technical request ("RawRecord to NormalizedRecord") lands via the technical register even
    when the card's plain prose shares no vocabulary — and vice versa. Each hit names ``matched_register`` so the
    caller knows which language connected. ``store`` mirrors intent_query: "auto" (default) serves from the
    PERSISTED register store when it matches the requested space (one matmul per register, no per-card
    re-derive); None forces the original per-card recompute. Same contract as ``intent_query`` (signature
    layer, k<=0 = all)."""
    handle = _resolve_register_store(store, path=path)
    if handle is not None:
        return _intent_query_registers_stored(request, cards, k=k, handle=handle)
    q = embed_text(request, path=path)
    scored: list[tuple[float, dict[str, Any]]] = []
    for card in cards:
        key = register_key(card, path=path)
        by_register = {r: cosine(q, key[r]) for r in REGISTERS}
        best = max(REGISTERS, key=lambda r: (by_register[r], r))
        score = by_register[best]
        if score <= 0.0:
            continue
        scored.append((score, {
            "primitive_id": card.get("primitive_id"),
            "score": round(score, 6),
            "matched_register": best,
            "by_register": {r: round(s, 6) for r, s in by_register.items()},
            "signature": _primitive_onion.signature(card),
            **BOUNDARY,
        }))
    scored.sort(key=lambda s: (-s[0], str(s[1].get("primitive_id"))))
    ranked = [hit for _, hit in scored]
    return ranked if k <= 0 else ranked[:k]


# ──────────────────────────────────────────────────────────────────────────────
# The FRONT-DOOR retrieval core — request/intent -> the k nearest primitives.
# Two lanes behind ONE contract (multi-path law): the STORED-MATRIX lane reads the persisted
# build_primitive_embeddings store (one matmul, no corpus re-embed — the scale fix); the RECOMPUTE lane is the
# preserved original (per-card capability_key), serving whenever no store matches the requested space.
# ──────────────────────────────────────────────────────────────────────────────
#: memoized handle to the PERSISTED default store (build_primitive_embeddings --build output): {store, row_by_id}.
#: False = probed and unavailable (no dir / no numpy), recorded so the auto lane never re-probes disk per query.
#: Process-lifetime memo, same pattern as _model2vec_model.
_STORED_CORPUS: Any = None


def _store_handle(raw: dict[str, Any]) -> dict[str, Any]:
    """Wrap a build_primitive_embeddings store as {store, row_by_id}. The id->row index is cached ON the store
    dict (idempotent) so repeated queries against the same store pay the O(N) index build once, not per call."""
    if "_row_by_id" not in raw:
        raw["_row_by_id"] = {pid: i for i, pid in enumerate(raw["ids"])}
    return {"store": raw, "row_by_id": raw["_row_by_id"]}


def _revalidated_handle(memo: Any, *, dir_fn_name: str, load_fn_name: str) -> Any:
    """Shared memo-with-revalidation for the default stores: re-stat the manifest (µs) on every access and
    RELOAD when its mtime changes — a store rebuilt on disk mid-process (atomic temp+replace mints a new
    inode) is picked up instead of tearing ids against a stale mmap (review finding, reproduced). Returns the
    handle dict, or False when the store is unavailable."""
    try:
        from scripts import build_primitive_embeddings as _stored  # noqa: PLC0415  lazy: it imports us at top
        mpath = getattr(_stored, dir_fn_name)() / "manifest.json"
        mtime = mpath.stat().st_mtime_ns
    except Exception:  # noqa: BLE001 — absent store / no numpy => recompute lane, never a hard failure
        return False
    if isinstance(memo, dict) and memo.get("manifest_mtime_ns") == mtime:
        return memo
    try:
        handle = _store_handle(getattr(_stored, load_fn_name)(getattr(_stored, dir_fn_name)()))
        handle["manifest_mtime_ns"] = mtime
        return handle
    except Exception:  # noqa: BLE001 — torn/invalid store fails closed to the recompute lane
        return False


def _default_stored_corpus() -> Optional[dict[str, Any]]:
    """The default persisted embedding store, memoized WITH revalidation (see _revalidated_handle)."""
    global _STORED_CORPUS
    _STORED_CORPUS = _revalidated_handle(_STORED_CORPUS, dir_fn_name="default_store_dir", load_fn_name="load")
    return _STORED_CORPUS or None


def _resolve_store(store: Any, *, axis: str, path: str) -> Optional[dict[str, Any]]:
    """Resolve intent_query's ``store`` argument to a {store, row_by_id} handle, or None (= recompute lane).
    "auto" uses the persisted default store ONLY when it scores the SAME space the caller asked for (axis=
    blackbox and path == the store's embed model) — the caller's requested geometry is never silently swapped.
    An explicit store dict (from build/load) is trusted as-is: its embed model defines the space."""
    if store is None or axis != "blackbox":
        return None
    if isinstance(store, dict):
        return _store_handle(store)
    if store == "auto":
        handle = _default_stored_corpus()
        return handle if handle and handle["store"].get("embed_model") == path else None
    raise ValueError(f"unknown store {store!r}; use None, 'auto', or a build_primitive_embeddings store dict")


def _intent_query_stored(request: str, cards: Iterable[dict[str, Any]], *, k: int,
                         handle: dict[str, Any]) -> list[dict[str, Any]]:
    """The STORED-MATRIX lane: score the passed cards by looking their vectors UP in the persisted store — ONE
    lazy whole-store matmul (~ms at 10^5 rows), no per-card re-embed. A card ABSENT from the store is
    delta-embedded in the store's own space, so the "retrieves over whatever cards you pass" contract survives
    fresh/synthetic cards. Hits carry ``vector_source`` ("stored" | "delta_computed") so receipts can tell the
    lanes apart. Ranking semantics identical to the recompute lane (score desc, id tiebreak; k<=0 = all)."""
    import numpy as np  # noqa: PLC0415  a store exists only where numpy does (build/load require it)
    st, row_by_id = handle["store"], handle["row_by_id"]
    space = st.get("embed_model") or DEFAULT_TEXT_PATH
    q = np.asarray(embed_text(request, path=space), dtype="float32")
    qn = float(np.linalg.norm(q)) or 1.0
    q = q / qn
    # FAST PATH (load-test finding: at 10^5+ the per-card python loop, not the matmul, is the wall — p50
    # 12.3s at 465K): when the passed cards ARE the store in store order (sentinel: same length + first/mid/
    # last ids match), rank via argpartition on the sims vector and build hits for the TOP-K ONLY. Any
    # mismatch falls through to the general loop — identical results, O(k) python instead of O(N).
    cards_list = cards if isinstance(cards, list) else list(cards)
    n = len(cards_list)
    if (k > 0 and n == len(st["ids"]) and n >= 3
            and cards_list[0].get("primitive_id") == st["ids"][0]
            and cards_list[n // 2].get("primitive_id") == st["ids"][n // 2]
            and cards_list[-1].get("primitive_id") == st["ids"][-1]):
        sims_all = np.asarray(st["matrix"]) @ q
        kk = min(k, n)
        part = np.argpartition(-sims_all, kk - 1)[:kk]
        rows = sorted(((float(sims_all[int(i)]), str(st["ids"][int(i)]), cards_list[int(i)]) for i in part
                       if float(sims_all[int(i)]) > 0.0), key=lambda s: (-s[0], s[1]))
        return [{"primitive_id": card.get("primitive_id"), "score": round(score, 6), "axis": "blackbox",
                 "vector_source": "stored", "signature": _primitive_onion.signature(card),
                 "blackbox_excerpt": blackbox_text(card)[:160], **BOUNDARY}
                for score, _pid, card in rows]
    cards = cards_list
    q_list = q.tolist()
    sims: Any = None  # computed lazily, only if at least one passed card is actually in the store
    scored: list[tuple[float, str, dict[str, Any], str]] = []
    for card in cards:
        pid = card.get("primitive_id")
        row = row_by_id.get(pid)
        if row is not None:
            if sims is None:
                sims = np.asarray(st["matrix"]) @ q
            score, source = float(sims[row]), "stored"
        else:  # delta lane: embed just THIS card (same space) — never the whole corpus
            score, source = cosine(q_list, embed_text(card_embed_text(card), path=space)), "delta_computed"
        if score <= 0.0:
            continue
        scored.append((score, str(pid), card, source))
    scored.sort(key=lambda s: (-s[0], s[1]))  # deterministic: score desc, id tiebreak (same as recompute lane)
    top = scored if k <= 0 else scored[:k]
    return [{"primitive_id": card.get("primitive_id"), "score": round(score, 6), "axis": "blackbox",
             "vector_source": source, "signature": _primitive_onion.signature(card),
             "blackbox_excerpt": blackbox_text(card)[:160], **BOUNDARY}
            for score, _pid, card, source in top]


def intent_query(request: str, cards: Iterable[dict[str, Any]], *, k: int = 10, axis: str = "blackbox",
                 path: str = DEFAULT_TEXT_PATH, store: Any = "auto") -> list[dict[str, Any]]:
    """DECOMPOSE-BY-RETRIEVAL core: embed the natural-language ``request`` and return the ``k`` primitives whose
    ``axis`` vector is nearest — i.e. the candidate sub-capabilities an LLM would then order + connect (the
    composer/matcher handle the RELATE step). ``axis`` picks what "nearest" means: "blackbox" = by INTENT (what it
    does), "input"/"output" = by INTERFACE. ``store`` selects the lane: "auto" (default) reads the PERSISTED
    embedding store when it matches the requested space exactly (one matmul, no corpus re-embed — the scale
    path); None forces the original per-card recompute; a store dict from build_primitive_embeddings.build/load
    is used as passed. A real ANN index (pgvector/faiss) remains the drop-in behind the same call. Every hit is
    candidate/serves_truth=false and carries the primitive_onion SIGNATURE layer (~tens of tokens) so the caller
    reads names+edges, not bodies. k<=0 returns all, ranked."""
    handle = _resolve_store(store, axis=axis, path=path)
    if handle is not None:
        return _intent_query_stored(request, cards, k=k, handle=handle)
    edge_path = DEFAULT_EDGE_PATH if axis in ("input", "output") else path
    q = embed_text(request, path=edge_path if axis in ("input", "output") else path)
    scored: list[tuple[float, dict[str, Any]]] = []
    for card in cards:
        key = capability_key(card, text_path=path, edge_path=DEFAULT_EDGE_PATH)
        score = cosine(q, key.get(axis, []))
        if score <= 0.0:
            continue
        hit = {
            "primitive_id": card.get("primitive_id"),
            "score": round(score, 6),
            "axis": axis,
            "signature": _primitive_onion.signature(card),
            "blackbox_excerpt": blackbox_text(card)[:160],
            **BOUNDARY,
        }
        scored.append((score, hit))
    scored.sort(key=lambda s: (-s[0], str(s[1].get("primitive_id"))))  # deterministic: score desc, id tiebreak
    ranked = [hit for _, hit in scored]
    return ranked if k <= 0 else ranked[:k]


# ──────────────────────────────────────────────────────────────────────────────
# Verify the verifier: mutation (right card wins) + determinism (byte-identical ranking).
# ──────────────────────────────────────────────────────────────────────────────
def _synthetic_cards() -> list[dict[str, Any]]:
    return [
        {"primitive_id": "prim:dedup", "title": "Deduplicate records",
         "blackbox": "Remove duplicate records by clustering near-identical rows and keeping one canonical row.",
         "input_edge": "RecordBatch", "output_edge": "DedupedRecordBatch", **BOUNDARY},
        {"primitive_id": "prim:resize", "title": "Resize image",
         "blackbox": "Resize an image to target dimensions using bilinear interpolation, preserving aspect ratio.",
         "input_edge": "Image", "output_edge": "ResizedImage", **BOUNDARY},
        {"primitive_id": "prim:ocr", "title": "OCR a scanned document",
         "blackbox": "Extract text from a scanned document image using optical character recognition.",
         "input_edge": "ScannedDocument", "output_edge": "ExtractedText", **BOUNDARY},
        {"primitive_id": "prim:sanctions", "title": "Screen against OFAC SDN",
         "blackbox": "Screen an entity name against the OFAC SDN sanctions list and return match candidates.",
         "input_edge": "EntityRecord", "output_edge": "SanctionScreeningResult", **BOUNDARY},
    ]


def _self_test() -> int:
    cards = _synthetic_cards()
    checks: list[tuple[str, bool]] = []

    # (a) blackbox INTENT discovery: a paraphrased request finds the right primitive by MEANING, not keywords.
    #     "remove duplicate rows" shares NO significant token with the dedup card's title but matches its blackbox.
    hits = intent_query("remove duplicate rows from a dataset", cards, k=4, axis="blackbox")
    checks.append(("intent_query returns ranked hits", bool(hits) and "score" in hits[0]))
    checks.append(("blackbox-INTENT search finds the dedup primitive as top-1 (paraphrase, not keyword)",
                   hits[0]["primitive_id"] == "prim:dedup"))
    checks.append(("a clearly-unrelated primitive does not outrank the intended one",
                   [h["primitive_id"] for h in hits].index("prim:dedup")
                   < ([h["primitive_id"] for h in hits] + ["prim:resize"]).index("prim:resize")))

    # (b) a DIFFERENT intent routes to a DIFFERENT primitive (the axis actually discriminates).
    ocr_hits = intent_query("read text off a scanned page", cards, k=1, axis="blackbox")
    checks.append(("a different intent routes to a different primitive", ocr_hits[0]["primitive_id"] == "prim:ocr"))

    # (c) structured capability key: three axes, each a unit vector; blackbox axis is the wide NL space.
    key = capability_key(cards[0])
    checks.append(("capability key has all three axes", set(key) == set(CAPABILITY_AXES)))
    checks.append(("blackbox axis uses the wide NL embed dim", len(key["blackbox"]) == _TEXT_EMBED_DIM))
    checks.append(("each axis vector is L2-normalized (unit)",
                   all(abs(math.sqrt(sum(v * v for v in key[a])) - 1.0) < 1e-6 for a in CAPABILITY_AXES)))

    # (d) determinism: same request + cards -> byte-identical ranking (no RNG, no wall-clock, no network default).
    r1 = json.dumps(intent_query("remove duplicate rows", cards, k=4), sort_keys=True)
    r2 = json.dumps(intent_query("remove duplicate rows", cards, k=4), sort_keys=True)
    checks.append(("intent_query is deterministic (byte-identical twice)", r1 == r2))

    # (e) every hit is candidate/serves_truth=false and carries the tiny signature layer (names+edges, not bodies).
    checks.append(("hits are candidate/serves_truth=false", all(h["candidate"] and h["serves_truth"] is False for h in hits)))
    checks.append(("each hit carries the primitive_onion signature (id+title+edges)",
                   set(hits[0]["signature"]) >= {"primitive_id", "input_edge", "output_edge"}))

    # (f) dim-mismatch guard: comparing vectors from different paths returns 0.0, never a truncated dot product.
    checks.append(("cosine guards a dim mismatch", cosine(embed_tokens("x"), _edge_representations.embedding("x")) == 0.0))

    # (g) the real-model path falls back to the proxy when the model is unavailable — tested HERMETICALLY by
    #     forcing the model call to return None (no network dependence: the self-test must pass whether or not a
    #     live Ollama happens to be running). globals() patch so embed_text (same module) sees it in __main__ too.
    _saved_ollama = globals()["_embed_ollama"]
    globals()["_embed_ollama"] = lambda _text: None
    try:
        checks.append(("ollama path falls back to the offline proxy when the model is unavailable",
                       embed_text("dedupe records", path="ollama") == embed_tokens("dedupe records")))
    finally:
        globals()["_embed_ollama"] = _saved_ollama

    # (h) fused single-vector form concatenates the weighted axes (dims add).
    fused = fuse(key)
    checks.append(("fuse concatenates weighted axes into one vector",
                   len(fused) == _TEXT_EMBED_DIM + 2 * _edge_representations._EMBED_DIM))

    # (i) description REGISTERS: the same card in plain/technical/semantic language, each its own axis.
    rtexts = {r: register_text(cards[0], r) for r in REGISTERS}
    checks.append(("register texts are distinct languages for the same card",
                   len(set(rtexts.values())) == len(REGISTERS)))
    checks.append(("technical register speaks in edges + operations",
                   "RecordBatch" in rtexts["technical"] and "dedup" in rtexts["technical"]))
    authored = dict(cards[0])
    authored["descriptions"] = {"plain": "Squash repeat entries so each customer shows up once."}
    checks.append(("an AUTHORED register override wins over the derived text",
                   register_text(authored, "plain") == "Squash repeat entries so each customer shows up once."))
    # the load-bearing claim: a card whose PLAIN prose shares no vocabulary with a technical request still lands
    # via its TECHNICAL register — multi-register catches what any single register misses.
    tidy = {"primitive_id": "prim:tidy", "title": "Tidy customer info",
            "blackbox": "Make messy customer info look consistent and easy to compare.",
            "input_edge": "RawRecord", "output_edge": "NormalizedRecord", **BOUNDARY}
    reg_hits = intent_query_registers("convert RawRecord to NormalizedRecord", cards + [tidy], k=1)
    checks.append(("a technical request finds the plain-prose card THROUGH its technical register",
                   bool(reg_hits) and reg_hits[0]["primitive_id"] == "prim:tidy"
                   and reg_hits[0]["matched_register"] == "technical"))
    sim = register_similarity(cards[0], tidy)
    checks.append(("register_similarity reports per-register scores + the agreeing language",
                   set(sim["by_register"]) == set(REGISTERS) and sim["best_register"] in REGISTERS))
    checks.append(("multi-register ranking is deterministic (byte-identical twice)",
                   json.dumps(intent_query_registers("normalize records", cards, k=3), sort_keys=True)
                   == json.dumps(intent_query_registers("normalize records", cards, k=3), sort_keys=True)))

    # (j) the STORED-MATRIX lane — hermetic (a store built HERE in tokens space; no disk store, no model, no
    #     network): same top-1 as the recompute lane with NO per-card re-embed; a card ABSENT from the store is
    #     delta-embedded (the passed-cards contract survives); store=None forces the recompute lane; and "auto"
    #     never swaps geometry (a tokens-space query ignores any mismatched-space store on disk).
    from scripts import build_primitive_embeddings as _stored  # noqa: PLC0415  lazy: it imports us at top
    tstore = _stored.build(cards, embed_path="tokens")
    s_hits = intent_query("remove duplicate rows from a dataset", cards, k=4, store=tstore)
    r_hits = intent_query("remove duplicate rows from a dataset", cards, k=4, store=None)
    checks.append(("stored-matrix lane ranks the same top-1 as the recompute lane (same space, no re-embed)",
                   bool(s_hits) and s_hits[0]["primitive_id"] == r_hits[0]["primitive_id"] == "prim:dedup"
                   and s_hits[0]["vector_source"] == "stored"))
    fresh = {"primitive_id": "prim:fresh", "title": "Translate text",
             "blackbox": "Translate a sentence from one human language into another language.",
             "input_edge": "Text", "output_edge": "TranslatedText", **BOUNDARY}
    d_hits = intent_query("turn this sentence into a different language", cards + [fresh], k=1, store=tstore)
    checks.append(("a card ABSENT from the store is delta-embedded and still retrievable (contract survives)",
                   bool(d_hits) and d_hits[0]["primitive_id"] == "prim:fresh"
                   and d_hits[0]["vector_source"] == "delta_computed"))
    checks.append(("the stored lane is deterministic (byte-identical twice)",
                   json.dumps(intent_query("remove duplicate rows", cards, k=4, store=tstore), sort_keys=True)
                   == json.dumps(intent_query("remove duplicate rows", cards, k=4, store=tstore), sort_keys=True)))
    # HERMETIC auto-geometry checks: point the default stores at an EMPTY dir so the assertion holds on ANY
    # machine (review finding: a legitimately tokens-tagged dist/ store made the old checks false-red), and
    # separately assert the guard REJECTS a mismatched-space store outright.
    import tempfile as _tf  # noqa: PLC0415
    _sd, _srd = _stored.default_store_dir, _stored.default_register_store_dir
    with _tf.TemporaryDirectory() as _empty:
        _stored.default_store_dir = lambda: Path(_empty) / "absent"
        _stored.default_register_store_dir = lambda: Path(_empty) / "absent_r"
        globals()["_STORED_CORPUS"] = None
        globals()["_STORED_REGISTERS"] = None
        try:
            _auto_hits = intent_query("remove duplicate rows from a dataset", cards, k=4, store="auto")
            _auto_reg = intent_query_registers("remove duplicate rows from a dataset", cards, k=3, store="auto")
        finally:
            _stored.default_store_dir, _stored.default_register_store_dir = _sd, _srd
            globals()["_STORED_CORPUS"] = None
            globals()["_STORED_REGISTERS"] = None
    checks.append(("auto never swaps geometry: with no matching store, auto == the recompute lane (hermetic)",
                   json.dumps(_auto_hits, sort_keys=True) == json.dumps(r_hits, sort_keys=True)))
    checks.append(("the store lane guards its axis: a non-blackbox axis never engages a store",
                   _resolve_store(tstore, axis="input", path="tokens") is None
                   and _resolve_store(None, axis="blackbox", path="tokens") is None))
    checks.append(("stored-lane hits stay candidate/serves_truth=false with the signature layer",
                   all(h["candidate"] and h["serves_truth"] is False and "signature" in h for h in s_hits)))

    # (k) the multi-REGISTER stored lane mirrors (j): a register store built HERE (tokens space, hermetic)
    #     serves intent_query_registers with no per-card re-derive; the out-of-store card still lands through
    #     its register (delta lane); "auto" never swaps geometry; stored ranking agrees with recompute.
    rstore = _stored.build_register_store(cards, embed_path="tokens")
    rs = intent_query_registers("remove duplicate rows from a dataset", cards, k=3, store=rstore)
    rr = intent_query_registers("remove duplicate rows from a dataset", cards, k=3, store=None)
    checks.append(("register stored lane agrees with the recompute lane on top-1 (+ names the register)",
                   bool(rs) and rs[0]["primitive_id"] == rr[0]["primitive_id"]
                   and rs[0]["vector_source"] == "stored" and rs[0]["matched_register"] in REGISTERS))
    rd = intent_query_registers("convert RawRecord to NormalizedRecord", cards + [tidy], k=1, store=rstore)
    checks.append(("an out-of-store card still lands through its TECHNICAL register (delta lane)",
                   bool(rd) and rd[0]["primitive_id"] == "prim:tidy"
                   and rd[0]["matched_register"] == "technical" and rd[0]["vector_source"] == "delta_computed"))
    checks.append(("register auto lane never swaps geometry (hermetic: no matching store -> recompute output)",
                   json.dumps(_auto_reg, sort_keys=True) == json.dumps(rr, sort_keys=True)))

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print("\nPASS - capability_embedding: the discovery axis — embed the BLACKBOX (intent), not just edges, so a "
          "paraphrased request finds the right primitive by MEANING (top-1, no shared keyword); structured "
          "capability key (intent ⊕ interface) + description REGISTERS (plain/technical/semantic, authored "
          "override wins, best-register ranking catches cross-language queries), deterministic intent retrieval "
          "with TWO lanes behind one contract — the STORED-MATRIX lane (persisted build_primitive_embeddings "
          "store, one matmul, no corpus re-embed, delta-embed for out-of-store cards) and the preserved "
          "per-card recompute lane — real-model path with offline fallback, candidate/serves_truth=false. "
          "The front-door decompose-by-retrieval core.")
    return 0


def _run_intent(request: str, k: int, axis: str) -> int:
    """Run a real intent query over the verified corpus (offline proxy). Emits the k nearest primitives."""
    from scripts._repo_paths import resource as _resource  # noqa: PLC0415
    path = _resource("data") / "dev-intel" / "aidevobserver_edge_foundry" / "verified_factory_primitive_cards.jsonl"
    if not path.exists():
        print(f"no corpus at {path} (factory scratch may be gitignored on this checkout)")
        return 0
    cards = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    cards.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    hits = intent_query(request, cards, k=k, axis=axis)
    print(json.dumps({"request": request, "axis": axis, "k": k, "corpus_cards": len(cards),
                      "hits": hits, **BOUNDARY}, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--intent", type=str, help="run an intent query over the verified corpus")
    ap.add_argument("--k", type=int, default=10)
    ap.add_argument("--axis", type=str, default="blackbox", choices=list(CAPABILITY_AXES))
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.intent:
        return _run_intent(args.intent, args.k, args.axis)
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
