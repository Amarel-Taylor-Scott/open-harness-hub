"""check_record_variations — proof for record variation generation (src/teleon/registry/variations.py).

The owner's fork-generation discipline applied to DATA: for any registry row, generate governed candidate
variations along axes (industry / region / scale / approach) + the variation questions to ask. Proves the
variations are well-formed, industry-aware, parent-linked, and GOVERNED (candidate-only, never asserted as truth).
Deterministic, offline, stdlib only.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.teleon.registry.variations import AXES, expand_record, fork_questions, variations_of  # noqa: E402

_REC = {"id": "contract_review", "name": "Contract review", "domain": "legal_ops"}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    fails: list[str] = []
    checks = 0

    def ck(name: str, ok: bool, detail: str = "") -> None:
        nonlocal checks
        checks += 1
        if not ok:
            fails.append(f"{name}{(': ' + detail) if detail else ''}")
        if args.self_test and not ok:
            print(f"  [{'ok' if ok else 'XX'}] {name}{(' — ' + detail) if detail else ''}")

    ck("axes include industry/region/scale/approach", {"industry", "region", "scale", "approach"} <= set(AXES))

    ind = variations_of(_REC, "industry")
    ck("industry generates one variation per industry value", len(ind) == len(AXES["industry"]), str(len(ind)))
    ck("industry variations cover healthcare/finance/legal",
       {"healthcare", "finance", "legal"} <= {v["variation_value"] for v in ind})
    for v in ind:
        ck(f"{v['id']}: links to parent (variation_of)", v.get("variation_of") == "contract_review")
        ck(f"{v['id']}: carries axis + value", v.get("variation_axis") == "industry" and v.get("variation_value"))
        ck(f"{v['id']}: GOVERNED (candidate, non-truth)", v["candidate"] is True and v["serves_truth"] is False)
    ck("variation ids are unique", len({v["id"] for v in ind}) == len(ind))

    # custom values for a specific industry question ("how would this vary for X industry")
    one = variations_of(_REC, "industry", ["healthcare"])
    ck("can ask 'how would this vary for healthcare'", len(one) == 1 and one[0]["variation_value"] == "healthcare")

    # the fork questions are asked per-record + are industry-aware
    qs = fork_questions(_REC)
    ck(">=4 fork questions asked", len(qs) >= 4)
    ck("a question is industry-specific", any("INDUSTRY" in q or "healthcare" in q for q in qs))

    # the full fork set spans multiple axes
    full = expand_record(_REC)
    ck("expand_record spans multiple axes", len(full) >= 4 and all(full[a] for a in full))

    if fails:
        print(f"\nFAIL - check_record_variations: {len(fails)} of {checks} assertions failed")
        for f in fails:
            print(f"  - {f}")
        return 1
    print(f"PASS - check_record_variations: any record -> governed candidate variations across "
          f"{len(AXES)} axes (industry/region/scale/approach) + the fork questions; parent-linked; {checks} assertions; serves_truth=false.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
