#!/usr/bin/env python3
"""Backs `processor/apqc-pcf-walker` (process_kind ``retrieve.tree_walk``).

Walk the APQC Process Classification Framework (Cross-Industry v7.4.0+,
~1,800 processes across 13 categories) and yield one structured knowledge
node per process. The framework itself is LICENSED content, so the parsed
rows are INJECTED (``pcf_rows`` — from the owner's licensed download); this
walker owns the tree discipline: level derived from the ``pcf_id`` dotted
depth, category from the leading number, the full ancestor path computed
from id prefixes, filters for categories / max_level / max_nodes, and
WalkStats-shaped accounting. Without rows it RAISES — framework content is
never bundled or fabricated.

Contract: deterministic; side_effects=read; on_error=raise.
Inputs pcf_variant, categories, max_level, max_nodes → nodes, walk_stats.

CLI / self-test: python3 scripts/processors/apqc_pcf_walker.py
"""
from __future__ import annotations

import json
from typing import Any

# ── Constants (No-Magic-Values) ───────────────────────────────────────────────

DEFAULT_VARIANT = "cross-industry"
#: The framework's 13 top-level categories (1.0 .. 13.0).
CATEGORY_COUNT = 13


def _level(pcf_id: str) -> int:
    """Dotted depth: '8.0'→1 (category), '8.2'→2, '8.2.1.1.1'→5."""
    parts = [p for p in pcf_id.split(".") if p != ""]
    if len(parts) == 2 and parts[1] == "0":
        return 1
    return len(parts)


def _category(pcf_id: str) -> str:
    return f"{pcf_id.split('.', 1)[0]}.0"


def _ancestors(pcf_id: str, known: set[str]) -> list[str]:
    parts = pcf_id.split(".")
    out = []
    for i in range(1, len(parts)):
        prefix = ".".join(parts[:i])
        cand = f"{prefix}.0" if i == 1 else prefix
        if cand in known and cand != pcf_id:
            out.append(cand)
    return out


def run(*, pcf_variant: str = DEFAULT_VARIANT, categories: list[str] | None = None,
        max_level: int | None = None, max_nodes: int | None = None,
        pcf_rows: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Walk the injected framework rows ({"pcf_id", "name"}) into knowledge nodes."""
    if not isinstance(pcf_variant, str) or not pcf_variant:
        raise ValueError("pcf_variant must be a non-empty str")
    if pcf_rows is None:
        raise RuntimeError("apqc_pcf_walker requires pcf_rows — the parsed rows of the "
                           "owner's LICENSED APQC download; framework content is never "
                           "bundled or fabricated")
    if max_level is not None and (not isinstance(max_level, int) or max_level < 1):
        raise ValueError(f"max_level must be a positive int, got {max_level!r}")
    if max_nodes is not None and (not isinstance(max_nodes, int) or max_nodes < 1):
        raise ValueError(f"max_nodes must be a positive int, got {max_nodes!r}")
    wanted = {str(c) for c in categories} if categories else None

    known_ids = set()
    for i, r in enumerate(pcf_rows):
        if not isinstance(r, dict) or not r.get("pcf_id") or not r.get("name"):
            raise ValueError(f"pcf_rows[{i}] needs pcf_id and name")
        known_ids.add(str(r["pcf_id"]))

    nodes: list[dict[str, Any]] = []
    skipped_category = skipped_level = 0
    truncated = False
    for r in sorted(pcf_rows, key=lambda x: [int(p) for p in str(x["pcf_id"]).split(".")]):
        pcf_id = str(r["pcf_id"])
        cat = _category(pcf_id)
        lvl = _level(pcf_id)
        if wanted is not None and cat not in wanted:
            skipped_category += 1
            continue
        if max_level is not None and lvl > max_level:
            skipped_level += 1
            continue
        if max_nodes is not None and len(nodes) >= max_nodes:
            truncated = True
            break
        nodes.append({"pcf_id": pcf_id, "name": str(r["name"]), "category": cat,
                      "level": lvl, "ancestor_path": _ancestors(pcf_id, known_ids),
                      "variant": pcf_variant,
                      "source_handle": f"apqc-pcf:{pcf_variant}#{pcf_id}"})
    return {"nodes": nodes,
            "walk_stats": {"rows_in": len(pcf_rows), "nodes_out": len(nodes),
                           "skipped_by_category": skipped_category,
                           "skipped_by_level": skipped_level,
                           "truncated_at_max_nodes": truncated,
                           "variant": pcf_variant}}


def _selftest() -> None:
    # SYNTHETIC mini-framework (shape demo only — not APQC content).
    rows = [
        {"pcf_id": "8.0", "name": "Manage Financial Resources"},
        {"pcf_id": "8.2", "name": "Perform revenue accounting"},
        {"pcf_id": "8.2.1", "name": "Process customer credit"},
        {"pcf_id": "8.2.1.1", "name": "Establish credit policies"},
        {"pcf_id": "9.0", "name": "Acquire, Construct, and Manage Assets"},
        {"pcf_id": "9.1", "name": "Plan and acquire assets"},
    ]
    out = run(pcf_rows=rows)
    by_id = {n["pcf_id"]: n for n in out["nodes"]}
    # Levels + categories derive from the id; ancestor paths are complete.
    assert by_id["8.0"]["level"] == 1 and by_id["8.2.1.1"]["level"] == 4
    assert by_id["8.2.1.1"]["category"] == "8.0"
    assert by_id["8.2.1.1"]["ancestor_path"] == ["8.0", "8.2", "8.2.1"]
    assert by_id["8.2"]["source_handle"] == "apqc-pcf:cross-industry#8.2"
    # Category + level filters with skip accounting.
    f = run(pcf_rows=rows, categories=["8.0"], max_level=2)
    assert [n["pcf_id"] for n in f["nodes"]] == ["8.0", "8.2"]
    assert f["walk_stats"]["skipped_by_category"] == 2
    assert f["walk_stats"]["skipped_by_level"] == 2
    # max_nodes truncates and SAYS so.
    t = run(pcf_rows=rows, max_nodes=3)
    assert len(t["nodes"]) == 3 and t["walk_stats"]["truncated_at_max_nodes"] is True
    # Numeric tree order (8.2.1.1 before 9.0, 10 would sort after 9).
    assert [n["pcf_id"] for n in out["nodes"]][:4] == ["8.0", "8.2", "8.2.1", "8.2.1.1"]
    # Licensed-content refusal + malformed rows raise.
    for bad in (lambda: run(),
                lambda: run(pcf_rows=[{"pcf_id": "1.0"}]),
                lambda: run(pcf_rows=rows, max_level=0)):
        raised = False
        try:
            bad()
        except (RuntimeError, ValueError):
            raised = True
        assert raised
    # Deterministic.
    assert json.dumps(run(pcf_rows=rows), sort_keys=True) == json.dumps(run(pcf_rows=rows), sort_keys=True)
    print("PASS — apqc_pcf_walker: injected licensed rows (never bundled), id-derived "
          "levels/categories/ancestor paths, category+level filters with skip "
          "accounting, reported truncation, numeric tree order verified")


if __name__ == "__main__":
    _selftest()
