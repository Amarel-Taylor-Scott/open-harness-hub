#!/usr/bin/env python3
"""scripts.esoteric_platform_primitive_pack — very-specific, platform/technology-specific, esoteric DETERMINISTIC
primitives with REAL reference implementations + oracle fixtures (candidate-only).

This is the negative-space wedge made concrete: obscure, platform-bound, deterministic transforms that base
models routinely get wrong (packed decimal, protobuf zigzag, ASN.1 DER length octets, RFC 5952 IPv6
compression, SemVer 2.0 precedence, EBCDIC, DICOM tags, HL7 MSH, FIX). Each primitive ships:

  - a working reference implementation (the executor body IS `inspect.getsource(fn)` — single source, no drift);
  - typed input/output edges;
  - ORACLE fixtures (input -> expected) that the self-test actually runs (mutation-gated: break an impl -> RED).

Unlike open-ended specs ("parse legacy MySQL"), these are pure, fixturable functions, so they are immediately
WORKING and certifiable with NO dependency on the throttled LLM synthesizer. Everything is candidate=true /
serves_truth=false; correctness here means "oracle fixtures pass", not "promoted truth".

Where a correct deterministic oracle already exists in the stdlib (cp037/punycode codecs, base32, zlib.crc32,
ipaddress), the primitive WRAPS it as a named, platform-tagged capability — reuse-first, and the stdlib is the
provenance.

    python3 scripts/esoteric_platform_primitive_pack.py --self-test
    python3 scripts/esoteric_platform_primitive_pack.py --emit
    python3 scripts/esoteric_platform_primitive_pack.py --show
"""
from __future__ import annotations

import sys
from pathlib import Path

# ── substrate-root bootstrap (sentinel; mirrors scripts/ml_lifecycle_primitive_minter.py) ────────────────────
_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots, resource  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import base64  # noqa: E402
import inspect  # noqa: E402
import ipaddress  # noqa: E402
import json  # noqa: E402
import zlib  # noqa: E402
from typing import Any, Callable  # noqa: E402

try:
    from src.teleon.experiments.ids import canonical_id  # noqa: E402
except Exception as exc:  # noqa: BLE001
    raise SystemExit(f"esoteric_platform_primitive_pack requires canonical_id; import failed: {exc}")

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
ESO_ID_PREFIX = "prim-eso"
ESO_RECORD_TYPE = "esoteric_platform_primitive_candidate"
PACK_FILENAME = "esoteric_platform_primitive_cards.jsonl"
MANIFEST_FILENAME = "esoteric_platform_primitive_manifest.json"
PACK_DIR_REL = "data/dev-intel/primitive_factory/specialized_packs"
PACKAGED_AT = "2026-07-08T00:00:00Z"


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════
# Reference implementations. Each is a pure, module-level function so inspect.getsource() yields a standalone
# executor body. Correctness is enforced by the fixtures below (the self-test runs them).
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════

def ebcdic_cp037_decode(data: bytes) -> str:
    """Mainframe (IBM z/OS, COBOL): decode EBCDIC code page 037 bytes to Unicode text."""
    return data.decode("cp037")


def cobol_comp3_decode(data: bytes) -> int:
    """Mainframe COBOL COMP-3 (packed decimal): 2 digits per byte, final nibble is the sign
    (0xC/0xF => positive, 0xD => negative)."""
    nibbles = []
    for byte in data:
        nibbles.append(byte >> 4)
        nibbles.append(byte & 0x0F)
    sign = nibbles.pop()
    value = 0
    for digit in nibbles:
        value = value * 10 + digit
    return -value if sign == 0x0D else value


def protobuf_varint_decode(data: bytes) -> int:
    """Protocol Buffers wire format: decode a base-128 varint (LEB128, 7 bits/byte, MSB = continuation)."""
    result = 0
    shift = 0
    for byte in data:
        result |= (byte & 0x7F) << shift
        if not (byte & 0x80):
            break
        shift += 7
    return result


