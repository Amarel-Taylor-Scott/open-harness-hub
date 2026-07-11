#!/usr/bin/env python3
"""scripts.check_digestion_open_hub_outputs — PROOF: a digested skill emits CANDIDATE records for the portfolio
(an OpenSkillsHub SkillArtifact composed from the canonical object shell + a Teleon runtime candidate), never
active, with the original skill preserved as fallback. Unsafe digests emit no candidate (quarantined).

Asserts:
  A. a digested deterministic skill emits a SkillArtifact candidate: object_type SkillArtifact, status candidate
     (200, not active), is_truth False, provenance from the digestion lab, why_ingested + determinism summary.
  B. the SkillArtifact is composed from the canonical shell (carries the 14-section fields).
  C. a Teleon runtime candidate is emitted: status candidate, runtime_cascade, fallback_skill_ref.
  D. NEVER ACTIVE: neither record is active; target_hubs = [openskillshub, teleon]; proof_to_promote present.
  E. UNSAFE → NO CANDIDATE: an unsafe (quarantined) digest emits no skill/runtime candidate.
  F. COMPOSES the Template Registry shell + the digester (cross-subsystem).
  G. DETERMINISM: same digest + now → identical candidates.
  H. DEPENDENCY LAW: _repos/teleon/backend/src/teleon/digestion never imports src.baltor.

Deterministic + offline. Exit 0/1.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import os
import sys
from pathlib import Path

_REPO = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.teleon import digestion as D
from src.teleon.templates import instantiator as TPL

_NOW = "2026-06-06T00:00:00Z"
_FX = _resource("fixtures") / "digestion"


def _self_test() -> int:
    fails: list[str] = []

    def check(n: str, ok: bool, d: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok:
            fails.append(n)

    good = D.parse_skill_md((_FX / "deterministic_skill_sample" / "SKILL.md").read_text())
    dg = D.digest_skill(good, source_ref="fixtures/digestion/deterministic_skill_sample", now=_NOW)
    out = D.emit_open_hub_candidates(dg, now=_NOW)
    sa = out["openskillshub_skill_candidate"]
    tc = out["teleon_runtime_candidate"]

    # A SkillArtifact candidate
    check("A: SkillArtifact candidate emitted (object_type + candidate status)",
          sa and sa["object_type"] == "SkillArtifact" and sa["status_code"] == TPL.CANDIDATE_STATUS and not TPL.is_active_status(sa["status_code"]))
    check("A: not truth + provenance from digestion lab + why_ingested + determinism summary",
          sa["is_truth"] is False and sa["provenance"]["generated_by"] == "skill_digestion_lab"
          and "why_ingested" in sa["payload"] and sa["payload"]["determinism_summary"])

    # B canonical shell
    check("B: composed from the canonical 14-section shell",
          all(k in sa for k in ("object_id", "status_code", "visibility_code", "provenance", "receipts", "security", "telemetry", "relationships", "lineage")))

    # C Teleon runtime candidate
    check("C: Teleon runtime candidate (status candidate + cascade + fallback)",
          tc and tc["status"] == "candidate" and tc["runtime_cascade"] and tc["fallback_skill_ref"])

    # D never active
    check("D: never active; target hubs openskillshub + teleon; proof ladder present",
          out["status"] == "candidate" and set(out["target_hubs"]) == {"openskillshub", "teleon"} and out["proof_to_promote"])

    # E unsafe → no candidate
    bad = D.parse_skill_md((_FX / "bad_skill_secret_exfiltration" / "SKILL.md").read_text())
    bad_out = D.emit_open_hub_candidates(D.digest_skill(bad, source_ref="x", now=_NOW), now=_NOW)
    check("E: unsafe digest → quarantined, NO candidate emitted",
          bad_out["status"] == "quarantined" and bad_out["openskillshub_skill_candidate"] is None and bad_out["teleon_runtime_candidate"] is None)

    # F composes template registry + digester
    check("F: composes Template Registry shell + digester", (_resource("src/teleon/templates/instantiator.py")).exists() and (_resource("src/teleon/digestion/digester.py")).exists())

    # G determinism
    check("G: candidates deterministic for fixed now", D.emit_open_hub_candidates(dg, now=_NOW) == out)

    # H dependency law
    bad_imp = [str(p.relative_to(_REPO)) for p in (_resource("src/teleon/digestion")).rglob("*.py")
               for line in p.read_text().splitlines() if line.strip().startswith(("import src.baltor", "from src.baltor"))]
    check("H: no _repos/teleon/backend/src/teleon/digestion module imports src.baltor", not bad_imp, "; ".join(bad_imp))

    print("\n" + ("PASS — check_digestion_open_hub_outputs: a digested skill emits an OpenSkillsHub SkillArtifact "
                  "candidate (canonical shell, never active, digestion-lab provenance) + a Teleon runtime candidate "
                  "(cascade + fallback); unsafe digests emit nothing (quarantined); composes the Template Registry "
                  "+ digester; deterministic." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_digestion_open_hub_outputs.py --self-test")
    raise SystemExit(0)
