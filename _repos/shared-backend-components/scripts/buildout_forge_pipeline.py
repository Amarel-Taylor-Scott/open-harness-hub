#!/usr/bin/env python3
"""scripts.buildout_forge_pipeline — BuildoutForge PIPELINE genome: the OTHER shape engineers actually build with
frontier models — a real, multi-step DATA PIPELINE / DAG, not an HTTP service. A many-module ETL project is BUILT,
RUN as a subprocess (`python run.py --input events.csv --dim vendors.csv --db out.db`), and verified by a HIDDEN
pipeline oracle that opens the produced sqlite DB + reads metrics.json and asserts ~25 named behavioral checks
(realism level B6). Nothing passes on plausibility — the built pipeline must actually transform the fixture and
land the right rows.

This mirrors scripts/buildout_forge.py (same `run_buildout`/`self_test`/`main` shape, same subprocess-oracle
machinery that prints one `ORACLE {json}` line) but the genome's `http_oracle` driver is a PIPELINE oracle: it does
NOT bind a socket — it runs the built pipeline and inspects its outputs (out.db tables + metrics.json), including a
second run to prove the load is INCREMENTAL + IDEMPOTENT (running twice must not double-load). The genome plugs into
scripts/buildout_forge_ab.py (same `_GENOMES[gid]` key shape: product_family, prompt_style, stack, solution_file,
http_oracle, realism_level, goal, primitive_targets, good, bad, stub).

The one genome is `sales_etl_pipeline_dag__stdlib_sqlite__v0`: a sales-event ETL DAG (extract -> validate ->
normalize -> dedupe -> join -> aggregate -> quality -> load) run over Python stdlib + sqlite3 ONLY (no pip, no
cluster) — LOCAL, and genuinely LARGE (ten modules -> a big decomposable surface). Non-insurance. It yields eight
pure primitives (validate_event, normalize_amount_cents, dedupe_by_key, inner_join_on, group_net_sum,
quality_metrics, topological_order, parse_iso_date).

Isolation note: a data pipeline does REAL I/O (reads CSVs, writes sqlite + metrics.json) so the primitive I/O-ban
sandbox does NOT apply here; buildouts run in an ephemeral temp workspace with a wall-clock timeout. The self-test
runs TRUSTED reference code. BENCHMARK_KIND=real_project_buildout; candidate=true / serves_truth=false.

    python3 scripts/buildout_forge_pipeline.py --self-test
    python3 scripts/buildout_forge_pipeline.py --run --solution good   # run the reference build + the hidden oracle
"""
from __future__ import annotations

import sys
from pathlib import Path

# ── substrate-root bootstrap (sentinel; mirrors scripts/buildout_forge.py) ────────────────────────────────────
_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots, resource  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import json  # noqa: E402
import subprocess  # noqa: E402  (the oracle RUNNER + pipeline runner, not model code)
import tempfile  # noqa: E402
import time  # noqa: E402
from typing import Any  # noqa: E402

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
BENCHMARK_KIND = "real_project_buildout"  # no_proxy_gate: passes only when the built pipeline RUNS + a hidden oracle passes
ARTIFACT_DIR_REL = "data/dev-intel/buildout_forge"
BUILDOUT_REALISM = "B6"  # built repo runs locally AND a hidden oracle inspects real outputs (sqlite + metrics.json)
_DEFAULT_GENOME = "sales_etl_pipeline_dag__stdlib_sqlite__v0"

