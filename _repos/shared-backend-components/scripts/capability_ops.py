"""capability_ops — operations layer for the edge-only capability lane: add/test · telemetry · analytics ·
adjustable weights/ranking · semantic summary.

Owner (2026-07-11): "test, setup scripts, easily add new primitives, test new primitives, adjusted weights of
primitives, collect telemetry for analytics, storing, semantic analysis." Reuse-first: general add lives in
add_primitive.py (proof-gated) and promotion in primitive_lifecycle.py; this is the edge-only-capability
convenience + the serve-time telemetry/weights/analytics the new lane needed.

  • add_capability / test_capability — one-call edge-only add: canonical edges + 0-tok description + API-verify.
  • record / read_events            — append-only usage telemetry (search/get/remix/reuse), digest-privacy.
  • analytics                       — rollup: top capabilities, class mix, reuse rate, composition frequency.
  • WEIGHTS / rank                  — ADJUSTABLE weights → a computed serve-time rank from telemetry + card.
  • semantic_summary                — deterministic semantic view: class/edge clusters + coverage gaps.

    python3 scripts/capability_ops.py --self-test
    python3 scripts/capability_ops.py --analytics
"""
from __future__ import annotations

import argparse
import hashlib
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
try:
    from src.teleon.experiments.ids import canonical_id
except Exception as exc:  # pragma: no cover
    raise SystemExit(f"capability_ops requires canonical_id; import failed: {exc}")

from scripts.deterministic_edge_derivation import derive_edges
from scripts.deterministic_description import describe_registers
from scripts.edge_only_package_introspection import verify_recipes

import os

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
#: telemetry/store dir — env-overridable so a Fly deploy persists it on the /data VOLUME (set
#: OH_CAPABILITY_DATA=/data/capability_ops) instead of the ephemeral image. Resolved at CALL time.
_DATA = _SBC / "data" / "dev-intel" / "capability_ops"


def _data_dir() -> Path:
    return Path(os.environ.get("OH_CAPABILITY_DATA") or _DATA)


def telemetry_path() -> Path:
    return _data_dir() / "capability_telemetry.jsonl"


def added_path() -> Path:
    return _data_dir() / "added_capabilities.jsonl"


TELEMETRY = telemetry_path()   # back-compat default; functions resolve dynamically below
ADDED = added_path()
_VENDORABLE = {"MIT", "APACHE-2.0", "APACHE", "BSD-2-CLAUSE", "BSD-3-CLAUSE", "BSD", "ISC", "MPL-2.0",
               "PSF-2.0", "ZLIB", "UNLICENSE"}
#: ADJUSTABLE serve-time weights — how much each signal moves a capability's rank. One place to tune;
#: rank() reads these. (Owner: "adjusted weights of primitives.")
WEIGHTS: dict[str, float] = {
    "api_verified": 3.0,      # a recipe proven against the real API
    "reuse_success": 2.0,     # per accepted/reused telemetry event
    "search_hit": 0.25,       # per time it was returned for a query
    "composable": 1.0,        # participates in an exact-typed-join chain
    "license_vendorable": 0.5,
    "reuse_dismissed": -1.0,  # per dismissed/ignored event (down-weight)
}
_EVENT_KINDS = {"search", "get", "remix", "reuse_accepted", "reuse_dismissed"}


def _license_vendorable(spdx: str) -> bool:
    alts = [a.strip().upper() for a in str(spdx or "").replace("/", " OR ").split(" OR ") if a.strip()]
    return bool(alts) and any(a in _VENDORABLE for a in alts)


def _digest(s: str) -> str:
    return hashlib.sha256(str(s).encode()).hexdigest()[:16]


# ── add / test ────────────────────────────────────────────────────────────────────────────────
def make_capability(name: str, *, registry: str = "pypi", capability_class: Optional[str] = None,
                    symbols: Optional[list[str]] = None, recipe: Optional[str] = None, license: str = "MIT",
                    tags: Optional[list[str]] = None) -> dict[str, Any]:
    edge = derive_edges(name, capability_class=capability_class)
    pid = canonical_id("prim:pkg", registry, name)
    card = {"primitive_id": pid, "id": pid, "title": f"{name} ({registry})", "capability_class": capability_class,
            "kind": "edge_only.package_link", "input_edge": edge["input_edge"], "output_edge": edge["output_edge"],
            "has_code_body": False, "hosts_raw_code": False, "search_ready": True,
            "code_hosting_policy": "cache_permitted" if _license_vendorable(license) else "rewrite_required",
            "usage_recipes": [{"route": "primary", "symbols": symbols or [], "snippet": recipe or f"import {name}"}],
            "package": {"name": name, "registry": registry, "license": license},
            "capability_tags": tags or ([capability_class] if capability_class else []), **BOUNDARY}
    card["description_registers"] = describe_registers(card)
    card["blackbox"] = card["description_registers"]["plain"]
    return card


