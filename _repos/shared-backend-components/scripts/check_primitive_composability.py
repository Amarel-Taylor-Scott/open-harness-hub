#!/usr/bin/env python3
"""scripts.check_primitive_composability — an ADD-ONLY composability gate for primitive cards (red-team gap F1).

The composition red-team (2026-07-03) found the load-bearing lie in the "retrieve capabilities, not code" thesis:
retrieved primitives are individually plausible but do NOT chain. Cards declare free-text `input_edge`/`output_edge`
snowflakes ("PolicyCompliantSecuritySchemeMap" -> "AuthValidationReport", "api_request" -> "paginated_request"),
so a primitive's output almost never equals another primitive's input — the route graph has ~no edges. A gate that
only checks a card's *shape* (verify_primitive_candidates.py) passes all of these; a *composability* gate does not.

This module is that gate, built ADDITIVELY: it does NOT edit verify_primitive_candidates.py or any contract-locked
retrieval file. It is a NEW parallel path that IMPORTS the existing machinery — `canonicalize_edge` from the sibling
foundation module `_repos/shared-backend-components/scripts/build_edge_type_retrofit.py` (falling back to a local minimal canonicalizer so this file's
--self-test passes standalone before that sibling lands), and the canonical type vocabulary from
`_repos/shared-backend-components/scripts/build_canonical_edge_type_vocabulary.py`. Because it is a separate wired path it is benchmarkable against
the old shape-only gate: run `scan_corpus` to measure what fraction of a real corpus would survive composability
today (spoiler from the red-team: LOW — that is the finding, not a bug in this checker).

Gate design (two independent reasons a card fails to compose):
  1. edge_untyped — canonicalize_edge could not turn the raw input_edge OR output_edge into a real type id
     (missing / blank / template-placeholder like "dg_pag_{idx}"). An untyped edge can never match anything.
  2. not route_reachable — even when typed, the card's input type is PRODUCED by no OTHER primitive AND its output
     type is CONSUMED by no OTHER primitive (a directional check over a type index). A typed island still doesn't
     chain. This check runs only when a `known_type_index` is supplied.

Boundary law kept: every emitted row is candidate=true / serves_truth=false (a composability verdict is a candidate
signal, never a truth claim). Offline + deterministic (no network, no wall-clock/RNG in row bodies). CLI:
  --self-test           pure, offline, standalone
  --scan [--path P] [--sample N]   measure the gate over a real corpus sample
  --write [--sample N] [--date D]  emit a candidate scan pack + manifest
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import datetime as dt
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Callable, Optional

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
# Raw-label markers that mean "template/placeholder, not a real edge type" (e.g. "dg_pag_{idx}", "<T>").
_PLACEHOLDER_MARKERS: tuple[str, ...] = ("{", "}", "<", ">", "$", "%")
# Catch-all type ids a canonicalizer emits for un-typeable input — these are NOT real types, so they read
# as edge_untyped. The retrofit canonicalizer maps blanks/whitespace to 'Unknown'.
_UNTYPED_SENTINELS: frozenset[str] = frozenset({"unknown", "none", "null", "any", "n/a", "todo"})
PACK_DIR = _resource("catalog") / "knowledge-packs" / "data" / "primitive-composability-gate"
DEFAULT_CORPUS = _resource("data") / "dev-intel" / "aidevobserver_edge_foundry" / "verified_factory_primitive_cards.jsonl"

# ── reuse existing machinery (import-with-fallback so --self-test is standalone) ──
_EXTERNAL_CANON: Optional[Callable[[str], Any]] = None
try:  # the sibling foundation module being built in parallel (gap F-edge-retrofit)
    from scripts.build_edge_type_retrofit import canonicalize_edge as _EXTERNAL_CANON  # type: ignore
except Exception:  # noqa: BLE001 — not importable yet: use the local minimal canonicalizer below
    _EXTERNAL_CANON = None

_CANON_TYPES: set[str] = set()
try:  # the canonical intermediate-type vocabulary — used to snap near-matches onto the shared spelling
    from scripts.build_canonical_edge_type_vocabulary import _all_types as _canon_all_types  # type: ignore

    _CANON_TYPES = set(_canon_all_types().keys())
except Exception:  # noqa: BLE001
    _CANON_TYPES = set()

_CANON_TYPES_LOWER: dict[str, str] = {t.lower(): t for t in _CANON_TYPES}

# labels that are placeholders, not real types — an edge carrying one is untyped by construction.
_PLACEHOLDER_TOKENS = {"", "none", "null", "any", "unknown", "todo", "tbd", "input", "output", "data", "value", "x"}


def _fallback_canonicalize_edge(edge_label: Any) -> Optional[str]:
    """Minimal, deterministic edge -> canonical type id. Returns None when no real type can be produced.

    Rules: strip; a compound edge ("A+B") canonicalizes on its PRIMARY (first) component; template markers ("{..}")
    are untyped; tokens split on non-alphanumerics and PascalCase-join (a single already-camel/Pascal token is kept);
    a purely-generic placeholder token is untyped; a near-match to the canonical vocabulary snaps onto its spelling.
    """
    if not isinstance(edge_label, str):
        return None
    label = edge_label.strip()
    if not label:
        return None
    if "+" in label:  # compound edge — primary component carries the type
        label = label.split("+")[0].strip()
    if "{" in label or "}" in label:  # template placeholder, e.g. "dg_pag_{idx}"
        return None
    parts = [p for p in re.split(r"[^0-9A-Za-z]+", label) if p]
    if not parts:
        return None
    if len(parts) == 1:
        tok = parts[0]
        canon = tok if re.search(r"[A-Z]", tok[1:]) else (tok[:1].upper() + tok[1:])
    else:
        canon = "".join(p[:1].upper() + p[1:] for p in parts)
    if canon.lower() in _PLACEHOLDER_TOKENS:
        return None
    return _CANON_TYPES_LOWER.get(canon.lower(), canon)


def canonicalize_edge(edge_label: Any) -> Optional[str]:
    """Wrapper over the external canonicalizer (when present) with a robust local fallback.

    Normalizes any falsy/empty result to None so `edge_untyped` is a clean boolean regardless of which
    canonicalizer answered.
    """
    # Screen structurally un-typeable raw labels FIRST: a blank/whitespace label, or a template placeholder
    # like "dg_pag_{idx}"/"<T>", is UNTYPED no matter what a canonicalizer coerces it into. (The external
    # retrofit canonicalizer maps blanks to the 'Unknown' catch-all and coerces "{idx}" into a bogus
    # CamelCase type — both would otherwise read as "typed" and silently disarm the gate.)
    if not (isinstance(edge_label, str) and edge_label.strip()):
        return None
    if any(mark in edge_label for mark in _PLACEHOLDER_MARKERS):
        return None
    result: Any = None
    if _EXTERNAL_CANON is not None:
        try:
            result = _EXTERNAL_CANON(edge_label)  # type: ignore[misc]
        except Exception:  # noqa: BLE001 — signature/behaviour drift: fall back per-call
            result = None
    if not (isinstance(result, str) and result.strip()):
        result = _fallback_canonicalize_edge(edge_label)
    if isinstance(result, str) and result.strip():
        canon = result.strip()
        # a catch-all sentinel ('Unknown', …) is not a real type → treat as untyped.
        if canon.lower() in _UNTYPED_SENTINELS:
            return None
        return canon
    return None


# ── directional type index: build once over a corpus, then check reachability per card ──
def build_type_index(cards: list[dict[str, Any]]) -> set[str]:
    """A directional set of type facts over a corpus: for each card, `produces:<T>` for its output type and
    `consumes:<T>` for its input type. Directionality means a card's OWN entries never satisfy its OWN reachability
    check (a card consumes its input / produces its output; reachability asks the opposite), so the whole corpus can
    be indexed without per-card exclusion.
    """
    idx: set[str] = set()
    for card in cards:
        in_t = canonicalize_edge(card.get("input_edge"))
        out_t = canonicalize_edge(card.get("output_edge"))
        if in_t:
            idx.add(f"consumes:{in_t}")
        if out_t:
            idx.add(f"produces:{out_t}")
    return idx


def composability_report(card: dict[str, Any], known_type_index: Optional[set[str]] = None) -> dict[str, Any]:
    """Verdict on whether one primitive card can participate in a route.

    Keys: input_type_id, output_type_id (canonical type ids or None), edge_untyped, route_reachable, gate_pass.
    The gate FAILS a card that is edge_untyped OR (when an index is provided) not route_reachable.
    """
    in_t = canonicalize_edge(card.get("input_edge"))
    out_t = canonicalize_edge(card.get("output_edge"))
    edge_untyped = in_t is None or out_t is None

    index_provided = known_type_index is not None
    if index_provided:
        producer_of_my_input = bool(in_t) and f"produces:{in_t}" in known_type_index  # someone feeds my input
        consumer_of_my_output = bool(out_t) and f"consumes:{out_t}" in known_type_index  # someone eats my output
        route_reachable = bool(producer_of_my_input or consumer_of_my_output)
    else:
        # no index to reason about routes — cannot penalize reachability, only typedness.
        route_reachable = True

    gate_pass = (not edge_untyped) and (route_reachable if index_provided else True)
    return {
        "record_type": "primitive_composability_verdict",
        "primitive_id": card.get("primitive_id"),
        "input_edge_raw": card.get("input_edge"),
        "output_edge_raw": card.get("output_edge"),
        "input_type_id": in_t,
        "output_type_id": out_t,
        "edge_untyped": edge_untyped,
        "route_reachable": route_reachable,
        "reachability_checked": index_provided,
        "gate_pass": gate_pass,
        **BOUNDARY,
    }


def _read_cards(path: Path, sample: Optional[int]) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as fh:
        for i, line in enumerate(fh):
            if sample is not None and i >= sample:
                break
            line = line.strip()
            if not line:
                continue
            try:
                cards.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return cards


def scan_corpus(path: Any, sample: Optional[int] = 500) -> dict[str, Any]:
    """Measure the composability gate over a real corpus sample. Reads a local file only (offline, deterministic);
    returns a summary with the pass fraction and the two failure-reason breakdowns. Missing file -> a graceful
    'sample unavailable' summary so callers/self-tests never crash.
    """
    p = Path(path)
    if not p.exists():
        return {"record_type": "primitive_composability_scan", "path": str(p), "available": False,
                "sampled": 0, "gate_pass_count": 0, "pass_fraction": None,
                "note": "corpus sample unavailable in this environment", **BOUNDARY}
    cards = _read_cards(p, sample)
    idx = build_type_index(cards)
    verdicts = [composability_report(c, idx) for c in cards]
    n = len(verdicts)
    gate_pass_count = sum(1 for v in verdicts if v["gate_pass"])
    edge_untyped_count = sum(1 for v in verdicts if v["edge_untyped"])
    unreachable_count = sum(1 for v in verdicts if not v["route_reachable"])
    typed_but_unreachable = sum(1 for v in verdicts if not v["edge_untyped"] and not v["route_reachable"])
    return {
        "record_type": "primitive_composability_scan",
        "path": str(p), "available": True,
        "sampled": n,
        "distinct_types_indexed": len(idx),
        "gate_pass_count": gate_pass_count,
        "pass_fraction": round(gate_pass_count / n, 4) if n else None,
        "edge_untyped_count": edge_untyped_count,
        "unreachable_count": unreachable_count,
        "typed_but_unreachable_count": typed_but_unreachable,
        "note": "LOW pass fraction is the red-team finding: cards declare snowflake edges that do not chain.",
        **BOUNDARY,
    }


# ── --write: emit a candidate scan pack (bounded per-card verdicts + summary + manifest) ──
def write_pack(*, path: Path, sample: int, date: str) -> dict[str, Any]:
    PACK_DIR.mkdir(parents=True, exist_ok=True)
    summary = scan_corpus(path, sample)
    verdict_rows: list[dict[str, Any]] = []
    if summary.get("available"):
        cards = _read_cards(path, sample)
        idx = build_type_index(cards)
        verdict_rows = [composability_report(c, idx) for c in cards]
    (PACK_DIR / "verdicts.jsonl").write_text(
        "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in verdict_rows), encoding="utf-8")
    (PACK_DIR / "scan_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    row_counts = {"verdicts.jsonl": len(verdict_rows), "scan_summary.json": 1}
    canonical = "\n".join(json.dumps(r, sort_keys=True, ensure_ascii=False) for r in verdict_rows) + \
        "\n" + json.dumps(summary, sort_keys=True, ensure_ascii=False)
    manifest = {
        "record_type": "primitive_composability_gate_manifest",
        "pack_id": "primitive-composability-gate",
        "generator": "scripts/check_primitive_composability.py",
        "generated_utc": date,
        "external_canonicalizer": _EXTERNAL_CANON is not None,
        "canonical_vocabulary_types": len(_CANON_TYPES),
        "row_counts": row_counts, "total_rows": sum(row_counts.values()),
        "pass_fraction": summary.get("pass_fraction"),
        "content_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        **BOUNDARY,
    }
    (PACK_DIR / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def self_test() -> int:
    checks: list[tuple[str, bool]] = []

    # canonicalizer behaviour
    checks.append(("blank/missing edge is untyped", canonicalize_edge("") is None and canonicalize_edge(None) is None))
    checks.append(("template placeholder is untyped", canonicalize_edge("dg_pag_{idx}") is None))
    checks.append(("snake_case edge canonicalizes", canonicalize_edge("api_request") == "ApiRequest"))
    checks.append(("PascalCase edge is preserved", canonicalize_edge("PolicyCompliantSecuritySchemeMap") == "PolicyCompliantSecuritySchemeMap"))
    checks.append(("compound edge uses primary component", canonicalize_edge("SamplingDecisionWindowStats+IngestBudgetPolicy") == "SamplingDecisionWindowStats"))

    # A directional index: an UPSTREAM card produces EdgeList; a DOWNSTREAM card consumes AdjacencyGraph.
    upstream = {"primitive_id": "up", "input_edge": "RawGraphInput", "output_edge": "EdgeList"}
    downstream = {"primitive_id": "down", "input_edge": "AdjacencyGraph", "output_edge": "AnswerArtifact"}
    idx = build_type_index([upstream, downstream])

    # 1) typed + reachable: consumes EdgeList (produced upstream) and outputs AdjacencyGraph (consumed downstream)
    typed_reachable = {"primitive_id": "mid", "input_edge": "EdgeList", "output_edge": "AdjacencyGraph"}
    r_ok = composability_report(typed_reachable, idx)
    checks.append(("typed+reachable card PASSES the gate",
                   r_ok["gate_pass"] is True and r_ok["edge_untyped"] is False and r_ok["route_reachable"] is True
                   and r_ok["input_type_id"] == "EdgeList" and r_ok["output_type_id"] == "AdjacencyGraph"))

    # 2) edge_untyped: missing input_edge -> untyped -> fails even with an index
    untyped_card = {"primitive_id": "u", "input_edge": "", "output_edge": "AdjacencyGraph"}
    r_untyped = composability_report(untyped_card, idx)
    checks.append(("edge_untyped card FAILS the gate",
                   r_untyped["gate_pass"] is False and r_untyped["edge_untyped"] is True and r_untyped["input_type_id"] is None))

    # 3) typed but unreachable: real types nobody else produces/consumes -> fails
    island = {"primitive_id": "iso", "input_edge": "FooBarUniqueEdgeAlpha", "output_edge": "BazQuxUniqueEdgeBeta"}
    r_island = composability_report(island, idx)
    checks.append(("typed-but-unreachable card FAILS the gate",
                   r_island["gate_pass"] is False and r_island["edge_untyped"] is False and r_island["route_reachable"] is False))

    # 4) directional index does not let a card satisfy its OWN reachability
    solo_idx = build_type_index([typed_reachable])
    r_solo = composability_report(typed_reachable, solo_idx)
    checks.append(("a card cannot self-satisfy reachability (directional index)", r_solo["route_reachable"] is False))

    # 5) no index -> reachability not penalized, only typedness gates
    r_noidx = composability_report(island, None)
    checks.append(("no index: typed card passes on typedness alone", r_noidx["gate_pass"] is True and r_noidx["reachability_checked"] is False))
    r_noidx_untyped = composability_report(untyped_card, None)
    checks.append(("no index: untyped card still fails", r_noidx_untyped["gate_pass"] is False))

    # 6) boundary law on emitted verdicts
    checks.append(("verdicts carry candidate/serves_truth=false", r_ok["candidate"] is True and r_ok["serves_truth"] is False))

    # 7) real-corpus scan is offline + graceful, and (when present) LOW — measured, not fabricated
    scan = scan_corpus(DEFAULT_CORPUS, 500)
    scan_ok = scan["available"] is False or (
        scan["sampled"] > 0 and scan["pass_fraction"] is not None and 0.0 <= scan["pass_fraction"] <= 1.0)
    checks.append(("scan_corpus runs offline and returns a valid (or gracefully-absent) fraction", scan_ok))

    failed = [n for n, ok in checks if not ok]
    if failed:
        print("FAIL - check_primitive_composability:\n  " + "\n  ".join(failed))
        return 1
    frac = scan.get("pass_fraction")
    frac_txt = (f"{frac:.1%} of {scan['sampled']} sampled cards" if scan.get("available") else "sample unavailable")
    canon_src = "external build_edge_type_retrofit.canonicalize_edge" if _EXTERNAL_CANON else "local fallback canonicalizer"
    print("PASS - check_primitive_composability: additive composability gate (edge_untyped OR not route_reachable "
          f"-> fail); reuses {canon_src} + {len(_CANON_TYPES)} canonical vocabulary types; measured gate pass on the "
          f"real corpus = {frac_txt} (LOW is the point — snowflake edges do not chain).")
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--scan", action="store_true", help="measure the gate over a real corpus sample")
    parser.add_argument("--write", action="store_true", help="emit a candidate scan pack + manifest")
    parser.add_argument("--path", default=str(DEFAULT_CORPUS))
    parser.add_argument("--sample", type=int, default=500)
    parser.add_argument("--date", default=None)
    args = parser.parse_args(argv)

    if args.write:
        date = args.date or dt.datetime.now(dt.timezone.utc).date().isoformat()
        manifest = write_pack(path=Path(args.path), sample=args.sample, date=date)
        print(json.dumps({k: v for k, v in manifest.items() if k != "content_sha256"}, indent=2, sort_keys=True))
        return self_test()
    if args.scan:
        print(json.dumps(scan_corpus(Path(args.path), args.sample), indent=2, sort_keys=True))
        return 0
    return self_test()


if __name__ == "__main__":
    raise SystemExit(main())
