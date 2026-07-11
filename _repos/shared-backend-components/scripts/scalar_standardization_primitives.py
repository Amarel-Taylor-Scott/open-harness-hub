#!/usr/bin/env python3
"""scripts.scalar_standardization_primitives — the owner's "scalar standardization kernel" §1/§2/§15 as
EXECUTABLE primitives (2026-07-08): the BASE ABSTRACTION where every observed value becomes a standardized
scalar object — raw preserved, type inferred, canonical form, match key, quality flags, trace, provenance —
BEFORE anything climbs to lists/arrays/matrices/graphs. "If '5 ft', '5'', '60 in', '1.524 m' are not
standardized correctly as scalar quantities, every downstream list, vector, embedding, matcher, and matrix
becomes polluted" (owner). This pack is the connective tissue that was missing: the type ROUTER
(infer_scalar_type) + the dirty-value parsers with no home yet (boolean/integer/decimal/percent/null) + the
one envelope (standardize_scalar) that composes the quantity/money/string packs already built.

Reuse-first (law §1 of this repo): quantities+money delegate to `quantity_money_primitives` (UCUM/ISO-4217,
Decimal, ranges kept); string match keys delegate to `string_standardization_primitives`
(diacritics/casefold/phonetic/blocking). This pack adds ONLY the scalar families those packs did not cover
and the router+envelope that unifies them. Nothing here re-defines a unit table or a currency table — it
imports the single source (law §6, no magic values).

Laws encoded: raw != cleaned != canonical != display != match (all kept, §1); identifiers preserve leading
zeros while quantities drop them ("00123" as account-id stays "00123"; as a count -> 123) — the distinction
is DATA-DRIVEN by field hint, never guessed silently; accounting negatives "(123.45)" -> -123.45; locale
decimal/thousands separators ("1,234.56" en vs "1.234,56" eu) are a PARAMETER, never assumed; "12%" -> 0.12
and "50 bps" -> 0.005 kept with their kind; dirty booleans (YES/y/1/on/active) normalized; null/placeholder/
unknown/reference-to-prior separated (§3.1). candidate=true, serves_truth=false.

    python3 scripts/scalar_standardization_primitives.py --self-test
    python3 scripts/scalar_standardization_primitives.py --demo "  5 ft. " --field height
    python3 scripts/scalar_standardization_primitives.py --demo "00123" --field account_id
"""
from __future__ import annotations

import sys
from pathlib import Path

_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import inspect  # noqa: E402
import json  # noqa: E402
import re  # noqa: E402
from decimal import Decimal, InvalidOperation  # noqa: E402
from typing import Any  # noqa: E402

try:
    from src.teleon.experiments.ids import canonical_id  # noqa: E402
except ImportError as exc:  # pragma: no cover
    raise SystemExit(f"scalar_standardization_primitives requires canonical_id; import failed: {exc}")

# reuse-first: quantities/money/string keys already exist as governed packs — compose, never re-implement
from scripts.quantity_money_primitives import (  # noqa: E402
    CURRENCY_SYMBOLS, UNIT_ALIASES, parse_money, parse_quantity)
from scripts.string_standardization_primitives import (  # noqa: E402
    casefold_for_match, generate_match_keys, strip_diacritics_for_match, trim_collapse_whitespace,
    unicode_normalize_nfc)

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
CARD_PREFIX = "prim-scalar"
SCALAR_RULES_VERSION = "scalar-std-v1"

# ── versioned token dictionaries (§3.1 null/placeholder, §2.3 boolean) — data, single source ─────────────────
NULL_TOKENS = frozenset({"", "n/a", "na", "null", "none", "nil", "nan", "-", "--", "---", ".", "..", "..."})
UNKNOWN_TOKENS = frozenset({"unknown", "unk", "?", "??", "tbd", "to be determined", "pending"})
REFERENCE_TOKENS = frozenset({"same as above", "see above", "ditto", "as above", "same"})
INVALID_STRUCTURED_TOKENS = frozenset({"see notes", "see note", "refer to notes"})
BOOL_TRUE_TOKENS = frozenset({"true", "t", "yes", "y", "1", "on", "enabled", "enable", "active",
                              "checked", "complete", "completed"})
BOOL_FALSE_TOKENS = frozenset({"false", "f", "no", "n", "0", "off", "disabled", "disable", "inactive",
                               "unchecked", "incomplete"})
