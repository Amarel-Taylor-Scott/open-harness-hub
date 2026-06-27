#!/usr/bin/env python3
"""check_hub_population_coverage — EVERY roster hub has a working automated-contribution path (no silent gaps).

The guarantee behind "automated systems contribute to each hub": for all 22 Open*Hubs in the roster
(architecture/portfolio_connection_map.json), the strategy (architecture/hub_population_strategy.json) must declare a
COMPLETE, VALID contribution path, and no hub may be STRANDED (a generate-only hub whose generator isn't wired AND
which has no discover sources). Also enforces single-source hygiene: contribution_mode + generator names come from the
file's own legends (no-magic-values). Run before trusting hub coverage.

  python3 scripts/check_hub_population_coverage.py            # check the repo
  python3 scripts/check_hub_population_coverage.py --self-test
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CONN = REPO / "architecture" / "portfolio_connection_map.json"
STRAT = REPO / "architecture" / "hub_population_strategy.json"
_MODES = {"discover", "generate", "both"}
#: OHH-native generators wired today (mirror of generators._WIRED — checked below so this never drifts). descent_brain
#: is operator-INJECTED (reads Teleon; the dependency law keeps it out of OHH), so it isn't in the OHH-native set.
_WIRED_EXPECTED = {"method_catalog"}
#: generators that ARE wired but via operator injection (recognized as non-stranded even though not OHH-native).
_WIRED_INJECTED = {"descent_brain"}


def _roster(conn: Path) -> list[str]:
    return [h["name"] for h in json.loads(conn.read_text(encoding="utf-8")).get("hubs", [])]


def check(conn: Path = CONN, strat: Path = STRAT) -> list[str]:
    problems: list[str] = []
    roster = _roster(conn)
    s = json.loads(strat.read_text(encoding="utf-8"))
    hubs = s.get("hubs", {})
    legend_modes = set(s.get("contribution_modes", {}))
    legend_gens = set(s.get("generators", {}))

    if legend_modes != _MODES:
        problems.append(f"contribution_modes legend {sorted(legend_modes)} != {sorted(_MODES)}")
    if not legend_gens:
        problems.append("generators legend is missing/empty")

    for hub in roster:
        c = hubs.get(hub)
        if not c:
            problems.append(f"{hub}: in the roster but has NO strategy entry (no automated contribution path)")
            continue
        mode = c.get("contribution_mode")
        if mode not in _MODES:
            problems.append(f"{hub}: contribution_mode {mode!r} not one of {sorted(_MODES)}")
        if not c.get("content_kind"):
            problems.append(f"{hub}: missing content_kind")
        if not c.get("verify_bar"):
            problems.append(f"{hub}: missing verify_bar")
        fb = c.get("freshness_bar")
        if not isinstance(fb, (int, float)) or not (0.0 <= fb <= 1.0):
            problems.append(f"{hub}: freshness_bar {fb!r} not in 0..1")
        has_sources = bool(c.get("sources"))
        gen = c.get("generator", "")
        if mode in ("discover", "both") and not has_sources:
            problems.append(f"{hub}: mode={mode} but no discover sources")
        if mode in ("generate", "both"):
            if not gen:
                problems.append(f"{hub}: mode={mode} but no generator named")
            elif gen not in legend_gens:
                problems.append(f"{hub}: generator {gen!r} not in the generators legend (no-magic-values)")
        # not stranded: a generate-ONLY hub whose generator isn't wired (native or injected) must still have sources
        if mode == "generate" and gen not in (_WIRED_EXPECTED | _WIRED_INJECTED) and not has_sources:
            problems.append(f"{hub}: STRANDED — generate-only, generator {gen!r} not wired, and no discover fallback")

    # settings must resolve for every roster hub (the settings plane covers all)
    try:
        sys.path.insert(0, str(REPO))
        from src.openhubforai.hub_settings import load_settings
        for hub in roster:
            st = load_settings(hub)
            if st.validate():
                problems.append(f"{hub}: settings invalid: {st.validate()}")
    except Exception as e:  # noqa: BLE001
        problems.append(f"settings plane failed to resolve: {e}")

    # the wired set the check expects must match what generators actually wires (no drift)
    try:
        from src.openhubforai.generators import _WIRED
        if set(_WIRED) != _WIRED_EXPECTED:
            problems.append(f"generators._WIRED {sorted(_WIRED)} != expected {sorted(_WIRED_EXPECTED)} (update this check)")
    except Exception as e:  # noqa: BLE001
        problems.append(f"could not import generators._WIRED: {e}")

    return problems


def _report(problems: list[str], n_roster: int) -> int:
    if problems:
        print(f"{len(problems)} COVERAGE PROBLEM(S):")
        for p in problems:
            print(f"  - {p}")
        return 1
    print(f"PASS - hub population coverage: all {n_roster} roster hubs have a complete, valid, non-stranded "
          "contribution path (discover sources and/or a generator), settings resolve, and modes/generators are "
          "single-sourced from the strategy legends. serves_truth=false.")
    return 0


def _self_test() -> int:
    import tempfile
    fails = []
    def ck(n, ok):
        print(f"  [{'ok' if ok else 'FAIL'}] {n}")
        if not ok: fails.append(n)
    ck("the live repo passes coverage (all roster hubs covered)", check() == [])
    with tempfile.TemporaryDirectory() as d:
        # a roster hub missing from the strategy is caught
        conn = {"hubs": [{"name": "OpenGhostHub"}, {"name": "OpenToolsHub"}]}
        cp = Path(d) / "conn.json"; cp.write_text(json.dumps(conn))
        probs = check(conn=cp, strat=STRAT)
        ck("a roster hub with no strategy entry is flagged", any("OpenGhostHub" in p and "NO strategy" in p for p in probs))
        # a stranded generate-only hub is caught
        strat = {"contribution_modes": {"discover": "", "generate": "", "both": ""},
                 "generators": {"foo": ""},
                 "hubs": {"OpenToolsHub": {"content_kind": "x", "contribution_mode": "generate", "generator": "foo",
                                           "freshness_bar": 0.5, "verify_bar": "x"}}}
        sp = Path(d) / "strat.json"; sp.write_text(json.dumps(strat))
        cp2 = Path(d) / "conn2.json"; cp2.write_text(json.dumps({"hubs": [{"name": "OpenToolsHub"}]}))
        ck("a stranded generate-only hub (unwired generator, no sources) is flagged",
           any("STRANDED" in p for p in check(conn=cp2, strat=sp)))
    print("\n" + ("PASS - check_hub_population_coverage: every roster hub has a non-stranded automated contribution "
                  "path; drift (missing entry / stranded / magic generator) is caught." if not fails
                  else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    raise SystemExit(_report(check(), len(_roster(CONN))))
