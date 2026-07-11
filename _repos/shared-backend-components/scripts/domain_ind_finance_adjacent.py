#!/usr/bin/env python3
"""scripts.domain_ind_finance_adjacent — WORKABLE (proven + TYPED) deterministic SHAPE leaves for finance-adjacent
formats (payments / banking / market-data message plumbing).

ADD-ONLY parallel path (its OWN shard file). It IMPORTS the shared machinery, never edits it:
  * `run_primitive_proof` / `MUTATOR_REGISTRY` / `_receipt` from `scripts.mutator_registry` — the proof-runner EXECUTES
    each pure mutator against a synthetic fixture and flips serves_truth false->true ONLY on a PASSING executed proof;
  * `canonicalize_edge` from `scripts.build_edge_type_retrofit` — folds each leaf's logical edge labels to canonical
    type_ids so every proven leaf is also TYPED (input_edge_type_id + output_edge_type_id) and can chain.

Covers parse / extract / validate / emit / checksum / convert / normalize SHAPES (SYNTHETIC / public-standard fixtures,
NO real PII / PAN / SSN / secrets) for:
  IBAN (mod-97 checksum, rearrange, country/check-digit/BBAN extract, compute-check-digits, normalize)
  · ABA bank routing number (weighted mod-10 checksum, compute check digit, routing-symbol / institution-id extract)
  · ISO 4217 currency (validate, minor-units, alpha->numeric)  · ISO 3166 country (validate, alpha2<->alpha3, numeric)
  · FIX tag (parse<->emit, tag/msg-type extract)  · card BIN + Luhn (SYNTHETIC test numbers only: validate, compute
  check digit, BIN extract, network-by-BIN shape, PAN mask, last-4)  · amount / decimal (normalize thousands, to/from
  minor units, half-up round)  · SWIFT-BIC (shape validate, bank/country/location/branch extract).

Every validator operates on the SHAPE only against SYNTHETIC or PUBLIC-STANDARD fixtures (well-known test IBAN
GB82WEST12345698765432, test card 4111111111111111, public routing shape 021000021 — no live account maps to these).

DOMAIN LAWS honored: NO insurance primitives (any domain); NO real PAN/PII/secrets — card work uses only published
test numbers and operates on SHAPE + Luhn; synthetic/public shapes only. NETWORK/EFFECTFUL capabilities (bank-account
verification API, card-network authorization, IBAN-lookup service, FX-rate fetch, sanctions/OFAC screening call,
market-data feed subscribe) are NEVER run through the proof runner and NEVER serve_truth — they are declared as GATED
EFFECT candidates (candidate=true, serves_truth=false, effect, proof_obligation) in a SEPARATE section of the shard,
with SEPARATE honest counts.

Deterministic + offline: no network, no LLM, no wall-clock, no RNG (fixed literal manifest timestamp; stable string
seeds only; Decimal arithmetic, never float). CLI: --self-test | --write.

Register tuple for the shared proof suite (REPORT ONLY — this module does NOT self-register):
    ("_repos/shared-backend-components/scripts/domain_ind_finance_adjacent.py", "domain_ind_finance_adjacent")
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import json
import re
import sys
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

# IMPORT the shared machinery — never edit it (ADD-ONLY / flexible-multi-path).
from scripts.mutator_registry import (  # noqa: E402
    MUTATOR_REGISTRY,
    _receipt,
    run_primitive_proof,
)
from scripts.build_edge_type_retrofit import canonicalize_edge  # noqa: E402

DOMAIN = "ind_finance_adjacent"
_FIXED_UTC = "2026-07-03"  # fixed literal timestamp — NO wall-clock (repo law: deterministic + offline)

OUT_DIR = _resource("data") / "dev-intel" / "domain_primitives"
OUT_JSONL = OUT_DIR / "domain_ind_finance_adjacent.jsonl"
OUT_MANIFEST = OUT_DIR / "manifest_ind_finance_adjacent.json"


# ── small PUBLIC-STANDARD lookup tables (single-source module constants; NOT PII — these are open ISO code lists) ──
#: ISO 4217 minor units (subset) — how many decimal places the currency's minor unit has.
_ISO4217_MINOR_UNITS = {"USD": 2, "EUR": 2, "GBP": 2, "JPY": 0, "CHF": 2, "CAD": 2, "AUD": 2, "CNY": 2, "KWD": 3, "BHD": 3}
#: ISO 4217 alpha -> numeric code (subset).
_ISO4217_NUMERIC = {"USD": "840", "EUR": "978", "GBP": "826", "JPY": "392", "CHF": "756", "CAD": "124",
                    "AUD": "036", "CNY": "156", "KWD": "414", "BHD": "048"}
#: ISO 3166-1 alpha2 -> (alpha3, numeric) (subset).
_ISO3166 = {"US": ("USA", "840"), "GB": ("GBR", "826"), "DE": ("DEU", "276"), "FR": ("FRA", "250"),
            "JP": ("JPN", "392"), "CH": ("CHE", "756"), "CA": ("CAN", "124"), "AU": ("AUS", "036"),
            "CN": ("CHN", "156"), "NL": ("NLD", "528")}
_ISO3166_ALPHA3_TO_ALPHA2 = {v[0]: k for k, v in _ISO3166.items()}


# ── PURE deterministic mutators, contract (payload, **kwargs) -> (output, receipt). Domain-prefixed (`fadj_`) so they
#    never collide with existing registry entries; registered via setdefault (idempotent, never overwrites). ──

# ---- IBAN (ISO 13616): mod-97 checksum + structural extraction. Public test IBAN only. ----
def _iban_mod97(iban: str) -> int:
    """Standard IBAN mod-97: move first 4 chars to end, map A-Z->10-35 / 0-9->0-9, take integer mod 97."""
    rearranged = iban[4:] + iban[:4]
    digits = "".join(str(int(c, 36)) for c in rearranged)  # int(c,36): '0'..'9'->0-9, 'A'..'Z'->10-35
    return int(digits) % 97


def fadj_iban_normalize(iban: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = iban.replace(" ", "").upper()
    return out, _receipt("fadj_iban_normalize", before=iban, after=out, lossless=False, note="strip spaces + uppercase IBAN")


def fadj_iban_checksum_valid(iban: str, **_kw: Any) -> tuple[bool, dict[str, Any]]:
    out = _iban_mod97(iban) == 1
    return out, _receipt("fadj_iban_checksum_valid", before=iban, after=out, lossless=False, note="IBAN valid iff mod-97 == 1 (ISO 13616)")


def fadj_iban_country_code(iban: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = iban[:2]
    return out, _receipt("fadj_iban_country_code", before=iban, after=out, lossless=False, note="IBAN country code (chars 0:2)")


def fadj_iban_check_digits(iban: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = iban[2:4]
    return out, _receipt("fadj_iban_check_digits", before=iban, after=out, lossless=False, note="IBAN check digits (chars 2:4)")


def fadj_iban_bban(iban: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = iban[4:]
    return out, _receipt("fadj_iban_bban", before=iban, after=out, lossless=False, note="IBAN basic bank account number (chars 4:)")


def fadj_iban_compute_check_digits(country_plus_bban: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    """Given country_code + BBAN (no check digits), compute the 2-digit IBAN check per ISO 13616 (98 - mod97)."""
    country, bban = country_plus_bban[:2], country_plus_bban[2:]
    rearranged = bban + country + "00"
    digits = "".join(str(int(c, 36)) for c in rearranged)
    check = 98 - (int(digits) % 97)
    out = f"{check:02d}"
    return out, _receipt("fadj_iban_compute_check_digits", before=country_plus_bban, after=out, lossless=False, note="compute IBAN check digits (98 - mod97)")


def fadj_iban_rearrange(iban: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = iban[4:] + iban[:4]
    return out, _receipt("fadj_iban_rearrange", before=iban, after=out, lossless=True, note="IBAN rearrange (first 4 -> end); fadj_iban_unrearrange restores")


def fadj_iban_unrearrange(rearranged: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = rearranged[-4:] + rearranged[:-4]
    return out, _receipt("fadj_iban_unrearrange", before=rearranged, after=out, lossless=True, note="undo IBAN rearrange (last 4 -> front)")


# ---- ABA bank routing number (9 digits): weighted mod-10 checksum + structural extraction. ----
def _aba_weighted_sum(routing: str) -> int:
    weights = (3, 7, 1, 3, 7, 1, 3, 7, 1)
    return sum(int(d) * w for d, w in zip(routing, weights))


def fadj_aba_checksum_valid(routing: str, **_kw: Any) -> tuple[bool, dict[str, Any]]:
    out = len(routing) == 9 and routing.isdigit() and _aba_weighted_sum(routing) % 10 == 0
    return out, _receipt("fadj_aba_checksum_valid", before=routing, after=out, lossless=False, note="ABA routing valid iff 9 digits and weighted sum mod 10 == 0")


def fadj_aba_compute_check_digit(first8: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    """Given the first 8 digits, compute the 9th (check) digit so the weighted mod-10 sum is 0. Check pos weight = 1."""
    weights = (3, 7, 1, 3, 7, 1, 3, 7)
    partial = sum(int(d) * w for d, w in zip(first8, weights))
    out = str((10 - (partial % 10)) % 10)
    return out, _receipt("fadj_aba_compute_check_digit", before=first8, after=out, lossless=False, note="compute ABA 9th check digit (weight 1)")


def fadj_aba_routing_symbol(routing: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = routing[:4]
    return out, _receipt("fadj_aba_routing_symbol", before=routing, after=out, lossless=False, note="ABA Federal Reserve routing symbol (chars 0:4)")


def fadj_aba_institution_id(routing: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = routing[4:8]
    return out, _receipt("fadj_aba_institution_id", before=routing, after=out, lossless=False, note="ABA institution identifier (chars 4:8)")


# ---- ISO 4217 currency ----
def fadj_iso4217_validate(code: str, **_kw: Any) -> tuple[bool, dict[str, Any]]:
    out = code in _ISO4217_MINOR_UNITS
    return out, _receipt("fadj_iso4217_validate", before=code, after=out, lossless=False, note="ISO 4217 alpha code in known set")


def fadj_iso4217_minor_units(code: str, **_kw: Any) -> tuple[int, dict[str, Any]]:
    out = _ISO4217_MINOR_UNITS[code]
    return out, _receipt("fadj_iso4217_minor_units", before=code, after=out, lossless=False, note="ISO 4217 minor-unit decimal places")


def fadj_iso4217_alpha_to_numeric(code: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = _ISO4217_NUMERIC[code]
    return out, _receipt("fadj_iso4217_alpha_to_numeric", before=code, after=out, lossless=False, note="ISO 4217 alpha -> numeric code")


# ---- ISO 3166 country ----
def fadj_iso3166_alpha2_validate(code: str, **_kw: Any) -> tuple[bool, dict[str, Any]]:
    out = code in _ISO3166
    return out, _receipt("fadj_iso3166_alpha2_validate", before=code, after=out, lossless=False, note="ISO 3166-1 alpha-2 in known set")


def fadj_iso3166_alpha2_to_alpha3(code: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = _ISO3166[code][0]
    return out, _receipt("fadj_iso3166_alpha2_to_alpha3", before=code, after=out, lossless=True, note="ISO 3166 alpha-2 -> alpha-3; fadj_iso3166_alpha3_to_alpha2 restores")


def fadj_iso3166_alpha3_to_alpha2(code: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = _ISO3166_ALPHA3_TO_ALPHA2[code]
    return out, _receipt("fadj_iso3166_alpha3_to_alpha2", before=code, after=out, lossless=True, note="ISO 3166 alpha-3 -> alpha-2")


def fadj_iso3166_alpha2_to_numeric(code: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = _ISO3166[code][1]
    return out, _receipt("fadj_iso3166_alpha2_to_numeric", before=code, after=out, lossless=False, note="ISO 3166 alpha-2 -> numeric code")


# ---- FIX tag (tag=value pairs; SOH shown as '|' in synthetic fixtures) ----
def fadj_fix_parse(msg: str, **_kw: Any) -> tuple[dict[str, str], dict[str, Any]]:
    out: dict[str, str] = {}
    for pair in msg.split("|"):
        if pair:
            k, v = pair.split("=", 1)
            out[k] = v
    return out, _receipt("fadj_fix_parse", before=msg, after=out, lossless=True, note="FIX message -> ordered {tag:value}; fadj_fix_emit restores")


def fadj_fix_emit(tags: dict[str, Any], **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = "|".join(f"{k}={v}" for k, v in tags.items())
    return out, _receipt("fadj_fix_emit", before=tags, after=out, lossless=True, note="{tag:value} -> FIX message string")


def fadj_fix_tag_value(msg: str, tag: str = "35", **_kw: Any) -> tuple[str, dict[str, Any]]:
    val = ""
    for pair in msg.split("|"):
        if pair and pair.split("=", 1)[0] == tag:
            val = pair.split("=", 1)[1]
            break
    return val, _receipt("fadj_fix_tag_value", before=msg, after=val, lossless=False, note=f"extract FIX tag {tag}")


def fadj_fix_msg_type(msg: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    val, _ = fadj_fix_tag_value(msg, tag="35")
    return val, _receipt("fadj_fix_msg_type", before=msg, after=val, lossless=False, note="extract FIX MsgType (tag 35)")


# ---- card BIN + Luhn. SYNTHETIC / published test numbers ONLY; operates on SHAPE, no real PAN. ----
def _luhn_sum(number: str) -> int:
    total = 0
    for i, ch in enumerate(reversed(number)):
        d = int(ch)
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total


def fadj_luhn_valid(number: str, **_kw: Any) -> tuple[bool, dict[str, Any]]:
    out = number.isdigit() and len(number) > 0 and _luhn_sum(number) % 10 == 0
    return out, _receipt("fadj_luhn_valid", before=number, after=out, lossless=False, note="Luhn valid iff mod-10 == 0 (synthetic test number)")


def fadj_luhn_compute_check_digit(partial: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    """Given a number WITHOUT its check digit, compute the Luhn check digit that makes the full number valid."""
    # append a placeholder 0, compute sum, the check digit closes it to mod 10.
    s = _luhn_sum(partial + "0")
    out = str((10 - (s % 10)) % 10)
    return out, _receipt("fadj_luhn_compute_check_digit", before=partial, after=out, lossless=False, note="compute Luhn check digit")


def fadj_card_bin_extract(number: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = number[:6]
    return out, _receipt("fadj_card_bin_extract", before=number, after=out, lossless=False, note="extract card BIN/IIN (first 6 digits)")


def fadj_card_network_by_bin(number: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    """Classify card network by leading-digit SHAPE (no lookup of a real account). Published prefix ranges."""
    n = number
    two = n[:2]
    if n[:1] == "4":
        net = "visa"
    elif two in {"34", "37"}:
        net = "amex"
    elif two in {"51", "52", "53", "54", "55"} or (len(n) >= 4 and 2221 <= int(n[:4]) <= 2720):
        net = "mastercard"
    elif n[:4] == "6011" or two == "65":
        net = "discover"
    else:
        net = "unknown"
    return net, _receipt("fadj_card_network_by_bin", before=number, after=net, lossless=False, note="card network by leading-digit shape")


def fadj_card_mask(number: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    """Mask all but the last 4 (PAN masking) — lossy by design; a masking transform never keeps the middle digits."""
    out = "*" * (len(number) - 4) + number[-4:] if len(number) > 4 else number
    return out, _receipt("fadj_card_mask", before=number, after=out, lossless=False, note="mask all but last 4 (PAN masking)")


def fadj_card_last4(number: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = number[-4:]
    return out, _receipt("fadj_card_last4", before=number, after=out, lossless=False, note="extract last 4 digits")


# ---- amount / decimal normalization (Decimal only — never float) ----
def fadj_amount_normalize(amount: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    """Strip thousands separators (commas) -> canonical decimal string."""
    out = amount.replace(",", "")
    return out, _receipt("fadj_amount_normalize", before=amount, after=out, lossless=False, note="strip thousands separators")


def fadj_amount_to_minor_units(amount: str, units: int = 2, **_kw: Any) -> tuple[int, dict[str, Any]]:
    out = int(Decimal(amount) * (10 ** units))
    return out, _receipt("fadj_amount_to_minor_units", before=amount, after=out, lossless=True, note="decimal string -> integer minor units; fadj_amount_from_minor_units restores")


def fadj_amount_from_minor_units(minor: int, units: int = 2, **_kw: Any) -> tuple[str, dict[str, Any]]:
    d = Decimal(int(minor)) / (10 ** units)
    out = f"{d:.{units}f}"
    return out, _receipt("fadj_amount_from_minor_units", before=minor, after=out, lossless=True, note="integer minor units -> fixed-decimals string")


def fadj_amount_round_half_up(amount: str, places: int = 2, **_kw: Any) -> tuple[str, dict[str, Any]]:
    q = Decimal(1).scaleb(-places)
    out = str(Decimal(amount).quantize(q, rounding=ROUND_HALF_UP))
    return out, _receipt("fadj_amount_round_half_up", before=amount, after=out, lossless=False, note="round to N places, half-up (Decimal)")


# ---- SWIFT-BIC (ISO 9362) shape: BANK(4 alpha) COUNTRY(2 alpha) LOCATION(2 alnum) [BRANCH(3 alnum)] ----
_BIC_RE = re.compile(r"^[A-Z]{4}[A-Z]{2}[A-Z0-9]{2}([A-Z0-9]{3})?$")


def fadj_bic_validate(bic: str, **_kw: Any) -> tuple[bool, dict[str, Any]]:
    out = bool(_BIC_RE.match(bic))
    return out, _receipt("fadj_bic_validate", before=bic, after=out, lossless=False, note="BIC shape valid (ISO 9362: 8 or 11 chars)")


def fadj_bic_bank_code(bic: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = bic[:4]
    return out, _receipt("fadj_bic_bank_code", before=bic, after=out, lossless=False, note="BIC bank/institution code (chars 0:4)")


def fadj_bic_country_code(bic: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = bic[4:6]
    return out, _receipt("fadj_bic_country_code", before=bic, after=out, lossless=False, note="BIC country code (chars 4:6)")


def fadj_bic_location_code(bic: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = bic[6:8]
    return out, _receipt("fadj_bic_location_code", before=bic, after=out, lossless=False, note="BIC location code (chars 6:8)")


def fadj_bic_branch_code(bic: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = bic[8:11] if len(bic) >= 11 else "XXX"
    return out, _receipt("fadj_bic_branch_code", before=bic, after=out, lossless=False, note="BIC branch code (chars 8:11) or default 'XXX'")


#: new pure mutators to plug into the shared registry (idempotent setdefault — never overwrites an existing entry)
_NEW_MUTATORS = {
    "fadj_iban_normalize": fadj_iban_normalize, "fadj_iban_checksum_valid": fadj_iban_checksum_valid,
    "fadj_iban_country_code": fadj_iban_country_code, "fadj_iban_check_digits": fadj_iban_check_digits,
    "fadj_iban_bban": fadj_iban_bban, "fadj_iban_compute_check_digits": fadj_iban_compute_check_digits,
    "fadj_iban_rearrange": fadj_iban_rearrange, "fadj_iban_unrearrange": fadj_iban_unrearrange,
    "fadj_aba_checksum_valid": fadj_aba_checksum_valid, "fadj_aba_compute_check_digit": fadj_aba_compute_check_digit,
    "fadj_aba_routing_symbol": fadj_aba_routing_symbol, "fadj_aba_institution_id": fadj_aba_institution_id,
    "fadj_iso4217_validate": fadj_iso4217_validate, "fadj_iso4217_minor_units": fadj_iso4217_minor_units,
    "fadj_iso4217_alpha_to_numeric": fadj_iso4217_alpha_to_numeric,
    "fadj_iso3166_alpha2_validate": fadj_iso3166_alpha2_validate,
    "fadj_iso3166_alpha2_to_alpha3": fadj_iso3166_alpha2_to_alpha3,
    "fadj_iso3166_alpha3_to_alpha2": fadj_iso3166_alpha3_to_alpha2,
    "fadj_iso3166_alpha2_to_numeric": fadj_iso3166_alpha2_to_numeric,
    "fadj_fix_parse": fadj_fix_parse, "fadj_fix_emit": fadj_fix_emit,
    "fadj_fix_tag_value": fadj_fix_tag_value, "fadj_fix_msg_type": fadj_fix_msg_type,
    "fadj_luhn_valid": fadj_luhn_valid, "fadj_luhn_compute_check_digit": fadj_luhn_compute_check_digit,
    "fadj_card_bin_extract": fadj_card_bin_extract, "fadj_card_network_by_bin": fadj_card_network_by_bin,
    "fadj_card_mask": fadj_card_mask, "fadj_card_last4": fadj_card_last4,
    "fadj_amount_normalize": fadj_amount_normalize, "fadj_amount_to_minor_units": fadj_amount_to_minor_units,
    "fadj_amount_from_minor_units": fadj_amount_from_minor_units, "fadj_amount_round_half_up": fadj_amount_round_half_up,
    "fadj_bic_validate": fadj_bic_validate, "fadj_bic_bank_code": fadj_bic_bank_code,
    "fadj_bic_country_code": fadj_bic_country_code, "fadj_bic_location_code": fadj_bic_location_code,
    "fadj_bic_branch_code": fadj_bic_branch_code,
}


def register_new_mutators() -> None:
    """Plug the domain's pure mutators into the shared MUTATOR_REGISTRY (registration, not a rewrite). Idempotent."""
    for name, fn in _NEW_MUTATORS.items():
        MUTATOR_REGISTRY.setdefault(name, fn)


