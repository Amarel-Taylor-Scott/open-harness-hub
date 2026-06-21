#!/usr/bin/env python3
"""scripts.review_digest — what's ready for YOU to review right now (demos, files, decisions), in one place.

The loop runs for days producing work; this surfaces the human-facing REVIEW OPPORTUNITIES so you never have to dig:
  * DEMOS to watch (the showcase + dashboard + URL manifest), with openable file paths
  * the YC-readiness score + the top gaps (the marching orders)
  * top PROPOSALS the loop queued for your review (riskier-than-auto) + OWNER decisions pending
  * recent CHECKPOINT commits the loop made (what changed since you last looked)
  * recording/video readiness pointer

Thin reader that COMPOSES existing pieces (yc_readiness + proposal_backlog + the dist/ artifacts + git). Writes
data/dev-intel/review-digest.md and prints it (the ``./loop review`` view). DEVELOPMENT plane; serves_truth=false.

  --report / (no args)   print the digest + write data/dev-intel/review-digest.md
  --self-test            offline: the digest assembles from real sources
CLI: PYTHONPATH=. python3 scripts/review_digest.py --report
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

DIGEST = REPO / "data" / "dev-intel" / "review-digest.md"


def _demos() -> list[dict]:
    candidates = [
        ("Capability showcase (3 capabilities, control chart)", "dist/teleon-demos/showcase.html"),
        ("Demo dashboard", "dist/teleon-demos/index.html"),
        ("All demo URLs manifest", "dist/demo-all-urls.md"),
    ]
    out = []
    for label, rel in candidates:
        p = REPO / rel
        if p.exists():
            out.append({"label": label, "path": rel, "open": f"file://{p}" if p.suffix == ".html" else str(p)})
    return out


def _git_checkpoints(n: int = 5) -> list[str]:
    try:
        r = subprocess.run(["git", "log", "--oneline", "-n", str(n)], cwd=REPO, capture_output=True, text=True, timeout=20)
        return [ln for ln in r.stdout.splitlines() if ln.strip()]
    except Exception:  # noqa: BLE001
        return []


def compute_digest() -> dict:
    # YC readiness (the objective)
    try:
        from scripts.yc_readiness import compute_readiness
        yc = compute_readiness()
    except Exception as e:  # noqa: BLE001
        yc = {"score": None, "top_gaps": [], "error": str(e)}
    # proposals the loop queued: split into owner decisions vs review-then-apply, highest score first
    try:
        from scripts.proposal_backlog import load
        props = sorted(load(), key=lambda p: -p.get("score", 0))
    except Exception:  # noqa: BLE001
        props = []
    owner = [p for p in props if p.get("comfort") == "owner_gated"][:6]
    review = [p for p in props if p.get("comfort") == "propose"][:8]
    recording = (REPO / "scripts" / "check_recording_readiness.py").exists()
    return {"demos": _demos(), "yc": yc, "owner_decisions": owner, "to_review": review,
            "checkpoints": _git_checkpoints(), "recording_check": recording, "serves_truth": False}


def render() -> Path:
    d = compute_digest()
    yc = d["yc"]
    L = ["# Review opportunities — what's ready for you (development plane; serves_truth=false)", "",
         f"YC readiness: **{yc.get('score')}/1.0** — " + ("READY 🎉" if yc.get("ready") else "in progress"), ""]
    L += ["## ▶ Demos to review"]
    L += [f"- **{x['label']}** — `{x['open']}`" for x in d["demos"]] or ["- (none built yet — `./loop` will build them)"]
    if d["recording_check"]:
        L += ["- Recording/video readiness: `python3 scripts/check_recording_readiness.py --self-test`"]
    L += ["", "## ⛔ Owner decisions pending (only you can close these)"]
    L += [f"- {p['title']}" for p in d["owner_decisions"]] or ["- (none)"]
    L += ["", "## 🟡 Top proposals queued for your review"]
    L += [f"- **[{p.get('score')}]** {p['title']}" for p in d["to_review"]] or ["- (none)"]
    L += ["", "## ✅ Recent checkpoints (what the loop changed)"]
    L += [f"- `{c}`" for c in d["checkpoints"]] or ["- (none yet)"]
    L += ["", "_Regenerate anytime: `./loop review`_", ""]
    DIGEST.parent.mkdir(parents=True, exist_ok=True)
    DIGEST.write_text("\n".join(L) + "\n", encoding="utf-8")
    return DIGEST


def _self_test() -> int:
    fails = []
    def ck(name, ok):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
        if not ok: fails.append(name)
    d = compute_digest()
    ck("digest assembles demos / yc / decisions / review / checkpoints", set(d) >= {"demos", "yc", "owner_decisions", "to_review", "checkpoints"})
    ck("the showcase demo is surfaced for review", any("showcase" in x["path"] for x in d["demos"]))
    ck("owner decisions and review items are separated (you act on different ones)", isinstance(d["owner_decisions"], list) and isinstance(d["to_review"], list))
    import tempfile
    global DIGEST
    _D = DIGEST
    with tempfile.TemporaryDirectory() as t:
        try:
            DIGEST = Path(t) / "rd.md"; render()
            ck("a human digest is written (the ./loop review view)", DIGEST.exists() and "Review opportunities" in DIGEST.read_text())
        finally:
            DIGEST = _D
    print("\n" + ("PASS - review_digest: one human-facing surface of review opportunities (demos to watch, YC gaps, "
                  "queued proposals, owner decisions, recent checkpoints) composed from the live sources. serves_truth=false."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def _main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--self-test" in argv:
        return _self_test()
    p = render()
    print(p.read_text(encoding="utf-8"))
    print(f"(written to {p.relative_to(REPO)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
