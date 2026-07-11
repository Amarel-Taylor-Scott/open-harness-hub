#!/usr/bin/env python3
"""check_substrate_backed_descent — proof that the model REGISTRY is load-bearing for the descent.

The descent's model_downgrade used to use a GUESSED constant (cheap_factor ~ 0.1) and named no model, so the model
registry was decorative — deepening it changed nothing. Now catalog_descent selects the cheapest FRESH model from
_repos/shared-backend-components/architecture/model_index.json (via substrate_selector, reusing the model-index selector) and records WHICH model in
each attempt's substrate_ref. This proves:

  1. LINEAGE   — every model_downgrade attempt names a real model that exists in the model registry.
  2. SOURCED   — the downgrade factor is the registry's real cheapest-fresh/frontier ratio, not a guess.
  3. THESIS    — deepening the model registry MEASURABLY increases the descent's saving (thin < deep < deepest),
                 over the SAME catalog. This is "for Teleon to work, the registries must be load-bearing", executable.
  4. LOSSLESS  — the replaced (frontier) model is preserved in the registry; the attempt keeps a rollback target.

CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_substrate_backed_descent.py --self-test
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _R not in sys.path:
        sys.path.insert(0, _R)

from src.teleon.evolution import catalog_descent, substrate_selector
from src.teleon.evolution.descent_attempt_store import DescentAttemptStore
from src.teleon.inference import model_index

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
_REAL_INDEX = _resource("architecture") / "model_index.json"


def _entry(model_id: str, cost_out: float, *, rank: int = 3, kind: str = "hosted_api") -> dict:
    """A minimal model-index entry with the fields the selector reads (fresh by construction)."""
    return {"model_id": model_id, "provider": "test", "kind": kind, "cost_per_mtok_in": cost_out / 2,
            "cost_per_mtok_out": cost_out, "quality_tier": "test", "quality_rank": rank, "specialization": "general",
            "live_endpoint": f"https://example.test/{model_id}", "download_location": "",
            "freshness": {"last_verified": "2026-06-20", "volatility_class": "low", "status": "fresh"},
            "serves_truth": False}


def _saving_with_index(entries: list[dict], caps: list[dict], tmp: str) -> float:
    """Run the descent over ``caps`` with model_index pointed at a temp index of ``entries``; return total cost saved."""
    idx_path = os.path.join(tmp, f"idx_{len(entries)}_{hash(tuple(e['model_id'] for e in entries)) & 0xffff}.json")
    Path(idx_path).write_text(json.dumps({"entries": entries}), encoding="utf-8")
    saved = model_index._INDEX_PATH
    try:
        model_index._INDEX_PATH = Path(idx_path)
        store = DescentAttemptStore(os.path.join(tmp, os.path.basename(idx_path) + ".store.jsonl"))
        return catalog_descent.convert_catalog(store, caps)["total_cost_saved"]
    finally:
        model_index._INDEX_PATH = saved


def _self_test() -> int:
    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    caps = catalog_descent.load_catalog()
    real_models = {e["model_id"] for e in model_index.load_index()}

    # ── 1. LINEAGE: every model_downgrade attempt names a real model from the registry ──
    with tempfile.TemporaryDirectory() as d:
        store = DescentAttemptStore(os.path.join(d, "lineage.jsonl"))
        catalog_descent.convert_catalog(store, caps)
        md = [r for r in store.all() if r["strategy"] == "model_downgrade"]
        ck("there are model_downgrade attempts to check", len(md) >= 1, str(len(md)))
        refs = {r["substrate_ref"] for r in md}
        named = {ref.split("#", 1)[1] for ref in refs if "#" in ref}
        ck("every model_downgrade names a CONCRETE model from architecture/model_index.json (lineage)",
           named and named <= real_models, f"named={named} not all in registry")
        ck("an llm_to_rule attempt descends into a deterministic_rule (not a model)",
           all(r["substrate_ref"] == "deterministic_rule" for r in store.all() if r["strategy"] == "llm_to_rule"))

    # ── 2. SOURCED: the factor is the registry's real cheapest-fresh/frontier ratio (not a guess) ──
    dg = substrate_selector.model_downgrade()
    fresh = [e for e in model_index.load_index() if e["freshness"]["status"] == "fresh"]
    cheapest = min(e["cost_per_mtok_out"] for e in fresh)
    frontier = max(e["cost_per_mtok_out"] for e in fresh)
    expected = round(cheapest / frontier, 6) if frontier else 0.0
    ck("the downgrade factor is registry-derived (sourced from model_index.json)", dg["registry_derived"] is True)
    ck("the factor equals the real cheapest-fresh / frontier-fresh model-cost ratio",
       dg["factor"] == expected, f"{dg['factor']} != {expected}")
    ck("the pick + the replaced frontier are both named (substrate lineage)",
       bool(dg["picked_model"]) and bool(dg["frontier_model"]) and dg["picked_model"] in real_models)

    # ── 3. THESIS: deepening the model registry MEASURABLY increases the saving (over the SAME catalog) ──
    with tempfile.TemporaryDirectory() as d:
        thin = [_entry("frontier-x", 75.0, rank=4), _entry("workhorse-y", 15.0, rank=3)]   # only expensive models
        deep = thin + [_entry("cheap-hosted-z", 0.28, rank=2)]                              # + a cheap hosted model
        deepest = deep + [_entry("local-free-w", 0.0, rank=2, kind="local_weights")]        # + a free local model
        s_thin = _saving_with_index(thin, caps, d)
        s_deep = _saving_with_index(deep, caps, d)
        s_deepest = _saving_with_index(deepest, caps, d)
        ck("a THIN model registry already produces some saving", s_thin > 0, str(s_thin))
        ck("DEEPENING the registry with a cheaper model INCREASES the saving (registry is load-bearing)",
           s_deep > s_thin, f"deep {s_deep} !> thin {s_thin}")
        ck("deepening further (a free local model) increases the saving again",
           s_deepest > s_deep, f"deepest {s_deepest} !> deep {s_deep}")

    # ── 4. LOSSLESS: the replaced frontier model is preserved; the attempt keeps a rollback target ──
    ck("the replaced frontier model is still present in the registry (not deleted)",
       dg["frontier_model"] in real_models)
    with tempfile.TemporaryDirectory() as d:
        store = DescentAttemptStore(os.path.join(d, "lossless.jsonl"))
        catalog_descent.convert_catalog(store, caps)
        ck("every attempt keeps a rollback_target to its unbounded form (lossless)",
           all(r["rollback_target"] for r in store.all()))

    print("\n" + (f"PASS - the model registry is LOAD-BEARING for the descent: every model_downgrade names a concrete "
                  f"model from model_index.json (lineage), the downgrade factor is the registry's real "
                  f"cheapest-fresh/frontier ratio (not a guess), and DEEPENING the registry measurably increases the "
                  f"descent's saving over the same catalog (thin < deep < deepest) — losslessly (frontier preserved, "
                  f"rollback kept)." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def _main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--self-test" in argv:
        return _self_test()
    print("usage: check_substrate_backed_descent.py --self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
