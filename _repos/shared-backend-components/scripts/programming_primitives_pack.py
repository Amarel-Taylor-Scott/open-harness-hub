#!/usr/bin/env python3
"""scripts.programming_primitives_pack — a broad batch of common PROGRAMMING/DEVELOPMENT primitives with oracle
fixtures (candidate-only). The high-frequency, high-addressability core.

Owner (2026-07-09): the verified set is still tiny and skewed to esoteric formats — grow it toward real
programming/development tasks. These are the everyday string/list/dict/math/algorithm utilities that appear in
nearly EVERY dev session (so they lift addressable_rate the most). Each is a self-contained, pure function whose
executor body IS inspect.getsource(fn) (inline imports; standalone-certifiable), proven by ORACLE fixtures the
self-test runs. candidate=true / serves_truth=false; immediately certifiable via the campaign, no LLM lane.

    python3 scripts/programming_primitives_pack.py --self-test
    python3 scripts/programming_primitives_pack.py --emit
"""
from __future__ import annotations

import sys
from pathlib import Path

# ── substrate-root bootstrap (sentinel; mirrors scripts/ml_lifecycle_primitive_minter.py) ────────────────────
_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots, resource  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import inspect  # noqa: E402
import json  # noqa: E402
from typing import Any, Callable  # noqa: E402

try:
    from src.teleon.experiments.ids import canonical_id  # noqa: E402
except Exception as exc:  # noqa: BLE001
    raise SystemExit(f"programming_primitives_pack requires canonical_id; import failed: {exc}")

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
PROG_ID_PREFIX = "prim-prog"
PROG_RECORD_TYPE = "programming_primitive_candidate"
PACK_FILENAME = "programming_primitive_cards.jsonl"
PACK_DIR_REL = "data/dev-intel/primitive_factory/specialized_packs"
PACKAGED_AT = "2026-07-09T00:00:00Z"


# ── STRING ───────────────────────────────────────────────────────────────────────────────────────────────────
def camel_to_snake(text: str) -> str:
    """Programming/string: 'camelCaseName' -> 'camel_case_name'."""
    import re
    return re.sub(r"(?<!^)(?=[A-Z])", "_", text).lower()


def snake_to_camel(text: str) -> str:
    """Programming/string: 'snake_case_name' -> 'snakeCaseName'."""
    parts = text.split("_")
    return parts[0] + "".join(p[:1].upper() + p[1:] for p in parts[1:])


def truncate_ellipsis(text: str, width: int) -> str:
    """Programming/string: truncate to width with a trailing ellipsis if longer."""
    return text if len(text) <= width else text[: max(0, width - 3)] + "..."


def is_palindrome(text: str) -> bool:
    """Programming/string: case-insensitive alphanumeric palindrome check."""
    s = [c.lower() for c in text if c.isalnum()]
    return s == s[::-1]


def capitalize_words(text: str) -> str:
    """Programming/string: 'hello world' -> 'Hello World'."""
    return " ".join(w[:1].upper() + w[1:] for w in text.split(" "))


def remove_extra_spaces(text: str) -> str:
    """Programming/string: collapse internal whitespace runs to single spaces + trim."""
    return " ".join(text.split())


def count_char_frequency(text: str) -> dict:
    """Programming/string: character -> count."""
    out: dict = {}
    for c in text:
        out[c] = out.get(c, 0) + 1
    return out


def count_words(text: str) -> int:
    """Programming/string: number of whitespace-separated words."""
    return len(text.split())


# ── LIST ─────────────────────────────────────────────────────────────────────────────────────────────────────
def chunk_list(items: list, size: int) -> list:
    """Programming/list: split into consecutive chunks of `size` (last may be shorter)."""
    return [items[i:i + size] for i in range(0, len(items), size)]


def flatten_one_level(items: list) -> list:
    """Programming/list: flatten one level of nesting."""
    out: list = []
    for x in items:
        out.extend(x if isinstance(x, list) else [x])
    return out


def unique_preserve_order(items: list) -> list:
    """Programming/list: de-duplicate while preserving first-seen order."""
    seen: set = set()
    out: list = []
    for x in items:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def rotate_left(items: list, n: int) -> list:
    """Programming/list: rotate left by n (wraps)."""
    if not items:
        return []
    n %= len(items)
    return items[n:] + items[:n]


