#!/usr/bin/env python3
"""scripts.check_local_blackboard_provider — PROOF (P2): the local SQLite blackboard provider is real, offline,
deterministic, append-only, source-backed, tenant-isolated, and governed (never serves truth).

A blackboard is the durable, typed analytical STATE substrate where bounded workers post typed entries across
iterations instead of re-reading docs. Teleon RUNS it; Baltor governs what (if anything) becomes truth. A
blackboard entry is WORKING STATE — never served truth.

Asserts:
  A. PORT CONTRACT: BlackboardProviderPort is runtime_checkable; LocalSqliteBlackboard satisfies it (provider_id
     + create_blackboard / append_entry / query / get_receipts); describe() card is local-first (append_only,
     no network, serves_truth False, is its own local_equivalent).
  B. APPEND-ONLY: a content-identical second append of the SAME entry is idempotent (same entry_id, no new row);
     a re-write of the same entry_id with DIFFERENT content raises BlackboardWriteRejected (append_only_violation)
     — there is no update/delete.
  C. SOURCE-BACKED: an observation with NO source_refs is REJECTED (sourceless_observation); an observation WITH
     a source_ref is accepted.
  D. NEVER TRUTH: an entry that sets serves_truth=true is REJECTED (serves_truth_forbidden); every STORED entry
     has serves_truth False; BLACKBOARD_SERVES_TRUTH is False.
  E. TENANT-ISOLATED + RECEIPTED: create/append with no tenant_scope is REJECTED (missing_tenant_scope); an append
     with no worker_receipt is REJECTED (missing_receipt); every stored entry has a recorded worker_receipt.
  F. DETERMINISTIC QUERY: the same (db contents, now) yields the SAME query order + ids; query filters narrow
     deterministically; the seed helper builds the documented 3-entry (signal/observation/gap) shape.
  G. NO BALTOR IMPORT / NO RAW KEYS: the teleon blackboard/port modules do not import src.baltor (line-anchored)
     and contain no raw API key literals.

Deterministic + offline. stdlib only. Uses a TEMP sqlite db (tempfile), never the real .agent db. Exit 0/1.
_REPO = parents[1]; sys.path.insert. No raw keys/secrets.
"""
from __future__ import annotations

import re
import sys
import tempfile
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.teleon.blackboard.local_sqlite_blackboard import (  # noqa: E402
    LOCAL_SQLITE_BLACKBOARD_PROVIDER_ID,
    LocalSqliteBlackboard,
    seed_demo_blackboard,
)
from src.teleon.ports.blackboard_provider import (  # noqa: E402
    BLACKBOARD_SERVES_TRUTH,
    KIND_GAP,
    KIND_OBSERVATION,
    KIND_SIGNAL,
    BlackboardProviderPort,
    BlackboardWriteRejected,
)

_NOW = "2026-01-01T00:00:00Z"
_TENANT = "tenant-demo"

# teleon modules that must NOT import src.baltor and must carry no raw keys.
_TELEON_FILES = [
    _REPO / "src" / "teleon" / "ports" / "blackboard_provider.py",
    _REPO / "src" / "teleon" / "blackboard" / "__init__.py",
    _REPO / "src" / "teleon" / "blackboard" / "local_sqlite_blackboard.py",
]

# crude raw-key detectors (provider key prefixes); env:// refs / the word in prose are fine.
_KEY_PATTERNS = [re.compile(p) for p in (r"sk-[A-Za-z0-9]{16,}", r"AKIA[0-9A-Z]{12,}", r"AIza[0-9A-Za-z_\-]{20,}")]


def _receipt(worker_id: str = "worker.test", worker_kind: str = "tester") -> dict:
    return {"worker_id": worker_id, "worker_kind": worker_kind, "started_at": _NOW, "completed_at": _NOW}


def _observation(source_refs: list[str], *, statement: str = "the date is 2026-04-15") -> dict:
    return {
        "kind": KIND_OBSERVATION,
        "author_worker_id": "worker.observer",
        "iteration": 1,
        "tenant_scope": _TENANT,
        "source_refs": source_refs,
        "body": {"statement": statement, "source_refs": source_refs, "confidence": 0.9},
    }


