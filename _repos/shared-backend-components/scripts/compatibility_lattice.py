#!/usr/bin/env python3
"""compatibility_lattice — graded, DIRECTIONAL edge compatibility: names retrieve, contracts authorize.

External research review (2026-07-10) landed the central correction to the whole composition design: an
"alignment" must not be an undirected name-alias that authorizes execution. Composition compatibility is a
DIRECTIONAL, GRADED relation, and only some grades may auto-execute; names, embeddings, and model similarity
RETRIEVE candidates but NEVER authorize a join (their grade caps at CLOSE_CANDIDATE). This module makes that
lattice executable — the bounded, first increment toward a contract algebra, reusing the edge machinery we
already have (edge_alignment_gate roles + the canonical alignment table) instead of inventing a parallel one.

The lattice (strongest→weakest authorization; research §5.3):

    IDENTICAL          producer output edge == consumer input edge                          -> AUTO
    FAMILY_COMPATIBLE  both fold to the same curated canonical type (registry-verified)     -> AUTO
    SAFE_STRUCTURAL    a promoted/curated alignment maps producer -> consumer, payload→payload -> AUTO
    VERIFIED_ADAPTER   a directional adapter with sufficient evidence exists                 -> AUTO
    LOSSY_OR_PARTIAL   a conversion exists but loses info / may fail                         -> POLICY-GATED
    CLOSE_CANDIDATE    name/token/embedding similarity only                                  -> RETRIEVAL ONLY
    UNKNOWN            checker incomplete / unknown role / no evidence                       -> RETRIEVAL ONLY
    INCOMPATIBLE       a role/direction contradiction (e.g. input-contract cannot satisfy a payload consumer) -> REFUSED

The load-bearing invariant, self-tested: a CLOSE_CANDIDATE (a name/embedding match) NEVER authorizes execution.

    PYTHONPATH=. python3 scripts/compatibility_lattice.py --self-test
    PYTHONPATH=. python3 scripts/compatibility_lattice.py --classify OfficerDirectorRowBatch OfficerRowBatch
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

#: grades ordered strongest→weakest authorization.
GRADES = ("IDENTICAL", "FAMILY_COMPATIBLE", "SAFE_STRUCTURAL", "VERIFIED_ADAPTER", "LOSSY_OR_PARTIAL",
          "CLOSE_CANDIDATE", "UNKNOWN", "INCOMPATIBLE")
#: grades that MAY authorize automatic execution (a deterministic composer may chain on these).
AUTO_EXECUTE_GRADES = frozenset({"IDENTICAL", "FAMILY_COMPATIBLE", "SAFE_STRUCTURAL", "VERIFIED_ADAPTER"})
#: grades that authorize ONLY under explicit policy + a typed error/guard.
POLICY_GATED_GRADES = frozenset({"LOSSY_OR_PARTIAL"})
#: grades that NEVER authorize execution — they are retrieval/candidate signals only (the research invariant).
RETRIEVAL_ONLY_GRADES = frozenset({"CLOSE_CANDIDATE", "UNKNOWN"})
#: token-Jaccard floor above which a name match is a CLOSE_CANDIDATE (retrieval only).
_CLOSE_SIMILARITY_FLOOR = 0.5


def authorizes_execution(grade: str, *, policy_allows_lossy: bool = False) -> bool:
    """Does this compatibility grade authorize a DETERMINISTIC composer to chain the join? Names/embeddings
    (CLOSE_CANDIDATE) and UNKNOWN never do; LOSSY_OR_PARTIAL only under explicit policy."""
    if grade in AUTO_EXECUTE_GRADES:
        return True
    if grade in POLICY_GATED_GRADES:
        return policy_allows_lossy
    return False


def classify_compatibility(producer_edge: str, consumer_edge: str, *,
                           alignments: Optional[dict[str, str]] = None,
                           adapters: Optional[set[tuple[str, str]]] = None,
                           curated_canonical: Optional[set[str]] = None,
                           similarity_fn: Optional[Callable[[str, str], float]] = None) -> dict[str, Any]:
    """DIRECTIONAL: can `producer_edge` (a producer's output) satisfy `consumer_edge` (a consumer's input)?
    Returns {grade, authorizes, direction, reason} — the graded verdict. Reuses edge_alignment_gate.edge_role
    (the ONE role authority) and the canonical alignment table; adapters/curated_canonical are optional
    registries a caller supplies. Similarity (names/embeddings) can only reach CLOSE_CANDIDATE."""
    from scripts.edge_alignment_gate import edge_role  # noqa: PLC0415  the ONE role authority
    if alignments is None:
        from scripts.primitive_groups_frameworks_and_remixers import CANONICAL_EDGE_ALIGNMENTS  # noqa: PLC0415
        alignments = dict(CANONICAL_EDGE_ALIGNMENTS)
    adapters = adapters or set()

    def _grade(g: str, reason: str) -> dict[str, Any]:
        return {"producer_edge": producer_edge, "consumer_edge": consumer_edge, "direction": "producer->consumer",
                "grade": g, "authorizes_execution": authorizes_execution(g), "reason": reason,
                "candidate": True, "serves_truth": False}

    if producer_edge == consumer_edge:
        return _grade("IDENTICAL", "producer output edge string == consumer input edge string")

    p_role, c_role = edge_role(producer_edge), edge_role(consumer_edge)
    # abstain FIRST on an unknown role — the checker is incomplete, so it is retrieval-only, not a refusal.
    if p_role == "unknown" or c_role == "unknown":
        return _grade("UNKNOWN", f"edge role unknown ({p_role}->{c_role}); the checker abstains — retrieval only")
    # a KNOWN non-payload producer (input-contract / decision-receipt) cannot satisfy a payload consumer: a
    # direction contradiction — this is the shape that makes input-contract→payload aliases fabricated chains.
    if p_role != "payload" and c_role == "payload":
        return _grade("INCOMPATIBLE", f"a {p_role} producer edge cannot satisfy a payload consumer (direction "
                                      "contradiction — the classic fabricated-chain shape)")

    # a direct curated/promoted alignment mapping producer -> consumer (payload→payload) is a structural safety.
    if alignments.get(producer_edge) == consumer_edge and p_role == "payload" and c_role == "payload":
        return _grade("SAFE_STRUCTURAL", "a curated/promoted alignment maps producer -> consumer (payload→payload)")

    # otherwise, if both fold onto the SAME curated canonical type, that is a registry-verified family match.
    def _fold(edge: str) -> str:
        return alignments.get(edge, edge)
    if _fold(producer_edge) == _fold(consumer_edge) and _fold(producer_edge) != producer_edge:
        return _grade("FAMILY_COMPATIBLE", f"both fold to the curated canonical type {_fold(producer_edge)!r}")

    if (producer_edge, consumer_edge) in adapters:
        return _grade("VERIFIED_ADAPTER", "a directional verified adapter exists for this producer->consumer pair")

    # name/token/embedding similarity is RETRIEVAL ONLY — it caps at CLOSE_CANDIDATE and never authorizes.
    sim = 0.0
    if similarity_fn is not None:
        sim = similarity_fn(producer_edge, consumer_edge)
    else:
        from scripts.propose_edge_alignments import similarity as _token_sim  # noqa: PLC0415  the shared token sim
        sim = _token_sim(producer_edge, consumer_edge)
    if sim >= _CLOSE_SIMILARITY_FLOOR and p_role == "payload" and c_role == "payload":
        return _grade("CLOSE_CANDIDATE", f"name/token similarity {sim:.2f} only — RETRIEVAL candidate, must be "
                                         "verified by structure/adapter/review before it can authorize a join")
    return _grade("INCOMPATIBLE", "no identity, family fold, alignment, adapter, or similarity — not composable")


def _self_test() -> int:
    checks: list[tuple[str, bool, str]] = []
    alignments = {"OfficerDirectorRowBatch": "OfficerRowBatch", "NonprofitOfficerRowBatch": "OfficerRowBatch"}

    # (1) IDENTICAL edges authorize.
    ident = classify_compatibility("OfficerRowBatch", "OfficerRowBatch", alignments=alignments)
    checks.append(("IDENTICAL: same edge -> IDENTICAL, authorizes execution",
                   ident["grade"] == "IDENTICAL" and ident["authorizes_execution"] is True, ""))

    # (2) a curated alignment producer->consumer -> SAFE_STRUCTURAL, authorizes.
    safe = classify_compatibility("OfficerDirectorRowBatch", "OfficerRowBatch", alignments=alignments)
    checks.append(("SAFE_STRUCTURAL: a curated alignment (DirectorRowBatch->OfficerRowBatch) authorizes",
                   safe["grade"] == "SAFE_STRUCTURAL" and safe["authorizes_execution"] is True, safe["grade"]))

    # (3) two edges that both fold to the same canonical -> FAMILY_COMPATIBLE, authorizes.
    fam = classify_compatibility("OfficerDirectorRowBatch", "NonprofitOfficerRowBatch", alignments=alignments)
    checks.append(("FAMILY_COMPATIBLE: two variants folding to the same canonical authorize",
                   fam["grade"] == "FAMILY_COMPATIBLE" and fam["authorizes_execution"] is True, fam["grade"]))

    # (4) THE INVARIANT: a name/token-similar-only pair -> CLOSE_CANDIDATE and does NOT authorize execution.
    close = classify_compatibility("VendorOfficerRowBatch", "OfficerRowBatch", alignments={})
    checks.append(("INVARIANT: a name/token-similar-only pair is CLOSE_CANDIDATE and NEVER authorizes execution "
                   "(names retrieve; they do not authorize)",
                   close["grade"] == "CLOSE_CANDIDATE" and close["authorizes_execution"] is False, close["grade"]))

    # (5) an input-contract producer edge -> a payload consumer is INCOMPATIBLE (the fabricated-chain shape).
    incomp = classify_compatibility("StateStatusNormalizeRequest", "SourceEntityRecordBatch", alignments={})
    checks.append(("INCOMPATIBLE: an input-contract producer cannot satisfy a payload consumer (the "
                   "fabricated-chain shape is refused)",
                   incomp["grade"] == "INCOMPATIBLE" and incomp["authorizes_execution"] is False, incomp["grade"]))

    # (6) an unknown-role edge -> UNKNOWN, retrieval only.
    unk = classify_compatibility("weird_lowercase_edge", "OfficerRowBatch", alignments={})
    checks.append(("UNKNOWN: an unknown-role edge abstains (UNKNOWN, retrieval only), never authorizes",
                   unk["grade"] == "UNKNOWN" and unk["authorizes_execution"] is False, unk["grade"]))

    # (7) a verified adapter authorizes a pair that otherwise would not chain.
    adapted = classify_compatibility("FooRowBatch", "BarRowBatch", alignments={},
                                     adapters={("FooRowBatch", "BarRowBatch")})
    checks.append(("VERIFIED_ADAPTER: a registered directional adapter authorizes the join",
                   adapted["grade"] == "VERIFIED_ADAPTER" and adapted["authorizes_execution"] is True, ""))

    # (8) DIRECTIONALITY: producer->consumer may differ from consumer->producer (an alias is not symmetric).
    fwd = classify_compatibility("OfficerDirectorRowBatch", "OfficerRowBatch", alignments=alignments)
    rev = classify_compatibility("OfficerRowBatch", "OfficerDirectorRowBatch", alignments=alignments)
    checks.append(("DIRECTIONAL: the relation is not symmetric — fwd (aligned) authorizes, rev does not",
                   fwd["authorizes_execution"] is True and rev["authorizes_execution"] is False,
                   f"fwd={fwd['grade']}, rev={rev['grade']}"))

    # (9) grade partition is well-formed: auto ∪ policy ∪ retrieval-only ∪ {INCOMPATIBLE} == GRADES.
    partition = AUTO_EXECUTE_GRADES | POLICY_GATED_GRADES | RETRIEVAL_ONLY_GRADES | {"INCOMPATIBLE"}
    checks.append(("the grade partition covers every grade exactly once (auto/policy/retrieval-only/refused)",
                   partition == set(GRADES)
                   and not (AUTO_EXECUTE_GRADES & RETRIEVAL_ONLY_GRADES), ""))

    # (10) LOSSY is policy-gated: refused by default, allowed only with explicit policy.
    checks.append(("LOSSY_OR_PARTIAL authorizes ONLY under explicit policy (a typed-error/guard opt-in)",
                   authorizes_execution("LOSSY_OR_PARTIAL") is False
                   and authorizes_execution("LOSSY_OR_PARTIAL", policy_allows_lossy=True) is True, ""))

    ok = all(passed for _n, passed, _d in checks)
    print(f"{'PASS' if ok else 'FAIL'} - compatibility_lattice: graded DIRECTIONAL edge compatibility (research "
          f"§5.3) — {len(GRADES)} grades where only IDENTICAL/FAMILY/STRUCTURAL/ADAPTER authorize execution; "
          f"names & embeddings cap at CLOSE_CANDIDATE (retrieval only, NEVER authorize); input-contract→payload "
          f"is INCOMPATIBLE; the relation is directional. The first increment of a contract algebra over the "
          f"existing edge machinery. serves_truth=false")
    for name, passed, detail in checks:
        print(f"  [{'ok' if passed else 'XX'}] {name}" + (f"  ({detail[:200]})" if not passed else ""))
    return 0 if ok else 1


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Graded directional edge compatibility (the contract lattice).")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--classify", nargs=2, metavar=("PRODUCER", "CONSUMER"))
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.classify:
        print(json.dumps(classify_compatibility(args.classify[0], args.classify[1]), indent=2, sort_keys=True))
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
