#!/usr/bin/env python3
"""Required-functionality graph checker (owner-directed 2026-06-27).

Reads _repos/shared-backend-components/architecture/required_functionality.json — a graph where each REQUIREMENT node says
"surface/page X requires functionality Y" and carries a deterministic `check` EDGE to the code that
must satisfy it. This resolves every edge against the actual files (regex over the source, zero LLM):

  * a `satisfied` requirement is REGRESSION-GUARDED — if the code that satisfies it disappears (or a
    forbidden anti-pattern reappears), this gate FAILS. That is how "this page requires this
    functionality" stays true over time.
  * a `gap` requirement is the live remediation backlog — reported, not failing, until it is built;
    when its code lands the checker flags it as resolved so the manifest can be updated.

So we can talk about a page requiring functionality and CHECK it by looking at the (typed, eventually
pyprefix-conformant) structure. serves_truth=false.

CLI:  python3 _repos/shared-backend-components/scripts/check_required_functionality.py --self-test   |   --report
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
SPEC = _resource("architecture") / "required_functionality.json"


def _resolve_check_file(rel: str, root: Path) -> Path:
    """Resolve a requirement's check `file` to its real path. The live spec stores repo-root-relative NAMES
    for dirs that moved under `_repos/` post-migration (dist/, scripts/, architecture/, …); against the real
    repo those resolve through the universal `_resource` resolver (no root symlink needed). A hermetic
    self-test passes its OWN temp root with plain relative files, which resolve against that root."""
    return _resource(rel) if root == REPO else (root / rel)


def _present(check: dict, root: Path) -> bool | None:
    """Does the check's pattern(s) appear in its file? None if the file is missing."""
    f = _resolve_check_file(check["file"], root)
    if not f.exists():
        return None
    txt = f.read_text(encoding="utf-8", errors="replace")
    if check["type"] == "regex_in_file":
        return re.search(check["pattern"], txt) is not None
    if check["type"] == "all_regex_in_file":
        return all(re.search(p, txt) is not None for p in check["patterns"])
    raise ValueError(f"unknown check type {check['type']!r}")


def evaluate(spec: dict, root: Path) -> dict:
    """Return {satisfied:[], regressions:[], open_gaps:[], resolved_gaps:[], missing_file:[]}."""
    out = {"satisfied": [], "regressions": [], "open_gaps": [], "resolved_gaps": [], "missing_file": []}
    for r in spec.get("requirements", []):
        chk = r["check"]
        present = _present(chk, root)
        if present is None:
            out["missing_file"].append({"id": r["id"], "file": chk["file"]})
            continue
        want_present = chk.get("expect", "present") == "present"
        satisfied_now = present == want_present
        if r["status"] == "satisfied":
            (out["satisfied"] if satisfied_now else out["regressions"]).append(r["id"])
        else:  # gap
            (out["resolved_gaps"] if satisfied_now else out["open_gaps"]).append(r["id"])
    return out


def _self_test() -> int:
    import tempfile
    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    ck("spec parses + has requirements with id/surface/check/status",
       SPEC.exists() and all(all(k in r for k in ("id", "surface", "check", "status"))
                             for r in json.loads(SPEC.read_text())["requirements"]))

    real = evaluate(json.loads(SPEC.read_text(encoding="utf-8")), REPO)
    ck("no satisfied requirement has regressed", not real["regressions"], str(real["regressions"]))
    ck("no requirement points at a missing file", not real["missing_file"], str(real["missing_file"]))
    ck("the gap backlog is live (>=1 open gap from the wiring review)", len(real["open_gaps"]) >= 1, str(real))
    if real["resolved_gaps"]:
        print(f"  [note] gap(s) now appear satisfied — update status to 'satisfied' in the spec: {real['resolved_gaps']}")

    # hermetic: present/absent + satisfied/gap logic
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        (root / "ok.py").write_text("WIRED_MARKER = 1\n", encoding="utf-8")
        spec = {"requirements": [
            {"id": "a", "surface": "s", "check": {"type": "regex_in_file", "file": "ok.py", "pattern": "WIRED_MARKER", "expect": "present"}, "status": "satisfied"},
            {"id": "b", "surface": "s", "check": {"type": "regex_in_file", "file": "ok.py", "pattern": "FORBIDDEN", "expect": "absent"}, "status": "satisfied"},
            {"id": "c", "surface": "s", "check": {"type": "regex_in_file", "file": "ok.py", "pattern": "NOT_YET", "expect": "present"}, "status": "gap"},
            {"id": "d", "surface": "s", "check": {"type": "regex_in_file", "file": "ok.py", "pattern": "WIRED_MARKER", "expect": "present"}, "status": "gap"},
            {"id": "e", "surface": "s", "check": {"type": "regex_in_file", "file": "gone.py", "pattern": "x", "expect": "present"}, "status": "satisfied"},
        ]}
        res = evaluate(spec, root)
        ck("satisfied+present and satisfied+absent both pass", set(res["satisfied"]) == {"a", "b"})
        ck("open gap detected (pattern not yet present)", res["open_gaps"] == ["c"])
        ck("resolved gap detected (gap's code now present)", res["resolved_gaps"] == ["d"])
        ck("missing file flagged", [m["id"] for m in res["missing_file"]] == ["e"])
        # a regression: a satisfied requirement whose required marker vanished
        spec2 = {"requirements": [{"id": "r", "surface": "s", "check": {"type": "regex_in_file", "file": "ok.py", "pattern": "VANISHED", "expect": "present"}, "status": "satisfied"}]}
        ck("regression detected (satisfied requirement's code missing)", evaluate(spec2, root)["regressions"] == ["r"])

    if fails:
        print(f"\nFAIL - check_required_functionality: {len(fails)} failure(s): {fails}")
        return 1
    s = real
    print(f"\nPASS - check_required_functionality: {len(s['satisfied'])} satisfied (regression-guarded), "
          f"{len(s['open_gaps'])} open gap(s) tracked, {len(s['resolved_gaps'])} resolved; every requirement edge "
          f"resolves against the code. Open gaps: {s['open_gaps']}")
    return 0


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    if "--self-test" in argv or not argv:
        return _self_test()
    if "--report" in argv:
        res = evaluate(json.loads(SPEC.read_text(encoding="utf-8")), REPO)
        print(json.dumps(res, indent=1))
        return 1 if (res["regressions"] or res["missing_file"]) else 0
    print("usage: --self-test | --report")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
