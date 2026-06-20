"""check_teleon_runtime_landscape — proof for architecture/teleon_runtime_landscape.json.

Answers "are there repos that do what Teleon does?" as a GOVERNED artifact and enforces the positioning:
  * none of these IS the Teleon runtime — teleon_role is always adapter-candidate / sandbox-adapter / inspiration /
    adjacent-registry; status is candidate|reference|inspiration|research, NEVER active. Teleon's own reference
    runtime + the CapabilityTask standard stay the stable layer.
  * every durable-workflow / execution substrate carries a do_not_adopt_as_primary note (so adopting a backend
    cannot silently become a SECOND durable ledger / worker framework — it stays behind ExecutionProviderPort);
  * Teleon's differentiation is articulated per competitor (what_it_lacks_vs_teleon) and globally (>= 8 differentiators);
  * the positioning law states Teleon is the control plane ABOVE these, "not another" framework/engine/runtime;
  * license_confidence is honest (verified|unverified); no raw keys.
Deterministic, offline, stdlib only.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_DOC = _REPO / "architecture" / "teleon_runtime_landscape.json"
_REQUIRED = ("provider_id", "name", "category", "source_url", "license_confidence", "what_it_covers",
             "what_it_lacks_vs_teleon", "teleon_role", "fit", "status", "do_not_adopt_as_primary")
_ALLOWED_ROLES = {"substrate_adapter_candidate", "sandbox_adapter_candidate", "inspiration_reference", "adjacent_registry"}
_ALLOWED_STATUS = {"candidate", "reference", "inspiration", "research"}   # NEVER "active" / "is_teleon"
_SUBSTRATE_ROLES = {"substrate_adapter_candidate", "sandbox_adapter_candidate"}
_KEY_RE = re.compile(r"(sk-[A-Za-z0-9]{8,}|AKIA[0-9A-Z]{12,}|gsk_[A-Za-z0-9]{8,}|xai-[A-Za-z0-9]{8,})")


def main() -> int:
    doc = json.loads(_DOC.read_text())
    entries = doc.get("entries", [])
    roles = set(doc.get("allowed_roles", []))
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        if not ok:
            fails.append(f"{name}{(': ' + detail) if detail else ''}")

    check("has a conclusion", bool(doc.get("conclusion")))
    check("declares >= 8 Teleon differentiators", len(doc.get("teleon_differentiators", [])) >= 8)
    law = doc.get("positioning_law", "").lower()
    for tok in ("control plane", "above", "not another"):
        check(f"positioning_law states '{tok}'", tok in law)
    check("allowed_roles == governance set", roles == _ALLOWED_ROLES, str(roles))
    check("entries >= 10", len(entries) >= 10, str(len(entries)))
    check("no raw API keys", not _KEY_RE.search(json.dumps(doc)))

    for e in entries:
        pid = e.get("provider_id", "?")
        for f in _REQUIRED:
            if not e.get(f):
                check(f"{pid} has non-empty '{f}'", False)
        check(f"{pid} teleon_role is allowed (never THE runtime)", e.get("teleon_role") in _ALLOWED_ROLES, str(e.get("teleon_role")))
        check(f"{pid} status candidate|reference|inspiration|research (never active)", e.get("status") in _ALLOWED_STATUS, str(e.get("status")))
        check(f"{pid} license_confidence verified|unverified", e.get("license_confidence") in {"verified", "unverified"})
        # a substrate/sandbox we might adopt MUST carry the no-second-framework guard.
        if e.get("teleon_role") in _SUBSTRATE_ROLES:
            check(f"{pid} (substrate) carries a do_not_adopt_as_primary guard", bool(e.get("do_not_adopt_as_primary")))

    # Teleon's own runtime is the stable layer — NOTHING here may claim to be it.
    check("no entry claims to BE Teleon (no active/runtime role)",
          not any(e.get("status") == "active" or e.get("teleon_role") == "the_teleon_runtime" for e in entries))
    # at least one honest inspiration reference (e.g. ARK = closest), and at least one adapter candidate.
    check("has >= 1 inspiration_reference", any(e.get("teleon_role") == "inspiration_reference" for e in entries))
    check("has >= 1 substrate_adapter_candidate", any(e.get("teleon_role") == "substrate_adapter_candidate" for e in entries))

    if fails:
        print("check_teleon_runtime_landscape: FAILURES")
        for f in fails[:20]:
            print("  -", f)
        return 1
    roles_count = {r: sum(1 for e in entries if e.get("teleon_role") == r) for r in _ALLOWED_ROLES}
    print(f"PASS — check_teleon_runtime_landscape: {len(entries)} entries ({roles_count}); none IS the Teleon runtime "
          f"(0 active); every substrate carries a no-second-framework guard; Teleon differentiation articulated "
          f"per competitor + globally; positioning = control plane ABOVE, not another framework.")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.parse_args()
    raise SystemExit(main())
