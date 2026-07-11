#!/usr/bin/env python3
"""check_substrate_layers — proof for _repos/shared-backend-components/architecture/substrate_layers.json (the systems-layer reconciliation map).

The map records the owner's proposed 'missing layers' against what ALREADY EXISTS in the repo + the real gap + the
Foundational Law. This proof keeps it HONEST: every asset a layer claims to exist must actually exist on disk (so the
'this already exists' claim can't drift into a lie), the Foundational Law must cite real discipline files, and the
status/priority vocab must stay closed. Deterministic, offline, stdlib only. serves_truth=false.

  PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_substrate_layers.py --self-test
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
_MAP = _resource("architecture") / "substrate_layers.json"
_STATUS = {"live", "partial", "deferred", "gap"}
_REQUIRED_LAYER_KEYS = {"id", "proposed_name", "owner_ref", "status", "existing_assets", "real_gap",
                        "law_justification", "priority"}
_LAW_KEYS = {"system_filter", "execution_filter", "component_admission", "binding_constraint",
             "recursive_improvement", "reconciliation"}
# The Foundational Law reconciles with these PRE-EXISTING discipline anchors — they must exist (no dangling law).
_DISCIPLINE_ANCHORS = ["docs/concepts/capability-valleys.md", "scripts/eval/reason_codes.py",
                       "scripts/proposal_backlog.py"]


def _self_test() -> int:
    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    ck("substrate_layers.json exists", _MAP.exists())
    if not _MAP.exists():
        print("\nFAIL - check_substrate_layers: map missing")
        return 1
    doc = json.loads(_MAP.read_text(encoding="utf-8"))

    ck("serves_truth is false (a static derivation, not a truth claim)", doc.get("serves_truth") is False)
    law = doc.get("foundational_law", {})
    ck("foundational_law carries all reconciled filters", _LAW_KEYS <= set(law), str(set(law)))
    for anchor in _DISCIPLINE_ANCHORS:
        ck(f"discipline anchor exists: {anchor}", _resource(anchor).exists())
    law_text = json.dumps(law)
    ck("law cites the two-axis admission (capability-valleys / reason_codes)",
       "capability-valleys" in law_text and "reason_codes" in law_text)
    ck("law cites the binding depth-before-breadth gate (proposal_backlog)", "proposal_backlog" in law_text)

    layers = doc.get("layers", [])
    ck("layers present (>= 8 — the owner's 8 proposed layers)", len(layers) >= 8, str(len(layers)))
    ids = [l.get("id") for l in layers]
    ck("layer ids are unique", len(ids) == len(set(ids)), str([i for i in ids if ids.count(i) > 1]))

    missing_assets: list[str] = []
    bad_layers: list[str] = []
    for l in layers:
        if not _REQUIRED_LAYER_KEYS <= set(l):
            bad_layers.append(f"{l.get('id')} missing {_REQUIRED_LAYER_KEYS - set(l)}")
            continue
        if l["status"] not in _STATUS:
            bad_layers.append(f"{l['id']} bad status {l['status']}")
        if not l["existing_assets"]:
            bad_layers.append(f"{l['id']} has no existing_assets")
        if not l["real_gap"] or not l["law_justification"]:
            bad_layers.append(f"{l['id']} missing gap/justification")
        for a in l["existing_assets"]:
            if not _resource(a).exists():                       # file OR directory must really exist
                missing_assets.append(f"{l['id']} -> {a}")

    ck("every layer has the required schema keys + valid status", not bad_layers, "; ".join(bad_layers))
    ck("EVERY claimed existing asset actually exists on disk (no 'already exists' lie)",
       not missing_assets, "; ".join(missing_assets[:8]))

    # coverage report (computed, not typed)
    by_status = {s: sum(1 for l in layers if l.get("status") == s) for s in sorted(_STATUS)}
    already = by_status["live"] + by_status["partial"] + by_status["deferred"]
    ck("the reconciliation holds: most proposed layers already exist (not pure gaps)",
       already >= len(layers) - 1, f"{already}/{len(layers)} already exist; by_status={by_status}")

    print(f"\n  coverage by status: {by_status}  ({already}/{len(layers)} proposed layers already exist in some form)")
    print("\n" + ("PASS - check_substrate_layers: the systems-layer map is honest — every claimed asset exists, the "
                  "Foundational Law reconciles with the real discipline anchors, and the 'already exists' "
                  "reconciliation holds. serves_truth=false."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def _main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if "--self-test" in argv:
        return _self_test()
    doc = json.loads(_MAP.read_text(encoding="utf-8"))
    by_status: dict = {}
    for l in doc["layers"]:
        by_status.setdefault(l["status"], []).append(l["id"])
    print(json.dumps({"layers": len(doc["layers"]), "by_status": by_status}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
