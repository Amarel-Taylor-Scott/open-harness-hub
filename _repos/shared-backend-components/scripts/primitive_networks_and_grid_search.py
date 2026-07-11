#!/usr/bin/env python3
"""primitive_networks_and_grid_search — networks of primitives: a step lattice, grid-searched for efficiency.

Owner (2026-07-10): "networks or primitives that are essentially a grid of potential primitives — a task that
required 3 steps would have step A, step B, and step C, but it can have multiple primitives for each step, and
test out a grid search of which ones are most efficient."

A PRIMITIVE NETWORK declares a task as an ordered chain of EDGE TYPES; each step becomes a SLOT whose member
pool is COMPUTED from the corpus (cards producing that step's edge and consuming the previous step's edge —
slots are never hand-listed, so a new card joins its slot automatically). The GRID is the cartesian product of
the slots; every path is valid BY CONSTRUCTION (adjacent members share exact canonical edges — recomputed and
asserted anyway). Grid search evaluates every combination (or a deterministic strided sample past the cap —
no RNG, no wall-clock) under a SCORER ZOO:

  - deterministic proxies, runnable today: proxy_context_tokens (the context an agent reads to use the path —
    a labeled UPPER-BOUND proxy, compose_token_bench convention), blackbox_tokens, declared_cost;
  - an `execution_seam` row marks where measured runtime/oracle efficiency plugs in (harness-bakeoff lane) —
    declared, kind-labeled, never silently run in the 0-token lane.

Rankings are NON-DESTRUCTIVE (owner law): every evaluated path is receipted with its scores; per-scorer
winners and the Pareto front are ranked CANDIDATES, never truth (`candidate=true, serves_truth=false`), and
losers are preserved as labeled fallbacks. Worked example: officer/entity networks over the corporate-records
pack + its edge-aligned remixes (the composition layer feeds this module).

    PYTHONPATH=. python3 scripts/primitive_networks_and_grid_search.py --self-test
    PYTHONPATH=. python3 scripts/primitive_networks_and_grid_search.py --build
    PYTHONPATH=. python3 scripts/primitive_networks_and_grid_search.py --demo
"""
from __future__ import annotations

import argparse
import itertools
import json
import math
import sys
from pathlib import Path
from typing import Any, Callable, Iterator, Optional

