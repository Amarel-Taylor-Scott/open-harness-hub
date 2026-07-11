#!/usr/bin/env python3
"""edge_alignment_gate — automate the SOUNDNESS half of canonical-edge alignment (open-problems gap 2.1).

Cross-mint edge chaining is ≈ 0 (independently-minted primitives never share an exact edge name), so the
composition layer depends on `CANONICAL_EDGE_ALIGNMENTS` — a table that maps a near-miss edge onto a shared
canonical one. This session that table was curated BY HAND: a 9-agent workflow proposed 14 alignments and a
human kept 4, rejected 10. This module turns the DETERMINISTIC part of that judgment into a reproducible gate,
so scaling alignment no longer means scaling manual review of the clearly-unsound.

The split that makes it tractable: an edge alignment has a SOUND-BY-SHAPE half (checkable) and a
SEMANTIC half (a judgment). This gate does the first and FLAGS the second — it is a NECESSARY, not sufficient,
filter. An admissible alignment is NOT auto-promoted; it becomes a `candidate` for review carrying evidence
(how many previously-refused compositions it would enable, and proof it breaks no existing exact chain).

Deterministic soundness rules (why each rejects a real proposal from this session):
  1. ROLE — both sides must be OUTPUT-PAYLOAD edges. Aligning an input-contract (…Request/Query/Plan/Window/
     Intent) or a decision-receipt (…Receipt/…DecisionReceipt) to a payload FABRICATES a chain by pretending
     "the request to fetch X" equals "the rows of X". (Rejects 7 of the 10: the Request/Query/Plan aliases.)
  2. AMBIGUITY — an alias is a single-valued function; if a source edge is proposed with >1 distinct target,
     ALL its proposals are rejected (don't arbitrarily pick one). (Rejects the 2 LeiRecordUpsertBatch→{two}.)
  3. CYCLE / RE-ALIAS — an alignment must not reverse or cycle an accepted one, nor re-alias an existing
     canonical target. (Rejects PatentConveyanceRowBatch→AssignmentPartyRowBatch, the reverse of an accepted.)
  4. SELF — no A→A.
Admitted proposals then get corpus EVIDENCE: `enables` (new exact producer→consumer pairs created on the
canonical edge) and `non_destructive` (the alias never lowers the total exact-chain count).

The self-test REPRODUCES the human 4-accept / 10-reject decision on this session's 14 proposals — the gate is
verified against the ground truth it is meant to automate (the verify-the-verifier law applied to alignment).

    PYTHONPATH=. python3 scripts/edge_alignment_gate.py --self-test
    PYTHONPATH=. python3 scripts/edge_alignment_gate.py --screen '{"from":"ExclusionCdcEventBatch","to":"RegistryChangeEventBatch"}'
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Optional

_HERE = Path(__file__).resolve()
_SBC = _HERE.parent.parent
_ROOT = _SBC.parent.parent
for _p in (str(_SBC), str(_SBC / "scripts"), str(_ROOT), str(_ROOT / "_repos" / "teleon" / "backend")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

#: edge-role classification by suffix (single source of the role vocabulary; extend = one row).
_INPUT_CONTRACT_SUFFIXES = ("Request", "Query", "Plan", "Window", "Intent", "File", "Text")
_DECISION_RECEIPT_SUFFIXES = ("Receipt", "Decision", "Denial")
_PAYLOAD_SUFFIXES = ("Batch", "Bundle", "Record", "Document", "Row", "Map", "Edge", "Facts", "List")


def edge_role(edge: str) -> str:
    """payload · input_contract · decision_receipt · unknown — the shape class of an edge name."""
    if edge.endswith(_DECISION_RECEIPT_SUFFIXES):
        return "decision_receipt"
    if edge.endswith(_INPUT_CONTRACT_SUFFIXES):
        return "input_contract"
    if edge.endswith(_PAYLOAD_SUFFIXES):
        return "payload"
    return "unknown"


def _reaches(alias: dict[str, str], start: str, goal: str) -> bool:
    """Does following the alias map from `start` ever reach `goal`? (cycle/transitive-target detection)"""
    seen, cur = set(), start
    while cur in alias and cur not in seen:
        seen.add(cur)
        cur = alias[cur]
        if cur == goal:
            return True
    return False


def screen(proposals: list[tuple[str, str]], existing: Optional[dict[str, str]] = None) -> list[dict[str, Any]]:
    """Apply the deterministic soundness gate to a BATCH of (from_edge, to_edge) proposals against the
    already-accepted `existing` alias map. Returns one verdict row per proposal (order preserved)."""
    existing = dict(existing or {})
    # ambiguity is a property of the batch: a source proposed with >1 distinct target is rejected wholesale.
    target_counts: dict[str, set[str]] = {}
    for frm, to in proposals:
        target_counts.setdefault(frm, set()).add(to)

    accepted = dict(existing)   # accumulates within the batch so later proposals see earlier admits
    verdicts: list[dict[str, Any]] = []
    for frm, to in proposals:
        from_role, to_role = edge_role(frm), edge_role(to)
        reason, admissible = "", False
        if existing.get(frm) == to:   # idempotent: this exact alias is already accepted, not a conflict
            verdicts.append({"from_edge": frm, "to_edge": to, "from_role": from_role, "to_role": to_role,
                             "admissible": True, "reason": "already an accepted alias (idempotent)",
                             "status": "already_accepted", "candidate": True, "serves_truth": False})
            continue
        if frm == to:
            reason = "self-alias (A→A) is meaningless"
        elif from_role != "payload" or to_role != "payload":
            reason = (f"role gate: alignment must be payload→payload, got {from_role}→{to_role} "
                      f"(an input-contract/receipt alias fabricates a chain)")
        elif len(target_counts.get(frm, set())) > 1:
            reason = (f"ambiguous: {frm} is proposed with {len(target_counts[frm])} distinct targets "
                      f"{sorted(target_counts[frm])} — an alias must be single-valued; rejecting all")
        elif frm in accepted:
            reason = f"conflict: {frm} is already aliased to {accepted[frm]!r}"
        elif to in accepted or _reaches(accepted, to, frm) or accepted.get(to) == frm:
            reason = f"cycle/re-alias: aligning to {to!r} would reverse or re-alias an existing canonical"
        elif _reaches(accepted, frm, to):
            reason = "redundant: already reachable through the existing alias chain"
        else:
            admissible, reason = True, "sound by shape — payload→payload, single-valued, acyclic (SEMANTIC review still required)"
            accepted[frm] = to
        verdicts.append({"from_edge": frm, "to_edge": to, "from_role": from_role, "to_role": to_role,
                         "admissible": admissible, "reason": reason,
                         "status": "candidate_for_review" if admissible else "rejected",
                         "candidate": True, "serves_truth": False})
    return verdicts


def _exact_chain_count(cards: list[dict[str, Any]], alias: dict[str, str]) -> int:
    """# of exact producer→consumer edges after applying `alias` to every card's input+output edge."""
    def a(e: Any) -> Any:
        return alias.get(e, e)
    producers: dict[Any, int] = {}
    consumers: dict[Any, int] = {}
    for c in cards:
        if c.get("output_edge"):
            producers[a(c["output_edge"])] = producers.get(a(c["output_edge"]), 0) + 1
        if c.get("input_edge"):
            consumers[a(c["input_edge"])] = consumers.get(a(c["input_edge"]), 0) + 1
    return sum(producers[e] * consumers[e] for e in producers if e in consumers)


