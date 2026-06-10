"""Jaro-Winkler similarity (0.0 to 1.0).

Standard implementation. Used heavily by sanctions screening (matching
entity names against OFAC SDN / UN / EU lists) and de-duplication.
"""
from __future__ import annotations

from typing import Any


def jaro(s1: str, s2: str) -> float:
    if not s1 and not s2:
        return 1.0
    if not s1 or not s2:
        return 0.0
    s1_len, s2_len = len(s1), len(s2)
    match_dist = max(s1_len, s2_len) // 2 - 1
    s1_matches = [False] * s1_len
    s2_matches = [False] * s2_len
    matches = 0
    for i, c1 in enumerate(s1):
        start = max(0, i - match_dist)
        end = min(i + match_dist + 1, s2_len)
        for j in range(start, end):
            if s2_matches[j]:
                continue
            if c1 != s2[j]:
                continue
            s1_matches[i] = True
            s2_matches[j] = True
            matches += 1
            break
    if matches == 0:
        return 0.0
    transpositions = 0
    k = 0
    for i in range(s1_len):
        if not s1_matches[i]:
            continue
        while not s2_matches[k]:
            k += 1
        if s1[i] != s2[k]:
            transpositions += 1
        k += 1
    return (
        matches / s1_len
        + matches / s2_len
        + (matches - transpositions / 2) / matches
    ) / 3.0


def jaro_winkler(s1: str, s2: str, p: float = 0.1, prefix_max: int = 4) -> float:
    j = jaro(s1, s2)
    if j == 0:
        return 0.0
    prefix = 0
    for c1, c2 in zip(s1[:prefix_max], s2[:prefix_max]):
        if c1 == c2:
            prefix += 1
        else:
            break
    return j + prefix * p * (1 - j)


def run(inputs: dict[str, Any]) -> dict[str, Any]:
    a = inputs.get("a", "")
    b = inputs.get("b", "")
    if not isinstance(a, str) or not isinstance(b, str):
        raise TypeError("a and b must be strings")
    case_insensitive = bool(inputs.get("case_insensitive", True))
    a_cmp = a.lower() if case_insensitive else a
    b_cmp = b.lower() if case_insensitive else b
    score = jaro_winkler(a_cmp, b_cmp)
    return {
        "a": a,
        "b": b,
        "case_insensitive": case_insensitive,
        "score": round(score, 6),
    }
