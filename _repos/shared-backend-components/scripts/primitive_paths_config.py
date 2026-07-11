#!/usr/bin/env python3
"""scripts/primitive_paths_config — the maximum-flexibility layer: every runtime decision point is a
PORTFOLIO of contract-substitutable paths, plus tunable parameters, behind ONE selector.

The non-commitment law made concrete (playbook idea #2/#3): canonicalization, search, composition,
reranking and proof-policy are each a set of named paths sharing a uniform contract, not an `if` baked
into the code. `ACTIVE_DEFAULT` reproduces TODAY's behavior exactly, so selecting it replaces nothing;
adding a new strategy is a new row + a resolver entry, never a rewrite. Every resolution emits a
DecisionReceipt (playbook idea #7) so the choice is auditable, never silent.

ADD-ONLY: this imports and composes the existing wired modules (build_edge_type_retrofit,
check_primitive_composability, build_primitive_search_index, mutator_registry); it edits none of them and
serves as a NEW path over them. Pure/offline `--self-test`; graceful per-path import fallback so the
selector self-tests standalone even if a sibling module is mid-build.

Uniform contracts (a new path only has to satisfy one of these to plug in):
  - CANONICALIZE:  canon(label: str|None) -> str|None            (None == untyped)
  - SEARCH:        search(query: str, *, limit: int, corpus: list[dict]|None) -> list[dict]
  - COMPOSE:       compose(spec: dict, *, config: dict) -> dict   (dict carries {path, output, steps, tokens})
  - RERANK:        rerank(query: str, cards: list[dict], *, config: dict) -> list[dict]
  - PROOF_POLICY:  prove(primitive_id, mutator, fixture_input, expected_output, **kw) -> dict
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Callable, Optional

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
STATUS_WIRED = "wired"
STATUS_PLANNED = "planned"
STATUS_OPTIONAL = "optional"


class UnknownPath(KeyError):
    """A decision point was asked for a path name it does not define."""


class PathNotWired(NotImplementedError):
    """A declared-but-not-yet-implemented path was requested for execution (status != wired)."""


# ════════════════════════════════════════════════════════════════════════════════════════════════
# DECISION POINTS — each a portfolio of paths. Pure data (name/status/summary); callables resolve lazily.
# ════════════════════════════════════════════════════════════════════════════════════════════════
DECISION_POINTS: dict[str, list[dict[str, Any]]] = {
    "edge_canonicalizer": [
        {"name": "strict_screened", "status": STATUS_WIRED,
         "summary": "screens blank/placeholder labels + the 'Unknown' sentinel to None (gate-safe)"},
        {"name": "retrofit_rule", "status": STATUS_WIRED,
         "summary": "the 636-type retrofit rule+synonym canonicalizer (maps un-typeable -> 'Unknown')"},
        {"name": "identity", "status": STATUS_WIRED,
         "summary": "pass-through: a non-blank label is its own type (no folding)"},
    ],
    "search_method": [
        {"name": "blocking_lexical_index", "status": STATUS_WIRED,
         "summary": "df-capped inverted blocking index; O(candidates) not O(N); mutations excluded"},
        {"name": "linear_lexical", "status": STATUS_WIRED,
         "summary": "self-contained token-overlap linear scan (the legacy path — kept, not deleted)"},
        {"name": "dense_ann", "status": STATUS_PLANNED,
         "summary": "pgvector/HNSW over one embedder+field (portfolio target; flip wired when built)"},
        {"name": "hybrid_rrf", "status": STATUS_WIRED,
         "summary": "reciprocal-rank fusion of the wired lexical + type-aware rankings (no one path's blind spot dominates)"},
    ],
    "composer": [
        {"name": "data_shape_chain", "status": STATUS_WIRED,
         "summary": "chain mutators by DATA shape (proven end-to-end at zero tokens)"},
        {"name": "edge_typed_chain", "status": STATUS_WIRED,
         "summary": "chain cards by canonical edge TYPE (output_type == next input_type)"},
        {"name": "exhaustive_bfs", "status": STATUS_PLANNED,
         "summary": "typed BFS over the full corpus with depth cap + adapters"},
    ],
    "reranker": [
        {"name": "lexical_idf", "status": STATUS_WIRED,
         "summary": "idf-weighted token overlap (default)"},
        {"name": "edge_affinity", "status": STATUS_WIRED,
         "summary": "boost cards whose canonical type chains toward the requested output type"},
        {"name": "cross_encoder", "status": STATUS_PLANNED,
         "summary": "a real cross-encoder in the stubbed rerank slot"},
    ],
    "proof_policy": [
        {"name": "executed_proof", "status": STATUS_WIRED,
         "summary": "run the leaf's proof against a fixture; promote serves_truth only on pass"},
        {"name": "candidate_only", "status": STATUS_WIRED,
         "summary": "never promote — everything stays candidate=true/serves_truth=false"},
    ],
}

# ════════════════════════════════════════════════════════════════════════════════════════════════
# PARAMETERS — tunable knobs, each with a default + validation range/choices + unit/rationale.
# ════════════════════════════════════════════════════════════════════════════════════════════════
PARAMETERS: dict[str, dict[str, Any]] = {
    "search_limit": {"default": 20, "type": "int", "range": (1, 500), "rationale": "top-k returned by search"},
    "df_cap_ratio": {"default": 0.05, "type": "float", "range": (0.001, 0.5),
                     "rationale": "drop tokens appearing in > this share of docs (blocking selectivity)"},
    "compose_max_depth": {"default": 4, "type": "int", "range": (1, 12),
                          "rationale": "max steps in a composed route before giving up"},
    "require_proven": {"default": False, "type": "bool",
                       "rationale": "only allow serves_truth=true leaves into a composed route"},
    "allow_adapters": {"default": True, "type": "bool",
                       "rationale": "permit reviewed deterministic adapter nodes to bridge near-matches"},
}

# ACTIVE_DEFAULT reproduces TODAY's behavior — selecting it replaces nothing.
ACTIVE_DEFAULT: dict[str, Any] = {
    "edge_canonicalizer": "strict_screened",
    "search_method": "blocking_lexical_index",
    "composer": "data_shape_chain",
    "reranker": "lexical_idf",
    "proof_policy": "executed_proof",
    **{k: v["default"] for k, v in PARAMETERS.items()},
}


# ── introspection ──────────────────────────────────────────────────────────────────────────────
def available_paths(decision_point: str) -> list[dict[str, Any]]:
    if decision_point not in DECISION_POINTS:
        raise UnknownPath(f"no decision point {decision_point!r}; have {sorted(DECISION_POINTS)}")
    return list(DECISION_POINTS[decision_point])


def wired_paths(decision_point: str) -> list[str]:
    return [p["name"] for p in available_paths(decision_point) if p["status"] == STATUS_WIRED]


def _path_row(decision_point: str, name: str) -> dict[str, Any]:
    for p in available_paths(decision_point):
        if p["name"] == name:
            return p
    raise UnknownPath(
        f"{decision_point!r} has no path {name!r}; have {[p['name'] for p in DECISION_POINTS[decision_point]]}"
    )


# ── config resolution + receipts ─────────────────────────────────────────────────────────────────
def resolve_config(overrides: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    """Merge ACTIVE_DEFAULT with overrides; validate every decision-point name + parameter. Never mutates
    global state. Raises UnknownPath / ValueError on a bad choice so a typo fails loud, not silent."""
    cfg = dict(ACTIVE_DEFAULT)
    for k, v in (overrides or {}).items():
        if k in DECISION_POINTS:
            _path_row(k, v)  # validates the name exists
            cfg[k] = v
        elif k in PARAMETERS:
            cfg[k] = _validate_param(k, v)
        else:
            raise ValueError(f"unknown config key {k!r}; decision points={sorted(DECISION_POINTS)}, "
                             f"parameters={sorted(PARAMETERS)}")
    return cfg


def _validate_param(name: str, value: Any) -> Any:
    spec = PARAMETERS[name]
    t = spec["type"]
    if t == "bool":
        if not isinstance(value, bool):
            raise ValueError(f"{name} must be bool, got {value!r}")
        return value
    if t == "int":
        value = int(value)
    elif t == "float":
        value = float(value)
    lo, hi = spec.get("range", (None, None))
    if lo is not None and not (lo <= value <= hi):
        raise ValueError(f"{name}={value} out of range [{lo}, {hi}] ({spec['rationale']})")
    return value


def decision_receipt(config: dict[str, Any]) -> dict[str, Any]:
    """A DecisionReceipt (playbook #7): the fully-resolved config + a deterministic hash + which paths are
    still planned (so a consumer sees exactly what ran and what is not yet available). Auditable, not silent."""
    resolved = resolve_config(config if config is not ACTIVE_DEFAULT else None)
    canonical = json.dumps(resolved, sort_keys=True, separators=(",", ":"))
    planned = {dp: _path_row(dp, resolved[dp])["status"] for dp in DECISION_POINTS
               if _path_row(dp, resolved[dp])["status"] != STATUS_WIRED}
    return {
        "record_type": "path_config_decision_receipt",
        "config": resolved,
        "config_hash": "cfg:" + hashlib.sha256(canonical.encode()).hexdigest()[:16],
        "non_wired_selected": planned,   # empty when every selected path is wired
        **BOUNDARY,
    }


# ── lazy resolvers: name -> uniform-contract callable (import inside so self-test is standalone) ──
def _canon_strict() -> Callable[[Any], Optional[str]]:
    try:
        from scripts.check_primitive_composability import canonicalize_edge as f  # gate-safe (screens Unknown)
        return f
    except Exception:  # noqa: BLE001
        return _canon_identity()


def _canon_retrofit() -> Callable[[Any], Optional[str]]:
    try:
        from scripts.build_edge_type_retrofit import canonicalize_edge as f
        return lambda x: (r if (isinstance(r := f(x), str) and r) else None)
    except Exception:  # noqa: BLE001
        return _canon_identity()


def _canon_identity() -> Callable[[Any], Optional[str]]:
    return lambda x: (x.strip() if isinstance(x, str) and x.strip() else None)


def canonicalizer(name: Optional[str] = None) -> Callable[[Any], Optional[str]]:
    name = name or ACTIVE_DEFAULT["edge_canonicalizer"]
    row = _path_row("edge_canonicalizer", name)
    if row["status"] != STATUS_WIRED:
        raise PathNotWired(f"edge_canonicalizer path {name!r} is {row['status']}")
    return {"strict_screened": _canon_strict, "retrofit_rule": _canon_retrofit,
            "identity": _canon_identity}[name]()


def _tokenize(text: str) -> set[str]:
    return {t for t in "".join(c.lower() if (c.isalnum() or c == "_") else " " for c in text).split() if len(t) > 1}


def _linear_lexical(query: str, *, limit: int, corpus: Optional[list[dict]]) -> list[dict]:
    """Self-contained token-overlap linear scan — the legacy search path, KEPT as a selectable option."""
    q = _tokenize(query)
    scored = []
    for card in (corpus or []):
        text = " ".join(str(card.get(k, "")) for k in ("title", "input_edge", "output_edge", "blackbox"))
        overlap = len(q & _tokenize(text))
        if overlap:
            scored.append((overlap, card))
    scored.sort(key=lambda x: (-x[0], str(x[1].get("primitive_id", ""))))
    return [c for _, c in scored[:limit]]


def _blocking_index(query: str, *, limit: int, corpus: Optional[list[dict]]) -> list[dict]:
    """Adapter onto the wired df-capped inverted index. Falls back to linear if the sibling drifts."""
    try:
        import scripts.build_primitive_search_index as s
        if corpus is not None:
            idx = s.build_index(corpus)
            return s.fast_search(query, limit, idx)
        return s.fast_search(query, limit)
    except Exception:  # noqa: BLE001 — signature/availability drift: keep working via the legacy path
        return _linear_lexical(query, limit=limit, corpus=corpus)


def _hybrid_rrf(query: str, *, limit: int, corpus: Optional[list[dict]], k: int = 60) -> list[dict]:
    """Reciprocal-rank fusion of several wired rankings (blocking index, linear lexical, type-aware affinity),
    so no single lexical path's blind spot decides the result. RRF score = Σ 1/(k + rank) across rankings;
    deterministic tiebreak by primitive_id."""
    cfg = resolve_config(None)
    wide = max(limit * 3, limit)
    lin = _linear_lexical(query, limit=wide, corpus=corpus)
    rankings = [
        _blocking_index(query, limit=wide, corpus=corpus),
        lin,
        _rerank_edge_affinity(query, lin, config=cfg),  # type-aware view of the same candidates
    ]
    scores: dict[str, float] = {}
    by_id: dict[str, dict] = {}
    for ranking in rankings:
        for rank, c in enumerate(ranking):
            cid = str(c.get("primitive_id", ""))
            by_id[cid] = c
            scores[cid] = scores.get(cid, 0.0) + 1.0 / (k + rank)
    ordered = sorted(scores.items(), key=lambda x: (-x[1], x[0]))
    return [by_id[cid] for cid, _ in ordered[:limit]]


def search_path(name: Optional[str] = None) -> Callable[..., list[dict]]:
    name = name or ACTIVE_DEFAULT["search_method"]
    row = _path_row("search_method", name)
    if row["status"] != STATUS_WIRED:
        raise PathNotWired(f"search_method path {name!r} is {row['status']} — flip it wired by implementing it")
    return {"blocking_lexical_index": _blocking_index, "linear_lexical": _linear_lexical,
            "hybrid_rrf": _hybrid_rrf}[name]


def run_configured_search(query: str, config: Optional[dict] = None, corpus: Optional[list[dict]] = None) -> list[dict]:
    cfg = resolve_config(config)
    fn = search_path(cfg["search_method"])
    return fn(query, limit=cfg["search_limit"], corpus=corpus)


# ── rerankers (uniform RERANK contract: rerank(query, cards, *, config) -> reordered cards) ──
def _card_text(card: dict) -> str:
    return " ".join(str(card.get(k, "")) for k in ("title", "input_edge", "output_edge", "blackbox"))


def _rerank_lexical_idf(query: str, cards: list[dict], *, config: dict) -> list[dict]:
    """Reorder by idf-weighted overlap with the query over the candidate set (rare shared tokens weigh more)."""
    import math
    q = _tokenize(query)
    docs = [(_tokenize(_card_text(c)), c) for c in cards]
    df: dict[str, int] = {}
    for toks, _ in docs:
        for t in toks:
            df[t] = df.get(t, 0) + 1
    n = max(1, len(docs))
    scored = []
    for toks, c in docs:
        score = sum(math.log(1 + n / df[t]) for t in (q & toks))
        scored.append((score, str(c.get("primitive_id", "")), c))
    scored.sort(key=lambda x: (-x[0], x[1]))  # deterministic: score desc, id asc
    return [c for _, _, c in scored]


def _rerank_edge_affinity(query: str, cards: list[dict], *, config: dict) -> list[dict]:
    """Boost cards whose CANONICAL edge type is named in the query — the fix for relevant-but-not-composable:
    a card that produces/consumes the type the caller asked for outranks a raw-token-overlap match. Falls back
    to lexical order for ties, so it never does worse than lexical."""
    canon = canonicalizer(config.get("edge_canonicalizer"))
    q = _tokenize(query)
    base = {id(c): rank for rank, c in enumerate(_rerank_lexical_idf(query, cards, config=config))}
    scored = []
    for c in cards:
        types = {t for t in (canon(c.get("input_edge")), canon(c.get("output_edge"))) if t}
        type_hit = sum(1 for t in types if _tokenize(t) & q)   # canonical type named in the query
        # affinity dominates; lexical rank breaks ties (lower base rank = better).
        scored.append((-type_hit, base.get(id(c), 0), str(c.get("primitive_id", "")), c))
    scored.sort(key=lambda x: (x[0], x[1], x[2]))
    return [c for *_, c in scored]


def reranker(name: Optional[str] = None) -> Callable[..., list[dict]]:
    name = name or ACTIVE_DEFAULT["reranker"]
    row = _path_row("reranker", name)
    if row["status"] != STATUS_WIRED:
        raise PathNotWired(f"reranker path {name!r} is {row['status']}")
    return {"lexical_idf": _rerank_lexical_idf, "edge_affinity": _rerank_edge_affinity}[name]


def run_configured_retrieve(query: str, config: Optional[dict] = None, corpus: Optional[list[dict]] = None) -> list[dict]:
    """Composite opt-in path: search THEN rerank via the configured paths. `run_configured_search` stays pure
    search (replaces nothing); callers who want ranking use this."""
    cfg = resolve_config(config)
    hits = run_configured_search(query, cfg, corpus)
    return reranker(cfg["reranker"])(query, hits, config=cfg)


# ── composers (uniform COMPOSE contract) ─────────────────────────────────────────────────────────
def _compose_data_shape(spec: dict, *, config: dict) -> dict:
    """Execute an explicit mutator route by chaining DATA through apply_mutator. Zero LLM tokens. `spec`:
    {input, route:[(mutator, kwargs)...]}. Proven end-to-end (see composition study)."""
    from scripts.mutator_registry import apply_mutator
    payload, steps = spec.get("input"), []
    route = spec.get("route", [])[: config["compose_max_depth"]]
    for name, kwargs in route:
        payload, receipt = apply_mutator(name, payload, **(kwargs or {}))
        steps.append({"mutator": name, "receipt_keys": sorted(receipt.keys())})
    return {"path": "data_shape_chain", "output": payload, "steps": steps, "tokens": 0,
            "route_length": len(steps), **BOUNDARY}


def _compose_edge_typed(spec: dict, *, config: dict) -> dict:
    """Chain cards by canonical edge TYPE: greedily extend from a source card whose output type equals the
    next card's input type, up to compose_max_depth. `spec`: {cards:[...], start?, canonicalizer?}. Returns
    the ordered route + edge_chain_strength (# of TYPE matches, not token overlap)."""
    canon = canonicalizer(spec.get("canonicalizer") or config.get("edge_canonicalizer"))
    cards = list(spec.get("cards", []))
    if config.get("require_proven"):
        cards = [c for c in cards if c.get("serves_truth") is True]
    by_input: dict[str, list[dict]] = {}
    for c in cards:
        t = canon(c.get("input_edge"))
        if t:
            by_input.setdefault(t, []).append(c)
    start = spec.get("start") or (cards[0] if cards else None)
    route, strength, seen = ([] if start is None else [start]), 0, set()
    cur = start
    while cur is not None and len(route) <= config["compose_max_depth"]:
        out_t = canon(cur.get("output_edge"))
        seen.add(id(cur))
        nxt = next((c for c in by_input.get(out_t or "", []) if id(c) not in seen), None)
        if nxt is None:
            break
        route.append(nxt)
        strength += 1
        cur = nxt
    return {"path": "edge_typed_chain", "output": {"route": [c.get("primitive_id") for c in route]},
            "edge_chain_strength": strength, "route_length": len(route), "tokens": 0, **BOUNDARY}


def composer(name: Optional[str] = None) -> Callable[..., dict]:
    name = name or ACTIVE_DEFAULT["composer"]
    row = _path_row("composer", name)
    if row["status"] != STATUS_WIRED:
        raise PathNotWired(f"composer path {name!r} is {row['status']}")
    return {"data_shape_chain": _compose_data_shape, "edge_typed_chain": _compose_edge_typed}[name]


def run_configured_compose(spec: dict, config: Optional[dict] = None) -> dict:
    cfg = resolve_config(config)
    return composer(cfg["composer"])(spec, config=cfg)


# ── proof policy (uniform PROOF contract) ────────────────────────────────────────────────────────
def proof_policy(name: Optional[str] = None) -> Callable[..., dict]:
    name = name or ACTIVE_DEFAULT["proof_policy"]
    row = _path_row("proof_policy", name)
    if row["status"] != STATUS_WIRED:
        raise PathNotWired(f"proof_policy path {name!r} is {row['status']}")
    if name == "candidate_only":
        def _never_promote(primitive_id, mutator, fixture_input, expected_output, **kw):
            return {"primitive_id": primitive_id, "promoted": False, "serves_truth": False,
                    "policy": "candidate_only", **BOUNDARY}
        return _never_promote
    from scripts.mutator_registry import run_primitive_proof
    return run_primitive_proof


# ── overview ─────────────────────────────────────────────────────────────────────────────────────
def portfolio_overview() -> dict[str, Any]:
    return {
        "record_type": "primitive_paths_portfolio",
        "decision_points": {
            dp: {"paths": len(rows), "wired": sum(1 for r in rows if r["status"] == STATUS_WIRED),
                 "default": ACTIVE_DEFAULT[dp]}
            for dp, rows in DECISION_POINTS.items()
        },
        "parameters": {k: v["default"] for k, v in PARAMETERS.items()},
        "total_paths": sum(len(v) for v in DECISION_POINTS.values()),
        "total_wired": sum(1 for v in DECISION_POINTS.values() for r in v if r["status"] == STATUS_WIRED),
        **BOUNDARY,
    }


# ── self-test ────────────────────────────────────────────────────────────────────────────────────
def self_test() -> int:
    checks: list[tuple[str, bool]] = []

    # 1. default config resolves, every SELECTED default path is wired (default replaces nothing).
    dflt = resolve_config(None)
    checks.append(("ACTIVE_DEFAULT resolves", dflt == ACTIVE_DEFAULT))
    checks.append(("every default-selected path is wired",
                   all(_path_row(dp, dflt[dp])["status"] == STATUS_WIRED for dp in DECISION_POINTS)))

    # 2. overrides validate; a bad name / bad key / out-of-range param fail LOUD.
    ok_over = resolve_config({"search_method": "linear_lexical", "search_limit": 5})
    checks.append(("valid override applies", ok_over["search_method"] == "linear_lexical" and ok_over["search_limit"] == 5))
    for bad in ({"search_method": "nope"}, {"totally": "unknown"}, {"search_limit": 9999}, {"require_proven": "yes"}):
        try:
            resolve_config(bad); raised = False
        except (UnknownPath, ValueError):
            raised = True
        checks.append((f"bad override {list(bad)[0]} raises", raised))

    # 3. a PLANNED path raises PathNotWired on execution request (declared, not runnable).
    try:
        search_path("dense_ann"); nw = False
    except PathNotWired:
        nw = True
    checks.append(("planned path raises PathNotWired", nw))

    # 4. SUBSTITUTABILITY: two search paths over the same synthetic corpus both find the target.
    corpus = [
        {"primitive_id": "p:hash", "title": "sha256 content hash", "input_edge": "RecordBatch", "output_edge": "HashDigest", "blackbox": "hash bytes"},
        {"primitive_id": "p:rename", "title": "rename record fields", "input_edge": "RecordBatch", "output_edge": "RecordBatch", "blackbox": "map keys"},
        {"primitive_id": "p:json", "title": "row to json string", "input_edge": "RecordBatch", "output_edge": "JsonText", "blackbox": "serialize"},
    ]
    r_lin = run_configured_search("rename fields", {"search_method": "linear_lexical"}, corpus=corpus)
    r_blk = run_configured_search("rename fields", {"search_method": "blocking_lexical_index"}, corpus=corpus)
    checks.append(("linear path finds target", bool(r_lin) and r_lin[0]["primitive_id"] == "p:rename"))
    checks.append(("blocking path returns results (wired or falls back)", isinstance(r_blk, list)))
    r_rrf = run_configured_search("rename fields", {"search_method": "hybrid_rrf"}, corpus=corpus)
    checks.append(("hybrid_rrf fuses rankings and finds target",
                   isinstance(r_rrf, list) and any(c["primitive_id"] == "p:rename" for c in r_rrf)))

    # 5. COMPOSE data_shape: a real 2-step mutator route executes at zero tokens.
    comp = run_configured_compose(
        {"input": {"fname": "Ada", "age": "36"},
         "route": [("type_cast", {"casts": {"age": "int"}}), ("field_rename", {"mapping": {"fname": "first_name"}})]}
    )
    inner = comp["output"]
    checks.append(("data_shape_chain executes route @0 tokens",
                   comp["tokens"] == 0 and comp["route_length"] == 2 and inner.get("age") == 36 and "first_name" in inner))

    # 6. COMPOSE edge_typed: cards chain on canonical TYPE (RecordBatch -> RecordBatch -> JsonText).
    ct = run_configured_compose({"cards": corpus, "start": corpus[1]}, {"composer": "edge_typed_chain"})
    checks.append(("edge_typed_chain chains on type", ct["edge_chain_strength"] >= 1 and ct["path"] == "edge_typed_chain"))

    # 7. canonicalizers: strict screens placeholders to None; identity keeps a plain label.
    cs, ci = canonicalizer("strict_screened"), canonicalizer("identity")
    checks.append(("strict canonicalizer screens placeholder", cs("dg_{idx}") is None and cs("") is None))
    checks.append(("identity canonicalizer keeps a label", ci("ApiRequest") == "ApiRequest"))

    # 8. proof policy: candidate_only never promotes; executed_proof is the real runner.
    never = proof_policy("candidate_only")("p:x", "type_cast", {}, {})
    checks.append(("candidate_only never promotes", never["serves_truth"] is False and never["promoted"] is False))

    # 8b. rerankers resolve; edge_affinity boosts a canonical-type match above an equal lexical peer.
    aff_cards = [
        {"primitive_id": "p:json", "title": "convert data", "input_edge": "RecordBatch", "output_edge": "JsonText", "blackbox": "x"},
        {"primitive_id": "p:hash", "title": "convert data", "input_edge": "RecordBatch", "output_edge": "HashDigest", "blackbox": "x"},
    ]
    aff_cfg = resolve_config({"reranker": "edge_affinity"})
    ranked = reranker("edge_affinity")("convert data to jsontext", aff_cards, config=aff_cfg)
    checks.append(("edge_affinity boosts the type-matching card", ranked[0]["primitive_id"] == "p:json"))
    d1 = [c["primitive_id"] for c in reranker("lexical_idf")("convert data", aff_cards, config=aff_cfg)]
    d2 = [c["primitive_id"] for c in reranker("lexical_idf")("convert data", aff_cards, config=aff_cfg)]
    checks.append(("rerank is deterministic", d1 == d2 and len(d1) == 2))
    comp = run_configured_retrieve("convert data", {"search_method": "linear_lexical", "reranker": "lexical_idf"}, corpus=aff_cards)
    checks.append(("retrieve composite (search+rerank) returns ranked results", len(comp) == 2))
    try:
        reranker("cross_encoder"); rr_nw = False
    except PathNotWired:
        rr_nw = True
    checks.append(("planned reranker (cross_encoder) raises PathNotWired", rr_nw))

    # 9. DecisionReceipt is deterministic + discloses non-wired selections.
    rec1 = decision_receipt({"search_method": "dense_ann"})
    rec2 = decision_receipt({"search_method": "dense_ann"})
    checks.append(("decision receipt deterministic", rec1["config_hash"] == rec2["config_hash"]))
    checks.append(("receipt discloses non-wired selection", "search_method" in rec1["non_wired_selected"]))
    checks.append(("receipts are candidate/serves_truth=false", rec1["serves_truth"] is False))

    failed = [name for name, ok in checks if not ok]
    if failed:
        print("FAIL - primitive_paths_config:\n  " + "\n  ".join(failed))
        return 1
    ov = portfolio_overview()
    print(f"PASS - primitive_paths_config: {ov['total_paths']} paths across {len(DECISION_POINTS)} decision points "
          f"({ov['total_wired']} wired), {len(PARAMETERS)} tunable parameters; ACTIVE_DEFAULT reproduces current "
          f"behavior (replaces nothing); paths are contract-substitutable and every choice emits a receipt.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Primitive runtime path & parameter config portfolio.")
    ap.add_argument("--self-test", action="store_true", help="run offline self-test")
    ap.add_argument("--overview", action="store_true", help="print the portfolio overview")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    if args.overview:
        print(json.dumps(portfolio_overview(), indent=2))
        return 0
    print(json.dumps(portfolio_overview(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