def evidence(frm: str, to: str, cards: list[dict[str, Any]],
             existing: Optional[dict[str, str]] = None) -> dict[str, Any]:
    """Corpus evidence for ONE admitted alignment: how many exact chain-edges it ADDS, and that it removes
    none (non-destructive). Deterministic over the given cards."""
    base = dict(existing or {})
    before = _exact_chain_count(cards, base)
    after_map = {**base, frm: to}
    after = _exact_chain_count(cards, after_map)
    return {"exact_chain_edges_before": before, "exact_chain_edges_after": after,
            "enables_new_edges": max(0, after - before), "non_destructive": after >= before,
            "candidate": True, "serves_truth": False}


# ── this session's 14 proposals + the human ground-truth verdict (the mutation gate for the aligner). ────────
_SESSION_PROPOSALS: list[tuple[str, str]] = [
    ("AssignmentPartyRowBatch", "PatentConveyanceRowBatch"),          # accept
    ("EdgarFilingReferenceBatch", "EdgarAccessionFetchPlan"),         # reject (to=Plan)
    ("EdgarSearchHitBatch", "EdgarAccessionFetchPlan"),               # reject (to=Plan)
    ("ExclusionCdcEventBatch", "RegistryChangeEventBatch"),           # accept
    ("LeiRecordUpsertBatch", "RegistryChangeEventBatch"),             # reject (ambiguous)
    ("LeiRecordUpsertBatch", "SourceEntityRecordBatch"),              # reject (ambiguous)
    ("PacerFetchPlan", "DocketReferenceBatch"),                       # reject (from=Plan)
    ("PatentConveyanceRowBatch", "AssignmentPartyRowBatch"),          # reject (reverse/cycle of #1)
    ("ProxyStatementDocument", "FilingDocumentBundle"),               # accept
    ("RecapDocketQuery", "CanonicalEntityRowBatch"),                  # reject (from=Query)
    ("StateAnnualReportRequest", "CanonicalEntityRowBatch"),          # reject (from=Request)
    ("StateStatusNormalizeRequest", "SourceEntityRecordBatch"),       # reject (from=Request)
    ("ThirteenFFilingDocument", "FilingDocumentBundle"),              # accept
    ("UccSearchRequest", "CanonicalEntityRowBatch"),                  # reject (from=Request)
]
_SESSION_GROUND_TRUTH_ACCEPT = {
    ("AssignmentPartyRowBatch", "PatentConveyanceRowBatch"),
    ("ExclusionCdcEventBatch", "RegistryChangeEventBatch"),
    ("ProxyStatementDocument", "FilingDocumentBundle"),
    ("ThirteenFFilingDocument", "FilingDocumentBundle"),
}


