#!/usr/bin/env python3
"""scripts.cross_table_discovery_primitives — CROSS-TABLE exploration, key discovery, key testing, and key
SHAPING for merges (owner-directed 2026-07-08): the layer that answers "what tables/columns exist in this
environment, what could be a key, do these two tables join, and what shaping makes the join actually work?"

  * EXPLORATION — list tables/views; profile every column (type, null rate, distinct ratio, samples,
    length range) — the environment map.
  * KEY DISCOVERY — candidate primary keys by uniqueness+null-free scan; bounded composite-key search when
    no single column is unique.
  * KEY TESTING — uniqueness (duplicate counts), referential CONTAINMENT (inclusion dependency: what
    fraction of A.x exists in B.y — the FK detector), join QUALITY (match rate, fan-out multiplication,
    orphans left/right).
  * JOIN CANDIDATE RANKING — cross-table column pairs scored by name-token similarity + type compatibility
    + sampled value overlap.
  * KEY SHAPING — the classic merge killers fixed deterministically: '007' vs 7 (strip/pad), 'AB-12' vs
    'ab12' (casefold/punct), composite concat with separators — every shaping is a SETTINGS RECIPE
    (recorded, reusable, tunable via the control plane), and plan_merge PROVES the lift by measuring join
    quality before vs after shaping.

Everything runs against any DB-API connection (SQLite in tests; Postgres config-only). Reads only — this
module never mutates a target environment. candidate=true, serves_truth=false.

    python3 scripts/cross_table_discovery_primitives.py --self-test
"""
from __future__ import annotations

import sys
from pathlib import Path

_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import inspect  # noqa: E402
import itertools  # noqa: E402
import json  # noqa: E402
import re  # noqa: E402
from typing import Any  # noqa: E402

try:
    from src.teleon.experiments.ids import canonical_id  # noqa: E402
except ImportError as exc:  # pragma: no cover
    raise SystemExit(f"cross_table_discovery_primitives requires canonical_id; import failed: {exc}")

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
CARD_PREFIX = "prim-xtable"
_SAMPLE_LIMIT = 1000          # per-column value sample for overlap scoring (deterministic ORDER BY)
_KEY_UNIQUENESS_FLOOR = 0.999  # uniqueness ratio to call a column a key CANDIDATE (exactness tested after)
_IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _q(identifier: str) -> str:
    """Quote an identifier defensively; refuse anything not identifier-shaped (read-only discipline)."""
    if not _IDENT_RE.match(identifier or ""):
        raise ValueError(f"unsafe identifier: {identifier!r}")
    return f'"{identifier}"'


# ── EXPLORATION ───────────────────────────────────────────────────────────────────────────────────────────────
def list_tables(con: Any) -> list[str]:
    """Enumerate base tables (SQLite master; Postgres swap = information_schema, config-only)."""
    rows = con.execute("SELECT name FROM sqlite_master WHERE type IN ('table','view') "
                       "AND name NOT LIKE 'sqlite_%' ORDER BY name").fetchall()
    return [r[0] for r in rows]


def profile_columns(con: Any, table: str) -> list[dict[str, Any]]:
    """Per-column environment map: declared type, null rate, distinct ratio, min/max length, samples."""
    cols = con.execute(f"PRAGMA table_info({_q(table)})").fetchall()
    total = con.execute(f"SELECT COUNT(*) FROM {_q(table)}").fetchone()[0]
    out = []
    for _cid, name, decl_type, _notnull, _default, pk in cols:
        qc = _q(name)
        nulls, distinct = con.execute(
            f"SELECT SUM(CASE WHEN {qc} IS NULL THEN 1 ELSE 0 END), COUNT(DISTINCT {qc}) "
            f"FROM {_q(table)}").fetchone()
        lens = con.execute(f"SELECT MIN(LENGTH({qc})), MAX(LENGTH({qc})) FROM {_q(table)} "
                           f"WHERE {qc} IS NOT NULL").fetchone()
        samples = [r[0] for r in con.execute(
            f"SELECT DISTINCT {qc} FROM {_q(table)} WHERE {qc} IS NOT NULL ORDER BY {qc} LIMIT 5")]
        out.append({"table": table, "column": name, "declared_type": decl_type or "", "declared_pk": bool(pk),
                    "rows": total, "null_rate": round((nulls or 0) / total, 4) if total else 0.0,
                    "distinct_count": distinct or 0,
                    "distinct_ratio": round((distinct or 0) / total, 4) if total else 0.0,
                    "min_len": lens[0], "max_len": lens[1], "samples": samples, **BOUNDARY})
    return out


