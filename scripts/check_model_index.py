#!/usr/bin/env python3
"""check_model_index — proof for the unified, freshness-governed model index: pick the best + cheapest
still-effective model, but ONLY from FRESH entries. Validates the index shape (local models carry a download
location, hosted models carry a live endpoint, costs are numeric), the selector correctness (cheapest fresh within
a quality floor), and — the wedge — that stale model facts are HELD OUT and never selected until re-verified.

CLI: PYTHONPATH=. python3 scripts/check_model_index.py --self-test
"""
from __future__ import annotations

import os
import sys

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _R not in sys.path:
        sys.path.insert(0, _R)

from src.teleon.inference.model_index import (
    STATUS_FRESH, apply_staleness, load_index, mark_stale, resync, select_best,
)

_MID, _FRONTIER = 2, 4  # quality_rank floors


def _self_test() -> int:
    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    idx = load_index()
    ck("index loads with >= 8 models incl. local-weight entries", len(idx) >= 8
       and any(e["kind"] == "local_weights" for e in idx))
    req = {"model_id", "provider", "kind", "cost_per_mtok_in", "cost_per_mtok_out", "quality_tier",
           "quality_rank", "live_endpoint", "download_location", "freshness"}
    ck("every entry carries cost + endpoint + download_location + quality + freshness",
       all(req <= set(e) for e in idx), str([e["model_id"] for e in idx if not req <= set(e)]))
    ck("local-weight models carry a download_location (the owner's ask)",
       all(e["download_location"] for e in idx if e["kind"] == "local_weights"))
    ck("hosted models carry a live endpoint", all(e["live_endpoint"] for e in idx if e["kind"] == "hosted_api"))
    ck("costs are numeric and non-negative",
       all(isinstance(e["cost_per_mtok_out"], (int, float)) and e["cost_per_mtok_out"] >= 0 for e in idx))
    ck("nothing in the index serves truth (facts are candidate-until-verified)",
       all(e["serves_truth"] is False for e in idx))

    # selector: cheapest FRESH hosted model meeting a mid quality floor → deepseek; frontier → o3
    pick_mid = select_best(idx, quality_floor_rank=_MID, kinds=("hosted_api",))
    ck("selects the cheapest fresh hosted model at the mid quality floor (deepseek-v4-flash)",
       pick_mid["picked"] == "deepseek-v4-flash", str(pick_mid))
    pick_frontier = select_best(idx, quality_floor_rank=_FRONTIER, kinds=("hosted_api",))
    _fpool = [e for e in idx if e["kind"] == "hosted_api" and e["quality_rank"] >= _FRONTIER and e["freshness"]["status"] == STATUS_FRESH]
    _fpicked = next(e for e in idx if e["model_id"] == pick_frontier["picked"])
    ck("selects the cheapest-cost fresh FRONTIER hosted model (whichever is currently cheapest)",
       _fpicked["quality_rank"] >= _FRONTIER and _fpicked["cost_per_mtok_out"] == min(e["cost_per_mtok_out"] for e in _fpool),
       str(pick_frontier))
    pick_local = select_best(idx, quality_floor_rank=_MID, prefer_local=True)
    ck("prefer_local picks a 0-cost local model, highest quality on the cost tie (qwen3)",
       pick_local["picked"] == "qwen3-next-80b" and pick_local["cost_per_mtok_out"] == 0.0, str(pick_local))
    ck("the pick carries its endpoint + download location (everything to run it)",
       pick_local["download_location"] and select_best(idx, kinds=("hosted_api",))["endpoint"])

    # FRESHNESS GOVERNANCE (the wedge): a stale model is HELD OUT and never selected
    staled = mark_stale(idx, "deepseek-v4-flash")
    pick_after = select_best(staled, quality_floor_rank=_MID, kinds=("hosted_api",))
    _spool = [e for e in staled if e["kind"] == "hosted_api" and e["quality_rank"] >= _MID and e["freshness"]["status"] == STATUS_FRESH]
    _spicked = next(e for e in staled if e["model_id"] == pick_after["picked"])
    ck("a CDC-staled model is excluded; selection falls back to the next cheapest FRESH model",
       "deepseek-v4-flash" in pick_after["excluded_stale"] and pick_after["picked"] != "deepseek-v4-flash"
       and _spicked["cost_per_mtok_out"] == min(e["cost_per_mtok_out"] for e in _spool), str(pick_after))
    pick_resynced = select_best(resync(staled, "deepseek-v4-flash", now="2026-06-20"), quality_floor_rank=_MID, kinds=("hosted_api",))
    ck("re-verifying makes it selectable again (back to deepseek)", pick_resynced["picked"] == "deepseek-v4-flash")

    # kept-up-to-date: age out by the volatility-matched cadence — high-volatility hosted facts go stale fast
    aged = apply_staleness(idx, now="2026-07-01")  # 11 days later
    hosted_fresh = [e["model_id"] for e in aged if e["kind"] == "hosted_api" and e["freshness"]["status"] == STATUS_FRESH]
    local_fresh = [e["model_id"] for e in aged if e["kind"] == "local_weights" and e["freshness"]["status"] == STATUS_FRESH]
    ck("high-volatility hosted facts age out (held out) after the cadence; low-volatility local facts stay fresh",
       not hosted_fresh and local_fresh, f"hosted_fresh={hosted_fresh}")
    ck("after aging, hosted selection is empty (refuse stale) but local still works",
       select_best(aged, kinds=("hosted_api",))["picked"] is None and select_best(aged, prefer_local=True)["picked"])

    ck("a selection never serves truth", pick_mid["serves_truth"] is False)
    ck("deterministic", select_best(load_index(), quality_floor_rank=_MID, kinds=("hosted_api",)) == pick_mid)

    print("\n" + (f"PASS - check_model_index: {len(idx)} models (cost + live endpoint + download location + quality + "
                  f"freshness); selector picks the cheapest FRESH model within a quality floor (best+cheapest+"
                  f"effective); stale model facts are HELD OUT and never selected until re-verified (kept-up-to-date "
                  f"is the wedge). Never serves truth."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def _main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--self-test" in argv:
        return _self_test()
    print("usage: check_model_index.py --self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
