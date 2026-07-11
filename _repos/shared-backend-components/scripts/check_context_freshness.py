#!/usr/bin/env python3
"""scripts.check_context_freshness — detect ROTTEN context so the written word stays honest over time (owner 2026-06-25).

Two rots that accumulate silently:
  1. BROKEN REFERENCES — a doc points at `scripts/x.py` / `docs/y.md` / `architecture/z.json` that no longer exists
     (moved, renamed, archived). Dead references are how docs go stale + mislead the next agent.
  2. SUPERSEDED-NOT-ARCHIVED — a doc carries a superseded/deprecated header marker but still lives in the active tree
     (should be moved to archive/legacy via archive_legacy_docs.py).

  --self-test   detector works + the CANONICAL docs (CLAUDE.md, AGENTS.md, _repos/shared-backend-components/docs/NORTHSTAR.md) have 0 broken refs (live guard)
  --check       report broken refs + un-archived superseded across _repos/shared-backend-components/docs/
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource  # noqa: E402

import re
import sys
from pathlib import Path

REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
CANONICAL = ("CLAUDE.md", "AGENTS.md", "docs/NORTHSTAR.md", "docs/BIBLE.md", "docs/DESIGN-BIBLE.md")
# captures leading ../ or ./ so relative markdown links resolve correctly (not just repo-root code paths)
REF = re.compile(r"((?:\.\.?/)*(?:archive|scripts|src|docs|architecture|web|vocabularies|schemas)/[A-Za-z0-9_./-]+\.(?:py|md|json|jsx|js|css|html))(?![A-Za-z])")
SUPERSEDED = re.compile(r"superseded[- ]by|^>?\s*deprecated\b|do[- ]not[- ]use", re.I | re.M)


def _md_files(root: str = "docs") -> list[Path]:
    base = _resource(root)
    return [f for f in base.rglob("*.md") if "archive/" not in str(f)] if base.is_dir() else []


def broken_refs(files: list[Path]) -> list[str]:
    out: list[str] = []
    for f in files:
        try:
            t = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        seen: set[str] = set()
        for m in REF.finditer(t):
            ref = m.group(1)
            # skip: dup, glob/template placeholders, dir refs, ellipsis-abbreviated (`docs/…`), and single-letter
            # convention placeholders (`scripts/x.py`, `docs/y.md`, `architecture/z.json`) — path-convention prose, not real refs.
            if (ref in seen or any(c in ref for c in "*{}<>…") or ref.endswith("/")
                    or Path(ref).stem in {"x", "y", "z", "w", "n"}):
                continue
            seen.add(ref)
            # valid if it resolves repo-root-relative (code paths in backticks) OR relative to the doc's dir (../ links)
            if (_resource(ref)).exists() or (f.parent / ref).resolve().exists():
                continue
            out.append(f"{f.relative_to(REPO)} → missing {ref}")
    return out


def unarchived_superseded() -> list[str]:
    out: list[str] = []
    for f in _md_files():
        try:
            head = f.read_text(encoding="utf-8", errors="replace")[:800]
        except OSError:
            continue
        if SUPERSEDED.search(head):
            out.append(str(f.relative_to(REPO)))
    return out


def check() -> int:
    canon = broken_refs([_resource(c) for c in CANONICAL if (_resource(c)).exists()])
    # goal/plan docs legitimately forward-reference checks/files that are yet to be built — not rot
    report_files = [f for f in _md_files() if "/goals/" not in str(f)]
    allrefs = broken_refs(report_files)
    for b in canon:
        print(f"  [BROKEN · canonical] {b}")
    shown = [b for b in allrefs if b not in canon][:30]
    for b in shown:
        print(f"  [broken ref] {b}")
    if len(allrefs) - len(canon) > 30:
        print(f"  … +{len(allrefs) - len(canon) - 30} more broken refs")
    print(f"context freshness: {len(canon)} canonical-broken · {len(allrefs)} total broken refs "
          f"(for superseded docs run: scripts/archive_legacy_docs.py --scan)")
    return 1 if canon else 0


def self_test() -> int:
    assert REF.search("see `scripts/foo.py`") and not REF.search("just prose with no path")
    assert REF.search("[x](../architecture/y.md)").group(1) == "../architecture/y.md", "captures relative links"
    assert isinstance(broken_refs(_md_files()[:3]), list) and isinstance(unarchived_superseded(), list)
    canon = broken_refs([_resource(c) for c in CANONICAL if (_resource(c)).exists()])
    assert canon == [], f"canonical docs reference missing files (fix or update): {canon[:6]}"   # live guard
    print("check_context_freshness self-test: OK (detector + canonical docs have 0 broken refs)")
    return 0


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        return self_test()
    if "--check" in argv:
        return check()
    print("usage: check_context_freshness.py --self-test | --check")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