_HERE = Path(__file__).resolve()
_SBC = _HERE.parent.parent
_ROOT = _SBC.parent.parent
for _p in (str(_SBC), str(_SBC / "scripts"), str(_ROOT), str(_ROOT / "_repos" / "teleon" / "backend")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    from src.teleon.experiments.ids import canonical_id  # noqa: E402  the ONE id authority (data plane law)
except Exception as exc:  # noqa: BLE001
    raise SystemExit(f"primitive_networks_and_grid_search requires canonical_id; import failed: {exc}")

OUT_DIR = _SBC / "data" / "dev-intel" / "primitive_factory" / "composition_layer"
NETWORKS_PATH = OUT_DIR / "primitive_networks.jsonl"
PATHS_PATH = OUT_DIR / "network_path_candidates.jsonl"
RECEIPTS_PATH = OUT_DIR / "network_grid_receipts.jsonl"
MANIFEST_PATH = OUT_DIR / "network_grid_manifest.json"
NETWORK_ID_PREFIX = "pnet"
PATH_ID_PREFIX = "pnpath"
RECEIPT_ID_PREFIX = "pnrcpt"
#: grid cap — past this, a deterministic coprime-strided sample walks the lattice (grid-remixer convention).
DEFAULT_MAX_PATHS = 10_000
_COPRIME_STRIDE = 2_147_483_647  # 2**31 - 1, prime — coprime to any smaller grid size
TOP_K = 5
_CANDIDATE_BITS = {"candidate": True, "serves_truth": False}
_PLACEHOLDER_MARKERS = ("todo", "tbd", "lorem", "fixme")


def aligned_corpus() -> list[dict[str, Any]]:
    """The composition layer's worked-example corpus: pack cards + their deterministic remixes."""
    from scripts.primitive_groups_frameworks_and_remixers import build_remixes, default_cards  # noqa: PLC0415
    cards = default_cards()
    return cards + build_remixes(cards)


# ──────────────────────────────────────────────────────────────────────────────────────────────────────────
# Scorer zoo — add a scorer = add a row. Lower is better for every runnable scorer.
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def _proxy_context_tokens(members: list[dict[str, Any]]) -> int:
    return sum(len(json.dumps(c, sort_keys=True)) for c in members) // 4


def _blackbox_tokens(members: list[dict[str, Any]]) -> int:
    return sum(len(str(c.get("blackbox") or "")) for c in members) // 4


def _declared_cost(members: list[dict[str, Any]]) -> int:
    return sum(int(c.get("cost") or 1) for c in members)


def _measured_execution(members: list[dict[str, Any]]) -> int:
    """Adapter: the grid-search scorer contract is fn(members)->int. Delegates to the standalone
    execution_scorer (gap 2.5, real instruction-count measurement); returns the measured instruction total, or
    a large sentinel when nothing was measurable (so an all-abstain path never looks 'cheap')."""
    from scripts.execution_scorer import score_path_execution  # noqa: PLC0415  the real measurement module
    result = score_path_execution(members)
    return result["measured_instructions"] if result["members_measured"] else 10 ** 12


PATH_SCORERS: dict[str, dict[str, Any]] = {
    "proxy_context_tokens": {"kind": "deterministic_proxy", "fn": _proxy_context_tokens,
                             "note": "full-card context an agent reads to use the path — labeled UPPER-BOUND "
                                     "proxy (compose_token_bench convention)"},
    "blackbox_tokens": {"kind": "deterministic_proxy", "fn": _blackbox_tokens,
                        "note": "signature-level read cost (blackbox only)"},
    "declared_cost": {"kind": "deterministic_proxy", "fn": _declared_cost,
                      "note": "sum of per-card declared cost hints (default 1)"},
    # the seam is now FILLED by a real module (scripts.execution_scorer, gap 2.5): measured EXECUTED
    # INSTRUCTION COUNT (deterministic, not wall-clock) over members that carry an executable_body. It stays
    # OUT of the default runnable_scorers() (kind != deterministic_proxy) so the 0-token grid is byte-identical;
    # opt in via runnable_scorers(include_execution=True) + measure_execution paths that carry bodies.
    "execution_efficiency": {"kind": "execution_measured", "fn": _measured_execution,
                             "note": "REAL measured execution (execution_scorer: instruction count over the "
                                     "member bodies); opt-in, abstains on non-executable governance cards"},
}


def runnable_scorers(include_execution: bool = False) -> dict[str, Callable[[list[dict[str, Any]]], int]]:
    kinds = {"deterministic_proxy"} | ({"execution_measured"} if include_execution else set())
    return {name: spec["fn"] for name, spec in sorted(PATH_SCORERS.items()) if spec["kind"] in kinds}


# ──────────────────────────────────────────────────────────────────────────────────────────────────────────
# Networks — a task as an edge-type chain; slots computed from the corpus.
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def build_network(name: str, edge_chain: list[str], cards: list[dict[str, Any]],
                  description: str = "", index: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    """Slots: step i pool = cards producing edge_chain[i] (and consuming edge_chain[i-1] for i>0). Step 0's
    input edge is free — same output contract, source-dependent entry (recorded per path). `index` is an
    optional prebuilt producer_edge_index: a faster SUBSTITUTABLE path for the O(N)-scan slot computation
    (proven equivalent in producer_edge_index's self-test); omit it for the exact linear default."""
    if not edge_chain:
        raise ValueError("build_network requires a non-empty edge_chain (a network with zero steps is meaningless)")
    if index is not None:
        from scripts.producer_edge_index import slot_members as _slot_members  # noqa: PLC0415
    slots: list[dict[str, Any]] = []
    for i, produced in enumerate(edge_chain):
        consumed = None if i == 0 else edge_chain[i - 1]
        if index is not None:
            member_ids = sorted(_slot_members(index, produced, consumed))
        else:
            member_ids = sorted(c["card_id"] for c in cards if c.get("output_edge") == produced
                                and (consumed is None or c.get("input_edge") == consumed))
        slots.append({"step": chr(ord("A") + i), "produces_edge": produced,
                      "consumes_edge": edge_chain[i - 1] if i else "(source-dependent)",
                      "member_ids": member_ids})
    slot_sizes = [len(s["member_ids"]) for s in slots]
    grid_size = 1
    for size in slot_sizes:
        grid_size *= size
    # network_id is CONTENT-derived: two different corpora with the same name+edge_chain resolve slots
    # differently, so the id folds a digest of the actual slot membership (not just the declared chain).
    member_digest = canonical_id("netslots", *sorted(m for s in slots for m in s["member_ids"])).rsplit("-", 1)[-1]
    return {"network_id": canonical_id(NETWORK_ID_PREFIX, name, *edge_chain, member_digest),
            "record_type": "primitive_network", "name": name, "description": description,
            "edge_chain": edge_chain, "slots": slots, "slot_sizes": slot_sizes,
            "grid_size": grid_size, "step_count": len(edge_chain),
            "schema_version": "1", **_CANDIDATE_BITS}


def _strided_combo_indices(slot_sizes: list[int], target: int) -> Iterator[tuple[int, ...]]:
    """Deterministic coprime-strided walk over the flattened grid (no RNG, no wall-clock). The stride must be
    coprime to grid_size for the walk to visit distinct cells; _COPRIME_STRIDE is prime, but grid_size can be a
    multiple of it, so enforce coprimality explicitly (terminates in a few steps, still deterministic)."""
    grid_size = 1
    for size in slot_sizes:
        grid_size *= size
    stride = _COPRIME_STRIDE % grid_size or 1
    while grid_size > 1 and math.gcd(stride, grid_size) != 1:
        stride += 1
    flat = 0
    for _ in range(min(target, grid_size)):
        remainder, combo = flat, []
        for size in reversed(slot_sizes):
            combo.append(remainder % size)
            remainder //= size
        yield tuple(reversed(combo))
        flat = (flat + stride) % grid_size


def grid_search(network: dict[str, Any], cards: list[dict[str, Any]],
                max_paths: int = DEFAULT_MAX_PATHS) -> dict[str, Any]:
    """Evaluate the lattice (full grid, or a deterministic strided sample past the cap) under every runnable
    scorer. NON-DESTRUCTIVE: every evaluated path is kept + scored; winners are ranked candidates."""
    max_paths = max(1, int(max_paths))   # a grid always has >=1 path to look at; refuse 0/negative honestly
    by_id = {c["card_id"]: c for c in cards}
    pools = [[by_id[m] for m in slot["member_ids"]] for slot in network["slots"]]
    if any(not pool for pool in pools):
        empty = [s["step"] for s, p in zip(network["slots"], pools) if not p]
        return {"receipt_id": canonical_id(RECEIPT_ID_PREFIX, network["network_id"], "empty"),
                "record_type": "network_grid_receipt", "network_id": network["network_id"],
                "network_name": network["name"], "grid_size": network["grid_size"],
                "evaluated": 0, "sampled": False, "empty_slots": empty, "paths": [], "rankings": {},
                "pareto_front": [], "note": "unfillable slots — a coverage gap, not an error",
                "schema_version": "1", **_CANDIDATE_BITS}

    sampled = network["grid_size"] > max_paths
    combos = (_strided_combo_indices(network["slot_sizes"], max_paths) if sampled
              else itertools.product(*(range(len(pool)) for pool in pools)))
    scorers = runnable_scorers()
    paths: list[dict[str, Any]] = []
    for combo in combos:
        members = [pools[i][j] for i, j in enumerate(combo)]
        for previous, current in zip(members, members[1:]):   # valid by construction — asserted anyway
            if previous["output_edge"] != current["input_edge"]:
                raise AssertionError(f"slot construction broken: {previous['card_id']} !-> {current['card_id']}")
        member_ids = [m["card_id"] for m in members]
        paths.append({"path_id": canonical_id(PATH_ID_PREFIX, network["network_id"], *member_ids),
                      "record_type": "network_path_candidate", "network_id": network["network_id"],
                      "member_ids": member_ids,
                      "member_titles": [m["title"] for m in members],
                      "entry_edge": members[0]["input_edge"],
                      "edge_path": [members[0]["input_edge"]] + network["edge_chain"],
                      "scores": {name: fn(members) for name, fn in scorers.items()},
                      "schema_version": "1", **_CANDIDATE_BITS})

    rankings = {}
    for name in scorers:
        ordered = sorted(paths, key=lambda p: (p["scores"][name], p["path_id"]))   # deterministic ties
        rankings[name] = {"winner_path_id": ordered[0]["path_id"],
                          "winner_members": ordered[0]["member_titles"],
                          "winner_score": ordered[0]["scores"][name],
                          "top": [{"path_id": p["path_id"], "score": p["scores"][name]}
                                  for p in ordered[:TOP_K]],
                          "losers_preserved": len(ordered)}
    # Pareto front over the FIXED scorer dimensions. Dedupe identical score vectors first (grids have many
    # ties), so the O(n^2) dominance scan runs over the few DISTINCT vectors, not every path — the reviewers
    # measured the naive all-pairs scan at ~6s on a 10k grid; this keeps it sub-second while identical.
    score_names = sorted(scorers)
    vectors = {p["path_id"]: tuple(p["scores"][n] for n in score_names) for p in paths}
    distinct = sorted(set(vectors.values()))
    nondominated = {v for v in distinct
                    if not any(w != v and all(w[i] <= v[i] for i in range(len(score_names)))
                               and any(w[i] < v[i] for i in range(len(score_names))) for w in distinct)}
    pareto = [pid for pid, v in vectors.items() if v in nondominated]
    receipt_paths_digest = canonical_id("netpaths", *sorted(vectors)).rsplit("-", 1)[-1]
    return {"receipt_id": canonical_id(RECEIPT_ID_PREFIX, network["network_id"], receipt_paths_digest),
            "record_type": "network_grid_receipt", "network_id": network["network_id"],
            "network_name": network["name"], "grid_size": network["grid_size"],
            "evaluated": len(paths), "sampled": sampled,
            "scorers": {n: PATH_SCORERS[n]["note"] for n in score_names},
            "execution_scorer_opt_in": PATH_SCORERS["execution_efficiency"]["kind"] == "execution_measured",
            "rankings": rankings, "pareto_front": sorted(pareto), "paths": paths,
            "schema_version": "1", **_CANDIDATE_BITS}


#: the worked-example networks over the pack + aligned remixes. Add a network = add a row.
#: (the 3-part additions below were folded in from the network-buildout workflow after INDEPENDENT
#: re-verification — every listed chain fills with a multi-member slot; unsound-alignment chains were dropped.)
NETWORK_TABLE: list[dict[str, Any]] = [
    {"name": "officer_intelligence_network",
     "edge_chain": ["OfficerRowBatch", "OfficerDedupeClusterBatch"],
     "description": "From any officer-bearing public filing to review-gated officer clusters: step A extracts "
                    "officers (multiple sources compete for the slot), step B dedupe-clusters them."},
    {"name": "canonical_entity_network",
     "edge_chain": ["SourceEntityRecordBatch", "CanonicalEntityRowBatch"],
     "description": "From any registry's records to canonical entity rows: step A produces source entity "
                    "records (registry adapters compete), step B normalizes to the canonical row family."},
    {"name": "patent_ip_transfer_network",
     "edge_chain": ["PatentConveyanceRowBatch", "IpTransferEdgeBatch"],
     "description": "Ownership-CHANGE signal: step A ingests USPTO patent-assignment bulk XML (daily/weekly/"
                    "monthly cadence variants compete), step B normalizes assignor/assignee parties into typed "
                    "IP-transfer edges that expose acquisition activity before press releases do."},
    {"name": "edgar_control_person_network",
     "edge_chain": ["EdgarFilingReferenceBatch", "EdgarAccessionFetchPlan", "FilingDocumentBundle",
                    "OfficerRowBatch", "OfficerDedupeClusterBatch"],
     "description": "The deep EDGAR control-person chain (5 steps): step A discovers filings (index-cadence "
                    "enumerators + full-text search compete), step B builds a governed accession fetch plan, "
                    "step C fetches the document bundle, step D extracts officers, step E dedupe-clusters into "
                    "review-gated control-person clusters. The end-to-end acquisition motion as one grid."},
]


def build(write: bool = True, cards: Optional[list[dict[str, Any]]] = None,
          max_paths: int = DEFAULT_MAX_PATHS) -> dict[str, Any]:
    corpus = cards if cards is not None else aligned_corpus()
    networks = [build_network(row["name"], row["edge_chain"], corpus, row["description"])
                for row in NETWORK_TABLE]
    receipts = [grid_search(n, corpus, max_paths=max_paths) for n in networks]
    all_paths = [p for r in receipts for p in r["paths"]]
    manifest = {"record_type": "network_grid_manifest",
                "networks": len(networks), "paths_evaluated": len(all_paths),
                "receipts": len(receipts),
                "per_network": {n["name"]: {"grid_size": n["grid_size"], "slot_sizes": n["slot_sizes"]}
                                for n in networks},
                "scorers": sorted(PATH_SCORERS),
                "source_ref": "owner-intent:primitive-networks-grid-search:2026-07-10",
                **_CANDIDATE_BITS}
    if write:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        NETWORKS_PATH.write_text("".join(json.dumps(n, sort_keys=True) + "\n" for n in networks))
        PATHS_PATH.write_text("".join(json.dumps(p, sort_keys=True) + "\n" for p in all_paths))
        RECEIPTS_PATH.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in receipts))
        MANIFEST_PATH.write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n")
    return {"manifest": manifest, "networks": networks, "receipts": receipts, "paths": all_paths}