def protobuf_zigzag_decode(n: int) -> int:
    """Protocol Buffers sint32/sint64 ZigZag decode: map an unsigned varint back to a signed int."""
    return (n >> 1) ^ -(n & 1)


def fix_message_parse(message: str) -> dict:
    """FIX protocol (finance/trading): split a SOH(0x01)-delimited message into {tag: value} (tags as strings)."""
    out: dict = {}
    for field in message.split("\x01"):
        if not field:
            continue
        tag, sep, value = field.partition("=")
        if sep:
            out[tag] = value
    return out


def asn1_der_length_decode(data: bytes) -> list:
    """ASN.1 DER (X.509/TLS/crypto): decode a length field. Returns [length_value, octets_consumed].
    Short form: first octet < 0x80 is the length. Long form: 0x80|n, then n big-endian length octets."""
    first = data[0]
    if first < 0x80:
        return [first, 1]
    n = first & 0x7F
    length = int.from_bytes(data[1:1 + n], "big")
    return [length, 1 + n]


def dicom_tag_parse(data: bytes) -> list:
    """DICOM (medical imaging): parse a 4-byte little-endian data element tag into [group, element] ints."""
    group = int.from_bytes(data[0:2], "little")
    element = int.from_bytes(data[2:4], "little")
    return [group, element]


def hl7_v2_msh_parse(segment: str) -> dict:
    """HL7 v2.x (healthcare messaging): parse an MSH header. MSH-1 is the field separator (char at index 3),
    MSH-2 is the encoding characters; return the load-bearing header fields."""
    if segment[:3] != "MSH":
        raise ValueError("not an MSH segment")
    field_sep = segment[3]
    fields = segment.split(field_sep)
    return {
        "field_separator": field_sep,
        "encoding_characters": fields[1],
        "sending_application": fields[2] if len(fields) > 2 else "",
        "message_type": fields[8] if len(fields) > 8 else "",
    }


def ipv6_compress_rfc5952(addr: str) -> str:
    """Networking (RFC 5952): produce the canonical compressed IPv6 text (lowercase, longest zero-run '::',
    no leading zeros). Wraps the stdlib ipaddress oracle."""
    import ipaddress
    return str(ipaddress.IPv6Address(addr))


def base32_rfc4648_decode(text: str) -> bytes:
    """Auth/2FA (RFC 4648 base32, e.g. TOTP secrets): decode, tolerating missing '=' padding."""
    import base64
    text = text.upper()
    pad = (-len(text)) % 8
    return base64.b32decode(text + "=" * pad)


def crc32_ieee(data: bytes) -> int:
    """Checksums (IEEE 802.3 CRC-32, zip/png/ethernet): unsigned 32-bit CRC of the bytes."""
    import zlib
    return zlib.crc32(data) & 0xFFFFFFFF


