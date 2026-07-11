"""check_teleon_adjacent_extended — proof for _repos/shared-backend-components/architecture/teleon_adjacent_extended.json.

Companion to check_teleon_runtime_landscape.py. Validates the SECOND wave of Teleon-adjacent
due-diligence, which adds a VALIDATION-RISK lens (thesis_strengthening | safe_to_wrap |
positioning_threat | quarantine) on top of a capability-slot classification, and enforces the
governance that keeps Teleon the CONTROL PLANE ABOVE substrates:

  * none of these IS the Teleon runtime — teleon_role is always substrate_adapter_candidate /
    inspiration_reference / adjacent (NEVER "the_teleon_runtime"); no entry is status active / "is teleon";
  * validation_risk is always in the allowed set; >= 1 positioning_threat AND >= 1 thesis_strengthening
    are present (we both name the closest competitors AND record the strongest validating signal);
  * every safe_to_wrap / substrate entry carries do_not_adopt_as_primary (so adopting a backend cannot
    silently become a second durable ledger / worker framework — it stays behind ExecutionProviderPort);
  * every entry articulates what_it_lacks_vs_teleon + a differentiation_move;
  * license_confidence is honest (verified | unverified); no raw keys;
  * the positioning_law states the "control plane" sits "above" the substrates.

Deterministic, offline, stdlib only. Run: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_teleon_adjacent_extended.py --self-test
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
_DOC = _resource("architecture") / "teleon_adjacent_extended.json"

_REQUIRED = (
    "provider_id", "name", "capability_slot", "source_url", "license_confidence",
    "what_it_covers", "teleon_role", "validation_risk",
    "what_it_lacks_vs_teleon", "differentiation_move",
)
_ALLOWED_RISK = {"thesis_strengthening", "safe_to_wrap", "positioning_threat", "quarantine"}
_ALLOWED_ROLE = {"substrate_adapter_candidate", "inspiration_reference", "adjacent"}
_FORBIDDEN_ROLE = "the_teleon_runtime"
# safe_to_wrap entries and substrate adapters must carry the no-second-framework guard.
_SUBSTRATE_RISK = {"safe_to_wrap"}
_SUBSTRATE_ROLE = {"substrate_adapter_candidate"}
_ALLOWED_LICENSE = {"verified", "unverified"}
_KEY_RE = re.compile(r"(sk-[A-Za-z0-9]{8,}|AKIA[0-9A-Z]{12,}|gsk_[A-Za-z0-9]{8,}|xai-[A-Za-z0-9]{8,})")


def main() -> int:
    raw = _DOC.read_text()
    doc = json.loads(raw)
    entries = doc.get("entries", [])
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        if not ok:
            fails.append(f"{name}{(': ' + detail) if detail else ''}")

    # ---- document-level invariants ----
    allowed_risk = set(doc.get("allowed_validation_risk", []))
    check("allowed_validation_risk == governance set", allowed_risk == _ALLOWED_RISK, str(allowed_risk))
    law = (doc.get("positioning_law") or "").lower()
    check("positioning_law states 'control plane'", "control plane" in law)
    check("positioning_law states 'above'", "above" in law)
    check("entries >= 10", len(entries) >= 10, str(len(entries)))
    check("no raw API keys", not _KEY_RE.search(raw))

    # ---- per-entry invariants ----
    for e in entries:
        pid = e.get("provider_id", "?")
        for f in _REQUIRED:
            if not e.get(f):
                check(f"{pid} has non-empty '{f}'", False)
        check(f"{pid} validation_risk in allowed set", e.get("validation_risk") in _ALLOWED_RISK, str(e.get("validation_risk")))
        check(f"{pid} teleon_role allowed (never the_teleon_runtime)", e.get("teleon_role") in _ALLOWED_ROLE, str(e.get("teleon_role")))
        check(f"{pid} teleon_role is not '{_FORBIDDEN_ROLE}'", e.get("teleon_role") != _FORBIDDEN_ROLE)
        check(f"{pid} license_confidence verified|unverified", e.get("license_confidence") in _ALLOWED_LICENSE, str(e.get("license_confidence")))
        # no entry may claim to BE Teleon / be active.
        status = str(e.get("status", "")).lower()
        check(f"{pid} not status 'active'", status != "active", status)
        check(f"{pid} does not claim to be teleon", "is teleon" not in status and status != "is_teleon", status)
        # every safe_to_wrap / substrate adapter MUST carry the no-second-framework guard.
        if e.get("validation_risk") in _SUBSTRATE_RISK or e.get("teleon_role") in _SUBSTRATE_ROLE:
            check(f"{pid} (substrate/safe_to_wrap) carries do_not_adopt_as_primary", bool(e.get("do_not_adopt_as_primary")))

    # ---- coverage invariants: we name BOTH the threats AND the validating signal ----
    risks = [e.get("validation_risk") for e in entries]
    check("has >= 1 positioning_threat", risks.count("positioning_threat") >= 1)
    check("has >= 1 thesis_strengthening", risks.count("thesis_strengthening") >= 1)
    check("no entry is quarantine OR doc honestly allows it",
          "quarantine" in allowed_risk)  # quarantine must be a *permitted* value even if unused
    # nothing here may be the runtime itself.
    check("no entry claims to BE the Teleon runtime",
          not any(e.get("teleon_role") == _FORBIDDEN_ROLE or str(e.get("status", "")).lower() == "active" for e in entries))

    if fails:
        print("check_teleon_adjacent_extended: FAILURES")
        for f in fails[:25]:
            print("  -", f)
        return 1

    slot_count: dict[str, int] = {}
    for e in entries:
        slot_count[e.get("capability_slot", "?")] = slot_count.get(e.get("capability_slot", "?"), 0) + 1
    print(
        f"PASS — check_teleon_adjacent_extended: {len(entries)} entries "
        f"({risks.count('thesis_strengthening')} thesis_strengthening, {risks.count('safe_to_wrap')} safe_to_wrap, "
        f"{risks.count('positioning_threat')} positioning_threat, {risks.count('quarantine')} quarantine); "
        f"slots={slot_count}; none IS the Teleon runtime; every safe_to_wrap/substrate carries a "
        f"no-second-framework guard; positioning = control plane ABOVE the substrates."
    )
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.parse_args()
    raise SystemExit(main())
