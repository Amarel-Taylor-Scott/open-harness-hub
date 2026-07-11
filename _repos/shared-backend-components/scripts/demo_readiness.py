#!/usr/bin/env python3
"""scripts.demo_readiness — the SELF-DIRECTING objective: how close are we to a perfect YC-demo, and what's the top gap?

The improvement loop shouldn't just sweep generically — it should STEER toward a goal. This is that goal, made
measurable: a scorecard over the demo-able surfaces + WORKING backend components (real live receipts, green proof
gates, generated deploy configs). The loop's `demo` flywheel computes this each pass and FILES the open gaps into the
proposal backlog (highest-weight gaps first), so the loop directs itself at closing them. Functionality, not vanity
numbers — every dimension is a real probe (a file that exists, a gate that's green, a receipt that was actually
produced). DEVELOPMENT plane; serves_truth=false.

  --report      print the scorecard + top gaps (the `./loop readiness` view) and write data/dev-intel/demo-readiness.md
  --file-gaps   push the open gaps into the proposal backlog (the loop self-directs at them) + reprioritize
  --self-test   offline: probes run, score in [0,1], gaps route through the comfort gate
CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/demo_readiness.py --report
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

REPORT = _resource("data") / "dev-intel" / "demo-readiness.md"
FLYWHEEL_STATE = _resource("data") / "dev-intel" / "flywheel-state.json"


def _exists(*rel: str) -> bool:
    return all((_resource(r)).exists() for r in rel)


def _probe_surfaces() -> tuple[bool, str, str]:
    want = {"Teleon site": "_repos/teleon/frontend", "Baltor site": "_repos/baltor/frontend", "design bundle": "dist/sites/aidoneright-design"}
    missing = [name for name, p in want.items() if not (_resource(p)).exists()]
    ok = not missing
    return ok, (f"{len(want) - len(missing)}/{len(want)} demo-able surfaces present"), \
        ("" if ok else f"build/restore the missing surfaces: {', '.join(missing)}")


def _probe_dashboard() -> tuple[bool, str, str]:
    ok = _exists("dist/teleon-demos/index.html")
    return ok, ("demo dashboard built" if ok else "no demo dashboard"), \
        ("" if ok else "build the demo dashboard: python3 scripts/demo_dashboard.py")


def _probe_demo_urls() -> tuple[bool, str, str]:
    ok = _exists("dist/demo-all-urls.md")
    return ok, ("demo URL manifest present" if ok else "no demo URL manifest"), \
        ("" if ok else "aggregate the demo URLs: python3 scripts/cloudflare_handoff.py / build_demo_control_tower.py")


def _probe_live_proof() -> tuple[bool, str, str]:
    receipts = list((_resource("data") / "live-receipts").glob("*.json")) if (_resource("data") / "live-receipts").exists() else []
    receipts += list((_resource("site") / "baltor-demos").glob("*/context-receipt.json")) if (_resource("site") / "baltor-demos").exists() else []
    ok = bool(receipts)
    return ok, (f"{len(receipts)} live backend receipt(s) — a real run was executed" if ok else "no live receipt"), \
        ("" if ok else "run ONE capability end-to-end live + capture a receipt: python3 scripts/run_teleon_demos_live.py")


def _probe_backends() -> tuple[bool, str, str]:
    health = "unknown"
    if FLYWHEEL_STATE.exists():
        try:
            health = json.loads(FLYWHEEL_STATE.read_text(encoding="utf-8")).get("health", "unknown")
        except Exception:  # noqa: BLE001
            pass
    ok = health == "ok"
    return ok, f"core proof gates: {health}", \
        ("" if ok else "run the health flywheel until gates are green: ./loop run  (or scripts/flywheel_orchestrator.py --run)")


def _probe_deploy() -> tuple[bool, str, str]:
    fly = list((_resource("fly")).glob("*.fly.toml")) if (_resource("fly")).exists() else []
    tofu = _exists("deploy/tofu/cloudflare/main.tf")
    ok = bool(fly) and tofu
    parts = [f"{len(fly)} fly config(s)", "cloudflare tofu" if tofu else "NO cloudflare tofu"]
    return ok, "deploy configs: " + ", ".join(parts), \
        ("" if ok else "generate provider configs: python3 scripts/deploy/generate_provider_configs.py")


def _probe_go_live_seams() -> tuple[bool, str, str]:
    """Informational (low weight): a DEMO doesn't need full production go-live, but the gap is worth surfacing."""
    try:
        from scripts.check_teleon_go_live_readiness import readiness_report
        r = readiness_report()
        n = r.get("n_blocking_seams", 0)
        ok = n == 0
        top = (r.get("blocking_seams") or ["—"])[0]
        return ok, f"{n} blocking production seam(s) remain (demo≠go-live)", \
            ("" if ok else f"toward full go-live, next blocking seam: {top}")
    except Exception as e:  # noqa: BLE001
        return False, f"go-live readiness unavailable: {e}", "wire scripts/check_teleon_go_live_readiness.readiness_report"


