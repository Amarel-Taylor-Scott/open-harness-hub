#!/usr/bin/env python3
"""scripts.check_verified_candidates_registry_load — gate the verified→registry bridge.

Asserts the loader (_repos/shared-backend-components/scripts/load_verified_candidates_into_registry.py) still produces registry-consumable cards:
mapping self-test passes, the output file is registered in registry_search._edge_foundry_paths(), and (when the
pack exists on disk) its cards carry the candidate boundary, a dict-shaped source_ref with no local path, and the
verified-factory id namespace. Offline; reads only, mutates nothing.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.load_verified_candidates_into_registry import (  # noqa: E402
    CARD_ID_PREFIX,
    OUTPUT_PATH,
    self_test as loader_self_test,
)


def _fail(msg: str) -> None:
    raise AssertionError(msg)


def self_test() -> dict:
    # 1. loader mapping self-test must pass
    if loader_self_test() != 0:
        _fail("loader mapping self-test failed")

    # 2. output path must be registered in the searchable edge-foundry path list
    from src.teleon.observer import registry_search as rs
    registered = {str(p) for p in rs._edge_foundry_paths()}
    if str(OUTPUT_PATH.resolve()) not in registered and str(OUTPUT_PATH) not in registered:
        _fail(f"verified-factory pack {OUTPUT_PATH} is NOT registered in registry_search._edge_foundry_paths()")

    # 3. if the pack is materialized, spot-check its cards + confirm search sees them
    pack_cards = 0
    if OUTPUT_PATH.exists():
        lines = [ln for ln in OUTPUT_PATH.read_text(encoding="utf-8").splitlines() if ln.strip()]
        pack_cards = len(lines)
        for ln in lines[:200]:
            card = json.loads(ln)
            if card.get("candidate") is not True or card.get("serves_truth") is not False:
                _fail("a verified-factory card violates the candidate boundary")
            if not str(card.get("primitive_id", "")).startswith(CARD_ID_PREFIX):
                _fail("a verified-factory card is missing the prim:vf: namespace")
            sref = card.get("source_ref")
            if not isinstance(sref, dict) or sref.get("path"):
                _fail("source_ref must be a dict with an empty path (no local-path leak)")
        # search integration: the loaded cards must be countable through the registry
        total = rs.load_edge_foundry_primitive_count()
        vf_visible = sum(
            1 for r in rs.load_edge_foundry_primitives()
            if str(r.get("primitive_id", "")).startswith(CARD_ID_PREFIX)
        )
        if vf_visible != pack_cards:
            _fail(f"registry sees {vf_visible} verified-factory cards but the pack has {pack_cards}")
        if total < vf_visible:
            _fail("edge-foundry total is smaller than the verified-factory subset")

    return {
        "check": "verified_candidates_registry_load",
        "registered_in_search_paths": True,
        "pack_cards": pack_cards,
        "candidate": True,
        "serves_truth": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if not args.self_test:
        parser.error("expected --self-test")
    result = self_test()
    print(json.dumps(result, indent=2, sort_keys=True))
    print("PASS - verified_candidates_registry_load: loader maps + pack is registered + cards are boundary-safe "
          "and search-visible.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
