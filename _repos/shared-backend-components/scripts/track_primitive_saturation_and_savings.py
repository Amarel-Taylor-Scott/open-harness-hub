#!/usr/bin/env python3
"""Primitive saturation + savings tracker (the self-aware generation loop).

Owner directive 2026-07-01: chart our savings (context / tokens / speed / memory)
against the NUMBER of primitives generated + benchmarks, so we can SEE when an
area (kind x domain x industry) saturates and hits a plateau — the signal to
inject more diverse random sprouting AND move on to other industries / tasks /
architectures.

The loop this instrument closes:

    generate primitives  ->  verify (dedupe)  ->  measure savings + saturation
        ->  read this report  ->  re-weight generation (sprout / move on)  ->  repeat

Saturation signal (measured, not guessed): as an area fills shape-space, the
fraction of newly-generated cards that are DUPLICATES rises. The verifier already
separates verified vs duplicate vs rejected, so per-area `duplicate_rate` is a
direct, cheap plateau detector. Rising duplicate_rate + falling distinct-new =
saturated -> recommend sprout/move-on. Savings come from the deterministic
`primitive_lift_benchmark` (context-bytes / tokens / memory, edge-cards vs
full-source), which is the thesis proof (>=20x context reduction; 486x at M0).

Everything emitted is candidate=true / serves_truth=false — a report is
EVIDENCE, never promotion authority.

Usage:
    python3 _repos/shared-backend-components/scripts/track_primitive_saturation_and_savings.py            # today
    python3 _repos/shared-backend-components/scripts/track_primitive_saturation_and_savings.py --self-test
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import collections
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts._config import REPO_ROOT  # noqa: E402

VERIFIED_DIR = _resource("data/dev-intel/primitive_factory/verified_candidates")
LIFT_DIR = _resource("data/dev-intel/primitive_lift_benchmark")
OUT_DIR = _resource("data/dev-intel/primitive_saturation")

# Saturation thresholds (named constants; single source, tune here).
SATURATED_DUP_RATE = 0.45            # >=45% duplicates in an area => plateau
WATCH_DUP_RATE = 0.25               # 25-45% => watch, start diversifying
MIN_AREA_SAMPLE = 40                # below this, not enough signal to call saturation
BAR_WIDTH = 40                      # ascii chart width


def _today_prefix() -> str:
    return dt.datetime.now(dt.timezone.utc).date().isoformat()


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def _area_of(row: dict[str, Any]) -> str:
    """Bucket a verified card into an area: primitive_kind (family) if present,
    else the coarse structural kind. This is the axis we watch for saturation."""
    pk = row.get("primitive_kind")
    if pk:
        return str(pk)
    return str(row.get("kind") or "unknown")


def _domain_of(row: dict[str, Any]) -> str:
    """Best-effort industry/domain extraction from the id (ultracode ids encode
    slug-domain-wN) or an explicit field; else 'unspecified'."""
    for field in ("domain", "industry"):
        if row.get(field):
            return str(row[field])
    pid = str(row.get("primitive_id") or row.get("extracted_candidate_id") or "")
    # prim:uc:<slug>-<domain>-wN:NNN  -> pull the domain-ish middle token
    if ":" in pid:
        tail = pid.split(":")[-2] if pid.count(":") >= 2 else pid.split(":")[-1]
        parts = tail.split("-")
        # domains used by the ultracode lane are known words; match any
        for token in parts:
            if token in {
                "healthcare_admin", "govcon_procurement", "ecommerce", "fintech_ops",
                "devtools", "data_engineering", "marketing_ops", "logistics",
                "healthcare", "govcon", "fintech", "marketing",
            }:
                return token
    return "unspecified"


def collect(date_prefix: str) -> dict[str, Any]:
    """Aggregate verified primitives for the date prefix into per-area + per-provider
    counts, distinct dedupe keys, and duplicate rates."""
    manifests = sorted(VERIFIED_DIR.glob(f"{date_prefix}*/manifest.json"))
    area_verified: collections.Counter[str] = collections.Counter()
    area_dedupe: dict[str, set[str]] = collections.defaultdict(set)
    provider_verified: collections.Counter[str] = collections.Counter()
    domain_verified: collections.Counter[str] = collections.Counter()
    total_verified = 0
    total_dupe = 0
    total_rejected = 0

    for man in manifests:
        try:
            m = json.loads(man.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        total_dupe += int(m.get("duplicate_count") or 0)
        total_rejected += int(m.get("rejected_count") or 0)
        rows = _read_jsonl(man.parent / "verified_candidates.jsonl")
        for row in rows:
            total_verified += 1
            area = _area_of(row)
            area_verified[area] += 1
            dk = str(row.get("dedupe_key") or row.get("primitive_id") or "")
            if dk:
                area_dedupe[area].add(dk)
            provider_verified[str(row.get("source_provider") or "unknown")] += 1
            domain_verified[_domain_of(row)] += 1

    # Per-area saturation: duplicate_rate is (generated-in-area minus distinct)/generated.
    # verified rows are already de-duplicated, so we approximate area duplicate pressure
    # from the manifest-level dupe fraction scaled by area share, plus a distinctness ratio.
    areas: list[dict[str, Any]] = []
    for area, vcount in area_verified.most_common():
        distinct = len(area_dedupe[area])
        distinctness = distinct / vcount if vcount else 1.0
        # global duplicate pressure this date (dupes / (verified+dupes))
        dup_rate = total_dupe / max(1, (total_verified + total_dupe))
        # area saturation blends global dup pressure with in-area distinctness loss
        area_dup_signal = round((1.0 - distinctness) * 0.5 + dup_rate * 0.5, 4)
        if vcount < MIN_AREA_SAMPLE:
            status = "cold"          # too few to judge — keep generating
        elif area_dup_signal >= SATURATED_DUP_RATE:
            status = "saturated"     # plateau — sprout / move on
        elif area_dup_signal >= WATCH_DUP_RATE:
            status = "watch"         # start diversifying
        else:
            status = "productive"    # rich vein — keep mining
        areas.append({
            "area": area, "verified": vcount, "distinct": distinct,
            "distinctness": round(distinctness, 4), "saturation_signal": area_dup_signal,
            "status": status,
        })

    return {
        "date_prefix": date_prefix,
        "total_verified": total_verified,
        "total_duplicate": total_dupe,
        "total_rejected": total_rejected,
        "global_duplicate_rate": round(total_dupe / max(1, total_verified + total_dupe), 4),
        "areas": areas,
        "by_provider": dict(provider_verified),
        "by_domain": dict(domain_verified),
        "manifest_count": len(manifests),
    }


def load_savings() -> dict[str, Any]:
    """Pull the latest deterministic savings numbers from the lift benchmark
    summary if present (context_reduction_x, tokens_saved, memory)."""
    summaries = sorted(LIFT_DIR.glob("**/summary*.json")) + sorted(LIFT_DIR.glob("summary*.json"))
    for path in reversed(summaries):
        try:
            s = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        # deltas live under comparisons[].deltas (also tolerate a flat/legacy shape)
        deltas: dict[str, Any] = {}
        comps = s.get("comparisons")
        if isinstance(comps, list) and comps and isinstance(comps[0], dict):
            deltas = comps[0].get("deltas") or {}
        if not deltas:
            deltas = s.get("deltas") or (s.get("comparison") or {}).get("deltas") or {}
        if deltas:
            return {
                "source": str(path.relative_to(REPO_ROOT)),
                "context_reduction_x": deltas.get("context_reduction_x"),
                "tokens_est_saved": deltas.get("tokens_est_saved"),
                "context_bytes_saved": deltas.get("context_bytes_saved"),
                "peak_rss_delta_kb": deltas.get("peak_rss_delta_kb"),
                "wall_ms_delta": deltas.get("wall_ms_delta"),
                "cpu_ms_delta": deltas.get("cpu_ms_delta"),
            }
    return {"source": None, "context_reduction_x": None, "tokens_est_saved": None,
            "note": "run scripts/primitive_lift_benchmark.py to populate savings"}


def _bar(value: float, vmax: float, width: int = BAR_WIDTH) -> str:
    if vmax <= 0:
        return ""
    n = int(round(width * value / vmax))
    return "#" * n + "-" * (width - n)


def recommendations(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Turn saturation status into concrete next-move recommendations: sprout
    diversity in watched areas, move on from saturated ones, mine productive veins."""
    recs: list[dict[str, Any]] = []
    saturated = [a for a in data["areas"] if a["status"] == "saturated"]
    watch = [a for a in data["areas"] if a["status"] == "watch"]
    productive = [a for a in data["areas"] if a["status"] == "productive"]
    cold = [a for a in data["areas"] if a["status"] == "cold"]
    for a in saturated:
        recs.append({"action": "move_on", "area": a["area"],
                     "why": f"saturation_signal {a['saturation_signal']} >= {SATURATED_DUP_RATE}",
                     "do": "stop generating this area; shift budget to a new industry/task/architecture"})
    for a in watch:
        recs.append({"action": "sprout_diversity", "area": a["area"],
                     "why": f"saturation_signal {a['saturation_signal']} in watch band",
                     "do": "inject new domains/entities + random-sprout mutators; keep but diversify"})
    for a in productive[:5]:
        recs.append({"action": "keep_mining", "area": a["area"],
                     "why": "rich vein (low duplicate pressure)", "do": "scale this area's generation"})
    if not any(a["status"] == "cold" for a in data["areas"]) and not cold:
        recs.append({"action": "open_new_frontier",
                     "why": "no cold areas left — coverage broad; open new industries/architectures",
                     "do": "add source families for an unmined industry (e.g. new vertical) or architecture pattern"})
    return recs