#: key -> (weight, probe). Working backend components (live receipts + green gates) weigh most — that's the point of a demo.
DIMENSIONS = [
    ("live_backend_proof", 3, _probe_live_proof),
    ("backends_green", 3, _probe_backends),
    ("surfaces_present", 2, _probe_surfaces),
    ("demo_dashboard", 1, _probe_dashboard),
    ("demo_urls", 1, _probe_demo_urls),
    ("deploy_artifacts", 1, _probe_deploy),
    ("go_live_seams", 1, _probe_go_live_seams),
]


def compute_readiness() -> dict:
    dims, earned, total = [], 0.0, 0.0
    for key, weight, probe in DIMENSIONS:
        try:
            ok, detail, gap = probe()
        except Exception as e:  # noqa: BLE001 — a probe failure is a gap, never a crash
            ok, detail, gap = False, f"probe error: {e}", f"fix the {key} probe"
        total += weight
        earned += weight if ok else 0
        dims.append({"key": key, "weight": weight, "ok": ok, "detail": detail, "gap": gap})
    score = round(earned / total, 3) if total else 0.0
    top_gaps = [d for d in sorted(dims, key=lambda d: -d["weight"]) if not d["ok"]]
    return {"score": score, "ready": score >= 0.85, "dimensions": dims, "top_gaps": top_gaps, "serves_truth": False}


def file_gaps() -> int:
    """Push each open gap into the proposal backlog (the loop self-directs at them). Returns # gaps filed."""
    from scripts.proposal_backlog import Proposal, propose, prioritize, assess_comfort
    r = compute_readiness()
    n = 0
    for d in r["top_gaps"]:
        gap = d["gap"] or f"close the {d['key']} gap"
        a = assess_comfort(gap)
        value = max(1, min(5, d["weight"] + 2))      # working-backend gaps (weight 3) -> value 5
        before_pid = Proposal(title=f"[demo-gap:{d['key']}] {gap}").pid()
        propose(Proposal(title=f"[demo-gap:{d['key']}] {gap}", kind="plan", source="demo-readiness",
                         value=value, comfort=a["comfort"], risk=a["risk"], reversibility=a["reversibility"],
                         confidence=a["confidence"], rationale=f"YC-demo readiness {r['score']}: {d['detail']}",
                         next_steps=gap, refs=("demo-readiness", d["key"])))
        n += 1
    prioritize()
    return n