#: only these route a bare token to `boolean` (1/0/x kept out — they look like ints/codes; the router must
#: not steal integers). parse_boolean, once the type is KNOWN boolean, still maps 1/0.
_ROUTER_BOOL_TOKENS = ((BOOL_TRUE_TOKENS | BOOL_FALSE_TOKENS) - {"1", "0", "t", "f", "n", "y", "x"})
#: field-name hints route ambiguous shapes (data-driven, extend as data)
ID_FIELD_HINTS = frozenset({"id", "code", "zip", "zipcode", "postal", "postcode", "account", "acct",
                            "ssn", "ein", "tin", "npi", "dea", "phone", "tel", "mobile", "fax", "sku",
                            "isbn", "upc", "gtin", "mrn", "routing", "iban", "number", "no", "num"})
#: fields that are genuinely counts/ordinals — drop leading zeros (id-hint wins over these when both fire)
INTEGER_FIELD_HINTS = frozenset({"count", "quantity", "qty", "age", "index", "rank", "level", "sequence",
                                 "position", "tally", "votes", "score", "points", "year", "quarter"})
QUANTITY_FIELD_HINTS = frozenset({"height", "width", "length", "depth", "distance", "weight", "size",
                                  "area", "volume", "mass", "diameter", "radius", "altitude", "elevation",
                                  "thickness", "speed", "dose", "dosage"})
MONEY_FIELD_HINTS = frozenset({"amount", "price", "cost", "revenue", "salary", "fee", "balance", "total",
                               "subtotal", "payment", "charge", "wage", "budget", "spend", "income",
                               "expense", "premium", "value", "usd"})
PERCENT_FIELD_HINTS = frozenset({"rate", "percent", "percentage", "pct", "margin", "discount", "apr",
                                 "apy", "yield", "interest", "utilization"})
_INT_RE = re.compile(r"^[+-]?\d{1,3}(?:,\d{3})+$|^[+-]?\d+$")
_DEC_RE = re.compile(r"^[+-]?(?:\d[\d,\. ]*)?\d(?:[eE][+-]?\d+)?$")
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# ── ATOMIC scalar parsers (pure stdlib, self-contained cards) ─────────────────────────────────────────────────
def parse_null(raw: str) -> dict[str, Any]:
    """§3.1 — separate the *kinds* of empty: null vs unknown vs reference-to-prior vs invalid-for-structured.
    NEVER collapse 'Unknown' (a known-unknown) and '' (absent) into the same thing."""
    low = (raw or "").strip().casefold()
    if low in NULL_TOKENS:
        return {"raw_value": raw, "classification": "null", "canonical": None, "reason": "empty_or_placeholder"}
    if low in UNKNOWN_TOKENS:
        return {"raw_value": raw, "classification": "unknown", "canonical": None, "reason": "known_unknown"}
    if low in REFERENCE_TOKENS:
        return {"raw_value": raw, "classification": "reference_prior", "canonical": None,
                "reason": "refers_to_prior_value"}
    if low in INVALID_STRUCTURED_TOKENS:
        return {"raw_value": raw, "classification": "invalid_for_structured", "canonical": None,
                "reason": "free_text_marker_in_structured_field"}
    return {"raw_value": raw, "classification": "value", "canonical": raw}


def parse_boolean(raw: str) -> dict[str, Any]:
    """§2.3 — dirty booleans (YES/y/1/on/active/checked -> True; no/f/0/off/inactive -> False). Ambiguous ->
    canonical None with low confidence, never a coin-flip."""
    low = (raw or "").strip().casefold()
    if low in BOOL_TRUE_TOKENS:
        return {"raw_value": raw, "canonical": True, "display": "Yes", "confidence": 1.0}
    if low in BOOL_FALSE_TOKENS:
        return {"raw_value": raw, "canonical": False, "display": "No", "confidence": 1.0}
    return {"raw_value": raw, "canonical": None, "display": None, "confidence": 0.0,
            "reason": "not_a_recognized_boolean"}


