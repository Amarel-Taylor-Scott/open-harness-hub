#!/usr/bin/env python3
"""scripts.check_artifact_security_metadata — proof: every artifact carries a complete security envelope,
and KMS key rotation changes the security metadata but NOT the content_hash (re-encryption, not reprocess).

CLI: python3 _repos/shared-backend-components/scripts/check_artifact_security_metadata.py --self-test
"""
from __future__ import annotations

import argparse

from scripts.pipeline_runtime.cfpb_artifacts import build_cfpb_artifacts
from scripts.pipeline_runtime.source_graph import build_cfpb_source_graph
from scripts.security.tenant_catalog import TenantPolicy, rotate_key, security_complete

RECORD = {"complaint_id": "CFPB-1", "product": "Credit card", "issue": "Billing dispute",
          "company": "Acme Bank", "state": "CA", "date_received": "2026-01-02",
          "consumer_complaint_narrative": "I was charged twice. The company refused to refund me. This is unfair."}


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    policy = TenantPolicy("acme", "database_per_tenant", data_plane_ref="db-acme")
    sg = build_cfpb_source_graph(RECORD, policy)
    out = build_cfpb_artifacts(RECORD, policy)

    check("every SOURCE artifact has a complete security envelope",
          all(security_complete(a.security_json) for a in sg.values()))
    check("every DERIVED artifact has a complete security envelope",
          all(security_complete(a.security_json) for a in out["artifacts"]))
    check("security metadata carries tenant + kms key ref + key version + retention + residency",
          all(a.security_json.get("kms_key_ref") and a.security_json.get("kms_key_version")
              and a.security_json.get("retention_policy_id") and a.security_json.get("data_residency")
              for a in out["artifacts"]))

    art = out["artifacts"][0]
    before_hash, before_ver = art.content_hash, art.security_json["kms_key_version"]
    rotated = rotate_key(art.security_json)
    check("KMS rotation BUMPS the key version", rotated["kms_key_version"] != before_ver,
          f"{before_ver}->{rotated['kms_key_version']}")
    check("KMS rotation does NOT change the artifact content_hash (re-encryption, not reprocess)",
          art.content_hash == before_hash)
    check("rotated envelope is still complete", security_complete(rotated))

    # a source artifact too
    sa = next(iter(sg.values()))
    h0 = sa.content_hash
    sa.security_json = rotate_key(sa.security_json)
    check("source artifact content_hash unchanged after key rotation", sa.content_hash == h0)

    print(f"\n{'PASS — check_artifact_security_metadata: complete security envelope on all artifacts; key rotation is re-encryption (content_hash unchanged).' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: artifact security metadata + key-rotation invariant.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
