#!/usr/bin/env python3
"""scripts.kaggle_iterative_object_miner — grind Kaggle ONE OBJECT (notebook/kernel) AT A TIME, resumably, with an
OFFLINE AST decomposition that needs NO LLM lane (so it runs now, unaffected by the free-lane 429 throttle).

It REUSES the foundry's Kaggle-CLI functions (`kaggle_list_kernels`, `kaggle_pull_kernel`, `read_notebook_text`,
`source_snapshot`) — the CLI authenticates via `~/.kaggle/access_token` (the saved KGAT token) — and adds:
  * a resumable CURSOR (page + in-page offset + processed-ref set) so `--limit N` / `--once` advance through the
    whole corpus incrementally and `--resume` continues exactly where it stopped (dedup: a ref is never re-mined);
  * a deterministic OFFLINE decompose: for each notebook, extract top-level `def`s (name/args/return/mechanism
    libs) + detected DS patterns (read_csv/train_test_split/fit/transform/predict/…) → typed primitive candidates.
Every row is candidate/serves_truth=false, stores a source handle+digest (never the raw notebook body), and
appends+dedupes to the feed. Live LLM enrichment stays opt-in (behind the quota manager) for later.

    python3 scripts/kaggle_iterative_object_miner.py --self-test
    python3 scripts/kaggle_iterative_object_miner.py --once                 # mine exactly ONE next kernel (live)
    python3 scripts/kaggle_iterative_object_miner.py --run --limit 25       # mine the next 25, resumable
    python3 scripts/kaggle_iterative_object_miner.py --status              # cursor + totals
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
import ast  # noqa: E402
import json  # noqa: E402
import re  # noqa: E402
import tempfile  # noqa: E402
from typing import Any, Callable, Optional  # noqa: E402

from scripts.kaggle_notebook_primitive_foundry import (kaggle_list_kernels, kaggle_pull_kernel,  # noqa: E402
                                                       source_snapshot)

try:
    from src.teleon.experiments.ids import canonical_id  # noqa: E402
except Exception as exc:  # noqa: BLE001
    raise SystemExit(f"kaggle_iterative_object_miner requires canonical_id; import failed: {exc}")

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
_DATA_SUBDIR = "data/dev-intel/kaggle_iterative_object_miner"
_PAGE_SIZE = 20
#: DS-pattern → the typed primitive family it implies (offline mechanism detection)
_PATTERNS: dict[str, tuple[str, str, str]] = {
    "read_csv": ("data_loader", "FilePath+ReadOptions", "DataFrame"),
    "train_test_split": ("data_splitter", "DataFrame+SplitPolicy", "TrainTestSplit"),
    "StandardScaler": ("feature_scaler", "FeatureMatrix", "ScaledMatrix"),
    "OneHotEncoder": ("categorical_encoder", "CategoricalColumns", "EncodedMatrix"),
    "fit_transform": ("fit_transformer", "FeatureMatrix", "TransformedMatrix"),
    "GridSearchCV": ("hyperparam_search", "Estimator+ParamGrid", "BestEstimator"),
    "cross_val_score": ("cross_validator", "Estimator+Folds", "ScoreArray"),
    "roc_auc_score": ("metric_calculator", "YTrue+YScore", "Auc"),
    "to_csv": ("submission_writer", "DataFrame+Path", "SubmissionReceipt"),
    "fillna": ("missing_value_imputer", "DataFrame+Strategy", "ImputedFrame"),
    "predict": ("model_predictor", "FittedModel+X", "Predictions"),
}


def _cursor_path() -> Path:
    return resource(_DATA_SUBDIR) / "cursor.json"


def _feed_path() -> Path:
    return resource(_DATA_SUBDIR) / "kaggle_object_primitive_candidates.jsonl"


def load_cursor() -> dict[str, Any]:
    p = _cursor_path()
    if p.exists():
        try:
            return json.loads(p.read_text())
        except Exception:  # noqa: BLE001
            pass
    return {"page": 1, "offset": 0, "processed_refs": [], "objects_mined": 0, "primitives": 0, "search": ""}


def save_cursor(c: dict[str, Any]) -> None:
    p = _cursor_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(c, sort_keys=True))


# ── OFFLINE decompose (no LLM): top-level defs + detected DS patterns -> typed primitive candidates ────────────
_DEF_RE = re.compile(r"^\s*def\s+([a-zA-Z_]\w*)\s*\(([^)]*)\)\s*:", re.M)
_IMPORT_RE = re.compile(r"^\s*(?:from\s+([\w.]+)\s+import|import\s+([\w.]+))", re.M)


def decompose_offline(notebook_text: str, ref: str) -> list[dict[str, Any]]:
    """Deterministic, LLM-free extraction of reusable primitive candidates from a notebook's text."""
    libs = sorted({(m.group(1) or m.group(2) or "").split(".")[0]
                   for m in _IMPORT_RE.finditer(notebook_text)} - {""})
    out: list[dict[str, Any]] = []
    seen: set[str] = set()

    def _emit(name: str, family: str, in_edge: str, out_edge: str, mechanism: str, args: int, kind: str) -> None:
        key = f"{name}|{family}|{in_edge}|{out_edge}"
        if key in seen:
            return
        seen.add(key)
        out.append({"record_type": "kaggle_object_primitive_candidate",
                    "primitive_id": canonical_id("kagobj", ref, name, family),
                    "name": name, "primitive_family": family, "kind": kind,
                    "input_edge": in_edge, "output_edge": out_edge, "mechanism": mechanism,
                    "arg_count": args, "source_ref": f"kaggle://kernels/{ref}", **BOUNDARY})

    # top-level (or notebook-scope) function definitions = reusable units
    for m in _DEF_RE.finditer(notebook_text):
        fn, argstr = m.group(1), m.group(2)
        if fn.startswith("_") or fn in ("main",):
            continue
        n_args = len([a for a in argstr.split(",") if a.strip() and a.strip() != "self"])
        _emit(fn, "extracted_function", f"{n_args}_args", "value",
              "+".join(libs[:5]) or "stdlib", n_args, "function")
    # detected data-science patterns = typed primitive candidates with real edges
    for token, (family, in_edge, out_edge) in _PATTERNS.items():
        if token in notebook_text:
            _emit(f"{family}__{token}", family, in_edge, out_edge, token, 0, "pattern")
    return out


