#!/usr/bin/env python3
"""Gate: DATA-OBJECT ids are minted by ONE authority — src.teleon.experiments.ids.

The owner naming law (deterministic globally-unique object naming, hardened 2026-07-01)
has two planes:
  * CODE objects  -> the pyprefix scheme (_repos/shared-backend-components/scripts/pyprefix.py + check_pyprefix_conformance.py);
  * DATA objects  -> canonical_id/sha256_hex over canonical_bytes ("{prefix}-{sha256[:16]}"),
    version in schema_version METADATA, never in a name/id.

Drift signal enforced here: direct `import hashlib` anywhere in src/** other than the
canonical module. Hand-rolled minting diverges (custom separators, missing sort_keys,
:12/:16/:20 suffixes) and collapses dedupe/index merges — the exact failure CLAUDE.md's
"ID And Hash Discipline" forbids. Legacy sites are RECORDED (never silently allowed) in
_repos/shared-backend-components/architecture/canonical_id_migration.json and must ratchet DOWN: a migrated file leaves the
baseline in the same change; a NEW site is a hard failure.

Usage:
  python3 _repos/shared-backend-components/scripts/check_canonical_id_single_source.py --self-test
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from scripts._repo_paths import canonical_code_path, repo_root

REPO = Path(__file__).resolve().parents[1]
# The src-scan MUST run from the real git root (the monorepo root, found by walking up to the .git marker),
# not from this repo dir: post-_repos/ migration the product backends live at `_repos/<x>/backend/src/<x>/…`,
# which git only tracks/resolves relative to the monorepo root. Running `git ls-files` (and reading the hits)
# from `REPO` (=shared-backend-components) matched NOTHING, so every moved-but-still-hashlib baltor file read
# as "stale". `canonical_code_path` then normalizes each physical hit back to its stable `src/<x>/…` id so it
# lines up with the baseline. Single-sourced via _repo_paths.repo_root() (no hardcoded parents[N]).
ROOT = repo_root()
MANIFEST_PATH = _resource("architecture") / "canonical_id_migration.json"
CANONICAL_MODULE = "src/teleon/experiments/ids.py"
# Matches a real import of hashlib (module-level or lazy), not the word in prose.
_HASHLIB_IMPORT_RE = re.compile(r"^\s*(import hashlib\b|from hashlib\b)", re.MULTILINE)


def _tracked_src_python_files() -> list[str]:
    out = subprocess.run(
        ["git", "ls-files", "src/*.py", "_repos/*/backend/src/*.py"],
        cwd=ROOT, capture_output=True, text=True, check=True,
    ).stdout
    return [line for line in out.splitlines() if line.strip()]


def _direct_hashlib_files(paths: list[str], root: Path) -> list[str]:
    hits: list[str] = []
    for rel in paths:
        if canonical_code_path(rel) == CANONICAL_MODULE:
            continue
        try:
            text = (root / rel).read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if _HASHLIB_IMPORT_RE.search(text):
            hits.append(canonical_code_path(rel))
    return sorted(hits)


def _load_manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def _checks() -> list[tuple[str, bool, str]]:
    results: list[tuple[str, bool, str]] = []

    # A. The canonical authority exists and behaves deterministically.
    sys.path.insert(0, str(REPO))
    try:
        from src.teleon.experiments.ids import (  # noqa: PLC0415
            ID_HASH_SUFFIX_LEN, canonical_bytes, canonical_id, sha256_hex,
        )
        a = canonical_id("row", "alpha", "beta")
        b = canonical_id("row", "alpha", "beta")
        c = canonical_id("row", "alpha", "GAMMA")
        ok = (
            a == b and a != c
            and a.startswith("row-")
            and len(a.split("-", 1)[1]) == ID_HASH_SUFFIX_LEN
            and canonical_bytes({"b": 1, "a": 2}) == canonical_bytes({"a": 2, "b": 1})
            and len(sha256_hex("x")) == 64
        )
        results.append(("canonical ids: ONE authority, deterministic, dash+16-hex, order-independent bytes", ok, a))
    except Exception as exc:  # pragma: no cover - import failure is the finding
        results.append(("canonical ids: ONE authority, deterministic, dash+16-hex, order-independent bytes", False, repr(exc)))

    # B. Manifest parses and declares the contract surface.
    try:
        manifest = _load_manifest()
        baseline = manifest.get("legacy_direct_hashlib", [])
        ok = (
            manifest.get("canonical_module") == CANONICAL_MODULE
            and manifest.get("gate") == "scripts/check_canonical_id_single_source.py"
            and isinstance(baseline, list) and all(isinstance(p, str) for p in baseline)
        )
        results.append(("manifest declares canonical module + gate + recorded baseline", ok, f"{len(baseline)} recorded"))
    except Exception as exc:
        results.append(("manifest declares canonical module + gate + recorded baseline", False, repr(exc)))
        return results

    # C. Live scan: no NEW direct-hashlib site in src/** beyond the recorded baseline.
    live = _direct_hashlib_files(_tracked_src_python_files(), ROOT)
    baseline_set = set(baseline)
    new_sites = [p for p in live if p not in baseline_set]
    results.append((
        "no NEW direct-hashlib minting site in src/** (mint via src.teleon.experiments.ids)",
        not new_sites, ", ".join(new_sites[:6]) or "clean",
    ))

    # D. Ratchet accuracy: every baseline entry still direct-hashes (stale entries must be
    #    removed in the same change that migrates the file — the ledger stays true).
    stale = [p for p in baseline if p not in set(live)]
    results.append((
        "baseline has no STALE entries (migrated files leave legacy_direct_hashlib same-change)",
        not stale, ", ".join(stale[:6]) or "accurate",
    ))

    # E. Negative proof: the scanner actually catches a synthetic new violation.
    with tempfile.TemporaryDirectory() as td:
        bad = Path(td) / "src" / "demo" / "minted.py"
        bad.parent.mkdir(parents=True)
        bad.write_text("import hashlib\n\nMY_ID = hashlib.sha256(b'x').hexdigest()[:8]\n", encoding="utf-8")
        caught = _direct_hashlib_files(["src/demo/minted.py"], Path(td))
        results.append(("negative: a synthetic hand-rolled minting site IS caught", caught == ["src/demo/minted.py"], str(caught)))

    return results


def main() -> int:
    results = _checks()
    failures = [name for name, ok, _ in results if not ok]
    for name, ok, detail in results:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}: {detail}")
    if failures:
        print(f"\n{len(failures)} FAILURES: {failures}")
        return 1
    print("\nPASS - check_canonical_id_single_source: data-object ids stay single-sourced "
          "(canonical_id over canonical_bytes; baseline ratchets down, never up)")
    return 0


if __name__ == "__main__":
    if "--self-test" in sys.argv or len(sys.argv) == 1:
        raise SystemExit(main())
    raise SystemExit(main())