# ──────────────────────────────────────────────────────────────────────────────────────────────────────────
# Self-test — synthetic 3-step fixture with a KNOWN winner + the real pack networks.
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def _synthetic_card(cid: str, title: str, input_edge: str, output_edge: str, blackbox: str,
                    cost: int = 1) -> dict[str, Any]:
    return {"card_id": cid, "primitive_id": cid, "title": title, "blackbox": blackbox,
            "input_edge": input_edge, "output_edge": output_edge, "family": "synthetic",
            "cost": cost, **_CANDIDATE_BITS}


def _synthetic_three_step_corpus() -> list[dict[str, Any]]:
    """Step A (2 options) → step B (3) → step C (2) = 12 paths. `a_lean+b_lean+c_lean` is the known
    proxy-token winner (shortest text); `b_lean` carries a HIGH declared cost so the declared_cost winner
    is a DIFFERENT path — proving the scorer choice is load-bearing, not decorative."""
    return [
        _synthetic_card("syn:a_lean", "Lean loader", "SynthSource", "SynthA", "Loads records tersely."),
        _synthetic_card("syn:a_verbose", "Verbose loader", "SynthSource", "SynthA",
                        "Loads records with an extremely long narration " + "of every detail " * 30),
        _synthetic_card("syn:b_lean", "Lean transformer", "SynthA", "SynthB", "Transforms tersely.", cost=9),
        _synthetic_card("syn:b_mid", "Middling transformer", "SynthA", "SynthB",
                        "Transforms records with moderate elaboration on the mapping rules involved."),
        _synthetic_card("syn:b_verbose", "Verbose transformer", "SynthA", "SynthB",
                        "Transforms records while explaining itself at great length " + "again and again " * 30),
        _synthetic_card("syn:c_lean", "Lean sink", "SynthB", "SynthC", "Writes rows tersely."),
        _synthetic_card("syn:c_verbose", "Verbose sink", "SynthB", "SynthC",
                        "Writes rows with a very long preamble " + "covering each column " * 30),
    ]


