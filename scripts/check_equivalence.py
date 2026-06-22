#!/usr/bin/env python3
"""check_equivalence — canonicalization done honestly (benchmark-relative, never proven).

Proves: agreement is the fraction of matching probe outputs; two runners that agree on the probe set are equivalent
(benchmark-relative), two that disagree are not; equivalence_classes clusters agreeing runners (paddleocr≈tesseract) and
separates a disagreeing one; every verdict is flagged proven=False / benchmark_relative=True. serves_truth=false.

  python3 scripts/check_equivalence.py --self-test
"""
from __future__ import annotations

from src.teleon.synthesis import equivalence as EQ


def _self_test() -> int:
    fails = []
    def ck(n, ok, d=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok: fails.append(n)

    # probe set of 4 documents; three OCR runners' outputs
    paddle = ["acme inc", "total 100", "date 2026", "po 42"]
    tess = ["acme inc", "total 100", "date 2026", "po 42"]          # agrees with paddle on all 4
    weak = ["acme inc", "total 1OO", "date 2026", "po 4Z"]          # disagrees on 2/4

    ck("agreement = fraction of matching probe outputs", EQ.agreement(paddle, tess) == 1.0 and EQ.agreement(paddle, weak) == 0.5)
    eqv = EQ.equivalent(paddle, tess)
    ck("two runners agreeing on the probe set are EQUIVALENT (benchmark-relative)", eqv["equivalent"] is True and eqv["proven"] is False and eqv["benchmark_relative"] is True)
    ck("two runners that disagree are NOT equivalent at threshold", EQ.equivalent(paddle, weak)["equivalent"] is False)
    ck("length mismatch / empty -> 0 agreement (no false equivalence)", EQ.agreement(paddle, ["acme inc"]) == 0.0 and EQ.agreement([], []) == 0.0)

    classes = EQ.equivalence_classes({"paddleocr": paddle, "tesseract": tess, "weak_ocr": weak})
    ck("equivalence_classes clusters agreeing runners + separates the disagreeing one",
       ["paddleocr", "tesseract"] in classes["classes"] and ["weak_ocr"] in classes["classes"])
    ck("the result is flagged NOT proven (undecidable in general) + benchmark-relative", classes["proven"] is False and classes["benchmark_relative"] is True and classes["probe_size"] == 4)
    ck("serves_truth=false", eqv["serves_truth"] is False)

    print("\n" + ("PASS - check_equivalence: benchmark-relative equivalence classes (agreement on a probe set), explicitly "
                  "NOT proven — what makes fallbacks/ladders/learning generalize." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(_self_test())
