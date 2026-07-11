#!/usr/bin/env python3
"""Gate: SECRET reads under scripts/ funnel through the ONE chokepoint — scripts.runtime.secret_resolve.

The key-depth audit found direct `os.environ`/`getenv` reads of credential-registry secrets scattered
across scripts/ files, each bypassing the single resolve() seam (`src.teleon.runtime.key_holder`, now
wrapped by `scripts/runtime/secret_resolve.py`). The existing credential gate only scans `src/teleon/**`,
so scripts/ was ungoverned. This gate inventories those direct SECRET reads (secret = the env-var NAMES
in `architecture/credential_registry.json`), records them as a ratcheting BASELINE in
`architecture/secret_chokepoint_migration.json` (like the canonical_id gate), and FAILS on a NEW one — so
the audit's sites migrate to `secret_resolve.resolve(name)` safely over time and a fresh direct read can
never be added silently.

A "site" is `<scripts-relative-path>::<SECRET_NAME>` — stable across the file's other edits, so a file
migrates by removing its entry in the SAME change (the ledger stays true). Chokepoint code that resolves
by a NAME variable (not a hardcoded secret literal) does not match, so migrating a site removes it.

  PYTHONPATH=. python3 scripts/check_secret_chokepoint.py --self-test
  PYTHONPATH=. python3 scripts/check_secret_chokepoint.py --emit-baseline   # regenerate the manifest baseline
"""
from __future__ import annotations

import json
import re
import sys
import tempfile
from pathlib import Path

from scripts._repo_paths import resource as _resource

REPO = Path(__file__).resolve().parents[1]
SCAN_ROOT_REL = "scripts"
CHOKEPOINT = "scripts/runtime/secret_resolve.py"
GATE = "scripts/check_secret_chokepoint.py"
MANIFEST_PATH = _resource("architecture") / "secret_chokepoint_migration.json"
CREDENTIAL_REGISTRY = _resource("architecture") / "credential_registry.json"

# A direct environment read whose quoted arg is a literal name: os.environ.get("X") / os.getenv("X") /
# os.environ["X"] (and the bare `getenv`/`environ.get`/`environ[` imported forms). A read parametrised by
# a NAME variable (as the chokepoint and its backends do) has no quoted literal here, so it never matches
# — which is exactly how a migrated site leaves the baseline.
_ENV_READ_RE = re.compile(
    r'(?:os\.environ\.get|os\.getenv|os\.environ\[|(?<![\w.])environ\.get|(?<![\w.])environ\[|(?<![\w.])getenv)'
    r'\s*\(?\s*["\']([A-Z][A-Z0-9_]{2,})["\']'
)
# Files that are PART of the chokepoint seam (they resolve secrets legitimately) — never flagged.
_SEAM_FILES = {CHOKEPOINT, GATE}


def _secret_names() -> set[str]:
    """The credential-registry env-var NAMES — the definition of 'a secret' (single source, no drift)."""
    reg = json.loads(CREDENTIAL_REGISTRY.read_text(encoding="utf-8"))
    return {v for s in reg["services"] for v in s["env_vars"]}


def _direct_secret_sites(root: Path, scan_rel: str, secret_names: set[str]) -> list[str]:
    """Every `<scan_rel-relative>::NAME` site under `root/scan_rel` that reads a SECRET name directly.
    Sorted + unique. The seam files themselves are excluded."""
    scan_dir = root / scan_rel
    sites: set[str] = set()
    for path in scan_dir.rglob("*.py"):
        rel = path.relative_to(root).as_posix()
        if rel in _SEAM_FILES:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for name in _ENV_READ_RE.findall(text):
            if name in secret_names:
                sites.add(f"{rel}::{name}")
    return sorted(sites)


def _load_manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def _build_manifest(baseline: list[str]) -> dict:
    return {
        "principle": (
            "Every SECRET read under scripts/ funnels through the ONE chokepoint "
            "scripts.runtime.secret_resolve.resolve(name) (which wraps the runtime key holder). "
            "This manifest records the direct os.environ/getenv secret reads that still bypass it as a "
            "ratcheting baseline: a migrated site is removed in the SAME change; a NEW direct read is a "
            "hard failure. secret = an env-var NAME in credential_registry.json. serves_truth=false."
        ),
        "serves_truth": False,
        "chokepoint": CHOKEPOINT,
        "gate": GATE,
        "scan_root": SCAN_ROOT_REL,
        "secret_name_source": "architecture/credential_registry.json",
        "site_format": "<scripts-relative-path>::<SECRET_NAME>",
        "legacy_direct_secret_reads": baseline,
    }