register_new_mutators()


# public-standard synthetic test fixtures (no live account/PAN maps to these)
_TEST_IBAN = "GB82WEST12345698765432"   # Wikipedia ISO 13616 example — a valid mod-97 IBAN
_TEST_ABA = "021000021"                 # published routing shape (valid weighted mod-10 checksum)
_TEST_CARD = "4111111111111111"         # published Visa test number (valid Luhn)


# ── proven-deterministic leaves: each a REAL SHAPE capability with a synthetic fixture + expected (+ inverse where a
#    roundtrip holds). spec fields: id, mutator, fixture, expected, args?, inverse?, format, input_edge, output_edge ──
LEAF_SPECS: list[dict[str, Any]] = [
    # IBAN
    {"id": "prim:leaf:fadj_iban_normalize", "mutator": "fadj_iban_normalize", "format": "iban",
     "fixture": "gb82 west 1234 5698 7654 32", "expected": _TEST_IBAN,
     "input_edge": "IbanRaw", "output_edge": "Iban"},
    {"id": "prim:leaf:fadj_iban_checksum_valid", "mutator": "fadj_iban_checksum_valid", "format": "iban",
     "fixture": _TEST_IBAN, "expected": True, "input_edge": "Iban", "output_edge": "ValidationResult"},
    {"id": "prim:leaf:fadj_iban_country_code", "mutator": "fadj_iban_country_code", "format": "iban",
     "fixture": _TEST_IBAN, "expected": "GB", "input_edge": "Iban", "output_edge": "CountryCode"},
    {"id": "prim:leaf:fadj_iban_check_digits", "mutator": "fadj_iban_check_digits", "format": "iban",
     "fixture": _TEST_IBAN, "expected": "82", "input_edge": "Iban", "output_edge": "CheckDigits"},
    {"id": "prim:leaf:fadj_iban_bban", "mutator": "fadj_iban_bban", "format": "iban",
     "fixture": _TEST_IBAN, "expected": "WEST12345698765432", "input_edge": "Iban", "output_edge": "Bban"},
    {"id": "prim:leaf:fadj_iban_compute_check_digits", "mutator": "fadj_iban_compute_check_digits", "format": "iban",
     "fixture": "GBWEST12345698765432", "expected": "82", "input_edge": "CountryBban", "output_edge": "CheckDigits"},
    {"id": "prim:leaf:fadj_iban_rearrange", "mutator": "fadj_iban_rearrange", "format": "iban",
     "fixture": _TEST_IBAN, "expected": "WEST12345698765432GB82", "inverse": "fadj_iban_unrearrange",
     "input_edge": "Iban", "output_edge": "IbanRearranged"},
    {"id": "prim:leaf:fadj_iban_unrearrange", "mutator": "fadj_iban_unrearrange", "format": "iban",
     "fixture": "WEST12345698765432GB82", "expected": _TEST_IBAN, "inverse": "fadj_iban_rearrange",
     "input_edge": "IbanRearranged", "output_edge": "Iban"},

    # ABA routing
    {"id": "prim:leaf:fadj_aba_checksum_valid", "mutator": "fadj_aba_checksum_valid", "format": "aba_routing",
     "fixture": _TEST_ABA, "expected": True, "input_edge": "AbaRouting", "output_edge": "ValidationResult"},
    {"id": "prim:leaf:fadj_aba_compute_check_digit", "mutator": "fadj_aba_compute_check_digit", "format": "aba_routing",
     "fixture": "02100002", "expected": "1", "input_edge": "AbaRoutingPartial", "output_edge": "CheckDigit"},
    {"id": "prim:leaf:fadj_aba_routing_symbol", "mutator": "fadj_aba_routing_symbol", "format": "aba_routing",
     "fixture": _TEST_ABA, "expected": "0210", "input_edge": "AbaRouting", "output_edge": "RoutingSymbol"},
    {"id": "prim:leaf:fadj_aba_institution_id", "mutator": "fadj_aba_institution_id", "format": "aba_routing",
     "fixture": _TEST_ABA, "expected": "0002", "input_edge": "AbaRouting", "output_edge": "InstitutionId"},

    # ISO 4217 currency
    {"id": "prim:leaf:fadj_iso4217_validate", "mutator": "fadj_iso4217_validate", "format": "iso4217_currency",
     "fixture": "USD", "expected": True, "input_edge": "CurrencyCode", "output_edge": "ValidationResult"},
    {"id": "prim:leaf:fadj_iso4217_minor_units", "mutator": "fadj_iso4217_minor_units", "format": "iso4217_currency",
     "fixture": "JPY", "expected": 0, "input_edge": "CurrencyCode", "output_edge": "MinorUnits"},
    {"id": "prim:leaf:fadj_iso4217_alpha_to_numeric", "mutator": "fadj_iso4217_alpha_to_numeric", "format": "iso4217_currency",
     "fixture": "EUR", "expected": "978", "input_edge": "CurrencyCode", "output_edge": "NumericCode"},

    # ISO 3166 country
    {"id": "prim:leaf:fadj_iso3166_alpha2_validate", "mutator": "fadj_iso3166_alpha2_validate", "format": "iso3166_country",
     "fixture": "GB", "expected": True, "input_edge": "CountryAlpha2", "output_edge": "ValidationResult"},
    {"id": "prim:leaf:fadj_iso3166_alpha2_to_alpha3", "mutator": "fadj_iso3166_alpha2_to_alpha3", "format": "iso3166_country",
     "fixture": "US", "expected": "USA", "inverse": "fadj_iso3166_alpha3_to_alpha2",
     "input_edge": "CountryAlpha2", "output_edge": "CountryAlpha3"},
    {"id": "prim:leaf:fadj_iso3166_alpha3_to_alpha2", "mutator": "fadj_iso3166_alpha3_to_alpha2", "format": "iso3166_country",
     "fixture": "DEU", "expected": "DE", "inverse": "fadj_iso3166_alpha2_to_alpha3",
     "input_edge": "CountryAlpha3", "output_edge": "CountryAlpha2"},
    {"id": "prim:leaf:fadj_iso3166_alpha2_to_numeric", "mutator": "fadj_iso3166_alpha2_to_numeric", "format": "iso3166_country",
     "fixture": "FR", "expected": "250", "input_edge": "CountryAlpha2", "output_edge": "NumericCode"},

    # FIX tag
    {"id": "prim:leaf:fadj_fix_parse", "mutator": "fadj_fix_parse", "format": "fix_tag",
     "fixture": "8=FIX.4.2|35=D|55=IBM", "expected": {"8": "FIX.4.2", "35": "D", "55": "IBM"},
     "inverse": "fadj_fix_emit", "input_edge": "FixMessage", "output_edge": "FixTagMap"},
    {"id": "prim:leaf:fadj_fix_emit", "mutator": "fadj_fix_emit", "format": "fix_tag",
     "fixture": {"8": "FIX.4.4", "35": "8"}, "expected": "8=FIX.4.4|35=8",
     "inverse": "fadj_fix_parse", "input_edge": "FixTagMap", "output_edge": "FixMessage"},
    {"id": "prim:leaf:fadj_fix_tag_value", "mutator": "fadj_fix_tag_value", "format": "fix_tag",
     "fixture": "8=FIX.4.4|35=D|55=AAPL", "expected": "AAPL", "args": {"tag": "55"},
     "input_edge": "FixMessage", "output_edge": "TagValue"},
    {"id": "prim:leaf:fadj_fix_msg_type", "mutator": "fadj_fix_msg_type", "format": "fix_tag",
     "fixture": "8=FIX.4.2|35=8|150=0", "expected": "8", "input_edge": "FixMessage", "output_edge": "MsgType"},

    # card BIN + Luhn (synthetic test numbers only)
    {"id": "prim:leaf:fadj_luhn_valid", "mutator": "fadj_luhn_valid", "format": "card_bin_luhn",
     "fixture": _TEST_CARD, "expected": True, "input_edge": "CardNumber", "output_edge": "ValidationResult"},
    {"id": "prim:leaf:fadj_luhn_compute_check_digit", "mutator": "fadj_luhn_compute_check_digit", "format": "card_bin_luhn",
     "fixture": "411111111111111", "expected": "1", "input_edge": "CardNumberPartial", "output_edge": "CheckDigit"},
    {"id": "prim:leaf:fadj_card_bin_extract", "mutator": "fadj_card_bin_extract", "format": "card_bin_luhn",
     "fixture": _TEST_CARD, "expected": "411111", "input_edge": "CardNumber", "output_edge": "CardBin"},
    {"id": "prim:leaf:fadj_card_network_by_bin", "mutator": "fadj_card_network_by_bin", "format": "card_bin_luhn",
     "fixture": _TEST_CARD, "expected": "visa", "input_edge": "CardNumber", "output_edge": "CardNetwork"},
    {"id": "prim:leaf:fadj_card_mask", "mutator": "fadj_card_mask", "format": "card_bin_luhn",
     "fixture": _TEST_CARD, "expected": "************1111", "input_edge": "CardNumber", "output_edge": "MaskedPan"},
    {"id": "prim:leaf:fadj_card_last4", "mutator": "fadj_card_last4", "format": "card_bin_luhn",
     "fixture": _TEST_CARD, "expected": "1111", "input_edge": "CardNumber", "output_edge": "Last4"},

    # amount / decimal
    {"id": "prim:leaf:fadj_amount_normalize", "mutator": "fadj_amount_normalize", "format": "amount_decimal",
     "fixture": "1,234,567.89", "expected": "1234567.89", "input_edge": "AmountRaw", "output_edge": "AmountDecimal"},
    {"id": "prim:leaf:fadj_amount_to_minor_units", "mutator": "fadj_amount_to_minor_units", "format": "amount_decimal",
     "fixture": "12.34", "expected": 1234, "inverse": "fadj_amount_from_minor_units",
     "input_edge": "AmountDecimal", "output_edge": "MinorUnits"},
    {"id": "prim:leaf:fadj_amount_from_minor_units", "mutator": "fadj_amount_from_minor_units", "format": "amount_decimal",
     "fixture": 1234, "expected": "12.34", "inverse": "fadj_amount_to_minor_units",
     "input_edge": "MinorUnits", "output_edge": "AmountDecimal"},
    {"id": "prim:leaf:fadj_amount_round_half_up", "mutator": "fadj_amount_round_half_up", "format": "amount_decimal",
     "fixture": "1.005", "expected": "1.01", "input_edge": "AmountDecimal", "output_edge": "AmountRounded"},

    # SWIFT-BIC
    {"id": "prim:leaf:fadj_bic_validate", "mutator": "fadj_bic_validate", "format": "swift_bic",
     "fixture": "DEUTDEFF500", "expected": True, "input_edge": "Bic", "output_edge": "ValidationResult"},
    {"id": "prim:leaf:fadj_bic_bank_code", "mutator": "fadj_bic_bank_code", "format": "swift_bic",
     "fixture": "DEUTDEFF500", "expected": "DEUT", "input_edge": "Bic", "output_edge": "BankCode"},
    {"id": "prim:leaf:fadj_bic_country_code", "mutator": "fadj_bic_country_code", "format": "swift_bic",
     "fixture": "DEUTDEFF500", "expected": "DE", "input_edge": "Bic", "output_edge": "CountryCode"},
    {"id": "prim:leaf:fadj_bic_location_code", "mutator": "fadj_bic_location_code", "format": "swift_bic",
     "fixture": "DEUTDEFF500", "expected": "FF", "input_edge": "Bic", "output_edge": "LocationCode"},
    {"id": "prim:leaf:fadj_bic_branch_code", "mutator": "fadj_bic_branch_code", "format": "swift_bic",
     "fixture": "DEUTDEFF", "expected": "XXX", "input_edge": "Bic", "output_edge": "BranchCode"},
]

