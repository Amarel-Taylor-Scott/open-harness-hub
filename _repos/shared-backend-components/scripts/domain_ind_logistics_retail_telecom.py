#!/usr/bin/env python3
"""scripts.domain_ind_logistics_retail_telecom — WORKABLE (proven + TYPED) deterministic leaf primitives for the
'ind_logistics_retail_telecom' domain (retail product identifiers, logistics shipping identifiers, and telecom
number/identity SHAPES), plus honestly-declared GATED-EFFECT candidates for the network/cloud CALLS in the same
domain.

The domain covers pure, offline, deterministic transforms + checksums over public interchange SHAPES:
  * Retail barcodes — GS1 mod-10 check digit / validate for UPC-A, EAN-13, GTIN-14; UPC-A<->EAN-13<->GTIN-14 convert
  * Book identifiers — ISBN-10 (mod-11, 'X') and ISBN-13 (GS1) check digit / validate; ISBN-10 -> ISBN-13 convert
  * Card/device checksums — generic Luhn check digit / validate; IMEI (15-digit Luhn) check digit / validate / parse
  * Logistics tracking — UPS 1Z-shape weighted mod-10 and FedEx-shape mod-11 tracking check digit / validate
  * Telecom numbers — E.164 phone normalize / validate / split (synthetic public numbers only)
  * Postal codes — US ZIP/ZIP+4, UK, and CA postcode SHAPE validate + normalize
  * Retail housekeeping — SKU normalize, address-component normalize (USPS suffix folding)

Repo law honored EXACTLY: serves_truth=true is set ONLY by a PASSING executed proof (imported `run_primitive_proof`
runs the mutator against a concrete fixture, checks the output, roundtrips any inverse, and re-runs for determinism —
it flips serves_truth false->true ONLY on pass; a deliberately-wrong fixture stays candidate and is NEVER persisted
as proven). A NETWORK/EFFECTFUL primitive (carrier rate quote, label buy, address-verify API, SMS gateway, HLR
lookup, ERP inventory write, GS1 GTIN registry lookup, shard file write) is NEVER run through the proof runner and
NEVER serves_truth=true — it is declared as a GATED EFFECT candidate: {candidate:true, serves_truth:false, effect,
proof_obligation, input_edge_type_id, output_edge_type_id}. The two families are counted SEPARATELY in the manifest
(proven_deterministic vs gated_effect_candidates); typed = proven rows carrying both canonical edge type_ids.

ADD-ONLY / flexible-multi-path: a NEW standalone shard file. It IMPORTS the shared machinery
(`scripts.mutator_registry.run_primitive_proof` / `MUTATOR_REGISTRY` / `_receipt`,
`scripts.build_edge_type_retrofit.canonicalize_edge`) and plugs its pure mutators in with `setdefault` (idempotent).
It edits NONE of the contract-locked/shared files (mutator_registry.py, build_edge_type_retrofit.py,
flywheel_proof_modules.py) and does NOT register into the flywheel (the caller gets a register tuple). Domain law
honored: NO insurance primitives (any form); NO clinical/healthcare-risk primitives; all identifiers are synthetic /
public SHAPES — no real PII/PAN/SSN/secrets (the Luhn/IMEI/phone/postal validators operate on SHAPE with synthetic
fixtures). Offline + deterministic: no network, no LLM, no wall-clock, no RNG; the write path uses a fixed literal
timestamp. CLI: --self-test | --write.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

# IMPORT the shared machinery — never edit it (ADD-ONLY seam).
from scripts.mutator_registry import (  # noqa: E402
    MUTATOR_REGISTRY,
    _receipt,
    run_primitive_proof,
)
from scripts.build_edge_type_retrofit import canonicalize_edge  # noqa: E402

DOMAIN = "ind_logistics_retail_telecom"
OUT_DIR = _resource("data") / "dev-intel" / "domain_primitives"
OUT_JSONL = OUT_DIR / "domain_ind_logistics_retail_telecom.jsonl"
OUT_MANIFEST = OUT_DIR / "manifest_ind_logistics_retail_telecom.json"
# Fixed literal timestamp — deterministic, no wall-clock read (repo law: no datetime.now/time.time).
FROZEN_TS = "2026-07-03T00:00:00Z"


# ── shared checksum kernels (pure) ──
def _gs1_check_digit(body: str) -> int:
    """GS1 mod-10 check digit over a digit body (UPC-A/EAN-13/GTIN-14/ISBN-13): weight 3 on rightmost, alternating."""
    s = 0
    for i, ch in enumerate(reversed(body)):
        s += int(ch) * (3 if i % 2 == 0 else 1)
    return (10 - (s % 10)) % 10


def _isbn10_check_char(body9: str) -> str:
    """ISBN-10 mod-11 check character over the 9-digit body; 10 -> 'X'."""
    s = sum(int(c) * (10 - i) for i, c in enumerate(body9))
    r = (11 - (s % 11)) % 11
    return "X" if r == 10 else str(r)


def _luhn_check_digit(body: str) -> int:
    """Luhn mod-10 check digit over a digit body (doubling every 2nd digit from the right)."""
    s = 0
    for i, ch in enumerate(reversed(body)):
        d = int(ch)
        if i % 2 == 0:
            d *= 2
            if d > 9:
                d -= 9
        s += d
    return (10 - (s % 10)) % 10


def _ups_check_digit(payload15: str) -> int:
    """UPS 1Z-shape weighted mod-10 over the 15-char payload (letters folded A=2..Z=7); even 1-indexed positions x2."""
    def _val(c: str) -> int:
        return int(c) if c.isdigit() else (ord(c.upper()) - 65 + 2) % 10
    odd = sum(_val(c) for i, c in enumerate(payload15) if (i + 1) % 2 == 1)
    even = sum(_val(c) for i, c in enumerate(payload15) if (i + 1) % 2 == 0)
    total = odd + even * 2
    c = total % 10
    return 0 if c == 0 else 10 - c


def _fedex_check_digit(d11: str) -> int:
    """FedEx-shape mod-11 tracking check digit over the 11 data digits (weights 1,3,7 cycling from the right)."""
    weights = [1, 3, 7]
    s = sum(int(ch) * weights[i % 3] for i, ch in enumerate(reversed(d11)))
    return (s % 11) % 10


# ── PURE deterministic mutators: signature (payload, **kwargs) -> (output, receipt_dict). No I/O. ──

# Retail barcodes (GS1) --------------------------------------------------------------------------------
def _upca_check_digit(body: str, **_kw: Any) -> tuple[int, dict[str, Any]]:
    out = _gs1_check_digit(body)
    return out, _receipt("upca_check_digit", before=body, after=out, lossless=False, note="GS1 mod-10 check digit for an 11-digit UPC-A body")


def _upca_validate(code: str, **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    valid = len(code) == 12 and code.isdigit() and _gs1_check_digit(code[:11]) == int(code[11])
    out = {"valid": valid}
    return out, _receipt("upca_validate", before=code, after=out, lossless=True, note="validate a 12-digit UPC-A via GS1 check digit")


def _ean13_check_digit(body: str, **_kw: Any) -> tuple[int, dict[str, Any]]:
    out = _gs1_check_digit(body)
    return out, _receipt("ean13_check_digit", before=body, after=out, lossless=False, note="GS1 mod-10 check digit for a 12-digit EAN-13 body")


def _ean13_validate(code: str, **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    valid = len(code) == 13 and code.isdigit() and _gs1_check_digit(code[:12]) == int(code[12])
    out = {"valid": valid}
    return out, _receipt("ean13_validate", before=code, after=out, lossless=True, note="validate a 13-digit EAN-13 via GS1 check digit")


def _gtin14_check_digit(body: str, **_kw: Any) -> tuple[int, dict[str, Any]]:
    out = _gs1_check_digit(body)
    return out, _receipt("gtin14_check_digit", before=body, after=out, lossless=False, note="GS1 mod-10 check digit for a 13-digit GTIN-14 body")


def _gtin14_validate(code: str, **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    valid = len(code) == 14 and code.isdigit() and _gs1_check_digit(code[:13]) == int(code[13])
    out = {"valid": valid}
    return out, _receipt("gtin14_validate", before=code, after=out, lossless=True, note="validate a 14-digit GTIN-14 via GS1 check digit")


def _upca_to_ean13(code: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = "0" + code
    return out, _receipt("upca_to_ean13", before=code, after=out, lossless=True, note="UPC-A -> EAN-13 (zero-prefix); ean13_to_upca restores")


def _ean13_to_upca(code: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = code[1:]
    return out, _receipt("ean13_to_upca", before=code, after=out, lossless=True, note="EAN-13 (0-prefixed) -> UPC-A (strip leading 0)")


def _ean13_to_gtin14(code: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = "0" + code
    return out, _receipt("ean13_to_gtin14", before=code, after=out, lossless=True, note="EAN-13 -> GTIN-14 (zero-pad); gtin14_to_ean13 restores")


def _gtin14_to_ean13(code: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = code[1:]
    return out, _receipt("gtin14_to_ean13", before=code, after=out, lossless=True, note="GTIN-14 (0-prefixed) -> EAN-13 (strip leading 0)")


# Book identifiers (ISBN) ------------------------------------------------------------------------------
def _isbn10_check_digit(body9: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = _isbn10_check_char(body9)
    return out, _receipt("isbn10_check_digit", before=body9, after=out, lossless=False, note="ISBN-10 mod-11 check char (0-9 or X) for a 9-digit body")


def _isbn10_validate(code: str, **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    valid = (
        len(code) == 10 and code[:9].isdigit()
        and (code[9].isdigit() or code[9].upper() == "X")
        and _isbn10_check_char(code[:9]) == code[9].upper()
    )
    out = {"valid": valid}
    return out, _receipt("isbn10_validate", before=code, after=out, lossless=True, note="validate a 10-char ISBN-10 (mod-11, trailing X allowed)")


def _isbn13_check_digit(body12: str, **_kw: Any) -> tuple[int, dict[str, Any]]:
    out = _gs1_check_digit(body12)
    return out, _receipt("isbn13_check_digit", before=body12, after=out, lossless=False, note="ISBN-13 (GS1 mod-10) check digit for a 12-digit body")


def _isbn13_validate(code: str, **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    valid = len(code) == 13 and code.isdigit() and _gs1_check_digit(code[:12]) == int(code[12])
    out = {"valid": valid}
    return out, _receipt("isbn13_validate", before=code, after=out, lossless=True, note="validate a 13-digit ISBN-13 via GS1 check digit")


def _isbn10_to_isbn13(code: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    body = "978" + code[:9]
    out = body + str(_gs1_check_digit(body))
    return out, _receipt("isbn10_to_isbn13", before=code, after=out, lossless=False, note="ISBN-10 -> ISBN-13 (prefix 978, recompute check)")


# Card/device checksums (Luhn / IMEI) ------------------------------------------------------------------
def _luhn_check_digit_m(body: str, **_kw: Any) -> tuple[int, dict[str, Any]]:
    out = _luhn_check_digit(body)
    return out, _receipt("luhn_check_digit", before=body, after=out, lossless=False, note="generic Luhn mod-10 check digit for a digit body")


def _luhn_validate(number: str, **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    valid = number.isdigit() and len(number) >= 2 and _luhn_check_digit(number[:-1]) == int(number[-1])
    out = {"valid": valid}
    return out, _receipt("luhn_validate", before=number, after=out, lossless=True, note="validate a Luhn-checksummed digit string (synthetic shape)")


def _imei_check_digit(body14: str, **_kw: Any) -> tuple[int, dict[str, Any]]:
    out = _luhn_check_digit(body14)
    return out, _receipt("imei_check_digit", before=body14, after=out, lossless=False, note="IMEI 15th (Luhn) check digit from a 14-digit body")


def _imei_validate(imei: str, **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    valid = len(imei) == 15 and imei.isdigit() and _luhn_check_digit(imei[:14]) == int(imei[14])
    out = {"valid": valid}
    return out, _receipt("imei_validate", before=imei, after=out, lossless=True, note="validate a 15-digit IMEI via Luhn (synthetic shape)")


def _imei_parse(imei: str, **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    out = {"tac": imei[:8], "serial": imei[8:14], "check": imei[14]}
    return out, _receipt("imei_parse", before=imei, after=out, lossless=True, note="split a 15-digit IMEI into TAC(8)/serial(6)/check(1)")


# Telecom numbers (E.164) ------------------------------------------------------------------------------
def _e164_normalize(arg: dict[str, Any], **_kw: Any) -> tuple[str, dict[str, Any]]:
    raw, cc = arg["raw"], str(arg["country_code"])
    digits = re.sub(r"\D", "", raw)
    national = digits[len(cc):] if digits.startswith(cc) else digits
    out = "+" + cc + national
    return out, _receipt("e164_normalize", before=arg, after=out, lossless=False, note="raw phone + country code -> E.164 '+<cc><national>'")


def _e164_validate(number: str, **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    valid = bool(re.fullmatch(r"\+[1-9]\d{6,14}", number))
    out = {"valid": valid}
    return out, _receipt("e164_validate", before=number, after=out, lossless=True, note="validate E.164 SHAPE (^\\+[1-9]\\d{6,14}$)")


def _e164_parse(arg: dict[str, Any], **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    e164, cc = arg["e164"], str(arg["country_code"])
    body = e164[1:] if e164.startswith("+") else e164
    if not body.startswith(cc):
        raise ValueError("e164 does not start with the declared country code")
    out = {"country_code": cc, "national_number": body[len(cc):]}
    return out, _receipt("e164_parse", before=arg, after=out, lossless=True, note="split E.164 into {country_code, national_number} given the cc")


# Postal codes -----------------------------------------------------------------------------------------
def _postal_us_validate(code: str, **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    valid = bool(re.fullmatch(r"\d{5}(-\d{4})?", code))
    out = {"valid": valid}
    return out, _receipt("postal_us_validate", before=code, after=out, lossless=True, note="validate US ZIP or ZIP+4 SHAPE")


def _postal_us_normalize(code: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    digits = re.sub(r"\D", "", code)
    out = f"{digits[:5]}-{digits[5:9]}" if len(digits) == 9 else digits[:5]
    return out, _receipt("postal_us_normalize", before=code, after=out, lossless=False, note="normalize US ZIP: 9 digits -> ZIP+4 dashed, else ZIP5")


def _postal_uk_validate(code: str, **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    valid = bool(re.fullmatch(r"[A-Z]{1,2}\d[A-Z\d]? \d[A-Z]{2}", code.upper()))
    out = {"valid": valid}
    return out, _receipt("postal_uk_validate", before=code, after=out, lossless=True, note="validate UK postcode SHAPE (uppercased)")


def _postal_uk_normalize(code: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    compact = re.sub(r"\s+", "", code).upper()
    out = compact[:-3] + " " + compact[-3:]
    return out, _receipt("postal_uk_normalize", before=code, after=out, lossless=False, note="normalize UK postcode: uppercase + single space before inward code")


def _postal_ca_validate(code: str, **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    valid = bool(re.fullmatch(r"[A-Z]\d[A-Z] \d[A-Z]\d", code.upper()))
    out = {"valid": valid}
    return out, _receipt("postal_ca_validate", before=code, after=out, lossless=True, note="validate CA postal-code SHAPE (A1A 1A1)")


def _postal_ca_normalize(code: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    compact = re.sub(r"\s+", "", code).upper()
    out = compact[:3] + " " + compact[3:]
    return out, _receipt("postal_ca_normalize", before=code, after=out, lossless=False, note="normalize CA postal code: uppercase + 'A1A 1A1' spacing")


# Retail housekeeping ----------------------------------------------------------------------------------
def _sku_normalize(sku: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    up = re.sub(r"[\s_]+", "-", sku.strip().upper())
    up = re.sub(r"-{2,}", "-", up).strip("-")
    return up, _receipt("sku_normalize", before=sku, after=up, lossless=False, note="uppercase, collapse space/underscore to single '-', trim separators")


_STREET_SUFFIX = {
    "STREET": "ST", "AVENUE": "AVE", "ROAD": "RD", "BOULEVARD": "BLVD",
    "DRIVE": "DR", "LANE": "LN", "COURT": "CT", "PLACE": "PL", "HIGHWAY": "HWY",
}


def _address_component_normalize(addr: dict[str, Any], **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    street = str(addr.get("street", "")).upper().strip()
    tokens = street.split()
    if tokens and tokens[-1] in _STREET_SUFFIX:
        tokens[-1] = _STREET_SUFFIX[tokens[-1]]
    out = {
        "street": " ".join(tokens),
        "city": str(addr.get("city", "")).upper().strip(),
        "state": str(addr.get("state", "")).upper().strip(),
        "zip": str(addr.get("zip", "")).strip(),
    }
    return out, _receipt("address_component_normalize", before=addr, after=out, lossless=False, note="uppercase + USPS street-suffix folding for an address component dict")


# Logistics tracking -----------------------------------------------------------------------------------
def _ups_tracking_check_digit(payload: str, **_kw: Any) -> tuple[int, dict[str, Any]]:
    """payload = the tracking number WITHOUT the final check digit (leading '1Z' allowed)."""
    body = payload[2:] if payload.upper().startswith("1Z") else payload
    out = _ups_check_digit(body)
    return out, _receipt("ups_tracking_check_digit", before=payload, after=out, lossless=False, note="UPS 1Z-shape weighted mod-10 check digit over the 15-char payload")


def _ups_tracking_validate(tracking: str, **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    valid = False
    if len(tracking) == 18 and tracking.upper().startswith("1Z"):
        body = tracking[2:17]
        try:
            valid = _ups_check_digit(body) == int(tracking[17])
        except ValueError:
            valid = False
    out = {"valid": valid}
    return out, _receipt("ups_tracking_validate", before=tracking, after=out, lossless=True, note="validate an 18-char UPS 1Z-shape tracking number")


def _fedex_tracking_check_digit(d11: str, **_kw: Any) -> tuple[int, dict[str, Any]]:
    out = _fedex_check_digit(d11)
    return out, _receipt("fedex_tracking_check_digit", before=d11, after=out, lossless=False, note="FedEx-shape mod-11 tracking check digit over 11 data digits")


def _fedex_tracking_validate(tracking: str, **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    valid = len(tracking) == 12 and tracking.isdigit() and _fedex_check_digit(tracking[:11]) == int(tracking[11])
    out = {"valid": valid}
    return out, _receipt("fedex_tracking_validate", before=tracking, after=out, lossless=True, note="validate a 12-digit FedEx-shape tracking number")


#: new pure mutators to plug into the shared registry (idempotent registration; never overwrites)
_NEW_MUTATORS = {
    "upca_check_digit": _upca_check_digit, "upca_validate": _upca_validate,
    "ean13_check_digit": _ean13_check_digit, "ean13_validate": _ean13_validate,
    "gtin14_check_digit": _gtin14_check_digit, "gtin14_validate": _gtin14_validate,
    "upca_to_ean13": _upca_to_ean13, "ean13_to_upca": _ean13_to_upca,
    "ean13_to_gtin14": _ean13_to_gtin14, "gtin14_to_ean13": _gtin14_to_ean13,
    "isbn10_check_digit": _isbn10_check_digit, "isbn10_validate": _isbn10_validate,
    "isbn13_check_digit": _isbn13_check_digit, "isbn13_validate": _isbn13_validate,
    "isbn10_to_isbn13": _isbn10_to_isbn13,
    "luhn_check_digit": _luhn_check_digit_m, "luhn_validate": _luhn_validate,
    "imei_check_digit": _imei_check_digit, "imei_validate": _imei_validate, "imei_parse": _imei_parse,
    "e164_normalize": _e164_normalize, "e164_validate": _e164_validate, "e164_parse": _e164_parse,
    "postal_us_validate": _postal_us_validate, "postal_us_normalize": _postal_us_normalize,
    "postal_uk_validate": _postal_uk_validate, "postal_uk_normalize": _postal_uk_normalize,
    "postal_ca_validate": _postal_ca_validate, "postal_ca_normalize": _postal_ca_normalize,
    "sku_normalize": _sku_normalize, "address_component_normalize": _address_component_normalize,
    "ups_tracking_check_digit": _ups_tracking_check_digit, "ups_tracking_validate": _ups_tracking_validate,
    "fedex_tracking_check_digit": _fedex_tracking_check_digit, "fedex_tracking_validate": _fedex_tracking_validate,
}


def register_new_mutators() -> None:
    """Plug the logistics/retail/telecom mutators into the shared MUTATOR_REGISTRY (setdefault — idempotent)."""
    for name, fn in _NEW_MUTATORS.items():
        MUTATOR_REGISTRY.setdefault(name, fn)


register_new_mutators()


# ── the leaf primitives: each a REAL transform with a concrete SYNTHETIC fixture + expected (+ inverse where reversible) ──
# spec fields: id, capability, mutator, fixture, expected, inverse?, input_edge, output_edge
LEAF_SPECS: list[dict[str, Any]] = [
    # Retail barcodes (GS1)
    {"id": "prim:retail:upca_check_digit", "capability": "compute the GS1 mod-10 check digit for an 11-digit UPC-A body",
     "mutator": "upca_check_digit", "fixture": "03600029145", "expected": 2,
     "input_edge": "UpcaBodyDigits", "output_edge": "CheckDigit"},
    {"id": "prim:retail:upca_validate", "capability": "validate a 12-digit UPC-A barcode via its GS1 check digit",
     "mutator": "upca_validate", "fixture": "036000291452", "expected": {"valid": True},
     "input_edge": "UpcaCode", "output_edge": "ValidationResult"},
    {"id": "prim:retail:ean13_check_digit", "capability": "compute the GS1 mod-10 check digit for a 12-digit EAN-13 body",
     "mutator": "ean13_check_digit", "fixture": "400638133393", "expected": 1,
     "input_edge": "Ean13BodyDigits", "output_edge": "CheckDigit"},
    {"id": "prim:retail:ean13_validate", "capability": "validate a 13-digit EAN-13 barcode via its GS1 check digit",
     "mutator": "ean13_validate", "fixture": "4006381333931", "expected": {"valid": True},
     "input_edge": "Ean13Code", "output_edge": "ValidationResult"},
    {"id": "prim:retail:gtin14_check_digit", "capability": "compute the GS1 mod-10 check digit for a 13-digit GTIN-14 body",
     "mutator": "gtin14_check_digit", "fixture": "0400638133393", "expected": 1,
     "input_edge": "Gtin14BodyDigits", "output_edge": "CheckDigit"},
    {"id": "prim:retail:gtin14_validate", "capability": "validate a 14-digit GTIN-14 via its GS1 check digit",
     "mutator": "gtin14_validate", "fixture": "04006381333931", "expected": {"valid": True},
     "input_edge": "Gtin14Code", "output_edge": "ValidationResult"},
    {"id": "prim:retail:upca_to_ean13", "capability": "convert a UPC-A barcode into its EAN-13 form (zero-prefix)",
     "mutator": "upca_to_ean13", "fixture": "036000291452", "expected": "0036000291452",
     "inverse": "ean13_to_upca", "input_edge": "UpcaCode", "output_edge": "Ean13Code"},
    {"id": "prim:retail:ean13_to_upca", "capability": "convert a zero-prefixed EAN-13 back into its UPC-A form",
     "mutator": "ean13_to_upca", "fixture": "0036000291452", "expected": "036000291452",
     "inverse": "upca_to_ean13", "input_edge": "Ean13Code", "output_edge": "UpcaCode"},
    {"id": "prim:retail:ean13_to_gtin14", "capability": "convert an EAN-13 into its GTIN-14 form (zero-pad)",
     "mutator": "ean13_to_gtin14", "fixture": "4006381333931", "expected": "04006381333931",
     "inverse": "gtin14_to_ean13", "input_edge": "Ean13Code", "output_edge": "Gtin14Code"},
    {"id": "prim:retail:gtin14_to_ean13", "capability": "convert a zero-prefixed GTIN-14 back into its EAN-13 form",
     "mutator": "gtin14_to_ean13", "fixture": "04006381333931", "expected": "4006381333931",
     "inverse": "ean13_to_gtin14", "input_edge": "Gtin14Code", "output_edge": "Ean13Code"},
    # Book identifiers (ISBN)
    {"id": "prim:retail:isbn10_check_digit", "capability": "compute the ISBN-10 mod-11 check char for a 9-digit body",
     "mutator": "isbn10_check_digit", "fixture": "030640615", "expected": "2",
     "input_edge": "Isbn10BodyDigits", "output_edge": "Isbn10CheckChar"},
    {"id": "prim:retail:isbn10_validate", "capability": "validate a 10-char ISBN-10 (mod-11, trailing X allowed)",
     "mutator": "isbn10_validate", "fixture": "0306406152", "expected": {"valid": True},
     "input_edge": "Isbn10Code", "output_edge": "ValidationResult"},
    {"id": "prim:retail:isbn13_check_digit", "capability": "compute the ISBN-13 (GS1) check digit for a 12-digit body",
     "mutator": "isbn13_check_digit", "fixture": "978030640615", "expected": 7,
     "input_edge": "Isbn13BodyDigits", "output_edge": "CheckDigit"},
    {"id": "prim:retail:isbn13_validate", "capability": "validate a 13-digit ISBN-13 via its GS1 check digit",
     "mutator": "isbn13_validate", "fixture": "9780306406157", "expected": {"valid": True},
     "input_edge": "Isbn13Code", "output_edge": "ValidationResult"},
    {"id": "prim:retail:isbn10_to_isbn13", "capability": "convert an ISBN-10 into its ISBN-13 form (978 prefix, recompute)",
     "mutator": "isbn10_to_isbn13", "fixture": "0306406152", "expected": "9780306406157",
     "input_edge": "Isbn10Code", "output_edge": "Isbn13Code"},
    # Card/device checksums (Luhn / IMEI)
    {"id": "prim:telecom:luhn_check_digit", "capability": "compute the Luhn mod-10 check digit for a digit body",
     "mutator": "luhn_check_digit", "fixture": "7992739871", "expected": 3,
     "input_edge": "DigitBody", "output_edge": "CheckDigit"},
    {"id": "prim:telecom:luhn_validate", "capability": "validate a Luhn-checksummed digit string (synthetic shape)",
     "mutator": "luhn_validate", "fixture": "79927398713", "expected": {"valid": True},
     "input_edge": "LuhnNumber", "output_edge": "ValidationResult"},
    {"id": "prim:telecom:imei_check_digit", "capability": "compute the IMEI 15th (Luhn) check digit from a 14-digit body",
     "mutator": "imei_check_digit", "fixture": "49015420323751", "expected": 8,
     "input_edge": "ImeiBodyDigits", "output_edge": "CheckDigit"},
    {"id": "prim:telecom:imei_validate", "capability": "validate a 15-digit IMEI via Luhn (synthetic shape)",
     "mutator": "imei_validate", "fixture": "490154203237518", "expected": {"valid": True},
     "input_edge": "Imei", "output_edge": "ValidationResult"},
    {"id": "prim:telecom:imei_parse", "capability": "split a 15-digit IMEI into TAC / serial / check parts",
     "mutator": "imei_parse", "fixture": "490154203237518",
     "expected": {"tac": "49015420", "serial": "323751", "check": "8"},
     "input_edge": "Imei", "output_edge": "ImeiParts"},
    # Telecom numbers (E.164)
    {"id": "prim:telecom:e164_normalize", "capability": "normalize a raw phone + country code into E.164 form",
     "mutator": "e164_normalize", "fixture": {"raw": "(415) 555-0132", "country_code": "1"},
     "expected": "+14155550132", "input_edge": "RawPhoneAndCountryCode", "output_edge": "E164Number"},
    {"id": "prim:telecom:e164_validate", "capability": "validate an E.164 phone-number SHAPE",
     "mutator": "e164_validate", "fixture": "+14155550132", "expected": {"valid": True},
     "input_edge": "E164Number", "output_edge": "ValidationResult"},
    {"id": "prim:telecom:e164_parse", "capability": "split an E.164 number into country code + national number",
     "mutator": "e164_parse", "fixture": {"e164": "+14155550132", "country_code": "1"},
     "expected": {"country_code": "1", "national_number": "4155550132"},
     "input_edge": "E164NumberAndCountryCode", "output_edge": "PhoneParts"},
    # Postal codes
    {"id": "prim:retail:postal_us_validate", "capability": "validate a US ZIP or ZIP+4 SHAPE",
     "mutator": "postal_us_validate", "fixture": "95014-1234", "expected": {"valid": True},
     "input_edge": "UsPostalCode", "output_edge": "ValidationResult"},
    {"id": "prim:retail:postal_us_normalize", "capability": "normalize a 9-digit US postal code into ZIP+4 dashed form",
     "mutator": "postal_us_normalize", "fixture": "950141234", "expected": "95014-1234",
     "input_edge": "UsPostalCode", "output_edge": "UsPostalCode"},
    {"id": "prim:retail:postal_uk_validate", "capability": "validate a UK postcode SHAPE",
     "mutator": "postal_uk_validate", "fixture": "SW1A 1AA", "expected": {"valid": True},
     "input_edge": "UkPostalCode", "output_edge": "ValidationResult"},
    {"id": "prim:retail:postal_uk_normalize", "capability": "normalize a UK postcode (uppercase + single inward space)",
     "mutator": "postal_uk_normalize", "fixture": "sw1a1aa", "expected": "SW1A 1AA",
     "input_edge": "UkPostalCode", "output_edge": "UkPostalCode"},
    {"id": "prim:retail:postal_ca_validate", "capability": "validate a Canadian postal-code SHAPE (A1A 1A1)",
     "mutator": "postal_ca_validate", "fixture": "K1A 0B1", "expected": {"valid": True},
     "input_edge": "CaPostalCode", "output_edge": "ValidationResult"},
    {"id": "prim:retail:postal_ca_normalize", "capability": "normalize a Canadian postal code into 'A1A 1A1' form",
     "mutator": "postal_ca_normalize", "fixture": "k1a0b1", "expected": "K1A 0B1",
     "input_edge": "CaPostalCode", "output_edge": "CaPostalCode"},
    # Retail housekeeping
    {"id": "prim:retail:sku_normalize", "capability": "normalize a SKU (uppercase, collapse separators to '-')",
     "mutator": "sku_normalize", "fixture": " widget_blue  large ", "expected": "WIDGET-BLUE-LARGE",
     "input_edge": "RawSku", "output_edge": "NormalizedSku"},
    {"id": "prim:retail:address_component_normalize", "capability": "normalize an address component dict (USPS suffix folding)",
     "mutator": "address_component_normalize",
     "fixture": {"street": "123 Main Street", "city": "Springfield", "state": "il", "zip": "62704"},
     "expected": {"street": "123 MAIN ST", "city": "SPRINGFIELD", "state": "IL", "zip": "62704"},
     "input_edge": "RawAddressComponents", "output_edge": "NormalizedAddressComponents"},
    # Logistics tracking
    {"id": "prim:logistics:ups_tracking_check_digit", "capability": "compute the UPS 1Z-shape mod-10 tracking check digit",
     "mutator": "ups_tracking_check_digit", "fixture": "1Z234567890123456", "expected": 2,
     "input_edge": "UpsTrackingPayload", "output_edge": "CheckDigit"},
    {"id": "prim:logistics:ups_tracking_validate", "capability": "validate an 18-char UPS 1Z-shape tracking number",
     "mutator": "ups_tracking_validate", "fixture": "1Z2345678901234562", "expected": {"valid": True},
     "input_edge": "UpsTrackingNumber", "output_edge": "ValidationResult"},
    {"id": "prim:logistics:fedex_tracking_check_digit", "capability": "compute the FedEx-shape mod-11 tracking check digit",
     "mutator": "fedex_tracking_check_digit", "fixture": "12345678901", "expected": 2,
     "input_edge": "FedexTrackingPayload", "output_edge": "CheckDigit"},
    {"id": "prim:logistics:fedex_tracking_validate", "capability": "validate a 12-digit FedEx-shape tracking number",
     "mutator": "fedex_tracking_validate", "fixture": "123456789012", "expected": {"valid": True},
     "input_edge": "FedexTrackingNumber", "output_edge": "ValidationResult"},
]

#: deliberately-wrong leaf — the executed proof gate MUST leave it candidate (never persisted as proven)
NEGATIVE_SPECS: list[dict[str, Any]] = [
    {"id": "prim:retail:WRONG_upca_check_digit", "capability": "UPC-A check digit with a wrong expected output",
     "mutator": "upca_check_digit", "fixture": "03600029145", "expected": 9,
     "input_edge": "UpcaBodyDigits", "output_edge": "CheckDigit"},
]

# ── GATED-EFFECT candidates: network/cloud/file CALLS. NEVER run through the proof runner, NEVER serves_truth=true. ──
# Each is declared honestly as candidate with an effect + a proof_obligation (live integration test w/ credential).
GATED_EFFECT_SPECS: list[dict[str, Any]] = [
    {"id": "prim:logistics:gated:carrier_rate_quote_api", "capability": "request live shipping rate quotes from a carrier API",
     "effect": "network_read", "proof_obligation": "live integration test with credential (carrier rating API key)",
     "input_edge": "ShipmentRequest", "output_edge": "RateQuoteList"},
    {"id": "prim:logistics:gated:create_shipping_label_api", "capability": "purchase and create a shipping label via a carrier API",
     "effect": "network_write", "proof_obligation": "live integration test with credential (carrier label API key + billing account)",
     "input_edge": "ShipmentRequest", "output_edge": "ShippingLabel"},
    {"id": "prim:logistics:gated:track_shipment_status_api", "capability": "fetch live tracking status for a tracking number via a carrier API",
     "effect": "network_read", "proof_obligation": "live integration test with credential (carrier tracking API key)",
     "input_edge": "TrackingNumber", "output_edge": "TrackingStatus"},
    {"id": "prim:logistics:gated:address_verify_usps_api", "capability": "verify/standardize a postal address via a hosted address API",
     "effect": "network_read", "proof_obligation": "live integration test with credential (address-verification API key)",
     "input_edge": "PostalAddress", "output_edge": "StandardizedAddress"},
    {"id": "prim:retail:gated:gtin_registry_lookup_api", "capability": "look up product metadata for a GTIN via a hosted registry API",
     "effect": "network_read", "proof_obligation": "live integration test with credential (GS1/registry API key)",
     "input_edge": "Gtin14Code", "output_edge": "ProductRecord"},
    {"id": "prim:retail:gated:inventory_update_erp_write", "capability": "write an inventory-level update to an ERP/commerce backend",
     "effect": "network_write", "proof_obligation": "live integration test with credential (ERP service account)",
     "input_edge": "InventoryUpdate", "output_edge": "WriteAck"},
    {"id": "prim:telecom:gated:sms_send_gateway", "capability": "send an SMS message via a telecom messaging gateway",
     "effect": "network_write", "proof_obligation": "live integration test with credential (SMS gateway API key)",
     "input_edge": "SmsMessage", "output_edge": "SmsSendReceipt"},
    {"id": "prim:telecom:gated:hlr_lookup_api", "capability": "query carrier/portability (HLR) info for a phone number via a hosted API",
     "effect": "network_read", "proof_obligation": "live integration test with credential (HLR lookup API key)",
     "input_edge": "E164Number", "output_edge": "HlrRecord"},
    {"id": "prim:telecom:gated:number_portability_query_api", "capability": "query number-portability routing for a phone number via a hosted API",
     "effect": "network_read", "proof_obligation": "live integration test with credential (portability API key)",
     "input_edge": "E164Number", "output_edge": "PortabilityRecord"},
    {"id": "prim:retail:gated:write_barcode_shard_file", "capability": "write a validated-barcode shard to a local file",
     "effect": "file_write", "proof_obligation": "live integration test on a writable temp path",
     "input_edge": "BarcodeRowList", "output_edge": "FilePath"},
]


def _prove_one(spec: dict[str, Any]) -> dict[str, Any]:
    receipt = run_primitive_proof(
        spec["id"], spec["mutator"], spec["fixture"], spec["expected"], has_inverse=spec.get("inverse"),
    )
    receipt["capability"] = spec["capability"]
    receipt["input_edge"] = spec["input_edge"]
    receipt["output_edge"] = spec["output_edge"]
    return receipt


def prove_all() -> list[dict[str, Any]]:
    """Run every declared deterministic leaf primitive through the imported executed-proof runner."""
    return [_prove_one(s) for s in LEAF_SPECS]


def _typed_row(receipt: dict[str, Any]) -> dict[str, Any]:
    """A persisted PROVEN-DETERMINISTIC row: proven (serves_truth=true) AND typed (canonical edge type_ids)."""
    return {
        "record_type": "proven_deterministic_primitive",
        "primitive_id": receipt["primitive_id"],
        "mutator": receipt["mutator"],
        "domain": DOMAIN,
        "capability": receipt["capability"],
        "serves_truth": True,
        "candidate": False,
        "verification_level": "L7_executed_proof",
        "input_edge": receipt["input_edge"],
        "output_edge": receipt["output_edge"],
        "input_edge_type_id": canonicalize_edge(receipt["input_edge"]),
        "output_edge_type_id": canonicalize_edge(receipt["output_edge"]),
        "has_roundtrip_proof": any(p["name"] == "roundtrip_test" and p["passed"] for p in receipt["proofs"]),
        "output_hash": receipt["output_hash"],
    }


def proven_typed_rows() -> list[dict[str, Any]]:
    """Only leaves whose executed proof PASSED, each TYPED via canonicalize_edge. Sorted for determinism."""
    rows = [_typed_row(r) for r in prove_all() if r["serves_truth"] is True]
    rows.sort(key=lambda r: r["primitive_id"])
    return rows


def gated_effect_rows() -> list[dict[str, Any]]:
    """Network/effectful CALLS declared as candidates: serves_truth=false, carry effect + proof_obligation + types."""
    rows: list[dict[str, Any]] = []
    for spec in GATED_EFFECT_SPECS:
        rows.append({
            "record_type": "gated_effect_candidate",
            "primitive_id": spec["id"],
            "domain": DOMAIN,
            "capability": spec["capability"],
            # LAW: an effectful primitive is NEVER proven-true; it is a gated candidate.
            "candidate": True,
            "serves_truth": False,
            "effect": spec["effect"],
            "proof_obligation": spec["proof_obligation"],
            "verification_level": "L0_gated_effect_unproven",
            "input_edge": spec["input_edge"],
            "output_edge": spec["output_edge"],
            "input_edge_type_id": canonicalize_edge(spec["input_edge"]),
            "output_edge_type_id": canonicalize_edge(spec["output_edge"]),
        })
    rows.sort(key=lambda r: r["primitive_id"])
    return rows


def build_manifest(proven: list[dict[str, Any]], gated: list[dict[str, Any]]) -> dict[str, Any]:
    typed = [r for r in proven if r["input_edge_type_id"] and r["output_edge_type_id"]]
    return {
        "record_type": "domain_ind_logistics_retail_telecom_manifest",
        "pack_id": "domain-ind-logistics-retail-telecom-primitives",
        "domain": DOMAIN,
        "generator": "scripts/domain_ind_logistics_retail_telecom.py",
        "generated_utc": FROZEN_TS,
        "declared_leaf_count": len(LEAF_SPECS),
        # SEPARATE, honest counts — never conflated.
        "proven_deterministic": len(proven),
        "typed": len(typed),
        "gated_effect_candidates": len(gated),
        "roundtrip_pair_count": sum(1 for r in proven if r["has_roundtrip_proof"]),
        "verification_level_proven": "L7_executed_proof",
        "gated_effect_by_type": {
            e: sum(1 for r in gated if r["effect"] == e) for e in sorted({r["effect"] for r in gated})
        },
        "proven_primitive_ids": [r["primitive_id"] for r in proven],
        "gated_effect_primitive_ids": [r["primitive_id"] for r in gated],
        "note": "serves_truth=true rows are PROVEN-DETERMINISTIC only — set solely by an executed passing proof "
                "(run_primitive_proof from scripts/mutator_registry.py), each TYPED via canonicalize_edge "
                "(scripts/build_edge_type_retrofit.py). GATED-EFFECT rows are network/cloud/file CALLS: candidate=true, "
                "serves_truth=false, each carrying an effect + a live-integration proof_obligation; they are NEVER run "
                "through the proof runner. A deliberately-wrong deterministic fixture stays candidate and is never "
                "persisted here. Domain law: no insurance; no clinical/healthcare-risk; synthetic/public SHAPES only "
                "(no real PII/PAN/SSN/secrets — the Luhn/IMEI/phone/postal validators operate on shape).",
    }


def write_pack() -> dict[str, Any]:
    proven = proven_typed_rows()
    gated = gated_effect_rows()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    # Two SEPARATE sections of the shard: a proven-deterministic header row, then proven rows, then a gated header
    # row, then gated rows — so the two families are never conflated when the shard is streamed.
    lines: list[str] = []
    lines.append(json.dumps({"record_type": "section_marker", "section": "proven_deterministic",
                             "domain": DOMAIN, "count": len(proven)}, sort_keys=True))
    lines += [json.dumps(r, ensure_ascii=False, sort_keys=True) for r in proven]
    lines.append(json.dumps({"record_type": "section_marker", "section": "gated_effect_candidates",
                             "domain": DOMAIN, "count": len(gated)}, sort_keys=True))
    lines += [json.dumps(r, ensure_ascii=False, sort_keys=True) for r in gated]
    OUT_JSONL.write_text("\n".join(lines) + "\n", encoding="utf-8")
    manifest = build_manifest(proven, gated)
    OUT_MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def self_test() -> int:
    receipts = prove_all()
    proven = proven_typed_rows()
    gated = gated_effect_rows()
    ids = [r["primitive_id"] for r in receipts]

    # a deliberately-wrong deterministic fixture must FAIL the executed proof -> stay CANDIDATE
    wrong = run_primitive_proof(
        NEGATIVE_SPECS[0]["id"], NEGATIVE_SPECS[0]["mutator"], NEGATIVE_SPECS[0]["fixture"],
        NEGATIVE_SPECS[0]["expected"], has_inverse=NEGATIVE_SPECS[0].get("inverse"))
    # a second wrong path: an un-runnable fixture (non-digit UPC-A) -> execution error -> not promoted
    err = run_primitive_proof("prim:retail:EXEC_ERROR", "upca_validate", 12345, "irrelevant")

    inverse_specs = [s for s in LEAF_SPECS if s.get("inverse")]
    proven_ids = {r["primitive_id"] for r in proven}
    all_ids = ids + [s["id"] for s in GATED_EFFECT_SPECS]

    checks: list[tuple[str, bool]] = [
        (">=25 deterministic leaf primitives declared", len(LEAF_SPECS) >= 25),
        ("all primitive ids unique across proven + gated", len(set(all_ids)) == len(all_ids)),
        (">=25 leaves PROVE serves_truth=true via an executed proof", len(proven) >= 25),
        ("EVERY declared leaf proved (all promoted)",
         all(r["serves_truth"] is True and r["promoted"] is True for r in receipts)),
        ("every proven receipt is L7_executed_proof with all sub-proofs passing",
         all(r["verification_level"] == "L7_executed_proof" and all(p["passed"] for p in r["proofs"]) for r in receipts)),
        ("EVERY proven row carries a non-null input_edge_type_id", all(bool(r["input_edge_type_id"]) for r in proven)),
        ("EVERY proven row carries a non-null output_edge_type_id", all(bool(r["output_edge_type_id"]) for r in proven)),
        ("typed == proven_deterministic (every workable leaf is typed)",
         build_manifest(proven, gated)["typed"] == build_manifest(proven, gated)["proven_deterministic"] == len(proven)),
        ("roundtrip-inverse pairs prove reversible (roundtrip_test passed)",
         all(any(p["name"] == "roundtrip_test" and p["passed"] for p in _prove_one(s)["proofs"]) for s in inverse_specs)),
        ("deterministic: re-running yields identical proven rows",
         [json.dumps(r, sort_keys=True) for r in proven_typed_rows()]
         == [json.dumps(r, sort_keys=True) for r in proven]),
        # gated-effect honesty law
        (">=1 gated-effect candidate declared", len(gated) >= 1),
        ("EVERY gated-effect row is candidate=true AND serves_truth=false",
         all(r["candidate"] is True and r["serves_truth"] is False for r in gated)),
        ("EVERY gated-effect row carries a known effect",
         all(r["effect"] in {"network_read", "network_write", "model_call", "file_write"} for r in gated)),
        ("EVERY gated-effect row carries a non-empty proof_obligation",
         all(isinstance(r["proof_obligation"], str) and r["proof_obligation"] for r in gated)),
        ("EVERY gated-effect row carries both canonical edge type_ids",
         all(bool(r["input_edge_type_id"]) and bool(r["output_edge_type_id"]) for r in gated)),
        ("NO gated-effect id leaked into the proven set", proven_ids.isdisjoint({r["primitive_id"] for r in gated})),
        # the proof gate is real
        ("a deliberately-wrong deterministic fixture FAILS (stays candidate, never promoted)",
         wrong["serves_truth"] is False and wrong["promoted"] is False),
        ("the wrong leaf is NOT in the persisted proven rows", NEGATIVE_SPECS[0]["id"] not in proven_ids),
        ("an un-runnable fixture fails the proof, does not promote",
         err["serves_truth"] is False and err["promoted"] is False),
        ("mutators registered into the shared registry (add-only seam)",
         all(m in MUTATOR_REGISTRY for m in _NEW_MUTATORS)),
    ]
    failed = [n for n, ok in checks if not ok]
    if failed:
        print("FAIL - domain_ind_logistics_retail_telecom:\n  " + "\n  ".join(failed))
        return 1
    print(f"PASS - domain_ind_logistics_retail_telecom: {len(proven)} PROVEN-DETERMINISTIC + TYPED "
          f"logistics/retail/telecom leaf primitives (serves_truth=true via executed proof, L7; all typed via "
          f"canonical edge ids; {sum(1 for r in proven if r['has_roundtrip_proof'])} reversible roundtrip pairs) and "
          f"{len(gated)} honestly-declared GATED-EFFECT candidates (candidate/serves_truth=false, each with an "
          "effect + live-integration proof_obligation). A wrong-expected fixture and an un-runnable fixture correctly "
          "stay candidate. Counts kept SEPARATE.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test and not args.write:
        return self_test()
    manifest = write_pack()
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return self_test()


if __name__ == "__main__":
    raise SystemExit(main())
