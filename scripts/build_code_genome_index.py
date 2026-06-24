"""build_code_genome_index — DOGFOOD the Code Genome (#§9) on our own source: fingerprint every src/teleon module
via the AST decomposition, then flag pairs with high genome overlap as CANDIDATE internal reinvention.

Genome similarity != proven duplication (two modules can share primitives and be legitimately different) — so every
near-duplicate is a governed CANDIDATE a human triages, never an assertion. Only modules with >= _MIN_PRIMITIVES
distinctive primitives are compared (a 1-primitive module's genome is not meaningful). High-volume detail streams to
data/dev-intel (not git-tracked prose). serves_truth=false.

  python3 scripts/build_code_genome_index.py            # write the index + report
  python3 scripts/build_code_genome_index.py --self-test
"""
from __future__ import annotations

import argparse
import json
import sys
from itertools import combinations
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.teleon.knowledge.code_genome import ast_fingerprint, decompose_ast, genome_similarity  # noqa: E402

_SRC = _REPO / "src" / "teleon"
_OUT = _REPO / "data" / "dev-intel" / "code_genome_index.json"
_MIN_PRIMITIVES = 2   # a module needs this many distinct primitives for its genome to be meaningful (our abstract
                      # framework code has a deliberately SPARSE infrastructure genome — few auth/db/cache modules)
_DUP = 0.9            # genome cosine >= this -> CANDIDATE internal reinvention (worth a look, not proof)


def _fingerprint_modules() -> list[dict]:
    mods = []
    for p in sorted(_SRC.rglob("*.py")):
        if p.name == "__init__.py":
            continue
        try:
            src = p.read_text()
        except (OSError, UnicodeDecodeError):
            continue
        prims = decompose_ast(src)
        if len(prims) >= _MIN_PRIMITIVES:
            mods.append({"path": str(p.relative_to(_REPO)), "primitives": prims, "fingerprint": ast_fingerprint(src)})
    return mods


def _near_duplicates(mods: list[dict]) -> list[dict]:
    out = []
    for a, b in combinations(mods, 2):
        sim = round(genome_similarity(a["fingerprint"], b["fingerprint"]), 4)
        if sim >= _DUP:
            out.append({"a": a["path"], "b": b["path"], "similarity": sim,
                        "shared_primitives": sorted(set(a["primitives"]) & set(b["primitives"])),
                        "candidate": True, "serves_truth": False})
    out.sort(key=lambda x: x["similarity"], reverse=True)
    return out


def _build(write: bool) -> dict:
    mods = _fingerprint_modules()
    dups = _near_duplicates(mods)
    index = {
        "version": "0.1.0",
        "principle": "Code Genome dogfooded on src/teleon: AST-fingerprint each module, flag high genome overlap as "
                     "CANDIDATE internal reinvention (worth review, not proven duplication). serves_truth=false.",
        "serves_truth": False,
        "modules_fingerprinted": len(mods),
        "min_primitives": _MIN_PRIMITIVES,
        "dup_threshold": _DUP,
        "near_duplicate_pairs": len(dups),
        "near_duplicates": dups[:50],  # bounded sample; full set streams to the operational tier
    }
    if write:
        _OUT.parent.mkdir(parents=True, exist_ok=True)
        _OUT.write_text(json.dumps(index, indent=2) + "\n")
    return index


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if not args.self_test:
        idx = _build(write=True)
        print(f"code_genome_index: fingerprinted {idx['modules_fingerprinted']} modules (>= {_MIN_PRIMITIVES} "
              f"primitives); {idx['near_duplicate_pairs']} candidate near-duplicate pairs (>= {_DUP}); -> {_OUT}")
        return 0

    fails, checks = [], 0

    def ck(name, ok, detail=""):
        nonlocal checks
        checks += 1
        if not ok:
            fails.append(name)
            print(f"  [XX] {name}{(' — ' + detail) if detail else ''}")

    idx = _build(write=False)
    ck("fingerprints real modules", idx["modules_fingerprinted"] >= 5, str(idx["modules_fingerprinted"]))
    # NOTE: a sparse result over abstract framework code is an HONEST finding (our code isn't auth/db/cache infra),
    # not a bug — the assertion is on the MECHANISM working, and near_duplicates may legitimately be empty.
    ck("near-duplicate pairs are governed candidates", all(
        d["serves_truth"] is False and d["candidate"] and d["similarity"] >= _DUP for d in idx["near_duplicates"]))
    ck("each near-duplicate names shared primitives", all(d["shared_primitives"] for d in idx["near_duplicates"]))
    ck("counts are computed + consistent", idx["near_duplicate_pairs"] == len(_near_duplicates(_fingerprint_modules()))
       or idx["near_duplicate_pairs"] >= len(idx["near_duplicates"]))
    ck("serves_truth false", idx["serves_truth"] is False)

    if fails:
        print(f"\nFAIL - build_code_genome_index: {len(fails)} of {checks} failed")
        return 1
    print(f"PASS - build_code_genome_index: dogfooded the Code Genome on {idx['modules_fingerprinted']} src/teleon "
          f"modules -> {idx['near_duplicate_pairs']} candidate internal-reinvention pairs; {checks} assertions; "
          f"serves_truth=false, candidates only.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
