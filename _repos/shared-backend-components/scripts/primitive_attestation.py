#!/usr/bin/env python3
"""primitive_attestation — make the import/vendor reuse lanes trustworthy (open-problems gap 2.6, Move 3).

The strongest token-saving reuse lane is package import / vendor (the model never sees the code), and
governance/provenance is the moat — yet today that lane has the WEAKEST trust story: `formalize_card` writes a
plain `provenance` dict and the packaging pack merely *declares* "cosign-signed" as prose. Nothing recomputes
the content hash, checks revocation, or expires the copy, so a tampered or stale vendored primitive verifies by
assertion. This module closes that: a signed, content-BOUND attestation whose verification recomputes the
digest from the shipped body (catching tampering/staleness), checks the signature, checks a revocation set, and
checks freshness against the existing `primitive_warranty` engine.

Shape (standards-aligned, offline): an in-toto v1 Statement whose subject digest is the SHA-256 of the actual
body, an SLSA-style predicate built from the fields `formalize_card` already emits, signed over a backend ZOO
(hmac_local default → ed25519 → cosign-cloud seam; extend = one row). Deterministic for the local backend.

    PYTHONPATH=. python3 scripts/primitive_attestation.py --self-test
"""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import sys
from pathlib import Path
from typing import Any, Optional

