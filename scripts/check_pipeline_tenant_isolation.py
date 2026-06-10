#!/usr/bin/env python3
"""scripts.check_pipeline_tenant_isolation — proof: per_tenant_db keeps tenants in SEPARATE db files.

For a pipeline whose manifest sets isolation=per_tenant_db, two tenants' runs + artifacts must live in
PHYSICALLY separate SQLite files — no row of one tenant can appear in another's db (the "never mix
customer data in a shared table" requirement). Cross-checked at the raw SQLite level. Also: tenant ids
are path-sanitized (no traversal); shared isolation still co-locates (contrast).

CLI:
    python3 scripts/check_pipeline_tenant_isolation.py --self-test
"""
from __future__ import annotations

import argparse
import shutil
import sqlite3
import tempfile
from pathlib import Path

from scripts.pipeline_runtime.isolation import db_for_tenant, resolve, tenant_slug
from scripts.pipeline_runtime.processors import default_registry
from scripts.pipeline_runtime.runner import run_pipeline
from scripts.pipeline_runtime.specs import discover, validate


def _raw_tenants(db_path: str) -> set[str]:
    c = sqlite3.connect(db_path)
    try:
        return {t for (t,) in c.execute("SELECT DISTINCT tenant_id FROM pipeline_runs").fetchall()}
    finally:
        c.close()


def _self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    reg = default_registry()
    specs = discover()
    spec = specs.get("cfpb_isolated_ingest@v1")
    check("cfpb_isolated_ingest@v1 discovered + isolation=per_tenant_db", spec and spec.isolation == "per_tenant_db")
    check("isolated pipeline validates", validate(spec, registry=reg) == [], str(validate(spec, registry=reg)))

    base = tempfile.mkdtemp(prefix="pipe-isolation-")
    run_input = {"fixture": True, "limit": 5, "source_id": "cfpb"}

    # path-safety: a malicious tenant id cannot escape the base dir
    check("tenant id is path-sanitized (no traversal)", tenant_slug("../../etc/passwd") == "etc-passwd")

    # distinct db files per tenant
    db_a = db_for_tenant("acme", base_dir=base, isolation="per_tenant_db")
    db_b = db_for_tenant("globex", base_dir=base, isolation="per_tenant_db")
    check("each tenant resolves to a SEPARATE db path", db_a != db_b and "acme" in db_a and "globex" in db_b)
    check("shared isolation co-locates (contrast)",
          db_for_tenant("acme", base_dir=base, isolation="shared") == db_for_tenant("globex", base_dir=base, isolation="shared"))

    # run the isolated pipeline for two tenants
    store_a, ledger_a, path_a = resolve(spec, "acme", base_dir=base)
    ra = run_pipeline(spec, tenant_id="acme", run_input=run_input, ledger=ledger_a, registry=reg)
    store_b, ledger_b, path_b = resolve(spec, "globex", base_dir=base)
    rb = run_pipeline(spec, tenant_id="globex", run_input=run_input, ledger=ledger_b, registry=reg)
    check("both tenant runs reached done", ra["status"] == "done" and rb["status"] == "done", f"{ra['status']}/{rb['status']}")
    check("the two runs went to different db files", path_a != path_b and path_a == db_a and path_b == db_b)
    check("both db files exist on disk", Path(path_a).exists() and Path(path_b).exists())

    # ledgers only see their own tenant
    check("acme ledger has acme's run, NOT globex's",
          {r["run_id"] for r in ledger_a.list_runs()} == {ra["run_id"]})
    check("globex ledger has globex's run, NOT acme's",
          {r["run_id"] for r in ledger_b.list_runs()} == {rb["run_id"]})

    # raw SQLite cross-check: NO row mixing at the file level
    check("acme.db contains ONLY tenant 'acme'", _raw_tenants(path_a) == {"acme"}, str(_raw_tenants(path_a)))
    check("globex.db contains ONLY tenant 'globex'", _raw_tenants(path_b) == {"globex"}, str(_raw_tenants(path_b)))
    # and artifacts are physically separated too
    ca = sqlite3.connect(path_a); na = ca.execute("SELECT COUNT(*) FROM artifacts").fetchone()[0]; ca.close()
    cb = sqlite3.connect(path_b); nb = cb.execute("SELECT COUNT(*) FROM artifacts").fetchone()[0]; cb.close()
    check("each tenant db holds its own artifacts (>0, separate files)", na > 0 and nb > 0)

    store_a.close()
    store_b.close()
    # isolation cache holds open handles; clear them so the temp dir can be removed cleanly
    from scripts.pipeline_runtime import isolation as _iso
    _iso._STORE_CACHE.clear()
    shutil.rmtree(base, ignore_errors=True)
    print(f"\n{'PASS — check_pipeline_tenant_isolation: per_tenant_db places each tenant in a SEPARATE db file; no cross-tenant row at the raw SQLite level; tenant ids path-sanitized.' if not failures else f'{len(failures)} FAILURES: {failures}'}")
    return 0 if not failures else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: per-tenant DB isolation (separate files, no row mixing).")
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args(argv)
    if args.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