def parse_integer(raw: str, *, is_identifier: bool = False) -> dict[str, Any]:
    """§2.4 — integers with thousands separators and accounting negatives. THE identifier distinction: as an
    identifier, '00123' preserves leading zeros (canonical stays the digit string); as a quantity it becomes
    123 with a leading_zeros_dropped flag. Never silently destroy an account/ZIP by casting to int."""
    v = (raw or "").strip()
    flags: list[str] = []
    trace = ["trim"]
    negative = False
    if v.startswith("(") and v.endswith(")"):  # accounting negative
        v = v[1:-1].strip()
        negative = True
        trace.append("parse_accounting_negative")
    if v[:1] in "+-":
        negative = negative or v[0] == "-"
        v = v[1:].strip()
        trace.append("parse_sign")
    cleaned = v.replace(",", "").replace(" ", "")
    if cleaned.replace(",", ""):
        trace.append("remove_thousands_separator")
    if not cleaned.isdigit():
        return {"raw_value": raw, "error": "not_an_integer", "confidence": 0.0, "transformation_trace": trace}
    had_leading_zero = len(cleaned) > 1 and cleaned[0] == "0"
    if is_identifier:
        canonical = ("-" + cleaned) if negative else cleaned  # PRESERVE leading zeros
        trace.append("preserve_leading_zeros_identifier")
        return {"raw_value": raw, "inferred_type": "identifier", "canonical": canonical,
                "value_int": int(cleaned) * (-1 if negative else 1), "is_identifier": True,
                "leading_zeros_preserved": had_leading_zero, "quality_flags": flags,
                "confidence": 0.97, "transformation_trace": trace}
    value = int(cleaned) * (-1 if negative else 1)
    if had_leading_zero:
        flags.append("leading_zeros_dropped")  # honest: we changed the surface form
    trace.append("cast_to_integer")
    return {"raw_value": raw, "inferred_type": "integer", "canonical": value, "value_int": value,
            "is_identifier": False, "quality_flags": flags, "confidence": 0.97,
            "transformation_trace": trace}


def parse_decimal(raw: str, *, locale: str = "en") -> dict[str, Any]:
    """§2.5 — decimals with locale-aware separators (en: '1,234.56'; eu: '1.234,56'), scientific notation,
    accounting negatives. Decimal arithmetic (never binary float — §2.5 owner law). Precision preserved."""
    v = (raw or "").strip()
    trace = ["trim", f"locale:{locale}"]
    negative = False
    if v.startswith("(") and v.endswith(")"):
        v, negative = v[1:-1].strip(), True
        trace.append("parse_accounting_negative")
    if locale == "eu":
        v = v.replace(".", "").replace(" ", "").replace(",", ".")
        trace.append("normalize_eu_separators")
    else:
        v = v.replace(",", "").replace(" ", "")
        trace.append("normalize_en_separators")
    try:
        dec = Decimal(v)
    except (InvalidOperation, ValueError):
        return {"raw_value": raw, "error": "not_a_decimal", "confidence": 0.0, "transformation_trace": trace}
    if negative:
        dec = -dec
    exponent = dec.as_tuple().exponent
    places = -exponent if isinstance(exponent, int) and exponent < 0 else 0
    return {"raw_value": raw, "inferred_type": "decimal", "canonical": str(dec), "value_decimal": str(dec),
            "decimal_places": places, "confidence": 0.95, "transformation_trace": trace + ["parse_decimal"]}


def parse_percent(raw: str) -> dict[str, Any]:
    """§3.9 — '12%' -> fraction 0.12 (percent_value 12); '50 bps' -> 0.005 (basis points); '1.5x' ->
    multiplier 1.5. Each KIND kept distinct — a rate field and a multiplier are not the same scalar."""
    low = (raw or "").strip().casefold().replace(" ", "")
    try:
        if low.endswith("%"):
            pv = Decimal(low[:-1].replace(",", ""))
            return {"raw_value": raw, "inferred_type": "percent", "kind": "percent", "percent_value": str(pv),
                    "canonical_fraction": str(pv / Decimal(100)), "confidence": 0.97,
                    "transformation_trace": ["parse_percent", "divide_by_100"]}
        if low.endswith("bps") or low.endswith("bp"):
            num = low[:-3] if low.endswith("bps") else low[:-2]
            bpv = Decimal(num.replace(",", ""))
            return {"raw_value": raw, "inferred_type": "percent", "kind": "basis_points",
                    "basis_points": str(bpv), "canonical_fraction": str(bpv / Decimal(10000)),
                    "confidence": 0.95, "transformation_trace": ["parse_basis_points", "divide_by_10000"]}
        if low.endswith("x"):
            mv = Decimal(low[:-1].replace(",", ""))
            return {"raw_value": raw, "inferred_type": "multiplier", "kind": "multiplier",
                    "multiplier": str(mv), "canonical_fraction": None, "confidence": 0.9,
                    "transformation_trace": ["parse_multiplier"]}
    except (InvalidOperation, ValueError):
        pass
    return {"raw_value": raw, "error": "not_a_percent", "confidence": 0.0}