def _self_test() -> int:
    checks: list[tuple[str, bool, str]] = []

    # (1) synthetic lattice: slots computed, grid enumerated fully, every path valid.
    synth = _synthetic_three_step_corpus()
    network = build_network("synthetic_three_step", ["SynthA", "SynthB", "SynthC"], synth)
    receipt = grid_search(network, synth)
    checks.append(("synthetic 3-step network: slots computed 2×3×2, full grid of 12 paths evaluated "
                   "(steps A/B/C each a slot of competing primitives)",
                   network["slot_sizes"] == [2, 3, 2] and network["grid_size"] == 12
                   and receipt["evaluated"] == 12 and receipt["sampled"] is False,
                   json.dumps(network["slot_sizes"])))

    # (2) grid search finds the KNOWN winner; a different scorer crowns a DIFFERENT path (scoring is
    #     load-bearing — the mutation gate for the ranking logic).
    proxy_winner = receipt["rankings"]["proxy_context_tokens"]["winner_members"]
    cost_winner_id = receipt["rankings"]["declared_cost"]["winner_path_id"]
    proxy_winner_id = receipt["rankings"]["proxy_context_tokens"]["winner_path_id"]
    checks.append(("grid search finds the known proxy-token winner (all-lean path) and the declared-cost "
                   "scorer crowns a DIFFERENT winner (b_lean's cost=9 penalty) — scorer choice matters",
                   proxy_winner == ["Lean loader", "Lean transformer", "Lean sink"]
                   and cost_winner_id != proxy_winner_id,
                   json.dumps(proxy_winner)))
    checks.append(("non-destructive: ALL 12 paths receipted with scores (losers preserved as labeled "
                   "fallbacks); pareto front computed and non-empty",
                   receipt["rankings"]["proxy_context_tokens"]["losers_preserved"] == 12
                   and len(receipt["paths"]) == 12 and receipt["pareto_front"],
                   f"pareto={len(receipt['pareto_front'])}"))

    # (3) the cap: a 5×5×5=125 grid with max_paths=40 walks a deterministic strided sample, honestly labeled.
    big = [_synthetic_card(f"syn:{s}{i}", f"{s}{i}", edge_in, edge_out, f"Synthetic member {s}{i}.")
           for s, edge_in, edge_out in (("x", "SynthSource", "SynthA"), ("y", "SynthA", "SynthB"),
                                        ("z", "SynthB", "SynthC")) for i in range(5)]
    big_network = build_network("synthetic_big", ["SynthA", "SynthB", "SynthC"], big)
    big_receipt = grid_search(big_network, big, max_paths=40)
    twice = grid_search(big_network, big, max_paths=40)
    checks.append(("past the cap: 125-point grid sampled at 40 via the coprime stride — sampled=true, "
                   "evaluated==cap, and the walk is deterministic (identical on re-run)",
                   big_receipt["sampled"] is True and big_receipt["evaluated"] == 40
                   and [p["path_id"] for p in big_receipt["paths"]] == [p["path_id"] for p in twice["paths"]],
                   f"evaluated={big_receipt['evaluated']}/125"))

    # (4) the REAL networks over the pack + aligned remixes: multiple primitives compete for step A.
    built = build(write=True)
    by_name = {n["name"]: n for n in built["networks"]}
    officer = by_name["officer_intelligence_network"]
    entity = by_name["canonical_entity_network"]
    officer_receipt = next(r for r in built["receipts"] if r["network_name"] == "officer_intelligence_network")
    checks.append(("real networks from the corporate pack: officer chain slot A has >=3 competing extractors "
                   "(DEF-14A/UK/990 aligned variants), entity chain slot A has >=4 registry adapters; every "
                   "grid path evaluated + ranked",
                   officer["slot_sizes"][0] >= 3 and entity["slot_sizes"][0] >= 4
                   and officer_receipt["evaluated"] == officer["grid_size"] >= 3
                   and officer_receipt["rankings"]["proxy_context_tokens"]["winner_path_id"],
                   f"officer slots={officer['slot_sizes']}, entity slots={entity['slot_sizes']}"))

    # (4b) the DEEP network: a 5-step EDGAR control-person chain (bridges make discovery→fetch→extract→cluster
    #      one grid), with a genuinely multi-member discovery slot — verifies depth WITHOUT fabricated edges.
    deep = by_name["edgar_control_person_network"]
    deep_receipt = next(r for r in built["receipts"] if r["network_name"] == "edgar_control_person_network")
    checks.append(("deep 5-step network fills honestly: discovery slot A multi-member, every downstream slot "
                   "bridged, all grid paths evaluated (no empty slots, no invented members)",
                   deep["step_count"] == 5 and deep["slot_sizes"][0] >= 2
                   and all(s >= 1 for s in deep["slot_sizes"])
                   and deep_receipt["evaluated"] == deep["grid_size"] >= 2
                   and not deep_receipt.get("empty_slots"),
                   f"deep slots={deep['slot_sizes']}"))

    # (5) empty-slot honesty: an unfillable chain is a coverage-gap receipt, not an error or invention.
    ghost = build_network("ghost", ["OfficerRowBatch", "EdgeNobodyProduces"], aligned_corpus())
    ghost_receipt = grid_search(ghost, aligned_corpus())
    checks.append(("unfillable slot -> honest coverage-gap receipt (0 paths, empty slot named, no invention)",
                   ghost_receipt["evaluated"] == 0 and ghost_receipt["empty_slots"] == ["B"]
                   and "coverage gap" in ghost_receipt["note"], json.dumps(ghost_receipt["empty_slots"])))

    # (5b) robustness (confirmed review findings): max_paths<=0 refuses honestly (clamped, no IndexError);
    #      an empty edge_chain is a clear contract error at construction, not a mid-search crash.
    clamped = grid_search(by_name["officer_intelligence_network"], aligned_corpus(), max_paths=0)
    empty_chain_rejected = False
    try:
        build_network("empty", [], aligned_corpus())
    except ValueError:
        empty_chain_rejected = True
    checks.append(("robustness: max_paths<=0 clamps to a real 1-path evaluation (no IndexError); empty "
                   "edge_chain raises ValueError at build (not a mid-grid crash)",
                   clamped["evaluated"] >= 1 and empty_chain_rejected, f"clamped_evaluated={clamped['evaluated']}"))

    # (6) determinism + hygiene + manifest.
    first_bytes = RECEIPTS_PATH.read_bytes()
    build(write=True)
    all_rows = built["networks"] + built["paths"] + built["receipts"]
    ids = [next(v for k, v in r.items() if k.endswith("_id")) for r in all_rows]
    manifest = json.loads(MANIFEST_PATH.read_text())
    checks.append(("deterministic build (receipts byte-identical); unique canonical ids; candidate-only "
                   "everywhere; the execution scorer stays OPT-IN (not in the default 0-token lane); "
                   "manifest counts computed",
                   first_bytes == RECEIPTS_PATH.read_bytes() and len(set(ids)) == len(ids)
                   and all(r["candidate"] is True and r["serves_truth"] is False for r in all_rows)
                   and "execution_efficiency" not in runnable_scorers()
                   and "execution_efficiency" in runnable_scorers(include_execution=True)
                   and manifest["paths_evaluated"] == len(built["paths"]), ""))
    checks.append(("no placeholder text in any emitted row",
                   all(marker not in json.dumps(r).lower() for r in all_rows
                       for marker in _PLACEHOLDER_MARKERS), ""))

    ok = all(passed for _n, passed, _d in checks)
    real_evaluated = sum(r["evaluated"] for r in built["receipts"])
    print(f"{'PASS' if ok else 'FAIL'} - primitive_networks_and_grid_search: step-lattice networks (slots "
          f"COMPUTED from edge contracts) + deterministic grid search under a scorer zoo — synthetic 12-path "
          f"lattice finds the known winner (and a different scorer crowns a different path), {len(built['networks'])} "
          f"real networks over the pack ({real_evaluated} paths receipted), strided sampling past the cap, "
          f"non-destructive rankings. serves_truth=false")
    for name, passed, detail in checks:
        print(f"  [{'ok' if passed else 'XX'}] {name}" + (f"  ({detail[:220]})" if not passed else ""))
    return 0 if ok else 1


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Primitive networks (step lattices) + grid search.")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--demo", action="store_true", help="print the ranked grids for the real networks")
    parser.add_argument("--max-paths", type=int, default=DEFAULT_MAX_PATHS)
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.build:
        print(json.dumps(build(write=True, max_paths=args.max_paths)["manifest"], indent=2, sort_keys=True))
        return 0
    if args.demo:
        built = build(write=False, max_paths=args.max_paths)
        for receipt in built["receipts"]:
            print(json.dumps({"network": receipt["network_name"], "grid_size": receipt["grid_size"],
                              "evaluated": receipt["evaluated"],
                              "winners": {name: {"members": rank["winner_members"], "score": rank["winner_score"]}
                                          for name, rank in receipt["rankings"].items()},
                              "pareto_front_size": len(receipt["pareto_front"])}, indent=2))
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
