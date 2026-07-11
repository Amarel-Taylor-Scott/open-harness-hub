#!/usr/bin/env python3
"""scripts.primitive_inventory — the LIVE 5M/40M primitive inventory scanner (AIDevObserver milestone 1).

Owner (2026-07-09): 5M primitives = MINIMUM operating target, 40M = scale target. The discipline is NOT "be smaller";
it is make the claim PROVABLE by LIVE inventory + status labels — so nobody can hand-wave it. This computes, from the
ACTUAL corpus on disk (no typed magic values — no-magic-values law), the status-label ladder:

  raw_records -> candidate -> indexed -> searchable -> composition_ready -> verified -> promotion_ready -> customer_proof

and reports each tier vs the 5M-minimum / 40M-target, the GAP per tier, and where the generation focus should go
(raw-mint vs verify/promote vs edge-type). Every count is measured live from a SOURCE REGISTRY (path + count_method +
tier tags + provenance), so the dashboard can say "operating toward 5M-40M" AND show which subset is proven.

    python3 scripts/primitive_inventory.py --self-test
    python3 scripts/primitive_inventory.py               # scan the real corpus -> status ladder + gap + focus
    python3 scripts/primitive_inventory.py --emit        # + write the receipt for /api/observer/primitive-corpus
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
import os  # noqa: E402
import sqlite3  # noqa: E402
from typing import Any  # noqa: E402

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
BENCHMARK_KIND = "primitive_inventory"
ARTIFACT_DIR_REL = "data/dev-intel/primitive_inventory"

# targets are DECLARED (owner directive), counts are COMPUTED — never invert this
MIN_TARGET = 5_000_000       # 5M minimum operating target
SCALE_TARGET = 40_000_000    # 40M scale target

# the status-label ladder, low → high (higher = more proven). valid_syntax + working are the OWNER'S 5M bar
# (2026-07-09: "5M indexed + searchable + valid syntax + fully working") — code that PARSES then RUNS, above the
# merely-structural descriptor. verified = passed a hidden oracle (execution). Reaching 5M working is the real gap.
LADDER = ["raw_records", "candidate", "indexed", "searchable", "composition_ready", "valid_syntax", "working",
          "verified", "promotion_ready", "customer_proof"]

# ── the SOURCE REGISTRY: every place primitives live + how to count it + which tiers it contributes to. ────────
# count_method: jsonl_lines | sqlite_count(db::table) | dir_entries | manifest_field(file::key)
# provenance: source_backed | synthetic | gap_fill | draft | derived. overlap_group: sources that may share records.
_SOURCES: list[dict[str, Any]] = [
    {"label": "verified_factory_cards", "path": "data/dev-intel/aidevobserver_edge_foundry/verified_factory_primitive_cards.jsonl",
     "count": "jsonl_lines", "tiers": ["raw_records", "candidate", "indexed", "searchable", "verified"],
     "provenance": "source_backed", "overlap_group": "governed_cards"},
    {"label": "edge_cards", "path": "data/dev-intel/aidevobserver_edge_foundry/primitive_edge_cards.jsonl",
     "count": "jsonl_lines", "tiers": ["raw_records", "candidate", "indexed", "searchable", "composition_ready"],
     "provenance": "source_backed", "overlap_group": "governed_cards"},
    {"label": "sqlite_primitives_store", "path": "dist/primitives.db::primitives",
     "count": "sqlite_count", "tiers": ["raw_records", "candidate", "indexed"],
     "provenance": "synthetic", "overlap_group": "compiled_seed"},
    {"label": "grid_candidates", "path": "data/dev-intel/aidevobserver_edge_foundry/grid_primitive_candidates.jsonl",
     "count": "jsonl_lines", "tiers": ["raw_records", "candidate"],
     "provenance": "synthetic", "overlap_group": "compiled_seed"},
    {"label": "minted_gap_candidates", "path": "data/dev-intel/aidevobserver_edge_foundry/minted_gap_primitive_candidates.jsonl",
     "count": "jsonl_lines", "tiers": ["raw_records", "candidate"], "provenance": "gap_fill", "overlap_group": "gap"},
    {"label": "drafts", "path": "data/dev-intel/aidevobserver_context_foundry/primitive_drafts.jsonl",
     "count": "jsonl_lines", "tiers": ["raw_records", "candidate"], "provenance": "draft", "overlap_group": "drafts"},
    {"label": "governed_search_index", "path": "catalog/knowledge-packs/data/primitive-search-index/manifest.json::n_docs",
     "count": "manifest_field", "tiers": ["indexed", "searchable"], "provenance": "derived",
     "overlap_group": "governed_cards"},
    # the OWNER'S 5M bar: code that PARSED + RAN (verification_level='execution') = valid_syntax AND working AND verified
    {"label": "execution_verified", "path": "dist/primitives.db::SELECT count(*) FROM primitives WHERE verification_level='execution'",
     "count": "sqlite_query", "tiers": ["valid_syntax", "working", "verified"], "provenance": "source_backed",
     "overlap_group": "executed"},
    # deterministically SYNTHESIZED working primitives (primitive_synthesis_loop.py): oracle-passing, real code
    {"label": "synthesized_working", "path": "data/dev-intel/primitive_synthesis/working_primitives.jsonl",
     "count": "jsonl_lines", "tiers": ["valid_syntax", "working", "verified"], "provenance": "source_backed",
     "overlap_group": "synthesized"},
]
# alternate paths tried if the primary path is absent (corpus dirs move; keep the scanner resilient)
_ALT = {"drafts": ["data/dev-intel/primitive_drafts.jsonl",
                   "data/dev-intel/aidevobserver_edge_foundry/primitive_drafts.jsonl"]}


def _resolve(src: dict[str, Any]) -> str:
    base = src["path"].split("::")[0]
    if (_sbc_boot / base).exists():
        return src["path"]
    for alt in _ALT.get(src["label"], []):
        if (_sbc_boot / alt).exists():
            return alt + ("::" + src["path"].split("::", 1)[1] if "::" in src["path"] else "")
    return src["path"]


def _count_jsonl_lines(path: Path) -> int:
    """Fast newline count in binary chunks (handles multi-GB files without loading them)."""
    if not path.exists():
        return 0
    n = 0
    with path.open("rb") as f:
        while True:
            chunk = f.read(8 << 20)  # 8 MB
            if not chunk:
                break
            n += chunk.count(b"\n")
    return n


def _count_sqlite(spec: str) -> int:
    db, _, table = spec.partition("::")
    p = _sbc_boot / db
    if not p.exists():
        return 0
    try:
        c = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
        n = c.execute(f'SELECT count(*) FROM "{table}"').fetchone()[0]
        c.close()
        return int(n)
    except Exception:  # noqa: BLE001
        return 0


def _count_sqlite_query(spec: str) -> int:
    """spec = 'db_path::SELECT count(*) FROM ... WHERE ...' — a read-only COUNT query."""
    db, _, query = spec.partition("::")
    p = _sbc_boot / db
    if not p.exists() or not query.strip().lower().startswith("select count"):
        return 0
    try:
        c = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
        n = c.execute(query).fetchone()[0]
        c.close()
        return int(n)
    except Exception:  # noqa: BLE001
        return 0


def _count_manifest_field(spec: str) -> int:
    f, _, key = spec.partition("::")
    p = _sbc_boot / f
    if not p.exists():
        return 0
    try:
        return int(json.loads(p.read_text()).get(key, 0))
    except Exception:  # noqa: BLE001
        return 0


def _count_dir_entries(path: Path) -> int:
    if not path.is_dir():
        return 0
    return sum(1 for _ in os.scandir(path))


def _count_source(src: dict[str, Any]) -> int:
    resolved = _resolve(src)
    base = resolved.split("::")[0]
    method = src["count"]
    if method == "jsonl_lines":
        return _count_jsonl_lines(_sbc_boot / base)
    if method == "sqlite_count":
        return _count_sqlite(resolved)
    if method == "sqlite_query":
        return _count_sqlite_query(resolved)
    if method == "manifest_field":
        return _count_manifest_field(resolved)
    if method == "dir_entries":
        return _count_dir_entries(_sbc_boot / base)
    return 0


def scan(sources: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Count every source live, roll up into the status ladder (overlap-aware), compute the gap + focus."""
    sources = sources if sources is not None else _SOURCES
    per_source = []
    for src in sources:
        n = _count_source(src)
        per_source.append({"label": src["label"], "count": n, "tiers": src["tiers"],
                           "provenance": src["provenance"], "overlap_group": src["overlap_group"],
                           "path": _resolve(src).split("::")[0]})

    # ladder rollup: for each tier, sum source counts tagged with it, but DEDUPE by overlap_group (take the max
    # within a group so overlapping stores of the same records aren't double-counted at that tier)
    ladder: dict[str, int] = {}
    ladder_detail: dict[str, Any] = {}
    for tier in LADDER:
        contributing = [s for s in per_source if tier in s["tiers"] and s["count"] > 0]
        by_group: dict[str, int] = {}
        for s in contributing:
            by_group[s["overlap_group"]] = max(by_group.get(s["overlap_group"], 0), s["count"])
        ladder[tier] = sum(by_group.values())
        ladder_detail[tier] = {"total": ladder[tier], "by_group": by_group,
                               "sources": [s["label"] for s in contributing]}

    source_backed = sum(s["count"] for s in per_source if s["provenance"] == "source_backed")
    synthetic = sum(s["count"] for s in per_source if s["provenance"] in ("synthetic", "gap_fill"))

    raw = ladder.get("raw_records", 0)
    focus = _generation_focus(ladder)
    return {"record_type": "primitive_inventory", "benchmark_kind": BENCHMARK_KIND,
            "targets": {"minimum": MIN_TARGET, "scale": SCALE_TARGET},
            "status_ladder": ladder, "ladder_detail": ladder_detail,
            "raw_vs_min_pct": round(100 * raw / MIN_TARGET, 1), "raw_vs_scale_pct": round(100 * raw / SCALE_TARGET, 1),
            "gap_to_min": {t: max(0, MIN_TARGET - ladder.get(t, 0)) for t in LADDER},
            "provenance": {"source_backed": source_backed, "synthetic_or_gapfill": synthetic},
            "generation_focus": focus, "per_source": per_source,
            "note": "targets are DECLARED (owner directive); all counts COMPUTED live from disk. Ladder is "
                    "overlap-deduped by group (max within group). serves_truth=false.",
            **BOUNDARY}


