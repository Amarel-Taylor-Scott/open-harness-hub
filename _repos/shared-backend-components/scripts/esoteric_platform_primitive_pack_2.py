#!/usr/bin/env python3
"""scripts.esoteric_platform_primitive_pack_2 — MORE real, oracle-tested, platform/technology-specific
deterministic primitives (candidate-only). Batch 2 of the negative-space vein (see
esoteric_platform_primitive_pack.py for batch 1).

Owner 2026-07-08: "continue to create primitives" (weighting/RL/feedback come later; do not gate generation
now). These are the highest-quality kind: check-digit validators, codecs, and format decoders that base models
routinely get wrong, each with a WORKING reference implementation whose executor body IS inspect.getsource(fn)
(single source, no drift), proven by ORACLE fixtures the self-test runs. Immediately usable/certifiable with no
LLM dependency. candidate=true / serves_truth=false throughout.

Domains: banking (IBAN/ABA), payments (Luhn), retail (GS1/EAN), crypto (base58), JWT (base64url), networking
(IPv4/CIDR), numerals (Roman), temporal (ISO-8601 duration), JSON (RFC 6901 pointer), web (hex color),
automotive (VIN), healthcare-admin (NPI — NOT insurance), telecom (IMEI), publishing (ISBN-13).

    python3 scripts/esoteric_platform_primitive_pack_2.py --self-test
    python3 scripts/esoteric_platform_primitive_pack_2.py --emit
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
import inspect  # noqa: E402
import json  # noqa: E402
from typing import Any, Callable  # noqa: E402

try:
    from src.teleon.experiments.ids import canonical_id  # noqa: E402
except Exception as exc:  # noqa: BLE001
    raise SystemExit(f"esoteric_platform_primitive_pack_2 requires canonical_id; import failed: {exc}")

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
ESO2_ID_PREFIX = "prim-eso2"
ESO2_RECORD_TYPE = "esoteric_platform_primitive_candidate"
PACK_FILENAME = "esoteric_platform_primitive_cards_2.jsonl"
MANIFEST_FILENAME = "esoteric_platform_primitive_manifest_2.json"
PACK_DIR_REL = "data/dev-intel/primitive_factory/specialized_packs"
PACKAGED_AT = "2026-07-08T00:00:00Z"


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════
# Reference implementations — each a self-contained, pure, module-level function (inspect.getsource -> executor).
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════

def iban_mod97_validate(iban: str) -> bool:
    """Banking (ISO 13616 IBAN): validate via the mod-97 checksum (move first 4 chars to end, A=10..Z=35,
    interpret as an integer, must be congruent to 1 mod 97)."""
    s = iban.replace(" ", "").upper()
    rearranged = s[4:] + s[:4]
    digits = "".join(str(int(c, 36)) if c.isalpha() else c for c in rearranged)
    return digits.isdigit() and int(digits) % 97 == 1


def isbn13_check_valid(digits: str) -> bool:
    """Publishing (ISBN-13 / EAN-13): valid iff sum(d_i * (1 if i even else 3)) is divisible by 10."""
    if len(digits) != 13 or not digits.isdigit():
        return False
    return sum(int(c) * (1 if i % 2 == 0 else 3) for i, c in enumerate(digits)) % 10 == 0


def aba_routing_valid(routing: str) -> bool:
    """US banking (ABA routing transit number): 9 digits, weighted 3-7-1, sum divisible by 10."""
    if len(routing) != 9 or not routing.isdigit():
        return False
    d = [int(c) for c in routing]
    return (3 * (d[0] + d[3] + d[6]) + 7 * (d[1] + d[4] + d[7]) + (d[2] + d[5] + d[8])) % 10 == 0


def ean13_check_digit(first12: str) -> int:
    """Retail (GS1 EAN-13 barcode): compute the 13th check digit from the first 12 digits."""
    d = [int(c) for c in first12]
    s = sum(x * (1 if i % 2 == 0 else 3) for i, x in enumerate(d))
    return (10 - (s % 10)) % 10


def luhn_generate_check_digit(number: str) -> int:
    """Payments (Luhn / ISO 7812): compute the check digit to append to a number (cards, IMEI, etc.)."""
    total = 0
    for i, c in enumerate(reversed(number)):
        d = int(c)
        if i % 2 == 0:  # the appended check digit will sit at position 0, so double positions 0,2,... here
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return (10 - (total % 10)) % 10


def base58_decode(text: str) -> bytes:
    """Crypto (Bitcoin base58): decode; leading '1's map to leading zero bytes."""
    alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    num = 0
    for c in text:
        num = num * 58 + alphabet.index(c)
    n_zeros = len(text) - len(text.lstrip("1"))
    body = num.to_bytes((num.bit_length() + 7) // 8, "big") if num else b""
    return b"\x00" * n_zeros + body


def base64url_decode(text: str) -> bytes:
    """JWT / URL-safe (RFC 4648 base64url): decode, tolerating stripped '=' padding."""
    import base64
    pad = (-len(text)) % 4
    return base64.urlsafe_b64decode(text + "=" * pad)


def ipv4_to_int(addr: str) -> int:
    """Networking: pack a dotted-quad IPv4 address into a 32-bit unsigned integer."""
    p = [int(x) for x in addr.split(".")]
    return (p[0] << 24) | (p[1] << 16) | (p[2] << 8) | p[3]


def cidr_contains(cidr: str, ip: str) -> bool:
    """Networking (CIDR): does the network contain the address?"""
    import ipaddress
    return ipaddress.ip_address(ip) in ipaddress.ip_network(cidr, strict=False)


def roman_to_int(roman: str) -> int:
    """Numerals (Roman): decode, handling subtractive pairs (IV, IX, ...)."""
    vals = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
    total = 0
    prev = 0
    for c in reversed(roman):
        v = vals[c]
        total += -v if v < prev else v
        prev = v
    return total


def iso8601_duration_seconds(duration: str) -> int:
    """Temporal (ISO 8601 duration): PnDTnHnMnS -> total seconds (day/hour/minute/second components)."""
    import re
    m = re.fullmatch(r"P(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?", duration)
    if not m:
        raise ValueError("bad ISO 8601 duration")
    d, h, mi, s = (int(x) if x else 0 for x in m.groups())
    return d * 86400 + h * 3600 + mi * 60 + s


def json_pointer_resolve(doc: object, pointer: str) -> object:
    """JSON (RFC 6901 pointer): resolve /a/b/0 against a JSON document; ~1 -> '/', ~0 -> '~'."""
    if pointer == "":
        return doc
    for tok in pointer.split("/")[1:]:
        tok = tok.replace("~1", "/").replace("~0", "~")
        doc = doc[int(tok)] if isinstance(doc, list) else doc[tok]
    return doc


def hex_color_to_rgb(hex_color: str) -> list:
    """Web (CSS hex color): #RGB or #RRGGBB -> [r, g, b] ints."""
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return [int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)]


