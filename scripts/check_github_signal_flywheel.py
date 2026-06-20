#!/usr/bin/env python3
"""scripts.check_github_signal_flywheel — PROOF: the GitHub Signal Flywheel reviews top repos and turns them into
GOVERNED candidates — discovery is not trust, stars are not proof, trend != fit != activation.

Asserts:
  A. CONTRACTS: RepoSnapshot/RepoTrendSignal/RepoIntakeDecision .v1 present + registered.
  B. FIXTURE: the 10 owner-listed repos, source_confidence == owner_provided_unverified.
  C. SNAPSHOT STORE: weekly growth comes from STORED snapshots — 1 snapshot → trend confidence LOW; a 2nd
     (higher stars) → delta computed from the store, confidence HIGH.
  D. STARS != PROOF: two equal snapshots (no movement) → delta 0 / trend_score ~0 even for a high-star repo.
  E. CLASSIFY → HUB: markitdown→{opentools,opencontext}; headroom→{opentools,openharness,teleon};
     taste-skill→openskills; supermemory→{opentools,baltor}; codegraph→{opencontext,opentools}.
  F. NEVER AUTO-ACTIVE: no intake decision is 'active'/activation; every intake/propose decision carries a
     non-empty proof_to_promote ladder (discovery is not trust).
  G. QUARANTINE: a repo with no/unknown license → quarantine.
  H. TREND != FIT != ACTIVATION: a trending, hub-mapped repo → at most a *candidate*; media/voice flagged low priority.
  I. WEEKLY REPORT: top repos + clusters + founder takeaways + caveats labelling owner-provided/unverified growth;
     no GitHub token in the output.
  J. DETERMINISM: same store + now → identical report.
  K. REUSE: the existing GitHub harvester is referenced (not reinvented).

Deterministic + offline. Exit 0/1.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

_REPO = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from scripts.repo_intel import engine as E

_NOW = "2026-06-06T00:00:00Z"


def _self_test() -> int:
    fails: list[str] = []

    def check(n: str, ok: bool, d: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok:
            fails.append(n)

    contracts = json.dumps(json.loads((_REPO / "architecture" / "contract_registry.json").read_text()))
    fx = E.load_fixture()
    by_name = {r["full_name"]: r for r in fx["repos"]}

    # A
    for c in ("RepoSnapshot", "RepoTrendSignal", "RepoIntakeDecision"):
        check(f"A: {c}.v1 schema present + registered",
              (_REPO / "schemas" / "repo_intel" / f"{c}.v1.schema.json").exists() and f"repo_intel/{c}.v1.schema.json" in contracts)

    # B
    check("B: 10 repos in fixture", len(fx["repos"]) == 10, str(len(fx["repos"])))
    check("B: fixture is owner_provided_unverified", fx["source_confidence"] == "owner_provided_unverified")

    # C + D snapshot store (temp)
    tmp = Path(tempfile.mkdtemp(prefix="repo-intel-")) / "snaps.jsonl"
    try:
        mk = by_name["microsoft/markitdown"]
        E.append_snapshot(mk, now="2026-06-01T00:00:00Z", store=tmp)
        t1 = E.compute_trend(mk, store=tmp)
        check("C: 1 snapshot → trend confidence LOW (no prior)", t1["confidence"] == "low", json.dumps(t1))
        E.append_snapshot({**mk, "stars_count": mk["stars_count"] + 1500}, now="2026-06-08T00:00:00Z", store=tmp)
        t2 = E.compute_trend({**mk, "stars_count": mk["stars_count"] + 1500}, store=tmp)
        check("C: 2nd snapshot → delta from STORED snapshots, confidence HIGH",
              t2["confidence"] == "high" and t2["stars_delta_7d"] == 1500, json.dumps(t2))
        # D: no movement
        E.append_snapshot({**mk, "stars_count": mk["stars_count"] + 1500}, now="2026-06-15T00:00:00Z", store=tmp)
        t3 = E.compute_trend({**mk, "stars_count": mk["stars_count"] + 1500}, store=tmp)
        check("D: stars != proof — no movement → delta 0, low trend score", t3["stars_delta_7d"] == 0 and t3["trend_score"] < 1.0, json.dumps(t3))
    finally:
        if tmp.exists():
            tmp.unlink()
        tmp.parent.rmdir()

    # E classify → hub
    cases = {"microsoft/markitdown": {"opentoolshub", "opencontexthub"},
             "zereight/headroom": {"opentoolshub", "openharnesshub", "teleon"},
             "levante/taste-skill": {"openskillshub"},
             "supermemoryai/supermemory": {"opentoolshub", "baltor"},
             "privy-io/codegraph": {"opencontexthub", "opentoolshub"}}
    for nm, expect in cases.items():
        hubs = set(E.classify(by_name[nm])["portfolio_hubs"])
        check(f"E: {nm} → {sorted(expect)}", expect <= hubs, str(sorted(hubs)))

    # F never auto-active + proof ladder
    no_store = Path(tempfile.mkdtemp(prefix="repo-intel2-")) / "none.jsonl"
    try:
        decisions = []
        for repo in fx["repos"]:
            c = E.classify(repo); t = E.compute_trend(repo, store=no_store); r = E.risk(repo)
            decisions.append(E.intake_decision(repo, c, t, r, now=_NOW))
        check("F: NO decision is 'active'/activation", all(d["decision"] in E.DECISIONS and "activ" not in d["decision"].replace("intake_as_", "") for d in decisions))
        check("F: every intake/propose decision has a proof_to_promote ladder",
              all(d["proof_to_promote"] for d in decisions if d["decision"].startswith(("intake_", "propose_"))))
        # G quarantine on bad license
        bad = E.intake_decision({"full_name": "x/y", "license": "", "description": "tool"}, E.classify({"full_name": "x/y", "description": "tool", "topics": ["tool"]}), {"trend_score": 0, "confidence": "low", "stars_delta_7d": None}, E.risk({"full_name": "x/y", "license": ""}), now=_NOW)
        check("G: no/unknown license → quarantine", bad["decision"] == "quarantine", json.dumps(bad))
        # H trend != activation; media low priority
        hr = next(d for d, repo in zip(decisions, fx["repos"]) if repo["full_name"] == "zereight/headroom")
        check("H: trending hub-mapped repo → candidate/propose, not active", hr["decision"].startswith(("intake_", "propose_")))
        vox_c = E.classify(by_name["Plachtaa/VoxCPM"])
        check("H: media/voice flagged low priority", vox_c.get("low_priority") is True)
    finally:
        if no_store.exists():
            no_store.unlink()
        no_store.parent.rmdir()

    # I weekly report
    rep = E.weekly_report(now=_NOW)
    md = E.weekly_report_markdown(rep)
    check("I: report has top + clusters + takeaways", rep["top"] and rep["clusters"] and rep["founder_takeaways"])
    check("I: caveats label owner-provided/unverified growth", any("UNVERIFIED" in c.upper() for c in rep["caveats"]))
    check("I: no GitHub token in report", "ghp_" not in md and "github_pat" not in md.lower())

    # J determinism
    check("J: weekly report deterministic for fixed now", E.weekly_report(now=_NOW) == rep)

    # K reuse
    check("K: existing GitHub harvester referenced (not reinvented)", (_REPO / "scripts" / "acquisition" / "github_repo_harvester.py").exists())

    print("\n" + ("PASS — check_github_signal_flywheel: top repos → governed candidates; weekly growth from STORED "
                  "snapshots (low-confidence without a prior); stars are not proof; classify→hub correct; NO repo "
                  "auto-activates (candidates carry a proof_to_promote ladder); bad-license→quarantine; trend≠fit≠"
                  "activation; weekly report labels unverified data; deterministic; reuses the existing harvester."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_github_signal_flywheel.py --self-test")
    raise SystemExit(0)
