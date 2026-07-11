#!/usr/bin/env python3
"""mint_validation_pack_runner — author + mint REAL, oracle-tested primitives for the DATA-VALIDATION / cleaning vertical.

Each spec is a real, deterministic, STDLIB-ONLY capability (`def run(...)`) plus a STRICT behavioral oracle (>=2
assertions). We mint through ``scripts.mint_vertical_pack.mint_pack`` — it gates every body via ast.parse -> exec ->
oracle and writes ONLY oracle-passing cards. Cards are candidate=true, serves_truth=false (candidate-only).

    PYTHONPATH=. python3 scripts/mint_validation_pack_runner.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, ".")
from scripts import mint_vertical_pack as m  # noqa: E402

_VAL = ["validation"]


SPECS = [
    # 1. validate email (regex)
    {
        "title": "Validate Email Address Format With Regex",
        "blackbox": "Returns True if the string is a syntactically valid email address (local@domain.tld), else False.",
        "input_edge": "EmailCandidate", "output_edge": "ValidationFlag",
        "capability_tags": ["validate", "email", "regex", "format"], "domains": _VAL,
        "body": r"""
import re
_EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
def run(s):
    return isinstance(s, str) and _EMAIL_RE.match(s) is not None
""",
        "oracle": lambda run: (
            run("a@b.com") is True
            and run("user.name+tag@sub.example.co") is True
            and run("bad") is False
            and run("x@y") is False
            and run("@no-local.com") is False
            and run(123) is False
        ),
    },
    # 2. validate E.164 phone
    {
        "title": "Validate E164 Telephone Number Format",
        "blackbox": "Returns True if the string is a valid E.164 phone number (a plus sign then 1..15 digits, no leading zero).",
        "input_edge": "PhoneNumberCandidate", "output_edge": "ValidationFlag",
        "capability_tags": ["validate", "phone", "e164", "regex"], "domains": _VAL,
        "body": r"""
import re
_E164_RE = re.compile(r"^\+[1-9]\d{1,14}$")
def run(s):
    return isinstance(s, str) and _E164_RE.match(s) is not None
""",
        "oracle": lambda run: (
            run("+14155552671") is True
            and run("+442071838750") is True
            and run("14155552671") is False
            and run("+0123") is False
            and run("+") is False
        ),
    },
    # 3. validate URL
    {
        "title": "Validate Http Or Https Url Format",
        "blackbox": "Returns True if the string is an http(s) URL with a non-empty host, else False.",
        "input_edge": "UrlCandidate", "output_edge": "ValidationFlag",
        "capability_tags": ["validate", "url", "http", "regex"], "domains": _VAL,
        "body": r"""
import re
_URL_RE = re.compile(r"^https?://[^\s/$.?#][^\s]*$")
def run(s):
    return isinstance(s, str) and _URL_RE.match(s) is not None
""",
        "oracle": lambda run: (
            run("https://example.com") is True
            and run("http://a.b/c?d=1") is True
            and run("ftp://x") is False
            and run("notaurl") is False
            and run("https://") is False
        ),
    },
    # 4. validate IPv4
    {
        "title": "Validate Ipv4 Dotted Decimal Address",
        "blackbox": "Returns True if the string is a dotted-decimal IPv4 address (four octets 0..255).",
        "input_edge": "IpAddressCandidate", "output_edge": "ValidationFlag",
        "capability_tags": ["validate", "ipv4", "network", "address"], "domains": _VAL,
        "body": r"""
def run(s):
    if not isinstance(s, str):
        return False
    parts = s.split(".")
    if len(parts) != 4:
        return False
    for p in parts:
        if not p.isdigit() or not (0 <= int(p) <= 255):
            return False
    return True
""",
        "oracle": lambda run: (
            run("192.168.0.1") is True
            and run("0.0.0.0") is True
            and run("255.255.255.255") is True
            and run("256.1.1.1") is False
            and run("1.2.3") is False
            and run("a.b.c.d") is False
        ),
    },
    # 5. validate UUID
    {
        "title": "Validate Uuid Canonical String Format",
        "blackbox": "Returns True if the string is a canonical 8-4-4-4-12 hexadecimal UUID.",
        "input_edge": "UuidCandidate", "output_edge": "ValidationFlag",
        "capability_tags": ["validate", "uuid", "identifier", "regex"], "domains": _VAL,
        "body": r"""