# ── the HIDDEN pipeline oracle: write fixture CSVs, RUN the built pipeline as a subprocess, open out.db + read ─
#    metrics.json, assert ~25 named behavioral checks, then RUN AGAIN to prove the load is idempotent. The build
#    never sees these fixtures. Every check is initialized False so a build that never runs (stub) still emits a
#    full checks dict (run_exits_0=False) instead of crashing the oracle.
_PIPELINE_ORACLE_DRIVER = r'''
import csv, json, os, sqlite3, subprocess, sys

# fixture: valid ok/refund rows + a duplicate event_id + a bad-amount row + an unknown-vendor row + a
# missing-vendor row + a bad-status row + one uppercase status (to exercise normalize's lowercasing).
EVENTS = [
    ("event_id", "vendor_id", "amount", "ts", "status"),
    ("E1", "V1", "10.00", "2026-01-01T10:00:00Z", "ok"),
    ("E2", "V1", "5.00", "2026-01-02T11:30:00Z", "refund"),
    ("E3", "V2", "20.00", "2026-01-03", "ok"),
    ("E4", "V2", "4.50", "2026-01-04", "ok"),
    ("E9", "V3", "15.00", "2026-01-10", "REFUND"),
    ("E1", "V1", "99.00", "2026-01-05", "ok"),        # duplicate event_id -> deduped (keep first)
    ("E5", "V1", "-3.00", "2026-01-06", "ok"),        # amount <= 0 -> reject bad_amount
    ("E6", "V9", "7.00", "2026-01-07", "ok"),         # vendor not in dimension -> reject unknown_vendor
    ("E7", "", "8.00", "2026-01-08", "ok"),           # missing vendor_id -> reject missing_vendor_id
    ("E8", "V1", "12.00", "2026-01-09", "pending"),   # status not in {ok, refund} -> reject bad_status
]
VENDORS = [
    ("vendor_id", "vendor_name", "region"),
    ("V1", "Acme Corp", "US"),
    ("V2", "Beta LLC", "EU"),
    ("V3", "Gamma Inc", "US"),
]


def _write_csv(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        csv.writer(fh).writerows(rows)


def _run_pipeline():
    return subprocess.run([sys.executable, "run.py", "--input", "events.csv",
                           "--dim", "vendors.csv", "--db", "out.db"],
                          capture_output=True, text=True, timeout=60)


CHECK_NAMES = [
    "run_exits_0", "tables_exist",
    "metrics_input_rows_correct", "metrics_valid_rows_correct", "metrics_rejected_rows_correct",
    "metrics_dedupe_removed_correct", "metrics_vendors_matched_correct", "metrics_total_net_cents_correct",
    "agg_row_count_correct", "agg_net_cents_correct", "event_count_correct",
    "agg_v2_net_cents_correct", "agg_refund_net_negative_correct",
    "rejects_row_count_correct", "bad_amount_rejected", "unknown_vendor_rejected",
    "missing_vendor_rejected", "bad_status_rejected", "rejects_have_reasons",
    "dag_topologically_ordered",
    "rerun_exits_0", "rerun_agg_rows_stable", "rerun_rejects_stable",
    "rerun_no_double_load", "rerun_metrics_stable",
]
checks = {name: False for name in CHECK_NAMES}

_write_csv("events.csv", EVENTS)
_write_csv("vendors.csv", VENDORS)

first = _run_pipeline()
checks["run_exits_0"] = (first.returncode == 0)

# ── metrics.json checks (guarded: a missing/garbage file leaves these at their default False) ────────────────
metrics = {}
try:
    with open("metrics.json", encoding="utf-8") as fh:
        metrics = json.load(fh)
except Exception:
    metrics = {}
try:
    checks["metrics_input_rows_correct"] = metrics.get("input_rows") == 10
    checks["metrics_valid_rows_correct"] = metrics.get("valid_rows") == 7
    checks["metrics_rejected_rows_correct"] = metrics.get("rejected_rows") == 4
    checks["metrics_dedupe_removed_correct"] = metrics.get("dedupe_removed") == 1
    checks["metrics_vendors_matched_correct"] = metrics.get("vendors_matched") == 5
    checks["metrics_total_net_cents_correct"] = metrics.get("total_net_cents") == 1450
    order = metrics.get("dag_order") or []

    def _before(a, b):
        return a in order and b in order and order.index(a) < order.index(b)

    checks["dag_topologically_ordered"] = (
        len(order) == 8
        and _before("extract", "validate") and _before("validate", "normalize")
        and _before("normalize", "dedupe") and _before("dedupe", "join")
        and _before("join", "aggregate") and _before("aggregate", "quality")
        and _before("quality", "load"))
except Exception:
    pass

# ── out.db checks (guarded the same way) ─────────────────────────────────────────────────────────────────────
try:
    conn = sqlite3.connect("out.db")
    cur = conn.cursor()
    tables = {r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    checks["tables_exist"] = ("fact_sales_agg" in tables and "rejects" in tables)
    if checks["tables_exist"]:
        agg = {(v, rg): (net, cnt) for v, rg, net, cnt in
               cur.execute("SELECT vendor_id, region, net_cents, event_count FROM fact_sales_agg")}
        checks["agg_row_count_correct"] = len(agg) == 3
        # (V1, US): +1000 (ok) - 500 (refund) = 500 net; 2 events (the 99.00 dup is deduped out)
        checks["agg_net_cents_correct"] = agg.get(("V1", "US"), (None, None))[0] == 500
        checks["event_count_correct"] = agg.get(("V1", "US"), (None, None))[1] == 2
        # (V2, EU): +2000 +450 (both ok) = 2450 net
        checks["agg_v2_net_cents_correct"] = agg.get(("V2", "EU"), (None, None))[0] == 2450
        # (V3, US): a single refund of 1500 -> net must be NEGATIVE (-1500), proving refund subtraction
        checks["agg_refund_net_negative_correct"] = agg.get(("V3", "US"), (None, None))[0] == -1500
        rej = list(cur.execute("SELECT event_id, reason FROM rejects"))
        rej_set = {(e, r) for e, r in rej}
        checks["rejects_row_count_correct"] = len(rej) == 4
        checks["bad_amount_rejected"] = ("E5", "bad_amount") in rej_set
        checks["unknown_vendor_rejected"] = ("E6", "unknown_vendor") in rej_set
        checks["missing_vendor_rejected"] = ("E7", "missing_vendor_id") in rej_set
        checks["bad_status_rejected"] = ("E8", "bad_status") in rej_set
        checks["rejects_have_reasons"] = (len(rej) == 4 and all(bool(reason) for _, reason in rej))
    conn.close()
except Exception:
    pass

# ── incremental + idempotent: run the SAME input again; row counts must be stable, no double-load ────────────
try:
    second = _run_pipeline()
    checks["rerun_exits_0"] = (second.returncode == 0)
    conn = sqlite3.connect("out.db")
    cur = conn.cursor()
    n_agg = cur.execute("SELECT COUNT(*) FROM fact_sales_agg").fetchone()[0]
    n_rej = cur.execute("SELECT COUNT(*) FROM rejects").fetchone()[0]
    checks["rerun_agg_rows_stable"] = (n_agg == 3)
    checks["rerun_rejects_stable"] = (n_rej == 4)
    row = cur.execute("SELECT net_cents, event_count FROM fact_sales_agg "
                      "WHERE vendor_id = 'V1' AND region = 'US'").fetchone()
    checks["rerun_no_double_load"] = (row == (500, 2))
    conn.close()
    with open("metrics.json", encoding="utf-8") as fh:
        metrics2 = json.load(fh)
    checks["rerun_metrics_stable"] = (metrics != {} and metrics2 == metrics)
except Exception:
    pass

oracle_pass = len(checks) >= 15 and all(checks.values())
print("ORACLE " + json.dumps({"checks": checks, "oracle_pass": oracle_pass}))
'''

# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════
# reference GOOD buildout: a real ten-module sales-ETL DAG (stdlib + sqlite3 only -> runs here, no deps).
# Each module holds one DAG step plus the PURE primitive it is built from; run.py is the CLI + DAG driver.
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════

_GOOD_DAG = r'''
"""dag — the DAG engine: a topological_order primitive (Kahn's algorithm) + a step runner.

The pipeline is a directed acyclic graph of named steps with dependencies; run_dag executes the step functions
in a valid topological order and records that order on the shared context so downstream tooling (and the hidden
oracle) can confirm the ordering was respected.
"""
import time


def topological_order(deps):
    """Return a deterministic topological ordering of a DAG.

    deps maps each node to the list of nodes that must run BEFORE it (its prerequisites). Uses Kahn's algorithm
    with a sorted tie-break so the order is stable across runs. Raises ValueError on a cycle. PURE primitive.
    """
    nodes = set(deps)
    for prereqs in deps.values():
        nodes.update(prereqs)
    indegree = {node: 0 for node in nodes}
    adjacency = {node: [] for node in nodes}
    for node, prereqs in deps.items():
        for prereq in prereqs:
            adjacency[prereq].append(node)
            indegree[node] += 1
    ready = sorted(node for node in nodes if indegree[node] == 0)
    order = []
    while ready:
        current = ready.pop(0)
        order.append(current)
        for neighbor in sorted(adjacency[current]):
            indegree[neighbor] -= 1
            if indegree[neighbor] == 0:
                ready.append(neighbor)
        ready.sort()
    if len(order) != len(nodes):
        raise ValueError("cycle detected in DAG dependencies")
    return order


def validate_deps(step_funcs, deps):
    """Confirm the dependency graph and the step-function table describe the SAME set of steps.

    Every node named in deps (as a key or as a prerequisite) must have a callable in step_funcs, and every
    step_funcs entry must appear in deps. Raises ValueError on any mismatch so a mis-wired DAG fails loudly at
    startup rather than silently skipping a step. PURE (read-only) check.
    """
    graph_nodes = set(deps)
    for prereqs in deps.values():
        graph_nodes.update(prereqs)
    missing_funcs = sorted(graph_nodes - set(step_funcs))
    if missing_funcs:
        raise ValueError("DAG nodes with no step function: " + ", ".join(missing_funcs))
    orphan_funcs = sorted(set(step_funcs) - graph_nodes)
    if orphan_funcs:
        raise ValueError("step functions absent from the DAG: " + ", ".join(orphan_funcs))
    return True


def run_dag(step_funcs, deps, ctx):
    """Execute step_funcs (name -> callable(ctx)) in topological order.

    Records the topological plan on ctx['dag_order'], the realized order on ctx['executed_order'], and a
    per-step wall-time on ctx['step_timings'] (name -> seconds) for lightweight observability. The timings are
    deliberately NOT written to metrics.json so the persisted metrics stay byte-stable across identical runs.
    """
    validate_deps(step_funcs, deps)
    order = topological_order(deps)
    ctx["dag_order"] = list(order)
    executed = []
    timings = {}
    for name in order:
        started = time.perf_counter()
        step_funcs[name](ctx)
        timings[name] = round(time.perf_counter() - started, 6)
        executed.append(name)
    ctx["executed_order"] = executed
    ctx["step_timings"] = timings
    return ctx
'''

_GOOD_EXTRACT = r'''
"""extract — DAG step 1: read the raw events CSV and the vendor dimension CSV (stdlib csv only)."""
import csv

EXPECTED_EVENT_COLUMNS = ("event_id", "vendor_id", "amount", "ts", "status")
EXPECTED_DIM_COLUMNS = ("vendor_id", "vendor_name", "region")


def require_columns(fieldnames, expected, source):
    """Raise ValueError if any expected column is absent from a CSV header (fail fast on a schema drift)."""
    present = set(fieldnames or ())
    missing = [column for column in expected if column not in present]
    if missing:
        raise ValueError(source + " is missing required columns: " + ", ".join(missing))
    return True


def read_events(path):
    """Read the raw events CSV into a list of dict rows (event_id, vendor_id, amount, ts, status)."""
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        require_columns(reader.fieldnames, EXPECTED_EVENT_COLUMNS, "events CSV")
        return [dict(row) for row in reader]


def load_dimension(path):
    """Read the vendor dimension CSV into an index {vendor_id: {vendor_name, region}} for the join step."""
    index = {}
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        require_columns(reader.fieldnames, EXPECTED_DIM_COLUMNS, "vendors CSV")
        for row in reader:
            vendor_id = (row.get("vendor_id") or "").strip()
            if not vendor_id:
                continue
            index[vendor_id] = {"vendor_name": (row.get("vendor_name") or "").strip(),
                                "region": (row.get("region") or "").strip()}
    return index


def step(ctx):
    ctx["raw_events"] = read_events(ctx["input_path"])
    ctx["dimension"] = load_dimension(ctx["dim_path"])
    ctx["input_rows"] = len(ctx["raw_events"])
    return ctx
'''