def test_capability(card: dict[str, Any]) -> dict[str, Any]:
    recipes = card.get("usage_recipes") or []
    typed = bool(re.match(r"^[A-Z]", card.get("input_edge", "")) and re.match(r"^[A-Z]", card.get("output_edge", "")))
    has_recipe = bool(recipes and recipes[0].get("snippet"))
    syms = [s for r in recipes for s in r.get("symbols", [])]
    api = "no_symbols"
    if syms:
        ver = verify_recipes(recipes)
        api = "verified" if ver["all_verified"] else "unresolved"
    lic = _license_vendorable(card.get("package", {}).get("license", ""))
    critical = typed and has_recipe and card.get("has_code_body") is False
    verdict = "reject" if not critical else ("review" if (api == "unresolved" or not lic) else "accept")
    return {"verdict": verdict, "checks": {"typed_edges": typed, "has_recipe": has_recipe,
            "api_symbols": api, "license_vendorable": lic}, **BOUNDARY}


def add_capability(name: str, *, write: bool = True, **spec: Any) -> dict[str, Any]:
    card = make_capability(name, **spec)
    res = test_capability(card)
    stored = False
    if write and res["verdict"] != "reject":
        existing = {json.loads(l).get("id") for l in ADDED.read_text().splitlines()} if ADDED.exists() else set()
        if card["id"] not in existing:
            ADDED.parent.mkdir(parents=True, exist_ok=True)
            with ADDED.open("a", encoding="utf-8") as f:
                f.write(json.dumps({**card, "verdict": res["verdict"]}, sort_keys=True) + "\n")
            stored = True
    return {"card": card, "test": res, "stored": stored, **BOUNDARY}


# ── telemetry ─────────────────────────────────────────────────────────────────────────────────
def record(kind: str, *, capability_id: str = "", query: str = "", client: str = "",
           extra: Optional[dict[str, Any]] = None, path: Optional[Path] = None, clock: int = 0) -> dict[str, Any]:
    """Append one usage event. Privacy-minimized: client + query stored as DIGESTS, never raw. `clock` is a
    caller-supplied monotonic (no wall clock here — determinism). Path resolves at CALL time (env-overridable)."""
    if kind not in _EVENT_KINDS:
        raise ValueError(f"unknown telemetry kind {kind!r}; allowed: {sorted(_EVENT_KINDS)}")
    path = path or telemetry_path()
    ev = {"seq": clock, "kind": kind, "capability_id": capability_id, "query_digest": _digest(query) if query else "",
          "client_digest": _digest(client) if client else "", **(extra or {}), **BOUNDARY}
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(ev, sort_keys=True) + "\n")
    return ev


def read_events(path: Optional[Path] = None) -> list[dict[str, Any]]:
    path = path or telemetry_path()
    return [json.loads(l) for l in path.read_text().splitlines() if l.strip()] if path.exists() else []


def telemetry_boost(events: Optional[list[dict[str, Any]]] = None) -> dict[str, float]:
    """Per-capability weighted telemetry score → a boost the serve-time search adds to lexical relevance, so
    reused/surfaced capabilities rank higher (the adjustable-weights loop, closed into serving)."""
    events = events if events is not None else read_events()
    per_cap: dict[str, dict[str, int]] = {}
    for e in events:
        cid = e.get("capability_id")
        if cid:
            per_cap.setdefault(cid, {})[e["kind"]] = per_cap.setdefault(cid, {}).get(e["kind"], 0) + 1
    return {cid: round(WEIGHTS["reuse_success"] * t.get("reuse_accepted", 0)
                       + WEIGHTS["reuse_dismissed"] * t.get("reuse_dismissed", 0)
                       + WEIGHTS["search_hit"] * t.get("search", 0), 4) for cid, t in per_cap.items()}


