#!/usr/bin/env python3
"""scripts.party_name_primitives — the owner's human-name/party-name spec (2026-07-07) as executable
primitives: a "name field" is NEVER assumed to be one human with first+last. The pipeline is

    raw party-name observation -> normalized string -> PARTY CLASSIFICATION (person / multiple people /
    person_group / household / estate / trust / company / role_only / mixed_person_company / unknown)
    -> NAME EXPRESSION parse (shared_surname_pair / explicit_multi_person / marital_title_expression /
    ambiguous_slash / family_group / estate / trust / care_of / dba) -> SAFE EXPANSION -> per-person parse
    -> match keys -> issues + standardization level.

Owner laws encoded and oracle-tested on the spec's golden set: raw preserved; "James and Jane Doe" expands
with `inferred_family_name` marked on James; "Mr. and Mrs. James Doe" NEVER invents the spouse's given name;
"The Doe Family" yields a group with no fabricated individuals; estates/trusts are entities related to a
person, flagged do_not_merge_with_person; d/b/a splits into person + business; particles get strict AND
relaxed keys. Reuses the string-standardization pack's atoms (imports, not copies). candidate=true,
serves_truth=false.

    python3 scripts/party_name_primitives.py --self-test
    python3 scripts/party_name_primitives.py --demo "James and Jane Doe"
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
from typing import Any  # noqa: E402

from scripts.string_standardization_primitives import (  # noqa: E402 — reuse-first: the pack's atoms
    HONORIFIC_PREFIXES, HONORIFIC_SUFFIXES, LEGAL_SUFFIXES, NAME_PARTICLES,
    standardize_person_name, tokenize_alnum, trim_collapse_whitespace, unicode_normalize_nfc)

try:
    from src.teleon.experiments.ids import canonical_id  # noqa: E402  THE data-plane id authority
except ImportError as exc:  # pragma: no cover
    raise SystemExit(f"party_name_primitives requires canonical_id; import failed: {exc}")

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
CARD_PREFIX = "prim-party"
DICTIONARY_VERSION = "party-dicts-v1"

# ── versioned dictionaries (data rows, never scattered literals) ─────────────────────────────────────────────
PLACEHOLDER_TOKENS = frozenset({"n/a", "na", "none", "null", "unknown", "-", "--", ".", "?", "tbd", "xxx"})
TEST_NAME_TOKENS = frozenset({"test", "asdf", "qwerty", "sample", "demo", "dummy", "fake"})
ROLE_TOKENS = frozenset({"admin", "administrator", "billing", "accounts", "payable", "receivable",
                         "support", "customer", "info", "sales", "office", "manager", "owner",
                         "occupant", "resident", "department", "dept", "team", "staff", "hr"})
ORG_TOKENS = frozenset({"university", "school", "college", "hospital", "clinic", "bank", "group",
                        "holdings", "partners", "associates", "consulting", "logistics", "solutions",
                        "services", "manufacturing", "industries", "agency", "foundation", "institute",
                        "church", "ministries", "enterprises", "medical", "dental", "law"})
GOV_TOKENS = frozenset({"city", "county", "state", "department", "bureau", "commission", "authority",
                        "district", "municipality"})
#: seed given-name dictionary (signal only, never proof; extensible data)
GIVEN_NAME_SEEDS = frozenset("james jane john mary robert maria michael jennifer william linda david susan "
                             "richard sarah joseph karen thomas nancy charles lisa daniel betty anne marie "
                             "jose juan carlos luis ana wei min sean patrick johannes".split())
CONNECTOR_RE = re.compile(r"\s+(?:and|&)\s+|\s*/\s*", re.IGNORECASE)
_MARITAL_RE = re.compile(r"^(?:mr|mrs|ms|dr)\.?\s*(?:and|&)\s*(?:mr|mrs|ms|dr)\.?\s+(.+)$", re.IGNORECASE)
_ESTATE_RE = re.compile(r"^estate\s+of\s+(.+)$", re.IGNORECASE)
_TRUST_RE = re.compile(r"^(.*?)\s+(?:living\s+|family\s+|revocable\s+)?trust$", re.IGNORECASE)
_DBA_RE = re.compile(r"^(.*?)\s+d[/.]?b[/.]?a[/.]?\s+(.+)$", re.IGNORECASE)
_CARE_OF_RE = re.compile(r"^(.*?)\s+c/o\s+(.+)$", re.IGNORECASE)
_FAMILY_RE = re.compile(r"^(?:the\s+)?(\w[\w'-]*)\s+(?:family|household)$", re.IGNORECASE)


# ── ATOMIC primitives ─────────────────────────────────────────────────────────────────────────────────────────
def detect_placeholder_name(raw: str) -> str:
    """'' -> missing; 'N/A'/'Unknown' -> missing; 'Test User' -> test; 'Accounts Payable' -> role_only;
    real-looking names -> '' (no flag)."""
    cleaned = trim_collapse_whitespace(raw or "").casefold()
    if not cleaned or cleaned in PLACEHOLDER_TOKENS:
        return "missing"
    toks = tokenize_alnum(cleaned)
    if toks and all(t in TEST_NAME_TOKENS or t in ("user", "account") for t in toks):
        return "test"
    if toks and all(t in ROLE_TOKENS for t in toks):
        return "role_only"
    if not toks:
        return "invalid"
    return ""


def company_signals(raw: str) -> list[str]:
    """Signals suggesting an ORGANIZATION (legal suffix, org/gov/institution tokens, acronym-only)."""
    toks = tokenize_alnum(raw or "")
    signals = []
    if any(t in LEGAL_SUFFIXES for t in toks):
        signals.append("company_legal_suffix")
    if any(t in ORG_TOKENS for t in toks):
        signals.append("organization_token")
    if toks and toks[0] in GOV_TOKENS and "of" in (raw or "").casefold():
        signals.append("government_pattern")
    stripped = re.sub(r"[^A-Za-z]", "", raw or "")
    if stripped.isupper() and 2 <= len(stripped) <= 6 and len(toks) == 1:
        signals.append("all_caps_acronym")
    return signals


def person_signals(raw: str) -> list[str]:
    """Signals suggesting a HUMAN (honorifics, generational/professional suffixes, given-name hits,
    last-comma-first, initials)."""
    toks = tokenize_alnum(raw or "")
    signals = []
    if toks and toks[0] in HONORIFIC_PREFIXES:
        signals.append("honorific_prefix")
    if any(t in HONORIFIC_SUFFIXES for t in toks):
        signals.append("honorific_or_generational_suffix")
    if any(t in GIVEN_NAME_SEEDS for t in toks):
        signals.append("given_name_dictionary_hit")
    if re.match(r"^\s*[A-Z][\w'-]+\s*,\s*[A-Z]", raw or ""):
        signals.append("family_comma_given_pattern")
    if re.search(r"\b[A-Z]\.\s", (raw or "") + " "):
        signals.append("initial_pattern")
    return signals


def detect_name_expression(raw: str) -> dict[str, Any]:
    """Classify the EXPRESSION shape: single / shared_surname_pair / explicit_multi_person /
    marital_title_expression / ambiguous_slash / family_group / estate / trust / care_of / dba."""
    v = trim_collapse_whitespace(unicode_normalize_nfc(raw or ""))
    if m := _ESTATE_RE.match(v):
        return {"expression_type": "estate_expression", "related_name": m.group(1), "raw_expression": v}
    if m := _DBA_RE.match(v):
        return {"expression_type": "dba_expression", "person_part": m.group(1), "business_part": m.group(2),
                "raw_expression": v}
    if m := _CARE_OF_RE.match(v):
        return {"expression_type": "care_of_expression", "primary_part": m.group(1),
                "contact_part": m.group(2), "raw_expression": v}
    if m := _FAMILY_RE.match(v):
        return {"expression_type": "family_group", "shared_family_name": m.group(1).title(),
                "raw_expression": v}
    if (m := _TRUST_RE.match(v)) and not company_signals(m.group(1)):
        return {"expression_type": "trust_expression", "related_name": m.group(1), "raw_expression": v}
    if m := _MARITAL_RE.match(v):
        return {"expression_type": "marital_title_expression", "named_person": m.group(1),
                "raw_expression": v}
    if "/" in v and CONNECTOR_RE.search(v):
        pass  # slash handled below with connectors
    parts = [p for p in CONNECTOR_RE.split(v) if p and p.strip()]
    if len(parts) >= 2:
        connector = "/" if "/" in v else ("&" if "&" in v else "and")
        last_tokens = parts[-1].split()
        if connector == "/":
            return {"expression_type": "ambiguous_slash_expression", "segments": parts,
                    "raw_expression": v, "requires_review": True}
        # shared surname: earlier segments are single given-name tokens, last segment has >=2 tokens
        if len(last_tokens) >= 2 and all(len(p.split()) == 1 for p in parts[:-1]):
            return {"expression_type": "shared_surname_pair", "segments": parts, "connector": connector,
                    "shared_family_name": " ".join(last_tokens[1:]), "raw_expression": v}
        return {"expression_type": "explicit_multi_person", "segments": parts, "connector": connector,
                "raw_expression": v}
    return {"expression_type": "single_name", "segments": [v], "raw_expression": v}


def expand_name_expression(expr: dict[str, Any]) -> list[dict[str, Any]]:
    """SAFE expansion into person candidates. Shared surnames are marked inferred_family_name; the marital
    form NEVER invents the spouse's given name; slash forms expand nothing (review instead)."""
    etype = expr.get("expression_type")
    if etype == "shared_surname_pair":
        segs = expr["segments"]
        fam = expr["shared_family_name"]
        people = []
        for i, seg in enumerate(segs):
            given = seg.split()[0] if i < len(segs) - 1 else segs[-1].split()[0]
            people.append({"display_name": f"{given} {fam}", "given_name": given, "family_name": fam,
                           "inferred_family_name": i < len(segs) - 1, "source_segment": seg})
        return people
    if etype == "explicit_multi_person":
        return [{"display_name": trim_collapse_whitespace(s), "inferred_family_name": False,
                 "source_segment": s} for s in expr["segments"]]
    if etype == "marital_title_expression":
        named = standardize_person_name(expr["named_person"])
        fam = named["core_name"].split()[-1] if named["core_name"] else ""
        return [
            {"display_name": named["display_name"], "given_name": named["core_name"].split()[0]
             if named["core_name"] else "", "family_name": fam, "explicitly_named": True,
             "inferred_family_name": False},
            {"display_name": f"Spouse of {named['display_name']}", "given_name": None, "family_name": fam,
             "explicitly_named": False, "inferred_family_name": True,
             "issues": ["spouse_given_name_unknown", "do_not_infer_spouse_first_name"]}]
    return []