_GOOD_VALIDATE = r'''
"""validate — DAG step 2: flag bad rows into rejects (with a reason) instead of silently dropping them."""

ALLOWED_STATUS = ("ok", "refund")


def validate_event(row):
    """Validate one raw event row.

    Returns (is_valid, reason). A row is rejected (is_valid False) with a specific reason when:
    the event_id is missing, the vendor_id is missing, the amount is non-numeric or <= 0, or the status is not
    one of {ok, refund}. Status membership is case-insensitive (normalize lowercases it later). PURE primitive.
    """
    event_id = (row.get("event_id") or "").strip()
    vendor_id = (row.get("vendor_id") or "").strip()
    amount_raw = (row.get("amount") or "").strip()
    status = (row.get("status") or "").strip().lower()
    if not event_id:
        return (False, "missing_event_id")
    if not vendor_id:
        return (False, "missing_vendor_id")
    try:
        amount = float(amount_raw)
    except (TypeError, ValueError):
        return (False, "bad_amount")
    if amount <= 0:
        return (False, "bad_amount")
    if status not in ALLOWED_STATUS:
        return (False, "bad_status")
    return (True, None)


def step(ctx):
    valid = []
    rejects = ctx.setdefault("rejects", [])
    for row in ctx["raw_events"]:
        is_valid, reason = validate_event(row)
        if is_valid:
            valid.append(row)
        else:
            rejects.append(((row.get("event_id") or "").strip(), reason))
    ctx["valid_events"] = valid
    ctx["valid_rows"] = len(valid)
    return ctx


def summarize_rejects(rejects):
    """Roll up rejects into {reason: count} (deterministic; a small data-quality report). PURE primitive."""
    summary = {}
    for _event_id, reason in rejects:
        summary[reason] = summary.get(reason, 0) + 1
    return summary
'''

_GOOD_NORMALIZE = r'''
"""normalize — DAG step 3: amount -> integer cents, ts -> ISO date, status lowercased."""
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP


def normalize_amount_cents(amount):
    """Convert a dollar amount (str or number) to an integer number of cents, half-up. PURE primitive.

    A leading currency symbol and thousands separators are stripped ('$1,234.50' -> 123450). Decimal is used
    so 10.00 -> 1000 and 4.50 -> 450 exactly (no binary-float rounding drift).
    """
    text = str(amount).strip().replace("$", "").replace(",", "")
    value = Decimal(text)
    cents = (value * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return int(cents)


def parse_iso_date(ts):
    """Normalize a timestamp to an ISO date string 'YYYY-MM-DD'. PURE primitive.

    Accepts a bare date ('2026-01-03') or a datetime ('2026-01-01T10:00:00Z' / space-separated); the date part
    before the first 'T' or space is taken and validated via datetime.strptime. Empty input -> ''.
    """
    text = (ts or "").strip()
    if not text:
        return ""
    date_part = text.split("T", 1)[0].split(" ", 1)[0]
    return datetime.strptime(date_part, "%Y-%m-%d").strftime("%Y-%m-%d")


def normalize_event(row):
    """Return a normalized copy of a validated event row (amount_cents, date, lowercased status)."""
    normalized = dict(row)
    normalized["event_id"] = (row.get("event_id") or "").strip()
    normalized["vendor_id"] = (row.get("vendor_id") or "").strip()
    normalized["amount_cents"] = normalize_amount_cents(row.get("amount"))
    normalized["date"] = parse_iso_date(row.get("ts"))
    normalized["status"] = (row.get("status") or "").strip().lower()
    return normalized


def step(ctx):
    ctx["normalized_events"] = [normalize_event(row) for row in ctx["valid_events"]]
    return ctx
'''

_GOOD_DEDUPE = r'''
"""dedupe — DAG step 4: drop duplicate event_id, keep the FIRST occurrence (idempotent)."""


def dedupe_by_key(rows, key):
    """Return (kept_rows, removed_count), keeping the first row seen per key value. PURE primitive."""
    seen = set()
    kept = []
    removed = 0
    for row in rows:
        value = row.get(key)
        if value in seen:
            removed += 1
            continue
        seen.add(value)
        kept.append(row)
    return kept, removed


def step(ctx):
    kept, removed = dedupe_by_key(ctx["normalized_events"], "event_id")
    ctx["deduped_events"] = kept
    ctx["dedupe_removed"] = removed
    return ctx
'''