# ── COMPOSITE: the type ROUTER + the ENVELOPE (primitives OF primitives, cross-pack) ─────────────────────────
def infer_scalar_type(raw: str, *, field_name: str = "") -> dict[str, Any]:
    """§1/§2 — decide what a raw value IS, from value shape + field-name hints (data-driven, never the model's
    own guess). Order matters: null/unknown first, then unambiguous boolean, percent, money (currency present
    OR money-hint field), quantity (unit present OR quantity-hint field), identifier (id-hint field OR
    leading-zero digits), integer, decimal, email/url, else string. Returns the type + confidence + the
    SIGNALS that fired (auditable)."""
    s = (raw or "").strip()
    low = s.casefold()
    fhints = {t for t in re.split(r"[^a-z0-9]+", (field_name or "").casefold()) if t}
    signals: list[str] = []
    nul = parse_null(raw)
    if nul["classification"] != "value":
        return {"raw_value": raw, "source_field": field_name, "inferred_type": nul["classification"],
                "confidence": 0.9, "signals": [f"null_dict:{nul['reason']}"]}
    if low in _ROUTER_BOOL_TOKENS:
        return {"raw_value": raw, "source_field": field_name, "inferred_type": "boolean", "confidence": 0.9,
                "signals": ["boolean_token"]}
    if s.endswith("%") or low.replace(" ", "").endswith("bps") or (fhints & PERCENT_FIELD_HINTS and "%" in s):
        signals.append("percent_marker")
        return {"raw_value": raw, "source_field": field_name, "inferred_type": "percent", "confidence": 0.9,
                "signals": signals}
    has_currency = any(sym in s for sym in ("$", "€", "£", "¥")) or \
        any(tok in CURRENCY_SYMBOLS for tok in low.replace(",", " ").split())
    if has_currency or (fhints & MONEY_FIELD_HINTS and re.search(r"\d", s)):
        signals.append("currency_symbol" if has_currency else "money_field_hint")
        return {"raw_value": raw, "source_field": field_name, "inferred_type": "money", "confidence": 0.88,
                "signals": signals}
    unit_tail = re.match(r"^\s*[~<>]?\s*[\d,\.\-–\s]+([a-zA-Z'\"″′]+)\.?\s*$", s)
    tail_unit = (unit_tail.group(1).strip().rstrip(".").casefold() if unit_tail else "")
    has_unit = tail_unit in UNIT_ALIASES or bool(re.match(r"^\s*\d+\s*['′]\s*\d*\s*[\"″]?\s*$", s))
    if has_unit or (fhints & QUANTITY_FIELD_HINTS and re.search(r"\d", s)):
        signals.append("unit_token" if has_unit else "quantity_field_hint")
        return {"raw_value": raw, "source_field": field_name, "inferred_type": "quantity", "confidence": 0.85,
                "signals": signals}
    digits_only = re.sub(r"[+\-(),\s]", "", s)
    is_id_field = bool(fhints & ID_FIELD_HINTS)
    is_int_field = bool(fhints & INTEGER_FIELD_HINTS)
    if digits_only.isdigit():
        leading_zero = len(digits_only) > 1 and digits_only[0] == "0"
        if is_id_field:  # explicit id field: PRESERVE leading zeros (account/ZIP/SSN)
            return {"raw_value": raw, "source_field": field_name, "inferred_type": "identifier",
                    "confidence": 0.85, "signals": ["id_field_hint"]}
        if is_int_field:  # explicit count/ordinal field: it is a number, drop leading zeros (+flag)
            return {"raw_value": raw, "source_field": field_name, "inferred_type": "integer",
                    "confidence": 0.85, "signals": ["integer_field_hint"]}
        if leading_zero:  # ambiguous + destructive-to-cast: default to PRESERVE (identifier)
            return {"raw_value": raw, "source_field": field_name, "inferred_type": "identifier",
                    "confidence": 0.7, "signals": ["leading_zero_digits_conservative_preserve"]}
    if _INT_RE.match(s) or (s.startswith("(") and s.endswith(")") and digits_only.isdigit()):
        return {"raw_value": raw, "source_field": field_name, "inferred_type": "integer", "confidence": 0.9,
                "signals": ["integer_shape"]}
    if _DEC_RE.match(s) and re.search(r"\d", s):
        return {"raw_value": raw, "source_field": field_name, "inferred_type": "decimal", "confidence": 0.85,
                "signals": ["decimal_shape"]}
    if _EMAIL_RE.match(s):
        return {"raw_value": raw, "source_field": field_name, "inferred_type": "email", "confidence": 0.92,
                "signals": ["email_shape"]}
    if low.startswith("http://") or low.startswith("https://") or low.startswith("www."):
        return {"raw_value": raw, "source_field": field_name, "inferred_type": "url", "confidence": 0.9,
                "signals": ["url_shape"]}
    return {"raw_value": raw, "source_field": field_name, "inferred_type": "string", "confidence": 0.6,
            "signals": ["fallthrough_string"]}


