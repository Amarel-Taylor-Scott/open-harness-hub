"""check_registry_enrich — proof for the registry enrichment worker (src/teleon/registry/enrich.py, registry #84).

The Baltor-Enhance worker: generates embedding/description/long_description/use_cases/labels/keywords for
registry records. Verifies the generated metadata is right + DETERMINISTIC (same record -> same embedding) and
that it works uniformly across catalogs (via the RegistryPort). Deterministic, offline, stdlib only.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.teleon.registry import catalog  # noqa: E402
from src.teleon.registry.enrich import embedding, enrich_catalog, enrich_record  # noqa: E402

_EMBED_DIM = 64


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

    rec = catalog("lookup_portals").lookup("us_nws_weather")
    e = enrich_record(rec)["_enrichment"]

    ck("embedding has the right dim", len(e["embedding"]) == _EMBED_DIM, str(len(e["embedding"])))
    ck("embedding is L2-normalized", abs(sum(x * x for x in e["embedding"]) - 1.0) < 1e-3)
    ck("embedding is deterministic", embedding(rec) == embedding(rec))
    ck("description names the record", "Weather" in e["description"], e["description"])
    ck("keywords include 'weather'", "weather" in e["keywords"], str(e["keywords"]))
    ck("labels include domain:weather", "domain:weather" in e["labels"], str(e["labels"]))
    ck("use_cases non-empty", len(e["use_cases"]) >= 1)
    ck("long_description carries detail", "ref=" in e["long_description"], e["long_description"][:80])

    # uniform across a different catalog: every record gets a full enrichment block
    enriched = enrich_catalog("observability")
    ck("enrich_catalog enriches every record", all("_enrichment" in r for r in enriched), str(len(enriched)))
    ck("each enriched record has all fields", all(
        {"embedding", "description", "long_description", "keywords", "labels", "use_cases"} <= set(r["_enrichment"])
        for r in enriched))

    if fails:
        print(f"\nFAIL - check_registry_enrich: {len(fails)} of {checks} assertions failed")
        for f in fails:
            print(f"  - {f}")
        return 1
    print(f"PASS - check_registry_enrich: enrichment worker generates deterministic embedding + description + "
          f"long_description + use_cases + labels + keywords, uniformly across catalogs; {checks} assertions.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