def vin_check_digit(vin: str) -> str:
    """Automotive (NHTSA VIN, 17 chars): compute the 9th-position check digit (letters transliterated, position
    weights, mod 11; 10 -> 'X')."""
    trans = {**{str(i): i for i in range(10)},
             "A": 1, "B": 2, "C": 3, "D": 4, "E": 5, "F": 6, "G": 7, "H": 8, "J": 1, "K": 2, "L": 3, "M": 4,
             "N": 5, "P": 7, "R": 9, "S": 2, "T": 3, "U": 4, "V": 5, "W": 6, "X": 7, "Y": 8, "Z": 9}
    weights = [8, 7, 6, 5, 4, 3, 2, 10, 0, 9, 8, 7, 6, 5, 4, 3, 2]
    total = sum(trans[c] * w for c, w in zip(vin, weights))
    r = total % 11
    return "X" if r == 10 else str(r)


def npi_valid(npi: str) -> bool:
    """Healthcare-admin (NPI, NOT insurance): 10-digit National Provider Identifier is Luhn-valid over the
    '80840'-prefixed string."""
    if len(npi) != 10 or not npi.isdigit():
        return False
    num = "80840" + npi
    total = 0
    for i, c in enumerate(reversed(num)):
        d = int(c)
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def imei_luhn_valid(imei: str) -> bool:
    """Telecom (IMEI): 15-digit mobile equipment identity, Luhn-valid."""
    if len(imei) != 15 or not imei.isdigit():
        return False
    total = 0
    for i, c in enumerate(reversed(imei)):
        d = int(c)
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════
# Primitive table: (fn, platform, technology, input_edge, output_edge, fixtures[(args, expected)]).
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════
_PRIMITIVES: list[dict[str, Any]] = [
    {"fn": iban_mod97_validate, "platform": "banking_iban", "technology": "iso13616_mod97",
     "input_edge": "IbanString", "output_edge": "IsValid",
     "fixtures": [(("GB82WEST12345698765432",), True), (("GB82WEST12345698765431",), False),
                  (("DE89370400440532013000",), True)]},
    {"fn": isbn13_check_valid, "platform": "publishing_isbn", "technology": "isbn13_ean13_checksum",
     "input_edge": "Isbn13Digits", "output_edge": "IsValid",
     "fixtures": [(("9780306406157",), True), (("9780306406158",), False), (("9783161484100",), True)]},
    {"fn": aba_routing_valid, "platform": "us_banking_aba", "technology": "aba_routing_checksum",
     "input_edge": "AbaRoutingNumber", "output_edge": "IsValid",
     "fixtures": [(("021000021",), True), (("021000022",), False), (("011401533",), True)]},
    {"fn": ean13_check_digit, "platform": "retail_gs1_barcode", "technology": "ean13_check_digit",
     "input_edge": "Ean13First12", "output_edge": "CheckDigit",
     "fixtures": [(("978030640615",), 7), (("400638133393",), 1), (("000000000000",), 0)]},
    {"fn": luhn_generate_check_digit, "platform": "payments_luhn", "technology": "iso7812_luhn_generate",
     "input_edge": "NumberWithoutCheck", "output_edge": "CheckDigit",
     "fixtures": [(("7992739871",), 3), (("123456789",), 7), (("0",), 0)]},
    {"fn": base58_decode, "platform": "crypto_bitcoin_base58", "technology": "base58_btc",
     "input_edge": "Base58String", "output_edge": "DecodedBytes",
     "fixtures": [(("2g",), b"a"), (("1",), b"\x00"), (("1111",), b"\x00\x00\x00\x00")]},
    {"fn": base64url_decode, "platform": "jwt_base64url", "technology": "rfc4648_base64url",
     "input_edge": "Base64UrlString", "output_edge": "DecodedBytes",
     "fixtures": [(("SGVsbG8",), b"Hello"), (("SGVsbG8gV29ybGQ",), b"Hello World"), (("YQ",), b"a")]},
    {"fn": ipv4_to_int, "platform": "networking_ipv4", "technology": "ipv4_pack",
     "input_edge": "IPv4DottedQuad", "output_edge": "UInt32",
     "fixtures": [(("192.168.1.1",), 3232235777), (("0.0.0.0",), 0), (("255.255.255.255",), 4294967295)]},
    {"fn": cidr_contains, "platform": "networking_cidr", "technology": "cidr_membership",
     "input_edge": "CidrAndAddress", "output_edge": "IsContained",
     "fixtures": [(("192.168.1.0/24", "192.168.1.55"), True), (("10.0.0.0/8", "192.168.1.1"), False),
                  (("2001:db8::/32", "2001:db8::1"), True)]},
    {"fn": roman_to_int, "platform": "numeral_roman", "technology": "roman_subtractive",
     "input_edge": "RomanNumeral", "output_edge": "Integer",
     "fixtures": [(("MCMXCIV",), 1994), (("IV",), 4), (("XLII",), 42), (("MMXXVI",), 2026)]},
    {"fn": iso8601_duration_seconds, "platform": "temporal_iso8601_duration", "technology": "iso8601_duration",
     "input_edge": "Iso8601Duration", "output_edge": "Seconds",
     "fixtures": [(("PT1H30M",), 5400), (("P1DT2H",), 93600), (("PT45S",), 45)]},
    {"fn": json_pointer_resolve, "platform": "json_rfc6901_pointer", "technology": "rfc6901",
     "input_edge": "JsonDocAndPointer", "output_edge": "ResolvedValue",
     "fixtures": [(({"a": {"b": [10, 20]}}, "/a/b/1"), 20), (({"m~n": 5}, "/m~0n"), 5),
                  (({"a/b": 7}, "/a~1b"), 7)]},
    {"fn": hex_color_to_rgb, "platform": "web_color_hex", "technology": "css_hex_color",
     "input_edge": "HexColor", "output_edge": "RgbTriple",
     "fixtures": [(("#FF8800",), [255, 136, 0]), (("#fff",), [255, 255, 255]), (("000000",), [0, 0, 0])]},
    {"fn": vin_check_digit, "platform": "automotive_vin", "technology": "nhtsa_vin_check",
     "input_edge": "VinString", "output_edge": "CheckDigit",
     "fixtures": [(("1M8GDM9AXKP042788",), "X"), (("11111111111111111",), "1")]},
    {"fn": npi_valid, "platform": "healthcare_npi", "technology": "npi_luhn_80840",
     "input_edge": "NpiString", "output_edge": "IsValid",
     "fixtures": [(("1234567893",), True), (("1234567890",), False), (("1245319599",), True)]},
    {"fn": imei_luhn_valid, "platform": "telecom_imei", "technology": "imei_luhn",
     "input_edge": "ImeiString", "output_edge": "IsValid",
     "fixtures": [(("490154203237518",), True), (("490154203237519",), False)]},
]