def family_name_span(core_name_tokens: list[str]) -> list[str]:
    """The surname span of a parsed name: from the FIRST particle onward ('maria de la cruz' ->
    ['de','la','cruz']); otherwise just the final token. Particles are part of the family name."""
    if len(core_name_tokens) < 2:
        return core_name_tokens
    for i, tok in enumerate(core_name_tokens[1:], start=1):
        if tok in NAME_PARTICLES:
            return core_name_tokens[i:]
    return core_name_tokens[-1:]


def parse_compound_family(tokens: list[str]) -> dict[str, Any]:
    """Particles/hyphens in family names: strict + relaxed match keys ('maria de la cruz' / 'maria cruz')."""
    particles = [t for t in tokens if t in NAME_PARTICLES]
    non_particles = [t for t in tokens if t not in NAME_PARTICLES]
    return {"family_particles": particles,
            "match_key_strict": " ".join(tokens),
            "match_key_relaxed": " ".join(non_particles),
            "compound": len(tokens) > 1,
            "hyphenated": any("-" in t for t in tokens)}


def classify_party_type(raw: str) -> dict[str, Any]:
    """The party-type decision flow (§13 of the owner spec): placeholder -> entity patterns -> connectors ->
    company vs person signals -> single_person / company / person_group / ... / unknown."""
    v = trim_collapse_whitespace(unicode_normalize_nfc(raw or ""))
    placeholder = detect_placeholder_name(v)
    if placeholder:
        return {"party_type": {"missing": "unknown", "invalid": "unknown"}.get(placeholder, placeholder),
                "subtype": placeholder, "confidence": 0.95, "signals": [f"placeholder:{placeholder}"],
                **BOUNDARY}
    expr = detect_name_expression(v)
    etype = expr["expression_type"]
    mapped = {"estate_expression": ("estate", "estate", 0.93),
              "trust_expression": ("trust", "trust", 0.9),
              "dba_expression": ("mixed_person_company", "doing_business_as", 0.9),
              "care_of_expression": ("mixed_person_company", "care_of", 0.85),
              "family_group": ("person_group", "family", 0.9),
              "marital_title_expression": ("person_group", "marital_title", 0.9),
              "shared_surname_pair": ("person_group", "couple_or_multiple_people", 0.9),
              "explicit_multi_person": ("multiple_people", "explicit_list", 0.88),
              "ambiguous_slash_expression": ("person_group", "ambiguous_pair", 0.6)}
    if etype in mapped:
        pt, st, conf = mapped[etype]
        return {"party_type": pt, "subtype": st, "confidence": conf,
                "signals": [f"expression:{etype}"], "expression": expr, **BOUNDARY}
    comp, pers = company_signals(v), person_signals(v)
    if comp and not pers:
        return {"party_type": "company", "subtype": "organization", "confidence": 0.9, "signals": comp,
                **BOUNDARY}
    if pers and not comp:
        toks = tokenize_alnum(v)
        subtype = "mononym" if len(toks) == 1 else "standard"
        return {"party_type": "single_person", "subtype": subtype,
                "confidence": 0.85 if len(pers) > 1 else 0.7, "signals": pers, **BOUNDARY}
    if comp and pers:
        return {"party_type": "mixed_person_company", "subtype": "person_named_entity", "confidence": 0.6,
                "signals": comp + pers, **BOUNDARY}
    toks = tokenize_alnum(v)
    if len(toks) == 1:
        return {"party_type": "single_person", "subtype": "mononym", "confidence": 0.5,
                "signals": ["single_token"], **BOUNDARY}
    if 2 <= len(toks) <= 4:
        return {"party_type": "single_person", "subtype": "unverified_name_shape", "confidence": 0.55,
                "signals": ["name_like_shape"], **BOUNDARY}
    return {"party_type": "unknown", "subtype": "unclassified", "confidence": 0.3, "signals": [], **BOUNDARY}