def _scalar_match_key(itype: str, parsed: dict[str, Any], cleaned: str) -> str:
    """Build the §1 match_key: a compact type-tagged canonical string so equal-meaning values collide
    ('5 ft' and '60 in' both -> 'qty.length:1.5240:m'). One key format per type family."""
    if itype in ("null", "unknown", "reference_prior", "invalid_for_structured"):
        return f"null:{itype}"
    if itype == "boolean":
        return f"bool:{parsed.get('canonical')}"
    if itype == "money":
        cv = parsed.get("canonical_value") or {}
        return f"money:{cv.get('currency', '?')}:{cv.get('amount', '?')}"
    if itype == "quantity":
        cv = parsed.get("canonical_value") or parsed.get("canonical") or {}
        if "low" in cv:  # a range
            return f"qty.range:{cv['low'].get('value')}-{cv['high'].get('value')}:{cv['low'].get('unit')}"
        return f"qty:{cv.get('value', '?')}:{cv.get('unit', '?')}"
    if itype == "identifier":
        return f"id:{parsed.get('canonical')}"
    if itype == "integer":
        return f"int:{parsed.get('canonical')}"
    if itype == "decimal":
        return f"dec:{parsed.get('canonical')}"
    if itype in ("percent", "multiplier"):
        return f"pct:{parsed.get('canonical_fraction') or parsed.get('multiplier')}"
    return f"str:{cleaned}"  # normalized (diacritic-stripped, casefolded) for email/url/string