def semver_precedence_compare(v1: str, v2: str) -> int:
    """SemVer 2.0.0 precedence: compare major.minor.patch numerically, then pre-release (a version WITH a
    pre-release has LOWER precedence than the same without; numeric identifiers compare numerically and rank
    below alphanumeric; build metadata is ignored). Returns -1, 0, or 1."""
    def _parse(v: str):
        v = v.lstrip("v")
        core, _, rest = v.partition("-")
        core = core.split("+")[0]
        pre = rest.partition("+")[0]
        major, minor, patch = (int(x) for x in core.split("."))
        return (major, minor, patch), pre

    def _cmp_pre(p1: str, p2: str) -> int:
        if p1 == p2:
            return 0
        if p1 == "":
            return 1
        if p2 == "":
            return -1
        ids1, ids2 = p1.split("."), p2.split(".")
        for a, b in zip(ids1, ids2):
            an, bn = a.isdigit(), b.isdigit()
            if an and bn:
                c = (int(a) > int(b)) - (int(a) < int(b))
            elif an and not bn:
                c = -1
            elif bn and not an:
                c = 1
            else:
                c = (a > b) - (a < b)
            if c != 0:
                return c
        return (len(ids1) > len(ids2)) - (len(ids1) < len(ids2))

    core1, pre1 = _parse(v1)
    core2, pre2 = _parse(v2)
    if core1 != core2:
        return (core1 > core2) - (core1 < core2)
    return _cmp_pre(pre1, pre2)


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════
# Primitive table: (fn, platform, technology, input_edge, output_edge, fixtures[(args, expected)]).
# Fixtures are the ORACLE — the self-test runs every one.
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════
_PRIMITIVES: list[dict[str, Any]] = [
    {"fn": ebcdic_cp037_decode, "platform": "ibm_mainframe_zos", "technology": "ebcdic_cp037",
     "input_edge": "EbcdicCp037Bytes", "output_edge": "UnicodeText",
     "fixtures": [((b"\xc8\x89",), "Hi"), ((b"\xc1\xc2\xc3",), "ABC"), ((b"\xf1\xf2\xf3",), "123")]},
    {"fn": cobol_comp3_decode, "platform": "ibm_mainframe_cobol", "technology": "comp3_packed_decimal",
     "input_edge": "Comp3PackedDecimalBytes", "output_edge": "SignedInteger",
     "fixtures": [((b"\x12\x3c",), 123), ((b"\x12\x3d",), -123), ((b"\x00\x0c",), 0), ((b"\x98\x7c",), 987)]},
    {"fn": protobuf_varint_decode, "platform": "protocol_buffers", "technology": "wire_varint_leb128",
     "input_edge": "ProtobufVarintBytes", "output_edge": "UnsignedInteger",
     "fixtures": [((b"\xac\x02",), 300), ((b"\x01",), 1), ((b"\x00",), 0), ((b"\x80\x80\x01",), 16384)]},
    {"fn": protobuf_zigzag_decode, "platform": "protocol_buffers", "technology": "zigzag_sint",
     "input_edge": "ZigZagEncodedUnsigned", "output_edge": "SignedInteger",
     "fixtures": [((0,), 0), ((1,), -1), ((2,), 1), ((3,), -2), ((4294967294,), 2147483647)]},
    {"fn": fix_message_parse, "platform": "fix_protocol_trading", "technology": "fix_4_2_soh_delimited",
     "input_edge": "FixSohDelimitedMessage", "output_edge": "FixTagValueMap",
     "fixtures": [(("8=FIX.4.2\x0135=A\x0149=SENDER\x01",), {"8": "FIX.4.2", "35": "A", "49": "SENDER"}),
                  (("35=D\x0155=AAPL\x0154=1\x01",), {"35": "D", "55": "AAPL", "54": "1"})]},
    {"fn": asn1_der_length_decode, "platform": "x509_tls_crypto", "technology": "asn1_der_length",
     "input_edge": "Asn1DerLengthOctets", "output_edge": "LengthAndConsumed",
     "fixtures": [((b"\x2a",), [42, 1]), ((b"\x81\x80",), [128, 2]), ((b"\x82\x01\x00",), [256, 3]),
                  ((b"\x7f",), [127, 1])]},
    {"fn": dicom_tag_parse, "platform": "dicom_medical_imaging", "technology": "dicom_explicit_vr_le_tag",
     "input_edge": "DicomTagBytesLE", "output_edge": "GroupElementPair",
     "fixtures": [((b"\x08\x00\x60\x00",), [8, 96]), ((b"\x10\x00\x10\x00",), [16, 16]),
                  ((b"\xe0\x7f\x10\x00",), [32736, 16])]},
    {"fn": hl7_v2_msh_parse, "platform": "hl7_v2_healthcare", "technology": "hl7_v2_msh_segment",
     "input_edge": "Hl7V2MshSegment", "output_edge": "MshHeaderFields",
     "fixtures": [(("MSH|^~\\&|SendApp|SendFac|RecvApp|RecvFac|20260708||ADT^A01|MSG1|P|2.5",),
                   {"field_separator": "|", "encoding_characters": "^~\\&",
                    "sending_application": "SendApp", "message_type": "ADT^A01"})]},
    {"fn": ipv6_compress_rfc5952, "platform": "ipv6_networking", "technology": "rfc5952_canonical",
     "input_edge": "ExpandedIPv6Text", "output_edge": "CanonicalIPv6Text",
     "fixtures": [(("2001:0db8:0000:0000:0000:0000:0000:0001",), "2001:db8::1"),
                  (("fe80:0000:0000:0000:0000:0000:0000:0001",), "fe80::1"),
                  (("0000:0000:0000:0000:0000:0000:0000:0000",), "::")]},
    {"fn": base32_rfc4648_decode, "platform": "auth_2fa_totp", "technology": "rfc4648_base32",
     "input_edge": "Base32Text", "output_edge": "DecodedBytes",
     "fixtures": [(("JBUQ",), b"Hi"), (("JBSWY3DP",), b"Hello"), (("MFRGG",), b"abc")]},
    {"fn": crc32_ieee, "platform": "checksums_ethernet_zip", "technology": "ieee_crc32",
     "input_edge": "PayloadBytes", "output_edge": "Crc32Unsigned",
     "fixtures": [((b"123456789",), 3421780262), ((b"",), 0), ((b"The quick brown fox jumps over the lazy dog",),
                                                              1095738169)]},
    {"fn": semver_precedence_compare, "platform": "semver_versioning", "technology": "semver_2_precedence",
     "input_edge": "SemVerPair", "output_edge": "PrecedenceSign",
     "fixtures": [(("1.0.0", "2.0.0"), -1), (("1.0.0-alpha", "1.0.0"), -1),
                  (("1.0.0-alpha", "1.0.0-alpha.1"), -1), (("1.0.0-alpha.1", "1.0.0-alpha.beta"), -1),
                  (("1.0.0-beta", "1.0.0-beta"), 0), (("1.0.0+build.9", "1.0.0"), 0),
                  (("2.1.0", "2.0.9"), 1), (("1.0.0-rc.1", "1.0.0"), -1)]},
]