import re
_UUID_RE = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")
def run(s):
    return isinstance(s, str) and _UUID_RE.match(s) is not None
""",
        "oracle": lambda run: (
            run("550e8400-e29b-41d4-a716-446655440000") is True
            and run("550E8400-E29B-41D4-A716-446655440000") is True
            and run("not-a-uuid") is False
            and run("550e8400e29b41d4a716446655440000") is False
        ),
    },
    # 6. validate ISO-8601 date
    {
        "title": "Validate Iso8601 Calendar Date String",
        "blackbox": "Returns True if the string is a valid YYYY-MM-DD calendar date (real month/day), else False.",
        "input_edge": "DateStringCandidate", "output_edge": "ValidationFlag",
        "capability_tags": ["validate", "date", "iso8601", "calendar"], "domains": _VAL,
        "body": r"""
import datetime
def run(s):
    if not isinstance(s, str):
        return False
    try:
        datetime.datetime.strptime(s, "%Y-%m-%d")
        return True
    except ValueError:
        return False
""",
        "oracle": lambda run: (
            run("2026-07-10") is True
            and run("2000-02-29") is True
            and run("2026-13-01") is False
            and run("2026-02-30") is False
            and run("not-a-date") is False
        ),
    },
    # 7. parse ISO date to (y, m, d)
    {
        "title": "Parse Iso8601 Date Into Year Month Day Tuple",
        "blackbox": "Parses a YYYY-MM-DD string into an integer (year, month, day) tuple; returns None if unparseable.",
        "input_edge": "IsoDateString", "output_edge": "DateComponents",
        "capability_tags": ["parse", "date", "iso8601", "decompose"], "domains": _VAL,
        "body": r"""
import datetime
def run(s):
    try:
        dt = datetime.datetime.strptime(s, "%Y-%m-%d")
        return (dt.year, dt.month, dt.day)
    except (ValueError, TypeError):
        return None
""",
        "oracle": lambda run: (
            run("2026-07-10") == (2026, 7, 10)
            and run("1999-12-31") == (1999, 12, 31)
            and run("bad") is None
            and run(None) is None
        ),
    },
    # 8. coerce to int (safe)
    {
        "title": "Safely Coerce Scalar To Integer Or Null",
        "blackbox": "Coerces a scalar/string to int (trimming whitespace); returns None instead of raising on failure.",
        "input_edge": "RawScalar", "output_edge": "IntegerOrNull",
        "capability_tags": ["coerce", "int", "safe", "cleaning"], "domains": _VAL,
        "body": r"""
def run(x):
    if isinstance(x, bool):
        return None
    if isinstance(x, int):
        return x
    try:
        return int(str(x).strip())
    except (ValueError, TypeError):
        return None
""",
        "oracle": lambda run: (
            run("42") == 42
            and run("  10 ") == 10
            and run(3) == 3
            and run("-7") == -7
            and run("3.5") is None
            and run("abc") is None
        ),
    },
    # 9. coerce to float (safe)
    {
        "title": "Safely Coerce Scalar To Float Or Null",
        "blackbox": "Coerces a scalar/string to float (trimming whitespace); returns None instead of raising on failure.",
        "input_edge": "RawScalar", "output_edge": "FloatOrNull",
        "capability_tags": ["coerce", "float", "safe", "cleaning"], "domains": _VAL,
        "body": r"""
def run(x):
    if isinstance(x, bool):
        return None
    try:
        return float(str(x).strip())
    except (ValueError, TypeError):
        return None
