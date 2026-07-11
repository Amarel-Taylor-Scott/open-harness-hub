#!/usr/bin/env python3
"""scripts.prove_leaves_list_sequence — WORKABLE (proven + TYPED) deterministic leaf primitives, family 'list_sequence'.

The proven-primitive substrate (_repos/shared-backend-components/scripts/mutator_registry.py) can flip serves_truth false->true ONLY via an executed
passing proof, and _repos/shared-backend-components/scripts/build_edge_type_retrofit.py can fold a raw edge string to a canonical type_id so proven
leaves can actually CHAIN. This module is the list/sequence-family fix for the "proven but untyped" gap: it declares
>=28 REAL pure deterministic leaf primitives over RecordBatch->RecordBatch-shaped list transforms (dedupe-preserve-
order, flatten-one-level, chunk, sliding-window, unique-by-key, partition, interleave, running-pairs, rotate,
take/drop, RLE, enumerate, zip, scan/diff, ...), runs EVERY ONE through the imported `run_primitive_proof`, keeps ONLY
the passers, and TYPES every persisted row with `canonicalize_edge(input_edge)`/`canonicalize_edge(output_edge)`.

ADD-ONLY / flexible-multi-path: it IMPORTS the contract-locked machinery (mutator_registry, build_edge_type_retrofit)
and never edits it; new pure mutators plug into the shared MUTATOR_REGISTRY via setdefault (idempotent registration,
never overwrite). serves_truth=true here is CORRECT + required — it is set ONLY by an executed passing proof; a
deliberately-wrong-expected leaf stays candidate and is NEVER persisted. Where a leaf has a true inverse the ROUNDTRIP
is proven (chunk<->flatten, rle_encode<->rle_decode, enumerate<->deindex, zip<->unzip, scan_sum<->diff, reverse and
pairwise_swap are self-inverse). Offline + deterministic (no wall-clock/RNG/network/LLM in bodies).

CLI: --self-test (offline, standalone) | --write [--date D]. --write persists to
data/dev-intel/proven_primitives/proven_list_sequence.jsonl + manifest_list_sequence.json.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

# IMPORT the existing machinery — never edit it (ADD-ONLY / flexible-multi-path).
from scripts.mutator_registry import (  # noqa: E402
    MUTATOR_REGISTRY,
    _receipt,
    run_primitive_proof,
)
from scripts.build_edge_type_retrofit import canonicalize_edge  # noqa: E402

FAMILY = "list_sequence"
OUT_DIR = _resource("data") / "dev-intel" / "proven_primitives"
OUT_JSONL = OUT_DIR / "proven_list_sequence.jsonl"
OUT_MANIFEST = OUT_DIR / "manifest_list_sequence.json"
# Fixed literal timestamp — no wall-clock (determinism law).
DEFAULT_DATE = "2026-07-03"


# ── PURE deterministic list/sequence mutators. Each (payload, **kwargs) -> (output, receipt_dict). No I/O, no state. ──
def seq_dedupe_order(items: list[Any]) -> tuple[list[Any], dict[str, Any]]:
    out = list(dict.fromkeys(items))
    return out, _receipt("seq_dedupe_order", before=items, after=out, lossless=False, note="order-preserving dedupe")


def seq_dedupe_adjacent(items: list[Any]) -> tuple[list[Any], dict[str, Any]]:
    out: list[Any] = []
    for x in items:
        if not out or out[-1] != x:
            out.append(x)
    return out, _receipt("seq_dedupe_adjacent", before=items, after=out, lossless=False, note="collapse consecutive dups")


def seq_flatten_one(nested: list[Any]) -> tuple[list[Any], dict[str, Any]]:
    out: list[Any] = []
    for sub in nested:
        if isinstance(sub, list):
            out.extend(sub)
        else:
            out.append(sub)
    return out, _receipt("seq_flatten_one", before=nested, after=out, lossless=False, note="flatten one level")


def seq_chunk(items: list[Any], size: int = 2) -> tuple[list[list[Any]], dict[str, Any]]:
    out = [items[i:i + size] for i in range(0, len(items), size)]
    return out, _receipt("seq_chunk", before=items, after=out, lossless=True, note=f"chunk into size {size}; flatten restores")


def seq_sliding_window(items: list[Any], size: int = 2) -> tuple[list[list[Any]], dict[str, Any]]:
    out = [items[i:i + size] for i in range(0, len(items) - size + 1)] if size <= len(items) else []
    return out, _receipt("seq_sliding_window", before=items, after=out, lossless=False, note=f"sliding windows of {size}")


def seq_unique_by_key(rows: list[dict[str, Any]], key: str = "k") -> tuple[list[dict[str, Any]], dict[str, Any]]:
    seen: dict[Any, dict[str, Any]] = {}
    for r in rows:
        k = r.get(key)
        if k not in seen:
            seen[k] = r
    out = list(seen.values())
    return out, _receipt("seq_unique_by_key", before=rows, after=out, lossless=False, note=f"first-wins unique by {key}")


def seq_partition_parity(items: list[int]) -> tuple[list[list[int]], dict[str, Any]]:
    evens = [x for x in items if x % 2 == 0]
    odds = [x for x in items if x % 2 != 0]
    out = [evens, odds]
    return out, _receipt("seq_partition_parity", before=items, after=out, lossless=True, note="partition [even, odd]")


def seq_interleave(pair: list[list[Any]]) -> tuple[list[Any], dict[str, Any]]:
    a, b = pair[0], pair[1]
    out: list[Any] = []
    for i in range(max(len(a), len(b))):
        if i < len(a):
            out.append(a[i])
        if i < len(b):
            out.append(b[i])
    return out, _receipt("seq_interleave", before=pair, after=out, lossless=True, note="interleave two lists")


def seq_running_pairs(items: list[Any]) -> tuple[list[list[Any]], dict[str, Any]]:
    out = [[items[i], items[i + 1]] for i in range(len(items) - 1)]
    return out, _receipt("seq_running_pairs", before=items, after=out, lossless=False, note="consecutive (a,b) pairs")


def seq_rotate_left(items: list[Any], n: int = 1) -> tuple[list[Any], dict[str, Any]]:
    n = n % len(items) if items else 0
    out = items[n:] + items[:n]
    return out, _receipt("seq_rotate_left", before=items, after=out, lossless=True, note=f"rotate left {n}")


def seq_rotate_right(items: list[Any], n: int = 1) -> tuple[list[Any], dict[str, Any]]:
    n = n % len(items) if items else 0
    out = items[-n:] + items[:-n] if n else list(items)
    return out, _receipt("seq_rotate_right", before=items, after=out, lossless=True, note=f"rotate right {n}")


def seq_take(items: list[Any], n: int = 1) -> tuple[list[Any], dict[str, Any]]:
    out = items[:n]
    return out, _receipt("seq_take", before=items, after=out, lossless=False, note=f"take first {n}")


def seq_drop(items: list[Any], n: int = 1) -> tuple[list[Any], dict[str, Any]]:
    out = items[n:]
    return out, _receipt("seq_drop", before=items, after=out, lossless=False, note=f"drop first {n}")


def seq_take_last(items: list[Any], n: int = 1) -> tuple[list[Any], dict[str, Any]]:
    out = items[-n:] if n else []
    return out, _receipt("seq_take_last", before=items, after=out, lossless=False, note=f"take last {n}")


def seq_take_while_lt(items: list[int], threshold: int = 0) -> tuple[list[int], dict[str, Any]]:
    out: list[int] = []
    for x in items:
        if x < threshold:
            out.append(x)
        else:
            break
    return out, _receipt("seq_take_while_lt", before=items, after=out, lossless=False, note=f"take while < {threshold}")


def seq_drop_while_lt(items: list[int], threshold: int = 0) -> tuple[list[int], dict[str, Any]]:
    i = 0
    while i < len(items) and items[i] < threshold:
        i += 1
    out = items[i:]
    return out, _receipt("seq_drop_while_lt", before=items, after=out, lossless=False, note=f"drop while < {threshold}")


def seq_step(items: list[Any], step: int = 2) -> tuple[list[Any], dict[str, Any]]:
    out = items[::step]
    return out, _receipt("seq_step", before=items, after=out, lossless=False, note=f"every {step}th element")


def seq_reverse(items: list[Any]) -> tuple[list[Any], dict[str, Any]]:
    out = list(reversed(items))
    return out, _receipt("seq_reverse", before=items, after=out, lossless=True, note="reverse; self-inverse")


def seq_pairwise_swap(items: list[Any]) -> tuple[list[Any], dict[str, Any]]:
    out = list(items)
    for i in range(0, len(out) - 1, 2):
        out[i], out[i + 1] = out[i + 1], out[i]
    return out, _receipt("seq_pairwise_swap", before=items, after=out, lossless=True, note="swap adjacent pairs; self-inverse (even)")


def seq_rle_encode(items: list[Any]) -> tuple[list[list[Any]], dict[str, Any]]:
    out: list[list[Any]] = []
    for x in items:
        if out and out[-1][0] == x:
            out[-1][1] += 1
        else:
            out.append([x, 1])
    return out, _receipt("seq_rle_encode", before=items, after=out, lossless=True, note="run-length encode; rle_decode restores")


def seq_rle_decode(runs: list[list[Any]]) -> tuple[list[Any], dict[str, Any]]:
    out: list[Any] = []
    for value, count in runs:
        out.extend([value] * count)
    return out, _receipt("seq_rle_decode", before=runs, after=out, lossless=True, note="run-length decode")


def seq_enumerate(items: list[Any]) -> tuple[list[list[Any]], dict[str, Any]]:
    out = [[i, x] for i, x in enumerate(items)]
    return out, _receipt("seq_enumerate", before=items, after=out, lossless=True, note="zip with index; deindex restores")


def seq_deindex(indexed: list[list[Any]]) -> tuple[list[Any], dict[str, Any]]:
    out = [pair[1] for pair in indexed]
    return out, _receipt("seq_deindex", before=indexed, after=out, lossless=True, note="strip index")


def seq_zip(pair: list[list[Any]]) -> tuple[list[list[Any]], dict[str, Any]]:
    a, b = pair[0], pair[1]
    out = [[a[i], b[i]] for i in range(min(len(a), len(b)))]
    return out, _receipt("seq_zip", before=pair, after=out, lossless=True, note="zip two equal lists; unzip restores")


def seq_unzip(pairs: list[list[Any]]) -> tuple[list[list[Any]], dict[str, Any]]:
    out = [[p[0] for p in pairs], [p[1] for p in pairs]]
    return out, _receipt("seq_unzip", before=pairs, after=out, lossless=True, note="unzip pairs into two lists")


def seq_group_adjacent(items: list[Any]) -> tuple[list[list[Any]], dict[str, Any]]:
    out: list[list[Any]] = []
    for x in items:
        if out and out[-1][0] == x:
            out[-1].append(x)
        else:
            out.append([x])
    return out, _receipt("seq_group_adjacent", before=items, after=out, lossless=True, note="group consecutive equal; flatten restores")


def seq_scan_sum(items: list[int]) -> tuple[list[int], dict[str, Any]]:
    out: list[int] = []
    total = 0
    for x in items:
        total += x
        out.append(total)
    return out, _receipt("seq_scan_sum", before=items, after=out, lossless=True, note="cumulative sums; diff restores")


def seq_diff(items: list[int]) -> tuple[list[int], dict[str, Any]]:
    out: list[int] = []
    prev = 0
    for x in items:
        out.append(x - prev)
        prev = x
    return out, _receipt("seq_diff", before=items, after=out, lossless=True, note="consecutive differences")


def seq_head(items: list[Any]) -> tuple[Any, dict[str, Any]]:
    out = items[0]
    return out, _receipt("seq_head", before=items, after=out, lossless=False, note="first element")


def seq_last(items: list[Any]) -> tuple[Any, dict[str, Any]]:
    out = items[-1]
    return out, _receipt("seq_last", before=items, after=out, lossless=False, note="last element")


def seq_tail(items: list[Any]) -> tuple[list[Any], dict[str, Any]]:
    out = items[1:]
    return out, _receipt("seq_tail", before=items, after=out, lossless=False, note="all but first")


def seq_init(items: list[Any]) -> tuple[list[Any], dict[str, Any]]:
    out = items[:-1]
    return out, _receipt("seq_init", before=items, after=out, lossless=False, note="all but last")


def seq_compact(items: list[Any]) -> tuple[list[Any], dict[str, Any]]:
    out = [x for x in items if x]
    return out, _receipt("seq_compact", before=items, after=out, lossless=False, note="drop falsy/None values")


def seq_intersperse(items: list[Any], sep: Any = 0) -> tuple[list[Any], dict[str, Any]]:
    out: list[Any] = []
    for i, x in enumerate(items):
        if i:
            out.append(sep)
        out.append(x)
    return out, _receipt("seq_intersperse", before=items, after=out, lossless=False, note=f"insert {sep!r} between elements")


#: new pure mutators to plug into the shared registry (idempotent registration; never overwrites existing entries)
_NEW_MUTATORS = {
    "seq_dedupe_order": seq_dedupe_order, "seq_dedupe_adjacent": seq_dedupe_adjacent,
    "seq_flatten_one": seq_flatten_one, "seq_chunk": seq_chunk, "seq_sliding_window": seq_sliding_window,
    "seq_unique_by_key": seq_unique_by_key, "seq_partition_parity": seq_partition_parity,
    "seq_interleave": seq_interleave, "seq_running_pairs": seq_running_pairs,
    "seq_rotate_left": seq_rotate_left, "seq_rotate_right": seq_rotate_right,
    "seq_take": seq_take, "seq_drop": seq_drop, "seq_take_last": seq_take_last,
    "seq_take_while_lt": seq_take_while_lt, "seq_drop_while_lt": seq_drop_while_lt, "seq_step": seq_step,
    "seq_reverse": seq_reverse, "seq_pairwise_swap": seq_pairwise_swap,
    "seq_rle_encode": seq_rle_encode, "seq_rle_decode": seq_rle_decode,
    "seq_enumerate": seq_enumerate, "seq_deindex": seq_deindex,
    "seq_zip": seq_zip, "seq_unzip": seq_unzip, "seq_group_adjacent": seq_group_adjacent,
    "seq_scan_sum": seq_scan_sum, "seq_diff": seq_diff,
    "seq_head": seq_head, "seq_last": seq_last, "seq_tail": seq_tail, "seq_init": seq_init,
    "seq_compact": seq_compact, "seq_intersperse": seq_intersperse,
}


def register_new_mutators() -> None:
    """Plug the list/sequence mutators into the shared MUTATOR_REGISTRY (registration, not a rewrite). Idempotent."""
    for name, fn in _NEW_MUTATORS.items():
        MUTATOR_REGISTRY.setdefault(name, fn)


register_new_mutators()


# ── the leaf primitives: each a REAL capability with a concrete fixture + expected output (+ optional inverse) ──
# spec fields: id, capability, mutator, fixture, expected, args, inverse, input_edge, output_edge
_L = "RecordBatch"   # family shape: a list/batch of records/items
_LL = "NestedRecordBatch"  # a list of lists (chunked / grouped / windowed)
_PAIR = "RecordBatchPair"   # a two-list bundle (zip/interleave input, unzip/partition output)
_EL = "Any"          # a single element pulled out of the batch
LEAF_SPECS: list[dict[str, Any]] = [
    {"id": "prim:leaf:seq_dedupe_order", "capability": "order-preserving dedupe of a batch",
     "mutator": "seq_dedupe_order", "fixture": [3, 1, 3, 2, 1], "expected": [3, 1, 2], "args": {},
     "input_edge": _L, "output_edge": _L},
    {"id": "prim:leaf:seq_dedupe_adjacent", "capability": "collapse consecutive duplicate items",
     "mutator": "seq_dedupe_adjacent", "fixture": [1, 1, 2, 2, 2, 3, 1], "expected": [1, 2, 3, 1], "args": {},
     "input_edge": _L, "output_edge": _L},
    {"id": "prim:leaf:seq_chunk", "capability": "chunk a batch into fixed-size groups (roundtrips via flatten)",
     "mutator": "seq_chunk", "fixture": [1, 2, 3, 4], "expected": [[1, 2], [3, 4]], "args": {"size": 2},
     "inverse": "seq_flatten_one", "input_edge": _L, "output_edge": _LL},
    {"id": "prim:leaf:seq_flatten_one", "capability": "flatten a nested batch by one level",
     "mutator": "seq_flatten_one", "fixture": [[1, 2], [3], [4, 5]], "expected": [1, 2, 3, 4, 5], "args": {},
     "input_edge": _LL, "output_edge": _L},
    {"id": "prim:leaf:seq_sliding_window", "capability": "sliding windows of fixed size over a batch",
     "mutator": "seq_sliding_window", "fixture": [1, 2, 3], "expected": [[1, 2], [2, 3]], "args": {"size": 2},
     "input_edge": _L, "output_edge": _LL},
    {"id": "prim:leaf:seq_unique_by_key", "capability": "first-wins unique of records by a key field",
     "mutator": "seq_unique_by_key",
     "fixture": [{"k": 1, "v": "a"}, {"k": 1, "v": "b"}, {"k": 2, "v": "c"}],
     "expected": [{"k": 1, "v": "a"}, {"k": 2, "v": "c"}], "args": {"key": "k"},
     "input_edge": _L, "output_edge": _L},
    {"id": "prim:leaf:seq_partition_parity", "capability": "partition a numeric batch into [even, odd]",
     "mutator": "seq_partition_parity", "fixture": [1, 2, 3, 4], "expected": [[2, 4], [1, 3]], "args": {},
     "input_edge": _L, "output_edge": _PAIR},
    {"id": "prim:leaf:seq_interleave", "capability": "interleave two batches",
     "mutator": "seq_interleave", "fixture": [[1, 3, 5], [2, 4, 6]], "expected": [1, 2, 3, 4, 5, 6], "args": {},
     "input_edge": _PAIR, "output_edge": _L},
    {"id": "prim:leaf:seq_running_pairs", "capability": "consecutive (a,b) pairs over a batch",
     "mutator": "seq_running_pairs", "fixture": [1, 2, 3, 4], "expected": [[1, 2], [2, 3], [3, 4]], "args": {},
     "input_edge": _L, "output_edge": _LL},
    {"id": "prim:leaf:seq_rotate_left", "capability": "rotate a batch left by n",
     "mutator": "seq_rotate_left", "fixture": [1, 2, 3], "expected": [2, 3, 1], "args": {"n": 1},
     "input_edge": _L, "output_edge": _L},
    {"id": "prim:leaf:seq_rotate_right", "capability": "rotate a batch right by n",
     "mutator": "seq_rotate_right", "fixture": [1, 2, 3], "expected": [3, 1, 2], "args": {"n": 1},
     "input_edge": _L, "output_edge": _L},
    {"id": "prim:leaf:seq_take", "capability": "take the first n items of a batch",
     "mutator": "seq_take", "fixture": [1, 2, 3, 4], "expected": [1, 2], "args": {"n": 2},
     "input_edge": _L, "output_edge": _L},
    {"id": "prim:leaf:seq_drop", "capability": "drop the first n items of a batch",
     "mutator": "seq_drop", "fixture": [1, 2, 3, 4], "expected": [3, 4], "args": {"n": 2},
     "input_edge": _L, "output_edge": _L},
    {"id": "prim:leaf:seq_take_last", "capability": "take the last n items of a batch",
     "mutator": "seq_take_last", "fixture": [1, 2, 3, 4], "expected": [3, 4], "args": {"n": 2},
     "input_edge": _L, "output_edge": _L},
    {"id": "prim:leaf:seq_take_while_lt", "capability": "take a prefix while items are below a threshold",
     "mutator": "seq_take_while_lt", "fixture": [1, 2, 3, 4, 1], "expected": [1, 2], "args": {"threshold": 3},
     "input_edge": _L, "output_edge": _L},
    {"id": "prim:leaf:seq_drop_while_lt", "capability": "drop a prefix while items are below a threshold",
     "mutator": "seq_drop_while_lt", "fixture": [1, 2, 3, 4, 1], "expected": [3, 4, 1], "args": {"threshold": 3},
     "input_edge": _L, "output_edge": _L},
    {"id": "prim:leaf:seq_step", "capability": "take every nth item of a batch",
     "mutator": "seq_step", "fixture": [1, 2, 3, 4, 5], "expected": [1, 3, 5], "args": {"step": 2},
     "input_edge": _L, "output_edge": _L},
    {"id": "prim:leaf:seq_reverse", "capability": "reverse a batch (self-inverse; roundtrips)",
     "mutator": "seq_reverse", "fixture": [1, 2, 3], "expected": [3, 2, 1], "args": {},
     "inverse": "seq_reverse", "input_edge": _L, "output_edge": _L},
    {"id": "prim:leaf:seq_pairwise_swap", "capability": "swap adjacent pairs (self-inverse on even length)",
     "mutator": "seq_pairwise_swap", "fixture": [1, 2, 3, 4], "expected": [2, 1, 4, 3], "args": {},
     "inverse": "seq_pairwise_swap", "input_edge": _L, "output_edge": _L},
    {"id": "prim:leaf:seq_rle_encode", "capability": "run-length encode a batch (roundtrips via rle_decode)",
     "mutator": "seq_rle_encode", "fixture": [1, 1, 2, 3, 3, 3], "expected": [[1, 2], [2, 1], [3, 3]], "args": {},
     "inverse": "seq_rle_decode", "input_edge": _L, "output_edge": _LL},
    {"id": "prim:leaf:seq_rle_decode", "capability": "run-length decode back to a batch",
     "mutator": "seq_rle_decode", "fixture": [[1, 2], [2, 1]], "expected": [1, 1, 2], "args": {},
     "input_edge": _LL, "output_edge": _L},
    {"id": "prim:leaf:seq_enumerate", "capability": "zip a batch with its indices (roundtrips via deindex)",
     "mutator": "seq_enumerate", "fixture": ["a", "b"], "expected": [[0, "a"], [1, "b"]], "args": {},
     "inverse": "seq_deindex", "input_edge": _L, "output_edge": _LL},
    {"id": "prim:leaf:seq_deindex", "capability": "strip indices from an enumerated batch",
     "mutator": "seq_deindex", "fixture": [[0, "a"], [1, "b"]], "expected": ["a", "b"], "args": {},
     "input_edge": _LL, "output_edge": _L},
    {"id": "prim:leaf:seq_zip", "capability": "zip two equal-length batches into pairs (roundtrips via unzip)",
     "mutator": "seq_zip", "fixture": [[1, 2], ["a", "b"]], "expected": [[1, "a"], [2, "b"]], "args": {},
     "inverse": "seq_unzip", "input_edge": _PAIR, "output_edge": _LL},
    {"id": "prim:leaf:seq_unzip", "capability": "unzip a batch of pairs into two batches",
     "mutator": "seq_unzip", "fixture": [[1, "a"], [2, "b"]], "expected": [[1, 2], ["a", "b"]], "args": {},
     "input_edge": _LL, "output_edge": _PAIR},
    {"id": "prim:leaf:seq_group_adjacent", "capability": "group consecutive equal items (roundtrips via flatten)",
     "mutator": "seq_group_adjacent", "fixture": [1, 1, 2, 3, 3], "expected": [[1, 1], [2], [3, 3]], "args": {},
     "inverse": "seq_flatten_one", "input_edge": _L, "output_edge": _LL},
    {"id": "prim:leaf:seq_scan_sum", "capability": "cumulative sums over a numeric batch (roundtrips via diff)",
     "mutator": "seq_scan_sum", "fixture": [1, 2, 3], "expected": [1, 3, 6], "args": {},
     "inverse": "seq_diff", "input_edge": _L, "output_edge": _L},
    {"id": "prim:leaf:seq_diff", "capability": "consecutive differences over a numeric batch",
     "mutator": "seq_diff", "fixture": [1, 3, 6], "expected": [1, 2, 3], "args": {},
     "input_edge": _L, "output_edge": _L},
    {"id": "prim:leaf:seq_head", "capability": "first element of a batch",
     "mutator": "seq_head", "fixture": [1, 2, 3], "expected": 1, "args": {},
     "input_edge": _L, "output_edge": _EL},
    {"id": "prim:leaf:seq_last", "capability": "last element of a batch",
     "mutator": "seq_last", "fixture": [1, 2, 3], "expected": 3, "args": {},
     "input_edge": _L, "output_edge": _EL},
    {"id": "prim:leaf:seq_tail", "capability": "all but the first item of a batch",
     "mutator": "seq_tail", "fixture": [1, 2, 3], "expected": [2, 3], "args": {},
     "input_edge": _L, "output_edge": _L},
    {"id": "prim:leaf:seq_init", "capability": "all but the last item of a batch",
     "mutator": "seq_init", "fixture": [1, 2, 3], "expected": [1, 2], "args": {},
     "input_edge": _L, "output_edge": _L},
    {"id": "prim:leaf:seq_compact", "capability": "drop falsy/None items from a batch",
     "mutator": "seq_compact", "fixture": [0, 1, None, 2, "", 3], "expected": [1, 2, 3], "args": {},
     "input_edge": _L, "output_edge": _L},
    {"id": "prim:leaf:seq_intersperse", "capability": "insert a separator between items of a batch",
     "mutator": "seq_intersperse", "fixture": [1, 2, 3], "expected": [1, 0, 2, 0, 3], "args": {"sep": 0},
     "input_edge": _L, "output_edge": _L},
]

#: deliberately-wrong leaves — the proof gate MUST leave these candidate (never persisted as proven)
NEGATIVE_SPECS: list[dict[str, Any]] = [
    {"id": "prim:leaf:WRONG_expected_reverse", "capability": "seq_reverse with a wrong expected output",
     "mutator": "seq_reverse", "fixture": [1, 2, 3], "expected": [1, 2, 3], "args": {},
     "input_edge": _L, "output_edge": _L},
]


def _prove_one(spec: dict[str, Any]) -> dict[str, Any]:
    receipt = run_primitive_proof(
        spec["id"], spec["mutator"], spec["fixture"], spec["expected"],
        mutator_args=spec.get("args") or {}, has_inverse=spec.get("inverse"),
    )
    receipt["capability"] = spec["capability"]
    receipt["input_edge"] = spec["input_edge"]
    receipt["output_edge"] = spec["output_edge"]
    return receipt


def prove_all() -> list[dict[str, Any]]:
    """Run every declared leaf primitive through the imported executed-proof runner."""
    return [_prove_one(s) for s in LEAF_SPECS]


def proven_primitive_index() -> dict[str, dict[str, Any]]:
    """{primitive_id -> ProofReceipt} for leaves whose executed proof PASSED (serves_truth=true)."""
    return {r["primitive_id"]: r for r in prove_all() if r["serves_truth"] is True}


def build_rows() -> list[dict[str, Any]]:
    """The persisted rows: ONLY proven leaves, each TYPED with canonical input/output edge type ids so it can chain."""
    index = proven_primitive_index()
    rows: list[dict[str, Any]] = []
    for pid in sorted(index):
        r = index[pid]
        input_edge = r["input_edge"]
        output_edge = r["output_edge"]
        rows.append({
            "record_type": "proven_leaf_primitive",
            "family": FAMILY,
            "primitive_id": r["primitive_id"],
            "mutator": r["mutator"],
            "capability": r["capability"],
            "serves_truth": True,
            "candidate": False,
            "verification_level": "L7_executed_proof",
            "input_edge": input_edge,
            "output_edge": output_edge,
            "input_edge_type_id": canonicalize_edge(input_edge),
            "output_edge_type_id": canonicalize_edge(output_edge),
            "proofs": r["proofs"],
            "input_hash": r["input_hash"],
            "output_hash": r["output_hash"],
        })
    return rows


def build_manifest(rows: list[dict[str, Any]], *, date: str) -> dict[str, Any]:
    typed = [r for r in rows if r["input_edge_type_id"] and r["output_edge_type_id"]]
    canonical = "\n".join(json.dumps(r, sort_keys=True, ensure_ascii=False) for r in rows)
    return {
        "record_type": "proven_list_sequence_manifest",
        "pack_id": "proven-list-sequence-primitives",
        "generator": "scripts/prove_leaves_list_sequence.py",
        "family": FAMILY,
        "generated_utc": date,
        "declared_leaf_count": len(LEAF_SPECS),
        "proven_count": len(rows),
        "typed_count": len(typed),
        "proven_primitive_ids": sorted(r["primitive_id"] for r in rows),
        "verification_level": "L7_executed_proof",
        "roundtrip_pairs": sorted(
            [s["mutator"], s["inverse"]] for s in LEAF_SPECS if s.get("inverse")),
        "row_counts": {OUT_JSONL.name: len(rows)},
        "total_rows": len(rows),
        "note": "serves_truth=true here is CORRECT + required — set ONLY by an executed passing proof "
                "(run_primitive_proof, imported from scripts/mutator_registry.py); every persisted row is TYPED via "
                "canonicalize_edge (imported from scripts/build_edge_type_retrofit.py) so it can chain. A "
                "deliberately-wrong leaf stays candidate and is never persisted here.",
        "content_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
    }


def write_pack(*, date: str) -> dict[str, Any]:
    rows = build_rows()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSONL.write_text(
        "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows), encoding="utf-8")
    manifest = build_manifest(rows, date=date)
    OUT_MANIFEST.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def self_test() -> int:
    receipts = prove_all()
    index = proven_primitive_index()
    rows = build_rows()
    ids = [r["primitive_id"] for r in receipts]

    # a deliberately-wrong leaf must stay candidate (the gate is real, not a rubber stamp)
    wrong = _prove_one(NEGATIVE_SPECS[0])
    # a second wrong path: a fixture the mutator cannot handle -> execution error -> not promoted
    err = run_primitive_proof("prim:leaf:EXEC_ERROR", "seq_head", [], "irrelevant")

    roundtrip_specs = [s for s in LEAF_SPECS if s.get("inverse")]

    checks: list[tuple[str, bool]] = [
        (">=28 leaf primitives declared", len(LEAF_SPECS) >= 28),
        ("unique primitive ids", len(set(ids)) == len(ids)),
        ("EVERY declared leaf PROVES serves_truth=true via an executed proof",
         all(r["serves_truth"] is True and r["promoted"] is True for r in receipts)),
        ("every proven receipt is L7_executed_proof with all sub-proofs passing",
         all(r["verification_level"] == "L7_executed_proof" and all(p["passed"] for p in r["proofs"]) for r in receipts)),
        (">=28 primitives PROVEN in the index", len(index) >= 28),
        (">=28 rows persisted", len(rows) >= 28),
        ("EVERY persisted row carries a non-null input_edge_type_id",
         all(bool(r["input_edge_type_id"]) for r in rows)),
        ("EVERY persisted row carries a non-null output_edge_type_id",
         all(bool(r["output_edge_type_id"]) for r in rows)),
        ("no persisted edge type folds to Unknown",
         all(r["input_edge_type_id"] != "Unknown" and r["output_edge_type_id"] != "Unknown" for r in rows)),
        ("every persisted row is serves_truth=true / candidate=false / typed family",
         all(r["serves_truth"] is True and r["candidate"] is False and r["family"] == FAMILY for r in rows)),
        ("typed_count == proven_count (every workable leaf is typed)",
         build_manifest(rows, date="X")["typed_count"] == build_manifest(rows, date="X")["proven_count"]),
        ("roundtrip-inverse pairs actually PROVE reversibility", all(
            any(p["name"] == "roundtrip_test" and p["passed"] for p in index[s["id"]]["proofs"])
            for s in roundtrip_specs)),
        (">=5 roundtrip-inverse pairs proven", len(roundtrip_specs) >= 5),
        ("deterministic: re-running yields identical rows",
         [json.dumps(r, sort_keys=True) for r in build_rows()] == [json.dumps(r, sort_keys=True) for r in rows]),
        ("a deliberately-wrong leaf stays CANDIDATE (never promoted)",
         wrong["serves_truth"] is False and wrong["promoted"] is False),
        ("the wrong leaf is NOT persisted", wrong["primitive_id"] not in {r["primitive_id"] for r in rows}),
        ("an un-runnable fixture fails the proof, does not promote",
         err["serves_truth"] is False and err["promoted"] is False),
        ("new mutators registered into the shared registry (add-only seam)",
         all(m in MUTATOR_REGISTRY for m in _NEW_MUTATORS)),
    ]
    failed = [n for n, ok in checks if not ok]
    if failed:
        print("FAIL - prove_leaves_list_sequence:\n  " + "\n  ".join(failed))
        return 1
    print(f"PASS - prove_leaves_list_sequence: {len(rows)} REAL list_sequence leaf primitives PROVEN end-to-end "
          f"(serves_truth=true, L7_executed_proof) AND TYPED (input/output_edge_type_id via canonicalize_edge); "
          f"{len(roundtrip_specs)} roundtrip-inverse pairs proven reversible; a deliberately-wrong leaf and an "
          "un-runnable fixture correctly stay candidate. Workable = proven + typed.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--date", default=None)
    args = parser.parse_args(argv)
    if args.self_test and not args.write:
        return self_test()
    date = args.date or DEFAULT_DATE
    manifest = write_pack(date=date)
    print(json.dumps({k: v for k, v in manifest.items() if k != "content_sha256"}, indent=2, sort_keys=True))
    return self_test()


if __name__ == "__main__":
    raise SystemExit(main())
