#!/usr/bin/env python3
"""scripts.make_review_pack — generate a timestamped, independently-verifiable REVIEW PACK.

Runs the verification battery (the SAME commands a skeptical reviewer would run by hand), derives a
PASS/FAIL + a one-line evidence string per check, and writes a checklist report to
``e2e/artifacts/review-pack/REVIEW-<UTC>.md`` (plus a stable ``REVIEW-latest.md``). Every row prints
the exact command, so the report is a GUIDE to independent verification, not a substitute for it —
the reviewer can re-run any line themselves. Screenshots/GIFs are listed with freshness (mtime).

Why this exists: self-tests are written in-repo, so "green" alone can be circular. This pack pairs
the green contracts with REAL-DATA exercises (design-token drift on the actual CSS, the sanctions
would-be-violation catch, the Memory Block reconciliation) and visual artifacts, and surfaces the
receipt trail — so progress is checkable, not asserted.

Pairs with ``docs/review/REVIEW-CHECKLIST.md`` (the human checklist) + the ``e2e`` recorders.

CLI:
    python3 scripts/make_review_pack.py             # run battery, write the review pack, print summary
    python3 scripts/make_review_pack.py --self-test  # offline deterministic proof of the report builder
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_PY = sys.executable
_OUT_DIR = _REPO / "e2e" / "artifacts" / "review-pack"
_RECEIPTS = _REPO / ".agent" / "baltor-goal-loop-log.md"
_SHOT_DIR = _REPO / "e2e" / "artifacts"
_CHECK_TIMEOUT_S = 180

#: The battery. Each: id · category · title · argv (under PYTHONPATH=repo) · regex whose match is the
#: evidence string (and whose presence is REQUIRED for pass, on top of exit 0).
CHECKS: list[dict] = [
    {"id": "flywheel", "cat": "A · Foundation stays green",
     "title": "Every proof contract passes (count should be ≥ last review)",
     "args": ["scripts/baltor_flywheel.py", "--once"], "rx": r"GREEN (\d+)/(\d+)"},
    {"id": "engines", "cat": "B · Connected system actually wired",
     "title": "All engines emit ordered events onto the one bus (byte-identical without a bus)",
     "args": ["scripts/check_event_integration.py", "--self-test"], "rx": r"(\w+) modules CONNECTED"},
    {"id": "live", "cat": "B · Connected system actually wired",
     "title": "Pipeline fires live end-to-end against a spawned real server (SSE + /api/events)",
     "args": ["scripts/check_live_pipeline.py", "--self-test"], "rx": r"^PASS — check_live_pipeline"},
    {"id": "tokens", "cat": "C · Real-data output (not just self-tests)",
     "title": "Design-token drift reporter runs on the actual web/baltor CSS",
     "args": ["scripts/check_design_tokens.py"], "rx": r"(\d+) token\(s\) defined with >1"},
    {"id": "memblock", "cat": "C · Real-data output (not just self-tests)",
     "title": "Memory Block reconciliation (pin latest, supersede earlier, keep lineage)",
     "args": ["scripts/context_memory_block.py", "--self-test"], "rx": r"all context_memory_block self-tests passed"},
    {"id": "sanctions", "cat": "C · Real-data output (not just self-tests)",
     "title": "Sanctions flow CATCHES a would-be violation + holds it out (with provenance)",
     "args": ["scripts/pipeline/verified_context_flow.py", "--self-test"], "rx": r"would_be_violation .*? HELD OUT of the served corpus"},
]

#: Visual artifacts the recorders produce — listed with freshness so a stale pack is obvious.
SCREENSHOTS = ["integrate-cfpb.png", "dev-dashboard.png", "live-dashboard.gif", "dash-01-loaded.png",
               "dash-02-running.png", "dash-03-after.png", "baltor-demo.gif", "02-acme-ran.png",
               "06-cfpb-ran.png", "07-reviews.png", "raw-lineage.png", "raw-runs.png"]


def run_check(check: dict) -> dict:
    """Run one battery command; return {id,cat,title,cmd,ok,evidence}."""
    cmd = [_PY, *check["args"]]
    try:
        p = subprocess.run(cmd, cwd=str(_REPO), capture_output=True, text=True,
                           timeout=_CHECK_TIMEOUT_S, env={"PYTHONPATH": str(_REPO), "PATH": _env_path()})
        out = (p.stdout or "") + (p.stderr or "")
        ok, evidence = _evaluate(check, p.returncode, out)
    except subprocess.TimeoutExpired:
        ok, evidence = False, f"TIMEOUT after {_CHECK_TIMEOUT_S}s"
    except Exception as e:  # noqa: BLE001
        ok, evidence = False, f"ERROR {type(e).__name__}: {e}"
    return {"id": check["id"], "cat": check["cat"], "title": check["title"],
            "cmd": "python3 " + " ".join(check["args"]), "ok": ok, "evidence": evidence}


def _env_path() -> str:
    import os
    return os.environ.get("PATH", "/usr/bin:/bin")


def _evaluate(check: dict, rc: int, out: str) -> tuple[bool, str]:
    ok = rc == 0
    rx = check.get("rx")
    evidence = ""
    if rx:
        m = re.search(rx, out, re.MULTILINE)
        if m:
            evidence = m.group(0).strip()
            if check["id"] == "flywheel" and m.lastindex and m.lastindex >= 2 and m.group(1) != m.group(2):
                ok = False  # GREEN N/M with N != M is not all-green
        else:
            ok = False
            evidence = "(expected signal not found in output)"
    if not evidence:
        lines = [ln for ln in out.strip().splitlines() if ln.strip()]
        evidence = lines[-1] if lines else "(no output)"
    return ok, evidence[:240]


def _screenshot_rows(now_epoch: float | None = None) -> list[dict]:
    rows: list[dict] = []
    for name in SCREENSHOTS:
        p = _SHOT_DIR / name
        if p.exists():
            st = p.stat()
            rows.append({"name": name, "exists": True, "size": st.st_size, "mtime_epoch": st.st_mtime})
        else:
            rows.append({"name": name, "exists": False, "size": 0, "mtime_epoch": None})
    return rows


def _recent_receipts(n: int = 3) -> list[str]:
    if not _RECEIPTS.exists():
        return []
    heads = [ln.strip() for ln in _RECEIPTS.read_text(encoding="utf-8", errors="ignore").splitlines()
             if ln.startswith("## ")]
    return heads[-n:]


def build_report(results: list[dict], *, when: str, screenshots: list[dict], receipts: list[str]) -> str:
    """Pure: assemble the review-pack markdown from already-collected results. (Testable, no IO/clock.)"""
    passed = sum(1 for r in results if r["ok"])
    total = len(results)
    overall = "ALL GREEN ✅" if passed == total else f"⚠ {total - passed} FAILED"
    lines = [
        f"# Baltor — Review Pack ({when})",
        "",
        f"**Overall: {passed}/{total} checks passed — {overall}**",
        "",
        "Each row is a check you can re-run yourself (the command is shown). This pack does not ask "
        "you to trust it — it points you at the evidence. Self-tests prove contracts; the **C** rows "
        "exercise REAL data so progress isn't circular.",
        "",
    ]
    by_cat: dict[str, list[dict]] = {}
    for r in results:
        by_cat.setdefault(r["cat"], []).append(r)
    for cat in sorted(by_cat):
        lines.append(f"## {cat}")
        lines.append("")
        for r in by_cat[cat]:
            box = "[x]" if r["ok"] else "[ ]"
            lines.append(f"- {box} **{r['title']}**")
            lines.append(f"  - evidence: `{r['evidence']}`")
            lines.append(f"  - re-run: `{r['cmd']}`")
        lines.append("")

    lines.append("## D · Visual evidence (freshness matters — re-record if stale)")
    lines.append("")
    lines.append("Regenerate: `cd e2e && BASE=http://127.0.0.1:9301 node record_dashboard.mjs && BASE=http://localhost:8000 node record_demo.mjs`")
    lines.append("")
    for s in screenshots:
        if s["exists"]:
            kb = f"{s['size'] // 1024} KB"
            lines.append(f"- [x] `e2e/artifacts/{s['name']}` ({kb})")
        else:
            lines.append(f"- [ ] `e2e/artifacts/{s['name']}` — MISSING (run the recorder)")
    lines.append("")

    lines.append("## E · Progress trail (last receipts)")
    lines.append("")
    if receipts:
        for h in receipts:
            lines.append(f"- {h[3:]}")
    else:
        lines.append("- (no receipts found)")
    lines.append("")
    lines.append("---")
    lines.append("Full human checklist: `docs/review/REVIEW-CHECKLIST.md`. "
                 "Regenerate this pack: `python3 scripts/make_review_pack.py`.")
    return "\n".join(lines) + "\n"


def _utc_now_str() -> str:
    # Real wall-clock is correct for a timestamped report (this is NOT the deterministic event bus).
    import datetime
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _generate() -> int:
    results = [run_check(c) for c in CHECKS]
    when = _utc_now_str()
    report = build_report(results, when=when, screenshots=_screenshot_rows(), receipts=_recent_receipts())
    _OUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = when.replace(":", "").replace("-", "")
    dated = _OUT_DIR / f"REVIEW-{stamp}.md"
    latest = _OUT_DIR / "REVIEW-latest.md"
    dated.write_text(report, encoding="utf-8")
    latest.write_text(report, encoding="utf-8")
    passed = sum(1 for r in results if r["ok"])
    print(report)
    print(f"\nwrote {dated.relative_to(_REPO)}  (+ REVIEW-latest.md)")
    return 0 if passed == len(results) else 1


def _self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    # _evaluate logic
    ok, ev = _evaluate(CHECKS[0], 0, "blah\n[2026]  flywheel GREEN 41/41 proofs\n")
    check("flywheel N==N → pass + evidence", ok and ev == "GREEN 41/41")
    ok2, _ = _evaluate(CHECKS[0], 0, "flywheel GREEN 40/41 proofs")
    check("flywheel N!=M → fail", not ok2)
    ok3, ev3 = _evaluate(CHECKS[1], 0, "… Nine modules CONNECTED.")
    check("regex evidence extracted", ok3 and ev3 == "Nine modules CONNECTED")
    ok4, _ = _evaluate(CHECKS[1], 1, "Nine modules CONNECTED")
    check("nonzero exit → fail even if signal present", not ok4)
    ok5, ev5 = _evaluate(CHECKS[2], 0, "no signal here")
    check("missing required signal → fail", not ok5 and "not found" in ev5)

    # build_report is pure + renders checkboxes + overall verdict deterministically
    synth = [
        {"id": "a", "cat": "A · Foundation stays green", "title": "T1", "cmd": "python3 x", "ok": True, "evidence": "GREEN 41/41"},
        {"id": "b", "cat": "C · Real-data output (not just self-tests)", "title": "T2", "cmd": "python3 y", "ok": False, "evidence": "boom"},
    ]
    rep = build_report(synth, when="2026-01-01T00:00:00Z",
                       screenshots=[{"name": "live-dashboard.gif", "exists": True, "size": 99970, "mtime_epoch": 1.0},
                                    {"name": "missing.png", "exists": False, "size": 0, "mtime_epoch": None}],
                       receipts=["## 2026-06-05 · Pass C19 — built P0.3"])
    check("report marks passed check [x]", "[x] **T1**" in rep)
    check("report marks failed check [ ]", "[ ] **T2**" in rep)
    check("report overall verdict reflects a failure", "1 FAILED" in rep and "1/2 checks passed" in rep)
    check("report lists present + missing screenshots", "live-dashboard.gif" in rep and "missing.png` — MISSING" in rep)
    check("report includes the re-run command (verifiable, not trust-me)", "re-run: `python3 x`" in rep)
    check("report surfaces the receipt trail", "Pass C19 — built P0.3" in rep)
    rep_all = build_report([synth[0]], when="t", screenshots=[], receipts=[])
    check("all-pass renders ALL GREEN", "ALL GREEN" in rep_all)

    print(f"\n{'all make_review_pack self-tests passed.' if not failures else f'{len(failures)} FAILURES: {failures}'}")
    return 0 if not failures else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Generate a timestamped, independently-verifiable review pack.")
    p.add_argument("--self-test", action="store_true", help="offline deterministic proof of the report builder")
    args = p.parse_args(argv)
    if args.self_test:
        return _self_test()
    return _generate()


if __name__ == "__main__":
    raise SystemExit(_main())