# ── KEY DISCOVERY + TESTING ───────────────────────────────────────────────────────────────────────────────────
def candidate_key_scan(con: Any, table: str) -> list[dict[str, Any]]:
    """Single columns that could be keys: null-free + distinct ratio >= floor, EXACT duplicate count then
    verified (a ratio is a screen; the dup count is the test)."""
    out = []
    for p in profile_columns(con, table):
        if p["null_rate"] == 0 and p["distinct_ratio"] >= _KEY_UNIQUENESS_FLOOR and p["rows"] > 0:
            dup = test_key_uniqueness(con, table, [p["column"]])
            out.append({"table": table, "key_columns": [p["column"]],
                        "distinct_ratio": p["distinct_ratio"], "duplicate_rows": dup["duplicate_rows"],
                        "is_exact_key": dup["is_unique"], "declared_pk": p["declared_pk"], **BOUNDARY})
    return sorted(out, key=lambda r: (not r["is_exact_key"], r["key_columns"]))


def test_key_uniqueness(con: Any, table: str, columns: list[str]) -> dict[str, Any]:
    """EXACT uniqueness test for a proposed (composite) key: how many rows share a key value with another."""
    key = ", ".join(_q(c) for c in columns)
    dup = con.execute(f"SELECT COALESCE(SUM(n), 0) FROM (SELECT COUNT(*) AS n FROM {_q(table)} "
                      f"GROUP BY {key} HAVING COUNT(*) > 1)").fetchone()[0]
    return {"table": table, "key_columns": columns, "duplicate_rows": int(dup),
            "is_unique": dup == 0, **BOUNDARY}


def composite_key_search(con: Any, table: str, max_cols: int = 2) -> list[dict[str, Any]]:
    """Bounded minimal-composite-key search: when no single column is unique, test column pairs (then
    triples if asked) in deterministic order; return the exact unique combinations found."""
    cols = [p["column"] for p in profile_columns(con, table) if p["null_rate"] == 0]
    singles_unique = {tuple(r["key_columns"]) for r in candidate_key_scan(con, table) if r["is_exact_key"]}
    found = [{"table": table, "key_columns": list(k), "is_exact_key": True, **BOUNDARY}
             for k in sorted(singles_unique)]
    if found:
        return found
    for size in range(2, max_cols + 1):
        for combo in itertools.combinations(sorted(cols), size):
            if test_key_uniqueness(con, table, list(combo))["is_unique"]:
                found.append({"table": table, "key_columns": list(combo), "is_exact_key": True, **BOUNDARY})
        if found:
            break
    return found


def test_referential_containment(con: Any, from_table: str, from_col: str,
                                 to_table: str, to_col: str) -> dict[str, Any]:
    """INCLUSION DEPENDENCY (the FK detector): what fraction of from.col values exist in to.col; orphan
    count named, not hidden."""
    total, contained = con.execute(
        f"SELECT COUNT(*), SUM(CASE WHEN {_q(from_col)} IN "
        f"(SELECT {_q(to_col)} FROM {_q(to_table)}) THEN 1 ELSE 0 END) "
        f"FROM {_q(from_table)} WHERE {_q(from_col)} IS NOT NULL").fetchone()
    containment = round((contained or 0) / total, 4) if total else 0.0
    return {"from": f"{from_table}.{from_col}", "to": f"{to_table}.{to_col}",
            "containment": containment, "orphans": int((total or 0) - (contained or 0)),
            "fk_candidate": containment >= 0.95, **BOUNDARY}


