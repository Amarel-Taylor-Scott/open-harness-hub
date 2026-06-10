#!/usr/bin/env python3
"""scripts.check_no_consumption_bypass — proof (C-CONSUME-1): you cannot get served facts without going
through the ConsumptionService + its gate. (1) serve() yields ZERO served facts for a non-consumable pack;
(2) the ContextResponse truth object is CONSTRUCTED only in scripts/runtime/consumption.py within the governed
runtime; (3) no web page builds served_facts / a ContextResponse (projection-only); (4) the consumption module
reaches no admin server / web / global bus.

CLI: python3 scripts/check_no_consumption_bypass.py --self-test
"""
from __future__ import annotations

import argparse
from pathlib import Path

from scripts.runtime.consumption import ConsumptionService
from scripts.runtime.optimization import ConsumptionReadinessGate

_REPO = Path(__file__).resolve().parents[1]
NOW = "2026-06-05T00:00:00Z"


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    # 1) no consumable → no served facts (the core anti-bypass): cannot serve truth past a failed gate
    pack = {"pack_id": "p", "tenant_id": "demo", "artifacts": [
        {"artifact_id": "alleg-1", "artifact_type": "narrative_allegation", "claim_type": "narrative_allegation",
         "claim_status": "unverified_allegation", "source_handle": "ctx://x#n", "content_hash": "h", "tenant_id": "demo"}]}
    rdy = ConsumptionReadinessGate().assess(pack, verification_receipt={"decision": "allow", "receipt_id": "v"},
                                            optimization_receipt={"decision": "promote", "receipt_id": "o"},
                                            signals={"excluded_ids": set()}, now=NOW)
    out = ConsumptionService().serve(tenant_id="demo", promoted_pack=pack, verification_receipt={"decision": "allow", "receipt_id": "v"},
                                     optimization_receipt={"decision": "promote", "receipt_id": "o"}, readiness_report=rdy,
                                     held_out=[], answer="x", now=NOW)
    check("serve() yields NO served facts when the readiness gate fails", out["response"].to_dict()["served_facts"] == [])

    # 2) ContextResponse is constructed only in consumption.py within the governed runtime
    runtime_dir = _REPO / "scripts" / "runtime"
    builders = [p.name for p in runtime_dir.glob("*.py") if "ContextResponse(" in p.read_text(encoding="utf-8", errors="ignore")]
    check("ContextResponse is built only in scripts/runtime/consumption.py", builders == ["consumption.py"], str(builders))
    defs = [p.name for p in runtime_dir.glob("*.py") if "class ContextResponse" in p.read_text(encoding="utf-8", errors="ignore")]
    check("ContextResponse is DEFINED only in consumption.py", defs == ["consumption.py"], str(defs))

    # 3) no web page builds served_facts or a ContextResponse (projection-only — it may only fetch them)
    web = _REPO / "web" / "baltor"
    web_offenders = []
    if web.is_dir():
        for p in web.rglob("*.html"):
            t = p.read_text(encoding="utf-8", errors="ignore")
            if "ContextResponse(" in t or "served_facts =" in t or "served_facts.push" in t:
                web_offenders.append(p.name)
    check("no web page constructs served_facts / a ContextResponse (projection-only)", web_offenders == [], str(web_offenders))

    # 4) the consumption module reaches no admin server / web / global bus
    src = (_REPO / "scripts/runtime/consumption.py").read_text(encoding="utf-8")
    forbidden = ["baltor_admin_demo_server", "from web", "import web", "BUS.publish"]
    check("consumption module imports no admin server / web / global bus", not any(f in src for f in forbidden),
          str([f for f in forbidden if f in src]))

    print(f"\n{'PASS — check_no_consumption_bypass: no served facts without passing the gate; ContextResponse is built only in the consumption runtime; web is projection-only; no admin/web/bus bypass.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: no consumption bypass.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