_GOOD_JOIN = r'''
"""join — DAG step 5: inner-join events to the vendor dimension; unmatched vendor_id -> a reject."""


def inner_join_on(left_rows, right_index, key):
    """Inner-join left_rows to right_index (a dict keyed by the join value).

    Returns (joined, unmatched). Each joined row is the left row merged with its matching right record; left
    rows whose key is absent from right_index are returned in `unmatched` (never merged). PURE primitive.
    """
    joined = []
    unmatched = []
    for row in left_rows:
        match = right_index.get(row.get(key))
        if match is None:
            unmatched.append(row)
            continue
        merged = dict(row)
        merged.update(match)
        joined.append(merged)
    return joined, unmatched


def step(ctx):
    joined, unmatched = inner_join_on(ctx["deduped_events"], ctx["dimension"], "vendor_id")
    rejects = ctx.setdefault("rejects", [])
    for row in unmatched:
        rejects.append(((row.get("event_id") or "").strip(), "unknown_vendor"))
    ctx["joined_events"] = joined
    ctx["vendors_matched"] = len(joined)
    # observability: the distinct vendor_ids that failed the dimension lookup (drives dimension-gap alerts).
    ctx["unknown_vendor_ids"] = sorted({(row.get("vendor_id") or "").strip() for row in unmatched})
    return ctx
'''

_GOOD_AGGREGATE = r'''
"""aggregate — DAG step 6: per (vendor_id, region) net_cents (ok minus refund) and event_count."""


def group_net_sum(rows, group_keys, amount_key, status_key, refund_status="refund"):
    """Group rows and compute net_cents + event_count per group. PURE primitive.

    net_cents = sum(non-refund amounts) - sum(refund amounts); event_count = number of rows in the group.
    group_keys is a tuple of row keys (e.g. ('vendor_id', 'region')). Returns {group_tuple: {net_cents, event_count}}.
    """
    aggregates = {}
    for row in rows:
        group = tuple(row.get(key) for key in group_keys)
        bucket = aggregates.setdefault(group, {"net_cents": 0, "event_count": 0})
        amount = row.get(amount_key, 0)
        if row.get(status_key) == refund_status:
            bucket["net_cents"] -= amount
        else:
            bucket["net_cents"] += amount
        bucket["event_count"] += 1
    return aggregates


def step(ctx):
    ctx["aggregates"] = group_net_sum(ctx["joined_events"], ("vendor_id", "region"), "amount_cents", "status")
    return ctx
'''

_GOOD_QUALITY = r'''
"""quality — DAG step 7: compute the pipeline metrics and write metrics.json."""
import json

from validate import summarize_rejects


def quality_metrics(input_rows, valid_rows, rejected_rows, dedupe_removed, vendors_matched, aggregates):
    """Assemble the pipeline metrics dict from the stage counts + aggregates. PURE primitive.

    total_net_cents is the sum of every group's net_cents (a data-quality reconciliation number).
    """
    total_net_cents = sum(bucket["net_cents"] for bucket in aggregates.values())
    return {
        "input_rows": input_rows,
        "valid_rows": valid_rows,
        "rejected_rows": rejected_rows,
        "dedupe_removed": dedupe_removed,
        "vendors_matched": vendors_matched,
        "total_net_cents": total_net_cents,
    }


def reconcile_totals(metrics, aggregates):
    """Assert the headline total reconciles with the sum of the per-group nets (a data-quality invariant).

    Raises ValueError if metrics['total_net_cents'] disagrees with the aggregates, so a silently-wrong roll-up
    fails the run instead of landing bad numbers. Returns True on success. PURE (read-only) check.
    """
    group_total = sum(bucket["net_cents"] for bucket in aggregates.values())
    if metrics["total_net_cents"] != group_total:
        raise ValueError("total_net_cents does not reconcile with the aggregate group nets")
    return True


def step(ctx):
    metrics = quality_metrics(
        input_rows=ctx["input_rows"],
        valid_rows=ctx["valid_rows"],
        rejected_rows=len(ctx.get("rejects", [])),
        dedupe_removed=ctx["dedupe_removed"],
        vendors_matched=ctx["vendors_matched"],
        aggregates=ctx["aggregates"],
    )
    # carry the topological execution plan through so the run is auditable end to end.
    metrics["dag_order"] = list(ctx.get("dag_order", []))
    # a deterministic reject breakdown (same input -> same roll-up), safe to persist alongside the metrics.
    metrics["rejects_by_reason"] = summarize_rejects(ctx.get("rejects", []))
    reconcile_totals(metrics, ctx["aggregates"])   # fail fast if the headline total does not reconcile
    ctx["metrics"] = metrics
    with open(ctx["metrics_path"], "w", encoding="utf-8") as fh:
        json.dump(metrics, fh, indent=2, sort_keys=True)
    return ctx
'''

_GOOD_LOAD = r'''
"""load — DAG step 8: idempotent upsert into sqlite (fact_sales_agg + rejects)."""
import sqlite3

DDL_FACT = (
    "CREATE TABLE IF NOT EXISTS fact_sales_agg ("
    "vendor_id TEXT NOT NULL, region TEXT NOT NULL, "
    "net_cents INTEGER NOT NULL, event_count INTEGER NOT NULL, "
    "PRIMARY KEY (vendor_id, region))"
)
DDL_REJECTS = (
    "CREATE TABLE IF NOT EXISTS rejects ("
    "event_id TEXT NOT NULL, reason TEXT NOT NULL, "
    "PRIMARY KEY (event_id, reason))"
)


def load_sqlite(db_path, aggregates, rejects):
    """Write aggregates + rejects into sqlite, INCREMENTALLY and IDEMPOTENTLY.

    Both tables have a primary key (fact_sales_agg by (vendor_id, region); rejects by (event_id, reason)) and
    are written with INSERT OR REPLACE, so re-running the pipeline on the same input replaces each row in place
    instead of appending — row counts and values stay stable (no double-load), while a genuinely new key from a
    later input is added. PURE-ish side effect: the only mutation is the target DB.
    """
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute(DDL_FACT)
        cur.execute(DDL_REJECTS)
        for (vendor_id, region), bucket in sorted(aggregates.items()):
            cur.execute(
                "INSERT OR REPLACE INTO fact_sales_agg (vendor_id, region, net_cents, event_count) "
                "VALUES (?, ?, ?, ?)",
                (vendor_id, region, int(bucket["net_cents"]), int(bucket["event_count"])),
            )
        seen = set()
        for event_id, reason in rejects:
            if (event_id, reason) in seen:
                continue
            seen.add((event_id, reason))
            cur.execute(
                "INSERT OR REPLACE INTO rejects (event_id, reason) VALUES (?, ?)",
                (event_id, reason),
            )
        conn.commit()
    finally:
        conn.close()


def step(ctx):
    load_sqlite(ctx["db_path"], ctx["aggregates"], ctx.get("rejects", []))
    return ctx
'''

