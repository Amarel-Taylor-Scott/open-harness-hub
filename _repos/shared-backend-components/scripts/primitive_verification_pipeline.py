#!/usr/bin/env python3
"""scripts.primitive_verification_pipeline — the scalable path from millions of CANDIDATES to millions of
VERIFIED primitives. Truly proving 20M primitives correct one-LLM-call-at-a-time is bandwidth-bound; this
pipeline tiers verification so most primitives reach a verified level at DETERMINISTIC speed (no LLM per card),
and only the top tier needs execution/LLM:

  * L3 EXECUTION   — the primitive is code with a PASSING oracle test (executable pool). Truly verified-correct.
  * L2 SOURCE      — the primitive traces to a real source/corpus (verified_factory / edge / kaggle / enriched).
  * L1 STRUCTURAL  — passes the deterministic usefulness gate (not placeholder) + typed CamelCase edges +
                     carries >= 2 concept tokens. Verified-USEFUL (composable, non-vacuous), scalable to 20M.
  * L0 CANDIDATE   — placeholder/weak: routed to enrichment, NEVER discarded (owner law).

"Verified" = level >= L1. The pipeline reads the SQLite primitive database, computes each row's level with pure
functions (reusing primitive_usefulness_gate), writes a verification_level column, and reports the distribution
— so "how many verified" is a MEASURED number, and verifying 20M is a deterministic O(n) pass, not 20M LLM
calls. serves_truth=false (this labels verification LEVEL; only L3/L2 approach served truth, still funnel-gated).

    python3 scripts/primitive_verification_pipeline.py --self-test
    python3 scripts/primitive_verification_pipeline.py --run [--limit N]     # tier the primitive database
"""
from __future__ import annotations

import sys
from pathlib import Path

_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots, resource  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import json  # noqa: E402
import re  # noqa: E402
import sqlite3  # noqa: E402
from typing import Any, Optional  # noqa: E402

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
_CAMEL = re.compile(r"^[A-Z][A-Za-z0-9]*$")
_EXECUTION_POOLS = frozenset({"executable"})
_SOURCE_POOLS = frozenset({"verified_factory", "primitive_edge", "kaggle", "enriched"})
#: `integration` is the TOP level (above execution): a LARGE / multi-file primitive whose contract is an SLA
#: over a running system cannot be certified by a unit oracle — it is certified by a passing EXECUTED
#: integration run. A card reaches it only by referencing a `buildout_run_receipt` with `oracle_pass=True`
#: (open-problems gap 2.3: proving a large primitive scales with size). Ordered lowest→highest.
LEVELS = ("candidate", "structural", "source", "execution", "integration")
INTEGRATION_RECEIPT_TYPE = "buildout_run_receipt"


def _passing_integration_receipt(card: dict[str, Any],
                                 receipts_by_id: Optional[dict[str, Any]] = None) -> bool:
    """True iff the card carries (inline) or references (by id, resolved via receipts_by_id) a
    buildout_run_receipt with oracle_pass=True — an EXECUTED integration certificate."""
    inline = card.get("integration_receipt")
    if isinstance(inline, dict) and inline.get("record_type") == INTEGRATION_RECEIPT_TYPE \
            and inline.get("oracle_pass") is True:
        return True
    ref = card.get("buildout_run_receipt_ref")
    if ref and receipts_by_id:
        receipt = receipts_by_id.get(ref)
        if isinstance(receipt, dict) and receipt.get("record_type") == INTEGRATION_RECEIPT_TYPE \
                and receipt.get("oracle_pass") is True:
            return True
    return False


def verify_card(card: dict[str, Any], receipts_by_id: Optional[dict[str, Any]] = None) -> str:
    """The level for a full card dict: `integration` if it carries a passing buildout_run_receipt, else the
    deterministic per-row level (verify_row over its fields). Keeps verify_row unchanged (backward-compatible)."""
    if _passing_integration_receipt(card, receipts_by_id):
        return "integration"
    return verify_row(str(card.get("pool") or ""), str(card.get("title") or ""),
                      str(card.get("blackbox") or ""),
                      " ".join(card.get("capability_tags") or []) if isinstance(card.get("capability_tags"), list)
                      else str(card.get("tags") or ""),
                      str(card.get("input_edge") or ""), str(card.get("output_edge") or ""))