def render() -> Path:
    r = compute_readiness()
    bar = "█" * int(r["score"] * 20) + "░" * (20 - int(r["score"] * 20))
    lines = ["# YC-demo readiness (development plane; serves_truth=false)", "",
             f"**Score: {r['score']} / 1.0**  `{bar}`  →  {'READY' if r['ready'] else 'not yet ready'} (bar: 0.85)", "",
             "The loop steers toward this: the `demo` flywheel files the open gaps below into the proposal backlog.", "",
             "| dim | weight | status | detail |", "|---|---|---|---|"]
    for d in r["dimensions"]:
        lines.append(f"| {d['key']} | {d['weight']} | {'✅' if d['ok'] else '⬜'} | {d['detail']} |")
    if r["top_gaps"]:
        lines += ["", "## Top gaps (highest-weight first — the loop's marching orders)"]
        lines += [f"- **[{d['key']}]** {d['gap']}" for d in r["top_gaps"]]
    else:
        lines += ["", "All dimensions green — the demo is ready. 🎉"]
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
    ck("every dimension has weight/ok/detail/gap (real probes, not vanity numbers)",
       all(set(d) >= {"key", "weight", "ok", "detail", "gap"} for d in r["dimensions"]))
    ck("working-backend dims (live receipt + green gates) carry the most weight",
       max(DIMENSIONS, key=lambda x: x[1])[1] == 3 and {"live_backend_proof", "backends_green"} <= {k for k, w, _ in DIMENSIONS if w == 3})
    ck("top_gaps are the FAILING dims, highest-weight first (the loop's marching orders)",
       all(not d["ok"] for d in r["top_gaps"]) and r["top_gaps"] == sorted(r["top_gaps"], key=lambda d: -d["weight"]))
    ck("readiness has an honest go/no-go (ready only at a high bar)", r["ready"] == (r["score"] >= 0.85))
    # file_gaps routes through the comfort gate into a temp backlog
    import tempfile
    import scripts.proposal_backlog as pb
    _L, _P = pb.LEDGER, pb.PRIORITIZED
    with tempfile.TemporaryDirectory() as d:
        try:
            pb.LEDGER = Path(d) / "p.jsonl"; pb.PRIORITIZED = Path(d) / "pr.md"
            n = file_gaps()
            ck("open gaps are filed as governed proposals the loop self-directs at", n == len(r["top_gaps"]))
            ck("filed gaps are demo-tagged candidates (serves_truth=false)",
               (n == 0) or all(p["serves_truth"] is False and "demo-gap:" in p["title"] for p in pb.load()))
            ck("a prioritized backlog is (re)written", pb.PRIORITIZED.exists())
        finally:
            pb.LEDGER, pb.PRIORITIZED = _L, _P
    # render
    import tempfile as _t
    with _t.TemporaryDirectory() as d:
        global REPORT
        _R = REPORT
        try:
            REPORT = Path(d) / "r.md"
            render()
            ck("a human scorecard is written (the ./loop readiness view)", REPORT.exists() and "YC-demo readiness" in REPORT.read_text())
        finally:
            REPORT = _R
    print("\n" + ("PASS - demo_readiness: a SELF-DIRECTING scorecard over demo-able surfaces + WORKING backend components "
                  "(live receipts, green gates, generated deploy configs) — real probes, an honest go/no-go bar, and gaps "
                  "auto-filed into the comfort-gated backlog so the loop steers itself at them. serves_truth=false."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def _main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--self-test" in argv:
        return _self_test()
    if "--file-gaps" in argv:
        n = file_gaps()
        p = render()
        print(f"filed {n} demo gap(s) into the proposal backlog; scorecard -> {p.relative_to(REPO)}")
        return 0
    if "--report" in argv or not argv:
        r = compute_readiness()
        p = render()
        bar = "█" * int(r["score"] * 20) + "░" * (20 - int(r["score"] * 20))
        print(f"YC-demo readiness: {r['score']}/1.0  [{bar}]  {'READY' if r['ready'] else 'not yet'}")
        for d in r["dimensions"]:
            print(f"  {'✅' if d['ok'] else '⬜'} {d['key']:<20} (w{d['weight']}) — {d['detail']}")
        if r["top_gaps"]:
            print("\n  top gaps (the loop's marching orders):")
            for d in r["top_gaps"]:
                print(f"   → [{d['key']}] {d['gap']}")
        print(f"\n  scorecard: {p.relative_to(REPO)}")
        return 0
    print("usage: demo_readiness.py --report | --file-gaps | --self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