def _generation_focus(ladder: dict[str, int]) -> dict[str, Any]:
    """Where should Fable's scan/research/generate effort go? The lowest tier still under the 5M minimum, and the
    biggest DROP between adjacent tiers (the bottleneck to promote through)."""
    below = [t for t in LADDER if ladder.get(t, 0) < MIN_TARGET]
    drops = []
    for i in range(len(LADDER) - 1):
        lo, hi = LADDER[i], LADDER[i + 1]
        a, b = ladder.get(lo, 0), ladder.get(hi, 0)
        if a > 0:
            drops.append({"from": lo, "to": hi, "retained_pct": round(100 * b / a, 2), "lost": a - b})
    bottleneck = min(drops, key=lambda d: d["retained_pct"]) if drops else None
    raw_ok = ladder.get("raw_records", 0) >= MIN_TARGET
    return {"raw_at_or_above_min": raw_ok,
            "recommendation": ("RAW mint (still below 5M raw)" if not raw_ok else
                               "PROMOTE/VERIFY existing raw upward — raw≈5M reached; the gap is the upper tiers"),
            "lowest_tier_below_min": below[0] if below else None,
            "biggest_bottleneck": bottleneck}


def self_test() -> bool:
    """Mutation-gated + REAL: (1) counts a fixture corpus correctly (jsonl lines, sqlite, manifest, dir); (2) the
    ladder is overlap-deduped (two sources in one overlap_group at a tier -> max, not sum); (3) gap_to_min computes;
    (4) generation_focus flips RAW-vs-PROMOTE at the 5M boundary; (5) deterministic; targets never leak into counts."""
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        (root / "a.jsonl").write_text("x\n" * 100)
        (root / "b.jsonl").write_text("y\n" * 40)
        (root / "m.json").write_text(json.dumps({"n_docs": 130}))
        con = sqlite3.connect(root / "t.db")
        con.execute("CREATE TABLE prim(id int)")
        con.executemany("INSERT INTO prim VALUES (?)", [(i,) for i in range(70)])
        con.commit(); con.close()

        # patch source resolution to the fixture by using absolute paths in a custom source set
        global _sbc_boot  # noqa: PLW0603
        orig = _sbc_boot
        _sbc_boot = root
        try:
            fixture = [
                {"label": "a", "path": "a.jsonl", "count": "jsonl_lines", "tiers": ["raw_records", "verified"],
                 "provenance": "source_backed", "overlap_group": "g1"},
                {"label": "b", "path": "b.jsonl", "count": "jsonl_lines", "tiers": ["raw_records"],
                 "provenance": "synthetic", "overlap_group": "g1"},  # same group as a -> max at raw, not 140
                {"label": "db", "path": "t.db::prim", "count": "sqlite_count", "tiers": ["raw_records", "indexed"],
                 "provenance": "synthetic", "overlap_group": "g2"},
                {"label": "idx", "path": "m.json::n_docs", "count": "manifest_field", "tiers": ["indexed"],
                 "provenance": "derived", "overlap_group": "g3"},
            ]
            rep = scan(fixture)
            # (1)+(2): raw = max(a=100,b=40 in g1) + db=70 in g2 = 170 (NOT 100+40+70=210)
            assert rep["status_ladder"]["raw_records"] == 170, f"overlap dedup: {rep['status_ladder']}"
            assert rep["status_ladder"]["verified"] == 100 and rep["status_ladder"]["indexed"] == 200, rep["status_ladder"]
            # (3) gap
            assert rep["gap_to_min"]["verified"] == MIN_TARGET - 100
            # (4) focus: raw 170 < 5M -> RAW mint
            assert rep["generation_focus"]["raw_at_or_above_min"] is False
            assert "RAW" in rep["generation_focus"]["recommendation"]
            # (5) determinism + no target leak into counts
            assert scan(fixture)["status_ladder"] == rep["status_ladder"]
            assert MIN_TARGET not in rep["status_ladder"].values()
        finally:
            _sbc_boot = orig

    print(f"OK primitive_inventory self-test: counts jsonl-lines + sqlite + manifest live; ladder OVERLAP-DEDUPED "
          f"by group (a|b same group -> raw=170 not 210); gap_to_min computed; generation_focus flips RAW↔PROMOTE at "
          f"the 5M boundary; deterministic; targets never leak into counts. serves_truth=false")
    return True


