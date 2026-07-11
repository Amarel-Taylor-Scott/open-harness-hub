#!/usr/bin/env python3
"""scripts.graph_autotune — SELF-TUNING for the path graph: race the ranking-relevant configs on a labelled set
(path_graph_bench), pick the CHAMPION by measured receipt, and PERSIST it as the graph's ACTIVE config — so the
default path is chosen by evidence, not hand-set, and RE-ADAPTS whenever you re-tune (new cards, new options, a
new embedder). The multi-path law's "race by receipt, keep the losers" made into a running selector.

  autotune(cards, labelled) -> race → champion → persist active_config.json → receipt (champion + full leaderboard).
  active_config()           -> the persisted champion ranking-config the serving default reads (safe fallback if
                               never tuned). Turning an option off + re-tuning simply picks a new champion.

serves_truth=false — a tuned config is a candidate default backed by a receipt, never truth.

    PYTHONPATH=. python3 scripts/graph_autotune.py --self-test
    PYTHONPATH=. python3 scripts/graph_autotune.py --tune --sample 200      # race + persist the active config
    PYTHONPATH=. python3 scripts/graph_autotune.py --active                 # show the current active config
"""
from __future__ import annotations

import sys
from pathlib import Path

# ── substrate-root bootstrap (sentinel; mirrors scripts/capability_retrieval_mcp_server.py) ──────────────────
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

from scripts import path_graph_bench as _bench  # noqa: E402  REUSE: the race + labelled set + corpus
from scripts import pipeline_path_graph as _graph  # noqa: E402  REUSE: stage/option validity

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}

_RANKING_STAGES = _bench._RANKING_STAGES  # single source: (expand, search, fuse, rerank)
#: safe fallback ranking-config when the graph has never been tuned — a valid, reasonable default (full union +
#: the production-standard RRF). Every value is asserted a real option at import/self-test.
_FALLBACK_CONFIG: dict[str, str] = {"expand": "none", "search": "all", "fuse": "rrf", "rerank": "none"}


def _default_active_path() -> Path:
    return resource("dist") / "graph-autotune" / "active_config.json"


def _valid_config(cfg: dict[str, str]) -> bool:
    """A config is valid iff each ranking stage names a real option of that stage."""
    return all(cfg.get(s) in _graph.STAGE_OPTIONS.get(s, {}) for s in _RANKING_STAGES)


def autotune(cards: list[dict[str, Any]], labelled: list[dict[str, str]], *, k: int = _bench._DEFAULT_K,
             out_path: Optional[Path] = None, persist: bool = True) -> dict[str, Any]:
    """Race every ranking-relevant config, select the champion by (nDCG, recall), and persist it as the active
    config. Returns the champion config + the full leaderboard receipt. Re-run to RE-TUNE."""
    receipt = _bench.quality_bench(cards, labelled, k=k)
    champ = receipt["champion"] or _FALLBACK_CONFIG
    config = {s: champ[s] for s in _RANKING_STAGES if s in champ} or dict(_FALLBACK_CONFIG)
    active = {"record_type": "graph_active_config", "config": config,
              "metrics": {m: champ.get(m) for m in ("recall_at_k", "mrr", "ndcg_at_k")},
              "k": k, "embed_path": receipt["embed_path"], "corpus_size": receipt["corpus_size"],
              "queries": receipt["queries"], "configs_raced": receipt["configs_raced"], **BOUNDARY}
    if persist:
        out = out_path or _default_active_path()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(active, indent=2, sort_keys=True))
        active["persisted_to"] = str(out)
    return {"record_type": "graph_autotune_receipt", "champion": config, "active": active,
            "leaderboard": receipt["top_configs"], "union_vs_lexical_ndcg_lift": receipt["union_vs_lexical_ndcg_lift"],
            **BOUNDARY}


def active_config(path: Optional[Path] = None) -> dict[str, str]:
    """The persisted champion ranking-config the serving default reads — safe fallback if never tuned or invalid
    (e.g. an option was removed since the last tune)."""
    p = path or _default_active_path()
    try:
        cfg = json.loads(p.read_text())["config"]
        if _valid_config(cfg):
            return cfg
    except Exception:  # noqa: BLE001 — no file / bad file / stale option => fallback
        pass
    return dict(_FALLBACK_CONFIG)


def _self_test() -> int:
    import tempfile  # noqa: PLC0415
    checks: list[tuple[str, bool]] = []
    distractors = [{"primitive_id": f"d:{i}", "title": f"zeta{i} widget",
                    "blackbox": f"sigma{i} unrelated distractor {i}.", "input_edge": f"In{i}",
                    "output_edge": f"Out{i}", **BOUNDARY} for i in range(20)]
    cards = _bench._gold_corpus() + distractors
    labelled = list(_bench._LABELLED_QUERIES)

    checks.append(("the fallback config is a valid graph path", _valid_config(_FALLBACK_CONFIG)))

    with tempfile.TemporaryDirectory() as d:
        out = Path(d) / "active_config.json"
        res = autotune(cards, labelled, k=5, out_path=out)
        champ = res["champion"]
        checks.append(("autotune races configs and picks a VALID champion config",
                       _valid_config(champ) and set(champ) == set(_RANKING_STAGES)))
        checks.append(("the champion is the top of the leaderboard (best nDCG)",
                       res["leaderboard"][0]["ndcg_at_k"] >= res["leaderboard"][-1]["ndcg_at_k"]
                       and all(champ[s] == res["leaderboard"][0][s] for s in _RANKING_STAGES)))
        checks.append(("the active config is PERSISTED and reads back identically",
                       out.exists() and active_config(out) == champ))
        # RE-TUNE is deterministic on the same inputs
        checks.append(("re-tuning is deterministic (same champion twice)",
                       autotune(cards, labelled, k=5, persist=False)["champion"]
                       == autotune(cards, labelled, k=5, persist=False)["champion"]))
        # SELF-HEAL: if a tuned option is later removed/disabled, active_config falls back to a valid default
        stale = Path(d) / "stale.json"
        stale.write_text(json.dumps({"config": {"expand": "none", "search": "NONEXISTENT",
                                                 "fuse": "rrf", "rerank": "none"}}))
        checks.append(("a stale/invalid persisted config falls back to a valid default",
                       _valid_config(active_config(stale))))

    checks.append(("autotune receipt is candidate/serves_truth=false", res["serves_truth"] is False))

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print(f"\nPASS - graph_autotune: SELF-TUNING — race the ranking configs, pick the champion by nDCG/recall "
          f"receipt, PERSIST it as the graph's active config (champion this run: {res['champion']}), and read it "
          f"back for serving with a safe fallback when never-tuned or stale. Re-run to re-adapt. serves_truth=false.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--tune", action="store_true", help="race + persist the active config over the real corpus")
    ap.add_argument("--active", action="store_true", help="print the current active (tuned) config")
    ap.add_argument("--sample", type=int, default=200, help="real distractor cards mixed into the gold families")
    ap.add_argument("--k", type=int, default=_bench._DEFAULT_K)
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.tune:
        cards = _bench.bench_corpus(args.sample)
        rec = autotune(cards, list(_bench._LABELLED_QUERIES), k=args.k)
        print(json.dumps({"champion": rec["champion"], "active": rec["active"],
                          "leaderboard_top3": rec["leaderboard"][:3]}, indent=2, sort_keys=True))
        return 0
    if args.active:
        print(json.dumps(active_config(), indent=2, sort_keys=True))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
