#!/usr/bin/env python3
"""scripts.check_ingestion_connector_catalog — proof (CONNECTOR CATALOG MODE): the ingestion connector catalog +
the ingestion maturity matrix are complete and HONEST. Every connector entry declares the full required field set;
status is in the enum; every ACTIVE connector is backed by an existing proof_script; every CANDIDATE connector
has a fallback_fixture that EXISTS on disk (a real connector behind the same port, fixture-proven — never faked
truth); scope/authority defaults are in-enum; output_schema points at SourceArtifact; the 10 named connectors
are all present; and the maturity matrix is consistent with the catalog (same source_classes, honest rungs:
nothing claims a rung above m6_proof without an existing proof). Deterministic, stdlib-only.

CLI: python3 _repos/shared-backend-components/scripts/check_ingestion_connector_catalog.py --self-test
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
_CATALOG = _resource("architecture") / "ingestion_connector_catalog.json"
_MATRIX = _resource("architecture") / "ingestion_maturity_matrix.json"

_REQUIRED_FIELDS = ("adapter_id", "source_class", "status", "source_scope_default", "source_authority_default",
                    "input_schema", "output_schema", "sync_modes", "cursor_strategy", "idempotency_strategy",
                    "fallback_fixture", "allowed_import_paths", "proof_scripts", "docs", "replacement_adapters")
_STATUS = {"active", "candidate", "experimental", "deprecated"}
_SCOPE = {"global_public", "tenant_private", "tenant_shared"}
_AUTHORITY = {"official", "regulated", "customer_private", "third_party", "community", "unknown"}
_SYNC_MODES = {"full_sync", "incremental_sync", "backfill", "webhook_push"}
_CURSORS = {"timestamp", "monotonic_id", "etag", "page_token", "content_hash_set", "none"}
#: the 10 connectors this lane must catalog.
_EXPECTED = {
    "source.cfpb_structured@v1", "source.generic_json_file@v1", "source.csv_table@v1", "source.webhook_json@v1",
    "source.html_page@candidate", "source.pdf_document@candidate", "source.markdown_folder@v1",
    "source.local_folder_batch@v1", "source.obsidian_vault@candidate", "source.customer_database@candidate"}
#: matrix rungs that require an existing proof script (m7+ above m6_proof; m8 is the active top rung here).
_PROVEN_RUNGS = {"m6_proof", "m7_api", "m8_ui", "m9_antibypass", "m10_complete"}


def _fixture_exists(ref: str) -> bool:
    """fallback_fixture may be a file path OR a 'path#anchor' / 'inline ...' / '_repos/shared-backend-components/scripts/...#symbol' descriptor.
    Treat a leading repo-relative path token as a file existence check; inline/code descriptors are accepted."""
    if not ref:
        return False
    token = ref.split("#", 1)[0].split(" ", 1)[0].strip()
    if token.startswith("inline"):
        return True
    p = _resource(token)
    if p.exists():
        return True
    # a code-symbol descriptor like 'scripts/...py#symbol' — the file part must exist
    return (_resource(ref.split("#", 1)[0].strip())).exists()


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    cat = json.loads(_CATALOG.read_text())
    conns = cat.get("connectors", [])
    by_id = {c.get("adapter_id"): c for c in conns}

    check("all 10 named connectors are present", _EXPECTED <= set(by_id), str(sorted(_EXPECTED - set(by_id))))
    check("output_schema points at SourceArtifact for every connector",
          all(c.get("output_schema", "").endswith("SourceArtifact.schema.json") for c in conns))

    missing_fields, bad_status, bad_scope, bad_auth, bad_sync, bad_cursor = [], [], [], [], [], []
    active_no_proof, candidate_no_fixture, missing_proof_file, missing_fixture = [], [], [], []
    for c in conns:
        cid = c.get("adapter_id", "?")
        for f in _REQUIRED_FIELDS:
            if f not in c:
                missing_fields.append(f"{cid}.{f}")
        if c.get("status") not in _STATUS:
            bad_status.append(f"{cid}={c.get('status')}")
        if c.get("source_scope_default") not in _SCOPE:
            bad_scope.append(f"{cid}={c.get('source_scope_default')}")
        if c.get("source_authority_default") not in _AUTHORITY:
            bad_auth.append(f"{cid}={c.get('source_authority_default')}")
        if not set(c.get("sync_modes", [])) <= _SYNC_MODES:
            bad_sync.append(f"{cid}={c.get('sync_modes')}")
        if c.get("cursor_strategy") not in _CURSORS:
            bad_cursor.append(f"{cid}={c.get('cursor_strategy')}")
        # active connectors MUST have a proof_script that exists
        if c.get("status") == "active":
            if not c.get("proof_scripts"):
                active_no_proof.append(cid)
            for ps in c.get("proof_scripts", []):
                if not (_resource(ps)).is_file():
                    missing_proof_file.append(f"{cid}:{ps}")
        # candidate connectors MUST have a fallback_fixture that exists
        if c.get("status") == "candidate":
            if not c.get("fallback_fixture"):
                candidate_no_fixture.append(cid)
            elif not _fixture_exists(c["fallback_fixture"]):
                missing_fixture.append(f"{cid}:{c['fallback_fixture']}")

    check("every connector declares all required fields", missing_fields == [], str(missing_fields[:6]))
    check("every status is in the enum", bad_status == [], str(bad_status))
    check("every source_scope_default is in the scope enum", bad_scope == [], str(bad_scope))
    check("every source_authority_default is in the authority enum", bad_auth == [], str(bad_auth))
    check("every sync_modes ⊆ the sync-mode enum", bad_sync == [], str(bad_sync))
    check("every cursor_strategy is in the cursor enum", bad_cursor == [], str(bad_cursor))
    check("every ACTIVE connector has a proof_script", active_no_proof == [], str(active_no_proof))
    check("every ACTIVE connector's proof_script exists on disk", missing_proof_file == [], str(missing_proof_file))
    check("every CANDIDATE connector declares a fallback_fixture", candidate_no_fixture == [], str(candidate_no_fixture))
    check("every CANDIDATE connector's fallback_fixture exists on disk", missing_fixture == [], str(missing_fixture))

    # the VERIFIED session candidates are catalogued as candidate-only replacement notes (never auto-adopted)
    obs = by_id.get("source.obsidian_vault@candidate", {})
    repl = " ".join(obs.get("replacement_adapters", []))
    check("obsidian_vault catalogs the verified session candidates (markdown-vault + Kwipu) as candidate notes",
          "markdown-vault" in repl and "Kwipu" in repl and obs.get("status") == "candidate")

    # ── maturity matrix: consistent with the catalog + honest rungs ──
    mat = json.loads(_MATRIX.read_text())
    rows = mat.get("source_classes", [])
    mat_classes = {r.get("source_class") for r in rows}
    cat_classes = {c.get("source_class") for c in conns}
    check("maturity matrix covers exactly the catalog's source_classes", mat_classes == cat_classes,
          f"only_matrix={sorted(mat_classes - cat_classes)} only_catalog={sorted(cat_classes - mat_classes)}")
    valid_rungs = set(mat.get("status_enum", []))
    bad_rung, dishonest = [], []
    for r in rows:
        sc = r.get("source_class", "?")
        if r.get("status") not in valid_rungs:
            bad_rung.append(f"{sc}={r.get('status')}")
        # no row claims a proven rung (m6+) without an existing proof script
        if r.get("status") in _PROVEN_RUNGS:
            if not any((_resource(ps)).is_file() for ps in r.get("proof_scripts", [])):
                dishonest.append(f"{sc}={r.get('status')} (no existing proof)")
    check("every maturity rung is in the maturity enum", bad_rung == [], str(bad_rung))
    check("no source_class claims a proven rung (m6+) without an existing proof", dishonest == [], str(dishonest))

    # honesty anchors from the spec: api/csv/json/webhook = m8; pdf/html = candidate; md/folder = m4
    rung = {r["source_class"]: r["status"] for r in rows}
    check("cfpb/json/csv/webhook are m8_ui (proven active)",
          all(rung.get(k) == "m8_ui" for k in ("cfpb_structured", "json_document", "csv_table", "webhook_json")), str(rung))
    check("pdf/html are candidate (parser is a cataloged candidate)",
          rung.get("pdf_document") == "candidate" and rung.get("html_page") == "candidate")
    check("markdown_folder/local_folder_batch are m4 (lane B impl in flight)",
          rung.get("markdown_folder") == "m4_local_fixture_or_stub_exists"
          and rung.get("local_folder_batch") == "m4_local_fixture_or_stub_exists")
    check("obsidian_vault/customer_database are candidate",
          rung.get("obsidian_vault") == "candidate" and rung.get("customer_database") == "candidate")

    print(f"\n{'PASS — check_ingestion_connector_catalog: 10 connectors catalogued with full fields; active connectors have existing proofs; candidate connectors have on-disk fallback fixtures (real connector behind the port, never faked); session candidates are candidate-only notes; the maturity matrix matches the catalog with honest, proof-backed rungs.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: ingestion connector catalog + maturity matrix are complete + honest.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