# ── COMPOSITE (primitives OF primitives) ─────────────────────────────────────────────────────────────────────
COMPOSITE_PLANS: dict[str, list[str]] = {
    "standardize_party_name": ["detect_placeholder_name", "classify_party_type", "detect_name_expression",
                               "expand_name_expression", "parse_compound_family"],
}


def standardize_party_name(raw: str) -> dict[str, Any]:
    """COMPOSITE — the full §13 flow. Returns raw + classification + expression + SAFELY expanded people
    (+ per-person parse via the standardization pack) + issues + standardization_level. Never invents
    identities; groups/estates/trusts are entities, not people."""
    classification = classify_party_type(raw)
    expr = classification.get("expression") or detect_name_expression(raw or "")
    people = expand_name_expression(expr)
    issues: list[str] = []
    if classification["party_type"] in ("person_group", "multiple_people"):
        issues.append("multiple_people_detected")
    if any(p.get("inferred_family_name") for p in people):
        issues.append("shared_surname_inferred")
    for p in people:
        issues.extend(p.get("issues", []))
    if expr.get("requires_review"):
        issues.append("requires_human_review")
    parsed_people = []
    for p in people:
        if p.get("given_name") is None and not p.get("explicitly_named", True):
            parsed_people.append(p)  # the unnamed spouse: keep as-is, never parse into an invented person
            continue
        parsed = standardize_person_name(p["display_name"])
        fam_tokens = tokenize_alnum(p.get("family_name") or (parsed["core_name"].split()[-1]
                                                             if parsed["core_name"] else ""))
        parsed_people.append({**p, "parsed": parsed, "family_keys": parse_compound_family(fam_tokens)})
    single = classification["party_type"] == "single_person"
    if single:
        parsed = standardize_person_name(raw or "")
        parsed_people = [{"display_name": parsed["display_name"], "parsed": parsed,
                          "inferred_family_name": False,
                          "family_keys": parse_compound_family(
                              family_name_span(tokenize_alnum(parsed["core_name"])))}]
        if classification["subtype"] == "mononym":
            issues.append("mononym")
    level = 0 if not raw else (2 if not parsed_people and classification["party_type"] in
                               ("company", "unknown", "missing", "role_only", "test") else 4)
    entity_flags = {}
    if classification["party_type"] in ("estate", "trust"):
        entity_flags = {"do_not_merge_with_person": True,
                        "related_person_mention": expr.get("related_name", "")}
        issues.append("legal_entity_named_after_person")
    if classification["party_type"] == "mixed_person_company":
        entity_flags = {"person_part": expr.get("person_part") or expr.get("contact_part", ""),
                        "business_part": expr.get("business_part") or expr.get("primary_part", "")}
    return {"raw_value": raw, "classification": {k: v for k, v in classification.items()
                                                 if k != "expression"},
            "expression_type": expr["expression_type"], "people": parsed_people,
            "person_count": len([p for p in parsed_people if p.get("explicitly_named", True)]),
            "entity_flags": entity_flags, "issues": sorted(set(issues)),
            "standardization_level": level, "dictionary_version": DICTIONARY_VERSION, **BOUNDARY}