#: deliberately-wrong leaf — the proof gate MUST leave it candidate (never persisted as proven-deterministic)
NEGATIVE_SPEC: dict[str, Any] = {
    "id": "prim:leaf:fadj_WRONG_expected", "mutator": "fadj_iban_country_code", "format": "iban",
    "fixture": _TEST_IBAN, "expected": "ZZ", "input_edge": "Iban", "output_edge": "CountryCode"}


# ── GATED-EFFECT candidates: NETWORK / EFFECTFUL capabilities. NEVER run through the proof runner, NEVER serve_truth.
#    Each declares effect + proof_obligation (a live integration test with a credential) + typed edges. ──
GATED_EFFECT_SPECS: list[dict[str, Any]] = [
    {"id": "prim:gated:fadj_bank_account_verify", "capability": "bank account/routing verification via a banking API (e.g. micro-deposit or open-banking check)",
     "effect": "network_read", "proof_obligation": "live integration test against a sandbox banking-verification endpoint with a credential",
     "input_edge": "AbaRouting", "output_edge": "AccountVerificationResult", "format": "aba_routing"},
    {"id": "prim:gated:fadj_iban_lookup_service", "capability": "IBAN/BIC directory lookup against a remote IBAN validation service",
     "effect": "network_read", "proof_obligation": "live integration test against a sandbox IBAN-lookup endpoint with a credential",
     "input_edge": "Iban", "output_edge": "IbanDirectoryRecord", "format": "iban"},
    {"id": "prim:gated:fadj_card_network_authorize", "capability": "submit a card authorization request to a payment network/processor",
     "effect": "network_write", "proof_obligation": "live integration test against a sandbox payment-processor endpoint with merchant credentials",
     "input_edge": "CardNumber", "output_edge": "AuthorizationResponse", "format": "card_bin_luhn"},
    {"id": "prim:gated:fadj_fx_rate_fetch", "capability": "fetch a live FX conversion rate for a currency pair from a rates API",
     "effect": "network_read", "proof_obligation": "live integration test against a sandbox FX-rates endpoint with an API credential",
     "input_edge": "CurrencyCode", "output_edge": "FxRate", "format": "iso4217_currency"},
    {"id": "prim:gated:fadj_sanctions_screen_call", "capability": "screen a counterparty name against a sanctions/OFAC list service (public-list screening call)",
     "effect": "network_read", "proof_obligation": "live integration test against a sandbox sanctions-screening endpoint with a credential",
     "input_edge": "CounterpartyName", "output_edge": "ScreeningResult", "format": "swift_bic"},
    {"id": "prim:gated:fadj_market_data_subscribe", "capability": "subscribe to a real-time market-data feed (FIX/websocket session) and receive ticks",
     "effect": "network_read", "proof_obligation": "live integration test against a sandbox market-data feed with session credentials",
     "input_edge": "FixMessage", "output_edge": "MarketDataTick", "format": "fix_tag"},
]


