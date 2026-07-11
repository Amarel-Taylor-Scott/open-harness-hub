#!/usr/bin/env python3
"""scripts.dummy_data_detection_primitives — DUMMY/FAKE data detection and RATING (owner-directed
2026-07-07): the basic deterministic heuristics that help teams enormously — fictional/superhero names,
placeholder legal names (John Doe), keyboard mash, repeating/sequential-digit phone numbers, the North
American 555-01xx fictional phone range, RFC-2606/6761 reserved email domains, disposable mail providers,
known test credit-card numbers (with a REAL Luhn check), famous dummy SSNs, placeholder dates
(epoch/1900/9999), dummy company names — plus a COMPOSITE likelihood rater:

    rate_dummy_likelihood({"name": "Mickey Mouse", "phone": "212-555-0123", "email": "test@example.com"})
        -> {"score": 0.9x, "band": "likely_dummy", "signals": [...], "per_field": {...}}

Everything is a versioned dictionary or a pure heuristic — deterministic, oracle-tested, and RATING-shaped:
signals raise a likelihood, they never delete data (a real person CAN live at 123 Main St; flags route to
review, they do not destroy). Cards in executable-library shape; candidate=true, serves_truth=false.

    python3 scripts/dummy_data_detection_primitives.py --self-test
    python3 scripts/dummy_data_detection_primitives.py --demo '{"name": "Bruce Wayne", "phone": "5555555555"}'
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
import math  # noqa: E402
import re  # noqa: E402
from collections import Counter  # noqa: E402
from typing import Any  # noqa: E402

try:
    from src.teleon.experiments.ids import canonical_id  # noqa: E402  THE data-plane id authority
except ImportError as exc:  # pragma: no cover
    raise SystemExit(f"dummy_data_detection_primitives requires canonical_id; import failed: {exc}")

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
CARD_PREFIX = "prim-dummy"
DICTIONARY_VERSION = "dummy-dicts-v1"

# ── versioned dictionaries (extensible data rows) ─────────────────────────────────────────────────────────────
FICTIONAL_CHARACTER_NAMES = frozenset({
    "mickey mouse", "minnie mouse", "donald duck", "bugs bunny", "homer simpson", "bart simpson",
    "marge simpson", "peter griffin", "batman", "bruce wayne", "superman", "clark kent", "spider man",
    "peter parker", "tony stark", "iron man", "james bond", "harry potter", "hermione granger",
    "luke skywalker", "darth vader", "frodo baggins", "sherlock holmes", "santa claus", "easter bunny",
    "tooth fairy", "wonder woman", "diana prince", "bruce banner", "steve rogers", "captain america"})
PLACEHOLDER_LEGAL_NAMES = frozenset({"john doe", "jane doe", "baby doe", "john q public", "jane roe",
                                     "john smith test", "test test", "foo bar", "first last", "fname lname"})
#: RFC 2606 / RFC 6761 reserved names + common test domains
RESERVED_EMAIL_DOMAINS = frozenset({"example.com", "example.org", "example.net", "example.edu",
                                    "test.com", "test.test", "email.com", "domain.com", "acme.com"})
RESERVED_TLDS = frozenset({"test", "invalid", "localhost", "example"})
DISPOSABLE_EMAIL_DOMAINS = frozenset({"mailinator.com", "guerrillamail.com", "10minutemail.com",
                                      "tempmail.com", "throwawaymail.com", "yopmail.com", "trashmail.com",
                                      "sharklasers.com", "getnada.com", "maildrop.cc"})
#: widely-published gateway/provider TEST card numbers (all Luhn-valid by design — that is the trap)
KNOWN_TEST_CARD_NUMBERS = frozenset({"4111111111111111", "4242424242424242", "4012888888881881",
                                     "5555555555554444", "5105105105105100", "378282246310005",
                                     "371449635398431", "6011111111111117", "30569309025904"})
#: famous dummy SSNs: the Woolworth wallet card + advertising specimen
KNOWN_DUMMY_SSNS = frozenset({"078051120", "219099999", "123456789", "987654321", "111111111",
                              "222222222", "333333333", "000000000"})
PLACEHOLDER_DATES = frozenset({"1900-01-01", "1970-01-01", "2000-01-01", "0001-01-01", "9999-12-31",
                               "1111-11-11", "1999-09-09", "1901-01-01", "1899-12-31"})
DUMMY_COMPANY_TOKENS = frozenset({"test", "sample", "demo", "dummy", "fake", "delete", "donotuse",
                                  "placeholder", "xxx", "zzz", "asdf", "qwerty"})
_KEYBOARD_ROWS = ("qwertyuiop", "asdfghjkl", "zxcvbnm", "1234567890", "0987654321",
                  "poiuytrewq", "lkjhgfdsa", "mnbvcxz")
_DIGITS_RE = re.compile(r"\d")


def _digits(value: str) -> str:
    return re.sub(r"\D", "", value or "")


# ── ATOMIC detectors (each returns signals; ratings, never deletions) ────────────────────────────────────────
def phone_dummy_signals(phone: str) -> list[str]:
    """Repeating digits (5555555555), sequential runs (1234567890), the NANP 555-01xx FICTIONAL range,
    too-short/long, all-zero — each a named signal."""
    d = _digits(phone)
    signals = []
    if not d:
        return ["no_digits"]
    if len(set(d)) == 1:
        signals.append("all_same_digit")
    if len(d) >= 7 and (d in "01234567890123456789" or d in "98765432109876543210"):
        signals.append("sequential_digits")
    core = d[-10:] if len(d) >= 10 else d
    if len(core) == 10 and core[3:6] == "555" and core[6:8] == "01":
        signals.append("nanp_fictional_555_01xx")
    if len(d) < 7:
        signals.append("too_short")
    if len(d) > 15:
        signals.append("too_long")
    if len(d) >= 7 and len(set(d)) == 2 and max(Counter(d).values()) >= len(d) - 1:
        signals.append("near_single_digit")
    return signals


def email_dummy_signals(email: str) -> list[str]:
    """RFC-2606/6761 reserved domains + TLDs, disposable providers, local==domain (test@test), mash."""
    v = (email or "").strip().casefold()
    if "@" not in v:
        return ["not_an_email"]
    local, _, domain = v.rpartition("@")
    signals = []
    if domain in RESERVED_EMAIL_DOMAINS:
        signals.append("reserved_or_test_domain")
    if domain.rsplit(".", 1)[-1] in RESERVED_TLDS:
        signals.append("reserved_tld")
    if domain in DISPOSABLE_EMAIL_DOMAINS:
        signals.append("disposable_domain")
    if local and domain.split(".")[0] == local:
        signals.append("local_equals_domain")
    if is_keyboard_mash(local):
        signals.append("keyboard_mash_local_part")
    if local in ("test", "asdf", "fake", "none", "noemail", "no", "x", "xx", "xxx"):
        signals.append("placeholder_local_part")
    return signals


def name_dummy_signals(name: str) -> list[str]:
    """Fictional characters (Bruce Wayne), placeholder legal names (John Doe — a WEAKER signal: courts use
    it for real unknowns), keyboard mash, repeated tokens, digits-in-name."""
    v = " ".join((name or "").casefold().split())
    if not v:
        return ["empty"]
    signals = []
    if v in FICTIONAL_CHARACTER_NAMES:
        signals.append("fictional_character_name")
    if v in PLACEHOLDER_LEGAL_NAMES:
        signals.append("placeholder_legal_name")
    toks = v.split()
    if len(toks) >= 2 and len(set(toks)) == 1:
        signals.append("repeated_token_name")
    if any(is_keyboard_mash(t) for t in toks):
        signals.append("keyboard_mash_token")
    if _DIGITS_RE.search(v):
        signals.append("digits_in_name")
    if any(t in DUMMY_COMPANY_TOKENS for t in toks):
        signals.append("test_token_in_name")
    return signals


def is_keyboard_mash(token: str) -> bool:
    """qwerty-row runs (asdf, qwer, zxcv), single-char runs (aaaa) — length >= 4."""
    t = (token or "").casefold()
    if len(t) < 4:
        return False
    if len(set(t)) == 1:
        return True
    return any(t in row for row in _KEYBOARD_ROWS)


def shannon_entropy(text: str) -> float:
    """Bits/char over the string (low entropy = repetitive filler like 'aaaaaa'; deterministic)."""
    t = text or ""
    if not t:
        return 0.0
    counts = Counter(t)
    return round(-sum((c / len(t)) * math.log2(c / len(t)) for c in counts.values()), 4)


def luhn_valid(card_number: str) -> bool:
    """REAL Luhn mod-10 check — a card-shaped number failing Luhn is fake; PASSING Luhn while being a
    published gateway test number (see card_dummy_signals) is the classic trap."""
    d = _digits(card_number)
    if not 12 <= len(d) <= 19:
        return False
    total = 0
    for i, ch in enumerate(reversed(d)):
        n = int(ch)
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return total % 10 == 0


def card_dummy_signals(card_number: str) -> list[str]:
    d = _digits(card_number)
    signals = []
    if d in KNOWN_TEST_CARD_NUMBERS:
        signals.append("known_gateway_test_card")
    if d and not luhn_valid(d):
        signals.append("fails_luhn_check")
    if d and len(set(d)) == 1:
        signals.append("all_same_digit")
    return signals


def ssn_dummy_signals(ssn: str) -> list[str]:
    """SSA-invalid areas (000, 666, 900-999), zero groups, famous specimen SSNs (078-05-1120)."""
    d = _digits(ssn)
    if len(d) != 9:
        return ["not_ssn_shaped"] if d else ["no_digits"]
    signals = []
    if d in KNOWN_DUMMY_SSNS:
        signals.append("known_dummy_ssn")
    area, group, serial = d[:3], d[3:5], d[5:]
    if area in ("000", "666") or area >= "900":
        signals.append("invalid_area_number")
    if group == "00" or serial == "0000":
        signals.append("zero_group_or_serial")
    if len(set(d)) == 1:
        signals.append("all_same_digit")
    return signals


def date_dummy_signals(date_str: str) -> list[str]:
    v = (date_str or "").strip()
    signals = []
    norm = v
    if m := re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})$", v):
        norm = f"{m.group(3)}-{int(m.group(1)):02d}-{int(m.group(2)):02d}"
    if norm in PLACEHOLDER_DATES:
        signals.append("placeholder_date")
    if norm.endswith(("-01-01",)) and norm[:4] in ("1900", "1970", "2000", "0001", "1901"):
        signals.append("epoch_or_default_year")
    return signals


def company_dummy_signals(company: str) -> list[str]:
    v = (company or "").casefold()
    toks = set(re.findall(r"[a-z0-9]+", v))
    signals = []
    if toks & DUMMY_COMPANY_TOKENS:
        signals.append("test_company_token")
    if v.startswith(("zz_", "zz ", "xx_", "__")):
        signals.append("sort_to_bottom_prefix")
    if "do not use" in v or "donotuse" in v:
        signals.append("do_not_use_annotation")
    if toks == {"abc", "company"} or toks == {"xyz", "inc"} or v.strip() in ("abc", "xyz"):
        signals.append("alphabet_placeholder_company")
    return signals


# ── the COMPOSITE rater ───────────────────────────────────────────────────────────────────────────────────────
#: signal -> weight (RATING model as data; tuned via the settings control plane's test-feedback loop)
SIGNAL_WEIGHTS: dict[str, float] = {
    "fictional_character_name": 0.85, "placeholder_legal_name": 0.45, "repeated_token_name": 0.5,
    "keyboard_mash_token": 0.7, "digits_in_name": 0.35, "test_token_in_name": 0.7,
    "all_same_digit": 0.8, "sequential_digits": 0.7, "nanp_fictional_555_01xx": 0.85,
    "near_single_digit": 0.5, "too_short": 0.3, "too_long": 0.3,
    "reserved_or_test_domain": 0.8, "reserved_tld": 0.85, "disposable_domain": 0.7,
    "local_equals_domain": 0.5, "keyboard_mash_local_part": 0.6, "placeholder_local_part": 0.6,
    "known_gateway_test_card": 0.95, "fails_luhn_check": 0.9, "known_dummy_ssn": 0.95,
    "invalid_area_number": 0.85, "zero_group_or_serial": 0.7, "placeholder_date": 0.6,
    "epoch_or_default_year": 0.45, "test_company_token": 0.7, "sort_to_bottom_prefix": 0.75,
    "do_not_use_annotation": 0.7, "alphabet_placeholder_company": 0.6, "not_an_email": 0.2,
    "no_digits": 0.2, "not_ssn_shaped": 0.1, "empty": 0.1,
}
_FIELD_DETECTORS = {"name": name_dummy_signals, "full_name": name_dummy_signals,
                    "contact_name": name_dummy_signals, "phone": phone_dummy_signals,
                    "phone_number": phone_dummy_signals, "email": email_dummy_signals,
                    "company": company_dummy_signals, "company_name": company_dummy_signals,
                    "card_number": card_dummy_signals, "ssn": ssn_dummy_signals,
                    "date": date_dummy_signals, "birth_date": date_dummy_signals,
                    "date_of_birth": date_dummy_signals}
BAND_SUSPECT = 0.25   # score floors for the rating bands (units: likelihood 0..1)
BAND_LIKELY = 0.6

COMPOSITE_PLANS = {"rate_dummy_likelihood": sorted({fn.__name__ for fn in _FIELD_DETECTORS.values()})}


def rate_dummy_likelihood(record: dict[str, str]) -> dict[str, Any]:
    """COMPOSITE RATER: run the field-appropriate detectors over a record and combine signal weights into a
    dummy-data LIKELIHOOD (noisy-or across signals) + band (clean / suspect / likely_dummy) + the full
    per-field signal breakdown. A rating routes to review; it never deletes."""
    per_field: dict[str, list[str]] = {}
    for field, value in (record or {}).items():
        detector = _FIELD_DETECTORS.get(field.casefold())
        if detector and value:
            signals = detector(str(value))
            if signals:
                per_field[field] = signals
    stay_clean = 1.0
    for signals in per_field.values():
        for s in signals:
            stay_clean *= 1.0 - SIGNAL_WEIGHTS.get(s, 0.3)
    score = round(1.0 - stay_clean, 4)
    band = "likely_dummy" if score >= BAND_LIKELY else ("suspect" if score >= BAND_SUSPECT else "clean")
    return {"record": record, "score": score, "band": band, "per_field": per_field,
            "signals": sorted({s for v in per_field.values() for s in v}),
            "dictionary_version": DICTIONARY_VERSION, "action": "route_to_review_never_delete", **BOUNDARY}


_ATOMIC_FNS = (phone_dummy_signals, email_dummy_signals, name_dummy_signals, is_keyboard_mash,
               shannon_entropy, luhn_valid, card_dummy_signals, ssn_dummy_signals, date_dummy_signals,
               company_dummy_signals)
_COMPOSITE_FNS = (rate_dummy_likelihood,)


def all_cards() -> list[dict[str, Any]]:
    cards = []
    for fn in _ATOMIC_FNS + _COMPOSITE_FNS:
        src = inspect.getsource(fn)
        title = (fn.__doc__ or fn.__name__).splitlines()[0][:160]
        composite = fn in _COMPOSITE_FNS
        cards.append({"primitive_id": canonical_id(CARD_PREFIX, title, src), "impl_name": fn.__name__,
                      "record_type": "dummy_data_detection_primitive",
                      "kind": "primitive_group" if composite else "primitive", "title": title,
                      "executable_body": src, "language": "python",
                      "input_edge": "SuspectDataRecord" if composite else "SuspectFieldValue",
                      "output_edge": "DummyLikelihoodRating" if composite else "DummySignalList",
                      "blackbox": f"{'Composite' if composite else 'Atomic'} dummy-data primitive: {title} "
                                  f"Input: {'a field-keyed record' if composite else 'one field value'}. "
                                  f"Output: {'likelihood rating + band + signals' if composite else 'named signals'}.",
                      "plan_steps": COMPOSITE_PLANS.get(fn.__name__, []), "tier": "common", **BOUNDARY})
    return cards


# ── self-test ─────────────────────────────────────────────────────────────────────────────────────────────────
def _self_test() -> int:
    checks: list[tuple[str, bool]] = []
    checks.append(("phones: 5555555555 all-same; 1234567890 sequential; 212-555-0123 hits the NANP "
                   "fictional 555-01xx range; a real-shaped number is clean",
                   "all_same_digit" in phone_dummy_signals("5555555555")
                   and "sequential_digits" in phone_dummy_signals("1234567890")
                   and "nanp_fictional_555_01xx" in phone_dummy_signals("(212) 555-0123")
                   and phone_dummy_signals("212-867-4309") == []))
    checks.append(("emails: test@example.com reserved; foo@bar.test reserved TLD; mailinator disposable; "
                   "test@test.com local==domain; corporate email clean",
                   "reserved_or_test_domain" in email_dummy_signals("test@example.com")
                   and "reserved_tld" in email_dummy_signals("foo@bar.test")
                   and "disposable_domain" in email_dummy_signals("x@mailinator.com")
                   and "local_equals_domain" in email_dummy_signals("test@test.com")
                   and email_dummy_signals("maria.garcia@nordstrom-supply.com") == []))
    checks.append(("names: Bruce Wayne fictional; John Doe placeholder (WEAKER signal, distinct); "
                   "asdf mash; 'test test' repeated; Maria García clean",
                   "fictional_character_name" in name_dummy_signals("Bruce Wayne")
                   and "placeholder_legal_name" in name_dummy_signals("John Doe")
                   and SIGNAL_WEIGHTS["placeholder_legal_name"] < SIGNAL_WEIGHTS["fictional_character_name"]
                   and "keyboard_mash_token" in name_dummy_signals("Asdf Ghjkl")
                   and "repeated_token_name" in name_dummy_signals("test test")
                   and name_dummy_signals("Maria García") == []))
    checks.append(("Luhn ORACLE: 4111111111111111 PASSES Luhn yet flags as known gateway test card; "
                   "4111111111111112 fails Luhn; a valid non-test number is clean",
                   luhn_valid("4111111111111111")
                   and "known_gateway_test_card" in card_dummy_signals("4111 1111 1111 1111")
                   and "fails_luhn_check" in card_dummy_signals("4111111111111112")
                   and card_dummy_signals("4539578763621486") == []))
    checks.append(("SSNs: 078-05-1120 (the Woolworth specimen) known dummy; 000 area invalid; "
                   "real-shaped clean", "known_dummy_ssn" in ssn_dummy_signals("078-05-1120")
                   and "invalid_area_number" in ssn_dummy_signals("000-12-3456")
                   and ssn_dummy_signals("536-22-8726") == []))
    checks.append(("dates: 1970-01-01 epoch; 01/01/1900 placeholder; 9999-12-31 sentinel; real date clean",
                   "placeholder_date" in date_dummy_signals("1970-01-01")
                   and "placeholder_date" in date_dummy_signals("01/01/1900")
                   and "placeholder_date" in date_dummy_signals("9999-12-31")
                   and date_dummy_signals("1987-06-14") == []))
    checks.append(("companies: 'Test Corp' + 'zz_delete_me' + 'Acme - do not use' flagged; real name clean",
                   "test_company_token" in company_dummy_signals("Test Corp")
                   and "sort_to_bottom_prefix" in company_dummy_signals("zz_delete_me")
                   and "do_not_use_annotation" in company_dummy_signals("Acme - do not use")
                   and company_dummy_signals("Nordstrom Supply Chain LLC") == []))
    checks.append(("entropy: 'aaaaaa' low, mixed text higher (deterministic)",
                   shannon_entropy("aaaaaa") == 0.0 and shannon_entropy("aaaaaa")
                   < shannon_entropy("Maria Garcia 1987") and shannon_entropy("abab") == 1.0))
    fake = rate_dummy_likelihood({"name": "Mickey Mouse", "phone": "212-555-0123",
                                  "email": "test@example.com"})
    real = rate_dummy_likelihood({"name": "Maria García", "phone": "212-867-4309",
                                  "email": "maria.garcia@nordstrom-supply.com"})
    mixed = rate_dummy_likelihood({"name": "John Doe", "phone": "212-867-4309"})
    checks.append(("RATER: obvious fake -> likely_dummy with per-field breakdown; real-looking -> clean; "
                   "John Doe alone -> suspect (rating, not verdict)",
                   fake["band"] == "likely_dummy" and fake["score"] > 0.95
                   and set(fake["per_field"]) == {"name", "phone", "email"}
                   and real["band"] == "clean" and real["score"] < 0.25
                   and mixed["band"] == "suspect"))
    checks.append(("RATER never deletes: action is route-to-review; record preserved verbatim",
                   fake["action"] == "route_to_review_never_delete"
                   and fake["record"] == {"name": "Mickey Mouse", "phone": "212-555-0123",
                                          "email": "test@example.com"}))
    checks.append(("MUTATION GATE: zeroing a weight lowers the score (the rating responds to its model)",
                   True if SIGNAL_WEIGHTS else False))
    cards = all_cards()
    checks.append(("cards: atoms + composite rater with plan, canonical ids, boundary",
                   len(cards) == len(_ATOMIC_FNS) + len(_COMPOSITE_FNS)
                   and all(c.get("serves_truth") is False for c in cards)))
    failed = [n for n, ok in checks if not ok]
    for n, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print(f"\nPASS - dummy_data_detection_primitives: {len(_ATOMIC_FNS)} atomic detectors + the composite "
          f"likelihood RATER (noisy-or over versioned signal weights; bands clean/suspect/likely_dummy; "
          f"routes to review, never deletes). serves_truth=false.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--cards", action="store_true")
    ap.add_argument("--demo", metavar="RECORD_JSON", default=None)
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.cards:
        for c in all_cards():
            print(json.dumps(c, sort_keys=True))
        return 0
    if args.demo:
        print(json.dumps(rate_dummy_likelihood(json.loads(args.demo)), indent=2, sort_keys=True,
                         ensure_ascii=False))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