def sliding_window(items: list, size: int) -> list:
    """Programming/list: all consecutive windows of length `size`."""
    return [items[i:i + size] for i in range(len(items) - size + 1)] if size <= len(items) else []


def running_sum(items: list) -> list:
    """Programming/list: cumulative sums."""
    out: list = []
    total = 0
    for x in items:
        total += x
        out.append(total)
    return out


def partition_even_odd(items: list) -> list:
    """Programming/list: [[evens], [odds]] preserving order."""
    return [[x for x in items if x % 2 == 0], [x for x in items if x % 2 != 0]]


def top_k_largest(items: list, k: int) -> list:
    """Programming/list: the k largest values, descending."""
    return sorted(items, reverse=True)[:k]


def intersperse(items: list, sep: object) -> list:
    """Programming/list: insert `sep` between elements."""
    out: list = []
    for i, x in enumerate(items):
        if i:
            out.append(sep)
        out.append(x)
    return out


# ── DICT ─────────────────────────────────────────────────────────────────────────────────────────────────────
def deep_merge_dicts(a: dict, b: dict) -> dict:
    """Programming/dict: recursively merge b into a (b wins on scalar conflicts)."""
    out = dict(a)
    for k, v in b.items():
        out[k] = deep_merge_dicts(out[k], v) if isinstance(out.get(k), dict) and isinstance(v, dict) else v
    return out


def invert_dict(mapping: dict) -> dict:
    """Programming/dict: swap keys and values."""
    return {v: k for k, v in mapping.items()}


def pick_keys(mapping: dict, keys: list) -> dict:
    """Programming/dict: keep only the given keys that exist."""
    return {k: mapping[k] for k in keys if k in mapping}


def flatten_dict_dot(mapping: dict) -> dict:
    """Programming/dict: nested dict -> dotted-key flat dict."""
    out: dict = {}
    for k, v in mapping.items():
        if isinstance(v, dict):
            for ik, iv in flatten_dict_dot(v).items():
                out[f"{k}.{ik}"] = iv
        else:
            out[k] = v
    return out


# ── MATH ─────────────────────────────────────────────────────────────────────────────────────────────────────
def gcd_int(a: int, b: int) -> int:
    """Programming/math: greatest common divisor."""
    a, b = abs(a), abs(b)
    while b:
        a, b = b, a % b
    return a


def lcm_int(a: int, b: int) -> int:
    """Programming/math: least common multiple."""
    if a == 0 or b == 0:
        return 0
    x, y = abs(a), abs(b)
    g = x
    h = y
    while h:
        g, h = h, g % h
    return x // g * y


def clamp(value: int, low: int, high: int) -> int:
    """Programming/math: clamp value into [low, high]."""
    return low if value < low else high if value > high else value


def is_prime(n: int) -> bool:
    """Programming/math: primality test."""
    if n < 2:
        return False
    i = 2
    while i * i <= n:
        if n % i == 0:
            return False
        i += 1
    return True


def nth_fibonacci(n: int) -> int:
    """Programming/math: nth Fibonacci (fib(0)=0, fib(1)=1)."""
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def digit_sum(n: int) -> int:
    """Programming/math: sum of decimal digits (of abs value)."""
    return sum(int(c) for c in str(abs(n)))


def factorial_int(n: int) -> int:
    """Programming/math: n! for n >= 0."""
    r = 1
    for i in range(2, n + 1):
        r *= i
    return r


