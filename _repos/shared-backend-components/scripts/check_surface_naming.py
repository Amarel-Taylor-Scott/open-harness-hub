#!/usr/bin/env python3
"""Gate: product-facing copy uses the canonical surface names, never forbidden aliases.

Single source: _repos/shared-backend-components/architecture/surface_naming_registry.json (owner canonical operating
interpretation, 2026-07-01). The public family is AI Done Right · AIDevObserver ·
Teleon · Baltor · OpenHubForAI; the AIDevObserver Benchmark Lab is an internal/eval
mode, and its branded historical aliases (AIDevExplorer / AI Dev Explorer / …) must
not appear in PRODUCT-FACING copy unless the same line explicitly marks them
legacy/internal. Lowercase `aidevexplorer` path/script namespaces stay allowed as
legacy implementation details until a deliberate migration.

Usage: python3 _repos/shared-backend-components/scripts/check_surface_naming.py --self-test
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import json
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
REGISTRY_PATH = _resource("architecture") / "surface_naming_registry.json"
#: product-facing scope: the shipped surfaces + the repo front door.
PRODUCT_FACING_GLOBS = [("web", "*.jsx"), ("web", "*.js"), ("web", "*.html"), ("web", "*.json")]
PRODUCT_FACING_FILES = ["README.md"]
_SKIP_PARTS = {"node_modules", "vendor", "__pycache__"}


def _load_registry() -> dict:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def _forbidden_and_markers(reg: dict) -> tuple[list[str], list[str]]:
    forbidden: list[str] = []
    for surface in reg["surfaces"].values():
        forbidden.extend(surface.get("forbidden_public_names", []))
    return forbidden, list(reg.get("legacy_marker_tokens", []))


def _product_facing_files(root: Path) -> list[Path]:
    files = [root / f for f in PRODUCT_FACING_FILES if (root / f).is_file()]
    for base, pattern in PRODUCT_FACING_GLOBS:
        base_dir = root / base
        if base_dir.is_dir():
            files.extend(p for p in base_dir.rglob(pattern)
                         if not any(part in _SKIP_PARTS for part in p.parts))
    return files


def _scan(root: Path) -> list[str]:
    reg = _load_registry()
    forbidden, markers = _forbidden_and_markers(reg)
    hits: list[str] = []
    for path in _product_facing_files(root):
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for lineno, line in enumerate(lines, 1):
            for alias in forbidden:
                if alias in line and not any(marker in line for marker in markers):
                    hits.append(f"{path.relative_to(root)}:{lineno} uses forbidden public alias {alias!r}")
    return hits


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    reg = _load_registry()
    surfaces = reg.get("surfaces", {})
    check("registry parses and declares the 5 public surfaces + the internal benchmark-lab mode",
          {"ai_done_right", "aidevobserver", "teleon", "baltor", "openhubforai",
           "aidevobserver_benchmark_lab"} <= set(surfaces))
    check("every public surface with a web_root points at an existing app",
          all((_resource(s["web_root"])).is_dir() for s in surfaces.values() if s.get("web_root")))
    lab = surfaces["aidevobserver_benchmark_lab"]
    check("the benchmark lab is an internal mode under AIDevObserver with recorded legacy namespace",
          lab.get("kind") == "internal_eval_mode" and lab.get("parent") == "aidevobserver"
          and "aidevexplorer" in lab.get("legacy_namespaces", []))
    check("forbidden aliases include every branded historical casing",
          {"AIDevExplorer", "AI Dev Explorer", "AIDevExploer", "DevExplorer"}
          <= set(lab.get("forbidden_public_names", [])))
    check("the portfolio sentence names all five public surfaces",
          all(s["public_name"] in reg["portfolio_sentence"]
              for k, s in surfaces.items() if s.get("kind") != "internal_eval_mode"))

    live_hits = _scan(REPO)
    check("no product-facing file uses a forbidden alias without a same-line legacy marker",
          live_hits == [], "; ".join(live_hits[:5]))

    with tempfile.TemporaryDirectory() as td:
        bad_root = Path(td)
        (bad_root / "web").mkdir()
        (bad_root / "web" / "page.jsx").write_text(
            "<h1>AIDevExplorer is our product</h1>\n", encoding="utf-8")
        caught = _scan(bad_root)
        # one line can legitimately hit multiple aliases (AIDevExplorer contains DevExplorer)
        check("negative: a branded alias in product copy IS caught",
              len(caught) >= 1 and all("page.jsx:1" in c for c in caught), str(caught))
        (bad_root / "web" / "page.jsx").write_text(
            "// AIDevExplorer is a legacy namespace, not a branded surface\n", encoding="utf-8")
        check("negative control: a same-line legacy marker is allowed", _scan(bad_root) == [])

    print(f"\n{'PASS - check_surface_naming: the 5-surface family + internal Benchmark Lab hold; forbidden aliases stay out of product-facing copy' if not fails else str(len(fails)) + ' FAILURES: ' + str(fails)}")
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(_self_test() if ("--self-test" in sys.argv or len(sys.argv) == 1) else _self_test())
