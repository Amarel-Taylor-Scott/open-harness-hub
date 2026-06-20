#!/usr/bin/env python3
"""scripts.check_stateful_swarm_local_stub — PROOF: the OFFLINE local stateful-swarm runner is real, deterministic,
and governed (it writes typed entries to the local SQLite blackboard, the synthesis reads the BOARD, never truth).

A stateful swarm runs many BOUNDED workers against ONE shared, append-only blackboard so they build persistent
typed source-backed STATE instead of re-reading docs. Teleon RUNS the swarm; Baltor GOVERNS what (if anything)
becomes truth. A swarm run is WORKING STATE — never served truth.

Asserts:
  A. PORT CONTRACT: StatefulSwarmProviderPort is runtime_checkable; LocalStatefulSwarm satisfies it (provider_id +
     describe + run); describe() card is local-first (no network, no keys, serves_truth False, own local_equivalent).
  B. THE SWARM WRITES THE BOARD: running on a TEMP blackboard writes signals + observations + gaps + a synthesis
     (and the entity-resolution analysis); the run envelope's serves_truth is False; every entry serves_truth False.
  C. EVERY WORKER WROTE A RECEIPT: all six workers fire; each worker result carries a receipt_id; the board's
     receipt set covers every worker kind (planner/extractor/gap_detector/entity_resolver/synthesizer/governor).
  D. OBSERVATIONS CARRY SOURCE_REFS: every observation on the board has non-empty source_refs (source-backed).
  E. SYNTHESIS READS THE BOARD: the synthesis worker's read_entry_ids + the synthesis body's supporting_entry_ids
     are REAL blackboard entry_ids (it consumed board entries, not raw docs); supporting set is non-empty.
  F. DETERMINISTIC: the same (fixture, now) yields the SAME blackboard_id + the SAME entry_ids + the SAME synthesis.
  G. NO BALTOR IMPORT / NO RAW KEYS: the teleon swarm/port modules do not import src.baltor (line-anchored) and
     contain no raw API key literals; no live-LLM call symbol is referenced.

Deterministic + offline. stdlib only. Uses an in-memory / TEMP sqlite blackboard, never the real .agent db.
Exit 0/1. _REPO = parents[1]; sys.path.insert. No raw keys/secrets.

CLI: PYTHONPATH=. python3 scripts/check_stateful_swarm_local_stub.py --self-test
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.teleon.blackboard.local_sqlite_blackboard import LocalSqliteBlackboard  # noqa: E402
from src.teleon.ports.blackboard_provider import (  # noqa: E402
    KIND_ANALYSIS,
    KIND_GAP,
    KIND_OBSERVATION,
    KIND_SIGNAL,
    KIND_SYNTHESIS,
)
from src.teleon.ports.stateful_swarm_provider import (  # noqa: E402
    SWARM_SERVES_TRUTH,
    StatefulSwarmProviderPort,
    SwarmWorkerResult,
)
from src.teleon.stateful_swarms.local_swarm import (  # noqa: E402
    LOCAL_SWARM_PROVIDER_ID,
    SWARM_WORKER_ORDER,
    LocalStatefulSwarm,
)

_NOW = "2026-06-08T00:00:00Z"
_TENANT = "tenant-demo"

# teleon modules that must NOT import src.baltor and must carry no raw keys.
_TELEON_FILES = [
    _REPO / "src" / "teleon" / "ports" / "stateful_swarm_provider.py",
    _REPO / "src" / "teleon" / "stateful_swarms" / "__init__.py",
    _REPO / "src" / "teleon" / "stateful_swarms" / "local_swarm.py",
    _REPO / "src" / "teleon" / "stateful_swarms" / "cfpb_evidence_demo.py",
]

# crude raw-key detectors (provider key prefixes); env:// refs / the word in prose are fine.
_KEY_PATTERNS = [
    re.compile(p)
    for p in (r"sk-[A-Za-z0-9]{16,}", r"AKIA[0-9A-Z]{12,}", r"AIza[0-9A-Za-z_\-]{20,}", r"gsk_[A-Za-z0-9]{16,}")
]
# a line that imports src.baltor in any of its forms (relative or absolute, import or from-import).
_BALTOR_IMPORT = re.compile(r"^\s*(from|import)\s+.*\bbaltor\b", re.MULTILINE)


def _run_on_temp(now: str = _NOW) -> tuple[LocalSqliteBlackboard, str, dict, LocalStatefulSwarm]:
    """Create a fresh in-memory blackboard, run the swarm on it, return (bb, blackboard_id, envelope, swarm)."""
    bb = LocalSqliteBlackboard(db_path=":memory:")
    board = bb.create_blackboard(task="What is the effective resolution deadline?", tenant_scope=_TENANT, now=now)
    bid = board["blackboard_id"]
    swarm = LocalStatefulSwarm(blackboard=bb)
    env = swarm.run("What is the effective resolution deadline?", blackboard_id=bid, now=now)
    return bb, bid, env, swarm


def _self_test() -> int:
    fails: list[str] = []

    def check(n: str, ok: bool, d: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok:
            fails.append(n)

    # ── A. PORT CONTRACT ──────────────────────────────────────────────────────────────────
    swarm = LocalStatefulSwarm()
    check("A1 StatefulSwarmProviderPort runtime_checkable satisfied", isinstance(swarm, StatefulSwarmProviderPort))
    check("A2 provider_id is the active local stub", swarm.provider_id == LOCAL_SWARM_PROVIDER_ID,
          swarm.provider_id)
    card = swarm.describe()
    check("A3 describe() local-first golden-path card",
          card.get("requires_network") is False and card.get("requires_keys") is False
          and card.get("serves_truth") is False and card.get("local_equivalent") == LOCAL_SWARM_PROVIDER_ID,
          str(card))
    check("A4 SWARM_SERVES_TRUTH constant is False", SWARM_SERVES_TRUTH is False)

    # ── B. THE SWARM WRITES THE BOARD ───────────────────────────────────────────────────────
    bb, bid, env, _ = _run_on_temp()
    signals = bb.query(bid, kind=KIND_SIGNAL)
    observations = bb.query(bid, kind=KIND_OBSERVATION)
    gaps = bb.query(bid, kind=KIND_GAP)
    synthesis = bb.query(bid, kind=KIND_SYNTHESIS)
    analyses = bb.query(bid, kind=KIND_ANALYSIS)
    check("B1 signals written", len(signals) >= 1, f"{len(signals)}")
    check("B2 observations written", len(observations) >= 1, f"{len(observations)}")
    check("B3 gaps written", len(gaps) >= 1, f"{len(gaps)}")
    check("B4 synthesis written", len(synthesis) == 1, f"{len(synthesis)}")
    check("B5 entity-resolution analysis written", len(analyses) >= 1, f"{len(analyses)}")
    check("B6 run envelope serves_truth False", env["serves_truth"] is False)
    all_entries = bb.query(bid)
    check("B7 EVERY stored entry serves_truth False", all(e["serves_truth"] is False for e in all_entries))
    check("B8 run envelope provider_id is the active stub", env["provider_id"] == LOCAL_SWARM_PROVIDER_ID)

    # ── C. EVERY WORKER WROTE A RECEIPT ─────────────────────────────────────────────────────
    results: list[SwarmWorkerResult] = env["worker_results"]
    check("C1 all six workers fired", len(results) == 6 and tuple(r.worker_id for r in results) == SWARM_WORKER_ORDER,
          str([r.worker_id for r in results]))
    check("C2 every worker result carries a receipt_id", all(r.receipt_id for r in results))
    check("C3 every worker result serves_truth False", all(r.serves_truth is False for r in results))
    receipts = bb.get_receipts(bid)
    receipt_worker_kinds = {r["worker_kind"] for r in receipts}
    expected_kinds = {"planner", "extractor", "gap_detector", "entity_resolver", "synthesizer", "governor"}
    check("C4 board receipts cover every worker kind", expected_kinds <= receipt_worker_kinds,
          f"{sorted(receipt_worker_kinds)}")
    check("C5 every stored entry references a receipt", all(e["receipt_id"] for e in all_entries))

    # ── D. OBSERVATIONS CARRY SOURCE_REFS ───────────────────────────────────────────────────
    check("D1 every observation has non-empty source_refs",
          all(len(o["source_refs"]) >= 1 for o in observations) and len(observations) >= 1)
    check("D2 every observation body carries source_refs",
          all(len(o["body"].get("source_refs", [])) >= 1 for o in observations))

    # ── E. SYNTHESIS READS THE BOARD ────────────────────────────────────────────────────────
    synth_result = next(r for r in results if r.worker_id == "synthesis")
    board_entry_ids = {e["entry_id"] for e in all_entries}
    check("E1 synthesis worker read_entry_ids are REAL board entry_ids",
          len(synth_result.read_entry_ids) >= 1 and set(synth_result.read_entry_ids) <= board_entry_ids)
    synth_body = synthesis[0]["body"]
    supporting = synth_body.get("supporting_entry_ids", [])
    check("E2 synthesis supporting_entry_ids are REAL board entry_ids (read the board, not raw docs)",
          len(supporting) >= 1 and set(supporting) <= board_entry_ids, f"{supporting}")
    # the supporting ids must include observation ids (it consolidated the source-backed observations).
    obs_ids = {o["entry_id"] for o in observations}
    check("E3 synthesis consolidates the observations on the board", bool(obs_ids & set(supporting)))
    check("E4 synthesis body serves_truth False", synth_body.get("serves_truth") is False)

    # ── F. DETERMINISTIC ────────────────────────────────────────────────────────────────────
    bb1, bid1, env1, _ = _run_on_temp()
    bb2, bid2, env2, _ = _run_on_temp()
    check("F1 same now -> same blackboard_id", bid1 == bid2, f"{bid1} vs {bid2}")
    ids1 = [e["entry_id"] for e in bb1.query(bid1)]
    ids2 = [e["entry_id"] for e in bb2.query(bid2)]
    check("F2 same now -> same entry_ids in the same order", ids1 == ids2)
    s1 = bb1.query(bid1, kind=KIND_SYNTHESIS)[0]
    s2 = bb2.query(bid2, kind=KIND_SYNTHESIS)[0]
    check("F3 same now -> same synthesis entry_id + answer",
          s1["entry_id"] == s2["entry_id"] and s1["body"]["answer"] == s2["body"]["answer"])

    # ── G. NO BALTOR IMPORT / NO RAW KEYS ───────────────────────────────────────────────────
    baltor_hits: list[str] = []
    key_hits: list[str] = []
    llm_hits: list[str] = []
    for f in _TELEON_FILES:
        src = f.read_text()
        if _BALTOR_IMPORT.search(src):
            baltor_hits.append(f.name)
        for pat in _KEY_PATTERNS:
            if pat.search(src):
                key_hits.append(f.name)
        # a live-LLM call symbol would betray a non-deterministic / network path in a deterministic stub.
        for bad in ("openai.", "anthropic.", "requests.", "urllib.request.urlopen", "httpx."):
            if bad in src:
                llm_hits.append(f"{f.name}:{bad}")
    check("G1 no teleon swarm/port module imports src.baltor (line-anchored)", not baltor_hits, str(baltor_hits))
    check("G2 no raw API key literal in any teleon swarm/port module", not key_hits, str(key_hits))
    check("G3 no live-LLM / network call symbol in any teleon swarm/port module", not llm_hits, str(llm_hits))

    if fails:
        print(f"\ncheck_stateful_swarm_local_stub: FAIL ({len(fails)} failed)")
        return 1
    print("\nPASS — check_stateful_swarm_local_stub: port satisfied; swarm writes signals+observations+gaps+synthesis "
          "on a temp blackboard; all 6 workers wrote receipts; observations source-backed; synthesis reads the BOARD "
          "(supporting/read entry_ids are real); deterministic (same now -> same ids); no src.baltor import; no raw keys.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="offline self-test for the local stateful-swarm runner")
    ap.add_argument("--self-test", action="store_true", help="run the offline self-test (default)")
    ap.parse_args()
    return _self_test()


if __name__ == "__main__":
    raise SystemExit(main())
