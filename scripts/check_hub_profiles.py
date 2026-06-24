"""check_hub_profiles — anti-drift proof for architecture/hub_profiles.json.

hub_profiles.json is the SYSTEM-FACING map: every Open*Hub as a DIRECTORY the compiler/runtime pulls from,
declaring the TYPES of rules / context / modules pullable from it. Its load-bearing invariant is that the map
CANNOT DRIFT from the brand/release policy: every profiled hub id is a real hub, and every real hub is profiled.

This check enforces that invariant bidirectionally against the single sources of truth:
  - the 9 live hubs + the active candidates come from architecture/candidate_open_hubs.json (existing_hubs + candidates);
  - the 5 Baltor method hubs come from the method spine (products.js private bench / CLAUDE.md) — named here as a
    constant because candidate_open_hubs.json scopes itself to the candidate layer and does not list them.

Forward:  every profile's hub id is valid for its declared layer (open->existing, candidate->active candidate, method->method spine).
Reverse:  every existing hub, every active candidate, and every method hub HAS a profile (so the map can't fall behind).
Structural: each profile declares domain/layer/kind/pulls{rule_types,context_types,module_types}/substrate/example_pull; serves_truth=false.

Deterministic, offline, stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_PROFILES = _REPO / "architecture" / "hub_profiles.json"
_POLICY = _REPO / "architecture" / "candidate_open_hubs.json"

# The five Baltor method-spine hubs. Source of truth = products.js private bench (method stages) + CLAUDE.md
# portfolio note; candidate_open_hubs.json deliberately scopes to the candidate layer and omits them, so they
# are named here. If the method spine changes, this list and products.js change together (single edit point).
_METHOD_HUBS = (
    "OpenReconciliationHub",
    "OpenHardeningHub",
    "OpenEnrichmentHub",
    "OpenOptimizationHub",
    "OpenVerificationHub",
)
# A candidate is "active" (and so must be profiled) unless it carries a resolved disposition (merged/folded).
_ACTIVE_CANDIDATE_STATUS = "candidate"
_PULL_KINDS = ("rule_types", "context_types", "module_types")
# the status a profile carries for each layer (a live open registry says "live"; bench layers name themselves).
_STATUS_FOR_LAYER = {"open": "live", "candidate": "candidate", "method": "method"}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true", help="print every assertion; exit nonzero on any failure")
    args = ap.parse_args()

    prof_doc = json.loads(_PROFILES.read_text())
    pol_doc = json.loads(_POLICY.read_text())

    profiles = prof_doc.get("profiles", {})
    existing = list(pol_doc.get("existing_hubs", []))
    active_candidates = [c["hub_id"] for c in pol_doc.get("candidates", [])
                         if c.get("status") == _ACTIVE_CANDIDATE_STATUS]

    valid_for_layer = {
        "open": set(existing),
        "candidate": set(active_candidates),
        "method": set(_METHOD_HUBS),
    }

    fails: list[str] = []
    checks = 0

    def ck(name: str, ok: bool, detail: str = "") -> None:
        nonlocal checks
        checks += 1
        if not ok:
            fails.append(f"{name}{(': ' + detail) if detail else ''}")
        if args.self_test:
            print(f"  [{'ok' if ok else 'XX'}] {name}{(' — ' + detail) if detail and not ok else ''}")

    # top-level invariant: the map registers pointers/shapes, never truth.
    ck("serves_truth is false", prof_doc.get("serves_truth") is False, str(prof_doc.get("serves_truth")))

    # ---- forward: every profile is a real hub, valid for its declared layer + structurally complete ----
    for hid, p in sorted(profiles.items()):
        layer = p.get("layer")
        ck(f"{hid}: layer in {{open,candidate,method}}", layer in valid_for_layer, str(layer))
        if layer in valid_for_layer:
            ck(f"{hid}: id valid for layer '{layer}'", hid in valid_for_layer[layer],
               f"not in {sorted(valid_for_layer[layer])[:3]}...")
        ck(f"{hid}: status matches layer", p.get("status") == _STATUS_FOR_LAYER.get(layer),
           f"status={p.get('status')} layer={layer}")
        for field in ("domain", "kind", "substrate", "example_pull"):
            ck(f"{hid}: has '{field}'", bool(p.get(field)))
        pulls = p.get("pulls", {})
        for kind in _PULL_KINDS:
            ck(f"{hid}: pulls.{kind} is a list", isinstance(pulls.get(kind), list))
        ck(f"{hid}: declares at least one pullable type",
           any(pulls.get(k) for k in _PULL_KINDS))
        # model-authored display copy (rendered by build_hub_sites): value-prop + concrete use-cases.
        ck(f"{hid}: has a model-authored one_liner", bool(p.get("one_liner")))
        ck(f"{hid}: has >=2 use_cases",
           isinstance(p.get("use_cases"), list) and len(p.get("use_cases", [])) >= 2)

    # ---- reverse: every real hub HAS a profile (the map can't fall behind the policy) ----
    profiled = set(profiles)
    for hid in existing:
        ck(f"live hub '{hid}' is profiled (layer open)",
           hid in profiled and profiles.get(hid, {}).get("layer") == "open")
    for hid in active_candidates:
        ck(f"active candidate '{hid}' is profiled (layer candidate)",
           hid in profiled and profiles.get(hid, {}).get("layer") == "candidate")
    for hid in _METHOD_HUBS:
        ck(f"method hub '{hid}' is profiled (layer method)",
           hid in profiled and profiles.get(hid, {}).get("layer") == "method")

    # coverage summary (computed, never hand-typed)
    n_open = sum(1 for p in profiles.values() if p.get("layer") == "open")
    n_cand = sum(1 for p in profiles.values() if p.get("layer") == "candidate")
    n_meth = sum(1 for p in profiles.values() if p.get("layer") == "method")

    if fails:
        print(f"\nFAIL - check_hub_profiles: {len(fails)} of {checks} assertions failed")
        for f in fails:
            print(f"  - {f}")
        return 1
    print(f"PASS - check_hub_profiles: {len(profiles)} profiles cover every hub with no drift "
          f"({n_open} live + {n_cand} candidate + {n_meth} method); "
          f"{checks} assertions; serves_truth=false (pointers/shapes, never truth).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
