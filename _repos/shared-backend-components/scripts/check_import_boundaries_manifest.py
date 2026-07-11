#!/usr/bin/env python3
"""scripts.check_import_boundaries_manifest — proof: the import-boundary manifest is well-formed AND the
runtime core contains no domain/web/admin imports and processor adapters contain no admin/web imports.
Architecture drift (modules reaching across layers) becomes a failing check.

CLI: python3 _repos/shared-backend-components/scripts/check_import_boundaries_manifest.py --self-test
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    m = json.loads((_resource("architecture") / "import_boundaries.json").read_text())
    check("every layer rule declares (may_import + must_not_import) or a prose rule",
          all(("may_import" in v and "must_not_import" in v) or "rule" in v for v in m["rules"].values()))
    check("runtime must_not_import lists processors + web + admin server",
          {"processors", "web"} <= set(m["rules"]["runtime"]["must_not_import"]))

    # runtime CORE files contain none of the forbidden substrings (domain/web/admin leakage)
    bad = []
    for f in m["runtime_core_files"]:
        text = (_resource(f)).read_text(encoding="utf-8")
        for sub in m["runtime_core_forbidden_substrings"]:
            if sub in text:
                bad.append(f"{f}:{sub}")
    check("runtime CORE imports no admin/web/domain (cfpb/esg/demo) module", bad == [], str(bad))

    pbad = []
    for f in m.get("processor_files", []):
        text = (_resource(f)).read_text(encoding="utf-8")
        for sub in m["processor_forbidden_substrings"]:
            if sub in text:
                pbad.append(f"{f}:{sub}")
    check("processor adapters import no admin server / web", pbad == [], str(pbad))

    check("LLM rule forbids direct provider imports outside the gateway", "gateway" in m["rules"]["llm"]["rule"].lower())
    check("legacy allowlist documents the builtin_processors domain-adapter exception",
          any("builtin_processors" in e["path"] for e in m["legacy_allowlist"]))

    print(f"\n{'PASS — check_import_boundaries_manifest: layer rules well-formed; runtime core is domain/web/admin-free; processor adapters do not reach the admin server or web.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: import boundaries.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
