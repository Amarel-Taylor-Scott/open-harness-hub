#!/usr/bin/env python3
"""experiments/dogfood/scrape_topics_for_primitives — DOGFOOD demo: string our own primitives together to
scrape new topics into new candidate primitives.

This is not a new pipeline — it is the ONE-COMMAND, standalone-runnable front door to the pipeline that already
exists and passes its self-test (scripts/discovery_pipeline: scrape GitHub -> license-govern -> classify to a
plane -> ideate into tool/plugin/capability/ml_model candidates -> security-quarantine gate -> candidate feed).
The only thing that was "not wired" was running it OUTSIDE the proof harness: the cross-repo `src.*` roots
(teleon, openhubforai, ...) weren't on sys.path. This runner installs them first (via _repo_paths.install),
then runs the chain — so you can dogfood primitive ideation from a topic in one command.

  python3 experiments/dogfood/scrape_topics_for_primitives.py "ocr" "reranker" "pdf table extraction"

Every row stays candidate=true, serves_truth=false (discovery != trust). GitHub runs on the keyless cheap tier
(no key needed); governed social sources are honest-unavailable without a held BYO key.
"""
import sys
from pathlib import Path

# --- the bootstrap that was missing for standalone runs: put the cross-repo backends on sys.path ---
_here = Path(__file__).resolve()
_root = next((p for p in _here.parents if (p / "scripts" / "_repo_paths.py").exists()), _here.parents[2])
sys.path.insert(0, str(_root))
from scripts._repo_paths import install as _install     # noqa: E402
_install()                                              # adds _repos/*/backend so `import src.teleon` etc. resolve

from scripts import discovery_pipeline as dp             # noqa: E402  (now importable)


def main(argv: list[str]) -> int:
    topics = argv or ["ocr", "reranker", "pdf table extraction"]
    print(f"== dogfood: scraping {len(topics)} topic(s) into candidate primitives ==")
    for t in topics:
        print(f" • {t}")
    print("-- running the chain: scrape -> govern -> classify -> ideate -> quarantine-gate -> candidate feed --")
    cands = dp.run(topics)

    # summary — grouped by the idea kind each candidate primitive was ideated into
    from collections import Counter
    kinds = Counter(k for c in cands for k in c.get("idea_kinds", []))
    quarantined = sum(1 for c in cands if c.get("quarantined"))
    all_candidate = all(c.get("serves_truth") is False for c in cands)
    print("\n== result ==")
    print(f"  candidate primitive-ideas: {len(cands)}   (quarantined by the ingest gate: {quarantined})")
    print(f"  ideated kinds: {dict(kinds) or '(none — sources returned no hits this run)'}")
    print(f"  every row serves_truth=false: {all_candidate}")
    print(f"  feed: {dp.FEED}")
    if cands:
        print("  sample:")
        for c in cands[:5]:
            print(f"    - {c.get('id')}  plane={c.get('plane')}  kinds={c.get('idea_kinds')}  — {c.get('idea_rationale','')[:80]}")
    print("\n  next hop (already in the repo): these candidate ideas feed scripts/global_primitive_foundry_loop.py")
    print("  + scripts/capability_seeder.py -> primitive rows in the registry (still candidate; promotion is a separate gate).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