def verify_row(pool: str, title: str, blackbox: str, tags: str, input_edge: str, output_edge: str) -> str:
    """Deterministic verification LEVEL for one primitive (pure function; scalable to 20M)."""
    if pool in _EXECUTION_POOLS:
        return "execution"
    if pool in _SOURCE_POOLS:
        return "source"
    # L1 structural: not a placeholder (reuse the usefulness gate) + typed edges + concept tokens
    from scripts.primitive_usefulness_gate import evaluate_card  # noqa: PLC0415
    card = {"title": title, "blackbox": blackbox, "input_edge": input_edge, "output_edge": output_edge,
            "capability_tags": tags.split()}
    verdict = evaluate_card(card)["verdict"]
    typed = bool(_CAMEL.match(input_edge or "")) and bool(_CAMEL.match(output_edge or ""))
    tokens = [t for t in re.findall(r"[a-z0-9]+", (title + " " + blackbox).lower()) if len(t) > 3]
    if verdict != "placeholder" and typed and len(set(tokens)) >= 2:
        return "structural"
    return "candidate"


def run_pipeline(db_path: Optional[Path] = None, *, limit: Optional[int] = None) -> dict[str, Any]:
    from scripts.primitive_database import default_db_path  # noqa: PLC0415
    db_path = db_path or default_db_path()
    if not db_path.exists():
        return {"error": f"database not built: {db_path} (run primitive_database.py --build)", **BOUNDARY}
    con = sqlite3.connect(str(db_path))
    con.execute("PRAGMA journal_mode=WAL")
    cols = {r[1] for r in con.execute("PRAGMA table_info(primitives)")}
    if "verification_level" not in cols:
        con.execute("ALTER TABLE primitives ADD COLUMN verification_level TEXT")
        con.commit()
    dist: dict[str, int] = {lvl: 0 for lvl in LEVELS}
    by_pool_verified: dict[str, int] = {}
    sql = "SELECT rowid, pool, title, blackbox, tags, input_edge, output_edge FROM primitives"
    if limit:
        sql += f" LIMIT {int(limit)}"
    updates: list[tuple] = []
    n = 0
    for rowid, pool, title, blackbox, tags, ie, oe in con.execute(sql):
        lvl = verify_row(pool or "", title or "", blackbox or "", tags or "", ie or "", oe or "")
        dist[lvl] += 1
        if lvl != "candidate":
            by_pool_verified[pool] = by_pool_verified.get(pool, 0) + 1
        updates.append((lvl, rowid))
        n += 1
        if len(updates) >= 10000:
            con.executemany("UPDATE primitives SET verification_level=? WHERE rowid=?", updates)
            con.commit()
            updates.clear()
    if updates:
        con.executemany("UPDATE primitives SET verification_level=? WHERE rowid=?", updates)
        con.commit()
    con.close()
    verified = dist["structural"] + dist["source"] + dist["execution"] + dist["integration"]
    return {"record_type": "primitive_verification_receipt", "n_scored": n,
            "level_distribution": dist,
            "verified_total": verified, "verified_fraction": round(verified / max(1, n), 4),
            "verified_by_pool": dict(sorted(by_pool_verified.items(), key=lambda kv: -kv[1])),
            "note": "verified = level >= structural; execution+source approach served truth (still funnel-gated); "
                    "structural = verified-USEFUL (deterministic, scalable). Candidates route to enrichment, never discarded.",
            **BOUNDARY}