_HERE = Path(__file__).resolve()
_SBC = _HERE.parent.parent
_ROOT = _SBC.parent.parent
for _p in (str(_SBC), str(_SBC / "scripts"), str(_ROOT), str(_ROOT / "_repos" / "teleon" / "backend")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    from src.teleon.experiments.ids import canonical_id  # noqa: E402  the ONE id authority (data plane law)
except Exception as exc:  # noqa: BLE001
    raise SystemExit(f"primitive_attestation requires canonical_id; import failed: {exc}")

IN_TOTO_STATEMENT_TYPE = "https://in-toto.io/Statement/v1"
SLSA_PREDICATE_TYPE = "https://slsa.dev/provenance/v1"
ATTESTATION_ID_PREFIX = "patt"
_DEFAULT_LOCAL_KEY = "oh-attestation-local-dev-key"   # HMAC dev key; a deployment sets OH_ATTESTATION_KEY.


def _sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _canonical_bytes(statement: dict[str, Any]) -> str:
    """The exact bytes a signature covers — canonical JSON so signer and verifier agree byte-for-byte."""
    return json.dumps(statement, sort_keys=True, separators=(",", ":"))


# ── signing backend ZOO (extend = one row). Each: sign(payload, key) + verify(payload, sig, key). ────────────
def _hmac_sign(payload: str, key: str) -> str:
    return hmac.new(key.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()


def _hmac_verify(payload: str, signature: str, key: str) -> bool:
    return hmac.compare_digest(_hmac_sign(payload, key), signature)


SIGNING_BACKENDS: dict[str, dict[str, Any]] = {
    "hmac_local": {"sign": _hmac_sign, "verify": _hmac_verify, "kind": "deterministic",
                   "note": "symmetric HMAC-SHA256 (dev/CI default; a shared key). Deterministic + offline."},
    # ed25519 (public-key, asymmetric) and cosign/Sigstore (keyless, transparency-logged) are declared seams:
    # the real deployment lane. Not run here — no external crypto dependency in the offline self-test.
    "ed25519": {"sign": None, "verify": None, "kind": "seam",
                "note": "asymmetric ed25519 signing — the production lane (pynacl/cryptography); declared, not run"},
    "cosign": {"sign": None, "verify": None, "kind": "seam",
               "note": "keyless Sigstore/cosign + Rekor transparency log — the ecosystem lane; declared, not run"},
}


def build_attestation(formal_card: dict[str, Any], body: str) -> dict[str, Any]:
    """An in-toto v1 Statement over the primitive's ACTUAL body. subject.digest.sha256 = sha256(body) — a
    RECOMPUTABLE binding, so a verifier can catch a tampered/stale copy. Predicate = SLSA-style provenance from
    the fields formalize_card already emits (no new policy invented)."""
    content_digest = _sha256_hex(body)
    provenance = formal_card.get("provenance") or {}
    subject_name = str(formal_card.get("primitive_id") or formal_card.get("impl_name")
                       or formal_card.get("title") or "primitive")
    statement = {
        "_type": IN_TOTO_STATEMENT_TYPE,
        "subject": [{"name": subject_name, "digest": {"sha256": content_digest}}],
        "predicateType": SLSA_PREDICATE_TYPE,
        "predicate": {
            "buildType": "oh:primitive-package-contract",
            "artifact_hash": formal_card.get("artifact_hash"),
            "determinism_level": formal_card.get("determinism_level"),
            "risk_tier": formal_card.get("risk_tier"),
            "verifier_id": formal_card.get("verifier_id"),
            "contract_version": provenance.get("contract_version"),
            "source_pack": provenance.get("source_pack"),
            "lifecycle_stage": formal_card.get("lifecycle_stage", "candidate"),
        },
    }
    return {"attestation_id": canonical_id(ATTESTATION_ID_PREFIX, subject_name, content_digest),
            "record_type": "primitive_attestation_statement", "statement": statement,
            "content_digest_sha256": content_digest, "candidate": True, "serves_truth": False}


def sign_attestation(attestation: dict[str, Any], *, backend: str = "hmac_local",
                     key: str = _DEFAULT_LOCAL_KEY) -> dict[str, Any]:
    """Sign the statement's canonical bytes with the chosen backend. Returns a bundle {statement, signature,
    backend, key_id}. A seam backend (ed25519/cosign) is declared, not run offline."""
    spec = SIGNING_BACKENDS[backend]
    if spec["kind"] == "seam" or spec["sign"] is None:
        return {"record_type": "primitive_attestation_bundle", "statement": attestation["statement"],
                "backend": backend, "signed": False, "seam": True, "note": spec["note"],
                "candidate": True, "serves_truth": False}
    payload = _canonical_bytes(attestation["statement"])
    return {"record_type": "primitive_attestation_bundle", "statement": attestation["statement"],
            "backend": backend, "signature": spec["sign"](payload, key), "signed": True,
            "key_id": _sha256_hex(key)[:16],   # a key fingerprint, never the key itself
            "candidate": True, "serves_truth": False}


def verify_attestation(bundle: dict[str, Any], body: str, *, key: str = _DEFAULT_LOCAL_KEY,
                       revoked_digests: Optional[set[str]] = None,
                       warranty: Optional[dict[str, Any]] = None,
                       now_epoch: Optional[float] = None) -> dict[str, Any]:
    """Verify a signed attestation against the SHIPPED body. Independent checks, all must pass:
      (a) content binding — sha256(body) == the statement's subject digest (catches tamper/staleness);
      (b) signature — valid under the backend + key;
      (c) revocation — the digest is not in `revoked_digests`;
      (d) freshness — if a `warranty` is stapled, primitive_warranty says it is coherent + unexpired at now.
    Returns {verified, checks} — verified only if EVERY applicable check passes."""
    revoked_digests = revoked_digests or set()
    statement = bundle.get("statement") or {}
    claimed = ((statement.get("subject") or [{}])[0].get("digest") or {}).get("sha256")
    actual = _sha256_hex(body)
    checks: dict[str, Any] = {}

    checks["content_binding"] = (claimed == actual)
    backend = bundle.get("backend", "hmac_local")
    spec = SIGNING_BACKENDS.get(backend, {})
    if not bundle.get("signed") or spec.get("verify") is None:
        checks["signature"] = False
        checks["signature_note"] = "unsigned or seam backend — not verifiable offline"
    else:
        checks["signature"] = spec["verify"](_canonical_bytes(statement), bundle.get("signature", ""), key)
    checks["not_revoked"] = actual not in revoked_digests
    if warranty is not None:
        from scripts.primitive_warranty import check_warranty_valid  # noqa: PLC0415  reuse the expiry engine
        result = check_warranty_valid(warranty, now_epoch if now_epoch is not None else 0.0)
        checks["fresh"] = bool(result.get("valid"))
        if not checks["fresh"]:
            checks["fresh_reasons"] = result.get("reasons")
    else:
        checks["fresh"] = True   # no warranty stapled — freshness not asserted, not failed

    verified = bool(checks["content_binding"] and checks["signature"] and checks["not_revoked"]
                    and checks["fresh"])
    return {"record_type": "primitive_attestation_verdict", "verified": verified, "checks": checks,
            "content_digest_sha256": actual, "candidate": True, "serves_truth": False}


def _self_test() -> int:
    checks: list[tuple[str, bool, str]] = []
    body = "def retry(attempt, base=0.1):\n    return base * 2 ** attempt\n"
    formal = {"primitive_id": "prim:example:retry", "artifact_hash": canonical_id("artifact", body, "retry"),
              "determinism_level": "deterministic", "risk_tier": "low",
              "verifier_id": "pack::_self_test", "lifecycle_stage": "candidate",
              "provenance": {"contract_version": "1", "source_pack": "example"}}

    att = build_attestation(formal, body)
    checks.append(("attestation is an in-toto v1 Statement whose subject digest = sha256(the actual body) "
                   "(a recomputable binding), with an SLSA predicate from formalize_card's fields",
                   att["statement"]["_type"] == IN_TOTO_STATEMENT_TYPE
                   and att["statement"]["subject"][0]["digest"]["sha256"] == _sha256_hex(body)
                   and att["statement"]["predicateType"] == SLSA_PREDICATE_TYPE
                   and att["statement"]["predicate"]["determinism_level"] == "deterministic", ""))

    bundle = sign_attestation(att)
    checks.append(("signed with the local HMAC backend; the bundle carries a key FINGERPRINT, never the key",
                   bundle["signed"] and bundle["backend"] == "hmac_local"
                   and bundle.get("signature") and _DEFAULT_LOCAL_KEY not in json.dumps(bundle)
                   and len(bundle["key_id"]) == 16, ""))

    # HAPPY PATH: the untampered, signed, unrevoked body verifies.
    ok_verdict = verify_attestation(bundle, body)
    checks.append(("happy path: the untampered signed body verifies (content binding + signature + not-revoked)",
                   ok_verdict["verified"] is True and all(ok_verdict["checks"][k] for k in
                                                          ("content_binding", "signature", "not_revoked")), ""))

    # MUTATION GATE 1 — a flipped body byte breaks the content binding (catches a tampered/stale vendored copy).
    tampered_body = body.replace("2 ** attempt", "3 ** attempt")
    v1 = verify_attestation(bundle, tampered_body)
    checks.append(("mutation: a tampered body fails content_binding -> verified=False (stale/tampered copy caught)",
                   v1["verified"] is False and v1["checks"]["content_binding"] is False, ""))

    # MUTATION GATE 2 — the digest in the revocation set fails, even with a valid signature + body.
    v2 = verify_attestation(bundle, body, revoked_digests={_sha256_hex(body)})
    checks.append(("mutation: a revoked digest fails not_revoked -> verified=False (revocation is enforced)",
                   v2["verified"] is False and v2["checks"]["not_revoked"] is False
                   and v2["checks"]["content_binding"] is True, ""))

    # MUTATION GATE 3 — a corrupted signature fails, even with the right body.
    bad_bundle = {**bundle, "signature": bundle["signature"][:-4] + "0000"}
    v3 = verify_attestation(bad_bundle, body)
    checks.append(("mutation: a corrupted signature fails -> verified=False (signature is enforced)",
                   v3["verified"] is False and v3["checks"]["signature"] is False, ""))

    # MUTATION GATE 4 — an EXPIRED stapled warranty fails freshness, reusing primitive_warranty's real
    # check_warranty_valid (no re-implementation). A valid warranty at t=100 passes; the SAME warranty checked
    # after its expiry fails -> the whole attestation fails, so a stale vendored copy cannot verify.
    warranty = {"record_type": "primitive_warranty", "warranty_id": "war:example:1",
                "primitive_id": "prim:example:retry", "schema_version": "1", "tested_on": ["case1"],
                "expected_accuracy_range": [0.9, 1.0], "attested_accuracy": 0.95, "expires_after_days": 7,
                "issued_at": 100.0, "expires_at": 200.0, "evidence_refs": ["oracle:self_test"]}
    fresh_v = verify_attestation(bundle, body, warranty=warranty, now_epoch=150.0)     # within window
    expired_v = verify_attestation(bundle, body, warranty=warranty, now_epoch=300.0)   # past expires_at
    checks.append(("mutation: reusing primitive_warranty.check_warranty_valid, a stapled warranty valid at "
                   "now=150 passes but the SAME one at now=300 is EXPIRED -> verified=False (a stale copy fails)",
                   fresh_v["checks"]["fresh"] is True and fresh_v["verified"] is True
                   and expired_v["checks"]["fresh"] is False and expired_v["verified"] is False,
                   json.dumps({"fresh": fresh_v["checks"]["fresh"], "expired": expired_v["checks"]["fresh"]})))

    # DETERMINISM + backend zoo honesty.
    checks.append(("hmac backend deterministic (same statement+key -> same signature); ed25519/cosign are "
                   "DECLARED seams, not run offline",
                   sign_attestation(att)["signature"] == sign_attestation(att)["signature"]
                   and SIGNING_BACKENDS["ed25519"]["kind"] == "seam"
                   and sign_attestation(att, backend="cosign")["seam"] is True, ""))

    ok = all(passed for _n, passed, _d in checks)
    print(f"{'PASS' if ok else 'FAIL'} - primitive_attestation: signed, content-BOUND attestation for the "
          f"import/vendor lanes (gap 2.6) — in-toto v1 + SLSA predicate over sha256(body); verify recomputes "
          f"the digest (catches tampered/stale copies), checks signature + revocation + primitive_warranty "
          f"freshness; 4 injected defects each force verified=False. serves_truth=false")
    for name, passed, detail in checks:
        print(f"  [{'ok' if passed else 'XX'}] {name}" + (f"  ({detail[:200]})" if not passed else ""))
    return 0 if ok else 1


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Signed content-bound attestations for primitive packages.")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
