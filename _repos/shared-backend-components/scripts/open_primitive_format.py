#!/usr/bin/env python3
"""open_primitive_format — a candidate OPEN standard: the Open Primitive Format (OPF) + a stable query interface.

Owner (2026-07-10): registries index names/text/symbols/deps (candidates a human inspects) but none publish a
machine-verifiable "this output satisfies that input under these effects" graph; the agentic discovery drafts
(ARD/MCP/A2A/AgentSkill) stop before invocation; Google shipped an Open Knowledge Format but there is no Open
*Primitive*/*Edge* Format. Are we in a position to define one supporting multiple weighted edges, multiple
tunable embeddings, multiple search systems — and can Teleon / future extensions QUERY it?

This module is the affirmative, concrete answer: OPF v0 — a portable, validated record for a primitive with
MULTIPLE directional weighted typed ports (consumes[]/produces[], not one input/output), MULTIPLE tunable
embeddings (a pluggable list), evidence refs, the capability/implementation split, compatibility-grade
authority, and delivery modes — PLUS `OPFQuery`, a stable, EXTENSIBLE query contract (a zoo of query methods)
that an external consumer like Teleon calls WITHOUT touching internal card structure. Adding a query method, an
embedding model, or a search system is one row; consumers keep the same contract (that IS the extensibility).

    PYTHONPATH=. python3 scripts/open_primitive_format.py --self-test
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Callable, Optional

_HERE = Path(__file__).resolve()
_SBC = _HERE.parent.parent
_ROOT = _SBC.parent.parent
for _p in (str(_SBC), str(_SBC / "scripts"), str(_ROOT), str(_ROOT / "_repos" / "teleon" / "backend")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    from src.teleon.experiments.ids import canonical_id  # noqa: E402  the ONE id authority (data plane law)
except Exception as exc:  # noqa: BLE001
    raise SystemExit(f"open_primitive_format requires canonical_id; import failed: {exc}")

OPF_VERSION = "0"
OPF_ID_PREFIX = "opf"
_REQUIRED_TOP = ("opf_version", "record_type", "id", "capability_id", "ports", "embeddings",
                 "delivery_modes", "governance")


def to_opf(card: dict[str, Any], *, embeddings: Optional[list[dict[str, Any]]] = None) -> dict[str, Any]:
    """Serialize a primitive card into an OPF v0 record. A card's single input_edge/output_edge become one
    consumes/produces port each; a card may also declare ports[] directly (multi-port). Embeddings are a
    pluggable list (0..n, tunable) — the standard carries the SPACE + model + dim + a vector handle, not bytes."""
    consumes = card.get("consumes_ports")
    produces = card.get("produces_ports")
    if consumes is None:
        consumes = [{"edge": card["input_edge"], "role": "payload", "weight": 1.0, "required": True}] \
            if card.get("input_edge") else []
    if produces is None:
        produces = [{"edge": card["output_edge"], "role": "payload", "weight": 1.0}] \
            if card.get("output_edge") else []
    cap = str(card.get("capability_id") or card.get("output_edge") or card.get("title") or "capability")
    impl = str(card.get("card_id") or card.get("primitive_id") or canonical_id("impl", cap))
    return {
        "opf_version": OPF_VERSION, "record_type": "open_primitive",
        "id": canonical_id(OPF_ID_PREFIX, impl),
        "capability_id": cap, "implementation_id": impl, "title": card.get("title"),
        "ports": {"consumes": consumes, "produces": produces},
        "embeddings": embeddings if embeddings is not None else card.get("embeddings", []),
        "evidence_refs": card.get("evidence_refs", []),
        "compatibility": {"grade_authority": "compatibility_lattice",
                          "note": "a join's grade is decided by compatibility_lattice + edge_contract_and_adapters; "
                                  "an OPF edge NAME retrieves, it does not authorize"},
        "delivery_modes": card.get("delivery_modes", ["python_import"]),
        "search_systems": card.get("search_systems", ["lexical", "dense", "hybrid"]),
        "governance": {"candidate": True, "serves_truth": False,
                       "lifecycle": card.get("lifecycle", "candidate")},
    }


def validate_opf(record: dict[str, Any]) -> dict[str, Any]:
    """Validate an OPF record's shape. Returns {valid, errors}. Strict on the standard's invariants: version,
    the required top keys, well-formed weighted ports, well-formed embedding descriptors, and governance."""
    errors: list[str] = []
    if record.get("opf_version") != OPF_VERSION:
        errors.append(f"opf_version must be {OPF_VERSION!r}")
    for key in _REQUIRED_TOP:
        if key not in record:
            errors.append(f"missing required key: {key}")
    ports = record.get("ports", {})
    if not isinstance(ports, dict) or "consumes" not in ports or "produces" not in ports:
        errors.append("ports must be an object with consumes[] and produces[]")
    else:
        for side in ("consumes", "produces"):
            for i, port in enumerate(ports.get(side, [])):
                if not isinstance(port, dict) or "edge" not in port:
                    errors.append(f"ports.{side}[{i}] must be an object with an 'edge'")
                elif not isinstance(port.get("weight", 1.0), (int, float)):
                    errors.append(f"ports.{side}[{i}].weight must be numeric")
    for i, emb in enumerate(record.get("embeddings", [])):
        if not isinstance(emb, dict) or not {"model", "dim", "space"} <= set(emb):
            errors.append(f"embeddings[{i}] must carry model + dim + space (a tunable descriptor, not bytes)")
    gov = record.get("governance", {})
    if not isinstance(gov, dict) or gov.get("serves_truth") is not False:
        errors.append("governance.serves_truth must be present and false (candidate/truth boundary)")
    return {"valid": not errors, "errors": errors}


# ── the stable, EXTENSIBLE query interface — what Teleon / any extension calls (a zoo of methods). ────────────
def build_opf_index(records: list[dict[str, Any]]) -> dict[str, Any]:
    """A queryable index over OPF records: producers/consumers by edge, by capability, by delivery mode, by
    embedding model. One streaming pass; deterministic."""
    producers: dict[str, list[str]] = {}
    consumers: dict[str, list[str]] = {}
    by_capability: dict[str, list[str]] = {}
    by_delivery: dict[str, list[str]] = {}
    by_embed_model: dict[str, list[str]] = {}
    by_id: dict[str, dict[str, Any]] = {}
    for rec in records:
        rid = rec["id"]
        by_id[rid] = rec
        by_capability.setdefault(rec.get("capability_id", ""), []).append(rid)
        for port in rec.get("ports", {}).get("produces", []):
            producers.setdefault(port["edge"], []).append(rid)
        for port in rec.get("ports", {}).get("consumes", []):
            consumers.setdefault(port["edge"], []).append(rid)
        for mode in rec.get("delivery_modes", []):
            by_delivery.setdefault(mode, []).append(rid)
        for emb in rec.get("embeddings", []):
            by_embed_model.setdefault(emb.get("model", ""), []).append(rid)
    tables = {"producers": producers, "consumers": consumers, "by_capability": by_capability,
              "by_delivery": by_delivery, "by_embed_model": by_embed_model}
    for t in tables.values():
        for k in t:
            t[k] = sorted(set(t[k]))
    return {"record_type": "opf_index", "n_records": len(by_id), "by_id": by_id, **tables}


#: the QUERY-METHOD ZOO — the extension contract. Each: (index, **args) -> [record ids]. Add a method = one row;
#: an external consumer keeps calling `query(method, ...)` unchanged. This is the extensibility guarantee.
def _q_by_capability(index: dict, capability_id: str = "", **_: Any) -> list[str]:
    return index["by_capability"].get(capability_id, [])


def _q_producers_of(index: dict, edge: str = "", **_: Any) -> list[str]:
    return index["producers"].get(edge, [])


def _q_consumers_of(index: dict, edge: str = "", **_: Any) -> list[str]:
    return index["consumers"].get(edge, [])


def _q_by_delivery_mode(index: dict, mode: str = "", **_: Any) -> list[str]:
    return index["by_delivery"].get(mode, [])


def _q_by_embedding_model(index: dict, model: str = "", **_: Any) -> list[str]:
    return index["by_embed_model"].get(model, [])


QUERY_METHODS: dict[str, Callable[..., list[str]]] = {
    "by_capability": _q_by_capability, "producers_of": _q_producers_of, "consumers_of": _q_consumers_of,
    "by_delivery_mode": _q_by_delivery_mode, "by_embedding_model": _q_by_embedding_model,
}


def register_query_method(name: str, fn: Callable[..., list[str]]) -> None:
    """Extensibility: a NEW query method (or search system, or embedding lane) is one row. External consumers
    keep the same `query(...)` contract — extensions add capability without breaking callers."""
    QUERY_METHODS[name] = fn


def query(method: str, index: dict[str, Any], *, hydrate: bool = False, **args: Any) -> dict[str, Any]:
    """THE stable query contract any extension (Teleon, a future system) calls. Method-dispatched over the zoo;
    returns ids (or hydrated records). A consumer never needs the internal card shape — only OPF + this call."""
    if method not in QUERY_METHODS:
        raise ValueError(f"unknown query method {method!r}; known: {sorted(QUERY_METHODS)}")
    ids = QUERY_METHODS[method](index, **args)
    result: dict[str, Any] = {"method": method, "args": args, "n_results": len(ids), "ids": ids}
    if hydrate:
        result["records"] = [index["by_id"][i] for i in ids]
    return result


def _self_test() -> int:
    checks: list[tuple[str, bool, str]] = []

    # (1) a pack card round-trips into a VALID OPF record (the standard represents our real primitives).
    from scripts.corporate_records_scraping_primitive_pack import build_cards  # noqa: PLC0415
    cards = build_cards()
    opf_records = [to_opf(c) for c in cards]
    validations = [validate_opf(r) for r in opf_records]
    checks.append(("every corporate-pack card serializes into a VALID OPF v0 record (the standard represents "
                   "our real primitives)",
                   all(v["valid"] for v in validations) and len(opf_records) == len(cards),
                   json.dumps(validations[0]["errors"])[:120] if not validations[0]["valid"] else ""))

    # (2) MULTIPLE WEIGHTED EDGES: a multi-port primitive (2 consumes + 2 produces, each weighted) is valid and
    #     indexes on every port — the standard is not one-input-one-output.
    multiport = to_opf({"card_id": "multi:1", "title": "join two streams",
                        "capability_id": "join.two-streams",
                        "consumes_ports": [{"edge": "LeftRows", "weight": 0.7, "role": "payload", "required": True},
                                           {"edge": "RightRows", "weight": 0.3, "role": "payload", "required": True}],
                        "produces_ports": [{"edge": "JoinedRows", "weight": 1.0},
                                           {"edge": "RejectRows", "weight": 0.1}]})
    checks.append(("MULTIPLE WEIGHTED EDGES: a 2-consume/2-produce primitive with per-port weights is valid",
                   validate_opf(multiport)["valid"]
                   and len(multiport["ports"]["consumes"]) == 2 and len(multiport["ports"]["produces"]) == 2
                   and multiport["ports"]["consumes"][0]["weight"] == 0.7, ""))

    # (3) MULTIPLE TUNABLE EMBEDDINGS: several embedding descriptors (different model/dim/space) on one record,
    #     validated — the standard supports a pluggable multi-embedding lane, not one fixed vector.
    embedded = to_opf(cards[0], embeddings=[
        {"model": "model2vec-potion-8m", "dim": 256, "space": "cosine", "vector_ref": "vec://a", "tunable": True},
        {"model": "bge-small", "dim": 384, "space": "cosine", "vector_ref": "vec://b", "tunable": True},
        {"model": "lexical-splade", "dim": 30000, "space": "dot", "vector_ref": "vec://c", "tunable": False}])
    checks.append(("MULTIPLE TUNABLE EMBEDDINGS: 3 embedding descriptors (256/384/30000-d, cosine/dot) on one "
                   "record, all valid — a pluggable multi-embedding standard",
                   validate_opf(embedded)["valid"] and len(embedded["embeddings"]) == 3
                   and {e["model"] for e in embedded["embeddings"]} == {"model2vec-potion-8m", "bge-small", "lexical-splade"},
                   ""))

    # (4) the QUERY interface answers producers_of / consumers_of / by_capability over the OPF index — this is
    #     what an EXTENSION (Teleon) calls, WITHOUT the internal card shape.
    index = build_opf_index(opf_records + [multiport, embedded])
    producers = query("producers_of", index, edge="OfficerRowBatch")
    consumers = query("consumers_of", index, edge="OfficerRowBatch")
    checks.append(("the stable QUERY contract answers producers_of/consumers_of/by_capability over OPF records "
                   "(what Teleon/an extension calls — no internal card access needed)",
                   producers["n_results"] >= 1 and consumers["n_results"] >= 1
                   and query("by_capability", index, capability_id="join.two-streams")["n_results"] == 1, ""))

    # (5) TELEON-STYLE EXTERNAL CONSUMER: a caller that ONLY has the OPF + query contract (no card import) can
    #     resolve "what produces this edge" and hydrate the portable record — the substrate is queryable by
    #     downstream products through a stable seam (portfolio law: products consume the substrate).
    external = query("producers_of", index, edge="CanonicalEntityRowBatch", hydrate=True)
    checks.append(("a Teleon-style external consumer queries by edge + hydrates portable OPF records through the "
                   "stable contract (the substrate is queryable by extensions; products consume it, not reverse)",
                   external["n_results"] >= 1 and all(r["opf_version"] == OPF_VERSION for r in external["records"])
                   and all("card_id" not in r for r in external["records"]), ""))

    # (6) EXTENSIBILITY: registering a NEW query method is one row; existing consumers keep the same contract.
    register_query_method("by_search_system",
                          lambda index, system="", **_: sorted(rid for rid, rec in index["by_id"].items()
                                                               if system in rec.get("search_systems", [])))
    hybrid = query("by_search_system", index, system="hybrid")
    checks.append(("EXTENSIBILITY: a new query method (by_search_system) is one registered row; the query "
                   "contract is unchanged for callers — extensions add capability without breaking consumers",
                   "by_search_system" in QUERY_METHODS and hybrid["n_results"] >= 1, ""))

    # (7) governance + determinism: OPF carries the candidate/truth boundary; an edge NAME retrieves, never
    #     authorizes (the compatibility authority is named, not embedded); deterministic build.
    checks.append(("OPF carries the candidate/truth boundary + names the compatibility authority (an OPF edge "
                   "retrieves, it does not authorize); deterministic serialization",
                   opf_records[0]["governance"]["serves_truth"] is False
                   and opf_records[0]["compatibility"]["grade_authority"] == "compatibility_lattice"
                   and to_opf(cards[0]) == to_opf(cards[0]), ""))

    ok = all(passed for _n, passed, _d in checks)
    print(f"{'PASS' if ok else 'FAIL'} - open_primitive_format: OPF v0 — a candidate OPEN standard for a "
          f"primitive with MULTIPLE weighted directional edges + MULTIPLE tunable embeddings + multiple search "
          f"systems + evidence + capability/impl split, validated and round-tripping our real pack, PLUS a "
          f"stable EXTENSIBLE query contract (a query-method zoo) that Teleon / any extension calls — the "
          f"substrate is queryable by downstream products; an OPF edge retrieves, it does not authorize. "
          f"serves_truth=false")
    for name, passed, detail in checks:
        print(f"  [{'ok' if passed else 'XX'}] {name}" + (f"  ({detail[:200]})" if not passed else ""))
    return 0 if ok else 1


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="The Open Primitive Format (OPF) + a stable query interface.")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--emit-sample", action="store_true", help="print one OPF record from the pack")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.emit_sample:
        from scripts.corporate_records_scraping_primitive_pack import build_cards  # noqa: PLC0415
        print(json.dumps(to_opf(build_cards()[0]), indent=2, sort_keys=True))
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
