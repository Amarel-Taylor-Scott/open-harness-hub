#!/usr/bin/env python3
"""primitive_multi_model_store — populate a per-model embedding store for EVERY embedding model (build out, do not prune).

Owner (2026-07-10): "build out ALL possible mechanisms, paths, embedding models, THEN we tune and weight things in the
real world with real prompts. Controlled lab tests provide direction, NOT evidence to stop building other methods."

So this builds a SEPARATE embedding store PER model — every backend in `embedder_zoo` becomes a live lane, kept in its
own named space (never averaged across models). One vector per card (the `card_embed_text` surface) so strong models
(EmbeddingGemma / BGE-large / jina-code / GTE / mxbai / arctic / nomic) are feasible over a tier; model2vec's rich
90-facet store stays the cheap recall lane. At serve time the retrieval graph queries the model2vec facet store for
RECALL, then any subset of these strong-model lanes RERANK / RRF-fuse the shortlist — and which lanes/weights win is
decided by the REAL-WORLD usage ledger + `linker_scoring_zoo.train_weights`, not a lab micro-benchmark.

Stores live at `dist/primitive-model-stores/<backend>/` (matrix.npy + ids.json + manifest.json). Resumable per model
(skip if the manifest already covers the tier). A coverage report shows, per model, which tier is populated — the
proof that we are building EVERY lane, not stopping at one. serves_truth=false.

    PYTHONPATH=. python3 scripts/primitive_multi_model_store.py --report
    PYTHONPATH=. python3 scripts/primitive_multi_model_store.py --build fastembed_bge_large --tier verified
    PYTHONPATH=. python3 scripts/primitive_multi_model_store.py --self-test
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Callable, Optional

_HERE = Path(__file__).resolve()
_REPO = _HERE.parent.parent
for _p in (str(_REPO), str(_REPO / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    import numpy as np
except Exception:  # pragma: no cover
    np = None  # type: ignore

_EDGE = _REPO / "data" / "dev-intel" / "aidevobserver_edge_foundry"
_STORE_ROOT = _REPO / "dist" / "primitive-model-stores"

#: TIERS — which cards get strong-model embeddings. 'verified' + 'minted' are the feasible hot tier for slow models;
#: 'all' is the full 540K (fast models / cloud). Config, not a hardcoded subset — extend by adding a tier here.
TIERS: dict[str, list[str]] = {
    "verified": ["verified_factory_primitive_cards.jsonl"],
    "minted": ["minted_ml_kaggle_pack_cards.jsonl", "minted_http_pack_cards.jsonl", "minted_validation_pack_cards.jsonl",
               "minted_collections_pack_cards.jsonl", "minted_text_pack_cards.jsonl", "minted_vertical_pack_cards.jsonl"],
    "hot": ["verified_factory_primitive_cards.jsonl", "minted_ml_kaggle_pack_cards.jsonl", "minted_http_pack_cards.jsonl",
            "minted_validation_pack_cards.jsonl", "minted_collections_pack_cards.jsonl", "minted_text_pack_cards.jsonl",
            "minted_vertical_pack_cards.jsonl"],
    "all": ["verified_factory_primitive_cards.jsonl", "primitive_edge_cards.jsonl", "minted_ml_kaggle_pack_cards.jsonl",
            "minted_http_pack_cards.jsonl", "minted_validation_pack_cards.jsonl", "minted_collections_pack_cards.jsonl",
            "minted_text_pack_cards.jsonl", "minted_vertical_pack_cards.jsonl", "minted_synthesized_working_cards.jsonl"],
}


def all_models() -> list[str]:
    """Every embedding backend — all are lanes to build (no pruning)."""
    from scripts import embedder_zoo as _z  # noqa: PLC0415
    return list(_z.EMBEDDER_BACKENDS)


def _load_tier(tier: str) -> list[dict[str, Any]]:
    out = []
    for fn in TIERS.get(tier, TIERS["verified"]):
        p = _EDGE / fn
        if p.exists():
            for line in p.read_text().splitlines():
                if line.strip():
                    try:
                        out.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    return out


def store_dir(model: str) -> Path:
    return _STORE_ROOT / model


def build_model_store(model: str, *, tier: str = "verified", cards: Optional[list] = None,
                      embed: Optional[Callable] = None, resume: bool = True) -> dict[str, Any]:
    """Embed one vector per card (card_embed_text) under `model`; persist matrix.npy + ids.json + manifest."""
    if np is None:
        raise RuntimeError("numpy required")
    from scripts import capability_embedding as _ce  # noqa: PLC0415
    from scripts import linker_rerank as _rr  # noqa: PLC0415  reuse the batch embedder
    cards = cards if cards is not None else _load_tier(tier)
    out = store_dir(model)
    man = out / "manifest.json"
    if resume and man.exists():
        try:
            m = json.loads(man.read_text())
            if m.get("n_cards") == len(cards) and m.get("tier") == tier:
                return {**m, "skipped": True}
        except Exception:  # noqa: BLE001
            pass
    out.mkdir(parents=True, exist_ok=True)
    texts = [_ce.card_embed_text(c) or str(c.get("title") or "") for c in cards]
    ids = [c.get("primitive_id") for c in cards]
    embed = embed or (lambda t, mm: __import__("scripts.embedder_zoo", fromlist=["embed"]).embed(t, mm))
    mat = _rr._batch_embed(texts, model, embed)  # batched, L2-normalized
    np.save(out / "matrix.npy", mat)
    (out / "ids.json").write_text(json.dumps(ids))
    manifest = {"model": model, "tier": tier, "n_cards": len(cards), "dim": int(mat.shape[1]) if mat.size else 0,
                "candidate": True, "serves_truth": False}
    man.write_text(json.dumps(manifest, indent=2, sort_keys=True))
    return {**manifest, "skipped": False}


def coverage_report() -> dict[str, Any]:
    """Per-model lane status — which models are populated, over which tier. The proof we build EVERY lane."""
    lanes = {}
    for model in all_models():
        man = store_dir(model) / "manifest.json"
        if man.exists():
            try:
                lanes[model] = json.loads(man.read_text())
            except Exception:  # noqa: BLE001
                lanes[model] = {"status": "corrupt"}
        else:
            lanes[model] = {"status": "not_built"}
    built = [m for m, v in lanes.items() if v.get("n_cards")]
    return {"models_total": len(lanes), "models_built": len(built), "built": built,
            "tiers_available": list(TIERS), "lanes": lanes, "serves_truth": False}


def _self_test() -> int:
    checks: list[tuple[str, bool, str]] = []
    if np is None:
        print("FAIL - primitive_multi_model_store: numpy required"); return 1
    import tempfile

    cards = [{"primitive_id": f"p:{i}", "title": f"prim {i}", "blackbox": f"does thing {i}",
              "input_edge": "A", "output_edge": "B"} for i in range(8)]
    # deterministic offline embed stub (no model download)
    stub = lambda t, m: [float(len(t) % 5), float(sum(map(ord, t[:3])) % 7), 1.0]

    with tempfile.TemporaryDirectory() as td:
        global _STORE_ROOT
        old = _STORE_ROOT
        _STORE_ROOT = Path(td)
        try:
            r = build_model_store("proxy_crc32", cards=cards, tier="verified", embed=stub, resume=False)
            checks.append((f"builds a per-model store ({r['n_cards']} cards, dim {r['dim']})",
                           r["n_cards"] == 8 and (store_dir("proxy_crc32") / "matrix.npy").exists(), json.dumps(r)))
            # resume: second call skips
            r2 = build_model_store("proxy_crc32", cards=cards, tier="verified", embed=stub, resume=True)
            checks.append(("resume skips an already-built lane", r2.get("skipped") is True, ""))
            # every model is a candidate lane (no pruning)
            checks.append((f"all {len(all_models())} embedding backends are lanes to build",
                           len(all_models()) >= 15, str(len(all_models()))))
            rep = coverage_report()
            checks.append((f"coverage report shows built vs not_built ({rep['models_built']}/{rep['models_total']})",
                           rep["models_built"] >= 1 and "proxy_crc32" in rep["built"], ""))
        finally:
            _STORE_ROOT = old

    ok = all(c[1] for c in checks)
    print(f"{'PASS' if ok else 'FAIL'} - primitive_multi_model_store: per-model card-embedding lanes for EVERY "
          f"backend ({len(all_models())} models), resumable, tiered, coverage-reported. Build out, don't prune. serves_truth=false")
    for name, passed, detail in checks:
        print(f"  [{'ok' if passed else 'XX'}] {name}" + (f"  ({detail})" if not passed else ""))
    return 0 if ok else 1


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Build a per-model embedding store for EVERY model (build out, do not prune).")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--report", action="store_true", help="per-model lane coverage")
    ap.add_argument("--build", default=None, help="backend to build a store for")
    ap.add_argument("--tier", default="verified", help=f"card tier ({list(TIERS)})")
    ap.add_argument("--all-fast", action="store_true", help="build stores for all AVAILABLE fast (non-api) models over the tier")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.report:
        print(json.dumps(coverage_report(), indent=2))
        return 0
    if args.build:
        print(json.dumps(build_model_store(args.build, tier=args.tier), indent=2))
        return 0
    if args.all_fast:
        from scripts import embedder_zoo as _z
        done = {}
        for m in all_models():
            spec = _z.EMBEDDER_BACKENDS[m]
            if spec.get("kind") == "api_local":
                continue  # slow endpoint models built separately
            try:
                if _z.backend_available(m):
                    done[m] = build_model_store(m, tier=args.tier)
            except Exception as e:  # noqa: BLE001
                done[m] = {"error": str(e)}
        print(json.dumps({"built": {m: v.get("n_cards") for m, v in done.items()}}, indent=2))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