_GOOD_RUN = r'''
"""run — CLI entry + DAG driver for the sales ETL pipeline.

    python run.py --input <events.csv> --dim <vendors.csv> --db <out.db>

Wires the ten step modules into a dependency graph and executes them in topological order over a shared context
dict. metrics.json is written next to the output DB. Re-running on the same input is idempotent (see load).
"""
import argparse
import os

import dag
import extract
import validate
import normalize
import dedupe
import join
import aggregate
import quality
import load

# the DAG dependency graph: each step lists its prerequisites. dag.run_dag executes them in topological order.
DEPS = {
    "extract": [],
    "validate": ["extract"],
    "normalize": ["validate"],
    "dedupe": ["normalize"],
    "join": ["dedupe"],
    "aggregate": ["join"],
    "quality": ["aggregate"],
    "load": ["quality"],
}

STEP_FUNCS = {
    "extract": extract.step,
    "validate": validate.step,
    "normalize": normalize.step,
    "dedupe": dedupe.step,
    "join": join.step,
    "aggregate": aggregate.step,
    "quality": quality.step,
    "load": load.step,
}


def build_context(input_path, dim_path, db_path):
    """Seed the shared context dict the steps read/write (paths + an empty rejects accumulator)."""
    db_abspath = os.path.abspath(db_path)
    metrics_path = os.path.join(os.path.dirname(db_abspath) or ".", "metrics.json")
    return {
        "input_path": input_path,
        "dim_path": dim_path,
        "db_path": db_path,
        "metrics_path": metrics_path,
        "rejects": [],
    }


def run_pipeline(input_path, dim_path, db_path):
    ctx = build_context(input_path, dim_path, db_path)
    dag.run_dag(STEP_FUNCS, DEPS, ctx)
    return ctx


def main(argv=None):
    parser = argparse.ArgumentParser(description="Sales ETL pipeline (extract -> ... -> load).")
    parser.add_argument("--input", required=True, help="raw events CSV (event_id, vendor_id, amount, ts, status)")
    parser.add_argument("--dim", required=True, help="vendor dimension CSV (vendor_id, vendor_name, region)")
    parser.add_argument("--db", required=True, help="output sqlite database path")
    parser.add_argument("--verbose", action="store_true", help="print the executed step order and per-step timings")
    args = parser.parse_args(argv)
    ctx = run_pipeline(args.input, args.dim, args.db)
    metrics = ctx["metrics"]
    timings = ctx.get("step_timings", {})
    slowest_step = max(timings, key=timings.get) if timings else "n/a"
    if args.verbose:
        print("executed_order: " + " -> ".join(ctx.get("executed_order", [])))
        for name, seconds in timings.items():
            print("  timing " + name + ": " + str(seconds) + "s")
        if ctx.get("unknown_vendor_ids"):
            print("  unknown_vendor_ids: " + ", ".join(ctx["unknown_vendor_ids"]))
    print("PIPELINE_OK"
          + " input_rows=" + str(metrics.get("input_rows"))
          + " valid_rows=" + str(metrics.get("valid_rows"))
          + " rejected_rows=" + str(metrics.get("rejected_rows"))
          + " dedupe_removed=" + str(metrics.get("dedupe_removed"))
          + " vendors_matched=" + str(metrics.get("vendors_matched"))
          + " total_net_cents=" + str(metrics.get("total_net_cents"))
          + " slowest_step=" + slowest_step)
    for reason, count in sorted(metrics.get("rejects_by_reason", {}).items()):
        print("  reject " + reason + ": " + str(count))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''

_GOOD_BUILDOUT: dict[str, str] = {
    "run.py": _GOOD_RUN,
    "dag.py": _GOOD_DAG,
    "extract.py": _GOOD_EXTRACT,
    "validate.py": _GOOD_VALIDATE,
    "normalize.py": _GOOD_NORMALIZE,
    "dedupe.py": _GOOD_DEDUPE,
    "join.py": _GOOD_JOIN,
    "aggregate.py": _GOOD_AGGREGATE,
    "quality.py": _GOOD_QUALITY,
    "load.py": _GOOD_LOAD,
}

# a BAD buildout: a single-file pipeline that RUNS (exits 0, creates the tables) but skips validation, dedupe,
# the join, and idempotency — it just dumps naive per-vendor sums of EVERY row and APPENDS on every run. It fails
# the oracle on behavior (wrong aggregates, no rejects, region missing, rerun doubles the rows).
_BAD_RUN = r'''
import argparse
import csv
import json
import os
import sqlite3


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--dim", required=True)
    parser.add_argument("--db", required=True)
    args = parser.parse_args()
    with open(args.input, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    # NO validate / NO dedupe / NO join / NO idempotency: naive sum of ALL amounts per vendor_id.
    totals = {}
    for row in rows:
        vendor_id = (row.get("vendor_id") or "").strip()
        try:
            cents = int(round(float(row.get("amount") or "0") * 100))
        except Exception:
            cents = 0
        bucket = totals.setdefault(vendor_id, [0, 0])
        bucket[0] += cents          # ignores refund sign, includes bad-amount / dup / unknown-vendor rows
        bucket[1] += 1
    conn = sqlite3.connect(args.db)
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS fact_sales_agg "
                "(vendor_id TEXT, region TEXT, net_cents INTEGER, event_count INTEGER)")
    cur.execute("CREATE TABLE IF NOT EXISTS rejects (event_id TEXT, reason TEXT)")
    for vendor_id, (net, count) in totals.items():
        cur.execute("INSERT INTO fact_sales_agg (vendor_id, region, net_cents, event_count) "
                    "VALUES (?, ?, ?, ?)", (vendor_id, "", net, count))   # APPEND -> rerun doubles
    conn.commit()
    conn.close()
    metrics_path = os.path.join(os.path.dirname(os.path.abspath(args.db)) or ".", "metrics.json")
    with open(metrics_path, "w", encoding="utf-8") as fh:
        json.dump({"input_rows": len(rows)}, fh)


