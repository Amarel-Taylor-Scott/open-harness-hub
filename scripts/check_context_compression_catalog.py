#!/usr/bin/env python3
"""scripts.check_context_compression_catalog — proof (RESEARCH CANDIDATE, NEVER ACTIVE): the
context-compression provider catalog (architecture/context_compression_provider_catalog.json) is
GOVERNED by the lossless-distillation law.

Asserts the governance shape that keeps TokenTamer a fork-target rather than a deployed dependency:

  * TokenTamer is status=research_candidate (NOT active) — worth forking (ContextTamer), not deploying as-is.
  * TokenTamer's MITM/SSL-interception mode is quarantined_local_dev_opt_in_only (no trusted-CA /
    /etc/hosts rewrite / DNS bypass in any shared deployment).
  * TokenTamer's 50-80% savings claim is savings_status=unverified_until_benchmarked (proven on OUR traces first).
  * Every external candidate carries no_truth_authority=true (compression output is never promoted to truth).
  * EXACTLY ONE active provider exists, and it is the local deterministic skeleton invariant.
  * deterministic_tool pins no_llm_calls + same_input_same_output + preserves source_handles + held_out_warnings
    + rehydration_available (lossless-law compliance: shrink the text surface, keep the facts, allow rehydration).
  * compression_profiles has conservative + balanced + aggressive.
  * governance_law references the lossless law (docs/codex/lossless-distillation.md) and states
    compression != success unless fidelity survives.
  * no raw secret/key literals leak into the catalog.

Deterministic, stdlib-only, offline (no network, no RNG, no credentials). The local deterministic skeleton
is the working provider; external proxy/skeletonizer providers stay catalog candidates.

CLI: PYTHONPATH=. python3 scripts/check_context_compression_catalog.py --self-test
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

#: the catalog under proof (single source — used by every check below).
_CATALOG = _REPO / "architecture" / "context_compression_provider_catalog.json"

#: the lossless law this catalog must reference (the governing law for all compression).
_LOSSLESS_LAW_REF = "docs/codex/lossless-distillation.md"

#: the external provider that must stay a fork-target, never a deployed dependency.
_TOKENTAMER_ID = "tokentamer@research_candidate"
_REQUIRED_TOKENTAMER_STATUS = "research_candidate"
_REQUIRED_MITM_MODE = "quarantined_local_dev_opt_in_only"
_REQUIRED_SAVINGS_STATUS = "unverified_until_benchmarked"

#: the one active provider must be the local deterministic compression invariant.
_LOCAL_INVARIANT_ID = "context_skeleton.local@v1"

#: the lossless-law fidelity surface every compression view must preserve (text shrinks, these survive).
_REQUIRED_PRESERVES = {"answer_critical_facts", "source_handles", "held_out_warnings"}

#: the compression profiles the catalog must offer.
_REQUIRED_PROFILES = {"conservative", "balanced", "aggressive"}

#: heuristic patterns for raw secret/key literals that must NOT appear anywhere in the catalog.
_SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9]{16,}"),            # OpenAI-style secret keys
    re.compile(r"sk-ant-[A-Za-z0-9_\-]{16,}"),     # Anthropic-style secret keys
    re.compile(r"AKIA[0-9A-Z]{16}"),               # AWS access key id
    re.compile(r"(?i)(api[_-]?key|secret|password|bearer)\s*[:=]\s*['\"][A-Za-z0-9_\-]{12,}['\"]"),
)


def _self_test() -> int:
    fails: list[str] = []

    def chk(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    chk("catalog file exists", _CATALOG.exists(), str(_CATALOG))
    if not _CATALOG.exists():
        print("\nRESULT: FAIL (catalog missing)")
        return 1

    raw_text = _CATALOG.read_text()
    cat = json.loads(raw_text)  # JSON must load

    # ---- no raw secret/key literals anywhere in the catalog ----
    leaks = [p.pattern for p in _SECRET_PATTERNS if p.search(raw_text)]
    chk("no raw secret/key literals in catalog", not leaks, f"matched: {leaks}")

    # ---- lossless-law wiring ----
    chk("lossless_law_ref points at the lossless law", cat.get("lossless_law_ref") == _LOSSLESS_LAW_REF,
        f"got {cat.get('lossless_law_ref')!r}")
    gov = (cat.get("governance_law") or "")
    chk("governance_law references the lossless law", _LOSSLESS_LAW_REF in gov)
    gov_lower = gov.lower()
    chk("governance_law states compression != success unless fidelity survives",
        ("lossless" in gov_lower)
        and (("not success" in gov_lower) or ("not a cheaper" in gov_lower) or ("failed compression" in gov_lower))
        and ("fidelity" in gov_lower or "answer-critical" in gov_lower))

    entries = {e.get("provider_id"): e for e in cat.get("entries", [])}

    # ---- TokenTamer is a research_candidate, MITM quarantined, savings unverified, no truth authority ----
    tt = entries.get(_TOKENTAMER_ID)
    chk(f"{_TOKENTAMER_ID} present", tt is not None)
    if tt is not None:
        chk("tokentamer status is research_candidate (NOT active)",
            tt.get("status") == _REQUIRED_TOKENTAMER_STATUS, f"status={tt.get('status')!r}")
        chk("tokentamer status is not active", tt.get("status") != "active")
        chk("tokentamer mitm_mode is quarantined_local_dev_opt_in_only",
            tt.get("mitm_mode") == _REQUIRED_MITM_MODE, f"mitm_mode={tt.get('mitm_mode')!r}")
        chk("tokentamer savings_status is unverified_until_benchmarked",
            tt.get("savings_status") == _REQUIRED_SAVINGS_STATUS, f"savings_status={tt.get('savings_status')!r}")
        chk("tokentamer no_truth_authority is True", tt.get("no_truth_authority") is True)
        chk("tokentamer license recorded as MIT", tt.get("license") == "MIT", f"license={tt.get('license')!r}")
        chk("tokentamer maturity recorded as alpha", tt.get("maturity") == "alpha", f"maturity={tt.get('maturity')!r}")
        chk("tokentamer carries a non-empty proof_to_promote ladder",
            isinstance(tt.get("proof_to_promote"), list) and len(tt.get("proof_to_promote")) >= 1)

    # ---- exactly one active provider, and it is the local deterministic skeleton invariant ----
    active_ids = [pid for pid, e in entries.items() if e.get("status") == "active"]
    chk("exactly one active provider", len(active_ids) == 1, f"active={active_ids}")
    chk("the one active provider is the local deterministic skeleton invariant",
        active_ids == [_LOCAL_INVARIANT_ID], f"active={active_ids}")
    local = entries.get(_LOCAL_INVARIANT_ID)
    chk(f"{_LOCAL_INVARIANT_ID} present", local is not None)
    if local is not None:
        chk("local invariant is the active provider", local.get("status") == "active",
            f"status={local.get('status')!r}")

    # every external (non-active) entry must carry no_truth_authority (no compression output becomes truth)
    for pid, e in entries.items():
        if e.get("status") != "active":
            chk(f"{pid} carries no_truth_authority=True", e.get("no_truth_authority") is True)

    # ---- deterministic_tool: lossless-law compliance pins ----
    det = cat.get("deterministic_tool") or {}
    chk("deterministic_tool present", bool(det))
    chk("deterministic_tool.no_llm_calls is True", det.get("no_llm_calls") is True)
    chk("deterministic_tool.same_input_same_output is True", det.get("same_input_same_output") is True)
    chk("deterministic_tool.stable_parser_versions is True", det.get("stable_parser_versions") is True)
    chk("deterministic_tool.rehydration_available is True", det.get("rehydration_available") is True)
    det_preserves = set(det.get("preserves") or [])
    chk("deterministic_tool.preserves source_handles", "source_handles" in det_preserves)
    chk("deterministic_tool.preserves held_out_warnings", "held_out_warnings" in det_preserves)
    chk("deterministic_tool.preserves the full lossless fidelity surface",
        _REQUIRED_PRESERVES <= det_preserves, f"missing={sorted(_REQUIRED_PRESERVES - det_preserves)}")

    # ---- compression profiles: conservative + balanced + aggressive ----
    profiles = cat.get("compression_profiles") or {}
    have = set(profiles.keys())
    chk("compression_profiles has conservative + balanced + aggressive",
        _REQUIRED_PROFILES <= have, f"missing={sorted(_REQUIRED_PROFILES - have)}")
    for prof in sorted(_REQUIRED_PROFILES & have):
        pres = set((profiles.get(prof) or {}).get("preserves") or [])
        chk(f"profile {prof} preserves the lossless fidelity surface",
            _REQUIRED_PRESERVES <= pres, f"missing={sorted(_REQUIRED_PRESERVES - pres)}")

    ok = not fails
    print(f"\nRESULT: {'PASS' if ok else 'FAIL'} ({len(fails)} failing check(s))" + (f": {fails}" if fails else ""))
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Check the governed context-compression provider catalog.")
    ap.add_argument("--self-test", action="store_true", help="run the offline deterministic self-test")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