def standardize_scalar(raw: str, *, field_name: str = "", locale: str = "en") -> dict[str, Any]:
    """THE ENVELOPE (§1) — any observed value -> the standardized-scalar object: raw preserved, type inferred,
    canonical form, display form, match_key, quality flags, confidence, transformation_trace, provenance.
    Composes the whole kernel: quantity/money delegate to quantity_money_primitives, string keys to
    string_standardization_primitives, and the scalar families to this pack's atoms. This is the object every
    downstream list/vector/matrix/matcher is built on — get it right here or pollute everything above it."""
    t = infer_scalar_type(raw, field_name=field_name)
    itype = t["inferred_type"]
    cleaned = trim_collapse_whitespace(unicode_normalize_nfc(raw or ""))
    trace = ["infer_scalar_type", "normalize_unicode", "trim_collapse_whitespace"]
    parsed: dict[str, Any] = {}
    canonical: Any = None
    display = cleaned
    confidence = t["confidence"]
    flags: list[str] = []

    if itype in ("null", "unknown", "reference_prior", "invalid_for_structured"):
        parsed = parse_null(raw)
        canonical, display, flags = None, "", [parsed["reason"]]
    elif itype == "boolean":
        parsed = parse_boolean(raw)
        canonical, display, confidence = parsed["canonical"], parsed["display"], parsed["confidence"]
    elif itype == "percent":
        parsed = parse_percent(raw)
        canonical, confidence = parsed.get("canonical_fraction"), parsed.get("confidence", confidence)
    elif itype == "money":
        parsed = parse_money(raw)
        canonical, confidence = parsed.get("canonical_value"), parsed.get("confidence", confidence)
        flags = parsed.get("issues", [])
    elif itype == "quantity":
        parsed = parse_quantity(raw)
        canonical = parsed.get("canonical_value") or parsed.get("canonical")
        confidence = parsed.get("confidence", confidence)
    elif itype == "identifier":
        parsed = parse_integer(raw, is_identifier=True)
        canonical, confidence = parsed.get("canonical"), parsed.get("confidence", confidence)
        display = str(canonical) if canonical is not None else cleaned
    elif itype == "integer":
        parsed = parse_integer(raw)
        canonical, confidence = parsed.get("canonical"), parsed.get("confidence", confidence)
        flags = parsed.get("quality_flags", [])
        display = str(canonical) if canonical is not None else cleaned
    elif itype == "decimal":
        parsed = parse_decimal(raw, locale=locale)
        canonical, confidence = parsed.get("canonical"), parsed.get("confidence", confidence)
        display = str(canonical) if canonical is not None else cleaned
    else:  # email / url / string -> normalized match string (§2.2)
        parsed = generate_match_keys(raw)
        cleaned_key = casefold_for_match(strip_diacritics_for_match(cleaned))
        canonical = cleaned
        cleaned = cleaned_key  # match layer is accent-stripped + casefolded
        trace += ["strip_diacritics", "casefold_for_match"]
    if parsed.get("error"):
        flags = flags + [parsed["error"]]
        confidence = min(confidence, 0.3)
    match_key = _scalar_match_key(itype, parsed, cleaned)
    return {"raw_value": raw, "source_field": field_name, "raw_type": "string",
            "inferred_type": itype, "cleaned_value": trim_collapse_whitespace(unicode_normalize_nfc(raw or "")),
            "parsed_components": parsed, "canonical_value": canonical, "display_value": display,
            "match_key": match_key, "quality_flags": flags, "confidence": round(float(confidence), 3),
            "transformation_trace": trace, "type_signals": t["signals"],
            "provenance": {"rule_version": SCALAR_RULES_VERSION, "locale": locale}, **BOUNDARY}


_ATOMIC_FNS = (parse_null, parse_boolean, parse_integer, parse_decimal, parse_percent)
_COMPOSITE_FNS = (infer_scalar_type, standardize_scalar)
COMPOSITE_PLANS = {
    "infer_scalar_type": ["parse_null"],
    "standardize_scalar": ["infer_scalar_type", "parse_null", "parse_boolean", "parse_integer",
                           "parse_decimal", "parse_percent", "parse_money", "parse_quantity",
                           "generate_match_keys"]}