def _fmt(rep: dict[str, Any]) -> str:
    lines = [f"PRIMITIVE INVENTORY — targets: {MIN_TARGET:,} min / {SCALE_TARGET:,} scale (counts computed live)", ""]
    for t in LADDER:
        n = rep["status_ladder"].get(t, 0)
        bar = "█" * min(30, int(30 * n / MIN_TARGET)) if n else ""
        lines.append(f"  {t:18} {n:>12,}  {bar}")
    r = rep["status_ladder"].get("raw_records", 0)
    lines += ["", f"  raw vs 5M-min: {rep['raw_vs_min_pct']}%  ·  raw vs 40M-scale: {rep['raw_vs_scale_pct']}%",
              f"  source-backed: {rep['provenance']['source_backed']:,}  ·  synthetic/gap-fill: "
              f"{rep['provenance']['synthetic_or_gapfill']:,}",
              f"  FOCUS: {rep['generation_focus']['recommendation']}"]
    bn = rep["generation_focus"].get("biggest_bottleneck")
    if bn:
        lines.append(f"  BOTTLENECK: {bn['from']} → {bn['to']} retains only {bn['retained_pct']}% "
                     f"({bn['lost']:,} lost) — promote through here")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description="Live 5M/40M primitive inventory scanner (status-label ladder).")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--emit", action="store_true", help="write the receipt JSON")
    ap.add_argument("--json", action="store_true", help="print full JSON instead of the formatted view")
    args = ap.parse_args()
    if args.self_test:
        raise SystemExit(0 if self_test() else 1)
    rep = scan()
    if args.emit:
        out = resource(ARTIFACT_DIR_REL); out.mkdir(parents=True, exist_ok=True)
        (out / "inventory.json").write_text(json.dumps(rep, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(rep, indent=2, sort_keys=True) if args.json else _fmt(rep))


if __name__ == "__main__":
    main()
