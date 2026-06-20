#!/usr/bin/env python3
"""scripts.check_pattern_miner — proof: the pattern miner detects the repeated shapes it claims to.

Imports scripts.pattern_miner, builds the miner's own deterministic fixture tree (offline, temp dir,
cleaned up), runs the scan, and asserts: the report has the seven contracted keys; it detects the
check_* proof pattern, the API route pattern, and the docs page pattern; the detected patterns reference
real pattern_registry entries (carry registry maturity / in_registry); anti-patterns reference REAL files;
and the scan is deterministic (same input -> identical output). Also runs one read-only scan against the
real repo and asserts every example/anti-pattern path it reports actually exists (no fabricated paths).

CLI: python3 scripts/check_pattern_miner.py --self-test
"""
from __future__ import annotations

import argparse
import json
import shutil
import tempfile
from pathlib import Path

import scripts.pattern_miner as pm

_REPO = Path(__file__).resolve().parents[1]


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    # --- 1. run the miner against its deterministic fixture ---
    tmp = Path(tempfile.mkdtemp(prefix="check_pattern_miner_"))
    try:
        pm._build_fixture(tmp)
        report = pm.scan(tmp)

        check("report returns the seven contracted keys",
              set(pm.REPORT_KEYS) == set(report), str(sorted(set(report) ^ set(pm.REPORT_KEYS))))

        detected_ids = {d["pattern_id"] for d in report["detected_patterns"]}
        check("detects the check_* proof pattern", "proof_script_pattern" in detected_ids, str(sorted(detected_ids)))
        check("detects the API route pattern", "api_projection_route_pattern" in detected_ids, str(sorted(detected_ids)))
        check("detects the docs page pattern", "documentation_page_pattern" in detected_ids, str(sorted(detected_ids)))

        check("report references pattern_registry entries (maturity + in_registry on every detected)",
              all(("registry_maturity" in d and "in_registry" in d) for d in report["detected_patterns"]),
              "missing registry linkage")
        check("every detected pattern_id maps to a SHAPE_TO_PATTERN canonical id",
              detected_ids <= set(pm.SHAPE_TO_PATTERN.values()),
              str(sorted(detected_ids - set(pm.SHAPE_TO_PATTERN.values()))))

        check("anti-pattern paths reference REAL files in the fixture",
              all((tmp / a["path"]).exists() for a in report["anti_patterns"]),
              str([a["path"] for a in report["anti_patterns"] if not (tmp / a["path"]).exists()]))

        report2 = pm.scan(tmp)
        check("scan is deterministic (same input -> identical output)",
              json.dumps(report, sort_keys=True) == json.dumps(report2, sort_keys=True))

        md = pm.render_markdown(report)
        check("markdown render contains the seven section headings",
              all(h in md for h in ("Detected patterns", "Anti-patterns", "One-offs",
                                    "Waivers needed", "Candidate templates",
                                    "Recommended standard promotions", "Unstandardized repetitions")),
              "missing section heading")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # --- 2. read-only scan of the real repo: every reported path must exist (no fabrication) ---
    real = pm.scan(_REPO)
    bad_example_paths, bad_anti_paths = [], []
    for d in real["detected_patterns"]:
        for ex in d.get("examples", []):
            if not (_REPO / ex).exists():
                bad_example_paths.append(ex)
    for a in real["anti_patterns"]:
        if not (_REPO / a["path"]).exists():
            bad_anti_paths.append(a["path"])
    check("real-repo scan: every reported example path exists", bad_example_paths == [], str(bad_example_paths[:6]))
    check("real-repo scan: every anti-pattern path exists", bad_anti_paths == [], str(bad_anti_paths[:6]))
    check("real-repo scan: detected patterns map to real registry entries",
          all(d.get("in_registry") for d in real["detected_patterns"]),
          str([d["pattern_id"] for d in real["detected_patterns"] if not d.get("in_registry")]))

    print(f"\n{'PASS — check_pattern_miner: 7 report keys; detects proof/api/docs shapes; references the registry; deterministic; no fabricated paths.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: pattern miner detection contract.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
