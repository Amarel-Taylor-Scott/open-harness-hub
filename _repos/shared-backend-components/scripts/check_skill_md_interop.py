#!/usr/bin/env python3
"""check_skill_md_interop — proof that Baltor interoperates with Anthropic's SKILL.md (Agent Skills) format at the
EDGE without surrendering the core: import a SKILL.md into a governed skill and export a governed skill back to a
conformant SKILL.md whose frontmatter ALSO carries our assurance (verified / measured lift / source-authority /
receipt) — the part SKILL.md itself does not standardize.

Asserts: (1) the spec's name+description-required rule is enforced on import; (2) export emits a conformant
SKILL.md; (3) round-trip import(export(x)) is LOSSLESS for name/description/body + allowed-tools + the governance
sidecar + arbitrary frontmatter keys; (4) our lift/safety governance rides inside a conformant SKILL.md (we are the
only producer whose skills PROVE their lift) — SKILL.md is a PROJECTION, the governed skill is the core; (5) nothing
serves truth (an imported skill is a candidate until it passes the gap/lift + safety gates).

CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_skill_md_interop.py --self-test
"""
from __future__ import annotations

import os
import sys

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _R not in sys.path:
        sys.path.insert(0, _R)

from src.baltor.native.skill_md_adapter import (
    GOVERNANCE_KEY, GovernedSkill, SKILL_REQUIRED_KEYS, round_trip, skill_md_export, skill_md_import,
)


def _sample() -> GovernedSkill:
    return GovernedSkill(
        skill_id="reg-e-dispute-letter", name="reg-e-dispute-letter",
        description="Use when drafting a Regulation E error-resolution notice for a disputed electronic funds transfer.",
        body="Draft the notice citing the current Reg E deadline. Verify the deadline against the authoritative source.",
        license="MIT", version="1", allowed_tools=("Read", "Write"),
        governance={"verified": True, "measured_lift": 0.71, "source_authority": "ecfr://12/1005.11",
                    "receipt_id": "rcpt_skill_001"},
        extra={"owner_team": "compliance", "risk_tier": "high"})  # arbitrary SKILL.md keys — must survive


def _self_test() -> int:
    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    skill = _sample()
    md = skill_md_export(skill)

    # (1) the spec's hard rule enforced on import
    rejected = 0
    for bad in ("---\ndescription: no name here\n---\nbody", "---\nname: no-desc\n---\nbody"):
        try:
            skill_md_import("bad/SKILL.md", bad)
        except ValueError:
            rejected += 1
    ck("SKILL.md name+description-required rule enforced on import (both must be present)", rejected == 2)

    # (2) export is a conformant SKILL.md
    ck("export emits a conformant SKILL.md (frontmatter with name+description + a body)",
       md.startswith("---") and "name: reg-e-dispute-letter" in md and "description:" in md
       and md.count("---") >= 2 and "Draft the notice" in md)

    # (3) round-trip lossless (name/description/body + allowed-tools + governance + arbitrary extras)
    back = round_trip(skill)
    ck("round-trip preserves name/description/body (lossless)",
       back.name == skill.name and back.description == skill.description and back.body == skill.body)
    ck("round-trip preserves allowed-tools + license + version",
       back.allowed_tools == skill.allowed_tools and back.license == "MIT" and back.version == "1")
    ck("round-trip preserves the governance sidecar (verified / measured lift / source-authority / receipt)",
       back.governance.get("verified") is True and back.governance.get("measured_lift") == 0.71
       and back.governance.get("source_authority") == "ecfr://12/1005.11"
       and back.governance.get("receipt_id") == "rcpt_skill_001")
    ck("round-trip preserves ARBITRARY SKILL.md frontmatter keys (extra) — no lossy promotion",
       back.extra.get("owner_team") == "compliance" and back.extra.get("risk_tier") == "high")

    # (4) the assurance SKILL.md doesn't mandate rides inside a conformant SKILL.md; SKILL.md is a projection
    ck("our lift/safety governance rides in the SKILL.md frontmatter (the assurance SKILL.md does not standardize)",
       GOVERNANCE_KEY in md and '"verified": true' in md and '"measured_lift": 0.71' in md
       and '"serves_truth": false' in md)

    # (5) never serves truth + deterministic
    ck("no governed skill serves truth (a format adapter never serves truth; an imported skill is a candidate)",
       skill.as_dict()["serves_truth"] is False and '"serves_truth": false' in md and back.as_dict()["serves_truth"] is False)
    ck("deterministic (same skill -> identical SKILL.md)", skill_md_export(_sample()) == md)
    ck("SKILL_REQUIRED_KEYS are exactly name + description (the spec rule)", set(SKILL_REQUIRED_KEYS) == {"name", "description"})

    print("\n" + ("PASS - check_skill_md_interop: Baltor imports SKILL.md and exports conformant SKILL.md whose "
                  "frontmatter ALSO carries our assurance (verified / measured lift / source-authority / receipt) — "
                  "round-trip lossless (governance + arbitrary keys survive). SKILL.md rides at the edge as a "
                  "candidate projection; the governed skill stays the core. 'They standardize the skill format; "
                  "Baltor governs whether it lifts and is safe.' Never serves truth."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def _main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--self-test" in argv:
        return _self_test()
    print("usage: check_skill_md_interop.py --self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
