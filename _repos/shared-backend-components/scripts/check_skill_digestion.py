#!/usr/bin/env python3
"""scripts.check_skill_digestion — PROOF: the Skill Digestion Lab turns an expensive skill into a cheaper
DETERMINISTIC runtime candidate (keeping the original as fallback), parses skills WITHOUT executing them, and
quarantines unsafe skills. Discovery≠trust; promotion needs sandbox+eval+redteam.

Asserts:
  A. CONTRACTS: SkillDigestRun/DeterminismExtractionReport/SkillToRuntimeCandidate  present + registered.
  B. PARSE-ONLY: the deterministic SKILL.md parses to metadata; the adapter NEVER executes (no exec/subprocess/os.system).
  C. DETERMINISM EXTRACTION: the deterministic sample yields the expected substeps (allowlist · ranking · parser ·
     http_fetch_first · conflict_holdout) + a cheap→expensive cascade incl deterministic, confidence high.
  D. DIGEST: capability/I-O contracts + required tools/models inferred; decision = candidate (NOT active);
     fallback_skill_ref preserved; proof_to_promote includes sandbox_run + redteam.
  E. RUNTIME CANDIDATE: status candidate (never active); cascade + fallback + is_truth False.
  F. UNSAFE → QUARANTINE: the secret-exfil skill is flagged (secret env + exfil + log-destruction) → quarantine.
  G. NEVER AUTO-ACTIVE: no digest decision is 'active'; promotion always needs the proof ladder.
  H. COMPOSES SANDBOX: sandbox_run is in proof_to_promote AND the Sandbox Gateway contract exists (a sandbox run
     is required before a digested candidate promotes).
  I. DETERMINISM: digesting the same skill twice (fixed now) is identical.
  J. DEPENDENCY LAW: no module under _repos/teleon/backend/src/teleon/digestion imports src.baltor.

Deterministic + offline. Exit 0/1.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import json
import os
import sys
from pathlib import Path

_REPO = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.teleon import digestion as D

_NOW = "2026-06-06T00:00:00Z"
_FX = _resource("fixtures") / "digestion"


def _self_test() -> int:
    fails: list[str] = []

    def check(n: str, ok: bool, d: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok:
            fails.append(n)

    contracts = json.dumps(json.loads((_resource("architecture") / "contract_registry.json").read_text()))
    for c in ("SkillDigestRun", "DeterminismExtractionReport", "SkillToRuntimeCandidate"):
        check(f"A: {c} registered", f"digestion/{c}.schema.json" in contracts)

    # B parse-only
    good = D.parse_skill_md((_FX / "deterministic_skill_sample" / "SKILL.md").read_text())
    check("B: deterministic SKILL.md parsed (name + tools + body)",
          good["name"] == "research-official-regulatory-source" and "http.fetch" in good["required_tools"] and good["body"])
    adapter_src = (_resource("src/teleon/digestion/digester.py")).read_text()
    check("B: adapter never executes a skill (no exec/subprocess/os.system)",
          not any(t in adapter_src for t in ("subprocess", "os." + "system(", "exec(", "eval(")))

    # C determinism extraction
    det = D.extract_determinism(good)
    want = {"domain_allowlist", "deterministic_source_ranking", "deterministic_parser_rule", "http_fetch_first", "deterministic_conflict_holdout"}
    check("C: deterministic substeps extracted", want <= set(det["deterministic_substeps"]), str(set(det["deterministic_substeps"])))
    check("C: cheap→expensive cascade incl deterministic + browser + llm", {"deterministic", "browser", "llm"} <= set(det["recommended_cascade"]), str(det["recommended_cascade"]))
    check("C: confidence high (>=3 deterministic substeps)", det["confidence"] == "high")

    # D digest
    dg = D.digest_skill(good, source_ref="fixtures/digestion/deterministic_skill_sample", now=_NOW)
    check("D: capability + I/O contracts + tools/models inferred",
          dg["capability_slots"] and dg["inferred_output_contracts"] and dg["required_tools"] and dg["required_models"])
    check("D: decision = skill candidate (NOT active)", dg["promotion_decision"] == "intake_as_skill_candidate")
    check("D: original preserved as fallback", dg["fallback_skill_ref"].endswith("@fallback"))
    check("D: proof_to_promote includes sandbox_run + redteam", "sandbox_run" in dg["proof_to_promote"] and "redteam" in dg["proof_to_promote"])

    # E runtime candidate
    cand = D.build_runtime_candidate(dg, now=_NOW)
    check("E: runtime candidate status=candidate (never active) + cascade + fallback + not truth",
          cand["status"] == "candidate" and cand["runtime_cascade"] and cand["fallback_skill_ref"] and cand["is_truth"] is False)

    # F unsafe → quarantine
    bad = D.parse_skill_md((_FX / "bad_skill_secret_exfiltration" / "SKILL.md").read_text())
    flags = D.is_unsafe(bad)
    bad_dg = D.digest_skill(bad, source_ref="fixtures/digestion/bad_skill_secret_exfiltration", now=_NOW)
    check("F: secret-exfil skill flagged unsafe", len(flags) >= 2, str(flags))
    check("F: unsafe skill → quarantine", bad_dg["promotion_decision"] == "quarantine")

    # G never auto-active
    check("G: no digest decision is 'active'", "active" not in dg["promotion_decision"] and "active" not in bad_dg["promotion_decision"])

    # H composes the sandbox gateway
    check("H: sandbox run required before promotion + Sandbox Gateway contract exists",
          "sandbox_run" in dg["proof_to_promote"] and (_resource("schemas") / "sandbox" / "SandboxRunRequest.schema.json").exists())

    # I determinism
    check("I: digest deterministic for fixed now", D.digest_skill(good, source_ref="x", now=_NOW) == D.digest_skill(good, source_ref="x", now=_NOW))

    # J dependency law
    badimp = [str(p.relative_to(_REPO)) for p in (_resource("src/teleon/digestion")).rglob("*.py")
              for line in p.read_text().splitlines() if line.strip().startswith(("import src.baltor", "from src.baltor"))]
    check("J: no _repos/teleon/backend/src/teleon/digestion module imports src.baltor", not badimp, "; ".join(badimp))

    print("\n" + ("PASS — check_skill_digestion: skills parse without executing; deterministic substeps are "
                  "extracted into a cheap→expensive cascade; the digest is a CANDIDATE (never active) keeping the "
                  "original as fallback, with a sandbox+eval+redteam proof ladder; unsafe skills quarantine; "
                  "deterministic + dependency-law clean." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_skill_digestion.py --self-test")
    raise SystemExit(0)
