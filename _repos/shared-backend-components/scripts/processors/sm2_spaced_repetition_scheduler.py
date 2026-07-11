#!/usr/bin/env python3
"""Backs `processor/sm2-spaced-repetition-scheduler` (process_kind ``eval.rubric_deterministic``).

The SuperMemo SM-2 algorithm, exactly: take a quality-of-recall score (0–5)
and the card's current state (easiness factor, interval days, repetitions)
and emit the next review date and updated state. Wrong answers (quality < 3)
reset repetitions and re-show the card today; the easiness factor follows
the canonical update ``EF' = EF + (0.1 − (5−q)·(0.02·(5−q)+0.08))`` floored
at 1.3. Dates are day-offsets from the injected ``last_review_date`` — no
wall clock.

Contract: deterministic; side_effects=none; on_error=raise.
Inputs card_id, quality_score, easiness_factor, interval_days, repetitions,
last_review_date → next_review_date, new_interval_days, new_easiness_factor,
new_repetitions, reset_to_today.

CLI / self-test: python3 _repos/shared-backend-components/scripts/processors/sm2_spaced_repetition_scheduler.py
"""
from __future__ import annotations

import datetime
import json
from typing import Any

# ── Constants (No-Magic-Values; the canonical SM-2 parameters) ────────────────

QUALITY_MIN, QUALITY_MAX = 0, 5
#: quality >= 3 counts as a successful recall (SM-2's pass threshold).
PASS_QUALITY = 3
#: First two successful intervals are fixed by the algorithm.
FIRST_INTERVAL_DAYS = 1
SECOND_INTERVAL_DAYS = 6
#: EF floor — SM-2 never lets a card become harder than 1.3.
MIN_EASINESS_FACTOR = 1.3
DEFAULT_EASINESS_FACTOR = 2.5
EF_DECIMALS = 4


def run(*, card_id: str, quality_score: int, easiness_factor: float = DEFAULT_EASINESS_FACTOR,
        interval_days: int = 0, repetitions: int = 0,
        last_review_date: str = "1970-01-01") -> dict[str, Any]:
    """One SM-2 update step for one card."""
    if not isinstance(card_id, str) or not card_id:
        raise ValueError("card_id must be a non-empty str")
    if not isinstance(quality_score, int) or not QUALITY_MIN <= quality_score <= QUALITY_MAX:
        raise ValueError(f"quality_score must be an int {QUALITY_MIN}..{QUALITY_MAX}, got {quality_score!r}")
    if not isinstance(repetitions, int) or repetitions < 0:
        raise ValueError(f"repetitions must be >= 0, got {repetitions!r}")
    if float(easiness_factor) < MIN_EASINESS_FACTOR:
        raise ValueError(f"easiness_factor below the SM-2 floor {MIN_EASINESS_FACTOR}")
    try:
        last = datetime.date.fromisoformat(last_review_date)
    except ValueError as exc:
        raise ValueError(f"last_review_date must be ISO YYYY-MM-DD: {exc}") from exc

    q = quality_score
    # EF updates on EVERY graded recall (also on failures), per the algorithm.
    ef = float(easiness_factor) + (0.1 - (5 - q) * (0.02 * (5 - q) + 0.08))
    ef = round(max(MIN_EASINESS_FACTOR, ef), EF_DECIMALS)

    if q < PASS_QUALITY:
        reps = 0
        interval = 0          # re-show today
        reset = True
    else:
        reps = repetitions + 1
        if reps == 1:
            interval = FIRST_INTERVAL_DAYS
        elif reps == 2:
            interval = SECOND_INTERVAL_DAYS
        else:
            interval = round(int(interval_days) * ef)
        reset = False
    next_date = last + datetime.timedelta(days=interval)
    return {"next_review_date": next_date.isoformat(),
            "new_interval_days": interval,
            "new_easiness_factor": ef,
            "new_repetitions": reps,
            "reset_to_today": reset,
            "card_id": card_id}


def _selftest() -> None:
    # The canonical progression: q=5 from a fresh card → 1 day, 6 days, then EF-scaled.
    s1 = run(card_id="c", quality_score=5, last_review_date="2026-06-12")
    assert s1["new_interval_days"] == FIRST_INTERVAL_DAYS and s1["next_review_date"] == "2026-06-13"
    assert s1["new_easiness_factor"] == 2.6  # 2.5 + 0.1
    s2 = run(card_id="c", quality_score=5, easiness_factor=s1["new_easiness_factor"],
             interval_days=s1["new_interval_days"], repetitions=s1["new_repetitions"],
             last_review_date="2026-06-13")
    assert s2["new_interval_days"] == SECOND_INTERVAL_DAYS
    s3 = run(card_id="c", quality_score=4, easiness_factor=s2["new_easiness_factor"],
             interval_days=s2["new_interval_days"], repetitions=s2["new_repetitions"],
             last_review_date="2026-06-19")
    assert s3["new_interval_days"] == round(6 * s2["new_easiness_factor"])  # EF-scaled
    assert s3["new_repetitions"] == 3
    # q=4 leaves EF unchanged (the formula's fixed point at q=4).
    assert s3["new_easiness_factor"] == s2["new_easiness_factor"]
    # A failure resets repetitions and re-shows TODAY, but EF still degrades.
    fail = run(card_id="c", quality_score=1, easiness_factor=2.6, interval_days=15,
               repetitions=3, last_review_date="2026-07-04")
    assert fail["reset_to_today"] is True and fail["new_repetitions"] == 0
    assert fail["next_review_date"] == "2026-07-04" and fail["new_easiness_factor"] < 2.6
    # EF floor holds under repeated failures.
    worst = run(card_id="c", quality_score=0, easiness_factor=1.3, interval_days=1,
                repetitions=0, last_review_date="2026-06-12")
    assert worst["new_easiness_factor"] == MIN_EASINESS_FACTOR
    # Deterministic; on_error=raise.
    assert json.dumps(run(card_id="c", quality_score=5, last_review_date="2026-06-12"), sort_keys=True) == \
           json.dumps(run(card_id="c", quality_score=5, last_review_date="2026-06-12"), sort_keys=True)
    for bad in (lambda: run(card_id="c", quality_score=6),
                lambda: run(card_id="c", quality_score=3, last_review_date="June 12"),
                lambda: run(card_id="", quality_score=3),
                lambda: run(card_id="c", quality_score=3, easiness_factor=1.0)):
        raised = False
        try:
            bad()
        except ValueError:
            raised = True
        assert raised
    print("PASS — sm2_spaced_repetition_scheduler: canonical SM-2 (1d/6d/EF-scaled, "
          "q<3 resets to today, EF floor 1.3, EF fixed-point at q=4), injected dates "
          "only, deterministic verified")


if __name__ == "__main__":
    _selftest()
