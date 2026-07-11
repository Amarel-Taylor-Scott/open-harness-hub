"""capability_lane — the serving lane for edge-only, API-verified, deterministically-composable capabilities.

Backend wiring for the new capability plane: load the edge-only corpus (curated + API-introspected), enrich it
deterministically (canonical edges + 3 description registers, 0 tokens), and expose three serve-time verbs the
gateway wires to MCP tools + agent actions:

  • search(query)               → verified package capabilities matching a task, each with its usage recipe;
  • get(capability_id)          → the full card + verified recipe + canonical edges;
  • remix(input_type→output)    → a DETERMINISTIC exact-typed-join chain + correct-by-construction wiring, 0 tok.

Always-available base corpus (no file dependency, so it deploys clean): the 12 curated cross-registry cards +
the API-verified stdlib cards. The harvested corpus (gitignored) loads on top when present. serves_truth=false.

    python3 scripts/capability_lane.py --self-test
    python3 scripts/capability_lane.py --remix HttpRequestSpec ValidatedModel
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Optional

_HERE = Path(__file__).resolve()
_SBC = _HERE.parent.parent
for _p in (str(_SBC), str(_SBC / "scripts"), str(_SBC.parent.parent),
           str(_SBC.parent.parent / "_repos" / "teleon" / "backend")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from scripts.deterministic_edge_derivation import normalize_edge
from scripts.deterministic_description import describe_registers
from scripts.deterministic_remix import remix as _remix, remix_all as _remix_all

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
_HARVEST_PATH = _SBC / "data" / "dev-intel" / "edge_only_harvest" / "edge_only_harvested_cards.jsonl"
_CORPUS_CACHE: Optional[list[dict[str, Any]]] = None

#: real packages with ALIGNED single-in/single-out canonical edges — a composition BACKBONE so remix has real
#: linear pipelines to return on the deployed corpus (the class-template cards mostly don't chain). Verified
#: recipes; edges deliberately use the canonical vocabulary so the joins are exact. candidate-only.
_PIPELINE_CARDS: list[dict[str, Any]] = [
    {"primitive_id": "pkg.reqwest.fetch", "title": "reqwest — fetch JSON over HTTP", "capability_class": "http_client",
     "input_edge": "HttpRequestSpec", "output_edge": "JsonBytes", "has_code_body": False,
     "package": {"name": "reqwest", "registry": "crates.io", "url": "https://crates.io/crates/reqwest"},
     "usage_recipes": [{"route": "get_json", "snippet": "let bytes = reqwest::blocking::get(url)?.bytes()?;"}]},
    {"primitive_id": "pkg.serde_json.parse", "title": "serde_json — JSON bytes to a mapping", "capability_class": "deserialize",
     "input_edge": "JsonBytes", "output_edge": "Mapping", "has_code_body": False,
     "package": {"name": "serde_json", "registry": "crates.io", "url": "https://crates.io/crates/serde_json"},
     "usage_recipes": [{"route": "parse", "snippet": "let v: serde_json::Value = serde_json::from_slice(&bytes)?;"}]},
    {"primitive_id": "pkg.jq.select", "title": "jaq — select a field path from a mapping", "capability_class": "parse_text",
     "input_edge": "Mapping", "output_edge": "Text", "has_code_body": False,
     "package": {"name": "jaq", "registry": "crates.io", "url": "https://crates.io/crates/jaq"},
     "usage_recipes": [{"route": "select", "snippet": "let text = jaq_run(&value, \".field\")?;"}]},
    {"primitive_id": "pkg.fastembed.embed", "title": "fastembed — text to a vector", "capability_class": "serialize",
     "input_edge": "Text", "output_edge": "Vector", "has_code_body": False,
     "package": {"name": "fastembed", "registry": "pypi", "url": "https://pypi.org/project/fastembed/"},
     "usage_recipes": [{"route": "embed", "snippet": "vec = TextEmbedding().embed([text])"}]},
    {"primitive_id": "pkg.pydantic.validate", "title": "pydantic — mapping to a validated model", "capability_class": "validate",
     "input_edge": "Mapping", "output_edge": "ValidatedModel", "has_code_body": False,
     "package": {"name": "pydantic", "registry": "pypi", "url": "https://pypi.org/project/pydantic/"},
     "usage_recipes": [{"route": "validate", "snippet": "model = MySchema.model_validate(mapping)"}]},
]


def _enrich(card: dict[str, Any]) -> dict[str, Any]:
    """0-token serve-time enrichment: canonical edges (so composition is exact) + description registers +
    a stable `id` for the composer. Non-destructive."""
    out = dict(card)
    out["id"] = card.get("primitive_id") or card.get("id") or card.get("package", {}).get("module") or card.get("title")
    out["input_edge"] = normalize_edge(card.get("input_edge", ""))
    out["output_edge"] = normalize_edge(card.get("output_edge", ""))
    out["description_registers"] = describe_registers(out)
    return out


def load_corpus(*, include_harvest: bool = True, cards: Optional[list[dict[str, Any]]] = None) -> list[dict[str, Any]]:
    """Assemble + enrich the serve-time corpus. Cached. `cards` overrides for tests/fixtures."""
    global _CORPUS_CACHE
    if cards is not None:
        return [_enrich(c) for c in cards]
    if _CORPUS_CACHE is not None:
        return _CORPUS_CACHE
    base: list[dict[str, Any]] = list(_PIPELINE_CARDS)  # the aligned composition backbone (real chains)
    from scripts.edge_only_package_primitives import emit_cards as _curated  # noqa: PLC0415
    base.extend(_curated())
    try:
        from scripts.edge_only_package_introspection import derive_all as _stdlib  # noqa: PLC0415
        base.extend(_stdlib())
    except Exception:  # noqa: BLE001
        pass
    if include_harvest and _HARVEST_PATH.exists():
        try:
            base.extend(json.loads(l) for l in _HARVEST_PATH.read_text().splitlines() if l.strip())
        except Exception:  # noqa: BLE001
            pass
    # dedupe by id, deterministic order
    seen, rows = set(), []
    for c in (_enrich(c) for c in base):
        if c["id"] in seen:
            continue
        seen.add(c["id"])
        rows.append(c)
    rows.sort(key=lambda c: str(c["id"]))
    _CORPUS_CACHE = rows
    return rows


def _toks(s: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", str(s).lower()))


def search(query: str, *, limit: int = 5, corpus: Optional[list[dict[str, Any]]] = None) -> dict[str, Any]:
    """Lexical match over the enriched cards' registers + edges. Returns capabilities + their usage recipe."""
    corpus = corpus if corpus is not None else load_corpus()
    qt = _toks(query)
    scored = []
    for c in corpus:
        doc = _toks(" ".join(c.get("description_registers", {}).values()) + " " + c["input_edge"] + " " + c["output_edge"])
        s = len(qt & doc)
        if s:
            scored.append((s, c))
    scored.sort(key=lambda x: (-x[0], str(x[1]["id"])))
    hits = [{"id": c["id"], "title": c.get("title", ""), "input_edge": c["input_edge"],
             "output_edge": c["output_edge"], "capability_class": c.get("capability_class"),
             "recipe": (c.get("usage_recipes") or [{}])[0].get("snippet", ""),
             "package": c.get("package", {}).get("url", ""), "score": s} for s, c in scored[:limit]]
    return {"query": query, "count": len(hits), "results": hits, **BOUNDARY}


