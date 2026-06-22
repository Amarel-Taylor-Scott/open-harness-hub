#!/usr/bin/env python3
"""check_adapter_layers — the swappable-component coverage map is accurate (wired layers have a real port; gaps honest).

The single source `architecture/adapter_layers.json` tracks which swappable LAYERS sit behind an agnostic port/wrapper
(populated from a registry, drop-in tested) vs which are GAPS. This proves: every WIRED layer's port_module file exists;
gaps have no port_module; the flagship drop-in-tested layers (llm, browser) are marked; coverage is computed (no magic).
The 'adapters' flywheel consumes this to file gap proposals. serves_truth=false.

  python3 scripts/check_adapter_layers.py --self-test
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
REGISTRY = REPO / "architecture" / "adapter_layers.json"


def coverage() -> dict:
    layers = json.loads(REGISTRY.read_text(encoding="utf-8")).get("layers", [])
    wired = [L for L in layers if L.get("status") == "wired"]
    gaps = [L for L in layers if L.get("status") == "gap"]
    tested = [L for L in wired if L.get("drop_in_tested")]
    return {"total": len(layers), "wired": len(wired), "gaps": [L["layer"] for L in gaps],
            "drop_in_tested": [L["layer"] for L in tested], "serves_truth": False}


def _self_test() -> int:
    layers = json.loads(REGISTRY.read_text(encoding="utf-8")).get("layers", [])
    cov = coverage()
    fails = []
    def ck(n, ok, d=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok: fails.append(n)

    ck(f"adapter-layers registry loads ({cov['total']} layers: {cov['wired']} wired, {len(cov['gaps'])} gaps)", cov["total"] >= 10)
    missing = [L["layer"] for L in layers if L.get("status") == "wired"
               and not (L.get("port_module") and (REPO / L["port_module"]).exists())]
    ck("every WIRED layer's port_module file actually exists (no phantom ports)", not missing, str(missing))
    bad_gap = [L["layer"] for L in layers if L.get("status") == "gap" and L.get("port_module")]
    ck("every GAP layer is honest (no port_module) — not falsely claimed wired", not bad_gap, str(bad_gap))
    ck("the flagship layers are drop-in tested (llm + browser + ocr)", {"llm", "browser", "ocr_document_parse"} <= set(cov["drop_in_tested"]))
    ck("remaining gaps are surfaced honestly (reranker/tts-stt — for the agent to wrap)",
       "reranker" in cov["gaps"] and "tts_stt_generation" in cov["gaps"])
    ck("status is one of wired|gap; serves_truth=false", all(L.get("status") in ("wired", "gap") for L in layers)
       and cov["serves_truth"] is False)

    print("\n" + (f"PASS - check_adapter_layers: {cov['wired']}/{cov['total']} swappable layers wired behind a real port "
                  f"(drop-in tested: {cov['drop_in_tested']}); gaps honest ({cov['gaps']}); the adapters flywheel files "
                  "them for wrapping. serves_truth=false." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(_self_test() if "--self-test" in sys.argv else _self_test())
