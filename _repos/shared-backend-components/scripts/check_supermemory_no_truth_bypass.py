#!/usr/bin/env python3
"""scripts.check_supermemory_no_truth_bypass — proof (C-MEM-1, the governance line): a memory/recall result
can NEVER become a served/canonical fact without passing Baltor's existing VerificationGate + Reconciliation +
ConsumptionGate. A MemoryArtifact stays claim_status="candidate". Concretely:

  1) every memory result the Memory API returns is claim_status=candidate (artifacts + search + profile.dynamic);
  2) the Memory handler does NOT construct a ContextResponse / served_facts and does NOT promote memory to a
     fact (no claim_status "fact"/"canonical"/"served" written; no VerificationGate/Consumption bypass);
  3) the ONLY promoted facts the handler projects (profile.static) come from the governed consumption layer
     (the Consumption API), not from the provider — a provider cannot mint canonical facts;
  4) the Memory handler reaches no admin server / web / global bus (projection-only).

Deterministic, offline. Models _repos/shared-backend-components/scripts/check_no_consumption_bypass.py.

CLI: python3 _repos/shared-backend-components/scripts/check_supermemory_no_truth_bypass.py --self-test
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource  # noqa: E402

import argparse
from pathlib import Path

from scripts.api_memory_handler import CANDIDATE, handle

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
_HANDLER = _resource("scripts/api_memory_handler.py")

#: claim_status values that mean "served truth" — a memory artifact must NEVER carry one.
_TRUTH_STATUSES = ("fact", "canonical", "served", "promoted")


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    # 1) every memory result is a candidate (the core anti-bypass): a recall result is never a served fact.
    _, arts = handle("GET", "/api/memory/artifacts", {"tenant_id": "demo"})
    _, srch = handle("GET", "/api/memory/search", {"tenant_id": "demo", "q": "x"})
    _, prof = handle("GET", "/api/memory/profile", {"tenant_id": "demo"})
    mem_items = list(arts.get("artifacts", [])) + list(srch.get("results", [])) + list(prof.get("profile", {}).get("dynamic", []))
    check("every memory artifact / recall result is claim_status=candidate",
          all(i.get("claim_status") == CANDIDATE for i in mem_items if isinstance(i, dict)))
    check("no memory result carries a TRUTH claim_status (fact/canonical/served/promoted)",
          not any(i.get("claim_status") in _TRUTH_STATUSES for i in mem_items if isinstance(i, dict)))

    # 2) profile.static (promoted) NEVER comes from a provider: if anything is static, it must cite the
    #    consumption source, not a memory provider id.
    static = prof.get("profile", {}).get("static", [])
    check("profile.static promotions (if any) come from the consumption layer, not the provider",
          all(s.get("source") == "consumption-api" for s in static if isinstance(s, dict)), str(static[:2]))

    # 3) the handler SOURCE never constructs served truth and never bypasses the gate.
    src = _HANDLER.read_text(encoding="utf-8")
    forbidden_truth = ("ContextResponse(", "served_facts =", "served_facts.append",
                       '"claim_status": "fact"', "'claim_status': 'fact'",
                       '"claim_status": "canonical"', '"claim_status": "served"')
    truth_off = [f for f in forbidden_truth if f in src]
    check("memory handler constructs NO served-truth object (no ContextResponse / served_facts / fact status)",
          truth_off == [], str(truth_off))

    # the handler must pin CANDIDATE on provider output (defense-in-depth): _candidate() re-stamps it.
    check("handler forces claim_status=candidate on provider output (_candidate re-stamp)",
          "def _candidate(" in src and 'out["claim_status"] = CANDIDATE' in src)

    # 4) the handler reaches no admin server / web / global bus (projection-only).
    bypass = ["baltor_admin_demo_server", "from web", "import web", "BUS.publish", "DURABLE"]
    bypass_off = [b for b in bypass if b in src]
    check("memory handler imports no admin server / web / global bus / DURABLE", bypass_off == [], str(bypass_off))

    # 5) the only governed-promotion symbol the handler references is the consumption projection (read-only).
    check("handler promotes through the consumption layer only (api_context_handler.runtime_consumption)",
          "from scripts.api_context_handler import runtime_consumption" in src)
    # ...and does not call any promotion/verification mutator directly (it only READS the consumption projection).
    mutators = ["VerificationGate(", "ConsumptionService(", ".promote(", ".serve("]
    mut_off = [m for m in mutators if m in src]
    check("handler does not directly drive a gate/promotion mutator (read-only projection)", mut_off == [], str(mut_off))

    print(f"\n{'PASS — check_supermemory_no_truth_bypass: memory/recall results stay claim_status=candidate; the handler builds no served-truth object and bypasses no gate; only the governed consumption layer can supply promoted (static) facts; projection-only (no admin/web/bus).' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: memory cannot bypass the gate into a served fact.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