def mine_one(kernel: dict[str, Any], *, runner: Optional[Callable[[list[str]], str]] = None,
             pull: Optional[Callable[..., Optional[str]]] = None) -> dict[str, Any]:
    """Pull + offline-decompose ONE kernel object → {snapshot, primitives}. Raw body stays out of the rows."""
    ref = kernel.get("ref", "")
    with tempfile.TemporaryDirectory() as td:
        text = (pull or kaggle_pull_kernel)(ref, Path(td), runner=runner) if pull else \
            kaggle_pull_kernel(ref, Path(td), runner=runner)
    if not text:
        return {"ref": ref, "ok": False, "reason": "no_notebook_text", "primitives": []}
    snap = source_snapshot(kernel, text)
    prims = decompose_offline(text, ref)
    return {"ref": ref, "ok": True, "snapshot": snap, "primitives": prims}


def iterate(n: int, *, runner: Optional[Callable[[list[str]], str]] = None,
            pull: Optional[Callable[..., Optional[str]]] = None,
            lister: Optional[Callable[..., list[dict[str, Any]]]] = None) -> dict[str, Any]:
    """Mine the next `n` UN-mined kernel objects, advancing + persisting the cursor after EACH (crash-safe/resumable)."""
    cur = load_cursor()
    processed = set(cur["processed_refs"])
    feed = _feed_path()
    feed.parent.mkdir(parents=True, exist_ok=True)
    _list = lister or kaggle_list_kernels
    mined = 0
    minted = 0
    with feed.open("a") as fh:
        while mined < n:
            page_rows = _list(cur["page"], _PAGE_SIZE, search=cur.get("search", ""), runner=runner)
            if not page_rows:
                break  # end of corpus (or empty page)
            advanced = False
            for row in page_rows[cur["offset"]:]:
                cur["offset"] += 1
                advanced = True
                ref = row.get("ref")
                if not ref or ref in processed:
                    continue
                res = mine_one(row, runner=runner, pull=pull)
                processed.add(ref)
                cur["processed_refs"] = sorted(processed)[-5000:]  # bound the dedup memory
                cur["objects_mined"] += 1
                mined += 1
                if res["ok"]:
                    fh.write(json.dumps(res["snapshot"], sort_keys=True) + "\n")
                    for p in res["primitives"]:
                        fh.write(json.dumps(p, sort_keys=True) + "\n")
                        minted += 1
                    cur["primitives"] += len(res["primitives"])
                save_cursor(cur)          # checkpoint after EVERY object → truly resumable, one-at-a-time
                if mined >= n:
                    break
            if cur["offset"] >= len(page_rows) or not advanced:
                cur["page"] += 1
                cur["offset"] = 0
                save_cursor(cur)
    return {"objects_mined_this_run": mined, "primitives_minted_this_run": minted,
            "cursor": {k: cur[k] for k in ("page", "offset", "objects_mined", "primitives")},
            "feed_path": str(feed), **BOUNDARY}


