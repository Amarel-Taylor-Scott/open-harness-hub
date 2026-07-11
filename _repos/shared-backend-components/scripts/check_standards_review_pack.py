#!/usr/bin/env python3
"""scripts.check_standards_review_pack — proof: _repos/shared-backend-components/docs/status/standards-review-pack.md is grounded.

The standards review pack is the sign-off doc for the pattern/standards system: it summarizes the
pattern miner report, the standards catalog, the template catalog, the routine library, the waivers, the
top anti-patterns, a sample generated component, and the proof results. This proof keeps the pack honest:

  * the pack exists and carries its expected sections (miner report, standards catalog, template catalog,
    routine library, waivers, anti-patterns, sample generated component, proof results);
  * it references the REAL single-source catalogs (all must exist on disk);
  * it references the master proofs (the full-stack proof + the catalog proofs), all of which exist;
  * every anti-pattern path it cites EXISTS on disk (no fabricated anti-patterns — reality bar);
  * the sample-generation template id it names is a REAL active template in the template catalog.

Deterministic + offline (reads files only; no wall-clock, no RNG, no network).

CLI: python3 _repos/shared-backend-components/scripts/check_standards_review_pack.py --self-test
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource


def _on_disk(rel: str) -> bool:
    """True if a repo-relative path exists — via the universal resolver OR the repo-root fallback.
    `_resource` strips a leading dot (`.agent/...` -> `agent/...`), so a dotfile dir like `.agent`
    (a root symlink to the canonical generated dir) must resolve through `_REPO / rel`."""
    return _resource(rel).exists() or (_REPO / rel).exists()


_PACK = _resource("docs") / "status" / "standards-review-pack.md"
_TEMPLATES = _resource("architecture") / "template_catalog.json"

#: the single-source catalogs the pack must reference; all must exist on disk.
_REQUIRED_CATALOGS = (
    ".agent/pattern_miner_report.json",
    "architecture/standard_catalog.json",
    "architecture/template_catalog.json",
    "architecture/routine_library.json",
    "architecture/pattern_waivers.json",
)

#: master proofs the pack must reference; all must exist on disk.
_REQUIRED_PROOFS = (
    "scripts/check_pattern_standards_full_stack.py",
    "scripts/check_standard_catalog.py",
    "scripts/check_template_catalog.py",
    "scripts/check_routine_library.py",
    "scripts/check_pattern_waivers.py",
    "scripts/check_pattern_miner.py",
)

#: section markers the pack must contain (numbered headings).
_REQUIRED_SECTIONS = (
    "Pattern miner report",
    "Standards catalog",
    "Template catalog",
    "Routine library",
    "Waivers",
    "anti-patterns",          # "## 6. Top anti-patterns ..."
    "Sample generated component",
    "Proof results",
)

#: a path-like token inside backticks (scripts/foo.py etc.).
_PATH_RE = re.compile(r"`([A-Za-z0-9_][A-Za-z0-9_./@-]+\.(?:py|html|json|md))`")
#: --template <id> in the sample-generation command.
_TEMPLATE_RE = re.compile(r"--template\s+([A-Za-z0-9_.]+)")


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    if not _PACK.exists():
        check("docs/status/standards-review-pack.md exists", False, str(_PACK))
        print("\n1 FAILURES: ['pack missing']")
        return 1
    check("docs/status/standards-review-pack.md exists", True)
    text = _PACK.read_text(encoding="utf-8")

    # --- expected sections present ---
    missing_sections = [s for s in _REQUIRED_SECTIONS if s.lower() not in text.lower()]
    check("pack carries every expected section", missing_sections == [], str(missing_sections))

    # --- references the real single-source catalogs ---
    missing_catalogs = [c for c in _REQUIRED_CATALOGS if c not in text]
    check("pack references every single-source catalog", missing_catalogs == [], str(missing_catalogs))
    catalogs_on_disk = [c for c in _REQUIRED_CATALOGS if not _on_disk(c)]
    check("every referenced catalog EXISTS on disk", catalogs_on_disk == [], str(catalogs_on_disk))

    # --- references the master proofs, and they exist on disk ---
    missing_proof_refs = [p for p in _REQUIRED_PROOFS if p not in text]
    check("pack references every master proof", missing_proof_refs == [], str(missing_proof_refs))
    proofs_on_disk = [p for p in _REQUIRED_PROOFS if not (_resource(p)).exists()]
    check("every referenced master proof EXISTS on disk", proofs_on_disk == [], str(proofs_on_disk))

    # --- every cited path of any kind exists (no-fake), excluding generated-on-demand sample outputs ---
    # The pack documents the generator producing scripts/check_sample_demo.py + scripts/sample.py on demand
    # (NOT committed), so those are legitimately allowed to be absent.
    generated_on_demand = {"scripts/check_sample_demo.py", "scripts/sample.py"}
    cited = set(_PATH_RE.findall(text)) - generated_on_demand
    missing_cited = sorted(p for p in cited if not (_resource(p)).exists())
    check("every other cited path exists on disk (no-fake)", missing_cited == [], str(missing_cited))

    # --- the sample-generation template id is a REAL active template ---
    tmpl = json.loads(_TEMPLATES.read_text(encoding="utf-8"))
    active_ids = {t["template_id"] for t in tmpl.get("templates", []) if t.get("status") == "active"}
    cited_templates = set(_TEMPLATE_RE.findall(text))
    check("pack names a sample-generation template", bool(cited_templates), str(cited_templates))
    bad_templates = sorted(t for t in cited_templates if t not in active_ids)
    check("every cited generator template is a real ACTIVE template", bad_templates == [],
          str(bad_templates))

    # --- REALITY BAR: every anti-pattern path the pack cites exists on disk ---
    # The miner report is the source of truth; assert the path it names (and the pack repeats) is real.
    miner = json.loads(((_REPO / ".agent") / "pattern_miner_report.json").read_text(encoding="utf-8"))
    ap_paths = [a.get("path") for a in miner.get("anti_patterns", []) if a.get("path")]
    missing_ap = [p for p in ap_paths if not (_resource(p)).exists()]
    check("every anti-pattern path in the miner report is REAL (reality bar)", missing_ap == [],
          str(missing_ap))
    # and the pack actually surfaces at least one real anti-pattern path
    surfaced = [p for p in ap_paths if p in text]
    check("pack surfaces at least one real anti-pattern path", bool(surfaced) or not ap_paths,
          str(ap_paths))

    print(f"\n{'PASS — check_standards_review_pack: the review pack exists, carries every section, and references only real catalogs, proofs, anti-patterns, and an active generator template.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: standards-review-pack.md references real catalogs + proofs.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
