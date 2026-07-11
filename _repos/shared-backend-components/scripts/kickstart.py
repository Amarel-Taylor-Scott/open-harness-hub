#!/usr/bin/env python3
"""scripts.kickstart — the REHYDRATION / DOCTOR / KICKSTART injector: never let a stalled tool/task stop too soon.

The automation of the owner's #1 rule (escalate before concluding unavailable). Reads
_repos/shared-backend-components/architecture/search_exhaustion_ladder.json and drives scripts.interrogation_engine to INJECT new direction —
the next untried search rung + fresh questions + query mutations — whenever a tool/loop stalls. A 'no results'
is honest ONLY after the ladder is exhausted for the available keys AND the next key-gated rung is named.
serves_truth=false (injections are candidate next-actions).

  --self-test
  --next --tried a,b,c [--keys ENV1,ENV2]           the next untried rung (or honest exhaustion + the key that unlocks more)
  --kickstart "<goal>" [--object REF] [--tried ...] [--keys ...]   the full injection (rung + questions + mutations)
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
LADDER = _resource("architecture") / "search_exhaustion_ladder.json"

#: signals that mean "do NOT stop — kickstart instead" (the Doctor's stall taxonomy)
STALL_SIGNALS = ("no_results", "low_confidence", "repeated_failures", "premature_termination",
                 "insufficient_data", "low_diversity", "timeout")


def load_ladder() -> list[dict]:
    return sorted(json.loads(LADDER.read_text(encoding="utf-8"))["rungs"], key=lambda r: r["order"])


def _available(rung: dict, have_keys: set[str]) -> bool:
    k = rung.get("needs_key")
    return k is None or k in have_keys or bool(rung.get("key_optional"))


def next_rung(tried: list[str], have_keys: set[str]) -> dict:
    """The next untried rung whose key is available; else honest exhaustion naming the key that would unlock more."""
    tried_s = set(tried)
    skipped: list[dict] = []
    for r in load_ladder():
        if r["id"] in tried_s:
            continue
        if _available(r, have_keys):
            return {"status": "try", "rung": r["id"], "method": r["method"],
                    "needs_key": r.get("needs_key"), "why": r.get("when")}
        skipped.append({"rung": r["id"], "needs_key": r.get("needs_key")})
    return {"status": "exhausted_for_available_keys",
            "next_if_key_added": skipped[0] if skipped else None,
            "skipped_for_missing_key": skipped}


def detect_stall(signal: str) -> dict:
    stalled = signal in STALL_SIGNALS
    return {"stalled": stalled, "signal": signal, "remedy": "kickstart" if stalled else "continue"}


def kickstart(goal: str, object_ref: str | None = None, tried: list[str] | None = None,
              have_keys: set[str] | None = None) -> dict:
    """Inject new direction into a stall: next rung + fresh interrogation questions + query mutations."""
    tried = tried or []
    have_keys = set(have_keys or [])
    nxt = next_rung(tried, have_keys)
    questions: list[str] = []
    try:                                                    # pull injectable questions from the interrogation engine
        from scripts.interrogation_engine import generate, load_taxonomy
        rows, _ = generate([{"ref": object_ref or goal, "type": "tool"}], load_taxonomy(),
                           dims=["kickstart", "contextual_fitness", "alternatives"], context_samples=2, total_cap=12)
        questions = [r["question"] for r in rows]
    except Exception:                                       # interrogation engine optional — never let it block a kickstart
        pass
    mutations = [f"{goal} {m}" for m in ("alternative implementations", "competitors", "forks", "newsletter",
                                         "github topic", "reddit discussion", "awesome list", "foreign-language",
                                         "archived/cached pages", "pypi/npm/docker package")]
    return {"goal": goal, "object_ref": object_ref, "next_rung": nxt, "injected_questions": questions[:8],
            "query_mutations": mutations,
            "rule": "DO NOT STOP until next_rung.status=='exhausted_for_available_keys' AND its named key is unavailable",
            "serves_truth": False}


def self_test() -> int:
    lad = load_ladder()
    assert lad and lad[0]["order"] == 1, "ladder must load sorted by order"
    # nothing tried, no keys -> first keyless rung
    n0 = next_rung([], set())
    assert n0["status"] == "try" and n0["needs_key"] is None, f"first rung should be keyless: {n0}"
    # a key-gated rung is skipped without its key, surfaced WITH it
    keyed = next((r for r in lad if r.get("needs_key") and not r.get("key_optional")), None)
    assert keyed, "expected at least one key-gated rung"
    tried_all_keyless = [r["id"] for r in lad if _available(r, set())]
    ex = next_rung(tried_all_keyless, set())
    assert ex["status"] == "exhausted_for_available_keys" and ex["next_if_key_added"], "must name the next key-gated rung"
    got = next_rung(tried_all_keyless, {keyed["needs_key"]})
    assert got["status"] == "try" and got["rung"] == keyed["id"], "adding the key must unlock its rung"
    # stall detection
    assert detect_stall("no_results")["stalled"] and detect_stall("no_results")["remedy"] == "kickstart"
    assert not detect_stall("done")["stalled"]
    # kickstart injects a rung + questions + mutations, and refuses to authorize stopping early
    inj = kickstart("find AI newsletters", object_ref="newsletters")
    assert inj["next_rung"]["status"] in ("try", "exhausted_for_available_keys")
    assert inj["query_mutations"] and "DO NOT STOP" in inj["rule"]
    assert inj["serves_truth"] is False
    print(f"kickstart self-test: OK ({len(lad)} ladder rungs; next-rung honors keys + exhaustion; stall→kickstart "
          f"injects rung + {len(inj['injected_questions'])} questions + {len(inj['query_mutations'])} mutations)")
    return 0


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        return self_test()

    def opt(name, default=None):
        return argv[argv.index(name) + 1] if name in argv and argv.index(name) + 1 < len(argv) else default

    tried = (opt("--tried") or "").split(",") if opt("--tried") else []
    keys = set((opt("--keys") or "").split(",")) if opt("--keys") else {k for k in os.environ if k.endswith(("_KEY", "_TOKEN"))}
    if "--next" in argv:
        print(json.dumps(next_rung(tried, keys), indent=2))
        return 0
    if "--kickstart" in argv:
        print(json.dumps(kickstart(opt("--kickstart") or "discover sources", opt("--object"), tried, keys), indent=2))
        return 0
    print("usage: kickstart.py --self-test | --next --tried a,b [--keys ENV] | --kickstart '<goal>' [--object REF --tried ... --keys ...]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
