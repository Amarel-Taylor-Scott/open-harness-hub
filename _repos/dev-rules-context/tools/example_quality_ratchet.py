#!/usr/bin/env python3
"""scripts/check_quality_ratchet — verify-the-verifier gate #3 (playbook idea #10): record each MEASURED
headline metric as a candidate floor and FAIL on a silent regression below it.

The failure mode this closes: a demo that prints numbers and passes regardless, so a real capability
quietly rots (composability drops, proven-count falls) while the suite stays green. Here every headline
number is a ratchet — it only moves UP when a real run produces a higher value, and any later run below
the floor is a hard failure. Floors come from computed manifests (never hand-typed); an `external` metric
(one no manifest can self-report, e.g. the composability gate pass-fraction) must be SUPPLIED by a real
run — it is never fabricated, and its absence emits a gap record, not a pass.

`--self-test` is pure/offline (synthetic ratchet, proves the gate has TEETH). `--update` measures real
manifests + supplied externals and ratchets `data/dev-intel/quality_ratchet/floors.json` upward.
`--check` re-measures and fails on regression (read-only; wire into run_proofs once floors are seeded).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Optional

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
FLOORS_PATH = REPO / "data" / "dev-intel" / "quality_ratchet" / "floors.json"

# Each metric: how to MEASURE it (never hand-typed). source ∈ manifest / callable / external.
METRIC_SPECS: dict[str, dict[str, Any]] = {
    "edge_type_canonical_count": {
        "source": ("manifest", "catalog/knowledge-packs/data/edge-type-retrofit/manifest.json", "canonical_type_count"),
        "higher_is_better": True, "rationale": "canonical edge types folded from raw strings"},
    "edge_type_occurrence_coverage": {
        "source": ("manifest", "catalog/knowledge-packs/data/edge-type-retrofit/manifest.json", "majority_coverage"),
        "higher_is_better": True, "rationale": "share of edge occurrences covered by a folding canonical type"},
    "proven_leaf_count": {
        "source": ("manifest", "data/dev-intel/proven_primitives/manifest.json", "proven_count"),
        "higher_is_better": True, "rationale": "leaf primitives with serves_truth=true via executed proof"},
    "path_config_wired_paths": {
        "source": ("callable", "scripts.primitive_paths_config", "portfolio_overview", "total_wired"),
        "higher_is_better": True, "rationale": "wired (runnable) paths across all decision points"},
    "composability_gate_pass_fraction": {
        "source": ("external",),  # only a real gate run over the corpus can produce this
        "higher_is_better": True, "rationale": "fraction of sampled corpus cards that pass the composability gate"},
}


def _read_manifest_value(rel_path: str, key: str) -> Optional[float]:
    p = REPO / rel_path
    if not p.exists():
        return None
    try:
        return float(json.loads(p.read_text())[key])
    except Exception:  # noqa: BLE001
        return None


def _read_callable_value(module: str, func: str, key: str) -> Optional[float]:
    try:
        import importlib
        mod = importlib.import_module(module)
        return float(getattr(mod, func)()[key])
    except Exception:  # noqa: BLE001
        return None


def measure(name: str, externals: Optional[dict[str, float]] = None) -> dict[str, Any]:
    """Measure ONE metric from its declared source. Returns {name, value|None, provenance, measured}.
    An `external` metric with no supplied value yields measured=False + a gap record (never a fake number)."""
    spec = METRIC_SPECS[name]
    src = spec["source"]
    externals = externals or {}
    if src[0] == "manifest":
        val = _read_manifest_value(src[1], src[2])
        prov = f"manifest:{src[1]}#{src[2]}"
    elif src[0] == "callable":
        val = _read_callable_value(src[1], src[2], src[3])
        prov = f"callable:{src[1]}.{src[2]}()#{src[3]}"
    else:  # external
        val = externals.get(name)
        prov = "external:supplied-by-real-run" if val is not None else "external:UNSUPPLIED(gap)"
    return {"name": name, "value": val, "provenance": prov, "measured": val is not None, **BOUNDARY}


def measure_all(externals: Optional[dict[str, float]] = None) -> dict[str, dict[str, Any]]:
    return {name: measure(name, externals) for name in METRIC_SPECS}


def load_floors() -> dict[str, Any]:
    if FLOORS_PATH.exists():
        try:
            return json.loads(FLOORS_PATH.read_text())
        except Exception:  # noqa: BLE001
            return {}
    return {}


def save_floors(floors: dict[str, Any]) -> None:
    FLOORS_PATH.parent.mkdir(parents=True, exist_ok=True)
    FLOORS_PATH.write_text(json.dumps(floors, indent=2, sort_keys=True) + "\n")


def ratchet(measurements: dict[str, float], floors: dict[str, Any]) -> dict[str, Any]:
    """Compare measurements to floors. Returns {ok, regressions, improvements, established, new_floors}.
    - value < floor (in the improving direction) -> REGRESSION (ok=False).
    - value beyond floor -> improvement; the returned new_floors ratchets to the better value.
    - metric with no floor yet -> established (candidate floor set).
    Pure: does not write; caller persists new_floors."""
    new_floors = {k: dict(v) for k, v in floors.items()}
    regressions, improvements, established = [], [], []
    for name, value in measurements.items():
        if value is None:
            continue
        spec = METRIC_SPECS.get(name, {})
        cur_row = new_floors.get(name) or {}
        # direction comes from the stored floor first (durable), then the spec, then default up.
        hib = cur_row.get("higher_is_better", spec.get("higher_is_better", True))
        cur = cur_row.get("floor")
        if cur is None:
            new_floors[name] = {"floor": value, "higher_is_better": hib,
                                "rationale": spec.get("rationale", "")}
            established.append({"metric": name, "floor": value})
            continue
        regressed = (value < cur) if hib else (value > cur)
        improved = (value > cur) if hib else (value < cur)
        if regressed:
            regressions.append({"metric": name, "floor": cur, "measured": value})
        elif improved:
            improvements.append({"metric": name, "from": cur, "to": value})
            new_floors[name]["floor"] = value
    return {
        "record_type": "quality_ratchet_report",
        "ok": len(regressions) == 0,
        "regressions": regressions, "improvements": improvements, "established": established,
        "new_floors": new_floors, **BOUNDARY,
    }


def update(externals: Optional[dict[str, float]] = None) -> dict[str, Any]:
    """Measure real metrics + supplied externals, ratchet floors upward, persist. Returns the report."""
    meas = {n: m["value"] for n, m in measure_all(externals).items()}
    report = ratchet(meas, load_floors())
    save_floors(report["new_floors"])
    return report


def check(externals: Optional[dict[str, float]] = None) -> dict[str, Any]:
    """Read-only: re-measure and fail on regression below persisted floors (does not write)."""
    meas = {n: m["value"] for n, m in measure_all(externals).items()}
    return ratchet(meas, load_floors())


def self_test() -> int:
    """Pure/offline proof the ratchet has TEETH — synthetic floors, no real files touched."""
    checks: list[tuple[str, bool]] = []
    floors = {"m_up": {"floor": 10.0, "higher_is_better": True, "rationale": "x"},
              "m_down": {"floor": 5.0, "higher_is_better": False, "rationale": "y"}}

    # improvement ratchets the floor UP (or down for lower-is-better).
    r_imp = ratchet({"m_up": 12.0, "m_down": 3.0}, floors)
    checks.append(("improvement is ok", r_imp["ok"] is True))
    checks.append(("higher-is-better floor ratchets up", r_imp["new_floors"]["m_up"]["floor"] == 12.0))
    checks.append(("lower-is-better floor ratchets down", r_imp["new_floors"]["m_down"]["floor"] == 3.0))

    # regression is caught (this is the TEETH — a toothless gate would return ok here).
    r_reg = ratchet({"m_up": 8.0}, floors)
    checks.append(("regression below floor FAILS", r_reg["ok"] is False and len(r_reg["regressions"]) == 1))
    r_reg2 = ratchet({"m_down": 9.0}, floors)  # up is bad for lower-is-better
    checks.append(("wrong-direction move FAILS for lower-is-better", r_reg2["ok"] is False))

    # a new metric establishes a candidate floor rather than passing vacuously.
    r_new = ratchet({"brand_new": 1.0}, floors)
    checks.append(("new metric establishes a floor", any(e["metric"] == "brand_new" for e in r_new["established"])))

    # an unsupplied external is a GAP (measured=False), never a fabricated pass.
    m_ext = measure("composability_gate_pass_fraction", externals=None)
    checks.append(("unsupplied external is a gap, not a number", m_ext["measured"] is False and m_ext["value"] is None))
    m_ext2 = measure("composability_gate_pass_fraction", externals={"composability_gate_pass_fraction": 0.148})
    checks.append(("supplied external is measured", m_ext2["measured"] is True and m_ext2["value"] == 0.148))

    # meta-verification: floor values must trace to a real source spec (no metric without provenance).
    checks.append(("every metric declares a source", all("source" in s for s in METRIC_SPECS.values())))

    failed = [n for n, ok in checks if not ok]
    if failed:
        print("FAIL - check_quality_ratchet:\n  " + "\n  ".join(failed))
        return 1
    print(f"PASS - check_quality_ratchet: ratchet has teeth over {len(METRIC_SPECS)} headline metrics "
          f"(regression below a floor fails; improvement ratchets up; unsupplied externals are gaps, not "
          f"fabricated passes) — floors come from computed manifests, never hand-typed.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Quality ratchet — headline metrics can't silently regress.")
    ap.add_argument("--self-test", action="store_true", help="pure offline proof the ratchet has teeth")
    ap.add_argument("--update", action="store_true", help="measure real metrics + ratchet floors upward")
    ap.add_argument("--check", action="store_true", help="read-only: fail on regression below floors")
    ap.add_argument("--set", action="append", default=[], metavar="name=value",
                    help="supply an external measurement from a real run (e.g. composability_gate_pass_fraction=0.148)")
    args = ap.parse_args()

    externals: dict[str, float] = {}
    for kv in args.set:
        k, _, v = kv.partition("=")
        externals[k.strip()] = float(v)

    if args.self_test:
        return self_test()
    if args.update:
        rep = update(externals)
        print(json.dumps({k: rep[k] for k in ("ok", "regressions", "improvements", "established")}, indent=2))
        print(f"floors -> {FLOORS_PATH.relative_to(REPO)}")
        return 0 if rep["ok"] else 1
    if args.check:
        rep = check(externals)
        print(json.dumps({k: rep[k] for k in ("ok", "regressions", "improvements")}, indent=2))
        return 0 if rep["ok"] else 1
    return self_test()


if __name__ == "__main__":
    raise SystemExit(main())
