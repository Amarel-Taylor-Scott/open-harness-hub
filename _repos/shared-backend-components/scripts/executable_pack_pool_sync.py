#!/usr/bin/env python3
"""scripts.executable_pack_pool_sync — the missing wire between the EXECUTABLE PACKS and the DATABASE
(owner question 2026-07-07: "are you adding all of these primitives to the database?" — before this module,
honestly: no). Collects all_cards() from every registered pack (string standardization, UI design, party
name, settings control plane, dummy-data detection — a new pack = one row here), appends NEW cards
(dedupe by primitive_id, append-only, never rewrites history) into the ``executable_pack_cards.jsonl`` pool,
which primitive_database._POOLS ingests on the next build — from there the multi-index blocks/columns/
semantic stores index them like every other primitive. candidate=true, serves_truth=false.

    python3 scripts/executable_pack_pool_sync.py --self-test
    python3 scripts/executable_pack_pool_sync.py --run
"""
from __future__ import annotations

import sys
from pathlib import Path

_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots, resource  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import json  # noqa: E402
from typing import Any, Optional  # noqa: E402

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
#: the pack registry: a new executable pack = one module name here (each must expose all_cards())
PACK_MODULES: tuple[str, ...] = (
    "scripts.string_standardization_primitives",
    "scripts.scalar_standardization_primitives",
    "scripts.ui_design_primitives",
    "scripts.party_name_primitives",
    "scripts.primitive_settings_control_plane",
    "scripts.dummy_data_detection_primitives",
    "scripts.primitive_recipe_templates",
    "scripts.quantity_money_primitives",
    "scripts.cross_table_discovery_primitives",
    "scripts.temporal_cdc_primitives",
    "scripts.feature_comparison_primitives",
    "scripts.similarity_typo_primitives",
    "scripts.matching_scorecard_primitives",
)
POOL_FILENAME = "executable_pack_cards.jsonl"


def pool_path() -> Path:
    return resource("data") / "dev-intel" / "aidevobserver_edge_foundry" / POOL_FILENAME


def collect_pack_cards() -> list[dict[str, Any]]:
    """Every registered pack's cards, each promoted to a FORMAL PRIMITIVE PACKAGE (additive: the contract
    only appends verifier/permission-manifest/determinism/provenance/lifecycle fields; primitive_id + body
    are byte-identical). The pool therefore carries the governance/security metadata the supply chain needs."""
    from scripts.primitive_package_contract import formalize_card  # noqa: PLC0415  reuse-first, single source
    cards: list[dict[str, Any]] = []
    for mod_name in PACK_MODULES:
        mod = __import__(mod_name, fromlist=["all_cards"])
        for c in mod.all_cards():
            cards.append(formalize_card({**c, "pack_module": mod_name, "pool": "executable_packs"}))
    return cards


def sync(target: Optional[Path] = None) -> dict[str, Any]:
    target = target or pool_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    existing: set[str] = set()
    if target.exists():
        for line in target.read_text().splitlines():
            if line:
                existing.add(str(json.loads(line).get("primitive_id")))
    cards = collect_pack_cards()
    fresh = [c for c in cards if str(c["primitive_id"]) not in existing]
    with target.open("a") as f:
        for c in fresh:
            f.write(json.dumps(c, sort_keys=True) + "\n")
    return {"record_type": "executable_pack_pool_sync_receipt", "packs": len(PACK_MODULES),
            "cards_seen": len(cards), "appended": len(fresh), "already_on_file": len(existing),
            "pool_path": str(target), **BOUNDARY}


def _self_test() -> int:
    import tempfile  # noqa: PLC0415
    checks: list[tuple[str, bool]] = []
    cards = collect_pack_cards()
    checks.append(("collects cards from every registered pack with executable bodies + pack provenance",
                   len(cards) >= 45 and all(c.get("executable_body") for c in cards)
                   and {c["pack_module"] for c in cards} == set(PACK_MODULES)))
    checks.append(("ids unique across packs (the canonical_id law holds)",
                   len({c["primitive_id"] for c in cards}) == len(cards)))
    with tempfile.TemporaryDirectory() as td:
        t = Path(td) / "pool.jsonl"
        r1 = sync(t)
        r2 = sync(t)
        checks.append(("sync appends once then dedupes (append-only, idempotent)",
                       r1["appended"] == len(cards) and r2["appended"] == 0
                       and len(t.read_text().splitlines()) == len(cards)))
    checks.append(("boundary", all(c.get("serves_truth") is False for c in cards)))
    failed = [n for n, ok in checks if not ok]
    for n, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print(f"\nPASS - executable_pack_pool_sync: {len(PACK_MODULES)} packs -> the executable_packs POOL "
          f"(database-ingested); a new pack is one registry row. serves_truth=false.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--run", action="store_true")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.run:
        print(json.dumps(sync(), indent=2, sort_keys=True))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