""",
        "oracle": lambda run: (
            run("3.14") == 3.14
            and run("  2 ") == 2.0
            and run("-0.5") == -0.5
            and run("abc") is None
            and run("") is None
        ),
    },
    # 10. coerce to bool
    {
        "title": "Coerce Common Truthy Falsy Token To Boolean",
        "blackbox": "Maps common truthy/falsy tokens (true/1/yes/on, false/0/no/off) to a bool; returns None if unrecognized.",
        "input_edge": "RawScalar", "output_edge": "BooleanOrNull",
        "capability_tags": ["coerce", "bool", "token", "cleaning"], "domains": _VAL,
        "body": r"""
_TRUE = {"true", "1", "yes", "y", "on", "t"}
_FALSE = {"false", "0", "no", "n", "off", "f"}
def run(x):
    if isinstance(x, bool):
        return x
    s = str(x).strip().lower()
    if s in _TRUE:
        return True
    if s in _FALSE:
        return False
    return None
""",
        "oracle": lambda run: (
            run("true") is True
            and run("FALSE") is False
            and run("Yes") is True
            and run("0") is False
            and run("maybe") is None
        ),
    },
    # 11. strip / normalize whitespace
    {
        "title": "Normalize And Collapse Internal Whitespace",
        "blackbox": "Collapses every run of whitespace to a single space and trims the ends of the string.",
        "input_edge": "RawText", "output_edge": "NormalizedText",
        "capability_tags": ["normalize", "whitespace", "clean", "text"], "domains": _VAL,
        "body": r"""
import re
def run(s):
    return re.sub(r"\s+", " ", str(s)).strip()
""",
        "oracle": lambda run: (
            run("  a  b\tc\n") == "a b c"
            and run("x") == "x"
            and run("   ") == ""
            and run("no\n\nblanks") == "no blanks"
        ),
    },
    # 12. validate non-empty
    {
        "title": "Validate String Is Non Empty After Trim",
        "blackbox": "Returns True if the value is a string with at least one non-whitespace character.",
        "input_edge": "RawText", "output_edge": "ValidationFlag",
        "capability_tags": ["validate", "non-empty", "required", "text"], "domains": _VAL,
        "body": r"""
def run(s):
    return isinstance(s, str) and s.strip() != ""
""",
        "oracle": lambda run: (
            run("x") is True
            and run(" hello ") is True
            and run("   ") is False
            and run("") is False
            and run(None) is False
        ),
    },
    # 13. validate string length range
    {
        "title": "Validate String Length Within Inclusive Range",
        "blackbox": "Returns True if the string length is within [lo, hi] inclusive.",
        "input_edge": "TextWithLengthBounds", "output_edge": "ValidationFlag",
        "capability_tags": ["validate", "length", "range", "text"], "domains": _VAL,
        "body": r"""
def run(s, lo, hi):
    return isinstance(s, str) and lo <= len(s) <= hi
""",
        "oracle": lambda run: (
            run("abc", 1, 5) is True
            and run("abc", 3, 3) is True
            and run("", 1, 5) is False
            and run("toolong", 1, 3) is False
        ),
    },
    # 14. validate numeric range
    {
        "title": "Validate Number Within Inclusive Numeric Range",
        "blackbox": "Returns True if lo <= x <= hi (inclusive numeric bounds).",
        "input_edge": "NumberWithBounds", "output_edge": "ValidationFlag",
        "capability_tags": ["validate", "numeric", "range", "bounds"], "domains": _VAL,
        "body": r"""
def run(x, lo, hi):
    return lo <= x <= hi
""",
        "oracle": lambda run: (
            run(5, 1, 10) is True
            and run(1, 1, 10) is True
            and run(10, 1, 10) is True
            and run(0, 1, 10) is False
            and run(11, 1, 10) is False
        ),
    },
    # 15. validate one-of (enum)
    {
        "title": "Validate Value Is One Of Allowed Choices",
        "blackbox": "Returns True if the value is a member of the allowed-choices collection (enum membership).",
        "input_edge": "ValueWithChoices", "output_edge": "ValidationFlag",
        "capability_tags": ["validate", "enum", "one-of", "membership"], "domains": _VAL,
        "body": r"""
def run(x, choices):
    return x in choices
