"""check_plane_selection — proof for the generic policy-driven plane selector (src/teleon/registry/plane.py).

The flexible alternative to hardcoded best_X() wrappers: a plane of candidate adapters (forks) selected by POLICY,
descending to the first available. Proves policies pick DIFFERENTLY (no baked-in default), the fallback chain
descends past unavailable candidates, require_keyless filters, and adding a candidate / policy doesn't touch select().
Deterministic, offline, stdlib only.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.teleon.registry.plane import Candidate, POLICIES, ranked, register_policy, select  # noqa: E402


def _plane() -> list[Candidate]:
    # a differentiated plane so policies MUST diverge: cheap-weak-local, free-good-local, paid-best-cloud, top-but-DOWN.
    return [
        Candidate("local_lex", lambda: "LEX", locality="local", keyless=True, cost=0.0, quality=1),
        Candidate("local_sem", lambda: "SEM", locality="local", keyless=True, cost=0.0, quality=3),
        Candidate("cloud_best", lambda: "CLOUD", locality="cloud", keyless=False, cost=1.0, quality=5),
        Candidate("down_top", lambda: "DOWN", locality="local", keyless=True, cost=0.0, quality=9, probe=lambda: False),
    ]


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

    p = _plane()
    ck(">=5 policies registered", len(POLICIES) >= 5, str(list(POLICIES)))

    # policies DIVERGE — no baked-in default
    ck("local_first picks a LOCAL fork (descending past the down one) -> SEM", select(p, "local_first") == "SEM",
       str(select(p, "local_first")))
    ck("best_quality picks the highest-quality AVAILABLE -> CLOUD", select(p, "best_quality") == "CLOUD",
       str(select(p, "best_quality")))
    ck("local_first != best_quality (policies actually differ)", select(p, "local_first") != select(p, "best_quality"))

    # fallback chain: the top-ranked is unavailable (down_top) -> descends to the next
    ck("fallback descends past an unavailable candidate", "DOWN" not in str(select(p, "best_quality")))

    # require_keyless filters the cloud (keyed) fork out entirely
    ck("require_keyless excludes the keyed cloud fork", select(p, "best_quality", require_keyless=True) != "CLOUD")
    ck("require_keyless ranking has no keyed candidates", all(c.keyless for c in ranked(p, "best_quality", require_keyless=True)))

    # extensibility: a new policy is just a registered key; select() is untouched
    register_policy("prefer_lex", lambda c: (0 if c.name == "local_lex" else 1,))
    ck("a registered policy works without changing select()", select(p, "prefer_lex") == "LEX")

    # the real embedding plane still returns a working embedder (gate-safe)
    from src.teleon.retrieval.embedding_port import best_embedder, select_embedder_by_policy  # noqa: PLC0415
    ck("embedding plane: best_embedder works", hasattr(best_embedder(), "embed"))
    ck("embedding plane: policy selection works", hasattr(select_embedder_by_policy("best_quality"), "embed"))

    if fails:
        print(f"\nFAIL - check_plane_selection: {len(fails)} of {checks} assertions failed")
        for f in fails:
            print(f"  - {f}")
        return 1
    print(f"PASS - check_plane_selection: policy-driven plane selection — forks ranked + selected by policy "
          f"(local_first->SEM, best_quality->CLOUD), fallback chain, require_keyless filter, extensible; {checks} assertions.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
