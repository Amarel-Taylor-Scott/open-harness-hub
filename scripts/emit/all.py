#!/usr/bin/env python3
"""Run every emitter in scripts/emit/ in sequence.

Used by CI (.github/workflows/emit.yml) and by humans when they want to
refresh dist/ after a catalog change.
"""
from __future__ import annotations

import importlib
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

EMITTERS = [
    "scripts.emit.croissant",
    "scripts.emit.mcp_server",
    "scripts.emit.agent_skill",
    "scripts.emit.hf_model_card",
    "scripts.emit.hf_dataset_card",
    "scripts.emit.hf_space",
    "scripts.emit.lm_eval_harness",
    "scripts.emit.promptfoo",
    "scripts.emit.cyclonedx_ml",
    "scripts.emit.openlineage",
    "scripts.emit.c2pa",
    "scripts.emit.eu_ai_act_annex_iv",
    "scripts.emit.spdx_3",
]


def main() -> int:
    for mod in EMITTERS:
        print(f"\n=== {mod} ===")
        t0 = time.monotonic()
        m = importlib.import_module(mod)
        rc = m.main()
        print(f"  ({time.monotonic() - t0:.2f}s, rc={rc})")
        if rc != 0:
            return rc
    print("\nall emitters complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
