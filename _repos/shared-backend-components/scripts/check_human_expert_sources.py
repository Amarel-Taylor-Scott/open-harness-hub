"""check_human_expert_sources — proof for _repos/shared-backend-components/architecture/human_expert_sources.json (backs registry #74).

The HUMAN tier of the descent: a META, POINTER-ONLY catalog of external human-labor channels. Enforces:
  - every source carries id / name / engagement / skills / speed / cost_tier / ref; engagement in the legend;
  - POINTER-ONLY: short `ref`, no bulk data array, and NO worker-PII fields (this catalogs CHANNELS, not people);
  - coverage (>=10 sources across >=4 engagement types); serves_truth=false.

Deterministic, offline, stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
_DOC = _resource("architecture") / "human_expert_sources.json"
_REQ = ("id", "name", "engagement", "skills", "speed", "cost_tier", "ref")
_PII_KEYS = {"email", "phone", "ssn", "worker", "profile", "resume", "cv", "person"}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    doc = json.loads(_DOC.read_text())
    sources = doc.get("sources", [])
    legend = set(doc.get("engagement_legend", {}))
    fails: list[str] = []
    checks = 0

    def ck(name: str, ok: bool, detail: str = "") -> None:
        nonlocal checks
        checks += 1
        if not ok:
            fails.append(f"{name}{(': ' + detail) if detail else ''}")
        if args.self_test and not ok:
            print(f"  [XX] {name}{(' — ' + detail) if detail else ''}")

    ck("serves_truth is false", doc.get("serves_truth") is False)
    ck(">=10 sources", len(sources) >= 10, str(len(sources)))
    ck("engagement_legend defined", len(legend) >= 4, str(sorted(legend)))

    ids: set[str] = set()
    engagements: set[str] = set()
    for s in sources:
        sid = s.get("id", "?")
        for f in _REQ:
            ck(f"{sid}: has '{f}'", bool(s.get(f)))
        ck(f"{sid}: unique id", sid not in ids, "duplicate")
        ids.add(sid)
        engagements.add(s.get("engagement", ""))
        ck(f"{sid}: engagement in legend", s.get("engagement") in legend, str(s.get("engagement")))
        ck(f"{sid}: ref is a short pointer string", isinstance(s.get("ref"), str) and len(s.get("ref", "")) < 80)
        ck(f"{sid}: no worker-PII keys (channel catalog, not people)", not (_PII_KEYS & {k.lower() for k in s}))
        ck(f"{sid}: stores no bulk data (pointer-only)", not any(isinstance(v, list) and len(v) > 3 for v in s.values()))

    ck(">=4 engagement types", len(engagements) >= 4, str(sorted(engagements)))

    if fails:
        print(f"\nFAIL - check_human_expert_sources: {len(fails)} of {checks} assertions failed")
        for f in fails:
            print(f"  - {f}")
        return 1
    print(f"PASS - check_human_expert_sources: {len(sources)} pointer-only human-labor channels across "
          f"{len(engagements)} engagement types; no worker-PII; {checks} assertions; serves_truth=false.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
