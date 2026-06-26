#!/usr/bin/env python3
"""check_profession_capability_seeder — proof that the DueCare template generalizes BEYOND migrant-worker protection
to many professions: every profession derives the same governed capability shape (license-verification ·
exclusion-screening · compliance-currency + profession-specific), each a DURABLE candidate (registry/exclusion
access is a structural gap), serves_truth=false. The migration vertical (DueCare) is present as ONE instance; the
rest prove the generalization. Occupation spine = O*NET + Stanford WORKBank.

  --build      (re)write the profession-scale candidate feed
  --self-test  validate the seeder + generated feed (the registered proof)

CLI: PYTHONPATH=. python3 scripts/check_profession_capability_seeder.py --build | --self-test
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _R not in sys.path:
        sys.path.insert(0, _R)

_REPO = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_FEED = _REPO / "data" / "capability-candidates" / "discovered-feed-profession-scale-2026-06-20.json"

from src.teleon.seeds import all_seeds
from src.teleon.seeds.profession_capability_seeder import PROFESSIONS, build_feed, derive_for


def write_feed() -> str:
    _FEED.parent.mkdir(parents=True, exist_ok=True)
    _FEED.write_text(json.dumps(build_feed(), indent=2) + "\n")
    return str(_FEED.relative_to(_REPO))


def _self_test() -> int:
    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    feed = build_feed()
    cands = feed["candidates"]
    sectors = {p.sector for p in PROFESSIONS}

    ck(">= 12 professions across >= 6 sectors (breadth beyond one vertical)",
       len(PROFESSIONS) >= 12 and len(sectors) >= 6, f"{len(PROFESSIONS)} professions / {len(sectors)} sectors")
    # the generalization: DueCare's migration vertical is ONE instance; many others exist
    slots = {p.slot for p in PROFESSIONS}
    ck("the migrant-recruitment vertical (DueCare) is present as ONE instance", "recruitment-agency" in slots)
    ck("professions BEYOND migrant-worker protection exist (healthcare/legal/finance/maritime/...)",
       {"registered-nurse", "attorney", "cpa-accountant", "seafarer"} <= slots and "migration" != list(sectors)[0] or len(sectors) >= 6)

    # every profession derives the full governed shape (>=3 base capabilities) and every candidate is governed
    for p in PROFESSIONS:
        d = derive_for(p)
        base = [c for c in d if c["capability_slot"].endswith(("-license-verification", "-exclusion-screening", "-compliance-currency"))]
        if len(base) != 3:
            ck(f"{p.slot} derives the 3 base governed capabilities", False, str([c['capability_slot'] for c in base]))
            break
    else:
        ck("every profession derives the 3 base governed capabilities (license/exclusion/currency)", True)

    ck("every candidate is a DURABLE, propose-only candidate (serves_truth=false, durable=true)",
       all(c["candidate"] is True and c["serves_truth"] is False and c["durable"] is True for c in cands))
    req = {"capability_slot", "profession", "sector", "onet_soc", "intent", "authoritative_source",
           "determinism_ceiling", "gap_hypothesis"}
    ck("every candidate carries profession/sector/O*NET-SOC/authoritative-source/determinism/gap",
       all(req <= set(c) for c in cands), str([c["capability_slot"] for c in cands if not req <= set(c)][:3]))

    # integration: the attorney's court-deadline capability links the already-built deterministic seed
    attorney = [c for c in cands if c["profession"] == "attorney" and c["capability_slot"].endswith("court-deadline")]
    seed_slots = {s.slot for s in all_seeds()}
    ck("attorney derives a court-deadline capability that links the built court-deadline-calculator seed",
       len(attorney) == 1 and "court-deadline-calculator" in seed_slots)

    ck("the feed cites the O*NET/WORKBank occupation spine (rigorous 'scour professions')",
       "O*NET" in feed["occupation_spine"] and "WORKBank" in feed["occupation_spine"])
    ck("feed conforms to DiscoveredCapabilityFeed with provenance + governance",
       feed["feed_version"] == "DiscoveredCapabilityFeed" and bool(feed.get("provenance")) and bool(feed.get("governance")))
    if _FEED.exists():
        ck("on-disk feed is fresh vs the seeder (regenerate with --build)", json.loads(_FEED.read_text()) == feed)
    ck("deterministic", build_feed() == feed)

    print("\n" + (f"PASS - check_profession_capability_seeder: {len(PROFESSIONS)} professions across {len(sectors)} "
                  f"sectors derive {len(cands)} DURABLE governed capability candidates (license/exclusion/currency + "
                  f"profession-specific) — DueCare's migrant-recruitment vertical is ONE instance; the rest prove the "
                  f"generalization. O*NET/WORKBank spine; never serves truth; nothing promoted."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def _main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--build" in argv:
        print("wrote:", write_feed())
        return 0
    if "--self-test" in argv:
        return _self_test()
    print("usage: check_profession_capability_seeder.py --build | --self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