def all_cards() -> list[dict[str, Any]]:
    atomic_preamble = ("import re\nfrom decimal import Decimal, InvalidOperation\nfrom typing import Any\n\n"
                       f"NULL_TOKENS = {set(NULL_TOKENS)!r}\nUNKNOWN_TOKENS = {set(UNKNOWN_TOKENS)!r}\n"
                       f"REFERENCE_TOKENS = {set(REFERENCE_TOKENS)!r}\n"
                       f"INVALID_STRUCTURED_TOKENS = {set(INVALID_STRUCTURED_TOKENS)!r}\n"
                       f"BOOL_TRUE_TOKENS = {set(BOOL_TRUE_TOKENS)!r}\n"
                       f"BOOL_FALSE_TOKENS = {set(BOOL_FALSE_TOKENS)!r}\n"
                       f"BOUNDARY = {BOUNDARY!r}\nSCALAR_RULES_VERSION = {SCALAR_RULES_VERSION!r}\n\n")
    # composite cards note their cross-pack deps in the preamble (not claimed sandbox-standalone — they
    # compose sibling packs by design; the atomic cards ARE standalone and are the self-containment proof)
    composite_preamble = (atomic_preamble
                          + "from scripts.quantity_money_primitives import (CURRENCY_SYMBOLS, UNIT_ALIASES, "
                            "parse_money, parse_quantity)\n"
                            "from scripts.string_standardization_primitives import (casefold_for_match, "
                            "generate_match_keys, strip_diacritics_for_match, trim_collapse_whitespace, "
                            "unicode_normalize_nfc)\n"
                          + f"CARD_PREFIX = {CARD_PREFIX!r}\n"
                          + f"ID_FIELD_HINTS = {set(ID_FIELD_HINTS)!r}\n"
                          + f"INTEGER_FIELD_HINTS = {set(INTEGER_FIELD_HINTS)!r}\n"
                          + f"QUANTITY_FIELD_HINTS = {set(QUANTITY_FIELD_HINTS)!r}\n"
                          + f"MONEY_FIELD_HINTS = {set(MONEY_FIELD_HINTS)!r}\n"
                          + f"PERCENT_FIELD_HINTS = {set(PERCENT_FIELD_HINTS)!r}\n"
                          + f"_ROUTER_BOOL_TOKENS = {set(_ROUTER_BOOL_TOKENS)!r}\n"
                          + f"_INT_RE = re.compile({_INT_RE.pattern!r})\n_DEC_RE = re.compile({_DEC_RE.pattern!r})\n"
                          + f"_EMAIL_RE = re.compile({_EMAIL_RE.pattern!r})\n\n"
                          + inspect.getsource(parse_null) + "\n" + inspect.getsource(_scalar_match_key) + "\n")
    cards = []
    for fn in _ATOMIC_FNS + _COMPOSITE_FNS:
        composite = fn in _COMPOSITE_FNS
        title = (fn.__doc__ or fn.__name__).splitlines()[0][:160]
        body = (composite_preamble if composite else atomic_preamble) + inspect.getsource(fn)
        cards.append({"primitive_id": canonical_id(CARD_PREFIX, title, fn.__name__),
                      "impl_name": fn.__name__, "record_type": "scalar_standardization_primitive",
                      "kind": "primitive_group" if composite else "primitive", "title": title,
                      "executable_body": body, "language": "python",
                      "input_edge": "RawObservedScalar",
                      "output_edge": "StandardizedScalar" if composite else "TypedScalarComponent",
                      "blackbox": f"{'Composite' if composite else 'Atomic'} scalar-standardization primitive: "
                                  f"{title} Input: raw field value (+field-name/locale hints). Output: "
                                  f"{'the full standardized-scalar envelope' if composite else 'a typed scalar parse'} "
                                  f"(raw preserved, canonical, match_key, flags, trace).",
                      "plan_steps": COMPOSITE_PLANS.get(fn.__name__, []), "tier": "common", **BOUNDARY})
    return cards


