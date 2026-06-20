"""src.teleon.evolution.token_reduction — token-reduce a SKILL/prompt, losslessly. The descent at the PROMPT layer.

The owner's point: you don't need a whole capability — even a single SKILL's prompt can be compressed to fewer
INPUT tokens with the same behavior (lower context = cheaper, and a weaker/cheaper model can then handle it).
compress_skill applies DETERMINISTIC, lossless reductions (collapse whitespace, drop duplicated instructions,
prune lines marked optional) and MEASURES the input-token reduction. Lossless-distillation law: the raw skill is
preserved and answer-critical content (the ``must_keep`` markers) must survive — a real reducer (a learned one like
TokenTamer/LLMLingua is a candidate behind a port). Pure + deterministic; Teleon-layer — never imports src.baltor;
never serves truth.
"""
from __future__ import annotations

_OPTIONAL_MARK = "[optional]"


def estimate_tokens(text: str) -> int:
    """A standard ~4-chars-per-token estimate for INPUT-token accounting (no tokenizer dependency)."""
    return max(1, len(text or "") // 4)


def compress_skill(skill_slot: str, skill_text: str, *, must_keep: tuple = ()) -> dict:
    """Deterministically token-reduce a skill's prompt: collapse internal/edge whitespace, drop duplicate
    instruction lines (keep first), and prune lines marked ``[optional]`` (unless they contain a must_keep
    phrase). Returns the compressed skill + the measured input-token reduction. Lossless: the raw skill is
    preserved and every ``must_keep`` phrase must survive; otherwise lossless is False (escalate, don't ship)."""
    raw = skill_text or ""
    seen, out, prev_blank = set(), [], False
    for line in raw.splitlines():
        s = " ".join(line.split())  # collapse internal + edge whitespace
        if not s:
            if not prev_blank:
                out.append("")
            prev_blank = True
            continue
        prev_blank = False
        low = s.lower()
        if _OPTIONAL_MARK in low and not any(k.lower() in low for k in must_keep):
            continue  # prune optional boilerplate (unless it carries answer-critical content)
        if s in seen:
            continue  # drop a duplicated instruction
        seen.add(s)
        out.append(s)
    compressed = "\n".join(out).strip()

    before, after = estimate_tokens(raw), estimate_tokens(compressed)
    survived = all(m in compressed for m in must_keep)  # answer-critical content preserved?
    return {
        "skill_slot": skill_slot, "strategy": "prompt_compression",
        "tokens_in_before": before, "tokens_in_after": after, "tokens_saved": before - after,
        "reduction_pct": round(100.0 * (before - after) / before, 2) if before else 0.0,
        "compressed": compressed, "raw": raw, "raw_preserved": True,
        "must_keep_survived": survived, "lossless": survived, "serves_truth": False,
    }
