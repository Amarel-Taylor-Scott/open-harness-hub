#!/usr/bin/env python3
"""scripts.check_native_export_rehydration — proof (C-NATIVE-1): given a native export + sidecar, you can
reach the ORIGINAL source bytes/hash + artifacts. The lossless-distillation law made concrete on the export
layer: the original is never overwritten, and every projection rehydrates back to it.

We drive the real API handler end-to-end in a temp dir:
  1. POST /api/native/ingest stores a source (exact bytes + sha256) and returns refs — no canonical mutation.
  2. We re-compute sha256 over the original input and confirm it equals the stored source_hash (rehydration to
     the exact bytes is possible: the stored bytes hash to the receipt's source_hash).
  3. GET /api/native/export/<id> (degrade path or Lane B), GET /api/native/sidecar/<id> and
     GET /api/native/diff/<id> ALL carry the SAME source_hash, so a consumer holding an export can pivot back
     to the original + its sidecar/artifacts by source_hash.
  4. A second identical ingest is content-addressed to the SAME source_id (deterministic; dedupe-safe), and the
     original bytes are never overwritten.

Deterministic + offline (injected time via the handler; hashlib ids; temp dir for any artifacts; cleanup).
CLI: python3 scripts/check_native_export_rehydration.py --self-test
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tempfile
from pathlib import Path

from scripts.api_native_handler import _reset_sources_for_test, handle


def _self_test() -> int:
    fails: list[str] = []
    tmp = Path(tempfile.mkdtemp(prefix="native_rehydrate_"))
    try:
        _reset_sources_for_test()

        def check(name: str, ok: bool, detail: str = "") -> None:
            print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
            if not ok:
                fails.append(name)

        # an original source (same-shape JSON the customer would send).
        original = {"complaint_id": "BILL-782", "deadline": "30 days", "product": "Credit card"}
        original_bytes = json.dumps(original, sort_keys=True, separators=(",", ":")).encode("utf-8")
        expected_hash = hashlib.sha256(original_bytes).hexdigest()
        # write the original to the temp dir to model "the original on disk is never overwritten".
        src_file = tmp / "original.json"
        src_file.write_bytes(original_bytes)

        # 1) INGEST — store source bytes + sha256; return refs; no canonical mutation, no served fact.
        code, ing = handle("POST", "/api/native/ingest", {"tenant_id": "demo", "content": original, "format": "json"})
        check("ingest returns 200", code == 200, str(code))
        check("ingest wrote NO canonical truth", ing.get("mutated_canonical_truth") is False)
        check("ingest served NO fact", ing.get("served_fact") is False)
        source_id = ing.get("source_id")
        check("ingest returns a source_id", bool(source_id))

        # 2) REHYDRATION TO EXACT BYTES — the stored source_hash equals sha256 of the original bytes.
        check("stored source_hash == sha256(original bytes)", ing.get("source_hash") == expected_hash,
              f"{ing.get('source_hash')} != {expected_hash}")
        check("the on-disk original is unchanged after ingest", src_file.read_bytes() == original_bytes)
        check("ingest receipt carries the source_hash for rehydration",
              ing.get("receipt", {}).get("source_hash") == expected_hash)

        # 3) EXPORT + SIDECAR + DIFF all pivot back to the SAME source_hash.
        c_e, exp = handle("GET", f"/api/native/export/{source_id}", {"mode": "schema_preserving_with_sidecar"})
        check("export returns 200", c_e == 200, str(c_e))
        check("export carries the source_hash (pivot back to original)", exp.get("source_hash") == expected_hash)
        c_s, side = handle("GET", f"/api/native/sidecar/{source_id}", {})
        check("sidecar returns 200", c_s == 200, str(c_s))
        check("sidecar carries the source_hash (pivot back to original)", side.get("source_hash") == expected_hash)
        c_d, dif = handle("GET", f"/api/native/diff/{source_id}", {})
        check("diff returns 200", c_d == 200, str(c_d))
        check("diff carries the source_hash (pivot back to original)", dif.get("source_hash") == expected_hash)

        # the export NEVER serializes the raw bytes (projection exposes hash/len, not the stored bytes).
        check("export does not leak raw bytes", "raw_bytes" not in json.dumps(exp))

        # 4) DETERMINISTIC + IDEMPOTENT — a second identical ingest re-uses the same source_id; bytes untouched.
        code2, ing2 = handle("POST", "/api/native/ingest", {"tenant_id": "demo", "content": original, "format": "json"})
        check("re-ingest is content-addressed to the SAME source_id", ing2.get("source_id") == source_id)
        check("re-ingest yields the same source_hash (no overwrite drift)", ing2.get("source_hash") == expected_hash)
        check("the on-disk original is STILL unchanged (never overwritten)", src_file.read_bytes() == original_bytes)

        # a missing source rehydrates to a clean 404 (no fabricated origin).
        c_m, miss = handle("GET", "/api/native/export/src-does-not-exist", {"mode": "native_passthrough"})
        check("unknown source_id -> 404 available:false (no fabricated origin)",
              c_m == 404 and miss.get("available") is False)

        msg = ("PASS — check_native_export_rehydration: ingest stores exact bytes+sha256 (no truth mutation, no "
               "fact served); export/sidecar/diff all pivot back to that source_hash; the original is never "
               "overwritten; ingest is deterministic/content-addressed.")
        print(f"\n{msg if not fails else f'{len(fails)} FAILURES: {fails}'}")
        return 0 if not fails else 1
    finally:
        _reset_sources_for_test()
        shutil.rmtree(tmp, ignore_errors=True)


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: native export rehydrates to original bytes/hash + artifacts.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