""",
        "oracle": lambda run: (
            run("a", ["a", "b", "c"]) is True
            and run("c", ["a", "b", "c"]) is True
            and run("z", ["a", "b", "c"]) is False
            and run(2, {1, 2, 3}) is True
        ),
    },
    # 16. normalize email (lowercase + trim)
    {
        "title": "Normalize Email By Trimming And Lowercasing",
        "blackbox": "Normalizes an email string by stripping surrounding whitespace and lowercasing it.",
        "input_edge": "EmailCandidate", "output_edge": "NormalizedEmail",
        "capability_tags": ["normalize", "email", "lowercase", "clean"], "domains": _VAL,
        "body": r"""
def run(s):
    return str(s).strip().lower()
""",
        "oracle": lambda run: (
            run("  User@Example.COM ") == "user@example.com"
            and run("A@B.com") == "a@b.com"
            and run("already@lower.com") == "already@lower.com"
        ),
    },
    # 17. mask a credit-card-like number
    {
        "title": "Mask Card Number Keeping Only Last Four Digits",
        "blackbox": "Strips non-digits then masks all but the last four digits with asterisks (PAN masking).",
        "input_edge": "CardNumberCandidate", "output_edge": "MaskedCardNumber",
        "capability_tags": ["mask", "redact", "card", "pii"], "domains": _VAL,
        "body": r"""
import re
def run(s):
    digits = re.sub(r"\D", "", str(s))
    if len(digits) <= 4:
        return digits
    return "*" * (len(digits) - 4) + digits[-4:]
""",
        "oracle": lambda run: (
            run("4111 1111 1111 1234") == "*" * 12 + "1234"
            and run("1234567812345678") == "*" * 12 + "5678"
            and run("42") == "42"
        ),
    },
    # 18. Luhn-checksum validate
    {
        "title": "Validate Number Passes Luhn Checksum",
        "blackbox": "Returns True if the digit string satisfies the Luhn (mod-10) checksum used by payment cards.",
        "input_edge": "DigitStringCandidate", "output_edge": "ValidationFlag",
        "capability_tags": ["validate", "luhn", "checksum", "card"], "domains": _VAL,
        "body": r"""
def run(s):
    digits = [int(c) for c in str(s) if c.isdigit()]
    if not digits:
        return False
    total = 0
    for i, d in enumerate(reversed(digits)):
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0
""",
        "oracle": lambda run: (
            run("4111111111111111") is True
            and run("79927398713") is True
            and run("4111111111111112") is False
            and run("") is False
        ),
    },
    # 19. validate postal code (US zip)
    {
        "title": "Validate United States Zip Postal Code",
        "blackbox": "Returns True for a US ZIP (5 digits) or ZIP+4 (5-4 digits) postal code.",
        "input_edge": "PostalCodeCandidate", "output_edge": "ValidationFlag",
        "capability_tags": ["validate", "zip", "postal", "us"], "domains": _VAL,
        "body": r"""
import re
_ZIP_RE = re.compile(r"^\d{5}(-\d{4})?$")
def run(s):
    return isinstance(s, str) and _ZIP_RE.match(s) is not None
""",
        "oracle": lambda run: (
            run("94103") is True
            and run("94103-1234") is True
            and run("9410") is False
            and run("abcde") is False
            and run("94103-12") is False
        ),
    },
    # 20. detect + drop null/None fields from a dict
    {
        "title": "Drop None Valued Fields From Record",
        "blackbox": "Returns a shallow copy of the mapping with every key whose value is None removed.",
        "input_edge": "RecordWithNulls", "output_edge": "CleanRecord",
        "capability_tags": ["clean", "null", "dict", "prune"], "domains": _VAL,
        "body": r"""
def run(d):
    return {k: v for k, v in d.items() if v is not None}
""",
        "oracle": lambda run: (
            run({"a": 1, "b": None, "c": 3}) == {"a": 1, "c": 3}
            and run({"x": None}) == {}
            and run({"keep": 0, "drop": None}) == {"keep": 0}
        ),
    },
    # 21. require keys present in a dict
    {
        "title": "Validate Required Keys Present In Record",
        "blackbox": "Returns True if the mapping is a dict containing every required key.",
        "input_edge": "RecordWithRequiredKeys", "output_edge": "ValidationFlag",
        "capability_tags": ["validate", "required", "keys", "dict"], "domains": _VAL,
        "body": r"""