def _self_test() -> int:
    checks: list[tuple[str, bool, str]] = []

    # (1) role classification: payloads vs input-contracts vs receipts.
    checks.append(("edge roles classify by shape (payload vs input_contract vs decision_receipt)",
                   edge_role("OfficerRowBatch") == "payload" and edge_role("EdgarAccessionFetchPlan") == "input_contract"
                   and edge_role("StateStatusNormalizeRequest") == "input_contract"
                   and edge_role("LicenseGateDecisionReceipt") == "decision_receipt"
                   and edge_role("FilingDocumentBundle") == "payload", ""))

    # (2) THE mutation gate: the deterministic screen REPRODUCES the human 4-accept / 10-reject decision on
    #     this session's 14 proposals — verified against the ground truth it automates.
    verdicts = screen(_SESSION_PROPOSALS)
    admitted = {(v["from_edge"], v["to_edge"]) for v in verdicts if v["admissible"]}
    checks.append(("gate reproduces the hand-verified decision EXACTLY: 4 admitted, 10 rejected, same set",
                   admitted == _SESSION_GROUND_TRUTH_ACCEPT and len(verdicts) == 14
                   and sum(v["admissible"] for v in verdicts) == 4,
                   f"admitted={sorted(admitted)}"))

    # (3) each rejection carries the RIGHT reason class (role / ambiguous / cycle) — not a generic no.
    by_pair = {(v["from_edge"], v["to_edge"]): v for v in verdicts}
    role_rej = by_pair[("StateStatusNormalizeRequest", "SourceEntityRecordBatch")]
    ambig_rej = by_pair[("LeiRecordUpsertBatch", "RegistryChangeEventBatch")]
    cycle_rej = by_pair[("PatentConveyanceRowBatch", "AssignmentPartyRowBatch")]
    plan_rej = by_pair[("EdgarFilingReferenceBatch", "EdgarAccessionFetchPlan")]
    checks.append(("rejections are explained by the correct rule (role / ambiguity / cycle), not a generic no",
                   "role gate" in role_rej["reason"] and "ambiguous" in ambig_rej["reason"]
                   and ("cycle" in cycle_rej["reason"] or "re-alias" in cycle_rej["reason"])
                   and "role gate" in plan_rej["reason"],
                   json.dumps({"cycle": cycle_rej["reason"][:60]})))

    # (4) the gate is NECESSARY not SUFFICIENT: an admitted pair is a candidate_for_review carrying the
    #     "semantic review still required" flag — it is never auto-promoted.
    admits = [v for v in verdicts if v["admissible"]]
    checks.append(("admitted alignments are candidates_for_review (semantic judgment still required), never "
                   "auto-served truth",
                   all(v["status"] == "candidate_for_review" and v["serves_truth"] is False
                       and "SEMANTIC review" in v["reason"] for v in admits), ""))

    # (5) corpus evidence: an admitted alignment ENABLES new exact chain-edges and is non-destructive, over
    #     the real corporate pack. (AssignmentPartyRowBatch→PatentConveyanceRowBatch feeds the ingester→normalizer.)
    try:
        from scripts.corporate_records_scraping_primitive_pack import build_cards  # noqa: PLC0415
        cards = build_cards()
        ev = evidence("AssignmentPartyRowBatch", "PatentConveyanceRowBatch", cards)
        checks.append(("corpus evidence: an admitted alignment enables >=1 new exact chain-edge and removes "
                       "none (non-destructive), measured on the real pack",
                       ev["enables_new_edges"] >= 1 and ev["non_destructive"] is True,
                       json.dumps(ev)))
    except Exception as exc:  # noqa: BLE001
        checks.append(("corpus evidence computable", False, str(exc)[:120]))

    # (6) determinism: same batch, same verdicts (no RNG, no order surprises).
    checks.append(("deterministic: re-screening the batch yields identical verdicts",
                   [v["admissible"] for v in screen(_SESSION_PROPOSALS)]
                   == [v["admissible"] for v in verdicts], ""))

    # (7) the SHIPPED CANONICAL_EDGE_ALIGNMENTS are all admissible under the gate (self-consistency: the table
    #     we serve would pass its own soundness gate).
    try:
        from scripts.primitive_groups_frameworks_and_remixers import CANONICAL_EDGE_ALIGNMENTS  # noqa: PLC0415
        shipped = list(CANONICAL_EDGE_ALIGNMENTS.items())
        shipped_verdicts = screen(shipped)
        # every shipped alias is payload→payload (the load-bearing soundness property)
        all_payload = all(v["from_role"] == "payload" and v["to_role"] == "payload" for v in shipped_verdicts)
        checks.append(("the SHIPPED alignment table is self-consistent: every served alias is payload→payload "
                       "(passes its own role gate)",
                       all_payload, f"{len(shipped)} shipped aliases, all payload→payload={all_payload}"))
    except Exception as exc:  # noqa: BLE001
        checks.append(("shipped table screenable", False, str(exc)[:120]))

    # (8) idempotency: re-screening an already-accepted alias reports already_accepted, NOT a false conflict.
    idem = screen([("NonprofitOfficerRowBatch", "OfficerRowBatch")],
                  existing={"NonprofitOfficerRowBatch": "OfficerRowBatch"})
    checks.append(("idempotent: re-screening a shipped alias -> already_accepted (admissible, not a conflict)",
                   len(idem) == 1 and idem[0]["status"] == "already_accepted" and idem[0]["admissible"] is True,
                   idem[0]["status"]))

    ok = all(passed for _n, passed, _d in checks)
    print(f"{'PASS' if ok else 'FAIL'} - edge_alignment_gate: deterministic soundness gate for canonical-edge "
          f"alignment (gap 2.1) — role/ambiguity/cycle screen + corpus enable-evidence; REPRODUCES the "
          f"hand-verified 4-accept/10-reject decision on this session's 14 proposals; admits are "
          f"candidates_for_review, never auto-truth. serves_truth=false")
    for name, passed, detail in checks:
        print(f"  [{'ok' if passed else 'XX'}] {name}" + (f"  ({detail[:200]})" if not passed else ""))
    return 0 if ok else 1


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Deterministic soundness gate for canonical-edge alignments.")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--screen", help='JSON {"from":..,"to":..} or [{"from":..,"to":..},...] to screen')
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.screen:
        payload = json.loads(args.screen)
        pairs = [(payload["from"], payload["to"])] if isinstance(payload, dict) else \
                [(p["from"], p["to"]) for p in payload]
        from scripts.primitive_groups_frameworks_and_remixers import CANONICAL_EDGE_ALIGNMENTS  # noqa: PLC0415
        verdicts = screen(pairs, existing=dict(CANONICAL_EDGE_ALIGNMENTS))
        try:
            from scripts.corporate_records_scraping_primitive_pack import build_cards  # noqa: PLC0415
            cards = build_cards()
            for v in verdicts:
                if v["admissible"]:
                    v["evidence"] = evidence(v["from_edge"], v["to_edge"], cards,
                                             existing=dict(CANONICAL_EDGE_ALIGNMENTS))
        except Exception:  # noqa: BLE001
            pass
        print(json.dumps(verdicts, indent=2, sort_keys=True))
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
