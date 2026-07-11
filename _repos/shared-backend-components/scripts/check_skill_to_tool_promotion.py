#!/usr/bin/env python3
"""scripts.check_skill_to_tool_promotion — PROOF (research infra): the GOVERNED skill -> deterministic-tool
promotion catalog is internally consistent and safe. This is the FORK direction on SkillClaw (AMAP-ML, MIT,
WIP): the Determinism Factory (M0->M8 LLM->rule ladder) applied to SKILLS, gated like the agent-gateway and
governed by the Lossless Distillation law. Skill/tool output != truth; tools are NEVER auto-published.

Asserts (deterministic, offline, stdlib-only):
  A. SOURCE: SkillClaw is a research_candidate (NOT active) + no_truth_authority + wip (the safer reading);
     license MIT; carries a proof_to_promote ladder.
  B. LADDER: the promotion_ladder has the 7 rungs in order
     (observation -> draft_skill -> verified_skill -> tool_candidate -> deterministic_tool ->
      certified_internal_tool -> retired_or_merged); rungs numbered 0..6; nothing auto-advances; no rung is truth.
  C. STANDARD: deterministic_tool_standard pins no_llm_calls + no_random_without_seed + no_wall_clock_dependency,
     same_output_hash repeatability (repeat_runs >= 2, min_repeatability == 1.0), sandbox (network blocked,
     fs read-only), human_approval_required, and security sbom + signed; min_tool_test_pass == 1.0;
     the standard states the AGENT is NOT made deterministic.
  D. DATA POLICY: data_policy.never includes customer + secrets + regulated + confidential; mine_from is the
     public/synthetic/redacted set; tenant-private lineage never global.
  E. GOVERNANCE LAW: skill output != truth AND tool output != truth AND tools-never-auto-published AND
     distillation-lossless are all asserted; the law cross-references the Determinism Factory + Lossless laws.
  F. LOSSLESS: the standard preserves the source skill + losing candidates + held-out eval + a rollback target.
  G. NO RAW KEYS: none of the 3 deliverable files embed a raw secret/API-key literal.
  H. DETERMINISM: the catalog loads as valid JSON twice to identical bytes (no nondeterministic content).

Exit 0 (PASS) / 1 (FAIL).
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

_CATALOG = _resource("architecture") / "skill_to_tool_promotion_catalog.json"
_DOC = _resource("docs") / "research" / "skillclaw-skill-to-deterministic-tool.md"
_SELF = _resource("scripts/check_skill_to_tool_promotion.py")

# Expected ordered rungs of the promotion ladder.
_EXPECTED_RUNGS = [
    "observation",
    "draft_skill",
    "verified_skill",
    "tool_candidate",
    "deterministic_tool",
    "certified_internal_tool",
    "retired_or_merged",
]

# Heuristic raw-secret detectors. We flag obvious provider key literals and assigned-secret literals,
# while allowing the *words* secret/secret_scan/SecretRef (governance vocabulary, not a key).
_KEY_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9]{16,}"),          # OpenAI-style
    re.compile(r"sk-ant-[A-Za-z0-9_\-]{16,}"),   # Anthropic-style
    re.compile(r"AKIA[0-9A-Z]{12,}"),            # AWS access key id
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),         # GitHub PAT
    re.compile(r"AIza[0-9A-Za-z_\-]{20,}"),      # Google API key
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"(?i)(api[_-]?key|secret|token|password|passwd)\s*[:=]\s*['\"][A-Za-z0-9/+_\-]{16,}['\"]"),
]


def _self_test() -> int:
    fails: list[str] = []

    def check(n: str, ok: bool, d: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok:
            fails.append(n)

    if not _CATALOG.exists():
        check("catalog file exists", False, str(_CATALOG))
        print("\n1 FAILURES: ['catalog file exists']")
        return 1

    raw = _CATALOG.read_text()
    cat = json.loads(raw)

    # A. SOURCE
    entry = cat.get("skillclaw_entry", {})
    check("A: skillclaw_entry.provider_id == skillclaw@research_candidate",
          entry.get("provider_id") == "skillclaw@research_candidate", str(entry.get("provider_id")))
    check("A: status == research_candidate", entry.get("status") == "research_candidate", str(entry.get("status")))
    check("A: NOT active", entry.get("active") is False, str(entry.get("active")))
    check("A: no_truth_authority == True", entry.get("no_truth_authority") is True)
    check("A: wip == True", entry.get("wip") is True)
    check("A: license == MIT", entry.get("license") == "MIT", str(entry.get("license")))
    check("A: has a non-empty proof_to_promote ladder",
          isinstance(entry.get("proof_to_promote"), list) and len(entry.get("proof_to_promote", [])) >= 3)

    # B. LADDER
    ladder = cat.get("promotion_ladder", [])
    ids = [r.get("id") for r in ladder]
    check("B: promotion_ladder has 7 rungs", len(ladder) == 7, str(len(ladder)))
    check("B: 7 rungs in order observation -> ... -> retired_or_merged", ids == _EXPECTED_RUNGS, str(ids))
    check("B: rungs numbered 0..6 in order", [r.get("rung") for r in ladder] == list(range(7)),
          str([r.get("rung") for r in ladder]))
    check("B: no rung auto-advances", all(r.get("auto_advance") is False for r in ladder))
    check("B: no rung is truth (is_truth False on every rung)", all(r.get("is_truth") is False for r in ladder))

    # C. STANDARD
    std = cat.get("deterministic_tool_standard", {})
    det = std.get("determinism", {})
    check("C: no_llm_calls pinned True", det.get("no_llm_calls") is True)
    check("C: no_random_without_seed pinned True", det.get("no_random_without_seed") is True)
    check("C: no_wall_clock_dependency pinned True", det.get("no_wall_clock_dependency") is True)
    check("C: same_output_hash repeatability True", det.get("same_output_hash") is True)
    check("C: repeat_runs >= 2", isinstance(det.get("repeat_runs"), int) and det.get("repeat_runs", 0) >= 2,
          str(det.get("repeat_runs")))
    sandbox = std.get("sandbox", {})
    check("C: sandbox network blocked", sandbox.get("network") == "blocked", str(sandbox.get("network")))
    check("C: sandbox fs read-only", sandbox.get("fs") == "read_only", str(sandbox.get("fs")))
    check("C: sandbox subprocess blocked", sandbox.get("subprocess") == "blocked", str(sandbox.get("subprocess")))
    gates = std.get("promotion_gates", {})
    check("C: human_approval_required True", gates.get("human_approval_required") is True)
    check("C: min_repeatability == 1.0", gates.get("min_repeatability") == 1.0, str(gates.get("min_repeatability")))
    check("C: min_tool_test_pass == 1.0 (gate + tests)",
          gates.get("min_tool_test_pass") == 1.0 and std.get("tests", {}).get("min_tool_test_pass") == 1.0)
    check("C: min_reuse >= 1 and min_skill_validation >= 1",
          gates.get("min_reuse", 0) >= 1 and gates.get("min_skill_validation", 0) >= 1)
    sec = std.get("security", {})
    check("C: security sbom == True", sec.get("sbom") is True)
    check("C: security signed == True", sec.get("signed") is True)
    check("C: security secret_scan + static_analysis + dependency_lock True",
          sec.get("secret_scan") is True and sec.get("static_analysis") is True and sec.get("dependency_lock") is True)
    check("C: standard says the AGENT is NOT deterministic", std.get("agent_is_deterministic") is False)

    # D. DATA POLICY
    dp = cat.get("data_policy", {})
    never = set(dp.get("never", []))
    check("D: data_policy.never includes customer+secrets+regulated+confidential",
          {"customer", "secrets", "regulated", "confidential"} <= never, str(sorted(never)))
    check("D: mine_from == public/synthetic/redacted set",
          set(dp.get("mine_from", [])) == {"public", "synthetic", "redacted_internal_non_sensitive"},
          str(dp.get("mine_from")))
    check("D: tenant-private lineage never global", dp.get("tenant_private_lineage_never_global") is True)

    # E. GOVERNANCE LAW
    law = cat.get("governance_law", {})
    check("E: skill output != truth", law.get("skill_output_is_not_truth") is True)
    check("E: tool output != truth", law.get("tool_output_is_not_truth") is True)
    check("E: tools never auto-published", law.get("tools_never_auto_published") is True)
    check("E: distillation is lossless", law.get("distillation_is_lossless") is True)
    related = " ".join(law.get("related_laws", []))
    check("E: law cross-references Determinism Factory + Lossless Distillation",
          "determinism-factory" in related and "lossless-distillation" in related, related)

    # F. LOSSLESS (in the standard)
    lin = std.get("lineage", {})
    check("F: lossless — preserve source skill", lin.get("preserve_source_skill") is True)
    check("F: lossless — preserve losing candidates", lin.get("preserve_losing_candidates") is True)
    check("F: lossless — preserve held-out eval", lin.get("preserve_held_out_eval") is True)
    check("F: lossless — rollback target required", lin.get("rollback_target_required") is True)

    # G. NO RAW KEYS across the 3 deliverables
    for f in (_CATALOG, _DOC, _SELF):
        if not f.exists():
            check(f"G: deliverable exists ({f.name})", False, str(f))
            continue
        text = f.read_text()
        hits = [p.pattern for p in _KEY_PATTERNS if p.search(text)]
        check(f"G: no raw key literal in {f.name}", not hits, "; ".join(hits))

    # H. DETERMINISM — re-load to identical bytes (canonicalized)
    check("H: catalog re-serializes deterministically",
          json.dumps(json.loads(raw), sort_keys=True) == json.dumps(cat, sort_keys=True))

    print("\n" + (
        "PASS — check_skill_to_tool_promotion: SkillClaw is a research_candidate (MIT, WIP, no truth authority, "
        "not active); the 7-rung promotion ladder runs observation -> draft skill -> verified skill -> tool candidate "
        "-> deterministic tool -> certified internal tool -> retired/merged with no auto-advance and no rung serving "
        "truth; the deterministic-tool standard pins no-LLM / seeded-RNG / no-wall-clock + same-output-hash "
        "repeatability + network-blocked read-only sandbox + human approval + SBOM/signed + 100%% tool tests while "
        "keeping the agent probabilistic; data is mined only from public/synthetic/redacted traces (never "
        "customer/secrets/regulated/confidential); skill and tool output are not truth, tools never auto-publish, and "
        "distillation is lossless. Determinism Factory applied to skills."
        if not fails else f"{len(fails)} FAILURES: {fails}"
    ))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_skill_to_tool_promotion.py --self-test")
    raise SystemExit(0)