def _blocking_keys(spec: dict[str, Any]) -> list[str]:
    fn = spec["fn"]
    return sorted({t.lower() for t in (
        "esoteric", "platform specific", "deterministic primitive", spec["platform"], spec["technology"],
        fn.__name__, spec["input_edge"].lower(), spec["output_edge"].lower(),
    ) if t})


def build_cards() -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    for spec in _PRIMITIVES:
        fn: Callable = spec["fn"]
        name = fn.__name__
        body = inspect.getsource(fn)  # single source: the stored executor IS the tested function
        route_sig = f"{spec['input_edge']} -> {spec['output_edge']}"
        cid = canonical_id(ESO_ID_PREFIX, name, spec["platform"], spec["technology"])
        cards.append({
            "record_type": ESO_RECORD_TYPE,
            "kind": "esoteric_platform_deterministic_primitive",
            "card_id": cid,
            "primitive_id": cid,
            "title": f"{name} — {spec['platform']} / {spec['technology']} (esoteric, deterministic)",
            "blackbox": (inspect.getdoc(fn) or "").replace("\n", " ").strip(),
            "blocking_keys": _blocking_keys(spec),
            "domains": ["esoteric_platform_primitive", spec["platform"], spec["technology"],
                        "negative_space", "deterministic"],
            "candidate": True,
            "serves_truth": False,
            "platform": spec["platform"],
            "technology": spec["technology"],
            "visible_edge": route_sig,
            "edge_contract": {
                "candidate": True,
                "input_edge": spec["input_edge"],
                "output_edge": spec["output_edge"],
                "input_contract": {"Edge": spec["input_edge"]},
                "output_contract": {"Edge": spec["output_edge"]},
            },
            "composition_hints": {
                "candidate_only": True, "serves_truth": False,
                "consumes_edge": spec["input_edge"], "produces_edge": spec["output_edge"],
                "route_signature": route_sig,
                "proofs_to_run_before_linking": ["candidate_boundary_gate", "oracle_fixture_check",
                                                 "security_gate"],
            },
            "executor": {
                "language": "python",
                "entry": name,
                "python_body": body,
                "determinism": "pure_deterministic",
                "oracle_fixtures": [{"input": repr(args), "expected": repr(exp)}
                                    for args, exp in spec["fixtures"]],
                "n_fixtures": len(spec["fixtures"]),
            },
            "lift_reason": "MODEL_INDEPENDENT_STRUCTURAL: obscure platform-bound bit/byte/format semantics base "
                           "models mis-handle; a deterministic primitive is exact and never decays with model size.",
            "packaged_at": PACKAGED_AT,
        })
    return cards


