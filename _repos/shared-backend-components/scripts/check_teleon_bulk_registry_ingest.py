#!/usr/bin/env python3
"""check_teleon_bulk_registry_ingest — proof for the bulk registry ingester (the hundreds-of-thousands path).

Maps machine-readable registry DUMPS into governed candidate rows WITHOUT an LLM:
  * each registry FORMAT (generic_catalog / mcp_registry / airbyte_registry / npm_pypi_search / openapi_directory)
    maps deterministically to CapabilityCandidate rows that PASS the real seeder normalize + gap/lift screen.
  * a deterministic keyword classifier infers category (weather->geo-weather, stripe->financial-data, postgres->
    database, fhir->healthcare) and a kind->determinism table sets the prior (library 1.0, agent 0.3) — Stage-1
    of screen-before-confirm; every row is flagged BULK-INGESTED for a later confirm.
  * it SCALES: a 1,000-entry dump maps to ~1,000 candidates in one free deterministic pass (no LLM, no agents).
  * ingest_to_feed writes a discovered-feed JSON the existing runner ingests + dedups.
  * unknown format fails loud; deterministic; everything stays a candidate, nothing serves truth.

CLI: python3 _repos/shared-backend-components/scripts/check_teleon_bulk_registry_ingest.py --self-test
"""
from __future__ import annotations

import os
import sys
import tempfile

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _R not in sys.path:
        sys.path.insert(0, _R)

from scripts.capability_seeder import normalize_candidate, screen
from src.teleon.ingest import REGISTRY_FORMATS, ingest_dump, ingest_to_feed, map_entry