# ── INTERNATIONAL name handling (owner-directed 2026-07-08): scripts, char sets, name-order standards ────────
#: locale -> canonical name order (data row per standard; extend, never rewrite)
LOCALE_NAME_ORDER = {"zh": "family_first", "ja": "family_first", "ko": "family_first", "vi": "family_first",
                     "hu": "family_first", "mn": "family_first",
                     "en": "given_first", "es": "given_first", "fr": "given_first", "de": "given_first",
                     "pt": "given_first", "it": "given_first", "pl": "given_first", "ru": "given_first"}
#: romanized surnames that are strong FAMILY-FIRST signals when leading (seed data; frequency-extensible)
FAMILY_FIRST_SURNAME_SEEDS = frozenset(
    "zhang wang li chen liu yang huang zhao wu zhou xu sun ma zhu hu guo lin gao "
    "kim lee park choi jung kang cho yoon jang im "
    "nguyen tran le pham hoang phan vu vo dang bui do "
    "sato suzuki takahashi tanaka watanabe ito yamamoto nakamura kobayashi kato "
    "nagy kovacs toth szabo horvath".split())
_SCRIPT_RANGES = (("cjk", 0x4E00, 0x9FFF), ("cjk", 0x3400, 0x4DBF), ("hiragana", 0x3040, 0x309F),
                  ("katakana", 0x30A0, 0x30FF), ("hangul", 0xAC00, 0xD7AF), ("hangul", 0x1100, 0x11FF),
                  ("cyrillic", 0x0400, 0x04FF), ("greek", 0x0370, 0x03FF), ("arabic", 0x0600, 0x06FF),
                  ("hebrew", 0x0590, 0x05FF), ("thai", 0x0E00, 0x0E7F), ("devanagari", 0x0900, 0x097F))