# ── ALGORITHM ───────────────────────────────────────────────────────────────────────────────────────────────
def binary_search(sorted_items: list, target: object) -> int:
    """Programming/algorithm: index of target in a sorted list, or -1."""
    lo, hi = 0, len(sorted_items) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if sorted_items[mid] == target:
            return mid
        if sorted_items[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1


def run_length_encode(text: str) -> str:
    """Programming/algorithm: 'aaabbc' -> 'a3b2c1'."""
    if not text:
        return ""
    out = []
    prev = text[0]
    count = 1
    for c in text[1:]:
        if c == prev:
            count += 1
        else:
            out.append(f"{prev}{count}")
            prev, count = c, 1
    out.append(f"{prev}{count}")
    return "".join(out)


def levenshtein_distance(a: str, b: str) -> int:
    """Programming/algorithm: edit distance between two strings."""
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def hamming_distance(a: str, b: str) -> int:
    """Programming/algorithm: positions where equal-length strings differ."""
    return sum(1 for x, y in zip(a, b) if x != y)


def caesar_cipher(text: str, shift: int) -> str:
    """Programming/algorithm: shift lowercase a-z by `shift` (wraps); non-letters unchanged."""
    out = []
    for c in text:
        if "a" <= c <= "z":
            out.append(chr((ord(c) - 97 + shift) % 26 + 97))
        else:
            out.append(c)
    return "".join(out)


# ── the table: (fn, category, input_edge, output_edge, fixtures) ─────────────────────────────────────────────
_PRIMITIVES: list[dict[str, Any]] = [
    {"fn": camel_to_snake, "cat": "string", "fixtures": [(("camelCaseName",), "camel_case_name"),
                                                          (("simple",), "simple")]},
    {"fn": snake_to_camel, "cat": "string", "fixtures": [(("snake_case_name",), "snakeCaseName"),
                                                         (("one",), "one")]},
    {"fn": truncate_ellipsis, "cat": "string", "fixtures": [(("hello world", 8), "hello..."),
                                                            (("hi", 8), "hi")]},
    {"fn": is_palindrome, "cat": "string", "fixtures": [(("Racecar",), True), (("hello",), False),
                                                        (("A man a plan a canal Panama",), True)]},
    {"fn": capitalize_words, "cat": "string", "fixtures": [(("hello world",), "Hello World"),
                                                           (("a b c",), "A B C")]},
    {"fn": remove_extra_spaces, "cat": "string", "fixtures": [(("a   b  c",), "a b c"), (("  x ",), "x")]},
    {"fn": count_char_frequency, "cat": "string", "fixtures": [(("aabbbc",), {"a": 2, "b": 3, "c": 1})]},
    {"fn": count_words, "cat": "string", "fixtures": [(("hello world foo",), 3), (("",), 0)]},
    {"fn": chunk_list, "cat": "list", "fixtures": [(([1, 2, 3, 4, 5], 2), [[1, 2], [3, 4], [5]])]},
    {"fn": flatten_one_level, "cat": "list", "fixtures": [(([[1, 2], [3], [4, 5]],), [1, 2, 3, 4, 5])]},
    {"fn": unique_preserve_order, "cat": "list", "fixtures": [(([1, 2, 1, 3, 2],), [1, 2, 3])]},
    {"fn": rotate_left, "cat": "list", "fixtures": [(([1, 2, 3, 4, 5], 2), [3, 4, 5, 1, 2]),
                                                    (([1, 2, 3], 3), [1, 2, 3])]},
    {"fn": sliding_window, "cat": "list", "fixtures": [(([1, 2, 3, 4], 2), [[1, 2], [2, 3], [3, 4]])]},
    {"fn": running_sum, "cat": "list", "fixtures": [(([1, 2, 3, 4],), [1, 3, 6, 10])]},
    {"fn": partition_even_odd, "cat": "list", "fixtures": [(([1, 2, 3, 4, 5, 6],), [[2, 4, 6], [1, 3, 5]])]},
    {"fn": top_k_largest, "cat": "list", "fixtures": [(([5, 1, 3, 2, 4], 3), [5, 4, 3])]},
    {"fn": intersperse, "cat": "list", "fixtures": [(([1, 2, 3], 0), [1, 0, 2, 0, 3])]},
    {"fn": deep_merge_dicts, "cat": "dict", "fixtures": [(({"a": {"x": 1}}, {"a": {"y": 2}}),
                                                          {"a": {"x": 1, "y": 2}})]},
    {"fn": invert_dict, "cat": "dict", "fixtures": [(({"a": 1, "b": 2},), {1: "a", 2: "b"})]},
    {"fn": pick_keys, "cat": "dict", "fixtures": [(({"a": 1, "b": 2, "c": 3}, ["a", "c"]), {"a": 1, "c": 3})]},
    {"fn": flatten_dict_dot, "cat": "dict", "fixtures": [(({"a": {"b": 1}, "c": 2},), {"a.b": 1, "c": 2})]},
    {"fn": gcd_int, "cat": "math", "fixtures": [((12, 18), 6), ((7, 13), 1), ((0, 5), 5)]},
    {"fn": lcm_int, "cat": "math", "fixtures": [((4, 6), 12), ((3, 5), 15)]},
    {"fn": clamp, "cat": "math", "fixtures": [((15, 0, 10), 10), ((-5, 0, 10), 0), ((5, 0, 10), 5)]},
    {"fn": is_prime, "cat": "math", "fixtures": [((7,), True), ((1,), False), ((9,), False), ((2,), True)]},
    {"fn": nth_fibonacci, "cat": "math", "fixtures": [((10,), 55), ((0,), 0), ((1,), 1)]},
    {"fn": digit_sum, "cat": "math", "fixtures": [((12345,), 15), ((0,), 0)]},
    {"fn": factorial_int, "cat": "math", "fixtures": [((5,), 120), ((0,), 1)]},
    {"fn": binary_search, "cat": "algorithm", "fixtures": [(([1, 3, 5, 7, 9], 7), 3), (([1, 3, 5], 4), -1)]},
    {"fn": run_length_encode, "cat": "algorithm", "fixtures": [(("aaabbc",), "a3b2c1"), (("",), "")]},
    {"fn": levenshtein_distance, "cat": "algorithm", "fixtures": [(("kitten", "sitting"), 3), (("a", "a"), 0)]},
    {"fn": hamming_distance, "cat": "algorithm", "fixtures": [(("1011101", "1001001"), 2)]},
    {"fn": caesar_cipher, "cat": "algorithm", "fixtures": [(("abc", 1), "bcd"), (("xyz", 3), "abc")]},
]


def build_cards() -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    for spec in _PRIMITIVES:
        fn: Callable = spec["fn"]
        name = fn.__name__
        body = inspect.getsource(fn)
        cid = canonical_id(PROG_ID_PREFIX, name, spec["cat"])
        cards.append({
            "record_type": PROG_RECORD_TYPE, "kind": "programming_deterministic_primitive",
            "card_id": cid, "primitive_id": cid,
            "title": f"{name} — programming/{spec['cat']} (deterministic)",
            "blackbox": (inspect.getdoc(fn) or "").replace("\n", " ").strip(),
            "domains": ["programming_primitive", spec["cat"], "developer_utility", "deterministic"],
            "candidate": True, "serves_truth": False, "category": spec["cat"],
            "executor": {"language": "python", "entry": name, "python_body": body,
                         "determinism": "pure_deterministic",
                         "oracle_fixtures": [{"input": repr(a), "expected": repr(e)} for a, e in spec["fixtures"]],
                         "n_fixtures": len(spec["fixtures"])},
            "lift_reason": "HIGH_FREQUENCY_DETERMINISTIC: everyday dev utility; reuse = 0-gen tokens + guaranteed "
                           "correct; broad addressability across every session.",
            "packaged_at": PACKAGED_AT,
        })
    return cards


def emit() -> dict[str, Any]:
    cards = build_cards()
    out_dir = resource(PACK_DIR_REL)
    out_dir.mkdir(parents=True, exist_ok=True)
    with (out_dir / PACK_FILENAME).open("w", encoding="utf-8") as fh:
        for c in cards:
            fh.write(json.dumps(c, sort_keys=True) + "\n")
    return {"pack_path": str(out_dir / PACK_FILENAME), "n_cards": len(cards),
            "categories": sorted({s["cat"] for s in _PRIMITIVES})}


def self_test() -> bool:
    """ORACLE-gated: every fixture reproduces; a broken impl / wrong fixture goes RED."""
    assert len(_PRIMITIVES) >= 30, f"expected >=30 programming primitives, got {len(_PRIMITIVES)}"
    total = 0
    for spec in _PRIMITIVES:
        fn = spec["fn"]
        for args, expected in spec["fixtures"]:
            got = fn(*args)
            assert got == expected, f"{fn.__name__}{args!r}: got {got!r}, expected {expected!r}"
            total += 1
    cards = build_cards()
    assert len({c["card_id"] for c in cards}) == len(cards), "duplicate ids"
    for c in cards:
        assert c["candidate"] is True and c["serves_truth"] is False
        assert c["executor"]["python_body"].lstrip().startswith("def ")
    cats = sorted({s["cat"] for s in _PRIMITIVES})
    print(f"OK programming_primitives_pack self-test: {len(_PRIMITIVES)} primitives across {cats}, "
          f"{total} oracle fixtures all pass, serves_truth=false")
    return True


def main() -> None:
    ap = argparse.ArgumentParser(description="Common programming/development primitives with oracle fixtures.")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--emit", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return
    if args.emit:
        print(json.dumps(emit(), indent=2))
        return
    self_test()


if __name__ == "__main__":
    main()
