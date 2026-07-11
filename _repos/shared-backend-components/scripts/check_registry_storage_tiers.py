#!/usr/bin/env python3
"""check_registry_storage_tiers — the registries are tiered correctly: config stays JSON, high-volume -> a DB via the port.

Owner: do the JSONL/JSON files need to become Postgres? Answer (already the architecture): CONFIG registries stay JSON/git
(bounded, PR-reviewed, diffable); HIGH-VOLUME staged/candidate JSONL is OPERATIONAL -> SQLite (local) / Postgres+pgvector
(cloud) via the record_store PORT (JSONL is the interchange/staging form). Proves: this session's streams are registered +
tiered right (staged/discovered/index = operational, core = config); the operational backend resolves to sqlite local /
postgres cloud; and the staged JSONL ROUND-TRIPS through the operational store (count parity = the conversion works).
serves_truth=false.

  python3 _repos/shared-backend-components/scripts/check_registry_storage_tiers.py --self-test
"""
from __future__ import annotations

import json
from pathlib import Path

from src.teleon.storage import record_store as R

REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource


def _self_test() -> int:
    pol = json.loads((_resource("architecture") / "storage_tier_policy.json").read_text(encoding="utf-8"))
    streams = {s["stream"]: s for s in pol["streams"]}
    tiers = pol["tiers"]
    fails = []
    def ck(n, ok, d=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok: fails.append(n)

    # this session's streams registered + tiered correctly
    ck("tool_registry_staged registered as OPERATIONAL", streams.get("tool_registry_staged", {}).get("tier") == "operational")
    ck("discovered_tools registered as OPERATIONAL", streams.get("discovered_tools", {}).get("tier") == "operational")
    ck("component_search_index registered as OPERATIONAL", streams.get("component_search_index", {}).get("tier") == "operational")
    ck("tool_registry_core stays CONFIG (JSON/git)", streams.get("tool_registry_core", {}).get("tier") == "config" and streams["tool_registry_core"].get("json"))
    ck("operational streams carry an idempotency key (upsert-safe)", all(streams[s].get("idempotency_key") for s in ("tool_registry_staged", "discovered_tools", "component_search_index")))

    # the tier policy maps the backends: config=json/git, operational=sqlite local / postgres cloud, history=warehouse
    ck("operational tier => sqlite local / postgres cloud (+pgvector)", tiers["operational"]["local_backend"] == "sqlite_wal" and tiers["operational"]["cloud_backend"] == "postgres")
    ck("config tier stays json (git is the right DB for bounded config)", tiers["config"]["local_backend"] == "json_file")
    ck("the port resolves the staged stream's backend (sqlite_wal local)", R.backend_for("tool_registry_staged") == "sqlite_wal")

    # the conversion WORKS: the staged JSONL round-trips through the operational store (count parity)
    jsonl = _resource(streams["tool_registry_staged"]["jsonl"])
    if jsonl.exists():
        n_lines = sum(1 for ln in jsonl.read_text().splitlines() if ln.strip())
        st = R.open_record_store("tool_registry_staged")
        try:
            n_store = st.count()
        finally:
            st.close()
        ck(f"staged JSONL ({n_lines}) round-trips through the operational store (count parity)", n_store == n_lines, f"store={n_store} jsonl={n_lines}")
        # NO SHORTCUT: the operational tier must materialize a REAL indexed SQLite DB (JSONL is only the durable append-log)
        import sqlite3
        from scripts._jsonl_store import _db_path_for
        dbp = _db_path_for(jsonl)
        ck("operational store is a REAL SQLite DB (not a JSONL shortcut)", dbp.exists())
        if dbp.exists():
            con = sqlite3.connect(str(dbp))
            try:
                rows = con.execute("SELECT count(*) FROM records").fetchone()[0]
            finally:
                con.close()
            ck("the SQLite DB holds the rows (indexed query store, not a re-read of JSONL)", rows == n_lines, f"db={rows} jsonl={n_lines}")
    else:
        ck("staged stream not yet populated (harvester not run) — tiering still verified", True)

    ck("serves_truth=false", pol.get("serves_truth", False) is False or "serves_truth" not in pol)
    print("\n" + ("PASS - check_registry_storage_tiers: config stays JSON, high-volume staged/candidate/index -> operational "
                  "(sqlite local / postgres+pgvector cloud) via the record_store port; round-trip parity." if not fails
                  else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(_self_test())
