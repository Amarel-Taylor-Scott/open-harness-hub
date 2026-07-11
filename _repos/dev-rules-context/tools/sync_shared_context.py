#!/usr/bin/env python3
"""tools/sync_shared_context — project the SINGLE-SOURCE shared context from this repo
(aidoneright-dev-rules-context) into every consumer repo as a generated `.aidoneright/` bundle, so a
developer can clone ONE repo and have the full rules + skills + agents + edges WITHOUT downloading any
other repo.

The reconciliation of "no duplication" with "every repo self-contained": the shared context is authored
ONCE here and COPIED (the necessary, deliberate duplication) into each repo as a GENERATED bundle, and
`--check` fails if any copy drifts from the source — so the duplication is single-source and never rots.
This is the same law the whole org runs on (NO-MAGIC-VALUES: "where a value must be mirrored, add a check
that fails on drift").

  --write  --repos-root <dir>   vendor the bundle into <dir>/<repo>/.aidoneright for every consumer surface
  --check  --repos-root <dir>   exit 1 if any vendored copy differs from the source (the CI drift gate)
  --self-test                   mutation gate (a real injected drift makes --check go red)

What travels (the self-sufficiency bundle — small, essential; NOT the heavy reference/archive material):
  standards/ · skills/ · agents/ · commands/ · hooks/ · the core _shared docs · the surface registry.
Edges travel separately as the generated AIDONERIGHT-UNIVERSE.md + EDGES.md (edge-graph-generator).

Offline, deterministic.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE_ROOT = HERE.parent                      # this repo = aidoneright-dev-rules-context = the single source
VENDOR_DIR = ".aidoneright"
SOURCE_SURFACE = "dev-rules-context"           # never vendored into itself (it IS the source)
REGISTRY_REL = "contracts/surface-registry.json"

# The bundle allowlist: dirs are copied whole, files individually. Kept deliberately SMALL — a dev needs the
# rules/skills/agents/glossary/registry to work solo, not the whole reference library (which stays in the source).
BUNDLE = [
    "standards",                      # the 8 law texts (linked from every CLAUDE.md)
    "skills",                         # reusable Claude Code skills
    "agents",                         # reusable subagent definitions
    "commands",                       # reusable slash-commands
    "hooks",                          # reusable hooks
    "_shared/GLOSSARY.md",
    "_shared/ARCHITECTURE-MAP.md",
    "_shared/OVERARCHING-GOAL.md",
    "_shared/PRODUCT-MARKET-FIT.md",
    "_shared/STANDARDS.md",
    REGISTRY_REL,                     # the single source of edges — lets a solo repo regenerate its universe
]


def _source_commit() -> str:
    try:
        return subprocess.run(["git", "-C", str(SOURCE_ROOT), "rev-parse", "--short", "HEAD"],
                              capture_output=True, text=True, timeout=5).stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def bundle_files(src_root: Path) -> list[tuple[str, Path]]:
    """Every (relpath, abspath) the bundle expands to, sorted — dirs walked, missing entries skipped."""
    out: list[tuple[str, Path]] = []
    for entry in BUNDLE:
        p = src_root / entry
        if p.is_dir():
            out += [(str(f.relative_to(src_root)), f) for f in p.rglob("*") if f.is_file()]
        elif p.is_file():
            out.append((entry, p))
    return sorted(out)


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def consumer_surfaces(src_root: Path) -> list[str]:
    """The consumer repos = every surface in the registry EXCEPT the source itself (single source of the list)."""
    reg = json.loads((src_root / REGISTRY_REL).read_text())
    return sorted(s for s in reg.get("surfaces", {}) if s != SOURCE_SURFACE)


def _generated_header(commit: str) -> str:
    return (f"# `.aidoneright/` — GENERATED shared context (do not edit here)\n\n"
            f"Vendored from the single source **aidoneright-dev-rules-context** (`{commit}`) by "
            f"`tools/sync_shared_context.py`.\n\n"
            f"- This bundle makes THIS repo self-contained: the org rules (`standards/`), skills, agents, "
            f"commands, hooks, glossary, and the surface registry travel with the repo, so you can work on it "
            f"without cloning any other repo.\n"
            f"- **Do not edit these files here** — edit them in `aidoneright-dev-rules-context` and re-run the "
            f"sync; a CI drift gate (`sync_shared_context.py --check`) fails if a copy is stale.\n"
            f"- Cross-repo edges/interfaces live in the repo-root `AIDONERIGHT-UNIVERSE.md` (the whole org, "
            f"self-contained) + `EDGES.md` (the terse neighbour digest).\n")


def write_bundle(src_root: Path, repos_root: Path) -> dict:
    files = bundle_files(src_root)
    commit = _source_commit()
    written = []
    for surface in consumer_surfaces(src_root):
        dest_repo = repos_root / surface
        if not dest_repo.is_dir():
            continue
        vendor = dest_repo / VENDOR_DIR
        if vendor.exists():
            shutil.rmtree(vendor)                       # clean projection — removed source files disappear here too
        for rel, abspath in files:
            target = vendor / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(abspath, target)
        (vendor / "GENERATED.md").write_text(_generated_header(commit))
        written.append(surface)
    return {"surfaces": written, "file_count": len(files), "source_commit": commit}


def check_bundle(src_root: Path, repos_root: Path) -> list[str]:
    """Return a list of drift descriptions (empty == in sync). Compares every vendored copy to the source."""
    files = bundle_files(src_root)
    src_hash = {rel: _digest(p) for rel, p in files}
    drift: list[str] = []
    for surface in consumer_surfaces(src_root):
        vendor = repos_root / surface / VENDOR_DIR
        if not (repos_root / surface).is_dir():
            continue
        if not vendor.is_dir():
            drift.append(f"{surface}: no {VENDOR_DIR}/ bundle (run --write)")
            continue
        have = {str(f.relative_to(vendor)): _digest(f) for f in vendor.rglob("*")
                if f.is_file() and f.name != "GENERATED.md"}
        for rel, h in src_hash.items():
            if rel not in have:
                drift.append(f"{surface}: missing {rel}")
            elif have[rel] != h:
                drift.append(f"{surface}: STALE {rel}")
        for rel in have:
            if rel not in src_hash:
                drift.append(f"{surface}: orphan {rel} (not in source)")
    return drift


def self_test() -> int:
    import tempfile
    checks = []
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        src = root / SOURCE_SURFACE
        (src / "standards").mkdir(parents=True)
        (src / "standards" / "LAW.md").write_text("law one")
        (src / "skills").mkdir(); (src / "skills" / "s.md").write_text("skill")
        (src / "agents").mkdir(); (src / "agents" / "a.md").write_text("agent")
        (src / "commands").mkdir(); (src / "hooks").mkdir()
        (src / "_shared").mkdir()
        for f in ("GLOSSARY.md", "ARCHITECTURE-MAP.md", "OVERARCHING-GOAL.md", "PRODUCT-MARKET-FIT.md", "STANDARDS.md"):
            (src / "_shared" / f).write_text(f)
        (src / "contracts").mkdir()
        (src / "contracts" / "surface-registry.json").write_text(json.dumps(
            {"surfaces": {"dev-rules-context": {}, "teleon": {}, "baltor": {}}}))
        (root / "teleon").mkdir(); (root / "baltor").mkdir()
        res = write_bundle(src, root)
        checks.append(("vendors into consumers only (not the source)", set(res["surfaces"]) == {"teleon", "baltor"}))
        checks.append(("law text present in a consumer's bundle",
                       (root / "teleon" / VENDOR_DIR / "standards" / "LAW.md").read_text() == "law one"))
        checks.append(("agent def travels with the repo",
                       (root / "baltor" / VENDOR_DIR / "agents" / "a.md").exists()))
        checks.append(("GENERATED header written", (root / "teleon" / VENDOR_DIR / "GENERATED.md").exists()))
        checks.append(("clean sync == no drift", check_bundle(src, root) == []))
        # inject a real drift -> --check must go red (mutation gate)
        (root / "teleon" / VENDOR_DIR / "standards" / "LAW.md").write_text("TAMPERED")
        checks.append(("a tampered copy is caught as STALE", any("STALE" in d for d in check_bundle(src, root))))
    failed = [n for n, ok in checks if not ok]
    if failed:
        print("FAIL - sync_shared_context:\n  " + "\n  ".join(failed)); return 1
    print("PASS - sync_shared_context: single source -> vendored .aidoneright bundle into every consumer, "
          "drift gate catches a stale/tampered/missing/orphan copy.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Vendor the single-source shared context into every consumer repo.")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--repos-root", type=Path, default=SOURCE_ROOT.parent,
                    help="dir holding every repo folder (default: this repo's parent = the _repos mirror)")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    if args.write:
        res = write_bundle(SOURCE_ROOT, args.repos_root)
        print(f"vendored {res['file_count']} shared files (source {res['source_commit']}) into "
              f"{len(res['surfaces'])} consumer repos under {args.repos_root}")
        return 0
    if args.check:
        drift = check_bundle(SOURCE_ROOT, args.repos_root)
        if drift:
            print(f"DRIFT ({len(drift)}):\n  " + "\n  ".join(drift[:40]))
            return 1
        print("in sync: every consumer's .aidoneright bundle matches the source")
        return 0
    print("usage: sync_shared_context.py --self-test | --write | --check  [--repos-root <dir>]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