# ── self-test: the owner's §1/§2/§3 worked examples as oracles, mutation-gated ────────────────────────────────
def _self_test() -> int:
    checks: list[tuple[str, bool]] = []
    # §1 worked example: "  5 ft. " in a height field -> quantity.length canonical 1.524 m, match key
    r = standardize_scalar("  5 ft. ", field_name="height")
    checks.append(("§1 envelope: '  5 ft. '/height -> quantity, canonical 1.5240 m, match_key qty:1.5240:m, "
                   "raw preserved",
                   r["inferred_type"] == "quantity" and r["canonical_value"]["value"] == "1.5240"
                   and r["match_key"] == "qty:1.5240:m" and r["raw_value"] == "  5 ft. "))
    # THE identifier distinction (§2.4): same '00123' routes differently by field
    rid = standardize_scalar("00123", field_name="account_id")
    rint = standardize_scalar("00123", field_name="item_count")
    checks.append(("'00123' as account_id -> identifier PRESERVES '00123'; as item_count -> int 123 + "
                   "leading_zeros_dropped flag",
                   rid["inferred_type"] == "identifier" and rid["canonical_value"] == "00123"
                   and rid["match_key"] == "id:00123"
                   and rint["inferred_type"] == "integer" and rint["canonical_value"] == 123
                   and "leading_zeros_dropped" in rint["quality_flags"]))
    checks.append(("accounting negative '(123.45)' -> -123.45 decimal",
                   parse_decimal("(123.45)")["canonical"] == "-123.45"))
    checks.append(("locale separators: '1,234.56' en -> 1234.56; '1.234,56' eu -> 1234.56",
                   parse_decimal("1,234.56", locale="en")["canonical"] == "1234.56"
                   and parse_decimal("1.234,56", locale="eu")["canonical"] == "1234.56"))
    checks.append(("percent kinds kept distinct: '12%' -> 0.12; '50 bps' -> 0.005; '1.5x' -> multiplier 1.5",
                   parse_percent("12%")["canonical_fraction"] == "0.12"
                   and parse_percent("50 bps")["canonical_fraction"] == "0.005"
                   and parse_percent("1.5x")["kind"] == "multiplier"))
    checks.append(("dirty booleans: YES->True/'Yes'; n->False; 'maybe'->None (no coin flip)",
                   parse_boolean("YES")["canonical"] is True and parse_boolean("YES")["display"] == "Yes"
                   and parse_boolean("n")["canonical"] is False
                   and parse_boolean("maybe")["canonical"] is None))
    checks.append(("§3.1 null kinds separated: ''/'-'->null; 'Unknown'->unknown; 'same as above'->ref_prior",
                   parse_null("")["classification"] == "null"
                   and parse_null("-")["classification"] == "null"
                   and parse_null("Unknown")["classification"] == "unknown"
                   and parse_null("same as above")["classification"] == "reference_prior"))
    # router: currency + money-field-hint + quantity-hint + boolean-token + email/url
    checks.append(("router types: '$1.2M'/revenue->money; 'true'->boolean; 'a@b.com'->email; "
                   "'https://x'->url; 'Acme'->string",
                   infer_scalar_type("$1.2M", field_name="revenue")["inferred_type"] == "money"
                   and infer_scalar_type("true")["inferred_type"] == "boolean"
                   and infer_scalar_type("jane@doe.com")["inferred_type"] == "email"
                   and infer_scalar_type("https://x.co")["inferred_type"] == "url"
                   and infer_scalar_type("Acme Logistics")["inferred_type"] == "string"))
    # money envelope match key + string accent-stripped match key
    rm = standardize_scalar("$1.2M", field_name="revenue")
    rs = standardize_scalar("José García")
    checks.append(("money envelope match_key money:USD:1200000.00; string match_key accent-stripped "
                   "'jose garcia'; raw kept",
                   rm["match_key"] == "money:USD:1200000.00"
                   and rs["inferred_type"] == "string" and rs["match_key"] == "str:jose garcia"
                   and rs["raw_value"] == "José García" and rs["canonical_value"] == "José García"))
    # equal-meaning quantities collide on match_key (the whole point of §1)
    checks.append(("'5 ft' and '60 in' produce the SAME match_key (equal-meaning scalars collide)",
                   standardize_scalar("5 ft")["match_key"] == standardize_scalar("60 in")["match_key"]
                   == "qty:1.5240:m"))
    # null envelope
    rn = standardize_scalar("N/A", field_name="middle_name")
    checks.append(("null envelope: 'N/A' -> inferred_type null, canonical None, flag reason, match_key null:*",
                   rn["inferred_type"] == "null" and rn["canonical_value"] is None
                   and rn["match_key"] == "null:null" and "empty_or_placeholder" in rn["quality_flags"]))
    # atomic cards are SELF-CONTAINED (the recipe-layer lesson, proven not asserted)
    card = next(c for c in all_cards() if c["impl_name"] == "parse_decimal")
    scope: dict[str, Any] = {}
    exec(compile(card["executable_body"], "card", "exec"), scope)
    checks.append(("atomic card bodies self-contained: injected parse_decimal runs standalone",
                   scope["parse_decimal"]("1.234,56", locale="eu")["canonical"] == "1234.56"))
    checks.append(("boundary everywhere; composite plan references its atoms",
                   all(c.get("serves_truth") is False for c in all_cards())
                   and "infer_scalar_type" in COMPOSITE_PLANS["standardize_scalar"]))
    failed = [n for n, ok in checks if not ok]
    for n, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print(f"\nPASS - scalar_standardization_primitives: {len(_ATOMIC_FNS)} atomic (null/boolean/integer/"
          f"decimal/percent) + {len(_COMPOSITE_FNS)} composite (type router + the standardized-scalar "
          f"envelope). The base abstraction under lists/arrays/matrices; composes the quantity/money/string "
          f"packs. Self-contained atomic cards. serves_truth=false.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--cards", action="store_true")
    ap.add_argument("--demo", default=None)
    ap.add_argument("--field", default="")
    ap.add_argument("--locale", default="en")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.cards:
        for c in all_cards():
            print(json.dumps(c, sort_keys=True))
        return 0
    if args.demo is not None:
        print(json.dumps(standardize_scalar(args.demo, field_name=args.field, locale=args.locale),
                         indent=2, sort_keys=True, ensure_ascii=False))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