def run(d, keys):
    return isinstance(d, dict) and all(k in d for k in keys)
""",
        "oracle": lambda run: (
            run({"a": 1, "b": 2}, ["a", "b"]) is True
            and run({"a": 1, "b": 2, "c": 3}, ["a", "b"]) is True
            and run({"a": 1}, ["a", "b"]) is False
            and run({"a": None}, ["a"]) is True
        ),
    },
    # 22. coerce empty-string to None
    {
        "title": "Coerce Empty Or Blank String To None",
        "blackbox": "Returns None when the value is a string that is empty or only whitespace; otherwise returns it unchanged.",
        "input_edge": "RawScalar", "output_edge": "ValueOrNull",
        "capability_tags": ["coerce", "empty", "null", "clean"], "domains": _VAL,
        "body": r"""
def run(x):
    if isinstance(x, str) and x.strip() == "":
        return None
    return x
""",
        "oracle": lambda run: (
            run("") is None
            and run("   ") is None
            and run("x") == "x"
            and run(0) == 0
            and run(0) is not None
        ),
    },
    # 23. validate JSON parseable
    {
        "title": "Validate String Is Parseable Json",
        "blackbox": "Returns True if the string parses as JSON via json.loads, else False (no exception raised).",
        "input_edge": "JsonStringCandidate", "output_edge": "ValidationFlag",
        "capability_tags": ["validate", "json", "parse", "format"], "domains": _VAL,
        "body": r"""
import json
def run(s):
    try:
        json.loads(s)
        return True
    except (ValueError, TypeError):
        return False
""",
        "oracle": lambda run: (
            run('{"a": 1}') is True
            and run("[1, 2, 3]") is True
            and run('"str"') is True
            and run("not json") is False
            and run("{bad}") is False
        ),
    },
    # 24. clamp a number to a range
    {
        "title": "Clamp Number Into Inclusive Range",
        "blackbox": "Clamps x into [lo, hi]: returns lo if below, hi if above, else x unchanged.",
        "input_edge": "NumberWithBounds", "output_edge": "ClampedNumber",
        "capability_tags": ["clamp", "range", "numeric", "bound"], "domains": _VAL,
        "body": r"""
def run(x, lo, hi):
    return max(lo, min(x, hi))
""",
        "oracle": lambda run: (
            run(5, 0, 10) == 5
            and run(-3, 0, 10) == 0
            and run(15, 0, 10) == 10
            and run(0, 0, 10) == 0
        ),
    },
    # 25. validate a probability (0..1)
    {
        "title": "Validate Probability Within Zero To One",
        "blackbox": "Returns True if the value is a real number (not bool) in the inclusive interval [0.0, 1.0].",
        "input_edge": "NumberCandidate", "output_edge": "ValidationFlag",
        "capability_tags": ["validate", "probability", "range", "numeric"], "domains": _VAL,
        "body": r"""
def run(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and 0 <= x <= 1
""",
        "oracle": lambda run: (
            run(0.5) is True
            and run(0) is True
            and run(1) is True
            and run(1.5) is False
            and run(-0.1) is False
            and run(True) is False
        ),
    },
]


def main() -> int:
    out_path = Path("data/dev-intel/aidevobserver_edge_foundry/minted_validation_pack_cards.jsonl")
    rec = m.mint_pack(SPECS, out_path=out_path)
    print(f"specs={rec['specs']} valid_syntax={rec['valid_syntax']} working={rec['working']} "
          f"appended={rec['appended']}")
    print(f"pack={rec['out']}")
    if rec["failed"]:
        print("FAILURES:")
        for f in rec["failed"]:
            print(f"  - {f['title']}: {f['error']}")
    else:
        print("FAILURES: none")
    print("EXAMPLE TITLES:")
    for c in rec["cards"][:5]:
        print(f"  - {c['title']}  [{c['input_edge']} -> {c['output_edge']}]  vlevel={c['verification_level']}")
    return 0 if rec["working"] == rec["specs"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