_FULLWIDTH_OFFSET = 0xFEE0  # fullwidth ASCII block -> halfwidth (ＡＢＣ -> ABC)


def detect_script(text: str) -> dict[str, Any]:
    """Which writing system(s) a name uses: latin/cjk/hiragana/katakana/hangul/cyrillic/... + mixed flag.
    Deterministic codepoint-range classification; the router for locale-specific parsing."""
    counts: dict[str, int] = {}
    for ch in text or "":
        if ch.isspace() or not ch.isalpha():
            continue
        code = ord(ch)
        name = next((n for n, lo, hi in _SCRIPT_RANGES if lo <= code <= hi),
                    "latin" if code < 0x0250 or 0x1E00 <= code <= 0x1EFF else "other")
        counts[name] = counts.get(name, 0) + 1
    dominant = max(counts, key=lambda k: (counts[k], k)) if counts else "none"
    return {"scripts": dict(sorted(counts.items())), "dominant_script": dominant,
            "mixed_script": len(counts) > 1, **BOUNDARY}


def fold_width_for_match(text: str) -> str:
    """Fullwidth chars -> halfwidth for MATCH keys (ＡＢＣ１２３ -> ABC123); display untouched."""
    return "".join(chr(ord(c) - _FULLWIDTH_OFFSET) if 0xFF01 <= ord(c) <= 0xFF5E else
                   (" " if c == "　" else c) for c in text or "")


