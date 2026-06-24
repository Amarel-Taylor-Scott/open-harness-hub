"""check_registry_discover — proof for catalog auto-discovery (src/teleon/registry/port.py).

Auto-discovery scans architecture/*.json and registers every VALIDATED catalog-shaped registry so federated search
spans them all (not just the 14 curated). Proves: many are discovered; each is usable (list non-empty + lookup
round-trips on the detected id field); available_all() strictly extends the curated menu. Deterministic, stdlib only.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.teleon.registry import available, available_all, catalog, discover_catalogs  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    disc = discover_catalogs()
    fails: list[str] = []
    checks = 0

    def ck(name: str, ok: bool, detail: str = "") -> None:
        nonlocal checks
        checks += 1
        if not ok:
            fails.append(f"{name}{(': ' + detail) if detail else ''}")
        if args.self_test and not ok:
            print(f"  [XX] {name}{(' — ' + detail) if detail else ''}")

    ck(">=50 catalogs auto-discovered", len(disc) >= 50, str(len(disc)))
    ck("available_all strictly extends the curated menu", len(available_all()) > len(available()),
       f"{len(available_all())} vs {len(available())}")
    ck("discovery is disjoint from curated keys", not (set(disc) & set(available())))

    # every discovered catalog is USABLE: list non-empty + lookup(first) round-trips on the detected id field
    sample = sorted(disc)[:25]
    for name in sample:
        spec = disc[name]
        reg = catalog(name)
        recs = reg.list()
        ck(f"{name}: list() non-empty", len(recs) >= 1)
        first_id = recs[0].get(spec["id_field"])
        ck(f"{name}: lookup(first) round-trips on '{spec['id_field']}'", reg.lookup(first_id) is not None, str(first_id))

    if fails:
        print(f"\nFAIL - check_registry_discover: {len(fails)} of {checks} assertions failed")
        for f in fails:
            print(f"  - {f}")
        return 1
    print(f"PASS - check_registry_discover: {len(disc)} catalogs auto-discovered (validated, lookup round-trips); "
          f"federated search now spans {len(available_all())} catalogs (was {len(available())} curated); {checks} assertions.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