def build_cards() -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    for spec in _PRIMITIVES:
        fn: Callable = spec["fn"]
        name = fn.__name__
        body = inspect.getsource(fn)
        route_sig = f"{spec['input_edge']} -> {spec['output_edge']}"
        cid = canonical_id(ESO2_ID_PREFIX, name, spec["platform"], spec["technology"])
        cards.append({
            "record_type": ESO2_RECORD_TYPE, "kind": "esoteric_platform_deterministic_primitive",
            "card_id": cid, "primitive_id": cid,
            "title": f"{name} — {spec['platform']} / {spec['technology']} (esoteric, deterministic)",
            "blackbox": (inspect.getdoc(fn) or "").replace("\n", " ").strip(),
            "blocking_keys": sorted({"esoteric", "platform specific", "deterministic primitive", spec["platform"],
                                     spec["technology"], name, spec["input_edge"].lower(),
                                     spec["output_edge"].lower()}),
            "domains": ["esoteric_platform_primitive", spec["platform"], spec["technology"], "negative_space",
                        "deterministic"],
            "candidate": True, "serves_truth": False,
            "platform": spec["platform"], "technology": spec["technology"], "visible_edge": route_sig,
            "edge_contract": {"candidate": True, "input_edge": spec["input_edge"],
                              "output_edge": spec["output_edge"], "input_contract": {"Edge": spec["input_edge"]},
                              "output_contract": {"Edge": spec["output_edge"]}},
            "composition_hints": {"candidate_only": True, "serves_truth": False,
                                  "consumes_edge": spec["input_edge"], "produces_edge": spec["output_edge"],
                                  "route_signature": route_sig,
                                  "proofs_to_run_before_linking": ["candidate_boundary_gate",
                                                                   "oracle_fixture_check", "security_gate"]},
            "executor": {"language": "python", "entry": name, "python_body": body,
                         "determinism": "pure_deterministic",
                         "oracle_fixtures": [{"input": repr(args), "expected": repr(exp)}
                                             for args, exp in spec["fixtures"]],
                         "n_fixtures": len(spec["fixtures"])},
            "lift_reason": "MODEL_INDEPENDENT_STRUCTURAL: exact check-digit/codec/format semantics base models "
                           "mis-handle; a deterministic primitive is exact and never decays with model size.",
            "packaged_at": PACKAGED_AT,
        })
    return cards