def _self_test() -> int:
    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    # generic_catalog dump across domains -> rows that pass the REAL seeder normalize + screen.
    generic = [
        {"name": "OpenWeather Forecast", "description": "current weather and forecast by city", "url": "https://ex/ow", "kind": "api", "license": "MIT"},
        {"name": "Stripe Charge Create", "description": "create a payment charge", "url": "https://ex/stripe", "kind": "api", "license": "MIT"},
        {"name": "Postgres Query", "description": "run SQL against a postgres database", "url": "https://ex/pg", "kind": "tool", "license": "Apache-2.0"},
        {"name": "FHIR Patient Read", "description": "read a clinical patient resource via FHIR", "url": "https://ex/fhir", "kind": "api", "license": "unknown"},
        {"name": "dateparser", "description": "parse human dates deterministically", "url": "https://ex/dp", "kind": "library", "license": "BSD-3-Clause"},
        {"name": "Autonomous Research Agent", "description": "multi-step web research", "url": "https://ex/ra", "kind": "agent", "license": "Apache-2.0"},
    ]
    rows = ingest_dump(generic, registry_format="generic_catalog")
    ck("bulk-mapped rows all pass the real seeder normalize + gap/lift screen",
       len(rows) == 6 and all(screen(normalize_candidate(r))["accepted"] for r in rows))
    by_slot = {r["capability_slot"]: r for r in rows}
    ck("category is inferred deterministically (weather->geo-weather, stripe->financial-data, postgres->database, fhir->healthcare)",
       by_slot["openweather-forecast"]["category"] == "geo-weather"
       and by_slot["stripe-charge-create"]["category"] == "financial-data"
       and by_slot["postgres-query"]["category"] == "database"
       and by_slot["fhir-patient-read"]["category"] == "healthcare",
       str({k: v["category"] for k, v in by_slot.items()}))
    ck("determinism prior follows the kind (library 1.0, agent 0.3)",
       by_slot["dateparser"]["determinism_ceiling"] == 1.0 and by_slot["autonomous-research-agent"]["determinism_ceiling"] == 0.3)
    ck("every bulk row is a candidate flagged for Stage-2 confirm (never truth)",
       all("BULK-INGESTED" in r["verify_note"] for r in rows) and all(normalize_candidate(r)["serves_truth"] is False for r in rows))

    # format adapters read format-specific field names (mcp_registry, airbyte_registry, npm_pypi_search).
    mcp = ingest_dump({"servers": [{"name": "weather-mcp", "description": "NOAA weather", "repository": "https://gh/w", "license": "MIT"}]},
                      registry_format="mcp_registry")
    ck("the mcp_registry adapter maps {servers:[...]} entries to mcp_server-kind rows",
       len(mcp) == 1 and mcp[0]["source_kind"] == "mcp_server" and mcp[0]["source_url"] == "https://gh/w")
    air = ingest_dump({"connectors": [{"name": "Stripe", "documentationUrl": "https://air/stripe", "license_type": "ELv2"}]},
                      registry_format="airbyte_registry")
    ck("the airbyte_registry adapter maps {connectors:[...]} entries (connector kind -> high determinism)",
       len(air) == 1 and air[0]["determinism_ceiling"] == 0.95 and air[0]["license"] == "ELv2")
    npm = ingest_dump([{"name": "phonenumbers", "description": "parse phone numbers", "repository": "https://gh/ph", "license": "Apache-2.0"}],
                      registry_format="npm_pypi_search")
    ck("the npm_pypi_search adapter maps a bare list of packages (library -> determinism 1.0)",
       len(npm) == 1 and npm[0]["determinism_ceiling"] == 1.0)

    # SCALE: a 1,000-entry dump -> ~1,000 candidates in one free deterministic pass.
    big = [{"name": f"connector-{i}", "description": f"extract data from source {i}", "url": f"https://ex/{i}", "kind": "connector", "license": "MIT"}
           for i in range(1000)]
    big_rows = ingest_dump(big, registry_format="generic_catalog")
    ck("bulk ingest scales: 1,000 dump entries -> 1,000 candidate rows in one pass (no LLM)",
       len(big_rows) == 1000 and all(screen(normalize_candidate(r))["accepted"] for r in big_rows[:50]))
    ck("within-dump dedup by slug holds", len(ingest_dump(big + big, registry_format="generic_catalog")) == 1000)

    # ingest_to_feed writes a discovered-feed the runner recognizes + ingests.
    with tempfile.TemporaryDirectory() as td:
        import json
        dump_path = os.path.join(td, "dump.json")
        with open(dump_path, "w", encoding="utf-8") as fh:
            json.dump(generic, fh)
        out = os.path.join(td, "discovered-feed-bulk-test.json")
        summary = ingest_to_feed(dump_path, registry_format="generic_catalog", out_path=out)
        ck("ingest_to_feed writes a discovered-feed JSON (runner-ingestible) and reports the count",
           summary["candidates"] == 6 and os.path.exists(out) and summary["serves_truth"] is False)
        from scripts.context_workers.capability_discovery_runner import discover_feed_files
        from pathlib import Path
        ck("the written feed is discovered by the runner's FeedFileSource",
           Path(out) in set(discover_feed_files(Path(td))))

    # unknown format fails loud; deterministic.
    raised = False
    try:
        ingest_dump(generic, registry_format="not_a_format")
    except ValueError:
        raised = True
    ck("an unknown registry format fails loud", raised)
    ck("ingest is deterministic (same dump -> same rows)",
       ingest_dump(generic, registry_format="generic_catalog") == rows)

    print("\n" + ("PASS - check_teleon_bulk_registry_ingest: machine-readable registry dumps map to governed "
                  "CapabilityCandidate rows WITHOUT an LLM (per-format adapters; deterministic category + kind->"
                  "determinism priors; every row passes the real seeder screen and is flagged BULK-INGESTED for a "
                  "Stage-2 confirm); it scales (1,000 entries -> 1,000 rows in one free pass), dedups, and writes a "
                  "feed the runner ingests. Unknown format fails loud; deterministic; nothing serves truth."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(_self_test() if "--self-test" in sys.argv else 0)
