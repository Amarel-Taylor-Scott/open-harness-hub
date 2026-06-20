#!/usr/bin/env python3
"""scripts.check_native_api — proof (C-NATIVE-1): the Native Format Preservation API
(scripts/api_native_handler.py) is projection-safe. Tests the PURE request handler (no socket), so the
contract is deterministic + offline.

Asserts each of the 5 routes returns the expected dict shape, and the safety invariants:
  - POST /api/native/ingest stores a source + returns refs; mutated_canonical_truth=false; served_fact=false;
  - GET  /api/native/export/<id>  is projection_only and carries source_hash; unknown mode -> 400; absent
    source -> 404; the degrade path returns the unchanged original (no value applied);
  - GET  /api/native/sidecar/<id>, /diff/<id>, /annotations/<id> all return well-formed dicts tied to source_hash;
  - non-GET on a read route -> 405; non-POST on ingest -> 405; an unknown route -> 404;
  - owns() recognizes every native route and rejects foreign ones;
  - NO secret marker appears in ANY response (defense-in-depth scrub) and raw bytes are never serialized.

Deterministic + offline. CLI: python3 scripts/check_native_api.py --self-test
"""
from __future__ import annotations

import argparse
import json

from scripts.api_native_handler import _reset_sources_for_test, handle, owns

#: a secret-LOOKING probe assembled at runtime so this proof never contains a literal sk-<16+chars> token.
#: We feed it as ingest content and assert nothing matching a secret marker comes back in any response.
_SECRET_TOKEN_PROBE = "Authorization: Bearer " + "sk-" + ("0123456789abcdef" * 2)


def _no_secret(payload) -> bool:
    blob = json.dumps(payload)
    return not any(m in blob for m in ("OH_SHOWCASE_TOKEN", "sk-", "Bearer ", "MEMORY.md", ".agent/"))


def _self_test() -> int:
    fails: list[str] = []
    _reset_sources_for_test()

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    # ── owns() ──
    for r in ("/api/native/ingest", "/api/native/export/abc", "/api/native/sidecar/abc",
              "/api/native/diff/abc", "/api/native/annotations/abc"):
        check(f"owns({r})", owns(r))
    check("owns() rejects a foreign route", not owns("/api/context/serve"))

    # ── POST /api/native/ingest ── (store-only; no canonical mutation; no fact served)
    code, ing = handle("POST", "/api/native/ingest",
                       {"tenant_id": "demo", "content": {"deadline": "30 days", "product": "card"}, "format": "json"})
    check("POST ingest returns 200", code == 200, str(code))
    check("ingest result is NativeIngestResult.v1", ing.get("schema_version") == "NativeIngestResult.v1")
    check("ingest mutated_canonical_truth=false", ing.get("mutated_canonical_truth") is False)
    check("ingest served_fact=false", ing.get("served_fact") is False)
    check("ingest returns source_id + source_hash + refs",
          bool(ing.get("source_id")) and bool(ing.get("source_hash")) and isinstance(ing.get("refs"), dict))
    check("ingest does NOT serialize raw_bytes", "raw_bytes" not in json.dumps(ing))
    source_id = ing["source_id"]

    # ingest with missing content -> 400 (clean, no crash)
    c_bad, p_bad = handle("POST", "/api/native/ingest", {"tenant_id": "demo"})
    check("ingest with no content -> 400", c_bad == 400 and "error" in p_bad)

    # ── GET /api/native/export/<id> ──
    c_e, exp = handle("GET", f"/api/native/export/{source_id}", {"mode": "native_passthrough"})
    check("export returns 200", c_e == 200, str(c_e))
    check("export is projection_only", exp.get("projection_only") is True)
    check("export carries source_hash", exp.get("source_hash") == ing["source_hash"])
    # degrade path (Lane B absent): passthrough returns the unchanged original, byte_identical, no diff applied.
    if exp.get("available") is False:
        check("degrade export is byte_identical passthrough", exp.get("byte_identical") is True)
        check("degrade export applies no value change", exp.get("diff", {}).get("changed_fields") == [])

    # unknown mode -> 400
    c_um, p_um = handle("GET", f"/api/native/export/{source_id}", {"mode": "not_a_mode"})
    check("unknown output_mode -> 400", c_um == 400 and "error" in p_um)
    # absent source -> 404
    c_404, p_404 = handle("GET", "/api/native/export/src-missing", {"mode": "native_passthrough"})
    check("absent source export -> 404 available:false", c_404 == 404 and p_404.get("available") is False)

    # ── GET sidecar / diff / annotations ──
    c_s, side = handle("GET", f"/api/native/sidecar/{source_id}", {})
    check("sidecar returns 200 with source_hash", c_s == 200 and side.get("source_hash") == ing["source_hash"])
    c_d, dif = handle("GET", f"/api/native/diff/{source_id}", {})
    check("diff returns 200 with a changed_fields list",
          c_d == 200 and isinstance(dif.get("diff", {}).get("changed_fields"), list))
    c_a, ann = handle("GET", f"/api/native/annotations/{source_id}", {})
    check("annotations returns 200 with an annotations list",
          c_a == 200 and isinstance(ann.get("annotations"), list))

    # ── method guards ──
    check("non-POST on ingest -> 405", handle("GET", "/api/native/ingest", {})[0] == 405)
    check("POST on a read route -> 405", handle("POST", f"/api/native/export/{source_id}", {})[0] == 405)
    check("unknown native route -> 404", handle("GET", "/api/native/unknown", {})[0] == 404)

    # ── secrets: probe ingest with secret-looking content; nothing leaks back ──
    c_sec, sec = handle("POST", "/api/native/ingest",
                        {"tenant_id": "demo", "content": _SECRET_TOKEN_PROBE, "format": "text"})
    check("secret-looking ingest still 200 (stored as bytes, hashed)", c_sec == 200)
    # every response we produced is secret-free
    for label, payload in (("ingest", ing), ("export", exp), ("sidecar", side), ("diff", dif),
                           ("annotations", ann), ("secret-ingest", sec)):
        check(f"no secret marker in {label} response", _no_secret(payload))

    print(f"\n{'PASS — check_native_api: all 5 native routes return expected dicts; ingest writes no canonical truth and serves no fact; export is projection-only (unknown mode 400, absent 404); method guards hold; no secrets leak.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    _reset_sources_for_test()
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: native API is projection-safe (ingest store-only; export read-only).")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