def _pack_dir() -> Path:
    return resource(PACK_DIR_REL)


def emit() -> dict[str, Any]:
    cards = build_cards()
    out_dir = _pack_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    pack_path = out_dir / PACK_FILENAME
    with pack_path.open("w", encoding="utf-8") as fh:
        for c in cards:
            fh.write(json.dumps(c, sort_keys=True) + "\n")
    manifest = {
        "record_type": "esoteric_platform_primitive_manifest",
        "pack_file": PACK_FILENAME,
        "n_cards": len(cards),
        "n_fixtures_total": sum(len(s["fixtures"]) for s in _PRIMITIVES),
        "platforms": sorted({s["platform"] for s in _PRIMITIVES}),
        "primitives": [s["fn"].__name__ for s in _PRIMITIVES],
        "packaged_at": PACKAGED_AT,
        "candidate": True, "serves_truth": False,
    }
    (out_dir / MANIFEST_FILENAME).write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return {"pack_path": str(pack_path), "n_cards": len(cards),
            "n_fixtures": manifest["n_fixtures_total"], "platforms": manifest["platforms"]}


def self_test() -> bool:
    """ORACLE-gated: every fixture must reproduce; a broken impl or lost boundary bit goes RED."""
    assert len(_PRIMITIVES) >= 12, "expected >=12 esoteric primitives"
    total = 0
    for spec in _PRIMITIVES:
        fn = spec["fn"]
        assert spec["fixtures"], f"{fn.__name__} has no oracle fixtures"
        for args, expected in spec["fixtures"]:
            got = fn(*args)
            assert got == expected, f"{fn.__name__}{args!r}: got {got!r}, expected {expected!r}"
            total += 1

    # cards: boundary + typed edges + stored body reproduces the fn.
    cards = build_cards()
    assert len(cards) == len(_PRIMITIVES)
    ids = [c["card_id"] for c in cards]
    assert len(set(ids)) == len(ids), "duplicate card ids"
    for c in cards:
        assert c["candidate"] is True and c["serves_truth"] is False
        assert c["edge_contract"]["input_edge"] and c["edge_contract"]["output_edge"]
        assert c["executor"]["python_body"].lstrip().startswith("def "), "executor body not a def"

    # determinism of the id mint.
    assert build_cards()[0]["card_id"] == cards[0]["card_id"]

    print(f"OK esoteric_platform_primitive_pack self-test: {len(_PRIMITIVES)} platform-specific primitives, "
          f"{total} oracle fixtures all pass, {len(set(s['platform'] for s in _PRIMITIVES))} platforms, "
          f"serves_truth=false")
    return True


def main() -> None:
    ap = argparse.ArgumentParser(description="Esoteric, platform-specific deterministic primitive pack.")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--emit", action="store_true")
    ap.add_argument("--show", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return
    if args.emit:
        print(json.dumps(emit(), indent=2))
        return
    if args.show:
        print(json.dumps(build_cards(), indent=2, sort_keys=True))
        return
    self_test()


if __name__ == "__main__":
    main()