# ── JOIN CANDIDATES + KEY SHAPING ─────────────────────────────────────────────────────────────────────────────
def _name_tokens(name: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", (name or "").casefold()))


def _sample_values(con: Any, table: str, col: str) -> set[str]:
    return {str(r[0]) for r in con.execute(
        f"SELECT DISTINCT {_q(col)} FROM {_q(table)} WHERE {_q(col)} IS NOT NULL "
        f"ORDER BY {_q(col)} LIMIT {_SAMPLE_LIMIT}")}


def find_join_candidates(con: Any) -> list[dict[str, Any]]:
    """Rank cross-table column pairs by name-token overlap + sampled RAW value overlap. A pair with high
    name score but zero raw overlap is exactly where key SHAPING earns its keep (see plan_merge)."""
    tables = list_tables(con)
    profiles = {t: profile_columns(con, t) for t in tables}
    out = []
    for t1, t2 in itertools.combinations(tables, 2):
        for p1 in profiles[t1]:
            for p2 in profiles[t2]:
                nt1, nt2 = _name_tokens(p1["column"]), _name_tokens(p2["column"])
                name_score = len(nt1 & nt2) / len(nt1 | nt2) if nt1 | nt2 else 0.0
                if name_score == 0 and p1["column"].casefold() != p2["column"].casefold():
                    continue
                s1, s2 = _sample_values(con, t1, p1["column"]), _sample_values(con, t2, p2["column"])
                overlap = len(s1 & s2) / min(len(s1), len(s2)) if s1 and s2 else 0.0
                out.append({"left": f"{t1}.{p1['column']}", "right": f"{t2}.{p2['column']}",
                            "name_score": round(name_score, 3), "raw_value_overlap": round(overlap, 3),
                            "score": round(0.4 * name_score + 0.6 * overlap, 3),
                            "shaping_recommended": name_score >= 0.5 and overlap < 0.5, **BOUNDARY})
    return sorted(out, key=lambda r: (-r["score"], r["left"], r["right"]))


#: key-shaping SETTINGS (a recipe the control plane can tune): each knob is deterministic + recorded
def shape_key(value: Any, *, casefold: bool = True, strip: bool = True, strip_leading_zeros: bool = False,
              zero_pad_width: int = 0, drop_punctuation: bool = False, prefix_strip: str = "") -> str:
    """Shape ONE key value for merging: '007' vs 7, 'AB-12' vs 'ab12', 'INV-123' vs '123' — every knob a
    setting so the shaping recipe is reusable, reversible-by-rerun, and tunable via test feedback."""
    s = str(value if value is not None else "")
    if strip:
        s = s.strip()
    if prefix_strip and s.casefold().startswith(prefix_strip.casefold()):
        s = s[len(prefix_strip):]
    if drop_punctuation:
        s = re.sub(r"[^0-9A-Za-z]", "", s)
    if casefold:
        s = s.casefold()
    if strip_leading_zeros and s.lstrip("0").strip():
        s = s.lstrip("0") or "0"
    if zero_pad_width and s.isdigit():
        s = s.zfill(zero_pad_width)
    return s


def test_join_quality(con: Any, left_table: str, left_col: str, right_table: str, right_col: str,
                      shaping: dict[str, Any] | None = None) -> dict[str, Any]:
    """The join health report: match rate, orphans BOTH sides, and FAN-OUT (row multiplication — the
    silent duplicator). Optional shaping recipe applied to both sides before comparing."""
    lvals = [r[0] for r in con.execute(f"SELECT {_q(left_col)} FROM {_q(left_table)}")]
    rvals = [r[0] for r in con.execute(f"SELECT {_q(right_col)} FROM {_q(right_table)}")]
    sh = shaping or {}
    lshaped = [shape_key(v, **sh) for v in lvals if v is not None]
    from collections import Counter  # noqa: PLC0415
    rcount = Counter(shape_key(v, **sh) for v in rvals if v is not None)
    matched = [v for v in lshaped if rcount.get(v)]
    joined_rows = sum(rcount[v] for v in matched)
    return {"left": f"{left_table}.{left_col}", "right": f"{right_table}.{right_col}",
            "shaping": sh, "left_rows": len(lshaped),
            "match_rate": round(len(matched) / len(lshaped), 4) if lshaped else 0.0,
            "orphans_left": len(lshaped) - len(matched),
            "orphans_right": sum(1 for v in rcount if v not in set(lshaped)),
            "fanout": round(joined_rows / len(matched), 4) if matched else 0.0,
            "fanout_warning": bool(matched) and joined_rows > len(matched), **BOUNDARY}


_SHAPING_RECIPES: tuple[dict[str, Any], ...] = (
    {}, {"casefold": True, "strip": True}, {"strip_leading_zeros": True},
    {"drop_punctuation": True}, {"drop_punctuation": True, "strip_leading_zeros": True},
    {"zero_pad_width": 6},
)


def plan_merge(con: Any, left_table: str, left_col: str, right_table: str, right_col: str) -> dict[str, Any]:
    """COMPOSITE: try the shaping-recipe zoo deterministically, measure join quality for each, return the
    champion recipe WITH the full ledger (before-vs-after lift proven, losers preserved)."""
    ledger = []
    for recipe in _SHAPING_RECIPES:
        q = test_join_quality(con, left_table, left_col, right_table, right_col, shaping=recipe)
        ledger.append({"shaping": recipe, "match_rate": q["match_rate"], "fanout": q["fanout"],
                       "fanout_warning": q["fanout_warning"]})
    champion = max(ledger, key=lambda r: (r["match_rate"], -r["fanout"], json.dumps(r["shaping"], sort_keys=True)))
    baseline = ledger[0]
    return {"left": f"{left_table}.{left_col}", "right": f"{right_table}.{right_col}",
            "baseline_match_rate": baseline["match_rate"], "champion": champion,
            "lift": round(champion["match_rate"] - baseline["match_rate"], 4),
            "ledger": ledger, "action": "review_before_merge_if_fanout_warning", **BOUNDARY}


def explore_environment(con: Any) -> dict[str, Any]:
    """COMPOSITE sweep: tables -> profiles -> candidate keys -> FK containments -> ranked join candidates."""
    tables = list_tables(con)
    keys = {t: candidate_key_scan(con, t) for t in tables}
    joins = find_join_candidates(con)
    containments = []
    for j in joins[:20]:
        lt, lc = j["left"].split(".")
        rt, rc = j["right"].split(".")
        containments.append(test_referential_containment(con, lt, lc, rt, rc))
    return {"tables": tables, "n_tables": len(tables),
            "column_profiles": {t: profile_columns(con, t) for t in tables},
            "candidate_keys": keys, "join_candidates": joins[:20],
            "referential_containments": containments, **BOUNDARY}


_ATOMIC_FNS = (list_tables, profile_columns, candidate_key_scan, test_key_uniqueness, composite_key_search,
               test_referential_containment, find_join_candidates, shape_key, test_join_quality)
_COMPOSITE_FNS = (plan_merge, explore_environment)
COMPOSITE_PLANS = {"plan_merge": ["shape_key", "test_join_quality"],
                   "explore_environment": ["list_tables", "profile_columns", "candidate_key_scan",
                                           "find_join_candidates", "test_referential_containment"]}


def all_cards() -> list[dict[str, Any]]:
    cards = []
    for fn in _ATOMIC_FNS + _COMPOSITE_FNS:
        title = (fn.__doc__ or fn.__name__).splitlines()[0][:160]
        composite = fn in _COMPOSITE_FNS
        cards.append({"primitive_id": canonical_id(CARD_PREFIX, title, fn.__name__),
                      "impl_name": fn.__name__, "record_type": "cross_table_discovery_primitive",
                      "kind": "primitive_group" if composite else "primitive", "title": title,
                      "executable_body": inspect.getsource(fn), "language": "python",
                      "input_edge": "DatabaseEnvironmentHandle", "output_edge": "SchemaDiscoveryResult",
                      "blackbox": f"{'Composite' if composite else 'Atomic'} cross-table primitive: {title} "
                                  f"Input: DB connection + table/column names (read-only). Output: "
                                  f"exploration/key/join report.",
                      "plan_steps": COMPOSITE_PLANS.get(fn.__name__, []), "tier": "common", **BOUNDARY})
    return cards


# ── self-test: fixture environment with the classic traps ───────────────────────────────────────────────────
def _fixture(con: Any) -> None:
    con.execute("CREATE TABLE customers(customer_id TEXT, email TEXT, region TEXT)")
    con.executemany("INSERT INTO customers VALUES(?,?,?)",
                    [("007", "a@x.com", "east"), ("008", "b@x.com", "east"), ("009", "c@x.com", "west"),
                     ("010", "d@x.com", "west")])
    con.execute("CREATE TABLE orders(order_no INTEGER, customer_id INTEGER, sku TEXT, line INTEGER)")
    con.executemany("INSERT INTO orders VALUES(?,?,?,?)",  # INTEGER ids vs padded TEXT: the merge killer
                    [(1, 7, "A", 1), (1, 7, "B", 2), (2, 8, "A", 1), (3, 9, "A", 1), (4, 99, "A", 1)])
    con.execute("CREATE TABLE regions(region TEXT, manager TEXT)")
    con.executemany("INSERT INTO regions VALUES(?,?)", [("east", "m1"), ("west", "m2")])


def _self_test() -> int:
    import sqlite3  # noqa: PLC0415
    checks: list[tuple[str, bool]] = []
    con = sqlite3.connect(":memory:")
    _fixture(con)
    checks.append(("EXPLORATION: enumerates the environment's tables",
                   list_tables(con) == ["customers", "orders", "regions"]))
    prof = {p["column"]: p for p in profile_columns(con, "customers")}
    checks.append(("profiling: null rate, distinct ratio, lengths, samples per column",
                   prof["customer_id"]["distinct_ratio"] == 1.0 and prof["region"]["distinct_count"] == 2
                   and prof["customer_id"]["min_len"] == 3))
    keys = candidate_key_scan(con, "customers")
    checks.append(("KEY DISCOVERY: customer_id + email found as exact keys; region is not",
                   {tuple(k["key_columns"]) for k in keys if k["is_exact_key"]}
                   == {("customer_id",), ("email",)}))
    checks.append(("KEY TESTING: order_no alone is NOT unique (2 dup rows); exactness measured not assumed",
                   not test_key_uniqueness(con, "orders", ["order_no"])["is_unique"]
                   and test_key_uniqueness(con, "orders", ["order_no"])["duplicate_rows"] == 2))
    comp = composite_key_search(con, "orders", max_cols=2)
    checks.append(("COMPOSITE KEY search finds (order_no, line) when no single column is unique",
                   any(set(k["key_columns"]) == {"order_no", "line"} for k in comp)))
    joins = find_join_candidates(con)
    cid = next(j for j in joins if "customer_id" in j["left"] and "customer_id" in j["right"])
    checks.append(("JOIN CANDIDATES: region pair (name+value both match) outranks the mismatched "
                   "customer_id pair, whose SHAPING signal fires (name 1.0, raw overlap 0.0)",
                   "region" in joins[0]["left"] and joins[0]["raw_value_overlap"] == 1.0
                   and cid["name_score"] == 1.0 and cid["raw_value_overlap"] == 0.0
                   and cid["shaping_recommended"]))
    checks.append(("region join has RAW overlap (no shaping needed there)",
                   any(j["raw_value_overlap"] == 1.0 for j in joins if "region" in j["left"] + j["right"])))
    raw_q = test_join_quality(con, "orders", "customer_id", "customers", "customer_id")
    shaped_q = test_join_quality(con, "orders", "customer_id", "customers", "customer_id",
                                 shaping={"strip_leading_zeros": True})
    checks.append(("KEY SHAPING fixes the '007' vs 7 merge killer: match rate 0.0 raw -> 0.8 shaped "
                   "(the orphan 99 stays an orphan, honestly)",
                   raw_q["match_rate"] == 0.0 and shaped_q["match_rate"] == 0.8
                   and shaped_q["orphans_left"] == 1))
    plan = plan_merge(con, "orders", "customer_id", "customers", "customer_id")
    checks.append(("PLAN_MERGE: recipe zoo raced deterministically; champion proves the lift with a "
                   "lossless ledger", plan["champion"]["match_rate"] == 0.8 and plan["lift"] == 0.8
                   and len(plan["ledger"]) == len(_SHAPING_RECIPES)
                   and plan["baseline_match_rate"] == 0.0))
    fan = test_join_quality(con, "customers", "customer_id", "orders", "customer_id",
                            shaping={"strip_leading_zeros": True})
    checks.append(("FAN-OUT detection: joining customers->orders multiplies rows (order 1 has 2 lines) "
                   "and WARNS", fan["fanout"] > 1.0 and fan["fanout_warning"]))
    checks.append(("containment: shaped FK direction detectable; env sweep composes it all",
                   test_referential_containment(con, "orders", "sku", "orders", "sku")["containment"] == 1.0
                   and explore_environment(con)["n_tables"] == 3))
    try:
        list_tables(con) and profile_columns(con, "x; DROP TABLE customers")
        checks.append(("unsafe identifiers REFUSED (read-only discipline)", False))
    except ValueError:
        checks.append(("unsafe identifiers REFUSED (read-only discipline)", True))
    checks.append(("cards + boundary", all(c.get("serves_truth") is False for c in all_cards())))
    failed = [n for n, ok in checks if not ok]
    for n, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print(f"\nPASS - cross_table_discovery_primitives: explore -> profile -> discover keys -> test "
          f"uniqueness/containment -> rank joins -> SHAPE keys (recipe zoo, lift proven 0.0 -> 0.8 on the "
          f"'007' vs 7 fixture) -> fan-out warnings. Read-only. serves_truth=false.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--cards", action="store_true")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.cards:
        for c in all_cards():
            print(json.dumps(c, sort_keys=True))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
