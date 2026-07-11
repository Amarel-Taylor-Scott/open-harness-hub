#!/usr/bin/env python3
"""scripts.check_demo_console_links — guard the demo console's discoverability + no dangling links.

The "view everything" surfaces (demo-console.html, reviews.html) are only useful if they exist, are
reachable from the site nav, and their data files are present. This proof asserts exactly that — so a
rename or a deleted data file fails fast instead of shipping a dead link.

CLI:
    python3 _repos/shared-backend-components/scripts/check_demo_console_links.py --self-test
    python3 _repos/shared-backend-components/scripts/check_demo_console_links.py            # report; exit 1 on any dangling link
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource  # noqa: E402

import argparse
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
_WEB = _resource("web/baltor")

#: files the console + queue need to exist (pages + their data).
REQUIRED_FILES = (
    "demo-console.html", "reviews.html", "dashboard.html", "app.js", "index.html",
    "demo-run.json", "demo-run.cfpb.json", "review-queue.json", "version-timeline.json",
    "consume.html",
)
#: (file that must reference, substring it must contain) — the no-dangling-link checks.
REFERENCES = (
    ("app.js", "demo-console.html"),            # nav links the console
    ("app.js", "reviews.html"),                 # nav links the review queue
    ("demo-console.html", "demo-run.json"),     # console loads the acme run
    ("demo-console.html", "demo-run.cfpb.json"),# console loads the cfpb run
    ("reviews.html", "review-queue.json"),      # queue loads its data
    ("dashboard.html", "/api/events/stream"),   # live dashboard subscribes to the SSE stream
    ("dashboard.html", "context_lift.calculated"),  # the measured-lift readout is wired
    ("dashboard.html", "/api/context/audit"),   # the Context Auditor → Optimizer panel is backed by the route
    ("consume.html", "/api/context/serve"),     # the consume page fetches the served ContextResponse
    ("consume.html", "/api/runtime/sections"),  # the consume page fetches the maturity scoreboard
)


def check() -> list[str]:
    problems: list[str] = []
    for rel in REQUIRED_FILES:
        if not (_WEB / rel).exists():
            problems.append(f"missing file: _repos/baltor/frontend/{rel}")
    for src, needle in REFERENCES:
        p = _WEB / src
        if not p.exists():
            problems.append(f"missing referrer: _repos/baltor/frontend/{src}")
            continue
        if needle not in p.read_text(encoding="utf-8"):
            problems.append(f"_repos/baltor/frontend/{src} does not reference {needle!r} (dangling/unwired)")
    return problems


def _self_test() -> int:
    failures: list[str] = []

    def chk(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    problems = check()
    chk("all required demo files exist", not any(p.startswith("missing file") for p in problems),
        "; ".join(p for p in problems if p.startswith("missing file"))[:160])
    chk("site nav links the console + review queue (reachable from homepage)",
        not any("app.js" in p for p in problems), "; ".join(p for p in problems if "app.js" in p))
    chk("no dangling data-file links in the console / queue", not problems, "; ".join(problems[:3]))
    chk("operator guide exists", (_resource("docs/deployment/demo-console.md")).exists())
    chk("repo-root quickstart exists", (_resource("docs/baltor-full-app-quickstart.md")).exists())
    chk("operator guide links the quickstart (not orphaned)",
        "baltor-full-app-quickstart.md" in (_resource("docs/deployment/demo-console.md")).read_text(encoding="utf-8"))
    # deterministic: same result twice
    chk("link check is deterministic", check() == problems)

    print(f"\n{'all check_demo_console_links self-tests passed.' if not failures else f'{len(failures)} FAILURES: {failures}'}")
    return 0 if not failures else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Guard the demo console's links + data files (no dangling links).")
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args(argv)
    if args.self_test:
        return _self_test()
    problems = check()
    if problems:
        print("FAIL — dangling links / missing files:")
        print("\n".join(f"  - {p}" for p in problems))
        return 1
    print(f"OK — {len(REQUIRED_FILES)} demo files present; {len(REFERENCES)} links wired.")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