def _self_test() -> int:
    fails: list[str] = []

    def check(n: str, ok: bool, d: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok:
            fails.append(n)

    def rejected_with(fn, code: str) -> tuple[bool, str]:
        """Run ``fn``; return (True, code) if it raised BlackboardWriteRejected with ``code``, else (False, why)."""
        try:
            fn()
        except BlackboardWriteRejected as e:
            return (e.code == code, f"raised {e.code!r}")
        except Exception as e:  # noqa: BLE001 — any other exception is a failure of the guard
            return (False, f"raised non-governance {type(e).__name__}: {e}")
        return (False, "did not raise")

    with tempfile.TemporaryDirectory() as tmp:
        db_path = str(Path(tmp) / "blackboard.test.db")
        bb = LocalSqliteBlackboard(db_path=db_path)  # TEMP db — never the real .agent db

        # ---- A. port contract -----------------------------------------------------------
        check("A: BlackboardProviderPort is runtime_checkable + LocalSqliteBlackboard satisfies it",
              isinstance(bb, BlackboardProviderPort))
        check("A: provider exposes provider_id + create/append/query/get_receipts",
              bb.provider_id == LOCAL_SQLITE_BLACKBOARD_PROVIDER_ID
              and callable(bb.create_blackboard) and callable(bb.append_entry)
              and callable(bb.query) and callable(bb.get_receipts))
        card = bb.describe()
        for key in ("provider_id", "name", "status", "append_only", "requires_network", "local_equivalent", "serves_truth"):
            check(f"A: describe() card has key {key!r}", key in card)
        check("A: card is local-first (append_only, no network) + is its own local_equivalent",
              card.get("append_only") is True and card.get("requires_network") is False
              and card.get("local_equivalent") == LOCAL_SQLITE_BLACKBOARD_PROVIDER_ID)
        check("A: card serves_truth is False", card.get("serves_truth") is False)

        board = bb.create_blackboard(task="effective date?", tenant_scope=_TENANT, now=_NOW)
        bid = board["blackboard_id"]
        check("A: created blackboard is born status=open, entry_count=0",
              board["status"] == "open" and board["entry_count"] == 0)

        # ---- B. append-only --------------------------------------------------------------
        src_ref = "src.x"
        e1 = bb.append_entry(bid, _observation([src_ref]), worker_receipt=_receipt(), now=_NOW)
        e1_dup = bb.append_entry(bid, _observation([src_ref]), worker_receipt=_receipt(), now=_NOW)
        check("B: identical re-append is idempotent (same entry_id)", e1["entry_id"] == e1_dup["entry_id"])
        check("B: identical re-append adds no new row (entry_count stable)",
              len(bb.query(bid, kind=KIND_OBSERVATION)) == 1, f"got {len(bb.query(bid, kind=KIND_OBSERVATION))}")
        # a re-write of the SAME entry_id with DIFFERENT content must be rejected (no update/delete).
        mutated = _observation([src_ref], statement="a DIFFERENT statement")
        mutated["entry_id"] = e1["entry_id"]  # force a collision on the existing id
        ok, why = rejected_with(
            lambda: bb.append_entry(bid, mutated, worker_receipt=_receipt(), now=_NOW),
            BlackboardWriteRejected.APPEND_ONLY_VIOLATION,
        )
        check("B: mutate of an existing entry_id raises append_only_violation (no update/delete)", ok, why)

        # ---- C. source-backed ------------------------------------------------------------
        ok, why = rejected_with(
            lambda: bb.append_entry(bid, _observation([]), worker_receipt=_receipt(), now=_NOW),
            BlackboardWriteRejected.SOURCELESS_OBSERVATION,
        )
        check("C: an observation with NO source_refs is rejected (sourceless_observation)", ok, why)
        obs_ok = bb.append_entry(bid, _observation(["src.y"], statement="sourced claim"),
                                 worker_receipt=_receipt(), now=_NOW)
        check("C: an observation WITH a source_ref is accepted", obs_ok["source_refs"] == ["src.y"])

        # ---- D. never truth --------------------------------------------------------------
        truthy = _observation([src_ref])
        truthy["serves_truth"] = True
        ok, why = rejected_with(
            lambda: bb.append_entry(bid, truthy, worker_receipt=_receipt(), now=_NOW),
            BlackboardWriteRejected.SERVES_TRUTH_FORBIDDEN,
        )
        check("D: an entry with serves_truth=true is rejected (serves_truth_forbidden)", ok, why)
        all_entries = bb.query(bid)
        check("D: every STORED entry has serves_truth False",
              all(e["serves_truth"] is False for e in all_entries) and len(all_entries) >= 1)
        check("D: BLACKBOARD_SERVES_TRUTH constant is False", BLACKBOARD_SERVES_TRUTH is False)

        # ---- E. tenant-isolated + receipted ----------------------------------------------
        ok, why = rejected_with(
            lambda: bb.create_blackboard(task="t", tenant_scope="", now=_NOW),
            BlackboardWriteRejected.MISSING_TENANT_SCOPE,
        )
        check("E: create_blackboard with empty tenant_scope is rejected (missing_tenant_scope)", ok, why)
        no_tenant = _observation([src_ref])
        no_tenant["tenant_scope"] = ""
        ok, why = rejected_with(
            lambda: bb.append_entry(bid, no_tenant, worker_receipt=_receipt(), now=_NOW),
            BlackboardWriteRejected.MISSING_TENANT_SCOPE,
        )
        check("E: append with empty tenant_scope is rejected (missing_tenant_scope)", ok, why)
        ok, why = rejected_with(
            lambda: bb.append_entry(bid, _observation([src_ref]), worker_receipt={}, now=_NOW),
            BlackboardWriteRejected.MISSING_RECEIPT,
        )
        check("E: append with no worker_receipt is rejected (missing_receipt)", ok, why)
        check("E: every stored entry references a recorded worker_receipt",
              all(e.get("receipt_id") for e in all_entries))
        receipt_ids = {r["receipt_id"] for r in bb.get_receipts(bid)}
        check("E: each stored entry's receipt_id is present in get_receipts() (provenance recorded)",
              all(e["receipt_id"] in receipt_ids for e in all_entries))
        check("E: recorded receipts carry worker_id + entries_written lineage",
              all(r.get("worker_id") and "entries_written" in r for r in bb.get_receipts(bid)))

        # ---- F. deterministic query ------------------------------------------------------
        order_1 = [e["entry_id"] for e in bb.query(bid)]
        order_2 = [e["entry_id"] for e in bb.query(bid)]
        check("F: query is stable on the same db (same order + ids)", order_1 == order_2)
        # a fresh store seeded with the SAME (db, now) reproduces the SAME ids (deterministic, content-addressed).
        with tempfile.TemporaryDirectory() as tmp2, tempfile.TemporaryDirectory() as tmp3:
            seeded_a = seed_demo_blackboard(db_path=str(Path(tmp2) / "seed.db"), now=_NOW, tenant_scope=_TENANT)
            seeded_b = seed_demo_blackboard(db_path=str(Path(tmp3) / "seed.db"), now=_NOW, tenant_scope=_TENANT)
            pa, pb = seeded_a["provider"], seeded_b["provider"]
            ids_a = [e["entry_id"] for e in pa.query(seeded_a["blackboard_id"])]
            ids_b = [e["entry_id"] for e in pb.query(seeded_b["blackboard_id"])]
            check("F: same (db, now) seed -> identical blackboard_id",
                  seeded_a["blackboard_id"] == seeded_b["blackboard_id"])
            check("F: same (db, now) seed -> identical entry order + ids (deterministic)", ids_a == ids_b)
            kinds = [e["kind"] for e in pa.query(seeded_a["blackboard_id"])]
            check("F: seed helper builds a signal + observation + gap (the documented 3-entry shape)",
                  KIND_SIGNAL in kinds and KIND_OBSERVATION in kinds and KIND_GAP in kinds)
            obs_only = pa.query(seeded_a["blackboard_id"], kind=KIND_OBSERVATION)
            check("F: query(kind=observation) filters deterministically",
                  len(obs_only) == 1 and obs_only[0]["kind"] == KIND_OBSERVATION)
            check("F: every seeded observation is source-backed (non-empty source_refs)",
                  all(len(e["source_refs"]) >= 1 for e in obs_only))
            pa.close()
            pb.close()
        bb.close()

    # ---- G. no baltor import / no raw keys ----------------------------------------------
    # Match a real IMPORT STATEMENT (line-start, optional indent) — NOT prose that names the rule
    # ("never imports Baltor" in a docstring is the invariant being documented, not a violation).
    baltor_import = re.compile(r"^[ \t]*(?:import|from)[ \t]+src\.baltor\b", re.MULTILINE)
    for f in _TELEON_FILES:
        text = f.read_text()
        check(f"G: {f.name} does not import src.baltor", not baltor_import.search(text))
        leaked = [p.pattern for p in _KEY_PATTERNS if p.search(text)]
        check(f"G: {f.name} contains no raw API key literal", not leaked, f"matched {leaked}")

    print("\n" + ("PASS — check_local_blackboard_provider: the local SQLite blackboard is APPEND-ONLY (identical "
                  "re-append idempotent; a content-different re-write of an entry_id raises append_only_violation; "
                  "no update/delete), SOURCE-BACKED (a sourceless observation is rejected), NEVER TRUTH "
                  "(serves_truth=true rejected; every stored entry serves_truth False), TENANT-ISOLATED + "
                  "RECEIPTED (missing tenant_scope / missing worker_receipt rejected; every entry carries a "
                  "recorded receipt), and DETERMINISTIC (same db+now -> same query order/ids). No src.baltor "
                  "import; no raw keys."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_local_blackboard_provider.py --self-test")
    raise SystemExit(0)
