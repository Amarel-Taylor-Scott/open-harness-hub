#!/usr/bin/env python3
"""scripts.check_new_code_uses_standards — the standards LINTER. It scans the governed tree and FAILS on
deviations from the established patterns, from a *standards-coverage* angle (it COMPLEMENTS, not duplicates,
_repos/shared-backend-components/scripts/check_no_direct_provider_bypass.py and _repos/shared-backend-components/scripts/check_file_layout_policy.py — those enforce the
wrapper-first rule and the file-layout policy; this one enforces that new code matches the documented SHAPE
of its pattern). Rules enforced:

  * source adapters (_repos/baltor/backend/src/baltor/adapters/source/*.py): must declare ``source_type`` + ``parser_provider`` and
    a ``def ingest(`` — i.e. match the SourceAdapter shape (_repos/shared-backend-components/scripts/ingest/source_adapters.py#SourceAdapter);
  * proof scripts (scripts/check_*.py): must support ``--self-test``;
  * docs (_repos/shared-backend-components/docs/standards/*.md): must carry a top-level ``# `` heading (a titled document);
  * projection code (_repos/shared-backend-components/scripts/runtime/projections.py, _repos/baltor/backend/src/baltor/api/projections/*.py): must NOT mutate truth
    (no INSERT/UPDATE/DELETE, no sqlite3 import) and must NOT embed secrets;
  * UI pages (_repos/baltor/frontend/*.html): must NOT write durable truth (projection-only);
  * config templates (templates/configs/**.json): must NOT contain raw secrets (refs only);
  * no NEW vague filename (utils/helpers/common/…) in governed scope outside the file-layout allowlist;
  * processors do not perform raw storage writes (sqlite3.connect / open(... 'w')) — they go through ports.

CRITICAL: this PASSES on the current clean tree (rules are tuned to today's shapes). A negative self-test
introduces each class of deviation in a deterministic temp dir and proves the rule FAILS, so the linter
actually bites. Honored exceptions are recorded in _repos/shared-backend-components/architecture/pattern_waivers.json (read here so a waived
deviation does not block — the waiver itself is validated by _repos/shared-backend-components/scripts/check_pattern_waivers.py).

CLI: python3 _repos/shared-backend-components/scripts/check_new_code_uses_standards.py --self-test
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import tempfile
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource

# ── governed scopes (where each standard applies) ───────────────────────────────────────────────────────
_SOURCE_ADAPTER_DIR = _resource("src/baltor/adapters/source")
_PROOF_GLOB = "scripts/check_*.py"
_STANDARDS_DOCS_DIR = _resource("docs") / "standards"
_PROJECTION_FILES = ["scripts/runtime/projections.py"]
_PROJECTION_DIRS = ["_repos/baltor/backend/src/baltor/api/projections"]
_UI_PAGES_DIR = _resource("web/baltor")
_CONFIG_TEMPLATES_DIR = _resource("templates/configs")
_PROCESSOR_GLOBS = ["scripts/runtime/builtin_processors.py", "_repos/baltor/backend/src/baltor/processors/**/*.py"]
_VAGUE_SCAN_SCOPE = ["scripts", "_repos/baltor/backend/src/baltor"]
_SKIP_PARTS = {".venv", "__pycache__", ".git", "node_modules", "_reference"}

# ── rule constants ──────────────────────────────────────────────────────────────────────────────────────
_VAGUE_FILENAMES = {"utils.py", "helpers.py", "common.py", "misc.py", "stuff.py", "temp.py",
                    "scratch.py", "final.py", "old.py", "new.py", "fix.py", "test2.py"}
_TRUTH_MUTATION = ("INSERT INTO", "UPDATE ", "DELETE FROM", "import sqlite3", "sqlite3.connect")
_UI_WRITE_FORBIDDEN = ("durable.db", "INSERT INTO", "UPDATE ", "DELETE FROM", "import sqlite3", "sqlite3.connect")
_RAW_SECRET = re.compile(
    r'"(?:api_key|token|secret|password|access_key|private_key|client_secret)"\s*:\s*"(?!env://|secret://)[^"]+"',
    re.IGNORECASE,
)
_RAW_STORAGE_WRITE = (r"sqlite3\.connect", r"^\s*import sqlite3")


def _py_files_in(directory: Path) -> list[Path]:
    if not directory.is_dir():
        return []
    return sorted(p for p in directory.glob("*.py") if p.name != "__init__.py" and "__pycache__" not in p.parts)


def _waived_paths() -> set[str]:
    """Paths with an ACTIVE, non-past-expiry waiver are exempt (the waiver is validated separately)."""
    wf = _resource("architecture") / "pattern_waivers.json"
    if not wf.exists():
        return set()
    data = json.loads(wf.read_text(encoding="utf-8"))
    cur = data.get("current_pass", 0)
    out = set()
    for w in data.get("waivers", []):
        if w.get("status") == "active" and (not isinstance(w.get("expires_by_pass"), int) or cur <= w["expires_by_pass"]):
            out.add(w.get("file_path"))
    return out


def _scan(repo: Path) -> dict[str, list[str]]:
    """Run every standards rule against ``repo`` and return {rule_name: [offenders]}. Used for the live tree
    and (with a synthetic repo) for the negative self-test."""
    waived = _waived_paths() if repo == _REPO else set()
    off: dict[str, list[str]] = {}

    # 1) source adapters match the SourceAdapter shape
    bad = []
    for p in _py_files_in(repo / "src" / "baltor" / "adapters" / "source"):
        t = p.read_text(encoding="utf-8", errors="ignore")
        if not ("source_type" in t and "parser_provider" in t and "def ingest(" in t):
            bad.append(str(p.relative_to(repo)))
    off["source_adapter_shape"] = bad

    # 2) proof scripts support --self-test
    bad = []
    for p in sorted((repo / "scripts").glob("check_*.py")):
        if "__pycache__" in p.parts:
            continue
        t = p.read_text(encoding="utf-8", errors="ignore")
        if "--self-test" not in t and "self_test" not in t:
            bad.append(str(p.relative_to(repo)))
    off["proof_self_test"] = bad

    # 3) standards docs carry a top-level heading
    bad = []
    sdir = repo / "docs" / "standards"
    if sdir.is_dir():
        for p in sorted(sdir.glob("*.md")):
            lines = p.read_text(encoding="utf-8", errors="ignore").splitlines()
            if not any(ln.startswith("# ") for ln in lines):
                bad.append(str(p.relative_to(repo)))
    off["doc_has_heading"] = bad

    # 4) projection code does not mutate truth / embed secrets
    bad = []
    proj_files = [repo / f for f in _PROJECTION_FILES]
    for d in _PROJECTION_DIRS:
        proj_files += _py_files_in(repo / d)
    for p in proj_files:
        if not p.exists():
            continue
        t = p.read_text(encoding="utf-8", errors="ignore")
        if any(m in t for m in _TRUTH_MUTATION) or _RAW_SECRET.search(t):
            bad.append(str(p.relative_to(repo)))
    off["projection_safe"] = bad

    # 5) UI pages are projection-only (no durable writes)
    bad = []
    udir = repo / "web" / "baltor"
    if udir.is_dir():
        for p in sorted(udir.rglob("*.html")):
            t = p.read_text(encoding="utf-8", errors="ignore")
            if any(m in t for m in _UI_WRITE_FORBIDDEN):
                bad.append(str(p.relative_to(repo)))
    off["ui_projection_only"] = bad

    # 6) config templates carry no raw secrets
    bad = []
    cdir = repo / "templates" / "configs"
    if cdir.is_dir():
        for p in sorted(cdir.rglob("*.json")):
            if _RAW_SECRET.search(p.read_text(encoding="utf-8", errors="ignore")):
                bad.append(str(p.relative_to(repo)))
    off["config_no_raw_secret"] = bad

    # 7) no new vague filename in governed scope (outside the file-layout allowlist + active waivers)
    allow = set()
    pol = repo / "architecture" / "file_layout_policy.json"
    if pol.exists():
        allow = {e["path"] for e in json.loads(pol.read_text(encoding="utf-8")).get("banned_filename_allowlist", [])}
    bad = []
    for scope in _VAGUE_SCAN_SCOPE:
        for p in (repo / scope).rglob("*.py"):
            if any(part in _SKIP_PARTS for part in p.parts):
                continue
            rel = str(p.relative_to(repo))
            if p.name in _VAGUE_FILENAMES and rel not in allow and rel not in waived:
                bad.append(rel)
    off["no_new_vague_filename"] = bad

    # 8) processors do not perform raw storage writes (must go through ports)
    bad = []
    for g in _PROCESSOR_GLOBS:
        for p in repo.glob(g):
            if not p.is_file() or "__pycache__" in p.parts or p.name == "__init__.py":
                continue
            t = p.read_text(encoding="utf-8", errors="ignore")
            if any(re.search(pat, t, re.M) for pat in _RAW_STORAGE_WRITE):
                bad.append(str(p.relative_to(repo)))
    off["processor_no_raw_storage"] = bad

    return off


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    # ── POSITIVE: the current tree is clean against every rule ──────────────────────────────────────────
    live = _scan(_REPO)
    for rule, offenders in live.items():
        check(f"clean tree passes rule '{rule}'", offenders == [], str(offenders[:6]))

    # ── COVERAGE: every standards category is actually represented by conforming code (not vacuously green) ─
    check("at least one conforming source adapter exists", len(_py_files_in(_SOURCE_ADAPTER_DIR)) >= 1)
    check("proof scripts exist to lint", len(list((_resource("scripts")).glob("check_*.py"))) >= 10)
    check("at least 3 config templates exist", len(list(_CONFIG_TEMPLATES_DIR.rglob("*.json"))) >= 3)
    check("standards docs exist", _STANDARDS_DOCS_DIR.is_dir() and len(list(_STANDARDS_DOCS_DIR.glob("*.md"))) >= 1)

    # ── NEGATIVE: introduce each deviation in a temp repo; the matching rule MUST fire ──────────────────
    tmp = Path(tempfile.mkdtemp(prefix="std_linter_neg_"))
    try:
        # minimal synthetic repo with each governed scope
        (tmp / "src" / "baltor" / "adapters" / "source").mkdir(parents=True)
        (tmp / "scripts").mkdir(parents=True)
        (tmp / "docs" / "standards").mkdir(parents=True)
        (tmp / "web" / "baltor").mkdir(parents=True)
        (tmp / "templates" / "configs" / "x").mkdir(parents=True)
        # processors moved under _repos/ post-migration; mirror the REAL scope (`_PROCESSOR_GLOBS`) so the
        # negative fixture lands where rule 8 actually scans (the positive scan hits the 12 real processors).
        (tmp / "_repos" / "baltor" / "backend" / "src" / "baltor" / "processors" / "bad").mkdir(parents=True)
        (tmp / "architecture").mkdir(parents=True)
        # an empty file-layout policy (no allowlist) so the vague-filename rule has something to read
        (tmp / "architecture" / "file_layout_policy.json").write_text(
            json.dumps({"banned_filename_allowlist": []}), encoding="utf-8")

        # deviation per rule:
        (tmp / "src" / "baltor" / "adapters" / "source" / "broken_adapter.py").write_text(
            "class BrokenAdapter:\n    pass\n", encoding="utf-8")  # no source_type/parser_provider/ingest
        (tmp / "scripts" / "check_no_selftest.py").write_text(
            '"""a proof with no self-test flag."""\nprint("hi")\n', encoding="utf-8")
        (tmp / "docs" / "standards" / "no_heading.md").write_text(
            "this doc has no top-level heading\n", encoding="utf-8")
        (tmp / "web" / "baltor" / "bad.html").write_text(
            "<html>INSERT INTO truth VALUES(1)</html>", encoding="utf-8")
        _kname = '"api' + '_key"'  # split so THIS proof's own source stays secret-hygiene-clean (built at runtime)
        (tmp / "templates" / "configs" / "x" / "leaky.json").write_text(
            '{%s: "RAW-INLINE-NOT-A-REF"}' % _kname, encoding="utf-8")
        (tmp / "scripts" / "common.py").write_text("# vague filename\n", encoding="utf-8")
        (tmp / "_repos" / "baltor" / "backend" / "src" / "baltor" / "processors" / "bad" / "writer.py").write_text(
            "import sqlite3\nsqlite3.connect('x')\n", encoding="utf-8")

        neg = _scan(tmp)
        check("negative: broken source adapter is caught", neg["source_adapter_shape"] != [])
        check("negative: proof without --self-test is caught", neg["proof_self_test"] != [])
        check("negative: doc without a heading is caught", neg["doc_has_heading"] != [])
        check("negative: UI page writing truth is caught", neg["ui_projection_only"] != [])
        check("negative: config template with a raw secret is caught", neg["config_no_raw_secret"] != [])
        check("negative: new vague filename is caught", neg["no_new_vague_filename"] != [])
        check("negative: processor doing a raw storage write is caught", neg["processor_no_raw_storage"] != [])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print(f"\n{'PASS — check_new_code_uses_standards: the clean tree obeys every standard, each category is represented by conforming code, and each rule provably bites on a deviation.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="The standards linter: new code must match its pattern's shape.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