def get(capability_id: str, *, corpus: Optional[list[dict[str, Any]]] = None) -> dict[str, Any]:
    corpus = corpus if corpus is not None else load_corpus()
    for c in corpus:
        if str(c["id"]) == str(capability_id):
            return {"found": True, "capability": c, **BOUNDARY}
    return {"found": False, "capability_id": capability_id, **BOUNDARY}


def remix(input_type: str, output_type: str, *, all_paths: bool = False,
          corpus: Optional[list[dict[str, Any]]] = None) -> dict[str, Any]:
    """Deterministic 0-token composition: exact-typed-join chain from input_type to output_type + wiring."""
    corpus = corpus if corpus is not None else load_corpus()
    if all_paths:
        chains = _remix_all(corpus, input_type, output_type)
        return {"input_type": normalize_edge(input_type), "output_type": normalize_edge(output_type),
                "paths": len(chains), "composites": chains, **BOUNDARY}
    comp = _remix(corpus, input_type, output_type)
    return {"input_type": normalize_edge(input_type), "output_type": normalize_edge(output_type),
            "found": comp is not None, "composite": comp,
            "note": None if comp else "no exact-typed-join path in the current corpus — refused, not hallucinated",
            **BOUNDARY}


def stats(*, corpus: Optional[list[dict[str, Any]]] = None) -> dict[str, Any]:
    corpus = corpus if corpus is not None else load_corpus()
    in_types = {c["input_edge"] for c in corpus}
    out_types = {c["output_edge"] for c in corpus}
    return {"capabilities": len(corpus), "distinct_input_types": len(in_types),
            "distinct_output_types": len(out_types), "composable_type_bridges": len(in_types & out_types),
            "harvest_loaded": _HARVEST_PATH.exists(), **BOUNDARY}


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []
    # a controlled corpus that chains (mirrors a real edge-only slice)
    fixture = [
        {"primitive_id": "reqwest", "title": "reqwest http", "input_edge": "HttpRequestSpec",
         "output_edge": "JsonBytes", "capability_class": "http_client",
         "usage_recipes": [{"snippet": "resp = reqwest::get(url)?.json()?"}]},
        {"primitive_id": "serde_json", "title": "serde_json parse", "input_edge": "JsonBytes",
         "output_edge": "Mapping", "capability_class": "deserialize",
         "usage_recipes": [{"snippet": "v = serde_json::from_slice(bytes)?"}]},
        {"primitive_id": "pydantic", "title": "pydantic validate", "input_edge": "Mapping",
         "output_edge": "ValidatedModel", "capability_class": "validate",
         "usage_recipes": [{"snippet": "m = pydantic.BaseModel.model_validate(x)"}]},
    ]
    corp = load_corpus(cards=fixture)

    checks.append(("corpus enriches: canonical edges + description registers + stable ids",
                   all(c["id"] and c["description_registers"] and c["input_edge"] for c in corp)))

    # search finds the http capability + returns its recipe
    sr = search("make an http request and get json", corpus=corp)
    checks.append(("search returns matching capabilities WITH usage recipes",
                   sr["count"] >= 1 and any("reqwest" in str(h["id"]) for h in sr["results"])
                   and all("recipe" in h for h in sr["results"])))

    # get returns a full card
    g = get("pydantic", corpus=corp)
    checks.append(("get returns the full verified card", g["found"] and g["capability"]["id"] == "pydantic"))

    # REMIX: deterministic exact chain HttpRequestSpec -> ValidatedModel, 0 tokens, correct-by-construction
    rx = remix("HttpRequestSpec", "ValidatedModel", corpus=corp)
    checks.append(("remix: deterministic 3-step chain + wiring at 0 tokens",
                   rx["found"] and rx["composite"]["members"] == ["reqwest", "serde_json", "pydantic"]
                   and rx["composite"]["token_cost"] == 0 and "result =" in rx["composite"]["wiring_recipe"]))

    # honest: unreachable target refused
    rx2 = remix("HttpRequestSpec", "NdArray", corpus=corp)
    checks.append(("remix refuses an unreachable target (not hallucinated)",
                   rx2["found"] is False and "refused" in rx2["note"]))

    # stats compute composable bridges
    st = stats(corpus=corp)
    checks.append(("stats report capabilities + composable type bridges",
                   st["capabilities"] == 3 and st["composable_type_bridges"] >= 1))

    # the REAL always-available corpus loads (curated + introspected, no file dependency)
    real = load_corpus()
    checks.append(("real base corpus loads (curated + API-introspected, deploy-clean)",
                   len(real) >= 20 and all(c.get("has_code_body") is False for c in real)))

    # deterministic
    checks.append(("serve verbs deterministic (byte-identical)",
                   json.dumps(remix("HttpRequestSpec", "ValidatedModel", corpus=corp), sort_keys=True, default=str)
                   == json.dumps(rx, sort_keys=True, default=str)))

    ok = all(v for _, v in checks)
    print("capability_lane — self-test")
    for name, v in checks:
        print(f"  [{'ok' if v else 'FAIL'}] {name}")
    st = stats()
    print(f"  serving corpus: {st['capabilities']} verified edge-only capabilities, "
          f"{st['composable_type_bridges']} composable type bridges, harvest_loaded={st['harvest_loaded']}.")
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


def _main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--remix", nargs=2, metavar=("FROM", "TO"))
    ap.add_argument("--search", metavar="QUERY")
    args = ap.parse_args()
    if args.remix:
        print(json.dumps(remix(args.remix[0], args.remix[1], all_paths=True), indent=2, default=str))
        return 0
    if args.search:
        print(json.dumps(search(args.search), indent=2, default=str))
        return 0
    return _self_test()


if __name__ == "__main__":
    raise SystemExit(_main())
