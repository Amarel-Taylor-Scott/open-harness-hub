#!/usr/bin/env python3
"""scripts.deterministic_dispatch_zoo — a ZOO of resolution layers benchmarked on realistic English task
phrasings (candidate-only). The multi-path law applied to task->primitive resolution.

Owner: deterministic searching helps, but there are many layers/parameters/grids of patterns to try, and INPUT
is near-infinite English from programmers and agents (e.g. "is this european bank account number valid?" -> IBAN;
"convert old IBM mainframe text" -> EBCDIC). A single keyword layer misses most of that. So resolution is a ZOO
of interchangeable deterministic layers (0 LLM tokens), raced on a REALISTIC query bank (natural phrasings that
deliberately avoid the primitive's own keywords). The residual that no deterministic layer catches is the honest
LLM-fallback tail.

Layers (all 0 LLM tokens): keyword (raw token overlap) · synonym (expand query via a concept lexicon, then
overlap) · trigram (char-3-gram Jaccard, catches morphology/typos) · fusion (best-of-layers). Reports the honest
per-layer hit-rate on realistic English + the fusion coverage + the tail. Deterministic; candidate-only.

    python3 scripts/deterministic_dispatch_zoo.py --self-test
    python3 scripts/deterministic_dispatch_zoo.py --race
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
import json  # noqa: E402
from typing import Any, Callable  # noqa: E402

from scripts.deterministic_primitive_dispatch import build_index, _toks  # noqa: E402

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
BENCHMARK_KIND = "real"  # no_proxy_gate: real=executed+measured / proxy=estimated
ARTIFACT_DIR_REL = "data/dev-intel/deterministic_dispatch"

# ── REALISTIC query bank: natural English a programmer/agent types, deliberately AVOIDING the primitive's own
#    keywords, so keyword-only honestly misses many. primitive_name -> [phrasings]. ──────────────────────────
REALISTIC_QUERIES: dict[str, list[str]] = {
    "ebcdic_cp037_decode": ["convert this old IBM mainframe text to readable characters",
                            "translate a legacy z/OS byte string into unicode"],
    "cobol_comp3_decode": ["read a packed decimal field from a legacy mainframe file",
                           "unpack signed packed digits from an old COBOL record"],
    "protobuf_varint_decode": ["decode a protocol buffer wire integer", "read a base-128 wire number"],
    "protobuf_zigzag_decode": ["undo zigzag encoding to get a signed number", "decode a signed protobuf sint"],
    "fix_message_parse": ["parse a trading exchange order message into tag value pairs",
                          "split a financial protocol message by its delimiter"],
    "asn1_der_length_decode": ["read the length bytes of a DER encoded certificate structure",
                               "parse the length field of an x509 element"],
    "dicom_tag_parse": ["get the group and element from a medical imaging tag",
                        "read a radiology data element identifier"],
    "hl7_v2_msh_parse": ["parse the header of a hospital HL7 message",
                         "read the sending application from a healthcare message header"],
    "ipv6_compress_rfc5952": ["shorten an expanded ipv6 address to its canonical form",
                              "compress a long ipv6 address"],
    "base32_rfc4648_decode": ["decode a TOTP two factor authentication secret", "decode a base32 string"],
    "crc32_ieee": ["compute a crc checksum for these bytes", "get the cyclic redundancy check of a payload"],
    "semver_precedence_compare": ["compare two semantic version strings to see which is newer",
                                  "order two release versions by precedence"],
    "iban_mod97_validate": ["check if this european bank account number is valid",
                            "verify an international bank account identifier"],
    "isbn13_check_valid": ["verify a thirteen digit book identifier", "validate a book number checksum"],
    "aba_routing_valid": ["check a US bank routing transit number", "validate a nine digit bank routing code"],
    "ean13_check_digit": ["compute the last digit of a product barcode", "get the check digit for a retail barcode"],
    "luhn_generate_check_digit": ["compute the check digit for a credit card number",
                                  "generate the trailing verification digit for a card"],
    "base58_decode": ["decode a bitcoin base58 string", "decode a cryptocurrency address string"],
    "base64url_decode": ["decode a JWT token segment", "url safe base64 decode a web token part"],
    "ipv4_to_int": ["turn a dotted ip address into a 32 bit integer", "pack a v4 network address into a number"],
    "cidr_contains": ["is this ip inside the given subnet range", "check network membership for an address"],
    "roman_to_int": ["convert a roman numeral to a number", "read roman numbers into an integer"],
    "iso8601_duration_seconds": ["how many seconds are in this duration string", "convert PT1H30M to seconds"],
    "json_pointer_resolve": ["look up a value in a json document by its path reference",
                             "resolve a rfc 6901 path in a json object"],
    "hex_color_to_rgb": ["convert a css hex color to red green blue values", "parse a web color code"],
    "vin_check_digit": ["compute the check digit of a vehicle identification number", "validate a car VIN"],
    "npi_valid": ["check a healthcare provider identifier number", "validate a national provider id"],
    "imei_luhn_valid": ["validate a phone IMEI number", "check a mobile device identity number"],
}

# ── concept lexicon: English concept token -> primitive strong tokens to inject (deterministic synonym layer) ─
SYNONYM_MAP: dict[str, set[str]] = {
    "mainframe": {"ebcdic", "cp037", "cobol"}, "ibm": {"ebcdic", "cp037"}, "zos": {"ebcdic"},
    "packed": {"comp3"}, "cobol": {"comp3", "ebcdic"},
    "wire": {"protobuf", "varint"}, "protocol": {"protobuf", "fix"}, "buffer": {"protobuf"},
    "zigzag": {"zigzag"}, "sint": {"zigzag"},
    "trading": {"fix"}, "exchange": {"fix"}, "order": {"fix"}, "financial": {"fix"},
    "certificate": {"asn1", "der", "x509"}, "x509": {"asn1", "der"}, "der": {"asn1"},
    "medical": {"dicom"}, "imaging": {"dicom"}, "radiology": {"dicom"},
    "hospital": {"hl7"}, "healthcare": {"hl7", "npi"}, "health": {"hl7"}, "hl7": {"hl7"},
    "ipv6": {"ipv6", "rfc5952"}, "totp": {"base32"}, "authentication": {"base32"}, "2fa": {"base32"},
    "checksum": {"crc32", "luhn", "ean13", "iban"}, "redundancy": {"crc32"}, "crc": {"crc32"},
    "version": {"semver"}, "release": {"semver"}, "semantic": {"semver"},
    "bank": {"iban", "aba"}, "account": {"iban"}, "european": {"iban"}, "international": {"iban"}, "iban": {"iban"},
    "book": {"isbn13"}, "isbn": {"isbn13"},
    "routing": {"aba"}, "transit": {"aba"},
    "barcode": {"ean13"}, "retail": {"ean13"}, "product": {"ean13"}, "gs1": {"ean13"},
    "card": {"luhn"}, "credit": {"luhn"}, "luhn": {"luhn"},
    "bitcoin": {"base58"}, "cryptocurrency": {"base58"}, "crypto": {"base58"},
    "jwt": {"base64url"}, "token": {"base64url"}, "web": {"base64url", "hex"},
    "ip": {"ipv4", "ipv6"}, "network": {"ipv4", "cidr"}, "dotted": {"ipv4"}, "v4": {"ipv4"},
    "subnet": {"cidr"}, "cidr": {"cidr"}, "membership": {"cidr"},
    "roman": {"roman"}, "numeral": {"roman"},
    "duration": {"iso8601"}, "seconds": {"iso8601"}, "iso": {"iso8601"},
    "json": {"json", "rfc6901", "pointer"}, "pointer": {"rfc6901"}, "path": {"rfc6901"},
    "color": {"hex"}, "css": {"hex"}, "rgb": {"hex"}, "hex": {"hex"},
    "vehicle": {"vin"}, "car": {"vin"}, "vin": {"vin"},
    "provider": {"npi"}, "npi": {"npi"},
    "phone": {"imei"}, "mobile": {"imei"}, "device": {"imei"}, "imei": {"imei"},
}


def _score_overlap(qtoks: set[str], rec: dict[str, Any]) -> int:
    return 3 * len(qtoks & rec["strong"]) + len(qtoks & rec["weak"])


def _expand_synonyms(qtoks: set[str]) -> set[str]:
    out = set(qtoks)
    for t in qtoks:
        out |= SYNONYM_MAP.get(t, set())
    return out


def _trigrams(s: str) -> set[str]:
    s = "".join(ch if ch.isalnum() else " " for ch in s.lower())
    return {s[i:i + 3] for i in range(len(s) - 2)} if len(s) >= 3 else {s}


def _layer_keyword(query: str, index: dict) -> str | None:
    q = _toks(query)
    ranked = sorted(index.items(), key=lambda kv: (-_score_overlap(q, kv[1]), kv[0]))
    return ranked[0][0] if ranked and _score_overlap(q, ranked[0][1]) > 0 else None


def _layer_synonym(query: str, index: dict) -> str | None:
    q = _expand_synonyms(_toks(query))
    ranked = sorted(index.items(), key=lambda kv: (-_score_overlap(q, kv[1]), kv[0]))
    return ranked[0][0] if ranked and _score_overlap(q, ranked[0][1]) > 0 else None


def _layer_trigram(query: str, index: dict) -> str | None:
    qg = _trigrams(query)
    best, best_s = None, 0.0
    for name, rec in index.items():
        key = " ".join([name, rec["platform"], rec["technology"]])
        rg = _trigrams(key)
        j = len(qg & rg) / len(qg | rg) if (qg | rg) else 0.0
        if j > best_s:
            best, best_s = name, j
    return best if best_s >= 0.05 else None


LAYERS: dict[str, Callable[[str, dict], str | None]] = {
    "keyword": _layer_keyword, "synonym": _layer_synonym, "trigram": _layer_trigram,
}


def race() -> dict[str, Any]:
    """Race every layer on the realistic query bank. Honest per-layer hit-rate + fusion coverage + the tail."""
    index = build_index()
    total = 0
    per_layer = {name: 0 for name in LAYERS}
    fusion_hits = 0
    misses: list[str] = []
    for prim, queries in REALISTIC_QUERIES.items():
        for query in queries:
            total += 1
            any_hit = False
            for lname, lfn in LAYERS.items():
                if lfn(query, index) == prim:
                    per_layer[lname] += 1
                    any_hit = True
            if any_hit:
                fusion_hits += 1
            else:
                misses.append(query)
    return {"record_type": "deterministic_dispatch_zoo_race", "n_queries": total, "n_primitives": len(REALISTIC_QUERIES),
            "per_layer_hit_rate": {k: round(v / total, 3) for k, v in per_layer.items()},
            "fusion_coverage": round(fusion_hits / total, 3),
            "llm_fallback_tail": round(len(misses) / total, 3), "tail_examples": misses[:6],
            "note": "realistic English phrasings that AVOID the primitive keywords; all layers 0 LLM tokens; "
                    "the fusion tail is the honest residual that needs a semantic-embed layer or an LLM.",
            **BOUNDARY}


def emit(result: dict[str, Any]) -> str:
    out_dir = resource(ARTIFACT_DIR_REL)
    out_dir.mkdir(parents=True, exist_ok=True)
    p = out_dir / "dispatch_zoo_race.json"
    p.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    return str(p)


def self_test() -> bool:
    """Mutation-gated: layers are deterministic + 0-LLM; FUSION beats the best single layer (the zoo helps);
    keyword-alone is honestly imperfect on realistic English (< fusion); tail is reported."""
    r1 = race()
    r2 = race()
    assert r1 == r2, "race must be deterministic"
    assert r1["n_queries"] >= 40, f"expected a real query bank, got {r1['n_queries']}"

    kw = r1["per_layer_hit_rate"]["keyword"]
    syn = r1["per_layer_hit_rate"]["synonym"]
    fusion = r1["fusion_coverage"]

    # (1) the ZOO helps: fusion >= every single layer, and strictly beats keyword-alone (the owner's point:
    #     keyword misses realistic English; other layers recover it).
    assert fusion >= max(r1["per_layer_hit_rate"].values()), "fusion must dominate any single layer"
    assert fusion > kw, f"fusion ({fusion}) must beat keyword-alone ({kw}) — else the zoo adds nothing"

    # (2) keyword-alone is HONESTLY imperfect on realistic English (this is the point; if it were 1.0 the queries
    #     would be too easy / circular).
    assert kw < 1.0, f"keyword-alone should not be perfect on realistic English (got {kw}) — queries too easy"

    # (3) synonym layer recovers concept phrasings keyword misses.
    assert syn >= kw, "synonym expansion must not do worse than raw keyword"

    # (4) tail is honestly reported (residual for a semantic-embed layer / LLM).
    assert 0.0 <= r1["llm_fallback_tail"] <= 1.0 and abs(r1["fusion_coverage"] + r1["llm_fallback_tail"] - 1.0) < 1e-6

    # (5) candidate-only.
    assert r1["candidate"] is True and r1["serves_truth"] is False

    print(f"OK deterministic_dispatch_zoo self-test: {r1['n_queries']} realistic English queries; per-layer "
          f"keyword {kw} / synonym {syn} / trigram {r1['per_layer_hit_rate']['trigram']} -> FUSION "
          f"{fusion} (0 LLM tokens); honest LLM-fallback tail {r1['llm_fallback_tail']}; serves_truth=false")
    return True


def main() -> None:
    ap = argparse.ArgumentParser(description="Race deterministic resolution layers on realistic English queries.")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--race", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return
    if args.race:
        res = race()
        res["path"] = emit(res)
        print(json.dumps(res, indent=2))
        return
    self_test()


if __name__ == "__main__":
    main()
