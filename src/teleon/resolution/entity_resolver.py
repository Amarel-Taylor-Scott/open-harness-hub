"""entity_resolver — registry-driven record linkage robust to typos in any column.

Per-entity-type RULESETS (architecture/entity_resolution_rules.json) drive everything: each column is normalized (person
nicknames/suffixes, company legal-suffix stripping, address/phone standardization) then scored by a comparator (exact /
Jaro-Winkler / token-set / phonetic), and the WEIGHTED column score decides match / review / no_match. A typo in one
column lowers its score but the others can still carry the match. An IDENTIFIER (e.g. NPI) overrides: equal valid ids =>
match; both-present-and-different => no_match (can't be the same entity). Blocking keys keep it scalable. serves_truth=false.
"""
from __future__ import annotations

import json
import re
from difflib import SequenceMatcher
from functools import lru_cache
from pathlib import Path

_RULES = Path(__file__).resolve().parents[3] / "architecture" / "entity_resolution_rules.json"


@lru_cache(maxsize=1)
def _rules() -> dict:
    return json.loads(_RULES.read_text())


def ruleset(name: str) -> dict:
    return _rules()["rulesets"][name]


# --- comparators (each returns 0..1) ---------------------------------------------------------------------------------
def _jaro(s1: str, s2: str) -> float:
    if s1 == s2:
        return 1.0
    if not s1 or not s2:
        return 0.0
    md = max(max(len(s1), len(s2)) // 2 - 1, 0)
    m1, m2, matches = [False] * len(s1), [False] * len(s2), 0
    for i, c in enumerate(s1):
        for j in range(max(0, i - md), min(i + md + 1, len(s2))):
            if not m2[j] and s2[j] == c:
                m1[i] = m2[j] = True
                matches += 1
                break
    if not matches:
        return 0.0
    t, k = 0, 0
    for i in range(len(s1)):
        if m1[i]:
            while not m2[k]:
                k += 1
            if s1[i] != s2[k]:
                t += 1
            k += 1
    t //= 2
    return (matches / len(s1) + matches / len(s2) + (matches - t) / matches) / 3


def jaro_winkler(a: str, b: str, p: float = 0.1) -> float:
    j = _jaro(a, b)
    pref = 0
    for x, y in zip(a, b):
        if x == y and pref < 4:
            pref += 1
        else:
            break
    return round(j + pref * p * (1 - j), 4)


def token_set(a: str, b: str) -> float:
    ta, tb = set(a.split()), set(b.split())
    return round(len(ta & tb) / len(ta | tb), 4) if (ta and tb) else 0.0


def levenshtein_ratio(a: str, b: str) -> float:
    return round(SequenceMatcher(None, a, b).ratio(), 4)


def soundex(s: str) -> str:
    s = re.sub(r"[^A-Za-z]", "", s).upper()
    if not s:
        return ""
    codes = {**dict.fromkeys("BFPV", "1"), **dict.fromkeys("CGJKQSXZ", "2"), **dict.fromkeys("DT", "3"),
             "L": "4", **dict.fromkeys("MN", "5"), "R": "6"}
    out, prev = s[0], codes.get(s[0], "")
    for c in s[1:]:
        code = codes.get(c, "")
        if code and code != prev:
            out += code
        if c not in "HW":
            prev = code
    return (out + "000")[:4]


_COMPARATORS = {
    "exact": lambda a, b: 1.0 if a == b and a != "" else 0.0,
    "jaro_winkler": jaro_winkler,
    "levenshtein_ratio": levenshtein_ratio,
    "token_set": token_set,
    "soundex": lambda a, b: 1.0 if soundex(a) == soundex(b) and soundex(a) else 0.0,
    "numeric_exact": lambda a, b: 1.0 if re.sub(r"\D", "", a) == re.sub(r"\D", "", b) and re.sub(r"\D", "", a) else 0.0,
}


# --- normalizers -----------------------------------------------------------------------------------------------------
_NICKNAMES = {"bob": "robert", "rob": "robert", "bobby": "robert", "bill": "william", "will": "william", "billy": "william",
              "jim": "james", "jimmy": "james", "joe": "joseph", "mike": "michael", "dave": "david", "tom": "thomas",
              "dick": "richard", "rick": "richard", "liz": "elizabeth", "beth": "elizabeth", "kate": "katherine",
              "cathy": "katherine", "peggy": "margaret", "meg": "margaret", "ed": "edward", "ted": "edward", "tony": "anthony",
              "chris": "christopher", "steve": "stephen", "ken": "kenneth", "sam": "samuel", "dan": "daniel"}
_NAME_SUFFIX = re.compile(r"\b(md|do|jr|sr|ii|iii|iv|phd|esq|rn|np|pa|dds|dmd|od|dvm|cpa|pe)\b\.?", re.I)
_LEGAL = re.compile(r"\b(llc|l\.l\.c|inc|incorporated|corp|corporation|ltd|limited|co|company|pllc|p\.a|pa|pc|llp|lp)\b\.?", re.I)
_COMPANY_ABBR = {"grp": "group", "assoc": "associates", "assocs": "associates", "ctr": "center", "svc": "services",
                 "svcs": "services", "intl": "international", "natl": "national", "dept": "department", "mgmt": "management",
                 "med": "medical", "ortho": "orthopedics", "cardio": "cardiology"}


def normalize_person_name(n) -> str:
    n = str(n or "").lower().replace(".", "")          # "m.d." -> "md" so dotted suffixes strip
    n = _NAME_SUFFIX.sub(" ", n)
    n = re.sub(r"[^\w\s]", " ", n)
    toks = [_NICKNAMES.get(t, t) for t in re.sub(r"\s+", " ", n).strip().split()]
    return " ".join(toks)


def normalize_company_name(c) -> str:
    c = str(c or "").lower().replace("&", "and")
    c = re.sub(r"^the\s+", "", c)
    c = _LEGAL.sub(" ", c)
    c = re.sub(r"[^\w\s]", " ", c)
    toks = [_COMPANY_ABBR.get(t, t) for t in re.sub(r"\s+", " ", c).strip().split()]
    return " ".join(toks)


_ADDR_ABBR = [(r"\bStreet\b", "St"), (r"\bAvenue\b", "Ave"), (r"\bDrive\b", "Dr"), (r"\bSuite\b", "Ste"),
              (r"\bRoad\b", "Rd"), (r"\bBoulevard\b", "Blvd"), (r"\bParkway\b", "Pkwy")]


def _norm_address(a) -> str:
    """Self-contained address normalizer — the resolution layer must not import UP into a vertical (correct layering:
    verticals depend on resolution, not the reverse)."""
    a = re.sub(r"\s+", " ", str(a or "").strip())
    for pat, rep in _ADDR_ABBR:
        a = re.sub(pat, rep, a, flags=re.I)
    return a.lower()


_NORMALIZERS = {"person_name": normalize_person_name, "company_name": normalize_company_name, "address": _norm_address,
                "phone": lambda p: re.sub(r"\D", "", str(p or "")), "lower": lambda s: str(s or "").strip().lower(),
                "none": lambda s: str(s or "")}


# --- the rule-driven matcher -----------------------------------------------------------------------------------------
def compare(ruleset_name: str, a: dict, b: dict) -> dict:
    """Compare two records under a ruleset. Returns {score, decision (match|review|no_match), per_column, identifier}."""
    rs = ruleset(ruleset_name)
    idf = rs.get("identifier_field")
    if idf:
        ia, ib = str(a.get(idf) or "").strip(), str(b.get(idf) or "").strip()
        if ia and ib:
            if ia == ib:
                return {"score": 1.0, "decision": "match", "identifier": "match", "per_column": [], "reason": "identifier exact match"}
            return {"score": 0.0, "decision": "no_match", "identifier": "conflict", "per_column": [], "reason": "identifier conflict — cannot be the same entity"}
    acc = tot = 0.0
    per = []
    for col in rs["columns"]:
        va, vb = a.get(col["field"]), b.get(col["field"])
        if va is None or vb is None:
            continue
        nrm = _NORMALIZERS[col["normalizer"]]
        sim = _COMPARATORS[col["comparator"]](nrm(va), nrm(vb))
        acc += col["weight"] * sim
        tot += col["weight"]
        per.append({"field": col["field"], "comparator": col["comparator"], "sim": round(sim, 3)})
    score = round(acc / tot, 4) if tot else 0.0
    decision = "match" if score >= rs["match_threshold"] else ("review" if score >= rs["review_threshold"] else "no_match")
    return {"score": score, "decision": decision, "identifier": "absent", "per_column": per, "serves_truth": False}


def blocking_key(ruleset_name: str, record: dict) -> str:
    """A cheap key so we only compare records likely to match (scales to millions). person -> soundex of the name;
    company -> first normalized token."""
    rs = ruleset(ruleset_name)
    if rs.get("blocking") == "soundex_name":
        return soundex(normalize_person_name(record.get("name")))
    if rs.get("blocking") == "company_token":
        toks = normalize_company_name(record.get("name")).split()
        return toks[0] if toks else ""
    if rs.get("blocking") == "zip":
        return re.sub(r"\D", "", str(record.get("zip") or ""))[:5]
    return ""


def resolve_entities(records: list, ruleset_name: str) -> dict:
    """Cluster records into entities: BLOCK, compare within blocks, union the matches; collect 'review' pairs for a human.
    Returns {entities: [[ids]], review_pairs: [(id,id,score)], comparisons, naive_comparisons}. ids = provider_id or index."""
    rs = ruleset(ruleset_name)
    idf = rs.get("identifier_field")
    ids = [r.get("provider_id", r.get("id", i)) for i, r in enumerate(records)]
    # MULTI-KEY blocking: each record gets its name/company block key AND (if present) its identifier as a key — so two
    # records sharing an identifier are ALWAYS compared (the identifier override must never be gated by name-blocking).
    key_to_idx: dict = {}
    for i, r in enumerate(records):
        keys = {blocking_key(ruleset_name, r)}
        if idf and str(r.get(idf) or "").strip():
            keys.add("ID:" + str(r.get(idf)).strip())
        for k in keys:
            key_to_idx.setdefault(k, []).append(i)
    parent = list(range(len(records)))
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    review, compared = [], set()
    for idxs in key_to_idx.values():
        for p in range(len(idxs)):
            for q in range(p + 1, len(idxs)):
                a, b = (idxs[p], idxs[q]) if idxs[p] < idxs[q] else (idxs[q], idxs[p])
                if (a, b) in compared:
                    continue
                compared.add((a, b))
                res = compare(ruleset_name, records[a], records[b])
                if res["decision"] == "match":
                    parent[find(a)] = find(b)
                elif res["decision"] == "review":
                    review.append((ids[a], ids[b], res["score"]))
    groups: dict = {}
    for i in range(len(records)):
        groups.setdefault(find(i), []).append(ids[i])
    n = len(records)
    return {"entities": [sorted(g, key=str) for g in groups.values()], "review_pairs": review,
            "comparisons": len(compared), "naive_comparisons": n * (n - 1) // 2, "serves_truth": False}
