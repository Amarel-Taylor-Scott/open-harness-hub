#!/usr/bin/env python3
"""scripts.quantity_money_primitives — the owner platform spec's "5 feet" and "$1.2M" problems as
EXECUTABLE primitives (2026-07-07): quantities with unit aliases -> canonical SI, imperial compound heights
(5'10"), ranges/approximations/tolerances DETECTED (never collapsed to one number silently), and money with
currency inference, accounting negatives, and abbreviated amounts — every parse returning the platform
shape: raw preserved, parsed components, canonical value, display value, confidence, trace.

Laws encoded: raw != cleaned != parsed != canonical != display (all kept); Decimal arithmetic (never binary
floats for money/quantities); currency conversion is NOT performed here (that needs a dated FX rate +
provider — an enrichment call, flagged as such); unit alias tables are versioned data mapping to UCUM-style
codes. candidate=true, serves_truth=false.

    python3 scripts/quantity_money_primitives.py --self-test
    python3 scripts/quantity_money_primitives.py --demo-quantity "5'10\""
    python3 scripts/quantity_money_primitives.py --demo-money "(1,234.50)"
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
from decimal import Decimal  # noqa: E402
from typing import Any  # noqa: E402

try:
    from src.teleon.experiments.ids import canonical_id  # noqa: E402
except ImportError as exc:  # pragma: no cover
    raise SystemExit(f"quantity_money_primitives requires canonical_id; import failed: {exc}")

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
CARD_PREFIX = "prim-qtymoney"
DICTIONARY_VERSION = "qtymoney-dicts-v1"

# ── versioned unit alias tables: alias -> (canonical unit, ucum-style code, dimension, factor-to-SI-base) ────
UNIT_ALIASES: dict[str, tuple[str, str, str, str]] = {
    # length -> meter
    "ft": ("foot", "[ft_i]", "length", "0.3048"), "foot": ("foot", "[ft_i]", "length", "0.3048"),
    "feet": ("foot", "[ft_i]", "length", "0.3048"), "'": ("foot", "[ft_i]", "length", "0.3048"),
    "′": ("foot", "[ft_i]", "length", "0.3048"),
    "in": ("inch", "[in_i]", "length", "0.0254"), "inch": ("inch", "[in_i]", "length", "0.0254"),
    "inches": ("inch", "[in_i]", "length", "0.0254"), '"': ("inch", "[in_i]", "length", "0.0254"),
    "″": ("inch", "[in_i]", "length", "0.0254"),
    "yd": ("yard", "[yd_i]", "length", "0.9144"), "yard": ("yard", "[yd_i]", "length", "0.9144"),
    "yards": ("yard", "[yd_i]", "length", "0.9144"),
    "mi": ("mile", "[mi_i]", "length", "1609.344"), "mile": ("mile", "[mi_i]", "length", "1609.344"),
    "miles": ("mile", "[mi_i]", "length", "1609.344"),
    "m": ("meter", "m", "length", "1"), "meter": ("meter", "m", "length", "1"),
    "metre": ("meter", "m", "length", "1"), "meters": ("meter", "m", "length", "1"),
    "cm": ("centimeter", "cm", "length", "0.01"), "centimeter": ("centimeter", "cm", "length", "0.01"),
    "mm": ("millimeter", "mm", "length", "0.001"), "km": ("kilometer", "km", "length", "1000"),
    # mass -> kilogram
    "lb": ("pound", "[lb_av]", "mass", "0.45359237"), "lbs": ("pound", "[lb_av]", "mass", "0.45359237"),
    "pound": ("pound", "[lb_av]", "mass", "0.45359237"), "pounds": ("pound", "[lb_av]", "mass", "0.45359237"),
    "oz": ("ounce", "[oz_av]", "mass", "0.028349523125"), "ounce": ("ounce", "[oz_av]", "mass", "0.028349523125"),
    "kg": ("kilogram", "kg", "mass", "1"), "kilogram": ("kilogram", "kg", "mass", "1"),
    "g": ("gram", "g", "mass", "0.001"), "gram": ("gram", "g", "mass", "0.001"),
    # volume -> liter
    "gal": ("gallon", "[gal_us]", "volume", "3.785411784"), "gallon": ("gallon", "[gal_us]", "volume", "3.785411784"),
    "gallons": ("gallon", "[gal_us]", "volume", "3.785411784"),
    "l": ("liter", "L", "volume", "1"), "liter": ("liter", "L", "volume", "1"),
    "ml": ("milliliter", "mL", "volume", "0.001"),
}
#: SI display unit per dimension
SI_UNIT = {"length": "m", "mass": "kg", "volume": "L"}
#: ISO-4217 subset: symbol/word -> code; code -> minor units (extensible data)
CURRENCY_SYMBOLS = {"$": "USD", "us$": "USD", "€": "EUR", "£": "GBP", "¥": "JPY", "dollars": "USD",
                    "dollar": "USD", "euros": "EUR", "euro": "EUR", "pounds sterling": "GBP", "usd": "USD",
                    "eur": "EUR", "gbp": "GBP", "jpy": "JPY", "cad": "CAD", "aud": "AUD", "chf": "CHF"}
CURRENCY_MINOR_UNITS = {"USD": 2, "EUR": 2, "GBP": 2, "JPY": 0, "CAD": 2, "AUD": 2, "CHF": 2}
_MAGNITUDE_SUFFIX = {"k": "1000", "m": "1000000", "mm": "1000000", "b": "1000000000", "bn": "1000000000"}
_NUM_RE = r"\d+(?:,\d{3})*(?:\.\d+)?|\.\d+"
_IMPERIAL_HEIGHT_RE = re.compile(r"^\s*(\d+)\s*['′]\s*(?:(\d+(?:\.\d+)?)\s*[\"″]?)?\s*$")
_QTY_RE = re.compile(rf"^\s*(~|about |approx\.?|approximately |<|>|<=|>=)?\s*({_NUM_RE})\s*"
                     rf"(?:(-|–|to)\s*({_NUM_RE})\s*)?([a-zA-Z'\"″′]+\.?)?\s*$")
_MONEY_RE = re.compile(rf"^\s*(\()?\s*(-)?\s*([^\d\s(]*?)\s*({_NUM_RE})\s*([kKmMbB]{{1,2}}n?)?\s*"
                       rf"([a-zA-Z]{{3}}|dollars?|euros?)?\s*(\))?\s*$")


def _dec(s: str) -> Decimal:
    return Decimal(s.replace(",", ""))


# ── ATOMIC primitives ─────────────────────────────────────────────────────────────────────────────────────────
def lookup_unit_alias(unit_raw: str) -> dict[str, Any]:
    """Alias -> (canonical unit, UCUM-style code, dimension, SI factor); unknown -> empty dict."""
    key = (unit_raw or "").strip().rstrip(".").casefold()
    key = key if key in UNIT_ALIASES else (unit_raw or "").strip()
    hit = UNIT_ALIASES.get(key)
    if not hit:
        return {}
    canonical, ucum, dimension, factor = hit
    return {"unit_canonical": canonical, "unit_code_ucum": ucum, "dimension": dimension,
            "si_factor": factor, "si_unit": SI_UNIT[dimension]}


def parse_imperial_height(raw: str) -> dict[str, Any]:
    """5'10\" / 5′ / 5' 6 -> compound feet+inches components + canonical meters (Decimal)."""
    m = _IMPERIAL_HEIGHT_RE.match(raw or "")
    if not m:
        return {}
    feet = Decimal(m.group(1))
    inches = Decimal(m.group(2)) if m.group(2) else Decimal(0)
    meters = feet * Decimal("0.3048") + inches * Decimal("0.0254")
    components = [{"value": str(feet), "unit": "foot"}]
    if m.group(2):
        components.append({"value": str(inches), "unit": "inch"})
    return {"components": components, "canonical": {"value": str(meters.quantize(Decimal('0.0001'))),
                                                    "unit": "m"},
            "display": f"{feet} ft" + (f" {inches} in" if m.group(2) else "")}


def parse_quantity(raw: str) -> dict[str, Any]:
    """The '5 ft' problem: number + unit alias (+ range/approx/inequality markers DETECTED, never silently
    collapsed) -> parsed components + canonical SI value + trace. Compound imperial heights delegate."""
    trace = ["trim"]
    v = (raw or "").strip()
    imperial = parse_imperial_height(v)
    if imperial:
        return {"raw_value": raw, "inferred_type": "quantity.length", **imperial,
                "qualifiers": {}, "confidence": 0.98,
                "transformation_trace": trace + ["parse_imperial_height", "convert_to_si"], **BOUNDARY}
    m = _QTY_RE.match(v)
    if not m:
        return {"raw_value": raw, "error": "not_a_quantity", "confidence": 0.0, **BOUNDARY}
    approx_raw, num1, range_sep, num2, unit_raw = m.groups()
    qualifiers: dict[str, Any] = {}
    if approx_raw:
        qualifiers["approximate" if approx_raw.strip().rstrip(".") in
                   ("~", "about", "approx", "approximately") else "inequality"] = approx_raw.strip()
        trace.append("detect_approximation_or_inequality")
    unit = lookup_unit_alias(unit_raw or "")
    if unit_raw and not unit:
        return {"raw_value": raw, "error": f"unknown_unit:{unit_raw}", "confidence": 0.2, **BOUNDARY}
    trace += ["extract_number", "map_unit_alias"] if unit else ["extract_number"]
    def canon(n: str) -> dict[str, str]:
        if not unit:
            return {"value": str(_dec(n)), "unit": ""}
        return {"value": str((_dec(n) * Decimal(unit["si_factor"])).quantize(Decimal("0.0001"))),
                "unit": unit["si_unit"]}
    if num2:  # a RANGE stays a range
        qualifiers["range"] = True
        trace.append("detect_range")
        return {"raw_value": raw, "inferred_type": f"quantity.range.{unit.get('dimension', 'scalar')}",
                "parsed_value": {"low": str(_dec(num1)), "high": str(_dec(num2)),
                                 "unit_raw": unit_raw or "", **unit},
                "canonical_value": {"low": canon(num1), "high": canon(num2)},
                "display_value": v, "qualifiers": qualifiers, "confidence": 0.93,
                "transformation_trace": trace + (["convert_to_si"] if unit else []), **BOUNDARY}
    return {"raw_value": raw, "inferred_type": f"quantity.{unit.get('dimension', 'scalar')}",
            "parsed_value": {"magnitude": str(_dec(num1)), "unit_raw": unit_raw or "", **unit},
            "canonical_value": canon(num1), "display_value": v, "qualifiers": qualifiers,
            "confidence": 0.97 if unit else 0.7,
            "transformation_trace": trace + (["convert_to_si"] if unit else []), **BOUNDARY}


def parse_money(raw: str) -> dict[str, Any]:
    """The '$1.2M' problem: symbol/code/word currency, accounting negatives (parentheses), abbreviated
    magnitudes (1.2M), Decimal amounts. Conversion NOT performed (needs dated FX — an enrichment call)."""
    m = _MONEY_RE.match((raw or "").strip())
    if not m:
        return {"raw_value": raw, "error": "not_money", "confidence": 0.0, **BOUNDARY}
    paren_open, minus, sym, num, magnitude, code_word, paren_close = m.groups()
    trace = ["trim", "extract_currency", "parse_decimal_amount"]
    currency = None
    inferred = False
    for probe in (sym, code_word):
        if probe and probe.strip().casefold() in CURRENCY_SYMBOLS:
            currency = CURRENCY_SYMBOLS[probe.strip().casefold()]
            break
    if currency is None and (sym or "").strip():
        return {"raw_value": raw, "error": f"unknown_currency_symbol:{sym}", "confidence": 0.2, **BOUNDARY}
    if currency is None:
        currency, inferred = "USD", True  # locale default; FLAGGED, never silent
        trace.append("infer_currency_from_locale")
    amount = _dec(num)
    if magnitude:
        factor = _MAGNITUDE_SUFFIX.get(magnitude.casefold())
        if factor:
            amount *= Decimal(factor)
            trace.append("parse_abbreviated_amount")
    negative = bool(minus) or (bool(paren_open) and bool(paren_close))
    if paren_open and paren_close:
        trace.append("parse_accounting_negative")
    if negative:
        amount = -amount
    minor = CURRENCY_MINOR_UNITS.get(currency, 2)
    amount = amount.quantize(Decimal(1).scaleb(-minor))
    return {"raw_value": raw, "inferred_type": "money",
            "parsed_value": {"amount": str(amount), "currency": currency, "minor_units": minor,
                             "currency_inferred": inferred, "negative": negative},
            "canonical_value": {"amount": str(amount), "currency": currency},
            "display_value": (raw or "").strip(), "confidence": 0.9 if not inferred else 0.75,
            "issues": (["currency_inferred"] if inferred else []),
            "fx_conversion": "not_performed_requires_dated_rate_provider",
            "transformation_trace": trace, **BOUNDARY}


def money_minor_units(amount: str, currency: str) -> int:
    """Major units -> integer minor units (cents) via the ISO-4217 minor-unit table (JPY: 0 decimals)."""
    minor = CURRENCY_MINOR_UNITS.get(currency.upper(), 2)
    return int((Decimal(amount) * (Decimal(10) ** minor)).to_integral_value())


def conformity_check(value: str, standard: str) -> dict[str, Any]:
    """Reference-conformity primitive: does the value belong to the named code list (iso4217_currency /
    unit_alias / dimension)? Returns the platform conformity-record shape."""
    checks = {"iso4217_currency": lambda v: v.upper() in CURRENCY_MINOR_UNITS,
              "unit_alias": lambda v: bool(lookup_unit_alias(v)),
              "length_dimension": lambda v: lookup_unit_alias(v).get("dimension") == "length"}
    fn = checks.get(standard)
    if fn is None:
        return {"conforms": False, "error": f"unknown_standard:{standard}", **BOUNDARY}
    ok = bool(fn(value))
    return {"field_value": value, "expected_standard": standard, "conforms": ok,
            "confidence": 0.99 if ok else 0.9, "rule_version": DICTIONARY_VERSION, **BOUNDARY}


_ATOMIC_FNS = (lookup_unit_alias, parse_imperial_height, money_minor_units, conformity_check)
_COMPOSITE_FNS = (parse_quantity, parse_money)
COMPOSITE_PLANS = {"parse_quantity": ["lookup_unit_alias", "parse_imperial_height"],
                   "parse_money": ["money_minor_units", "conformity_check"]}


def all_cards() -> list[dict[str, Any]]:
    preamble = ("import re\nfrom decimal import Decimal\nfrom typing import Any\n\n"
                f"UNIT_ALIASES = {UNIT_ALIASES!r}\nSI_UNIT = {SI_UNIT!r}\n"
                f"CURRENCY_SYMBOLS = {CURRENCY_SYMBOLS!r}\nCURRENCY_MINOR_UNITS = {CURRENCY_MINOR_UNITS!r}\n"
                f"_MAGNITUDE_SUFFIX = {_MAGNITUDE_SUFFIX!r}\n"
                f"_NUM_RE = {_NUM_RE!r}\n"
                f"_IMPERIAL_HEIGHT_RE = re.compile({_IMPERIAL_HEIGHT_RE.pattern!r})\n"
                f"_QTY_RE = re.compile({_QTY_RE.pattern!r})\n"
                f"_MONEY_RE = re.compile({_MONEY_RE.pattern!r})\n"
                f"BOUNDARY = {BOUNDARY!r}\n"
                f"DICTIONARY_VERSION = {DICTIONARY_VERSION!r}\n\n"
                + inspect.getsource(_dec) + "\n")
    deps = {"parse_quantity": (lookup_unit_alias, parse_imperial_height),
            "parse_money": (), "conformity_check": (lookup_unit_alias,)}
    cards = []
    for fn in _ATOMIC_FNS + _COMPOSITE_FNS:
        dep_src = "".join(inspect.getsource(d) + "\n" for d in deps.get(fn.__name__, ()))
        title = (fn.__doc__ or fn.__name__).splitlines()[0][:160]
        composite = fn in _COMPOSITE_FNS
        cards.append({"primitive_id": canonical_id(CARD_PREFIX, title, fn.__name__),
                      "impl_name": fn.__name__, "record_type": "quantity_money_primitive",
                      "kind": "primitive_group" if composite else "primitive", "title": title,
                      "executable_body": preamble + dep_src + inspect.getsource(fn), "language": "python",
                      "input_edge": "DirtyObservedValue", "output_edge": "TypedCanonicalValue",
                      "blackbox": f"{'Composite' if composite else 'Atomic'} quantity/money primitive: "
                                  f"{title} Input: raw field string. Output: platform-shaped typed value "
                                  f"(raw preserved, canonical SI/ISO-4217, trace).",
                      "plan_steps": COMPOSITE_PLANS.get(fn.__name__, []), "tier": "common", **BOUNDARY})
    return cards


# ── self-test (the owner spec's hard cases as oracles) ───────────────────────────────────────────────────────
def _self_test() -> int:
    checks: list[tuple[str, bool]] = []
    q = parse_quantity("5 ft.")
    checks.append(("'5 ft.' -> foot/[ft_i]/length -> canonical 1.524 m with trace (the spec's worked example)",
                   q["parsed_value"]["unit_canonical"] == "foot"
                   and q["parsed_value"]["unit_code_ucum"] == "[ft_i]"
                   and q["canonical_value"] == {"value": "1.5240", "unit": "m"}
                   and "map_unit_alias" in q["transformation_trace"]
                   and q["raw_value"] == "5 ft."))
    checks.append(("alias breadth: feet/'/′ all -> foot; 60 in == 5 ft in SI",
                   parse_quantity("5 feet")["canonical_value"]["value"] == "1.5240"
                   and parse_quantity("60 in")["canonical_value"]["value"] == "1.5240"))
    h = parse_quantity("5'10\"")
    checks.append(("imperial compound 5'10\" -> [5 foot, 10 inch] components + 1.778 m",
                   h["components"] == [{"value": "5", "unit": "foot"}, {"value": "10", "unit": "inch"}]
                   and h["canonical"]["value"] == "1.7780"))
    r = parse_quantity("5-10 ft")
    checks.append(("RANGE stays a range (never silently collapsed): low 1.524 high 3.048",
                   r["qualifiers"].get("range") and r["canonical_value"]["low"]["value"] == "1.5240"
                   and r["canonical_value"]["high"]["value"] == "3.0480"))
    a = parse_quantity("~5 ft")
    checks.append(("approximation marker DETECTED and kept as qualifier",
                   a["qualifiers"].get("approximate") == "~" and a["canonical_value"]["value"] == "1.5240"))
    checks.append(("mass + volume dimensions convert (2.2 lb -> ~0.9979 kg; 1 gal -> 3.7854 L)",
                   parse_quantity("2.2 lbs")["canonical_value"] == {"value": "0.9979", "unit": "kg"}
                   and parse_quantity("1 gallon")["canonical_value"] == {"value": "3.7854", "unit": "L"}))
    checks.append(("unknown unit rejects with the unit named (no silent guess)",
                   parse_quantity("5 flibbers")["error"] == "unknown_unit:flibbers"))
    mny = parse_money("$1,234.50")
    checks.append(("'$1,234.50' -> USD Decimal 1234.50, minor units 2",
                   mny["parsed_value"]["amount"] == "1234.50" and mny["parsed_value"]["currency"] == "USD"
                   and not mny["parsed_value"]["currency_inferred"]))
    checks.append(("accounting negative '(1,234.50)' -> -1234.50, currency inferred + FLAGGED",
                   parse_money("(1,234.50)")["parsed_value"]["amount"] == "-1234.50"
                   and "currency_inferred" in parse_money("(1,234.50)")["issues"]))
    big = parse_money("$1.2M")
    checks.append(("'$1.2M' -> 1200000.00 USD (abbreviated magnitude)",
                   big["parsed_value"]["amount"] == "1200000.00"))
    checks.append(("word + code currencies: '100 dollars' + 'EUR 100' resolve; JPY has 0 minor units",
                   parse_money("100 dollars")["parsed_value"]["currency"] == "USD"
                   and parse_money("100 EUR")["parsed_value"]["currency"] == "EUR"
                   and money_minor_units("100", "JPY") == 100
                   and money_minor_units("1.50", "USD") == 150))
    checks.append(("FX conversion is explicitly NOT performed (needs dated rate provider)",
                   parse_money("$5")["fx_conversion"] == "not_performed_requires_dated_rate_provider"))
    checks.append(("conformity primitive: USD conforms to iso4217; 'flibber' does not conform to unit_alias",
                   conformity_check("USD", "iso4217_currency")["conforms"]
                   and not conformity_check("flibber", "unit_alias")["conforms"]))
    # cards are SELF-CONTAINED (the recipe-layer lesson applied from day one here)
    card = next(c for c in all_cards() if c["impl_name"] == "parse_quantity")
    scope: dict[str, Any] = {}
    exec(compile(card["executable_body"], "card", "exec"), scope)
    checks.append(("card bodies are self-contained: injected parse_quantity runs standalone",
                   scope["parse_quantity"]("5 ft")["canonical_value"]["value"] == "1.5240"))
    checks.append(("boundary + raw preserved everywhere",
                   all(c.get("serves_truth") is False for c in all_cards())
                   and parse_quantity(" 5 ft ")["raw_value"] == " 5 ft "))
    failed = [n for n, ok in checks if not ok]
    for n, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print("\nPASS - quantity_money_primitives: unit aliases -> UCUM codes -> Decimal SI conversion; imperial"
          " compounds; ranges/approximations kept as structure; money with inferred-currency flags and no "
          "silent FX. Self-contained cards. serves_truth=false.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--cards", action="store_true")
    ap.add_argument("--demo-quantity", default=None)
    ap.add_argument("--demo-money", default=None)
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.cards:
        for c in all_cards():
            print(json.dumps(c, sort_keys=True))
        return 0
    if args.demo_quantity:
        print(json.dumps(parse_quantity(args.demo_quantity), indent=2, sort_keys=True))
        return 0
    if args.demo_money:
        print(json.dumps(parse_money(args.demo_money), indent=2, sort_keys=True))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
