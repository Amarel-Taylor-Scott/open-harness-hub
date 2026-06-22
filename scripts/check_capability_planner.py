#!/usr/bin/env python3
"""check_capability_planner — open-ended capabilities are recognized as iterative / scheduled / multi-component.

Proves the owner's requirement: given "scrape the internet for additional skills to include in openskillshub.io", the
processor recognizes it's ITERATIVE (loops, with a stop condition), MULTI-COMPONENT (a typed plan stringing the research
descent + the hub lifecycle), resolves the right hub, drives the research-catalog descent (browser only for deep detail),
and can be SCHEDULED. Execution is tested with an injected per-round stub (deterministic, offline).

  python3 scripts/check_capability_planner.py --self-test
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def _self_test() -> int:
    from src.teleon.capability_planner import classify, resolve_hub, infer_capability, plan, execute
    fails = []
    def ck(n, ok, d=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok: fails.append(n)

    hubs = ["OpenSkillsHub", "OpenToolsHub", "OpenContextHub", "OpenMCPHub"]
    kinds = {"OpenSkillsHub": "skills", "OpenToolsHub": "tools", "OpenContextHub": "context", "OpenMCPHub": "mcp_servers"}
    owner = "scrape the internet for additional skills to include in openskillshub.io"

    # classify
    c = classify(owner)
    ck("recognizes the owner's example as ITERATIVE (additional/scrape)", c["iterative"] is True)
    ck("a one-shot ask is NOT iterative", classify("convert this one skill to a tool")["iterative"] is False)
    cs = classify("keep openskillshub fresh daily")
    ck("recognizes SCHEDULED (daily/keep fresh) + maps cadence to cycles", cs["scheduled"] and cs["schedule_every"] == 7)

    # resolve hub: domain + content-kind keyword
    ck("resolves the hub from a domain (openskillshub.io -> OpenSkillsHub)", resolve_hub(owner, hubs, kinds=kinds) == "OpenSkillsHub")
    ck("resolves the hub from a content-kind keyword (more tools -> OpenToolsHub)",
       resolve_hub("find more tools to add", hubs, kinds=kinds) == "OpenToolsHub")

    # infer capability -> research descent
    ck("infers a cheap capability for a plain scrape ('list')", infer_capability(owner) == "list")
    ck("infers 'deep_detail' when full details behind pages are asked for",
       infer_capability("get the full details behind each skill page") == "deep_detail")

    # plan: multi-component decomposition
    p = plan(owner, hubs=hubs, kinds=kinds)
    names = [s.name for s in p.steps]
    ck("plan is multi-component (research_select -> discover -> digest -> dedupe -> verify -> version)",
       names[:4] == ["research_select", "discover", "digest", "dedupe"] and "verify" in names and "version" in names)
    ck("plan cadence is 'iterate' for the owner's example", p.cadence == "iterate")
    p_imp = plan("scrape github for skills and improve them for openskillshub", hubs=hubs, kinds=kinds)
    ck("an 'improve them' intent adds the improve step", "improve" in [s.name for s in p_imp.steps])
    p_deep = plan("navigate each site for the full details behind each skill in openskillshub", hubs=hubs, kinds=kinds)
    ck("deep-detail plan descends research to the LLM-driven browser", p_deep.research_descent.get("selected") == "llm_driven_browser")

    # execute: bounded loop stops on no-new; totals accumulate (injected per-round stub)
    seq = iter([{"discovered": 5, "ingested": 2, "verified": 2}, {"discovered": 5, "ingested": 1, "verified": 1},
                {"discovered": 5, "ingested": 0, "verified": 0}, {"discovered": 5, "ingested": 0, "verified": 0},
                {"discovered": 5, "ingested": 9, "verified": 9}])
    r = execute(p, hub_engines={}, run_round=lambda hub, intent: next(seq))
    ck("iterative execution STOPS after no-new-for-2-rounds (doesn't run the 5th)", r["rounds_run"] == 4 and "no new" in r["stopped_because"])
    ck("totals accumulate across rounds (2+1+0+0 ingested)", r["totals"]["ingested"] == 3)

    # run_once for a one-shot intent
    p1 = plan("convert this one skill to a tool", hubs=hubs, kinds=kinds)
    r1 = execute(p1, hub_engines={}, run_round=lambda hub, intent: {"discovered": 1, "ingested": 1, "verified": 1})
    ck("a one-shot capability runs exactly ONE round", r1["rounds_run"] == 1 and r1["cadence"] == "run_once")

    # DOCUMENT-EXTRACTION capability routes to the cascade (the owner's "write the capability → made efficient")
    from src.teleon.capability_planner import classify_capability_type
    ck("classifies a doc-extraction capability ('extract ... from these PDFs')",
       classify_capability_type("intake these land lease PDFs and extract lessor, royalty, acreage") == "document_extraction")
    ck("a hub-scrape capability is NOT misread as doc-extraction",
       classify_capability_type("scrape the internet for additional skills for openskillshub.io") == "hub_population")
    pdoc = plan("intake a PDF/email and extract the land lease schema", hubs=hubs, kinds=kinds)
    dnames = [s.name for s in pdoc.steps]
    ck("doc-extraction plan routes to the cascade (acquire→prune→patterns→cheap_llm→supervise)",
       pdoc.capability_type == "document_extraction" and dnames == ["acquire", "prune_compress", "patterns", "cheap_llm", "supervise"]
       and pdoc.route.get("schema_template") == "land_lease")
    rdoc = execute(pdoc, hub_engines={})
    ck("executing a doc-extraction plan runs the cascade + returns computed savings (supervised < frontier)",
       rdoc["capability_type"] == "document_extraction" and rdoc["supervised_cost"] < rdoc["frontier_only_cost"]
       and rdoc["pct_saved"] >= 70 and rdoc["made_efficient"] is True)

    # scheduled -> a schedule descriptor is emitted
    ps = plan("keep openskillshub fresh daily", hubs=hubs, kinds=kinds)
    rs = execute(ps, hub_engines={}, run_round=lambda hub, intent: {"discovered": 0, "ingested": 0, "verified": 0})
    ck("a scheduled capability emits a recurring SCHEDULE descriptor", rs["schedule"] and rs["schedule"]["recurring"] is True)

    print("\n" + ("PASS - check_capability_planner: open-ended capabilities are classified (iterative/scheduled), the hub "
                  "is resolved, the research catalog is descended, the plan strings multiple components, and execution "
                  "is a bounded loop (stops on no-new / cap) or emits a schedule. serves_truth=false." if not fails
                  else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(_self_test())
