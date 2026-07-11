#!/usr/bin/env python3
"""Combinatorial query foundry — deterministic sampled generation of ingestion search queries (W11).

The owner's dimensional-multiplication design: Person × Directed-Question × Country × Time-Period ×
Industry × Problem × Solution × Diagram × Architecture × Code × Response-Format × Company × Movement ×
Publication-Medium (every dimension nullable). The seed vocabularies alone span ~5.7e13 combinations, so
the space is SAMPLED with reproducible seeds, never enumerated. Batches are deduped by canonical
token-set blocking keys, priority-scored (problem+industry presence), stamped candidate-only, and written
as JSONL for the governed fetch stage — which MUST run through the browsing guardrail stack and the W10
licensing owner gate before any volume ingestion. Downstream: fetched documents feed the decomposition
foundries → primitive/template candidates → the normal proof/promotion boundary.

Single source of dimensions: _repos/shared-backend-components/architecture/query_foundry_dimensions.json (no values re-typed here).

Usage:
  python3 _repos/shared-backend-components/scripts/query_foundry.py --seed 1 --size 500     # one reproducible batch
  python3 _repos/shared-backend-components/scripts/query_foundry.py --self-test
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import json
import random
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.teleon.experiments.ids import canonical_id  # noqa: E402

DIMENSIONS_PATH = _resource("architecture") / "query_foundry_dimensions.json"
OUT_DIR = _resource("data") / "dev-intel" / "query_foundry" / "batches"
#: priority weights: queries naming a concrete problem/industry screen better (gap-screen alignment).
PRIORITY_WEIGHTS = {"problem": 3, "industry": 2, "solution_form": 2, "diagram": 1, "architecture_style": 1}


def load_dimensions() -> dict:
    return json.loads(DIMENSIONS_PATH.read_text(encoding="utf-8"))


def space_size(spec: dict) -> int:
    size = 1
    for dim in spec["dimensions"].values():
        size *= len(dim["values"]) + 1  # +1 = the null value
    return size


def blocking_key(query: str) -> str:
    """Order-insensitive token-set key: permuted near-duplicates collapse into one block."""
    return canonical_id("qfblock", *sorted(set(query.lower().split())))


def sample_batch(spec: dict, *, seed: int, size: int) -> list[dict]:
    rng = random.Random(seed)  # seeded => reproducible; never wall-clock randomness
    order = spec["query_template_order"]
    excluded = [term.lower() for term in spec.get("excluded_terms", [])]
    rows: list[dict] = []
    seen_blocks: set[str] = set()
    attempts = 0
    while len(rows) < size and attempts < size * 20:
        attempts += 1
        chosen: dict[str, str] = {}
        for name in order:
            dim = spec["dimensions"][name]
            if rng.random() < float(dim.get("null_weight", 0.5)):
                continue
            chosen[name] = rng.choice(dim["values"])
        if len(chosen) < 3:  # a query needs enough signal to be searchable
            continue
        query = " ".join(chosen[name] for name in order if name in chosen)
        if any(term in query.lower() for term in excluded):
            continue  # scope law (e.g. insurance) enforced at generation, not cleanup
        block = blocking_key(query)
        if block in seen_blocks:
            continue
        seen_blocks.add(block)
        # Source-type operator (Google-dork-style) attached as structured INTENT — kept OUT of the
        # semantic `query` (so embeddings stay clean) and off the blocking key (so the same query with
        # different operators does not collapse). search_string is what the research agent actually runs.
        operator = None
        op_spec = spec.get("search_operators")
        if op_spec and rng.random() >= float(op_spec.get("null_weight", 0.5)):
            operator = rng.choice(op_spec["values"])
        rows.append({
            "record_type": "query_foundry_candidate",
            "schema_version": "query_foundry_candidate",
            "query_id": canonical_id("qf", str(seed), query, operator["op"] if operator else ""),
            "query": query,
            "search_operator": operator,  # {op, targets} or None
            "search_string": f"{query} {operator['op']}" if operator else query,
            "dimensions": chosen,
            "blocking_key": block,
            "priority": sum(PRIORITY_WEIGHTS.get(name, 0) for name in chosen) + (1 if operator else 0),
            "seed": seed,
            "fetch_gate": "governed_browsing_stack + W10 licensing owner gate (never fetch raw); operator applied literally-or-equivalently by the research agent",
            "candidate": True,
            "serves_truth": False,
        })
    rows.sort(key=lambda row: (-row["priority"], row["query_id"]))
    return rows


def write_batch(rows: list[dict], *, seed: int, out_dir: Path = OUT_DIR) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"batch-seed{seed}.jsonl"
    path.write_text("\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n", encoding="utf-8")
    return path


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    spec = load_dimensions()
    check("dimension spec loads with >=14 dimensions (they grow by design), all nullable-by-weight",
          len(spec["dimensions"]) >= 14 and all("null_weight" in d for d in spec["dimensions"].values()))
    check("the sampled space is astronomically larger than any batch (enumeration is impossible by design)",
          space_size(spec) > 10**12, f"{space_size(spec):.2e}")

    a = sample_batch(spec, seed=42, size=200)
    b = sample_batch(spec, seed=42, size=200)
    c = sample_batch(spec, seed=43, size=200)
    check("same seed reproduces the identical batch (deterministic sampling)", a == b)
    check("different seed produces a different batch", a != c)
    check("batch fills to requested size with unique blocking keys",
          len(a) == 200 and len({r["blocking_key"] for r in a}) == 200)
    check("null dimensions actually occur (queries vary in arity)",
          min(len(r["dimensions"]) for r in a) < max(len(r["dimensions"]) for r in a))
    check("scope law enforced at generation (excluded terms never appear)",
          all("insurance" not in r["query"].lower() for r in a))
    check("priority ranks problem+industry queries first",
          a[0]["priority"] >= a[-1]["priority"] and a[0]["priority"] > 0)
    check("ids are canonical and rows carry the truth boundary",
          all(r["query_id"].startswith("qf-") and r["candidate"] is True and r["serves_truth"] is False
              for r in a))
    permuted = blocking_key("banking invoice reconciliation pipeline")
    check("blocking key is order-insensitive (permuted duplicates collapse)",
          permuted == blocking_key("pipeline reconciliation invoice banking"))

    with_ops = [r for r in a if r.get("search_operator")]
    check("source-type operators attach to a fraction of queries (dork-style precision)",
          0 < len(with_ops) < len(a), f"{len(with_ops)}/{len(a)}")
    check("operator lives in search_string + structured field, NOT in the semantic query or blocking key",
          all(r["search_operator"]["op"] in r["search_string"] and r["search_operator"]["op"] not in r["query"]
              and r["search_operator"]["op"] not in r["blocking_key"] for r in with_ops))

    import tempfile
    with tempfile.TemporaryDirectory() as td:
        path = write_batch(a[:25], seed=42, out_dir=Path(td))
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        check("batch writes as JSONL with fetch gate recorded on every row",
              len(rows) == 25 and all("governed_browsing_stack" in r["fetch_gate"] for r in rows))

    print(f"\n{'PASS - query_foundry: reproducible sampled generation over a ~1e13 query space; blocked dedupe; scope law at generation; fetch stays behind the governed gate' if not fails else str(len(fails)) + ' FAILURES: ' + str(fails)}")
    return 0 if not fails else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--size", type=int, default=500)
    args = parser.parse_args()
    if args.self_test:
        return _self_test()
    spec = load_dimensions()
    rows = sample_batch(spec, seed=args.seed, size=args.size)
    path = write_batch(rows, seed=args.seed)
    print(f"wrote {len(rows)} query candidates -> {path.relative_to(REPO)} "
          f"(space {space_size(spec):.2e}; top: {rows[0]['query'][:90]!r})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
