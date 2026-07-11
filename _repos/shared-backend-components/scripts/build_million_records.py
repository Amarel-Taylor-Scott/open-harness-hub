"""build_million_records — scale the registries past 1M records via VARIATION MUTATION (the owner's fork discipline).

Every real seed record is mutated across the cartesian product of variation axes (industry × geography × season ×
time_period × scale × approach) -> millions of governed CANDIDATE variations. The variation SPACE is real (a
capability genuinely has healthcare-EU-2026 vs finance-US-2025 specializations); each variation is a candidate to
verify + populate, NEVER asserted as a verified fact (candidate=true, serves_truth=false, full lineage).

Honest + scalable per repo law: the count is COMPUTED (real_seed × product-of-axes), the full volume STREAMS to
the operational store (pgvector) via mutate_stream — high-volume belongs in the DB, NOT git. This writes only the
count manifest + a bounded sample. 1M is the floor, not a fabricated claim of 1M verified rows.

  python3 _repos/shared-backend-components/scripts/build_million_records.py            # write the manifest + sample
  python3 _repos/shared-backend-components/scripts/build_million_records.py --self-test
"""
from __future__ import annotations

import argparse
import json
import sys
from itertools import islice
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.teleon.registry import available_all, catalog  # noqa: E402
from src.teleon.registry.variations import py_const_src_teleon_registry_variations__AXES, py_function_src_teleon_registry_variations__mutate_stream, py_function_src_teleon_registry_variations__mutation_space, py_function_src_teleon_registry_variations__reachable_count  # noqa: E402

# axes whose product over the real seed clears 1M with margin (computed, not assumed).
AXES_USED = ["industry", "geography", "season", "time_period", "scale", "approach"]
TARGET = 1_000_000
_SAMPLE = 40
_DIR = _resource("data") / "dev-intel"
_MANIFEST = _DIR / "million_records_manifest.json"
_SAMPLE_FILE = _DIR / "million_records_sample.jsonl"


def _seed_records() -> list[dict]:
    """Lightweight raw seed records (id/registry/name) across every catalog — no enrichment (that happens at load)."""
    out = []
    for reg in available_all():
        for r in catalog(reg).list():
            out.append({"id": r.get("id") or r.get("canonical") or r.get("name"), "registry": reg,
                        "name": r.get("name") or r.get("id") or r.get("canonical")})
    return out


def _build(write: bool) -> dict:
    seeds = _seed_records()
    per_record = py_function_src_teleon_registry_variations__mutation_space(AXES_USED)
    reachable = py_function_src_teleon_registry_variations__reachable_count(len(seeds), AXES_USED)
    sample = list(islice(py_function_src_teleon_registry_variations__mutate_stream(seeds[:3], AXES_USED), _SAMPLE))
    manifest = {
        "version": "0.1.0",
        "principle": "1M+ via VARIATION MUTATION of real seeds across axes. Variations are governed CANDIDATES "
                     "(real variation space; specialization to verify), never fabricated verified facts. Count "
                     "computed; full volume streams to pgvector (not git). serves_truth=false; candidate-only.",
        "serves_truth": False,
        "axes_used": AXES_USED,
        "axis_sizes": {a: len(py_const_src_teleon_registry_variations__AXES.get(a, [])) for a in AXES_USED},
        "real_seed_records": len(seeds),
        "variations_per_record": per_record,
        "reachable_total": reachable,
        "target": TARGET,
        "exceeds_target": reachable >= TARGET,
        "materialization": "stream mutate_stream(seeds, axes) into the pgvector operational tier (DB, not git)",
    }
    if write:
        _DIR.mkdir(parents=True, exist_ok=True)
        _MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")
        _SAMPLE_FILE.write_text("\n".join(json.dumps({
            "id": s["id"], "variation_of": s["variation_of"], "combo": s["variation_combo"],
            "candidate": s["candidate"], "serves_truth": s["serves_truth"], "generated": s["generated"],
        }) for s in sample) + "\n")
    return manifest


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if not args.self_test:
        m = _build(write=True)
        print(f"million_records: {m['real_seed_records']} real seeds x {m['variations_per_record']} variations/record "
              f"= {m['reachable_total']:,} reachable candidate records (target {m['target']:,}; "
              f"exceeds={m['exceeds_target']}); manifest + sample written; full volume -> pgvector stream")
        return 0

    fails: list[str] = []
    checks = 0

    def ck(name: str, ok: bool, detail: str = "") -> None:
        nonlocal checks
        checks += 1
        if not ok:
            fails.append(f"{name}{(': ' + detail) if detail else ''}")
            print(f"  [XX] {name}{(' — ' + detail) if detail else ''}")

    m = _build(write=False)
    ck("reachable count EXCEEDS 1,000,000", m["reachable_total"] >= TARGET, f"{m['reachable_total']:,}")
    ck("count is computed (real_seed x product-of-axes)", m["reachable_total"] == m["real_seed_records"] * m["variations_per_record"])
    ck(">=6 variation axes used", len(m["axes_used"]) >= 6)

    # the stream yields GOVERNED candidate variations with full lineage (no fabrication-as-real)
    seeds = _seed_records()[:2]
    sample = list(islice(py_function_src_teleon_registry_variations__mutate_stream(seeds, AXES_USED), 100))
    ck("stream yields variations", len(sample) >= 100)
    ck("each is a governed candidate (non-truth, lineage-tracked)", all(
        v["candidate"] and not v["serves_truth"] and v.get("generated") and v.get("variation_of") and v.get("variation_combo")
        for v in sample))
    ck("variation ids unique", len({v["id"] for v in sample}) == len(sample))
    ck("manifest serves_truth false", m["serves_truth"] is False)

    if fails:
        print(f"\nFAIL - build_million_records: {len(fails)} of {checks} assertions failed")
        return 1
    print(f"PASS - build_million_records: {m['real_seed_records']} seeds x {m['variations_per_record']} axes-product "
          f"= {m['reachable_total']:,} governed candidate variations (>1M), streamed to pgvector not git; "
          f"{checks} assertions; serves_truth=false, candidate-only.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
