#!/usr/bin/env python3
"""scripts.string_standardization_primitives — the owner's data-loading + string-standardization playbook
(2026-07-07: addresses, person names, company names) built out as EXECUTABLE PRIMITIVES, two ways:

  * ATOMIC primitives — pure deterministic functions, one concern each (whitespace, Unicode NFC, diacritic
    strip, punctuation, casefold, tokenize, dictionary-driven suffix/unit/directional/state/legal-suffix/
    honorific maps, token-sorted / n-gram / phonetic / blocking match keys) — every one oracle-tested;
  * COMPOSITE primitives — primitives MADE OF primitives: standardize_company_name / standardize_person_name
    / standardize_us_address / generate_match_keys are declared PLAN chains over the atoms (the same
    ``A -> B -> C`` step format the deterministic builder in real_buildout_ab_harness consumes), validated
    end-to-end on the playbook's worked example.

Playbook laws encoded here: NEVER overwrite the raw string (every composite returns raw + cleaned + parsed
+ display + match keys side by side); display values preserve meaning (diacritics, suffixes) while MATCH
keys may be aggressive; rule tables are versioned DATA rows (the standardization_dictionary concept), never
hardcoded scatter. Cards are emitted in the executable-library shape (ids via the canonical_id authority) so
the orchestrated/planned lanes can compose them. candidate=true, serves_truth=false.

    python3 scripts/string_standardization_primitives.py --self-test
    python3 scripts/string_standardization_primitives.py --cards | head
    python3 scripts/string_standardization_primitives.py --demo '{"full_name": "  Dr. Jos\\u00e9 A. Garc\\u00eda-L\\u00f3pez Jr. "}'
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
import unicodedata  # noqa: E402
from typing import Any  # noqa: E402

try:
    from src.teleon.experiments.ids import canonical_id  # noqa: E402  THE data-plane id authority
except ImportError as exc:  # pragma: no cover
    raise SystemExit(f"string_standardization_primitives requires canonical_id; import failed: {exc}")

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
CARD_PREFIX = "prim-strstd"
DICTIONARY_VERSION = "strstd-dicts-v1"  # version lives in metadata, never in names

# ── rule tables (the standardization_dictionary concept: versioned DATA, action encoded per table) ───────────
#: USPS-Pub-28-style street suffixes (representative subset; action=replace). Full table = a data top-up.
ADDRESS_SUFFIX_MAP = {"street": "ST", "st": "ST", "avenue": "AVE", "ave": "AVE", "boulevard": "BLVD",
                      "blvd": "BLVD", "road": "RD", "rd": "RD", "drive": "DR", "dr": "DR", "lane": "LN",
                      "ln": "LN", "court": "CT", "ct": "CT", "place": "PL", "pl": "PL", "circle": "CIR",
                      "highway": "HWY", "hwy": "HWY", "parkway": "PKWY", "pkwy": "PKWY", "terrace": "TER",
                      "way": "WAY", "square": "SQ", "sq": "SQ"}
UNIT_TYPE_MAP = {"apartment": "APT", "apt": "APT", "suite": "STE", "ste": "STE", "unit": "UNIT",
                 "floor": "FL", "fl": "FL", "building": "BLDG", "bldg": "BLDG", "room": "RM", "rm": "RM"}
DIRECTIONAL_MAP = {"north": "N", "south": "S", "east": "E", "west": "W", "northeast": "NE",
                   "northwest": "NW", "southeast": "SE", "southwest": "SW", "n": "N", "s": "S", "e": "E",
                   "w": "W", "ne": "NE", "nw": "NW", "se": "SE", "sw": "SW"}
#: representative subset of US state/territory names -> USPS codes (full table = a data top-up)
STATE_CODE_MAP = {"new york": "NY", "california": "CA", "texas": "TX", "florida": "FL", "illinois": "IL",
                  "pennsylvania": "PA", "ohio": "OH", "georgia": "GA", "washington": "WA",
                  "massachusetts": "MA", "new jersey": "NJ", "virginia": "VA", "michigan": "MI",
                  "north carolina": "NC", "arizona": "AZ", "colorado": "CO", "puerto rico": "PR"}
#: corporate legal suffixes (action=preserve_for_display, remove_for_match)
LEGAL_SUFFIXES = frozenset("inc incorporated llc ltd limited corp corporation co company gmbh sa srl plc "
                           "llp lp pllc ag bv nv oy ab as kk pty".split())
#: honorifics + generational suffixes (action=preserve_for_display, remove_for_match)
HONORIFIC_PREFIXES = frozenset("mr mrs ms miss dr prof rev hon sir dame mx".split())
HONORIFIC_SUFFIXES = frozenset("jr sr ii iii iv v md phd esq dds jd".split())
#: name particles kept lowercase inside display names, kept in match keys
NAME_PARTICLES = frozenset("de del della der den van von la le al bin ibn da dos".split())
COMPANY_LOW_SIGNAL = frozenset({"the"})

_WS_RE = re.compile(r"\s+")
_ZW_RE = re.compile("[​‌‍﻿]")
_PUNCT_TO_SPACE_RE = re.compile(r"[,;:/\\|]+")
_APOSTROPHES = {"’": "'", "‘": "'", "‛": "'", "ʼ": "'"}


# ── ATOMIC primitives (pure; one concern each; the executable_body of each card is its own source) ───────────
def trim_collapse_whitespace(text: str) -> str:
    """Trim ends, collapse internal runs (incl. tabs/newlines/NBSP/zero-width) to single spaces."""
    return _WS_RE.sub(" ", _ZW_RE.sub("", (text or "").replace(" ", " "))).strip()


def unicode_normalize_nfc(text: str) -> str:
    """Unicode NFC (UAX #15): equivalent sequences get one representation; display-safe, lossless."""
    return unicodedata.normalize("NFC", text or "")


def strip_diacritics_for_match(text: str) -> str:
    """MATCH-KEY ONLY (lossy): NFD-decompose and drop combining marks — José -> Jose. Never for display."""
    return "".join(ch for ch in unicodedata.normalize("NFD", text or "")
                   if not unicodedata.combining(ch))


def normalize_apostrophes(text: str) -> str:
    """Curly/typographic apostrophes -> straight ASCII apostrophe (O’Connor -> O'Connor)."""
    return "".join(_APOSTROPHES.get(ch, ch) for ch in (text or ""))


def casefold_for_match(text: str) -> str:
    """Aggressive case-insensitive form for MATCH keys (casefold beats lower for ß etc.)."""
    return (text or "").casefold()


def normalize_punctuation_for_match(text: str) -> str:
    """MATCH-KEY ONLY: dotted acronyms collapse (A.C.M.E.->ACME), separators->space, rest stripped."""
    t = normalize_apostrophes(text or "")
    t = re.sub(r"\.(?=[A-Za-z]\.)", "", t).replace(".", " ")
    t = _PUNCT_TO_SPACE_RE.sub(" ", t)
    t = re.sub(r"[^\w\s'&-]", " ", t)
    return trim_collapse_whitespace(t)


def normalize_ampersand(text: str) -> str:
    """'&' -> ' and ' (match form; AT&T -> at and t after casefold)."""
    return trim_collapse_whitespace((text or "").replace("&", " and "))


def tokenize_alnum(text: str) -> list[str]:
    """Lower alnum tokens (apostrophes/hyphens split): the shared basis for keys and dedupe."""
    return re.findall(r"[a-z0-9]+", casefold_for_match(strip_diacritics_for_match(text or "")))


def remove_tokens(tokens: list[str], drop: frozenset[str] | set[str]) -> list[str]:
    """Dictionary-driven token removal (low-signal/legal/honorific) — MATCH keys only, never display."""
    return [t for t in tokens if t not in drop]


def map_tokens(tokens: list[str], mapping: dict[str, str]) -> list[str]:
    """Dictionary-driven token replacement (suffix/unit/directional/state maps)."""
    return [mapping.get(t, t) for t in tokens]


def token_sorted_key(tokens: list[str]) -> str:
    """Order-insensitive match key: sorted unique tokens joined ('Smith, John' == 'John Smith')."""
    return " ".join(sorted(set(tokens)))


def ngram_key(text: str, n: int = 3) -> str:
    """Character n-gram fingerprint of the casefolded string (typo-tolerant candidate key)."""
    s = re.sub(r"\W+", "", casefold_for_match(strip_diacritics_for_match(text or "")))
    return " ".join(sorted({s[i:i + n] for i in range(max(len(s) - n + 1, 0))})) if s else ""


def soundex_key(word: str) -> str:
    """Classic Soundex (deterministic, language-biased — a phonetic-key zoo row, not the only one)."""
    w = re.sub(r"[^a-z]", "", casefold_for_match(strip_diacritics_for_match(word or "")))
    if not w:
        return ""
    codes = {"b": "1", "f": "1", "p": "1", "v": "1", "c": "2", "g": "2", "j": "2", "k": "2", "q": "2",
             "s": "2", "x": "2", "z": "2", "d": "3", "t": "3", "l": "4", "m": "5", "n": "5", "r": "6"}
    out, prev = w[0].upper(), codes.get(w[0], "")
    for ch in w[1:]:
        code = codes.get(ch, "")
        if code and code != prev:
            out += code
        if ch not in "hw":
            prev = code
    return (out + "000")[:4]


def blocking_key(tokens: list[str], parts: int = 2) -> str:
    """Pipe-joined first significant tokens — the cheap candidate-group key for dedupe blocking."""
    return "|".join(tokens[:parts])


def extract_legal_suffix(tokens: list[str]) -> tuple[list[str], str]:
    """Split trailing corporate legal suffix off a company token list -> (core tokens, suffix or '')."""
    core = list(tokens)
    suffix = ""
    while core and core[-1] in LEGAL_SUFFIXES:
        suffix = (core.pop() + (" " + suffix if suffix else "")).strip()
    return core, suffix.upper()


def normalize_postal_code_us(text: str) -> str:
    """US ZIP / ZIP+4: keep digits, format 5 or 5-4; empty when not plausibly a ZIP."""
    digits = re.sub(r"\D", "", text or "")
    if len(digits) == 5:
        return digits
    if len(digits) == 9:
        return f"{digits[:5]}-{digits[5:]}"
    return ""


# ── COMPOSITE primitives — primitives MADE OF primitives (each declares its atom PLAN) ───────────────────────
#: composite name -> the ordered atom chain it composes (the planned-lane dialect: A -> B -> C)
COMPOSITE_PLANS: dict[str, list[str]] = {
    "standardize_company_name": [
        "trim_collapse_whitespace", "unicode_normalize_nfc", "normalize_apostrophes",
        "normalize_punctuation_for_match", "normalize_ampersand", "tokenize_alnum",
        "extract_legal_suffix", "remove_tokens", "token_sorted_key", "blocking_key", "soundex_key"],
    "standardize_person_name": [
        "trim_collapse_whitespace", "unicode_normalize_nfc", "normalize_apostrophes", "tokenize_alnum",
        "remove_tokens", "strip_diacritics_for_match", "token_sorted_key", "soundex_key", "blocking_key"],
    "standardize_us_address": [
        "trim_collapse_whitespace", "unicode_normalize_nfc", "normalize_punctuation_for_match",
        "tokenize_alnum", "map_tokens", "normalize_postal_code_us", "blocking_key"],
    "generate_match_keys": [
        "tokenize_alnum", "token_sorted_key", "ngram_key", "soundex_key", "blocking_key"],
}


def standardize_company_name(raw: str) -> dict[str, Any]:
    """COMPOSITE: raw company string -> raw + display + legal suffix + aggressive match keys (never
    overwrites raw; suffix preserved for display, removed from match)."""
    display = unicode_normalize_nfc(trim_collapse_whitespace(raw or ""))
    match_text = normalize_ampersand(normalize_punctuation_for_match(display))
    tokens = tokenize_alnum(match_text)
    core, legal_suffix = extract_legal_suffix(tokens)
    core = remove_tokens(core, COMPANY_LOW_SIGNAL)
    return {"raw_value": raw, "canonical_display_value": display, "legal_suffix": legal_suffix,
            "canonical_match_value": " ".join(core), "token_sorted_key": token_sorted_key(core),
            "blocking_key": blocking_key(core), "phonetic_key": soundex_key(core[0] if core else ""),
            "issues": {"empty_after_cleaning": not core}, **BOUNDARY}


def standardize_person_name(raw: str) -> dict[str, Any]:
    """COMPOSITE: raw person string -> display (diacritics/case preserved) + parsed honorifics + match
    keys. Parsing is conservative (W3C personal-names guidance): components only when unambiguous."""
    display = unicode_normalize_nfc(trim_collapse_whitespace(raw or ""))
    working = display
    if "," in working:  # 'Family, Given' -> 'Given Family' for the working order
        fam, _, given = working.partition(",")
        working = f"{given.strip()} {fam.strip()}"
    words = [w for w in normalize_apostrophes(working).replace(".", ". ").split() if w]
    prefix = ""
    while words and re.sub(r"\W", "", words[0]).casefold() in HONORIFIC_PREFIXES:
        prefix = f"{prefix} {words.pop(0)}".strip()
    suffix = ""
    while words and re.sub(r"\W", "", words[-1]).casefold() in HONORIFIC_SUFFIXES:
        suffix = f"{words.pop()} {suffix}".strip()
    match_tokens = remove_tokens(tokenize_alnum(" ".join(words)), frozenset())
    return {"raw_value": raw, "display_name": display, "honorific_prefix": prefix,
            "honorific_suffix": suffix, "core_name": " ".join(words),
            "canonical_match_value": " ".join(match_tokens),
            "token_sorted_key": token_sorted_key(match_tokens),
            "phonetic_key": soundex_key(match_tokens[-1] if match_tokens else ""),
            "blocking_key": blocking_key([match_tokens[-1], match_tokens[0][:1]] if match_tokens else []),
            "issues": {"single_token_name": len(match_tokens) <= 1}, **BOUNDARY}


def standardize_us_address(raw: str) -> dict[str, Any]:
    """COMPOSITE: raw US address -> postal-cased display + components + pipe blocking key. Rule-based
    (one-country row of the address-standardizer zoo; libpostal/postal-API lanes are other rows)."""
    display_src = unicode_normalize_nfc(trim_collapse_whitespace(raw or ""))
    tokens = tokenize_alnum(normalize_punctuation_for_match(display_src))
    postal = next((normalize_postal_code_us(t) for t in reversed(tokens)
                   if normalize_postal_code_us(t)), "")
    mapped = map_tokens(map_tokens(map_tokens(tokens, ADDRESS_SUFFIX_MAP), UNIT_TYPE_MAP), DIRECTIONAL_MAP)
    house = tokens[0] if tokens and tokens[0].isdigit() else ""
    street_words, street_suffix, unit_type, unit_number = [], "", "", ""
    i = 1 if house else 0
    while i < len(mapped):
        tok = mapped[i]
        if tok in set(ADDRESS_SUFFIX_MAP.values()):
            street_suffix = tok
            i += 1
            break
        if tok in set(UNIT_TYPE_MAP.values()):
            break
        street_words.append(tok)
        i += 1
    if i < len(mapped) and mapped[i] in set(UNIT_TYPE_MAP.values()):
        unit_type = mapped[i]
        unit_number = mapped[i + 1] if i + 1 < len(mapped) else ""
    state = next((v for k, v in STATE_CODE_MAP.items() if k in " ".join(tokens)),
                 next((t.upper() for t in tokens if t.upper() in STATE_CODE_MAP.values()), ""))
    key_parts = [p for p in (house, *street_words, street_suffix.lower(), unit_type.lower(), unit_number,
                             postal.split("-")[0], "us") if p]
    display = " ".join(x for x in (house, *[w.upper() for w in street_words], street_suffix,
                                   unit_type, unit_number.upper() if unit_number else "") if x)
    return {"raw_value": raw, "canonical_display": display, "house_number": house,
            "street_name": " ".join(w.upper() for w in street_words), "street_suffix": street_suffix,
            "unit_type": unit_type, "unit_number": unit_number, "administrative_area": state,
            "postal_code": postal, "country_code": "US",
            "canonical_match_key": "|".join(key_parts),
            "issues": {"missing_postal_code": not postal, "missing_house_number": not house}, **BOUNDARY}


def generate_match_keys(raw: str) -> dict[str, Any]:
    """COMPOSITE: any string -> the full key family (exact/normalized/token-sorted/ngram/phonetic/block)."""
    tokens = tokenize_alnum(raw or "")
    return {"raw_value": raw, "exact_key": (raw or "").strip(),
            "normalized_key": " ".join(tokens), "token_sorted_key": token_sorted_key(tokens),
            "ngram_key": ngram_key(raw or ""), "phonetic_key": soundex_key(tokens[0] if tokens else ""),
            "blocking_key": blocking_key(tokens), **BOUNDARY}


_ATOMIC_FNS = (trim_collapse_whitespace, unicode_normalize_nfc, strip_diacritics_for_match,
               normalize_apostrophes, casefold_for_match, normalize_punctuation_for_match,
               normalize_ampersand, tokenize_alnum, remove_tokens, map_tokens, token_sorted_key,
               ngram_key, soundex_key, blocking_key, extract_legal_suffix, normalize_postal_code_us)
_COMPOSITE_FNS = (standardize_company_name, standardize_person_name, standardize_us_address,
                  generate_match_keys)


def _card_preamble() -> str:
    """Imports + module constants rendered FROM THE LIVE OBJECTS (single source — the card source stays
    self-contained without a parallel literal copy of any table)."""
    return (
        "import re\nimport unicodedata\n\n"
        f"_WS_RE = re.compile({_WS_RE.pattern!r})\n"
        f"_ZW_RE = re.compile({_ZW_RE.pattern!r})\n"
        f"_PUNCT_TO_SPACE_RE = re.compile({_PUNCT_TO_SPACE_RE.pattern!r})\n"
        f"_APOSTROPHES = {_APOSTROPHES!r}\n"
        f"ADDRESS_SUFFIX_MAP = {ADDRESS_SUFFIX_MAP!r}\n"
        f"UNIT_TYPE_MAP = {UNIT_TYPE_MAP!r}\n"
        f"DIRECTIONAL_MAP = {DIRECTIONAL_MAP!r}\n"
        f"STATE_CODE_MAP = {STATE_CODE_MAP!r}\n"
        f"LEGAL_SUFFIXES = frozenset({sorted(LEGAL_SUFFIXES)!r})\n"
        f"HONORIFIC_PREFIXES = frozenset({sorted(HONORIFIC_PREFIXES)!r})\n"
        f"HONORIFIC_SUFFIXES = frozenset({sorted(HONORIFIC_SUFFIXES)!r})\n"
        f"NAME_PARTICLES = frozenset({sorted(NAME_PARTICLES)!r})\n"
        f"COMPANY_LOW_SIGNAL = frozenset({sorted(COMPANY_LOW_SIGNAL)!r})\n"
        f"BOUNDARY = {BOUNDARY!r}\n\n")


#: sibling functions each card's body calls (their sources ride along so every card runs standalone)
_CARD_DEPS: dict[str, tuple[str, ...]] = {
    "normalize_punctuation_for_match": ("normalize_apostrophes", "trim_collapse_whitespace"),
    "normalize_ampersand": ("trim_collapse_whitespace",),
    "tokenize_alnum": ("casefold_for_match", "strip_diacritics_for_match"),
    "ngram_key": ("casefold_for_match", "strip_diacritics_for_match"),
    "soundex_key": ("casefold_for_match", "strip_diacritics_for_match"),
    "standardize_company_name": ("unicode_normalize_nfc", "trim_collapse_whitespace", "normalize_ampersand",
                                 "normalize_punctuation_for_match", "normalize_apostrophes",
                                 "tokenize_alnum", "casefold_for_match", "strip_diacritics_for_match",
                                 "extract_legal_suffix", "remove_tokens", "token_sorted_key",
                                 "blocking_key", "soundex_key"),
    "standardize_person_name": ("unicode_normalize_nfc", "trim_collapse_whitespace", "normalize_apostrophes",
                                "tokenize_alnum", "casefold_for_match", "strip_diacritics_for_match",
                                "remove_tokens", "token_sorted_key", "soundex_key", "blocking_key"),
    "standardize_us_address": ("unicode_normalize_nfc", "trim_collapse_whitespace",
                               "normalize_punctuation_for_match", "normalize_apostrophes", "tokenize_alnum",
                               "casefold_for_match", "strip_diacritics_for_match", "map_tokens",
                               "normalize_postal_code_us"),
    "generate_match_keys": ("tokenize_alnum", "casefold_for_match", "strip_diacritics_for_match",
                            "token_sorted_key", "ngram_key", "soundex_key", "blocking_key"),
}
def all_cards() -> list[dict[str, Any]]:
    """Executable-library-shaped cards: atoms (kind=primitive) + composites (kind=primitive_group with
    their atom PLAN recorded — primitives made of primitives). Every executable_body is SELF-CONTAINED:
    preamble (imports + live-rendered constants) + dependency sources + the function itself."""
    by_name = {f.__name__: f for f in _ATOMIC_FNS + _COMPOSITE_FNS}
    preamble = _card_preamble()
    cards = []
    for fn in _ATOMIC_FNS + _COMPOSITE_FNS:
        deps = "".join(inspect.getsource(by_name[d]) + "\n" for d in _CARD_DEPS.get(fn.__name__, ())
                       if d in by_name)
        src = preamble + deps + inspect.getsource(fn)
        title = (fn.__doc__ or fn.__name__).splitlines()[0][:160]
        composite = fn in _COMPOSITE_FNS
        cards.append({
            "primitive_id": canonical_id(CARD_PREFIX, title, src), "impl_name": fn.__name__,
            "record_type": "string_standardization_primitive",
            "kind": "primitive_group" if composite else "primitive",
            "title": title, "executable_body": src, "language": "python",
            "input_edge": "RawStringValue", "output_edge": "StandardizedStringRecord" if composite else "NormalizedStringValue",
            "blackbox": f"{'Composite (primitives of primitives)' if composite else 'Atomic'} string-"
                        f"standardization primitive: {title} Input: raw string. Output: "
                        f"{'standardized record with raw preserved' if composite else 'normalized value'}.",
            "plan_steps": COMPOSITE_PLANS.get(fn.__name__, []),
            "dictionary_version": DICTIONARY_VERSION, "tier": "common", **BOUNDARY})
    return cards


# ── self-test (every atom + every composite oracle-tested; the playbook's worked example end-to-end) ─────────
def _self_test() -> int:
    checks: list[tuple[str, bool]] = []
    checks.append(("whitespace: trims, collapses, kills NBSP/zero-width",
                   trim_collapse_whitespace("  Acme ​   Inc\t\n") == "Acme Inc"))
    checks.append(("unicode NFC: combining accent composes; display keeps the accent",
                   unicode_normalize_nfc("José") == "José"))
    checks.append(("diacritic strip is MATCH-ONLY lossy: José->Jose, Müller->Muller",
                   strip_diacritics_for_match("José Müller") == "Jose Muller"))
    checks.append(("apostrophes: curly -> straight (O’Connor)",
                   normalize_apostrophes("O’Connor") == "O'Connor"))
    checks.append(("punctuation for match: A.C.M.E. -> ACME; separators -> space",
                   normalize_punctuation_for_match("A.C.M.E., Logistics") == "ACME Logistics"))
    checks.append(("ampersand: AT&T -> at and t (after casefold)",
                   casefold_for_match(normalize_ampersand("AT&T")) == "at and t"))
    checks.append(("tokenize: lower alnum, diacritic-free",
                   tokenize_alnum("Acme Logistics, Inc.") == ["acme", "logistics", "inc"]))
    checks.append(("dictionary maps: street->ST apartment->APT north->N (versioned data rows)",
                   map_tokens(["street", "apartment", "north"],
                              {**ADDRESS_SUFFIX_MAP, **UNIT_TYPE_MAP, **DIRECTIONAL_MAP}) == ["ST", "APT", "N"]))
    checks.append(("token-sorted key: 'Smith, John' == 'John Smith'",
                   token_sorted_key(tokenize_alnum("Smith, John")) == token_sorted_key(tokenize_alnum("John Smith"))))
    checks.append(("soundex: Robert/Rupert agree, Robert/Ashcraft differ",
                   soundex_key("Robert") == soundex_key("Rupert") == "R163"
                   and soundex_key("Robert") != soundex_key("Ashcraft")))
    checks.append(("ngram key survives an internal typo partially (shared trigrams)",
                   len(set(ngram_key("acme logistics").split()) & set(ngram_key("acme logistcs").split())) >= 8))
    checks.append(("legal suffix: extracted for display, removed from core",
                   extract_legal_suffix(["acme", "co", "llc"]) == (["acme"], "CO LLC")))
    checks.append(("ZIP: 5, 9->5-4, garbage->empty",
                   normalize_postal_code_us("10001") == "10001"
                   and normalize_postal_code_us("100011234") == "10001-1234"
                   and normalize_postal_code_us("1000") == ""))
    # composites on the playbook's worked example (raw ALWAYS preserved)
    comp = standardize_company_name(" The Acme Co., LLC ")
    checks.append(("company composite: display preserved, suffix split, match key 'acme'",
                   comp["raw_value"] == " The Acme Co., LLC " and comp["canonical_display_value"] == "The Acme Co., LLC"
                   and comp["legal_suffix"] == "CO LLC" and comp["canonical_match_value"] == "acme"))
    checks.append(("company match keys CONVERGE across the playbook's variants",
                   standardize_company_name("Acme, Inc.")["canonical_match_value"]
                   == standardize_company_name("ACME Incorporated")["canonical_match_value"]
                   == standardize_company_name("The Acme Company LLC")["canonical_match_value"] == "acme"))
    person = standardize_person_name("  Dr. José A. García-López Jr. ")
    checks.append(("person composite: display keeps diacritics+honorifics; match key drops both",
                   person["display_name"] == "Dr. José A. García-López Jr."
                   and person["honorific_prefix"] == "Dr." and person["honorific_suffix"] == "Jr."
                   and person["canonical_match_value"] == "jose a garcia lopez"))
    checks.append(("person: 'Smith, John Q.' and 'Dr. John Q. Smith Jr.' share the token-sorted key",
                   standardize_person_name("Smith, John Q.")["token_sorted_key"]
                   == standardize_person_name("Dr. John Q. Smith Jr.")["token_sorted_key"]))
    addr = standardize_us_address("123 main street apt. 5, New York, NY 10001")
    checks.append(("address composite: parsed components + postal display + pipe match key",
                   addr["house_number"] == "123" and addr["street_suffix"] == "ST"
                   and addr["unit_type"] == "APT" and addr["unit_number"] == "5"
                   and addr["administrative_area"] == "NY" and addr["postal_code"] == "10001"
                   and addr["canonical_match_key"] == "123|main|st|apt|5|10001|us"))
    checks.append(("address variants '123 Main St #5' vs 'apt. 5' agree on house|street|suffix block",
                   standardize_us_address("123 Main Street Apt 5 New York NY 10001")["canonical_match_key"]
                   == addr["canonical_match_key"]))
    keys = generate_match_keys("Acme Logistics")
    checks.append(("match-key family emitted (exact/normalized/sorted/ngram/phonetic/blocking)",
                   keys["normalized_key"] == "acme logistics" and keys["blocking_key"] == "acme|logistics"
                   and keys["phonetic_key"] and keys["ngram_key"]))
    cards = all_cards()
    checks.append(("cards: every atom + composite, canonical ids, composites carry their atom PLAN",
                   len(cards) == len(_ATOMIC_FNS) + len(_COMPOSITE_FNS)
                   and all(c["primitive_id"].startswith(CARD_PREFIX) for c in cards)
                   and all(c["plan_steps"] for c in cards if c["kind"] == "primitive_group")
                   and all(set(c["plan_steps"]) <= {f.__name__ for f in _ATOMIC_FNS}
                           for c in cards if c["kind"] == "primitive_group")))
    checks.append(("raw is NEVER overwritten (every composite carries raw_value verbatim)",
                   all(r["raw_value"] is x for r, x in
                       ((standardize_company_name(" x Inc "), " x Inc "),
                        (standardize_person_name(" Dr. Y "), " Dr. Y "),
                        (standardize_us_address(" 1 Main St "), " 1 Main St ")))))
    checks.append(("boundary on every card", all(c.get("serves_truth") is False for c in cards)))
    failed = [n for n, ok in checks if not ok]
    for n, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print(f"\nPASS - string_standardization_primitives: {len(_ATOMIC_FNS)} atomic + {len(_COMPOSITE_FNS)} "
          f"composite (primitives OF primitives, atom plans declared) — raw never overwritten, display "
          f"preserves meaning, match keys aggressive, dictionaries versioned data. serves_truth=false.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--cards", action="store_true")
    ap.add_argument("--demo", metavar="JSON", default=None)
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.cards:
        for c in all_cards():
            print(json.dumps(c, sort_keys=True))
        return 0
    if args.demo:
        row = json.loads(args.demo)
        out = {}
        if row.get("full_name"):
            out["person_name"] = standardize_person_name(row["full_name"])
        if row.get("company"):
            out["company_name"] = standardize_company_name(row["company"])
        if row.get("address"):
            out["address"] = standardize_us_address(row["address"])
        print(json.dumps(out, indent=2, sort_keys=True, ensure_ascii=False))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
