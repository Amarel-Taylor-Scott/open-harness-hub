#!/usr/bin/env python3
"""mint_collections_pack — author REAL, oracle-tested primitives for the COLLECTION / data-structure-ops vertical.

Each SPEC below is a genuine, deterministic, STDLIB-only Python capability (group-by, flatten, chunk, merge, invert,
frequency map, partition, transpose, sliding window, set ops, rotate, …). Bodies take one argument ``x``; composite
inputs are passed as a tuple (e.g. ``run((seq, n))`` for chunk). Every oracle carries >= 2 STRICT equality assertions.

The batch is validated + minted through ``scripts.mint_vertical_pack.mint_pack`` (ast.parse -> exec -> ORACLE gate):
only oracle-passing cards are appended, as ``candidate=true, serves_truth=false`` (never promoted truth).

    PYTHONPATH=. python3 scripts/mint_collections_pack.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

_REPO = Path(__file__).resolve().parent.parent
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from scripts.mint_vertical_pack import mint_pack  # noqa: E402


def _collection_specs() -> list[dict[str, Any]]:
    return [
        # 1. group-by key ------------------------------------------------------------------------------------------
        {
            "title": "Group Dict List Into Buckets By Key Field",
            "blackbox": "Groups a list of dicts into a mapping from each distinct value of a key field to the list of "
                        "dicts having that value (input order preserved within each bucket).",
            "input_edge": "DictListWithGroupKey", "output_edge": "GroupedDictBuckets",
            "capability_tags": ["group_by", "collection", "dict_list", "aggregate"],
            "domains": ["collections"],
            "body": (
                "def run(x):\n"
                "    items, key = x\n"
                "    out = {}\n"
                "    for item in items:\n"
                "        out.setdefault(item[key], []).append(item)\n"
                "    return out\n"
            ),
            "oracle": lambda run: (
                run(([{"t": "a", "v": 1}, {"t": "b", "v": 2}, {"t": "a", "v": 3}], "t"))
                == {"a": [{"t": "a", "v": 1}, {"t": "a", "v": 3}], "b": [{"t": "b", "v": 2}]}
                and run(([{"g": 1}], "g")) == {1: [{"g": 1}]}
                and run(([], "t")) == {}
            ),
        },
        # 2. flatten nested list, one level -----------------------------------------------------------------------
        {
            "title": "Flatten List Of Lists By One Level",
            "blackbox": "Concatenates a list of sublists into a single flat list, descending exactly one level.",
            "input_edge": "ListOfLists", "output_edge": "OneLevelFlatList",
            "capability_tags": ["flatten", "collection", "concat", "one_level"],
            "domains": ["collections"],
            "body": (
                "import itertools\n"
                "def run(x):\n"
                "    return list(itertools.chain.from_iterable(x))\n"
            ),
            "oracle": lambda run: (
                run([[1, 2], [3, 4], [5]]) == [1, 2, 3, 4, 5]
                and run([[], ["a"], ["b", "c"]]) == ["a", "b", "c"]
                and run([]) == []
            ),
        },
        # 3. flatten deep ------------------------------------------------------------------------------------------
        {
            "title": "Flatten Arbitrarily Nested List Fully",
            "blackbox": "Recursively flattens a list nested to any depth into a single flat list of its leaf items "
                        "(non-list leaves, including strings, are kept intact).",
            "input_edge": "DeeplyNestedList", "output_edge": "FullyFlatList",
            "capability_tags": ["flatten", "collection", "recursive", "deep"],
            "domains": ["collections"],
            "body": (
                "def run(x):\n"
                "    out = []\n"
                "    def walk(seq):\n"
                "        for item in seq:\n"
                "            if isinstance(item, list):\n"
                "                walk(item)\n"
                "            else:\n"
                "                out.append(item)\n"
                "    walk(x)\n"
                "    return out\n"
            ),
            "oracle": lambda run: (
                run([1, [2, [3, [4]]], 5]) == [1, 2, 3, 4, 5]
                and run([[[["deep"]]]]) == ["deep"]
                and run([1, 2, 3]) == [1, 2, 3]
            ),
        },
        # 4. chunk into size-n batches -----------------------------------------------------------------------------
        {
            "title": "Chunk Sequence Into Fixed Size Batches",
            "blackbox": "Splits a sequence into consecutive batches of at most n items; the final batch holds the "
                        "remainder.",
            "input_edge": "SequenceWithChunkSize", "output_edge": "FixedSizeBatches",
            "capability_tags": ["chunk", "batch", "collection", "window"],
            "domains": ["collections"],
            "body": (
                "def run(x):\n"
                "    seq, n = x\n"
                "    return [seq[i:i + n] for i in range(0, len(seq), n)]\n"
            ),
            "oracle": lambda run: (
                run(([1, 2, 3, 4, 5], 2)) == [[1, 2], [3, 4], [5]]
                and run(([1, 2, 3, 4, 5, 6], 3)) == [[1, 2, 3], [4, 5, 6]]
                and run(([], 4)) == []
            ),
        },
        # 5. unique preserving order -------------------------------------------------------------------------------
        {
            "title": "Deduplicate Sequence Preserving First Seen Order",
            "blackbox": "Removes duplicate items from a sequence, keeping the first occurrence of each in its "
                        "original position.",
            "input_edge": "SequenceWithDuplicates", "output_edge": "OrderPreservedUniqueList",
            "capability_tags": ["unique", "dedupe", "collection", "order_preserving"],
            "domains": ["collections"],
            "body": (
                "def run(x):\n"
                "    seen = set()\n"
                "    out = []\n"
                "    for item in x:\n"
                "        if item not in seen:\n"
                "            seen.add(item)\n"
                "            out.append(item)\n"
                "    return out\n"
            ),
            "oracle": lambda run: (
                run([1, 2, 1, 3, 2, 4]) == [1, 2, 3, 4]
                and run(["a", "b", "a", "c"]) == ["a", "b", "c"]
                and run([]) == []
            ),
        },
        # 6. merge two dicts (right wins) --------------------------------------------------------------------------
        {
            "title": "Merge Two Dicts Right Operand Wins",
            "blackbox": "Shallow-merges two dicts into a new dict; on key collision the second (right) operand's "
                        "value wins. Inputs are not mutated.",
            "input_edge": "DictPairToMerge", "output_edge": "ShallowMergedDict",
            "capability_tags": ["merge", "dict", "collection", "override"],
            "domains": ["collections"],
            "body": (
                "def run(x):\n"
                "    a, b = x\n"
                "    out = dict(a)\n"
                "    out.update(b)\n"
                "    return out\n"
            ),
            "oracle": lambda run: (
                run(({"a": 1, "b": 2}, {"b": 3, "c": 4})) == {"a": 1, "b": 3, "c": 4}
                and run(({}, {"x": 1})) == {"x": 1}
                and run(({"k": 1}, {})) == {"k": 1}
            ),
        },
        # 7. deep-merge dicts --------------------------------------------------------------------------------------
        {
            "title": "Deep Merge Two Nested Dicts Right Wins",
            "blackbox": "Recursively merges two nested dicts; where both hold a dict at the same key the dicts are "
                        "merged, otherwise the right value wins. Inputs are not mutated.",
            "input_edge": "NestedDictPairToMerge", "output_edge": "DeepMergedDict",
            "capability_tags": ["deep_merge", "dict", "collection", "recursive"],
            "domains": ["collections"],
            "body": (
                "def run(x):\n"
                "    a, b = x\n"
                "    def merge(d1, d2):\n"
                "        out = dict(d1)\n"
                "        for k, v in d2.items():\n"
                "            if k in out and isinstance(out[k], dict) and isinstance(v, dict):\n"
                "                out[k] = merge(out[k], v)\n"
                "            else:\n"
                "                out[k] = v\n"
                "        return out\n"
                "    return merge(a, b)\n"
            ),
            "oracle": lambda run: (
                run(({"a": {"x": 1, "y": 2}}, {"a": {"y": 3, "z": 4}})) == {"a": {"x": 1, "y": 3, "z": 4}}
                and run(({"a": 1}, {"b": 2})) == {"a": 1, "b": 2}
                and run(({"a": {"x": 1}}, {"a": 9})) == {"a": 9}
            ),
        },
        # 8. invert a dict -----------------------------------------------------------------------------------------
        {
            "title": "Invert Dict Swapping Keys And Values",
            "blackbox": "Builds a new dict mapping each value back to its key (assumes values are hashable and "
                        "distinct).",
            "input_edge": "DictToInvert", "output_edge": "InvertedDict",
            "capability_tags": ["invert", "dict", "collection", "reverse_map"],
            "domains": ["collections"],
            "body": (
                "def run(x):\n"
                "    return {v: k for k, v in x.items()}\n"
            ),
            "oracle": lambda run: (
                run({"a": 1, "b": 2}) == {1: "a", 2: "b"}
                and run({"x": "y"}) == {"y": "x"}
                and run({}) == {}
            ),
        },
        # 9. pick keys from dict -----------------------------------------------------------------------------------
        {
            "title": "Pick Subset Of Keys From Dict",
            "blackbox": "Returns a new dict containing only the requested keys that are present in the source dict.",
            "input_edge": "DictWithKeysToPick", "output_edge": "PickedSubsetDict",
            "capability_tags": ["pick", "dict", "collection", "subset"],
            "domains": ["collections"],
            "body": (
                "def run(x):\n"
                "    d, keys = x\n"
                "    return {k: d[k] for k in keys if k in d}\n"
            ),
            "oracle": lambda run: (
                run(({"a": 1, "b": 2, "c": 3}, ["a", "c"])) == {"a": 1, "c": 3}
                and run(({"a": 1}, ["a", "z"])) == {"a": 1}
                and run(({"a": 1}, [])) == {}
            ),
        },
        # 10. omit keys from dict ----------------------------------------------------------------------------------
        {
            "title": "Omit Subset Of Keys From Dict",
            "blackbox": "Returns a new dict with the requested keys removed; keys not present are ignored.",
            "input_edge": "DictWithKeysToOmit", "output_edge": "OmittedSubsetDict",
            "capability_tags": ["omit", "dict", "collection", "drop_keys"],
            "domains": ["collections"],
            "body": (
                "def run(x):\n"
                "    d, keys = x\n"
                "    drop = set(keys)\n"
                "    return {k: v for k, v in d.items() if k not in drop}\n"
            ),
            "oracle": lambda run: (
                run(({"a": 1, "b": 2, "c": 3}, ["b"])) == {"a": 1, "c": 3}
                and run(({"a": 1, "b": 2}, ["a", "b"])) == {}
                and run(({"a": 1}, ["z"])) == {"a": 1}
            ),
        },
        # 11. count occurrences (frequency map) --------------------------------------------------------------------
        {
            "title": "Count Occurrences Into Frequency Map",
            "blackbox": "Counts how many times each distinct item appears in a sequence, returning a value->count "
                        "mapping.",
            "input_edge": "SequenceToCount", "output_edge": "FrequencyMap",
            "capability_tags": ["count", "frequency", "collection", "histogram"],
            "domains": ["collections"],
            "body": (
                "import collections\n"
                "def run(x):\n"
                "    return dict(collections.Counter(x))\n"
            ),
            "oracle": lambda run: (
                run(["a", "b", "a", "c", "a"]) == {"a": 3, "b": 1, "c": 1}
                and run([1, 1, 2]) == {1: 2, 2: 1}
                and run([]) == {}
            ),
        },
        # 12. partition by predicate-key ---------------------------------------------------------------------------
        {
            "title": "Partition Dict List By Truthiness Of Key",
            "blackbox": "Splits a list of dicts into two lists: those whose value at the given key is truthy, and "
                        "those whose value is falsy (input order preserved in each).",
            "input_edge": "DictListWithPartitionKey", "output_edge": "TruthyFalsyPartition",
            "capability_tags": ["partition", "dict_list", "collection", "predicate"],
            "domains": ["collections"],
            "body": (
                "def run(x):\n"
                "    items, key = x\n"
                "    yes, no = [], []\n"
                "    for item in items:\n"
                "        (yes if item.get(key) else no).append(item)\n"
                "    return [yes, no]\n"
            ),
            "oracle": lambda run: (
                run(([{"ok": True, "id": 1}, {"ok": False, "id": 2}, {"ok": True, "id": 3}], "ok"))
                == [[{"ok": True, "id": 1}, {"ok": True, "id": 3}], [{"ok": False, "id": 2}]]
                and run(([{"a": 1}, {"a": 0}], "a")) == [[{"a": 1}], [{"a": 0}]]
                and run(([], "a")) == [[], []]
            ),
        },
        # 13. zip two lists to dict --------------------------------------------------------------------------------
        {
            "title": "Zip Key List And Value List Into Dict",
            "blackbox": "Pairs a list of keys with a list of values positionally into a dict; extra unpaired items "
                        "are dropped.",
            "input_edge": "KeyListAndValueList", "output_edge": "ZippedDict",
            "capability_tags": ["zip", "dict", "collection", "pair"],
            "domains": ["collections"],
            "body": (
                "def run(x):\n"
                "    keys, values = x\n"
                "    return dict(zip(keys, values))\n"
            ),
            "oracle": lambda run: (
                run((["a", "b", "c"], [1, 2, 3])) == {"a": 1, "b": 2, "c": 3}
                and run((["x"], [9])) == {"x": 9}
                and run((["a", "b"], [1])) == {"a": 1}
            ),
        },
        # 14. sort list of dicts by key ----------------------------------------------------------------------------
        {
            "title": "Sort Dict List Ascending By Key Field",
            "blackbox": "Returns a new list of dicts sorted ascending by the value at the given key (stable sort).",
            "input_edge": "DictListWithSortKey", "output_edge": "AscendingSortedDictList",
            "capability_tags": ["sort", "dict_list", "collection", "order_by"],
            "domains": ["collections"],
            "body": (
                "def run(x):\n"
                "    items, key = x\n"
                "    return sorted(items, key=lambda d: d[key])\n"
            ),
            "oracle": lambda run: (
                run(([{"n": 3}, {"n": 1}, {"n": 2}], "n")) == [{"n": 1}, {"n": 2}, {"n": 3}]
                and run(([{"name": "c"}, {"name": "a"}, {"name": "b"}], "name"))
                == [{"name": "a"}, {"name": "b"}, {"name": "c"}]
                and run(([], "n")) == []
            ),
        },
        # 15. top-n by key -----------------------------------------------------------------------------------------
        {
            "title": "Select Top N Dicts By Descending Key Field",
            "blackbox": "Returns the n dicts with the largest value at the given key, ordered from highest to lowest "
                        "(stable on ties).",
            "input_edge": "DictListWithKeyAndCount", "output_edge": "TopNDictList",
            "capability_tags": ["top_n", "dict_list", "collection", "rank"],
            "domains": ["collections"],
            "body": (
                "def run(x):\n"
                "    items, key, n = x\n"
                "    return sorted(items, key=lambda d: d[key], reverse=True)[:n]\n"
            ),
            "oracle": lambda run: (
                run(([{"s": 5}, {"s": 1}, {"s": 9}, {"s": 3}], "s", 2)) == [{"s": 9}, {"s": 5}]
                and run(([{"p": 1}, {"p": 2}], "p", 1)) == [{"p": 2}]
                and run(([{"p": 1}], "p", 5)) == [{"p": 1}]
            ),
        },
        # 16. running sum / cumsum ---------------------------------------------------------------------------------
        {
            "title": "Compute Running Cumulative Sum Of Numbers",
            "blackbox": "Returns the running (prefix) sums of a numeric sequence: each output item is the sum of all "
                        "inputs up to and including that position.",
            "input_edge": "NumberSequenceToAccumulate", "output_edge": "CumulativeSumList",
            "capability_tags": ["cumsum", "prefix_sum", "collection", "accumulate"],
            "domains": ["collections"],
            "body": (
                "import itertools\n"
                "def run(x):\n"
                "    return list(itertools.accumulate(x))\n"
            ),
            "oracle": lambda run: (
                run([1, 2, 3, 4]) == [1, 3, 6, 10]
                and run([5, 0, 5]) == [5, 5, 10]
                and run([]) == []
            ),
        },
        # 17. transpose list-of-lists ------------------------------------------------------------------------------
        {
            "title": "Transpose Rectangular List Of Rows",
            "blackbox": "Transposes a rectangular list of rows into a list of columns (rows become columns).",
            "input_edge": "ListOfRows", "output_edge": "TransposedListOfColumns",
            "capability_tags": ["transpose", "matrix", "collection", "pivot"],
            "domains": ["collections"],
            "body": (
                "def run(x):\n"
                "    return [list(col) for col in zip(*x)]\n"
            ),
            "oracle": lambda run: (
                run([[1, 2, 3], [4, 5, 6]]) == [[1, 4], [2, 5], [3, 6]]
                and run([[1, 2], [3, 4], [5, 6]]) == [[1, 3, 5], [2, 4, 6]]
                and run([[1], [2]]) == [[1, 2]]
            ),
        },
        # 18. index list-of-dicts by key ---------------------------------------------------------------------------
        {
            "title": "Index Dict List Into Lookup Map By Key",
            "blackbox": "Builds a lookup dict from a list of dicts keyed by the value at the given field; later "
                        "duplicates overwrite earlier ones.",
            "input_edge": "DictListWithIndexKey", "output_edge": "KeyedLookupMap",
            "capability_tags": ["index", "dict_list", "collection", "lookup"],
            "domains": ["collections"],
            "body": (
                "def run(x):\n"
                "    items, key = x\n"
                "    return {item[key]: item for item in items}\n"
            ),
            "oracle": lambda run: (
                run(([{"id": "a", "v": 1}, {"id": "b", "v": 2}], "id"))
                == {"a": {"id": "a", "v": 1}, "b": {"id": "b", "v": 2}}
                and run(([{"id": 1}, {"id": 2}], "id")) == {1: {"id": 1}, 2: {"id": 2}}
                and run(([], "id")) == {}
            ),
        },
        # 19. rename dict keys via map -----------------------------------------------------------------------------
        {
            "title": "Rename Dict Keys Through Rename Map",
            "blackbox": "Returns a new dict with keys renamed per a mapping; keys absent from the mapping are kept "
                        "unchanged. Values are preserved.",
            "input_edge": "DictWithRenameMap", "output_edge": "RenamedKeyDict",
            "capability_tags": ["rename", "dict", "collection", "remap_keys"],
            "domains": ["collections"],
            "body": (
                "def run(x):\n"
                "    d, mapping = x\n"
                "    return {mapping.get(k, k): v for k, v in d.items()}\n"
            ),
            "oracle": lambda run: (
                run(({"a": 1, "b": 2}, {"a": "alpha"})) == {"alpha": 1, "b": 2}
                and run(({"x": 1}, {"x": "y", "z": "w"})) == {"y": 1}
                and run(({"a": 1}, {})) == {"a": 1}
            ),
        },
        # 20. filter dict by value predicate-value -----------------------------------------------------------------
        {
            "title": "Filter Dict Entries By Minimum Value Threshold",
            "blackbox": "Returns a new dict keeping only entries whose value is greater than or equal to the given "
                        "threshold.",
            "input_edge": "DictWithValueThreshold", "output_edge": "ThresholdFilteredDict",
            "capability_tags": ["filter", "dict", "collection", "threshold"],
            "domains": ["collections"],
            "body": (
                "def run(x):\n"
                "    d, threshold = x\n"
                "    return {k: v for k, v in d.items() if v >= threshold}\n"
            ),
            "oracle": lambda run: (
                run(({"a": 1, "b": 5, "c": 3}, 3)) == {"b": 5, "c": 3}
                and run(({"a": 10, "b": 2}, 20)) == {}
                and run(({"a": 5}, 5)) == {"a": 5}
            ),
        },
        # 21. sliding window of size n -----------------------------------------------------------------------------
        {
            "title": "Slide Fixed Size Window Over Sequence",
            "blackbox": "Returns every consecutive contiguous window of exactly n items across the sequence; empty "
                        "when the sequence is shorter than n.",
            "input_edge": "SequenceWithWindowSize", "output_edge": "SlidingWindowList",
            "capability_tags": ["sliding_window", "collection", "window", "ngram"],
            "domains": ["collections"],
            "body": (
                "def run(x):\n"
                "    seq, n = x\n"
                "    return [seq[i:i + n] for i in range(len(seq) - n + 1)]\n"
            ),
            "oracle": lambda run: (
                run(([1, 2, 3, 4], 2)) == [[1, 2], [2, 3], [3, 4]]
                and run(([1, 2, 3], 3)) == [[1, 2, 3]]
                and run(([1, 2], 3)) == []
            ),
        },
        # 22. dedupe list-of-dicts by key --------------------------------------------------------------------------
        {
            "title": "Deduplicate Dict List By Key Keeping First",
            "blackbox": "Removes dicts whose value at the given key was already seen, keeping the first dict per "
                        "distinct key value (input order preserved).",
            "input_edge": "DictListWithDedupeKey", "output_edge": "KeyDedupedDictList",
            "capability_tags": ["dedupe", "dict_list", "collection", "unique_by_key"],
            "domains": ["collections"],
            "body": (
                "def run(x):\n"
                "    items, key = x\n"
                "    seen = set()\n"
                "    out = []\n"
                "    for item in items:\n"
                "        k = item[key]\n"
                "        if k not in seen:\n"
                "            seen.add(k)\n"
                "            out.append(item)\n"
                "    return out\n"
            ),
            "oracle": lambda run: (
                run(([{"id": 1, "v": "a"}, {"id": 2, "v": "b"}, {"id": 1, "v": "c"}], "id"))
                == [{"id": 1, "v": "a"}, {"id": 2, "v": "b"}]
                and run(([{"k": "x"}, {"k": "x"}, {"k": "y"}], "k")) == [{"k": "x"}, {"k": "y"}]
                and run(([], "id")) == []
            ),
        },
        # 23. set difference of two lists --------------------------------------------------------------------------
        {
            "title": "Ordered List Difference First Minus Second",
            "blackbox": "Returns the items of the first list that do not appear in the second, preserving the first "
                        "list's order (duplicates in the first are each kept unless excluded).",
            "input_edge": "ListPairForDifference", "output_edge": "OrderedListDifference",
            "capability_tags": ["set_difference", "collection", "list", "exclude"],
            "domains": ["collections"],
            "body": (
                "def run(x):\n"
                "    a, b = x\n"
                "    bs = set(b)\n"
                "    return [item for item in a if item not in bs]\n"
            ),
            "oracle": lambda run: (
                run(([1, 2, 3, 4], [2, 4])) == [1, 3]
                and run((["a", "b"], ["a"])) == ["b"]
                and run(([1, 2], [1, 2, 3])) == []
            ),
        },
        # 24. set intersection of two lists ------------------------------------------------------------------------
        {
            "title": "Ordered List Intersection Preserving First Order",
            "blackbox": "Returns the distinct items present in both lists, ordered by their first appearance in the "
                        "first list.",
            "input_edge": "ListPairForIntersection", "output_edge": "OrderedListIntersection",
            "capability_tags": ["set_intersection", "collection", "list", "common"],
            "domains": ["collections"],
            "body": (
                "def run(x):\n"
                "    a, b = x\n"
                "    bs = set(b)\n"
                "    seen = set()\n"
                "    out = []\n"
                "    for item in a:\n"
                "        if item in bs and item not in seen:\n"
                "            seen.add(item)\n"
                "            out.append(item)\n"
                "    return out\n"
            ),
            "oracle": lambda run: (
                run(([1, 2, 3, 4], [2, 4, 5])) == [2, 4]
                and run(([1, 1, 2], [1])) == [1]
                and run(([1, 2], [3, 4])) == []
            ),
        },
        # 25. set union of two lists -------------------------------------------------------------------------------
        {
            "title": "Ordered List Union Preserving First Seen Order",
            "blackbox": "Returns the distinct items from both lists combined, ordered by first appearance across the "
                        "first list then the second.",
            "input_edge": "ListPairForUnion", "output_edge": "OrderedListUnion",
            "capability_tags": ["set_union", "collection", "list", "combine"],
            "domains": ["collections"],
            "body": (
                "def run(x):\n"
                "    a, b = x\n"
                "    seen = set()\n"
                "    out = []\n"
                "    for item in list(a) + list(b):\n"
                "        if item not in seen:\n"
                "            seen.add(item)\n"
                "            out.append(item)\n"
                "    return out\n"
            ),
            "oracle": lambda run: (
                run(([1, 2, 3], [2, 3, 4])) == [1, 2, 3, 4]
                and run((["a"], ["b", "a"])) == ["a", "b"]
                and run(([], [1, 1, 2])) == [1, 2]
            ),
        },
        # 26. rotate a list by k -----------------------------------------------------------------------------------
        {
            "title": "Rotate List Left By K Positions",
            "blackbox": "Rotates a list left by k positions (k is reduced modulo the length, so k >= length wraps "
                        "around); the first k items move to the end.",
            "input_edge": "SequenceWithRotationOffset", "output_edge": "LeftRotatedList",
            "capability_tags": ["rotate", "collection", "list", "shift"],
            "domains": ["collections"],
            "body": (
                "def run(x):\n"
                "    seq, k = x\n"
                "    if not seq:\n"
                "        return list(seq)\n"
                "    k = k % len(seq)\n"
                "    return list(seq[k:]) + list(seq[:k])\n"
            ),
            "oracle": lambda run: (
                run(([1, 2, 3, 4, 5], 2)) == [3, 4, 5, 1, 2]
                and run(([1, 2, 3], 3)) == [1, 2, 3]
                and run(([1, 2, 3, 4], 1)) == [2, 3, 4, 1]
            ),
        },
    ]


def main() -> int:
    specs = _collection_specs()
    out_path = _REPO / "data" / "dev-intel" / "aidevobserver_edge_foundry" / "minted_collections_pack_cards.jsonl"
    rec = mint_pack(specs, out_path=out_path)

    print(f"specs      = {rec['specs']}")
    print(f"valid_syntax = {rec['valid_syntax']}")
    print(f"working    = {rec['working']}")
    print(f"appended   = {rec['appended']}")
    print(f"pack_path  = {rec['out']}")
    print(f"failed     = {json.dumps(rec['failed'], indent=2)}")
    titles = [c["title"] for c in rec["cards"]]
    print(f"example_titles (first 5) = {json.dumps(titles[:5], indent=2)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
