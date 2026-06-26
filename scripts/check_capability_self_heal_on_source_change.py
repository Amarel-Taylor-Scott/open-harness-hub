#!/usr/bin/env python3
"""scripts.check_capability_self_heal_on_source_change — PROOF: a capability SILENTLY broken by an
external source change is DETECTED (by its benchmark) and SELF-HEALED, with no user action — the
owner's pain (2026-06-11): scrapers / fact-checkers that keep running but return garbage when a
site/source moves.

The killer scenario, deterministic + offline:
  - a SCRAPER ('scrape_prices', depends on source 'site-x') whose bound parser worked on the OLD
    site but now FAILS its benchmark on the changed HTML (silent break) → a candidate parser that
    re-passes the benchmark HEALS it; the prior is kept as a reversible rollback; the broken output
    was never served.
  - a FACT-CHECKER ('factcheck_rege', depends on 'reg-e-source') whose source API moved and whose
    only candidate ALSO cannot re-ground the fact → DEGRADED (honest): benchmark still fails, no
    fabricated heal, escalation to the next rung recorded but NOT auto-dispatched, broken output not
    served as truth.
  - an UNRELATED capability (depends on 'weather-api') is UNTOUCHED by the 'site-x' change.
  - a capability with NO scorable benchmark → NO_BENCHMARK + degraded (never a fabricated clean bill).

Cross-cutting invariants (mirror check_purpose_task_self_heal_e2e): candidate never served before it
is proven; promotion reversible to a preserved rollback target; degraded ≠ silently-healthy; no
fabricated heal. Exit 0/1.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

_REPO = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.teleon.self_healing import reheal as rh

_NOW = "2026-06-11T00:00:00Z"

# ── the scraper: a parser that worked on the OLD site, and one adapted to the NEW site ──────────────
_PRICES = {"p1": "PRICE:42", "p2": "PRICE:99"}


def _result(output: str, cost: float = 1.0, handles=("ctx://site-x",)):
    return {"output": output, "output_contract": "Price", "cost": cost, "latency_ms": 5,
            "error": None, "source_handles": list(handles)}


def _scraper_old_parser(_inp):           # ran fine yesterday; the site changed → now returns junk
    return _result("PRICE:")


def _scraper_new_parser(inp):            # adapted to the new HTML → correct
    return _result(_PRICES.get(inp.get("page"), "PRICE:?"))


def _fc_old(_inp):                       # the Reg-E source API moved → can no longer ground the fact
    return {"output": "", "output_contract": "Fact", "cost": 1.0, "latency_ms": 5,
            "error": None, "source_handles": []}


def _fc_candidate_also_broken(_inp):     # the only candidate also cannot re-ground the moved source
    return {"output": "UNKNOWN", "output_contract": "Fact", "cost": 1.0, "latency_ms": 5,
            "error": None, "source_handles": []}


def _registry():
    return {
        "scrape_prices": [
            {"impl_id": "parser_oldsite", "priority": 30, "handler": _scraper_old_parser},
            {"impl_id": "parser_newsite", "priority": 20, "handler": _scraper_new_parser},
        ],
        "factcheck_rege": [
            {"impl_id": "factcheck", "priority": 30, "handler": _fc_old},
            {"impl_id": "factcheck", "priority": 20, "handler": _fc_candidate_also_broken},
        ],
        "weather": [{"impl_id": "weather", "priority": 30, "handler": lambda _i: _result("sunny")}],
        "no_suite_cap": [{"impl_id": "x", "priority": 30, "handler": lambda _i: _result("anything")}],
    }


def _suite(sid, pairs):
    return {"suite_id": sid, "examples": [{"input": i, "expected": e} for i, e in pairs]}


def _scraper_spec():
    return {"capability_id": "scrape-prices", "capability_slot": "scrape_prices",
            "output_contract": "Price", "success_criteria": {"max_cost": 5.0},
            "eval_suite": _suite("scrape", [({"page": "p1"}, "PRICE:42"), ({"page": "p2"}, "PRICE:99")]),
            "source_dependencies": ["site-x"], "alternatives": ["parser_newsite"]}


def _fc_spec():
    return {"capability_id": "factcheck-rege", "capability_slot": "factcheck_rege",
            "output_contract": "Fact", "success_criteria": {"max_cost": 5.0},
            "eval_suite": _suite("rege", [({"q": "deadline"}, "10 business days")]),
            "source_dependencies": ["reg-e-source"], "alternatives": ["factcheck"]}


def _unrelated_spec():
    return {"capability_id": "weather", "capability_slot": "weather", "output_contract": "W",
            "success_criteria": {}, "eval_suite": _suite("w", [({}, "sunny")]),
            "source_dependencies": ["weather-api"], "alternatives": []}


def _no_suite_spec():
    return {"capability_id": "no-suite", "capability_slot": "no_suite_cap", "output_contract": "X",
            "success_criteria": {}, "source_dependencies": ["site-x"], "alternatives": []}


def _self_test() -> int:
    fails: list[str] = []

    def check(n: str, ok: bool, d: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok:
            fails.append(n)

    reg = _registry()
    specs = [_scraper_spec(), _fc_spec(), _unrelated_spec()]

    # the SCRAPER, on the changed site, fails its benchmark (silent break — runs, wrong output)
    from src.teleon.purpose_tasks.purpose_task import provision
    bound = provision(_scraper_spec(), reg)
    h0 = rh.benchmark_health(bound, reg)
    check("0: on the CHANGED site the bound parser FAILS the benchmark (silent break — runs, wrong)",
          h0["meets"] is False and "benchmark_fail" in h0["drift"] and h0["failures"], str(h0["drift"]))

    # site-x changed → re-heal only the dependents
    ev = {"kind": "changed", "source": "site-x"}
    outs = {o.capability_id: o for o in rh.reheal_on_source_change(ev, specs, reg, now=_NOW)}

    s = outs.get("scrape-prices")
    check("1: the scraper (depends on site-x) was re-evaluated and DRIFT detected",
          s is not None and s.drifted is True)
    check("2: the scraper HEALED — a candidate that re-passes the benchmark was promoted",
          s and s.status == rh.HEAL_STATUS_HEALED and s.promoted is True
          and s.served_impl_id == "parser_newsite", s and s.status)
    check("3: the prior impl is kept as a reversible rollback target (lossless)",
          s and s.rollback_target == "parser_oldsite")

    check("4: the UNRELATED capability (weather-api) is UNTOUCHED by the site-x change",
          "weather" not in outs)

    fc = outs.get("factcheck-rege")
    check("5: the fact-checker also depends on site-x? NO — so it is untouched by THIS event",
          fc is None)

    # now the fact-checker's OWN source moves → it cannot re-ground → DEGRADED (honest)
    ev2 = {"kind": "changed", "source": "reg-e-source"}
    out_fc = {o.capability_id: o for o in rh.reheal_on_source_change(ev2, specs, reg, now=_NOW)}.get("factcheck-rege")
    check("6: the fact-checker's source moved → DRIFT detected (it can no longer ground the fact)",
          out_fc is not None and out_fc.drifted is True)
    check("7: no candidate re-grounds it → DEGRADED (honest: not silently healthy, broken not promoted)",
          out_fc and out_fc.status == rh.HEAL_STATUS_DEGRADED and out_fc.degraded is True
          and out_fc.promoted is False, out_fc and out_fc.status)
    check("8: the refusal is honest — escalation recorded to the next rung, NOT auto-dispatched",
          out_fc and isinstance(out_fc.escalation, dict)
          and out_fc.escalation.get("next_rung") == rh.NEXT_RUNG
          and out_fc.escalation.get("auto_dispatched") is False)
    check("9: a DEGRADED capability is NOT silently healthy — its benchmark still fails (truth-telling)",
          out_fc and rh.benchmark_health(provision(_fc_spec(), reg), reg)["meets"] is False)

    # NO-benchmark capability → cannot certify → degraded honestly (never a fabricated clean bill)
    out_ns = {o.capability_id: o for o in
              rh.reheal_on_source_change(ev, [_no_suite_spec()], reg, now=_NOW)}.get("no-suite")
    check("10: a capability with NO scorable benchmark → NO_BENCHMARK + degraded (no fabricated clean bill)",
          out_ns is not None and out_ns.status == rh.HEAL_STATUS_NO_BENCHMARK and out_ns.degraded is True)

    # a non-change event (unchanged) does nothing
    check("11: an 'unchanged' CDC event triggers no re-heal (only changed/new do)",
          rh.reheal_on_source_change({"kind": "unchanged", "source": "site-x"}, specs, reg, now=_NOW) == [])

    # determinism
    check("12: the whole motion is deterministic (same event → same outcomes)",
          [o.status for o in rh.reheal_on_source_change(ev, specs, reg, now=_NOW)]
          == [o.status for o in rh.reheal_on_source_change(ev, specs, reg, now=_NOW)])

    print(("PASS — " if not fails else f"{len(fails)} FAILURES — ")
          + "check_capability_self_heal_on_source_change: a source change is detected by the benchmark, "
            "the dependent scraper self-heals to a candidate that re-passes it (prior kept as rollback), "
            "a fact-checker that nothing can re-ground DEGRADES honestly (escalation recorded, never a "
            "fabricated heal, broken output never served), and unrelated capabilities are untouched.")
    return 1 if fails else 0


def main(argv=None) -> int:
    import argparse
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--self-test", action="store_true")
    p.parse_args(argv)
    return _self_test()


if __name__ == "__main__":
    raise SystemExit(main())