def _pack_dir() -> Path:
    return resource(PACK_DIR_REL)


def emit() -> dict[str, Any]:
    cards = build_cards()
    out_dir = _pack_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    with (out_dir / PACK_FILENAME).open("w", encoding="utf-8") as fh:
        for c in cards:
            fh.write(json.dumps(c, sort_keys=True) + "\n")
    manifest = {"record_type": "esoteric_platform_primitive_manifest_2", "pack_file": PACK_FILENAME,
                "n_cards": len(cards), "n_fixtures_total": sum(len(s["fixtures"]) for s in _PRIMITIVES),
                "platforms": sorted({s["platform"] for s in _PRIMITIVES}),
                "primitives": [s["fn"].__name__ for s in _PRIMITIVES], "packaged_at": PACKAGED_AT,
                "candidate": True, "serves_truth": False}
    (out_dir / MANIFEST_FILENAME).write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return {"pack_path": str(out_dir / PACK_FILENAME), "n_cards": len(cards),
            "n_fixtures": manifest["n_fixtures_total"], "platforms": manifest["platforms"]}


def self_test() -> bool:
    """ORACLE-gated: every fixture must reproduce; a broken impl / wrong fixture / lost boundary bit goes RED."""
    assert len(_PRIMITIVES) >= 15, "expected >=15 primitives in batch 2"
    total = 0
    for spec in _PRIMITIVES:
        fn = spec["fn"]
        assert spec["fixtures"], f"{fn.__name__} has no oracle fixtures"
        for args, expected in spec["fixtures"]:
            got = fn(*args)
            assert got == expected, f"{fn.__name__}{args!r}: got {got!r}, expected {expected!r}"
            total += 1
    cards = build_cards()
    ids = [c["card_id"] for c in cards]
    assert len(set(ids)) == len(ids), "duplicate card ids"
    for c in cards:
        assert c["candidate"] is True and c["serves_truth"] is False
        assert c["executor"]["python_body"].lstrip().startswith("def "), "executor body not a def"
    assert build_cards()[0]["card_id"] == cards[0]["card_id"], "ids not deterministic"
    print(f"OK esoteric_platform_primitive_pack_2 self-test: {len(_PRIMITIVES)} platform primitives, "
          f"{total} oracle fixtures all pass, {len(set(s['platform'] for s in _PRIMITIVES))} platforms, "
          f"serves_truth=false")
    return True


def main() -> None:
    ap = argparse.ArgumentParser(description="Esoteric platform primitive pack, batch 2.")
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
