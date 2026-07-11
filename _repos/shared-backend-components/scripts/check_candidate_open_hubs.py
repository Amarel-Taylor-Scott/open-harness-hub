"""check_candidate_open_hubs — proof for _repos/shared-backend-components/architecture/candidate_open_hubs.json.

Candidate Open*Hub.io websites drawn from real modular components. Enforces the PRIVATE-FIRST release policy:
every candidate is private_first + candidate (NEVER public/active), its domain needs owner trademark/clearance
(never silently claimed), it carries an open_trigger (open only when a competitor comes online / a planned
release) + a modular_component_source (it's drawn from something real) + a distinct_from (no overlap with the 9
existing hubs); the release_policy states discovery!=trust + never-public-without-clearance. No raw keys.
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
_DOC = _resource("architecture") / "candidate_open_hubs.json"
_REQ = ("hub_id", "proposed_domain", "domain_status", "thesis", "registers", "modular_component_source",
        "distinct_from", "status", "release_status", "open_trigger", "maturity")
_KEY_RE = re.compile(r"(sk-[A-Za-z0-9]{8,}|AKIA[0-9A-Z]{12,}|gsk_[A-Za-z0-9]{8,})")


def main() -> int:
    d = json.loads(_DOC.read_text())
    cands = d.get("candidates", [])
    existing = set(d.get("existing_hubs", []))
    pol = d.get("release_policy", {})
    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        if not ok:
            fails.append(f"{name}{(': ' + detail) if detail else ''}")

    ck(">=5 candidate hubs", len(cands) >= 5, str(len(cands)))
    ck("existing_hubs lists the 9", len(existing) >= 9, str(len(existing)))
    ck("no raw keys", not _KEY_RE.search(json.dumps(d)))

    # release policy: private-first, owner-gated domains, discovery!=trust, never public without clearance.
    ck("release_policy.default_status private_first", pol.get("default_status") == "private_first")
    ck("release_policy domain_trademark owner-gated", "owner_clearance" in str(pol.get("domain_trademark", "")).lower())
    ck("release_policy discovery_is_not_trust", pol.get("discovery_is_not_trust") is True)
    never = " ".join(pol.get("never", [])).lower()
    ck("release_policy never-public-without-clearance", "clearance" in never and ("public" in never or "active" in never))

    ids = set()
    for c in cands:
        hid = c.get("hub_id", "?")
        for f in _REQ:
            if not c.get(f):
                ck(f"{hid} has '{f}'", False)
        ck(f"{hid} status never active/public (candidate or a resolved disposition)", c.get("status") not in {"active", "public", "live", "promoted"}, str(c.get("status")))
        ck(f"{hid} release_status==private_first", c.get("release_status") == "private_first", str(c.get("release_status")))
        ck(f"{hid} domain owner_clearance_required (not claimed)", c.get("domain_status") == "owner_clearance_required")
        ck(f"{hid} is NOT a duplicate of an existing hub", hid not in existing)
        ck(f"{hid} maturity in {{ready_substrate,emerging}}", c.get("maturity") in {"ready_substrate", "emerging"})
        ids.add(hid)
    ck("no duplicate candidate hub_ids", len(ids) == len(cands))

    if fails:
        print("check_candidate_open_hubs: FAILURES")
        for f in fails[:25]:
            print("  -", f)
        return 1
    ready = sum(1 for c in cands if c.get("maturity") == "ready_substrate")
    resolved = sum(1 for c in cands if str(c.get("status", "")).startswith("resolved"))
    print(f"PASS — check_candidate_open_hubs: {len(cands)} candidate Open*Hubs ({ready} ready-substrate, {resolved} resolved "
          f"merge/fold) drawn from real modular components, all private_first (0 public/active), domains owner-clearance-gated, each with "
          f"an open-trigger + distinct-from the 9 existing hubs; release policy = open-on-competition, never public without "
          f"owner clearance; discovery!=trust.")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.parse_args()
    raise SystemExit(main())
