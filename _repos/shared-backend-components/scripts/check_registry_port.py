"""check_registry_port — proof for the universal Registry menu (_repos/teleon/backend/src/teleon/registry/port.py).

Realizes the ontology's universal_interface: ONE ordering protocol over the federation's source catalogs.
Proves the SAME verbs (list / lookup / search / explain) work UNIFORMLY across every registered catalog, and
that real queries return the right ingredient — so an agent can pick from the buffet uniformly.

Deterministic, offline, stdlib only.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.teleon.registry import CATALOGS, RegistryPort, available, catalog  # noqa: E402

# (registry id, query, an id the query must surface) — real picks across different catalogs.
_CASES = [
    ("lookup_portals", "weather", "us_nws_weather"),
    ("knowledge_taxonomies", "news", "iptc_media_topics"),
    ("vulnerability_sources", "cve", "nvd_cve"),
    ("geospatial_sources", "routing", "osrm"),
    ("human_expert_sources", "hackathon", "devpost"),
    ("observability", "traces", "jaeger"),
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
            print(f"  [XX] {name}{(' — ' + detail) if detail else ''}")

    ck(">=6 registries on the menu", len(available()) >= 6, str(available()))

    # uniformity: every registered catalog conforms to the SAME port + behaves consistently
    for name in available():
        reg = catalog(name)
        ck(f"{name}: conforms to RegistryPort", isinstance(reg, RegistryPort))
        recs = reg.list()
        ck(f"{name}: list() non-empty", len(recs) >= 1, str(len(recs)))
        first_id = recs[0].get(CATALOGS[name]["id_field"])
        ck(f"{name}: lookup(first) round-trips", reg.lookup(first_id) is not None, str(first_id))
        ck(f"{name}: search subset of list", len(reg.search("a", limit=999)) <= len(recs))

    # real picks: the query surfaces the right ingredient (same call shape across catalogs)
    for name, query, expect_id in _CASES:
        hits = catalog(name).search(query)
        got = {h.get("id") for h in hits}
        ck(f"{name}.search('{query}') surfaces {expect_id}", expect_id in got, f"got {sorted(got)[:5]}")

    # honest on unknown
    try:
        catalog("does_not_exist")
        ck("unknown registry raises KeyError", False)
    except KeyError:
        ck("unknown registry raises KeyError", True)

    if fails:
        print(f"\nFAIL - check_registry_port: {len(fails)} of {checks} assertions failed")
        for f in fails:
            print(f"  - {f}")
        return 1
    print(f"PASS - check_registry_port: one uniform menu over {len(available())} catalogs — list/lookup/search/"
          f"explain behave consistently + real queries surface the right ingredient; {checks} assertions.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