def _prove_one(spec: dict[str, Any]) -> dict[str, Any]:
    return run_primitive_proof(
        spec["id"], spec["mutator"], spec["fixture"], spec["expected"],
        mutator_args=spec.get("args") or {}, has_inverse=spec.get("inverse"),
    )


def prove_all() -> list[tuple[dict[str, Any], dict[str, Any]]]:
    """Run every declared deterministic leaf through the imported executed-proof runner. Returns [(spec, receipt), ...]."""
    return [(s, _prove_one(s)) for s in LEAF_SPECS]


def build_proven_rows() -> list[dict[str, Any]]:
    """Persist-ready rows for leaves whose executed proof PASSED — TYPED via canonicalize_edge (workable == typed)."""
    rows: list[dict[str, Any]] = []
    for spec, receipt in prove_all():
        if receipt["serves_truth"] is not True:
            continue  # a failing / wrong-expected leaf stays candidate and is NOT persisted (the gate is the point)
        rows.append({
            "primitive_id": receipt["primitive_id"],
            "mutator": receipt["mutator"],
            "domain": DOMAIN,
            "format": spec["format"],
            "row_section": "proven_deterministic",
            "candidate": False,
            "serves_truth": True,
            "verification_level": "L7_executed_proof",
            "input_edge": spec["input_edge"],
            "output_edge": spec["output_edge"],
            "input_edge_type_id": canonicalize_edge(spec["input_edge"]),
            "output_edge_type_id": canonicalize_edge(spec["output_edge"]),
            "has_inverse": spec.get("inverse"),
            "proofs": [p["name"] for p in receipt["proofs"] if p["passed"]],
        })
    return rows