def name_order_candidates(raw: str, *, locale_hint: str = "") -> dict[str, Any]:
    """The 'Zhang Wei' problem: NEVER force an order — emit ranked given_first/family_first CANDIDATES
    from script, locale hint, comma format, and leading-surname seeds. CJK scripts and family-first
    locales raise family_first; a comma form is explicit; pure-Latin default leans given_first with the
    ambiguity recorded. High-value records route to review per the owner spec."""
    v = trim_collapse_whitespace(fold_width_for_match(unicode_normalize_nfc(raw or "")))
    if "," in v:
        return {"raw_value": raw, "candidates": [{"name_order": "family_first_comma_explicit",
                                                  "confidence": 0.97}],
                "signals": ["comma_format_explicit"], "requires_review_if_high_value": False, **BOUNDARY}
    script = detect_script(v)
    tokens = tokenize_alnum(v)
    signals: list[str] = []
    family_first = 0.30  # base rate: most-of-world data mixes both
    if script["dominant_script"] in ("cjk", "hiragana", "katakana", "hangul"):
        family_first = 0.85
        signals.append(f"script:{script['dominant_script']}")
    order = LOCALE_NAME_ORDER.get((locale_hint or "").split("-")[0].casefold())
    if order == "family_first":
        family_first = max(family_first, 0.80)
        signals.append(f"locale:{locale_hint}:family_first")
    elif order == "given_first":
        family_first = min(family_first, 0.20)
        signals.append(f"locale:{locale_hint}:given_first")
    if tokens and tokens[0] in FAMILY_FIRST_SURNAME_SEEDS:
        family_first = max(family_first, 0.72)
        signals.append(f"leading_surname_seed:{tokens[0]}")
    if tokens and tokens[-1] in FAMILY_FIRST_SURNAME_SEEDS and tokens[0] not in FAMILY_FIRST_SURNAME_SEEDS:
        family_first = min(family_first, 0.28)
        signals.append(f"trailing_surname_seed:{tokens[-1]}")
    candidates = sorted([{"name_order": "family_first", "confidence": round(family_first, 2)},
                         {"name_order": "given_first", "confidence": round(1 - family_first, 2)}],
                        key=lambda c: -c["confidence"])
    return {"raw_value": raw, "normalized_for_match": v, "candidates": candidates,
            "dominant_script": script["dominant_script"], "signals": signals,
            "ambiguous": 0.35 <= family_first <= 0.65,
            "requires_review_if_high_value": 0.2 < family_first < 0.8, **BOUNDARY}


_ATOMIC_FNS = (detect_placeholder_name, company_signals, person_signals, detect_name_expression,
               expand_name_expression, family_name_span, parse_compound_family, classify_party_type,
               detect_script, fold_width_for_match, name_order_candidates)
_COMPOSITE_FNS = (standardize_party_name,)


def all_cards() -> list[dict[str, Any]]:
    cards = []
    for fn in _ATOMIC_FNS + _COMPOSITE_FNS:
        src = inspect.getsource(fn)
        title = (fn.__doc__ or fn.__name__).splitlines()[0][:160]
        composite = fn in _COMPOSITE_FNS
        cards.append({"primitive_id": canonical_id(CARD_PREFIX, title, src), "impl_name": fn.__name__,
                      "record_type": "party_name_primitive",
                      "kind": "primitive_group" if composite else "primitive", "title": title,
                      "executable_body": src, "language": "python",
                      "input_edge": "RawPartyNameObservation",
                      "output_edge": "StandardizedPartyRecord" if composite else "PartyNameSignal",
                      "blackbox": f"{'Composite' if composite else 'Atomic'} party-name primitive: {title} "
                                  f"Input: raw party-name string. Output: "
                                  f"{'classified+expanded party record' if composite else 'signal/expansion component'}.",
                      "plan_steps": COMPOSITE_PLANS.get(fn.__name__, []), "tier": "common", **BOUNDARY})
    return cards


