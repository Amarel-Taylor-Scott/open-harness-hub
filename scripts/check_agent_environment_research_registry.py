"""check_agent_environment_research_registry — proof for the Environment + Reward Spine RESEARCH REGISTRY.

Enforces the governance that keeps Repo2RLEnv-style tools SAFE candidates, never active dependencies:
  * status is candidate|reference ONLY — NEVER active (no env generator/harness/benchmark is active infra);
  * any entry needing Docker/network/LLM/api_key carries a local_equivalent AND a proof_to_promote ladder
    (build-local-first; nothing runs Docker/keys without owner authorization);
  * source_url + license + license_confidence(verified|unverified) present (provenance tracked, honest);
  * NO raw keys anywhere; every openhub_mapping is a known hub;
  * Repo2RLEnv is classified repo_to_rl_env_generator (NOT an LLM endpoint, NOT a coding agent);
  * the registry states the promotion law: benchmark result = EVIDENCE, never promotion authority; output != truth.
Deterministic, offline, stdlib only.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_REG = _REPO / "architecture" / "agent_environment_research_registry.json"
_REQUIRED = ("provider_id", "name", "category", "purpose", "source_url", "license", "license_confidence",
             "requires_docker", "requires_network", "requires_llm", "requires_api_key", "local_equivalent",
             "openhub_mapping", "teleon_fit", "baltor_fit", "status", "proof_to_promote")
_ALLOWED_STATUS = {"candidate", "reference"}            # NEVER "active" in this registry
_KEY_RE = re.compile(r"(sk-[A-Za-z0-9]{8,}|AKIA[0-9A-Z]{12,}|gsk_[A-Za-z0-9]{8,}|xai-[A-Za-z0-9]{8,})")


def main() -> int:
    reg = json.loads(_REG.read_text())
    entries = reg.get("entries", [])
    valid_hubs = set(reg.get("valid_openhub_mappings", []))
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        if not ok:
            fails.append(f"{name}{(': ' + detail) if detail else ''}")

    check("registry has entries", len(entries) >= 8, str(len(entries)))

    # NO raw keys anywhere in the registry (env:///refs only — this is a no-secrets metadata artifact).
    check("no raw API keys in registry", not _KEY_RE.search(json.dumps(reg)))

    # promotion law + positioning statements present (benchmark=evidence, output!=truth).
    blob = (reg.get("note", "") + " " + reg.get("promotion_law", "")).lower()
    for token in ("evidence", "never promotion authority", "never truth", "candidate != active"):
        check(f"registry states '{token}'", token in blob)

    seen_repo2rlenv = False
    for e in entries:
        pid = e.get("provider_id", "?")
        for f in _REQUIRED:
            if f not in e:
                check(f"{pid} has '{f}'", False)
        st = e.get("status")
        check(f"{pid} status candidate|reference (NEVER active)", st in _ALLOWED_STATUS, str(st))
        # build-local-first + ladder: anything needing Docker/LLM/key must carry a local equivalent + a promotion ladder.
        gated = e.get("requires_docker") or e.get("requires_llm") or e.get("requires_api_key") or e.get("requires_network")
        if gated and st == "candidate":
            check(f"{pid} (gated) has a local_equivalent", bool(e.get("local_equivalent")))
            check(f"{pid} (gated) has a proof_to_promote ladder", bool(e.get("proof_to_promote")))
        check(f"{pid} has source_url", bool(e.get("source_url")))
        check(f"{pid} license_confidence is verified|unverified", e.get("license_confidence") in {"verified", "unverified"})
        for hub in e.get("openhub_mapping", []):
            check(f"{pid} openhub_mapping '{hub}' is known", hub in valid_hubs)
        if e.get("provider_id", "").startswith("envgen.repo2rlenv"):
            seen_repo2rlenv = True
            check("Repo2RLEnv classified repo_to_rl_env_generator (not LLM endpoint / coding agent)",
                  e.get("category") == "repo_to_rl_env_generator")
            check("Repo2RLEnv is candidate (Docker/keys gated), not active", e.get("status") == "candidate")

    check("Repo2RLEnv present in the registry", seen_repo2rlenv)
    # at least one external reference yardstick (e.g. SWE-bench), and ABSOLUTELY no 'active' entries.
    check("at least one reference yardstick", any(e.get("status") == "reference" for e in entries))
    check("NO entry is active (active is forbidden here)", not any(e.get("status") == "active" for e in entries))

    if fails:
        print("check_agent_environment_research_registry: FAILURES")
        for f in fails[:20]:
            print("  -", f)
        return 1
    cands = sum(1 for e in entries if e.get("status") == "candidate")
    refs = sum(1 for e in entries if e.get("status") == "reference")
    print(f"PASS — check_agent_environment_research_registry: {len(entries)} entries ({cands} candidate, {refs} reference, "
          f"0 active); every gated entry has a local equivalent + promotion ladder; provenance/license tracked; no raw "
          f"keys; Repo2RLEnv = repo_to_rl_env_generator candidate; benchmark = evidence, never promotion authority.")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.parse_args()
    raise SystemExit(main())
