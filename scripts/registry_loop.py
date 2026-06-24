"""registry_loop — the registry refresh LOOP body: one pass that re-derives the whole registry surface.

Each pass: (0) auto-discover the menu [automatic, cached on import] -> (1) recompute the dependency-graph
meta-registry -> (2) rebuild records (enrich/embed/pgvector plan, honest ledger) -> (3) regenerate the MVP
showcase. Everything downstream of the registries is COMPUTED, so one pass keeps the dependency graph, the 1000+
records/registry, and the public showcase all current as registries are added/populated.

This is the loop BODY. Run it continuously via the existing orchestrator / cron / `./loop` (this process can't
hold a multi-hour daemon honestly) — e.g. `watch -n 900 python3 scripts/registry_loop.py --run`, or wire it as a
flywheel. serves_truth=false; all outputs are governed candidates.

  python3 scripts/registry_loop.py            # show the loop plan + how to schedule it
  python3 scripts/registry_loop.py --run      # execute one full refresh pass
  python3 scripts/registry_loop.py --self-test
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]

# the loop body: (label, script, args). Each is idempotent + computed; order matters (graph -> records -> mvp).
STEPS = [
    ("dependency_graph", "scripts/build_registry_dependency_graph.py", []),
    ("records", "scripts/build_registry_records.py", []),
    ("mvp_showcase", "scripts/build_capability_mvp.py", []),
]
# heavier population steps (run on a slower cadence; gated on credentials — see the roadblocks log):
POPULATION_STEPS = [
    ("kaggle_distill", "scripts/distill_kaggle_kernels.py", []),   # OH_LLM_API_KEY for the LLM path
]


def _run_one(script: str, args: list[str]) -> tuple[bool, str]:
    try:
        r = subprocess.run([sys.executable, script, *args], cwd=str(_REPO), capture_output=True, text=True,
                           timeout=300, env={"PYTHONPATH": "."})
        tail = (r.stdout or r.stderr or "").strip().splitlines()[-1:] or [""]
        return r.returncode == 0, tail[0][:140]
    except Exception as e:  # noqa: BLE001
        return False, f"{type(e).__name__}: {str(e)[:80]}"


def run(include_population: bool = False) -> int:
    steps = STEPS + (POPULATION_STEPS if include_population else [])
    bad = 0
    for label, script, args in steps:
        ok, detail = _run_one(script, args)
        print(f"  [{'ok' if ok else 'XX'}] {label}: {detail}")
        bad += 0 if ok else 1
    print(f"\nregistry_loop: {len(steps) - bad}/{len(steps)} steps green")
    return bad


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run", action="store_true", help="execute one full refresh pass")
    ap.add_argument("--with-population", action="store_true", help="also run the heavier population steps")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.run:
        return run(include_population=args.with_population)

    if args.self_test:
        checks = 0
        bad = []
        for label, script, _ in STEPS + POPULATION_STEPS:
            checks += 1
            if not (_REPO / script).exists():
                bad.append(f"{label}: missing {script}")
                print(f"  [XX] {label}: missing {script}")
        if bad:
            print(f"\nFAIL - registry_loop: {len(bad)} of {checks} steps missing")
            return 1
        print(f"PASS - registry_loop: the refresh loop wires {len(STEPS)} core + {len(POPULATION_STEPS)} population "
              f"steps (all present); run via `--run` on a cadence to keep the federation current; {checks} assertions.")
        return 0

    print("registry_loop — the registry refresh loop body. Steps:")
    for label, script, _ in STEPS:
        print(f"  - {label:18s} {script}")
    print("Population (slower cadence, credential-gated):")
    for label, script, _ in POPULATION_STEPS:
        print(f"  - {label:18s} {script}")
    print("\nrun one pass:  python3 scripts/registry_loop.py --run")
    print("schedule:      watch -n 900 'PYTHONPATH=. python3 scripts/registry_loop.py --run'   (or cron / ./loop)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