# ── self-test: the owner's golden set (§19), mutation-gated ──────────────────────────────────────────────────
def _self_test() -> int:
    checks: list[tuple[str, bool]] = []
    r = standardize_party_name("James and Jane Doe")
    checks.append(("'James and Jane Doe' -> person_group / shared_surname_pair -> James Doe (INFERRED) + "
                   "Jane Doe (explicit), flags set",
                   r["classification"]["party_type"] == "person_group"
                   and r["expression_type"] == "shared_surname_pair"
                   and [p["display_name"] for p in r["people"]] == ["James Doe", "Jane Doe"]
                   and r["people"][0]["inferred_family_name"] and not r["people"][1]["inferred_family_name"]
                   and {"multiple_people_detected", "shared_surname_inferred"} <= set(r["issues"])))
    r = standardize_party_name("James Doe and Jane Smith")
    checks.append(("'James Doe and Jane Smith' -> explicit_multi_person, NOTHING inferred",
                   r["expression_type"] == "explicit_multi_person"
                   and [p["display_name"] for p in r["people"]] == ["James Doe", "Jane Smith"]
                   and not any(p.get("inferred_family_name") for p in r["people"])))
    r = standardize_party_name("Mr. and Mrs. James Doe")
    spouse = r["people"][1]
    checks.append(("'Mr. and Mrs. James Doe' -> spouse given name is None and NEVER invented",
                   r["expression_type"] == "marital_title_expression"
                   and spouse["given_name"] is None and spouse["explicitly_named"] is False
                   and "do_not_infer_spouse_first_name" in r["issues"]))
    r = standardize_party_name("The Doe Family")
    checks.append(("'The Doe Family' -> family group, NO fabricated individuals",
                   r["classification"]["party_type"] == "person_group"
                   and r["classification"]["subtype"] == "family" and r["people"] == []))
    r = standardize_party_name("Estate of Jane Doe")
    checks.append(("'Estate of Jane Doe' -> estate entity, do_not_merge_with_person, decedent related",
                   r["classification"]["party_type"] == "estate"
                   and r["entity_flags"]["do_not_merge_with_person"]
                   and r["entity_flags"]["related_person_mention"] == "Jane Doe"))
    r = standardize_party_name("Jane Doe Trust")
    checks.append(("'Jane Doe Trust' -> trust entity, not a person",
                   r["classification"]["party_type"] == "trust"
                   and r["entity_flags"]["do_not_merge_with_person"]))
    r = standardize_party_name("John Doe d/b/a JD Consulting")
    checks.append(("d/b/a -> mixed_person_company with person/business split",
                   r["classification"]["party_type"] == "mixed_person_company"
                   and r["entity_flags"]["person_part"] == "John Doe"
                   and r["entity_flags"]["business_part"] == "JD Consulting"))
    r = standardize_party_name("Acme c/o Jane Doe")
    checks.append(("care-of -> mixed, contact person captured",
                   r["classification"]["party_type"] == "mixed_person_company"
                   and r["entity_flags"]["person_part"] == "Jane Doe"))
    checks.append(("'Acme Inc.' -> company; 'IBM' acronym -> company",
                   classify_party_type("Acme Inc.")["party_type"] == "company"
                   and classify_party_type("IBM")["party_type"] == "company"))
    checks.append(("placeholders: N/A->missing, Test User->test, Accounts Payable->role_only",
                   detect_placeholder_name("N/A") == "missing"
                   and detect_placeholder_name("Test User") == "test"
                   and detect_placeholder_name("Accounts Payable") == "role_only"))
    r = standardize_party_name("Maria de la Cruz")
    fk = r["people"][0]["family_keys"]
    checks.append(("'Maria de la Cruz' -> particles kept: strict 'de la cruz' vs relaxed 'cruz'",
                   r["classification"]["party_type"] == "single_person"
                   and fk["match_key_strict"] == "de la cruz" and fk["match_key_relaxed"] == "cruz"))
    r = standardize_party_name("Madonna")
    checks.append(("'Madonna' -> mononym flagged, not first+missing-last",
                   r["classification"]["subtype"] == "mononym" and "mononym" in r["issues"]))
    r = standardize_party_name("John/Jane Doe")
    checks.append(("'John/Jane Doe' -> ambiguous slash: NO expansion, review required",
                   r["expression_type"] == "ambiguous_slash_expression" and r["people"] == []
                   and "requires_human_review" in r["issues"]))
    checks.append(("raw always preserved verbatim",
                   standardize_party_name(" X and Y Doe ")["raw_value"] == " X and Y Doe "))
    r = name_order_candidates("Zhang Wei")
    checks.append(("'Zhang Wei' -> BOTH order candidates emitted, family_first leads via surname seed, "
                   "review-if-high-value (NEVER forces one parse)",
                   [c["name_order"] for c in r["candidates"]] == ["family_first", "given_first"]
                   and r["candidates"][0]["confidence"] >= 0.7 and len(r["candidates"]) == 2
                   and r["requires_review_if_high_value"]))
    r = name_order_candidates("Wei Zhang")
    checks.append(("'Wei Zhang' -> trailing surname seed flips toward given_first (Western-ordered)",
                   r["candidates"][0]["name_order"] == "given_first"
                   and any(s.startswith("trailing_surname_seed") for s in r["signals"])))
    r = name_order_candidates("王伟")
    checks.append(("'王伟' -> CJK script detected, family_first dominant",
                   r["dominant_script"] == "cjk" and r["candidates"][0]["name_order"] == "family_first"
                   and r["candidates"][0]["confidence"] >= 0.85))
    r = name_order_candidates("Nagy Katalin", locale_hint="hu")
    checks.append(("Hungarian locale hint -> family_first (the European family-first standard)",
                   r["candidates"][0]["name_order"] == "family_first"))
    r = name_order_candidates("Jane Doe", locale_hint="en")
    checks.append(("'Jane Doe' en -> given_first, ambiguity NOT flagged",
                   r["candidates"][0]["name_order"] == "given_first" and not r["ambiguous"]))
    checks.append(("comma form explicit family-first; fullwidth folds for match; scripts classify (mixed/CJK)",
                   name_order_candidates("Doe, Jane")["candidates"][0]["name_order"]
                   == "family_first_comma_explicit"
                   and fold_width_for_match("ＡＣＭＥ　Ｃｏｒｐ") == "ACME Corp"
                   and detect_script("García Иван")["mixed_script"]
                   and detect_script("佐藤太郎")["dominant_script"] == "cjk"))
    cards = all_cards()
    checks.append(("cards: atoms + composite with atom plan, canonical ids, boundary",
                   len(cards) == len(_ATOMIC_FNS) + len(_COMPOSITE_FNS)
                   and all(c.get("serves_truth") is False for c in cards)
                   and any(c["plan_steps"] for c in cards)))
    failed = [n for n, ok in checks if not ok]
    for n, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print(f"\nPASS - party_name_primitives: {len(_ATOMIC_FNS)} atomic + {len(_COMPOSITE_FNS)} composite — "
          f"party classification, expression parsing, SAFE expansion (inferred surnames marked, spouse "
          f"names never invented, groups/estates/trusts never people). Golden-set oracle. serves_truth=false.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--cards", action="store_true")
    ap.add_argument("--demo", metavar="RAW_NAME", default=None)
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.cards:
        for c in all_cards():
            print(json.dumps(c, sort_keys=True))
        return 0
    if args.demo is not None:
        print(json.dumps(standardize_party_name(args.demo), indent=2, sort_keys=True, ensure_ascii=False))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
