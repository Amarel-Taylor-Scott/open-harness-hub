#!/usr/bin/env python3
"""scripts.prove_leaves_hashing_checksum — WORKABLE (proven + TYPED) deterministic leaf primitives for the
`hashing_checksum` family.

A "workable" primitive is not vocabulary: it is a REAL pure deterministic callable that (1) PASSES an executed
proof against a concrete fixture (so serves_truth=true is earned, never hand-set) AND (2) carries CANONICAL edge
types so it can chain in the graph. This module declares >=28 REAL hashing/checksum/content-address leaves
(sha256/sha1/md5/sha224/sha384/sha512/sha3/blake2b/blake2s, crc32/adler32, content-address-id, short-hash,
hmac-shape with a fixed demo key, digest re-encodings) plus a few TRUE-inverse encode/decode pairs proved
reversible via a roundtrip proof, runs EVERY ONE through the imported `run_primitive_proof` (the ONLY thing that
flips serves_truth false->true), keeps ONLY passers, and TYPES each persisted row via `canonicalize_edge` so a
proven leaf is also a chainable one. A deliberately-wrong-expected leaf stays candidate and is never persisted —
that gate is the whole point.

ADD-ONLY / flexible: this is a NEW parallel path. It IMPORTS the shared machinery
(`scripts.mutator_registry.run_primitive_proof`, `scripts.build_edge_type_retrofit.canonicalize_edge`) and plugs
extra pure mutators into the shared `MUTATOR_REGISTRY` via setdefault (idempotent registration, never a rewrite).
It edits NO contract-locked/shared file. All mutator names are `hc_`-prefixed to guarantee no collision with a
concurrent workflow's registrations. Deterministic + offline: no network, no LLM, no wall-clock, no RNG. Fixed
literal timestamp. CLI: --self-test | --write.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import base64 as _b64
import hashlib
import hmac
import json
import sys
import zlib
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

# IMPORT the shared machinery — never edit it (ADD-ONLY).
from scripts.mutator_registry import MUTATOR_REGISTRY, run_primitive_proof  # noqa: E402
from scripts.build_edge_type_retrofit import canonicalize_edge  # noqa: E402

FAMILY = "hashing_checksum"
GENERATED_UTC = "2026-07-03"  # fixed literal — NEVER wall-clock (determinism law)
OUT_DIR = _resource("data") / "dev-intel" / "proven_primitives"
OUT_JSONL = OUT_DIR / "proven_hashing_checksum.jsonl"
OUT_MANIFEST = OUT_DIR / "manifest_hashing_checksum.json"

# A fixed, non-secret demo key for the HMAC-shape leaves (fixed key per the family spec — never random/secret).
_HMAC_KEY = b"hashing-checksum-fixed-demo-key-v1"


# ── receipt helper for the mutator contract (2-tuple: transformed output + a small receipt dict) ──
def _rc(name: str, note: str, *, lossless: bool = False) -> dict[str, Any]:
    return {"record_type": "mutator_receipt", "mutator": name, "family": FAMILY,
            "lossless": lossless, "note": note}


# ── PURE deterministic leaf callables — signature (payload, **kwargs) -> (output, receipt). No I/O, no side effects.
def hc_sha256_hex(payload: str, **_: Any) -> tuple[str, dict[str, Any]]:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest(), _rc("hc_sha256_hex", "SHA-256 hex digest")


def hc_sha1_hex(payload: str, **_: Any) -> tuple[str, dict[str, Any]]:
    return hashlib.sha1(payload.encode("utf-8")).hexdigest(), _rc("hc_sha1_hex", "SHA-1 hex digest")


def hc_md5_hex(payload: str, **_: Any) -> tuple[str, dict[str, Any]]:
    return hashlib.md5(payload.encode("utf-8")).hexdigest(), _rc("hc_md5_hex", "MD5 hex digest")


def hc_sha224_hex(payload: str, **_: Any) -> tuple[str, dict[str, Any]]:
    return hashlib.sha224(payload.encode("utf-8")).hexdigest(), _rc("hc_sha224_hex", "SHA-224 hex digest")


def hc_sha384_hex(payload: str, **_: Any) -> tuple[str, dict[str, Any]]:
    return hashlib.sha384(payload.encode("utf-8")).hexdigest(), _rc("hc_sha384_hex", "SHA-384 hex digest")


def hc_sha512_hex(payload: str, **_: Any) -> tuple[str, dict[str, Any]]:
    return hashlib.sha512(payload.encode("utf-8")).hexdigest(), _rc("hc_sha512_hex", "SHA-512 hex digest")


def hc_sha3_256_hex(payload: str, **_: Any) -> tuple[str, dict[str, Any]]:
    return hashlib.sha3_256(payload.encode("utf-8")).hexdigest(), _rc("hc_sha3_256_hex", "SHA3-256 hex digest")


def hc_sha3_512_hex(payload: str, **_: Any) -> tuple[str, dict[str, Any]]:
    return hashlib.sha3_512(payload.encode("utf-8")).hexdigest(), _rc("hc_sha3_512_hex", "SHA3-512 hex digest")


def hc_blake2b_hex(payload: str, **_: Any) -> tuple[str, dict[str, Any]]:
    return hashlib.blake2b(payload.encode("utf-8")).hexdigest(), _rc("hc_blake2b_hex", "BLAKE2b hex digest")


def hc_blake2s_hex(payload: str, **_: Any) -> tuple[str, dict[str, Any]]:
    return hashlib.blake2s(payload.encode("utf-8")).hexdigest(), _rc("hc_blake2s_hex", "BLAKE2s hex digest")


def hc_crc32_hex(payload: str, **_: Any) -> tuple[str, dict[str, Any]]:
    return format(zlib.crc32(payload.encode("utf-8")) & 0xFFFFFFFF, "08x"), _rc("hc_crc32_hex", "CRC-32 checksum (8 hex)")


def hc_adler32_hex(payload: str, **_: Any) -> tuple[str, dict[str, Any]]:
    return format(zlib.adler32(payload.encode("utf-8")) & 0xFFFFFFFF, "08x"), _rc("hc_adler32_hex", "Adler-32 checksum (8 hex)")


def hc_short_hash_16(payload: str, **_: Any) -> tuple[str, dict[str, Any]]:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16], _rc("hc_short_hash_16", "first 16 hex of SHA-256")


def hc_short_hash_12(payload: str, **_: Any) -> tuple[str, dict[str, Any]]:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12], _rc("hc_short_hash_12", "first 12 hex of SHA-256")


def hc_short_hash_8(payload: str, **_: Any) -> tuple[str, dict[str, Any]]:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:8], _rc("hc_short_hash_8", "first 8 hex of SHA-256")


def hc_content_address_id(payload: str, **_: Any) -> tuple[str, dict[str, Any]]:
    return "cid:sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest(), _rc(
        "hc_content_address_id", "content-address id (cid:sha256:<digest>)")


def hc_named_content_hash(payload: str, **_: Any) -> tuple[str, dict[str, Any]]:
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest(), _rc(
        "hc_named_content_hash", "algo-tagged digest (sha256:<digest>)")


def hc_double_sha256(payload: str, **_: Any) -> tuple[str, dict[str, Any]]:
    inner = hashlib.sha256(payload.encode("utf-8")).digest()
    return hashlib.sha256(inner).hexdigest(), _rc("hc_double_sha256", "SHA-256(SHA-256(bytes)) hex digest")


def hc_sha256_upper_hex(payload: str, **_: Any) -> tuple[str, dict[str, Any]]:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest().upper(), _rc("hc_sha256_upper_hex", "uppercase SHA-256 hex")


def hc_sha256_base64(payload: str, **_: Any) -> tuple[str, dict[str, Any]]:
    return _b64.b64encode(hashlib.sha256(payload.encode("utf-8")).digest()).decode("ascii"), _rc(
        "hc_sha256_base64", "base64 of raw SHA-256 digest bytes")


def hc_canonical_json_sha256(payload: dict[str, Any], **_: Any) -> tuple[str, dict[str, Any]]:
    canon = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(canon).hexdigest(), _rc("hc_canonical_json_sha256", "SHA-256 over canonical (sorted) JSON")


def hc_hmac_sha256_fixed(payload: str, **_: Any) -> tuple[str, dict[str, Any]]:
    return hmac.new(_HMAC_KEY, payload.encode("utf-8"), hashlib.sha256).hexdigest(), _rc(
        "hc_hmac_sha256_fixed", "HMAC-SHA256 under a fixed demo key")


def hc_hmac_sha1_fixed(payload: str, **_: Any) -> tuple[str, dict[str, Any]]:
    return hmac.new(_HMAC_KEY, payload.encode("utf-8"), hashlib.sha1).hexdigest(), _rc(
        "hc_hmac_sha1_fixed", "HMAC-SHA1 under a fixed demo key")


def hc_hmac_md5_fixed(payload: str, **_: Any) -> tuple[str, dict[str, Any]]:
    return hmac.new(_HMAC_KEY, payload.encode("utf-8"), hashlib.md5).hexdigest(), _rc(
        "hc_hmac_md5_fixed", "HMAC-MD5 under a fixed demo key")


def hc_hmac_sha512_fixed(payload: str, **_: Any) -> tuple[str, dict[str, Any]]:
    return hmac.new(_HMAC_KEY, payload.encode("utf-8"), hashlib.sha512).hexdigest(), _rc(
        "hc_hmac_sha512_fixed", "HMAC-SHA512 under a fixed demo key")


def hc_hmac_blake2b_fixed(payload: str, **_: Any) -> tuple[str, dict[str, Any]]:
    return hmac.new(_HMAC_KEY, payload.encode("utf-8"), hashlib.blake2b).hexdigest(), _rc(
        "hc_hmac_blake2b_fixed", "HMAC-BLAKE2b under a fixed demo key")


# ── TRUE-inverse encode/decode pairs (proved reversible via roundtrip). Bytes<->encoded string. ──
def hc_hex_encode(payload: str, **_: Any) -> tuple[str, dict[str, Any]]:
    return payload.encode("utf-8").hex(), _rc("hc_hex_encode", "utf-8 bytes -> hex string; hc_hex_decode restores", lossless=True)


def hc_hex_decode(payload: str, **_: Any) -> tuple[str, dict[str, Any]]:
    return bytes.fromhex(payload).decode("utf-8"), _rc("hc_hex_decode", "hex string -> utf-8 text", lossless=True)


def hc_base64_encode(payload: str, **_: Any) -> tuple[str, dict[str, Any]]:
    return _b64.b64encode(payload.encode("utf-8")).decode("ascii"), _rc(
        "hc_base64_encode", "utf-8 bytes -> base64; hc_base64_decode restores", lossless=True)


def hc_base64_decode(payload: str, **_: Any) -> tuple[str, dict[str, Any]]:
    return _b64.b64decode(payload.encode("ascii")).decode("utf-8"), _rc("hc_base64_decode", "base64 -> utf-8 text", lossless=True)


def hc_base32_encode(payload: str, **_: Any) -> tuple[str, dict[str, Any]]:
    return _b64.b32encode(payload.encode("utf-8")).decode("ascii"), _rc(
        "hc_base32_encode", "utf-8 bytes -> base32; hc_base32_decode restores", lossless=True)


def hc_base32_decode(payload: str, **_: Any) -> tuple[str, dict[str, Any]]:
    return _b64.b32decode(payload.encode("ascii")).decode("utf-8"), _rc("hc_base32_decode", "base32 -> utf-8 text", lossless=True)


#: new pure mutators to plug into the shared registry (idempotent; `hc_`-prefixed to avoid any collision)
_NEW_MUTATORS = {
    "hc_sha256_hex": hc_sha256_hex, "hc_sha1_hex": hc_sha1_hex, "hc_md5_hex": hc_md5_hex,
    "hc_sha224_hex": hc_sha224_hex, "hc_sha384_hex": hc_sha384_hex, "hc_sha512_hex": hc_sha512_hex,
    "hc_sha3_256_hex": hc_sha3_256_hex, "hc_sha3_512_hex": hc_sha3_512_hex,
    "hc_blake2b_hex": hc_blake2b_hex, "hc_blake2s_hex": hc_blake2s_hex,
    "hc_crc32_hex": hc_crc32_hex, "hc_adler32_hex": hc_adler32_hex,
    "hc_short_hash_16": hc_short_hash_16, "hc_short_hash_12": hc_short_hash_12, "hc_short_hash_8": hc_short_hash_8,
    "hc_content_address_id": hc_content_address_id, "hc_named_content_hash": hc_named_content_hash,
    "hc_double_sha256": hc_double_sha256, "hc_sha256_upper_hex": hc_sha256_upper_hex,
    "hc_sha256_base64": hc_sha256_base64, "hc_canonical_json_sha256": hc_canonical_json_sha256,
    "hc_hmac_sha256_fixed": hc_hmac_sha256_fixed, "hc_hmac_sha1_fixed": hc_hmac_sha1_fixed,
    "hc_hmac_md5_fixed": hc_hmac_md5_fixed, "hc_hmac_sha512_fixed": hc_hmac_sha512_fixed,
    "hc_hmac_blake2b_fixed": hc_hmac_blake2b_fixed,
    "hc_hex_encode": hc_hex_encode, "hc_hex_decode": hc_hex_decode,
    "hc_base64_encode": hc_base64_encode, "hc_base64_decode": hc_base64_decode,
    "hc_base32_encode": hc_base32_encode, "hc_base32_decode": hc_base32_decode,
}


def register_new_mutators() -> None:
    """Plug the family's pure mutators into the shared MUTATOR_REGISTRY (setdefault — idempotent, never overwrite)."""
    for name, fn in _NEW_MUTATORS.items():
        MUTATOR_REGISTRY.setdefault(name, fn)