def _self_test() -> int:
    import tempfile  # noqa: PLC0415
    checks: list[tuple[str, bool]] = []
    # per-row verification tiers
    checks.append(("executable pool -> execution-verified",
                   verify_row("executable", "kadane max subarray", "Kadane running max via O(n) DP", "tier:rare", "In", "Out") == "execution"))
    checks.append(("verified_factory pool -> source-verified",
                   verify_row("verified_factory", "topological sort", "Kahn cycle-detect", "", "Nodes", "Ordered") == "source"))
    checks.append(("a concrete generated card -> structural-verified",
                   verify_row("grid", "Parse shipments with balanced tree over a CDC pipeline",
                              "uses a balanced tree structure to parse supply-chain shipments over a CDC pipeline",
                              "op:parse", "LogisticsInput", "ParseResult") == "structural"))
    checks.append(("a placeholder card stays candidate (routes to enrichment)",
                   verify_row("minted_gap", "X", "Calls X with Y and returns Z.", "", "In", "Out") == "candidate"))
    checks.append(("a card with generic edges is NOT structurally verified",
                   verify_row("grid", "some title here now", "a real mechanism sentence with tokens", "", "in", "out") == "candidate"))

    # integration level (gap 2.3): a large primitive is certified by a PASSING executed integration run, not a
    # unit oracle. It reaches `integration` ONLY via a buildout_run_receipt with oracle_pass=True.
    passing_receipt = {"record_type": INTEGRATION_RECEIPT_TYPE, "genome_id": "g1", "oracle_pass": True}
    failing_receipt = {"record_type": INTEGRATION_RECEIPT_TYPE, "genome_id": "g2", "oracle_pass": False}
    big_card = {"pool": "grid", "title": "A 100K-line service primitive", "blackbox": "a whole deployable service",
                "input_edge": "ClusterConfig", "output_edge": "ServedApi"}
    checks.append(("a large primitive with a PASSING buildout_run_receipt reaches `integration` (the top level)",
                   verify_card({**big_card, "integration_receipt": passing_receipt}) == "integration"))
    checks.append(("mutation: a FAILING integration receipt does NOT grant `integration` (falls to its base "
                   "level) — the certificate must actually pass",
                   verify_card({**big_card, "integration_receipt": failing_receipt}) != "integration"))
    checks.append(("integration by REFERENCE resolves through a receipts index; a dangling ref does not certify",
                   verify_card({**big_card, "buildout_run_receipt_ref": "r1"}, {"r1": passing_receipt}) == "integration"
                   and verify_card({**big_card, "buildout_run_receipt_ref": "missing"}, {"r1": passing_receipt})
                   != "integration"))
    checks.append(("`integration` is the top of the ordered LEVELS ladder",
                   LEVELS[-1] == "integration" and LEVELS.index("integration") > LEVELS.index("execution")))

    # end-to-end over a fixture DB
    with tempfile.TemporaryDirectory() as td:
        db = Path(td) / "primitives.db"
        con = sqlite3.connect(str(db))
        con.execute("""CREATE TABLE primitives(primitive_id TEXT PRIMARY KEY, pool TEXT, title TEXT,
            blackbox TEXT, tags TEXT, input_edge TEXT, output_edge TEXT, serves_truth INTEGER)""")
        rows = [("e1", "executable", "kadane", "Kadane O(n) running max DP", "", "Xs", "Best", 0),
                ("s1", "verified_factory", "toposort", "Kahn cycle detect", "", "Nodes", "Ordered", 0),
                ("g1", "grid", "Index invoices with an inverted index over postgres",
                 "uses an inverted index to index invoices over postgres with tfidf postings", "op:index", "InvoiceInput", "IndexResult", 0),
                ("p1", "minted_gap", "z", "Calls z with a and returns b.", "", "In", "Out", 0)]
        con.executemany("INSERT INTO primitives VALUES(?,?,?,?,?,?,?,?)", rows)
        con.commit(); con.close()
        rec = run_pipeline(db_path=db)
        checks.append(("pipeline tiers the DB: 1 execution + 1 source + 1 structural + 1 candidate "
                       "(+ 0 integration — the DB path has no receipt column yet)",
                       rec["level_distribution"] == {"candidate": 1, "structural": 1, "source": 1,
                                                     "execution": 1, "integration": 0}
                       and rec["verified_total"] == 3 and rec["verified_fraction"] == 0.75))
        # idempotent + the column persists
        rec2 = run_pipeline(db_path=db)
        checks.append(("verification is idempotent (same distribution, column persisted)",
                       rec2["level_distribution"] == rec["level_distribution"]))
        con = sqlite3.connect(str(db))
        levels = dict(con.execute("SELECT primitive_id, verification_level FROM primitives"))
        con.close()
        checks.append(("levels are written back to the database rows",
                       levels["e1"] == "execution" and levels["p1"] == "candidate"))
    checks.append(("receipts carry the boundary",
                   run_pipeline(db_path=Path("/nonexistent/primitives.db")).get("serves_truth") is False))

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print("\nPASS - primitive_verification_pipeline: deterministic per-row verification tiers (execution / source "
          "/ structural / candidate), written back to the primitive database; 'verified' (>= structural) is a "
          "MEASURED, scalable-to-20M number computed without an LLM per card; candidates route to enrichment, "
          "never discarded. serves_truth=false.")
    return 0


def _run(limit: Optional[int]) -> int:
    rec = run_pipeline(limit=limit)
    out = resource("data") / "dev-intel" / "session_emulation" / "primitive_verification_receipt.json"
    out.write_text(json.dumps(rec, indent=2, sort_keys=True))
    print(json.dumps({k: rec.get(k) for k in ("n_scored", "level_distribution", "verified_total",
                                              "verified_fraction", "verified_by_pool")}, indent=2, sort_keys=True))
    print(f"\nreceipt: {out}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.run:
        return _run(args.limit)
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