def build_gated_rows() -> list[dict[str, Any]]:
    """Gated-effect candidate rows — NEVER proven, NEVER serves_truth; typed so they still declare their edges."""
    rows: list[dict[str, Any]] = []
    for spec in GATED_EFFECT_SPECS:
        rows.append({
            "primitive_id": spec["id"],
            "domain": DOMAIN,
            "format": spec["format"],
            "row_section": "gated_effect_candidate",
            "capability": spec["capability"],
            "candidate": True,
            "serves_truth": False,
            "effect": spec["effect"],
            "proof_obligation": spec["proof_obligation"],
            "input_edge": spec["input_edge"],
            "output_edge": spec["output_edge"],
            "input_edge_type_id": canonicalize_edge(spec["input_edge"]),
            "output_edge_type_id": canonicalize_edge(spec["output_edge"]),
        })
    return rows


def build_manifest(proven: list[dict[str, Any]], gated: list[dict[str, Any]]) -> dict[str, Any]:
    typed = [r for r in proven if r["input_edge_type_id"] and r["output_edge_type_id"]]
    return {
        "record_type": "domain_primitive_shard_manifest",
        "domain": DOMAIN,
        "generator": "scripts/domain_ind_finance_adjacent.py",
        "generated_utc": _FIXED_UTC,
        "formats_covered": sorted({s["format"] for s in LEAF_SPECS}),
        # SEPARATE, honest counts (proven-deterministic vs gated-effect candidate).
        "defined_deterministic_count": len(LEAF_SPECS),
        "proven_deterministic": len(proven),
        "typed": len(typed),
        "gated_effect_candidates": len(gated),
        "gated_effect_by_effect": {e: sum(1 for r in gated if r["effect"] == e)
                                   for e in sorted({r["effect"] for r in gated})},
        "verification_level": "L7_executed_proof",
        "proven_primitive_ids": sorted(r["primitive_id"] for r in proven),
        "gated_effect_primitive_ids": sorted(r["primitive_id"] for r in gated),
        "note": "proven_deterministic rows: serves_truth=true set ONLY by an executed passing proof (run_primitive_proof, "
                "imported from scripts/mutator_registry.py); every row TYPED via canonicalize_edge (imported from "
                "scripts/build_edge_type_retrofit.py). gated_effect_candidate rows: network/effectful capabilities are "
                "NEVER proven and stay candidate/serves_truth=false with an effect + proof_obligation. Synthetic / "
                "public-standard shapes only (test IBAN/card/routing); NO insurance; NO real PAN/PII/secrets. Counts "
                "are separate and honest.",
    }


