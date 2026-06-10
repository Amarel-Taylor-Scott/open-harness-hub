#!/usr/bin/env python3
"""scripts.check_multi_source_regression — proof (MULTI-SOURCE REGRESSION): runs EVERY row of
architecture/multi_source_run_matrix.json through scripts.runtime.source_consumption.run_source_to_consumption
and asserts each source TYPE matches its expected consumption_status.

Contract enforced per row:
  * a CONSUMABLE row (api / generic json / csv / webhook) produces a schema-valid SERVED ContextResponse whose
    served facts carry source handles; narrative allegations (if any) are held out, NEVER served as truth;
  * a CANDIDATE row (html / pdf — parser unavailable) produces consumable:false + a non_consumable_reason and is
    NEVER served as fact (no faked response);
  * no tenant_private source leaks a fact into a global/public handle;
  * the whole matrix is deterministic (a second run is byte-identical).

The proof prints a per-source status table. If any source regressed (served what should be held out, faked a
response for an unparseable source, or leaked a private handle) the matching row turns red.

CLI: python3 scripts/check_multi_source_regression.py --self-test
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from scripts.runtime.schema_validator import validate_ref
from scripts.runtime.source_consumption import run_source_to_consumption

_REPO = Path(__file__).resolve().parents[1]
_MATRIX = _REPO / "architecture" / "multi_source_run_matrix.json"
NOW = "2026-06-05T00:00:00Z"


def _run_row(row: dict) -> dict:
    return run_source_to_consumption(row["source_type"], row["payload"], tenant_id=row["tenant_id"],
                                     source_id=row["source_id"], scope=row.get("scope", "global_public"),
                                     authority=row.get("authority", "unknown"), now=NOW)


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        if not ok:
            fails.append(name)
        return ok

    matrix = json.loads(_MATRIX.read_text(encoding="utf-8"))
    rows = matrix["rows"]
    table: list[tuple] = []

    for row in rows:
        rid = row["row_id"]
        res = _run_row(row)
        summary = res["summary"]
        actual = summary["consumption_status"]
        expected = row["expected_consumption_status"]
        row_ok = True

        # status matches the matrix expectation
        if not check(f"{rid}: consumption_status == {expected!r} (got {actual!r})", actual == expected):
            row_ok = False

        if row["consumable"]:
            resp = res["response"]
            # consumable rows must produce a valid SERVED ContextResponse
            if not check(f"{rid}: produced a response", resp is not None):
                row_ok = False
            else:
                if not check(f"{rid}: ContextResponse.v1 valid", validate_ref(resp, "consumption/ContextResponse.v1") == []):
                    row_ok = False
                served = resp["served_facts"]
                if not check(f"{rid}: served ≥ {row['expect_min_served_facts']} facts", len(served) >= row["expect_min_served_facts"]):
                    row_ok = False
                if not check(f"{rid}: every served fact carries a source handle", all(f.get("source_handle") for f in served)):
                    row_ok = False
                # candidate rows must NEVER be served as fact — verify allegations never appear as served truth
                if not check(f"{rid}: no allegation served as fact",
                             not any(f.get("claim_status") == "unverified_allegation" for f in served)):
                    row_ok = False
                if row.get("expect_allegations_held_out"):
                    if not check(f"{rid}: allegations present + held out",
                                 any(h["artifact_id"].startswith("narrative-") for h in resp["held_out_warnings"])):
                        row_ok = False
                # tenant_private source must NOT leak a fact into a global/public handle
                if row.get("scope") == "tenant_private":
                    leaked = [f["source_handle"] for f in served if f"ctx://tenant/{row['tenant_id']}/" not in f["source_handle"]]
                    if not check(f"{rid}: tenant_private → no global handle leak", leaked == [], str(leaked)):
                        row_ok = False
                    if not check(f"{rid}: response tenant_id == {row['tenant_id']}", resp["tenant_id"] == row["tenant_id"]):
                        row_ok = False
        else:
            # candidate / unknown rows: consumable:false + a reason + NO response (never faked as fact)
            if not check(f"{rid}: consumable is False", res["consumable"] is False):
                row_ok = False
            if not check(f"{rid}: response is None (NEVER served as fact)", res["response"] is None):
                row_ok = False
            want_reason = row.get("expected_non_consumable_reason", "")
            if not check(f"{rid}: non_consumable_reason contains {want_reason!r}", want_reason in res["non_consumable_reason"], res["non_consumable_reason"]):
                row_ok = False
            if not check(f"{rid}: 0 served facts in summary", summary["served_fact_count"] == 0):
                row_ok = False

        table.append((rid, row["source_type"], row.get("scope", ""), actual,
                      summary["served_fact_count"], summary["held_out_warning_count"],
                      ("ok" if row_ok else "FAIL")))

    # ── determinism across the whole matrix ──
    summaries_1 = [_run_row(r)["summary"] for r in rows]
    summaries_2 = [_run_row(r)["summary"] for r in rows]
    check("the whole matrix is deterministic (byte-identical second run)", summaries_1 == summaries_2)

    # ── coverage: every matrix row was exercised; both consumable + candidate classes present ──
    check("matrix covers ≥1 consumable + ≥1 candidate (non-consumable) source",
          any(r["consumable"] for r in rows) and any(not r["consumable"] for r in rows))

    # ── per-source status table ──
    print("\n  PER-SOURCE STATUS TABLE")
    print(f"  {'row_id':<22}{'type':<10}{'scope':<16}{'status':<16}{'served':<8}{'held':<6}{'result'}")
    for rid, st, sc, status, served, held, result in table:
        print(f"  {rid:<22}{st:<10}{sc:<16}{status:<16}{served:<8}{held:<6}{result}")

    print(f"\n{'PASS — check_multi_source_regression: every source type in multi_source_run_matrix.json matched its expected consumption_status — consumable rows served a schema-valid ContextResponse (facts carry handles, allegations held out, no tenant leak); candidate (pdf/html) rows returned a non_consumable_reason and were NEVER served as fact; deterministic.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: multi-source regression over the run matrix.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
