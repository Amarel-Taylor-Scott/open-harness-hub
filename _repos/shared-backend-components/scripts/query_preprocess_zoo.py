"""scripts.query_preprocess_zoo — the FULL GRAPH of query-preprocessing routes, each toggleable ON/OFF, so
we can try every combination (grid) — with and without LLM preprocessing, with and without each
deterministic agent — and MEASURE which route set retrieves best. No single chosen solution; a portfolio of
routes and a grid runner that races them (the multi-path law applied to query understanding).

A ROUTE is `fn(query, enrichment, llm) -> enrichment'` — it reads the query + what earlier routes added and
contributes NEW signals (rewritten text, extracted intent/object/action, sub-queries, expansion terms, typed
edges). Routes are ORDERED and each is a toggle. LLM routes call the live Ollama lane through an injected
``llm(prompt) -> str`` seam (None = the route no-ops, so the whole zoo runs offline/deterministically in the
self-test and CI). The enriched query is what retrieval then consumes.

Route families (turn any subset on):
  DETERMINISTIC (free, always available): normalize (case/whitespace/ascii-fold via robust_query_grains),
    decompose (query_decomposer clause split + constraints), facet (operation/datatype/keyphrase), grains
    (the 6 noise-robust match grains as query keys), typed_roles (hierarchical intent/object/action/outcome).
  LLM (opt-in, costs tokens — must save more than it spends): llm_normalize (fix typos / expand abbrev /
    translate mixed-language to canonical English), llm_intent (one-line canonical intent), llm_components
    (JSON sub-capability list), llm_typed_fields (intent/object/action/constraints as JSON), llm_expand
    (synonyms/related terms), llm_edge_types (guess input->output edge types directly).

``run_grid`` enumerates route-subset combinations and, given a scorer, returns the best route set by receipt.
serves_truth=false — a preprocessing result is a candidate enrichment, never truth.

    PYTHONPATH=. python3 scripts/query_preprocess_zoo.py --self-test
    PYTHONPATH=. python3 scripts/query_preprocess_zoo.py --catalog
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
import itertools  # noqa: E402
import json  # noqa: E402
from typing import Any, Callable, Optional  # noqa: E402

from scripts import primitive_descriptor as _desc  # noqa: E402  REUSE: facets
from scripts import query_decomposer as _decomp  # noqa: E402  REUSE: deterministic component split
from scripts import robust_query_grains as _grains  # noqa: E402  REUSE: normalize + grain keys
from scripts import hierarchical_semantic_embeddings as _hier  # noqa: E402  REUSE: typed roles

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}

# A route: (query, enrichment, llm_or_none) -> enrichment (mutated copy). ``kind`` says deterministic vs llm.
Route = Callable[[str, dict, Optional[Callable[[str], str]]], dict]


# ── DETERMINISTIC ROUTES (free, always on-able) ──────────────────────────────────────────────────────────────
def _det_normalize(query: str, enr: dict, llm: Optional[Callable]) -> dict:
    enr["normalized_text"] = _grains._ascii_fold(" ".join(query.lower().split()))
    return enr


def _det_decompose(query: str, enr: dict, llm: Optional[Callable]) -> dict:
    d = _decomp.decompose(query)
    enr["components"] = d["wiring_order"]
    enr["constraints"] = d["constraints"]
    return enr


def _det_facet(query: str, enr: dict, llm: Optional[Callable]) -> dict:
    qc = {"title": query, "blackbox": query, "input_edge": "", "output_edge": ""}
    enr["operations"] = sorted(_decomp._robust_operations(query))
    enr["datatypes"] = sorted(_desc.datatypes(qc))
    enr["keyphrases"] = sorted(_desc.keyphrases(qc))
    return enr


def _det_grains(query: str, enr: dict, llm: Optional[Callable]) -> dict:
    enr["char_trigrams"] = sorted(_grains._char_ngrams(query))[:40]
    return enr


def _det_typed_roles(query: str, enr: dict, llm: Optional[Callable]) -> dict:
    enr["role_texts"] = {r: _hier._q_role_text(query, r) for r in _hier.ROLES}
    return enr


# ── LLM ROUTES (opt-in; no-op when llm is None so the zoo runs offline) ──────────────────────────────────────
def _one_line(text: str) -> str:
    return " ".join(str(text).split())[:200]


def _llm_normalize(query: str, enr: dict, llm: Optional[Callable]) -> dict:
    if llm is None:
        return enr
    prompt = ("Rewrite this developer request in clean canonical English: fix typos, expand abbreviations, "
              "translate any non-English words. Output ONLY the rewritten sentence.\n\n" + query)
    enr["llm_normalized"] = _one_line(_safe_llm(llm, prompt))
    return enr


def _llm_intent(query: str, enr: dict, llm: Optional[Callable]) -> dict:
    if llm is None:
        return enr
    prompt = ("In one short phrase, state the core capability this request needs (the intent), no preamble:\n\n"
              + query)
    enr["llm_intent"] = _one_line(_safe_llm(llm, prompt))
    return enr


def _llm_components(query: str, enr: dict, llm: Optional[Callable]) -> dict:
    if llm is None:
        return enr
    prompt = ("Break this request into an ordered list of atomic sub-capabilities. Output ONLY a JSON array "
              "of short strings, nothing else.\n\n" + query)
    enr["llm_components"] = _safe_json_list(_safe_llm(llm, prompt))
    return enr


def _llm_typed_fields(query: str, enr: dict, llm: Optional[Callable]) -> dict:
    if llm is None:
        return enr
    prompt = ('Extract these fields from the request as JSON with keys intent, object, action, constraints '
              '(constraints is an array). Output ONLY the JSON object.\n\n' + query)
    enr["llm_typed_fields"] = _safe_json_obj(_safe_llm(llm, prompt))
    return enr


def _llm_expand(query: str, enr: dict, llm: Optional[Callable]) -> dict:
    if llm is None:
        return enr
    prompt = ("List 5 synonyms or closely related technical terms for the key capability in this request. "
              "Output ONLY a JSON array of single words.\n\n" + query)
    enr["llm_expansion"] = _safe_json_list(_safe_llm(llm, prompt))
    return enr


def _llm_edge_types(query: str, enr: dict, llm: Optional[Callable]) -> dict:
    if llm is None:
        return enr
    prompt = ('What input data type and output data type does this request transform between? Output ONLY '
              'JSON {"input": "TypeName", "output": "TypeName"}.\n\n' + query)
    enr["llm_edge_types"] = _safe_json_obj(_safe_llm(llm, prompt))
    return enr


def _llm_hyde(query: str, enr: dict, llm: Optional[Callable]) -> dict:
    """HyDE (Hypothetical Document Embeddings, Gao et al.): the LLM writes a hypothetical IDEAL PRIMITIVE CARD
    for the request, and retrieval runs on THAT text — which is written in CARD vocabulary (title + what-it-
    does + edges), not the user's query vocabulary. This is the canonical bridge for the query↔card word gap
    that plagues 'retry logic' → 'resilient call wrapper': the hypothetical card shares the corpus's words.
    Stored as ``hyde_text`` for the retriever to embed/match instead of (or beside) the raw query."""
    if llm is None:
        return enr
    prompt = ("Write a one-sentence description of the ideal reusable software primitive that would satisfy "
              "this request, phrased like a component catalog entry (what it does + its input and output "
              "data types). Output ONLY the sentence.\n\n" + query)
    enr["hyde_text"] = _one_line(_safe_llm(llm, prompt))
    return enr


def _safe_llm(llm: Callable, prompt: str) -> str:
    try:
        return str(llm(prompt))
    except Exception:  # noqa: BLE001 — an LLM route never crashes the pipeline; it degrades to no-op
        return ""


def _safe_json_list(text: str) -> list[str]:
    try:
        start, end = text.find("["), text.rfind("]")
        val = json.loads(text[start:end + 1]) if start != -1 and end != -1 else []
        return [str(x) for x in val] if isinstance(val, list) else []
    except (json.JSONDecodeError, ValueError):
        return []


def _safe_json_obj(text: str) -> dict[str, Any]:
    try:
        start, end = text.find("{"), text.rfind("}")
        val = json.loads(text[start:end + 1]) if start != -1 and end != -1 else {}
        return val if isinstance(val, dict) else {}
    except (json.JSONDecodeError, ValueError):
        return {}


#: THE ROUTE GRAPH — every preprocessing route by name, each a toggleable node. ``kind`` = deterministic|llm.
ROUTES: dict[str, dict[str, Any]] = {
    "det_normalize":   {"fn": _det_normalize, "kind": "deterministic"},
    "det_decompose":   {"fn": _det_decompose, "kind": "deterministic"},
    "det_facet":       {"fn": _det_facet, "kind": "deterministic"},
    "det_grains":      {"fn": _det_grains, "kind": "deterministic"},
    "det_typed_roles": {"fn": _det_typed_roles, "kind": "deterministic"},
    "llm_normalize":   {"fn": _llm_normalize, "kind": "llm"},
    "llm_intent":      {"fn": _llm_intent, "kind": "llm"},
    "llm_components":  {"fn": _llm_components, "kind": "llm"},
    "llm_typed_fields": {"fn": _llm_typed_fields, "kind": "llm"},
    "llm_expand":      {"fn": _llm_expand, "kind": "llm"},
    "llm_edge_types":  {"fn": _llm_edge_types, "kind": "llm"},
    "llm_hyde":        {"fn": _llm_hyde, "kind": "llm"},   # hypothetical ideal-card text (query↔card bridge)
}


def preprocess(query: str, routes: list[str], *, llm: Optional[Callable[[str], str]] = None) -> dict[str, Any]:
    """Run an ORDERED subset of routes over the query, accumulating enrichment. Unknown route names raise;
    an LLM route with ``llm=None`` no-ops (so any route set runs offline). serves_truth=false."""
    enr: dict[str, Any] = {"query": query, "routes_run": [], "llm_calls": 0}
    for name in routes:
        if name not in ROUTES:
            raise KeyError(f"unknown route {name!r}; routes are {sorted(ROUTES)}")
        spec = ROUTES[name]
        before = enr.get("llm_calls", 0)
        counting_llm = None
        if spec["kind"] == "llm" and llm is not None:
            def counting_llm(p, _llm=llm):  # noqa: E306 — count real LLM calls for the token receipt
                enr["llm_calls"] = enr.get("llm_calls", 0) + 1
                return _llm(p)
        enr = spec["fn"](query, enr, counting_llm if spec["kind"] == "llm" else None)
        enr["routes_run"].append(name)
        _ = before
    enr.update(BOUNDARY)
    return enr


def route_grid(*, include_llm: bool = False, max_routes: Optional[int] = None) -> list[list[str]]:
    """Every route-subset combination (the grid). Deterministic-only by default; ``include_llm`` adds the LLM
    routes. ``max_routes`` caps subset size to keep the grid tractable. Deterministic order within a subset."""
    names = [n for n, s in ROUTES.items() if include_llm or s["kind"] == "deterministic"]
    combos: list[list[str]] = []
    top = len(names) if max_routes is None else min(max_routes, len(names))
    for size in range(0, top + 1):
        for combo in itertools.combinations(names, size):
            combos.append(list(combo))
    return combos


def run_grid(query: str, scorer: Callable[[dict], float], *, include_llm: bool = False,
             max_routes: Optional[int] = None, llm: Optional[Callable[[str], str]] = None) -> dict[str, Any]:
    """Race every route-subset over the query, score each enriched result, rank by receipt. The best route
    set is a routing DEFAULT (never truth); every combination is kept as a labelled row (multi-path law)."""
    receipts: list[dict[str, Any]] = []
    for combo in route_grid(include_llm=include_llm, max_routes=max_routes):
        enr = preprocess(query, combo, llm=llm)
        receipts.append({"routes": combo, "score": round(float(scorer(enr)), 4),
                         "llm_calls": enr.get("llm_calls", 0)})
    ranked = sorted(receipts, key=lambda r: (-r["score"], r["llm_calls"], len(r["routes"])))
    return {"record_type": "preprocess_grid_receipt", "query": query,
            "combinations_raced": len(receipts), "champion": ranked[0] if ranked else None,
            "receipts": ranked, **BOUNDARY}


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []
    q = "add retry logik to teh importer, keeping the public api unchanged"  # deliberate typos

    # (a) the graph exposes both families as toggleable nodes
    checks.append(("route graph has deterministic AND llm families",
                   {s["kind"] for s in ROUTES.values()} == {"deterministic", "llm"}))
    # (b) a deterministic subset runs OFFLINE (llm=None) and enriches
    enr = preprocess(q, ["det_normalize", "det_decompose", "det_facet"])
    checks.append(("deterministic routes run offline and enrich",
                   "normalized_text" in enr and "components" in enr and "operations" in enr
                   and enr["llm_calls"] == 0))
    checks.append(("normalize handles typos/case (importer survives, ascii-folded, lowercased)",
                   "importer" in enr["normalized_text"] and enr["normalized_text"] == enr["normalized_text"].lower()))
    checks.append(("decompose strips the constraint (public api not a component)",
                   any("public api" in c for c in enr["constraints"])))
    # (c) an LLM route with llm=None NO-OPs; with a stub llm it fires and is COUNTED
    off = preprocess(q, ["llm_intent", "llm_components"])
    checks.append(("LLM routes no-op when llm is None (offline default)",
                   off["llm_calls"] == 0 and "llm_intent" not in off))
    stub = preprocess(q, ["llm_intent", "llm_components"],
                      llm=lambda p: '["fetch the data", "retry on failure"]' if "sub-capabil" in p else "retry a call")
    checks.append(("LLM routes fire + are token-counted with a live llm seam",
                   stub["llm_calls"] == 2 and stub.get("llm_intent") == "retry a call"
                   and stub.get("llm_components") == ["fetch the data", "retry on failure"]))
    checks.append(("a crashing LLM route degrades to no-op, never crashes",
                   preprocess(q, ["llm_intent"], llm=lambda p: (_ for _ in ()).throw(RuntimeError()))
                   .get("llm_intent") == ""))
    # HyDE route: the LLM writes a hypothetical ideal-card text (card vocabulary) for the retriever
    hyde = preprocess("add retry logic to the api client",
                      ["llm_hyde"], llm=lambda p: "A resilient call wrapper that retries a Call with backoff, input Call output ResilientCall.")
    checks.append(("HyDE route produces hypothetical ideal-card text in CARD vocabulary",
                   "hyde_text" in hyde and "wrapper" in hyde["hyde_text"] and hyde["llm_calls"] == 1))
    # (d) THE GRID: every subset combination is enumerable and raceable
    det_grid = route_grid(include_llm=False)
    n_det = sum(1 for s in ROUTES.values() if s["kind"] == "deterministic")
    checks.append(("the deterministic grid enumerates all 2^n subsets", len(det_grid) == 2 ** n_det))
    full_grid = route_grid(include_llm=True, max_routes=2)
    checks.append(("the full grid includes LLM routes and respects max_routes",
                   all(len(c) <= 2 for c in full_grid) and any("llm_intent" in c for c in full_grid)))
    # a toy scorer: reward more distinct enrichment keys (proxy for 'more signal') — the grid finds the best set
    grid = run_grid(q, scorer=lambda e: len([k for k in e if k not in ("query", "routes_run", "llm_calls",
                                                                        "candidate", "serves_truth")]),
                    include_llm=False)
    checks.append(("run_grid races every combo and picks a champion route set",
                   grid["champion"] is not None and grid["combinations_raced"] == 2 ** n_det
                   and len(grid["champion"]["routes"]) >= 1))
    # (e) determinism + governance
    checks.append(("preprocess is deterministic (byte-identical twice)",
                   json.dumps(preprocess(q, ["det_normalize", "det_facet"]), sort_keys=True)
                   == json.dumps(preprocess(q, ["det_normalize", "det_facet"]), sort_keys=True)))
    checks.append(("enrichment is candidate/serves_truth=false", enr["serves_truth"] is False))

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    n_llm = sum(1 for s in ROUTES.values() if s["kind"] == "llm")
    print(f"\nPASS - query_preprocess_zoo: a toggleable GRAPH of {len(ROUTES)} preprocessing routes "
          f"({n_det} deterministic + {n_llm} LLM), each on/off; LLM routes no-op offline and are token-counted "
          f"live; run_grid races EVERY subset combination and picks the champion route set by receipt "
          f"(with/without preprocessing, with/without each agent). No single chosen path — the full graph is "
          f"baked in and MEASURED. serves_truth=false.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--catalog", action="store_true", help="print the route graph")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.catalog:
        print(json.dumps({name: spec["kind"] for name, spec in ROUTES.items()}, indent=2))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
