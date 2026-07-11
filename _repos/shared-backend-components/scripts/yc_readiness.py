#!/usr/bin/env python3
"""scripts.yc_readiness — the SINGLE self-directing objective: how YC-ready is the whole portfolio, what's the top gap?

Generalizes demo_readiness from "is the demo ready" to "is the YC APPLICATION ready", grounded in YC's actual 2026
criteria and Summer-2026 Requests-for-Startups (researched 2026-06-21):

  * clarity — describe it in one matter-of-fact sentence ("we make X — like A, but B")   [PG: every unnecessary word subtracts]
  * proof of progress / traction — a REAL working demo + a live receipt beat any narrative
  * founder-market fit — why you know this problem better than anyone + the hardest thing you've built
  * who DESPERATELY needs this — a named ICP + acute pain (YC now asks this, not "how will you make money")
  * NOT a GPT wrapper — "AI is infrastructure, not a feature"; real layering, not a prompt around an API
  * why-now / earned insight, competition + moat, the ask/deck
  * RFS alignment — YC S26 wants #4 "Software for Agents" + #5 "the AI OS for companies" (Teleon + Baltor fit directly)

Each dimension is a REAL probe over the repo (reusing demo_readiness for the proof/demo/backend dims). Open gaps are
filed into the comfort-gated proposal backlog so `./loop` steers the WHOLE system toward YC preparedness, not just the
demo. Functionality over vanity; serves_truth=false. DEVELOPMENT plane.

  --report      print the YC-readiness scorecard + top gaps (the `./loop yc` view) -> data/dev-intel/yc-readiness.md
  --file-gaps   push the open gaps into the proposal backlog (the loop self-directs at them) + reprioritize
  --self-test   offline: probes run, score in [0,1], gaps route through the comfort gate
CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/yc_readiness.py --report
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

REPORT = _resource("data") / "dev-intel" / "yc-readiness.md"
YC_PREP_DOC = "docs/strategy/yc-readiness-and-prep-2026.md"


def _glob(*pats: str) -> list[str]:
    hits: list[str] = []
    for p in pats:
        hits += [str(x.relative_to(REPO)) for x in REPO.glob(p)]
    return hits


def _exists(*rel: str) -> bool:
    return any((_resource(r)).exists() for r in rel)


def _D(key, weight, ok, detail, gap):
    return {"key": key, "weight": weight, "ok": bool(ok), "detail": detail, "gap": ("" if ok else gap)}


def compute_readiness() -> dict:
    """The YC-readiness scorecard. Reuses demo_readiness for the proof/demo/backend dims; adds the narrative dims YC
    actually grades. Every dim is a real probe (a receipt that exists, a doc that exists, a gate that's green)."""
    try:
        from scripts.demo_readiness import compute_readiness as _demo
        drd = {x["key"]: x for x in _demo()["dimensions"]}
    except Exception:  # noqa: BLE001 — degrade gracefully; demo dims become gaps
        drd = {}
    def dr(k, default_gap):
        d = drd.get(k)
        return (d["ok"], d["detail"], d["gap"]) if d else (False, f"{k} unavailable", default_gap)

    proof_ok, proof_det, proof_gap = dr("live_backend_proof", "run ONE capability live + capture a receipt")
    back_ok, back_det, back_gap = dr("backends_green", "run the health flywheel until gates are green: ./loop run")
    showcase = _exists("dist/teleon-demos/showcase.html")
    deck = _exists("architecture/teleon_pitch_deck.json")
    pitch = bool(_glob("docs/strategy/*business-plan-and-pitch*.md", "docs/strategy/*master-current-state*.md"))
    appdraft = bool(_glob("docs/strategy/yc-application*.md"))
    landscape = bool(_glob("docs/strategy/*competitive-landscape*.md", "docs/strategy/*context-landscape*.md"))
    law = _exists("architecture/portfolio_dependency_law.json")
    fmf = bool(_glob("docs/strategy/*founder*.md", "docs/strategy/*team*.md", "docs/strategy/*founder-market*.md"))
    whynow = _exists("docs/strategy/north-stars.md") or pitch
    rfs = _exists(YC_PREP_DOC)
    who = bool(_glob("docs/strategy/*first-live-capability*.md"))
    partner = bool(_glob("docs/strategy/*design-partner*.md", "docs/strategy/*pilot*.md", "docs/strategy/*traction*.md"))
    decisions = bool(_glob("docs/strategy/*decisions-locked*.md", "docs/strategy/*ratified*.md"))

    dims = [
        _D("proof_point", 3, proof_ok, proof_det, proof_gap),
        _D("working_demo", 3, showcase, ("clean showcase built" if showcase else "no clean showcase page"),
           "build the clean showcase: python3 scripts/build_teleon_demo_showcase.py"),
        _D("traction_design_partner", 3, partner, ("design-partner / pilot artifact present" if partner else "no signed design partner / paid pilot"),
           "secure 1 design partner + a paid pilot that EXPORTS a package consumed by their own agent/RAG, with a before/after report (the 90-day bottleneck) — owner GTM"),
        _D("backends_green", 2, back_ok, back_det, back_gap),
        _D("founder_market_fit", 2, fmf, ("founder-market-fit doc present" if fmf else "founder/team story UNFILLED (the critical blocker)"),
           "fill the founder/team story — why you know this better than anyone + the hardest thing you've built — owner"),
        _D("who_needs_it", 2, who, ("named ICP + acute pain (sanctions/compliance wedge)" if who else "no named ICP"),
           "name who DESPERATELY needs this + the acute pain (a first-live-capability / ICP doc)"),
        _D("not_a_wrapper", 2, law, ("real infra: enforced dependency law Baltor→Teleon→OHH" if law else "no infra-layering proof"),
           "show this is INFRASTRUCTURE, not a GPT wrapper (dependency law + plane separation)"),
        _D("clarity_one_liner", 2, (pitch or appdraft), ("pitch / one-liner artifact present" if (pitch or appdraft) else "no one-sentence pitch"),
           "lock ONE one-sentence pitch ('we make X — like A, but B'); 5+ compete across docs today — owner"),
        _D("competition_moat", 1, landscape, ("competitive landscape mapped" if landscape else "no landscape doc"),
           "map the competition + the moat (governance / verification / receipts)"),
        _D("why_now_insight", 1, whynow, ("why-now / earned-insight present (EU AI Act forcing function)" if whynow else "no why-now"),
           "articulate the earned insight + 'why now' (EU AI Act Aug 2 2026 enforcement)"),
        _D("ask_deck", 1, deck, ("pitch deck present" if deck else "no pitch deck"),
           "finish the pitch deck + lock the ASK (raise size / use-of-funds) — owner"),
        _D("rfs_alignment", 1, rfs, ("YC RFS mapping present" if rfs else "no RFS mapping"),
           f"map to YC S26 RFS #4 (Software for Agents) + #5 (AI OS for companies) in {YC_PREP_DOC}"),
        _D("decisions_locked", 1, decisions, ("owner decisions ratified" if decisions else "raise/pricing/one-liner not ratified"),
           "owner: ratify raise size + pricing + lock the one-liner (owner-gated decisions)"),
    ]
    earned = sum(d["weight"] for d in dims if d["ok"])
    total = sum(d["weight"] for d in dims)
    score = round(earned / total, 3) if total else 0.0
    top_gaps = [d for d in sorted(dims, key=lambda d: -d["weight"]) if not d["ok"]]
    return {"score": score, "ready": score >= 0.85, "dimensions": dims, "top_gaps": top_gaps, "serves_truth": False}


def file_gaps() -> int:
    """Push each open YC gap into the proposal backlog (highest weight -> highest value). Returns # gaps filed."""
    from scripts.proposal_backlog import Proposal, propose, prioritize, assess_comfort
    r = compute_readiness()
    n = 0
    for d in r["top_gaps"]:
        gap = d["gap"] or f"close the {d['key']} gap"
        a = assess_comfort(gap)
        value = max(1, min(5, d["weight"] + 2))
        propose(Proposal(title=f"[yc-gap:{d['key']}] {gap}", kind="plan", source="yc-readiness",
                         value=value, comfort=a["comfort"], risk=a["risk"], reversibility=a["reversibility"],
                         confidence=a["confidence"], rationale=f"YC readiness {r['score']}: {d['detail']}",
                         next_steps=gap, refs=("yc-readiness", d["key"])))
        n += 1
    prioritize()
    return n


def render() -> Path:
    r = compute_readiness()
    bar = "█" * int(r["score"] * 20) + "░" * (20 - int(r["score"] * 20))
    lines = ["# YC readiness (development plane; serves_truth=false)", "",
             f"**Score: {r['score']} / 1.0**  `{bar}`  →  {'YC-READY' if r['ready'] else 'not yet ready'} (bar: 0.85)", "",
             "The single self-directing objective: `./loop`'s `yc` flywheel files the open gaps below into the proposal "
             "backlog and the loop steers at them. Grounded in YC's 2026 criteria + S26 Requests-for-Startups.", "",
             "| dimension | weight | status | detail |", "|---|---|---|---|"]
    for d in r["dimensions"]:
        lines.append(f"| {d['key']} | {d['weight']} | {'✅' if d['ok'] else '⬜'} | {d['detail']} |")
    if r["top_gaps"]:
        lines += ["", "## Top gaps (highest-weight first — the loop's marching orders)"]
        lines += [f"- **[{d['key']}]** {d['gap']}" for d in r["top_gaps"]]
    else:
        lines += ["", "All dimensions green — the application is ready to submit. 🎉"]
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return REPORT


def _self_test() -> int:
    fails = []
    def ck(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': '+detail) if detail and not ok else ''}")
        if not ok: fails.append(name)
    r = compute_readiness()
    ck("score is a fraction in [0,1]", isinstance(r["score"], float) and 0.0 <= r["score"] <= 1.0, str(r["score"]))
    keys = {d["key"] for d in r["dimensions"]}
    ck("covers YC's real criteria (clarity/proof/traction/FMF/who-needs-it/not-a-wrapper/why-now/competition/ask/RFS/decisions)",
       {"clarity_one_liner", "proof_point", "traction_design_partner", "founder_market_fit", "who_needs_it",
        "not_a_wrapper", "why_now_insight", "competition_moat", "ask_deck", "rfs_alignment", "working_demo",
        "backends_green", "decisions_locked"} <= keys)
    ck("proof + working demo carry the most weight (proof of progress beats narrative)",
       max(d["weight"] for d in r["dimensions"]) == 3 and {"proof_point", "working_demo"} <= {d["key"] for d in r["dimensions"] if d["weight"] == 3})
    ck("top_gaps are the failing dims, highest-weight first", all(not d["ok"] for d in r["top_gaps"]) and r["top_gaps"] == sorted(r["top_gaps"], key=lambda d: -d["weight"]))
    ck("honest go/no-go at a high bar", r["ready"] == (r["score"] >= 0.85))
    import tempfile
    import scripts.proposal_backlog as pb
    _L, _P = pb.LEDGER, pb.PRIORITIZED
    with tempfile.TemporaryDirectory() as d:
        try:
            pb.LEDGER = Path(d) / "p.jsonl"; pb.PRIORITIZED = Path(d) / "pr.md"
            n = file_gaps()
            ck("open YC gaps are filed as governed proposals the loop self-directs at", n == len(r["top_gaps"]))
            ck("filed gaps are yc-tagged candidates (serves_truth=false)",
               (n == 0) or all(p["serves_truth"] is False and "yc-gap:" in p["title"] for p in pb.load()))
        finally:
            pb.LEDGER, pb.PRIORITIZED = _L, _P
    with tempfile.TemporaryDirectory() as d:
        global REPORT
        _R = REPORT
        try:
            REPORT = Path(d) / "r.md"; render()
            ck("a human scorecard is written (the ./loop yc view)", REPORT.exists() and "YC readiness" in REPORT.read_text())
        finally:
            REPORT = _R
    print("\n" + ("PASS - yc_readiness: ONE self-directing objective scoring the whole portfolio against YC's real 2026 "
                  "criteria + S26 RFS (clarity, proof of progress, founder-market fit, who-needs-it, not-a-wrapper, "
                  "why-now, competition, ask, RFS-fit) — real probes, gaps auto-filed into the comfort-gated backlog so "
                  "`./loop` drives YC preparedness. serves_truth=false."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def _main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--self-test" in argv:
        return _self_test()
    if "--file-gaps" in argv:
        n = file_gaps(); p = render()
        print(f"filed {n} YC gap(s) into the proposal backlog; scorecard -> {p.relative_to(REPO)}")
        return 0
    if "--report" in argv or not argv:
        r = compute_readiness(); p = render()
        bar = "█" * int(r["score"] * 20) + "░" * (20 - int(r["score"] * 20))
        print(f"YC readiness: {r['score']}/1.0  [{bar}]  {'YC-READY' if r['ready'] else 'not yet'}")
        for d in r["dimensions"]:
            print(f"  {'✅' if d['ok'] else '⬜'} {d['key']:<20} (w{d['weight']}) — {d['detail']}")
        if r["top_gaps"]:
            print("\n  top gaps (the loop's marching orders):")
            for d in r["top_gaps"]:
                print(f"   → [{d['key']}] {d['gap']}")
        print(f"\n  scorecard: {p.relative_to(REPO)}")
        return 0
    print("usage: yc_readiness.py --report | --file-gaps | --self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