if __name__ == "__main__":
    main()
'''
_BAD_BUILDOUT: dict[str, str] = {"run.py": _BAD_RUN}

# a STUB buildout: importing/running run.py raises immediately -> the pipeline never runs (run_exits_0 False).
_STUB_BUILDOUT: dict[str, str] = {"run.py": "raise NotImplementedError('pipeline not built')\n"}


# ── the BuildoutGenome (one large, non-insurance PIPELINE genome; same key shape as buildout_forge._GENOMES) ──
_GENOMES: dict[str, dict[str, Any]] = {
    "sales_etl_pipeline_dag__stdlib_sqlite__v0": {
        "product_family": "sales_etl_pipeline", "prompt_style": "data_engineer_ticket",
        "stack": "python_stdlib_sqlite", "solution_file": "run.py", "http_oracle": _PIPELINE_ORACLE_DRIVER,
        "realism_level": BUILDOUT_REALISM,
        "goal": (
            "Build a local sales-event ETL pipeline as a multi-module DAG (Python stdlib + sqlite3 ONLY; no pip, "
            "no cluster). Entry point: `python run.py --input <events.csv> --dim <vendors.csv> --db <out.db>`. "
            "Structure it as many small modules: run.py (CLI + DAG driver), dag.py (topological ordering + step "
            "runner), extract.py, validate.py, normalize.py, dedupe.py, join.py, aggregate.py, quality.py, "
            "load.py.\n"
            "Inputs: events.csv has columns event_id, vendor_id, amount, ts, status; vendors.csv (the dimension) "
            "has vendor_id, vendor_name, region.\n"
            "DAG steps, executed in TOPOLOGICAL order (extract -> validate -> normalize -> dedupe -> join -> "
            "aggregate -> quality -> load):\n"
            "- validate: flag rows with a missing event_id or vendor_id, a non-numeric or <= 0 amount, or a "
            "status not in {ok, refund}; a flagged row goes to a rejects table with a reason (NOT silently "
            "dropped).\n"
            "- normalize: amount -> integer cents, ts -> ISO date (YYYY-MM-DD), status lowercased.\n"
            "- dedupe: by event_id, keep the first occurrence (idempotent).\n"
            "- join: inner-join events to the vendor dimension on vendor_id; an unmatched vendor_id becomes a "
            "reject with reason 'unknown_vendor'.\n"
            "- aggregate: per (vendor_id, region), net_cents = sum(ok amounts) - sum(refund amounts), plus "
            "event_count.\n"
            "- quality: compute metrics {input_rows, valid_rows, rejected_rows, dedupe_removed, vendors_matched, "
            "total_net_cents} and write metrics.json.\n"
            "- load: write sqlite tables fact_sales_agg (vendor_id, region, net_cents, event_count) and rejects "
            "(event_id, reason). The load must be INCREMENTAL + IDEMPOTENT: running run.py twice on the same "
            "input must NOT double-load (upsert by key) and the metrics must be stable."),
        "primitive_targets": ["validate_event", "normalize_amount_cents", "dedupe_by_key", "inner_join_on",
                              "group_net_sum", "quality_metrics", "topological_order", "parse_iso_date"],
        "good": _GOOD_BUILDOUT, "bad": _BAD_BUILDOUT, "stub": _STUB_BUILDOUT},
}


def run_buildout(genome_id: str, files: dict[str, str], lane: str = "harness_alone",
                 extra_files: dict[str, str] | None = None) -> dict[str, Any]:
    """Write the multi-module build to an ephemeral workspace, RUN the HIDDEN pipeline oracle, receipt.
    Never returns oracle_pass=True without the pipeline running + the executed oracle passing (real sqlite)."""
    genome = _GENOMES[genome_id]
    t0 = time.time()
    proc = None
    with tempfile.TemporaryDirectory() as ws:
        wsp = Path(ws)
        for fname, content in (extra_files or {}).items():        # pre-installed verified-primitive package (reuse lane)
            (wsp / fname).parent.mkdir(parents=True, exist_ok=True)
            (wsp / fname).write_text(content, encoding="utf-8")
        for fname, content in files.items():                      # the buildout's own modules
            (wsp / fname).parent.mkdir(parents=True, exist_ok=True)
            (wsp / fname).write_text(content, encoding="utf-8")
        (wsp / "oracle.py").write_text(genome["http_oracle"], encoding="utf-8")   # hidden oracle (never shown to the build)
        try:
            proc = subprocess.run([sys.executable, "-I", "oracle.py"], cwd=ws, capture_output=True,
                                  text=True, timeout=180)
        except subprocess.TimeoutExpired:
            return {"record_type": "buildout_run_receipt", "genome_id": genome_id, "lane": lane,
                    "benchmark_kind": BENCHMARK_KIND, "realism_level": genome["realism_level"],
                    "oracle_pass": False, "error": "timeout", "oracle_checks": {}, **BOUNDARY}
        line = next((ln for ln in proc.stdout.splitlines() if ln.startswith("ORACLE ")), None)
        result = json.loads(line[len("ORACLE "):]) if line else {"checks": {}, "oracle_pass": False}
    return {"record_type": "buildout_run_receipt", "genome_id": genome_id,
            "product_family": genome["product_family"], "lane": lane, "benchmark_kind": BENCHMARK_KIND,
            "realism_level": genome["realism_level"], "n_files": len(files),
            "commands_run": [f"{Path(sys.executable).name} -I oracle.py (runs run.py + inspects out.db/metrics.json)"],
            "oracle_checks": result["checks"], "oracle_pass": bool(result["oracle_pass"]),
            "wall_time_s": round(time.time() - t0, 3),
            "stderr_tail": ((proc.stderr or "")[-200:] if (proc and not result["oracle_pass"]) else ""), **BOUNDARY}


def self_test() -> bool:
    """Mutation-gated + REAL: the reference ten-module ETL DAG RUNS as a subprocess and passes the hidden pipeline
    oracle (opens out.db + reads metrics.json, incl. an idempotent rerun); a runs-but-wrong build FAILS on
    behavior; a stub that raises on import FAILS to run. Real subprocess, real sqlite — nothing on plausibility."""
    gid = _DEFAULT_GENOME
    genome = _GENOMES[gid]

    good = run_buildout(gid, genome["good"])
    assert good["oracle_pass"] is True, f"reference pipeline must RUN + pass the hidden oracle: {good}"
    assert len(good["oracle_checks"]) >= 15 and all(good["oracle_checks"].values()), \
        f"every named check must pass: {good['oracle_checks']}"
    assert good["oracle_checks"].get("run_exits_0") is True
    assert good["oracle_checks"].get("rerun_no_double_load") is True, "the load must be idempotent on rerun"
    assert good["n_files"] == 10, f"the reference build is a ten-module DAG: {good['n_files']}"

    bad = run_buildout(gid, genome["bad"])
    assert bad["oracle_pass"] is False, f"a runs-but-wrong pipeline MUST fail the oracle (else it's fake): {bad}"
    assert bad["oracle_checks"].get("run_exits_0") is True, "the bad build still RUNS (it fails on behavior)"
    assert bad["oracle_checks"].get("rerun_agg_rows_stable") is False, "the bad append-load must double on rerun"

    stub = run_buildout(gid, genome["stub"])
    assert stub["oracle_pass"] is False and stub["oracle_checks"].get("run_exits_0") is False, \
        "a stub that raises on import must fail with run_exits_0=False"

    assert BENCHMARK_KIND == "real_project_buildout" and good["realism_level"] == "B6"
    assert good["candidate"] is True and good["serves_truth"] is False
    n_files = good["n_files"]
    n_checks = len(good["oracle_checks"])
    print(f"OK buildout_forge_pipeline self-test: reference {n_files}-module ETL DAG RUNS "
          f"(extract->validate->normalize->dedupe->join->aggregate->quality->load) + passes a HIDDEN pipeline "
          f"oracle ({n_checks} named checks over out.db + metrics.json, incl. idempotent rerun) in "
          f"{good['wall_time_s']}s; a runs-but-wrong build FAILS on behavior; a stub that raises on import FAILS; "
          f"benchmark_kind=real_project_buildout realism={good['realism_level']}; serves_truth=false")
    return True


def main() -> None:
    ap = argparse.ArgumentParser(description="BuildoutForge PIPELINE genome: run a real ETL DAG + hidden oracle.")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--genome", default=_DEFAULT_GENOME, choices=list(_GENOMES))
    ap.add_argument("--solution", default="good", choices=["good", "bad", "stub"])
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return
    if args.run:
        res = run_buildout(args.genome, _GENOMES[args.genome][args.solution])
        out_dir = resource(ARTIFACT_DIR_REL)
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / f"{args.genome}_{args.solution}_receipt.json").write_text(
            json.dumps(res, indent=2, sort_keys=True), encoding="utf-8")
        print(json.dumps(res, indent=2))
        return
    self_test()


if __name__ == "__main__":
    main()
