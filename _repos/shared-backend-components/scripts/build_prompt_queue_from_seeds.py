#!/usr/bin/env python3
"""scripts.build_prompt_queue_from_seeds — turn the MILLION-row compact seed packs into a bounded PROMPT QUEUE.

The owner's `generated_primitive_packs/*.zip` bundles (million_primitive_variation_pack, naics 300k, atlas 1m+ seed)
hold ~1M compact VARIATION SEEDS — one row per (family × industry × region × object × schema × transform × runtime).
You cannot make a model call per seed (cost/time), and each seed is too skinny to be a primitive on its own. So we
CLUSTER seeds by (domain, family) and emit ONE prompt brief per cluster: the brief tells a generation lane which
variation axes the family spans and gives representative base_edges, then asks it to emit the family's MEMBER
primitives (variations captured as variation_profile metadata, not N restated rows). The queue is a durable JSONL
drained incrementally by the Fable/Ollama lanes → verify → registry bridge.

Streams the .tsv members straight out of the .zip (no full extraction); deterministic (clusters in first-seen
order, base_edges sampled by first-K-distinct — no RNG); bounded by --max-rows with the cap RECORDED in the manifest
(never a silent truncation). Every brief candidate=true / serves_truth=false.
CLI: --self-test | --write --zip <path> [--max-rows N] [--per-cluster-edges K] [--date D] [--out PATH].
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import csv
import datetime as dt
import hashlib
import io
import json
import sys
import zipfile
from pathlib import Path
from typing import Any, Iterator

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

DEFAULT_OUT = _resource("data") / "dev-intel" / "primitive_factory" / "prompt_queue"
AXIS_COLS = ("industry", "region", "jurisdiction", "role", "schema_standard", "data_shape", "transform",
             "runtime_target", "package_target")
MAX_AXIS_VALUES = 12  # cap distinct values recorded per axis (a brief is a summary, not a dump)


def _iter_tsv_rows(zip_path: Path, *, max_rows: int) -> Iterator[dict[str, str]]:
    """Stream rows across every .tsv member of the zip, up to max_rows total."""
    seen = 0
    with zipfile.ZipFile(zip_path) as zf:
        for name in sorted(zf.namelist()):
            if not name.endswith(".tsv"):
                continue
            with zf.open(name) as raw:
                reader = csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8"), delimiter="\t")
                for row in reader:
                    yield row
                    seen += 1
                    if seen >= max_rows:
                        return


def cluster_seeds(zip_path: Path, *, max_rows: int, per_cluster_edges: int) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    clusters: dict[tuple[str, str], dict[str, Any]] = {}
    order: list[tuple[str, str]] = []
    rows_scanned = 0
    for row in _iter_tsv_rows(zip_path, max_rows=max_rows):
        rows_scanned += 1
        domain = (row.get("pack_id") or "unknown").strip()
        family = (row.get("family") or "unknown").strip()
        key = (domain, family)
        c = clusters.get(key)
        if c is None:
            c = {"domain": domain, "family": family, "seed_count": 0,
                 "axes": {a: [] for a in AXIS_COLS}, "base_edges": [], "record_types": [], "model_lanes": []}
            clusters[key] = c
            order.append(key)
        c["seed_count"] += 1
        for a in AXIS_COLS:
            v = (row.get(a) or "").strip()
            if v and v not in c["axes"][a] and len(c["axes"][a]) < MAX_AXIS_VALUES:
                c["axes"][a].append(v)
        ie, oe = (row.get("input_edge") or "").strip(), (row.get("output_edge") or "").strip()
        if ie and oe:
            edge = f"{ie} -> {oe}"
            if edge not in c["base_edges"] and len(c["base_edges"]) < per_cluster_edges:
                c["base_edges"].append(edge)
        rt = (row.get("record_type") or "").strip()
        if rt and rt not in c["record_types"]:
            c["record_types"].append(rt)
        ml = (row.get("model_lane") or "").strip()
        if ml and ml not in c["model_lanes"]:
            c["model_lanes"].append(ml)

    briefs: list[dict[str, Any]] = []
    for key in order:
        c = clusters[key]
        # target: one member primitive per ~distinct base-edge shape, min 8, capped 40 (a brief is a shard)
        target = max(8, min(len(c["base_edges"]) * 4, 40))
        bid = "sqb:" + hashlib.sha256(f"{c['domain']}::{c['family']}".encode()).hexdigest()[:16]
        briefs.append({
            "record_type": "seed_cluster_prompt_brief",
            "brief_id": bid,
            "domain": c["domain"],
            "family": c["family"],
            "seed_count": c["seed_count"],
            "variation_axes": {a: v for a, v in c["axes"].items() if v},
            "base_edges": c["base_edges"],
            "record_types": c["record_types"],
            "model_lane_hint": c["model_lanes"][:3],
            "target_rows": target,
            "instruction": (
                f"Family '{c['family']}' in domain '{c['domain']}'. Emit {target} MEMBER primitive/primitive_group "
                f"candidates that decompose this family across the base_edges shown. Capture the variation_axes "
                f"(industry/region/schema/transform/runtime) as a variation_profile field on each row, NOT as "
                f"separate restated rows. Full verifier schema; candidate=true, serves_truth=false; official public "
                f"https source_refs; proof_requirements incl candidate_boundary_gate."),
            "candidate": True,
            "serves_truth": False,
        })
    stats = {
        "record_type": "seed_prompt_queue_manifest",
        "zip": zip_path.name,
        "rows_scanned": rows_scanned,
        "max_rows_cap": max_rows,
        "capped": rows_scanned >= max_rows,
        "clusters": len(briefs),
        "total_target_rows": sum(b["target_rows"] for b in briefs),
        "candidate": True,
        "serves_truth": False,
    }
    return briefs, stats


def write_queue(zip_path: Path, out_path: Path, *, max_rows: int, per_cluster_edges: int) -> dict[str, Any]:
    briefs, stats = cluster_seeds(zip_path, max_rows=max_rows, per_cluster_edges=per_cluster_edges)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("".join(json.dumps(b, ensure_ascii=False, sort_keys=True) + "\n" for b in briefs),
                        encoding="utf-8")
    (out_path.with_suffix(".manifest.json")).write_text(
        json.dumps(stats, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    stats["queue_path"] = str(out_path.relative_to(REPO)) if out_path.is_relative_to(REPO) else str(out_path)
    return stats


def self_test() -> int:
    # synthetic 2-family, 4-row TSV in a temp zip (never touches the real packs)
    import tempfile
    hdr = "record_id\trow_global\tpack_id\trecord_type\tfamily\ttitle\tindustry\tregion\tjurisdiction\trole\tbusiness_object\tschema_standard\tdata_shape\ttransform\tinput_edge\toutput_edge\truntime_target\tpackage_target\tsource_ref_families\tknown_implementation_families\teffects\tguardrail\tmutators\tremix_methods\tproof_requirements\tbenchmark_hook\tmodel_lane\ttelemetry_signals\tcache_key_hint\tsearch_query\tnext_actions\tevidence_level\tcandidate\tserves_truth"
    def row(fam, ie, oe, ind):
        cols = ["c1", "1", "auth", "primitive", fam, f"{fam} t", ind, "US", "fed", "eng", "account", "JSON_Schema",
                "enum", "extract", ie, oe, "local_python", "npm", "OpenAPI_spec", "impl", "artifact_write", "g",
                "m", "r", "candidate_boundary_gate", "b", "glm", "t", "k", "q", "n", "L1", "true", "false"]
        return "\t".join(cols)
    tsv = "\n".join([hdr,
                     row("credential_login", "A+P", "B+R", "enterprise_software"),
                     row("credential_login", "C+P", "D+R", "public_sector"),
                     row("email_verification", "E+P", "F+R", "retail"),
                     row("email_verification", "G+P", "H+R", "healthcare")])
    with tempfile.TemporaryDirectory() as td:
        zp = Path(td) / "t.zip"
        with zipfile.ZipFile(zp, "w") as zf:
            zf.writestr("data/tsv/01_x_25000.tsv", tsv)
        briefs, stats = cluster_seeds(zp, max_rows=1000, per_cluster_edges=8)
    fams = {b["family"] for b in briefs}
    checks = [
        ("clusters by family", fams == {"credential_login", "email_verification"}),
        ("2 briefs from 4 seeds (2 per family)", len(briefs) == 2),
        ("seed_count aggregated", all(b["seed_count"] == 2 for b in briefs)),
        ("variation axes captured", all(len(b["variation_axes"]["industry"]) == 2 for b in briefs)),
        ("base_edges collected distinct", all(len(b["base_edges"]) == 2 for b in briefs)),
        ("target_rows bounded 8..40", all(8 <= b["target_rows"] <= 40 for b in briefs)),
        ("brief_id is deterministic hash", all(b["brief_id"].startswith("sqb:") and len(b["brief_id"]) == 20 for b in briefs)),
        ("boundary held", all(b["candidate"] is True and b["serves_truth"] is False for b in briefs)),
        ("instruction says variation_profile not restated rows", all("variation_profile" in b["instruction"] for b in briefs)),
        ("manifest records the cap honestly", stats["max_rows_cap"] == 1000 and "capped" in stats),
    ]
    failed = [n for n, ok in checks if not ok]
    if failed:
        print("FAIL - build_prompt_queue_from_seeds:\n  " + "\n  ".join(failed))
        return 1
    print("PASS - build_prompt_queue_from_seeds: seeds cluster by family into bounded prompt briefs "
          "(axes summarized, base_edges sampled, target bounded, cap recorded).")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--zip", default=None)
    parser.add_argument("--max-rows", type=int, default=200_000)
    parser.add_argument("--per-cluster-edges", type=int, default=8)
    parser.add_argument("--date", default=None)
    parser.add_argument("--out", default=None)
    args = parser.parse_args(argv)
    if args.self_test and not args.write:
        return self_test()
    if not args.zip:
        parser.error("--write requires --zip <path>")
    date = args.date or dt.datetime.now(dt.timezone.utc).date().isoformat()
    out = Path(args.out) if args.out else (DEFAULT_OUT / f"{date}-seed-queue.jsonl")
    stats = write_queue(Path(args.zip), out, max_rows=args.max_rows, per_cluster_edges=args.per_cluster_edges)
    print(json.dumps(stats, indent=2, sort_keys=True))
    return self_test()


if __name__ == "__main__":
    raise SystemExit(main())