def write_shard() -> dict[str, Any]:
    proven = build_proven_rows()
    gated = build_gated_rows()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    # Both sections written to the SAME shard, each row self-labels via row_section.
    all_rows = proven + gated
    OUT_JSONL.write_text(
        "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in all_rows), encoding="utf-8")
    manifest = build_manifest(proven, gated)
    OUT_MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def self_test() -> int:
    proven = prove_all()
    rows = build_proven_rows()
    gated = build_gated_rows()
    ids = [r["primitive_id"] for r in rows]
    typed = [r for r in rows if r["input_edge_type_id"] and r["output_edge_type_id"]]
    roundtrip_specs = [s for s in LEAF_SPECS if s.get("inverse")]
    proven_by_id = {r["primitive_id"]: r for (s, r) in proven}

    # deliberately-wrong leaf must stay candidate (proof gate is real) — and never enter the proven section
    wrong = _prove_one(NEGATIVE_SPEC)
    # a second wrong path: an un-runnable fixture -> execution error -> not promoted
    err = run_primitive_proof("prim:leaf:fadj_EXEC_ERROR", "fadj_fix_parse", object(), "irrelevant")

    manifest = build_manifest(rows, gated)
    valid_effects = {"network_read", "network_write", "model_call", "file_write"}
    target_formats = {"iban", "aba_routing", "iso4217_currency", "iso3166_country", "fix_tag",
                      "card_bin_luhn", "amount_decimal", "swift_bic"}

    checks: list[tuple[str, bool]] = [
        (">=25 deterministic leaves declared", len(LEAF_SPECS) >= 25),
        ("unique proven primitive ids", len(set(ids)) == len(ids)),
        (">=25 leaves PROVE serves_truth=true via an executed proof", len(rows) >= 25),
        ("every proven receipt is L7_executed_proof with all sub-proofs passing",
         all(r["verification_level"] == "L7_executed_proof" and all(p["passed"] for p in r["proofs"])
             for (_s, r) in proven if r["serves_truth"] is True)),
        ("every declared leaf actually PROVED (no silent drop)", len(rows) == len(LEAF_SPECS)),
        ("EVERY proven row carries non-null input+output edge type ids", len(typed) == len(rows)),
        ("manifest typed == proven_deterministic", manifest["typed"] == manifest["proven_deterministic"]),
        ("all 8 target formats are covered", set(manifest["formats_covered"]) == target_formats),
        ("roundtrip-inverse pairs actually ran + PASSED a roundtrip proof", all(
            any(p["name"] == "roundtrip_test" and p["passed"] for p in proven_by_id[s["id"]]["proofs"])
            for s in roundtrip_specs)),
        (">=3 roundtrip-inverse pairs declared", len(roundtrip_specs) >= 3),
        ("domain stamped on every proven row", all(r["domain"] == DOMAIN for r in rows)),
        ("deterministic: re-running yields identical proven rows",
         [json.dumps(r, sort_keys=True) for r in build_proven_rows()] == [json.dumps(r, sort_keys=True) for r in rows]),
        # gated-effect law: EVERY gated row is candidate / serves_truth=false with a valid effect + proof_obligation
        (">=1 gated-effect candidate declared", len(gated) >= 1),
        ("EVERY gated-effect row is candidate + serves_truth=false",
         all(r["candidate"] is True and r["serves_truth"] is False for r in gated)),
        ("EVERY gated-effect row has a valid effect + non-empty proof_obligation",
         all(r["effect"] in valid_effects and isinstance(r["proof_obligation"], str) and r["proof_obligation"]
             for r in gated)),
        ("EVERY gated-effect row is TYPED (input+output edge type ids)",
         all(r["input_edge_type_id"] and r["output_edge_type_id"] for r in gated)),
        ("no gated-effect id leaked into the proven section", not (set(r["primitive_id"] for r in gated) & set(ids))),
        # the proof gate is real
        ("a deliberately-wrong leaf stays CANDIDATE (never promoted)",
         wrong["serves_truth"] is False and wrong["promoted"] is False),
        ("the wrong leaf is NOT persisted as proven", NEGATIVE_SPEC["id"] not in set(ids)),
        ("an un-runnable fixture fails the proof, does not promote",
         err["serves_truth"] is False and err["promoted"] is False),
        ("new mutators registered into the shared registry (add-only seam)",
         all(m in MUTATOR_REGISTRY for m in _NEW_MUTATORS)),
    ]
    failed = [n for n, ok in checks if not ok]
    if failed:
        print("FAIL - domain_ind_finance_adjacent:\n  " + "\n  ".join(failed))
        return 1
    print(f"PASS - domain_ind_finance_adjacent: {len(rows)} WORKABLE (proven + TYPED) deterministic SHAPE leaves for "
          f"'{DOMAIN}' (serves_truth=true, L7_executed_proof; typed=={len(rows)}) across 8 finance-adjacent formats; "
          f"{len(roundtrip_specs)} inverse pairs proven reversible via roundtrip; {len(gated)} network/effectful "
          "capabilities declared as GATED-EFFECT candidates (serves_truth=false, effect + proof_obligation). "
          "A deliberately-wrong leaf and an un-runnable fixture correctly stay candidate. Synthetic/public shapes; "
          "no insurance; no real PAN/PII.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    if args.write:
        manifest = write_shard()
        print(json.dumps(manifest, indent=2, sort_keys=True))
        return self_test()
    return self_test()


if __name__ == "__main__":
    raise SystemExit(main())
