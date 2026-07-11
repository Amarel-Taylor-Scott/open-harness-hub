#!/usr/bin/env python3
"""check_tool_registry — the deterministic-replacement registry (the moat) is real, governed, and license-disciplined.

Proves: every tool maps to a declared tool-plane; ids are unique; license_class/vendorable are DERIVED from the single
source (_repos/openhubforai/backend/src/openhubforai/licenses.classify_license), never hand-stored; COPYLEFT/NON-COMMERCIAL/UNSTATED licenses are
technique-only (not vendorable — spot-checked on real AGPL/GPL entries); the planes with a dedicated registry
(ocr/browser/llm) are intentionally NOT duplicated here; every populated plane has real coverage. serves_truth=false
(discovery≠trust — candidates, not adopted). Prints per-plane coverage + the vendorable vs technique-only split.

  python3 _repos/shared-backend-components/scripts/check_tool_registry.py --self-test
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from src.openhubforai.licenses import classify_license

REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource

# Planes that already have a dedicated, populated registry — must NOT be re-listed here (single-source / no duplication).
_DEDICATED = {"ocr": "ocr_provider_registry.json", "browser": "web_browsing_stack_registry.json", "llm": "model_index"}
_MIN_PER_PLANE = 3
_MIN_TOTAL = 80


def _load(name):
    return json.loads((_resource("architecture") / name).read_text(encoding="utf-8"))


def _self_test() -> int:
    reg = _load("tool_registry.json")
    tools = reg["tools"]
    planes = {p["plane"] for p in _load("tool_planes.json")["planes"]}
    fails = []
    def ck(n, ok, d=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok: fails.append(n)

    ck(f"registry significantly populated ({len(tools)} tools >= {_MIN_TOTAL})", len(tools) >= _MIN_TOTAL)
    ids = [t["id"] for t in tools]
    dups = sorted({i for i in ids if ids.count(i) > 1})
    ck("tool ids unique", not dups, str(dups))
    bad_plane = sorted({t["plane"] for t in tools if t["plane"] not in planes})
    ck("every tool maps to a declared tool-plane", not bad_plane, str(bad_plane))
    dup_dedicated = sorted({t["plane"] for t in tools if t["plane"] in _DEDICATED})
    ck("no duplication of planes that own a dedicated registry (ocr/browser/llm)", not dup_dedicated, str(dup_dedicated))
    ck("no tool stores vendorable/license_class (derived from the single-source classifier, never hand-typed)",
       not any(("vendorable" in t or "license_class" in t) for t in tools))

    # derive license posture from the single source
    derived = {t["id"]: classify_license(t.get("license")) for t in tools}
    no_lic = [t["id"] for t in tools if not t.get("license")]
    ck("every tool declares a license string", not no_lic, str(no_lic))
    # discipline spot-check: known copyleft entries MUST come back not-vendorable
    for tid in ("pymupdf", "ultralytics_yolo", "comfyui", "searxng"):
        if tid in derived:
            ck(f"copyleft entry {tid} flagged technique-only (not vendorable)", derived[tid][1] is False, str(derived[tid]))
    # and a known permissive one IS vendorable
    ck("permissive entry (faiss) is vendorable", derived.get("faiss", (None, False))[1] is True)
    # invariant: anything marked vendorable is permissive-class
    leaks = [tid for tid, (cls, vend) in derived.items() if vend and cls != "permissive"]
    ck("vendorable ⊆ permissive (no copyleft/noncommercial/unstated leaks into vendorable)", not leaks, str(leaks))

    per_plane = Counter(t["plane"] for t in tools)
    thin = sorted(p for p, c in per_plane.items() if c < _MIN_PER_PLANE)
    ck(f"every populated plane has >= {_MIN_PER_PLANE} candidate tools", not thin, str(thin))
    ck("serves_truth=false (candidates; discovery≠trust)", reg.get("serves_truth") is False)

    vendorable = sum(1 for _, (_, v) in derived.items() if v)
    print(f"\n  coverage ({len(per_plane)} planes populated here; ocr/browser/llm via dedicated registries):")
    for p in sorted(per_plane):
        print(f"    {p:24s} {per_plane[p]:>2d}")
    print(f"  posture: {vendorable} vendorable (permissive) · {len(tools) - vendorable} technique-only/service "
          "(copyleft/non-commercial/unstated — study clean-room or use as a hosted-service lane, never vendor the code)")
    print("\n" + (f"PASS - check_tool_registry: {len(tools)} real deterministic-replacement tools across {len(per_plane)} "
                  "planes, license-disciplined + governed. A new tool drops in as one row. serves_truth=false."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(_self_test())