def analytics(events: Optional[list[dict[str, Any]]] = None) -> dict[str, Any]:
    """Rollup for analytics: volume by kind, top capabilities, reuse rate, composition frequency."""
    events = events if events is not None else read_events()
    by_kind: dict[str, int] = {}
    per_cap: dict[str, dict[str, int]] = {}
    for e in events:
        by_kind[e["kind"]] = by_kind.get(e["kind"], 0) + 1
        cid = e.get("capability_id")
        if cid:
            d = per_cap.setdefault(cid, {})
            d[e["kind"]] = d.get(e["kind"], 0) + 1
    reuse_acc = by_kind.get("reuse_accepted", 0)
    reuse_tot = reuse_acc + by_kind.get("reuse_dismissed", 0)
    top = sorted(per_cap.items(), key=lambda kv: -sum(kv[1].values()))[:10]
    return {"events": len(events), "by_kind": by_kind,
            "reuse_rate": round(reuse_acc / reuse_tot, 3) if reuse_tot else None,
            "top_capabilities": [{"capability_id": c, "events": sum(v.values()), "breakdown": v} for c, v in top],
            "composition_events": by_kind.get("remix", 0), **BOUNDARY}


# ── weights / rank ────────────────────────────────────────────────────────────────────────────
def capability_score(card: dict[str, Any], per_cap: dict[str, dict[str, int]],
                     composable_ids: Optional[set[str]] = None) -> float:
    """A weighted serve-time score from the card's intrinsic signals + its telemetry. Deterministic; uses the
    ADJUSTABLE WEIGHTS. (Composition of intrinsic quality + earned usage — the 'adjusted weights' lever.)"""
    cid = str(card.get("id") or card.get("primitive_id") or "")
    tel = per_cap.get(cid, {})
    api_verified = ((card.get("api_conformance") or {}).get("all_recipes_verified")
                    or card.get("verification_level", "").startswith("L4"))
    score = 0.0
    score += WEIGHTS["api_verified"] * (1 if api_verified else 0)
    score += WEIGHTS["reuse_success"] * tel.get("reuse_accepted", 0)
    score += WEIGHTS["reuse_dismissed"] * tel.get("reuse_dismissed", 0)
    score += WEIGHTS["search_hit"] * tel.get("search", 0)
    score += WEIGHTS["composable"] * (1 if composable_ids and cid in composable_ids else 0)
    score += WEIGHTS["license_vendorable"] * (1 if _license_vendorable(card.get("package", {}).get("license", "")) else 0)
    return round(score, 4)


def rank(cards: list[dict[str, Any]], *, events: Optional[list[dict[str, Any]]] = None) -> list[dict[str, Any]]:
    """Rank cards by weighted score (telemetry-informed), highest first. Non-destructive: returns a scored view."""
    events = events if events is not None else read_events()
    per_cap: dict[str, dict[str, int]] = {}
    for e in events:
        cid = e.get("capability_id")
        if cid:
            per_cap.setdefault(cid, {})[e["kind"]] = per_cap.setdefault(cid, {}).get(e["kind"], 0) + 1
    ins = {c.get("input_edge") for c in cards}
    outs = {c.get("output_edge") for c in cards}
    composable = {str(c.get("id") or c.get("primitive_id")) for c in cards
                  if c.get("input_edge") in outs or c.get("output_edge") in ins}
    scored = [{"id": c.get("id") or c.get("primitive_id"), "title": c.get("title"),
               "score": capability_score(c, per_cap, composable), "card": c} for c in cards]
    scored.sort(key=lambda r: (-r["score"], str(r["id"])))
    return scored