def _emit_baseline() -> int:
    baseline = _direct_secret_sites(REPO, SCAN_ROOT_REL, _secret_names())
    MANIFEST_PATH.write_text(json.dumps(_build_manifest(baseline), indent=2) + "\n", encoding="utf-8")
    print(f"wrote {MANIFEST_PATH} — {len(baseline)} baseline site(s)")
    return 0


def _checks() -> list[tuple[str, bool, str]]:
    results: list[tuple[str, bool, str]] = []
    secret_names = _secret_names()

    # A. The chokepoint module exists and resolve(name) works on an injected env.
    try:
        from scripts.runtime import secret_resolve as _sr  # noqa: PLC0415
        ok = (
            _sr.resolve("OH_LLM_API_KEY", env={"OH_LLM_API_KEY": "x"}) == "x"
            and _sr.resolve("OH_LLM_API_KEY", env={}) is None
        )
        results.append(("chokepoint scripts.runtime.secret_resolve.resolve(name) exists + works", ok, CHOKEPOINT))
    except Exception as exc:  # noqa: BLE001
        results.append(("chokepoint scripts.runtime.secret_resolve.resolve(name) exists + works", False, repr(exc)))

    # B. Manifest parses and declares the contract surface.
    try:
        manifest = _load_manifest()
        baseline = manifest.get("legacy_direct_secret_reads", [])
        ok = (
            manifest.get("chokepoint") == CHOKEPOINT
            and manifest.get("gate") == GATE
            and manifest.get("scan_root") == SCAN_ROOT_REL
            and isinstance(baseline, list) and all(isinstance(s, str) and "::" in s for s in baseline)
        )
        results.append(("manifest declares chokepoint + gate + recorded baseline", ok, f"{len(baseline)} recorded"))
    except Exception as exc:  # noqa: BLE001
        results.append(("manifest declares chokepoint + gate + recorded baseline", False, repr(exc)))
        return results

    # C. Live scan: no NEW direct-secret read site under scripts/ beyond the recorded baseline.
    live = _direct_secret_sites(REPO, SCAN_ROOT_REL, secret_names)
    baseline_set = set(baseline)
    new_sites = [s for s in live if s not in baseline_set]
    results.append((
        "no NEW direct-secret read under scripts/ (funnel via secret_resolve.resolve)",
        not new_sites, ", ".join(new_sites[:6]) or f"clean ({len(live)} known)",
    ))

    # D. Ratchet accuracy: every baseline site still reads directly (a migrated file leaves the baseline
    #    in the SAME change — no stale entries).
    live_set = set(live)
    stale = [s for s in baseline if s not in live_set]
    results.append((
        "baseline has no STALE entries (migrated sites leave the baseline same-change)",
        not stale, ", ".join(stale[:6]) or "accurate",
    ))

    # E. Negative proof: the scanner actually catches a synthetic new violation. The payload is built
    #    from a NAME VARIABLE so this gate's OWN source never contains a matching literal.
    with tempfile.TemporaryDirectory() as td:
        probe_name = sorted(secret_names)[0]
        bad = Path(td) / "scripts" / "demo_leak.py"
        bad.parent.mkdir(parents=True)
        bad.write_text("import os\nKEY = os.environ.get(%r)\n" % probe_name, encoding="utf-8")
        caught = _direct_secret_sites(Path(td), "scripts", secret_names)
        want = [f"scripts/demo_leak.py::{probe_name}"]
        results.append(("negative: a synthetic direct-secret read IS caught", caught == want, str(caught)))

    return results


def main() -> int:
    if "--emit-baseline" in sys.argv:
        return _emit_baseline()
    results = _checks()
    failures = [name for name, ok, _ in results if not ok]
    for name, ok, detail in results:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}: {detail}")
    if failures:
        print(f"\n{len(failures)} FAILURES: {failures}")
        return 1
    print("\nPASS - check_secret_chokepoint: no NEW literal-name os.environ/getenv secret read under "
          "scripts/ outside secret_resolve (a determined bypass via an aliased var / f-string / split "
          "literal evades the regex — this is a floor, not a proof); the baseline is a review-gated set, "
          "not a git-diff-enforced monotone ratchet.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
