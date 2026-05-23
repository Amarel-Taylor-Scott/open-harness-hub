"""Approximate token count — character / 4 heuristic.

Cheaper than tiktoken; accurate to ~±10% for English. For exact
counts use the actual tokenizer of your target model.
"""
from __future__ import annotations

from typing import Any


def run(inputs: dict[str, Any]) -> dict[str, Any]:
    text = inputs.get("text", "")
    if not isinstance(text, str):
        raise TypeError(f"text must be str, got {type(text).__name__}")
    char_count = len(text)
    # Heuristic: GPT-family English ≈ 4 chars / token; CJK ≈ 1 char / token.
    cjk = sum(1 for c in text if "一" <= c <= "鿿" or "぀" <= c <= "ヿ" or "가" <= c <= "힯")
    non_cjk = char_count - cjk
    approx = cjk + non_cjk // 4
    return {
        "char_count": char_count,
        "cjk_char_count": cjk,
        "approx_tokens": approx,
        "method": "char-div-4 + 1-per-cjk-char",
    }
