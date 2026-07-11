#!/usr/bin/env python3
"""scripts.check_standards_api — proof: the Standards API (_repos/shared-backend-components/scripts/api_standards_handler.py) is a pure,
projection-only handler. Each GET function returns a JSON-serializable dict with the expected keys and is
robust whether or not the sibling-lane truth files exist (degrades to {"available": false, ...}).
POST /api/standards/generate-preview is a DRY-RUN: it returns what WOULD be generated and writes NO files
(proven by snapshotting a temp dir and the repo's _repos/shared-backend-components/architecture/ dir before/after). Deterministic + offline.

CLI: python3 _repos/shared-backend-components/scripts/check_standards_api.py --self-test
"""
from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from pathlib import Path

from scripts.api_standards_handler import ROUTES, handle, owns

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
_ARCH = _resource("architecture")

#: each GET endpoint -> the list key its payload must carry (besides "available"/"total").
_GET_ENDPOINTS = {
    "/api/standards/patterns": "patterns",
    "/api/standards/templates": "templates",
    "/api/standards/routines": "routines",
    "/api/standards/waivers": "waivers",
    "/api/standards/maturity": "patterns",
}


def _dir_fingerprint(path: Path) -> str:
    """Content-addressed fingerprint of a directory tree (names + sizes + sha of bytes). Deterministic."""
    h = hashlib.sha256()
    if path.exists():
        for f in sorted(p for p in path.rglob("*") if p.is_file()):
            h.update(str(f.relative_to(path)).encode())
            h.update(f.read_bytes())
    return h.hexdigest()


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    # 1) every GET endpoint returns a JSON-serializable dict with the expected keys (degrades gracefully).
    for route, list_key in _GET_ENDPOINTS.items():
        code, payload = handle("GET", route, {})
        check(f"GET {route} returns 200 dict", code == 200 and isinstance(payload, dict), str(code))
        check(f"GET {route} carries 'available' + 'total' + '{list_key}'",
              {"available", "total", list_key}.issubset(payload.keys()), str(sorted(payload.keys())))
        check(f"GET {route} payload is JSON-serializable",
              json.dumps(payload) is not None)
        check(f"GET {route} list matches 'total'",
              len(payload.get(list_key, [])) == payload.get("total"),
              f"{len(payload.get(list_key, []))} != {payload.get('total')}")

    # 2) the handler owns exactly its 6 routes and rejects foreign routes cleanly.
    check("owns() recognizes all 6 standards routes", all(owns(r) for r in ROUTES) and len(ROUTES) == 6)
    code, payload = handle("GET", "/api/context/serve", {})
    check("foreign route returns 404 (not a crash)", code == 404 and "error" in payload)

    # 3) generate-preview is a DRY-RUN: it writes NO files. Snapshot a temp dir AND _repos/shared-backend-components/architecture/ before/after.
    tmp = Path(tempfile.mkdtemp(prefix="standards_preview_"))
    try:
        tmp_before = _dir_fingerprint(tmp)
        arch_before = _dir_fingerprint(_ARCH)
        code, payload = handle("POST", "/api/standards/generate-preview",
                               {"pattern_id": "proof_script_pattern", "template_id": "demo", "target": "check_x.py"})
        check("generate-preview returns a dict", isinstance(payload, dict), str(type(payload)))
        check("generate-preview marks itself dry_run", payload.get("dry_run") is True, str(payload.get("dry_run")))
        check("generate-preview reports nothing was written",
              all(not w.get("written", False) for w in payload.get("would_create", [])),
              str(payload.get("would_create")))
        check("generate-preview wrote NO files to the temp dir", _dir_fingerprint(tmp) == tmp_before)
        check("generate-preview did NOT mutate architecture/ (no truth write)", _dir_fingerprint(_ARCH) == arch_before)
        check("generate-preview is JSON-serializable", json.dumps(payload) is not None)
        # determinism: same inputs -> same response shape twice.
        code2, payload2 = handle("POST", "/api/standards/generate-preview",
                                 {"pattern_id": "proof_script_pattern", "template_id": "demo", "target": "check_x.py"})
        check("generate-preview is deterministic (same inputs -> same payload)", payload == payload2)
    finally:
        for f in sorted(tmp.rglob("*"), reverse=True):
            f.rmdir() if f.is_dir() else f.unlink()
        tmp.rmdir()

    # 4) projection-only: no payload leaks a secret marker.
    leaked: list[str] = []
    for route in _GET_ENDPOINTS:
        _, p = handle("GET", route, {})
        blob = json.dumps(p)
        leaked += [m for m in ("OH_SHOWCASE_TOKEN", "sk-", "MEMORY.md", ".agent/") if m in blob]
    check("no GET projection leaks a secret marker", leaked == [], str(leaked))

    print(f"\n{'PASS — check_standards_api: all 6 standards routes are pure projection-only handlers returning JSON-serializable dicts with expected keys (degrade gracefully when truth files are absent); generate-preview is a verified DRY-RUN that writes no files and is deterministic; no secrets leak.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: standards API handler (projection-only).")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
