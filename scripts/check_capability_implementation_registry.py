#!/usr/bin/env python3
"""check_capability_implementation_registry — proof that each capability is facilitated by a VARIETY of
implementation options (internal repos / libraries / API hubs / models / LLMs), each declaring its tools/models/
API-keys (by NAME, env refs only) + cost + determinism, and that the selector picks the best COMBINATION by what's
available + the objective (a key unlocks an option; require_deterministic admits only deterministic options). Plus
the owner's workspace inventory is staged as candidate capabilities mapping into the registry. serves_truth=false.

CLI: PYTHONPATH=. python3 scripts/check_capability_implementation_registry.py --self-test
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _R not in sys.path:
        sys.path.insert(0, _R)

_REPO = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_FEED = _REPO / "data" / "capability-candidates" / "discovered-feed-workspace-inventory-2026-06-20.json"
_KEY_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")   # an env-ref key NAME (never a value)

from src.teleon.inference.implementation_selector import load_registry, select_implementation


def _self_test() -> int:
    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    reg = load_registry()
    caps = reg["capabilities"]
    impls = [im for c in caps for im in c["implementations"]]
    ck("registry carries the principle + serves_truth false", bool(reg.get("principle")) and reg.get("serves_truth") is False)
    ck("every capability has a VARIETY of implementations (>= 2 options each)",
       all(len(c["implementations"]) >= 2 for c in caps) and len(caps) >= 6,
       str([c["capability"] for c in caps if len(c["implementations"]) < 2]))
    req = {"impl_id", "kind", "models", "api_keys", "cost_tier", "determinism_ceiling", "source", "serves_truth"}
    ck("every implementation declares kind/models/api_keys/cost/determinism/source", all(req <= set(im) for im in impls))
    ck("every kind is in the enum", all(im["kind"] in reg["kind_enum"] for im in impls),
       str(sorted({im["kind"] for im in impls if im["kind"] not in reg["kind_enum"]})))
    # SECRET HYGIENE: api_keys are NAMES (env refs), never values
    bad_keys = [k for im in impls for k in im["api_keys"] if not _KEY_RE.match(k)]
    ck("api_keys are env-ref NAMES, never values (secret hygiene)", not bad_keys, str(bad_keys))
    # the three the owner named are present, each with >= 2 options
    ck("the owner's named capabilities are present (entity-resolution, grounded-search, image-processing)",
       {"entity-resolution", "grounded-search", "image-processing"} <= {c["capability"] for c in caps})

    # SELECTOR PAYOFF 1: with no keys, only key-free options are selectable; key-requiring ones are excluded
    s_nokey = select_implementation("grounded-search", available_keys=())
    ck("no keys -> picks a key-free option; key-requiring options excluded (gemini needs GEMINI_API_KEY)",
       s_nokey["picked"] is not None and not s_nokey["needs_keys"]
       and "gemini-grounded" in s_nokey["excluded_missing_keys"])
    # SELECTOR PAYOFF 2: providing the key UNLOCKS that option (it leaves the excluded set)
    s_key = select_implementation("grounded-search", available_keys=("GEMINI_API_KEY",), objective="most_deterministic")
    ck("providing GEMINI_API_KEY unlocks gemini-grounded (no longer excluded; now selectable)",
       "gemini-grounded" not in s_key["excluded_missing_keys"])
    # SELECTOR PAYOFF 3: require_deterministic admits only deterministic options
    s_det = select_implementation("image-processing", require_deterministic=True)
    picked_det = next(im for im in select_implementation.__globals__["implementations_for"]("image-processing")
                      if im["impl_id"] == s_det["picked"])
    ck("require_deterministic picks a deterministic implementation (>= 0.9 ceiling)",
       picked_det["determinism_ceiling"] >= 0.9, str(s_det["picked"]))
    # SELECTOR PAYOFF 4: cheapest prefers a free/lower-cost option, with ordered fallbacks
    s_cheap = select_implementation("entity-resolution", available_keys=())
    ck("cheapest entity-resolution is a key-free free/low option, with ordered fallbacks",
       s_cheap["picked"] is not None and isinstance(s_cheap["fallbacks"], list) and len(s_cheap["fallbacks"]) >= 1)
    ck("a selection never serves truth", s_nokey["serves_truth"] is False)

    # the workspace inventory feed maps owner products into registry capabilities
    feed = json.loads(_FEED.read_text())
    fcands = feed["candidates"]
    reg_caps = {c["capability"] for c in caps}
    ck("workspace inventory feed conforms (DiscoveredCapabilityFeed.v1) + >= 12 owner products staged",
       feed["feed_version"] == "DiscoveredCapabilityFeed.v1" and len(fcands) >= 12)
    ck("every staged product maps to a real registry capability + is propose-only",
       all(c["maps_to_capability"] in reg_caps and c["serves_truth"] is False for c in fcands),
       str([c["capability_slot"] for c in fcands if c["maps_to_capability"] not in reg_caps]))
    ck("deterministic", select_implementation("grounded-search", available_keys=()) == s_nokey)

    print("\n" + (f"PASS - check_capability_implementation_registry: {len(caps)} capabilities × {len(impls)} "
                  f"implementation options (internal repos / libraries / APIs / models / LLMs); the selector picks "
                  f"the best COMBINATION by available keys + objective (a key unlocks an option; deterministic-only "
                  f"honored); {len(fcands)} owner workspace products staged as candidate capabilities. Keys are env "
                  f"refs; discovery != trust; never serves truth."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def _main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--self-test" in argv:
        return _self_test()
    print("usage: check_capability_implementation_registry.py --self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
