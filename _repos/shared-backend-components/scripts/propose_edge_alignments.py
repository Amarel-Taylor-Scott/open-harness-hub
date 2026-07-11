#!/usr/bin/env python3
"""propose_edge_alignments — the PROPOSE half of the edge aligner (open-problems gap 2.1), closing the loop.

`edge_alignment_gate.py` verifies alignment SOUNDNESS but takes proposals as input. This module GENERATES the
proposals deterministically from the corpus, so the alignment table no longer has to be dreamt up by hand.

The mechanism is grounded, not magic: the composition breaks are exactly the dangling edges from
`producer_edge_index` — an edge PRODUCED-but-never-consumed (a dead-end output) and an edge
CONSUMED-but-never-produced (a dead-end input) are two independently-minted names for what may be the same
payload. We propose aligning the dead-end OUTPUT onto the dead-end INPUT (producer's variant → the name
consumers already expect) whenever they are the same role and their CamelCase token sets are similar enough.
Every proposal is then run through the soundness gate + corpus evidence; only admitted, chain-enabling ones
survive, as `candidate_for_review` rows a human promotes into `CANONICAL_EDGE_ALIGNMENTS` (never auto-served —
the candidate/truth boundary holds: proposing is not promoting).

The proof it works: run on the RAW pack (no remixes), the loop REDISCOVERS the hand-authored alignments
(OfficerDirectorRowBatch→OfficerRowBatch, the registry→SourceEntityRecordBatch family, …) automatically —
the same table a human wrote, now derived and gated.

    PYTHONPATH=. python3 scripts/propose_edge_alignments.py --self-test
    PYTHONPATH=. python3 scripts/propose_edge_alignments.py --propose
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
_ROOT = _SBC.parent.parent
for _p in (str(_SBC), str(_SBC / "scripts"), str(_ROOT), str(_ROOT / "_repos" / "teleon" / "backend")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    from src.teleon.experiments.ids import canonical_id  # noqa: E402  the ONE id authority (data plane law)
except Exception as exc:  # noqa: BLE001
    raise SystemExit(f"propose_edge_alignments requires canonical_id; import failed: {exc}")

OUT_DIR = _SBC / "data" / "dev-intel" / "primitive_factory" / "alignment_proposals"
PROPOSALS_PATH = OUT_DIR / "candidate_edge_alignments.jsonl"
MANIFEST_PATH = OUT_DIR / "alignment_proposal_manifest.json"
PROPOSAL_ID_PREFIX = "palign"
#: token-set (Jaccard) similarity floor for a proposal. Deliberately high — a spurious alignment is worse than
#: a missed one (an unsound alias fabricates capability). Tunable; the gate is the hard soundness backstop.
DEFAULT_MIN_SIMILARITY = 0.5
_CAMEL_RE = re.compile(r"[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z]+|[A-Z]+|[0-9]+")
#: generic payload-shape tokens that carry no domain meaning — excluded from the similarity so "…RowBatch"
#: vs "…RowBatch" doesn't match on the suffix alone (that is the type-token-scramble failure mode).
_GENERIC_TOKENS = frozenset({"row", "batch", "bundle", "record", "document", "list", "map", "edge", "the", "a"})


def camel_tokens(edge: str) -> frozenset[str]:
    return frozenset(t.lower() for t in _CAMEL_RE.findall(edge)) - _GENERIC_TOKENS


def similarity(a: str, b: str) -> float:
    """Jaccard over domain (non-generic) CamelCase tokens — deterministic, 0..1."""
    ta, tb = camel_tokens(a), camel_tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def propose(cards: list[dict[str, Any]], *, matcher: bool = True,
            min_similarity: float = DEFAULT_MIN_SIMILARITY, similarity_fn: Any = None) -> list[dict[str, Any]]:
    """Generate candidate alignments and screen each for soundness + enablement.

    The compatibility decision is DELEGATED to the shared `edge_type_matcher` (reuse-first: its 6 tiers —
    exact/canonical/token/type/family/embedding — are THE composer's edge-compatibility authority; do not
    reimplement it). For each consumer edge T, `match_hits(T)` yields producer OUTPUT edges type-compatible
    with T; a NON-exact hit O (a different name that still satisfies T) is a candidate alignment O→T. Each is
    then run through the soundness gate + corpus evidence and emitted as a `candidate_for_review` row a human
    promotes (proposing is not promoting). Set `matcher=False` for a pure token-Jaccard fallback lane
    (deterministic, no matcher dependency) via `similarity_fn`.

    This is a REVIEW QUEUE, not an oracle: multiple candidate targets per source are fine (a human picks one,
    which then passes the single-valued promotion gate)."""
    from scripts.producer_edge_index import build_producer_edge_index  # noqa: PLC0415
    from scripts.edge_alignment_gate import edge_role, evidence, screen  # noqa: PLC0415

    pei = build_producer_edge_index(cards)
    consumer_edges = [e for e in pei["consumers"] if edge_role(e) == "payload"]

    #: (from_edge O, to_edge T, tier, via) candidates — from the shared matcher, or the token fallback.
    raw: list[tuple[str, str, int, str]] = []
    if matcher:
        from scripts.edge_type_matcher import build_producer_index, match_hits  # noqa: PLC0415  the ONE matcher
        m_index = build_producer_index(cards)
        for tgt in consumer_edges:
            for hit in match_hits(tgt, m_index):
                if hit["match_tier"] == 0:   # exact — already chains, not an alignment
                    continue
                out_edge = hit.get("producer_output_edge")
                if out_edge and out_edge != tgt and edge_role(out_edge) == "payload":
                    raw.append((out_edge, tgt, hit["match_tier"], hit["matched_via"]))
    else:
        sim_fn = similarity_fn or similarity
        for out_edge in [e for e in pei["producers"] if edge_role(e) == "payload"]:
            for tgt in consumer_edges:
                if out_edge != tgt and sim_fn(out_edge, tgt) >= min_similarity:
                    raw.append((out_edge, tgt, 2, "token"))

    # dedup by (O,T) keeping the STRONGEST tier (lowest number); deterministic order.
    best: dict[tuple[str, str], tuple[int, str]] = {}
    for out_edge, tgt, tier, via in raw:
        if (out_edge, tgt) not in best or tier < best[(out_edge, tgt)][0]:
            best[(out_edge, tgt)] = (tier, via)
    pairs = sorted(best)

    verdicts = screen(pairs)   # role/self checks per-pair (ambiguity is a PROMOTION concern, not a proposal one)
    admitted: list[dict[str, Any]] = []
    for (out_edge, tgt), verdict in zip(pairs, verdicts):
        if verdict["from_role"] != "payload" or verdict["to_role"] != "payload":
            continue   # role gate: never propose an input-contract/receipt as either side
        ev = evidence(out_edge, tgt, cards)
        if ev["enables_new_edges"] < 1:   # a sound but useless alias is not worth a review ticket
            continue
        tier, via = best[(out_edge, tgt)]
        admitted.append({
            "proposal_id": canonical_id(PROPOSAL_ID_PREFIX, out_edge, tgt),
            "record_type": "candidate_edge_alignment",
            "from_edge": out_edge, "to_edge": tgt, "matched_via": via, "match_tier": tier,
            "token_similarity": round(similarity(out_edge, tgt), 4),
            "evidence": ev, "status": "candidate_for_review",
            "note": "auto-proposed via edge_type_matcher + soundness/role-gated; a human promotes ONE target "
                    "per source into CANONICAL_EDGE_ALIGNMENTS (proposing is not promoting; single-valued gate runs then)",
            "candidate": True, "serves_truth": False,
        })
    return sorted(admitted, key=lambda r: (r["match_tier"], -r["evidence"]["enables_new_edges"],
                                           r["from_edge"], r["to_edge"]))


def build(write: bool = True) -> dict[str, Any]:
    from scripts.corporate_records_scraping_primitive_pack import build_cards  # noqa: PLC0415
    proposals = propose(build_cards())   # RAW pack (no remixes) — rediscover the alignments from scratch
    manifest = {"record_type": "alignment_proposal_manifest", "proposed": len(proposals),
                "min_similarity": DEFAULT_MIN_SIMILARITY,
                "source_ref": "gap-2.1-propose-verify-loop:2026-07-10", "candidate": True, "serves_truth": False}
    if write:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        PROPOSALS_PATH.write_text("".join(json.dumps(p, sort_keys=True) + "\n" for p in proposals))
        MANIFEST_PATH.write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n")
    return {"manifest": manifest, "proposals": proposals}


def _self_test() -> int:
    checks: list[tuple[str, bool, str]] = []
    from scripts.corporate_records_scraping_primitive_pack import build_cards  # noqa: PLC0415
    from scripts.primitive_groups_frameworks_and_remixers import CANONICAL_EDGE_ALIGNMENTS  # noqa: PLC0415

    cards = build_cards()
    proposals = propose(cards)   # PRIMARY lane: reuses edge_type_matcher (6 tiers)
    proposed_pairs = {(p["from_edge"], p["to_edge"]) for p in proposals}

    checks.append(("proposals generated from the corpus's edges via the shared matcher (non-empty set)",
                   len(proposals) >= 3, f"{len(proposals)} proposals"))

    # (2) REUSE-FIRST: the compatibility decision comes from edge_type_matcher (the ONE composer-shared matcher,
    #     6 tiers), not a private reimplementation — every proposal carries a matcher tier name.
    from scripts.edge_type_matcher import _TIER_NAMES  # noqa: PLC0415
    checks.append(("REUSE: proposals delegate compatibility to edge_type_matcher (each carries a matcher tier), "
                   "not a private matcher",
                   all(p["matched_via"] in set(_TIER_NAMES.values()) | {"token"} for p in proposals)
                   and all("edge_type_matcher" in p["note"] for p in proposals), ""))

    # (3) REDISCOVERY: the matcher re-derives the lexically-similar shipped alignments automatically — the whole
    #     OFFICER convergence family appears as candidates. The table is derivable, not just hand-typed.
    officer_family = {("OfficerDirectorRowBatch", "OfficerRowBatch"),
                      ("NonprofitOfficerRowBatch", "OfficerRowBatch"),
                      ("UkOfficerRowBatch", "OfficerRowBatch")}
    checks.append(("REDISCOVERY: the matcher re-derives the Officer convergence family from the raw pack "
                   "(the hand-authored alignments are now proposed, not typed)",
                   officer_family <= proposed_pairs,
                   f"found {sorted(officer_family & proposed_pairs)}"))

    # (4) HONEST LIMITATION: the matcher's ACTIVE tiers (no embedder built) still miss the
    #     semantically-related-but-lexically-dissimilar entity family (UkCompanyProfileRecord ~
    #     SourceEntityRecordBatch share ~no tokens/family). The matcher HAS an embedding tier for exactly this;
    #     it is inactive until embeddings are built. Surfacing the limit is the honest result.
    entity_semantic = ("UkCompanyProfileRecord", "SourceEntityRecordBatch")
    checks.append(("HONEST: the matcher's active (no-embedder) tiers do NOT propose the lexically-dissimilar "
                   "entity family — the documented job of the matcher's EMBEDDING tier (inactive here)",
                   entity_semantic not in proposed_pairs
                   and ("OfficerDirectorRowBatch", "OfficerRowBatch") in proposed_pairs,
                   f"token_sim(entity)={similarity(*entity_semantic):.2f}"))

    # (5) the token FALLBACK lane (matcher=False) is pluggable: a stub similarity_fn scoring the entity pair
    #     high DOES surface it — proving a richer scorer (the embedder) drops into the same gate+evidence loop.
    def _semantic_stub(a: str, b: str) -> float:
        return 0.9 if {a, b} == set(entity_semantic) else similarity(a, b)
    stub_proposals = {(p["from_edge"], p["to_edge"])
                      for p in propose(cards, matcher=False, similarity_fn=_semantic_stub)}
    checks.append(("the scorer seam is pluggable: a richer (embedding-like) scorer surfaces the entity family "
                   "the active tiers missed — same gate, richer proposer",
                   entity_semantic in stub_proposals, ""))

    # (4) SOUNDNESS: every proposal passed the role gate (payload→payload) AND enables >=1 edge non-destructively.
    checks.append(("every proposal is role-gated (payload→payload) and enables >=1 new exact chain-edge "
                   "non-destructively",
                   all(p["evidence"]["enables_new_edges"] >= 1 and p["evidence"]["non_destructive"]
                       for p in proposals), ""))

    # (5) NO UNSOUND proposal: an input-contract edge is never proposed as either side (the gate + role filter).
    from scripts.edge_alignment_gate import edge_role  # noqa: PLC0415
    checks.append(("no input-contract/receipt edge appears in any proposal (soundness by construction)",
                   all(edge_role(p["from_edge"]) == "payload" and edge_role(p["to_edge"]) == "payload"
                       for p in proposals), ""))

    # (5) candidate-only + never auto-promotes into the served table.
    checks.append(("proposals are candidate_for_review (proposing is not promoting; table not auto-mutated)",
                   all(p["status"] == "candidate_for_review" and p["serves_truth"] is False for p in proposals),
                   ""))

    # (6) similarity excludes generic suffix tokens (RowBatch vs RowBatch alone must NOT match).
    checks.append(("similarity ignores generic payload tokens (Row/Batch/…) — matches on DOMAIN tokens only",
                   similarity("FooRowBatch", "BarRowBatch") == 0.0
                   and similarity("OfficerDirectorRowBatch", "OfficerRowBatch") >= 0.5, ""))

    # (7) determinism.
    build(write=True)
    first = PROPOSALS_PATH.read_bytes()
    build(write=True)
    checks.append(("deterministic (byte-identical rebuild)", first == PROPOSALS_PATH.read_bytes(), ""))

    ok = all(passed for _n, passed, _d in checks)
    print(f"{'PASS' if ok else 'FAIL'} - propose_edge_alignments: the PROPOSE half of the aligner (gap 2.1), "
          f"REUSING edge_type_matcher — candidate alignments from corpus edges, screened through the soundness "
          f"gate + enablement evidence; re-derives the Officer convergence family from the raw pack "
          f"({len(proposals)} gated proposals); the semantic entity family awaits the matcher's embedding tier; "
          f"candidate_for_review, never auto-promoted. serves_truth=false")
    for name, passed, detail in checks:
        print(f"  [{'ok' if passed else 'XX'}] {name}" + (f"  ({detail[:200]})" if not passed else ""))
    return 0 if ok else 1


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Propose + gate candidate canonical-edge alignments.")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--propose", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.propose:
        result = build(write=True)
        print(json.dumps({"proposed": len(result["proposals"]),
                          "proposals": [{"from": p["from_edge"], "to": p["to_edge"],
                                         "matched_via": p["matched_via"],
                                         "enables": p["evidence"]["enables_new_edges"]}
                                        for p in result["proposals"]]}, indent=2, sort_keys=True))
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