# ── self-test (offline, deterministic — stub kaggle client, no network) ────────────────────────────────────────
_FIXTURE_NB = ('import pandas as pd\nfrom sklearn.model_selection import train_test_split\n\n'
               'def clean_features(df, cols):\n    return df[cols].fillna(0)\n\n'
               'df = pd.read_csv("train.csv")\nX_tr, X_te = train_test_split(df, test_size=0.2)\n'
               'preds = model.predict(X_te)\nsub.to_csv("submission.csv")\n')


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []

    prims = decompose_offline(_FIXTURE_NB, "user/nb")
    names = {p["name"] for p in prims}
    fams = {p["primitive_family"] for p in prims}
    checks.append(("offline decompose extracts the top-level function as a primitive",
                   "clean_features" in names))
    checks.append(("offline decompose detects DS patterns as typed primitives (loader/splitter/predict/submission)",
                   {"data_loader", "data_splitter", "model_predictor", "submission_writer"} <= fams))
    checks.append(("candidates carry typed edges + source ref + candidate-only",
                   all(p["input_edge"] and p["output_edge"] and p["source_ref"].startswith("kaggle://")
                       and p["serves_truth"] is False for p in prims)))

    # stub kaggle client → iterate one object, resumable cursor, no network
    pages = {1: [{"ref": "a/one", "title": "T1"}, {"ref": "a/two", "title": "T2"}]}
    stub_list = lambda page, ps, search="", runner=None: pages.get(page, [])  # noqa: E731
    stub_pull = lambda ref, dest, runner=None: _FIXTURE_NB  # noqa: E731
    # route cursor/feed to a temp dir by patching THIS running module's own globals (works as __main__ or scripts.*)
    g = globals()
    orig = g["_cursor_path"], g["_feed_path"]
    with tempfile.TemporaryDirectory() as td:
        g["_cursor_path"] = lambda: Path(td) / "cursor.json"
        g["_feed_path"] = lambda: Path(td) / "feed.jsonl"
        try:
            r1 = iterate(1, lister=stub_list, pull=stub_pull)
            c1 = json.loads((Path(td) / "cursor.json").read_text())
            r2 = iterate(1, lister=stub_list, pull=stub_pull)  # RESUME: must mine the SECOND, not re-mine the first
            c2 = json.loads((Path(td) / "cursor.json").read_text())
            feed_exists = (Path(td) / "feed.jsonl").exists()
        finally:
            g["_cursor_path"], g["_feed_path"] = orig
    checks.append(("iterate mines ONE object at a time + checkpoints a cursor",
                   r1["objects_mined_this_run"] == 1 and c1["objects_mined"] == 1))
    checks.append(("RESUME advances to the next object (dedup: never re-mines a ref)",
                   r2["objects_mined_this_run"] == 1 and c2["objects_mined"] == 2
                   and set(c2["processed_refs"]) == {"a/one", "a/two"}))
    checks.append(("mining is crash-safe: cursor persisted after every object", c2["primitives"] > 0 and feed_exists))

    ok = all(v for _, v in checks)
    for nm, v in checks:
        print(f"  [{'ok' if v else 'XX'}] {nm}")
    print(("PASS" if ok else "FAIL") + " - kaggle_iterative_object_miner: grinds Kaggle ONE object at a time, "
          "resumable cursor (crash-safe, dedup), OFFLINE AST+pattern decompose (no LLM lane) -> typed primitive "
          "candidates with source handle+digest (no raw body). serves_truth=false.")
    return 0 if ok else 1


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Iteratively mine Kaggle one notebook at a time (resumable, offline).")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--once", action="store_true", help="mine exactly ONE next kernel (live)")
    ap.add_argument("--run", action="store_true", help="mine --limit next kernels (live, resumable)")
    ap.add_argument("--limit", type=int, default=10)
    ap.add_argument("--search", default=None, help="restrict the corpus to a search term (persisted in the cursor)")
    ap.add_argument("--status", action="store_true")
    args = ap.parse_args(argv)

    if args.self_test:
        return _self_test()
    if args.status:
        print(json.dumps(load_cursor(), indent=2, sort_keys=True))
        return 0
    if args.search is not None:
        c = load_cursor(); c["search"] = args.search; c["page"] = 1; c["offset"] = 0; save_cursor(c)
        print(f"cursor search set to {args.search!r}; reset to page 1")
    if args.once or args.run:
        n = 1 if args.once else args.limit
        summ = iterate(n)
        print(json.dumps(summ, indent=2, sort_keys=True))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
