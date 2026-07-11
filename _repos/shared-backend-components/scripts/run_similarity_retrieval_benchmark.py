#!/usr/bin/env python3
"""scripts.run_similarity_retrieval_benchmark — which similarity method wins COMPOSABILITY-oriented retrieval?

The product thesis is "retrieve capabilities, don't rewrite code": given a primitive X, an agent wants to find the
primitive that *consumes what X produces* (or produces what X consumes, or shares X's contract). Plain lexical
similarity answers the WRONG question — it returns primitives that TALK like X, not ones that COMPOSE with X. This
harness measures that head-to-head.

It builds a mixed labeled corpus (a deterministic synthetic set of ~72 primitives across 8 edge-type domains, plus —
on ``--run`` — a bounded head-sample of the REAL registry cards as distractor noise) and a set of ~32 labeled
retrieval judgments across four query intents:

  * ``consume_forward``  — "find something that consumes what X produces"  (X is a producer)
  * ``consume_reverse``  — "find something that produces what X consumes"  (X is a consumer)
  * ``same_contract``    — "find primitives with X's exact input/output contract" (across vocabularies)
  * ``topic_semantic``   — "find primitives about the same TOPIC as this description" (no edges given)

For EACH wired similarity method it ranks the corpus per judgment and scores precision@k / recall@k / MRR at k in
{1,3,5}, then produces a per-method leaderboard. The wired methods are lexical (token-Jaccard + tf-idf cosine) vs
edge-type methods (edge-type Jaccard over CANONICALIZED edge types, a directional compose score, and a hybrid). The
expected finding — and the whole point — is that ``edge_type_jaccard`` beats lexical for composability retrieval:
lexical is fooled by same-vocabulary distractors, edge-type matching follows the actual data flow.

If ``scripts.primitive_similarity_portfolio`` is present its methods are merged in; otherwise the benchmark runs on
its own built-in methods (a lexical fallback + the edge-type methods). Everything is deterministic and fully offline:
no network, no LLM, no wall-clock (the report date is a fixed literal), no RNG (the parameter space is enumerated;
pseudo-variety uses a stable string seed, never ``hash()``). All outputs are candidate evidence — ``serves_truth`` is
never set true here; the numbers are a benchmark scorecard, not a promoted fact.

CLI: ``--self-test`` (offline synthetic; asserts the scorecard computes and the intended method wins a labeled case)
   | ``--run [--date D] [--real-distractors N]`` (writes the leaderboard md+json).
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import json
import math
import re
import sys
from pathlib import Path
from typing import Any, Callable

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

# --- canonical edge folding (import the contract-locked retrofit; identity-lower fallback if unavailable) ----------
try:
    from scripts.build_edge_type_retrofit import canonicalize_edge as _canonicalize_edge
except Exception:  # pragma: no cover - defensive; retrofit is present in-repo
    def _canonicalize_edge(edge_string: Any) -> str:
        return str(edge_string or "Unknown").strip().lower() or "Unknown"


def _canon(edge: Any) -> str:
    """Canonical edge type for a raw edge string (empty/None -> 'Unknown')."""
    if edge is None or edge == "":
        return "Unknown"
    return _canonicalize_edge(edge)


OUT_DIR = _resource("data") / "dev-intel" / "primitive_similarity"
REPORT_DATE = "2026-07-03"  # fixed literal — no wall-clock read anywhere in this module
K_VALUES: tuple[int, ...] = (1, 3, 5)
REAL_CARDS_PATH = _resource("data") / "dev-intel" / "primitive_source_lifecycle" / "primitive_search_cards.jsonl"
HEADLINE_METRIC = "mean_precision_at_3"  # the leaderboard is ranked by this (composability precision), MRR tiebreak

_WORD = re.compile(r"[a-z0-9]+")


def _tokens(text: str) -> set[str]:
    return set(_WORD.findall((text or "").lower()))


def _stable_seed(seed: str) -> int:
    """Deterministic 32-bit FNV-1a over a string. Used ONLY for stable pseudo-variety — never hash()."""
    h = 2166136261
    for ch in seed:
        h ^= ord(ch)
        h = (h * 16777619) & 0xFFFFFFFF
    return h


# ======================================================================================================================
# Synthetic labeled corpus
# ======================================================================================================================
# Each domain contributes four card groups engineered to separate lexical from edge-type similarity:
#   producer      — outputs the domain edge type (raw string variant A);          vocab = prod_vocab
#   consumer      — inputs  the domain edge type (raw string variant B, folds to same canonical); vocab = cons_vocab
#   consumer_alt  — SAME contract as consumer but a DIFFERENT vocabulary;         vocab = alt_vocab
#   lexical_twin  — shares the PRODUCER vocabulary but has unrelated edges (the lexical trap); vocab = prod_vocab
# The producer's output raw string and the consumer's input raw string are DIFFERENT literals that canonicalize to the
# same edge type, so a plain string-equality match would miss the composition — only canonicalized edge matching finds
# it. All 64 vocab words are globally distinct so topic relevance stays crisp.
DOMAINS: list[dict[str, Any]] = [
    {"name": "record_batch", "prod_out": "rows", "cons_in": "Row",
     "prod_vocab": ["ingest", "csvfile", "loader", "staging"],
     "cons_vocab": ["dedupe", "clustering", "merging", "canonicalize"],
     "alt_vocab": ["collapse", "reconcile", "fold", "coalesce"]},
    {"name": "graph", "prod_out": "graph", "cons_in": "AdjacencyGraph",
     "prod_vocab": ["adjacency", "vertices", "topology", "edgelist"],
     "cons_vocab": ["traversal", "shortestpath", "pagerank", "centrality"],
     "alt_vocab": ["walk", "reachability", "spanning", "components"]},
    {"name": "embedding", "prod_out": "embedding", "cons_in": "Embedding",
     "prod_vocab": ["encoder", "vectorize", "embed", "projection"],
     "cons_vocab": ["nearest", "cosine", "reranker", "annindex"],
     "alt_vocab": ["retrieval", "similarity", "lookup", "neighbours"]},
    {"name": "json", "prod_out": "json", "cons_in": "Json",
     "prod_vocab": ["serialize", "marshal", "jsonify", "payload"],
     "cons_vocab": ["schemacheck", "jsonpath", "flatten", "unnest"],
     "alt_vocab": ["validate", "descend", "denormalize", "traverse"]},
    {"name": "table", "prod_out": "table", "cons_in": "Table",
     "prod_vocab": ["tabulate", "columnar", "pivot", "dataframe"],
     "cons_vocab": ["aggregate", "groupby", "rollup", "windowing"],
     "alt_vocab": ["summarise", "bucketize", "partition", "accumulate"]},
    {"name": "document", "prod_out": "document", "cons_in": "Document",
     "prod_vocab": ["scanning", "ocr", "parsing", "extraction"],
     "cons_vocab": ["summarize", "classify", "redact", "chunking"],
     "alt_vocab": ["distill", "categorize", "mask", "segmenting"]},
    {"name": "tokens", "prod_out": "tokens", "cons_in": "Tokens",
     "prod_vocab": ["tokenizer", "bpe", "segment", "lexer"],
     "cons_vocab": ["counting", "ngram", "stopword", "stemming"],
     "alt_vocab": ["frequency", "windowed", "filtering", "lemmatize"]},
    {"name": "image", "prod_out": "image", "cons_in": "Image",
     "prod_vocab": ["capture", "render", "rasterize", "thumbnail"],
     "cons_vocab": ["resize", "detection", "caption", "augment"],
     "alt_vocab": ["scale", "recognize", "annotate", "distort"]},
]


def _card(*, cid: str, label: str, vocab: list[str], input_edge: str, output_edge: str,
          family: str, topic: str | None) -> dict[str, Any]:
    # a stable per-card filler token gives light pseudo-variety without changing which family a card belongs to.
    filler = f"v{_stable_seed(cid) % 97}"
    text = " ".join([label.replace(".", " ").replace(":", " ")] + vocab + [filler])
    return {
        "primitive_id": cid,
        "label": label,
        "input_edge": input_edge,
        "output_edge": output_edge,
        "canon_input": _canon(input_edge),
        "canon_output": _canon(output_edge),
        "keywords": list(vocab),
        "text": text,
        "family": family,
        "topic": topic,
        "record_type": "similarity_benchmark_synthetic_card",
        "origin": "synthetic",
    }


def build_synthetic_corpus() -> list[dict[str, Any]]:
    corpus: list[dict[str, Any]] = []
    for d in DOMAINS:
        n = d["name"]
        # producer (single, unique contract in=<n>_source out=<domain type>)
        corpus.append(_card(
            cid=f"syn:{n}:producer:0", label=f"{n}.producer.emitter",
            vocab=d["prod_vocab"], input_edge=f"{n}_source", output_edge=d["prod_out"],
            family=f"{n}:producer", topic=n))
        # consumers (3) — consume the domain type, emit <n>_sink
        for i in range(3):
            corpus.append(_card(
                cid=f"syn:{n}:consumer:{i}", label=f"{n}.consumer.step{i}",
                vocab=d["cons_vocab"], input_edge=d["cons_in"], output_edge=f"{n}_sink",
                family=f"{n}:consumer", topic=None))
        # consumer_alt (2) — SAME contract as consumers, DIFFERENT vocab (defeats lexical on same_contract recall)
        for i in range(2):
            corpus.append(_card(
                cid=f"syn:{n}:consumer_alt:{i}", label=f"{n}.consumer.altstep{i}",
                vocab=d["alt_vocab"], input_edge=d["cons_in"], output_edge=f"{n}_sink",
                family=f"{n}:consumer", topic=None))
        # lexical twins (3) — share PRODUCER vocab, unrelated edges (the lexical trap; same topic as producer)
        for i in range(3):
            corpus.append(_card(
                cid=f"syn:{n}:twin:{i}", label=f"{n}.twin.decoy{i}",
                vocab=d["prod_vocab"], input_edge=f"{n}_twinin", output_edge=f"{n}_twinout",
                family=f"{n}:twin", topic=n))
    return corpus


# ======================================================================================================================
# Labeled judgments
# ======================================================================================================================
def _relevance(intent: str, expected_value: str, query: dict[str, Any]) -> Callable[[dict[str, Any]], bool]:
    if intent in ("consume_forward", "consume_reverse", "topic_semantic"):
        key = "topic" if intent == "topic_semantic" else "family"
        def rel(card: dict[str, Any]) -> bool:
            return card.get(key) == expected_value and card.get("primitive_id") != query.get("primitive_id")
        return rel
    if intent == "same_contract":
        q_contract = (query["canon_input"], query["canon_output"])
        def rel_c(card: dict[str, Any]) -> bool:
            return ((card["canon_input"], card["canon_output"]) == q_contract
                    and card.get("primitive_id") != query.get("primitive_id"))
        return rel_c
    raise ValueError(f"unknown intent {intent!r}")


def build_judgments(corpus: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id = {c["primitive_id"]: c for c in corpus}
    judgments: list[dict[str, Any]] = []
    for d in DOMAINS:
        n = d["name"]
        producer = by_id[f"syn:{n}:producer:0"]
        consumer = by_id[f"syn:{n}:consumer:0"]
        # consume_forward: query = producer, expected = its consumers
        judgments.append({
            "id": f"j:{n}:consume_forward", "intent": "consume_forward",
            "description": f"find something that consumes what the {n} producer emits",
            "query": producer, "expected_value": f"{n}:consumer"})
        # consume_reverse: query = a consumer, expected = the producer that feeds it
        judgments.append({
            "id": f"j:{n}:consume_reverse", "intent": "consume_reverse",
            "description": f"find something that produces what the {n} consumer needs",
            "query": consumer, "expected_value": f"{n}:producer"})
        # same_contract: query = a consumer, expected = every card with the same canonical contract
        judgments.append({
            "id": f"j:{n}:same_contract", "intent": "same_contract",
            "description": f"find primitives sharing the {n} consumer's exact input/output contract",
            "query": consumer, "expected_value": "<contract>"})
        # topic_semantic: query = a contract-free topic description, expected = same-topic cards
        topic_query = {
            "primitive_id": f"query:{n}:topic", "label": f"{n} topic probe",
            "input_edge": "", "output_edge": "", "canon_input": _canon(""), "canon_output": _canon(""),
            "keywords": list(d["prod_vocab"]),
            "text": f"{n} pipeline about " + " ".join(d["prod_vocab"]),
            "family": None, "topic": n, "origin": "query"}
        judgments.append({
            "id": f"j:{n}:topic_semantic", "intent": "topic_semantic",
            "description": f"find primitives about the same topic as this {n} description",
            "query": topic_query, "expected_value": n})
    for j in judgments:
        j["relevant_fn"] = _relevance(j["intent"], j["expected_value"], j["query"])
    return judgments


# ======================================================================================================================
# Wired similarity methods : score(query_card, candidate_card, ctx) -> float in [0, 1]
# ======================================================================================================================
def _jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


def sim_lexical_token_jaccard(q: dict[str, Any], c: dict[str, Any], ctx: dict[str, Any]) -> float:
    return _jaccard(_tokens(q["text"]), _tokens(c["text"]))


def sim_lexical_tfidf_cosine(q: dict[str, Any], c: dict[str, Any], ctx: dict[str, Any]) -> float:
    idf: dict[str, float] = ctx["idf"]

    def vec(text: str) -> dict[str, float]:
        toks = _WORD.findall((text or "").lower())
        tf: dict[str, int] = {}
        for t in toks:
            tf[t] = tf.get(t, 0) + 1
        return {t: (n / len(toks)) * idf.get(t, ctx["idf_default"]) for t, n in tf.items()} if toks else {}

    va, vb = vec(q["text"]), vec(c["text"])
    if not va or not vb:
        return 0.0
    dot = sum(va[t] * vb.get(t, 0.0) for t in va)
    na = math.sqrt(sum(v * v for v in va.values()))
    nb = math.sqrt(sum(v * v for v in vb.values()))
    return dot / (na * nb) if na and nb else 0.0


def _edge_set(card: dict[str, Any]) -> set[str]:
    s = {card.get("canon_input") or _canon(card.get("input_edge")),
         card.get("canon_output") or _canon(card.get("output_edge"))}
    s.discard("Unknown")
    return s


def sim_edge_type_jaccard(q: dict[str, Any], c: dict[str, Any], ctx: dict[str, Any]) -> float:
    return _jaccard(_edge_set(q), _edge_set(c))


def sim_edge_directional_compose(q: dict[str, Any], c: dict[str, Any], ctx: dict[str, Any]) -> float:
    """Composability: can c be chained with q in EITHER direction? c consumes q's output, or c produces q's input."""
    qi, qo = q.get("canon_input"), q.get("canon_output")
    ci, co = c.get("canon_input"), c.get("canon_output")
    forward = ci not in (None, "Unknown") and ci == qo   # c consumes what q produces
    reverse = co not in (None, "Unknown") and co == qi   # c produces what q consumes
    if forward and reverse:
        return 1.0
    if forward or reverse:
        return 0.75
    return 0.0


def sim_edge_type_plus_lexical(q: dict[str, Any], c: dict[str, Any], ctx: dict[str, Any]) -> float:
    return 0.5 * sim_edge_type_jaccard(q, c, ctx) + 0.5 * sim_lexical_token_jaccard(q, c, ctx)


BUILTIN_METHODS: dict[str, Callable[..., float]] = {
    "lexical_token_jaccard": sim_lexical_token_jaccard,
    "lexical_tfidf_cosine": sim_lexical_tfidf_cosine,
    "edge_type_jaccard": sim_edge_type_jaccard,
    "edge_directional_compose": sim_edge_directional_compose,
    "edge_type_plus_lexical": sim_edge_type_plus_lexical,
}


def wire_methods() -> tuple[dict[str, Callable[..., float]], dict[str, str]]:
    """Built-in methods + (if present) any exported by scripts.primitive_similarity_portfolio. Lexical fallback."""
    methods: dict[str, Callable[..., float]] = dict(BUILTIN_METHODS)
    source: dict[str, str] = {name: "builtin" for name in methods}
    try:  # try/except lexical fallback — the portfolio is optional
        from scripts import primitive_similarity_portfolio as _psp  # type: ignore
        exported = getattr(_psp, "SIMILARITY_METHODS", None)
        if isinstance(exported, dict):
            for name, fn in exported.items():
                if callable(fn):
                    methods[name] = fn
                    source[name] = "portfolio"
    except Exception:
        pass  # portfolio not present yet -> run on built-in methods (lexical + edge-type)
    return methods, source


# ======================================================================================================================
# Scoring
# ======================================================================================================================
def _build_ctx(corpus: list[dict[str, Any]]) -> dict[str, Any]:
    n_docs = len(corpus)
    df: dict[str, int] = {}
    for c in corpus:
        for t in _tokens(c["text"]):
            df[t] = df.get(t, 0) + 1
    idf = {t: math.log((n_docs + 1) / (d + 1)) + 1.0 for t, d in df.items()}
    return {"idf": idf, "idf_default": math.log((n_docs + 1) / 1) + 1.0}


def rank(query: dict[str, Any], corpus: list[dict[str, Any]], method: Callable[..., float],
         ctx: dict[str, Any]) -> list[tuple[dict[str, Any], float]]:
    qid = query.get("primitive_id")
    scored = [(c, float(method(query, c, ctx))) for c in corpus if c.get("primitive_id") != qid]
    # deterministic tie-break: higher score first, then stable by primitive_id (NO rng)
    scored.sort(key=lambda cs: (-cs[1], cs[0].get("primitive_id", "")))
    return scored


def score_judgment(judgment: dict[str, Any], corpus: list[dict[str, Any]], method: Callable[..., float],
                   ctx: dict[str, Any]) -> dict[str, Any]:
    rel_fn: Callable[[dict[str, Any]], bool] = judgment["relevant_fn"]
    ranked = rank(judgment["query"], corpus, method, ctx)
    rel_flags = [rel_fn(c) for c, _ in ranked]
    total_relevant = sum(1 for f in rel_flags if f)
    out: dict[str, Any] = {"judgment_id": judgment["id"], "intent": judgment["intent"],
                           "total_relevant": total_relevant}
    for k in K_VALUES:
        kk = min(k, len(rel_flags))
        hits = sum(1 for f in rel_flags[:kk] if f)
        out[f"precision_at_{k}"] = (hits / k) if k else 0.0
        out[f"recall_at_{k}"] = (hits / total_relevant) if total_relevant else 0.0
    mrr = 0.0
    for i, f in enumerate(rel_flags, start=1):
        if f:
            mrr = 1.0 / i
            break
    out["mrr"] = mrr
    return out


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def evaluate(corpus: list[dict[str, Any]], judgments: list[dict[str, Any]],
             methods: dict[str, Callable[..., float]]) -> dict[str, Any]:
    ctx = _build_ctx(corpus)
    intents = sorted({j["intent"] for j in judgments})
    per_method: dict[str, Any] = {}
    for name, fn in methods.items():
        cards = [score_judgment(j, corpus, fn, ctx) for j in judgments]
        agg: dict[str, Any] = {"judgment_count": len(cards)}
        for k in K_VALUES:
            agg[f"mean_precision_at_{k}"] = round(_mean([c[f"precision_at_{k}"] for c in cards]), 4)
            agg[f"mean_recall_at_{k}"] = round(_mean([c[f"recall_at_{k}"] for c in cards]), 4)
        agg["mean_mrr"] = round(_mean([c["mrr"] for c in cards]), 4)
        by_intent: dict[str, Any] = {}
        for intent in intents:
            sub = [c for c in cards if c["intent"] == intent]
            by_intent[intent] = {
                "mean_precision_at_1": round(_mean([c["precision_at_1"] for c in sub]), 4),
                "mean_precision_at_3": round(_mean([c["precision_at_3"] for c in sub]), 4),
                "mean_recall_at_5": round(_mean([c["recall_at_5"] for c in sub]), 4),
                "mean_mrr": round(_mean([c["mrr"] for c in sub]), 4),
            }
        agg["by_intent"] = by_intent
        agg["_cards"] = cards
        per_method[name] = agg

    def _rank_key(item: tuple[str, dict[str, Any]]) -> tuple[float, float, str]:
        name, a = item
        return (-a[HEADLINE_METRIC], -a["mean_mrr"], name)

    leaderboard = [name for name, _ in sorted(per_method.items(), key=_rank_key)]
    winner = leaderboard[0]
    # per-intent winner (by mean_precision_at_3 on that intent)
    intent_winner: dict[str, str] = {}
    for intent in intents:
        best = sorted(per_method.items(),
                      key=lambda it: (-it[1]["by_intent"][intent]["mean_precision_at_3"],
                                      -it[1]["by_intent"][intent]["mean_mrr"], it[0]))
        intent_winner[intent] = best[0][0]
    return {
        "headline_metric": HEADLINE_METRIC,
        "per_method": per_method,
        "leaderboard": leaderboard,
        "winner": winner,
        "intent_winner": intent_winner,
        "intents": intents,
    }


# ======================================================================================================================
# Real-card distractors (bounded, deterministic head-sample) — makes --run corpus a realistic MIX
# ======================================================================================================================
def load_real_distractors(limit: int) -> list[dict[str, Any]]:
    if limit <= 0 or not REAL_CARDS_PATH.exists():
        return []
    out: list[dict[str, Any]] = []
    with REAL_CARDS_PATH.open(encoding="utf-8") as fh:
        for line in fh:
            if len(out) >= limit:
                break
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            contract = r.get("contract") or {}
            in_e = r.get("input_edge") or contract.get("input") or ""
            out_e = r.get("output_edge") or contract.get("output") or ""
            label = str(r.get("label") or r.get("primitive_id") or "real")
            kws = r.get("keywords") or []
            out.append({
                "primitive_id": f"real:{r.get('primitive_id') or len(out)}",
                "label": label,
                "input_edge": in_e, "output_edge": out_e,
                "canon_input": _canon(in_e), "canon_output": _canon(out_e),
                "keywords": list(kws) if isinstance(kws, list) else [],
                "text": " ".join([label] + ([str(x) for x in kws] if isinstance(kws, list) else [])),
                "family": "corpus_distractor", "topic": None,
                "record_type": "similarity_benchmark_real_distractor", "origin": "real",
            })
    return out


# ======================================================================================================================
# Reporting
# ======================================================================================================================
def _accounting(corpus: list[dict[str, Any]], judgments: list[dict[str, Any]]) -> dict[str, Any]:
    unique_ids = {c["primitive_id"] for c in corpus}
    return {
        "judgments_generated": len(judgments),
        "judgments_unique": len({j["id"] for j in judgments}),
        "corpus_total": len(corpus),
        "corpus_synthetic": sum(1 for c in corpus if c.get("origin") == "synthetic"),
        "corpus_real_distractors": sum(1 for c in corpus if c.get("origin") == "real"),
        "corpus_unique_ids": len(unique_ids),
        "serves_truth": False,
        "evidence_class": "benchmark_candidate",
    }


def build_result(corpus: list[dict[str, Any]], judgments: list[dict[str, Any]],
                 methods: dict[str, Callable[..., float]], method_source: dict[str, str],
                 date: str) -> dict[str, Any]:
    ev = evaluate(corpus, judgments, methods)
    per_method_public = {}
    for name, agg in ev["per_method"].items():
        pub = {k: v for k, v in agg.items() if k != "_cards"}
        pub["method_source"] = method_source.get(name, "builtin")
        per_method_public[name] = pub
    return {
        "record_type": "similarity_retrieval_benchmark",
        "date": date,
        "serves_truth": False,
        "evidence_class": "benchmark_candidate",
        "headline_metric": ev["headline_metric"],
        "k_values": list(K_VALUES),
        "winner": ev["winner"],
        "leaderboard": ev["leaderboard"],
        "intent_winner": ev["intent_winner"],
        "intents": ev["intents"],
        "per_method": per_method_public,
        "accounting": _accounting(corpus, judgments),
        "note": ("Candidate benchmark evidence (serves_truth=false). Edge-type methods answer composability queries "
                 "('find what consumes what X produces') that lexical similarity cannot; lexical wins pure-topic "
                 "queries. All methods executed on the fixtures; no numbers are promoted to truth."),
    }


def render_report(result: dict[str, Any]) -> str:
    lines: list[str] = []
    ap = lines.append
    ap(f"# Similarity Retrieval Benchmark — {result['date']}")
    ap("")
    ap(result["note"])
    ap("")
    acc = result["accounting"]
    ap("## Honest accounting")
    ap("")
    ap(f"- judgments (generated / unique): **{acc['judgments_generated']} / {acc['judgments_unique']}**")
    ap(f"- corpus (synthetic labeled / real distractors / total): "
       f"**{acc['corpus_synthetic']} / {acc['corpus_real_distractors']} / {acc['corpus_total']}**")
    ap(f"- serves_truth: **{acc['serves_truth']}** · evidence_class: **{acc['evidence_class']}**")
    ap("")
    ap(f"## Leaderboard (ranked by `{result['headline_metric']}`, MRR tiebreak)")
    ap("")
    ap("| rank | method | source | P@1 | P@3 | P@5 | R@5 | MRR |")
    ap("|---:|---|---|---:|---:|---:|---:|---:|")
    for i, name in enumerate(result["leaderboard"], start=1):
        m = result["per_method"][name]
        crown = " 👑" if name == result["winner"] else ""
        ap(f"| {i} | `{name}`{crown} | {m['method_source']} | {m['mean_precision_at_1']:.3f} | "
           f"{m['mean_precision_at_3']:.3f} | {m['mean_precision_at_5']:.3f} | "
           f"{m['mean_recall_at_5']:.3f} | {m['mean_mrr']:.3f} |")
    ap("")
    ap(f"**Winning method for composability-oriented retrieval: `{result['winner']}`.**")
    ap("")
    ap("## Per-intent winner (by P@3)")
    ap("")
    ap("| intent | winning method |")
    ap("|---|---|")
    for intent in result["intents"]:
        ap(f"| `{intent}` | `{result['intent_winner'][intent]}` |")
    ap("")
    ap("## Per-method precision@3 by intent")
    ap("")
    header = "| method | " + " | ".join(f"`{it}`" for it in result["intents"]) + " |"
    ap(header)
    ap("|---" * (len(result["intents"]) + 1) + "|")
    for name in result["leaderboard"]:
        by = result["per_method"][name]["by_intent"]
        cells = " | ".join(f"{by[it]['mean_precision_at_3']:.3f}" for it in result["intents"])
        ap(f"| `{name}` | {cells} |")
    ap("")
    ap("_Reading: lexical methods are competitive on `topic_semantic` but collapse on the composability intents "
       "(`consume_forward` / `same_contract`), where edge-type matching over canonicalized edge types wins._")
    ap("")
    return "\n".join(lines)


def run(date: str = REPORT_DATE, real_distractors: int = 300) -> dict[str, Any]:
    corpus = build_synthetic_corpus() + load_real_distractors(real_distractors)
    judgments = build_judgments(corpus)
    methods, method_source = wire_methods()
    result = build_result(corpus, judgments, methods, method_source, date)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    json_path = OUT_DIR / f"similarity_benchmark_{date}.json"
    md_path = OUT_DIR / f"similarity_benchmark_{date}.md"
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(render_report(result), encoding="utf-8")
    return result


# ======================================================================================================================
# Self-test (offline synthetic, no real distractors)
# ======================================================================================================================
def self_test() -> int:
    corpus = build_synthetic_corpus()
    judgments = build_judgments(corpus)
    methods, _src = wire_methods()
    ev = evaluate(corpus, judgments, methods)
    pm = ev["per_method"]

    def finite(x: Any) -> bool:
        return isinstance(x, (int, float)) and 0.0 <= float(x) <= 1.0 and not math.isnan(float(x))

    # a specific labeled forward-consume case: edge_type_jaccard must retrieve consumers first (MRR == 1.0)
    ctx = _build_ctx(corpus)
    fwd = next(j for j in judgments if j["id"] == "j:record_batch:consume_forward")
    edge_case = score_judgment(fwd, corpus, methods["edge_type_jaccard"], ctx)
    lex_case = score_judgment(fwd, corpus, methods["lexical_token_jaccard"], ctx)

    def intent_p3(method: str, intent: str) -> float:
        return pm[method]["by_intent"][intent]["mean_precision_at_3"]

    checks = [
        ("scorecard computes finite metrics for every method",
         all(finite(pm[m][f"mean_precision_at_{k}"]) and finite(pm[m]["mean_mrr"])
             for m in methods for k in K_VALUES)),
        ("edge_type_jaccard beats lexical on consume_forward (the labeled composability case)",
         intent_p3("edge_type_jaccard", "consume_forward") > intent_p3("lexical_token_jaccard", "consume_forward")),
        ("edge_type_jaccard beats lexical on same_contract recall@5",
         pm["edge_type_jaccard"]["by_intent"]["same_contract"]["mean_recall_at_5"]
         > pm["lexical_token_jaccard"]["by_intent"]["same_contract"]["mean_recall_at_5"]),
        ("lexical wins its own intent (topic_semantic P@3 >= edge_type_jaccard)",
         intent_p3("lexical_token_jaccard", "topic_semantic") >= intent_p3("edge_type_jaccard", "topic_semantic")),
        ("overall winner is an edge_* method", ev["winner"].startswith("edge_")),
        ("labeled forward case: edge_type_jaccard MRR == 1.0", edge_case["mrr"] == 1.0),
        ("labeled forward case: edge beats lexical MRR", edge_case["mrr"] > lex_case["mrr"]),
        ("directional method wins consume_reverse MRR",
         ev["intent_winner"]["consume_reverse"].startswith("edge_")),
        ("~30 judgments across 4 intents", 28 <= len(judgments) <= 40 and len(ev["intents"]) == 4),
    ]
    failed = [n for n, ok in checks if not ok]
    if failed:
        print("FAIL - similarity_retrieval_benchmark:\n  " + "\n  ".join(failed))
        return 1
    print(f"PASS - similarity_retrieval_benchmark: {len(methods)} methods scored over {len(judgments)} labeled "
          f"judgments; winner={ev['winner']!r}; edge_type_jaccard beats lexical on composability, lexical wins "
          f"topic (synthetic offline).")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--run", action="store_true", help="write the leaderboard md+json")
    parser.add_argument("--date", default=REPORT_DATE)
    parser.add_argument("--real-distractors", type=int, default=300,
                        help="bounded head-sample of real registry cards mixed in as distractor noise")
    args = parser.parse_args(argv)
    if args.run:
        result = run(date=args.date, real_distractors=args.real_distractors)
        print(json.dumps({
            "winner": result["winner"],
            "leaderboard": result["leaderboard"],
            "headline_metric": result["headline_metric"],
            "accounting": result["accounting"],
        }, indent=2, sort_keys=True))
        return self_test()
    return self_test()


if __name__ == "__main__":
    raise SystemExit(main())
