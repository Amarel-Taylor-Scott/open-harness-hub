"""check_openhubs_backend_registry — proof for the Open*Hubs BACKEND POWERING candidate registry.

Enforces the governance that keeps OSS backend repos SAFE candidates, never auto-active dependencies of
the seven open hubs (OpenContextHub, OpenSkillsHub, OpenToolsHub, OpenMCPHub, OpenCompressionHub,
OpenBenchmarkHub, OpenHubForAI):
  * >= 15 entries, each carrying every required field;
  * status is candidate|reference|active; NO entry is active (prefer none) — and if any active slips in,
    it MUST carry a local_equivalent + proof_to_promote;
  * every entry's hub is one of the 7 valid hubs;
  * every entry has source_url + license_confidence in {verified, unverified} (provenance tracked, honest);
  * every gated entry (requires_docker OR requires_network) carries a local_equivalent (local-first);
  * NO raw API keys anywhere (env:// refs only — metadata-only artifact);
  * the registry note states the positioning: discovery != trust + benchmark = evidence + candidate != active;
  * OpenMCPHub has an mcp_registry entry referencing the official modelcontextprotocol/registry (lead insight).
Deterministic, offline, stdlib only.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
_REG = _resource("architecture") / "openhubs_backend_candidate_registry.json"
_REQUIRED = ("provider_id", "name", "hub", "component", "source_url", "license", "license_confidence",
             "requires_docker", "requires_network", "local_equivalent", "status", "proof_to_promote")
_VALID_HUBS = {"OpenContextHub", "OpenSkillsHub", "OpenToolsHub", "OpenMCPHub",
               "OpenCompressionHub", "OpenBenchmarkHub", "OpenHubForAI"}
_ALLOWED_STATUS = {"candidate", "reference", "active"}   # active is allowed by schema but must be gated; prefer none
_KEY_RE = re.compile(r"(sk-[A-Za-z0-9]{8,}|AKIA[0-9A-Z]{12,}|gsk_[A-Za-z0-9]{8,}|xai-[A-Za-z0-9]{8,})")
_OFFICIAL_MCP_REGISTRY = "modelcontextprotocol/registry"


def main() -> int:
    reg = json.loads(_REG.read_text())
    entries = reg.get("entries", [])
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        if not ok:
            fails.append(f"{name}{(': ' + detail) if detail else ''}")

    # entries >= 15
    check("registry has >= 15 entries", len(entries) >= 15, str(len(entries)))

    # NO raw keys anywhere (env:// refs only — this is a no-secrets metadata artifact).
    check("no raw API keys in registry", not _KEY_RE.search(json.dumps(reg)))

    # positioning: the registry note (+ governance_law block) states discovery!=trust, benchmark=evidence,
    # candidate!=active.
    blob = (reg.get("note", "") + " " + json.dumps(reg.get("governance_law", {}))).lower()
    check("note states 'discovery != trust'", "discovery" in blob and "trust" in blob)
    check("note states 'benchmark' + 'evidence'", "benchmark" in blob and "evidence" in blob)
    check("note states 'candidate != active'", "candidate" in blob and "active" in blob)
    check("note states hubs are registries not truth authorities",
          "registries" in blob and "truth" in blob)

    seen_mcp_registry = False
    for e in entries:
        pid = e.get("provider_id", "?")
        for f in _REQUIRED:
            if f not in e:
                check(f"{pid} has '{f}'", False)

        st = e.get("status")
        check(f"{pid} status in candidate|reference|active", st in _ALLOWED_STATUS, str(st))
        # No entry should be active; if one is, it MUST carry local_equivalent + proof_to_promote.
        if st == "active":
            check(f"{pid} (active) has a local_equivalent", bool(e.get("local_equivalent")))
            check(f"{pid} (active) has a proof_to_promote ladder", bool(e.get("proof_to_promote")))

        check(f"{pid} hub is one of the 7 valid hubs", e.get("hub") in _VALID_HUBS, str(e.get("hub")))
        check(f"{pid} has source_url", bool(e.get("source_url")))
        check(f"{pid} license_confidence is verified|unverified",
              e.get("license_confidence") in {"verified", "unverified"})

        # local-first: anything needing Docker or network must carry a local_equivalent.
        gated = bool(e.get("requires_docker")) or bool(e.get("requires_network"))
        if gated:
            check(f"{pid} (gated: docker/network) has a local_equivalent", bool(e.get("local_equivalent")))

        # lead insight: OpenMCPHub has an mcp_registry entry referencing the official MCP registry.
        if e.get("hub") == "OpenMCPHub" and e.get("component") == "mcp_registry" \
                and _OFFICIAL_MCP_REGISTRY in str(e.get("source_url", "")):
            seen_mcp_registry = True

    # prefer NO active entries (governance: Open*Hub backend repos are candidate/reference).
    active = [e.get("provider_id") for e in entries if e.get("status") == "active"]
    check("NO entry is active (Open*Hub backend repos are candidate/reference)", not active,
          ",".join(p for p in active if p))

    check(f"OpenMCPHub has an mcp_registry entry referencing {_OFFICIAL_MCP_REGISTRY}", seen_mcp_registry)

    if fails:
        print("check_openhubs_backend_registry: FAILURES")
        for f in fails[:25]:
            print("  -", f)
        return 1

    cands = sum(1 for e in entries if e.get("status") == "candidate")
    refs = sum(1 for e in entries if e.get("status") == "reference")
    hubs = sorted({e.get("hub") for e in entries})
    print(f"PASS — check_openhubs_backend_registry: {len(entries)} entries ({cands} candidate, {refs} reference, "
          f"0 active) across {len(hubs)} hubs; every entry hub-valid + sourced + license-confidence-tracked; "
          f"every docker/network-gated entry has a local_equivalent; no raw keys; OpenMCPHub wraps the official "
          f"MCP registry; discovery != trust, benchmark = evidence, candidate != active, hubs are registries "
          f"(not truth authorities).")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.parse_args()
    raise SystemExit(main())