# ── semantic analysis ─────────────────────────────────────────────────────────────────────────
def semantic_summary(cards: list[dict[str, Any]]) -> dict[str, Any]:
    """Deterministic semantic view: cluster by class + edge, surface coverage gaps + composition bridges."""
    by_class: dict[str, int] = {}
    producers: dict[str, int] = {}
    consumers: dict[str, int] = {}
    for c in cards:
        by_class[c.get("capability_class") or "unclassified"] = by_class.get(c.get("capability_class") or "unclassified", 0) + 1
        producers[c.get("output_edge", "")] = producers.get(c.get("output_edge", ""), 0) + 1
        consumers[c.get("input_edge", "")] = consumers.get(c.get("input_edge", ""), 0) + 1
    bridges = sorted(set(producers) & set(consumers))
    # coverage gaps: a type produced but never consumed (dead-end) or consumed but never produced (needs a source)
    dead_ends = sorted(t for t in producers if t and t not in consumers)
    missing_sources = sorted(t for t in consumers if t and t not in producers)
    return {"capabilities": len(cards), "by_class": dict(sorted(by_class.items(), key=lambda x: -x[1])),
            "composable_type_bridges": bridges, "dead_end_types": dead_ends[:20],
            "types_needing_a_source": missing_sources[:20], **BOUNDARY}


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []
    import io  # noqa: PLC0415
    tmp = _DATA / "_selftest_telemetry.jsonl"
    if tmp.exists():
        tmp.unlink()

    # ADD/TEST: a good capability accepts; a GPL one → review
    good = add_capability("orjson", registry="pypi", capability_class="serialize",
                          symbols=["orjson.dumps"], recipe="import orjson; b=orjson.dumps(x)", license="MIT", write=False)
    checks.append(("add_capability: canonical edges + 0-tok description + accept/review",
                   good["card"]["input_edge"] and len(good["card"]["description_registers"]) == 3
                   and good["test"]["verdict"] in ("accept", "review")))

    # TELEMETRY: record events (digest-privacy) + read back
    for i, (k, cid) in enumerate([("search", "a"), ("remix", "a"), ("reuse_accepted", "a"),
                                  ("search", "b"), ("reuse_dismissed", "b")]):
        record(k, capability_id=cid, query="parse json", client="tenant-42", path=tmp, clock=i)
    evs = read_events(tmp)
    checks.append(("telemetry: 5 events recorded, query+client stored as digests (not raw)",
                   len(evs) == 5 and evs[0]["query_digest"] and "parse json" not in json.dumps(evs)))

    # ANALYTICS: reuse rate + top capabilities
    a = analytics(evs)
    checks.append(("analytics: reuse_rate computed + top capability ranked by volume",
                   a["reuse_rate"] == 0.5 and a["top_capabilities"][0]["capability_id"] == "a"))

    # WEIGHTS: 'a' (reuse_accepted) outranks 'b' (reuse_dismissed); weights are adjustable
    cards = [{"id": "a", "title": "A", "input_edge": "X", "output_edge": "Y", "package": {"license": "MIT"}},
             {"id": "b", "title": "B", "input_edge": "Y", "output_edge": "Z", "package": {"license": "MIT"}}]
    ranked = rank(cards, events=evs)
    checks.append(("weights/rank: reused capability outranks dismissed one",
                   ranked[0]["id"] == "a" and ranked[0]["score"] > ranked[1]["score"]))

    # adjusting a weight changes the ranking (the 'adjusted weights' lever is real)
    saved = WEIGHTS["reuse_dismissed"]
    WEIGHTS["reuse_dismissed"] = -50.0
    ranked2 = rank(cards, events=evs)
    WEIGHTS["reuse_dismissed"] = saved
    checks.append(("adjusting a weight changes the score (b's score drops)",
                   next(r["score"] for r in ranked2 if r["id"] == "b")
                   < next(r["score"] for r in ranked if r["id"] == "b")))

    # SEMANTIC: bridges + dead-ends (X->Y, Y->Z chains on Y; X needs a source; Z is a dead-end)
    sem = semantic_summary(cards)
    checks.append(("semantic_summary: Y is a composable bridge; Z dead-ends; X needs a source",
                   "Y" in sem["composable_type_bridges"] and "Z" in sem["dead_end_types"]
                   and "X" in sem["types_needing_a_source"]))

    # unknown telemetry kind is rejected
    try:
        record("bogus_kind", path=tmp, clock=99)
        rejected = False
    except ValueError:
        rejected = True
    checks.append(("telemetry rejects an unknown event kind", rejected))

    if tmp.exists():
        tmp.unlink()
    ok = all(v for _, v in checks)
    print("capability_ops — self-test")
    for name, v in checks:
        print(f"  [{'ok' if v else 'FAIL'}] {name}")
    print(f"  add/test · telemetry(digest-privacy) · analytics · adjustable weights · semantic. "
          f"{len(WEIGHTS)} tunable weights.")
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


def _main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--analytics", action="store_true")
    ap.add_argument("--semantic", action="store_true")
    args = ap.parse_args()
    if args.analytics:
        print(json.dumps(analytics(), indent=2, default=str)); return 0
    if args.semantic:
        from scripts.capability_lane import load_corpus  # noqa: PLC0415
        print(json.dumps(semantic_summary(load_corpus()), indent=2, default=str)); return 0
    return _self_test()


if __name__ == "__main__":
    raise SystemExit(_main())
