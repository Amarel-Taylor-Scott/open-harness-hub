#!/usr/bin/env python3
"""scripts.prove_leaves_encoding_codec — WORKABLE (proven + TYPED) deterministic leaf primitives for the
'encoding_codec' family.

A workable leaf must be BOTH proven (serves_truth=true set ONLY by a PASSING executed proof — never hand-set) AND
typed (carry canonical edge type_ids so it can chain). This module declares >=28 REAL pure deterministic leaf
codecs — base64 (std/urlsafe) enc/dec, base32, base16, base85, ascii85, hex enc/dec, url quote/unquote (+plus),
percent-encode/decode, rot13, ascii-fold, quoted-printable, unicode-escape, html-escape, newline-escape,
char<->binary — runs EVERY ONE through the imported `run_primitive_proof` (executes the mutator against a concrete
fixture and flips serves_truth false->true ONLY on pass), keeps ONLY passers, TYPES each persisted row via
`canonicalize_edge`, and proves every enc/dec pair reversible through the roundtrip (has_inverse) proof.

ADD-ONLY / flexible-multi-path: this is a NEW parallel file. It IMPORTS the shared machinery
(`scripts.mutator_registry.run_primitive_proof` / `MUTATOR_REGISTRY`, `scripts.build_edge_type_retrofit`
`.canonicalize_edge`) and plugs its extra pure mutators in with `setdefault` (idempotent registration, never an
overwrite). It edits NONE of the contract-locked files. serves_truth=true here is CORRECT + required: it is only
ever set by an executed passing proof — a deliberately-wrong leaf stays candidate and is never persisted. Offline +
deterministic: no wall-clock/RNG/network; the write path uses a fixed literal timestamp. CLI: --self-test | --write.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import base64 as _b64
import codecs as _codecs
import html as _html
import json
import quopri as _quopri
import sys
import unicodedata as _ud
import urllib.parse as _up
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

FAMILY = "encoding_codec"
OUT_DIR = _resource("data") / "dev-intel" / "proven_primitives"
OUT_JSONL = OUT_DIR / "proven_encoding_codec.jsonl"
OUT_MANIFEST = OUT_DIR / "manifest_encoding_codec.json"
# Fixed literal timestamp — deterministic, no wall-clock read (repo law: no datetime.now/time.time).
FROZEN_TS = "2026-07-03T00:00:00Z"


# ── PURE deterministic codec mutators: signature (payload, **kwargs) -> (output, receipt_dict). No I/O. ──
def _enc_base64_std(text: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = _b64.b64encode(text.encode("utf-8")).decode("ascii")
    return out, _receipt("enc_base64_std", before=text, after=out, lossless=True, note="base64 std encode; dec restores")


def _dec_base64_std(text: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = _b64.b64decode(text.encode("ascii")).decode("utf-8")
    return out, _receipt("dec_base64_std", before=text, after=out, lossless=True, note="base64 std decode")


def _enc_base64_url(text: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = _b64.urlsafe_b64encode(text.encode("utf-8")).decode("ascii")
    return out, _receipt("enc_base64_url", before=text, after=out, lossless=True, note="base64 urlsafe encode; dec restores")


def _dec_base64_url(text: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = _b64.urlsafe_b64decode(text.encode("ascii")).decode("utf-8")
    return out, _receipt("dec_base64_url", before=text, after=out, lossless=True, note="base64 urlsafe decode")


def _enc_base32(text: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = _b64.b32encode(text.encode("utf-8")).decode("ascii")
    return out, _receipt("enc_base32", before=text, after=out, lossless=True, note="base32 encode; dec restores")


def _dec_base32(text: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = _b64.b32decode(text.encode("ascii")).decode("utf-8")
    return out, _receipt("dec_base32", before=text, after=out, lossless=True, note="base32 decode")


def _enc_base16(text: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = _b64.b16encode(text.encode("utf-8")).decode("ascii")
    return out, _receipt("enc_base16", before=text, after=out, lossless=True, note="base16 (uppercase hex) encode; dec restores")


def _dec_base16(text: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = _b64.b16decode(text.encode("ascii")).decode("utf-8")
    return out, _receipt("dec_base16", before=text, after=out, lossless=True, note="base16 decode")


def _enc_base85(text: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = _b64.b85encode(text.encode("utf-8")).decode("ascii")
    return out, _receipt("enc_base85", before=text, after=out, lossless=True, note="base85 encode; dec restores")


def _dec_base85(text: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = _b64.b85decode(text.encode("ascii")).decode("utf-8")
    return out, _receipt("dec_base85", before=text, after=out, lossless=True, note="base85 decode")


def _enc_ascii85(text: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = _b64.a85encode(text.encode("utf-8")).decode("ascii")
    return out, _receipt("enc_ascii85", before=text, after=out, lossless=True, note="ascii85 encode; dec restores")


def _dec_ascii85(text: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = _b64.a85decode(text.encode("ascii")).decode("utf-8")
    return out, _receipt("dec_ascii85", before=text, after=out, lossless=True, note="ascii85 decode")


def _enc_hex(text: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = text.encode("utf-8").hex()
    return out, _receipt("enc_hex", before=text, after=out, lossless=True, note="lowercase hex encode; dec restores")


def _dec_hex(text: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = bytes.fromhex(text).decode("utf-8")
    return out, _receipt("dec_hex", before=text, after=out, lossless=True, note="hex decode")


def _url_quote(text: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = _up.quote(text)
    return out, _receipt("url_quote", before=text, after=out, lossless=True, note="url quote (safe='/'); unquote restores")


def _url_unquote(text: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = _up.unquote(text)
    return out, _receipt("url_unquote", before=text, after=out, lossless=True, note="url unquote")


def _url_quote_plus(text: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = _up.quote_plus(text)
    return out, _receipt("url_quote_plus", before=text, after=out, lossless=True, note="url quote_plus (space->+); unquote_plus restores")


def _url_unquote_plus(text: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = _up.unquote_plus(text)
    return out, _receipt("url_unquote_plus", before=text, after=out, lossless=True, note="url unquote_plus")


def _percent_encode_all(text: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = _up.quote(text, safe="")
    return out, _receipt("percent_encode_all", before=text, after=out, lossless=True, note="percent-encode all reserved (safe=''); percent_decode restores")


def _percent_decode(text: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = _up.unquote(text)
    return out, _receipt("percent_decode", before=text, after=out, lossless=True, note="percent decode")


def _rot13(text: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = _codecs.encode(text, "rot_13")
    return out, _receipt("rot13", before=text, after=out, lossless=True, note="rot13 (self-inverse)")


def _ascii_fold(text: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = _ud.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return out, _receipt("ascii_fold", before=text, after=out, lossless=False, note="fold accents to ascii (lossy)")


def _qp_encode(text: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = _quopri.encodestring(text.encode("utf-8")).decode("ascii")
    return out, _receipt("qp_encode", before=text, after=out, lossless=True, note="quoted-printable encode; qp_decode restores")


def _qp_decode(text: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = _quopri.decodestring(text.encode("ascii")).decode("utf-8")
    return out, _receipt("qp_decode", before=text, after=out, lossless=True, note="quoted-printable decode")


def _unicode_escape_encode(text: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = text.encode("unicode_escape").decode("ascii")
    return out, _receipt("unicode_escape_encode", before=text, after=out, lossless=True, note="unicode-escape encode; decode restores")


def _unicode_escape_decode(text: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = text.encode("ascii").decode("unicode_escape")
    return out, _receipt("unicode_escape_decode", before=text, after=out, lossless=True, note="unicode-escape decode")


def _html_escape(text: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = _html.escape(text)
    return out, _receipt("html_escape", before=text, after=out, lossless=True, note="html-escape entities; html_unescape restores")


def _html_unescape(text: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = _html.unescape(text)
    return out, _receipt("html_unescape", before=text, after=out, lossless=True, note="html unescape entities")


def _newline_escape(text: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = text.replace("\\", "\\\\").replace("\n", "\\n").replace("\t", "\\t")
    return out, _receipt("newline_escape", before=text, after=out, lossless=True, note="escape newlines/tabs to \\n/\\t; newline_unescape restores")


def _newline_unescape(text: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = text.replace("\\n", "\n").replace("\\t", "\t").replace("\\\\", "\\")
    return out, _receipt("newline_unescape", before=text, after=out, lossless=True, note="unescape \\n/\\t back to newlines/tabs")


def _char_to_binary(text: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = "".join(format(b, "08b") for b in text.encode("utf-8"))
    return out, _receipt("char_to_binary", before=text, after=out, lossless=True, note="chars->8-bit binary string; binary_to_char restores")


def _binary_to_char(text: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = bytes(int(text[i:i + 8], 2) for i in range(0, len(text), 8)).decode("utf-8")
    return out, _receipt("binary_to_char", before=text, after=out, lossless=True, note="8-bit binary string->chars")


#: new pure codec mutators to plug into the shared registry (idempotent registration; never overwrites)
_NEW_MUTATORS = {
    "enc_base64_std": _enc_base64_std, "dec_base64_std": _dec_base64_std,
    "enc_base64_url": _enc_base64_url, "dec_base64_url": _dec_base64_url,
    "enc_base32": _enc_base32, "dec_base32": _dec_base32,
    "enc_base16": _enc_base16, "dec_base16": _dec_base16,
    "enc_base85": _enc_base85, "dec_base85": _dec_base85,
    "enc_ascii85": _enc_ascii85, "dec_ascii85": _dec_ascii85,
    "enc_hex": _enc_hex, "dec_hex": _dec_hex,
    "url_quote": _url_quote, "url_unquote": _url_unquote,
    "url_quote_plus": _url_quote_plus, "url_unquote_plus": _url_unquote_plus,
    "percent_encode_all": _percent_encode_all, "percent_decode": _percent_decode,
    "rot13": _rot13, "ascii_fold": _ascii_fold,
    "qp_encode": _qp_encode, "qp_decode": _qp_decode,
    "unicode_escape_encode": _unicode_escape_encode, "unicode_escape_decode": _unicode_escape_decode,
    "html_escape": _html_escape, "html_unescape": _html_unescape,
    "newline_escape": _newline_escape, "newline_unescape": _newline_unescape,
    "char_to_binary": _char_to_binary, "binary_to_char": _binary_to_char,
}


def register_new_mutators() -> None:
    """Plug the codec mutators into the shared MUTATOR_REGISTRY (setdefault — idempotent, never overwrites)."""
    for name, fn in _NEW_MUTATORS.items():
        MUTATOR_REGISTRY.setdefault(name, fn)


register_new_mutators()


# ── the leaf primitives: each a REAL codec with a concrete fixture + expected (+ an inverse where reversible) ──
# spec fields: id, capability, mutator, fixture, expected, inverse?, input_edge, output_edge
LEAF_SPECS: list[dict[str, Any]] = [
    {"id": "prim:leaf:enc_base64_std", "capability": "base64 (standard) encode text",
     "mutator": "enc_base64_std", "fixture": "data", "expected": "ZGF0YQ==", "inverse": "dec_base64_std",
     "input_edge": "Text", "output_edge": "Base64Text"},
    {"id": "prim:leaf:dec_base64_std", "capability": "base64 (standard) decode",
     "mutator": "dec_base64_std", "fixture": "aGVsbG8=", "expected": "hello",
     "input_edge": "Base64Text", "output_edge": "Text"},
    {"id": "prim:leaf:enc_base64_url", "capability": "base64 (urlsafe) encode text",
     "mutator": "enc_base64_url", "fixture": ">>>?", "expected": "Pj4-Pw==", "inverse": "dec_base64_url",
     "input_edge": "Text", "output_edge": "Base64UrlText"},
    {"id": "prim:leaf:dec_base64_url", "capability": "base64 (urlsafe) decode",
     "mutator": "dec_base64_url", "fixture": "Pj4-Pw==", "expected": ">>>?",
     "input_edge": "Base64UrlText", "output_edge": "Text"},
    {"id": "prim:leaf:enc_base32", "capability": "base32 encode text",
     "mutator": "enc_base32", "fixture": "data", "expected": "MRQXIYI=", "inverse": "dec_base32",
     "input_edge": "Text", "output_edge": "Base32Text"},
    {"id": "prim:leaf:dec_base32", "capability": "base32 decode",
     "mutator": "dec_base32", "fixture": "MRQXIYI=", "expected": "data",
     "input_edge": "Base32Text", "output_edge": "Text"},
    {"id": "prim:leaf:enc_base16", "capability": "base16 (uppercase hex) encode text",
     "mutator": "enc_base16", "fixture": "data", "expected": "64617461", "inverse": "dec_base16",
     "input_edge": "Text", "output_edge": "Base16Text"},
    {"id": "prim:leaf:dec_base16", "capability": "base16 decode",
     "mutator": "dec_base16", "fixture": "64617461", "expected": "data",
     "input_edge": "Base16Text", "output_edge": "Text"},
    {"id": "prim:leaf:enc_base85", "capability": "base85 encode text",
     "mutator": "enc_base85", "fixture": "data", "expected": "WMOn+", "inverse": "dec_base85",
     "input_edge": "Text", "output_edge": "Base85Text"},
    {"id": "prim:leaf:dec_base85", "capability": "base85 decode",
     "mutator": "dec_base85", "fixture": "WMOn+", "expected": "data",
     "input_edge": "Base85Text", "output_edge": "Text"},
    {"id": "prim:leaf:enc_ascii85", "capability": "ascii85 encode text",
     "mutator": "enc_ascii85", "fixture": "data", "expected": "A79Rg", "inverse": "dec_ascii85",
     "input_edge": "Text", "output_edge": "Ascii85Text"},
    {"id": "prim:leaf:dec_ascii85", "capability": "ascii85 decode",
     "mutator": "dec_ascii85", "fixture": "A79Rg", "expected": "data",
     "input_edge": "Ascii85Text", "output_edge": "Text"},
    {"id": "prim:leaf:enc_hex", "capability": "lowercase hex encode text",
     "mutator": "enc_hex", "fixture": "data", "expected": "64617461", "inverse": "dec_hex",
     "input_edge": "Text", "output_edge": "HexText"},
    {"id": "prim:leaf:dec_hex", "capability": "hex decode",
     "mutator": "dec_hex", "fixture": "68656c6c6f", "expected": "hello",
     "input_edge": "HexText", "output_edge": "Text"},
    {"id": "prim:leaf:url_quote", "capability": "url percent-quote a string",
     "mutator": "url_quote", "fixture": "a b/c", "expected": "a%20b/c", "inverse": "url_unquote",
     "input_edge": "Text", "output_edge": "PercentEncodedText"},
    {"id": "prim:leaf:url_unquote", "capability": "url percent-unquote a string",
     "mutator": "url_unquote", "fixture": "a%20b", "expected": "a b",
     "input_edge": "PercentEncodedText", "output_edge": "Text"},
    {"id": "prim:leaf:url_quote_plus", "capability": "url quote_plus (space->+) a string",
     "mutator": "url_quote_plus", "fixture": "a b+c", "expected": "a+b%2Bc", "inverse": "url_unquote_plus",
     "input_edge": "Text", "output_edge": "FormEncodedText"},
    {"id": "prim:leaf:url_unquote_plus", "capability": "url unquote_plus a string",
     "mutator": "url_unquote_plus", "fixture": "a+b", "expected": "a b",
     "input_edge": "FormEncodedText", "output_edge": "Text"},
    {"id": "prim:leaf:percent_encode_all", "capability": "percent-encode all reserved characters",
     "mutator": "percent_encode_all", "fixture": "a b/c", "expected": "a%20b%2Fc", "inverse": "percent_decode",
     "input_edge": "Text", "output_edge": "PercentEncodedText"},
    {"id": "prim:leaf:percent_decode", "capability": "percent-decode a string",
     "mutator": "percent_decode", "fixture": "a%2Fb", "expected": "a/b",
     "input_edge": "PercentEncodedText", "output_edge": "Text"},
    {"id": "prim:leaf:rot13", "capability": "rot13 transform text (self-inverse)",
     "mutator": "rot13", "fixture": "Hello", "expected": "Uryyb", "inverse": "rot13",
     "input_edge": "Text", "output_edge": "Rot13Text"},
    {"id": "prim:leaf:ascii_fold_cafe", "capability": "fold accented text to ascii (café->cafe)",
     "mutator": "ascii_fold", "fixture": "café", "expected": "cafe",
     "input_edge": "UnicodeText", "output_edge": "AsciiText"},
    {"id": "prim:leaf:ascii_fold_naive", "capability": "fold accented text to ascii (naïve->naive)",
     "mutator": "ascii_fold", "fixture": "naïve", "expected": "naive",
     "input_edge": "UnicodeText", "output_edge": "AsciiText"},
    {"id": "prim:leaf:qp_encode", "capability": "quoted-printable encode text",
     "mutator": "qp_encode", "fixture": "a=b", "expected": "a=3Db", "inverse": "qp_decode",
     "input_edge": "Text", "output_edge": "QuotedPrintableText"},
    {"id": "prim:leaf:qp_decode", "capability": "quoted-printable decode",
     "mutator": "qp_decode", "fixture": "a=3Db", "expected": "a=b",
     "input_edge": "QuotedPrintableText", "output_edge": "Text"},
    {"id": "prim:leaf:unicode_escape_encode", "capability": "unicode-escape encode text",
     "mutator": "unicode_escape_encode", "fixture": "a\tb", "expected": "a\\tb", "inverse": "unicode_escape_decode",
     "input_edge": "Text", "output_edge": "UnicodeEscapedText"},
    {"id": "prim:leaf:unicode_escape_decode", "capability": "unicode-escape decode",
     "mutator": "unicode_escape_decode", "fixture": "a\\tb", "expected": "a\tb",
     "input_edge": "UnicodeEscapedText", "output_edge": "Text"},
    {"id": "prim:leaf:html_escape", "capability": "html-escape entities",
     "mutator": "html_escape", "fixture": "<a>&", "expected": "&lt;a&gt;&amp;", "inverse": "html_unescape",
     "input_edge": "Text", "output_edge": "HtmlEscapedText"},
    {"id": "prim:leaf:html_unescape", "capability": "html unescape entities",
     "mutator": "html_unescape", "fixture": "&lt;a&gt;", "expected": "<a>",
     "input_edge": "HtmlEscapedText", "output_edge": "Text"},
    {"id": "prim:leaf:newline_escape", "capability": "escape newlines/tabs to \\n/\\t",
     "mutator": "newline_escape", "fixture": "a\nb", "expected": "a\\nb", "inverse": "newline_unescape",
     "input_edge": "Text", "output_edge": "EscapedText"},
    {"id": "prim:leaf:newline_unescape", "capability": "unescape \\n/\\t to newlines/tabs",
     "mutator": "newline_unescape", "fixture": "a\\nb", "expected": "a\nb",
     "input_edge": "EscapedText", "output_edge": "Text"},
    {"id": "prim:leaf:char_to_binary", "capability": "encode chars to an 8-bit binary string",
     "mutator": "char_to_binary", "fixture": "A", "expected": "01000001", "inverse": "binary_to_char",
     "input_edge": "Text", "output_edge": "BinaryString"},
    {"id": "prim:leaf:binary_to_char", "capability": "decode an 8-bit binary string to chars",
     "mutator": "binary_to_char", "fixture": "01000001", "expected": "A",
     "input_edge": "BinaryString", "output_edge": "Text"},
]

#: deliberately-wrong leaf — the proof gate MUST leave it candidate (never persisted as proven)
NEGATIVE_SPECS: list[dict[str, Any]] = [
    {"id": "prim:leaf:WRONG_base64", "capability": "base64 encode with a wrong expected output",
     "mutator": "enc_base64_std", "fixture": "data", "expected": "WRONG!!", "inverse": "dec_base64_std",
     "input_edge": "Text", "output_edge": "Base64Text"},
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
    """Run every declared leaf primitive through the imported executed-proof runner."""
    return [_prove_one(s) for s in LEAF_SPECS]


def _typed_row(receipt: dict[str, Any]) -> dict[str, Any]:
    """A persisted WORKABLE row: proven (serves_truth=true) AND typed (canonical edge type_ids)."""
    return {
        "record_type": "proven_leaf_primitive",
        "primitive_id": receipt["primitive_id"],
        "mutator": receipt["mutator"],
        "family": FAMILY,
        "capability": receipt["capability"],
        "serves_truth": True,
        "candidate": False,
        "verification_level": "L7_executed_proof",
        "input_edge": receipt["input_edge"],
        "output_edge": receipt["output_edge"],
        # THE TYPING FIX: a workable primitive carries canonical edge types so it can chain.
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


def build_manifest(rows: list[dict[str, Any]]) -> dict[str, Any]:
    typed = [r for r in rows if r["input_edge_type_id"] and r["output_edge_type_id"]]
    return {
        "record_type": "proven_encoding_codec_manifest",
        "pack_id": "proven-encoding-codec-leaves",
        "family": FAMILY,
        "generator": "scripts/prove_leaves_encoding_codec.py",
        "generated_utc": FROZEN_TS,
        "declared_leaf_count": len(LEAF_SPECS),
        "proven_count": len(rows),
        "typed_count": len(typed),
        "roundtrip_pair_count": sum(1 for r in rows if r["has_roundtrip_proof"]),
        "verification_level": "L7_executed_proof",
        "proven_primitive_ids": [r["primitive_id"] for r in rows],
        "note": "serves_truth=true here is CORRECT + required — set ONLY by an executed passing proof "
                "(run_primitive_proof, imported from scripts/mutator_registry.py). Every persisted row is also "
                "TYPED via canonicalize_edge (imported from scripts/build_edge_type_retrofit.py) so it can chain. "
                "A deliberately-wrong leaf stays candidate and is never persisted here.",
    }


def write_pack() -> dict[str, Any]:
    rows = proven_typed_rows()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSONL.write_text(
        "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows), encoding="utf-8")
    manifest = build_manifest(rows)
    OUT_MANIFEST.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def self_test() -> int:
    receipts = prove_all()
    rows = proven_typed_rows()
    ids = [r["primitive_id"] for r in receipts]

    # a deliberately-wrong-expected leaf must stay CANDIDATE (the gate is real)
    wrong = run_primitive_proof(
        NEGATIVE_SPECS[0]["id"], NEGATIVE_SPECS[0]["mutator"], NEGATIVE_SPECS[0]["fixture"],
        NEGATIVE_SPECS[0]["expected"], has_inverse=NEGATIVE_SPECS[0].get("inverse"))
    # a second wrong path: an un-runnable fixture (bad hex) -> execution error -> not promoted
    err = run_primitive_proof("prim:leaf:EXEC_ERROR", "dec_hex", "zzzz", "irrelevant")

    inverse_specs = [s for s in LEAF_SPECS if s.get("inverse")]
    proven_ids = {r["primitive_id"] for r in rows}

    checks: list[tuple[str, bool]] = [
        (">=28 leaf primitives declared", len(LEAF_SPECS) >= 28),
        ("unique primitive ids", len(set(ids)) == len(ids)),
        (">=28 leaves PROVE serves_truth=true via an executed proof", len(rows) >= 28),
        ("EVERY declared leaf proved (all promoted)",
         all(r["serves_truth"] is True and r["promoted"] is True for r in receipts)),
        ("every proven receipt is L7_executed_proof with all sub-proofs passing",
         all(r["verification_level"] == "L7_executed_proof" and all(p["passed"] for p in r["proofs"]) for r in receipts)),
        ("EVERY persisted row carries a non-null input_edge_type_id",
         all(bool(r["input_edge_type_id"]) for r in rows)),
        ("EVERY persisted row carries a non-null output_edge_type_id",
         all(bool(r["output_edge_type_id"]) for r in rows)),
        ("typed_count == proven_count (every workable leaf is typed)",
         build_manifest(rows)["typed_count"] == build_manifest(rows)["proven_count"] == len(rows)),
        ("roundtrip-inverse pairs prove reversible (roundtrip_test passed)",
         all(any(p["name"] == "roundtrip_test" and p["passed"] for p in _prove_one(s)["proofs"]) for s in inverse_specs)),
        (">=15 reversible enc/dec roundtrip pairs proven",
         sum(1 for r in rows if r["has_roundtrip_proof"]) >= 15),
        ("deterministic: re-running yields identical typed rows",
         [json.dumps(r, sort_keys=True) for r in proven_typed_rows()]
         == [json.dumps(r, sort_keys=True) for r in rows]),
        ("a deliberately-wrong-expected leaf stays CANDIDATE (never promoted)",
         wrong["serves_truth"] is False and wrong["promoted"] is False),
        ("the wrong leaf is NOT in the persisted rows", NEGATIVE_SPECS[0]["id"] not in proven_ids),
        ("an un-runnable fixture fails the proof, does not promote",
         err["serves_truth"] is False and err["promoted"] is False),
        ("codec mutators registered into the shared registry (add-only seam)",
         all(m in MUTATOR_REGISTRY for m in _NEW_MUTATORS)),
    ]
    failed = [n for n, ok in checks if not ok]
    if failed:
        print("FAIL - prove_leaves_encoding_codec:\n  " + "\n  ".join(failed))
        return 1
    print(f"PASS - prove_leaves_encoding_codec: {len(rows)} WORKABLE encoding_codec leaf primitives — PROVEN "
          f"(serves_truth=true via executed proof, L7) AND TYPED (canonical input/output edge type_ids); "
          f"{sum(1 for r in rows if r['has_roundtrip_proof'])} reversible enc/dec pairs proven via roundtrip. "
          "A wrong-expected leaf and an un-runnable fixture correctly stay candidate.")
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
