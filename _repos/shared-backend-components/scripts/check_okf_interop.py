#!/usr/bin/env python3
"""check_okf_interop — proof that Baltor interoperates with Google's Open Knowledge Format (OKF) at the EDGES
without surrendering the core: we IMPORT an OKF repo into governed objects and EXPORT governed objects back to
conformant OKF whose frontmatter ALSO carries our assurance (verified / authoritative_source / freshness / receipt)
plus a reserved log.md reconstructed from our CDC history — the part OKF itself does not standardize.

Asserts: (1) OKF's `type`-required rule is enforced on import; (2) export emits a conformant OKF repo (markdown +
YAML frontmatter, one concept per file, reserved index.md/log.md); (3) round-trip import(export(x)) is LOSSLESS for
answer-critical fields + the governance sidecar + arbitrary frontmatter keys (lossless-distillation law); (4) the
governance OKF doesn't mandate rides inside a conformant OKF file (we are the only producer whose OKF proves whether
content is true/current) — OKF is a PROJECTION, our object is the core; (5) the CDC/freshness history lands in
log.md; (6) nothing ever serves truth. OKF is v0.1 DRAFT/single-vendor → adopted as a CANDIDATE interop format
(discovery ≠ trust).

CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_okf_interop.py --self-test
"""
from __future__ import annotations

import os
import sys

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _R not in sys.path:
        sys.path.insert(0, _R)

from src.baltor.native.okf_adapter import (
    GOVERNANCE_KEY, GovernedConcept, OKF_INDEX_FILE, OKF_LOG_FILE, OKF_REQUIRED_KEY,
    okf_export, okf_import, round_trip,
)


def _sample() -> list[GovernedConcept]:
    return [
        GovernedConcept(
            concept_id="reg-e-error-resolution-deadline", type="runbook",
            title="Reg E error-resolution deadline", description="Days to resolve a disputed EFT.",
            resource="ecfr://12/1005.11", timestamp="2026-06-19", tags=("regulation", "reg-e"),
            body="The financial institution must resolve within the regulatory deadline.",
            governance={"verified": True, "authoritative_source": "ecfr://12/1005.11",
                        "freshness_status": "fresh", "receipt_id": "rcpt_abc123",
                        "cdc_history": [{"kind": "changed", "version": "2026-edition", "source": "ecfr://12/1005.11"}]},
            extra={"owner_team": "compliance", "review_cycle": "quarterly"}),  # arbitrary OKF keys — must survive
        GovernedConcept(
            concept_id="us-tax-bracket-owed", type="metric",
            title="US federal tax owed", tags=("tax",),
            body="Compute owed tax from bracketed income.",
            governance={"verified": False, "freshness_status": "held_out"}),
    ]


def _self_test() -> int:
    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    concepts = _sample()
    repo = okf_export(concepts)

    # (1) OKF's one hard rule enforced on import
    rejected = False
    try:
        okf_import({"bad.md": "---\ntitle: no type here\n---\nbody"})
    except ValueError:
        rejected = True
    ck("OKF `type`-required rule is enforced on import (a concept without type is rejected)", rejected)

    # (2) export is a conformant OKF repo
    ck("export emits one markdown concept file per concept + reserved index.md/log.md",
       OKF_INDEX_FILE in repo and OKF_LOG_FILE in repo
       and "reg-e-error-resolution-deadline.md" in repo and "us-tax-bracket-owed.md" in repo)
    one = repo["reg-e-error-resolution-deadline.md"]
    ck("each concept file is markdown + YAML frontmatter with the required `type`",
       one.startswith("---") and f"{OKF_REQUIRED_KEY}: runbook" in one and one.count("---") >= 2)

    # (3) round-trip lossless (answer-critical fields + governance + arbitrary extras)
    back = {c.concept_id: c for c in round_trip(concepts)}
    src = {c.concept_id: c for c in concepts}
    rid = "reg-e-error-resolution-deadline"
    ck("round-trip preserves type/title/body/tags (lossless)",
       back[rid].type == src[rid].type and back[rid].title == src[rid].title
       and back[rid].body == src[rid].body and back[rid].tags == src[rid].tags)
    ck("round-trip preserves the governance sidecar (verified/source/freshness/receipt)",
       back[rid].governance.get("verified") is True
       and back[rid].governance.get("authoritative_source") == "ecfr://12/1005.11"
       and back[rid].governance.get("freshness_status") == "fresh"
       and back[rid].governance.get("receipt_id") == "rcpt_abc123")
    ck("round-trip preserves ARBITRARY OKF frontmatter keys (extra) — no lossy promotion",
       back[rid].extra.get("owner_team") == "compliance" and back[rid].extra.get("review_cycle") == "quarterly")

    # (4) the assurance OKF doesn't mandate rides inside a conformant OKF file; OKF is a projection, object is core
    ck("our governance rides in the OKF frontmatter (the assurance OKF itself does not standardize)",
       GOVERNANCE_KEY in one and '"verified": true' in one and '"serves_truth": false' in one)

    # (5) CDC/freshness history lands in the reserved log.md (what makes our OKF provably current)
    ck("the reserved log.md carries the CDC/freshness change history",
       "2026-edition" in repo[OKF_LOG_FILE] and "ecfr://12/1005.11" in repo[OKF_LOG_FILE])
    ck("the reserved index.md shows verification + freshness per concept (progressive disclosure)",
       "verified" in repo[OKF_INDEX_FILE] and "freshness" in repo[OKF_INDEX_FILE])

    # (6) never serves truth + deterministic
    ck("no concept serves truth (a format adapter never serves truth)",
       all(c.as_dict()["serves_truth"] is False for c in concepts)
       and all('"serves_truth": false' in repo[f"{c.concept_id}.md"] for c in concepts if c.governance))
    ck("deterministic (same concepts -> identical OKF repo)", okf_export(_sample()) == repo)

    print("\n" + ("PASS - check_okf_interop: Baltor imports OKF and exports conformant OKF whose frontmatter ALSO "
                  "carries our assurance (verified/source/freshness/receipt) + a CDC log.md — round-trip lossless "
                  "(governance + arbitrary keys survive). OKF rides at the edge as a CANDIDATE interop format; our "
                  "governed object stays the core. 'They standardize where context lives; Baltor governs whether "
                  "it's true.' Never serves truth."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def _main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--self-test" in argv:
        return _self_test()
    print("usage: check_okf_interop.py --self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