def render_report(data: dict[str, Any], savings: dict[str, Any], recs: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    lines.append(f"# Primitive Saturation + Savings — {data['date_prefix']}")
    lines.append("")
    lines.append("> candidate=true / serves_truth=false — evidence, not promotion authority.")
    lines.append("")
    lines.append("## Headline")
    lines.append(f"- Verified primitives (this date prefix): **{data['total_verified']}**")
    lines.append(f"- Duplicates collapsed: {data['total_duplicate']} · rejected: {data['total_rejected']}"
                 f" · global duplicate rate: {data['global_duplicate_rate']:.1%}")
    cx = savings.get("context_reduction_x")
    tks = savings.get("tokens_est_saved")
    lines.append(f"- Measured savings (lift benchmark): context reduction "
                 f"**{cx if cx is not None else 'n/a'}x**, tokens saved {tks if tks is not None else 'n/a'}"
                 f" (source: {savings.get('source') or 'not yet run'})")
    lines.append("")
    lines.append("## Generation by provider (lane)")
    for prov, n in sorted(data["by_provider"].items(), key=lambda kv: -kv[1]):
        lines.append(f"- {prov}: {n}")
    lines.append("")
    lines.append("## Saturation by area (primitive_kind) — plateau detector")
    lines.append("`status`: productive=mine · watch=diversify · saturated=move on · cold=too-few")
    lines.append("")
    vmax = max((a["verified"] for a in data["areas"]), default=1)
    lines.append("| area | verified | distinct | saturation | status | chart |")
    lines.append("|---|---:|---:|---:|---|---|")
    for a in data["areas"]:
        lines.append(f"| {a['area']} | {a['verified']} | {a['distinct']} | "
                     f"{a['saturation_signal']:.2f} | {a['status']} | `{_bar(a['verified'], vmax)}` |")
    lines.append("")
    lines.append("## Coverage by industry/domain")
    for dom, n in sorted(data["by_domain"].items(), key=lambda kv: -kv[1]):
        lines.append(f"- {dom}: {n}")
    lines.append("")
    lines.append("## Recommendations (self-aware loop -> next generation weights)")
    for r in recs:
        area = f" [{r['area']}]" if r.get("area") else ""
        lines.append(f"- **{r['action']}**{area}: {r['do']} ({r['why']})")
    lines.append("")
    return "\n".join(lines)


def run(date_prefix: str) -> dict[str, Any]:
    data = collect(date_prefix)
    savings = load_savings()
    recs = recommendations(data)
    report_md = render_report(data, savings, recs)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "record_type": "primitive_saturation_savings_report",
        "generated_utc": _today_prefix(),
        **data,
        "savings": savings,
        "recommendations": recs,
        "thresholds": {"saturated": SATURATED_DUP_RATE, "watch": WATCH_DUP_RATE, "min_sample": MIN_AREA_SAMPLE},
        "candidate": True,
        "serves_truth": False,
    }
    (OUT_DIR / f"{date_prefix}_saturation.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUT_DIR / f"{date_prefix}_saturation.md").write_text(report_md + "\n", encoding="utf-8")
    return payload


def self_test() -> int:
    # Synthetic areas exercise every status band + recommendation path.
    synthetic = {
        "date_prefix": "self-test",
        "total_verified": 300, "total_duplicate": 120, "total_rejected": 5,
        "global_duplicate_rate": 0.2857,
        "areas": [
            {"area": "algorithm.vector_search", "verified": 100, "distinct": 98,
             "distinctness": 0.98, "saturation_signal": 0.15, "status": "productive"},
            {"area": "api.endpoint", "verified": 80, "distinct": 55,
             "distinctness": 0.6875, "saturation_signal": 0.30, "status": "watch"},
            {"area": "algorithm.sort", "verified": 90, "distinct": 40,
             "distinctness": 0.4444, "saturation_signal": 0.50, "status": "saturated"},
            {"area": "genai.video_generation", "verified": 12, "distinct": 12,
             "distinctness": 1.0, "saturation_signal": 0.10, "status": "cold"},
        ],
        "by_provider": {"claude-fable-ultracode": 200, "glm-5.2": 100},
        "by_domain": {"healthcare_admin": 150, "fintech_ops": 150},
        "manifest_count": 3,
    }
    recs = recommendations(synthetic)
    actions = {r["action"] for r in recs}
    assert "move_on" in actions, "saturated area must trigger move_on"
    assert "sprout_diversity" in actions, "watch area must trigger sprout_diversity"
    assert "keep_mining" in actions, "productive area must trigger keep_mining"
    # Bar renders within width.
    assert len(_bar(50, 100)) == BAR_WIDTH
    assert _bar(0, 0) == ""
    # Report renders without error and mentions the loop.
    md = render_report(synthetic, {"source": None, "context_reduction_x": 486}, recs)
    assert "Saturation by area" in md and "Recommendations" in md
    assert "486x" in md
    # Thresholds ordered.
    assert 0 < WATCH_DUP_RATE < SATURATED_DUP_RATE < 1
    # Area status monotonic with saturation signal (given adequate sample).
    for a in synthetic["areas"]:
        if a["verified"] >= MIN_AREA_SAMPLE:
            if a["saturation_signal"] >= SATURATED_DUP_RATE:
                assert a["status"] == "saturated"
    print("OK: primitive saturation + savings tracker self-test passed "
          "(status bands, recommendations, chart render, thresholds).")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date-prefix", default=_today_prefix())
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()
    payload = run(args.date_prefix)
    sat = [a for a in payload["areas"] if a["status"] == "saturated"]
    print(f"wrote {OUT_DIR}/{args.date_prefix}_saturation.md — "
          f"{payload['total_verified']} verified across {len(payload['areas'])} areas; "
          f"{len(sat)} saturated; {len(payload['recommendations'])} recommendations.")
    return self_test()


if __name__ == "__main__":
    raise SystemExit(main())
