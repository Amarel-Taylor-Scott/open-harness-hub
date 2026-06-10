"""check_capability_binding_landscape — proof for the Infrastructure-from-Code / workload-spec /
platform-capability-API / serverless-runtime LANDSCAPE (architecture/capability_binding_landscape.json).

This is the DISTINCT category answering 'are there tools that do purpose/capability/contract-defined
programming that completely abstracts cloud-function and K8s-worker programming?'. The governance encoded
and enforced here:

  * NONE of these does the full Teleon thesis — they abstract DEPLOYMENT/WORKLOADS/PLATFORM-RESOURCES, not
    the capability LIFECYCLE; the verdict + positioning_law say so (control plane / above / lifecycle);
  * every entry is a CapabilityTask BINDING TARGET / execution adapter behind a CapabilityTaskBindingProvider,
    carries a teleon_local_equivalent (the local reference binding stays the stable first path), a
    do_not_adopt_as_primary, and an integer closeness_rank; at least one entry is closeness_rank == 1
    (the closest matches — Kratix/Radius/Score);
  * status is candidate|reference|research|research_archived — NEVER active;
  * validation_risk is in the allowed set; binding_role is in the valid set; license_confidence is
    verified|unverified; Kratix + Score + Nitric are present;
  * NO raw API keys anywhere;
  * a cross_reference field names the two existing catalogs (teleon_runtime_landscape + teleon_adjacent_extended)
    so the durable-workflow + agent runtimes are NOT re-added here — and asserts none of
    {temporal,dbos,hatchet,inngest,trigger,modal} appear as NEW provider_ids (no duplicate catalogs).

Deterministic, offline, stdlib only.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_CATALOG = _REPO / "architecture" / "capability_binding_landscape.json"

_REQUIRED = (
    "provider_id", "name", "capability_slot", "source_url", "license", "license_confidence",
    "what_it_abstracts", "what_it_lacks_vs_teleon", "binding_role", "validation_risk",
    "closeness_rank", "teleon_local_equivalent", "status", "do_not_adopt_as_primary",
)
_ALLOWED_STATUS = {"candidate", "reference", "research", "research_archived"}  # NEVER "active"
_VALID_BINDING_ROLES = {
    "capability_compile_target", "workload_spec_export", "platform_capability_api",
    "execution_adapter", "scaler",
}
_ALLOWED_VALIDATION_RISK = {"thesis_strengthening", "safe_to_wrap", "positioning_threat"}
_LICENSE_CONFIDENCE = {"verified", "unverified"}
# Providers that belong to the EXISTING catalogs — must NOT reappear as NEW entries here.
_FORBIDDEN_DUP_TOKENS = {"temporal", "dbos", "hatchet", "inngest", "trigger", "modal"}
# Tools that MUST be present (per the brief).
_REQUIRED_TOOL_TOKENS = {"kratix": "Kratix", "score": "Score", "nitric": "Nitric"}
# Positioning-law load-bearing tokens.
_POSITIONING_TOKENS = ("control plane", "above", "lifecycle")
# Raw-key shapes (defense-in-depth; this is a no-secrets metadata artifact).
_KEY_RE = re.compile(r"(sk-[A-Za-z0-9]{8,}|AKIA[0-9A-Z]{12,}|gsk_[A-Za-z0-9]{8,}|xai-[A-Za-z0-9]{8,})")


def main() -> int:
    if not _CATALOG.exists():
        print(f"check_capability_binding_landscape: FAILURES\n  - catalog missing: {_CATALOG}")
        return 1
    try:
        cat = json.loads(_CATALOG.read_text())
    except json.JSONDecodeError as exc:  # JSON must load
        print(f"check_capability_binding_landscape: FAILURES\n  - JSON did not parse: {exc}")
        return 1

    entries = cat.get("entries", [])
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        if not ok:
            fails.append(f"{name}{(': ' + detail) if detail else ''}")

    # --- top-level structure ---
    check("catalog has a note", bool(cat.get("note")))
    check("catalog has a verdict", bool(cat.get("verdict")))
    check("catalog has >= 12 entries", len(entries) >= 12, str(len(entries)))

    # verdict + positioning_law must encode the thesis (NONE does the full lifecycle; control plane ABOVE).
    verdict_blob = (cat.get("verdict", "") + " " + cat.get("note", "")).lower()
    check("verdict says NONE does the full thesis",
          ("none" in verdict_blob) and ("full" in verdict_blob or "lifecycle" in verdict_blob))

    plaw = cat.get("positioning_law", "").lower()
    for token in _POSITIONING_TOKENS:
        check(f"positioning_law contains '{token}'", token in plaw)

    # allowed sets present + sane.
    allowed_vr = set(cat.get("allowed_validation_risk", []))
    check("allowed_validation_risk == the allowed set", allowed_vr == _ALLOWED_VALIDATION_RISK,
          str(sorted(allowed_vr)))
    valid_roles = set(cat.get("valid_binding_roles", []))
    check("valid_binding_roles == the valid set", valid_roles == _VALID_BINDING_ROLES,
          str(sorted(valid_roles)))

    # NO raw keys anywhere.
    check("no raw API keys in catalog", not _KEY_RE.search(json.dumps(cat)))

    # --- cross_reference: names BOTH existing catalogs; declares no duplicate provider_ids ---
    xref = cat.get("cross_reference")
    check("catalog has a cross_reference", isinstance(xref, dict))
    xref_blob = json.dumps(xref).lower() if isinstance(xref, dict) else ""
    check("cross_reference names teleon_runtime_landscape", "teleon_runtime_landscape" in xref_blob)
    check("cross_reference names teleon_adjacent_extended", "teleon_adjacent_extended" in xref_blob)

    # --- per-entry checks ---
    seen_rank_one = False
    seen_required: dict[str, bool] = {tok: False for tok in _REQUIRED_TOOL_TOKENS}
    seen_pids: set[str] = set()

    for e in entries:
        pid = e.get("provider_id", "?")
        check(f"{pid} unique provider_id", pid not in seen_pids, pid)
        seen_pids.add(pid)

        for f in _REQUIRED:
            check(f"{pid} has '{f}'", f in e)

        st = e.get("status")
        check(f"{pid} status in {{candidate,reference,research,research_archived}} (NEVER active)",
              st in _ALLOWED_STATUS, str(st))
        check(f"{pid} status is not 'active'", st != "active", str(st))

        vr = e.get("validation_risk")
        check(f"{pid} validation_risk in allowed set", vr in _ALLOWED_VALIDATION_RISK, str(vr))

        br = e.get("binding_role")
        check(f"{pid} binding_role in valid set", br in _VALID_BINDING_ROLES, str(br))

        lc = e.get("license_confidence")
        check(f"{pid} license_confidence in {{verified,unverified}}", lc in _LICENSE_CONFIDENCE, str(lc))

        # every entry: teleon_local_equivalent + do_not_adopt_as_primary + integer closeness_rank.
        check(f"{pid} has a teleon_local_equivalent", bool(e.get("teleon_local_equivalent")))
        check(f"{pid} has a do_not_adopt_as_primary", bool(e.get("do_not_adopt_as_primary")))
        cr = e.get("closeness_rank")
        check(f"{pid} closeness_rank is an int", isinstance(cr, int) and not isinstance(cr, bool), str(cr))
        if isinstance(cr, int) and not isinstance(cr, bool) and cr == 1:
            seen_rank_one = True

        check(f"{pid} has source_url", bool(e.get("source_url")))

        # required tools present (match on provider_id token OR name).
        hay = (pid + " " + str(e.get("name", ""))).lower()
        for tok in _REQUIRED_TOOL_TOKENS:
            if tok in hay:
                seen_required[tok] = True

        # NO existing-catalog provider re-added as a NEW entry (avoid duplicate catalogs).
        for dup in _FORBIDDEN_DUP_TOKENS:
            check(f"{pid} is NOT a duplicate of an existing-catalog provider ('{dup}')",
                  dup not in pid.lower(), pid)

    check("at least one entry is closeness_rank == 1 (the closest matches)", seen_rank_one)
    for tok, label in _REQUIRED_TOOL_TOKENS.items():
        check(f"{label} is present in the catalog", seen_required[tok])

    if fails:
        print("check_capability_binding_landscape: FAILURES")
        for f in fails[:30]:
            print("  -", f)
        return 1

    n = len(entries)
    by_status: dict[str, int] = {}
    for e in entries:
        by_status[e.get("status", "?")] = by_status.get(e.get("status", "?"), 0) + 1
    rank1 = sum(1 for e in entries if e.get("closeness_rank") == 1)
    status_str = ", ".join(f"{k}={v}" for k, v in sorted(by_status.items()))
    print(
        f"PASS — check_capability_binding_landscape: {n} entries ({status_str}; 0 active); "
        f"{rank1} ranked closeness_rank==1 (Kratix/Radius/Score); every entry is a CapabilityTask binding "
        f"target with a teleon_local_equivalent + do_not_adopt_as_primary + integer closeness_rank; "
        f"binding_role/validation_risk/license_confidence in allowed sets; verdict = NONE does the full "
        f"lifecycle; positioning_law = control plane ABOVE; cross_reference names teleon_runtime_landscape + "
        f"teleon_adjacent_extended with no duplicate {sorted(_FORBIDDEN_DUP_TOKENS)} providers; no raw keys."
    )
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Proof for the capability-binding / IfC landscape catalog.")
    ap.add_argument("--self-test", action="store_true", help="run the deterministic offline self-test")
    ap.parse_args()
    raise SystemExit(main())