register_new_mutators()


# ── reference fixtures + expected outputs (independent recomputation via stdlib — the repo's own proof pattern) ──
_TXT = "the quick brown fox"  # canonical fixture text for the one-arg hashing leaves
_DCT = {"b": 2, "a": 1}       # unsorted on purpose — canonical-json hashing must sort


def _sha(algo: str, data: bytes) -> str:
    return hashlib.new(algo, data).hexdigest()


_TXTB = _TXT.encode("utf-8")

# spec fields: primitive_id, capability, mutator, fixture, expected, args?, inverse?, input_edge, output_edge
LEAF_SPECS: list[dict[str, Any]] = [
    {"id": "prim:leaf:hc_sha256_hex", "capability": "SHA-256 hex digest of bytes",
     "mutator": "hc_sha256_hex", "fixture": _TXT, "expected": _sha("sha256", _TXTB),
     "input_edge": "Bytes", "output_edge": "HashDigest"},
    {"id": "prim:leaf:hc_sha1_hex", "capability": "SHA-1 hex digest of bytes",
     "mutator": "hc_sha1_hex", "fixture": _TXT, "expected": _sha("sha1", _TXTB),
     "input_edge": "Bytes", "output_edge": "HashDigest"},
    {"id": "prim:leaf:hc_md5_hex", "capability": "MD5 hex digest of bytes",
     "mutator": "hc_md5_hex", "fixture": _TXT, "expected": _sha("md5", _TXTB),
     "input_edge": "Bytes", "output_edge": "HashDigest"},
    {"id": "prim:leaf:hc_sha224_hex", "capability": "SHA-224 hex digest of bytes",
     "mutator": "hc_sha224_hex", "fixture": _TXT, "expected": _sha("sha224", _TXTB),
     "input_edge": "Bytes", "output_edge": "HashDigest"},
    {"id": "prim:leaf:hc_sha384_hex", "capability": "SHA-384 hex digest of bytes",
     "mutator": "hc_sha384_hex", "fixture": _TXT, "expected": _sha("sha384", _TXTB),
     "input_edge": "Bytes", "output_edge": "HashDigest"},
    {"id": "prim:leaf:hc_sha512_hex", "capability": "SHA-512 hex digest of bytes",
     "mutator": "hc_sha512_hex", "fixture": _TXT, "expected": _sha("sha512", _TXTB),
     "input_edge": "Bytes", "output_edge": "HashDigest"},
    {"id": "prim:leaf:hc_sha3_256_hex", "capability": "SHA3-256 hex digest of bytes",
     "mutator": "hc_sha3_256_hex", "fixture": _TXT, "expected": hashlib.sha3_256(_TXTB).hexdigest(),
     "input_edge": "Bytes", "output_edge": "HashDigest"},
    {"id": "prim:leaf:hc_sha3_512_hex", "capability": "SHA3-512 hex digest of bytes",
     "mutator": "hc_sha3_512_hex", "fixture": _TXT, "expected": hashlib.sha3_512(_TXTB).hexdigest(),
     "input_edge": "Bytes", "output_edge": "HashDigest"},
    {"id": "prim:leaf:hc_blake2b_hex", "capability": "BLAKE2b hex digest of bytes",
     "mutator": "hc_blake2b_hex", "fixture": _TXT, "expected": hashlib.blake2b(_TXTB).hexdigest(),
     "input_edge": "Bytes", "output_edge": "HashDigest"},
    {"id": "prim:leaf:hc_blake2s_hex", "capability": "BLAKE2s hex digest of bytes",
     "mutator": "hc_blake2s_hex", "fixture": _TXT, "expected": hashlib.blake2s(_TXTB).hexdigest(),
     "input_edge": "Bytes", "output_edge": "HashDigest"},
    {"id": "prim:leaf:hc_crc32_hex", "capability": "CRC-32 checksum (8 hex) of bytes",
     "mutator": "hc_crc32_hex", "fixture": _TXT, "expected": format(zlib.crc32(_TXTB) & 0xFFFFFFFF, "08x"),
     "input_edge": "Bytes", "output_edge": "Checksum"},
    {"id": "prim:leaf:hc_adler32_hex", "capability": "Adler-32 checksum (8 hex) of bytes",
     "mutator": "hc_adler32_hex", "fixture": _TXT, "expected": format(zlib.adler32(_TXTB) & 0xFFFFFFFF, "08x"),
     "input_edge": "Bytes", "output_edge": "Checksum"},
    {"id": "prim:leaf:hc_short_hash_16", "capability": "first 16 hex of SHA-256 (short id)",
     "mutator": "hc_short_hash_16", "fixture": _TXT, "expected": _sha("sha256", _TXTB)[:16],
     "input_edge": "Bytes", "output_edge": "ShortHash"},
    {"id": "prim:leaf:hc_short_hash_12", "capability": "first 12 hex of SHA-256 (short id)",
     "mutator": "hc_short_hash_12", "fixture": _TXT, "expected": _sha("sha256", _TXTB)[:12],
     "input_edge": "Bytes", "output_edge": "ShortHash"},
    {"id": "prim:leaf:hc_short_hash_8", "capability": "first 8 hex of SHA-256 (short id)",
     "mutator": "hc_short_hash_8", "fixture": _TXT, "expected": _sha("sha256", _TXTB)[:8],
     "input_edge": "Bytes", "output_edge": "ShortHash"},
    {"id": "prim:leaf:hc_content_address_id", "capability": "content-address id (cid:sha256:<digest>)",
     "mutator": "hc_content_address_id", "fixture": _TXT, "expected": "cid:sha256:" + _sha("sha256", _TXTB),
     "input_edge": "Bytes", "output_edge": "ContentAddressId"},
    {"id": "prim:leaf:hc_named_content_hash", "capability": "algo-tagged digest (sha256:<digest>)",
     "mutator": "hc_named_content_hash", "fixture": _TXT, "expected": "sha256:" + _sha("sha256", _TXTB),
     "input_edge": "Bytes", "output_edge": "ContentAddressId"},
    {"id": "prim:leaf:hc_double_sha256", "capability": "SHA-256(SHA-256(bytes)) hex digest",
     "mutator": "hc_double_sha256", "fixture": _TXT,
     "expected": hashlib.sha256(hashlib.sha256(_TXTB).digest()).hexdigest(),
     "input_edge": "Bytes", "output_edge": "HashDigest"},
    {"id": "prim:leaf:hc_sha256_upper_hex", "capability": "uppercase SHA-256 hex digest",
     "mutator": "hc_sha256_upper_hex", "fixture": _TXT, "expected": _sha("sha256", _TXTB).upper(),
     "input_edge": "Bytes", "output_edge": "HashDigest"},
    {"id": "prim:leaf:hc_sha256_base64", "capability": "base64 of raw SHA-256 digest bytes",
     "mutator": "hc_sha256_base64", "fixture": _TXT,
     "expected": _b64.b64encode(hashlib.sha256(_TXTB).digest()).decode("ascii"),
     "input_edge": "Bytes", "output_edge": "HashDigest"},
    {"id": "prim:leaf:hc_canonical_json_sha256", "capability": "SHA-256 over canonical (sorted) JSON",
     "mutator": "hc_canonical_json_sha256", "fixture": _DCT,
     "expected": hashlib.sha256(json.dumps(_DCT, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest(),
     "input_edge": "CanonicalJson", "output_edge": "HashDigest"},
    {"id": "prim:leaf:hc_hmac_sha256_fixed", "capability": "HMAC-SHA256 under a fixed demo key",
     "mutator": "hc_hmac_sha256_fixed", "fixture": _TXT,
     "expected": hmac.new(_HMAC_KEY, _TXTB, hashlib.sha256).hexdigest(),
     "input_edge": "Bytes", "output_edge": "MacDigest"},
    {"id": "prim:leaf:hc_hmac_sha1_fixed", "capability": "HMAC-SHA1 under a fixed demo key",
     "mutator": "hc_hmac_sha1_fixed", "fixture": _TXT,
     "expected": hmac.new(_HMAC_KEY, _TXTB, hashlib.sha1).hexdigest(),
     "input_edge": "Bytes", "output_edge": "MacDigest"},
    {"id": "prim:leaf:hc_hmac_md5_fixed", "capability": "HMAC-MD5 under a fixed demo key",
     "mutator": "hc_hmac_md5_fixed", "fixture": _TXT,
     "expected": hmac.new(_HMAC_KEY, _TXTB, hashlib.md5).hexdigest(),
     "input_edge": "Bytes", "output_edge": "MacDigest"},
    {"id": "prim:leaf:hc_hmac_sha512_fixed", "capability": "HMAC-SHA512 under a fixed demo key",
     "mutator": "hc_hmac_sha512_fixed", "fixture": _TXT,
     "expected": hmac.new(_HMAC_KEY, _TXTB, hashlib.sha512).hexdigest(),
     "input_edge": "Bytes", "output_edge": "MacDigest"},
    {"id": "prim:leaf:hc_hmac_blake2b_fixed", "capability": "HMAC-BLAKE2b under a fixed demo key",
     "mutator": "hc_hmac_blake2b_fixed", "fixture": _TXT,
     "expected": hmac.new(_HMAC_KEY, _TXTB, hashlib.blake2b).hexdigest(),
     "input_edge": "Bytes", "output_edge": "MacDigest"},
    # ── TRUE-inverse encode/decode pairs — roundtrip-proved reversible ──
    {"id": "prim:leaf:hc_hex_roundtrip", "capability": "utf-8 bytes -> hex string (reversible)",
     "mutator": "hc_hex_encode", "fixture": _TXT, "expected": _TXTB.hex(), "inverse": "hc_hex_decode",
     "input_edge": "Bytes", "output_edge": "HexString"},
    {"id": "prim:leaf:hc_hex_decode", "capability": "hex string -> utf-8 text",
     "mutator": "hc_hex_decode", "fixture": _TXTB.hex(), "expected": _TXT,
     "input_edge": "HexString", "output_edge": "Bytes"},
    {"id": "prim:leaf:hc_base64_roundtrip", "capability": "utf-8 bytes -> base64 (reversible)",
     "mutator": "hc_base64_encode", "fixture": _TXT,
     "expected": _b64.b64encode(_TXTB).decode("ascii"), "inverse": "hc_base64_decode",
     "input_edge": "Bytes", "output_edge": "Base64String"},
    {"id": "prim:leaf:hc_base64_decode", "capability": "base64 -> utf-8 text",
     "mutator": "hc_base64_decode", "fixture": _b64.b64encode(_TXTB).decode("ascii"), "expected": _TXT,
     "input_edge": "Base64String", "output_edge": "Bytes"},
    {"id": "prim:leaf:hc_base32_roundtrip", "capability": "utf-8 bytes -> base32 (reversible)",
     "mutator": "hc_base32_encode", "fixture": _TXT,
     "expected": _b64.b32encode(_TXTB).decode("ascii"), "inverse": "hc_base32_decode",
     "input_edge": "Bytes", "output_edge": "Base32String"},
    {"id": "prim:leaf:hc_base32_decode", "capability": "base32 -> utf-8 text",
     "mutator": "hc_base32_decode", "fixture": _b64.b32encode(_TXTB).decode("ascii"), "expected": _TXT,
     "input_edge": "Base32String", "output_edge": "Bytes"},
]

#: deliberately-wrong leaf — the proof gate MUST leave this candidate (never persisted as proven)
NEGATIVE_SPECS: list[dict[str, Any]] = [
    {"id": "prim:leaf:hc_WRONG_expected", "capability": "sha256 with a wrong expected output",
     "mutator": "hc_sha256_hex", "fixture": _TXT, "expected": "deadbeef" * 8,
     "input_edge": "Bytes", "output_edge": "HashDigest"},
]

_SPEC_BY_ID = {s["id"]: s for s in LEAF_SPECS}


def _prove_one(spec: dict[str, Any]) -> dict[str, Any]:
    receipt = run_primitive_proof(
        spec["id"], spec["mutator"], spec["fixture"], spec["expected"],
        mutator_args=spec.get("args") or {}, has_inverse=spec.get("inverse"),
    )
    receipt["capability"] = spec["capability"]
    return receipt


def prove_all() -> list[dict[str, Any]]:
    """Run every declared leaf through the imported executed-proof runner."""
    return [_prove_one(s) for s in LEAF_SPECS]


def proven_index() -> dict[str, dict[str, Any]]:
    """{primitive_id -> receipt} for leaves whose executed proof PASSED (serves_truth=true)."""
    return {r["primitive_id"]: r for r in prove_all() if r["serves_truth"] is True}


def build_rows() -> list[dict[str, Any]]:
    """Proven receipts -> TYPED persistable rows. Only serves_truth=true leaves; each carries canonical edge types."""
    rows: list[dict[str, Any]] = []
    index = proven_index()
    for pid in sorted(index):
        r = index[pid]
        spec = _SPEC_BY_ID[pid]
        input_type = canonicalize_edge(spec["input_edge"])
        output_type = canonicalize_edge(spec["output_edge"])
        rows.append({
            "primitive_id": pid,
            "mutator": r["mutator"],
            "capability": spec["capability"],
            "family": FAMILY,
            "serves_truth": True,
            "candidate": False,
            "verification_level": "L7_executed_proof",
            "input_edge": spec["input_edge"],
            "output_edge": spec["output_edge"],
            "input_edge_type_id": input_type,
            "output_edge_type_id": output_type,
            "has_inverse": spec.get("inverse"),
            "proofs": r["proofs"],
            "input_hash": r["input_hash"],
            "output_hash": r["output_hash"],
        })
    return rows


def build_manifest(rows: list[dict[str, Any]]) -> dict[str, Any]:
    typed = [r for r in rows if r.get("input_edge_type_id") and r.get("output_edge_type_id")]
    canonical = "\n".join(json.dumps(r, sort_keys=True, ensure_ascii=False) for r in rows)
    return {
        "record_type": "proven_hashing_checksum_manifest",
        "pack_id": "proven-hashing-checksum",
        "family": FAMILY,
        "generator": "scripts/prove_leaves_hashing_checksum.py",
        "generated_utc": GENERATED_UTC,
        "declared_leaf_count": len(LEAF_SPECS),
        "proven_count": len(rows),
        "typed_count": len(typed),
        "proven_primitive_ids": sorted(r["primitive_id"] for r in rows),
        "verification_level": "L7_executed_proof",
        "row_counts": {OUT_JSONL.name: len(rows)},
        "total_rows": len(rows),
        "note": "serves_truth=true is set ONLY by an executed passing proof (run_primitive_proof, imported from "
                "scripts/mutator_registry.py); every proven leaf is TYPED via canonicalize_edge so it can chain. "
                "A deliberately-wrong leaf stays candidate and is never persisted here.",
        "content_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
    }


def write_pack() -> dict[str, Any]:
    rows = build_rows()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSONL.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows), encoding="utf-8")
    manifest = build_manifest(rows)
    OUT_MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def self_test() -> int:
    receipts = prove_all()
    index = proven_index()
    rows = build_rows()
    ids = [r["primitive_id"] for r in receipts]

    # a deliberately-wrong leaf must stay candidate (the gate is real, not a rubber stamp)
    wrong = _prove_one(NEGATIVE_SPECS[0])
    # an un-runnable fixture -> execution error -> not promoted
    err = run_primitive_proof("prim:leaf:hc_EXEC_ERROR", "hc_sha256_hex", object(), "irrelevant")

    typed_rows = [r for r in rows if r.get("input_edge_type_id") and r.get("output_edge_type_id")]
    inverse_specs = [s for s in LEAF_SPECS if s.get("inverse")]

    checks: list[tuple[str, bool]] = [
        (">=28 leaf primitives declared", len(LEAF_SPECS) >= 28),
        ("unique primitive ids", len(set(ids)) == len(ids)),
        ("EVERY declared leaf PROVES serves_truth=true via an executed proof",
         all(r["serves_truth"] is True and r["promoted"] is True for r in receipts)),
        (">=28 leaves proven (serves_truth=true)", len(index) >= 28),
        ("every proven receipt is L7_executed_proof with all sub-proofs passing",
         all(r["verification_level"] == "L7_executed_proof" and all(p["passed"] for p in r["proofs"]) for r in receipts)),
        ("EVERY persisted row carries non-null input_edge_type_id + output_edge_type_id",
         len(typed_rows) == len(rows) and len(rows) >= 28),
        ("proven_count == typed_count (every workable leaf is typed)", len(rows) == len(typed_rows)),
        ("roundtrip-inverse pairs prove reversible", bool(inverse_specs) and all(
            any(p["name"] == "roundtrip_test" and p["passed"] for p in index[s["id"]]["proofs"])
            for s in inverse_specs)),
        ("deterministic: re-running yields identical receipts",
         [json.dumps(r, sort_keys=True) for r in prove_all()] == [json.dumps(r, sort_keys=True) for r in receipts]),
        ("a deliberately-wrong leaf stays CANDIDATE (never promoted)",
         wrong["serves_truth"] is False and wrong["promoted"] is False),
        ("the wrong leaf is NOT in the proven index / rows",
         wrong["primitive_id"] not in index and wrong["primitive_id"] not in {r["primitive_id"] for r in rows}),
        ("an un-runnable fixture fails the proof, does not promote",
         err["serves_truth"] is False and err["promoted"] is False),
        ("manifest proven_count/typed_count match the rows",
         build_manifest(rows)["proven_count"] == len(rows) and build_manifest(rows)["typed_count"] == len(typed_rows)),
        ("new mutators registered into the shared registry (add-only seam)",
         all(m in MUTATOR_REGISTRY for m in _NEW_MUTATORS)),
    ]
    failed = [n for n, ok in checks if not ok]
    if failed:
        print("FAIL - prove_leaves_hashing_checksum:\n  " + "\n  ".join(failed))
        return 1
    print(f"PASS - prove_leaves_hashing_checksum: {len(index)} REAL {FAMILY} leaf primitives PROVEN end-to-end "
          f"(serves_truth=true, L7_executed_proof) and TYPED (every row carries canonical input+output edge types); "
          f"{len(inverse_specs)} roundtrip-inverse pairs proved reversible; a deliberately-wrong leaf and an "
          f"un-runnable fixture correctly stay candidate. Workable = proven AND typed.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test and not args.write:
        return self_test()
    manifest = write_pack()
    print(json.dumps({k: v for k, v in manifest.items() if k != "content_sha256"}, indent=2, sort_keys=True))
    return self_test()


if __name__ == "__main__":
    raise SystemExit(main())
